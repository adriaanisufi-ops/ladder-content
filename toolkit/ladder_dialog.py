"""Ladder dialog renderer (default format from 2026-11-12, approved by Adriaan as "Juist").

A faceless silhouette ("you", white text, left) asks, the ladder answers (gold text, right of the ladder),
a small spaced label names the idea (top right). Night, rain, black and white with gold. No voice:
rain ambience only, Adriaan adds the music in TikTok. The rain stops, stars appear and the first rung
lights gold when the last answer starts; that answer stays on screen for the rewatch.

Usage:  python3 toolkit/ladder_dialog.py SPEC.json OUT.mp4 [--preview 0.03,5,12]
Spec:
{
  "title": "Expectation outrunning action",        # the named idea, shown as the label
  "lines": [                                        # alternate "you" and "ladder", end on "ladder"
    {"who": "you",    "text": "Why does every year feel faster than the last?"},
    {"who": "ladder", "text": "Because time isn't speeding up. The gap is."},
    ...
  ]
}
Optional: "start"/"end" per line, "length", "rung", "calm", "audio". Without them the timing is automatic
(reading speed, last answer held about 9 s; about 27 s in total like the approved video).
All text stays between x 130 and 950: tall phones crop about 100 px off each side of a 9:16 video.
"""
import json, math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
G = 1360                      # ground line (stays above TikTok's bottom UI)
K = 1.25                      # scene scale around (540, G)
BLX0, BLX1, BRUNG = 480, 620, 110   # base geometry used in the pose definitions
def sc(pt): return (540 + (pt[0] - 540) * K - 40, G + (pt[1] - G) * K)
LX0, LX1 = sc((BLX0, 0))[0], sc((BLX1, 0))[0]
RUNG = BRUNG * K
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"
GOLD = (245, 197, 66)

spec = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[3] == "--preview" else None
segs = spec["lines"]
if "start" not in segs[0]:                       # automatic reading timing
    t = 0.0
    for i, s in enumerate(segs):
        w = len(s["text"].split())
        last = i == len(segs) - 1
        dur = max(1.8, 0.8 + 0.3 * w) if s["who"] == "you" else max(3.0, 1.2 + 0.3 * w)
        if last: dur = max(9.5, dur + 6.0)
        s["start"], s["end"] = round(t, 2), round(t + dur, 2); t += dur
    spec.setdefault("length", segs[-1]["end"])
    spec.setdefault("rung", segs[-1]["start"] + 0.1)
    spec.setdefault("calm", segs[-1]["start"])
    spec.setdefault("title_end", 99)
T_END = spec["length"]
def S(i): return segs[i]["start"]
def E(i): return segs[i]["end"]

def smooth(a, b, t):          # 0..1 smoothstep between times a and b
    if t <= a: return 0.0
    if t >= b: return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)

rng = random.Random(7)

# ---------- static layers ----------
def radial(w, h, color, power=2.0):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    a = np.clip(1 - d, 0, 1) ** power
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = color
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")

