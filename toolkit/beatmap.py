"""Measure a sound for the VYZEE engine: beat grid, the silence before the drop, the drop beat and the breakdown.

Usage:  python3 toolkit/beatmap.py SOUND(.mp3/.m4a/.mp4/.wav) toolkit/sounds/<name>.json [--start 0] [--name "..."]
SOUND = the trending sound as Adriaan will use it in TikTok (saved video or screen recording, starting at 0:00 of "Use this sound").
Prints the map and writes the profile; a spec picks it with "sound": "<name>". Always check the printed drop by ear/eye:
pass --drop SECONDS (and --break SECONDS) to override when the guess is wrong.
"""
import argparse, json, os, subprocess, tempfile
import numpy as np
import librosa

ap = argparse.ArgumentParser()
ap.add_argument("sound"); ap.add_argument("out")
ap.add_argument("--start", type=float, default=0.0); ap.add_argument("--name")
ap.add_argument("--drop", type=float); ap.add_argument("--brk", "--break", dest="brk", type=float)
a = ap.parse_args()

wav = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", a.sound, "-vn", "-ac", "1", "-ar", "22050", wav], check=True)
y, sr = librosa.load(wav, sr=22050); os.remove(wav)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", tightness=120)
tempo = float(np.atleast_1d(tempo)[0]); beats = [round(float(b), 2) for b in beats]
# extend the grid evenly over gaps (silences have no detected beats) and to the end
step = 60.0 / tempo; grid = []
for b in beats:
    while grid and b - grid[-1] > step * 1.5: grid.append(round(grid[-1] + step, 2))
    grid.append(b)
while grid[0] - step > 0: grid.insert(0, round(grid[0] - step, 2))
while grid[-1] + step < max(dur, 60): grid.append(round(grid[-1] + step, 2))

hop = 512; rms = librosa.feature.rms(y=y, hop_length=hop)[0]; ts = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
def level(t0, t1):
    m = (ts >= t0) & (ts < t1); return float(rms[m].mean()) if m.any() else 0.0
if a.drop is None:
    # drop = the beat with the biggest jump in loudness (next 4 s vs previous 4 s), searched after 6 s
    cands = [b for b in grid if 6 < b < dur - 4]
    drop = max(cands, key=lambda b: level(b, b + 4) - level(b - 4, b)) if cands else grid[len(grid) // 3]
else: drop = a.drop
drop_beat = int(np.argmin([abs(g - drop) for g in grid])); drop = grid[drop_beat]
# silence = start of the quiet stretch right before the drop (rms under 25% of the build's level), max 2.5 s back
ref = level(max(0, drop - 8), drop - 1.5) or 1e-6; silence = drop - .8
i = int(np.searchsorted(ts, drop - .1))
while i > 0 and ts[i] > drop - 2.5 and rms[i] < .25 * ref: i -= 1
if ts[i] < drop - .25: silence = float(ts[i + 1])
silence = round(silence, 2)
if a.brk is None:
    cands = [b for b in grid if drop + 8 < b < dur - 3]
    brk = max(cands, key=lambda b: level(b - 4, b) - level(b, b + 4)) if cands else drop + 20
else: brk = a.brk
prof = {"name": a.name or os.path.splitext(os.path.basename(a.out))[0], "source": os.path.basename(a.sound), "bpm": round(tempo, 1),
        "grid": grid, "silence": silence, "drop_beat": drop_beat, "break_t": round(float(brk), 2), "duration": round(dur, 2)}
json.dump(prof, open(a.out, "w"), indent=1)
print(f"{prof['name']}: {tempo:.1f} BPM, {len(grid)} beats, duration {dur:.1f} s")
print(f"silence {silence:.2f} s | DROP beat {drop_beat} at {drop:.2f} s | breakdown {brk:.2f} s")
print("loudness per 2 s:", " ".join(f"{level(t, t + 2):.2f}" for t in np.arange(0, min(dur, 60), 2)))
print("wrote", a.out)
