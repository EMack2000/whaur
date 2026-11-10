"""Draws the home-screen icons and the link-preview picture for the hosted game.

Icon: the Saltire (white diagonal cross on blue) with the game's yellow target at the centre.
Run with:  python3 tools/make_icons.py <folder holding the two font packages>
"""
import os, sys
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "icons"); os.makedirs(OUT, exist_ok=True)
FONTS = sys.argv[1]
BLUE, DEEP, WHITE, GORSE = (11, 87, 184), (7, 52, 118), (255, 255, 255), (255, 200, 61)

def icon(size, inset):
    """inset = how far the artwork is pulled in from the edge (bigger for icons the phone crops to a circle)."""
    n = 1024; im = Image.new("RGB", (n, n), BLUE); d = ImageDraw.Draw(im)
    w = int(n * .12)
    d.line([(0, 0), (n, n)], fill=WHITE, width=w); d.line([(n, 0), (0, n)], fill=WHITE, width=w)
    c, r = n / 2, n * (.30 - inset)
    disc = lambda rad, fill: d.ellipse([c - rad, c - rad, c + rad, c + rad], fill=fill)
    disc(r * 1.16, BLUE); disc(r, GORSE); disc(r * .72, DEEP); disc(r * .34, GORSE)
    return im.resize((size, size), Image.LANCZOS)

icon(512, 0).save(os.path.join(OUT, "icon-512.png"))
icon(192, 0).save(os.path.join(OUT, "icon-192.png"))
icon(180, 0).save(os.path.join(OUT, "apple-touch-icon.png"))
icon(32, 0).save(os.path.join(OUT, "icon-32.png"))
icon(512, .05).save(os.path.join(OUT, "icon-maskable-512.png"))

# Link-preview picture (what WhatsApp, iMessage and so on show when the link is shared).
sat = "file://" + os.path.join(HERE, "data", "sat", "sat-full.webp")
f1 = "file://" + os.path.join(FONTS, "@fontsource/bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff2")
f2 = "file://" + os.path.join(FONTS, "@fontsource/newsreader/files/newsreader-latin-400-italic.woff2")
html = f"""<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: B; src: url("{f1}"); font-weight: 800; }}
@font-face {{ font-family: N; src: url("{f2}"); font-style: italic; }}
body {{ margin: 0; width: 1200px; height: 630px; display: grid; grid-template-columns: 560px 640px; background: #0b57b8; color: #fff; overflow: hidden; }}
.t {{ padding: 0 64px; display: flex; flex-direction: column; justify-content: center; gap: 18px; }}
h1 {{ margin: 0; font: 800 132px/0.9 B, sans-serif; letter-spacing: -.04em; }} h1 b {{ color: #ffc83d; }}
.tag {{ margin: 0; font: italic 38px/1.1 N, serif; opacity: .95; }}
.d {{ margin: 18px 0 0; font: italic 30px/1.3 N, serif; opacity: .9; max-width: 400px; }}
.m {{ position: relative; background: #2a4975 url("{sat}") no-repeat; background-size: 880px auto; background-position: -130px -428px; }}
.c {{ position: absolute; left: 14px; right: 14px; bottom: 10px; font: 13px/1.3 sans-serif; color: rgba(255,255,255,.85); text-shadow: 0 1px 2px #000; }}
</style><div class="t"><h1>Whaur<b>?</b></h1><p class="tag">Scots for &ldquo;where?&rdquo;</p><p class="d">Five Scottish places a day. Tap the map, score out of 1,000.</p></div>
<div class="m"><div class="c">EOxCloudless by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2025)</div></div>"""
tmp = os.path.join(OUT, "_share.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + tmp); pg.wait_for_timeout(600); pg.screenshot(path=os.path.join(OUT, "share.jpg"), type="jpeg", quality=86); b.close()
os.remove(tmp)
print(sorted(os.listdir(OUT)))
