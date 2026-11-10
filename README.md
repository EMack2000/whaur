# Whaur?

*Scots for "where?"*

A daily map game for Scotland. You get five Scottish places a day, tap a satellite map where you think
each one is, and score out of 1,000. Everyone gets the same five places on the same day.

Play it: https://emack2000.github.io/whaur/

It is a free, non-commercial project for friends and family.

## How it is put together

| Folder or file | What it is |
| --- | --- |
| `src/places.js` | The list of places: name, coordinates, difficulty tier and a short story. The file to edit most. |
| `src/page.html` | The game itself: layout, colours and all the game code. |
| `data/` | The map: Scotland's coastline, the satellite picture and the app icons. |
| `tools/` | Scripts that made the satellite picture and the icons. Only needed if those change. |
| `build.js` | Combines the files above into the finished game. |
| `docs/` | The finished game. This folder is the website. |

## Changing something

1. Edit `src/places.js` (to add or fix a place) or `src/page.html` (to change the game).
2. Rebuild: `SITE_URL=https://emack2000.github.io/whaur/ node build.js`
3. Commit and push. The website updates a minute or two later.

Adding or removing places reshuffles which places come up on future days.

## Scores

Scores are saved in each player's own browser. Nothing is sent anywhere, and there are no accounts.

## Credits

- Satellite image: [EOxCloudless](https://cloudless.eox.at) by [EOX IT Services GmbH](https://eox.at)
  (Contains modified Copernicus Sentinel data 2025), used under
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). It has been re-projected,
  brightened and partly greyed for this game. The image files in `data/sat/` and `docs/` carry the same
  licence: non-commercial use only, share-alike.
- Coastline: contains National Statistics and OS data © Crown copyright and database right, via the
  [UK-GeoJSON](https://github.com/martinjc/UK-GeoJSON) project.
- Neighbouring coasts used for shading: [Natural Earth](https://www.naturalearthdata.com).
- The idea of a daily tap-the-map game comes from [MapTap](https://maptap.gg). This is an independent
  project and is not connected to it.
