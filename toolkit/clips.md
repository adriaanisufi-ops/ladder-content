# Clip library (ladder-content/clips)

All clips are free Pexels videos. Text position values are what worked in reel.py.

## Use these (night, cars, city, nature, no people)
| File | What | Text | Settings |
|---|---|---|---|
| ladder-src-11.mp4 | Night highway, driver view, street lamps, 31s | bottom | y0 1160, top false, blob 0.45 |
| ladder-src-12.mp4 | City highway traffic seen from a bridge, dark sky, 25s | top | y0 330, blob 0.3 |
| ladder-src-13.mp4 | Rainy highway, wet reflections, lamps, 19s | top | y0 300, blob 0.45 |
| ladder-src-14.mp4 | Side mirror in a tunnel, very dark, 21s | bottom | y0 1180, top false, blob 0.3 |
| ladder-src-15.mp4 | Wet street with tall lamps, teal sky, 54s | top | y0 330, blob 0.45 |
| ladder-src-03c.mp4 | City at night from a drone, dark sky above, 31s | top | y0 380, blob 0.35 |
| ladder-stad-11240584.mp4 | Suburb at night from above, orange lights, 46s | top | y0 260, blob 0.4 (good for book outro) |
| ladder-stad-19735541.mp4 | Drone over a city street with cars, 21s | top | y0 560 (video 02 used a mirrored version) |
| ladder-snelweg-36601677-4k.mp4 | Empty highway at night, black and white, 23s | top | y0 560 (video 01) |
| ladder-src-07.mp4 | Waves on black sand from above, 28s | top | y0 560 |
| ladder-src-10.mp4 | Moonlight on the sea, 15s | top | y0 560 |

## Do not use (Adriaan did not like these)
ladder-src-03, 03b, 04, 04b, 05, 06, 08, 09: people, objects or too abstract. Keep to vibe footage: cars, roads, city lights, buildings, nature.

## Finding new clips
Pexels is only reachable through the browser pane in the Claude desktop app, not from a shell.
Search portrait videos: `https://www.pexels.com/search/videos/QUERY/?orientation=portrait`
Good queries: night drive highway, car driving at night, rainy road night car, city at night aerial, tunnel lights night drive.

## Pexels batch, 2026-10-23 (pex-*.mp4)
59 night clips with cars, roads and city lights, picked from a contact sheet. Text placement per clip is in `clips/clips.json` (guessed from brightness by `toolkit/clipinfo.py`; fix it there when a render shows a problem).
