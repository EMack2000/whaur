"""Builds the satellite base map for the game.

What it does, in order:
  1. Downloads the Sentinel-2 cloudless mosaic for Scotland from EOX in pieces.
  2. Re-draws it in the same map projection the game uses, so pins land in the right place.
  3. Brightens it for phone screens.
  4. Greys out land that is not in play (England, Ireland, Isle of Man).
  5. Saves three sizes: a tiny one built into the page, a medium one and a full one.

Run with:  python3 tools/make_satellite.py <folder for downloaded pieces>
Imagery: EOxCloudless by EOX IT Services GmbH, CC BY-NC-SA 4.0 (non-commercial, share-alike).
"""
import base64, io, json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1]
YEAR = 2025
LAYER = "s2cloudless-%d" % YEAR

# The game's projection (must match project() in src/page.html): km east and km south of a centre point.
R, LON0, LAT0 = 6371.0, math.radians(-4.2), math.radians(57.7)
def project(lon, lat):
    l, p = np.radians(lon) - LON0, np.radians(lat)
    return R * np.arctanh(np.cos(p) * np.sin(l)), -R * (np.arctan2(np.tan(p), np.cos(l)) - LAT0)
def unproject(x, y):
    X, Y = x / R, -y / R + LAT0
    return np.degrees(LON0 + np.arctan2(np.sinh(X), np.cos(Y))), np.degrees(np.arcsin(np.sin(Y) / np.cosh(X)))

# The area the image covers, in km, and its detail.
X0, Y0, X1, Y1 = -345.0, -425.0, 272.0, 412.0
KM_PER_PX = 0.205
W, H = round((X1 - X0) / KM_PER_PX), round((Y1 - Y0) / KM_PER_PX)

# 1. Download ---------------------------------------------------------------
ex = np.linspace(X0, X1, 50); ey = np.linspace(Y0, Y1, 50)
gx, gy = np.meshgrid(ex, ey); glon, glat = unproject(gx, gy)
LON_A, LON_B = math.floor(glon.min() * 10) / 10 - .1, math.ceil(glon.max() * 10) / 10 + .1
LAT_A, LAT_B = math.floor(glat.min() * 10) / 10 - .1, math.ceil(glat.max() * 10) / 10 + .1
DLON, DLAT = 0.0022, 0.0012          # about 130 m per source pixel
SW, SH = round((LON_B - LON_A) / DLON), round((LAT_B - LAT_A) / DLAT)
CH = 1800
src = np.zeros((SH, SW, 3), np.uint8)
for j in range(0, SH, CH):
    for i in range(0, SW, CH):
        w, h = min(CH, SW - i), min(CH, SH - j)
        lon_a, lon_b = LON_A + i * DLON, LON_A + (i + w) * DLON
        lat_b, lat_a = LAT_B - j * DLAT, LAT_B - (j + h) * DLAT
        f = os.path.join(CACHE, "%s_%d_%d.jpg" % (LAYER, i, j))
        if not os.path.exists(f) or os.path.getsize(f) < 2000:
            url = ("https://tiles.maps.eox.at/wms?service=WMS&version=1.1.1&request=GetMap&layers=%s&styles=&srs=EPSG:4326"
                   "&bbox=%.6f,%.6f,%.6f,%.6f&width=%d&height=%d&format=image/jpeg" % (LAYER, lon_a, lat_a, lon_b, lat_b, w, h))
            subprocess.run(["curl", "-sS", "-m", "180", "--retry", "2", "-o", f, url], check=True)
        src[j:j + h, i:i + w] = np.asarray(Image.open(f).convert("RGB"))
print("downloaded", SW, "x", SH)

