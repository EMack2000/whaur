// Builds the single-file game: takes the page template, the map shapes and the places list,
// and writes dist/whaur.html.   Run with:  node build.js
const fs = require("fs");
const path = require("path");
const here = (...p) => path.join(__dirname, ...p);
const PLACES = require("./src/places.js");

const F = 2000; // coordinates are stored to 1/2000 of a degree (about 30-50 m)

// Compact "polyline" text encoding, so thousands of coastline points stay small in the page.
function enc(v) {
  v = v < 0 ? ~(v << 1) : v << 1;
  let s = "";
  while (v >= 0x20) { s += String.fromCharCode((0x20 | (v & 0x1f)) + 63); v >>= 5; }
  return s + String.fromCharCode(v + 63);
}
function encodeLine(line) {
  let pa = 0, pb = 0, s = "", n = 0;
  for (const [lon, lat] of line) {
    const a = Math.round(lat * F), b = Math.round(lon * F);
    if (n && a === pa && b === pb) continue;
    s += enc(a - pa) + enc(b - pb); pa = a; pb = b; n++;
  }
  return n > 1 ? s : null;
}
function lines(file) {
  const g = JSON.parse(fs.readFileSync(here("data", file)));
  const geoms = g.features ? g.features.map(f => f.geometry) : g.geometries || [g];
  const out = [];
  for (const geom of geoms) {
    if (!geom) continue;
    const c = geom.coordinates;
    const sets = geom.type === "Polygon" ? c : geom.type === "MultiPolygon" ? c.flat() :
                 geom.type === "LineString" ? [c] : geom.type === "MultiLineString" ? c : [];
    for (const l of sets) { const e = encodeLine(l); if (e) out.push(e); }
  }
  return out;
}

const sat = JSON.parse(fs.readFileSync(here("data", "sat", "sat.json")));   // made by tools/make_satellite.py
const DATA = { f: F, land: lines("land.geojson"), sat };
const safe = o => JSON.stringify(o).replace(/</g, "\\u003c");
let html = fs.readFileSync(here("src", "page.html"), "utf8");
html = html.replace("/*__DATA__*/null", () => safe(DATA)).replace("/*__PLACES__*/null", () => safe(PLACES));
fs.mkdirSync(here("dist"), { recursive: true });
fs.writeFileSync(here("dist", "whaur.html"), html);
for (const f of ["sat-medium.webp", "sat-full.webp"]) fs.copyFileSync(here("data", "sat", f), here("dist", f));
console.log("Built dist/whaur.html -", Math.round(html.length / 1024), "KB,", PLACES.length, "places");

// ── The stand-alone web app (the docs/ folder is what GitHub Pages serves) ──
// dist/whaur.html is only the inside of a page. A real website needs the full wrapper: a head with the
// title, the phone settings, the home-screen icon and the link-preview details.
// Set SITE_URL when building so link previews can point at the picture, e.g.
//   SITE_URL=https://example.com/whaur/ node build.js
const SITE_URL = (process.env.SITE_URL || "").replace(/\/?$/, "/").replace(/^\/$/, "");
const DESCRIPTION = "A daily map game for Scotland. Find five places on a satellite view and score out of 1,000.";
const cut = html.indexOf('<div class="app">');
const headPart = html.slice(0, cut).replace(/<meta name="claude:viewport-fit-sides"[^>]*>\s*/, "");
const bodyPart = html.slice(cut);
const page = `<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="${DESCRIPTION}">
<meta name="theme-color" content="#0b57b8">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="icon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Whaur?">
<meta name="mobile-web-app-capable" content="yes">
<meta property="og:type" content="website">
<meta property="og:title" content="Whaur?">
<meta property="og:description" content="${DESCRIPTION}">
${SITE_URL ? `<meta property="og:url" content="${SITE_URL}">
<meta property="og:image" content="${SITE_URL}share.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">` : ""}
<style>
html { height: 100%; box-sizing: border-box; background: #0b57b8; color-scheme: light;
  padding: env(safe-area-inset-top, 0px) 0 env(safe-area-inset-bottom, 0px); }
body { margin: 0; font: 14px system-ui, sans-serif; overscroll-behavior: none; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
${headPart.trim()}
</head>
<body>
${bodyPart.trim()}
</body>
</html>
`;
const manifest = {
  name: "Whaur?", short_name: "Whaur?", description: DESCRIPTION, lang: "en-GB",
  start_url: "./", scope: "./", display: "standalone", orientation: "any",
  background_color: "#0b57b8", theme_color: "#0b57b8",
  icons: [
    { src: "icon-192.png", sizes: "192x192", type: "image/png" },
    { src: "icon-512.png", sizes: "512x512", type: "image/png" },
    { src: "icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
  ],
};
fs.mkdirSync(here("docs"), { recursive: true });
fs.writeFileSync(here("docs", "index.html"), page);
fs.writeFileSync(here("docs", "manifest.webmanifest"), JSON.stringify(manifest, null, 2));
fs.writeFileSync(here("docs", ".nojekyll"), "");
for (const f of ["sat-medium.webp", "sat-full.webp"]) fs.copyFileSync(here("data", "sat", f), here("docs", f));
if (fs.existsSync(here("data", "icons"))) for (const f of fs.readdirSync(here("data", "icons"))) fs.copyFileSync(here("data", "icons", f), here("docs", f));
console.log("Built docs/ -", fs.readdirSync(here("docs")).join(", "), SITE_URL ? "for " + SITE_URL : "(no SITE_URL set: link preview picture left out)");