def background():
    y = np.linspace(0, 1, H)[:, None]
    sky = (6 + 14 * y) * np.ones((1, W))
    bg = np.stack([sky, sky * 1.02, sky * 1.08], -1).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(bg, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    # far skyline
    x = -20
    while x < W:
        w = rng.randint(50, 140); h = rng.randint(120, 420)
        d.rectangle([x, G - h, x + w, G], fill=(13, 14, 17, 255))
        for wy in range(G - h + 14, G - 10, 22):
            for wx in range(x + 8, x + w - 8, 16):
                if rng.random() < 0.13:
                    c = rng.randint(40, 95)
                    d.rectangle([wx, wy, wx + 5, wy + 8], fill=(c, c, c - 3, 255))
        x += w + rng.randint(-10, 20)
    # near skyline, darker
    x = -40
    while x < W:
        w = rng.randint(90, 200); h = rng.randint(60, 230)
        if not (LX0 - 160 < x + w / 2 < LX1 + 160):
            d.rectangle([x, G - h, x + w, G], fill=(7, 8, 10, 255))
        x += w + rng.randint(30, 120)
    d.rectangle([0, G, W, H], fill=(9, 10, 12, 255))
    d.line([0, G, W, G], fill=(38, 40, 44, 255), width=2)
    return im

BG = background()
POOL = radial(1000, 1300, (175, 180, 188), 1.6)            # streetlight pool behind the figure
POOL_FLOOR = radial(900, 120, (150, 155, 160), 1.4)
TOPGLOW = radial(900, 700, GOLD, 2.2)
PHONE = radial(260, 260, (200, 220, 255), 1.8)
RUNGGLOW = radial(420, 120, GOLD, 1.5)
RING_FONT = None
GRAIN = [Image.fromarray(np.random.default_rng(i).integers(0, 255, (H // 2, W // 2), dtype=np.uint8), "L")
         .resize((W, H)) for i in range(6)]
STARS = [(rng.randint(0, W), rng.randint(60, 900), rng.random()) for _ in range(90)]
RAIN = [(rng.randint(0, W), rng.randint(0, H), rng.uniform(0.6, 1.0)) for _ in range(140)]
F_CAP = ImageFont.truetype(FONTS + "Inter-Medium.otf", 54)
F_CAPB = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", 54)
F_HOOK = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", 84)

def paste(im, sprite, cx, cy, alpha):
    if alpha <= 0.01: return
    sp = sprite if alpha >= 0.99 else sprite.copy()
    if alpha < 0.99:
        a = sp.getchannel("A").point(lambda v: int(v * alpha))
        sp.putalpha(a)
    im.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

# ---------- the figure ----------
def P(**kw): return kw
SIDE_STAND = P(hip=(360, G-170), neck=(360, G-277), head=(364, G-312), k1=(366, G-86), f1=(374, G), k2=(354, G-86), f2=(346, G),
               e1=(370, G-215), h1=(374, G-158), e2=(352, G-215), h2=(348, G-158))
SIDE_LOOKUP = dict(SIDE_STAND, neck=(354, G-276), head=(350, G-314))
SIDE_PHONE = dict(SIDE_STAND, neck=(366, G-274), head=(378, G-304), e1=(394, G-200), h1=(398, G-262), e2=(356, G-214), h2=(372, G-205))
SIDE_SCROLL = dict(SIDE_PHONE, h2=(386, G-240), e2=(366, G-205))
SIT = P(hip=(345, G-32), neck=(352, G-138), head=(360, G-173), k1=(410, G-92), f1=(452, G), k2=(404, G-84), f2=(446, G),
        e1=(372, G-80), h1=(410, G-96), e2=(366, G-86), h2=(404, G-100))
SIT_REACH = dict(SIT, e1=(392, G-60), h1=(436, G-40))
BACK_STAND = P(hip=(550, G-170), neck=(550, G-277), head=(550, G-312), k1=(532, G-86), f1=(528, G), k2=(568, G-86), f2=(572, G),
               e1=(520, G-215), h1=(514, G-158), e2=(580, G-215), h2=(586, G-158))
CLIMB = P(hip=(550, G-222), neck=(550, G-330), head=(550, G-365), k1=(528, G-186), f1=(526, G-BRUNG+4), k2=(566, G-110), f2=(570, G),
          e1=(486, G-330), h1=(BLX0+6, G-3.3*BRUNG), e2=(614, G-330), h2=(BLX1-6, G-3.3*BRUNG))

def lerp(a, b, s): return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)
def mix(p, q, s): return {k: lerp(p[k], q[k], s) for k in p}

def lerp(a, b, s): return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)
def mix(p, q, s): return {k: lerp(p[k], q[k], s) for k in p}

def pulse(t, c, up=.15, hold=.45, down=.25):
    return smooth(c, c + up, t) * (1 - smooth(c + up + hold, c + up + hold + down, t))

ITEMS = [S(2) + .05, S(2) + 1.1, S(2) + 2.0]           # red light, queue, before sleep

def phone_w(t):
    w = max(pulse(t, c) for c in ITEMS)
    return max(w, smooth(S(3) + .1, S(3) + .7, t) * (1 - smooth(S(8) + .5, S(8) + 1.2, t)))

def draw_figure(d, p, col=(2, 2, 3, 255)):
    ln = lambda a, b, w: d.line([a, b], fill=col, width=w, joint="curve")
    for a, b in (("hip", "k2"), ("k2", "f2"), ("neck", "e2"), ("e2", "h2")):
        ln(p[a], p[b], int(24 * K))
    ln(p["hip"], p["neck"], int(40 * K))
    for a, b in (("hip", "k1"), ("k1", "f1"), ("neck", "e1"), ("e1", "h1")):
        ln(p[a], p[b], int(24 * K))
    for k, r in (("hip", 21), ("neck", 21), ("k1", 12), ("k2", 12), ("e1", 12), ("e2", 12), ("h1", 11), ("h2", 11), ("f1", 13), ("f2", 13)):
        x, y = p[k]; r *= K; d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    x, y = p["head"]; d.ellipse([x - 30 * K, y - 33 * K, x + 30 * K, y + 33 * K], fill=col)


F_Q = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", 44)
_yy = np.arange(H)[:, None]
_m = 1 - 0.0 * np.clip(np.minimum((_yy - 240) / 120, (900 - _yy) / 120), 0, 1)   # ladder fades behind the text band (y 240 to 900)
LMASK = Image.fromarray((np.repeat(_m, W, 1) * 255).astype(np.uint8), "L")
F_A = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", 44)
F_T = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", 24)

def wrap(d, text, font, width):
    lines, cur = [], []
    for wd in text.split():
        if cur and d.textlength(" ".join(cur + [wd]), font=font) > width: lines.append(" ".join(cur)); cur = []
        cur.append(wd)
    return lines + [" ".join(cur)]

def active(t, sp):
    return [i for i, s in enumerate(segs) if s["who"] == sp and s["start"] <= t and (t < s["end"])]

def pose(t):
    asking = sum(smooth(s["start"], s["start"] + .3, t) * (1 - smooth(s["end"] - .3, s["end"], t)) for s in segs if s["who"] == "you")
    p = mix(SIDE_STAND, SIDE_LOOKUP, min(1, asking))
    br = math.sin(t * 2.1) * 2
    return {k: sc((v[0], v[1] + (br if k in ("neck", "head", "e1", "e2", "h1", "h2") else 0))) for k, v in p.items()}

def frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im, "RGBA")
    calm = smooth(spec["calm"], spec["calm"] + 1.5, t)
    for x, y, b in STARS:
        a = int(calm * (90 + 120 * b) * (0.7 + 0.3 * math.sin(t * 3 + x)))
        if a > 5: d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(220, 222, 226, a))
    rain = 1 - calm
    for x, y, s in RAIN:
        yy = (y + t * 1500 * s) % H; xx = (x - t * 160 * s) % W
        if rain > .02: d.line([xx, yy, xx - 6, yy + 44], fill=(150, 155, 165, int(55 * rain * s)), width=2)
    speak = sum(smooth(s["start"], s["start"] + .3, t) * (1 - smooth(s["end"] - .3, s["end"], t)) for s in segs if s["who"] == "ladder")
    paste(im, TOPGLOW, (LX0 + LX1) / 2, 40, min(1, 0.4 + 0.45 * speak + 0.4 * calm))
    paste(im, POOL, 400, G - 470, 0.8); paste(im, POOL_FLOOR, 440, G + 20, 0.8)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    rc = (205, 208, 214, 255)
    for x in (LX0, LX1): dl.line([x, G + 2, x, -20], fill=rc, width=9)
    for k in range(1, 10):
        y = G - RUNG * k; dl.line([LX0, y, LX1, y], fill=rc, width=8)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), LMASK))
    im.alpha_composite(lay); d = ImageDraw.Draw(im, "RGBA")
    # when the ladder speaks, light travels up the rungs
    if speak > 0.02:
        ph = (t * 1.6) % 1
        k = 1 + int(ph * 8)
        y = G - RUNG * k
        paste(im, RUNGGLOW, (LX0 + LX1) / 2, y, 0.35 * speak)
    g = smooth(spec["rung"], spec["rung"] + .5, t)
    if g > 0:
        y = G - RUNG
        paste(im, RUNGGLOW, (LX0 + LX1) / 2, y, g)
        d.line([LX0, y, LX1, y], fill=GOLD + (int(255 * g),), width=10)
    draw_figure(d, pose(t))
    gr = GRAIN[int(t * FPS) % len(GRAIN)]
    im = Image.blend(im.convert("RGB"), Image.merge("RGB", (gr, gr, gr)), 0.035).convert("RGBA")
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt, "RGBA")
    # side layout like the approved version, but everything inside x 130..950 (phones crop the sides)
    XA = 625
    sw = lambda txt: sum(d.textlength(ch, font=F_T) + 3 for ch in txt) - 3
    tl, cur = [], ""
    for wd in spec["title"].upper().split():
        if cur and sw(cur + " " + wd) > 285: tl.append(cur); cur = wd
        else: cur = (cur + " " + wd).strip()
    tl.append(cur)
    for i, ln in enumerate(tl):
        x = XA
        for ch in ln:
            d.text((x, 300 + i * 40), ch, font=F_T, fill=(200, 204, 210, 235)); x += d.textlength(ch, font=F_T) + 3
    ry = 300 + len(tl) * 40 + 12
    d.line([XA, ry, XA + 70, ry], fill=GOLD + (230,), width=3)
    for s in segs:
        if not (s["start"] <= t < s["end"]): continue
        a = (1 if s["start"] == 0 else smooth(s["start"], s["start"] + .2, t)) * ((1 - smooth(s["end"] - .2, s["end"], t)) if s["end"] < T_END - .01 else 1)
        if s["who"] == "you":
            lines = wrap(d, s["text"], F_Q, 260)
            y = 860 - len(lines) * 56
            for i, ln in enumerate(lines): d.text((135, y + i * 56), ln, font=F_Q, fill=(240, 242, 245, int(255 * a)))
        else:
            lines = wrap(d, s["text"], F_A, 290)
            for i, ln in enumerate(lines): d.text((XA, ry + 40 + i * 56), ln, font=F_A, fill=GOLD + (int(255 * a),))
    reg = txt
    sh = reg.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, int(v * 2.4)))
    shadow = Image.new("RGBA", reg.size, (0, 0, 0, 255)); shadow.putalpha(sh)
    im.alpha_composite(shadow); im.alpha_composite(reg)
    return im.convert("RGB")