# 2. Re-draw in the game's projection (at double size, then shrink, for a smooth result) ----------
SS = 2
px = X0 + (np.arange(W * SS, dtype=np.float64) + .5) * KM_PER_PX / SS
py = Y0 + (np.arange(H * SS, dtype=np.float64) + .5) * KM_PER_PX / SS
out = np.zeros((H * SS, W * SS, 3), np.uint8)
for a in range(0, H * SS, 1024):
    b = min(H * SS, a + 1024)
    mx, my = np.meshgrid(px, py[a:b])
    lon, lat = unproject(mx, my)
    out[a:b] = cv2.remap(src, ((lon - LON_A) / DLON - .5).astype(np.float32), ((LAT_B - lat) / DLAT - .5).astype(np.float32),
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
img = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
del src, out

# 3. Brighten ---------------------------------------------------------------
img = np.power(img, 0.66)
lum = (img * [0.299, 0.587, 0.114]).sum(2, keepdims=True)
img = np.clip(lum + (img - lum) * 1.18, 0, 1)            # a little more colour
img = np.clip((img - .5) * 1.06 + .5, 0, 1)              # a little more contrast

# 4. Grey out land that is not in play --------------------------------------
def rings(name):
    g = json.load(open(os.path.join(HERE, "data", name)))
    geoms = [f["geometry"] for f in g["features"]] if "features" in g else g.get("geometries", [g])
    for geom in geoms:
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            yield poly
def mask(name):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for poly in rings(name):
        for k, ring in enumerate(poly):
            a = np.asarray(ring, np.float64); x, y = project(a[:, 0], a[:, 1])
            pts = list(zip(((x - X0) / KM_PER_PX).tolist(), ((y - Y0) / KM_PER_PX).tolist()))
            if len(pts) > 2: d.polygon(pts, fill=255 if k == 0 else 0)
    return m
scot = np.asarray(mask("land.geojson"), np.float32) / 255
off = np.maximum(np.asarray(mask("mask-england.geojson").filter(ImageFilter.MaxFilter(5)), np.float32),
                 np.asarray(mask("mask-ireland.geojson").filter(ImageFilter.MaxFilter(13)), np.float32)) / 255
off = off * (1 - scot)
blueness = img[..., 2] - np.maximum(img[..., 0], img[..., 1])          # sea is blue, land is not
off = cv2.GaussianBlur(off * np.clip((.04 - blueness) / .08, 0, 1), (0, 0), 1.2)[..., None]
lum = (img * [0.299, 0.587, 0.114]).sum(2, keepdims=True)

# The flat sea colour used beyond the edge of the image.
edge = np.concatenate([img[:12].reshape(-1, 3), img[:, :12].reshape(-1, 3), img[:, -12:].reshape(-1, 3)])
sea = np.median(edge, 0)
shaded = (lum * .8 + img * .2) * .5 + sea * .16
img = img * (1 - off) + shaded * off

# Fade the outer 30 km into the flat sea colour so the image has no visible edge.
fx = np.minimum(np.arange(W), W - 1 - np.arange(W)) * KM_PER_PX / 30
fy = np.minimum(np.arange(H), H - 1 - np.arange(H)) * KM_PER_PX / 30
fade = np.clip(np.minimum(fx[None, :], fy[:, None]), 0, 1)[..., None]
img = img * fade + sea * (1 - fade)

# 5. Save -------------------------------------------------------------------
full = Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8))
os.makedirs(os.path.join(HERE, "data", "sat"), exist_ok=True)
full.save(os.path.join(HERE, "data", "sat", "sat-full.webp"), quality=80, method=6)
med = full.resize((W // 3, H // 3), Image.LANCZOS)
med.save(os.path.join(HERE, "data", "sat", "sat-medium.webp"), quality=82, method=6)
buf = io.BytesIO(); full.resize((W // 10, H // 10), Image.LANCZOS).save(buf, "JPEG", quality=58, optimize=True)
meta = {"x0": X0, "y0": Y0, "w": X1 - X0, "h": Y1 - Y0, "kmPerPx": KM_PER_PX, "year": YEAR,
        "sea": "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in sea),
        "thumb": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}
json.dump(meta, open(os.path.join(HERE, "data", "sat", "sat.json"), "w"))
med.convert("RGB").save(os.path.join(HERE, "data", "sat", "check-medium.jpg"), quality=85)
print("image", W, "x", H, "sea", meta["sea"], "thumb KB", len(meta["thumb"]) // 1024)
for n in ("sat-full.webp", "sat-medium.webp"): print(n, os.path.getsize(os.path.join(HERE, "data", "sat", n)) // 1024, "KB")
