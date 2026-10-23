"""Add new clips in clips/ to clips/clips.json with text placement guessed from brightness.

    python3 -I toolkit/clipinfo.py <repo_root>

For every clip not yet in clips.json: samples 5 frames, measures how bright the upper text
area (y 250..700) and the lower text area (y 1100..1550) are, puts the text in the darker one,
and sets blob (text area darkening) and an optional gamma pre filter for bright clips.
Existing entries are never changed, so hand tuned values stay.
"""
import json, os, subprocess, sys
import numpy as np

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
CJ = os.path.join(ROOT, "clips", "clips.json")
data = json.load(open(CJ)) if os.path.exists(CJ) else {}


def frames(path):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.strip() or 0)
    out = []
    for k in range(5):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{d * (k + 0.5) / 5:.2f}", "-i", path, "-frames:v", "1",
                              "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=gray",
                              "-f", "rawvideo", "-"], capture_output=True).stdout
        if len(raw) == 1080 * 1920:
            out.append(np.frombuffer(raw, np.uint8).reshape(1920, 1080))
    return d, out


for f in sorted(os.listdir(os.path.join(ROOT, "clips"))):
    if not f.endswith(".mp4") or f in data:
        continue
    d, fr = frames(os.path.join(ROOT, "clips", f))
    if not fr:
        print("skip", f); continue
    top = float(np.mean([x[250:700, 60:760].mean() for x in fr]))
    low = float(np.mean([x[1100:1550, 60:760].mean() for x in fr]))
    whole = float(np.mean([x.mean() for x in fr]))
    use_top = top <= low * 1.15
    area = top if use_top else low
    e = {"y0": 330 if use_top else 1160, "top": use_top,
         "blob": round(min(0.6, max(0.3, 0.3 + area / 200)), 2),
         "pre": "eq=gamma=0.72:brightness=-0.06," if whole > 70 else "",
         "len": round(d, 2), "tags": ["new"], "last_used": ""}
    data[f] = e
    print(f, e, f"top={top:.0f} low={low:.0f} whole={whole:.0f}")

json.dump(data, open(CJ, "w"), indent=1, sort_keys=True)