def check():
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for s in segs:
        n = len(wrap(d, s["text"], F_Q if s["who"] == "you" else F_A, 260 if s["who"] == "you" else 290))
        lim = 6 if s["who"] == "you" else 8
        if n > lim: print(f"WARNING: too long ({n} lines, max {lim}): {s['text']}")
        f, wmax = (F_Q, 260) if s["who"] == "you" else (F_A, 290)
        for wd in s["text"].split():
            if d.textlength(wd, font=f) > wmax: print(f"WARNING: word too wide for the column, rephrase: {wd}")
    print("timing:", ", ".join(f"{s['who']} {s['start']}-{s['end']}" for s in segs), "| length", T_END, "| last answer at", segs[-1]["start"])
check()

if PREVIEW:
    for t in PREVIEW: frame(t).save(OUT.replace(".mp4", f"_{t:05.1f}.png"))
    sys.exit()
N = int(T_END * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    *(["-i", spec["audio"], "-filter_complex", f"anoisesrc=c=brown:a=0.02:d={T_END},lowpass=f=900,volume={spec.get("rain_vol", 0.5)}[rn];[1:a]apad,atrim=0:{T_END},volume=1.15[v];[v][rn]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
      if spec.get("audio") else ["-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.02:d={T_END},lowpass=f=900,volume=0.5"]),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", OUT], stdin=subprocess.PIPE)
for i in range(N): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", OUT)
