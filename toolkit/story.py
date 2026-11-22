"""Two people talking over real night footage (Adriaan 2026-11-22: "music and a good story line, two people talking,
for the masses, it needs to bring out emotion with the video as well").

A short conversation everyone has had (a friend asking "you good?", grandma saying you never visit), shown line by
line in the middle with a small name label. The previous line dims and moves up, so you can follow the exchange.
Footage is cold and grey while the conversation is stuck, the sting line lands on the drop (17.2 s by default) where
the colour comes back, then one gold line held on a warm shot. Slow push in on every clip, long holds.
No voice, no music: a soft rain bed only, Adriaan adds the song in TikTok.

Usage:  python3 toolkit/story.py SPEC.json OUT.mp4 [--preview 0.1,10,17.4,26]
Spec:
  length   seconds (about 27)
  names    {"a": "GRANDMA", "b": "YOU"}    labels; "b" lines are drawn in a soft blue grey, "a" lines in white
  lines    [{"t": 0, "who": "a", "text": "You never visit anymore."}, ...]   each runs until the next one
  end      {"t": 20.6, "text": "Soon runs out. Go this week."}            the gold line, held to the end
  cuts     [{"t": 0, "clip": "pex-1.mp4", "start": 1, "sat": .15, "dark": .3, "zoom": .08}]  seconds, each until the next
  rain     rain bed volume (default .45)
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vyzee as V
import night as N

BLUE = (178, 200, 228)

def base_video(spec, LEN, out):
    """night.build_base wants beats; give it seconds through {"t": s}"""
    cuts = [dict(c, **{"from": {"t": c["t"]}}) for c in spec["cuts"]]
    N.build_base({"cuts": cuts}, LEN, out)

def cl(x): return max(0.0, min(1.0, x))
def ease(x): x = cl(x); return 1 - (1 - x) ** 3

_SZ = {}
def fit(d, txt, top=66, low=50):
    """biggest size with at most 3 lines and no single word left alone on the last line"""
    if txt not in _SZ:
        _SZ[txt] = low
        _SZ[txt] = top - 2                     # an orphan word beats tiny text
        for sz in range(top, top - 10, -2):
            L = V.wrap_lines(d, txt, sz, 760)
            if len(L) <= 3 and (len(L) == 1 or len(L[-1].split()) > 1): _SZ[txt] = sz; break
    return _SZ[txt]

def block_h(d, txt, sz): return len(V.wrap_lines(d, txt, sz, 760)) * sz * 1.12

def draw(t, d, g, spec, LEN):
    lines = spec["lines"]; end = spec["end"]; names = spec.get("names", {"a": "THEM", "b": "YOU"})
    if t >= end["t"]:
        a = ease((t - end["t"]) / .5)
        V.big(g, end["text"], 760, end.get("size", fit(d, end["text"], 74)), a, V.GOLD)
        return
    cur = max([i for i, l in enumerate(lines) if l["t"] <= t] or [0])
    fade_out = cl((end["t"] - t) / .35)
    for i in (cur - 1, cur):
        if i < 0: continue
        l = lines[i]; k = t - l["t"]
        col = V.WHITE if l["who"] == "a" else BLUE
        sz = l.get("size", fit(d, l["text"]))
        if i == cur:
            a = (1.0 if l["t"] <= 0.05 else ease(k / .3)) * fade_out; y = 780 + (1 - ease(k / .35)) * 18
        else:
            nk = t - lines[cur]["t"]; a = (1 - .65 * ease(nk / .35)) * fade_out
            y = 780 - ease(nk / .35) * (block_h(d, l["text"], sz) + 105)
            if lines[cur].get("alone"): a *= cl(1 - nk / .3)
        if a <= .01: continue
        V.text_c(d, names[l["who"]], y - 50, 28, a * .75, col, sp=6)
        V.big(d, l["text"], y, sz, a, col)

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; LEN = float(spec.get("length", 27))
    base = out.replace(".mp4", ".base.mp4"); base_video(spec, LEN, base)
    shade = N.shade_layer(spec.get("shade", .7), 800)
    cuts = spec["cuts"]
    def zoomed(fr, t):
        i = max(j for j, c in enumerate(cuts) if c["t"] <= t + 1e-6)
        t0 = cuts[i]["t"]; t1 = cuts[i + 1]["t"] if i + 1 < len(cuts) else LEN
        z = 1 + cuts[i].get("zoom", .07) * cl((t - t0) / max(.1, t1 - t0))
        w2, h2 = int(V.W * z), int(V.H * z)
        return fr.resize((w2, h2), Image.BILINEAR).crop(((w2 - V.W) // 2, (h2 - V.H) // 2, (w2 - V.W) // 2 + V.W, (h2 - V.H) // 2 + V.H))
    def comp(t, fr):
        im = zoomed(fr, t).convert("RGBA")
        im = Image.composite(Image.new("RGBA", im.size, (0, 0, 0, 255)), im, shade)
        lay = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0)); gl = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0))
        draw(t, ImageDraw.Draw(lay), ImageDraw.Draw(gl), spec, LEN)
        lay.alpha_composite(gl)
        glow = lay.resize((V.W // 2, V.H // 2)).filter(ImageFilter.GaussianBlur(8)).resize((V.W, V.H))
        im.alpha_composite(glow); im.alpha_composite(lay)
        return im.convert("RGB")
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = int(LEN * V.FPS); fsz = V.W * V.H * 3
    prev = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[3] == "--preview" else None
    if prev:
        want = {int(p * V.FPS): p for p in prev}
        for i in range(n):
            buf = rd.stdout.read(fsz)
            if len(buf) < fsz: break
            if i in want: comp(i / V.FPS, Image.frombytes("RGB", (V.W, V.H), buf)).save(out.replace(".mp4", f"_{want[i]:05.2f}.png"))
        rd.kill(); os.remove(base); return
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{V.W}x{V.H}", "-r", str(V.FPS), "-i", "-",
                           "-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.02:d={LEN},lowpass=f=900,volume={spec.get('rain', .45)},afade=t=in:d=1",
                           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", "-t", f"{LEN}", out], stdin=subprocess.PIPE)
    last = None
    for i in range(n):
        buf = rd.stdout.read(fsz)
        if len(buf) == fsz: last = buf
        ff.stdin.write(comp(i / V.FPS, Image.frombytes("RGB", (V.W, V.H), last)).tobytes())
    ff.stdin.close(); ff.wait(); rd.kill(); rd.wait(); os.remove(base); print("done", out)

if __name__ == "__main__":
    main()
