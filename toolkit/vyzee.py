"""Ladder explainer videos on VYZEE (default format from 2026-11-13, approved by Adriaan: "Price Tags").

Minimal glowing white line animation on black, one gold accent at the end, an AI voice (Kokoro, am_michael),
everything timed to the beat grid of the VYZEE sound Adriaan uses ("Use this sound" on his reference video,
starting at 0:00). The video has NO music: he adds VYZEE in TikTok. Output = voice only.

Song map (measured from his reference): ~107.7 BPM, calm intro, silence at 16.4 s, DROP at 17.18 s (beat 31),
loud part until the breakdown at 36.8 s, quiet part after that (second drop at 47.2 s, only for long videos).

Usage:  python3 toolkit/vyzee.py SPEC.json OUT.mp4 [--preview 0.03,17.3,40]
Example spec: toolkit/specs/example-vyzee-price-tags.json (the approved video).

Spec:
  length      seconds (about 40 to 45)
  voice       Kokoro voice (default am_michael), speed (default 1.05)
  lines       [{"beat": 4, "text": "..."}]  or {"at": 0.12, ...}: spoken lines, start on a beat of GRID
  text        [{"from": 0, "to": 4, "big": "..."} | {"pill": "..."} | {"small": "..."}, optional "y", "size", "gold"]
              on-screen words; from/to are beat numbers (floats ok) or {"t": seconds}; "to" may be omitted
  shots       graphics, each {"type": ..., "from": beat, "to": beat, ...}; see SHOTS below
Beat numbers refer to GRID (index into the measured beats). Beat 31 is the drop. Use "t" for exact seconds.
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TK = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(TK, "fonts") + "/"
W, H, FPS = 1080, 1920, 30
GOLD = (245, 197, 66); WHITE = (240, 242, 245); INK = (12, 12, 14)
GROUND = 1300

# measured beat grid of the VYZEE cut in Adriaan's reference video (seconds)
GRID = [0.09, 0.65, 1.21, 1.74, 2.3, 2.86, 3.39, 3.95, 4.5, 5.06, 5.62, 6.15, 6.71, 7.27, 7.8, 8.36, 8.92, 9.47, 10.03, 10.57,
        11.12, 11.68, 12.24, 12.77, 13.33, 13.86, 14.42, 14.98, 15.53, 16.09, 16.65, 17.18, 17.74, 18.3, 18.83, 19.39, 19.95,
        20.5, 21.06, 21.59, 22.13, 22.69, 23.24, 23.8, 24.36, 24.92, 25.47, 26.01, 26.56, 27.1, 27.65, 28.21, 28.77, 29.33,
        29.88, 30.42, 30.98, 31.53, 32.09, 32.62, 33.18, 33.74, 34.27, 34.81, 35.36, 35.92, 36.48, 37.01, 37.57, 38.13, 38.68,
        39.22, 39.78, 40.31, 40.87, 41.42, 41.98, 42.54, 43.09, 43.64, 44.19, 44.75, 45.3, 45.86, 46.41, 46.97, 47.52, 48.08,
        48.63, 49.18, 49.74, 50.29, 50.85, 51.4, 51.96, 52.51, 53.07]
SILENCE, DROP_BEAT, BREAK_T = 16.4, 31, 36.8

def T(v):
    """beat number (float ok) or {"t": seconds} -> seconds"""
    if isinstance(v, dict): return float(v["t"])
    if v <= 0: return 0.0                     # beat 0 = the first frame (the hook must be there from frame 1)
    return float(np.interp(v, range(len(GRID)), GRID))

def cl(x): return max(0.0, min(1.0, x))
def ease(x): x = cl(x); return 1 - (1 - x) ** 3
def win(t, a, b, fi=.15, fo=.15): return cl((t - a) / fi) * cl((b - t) / fo)

_F = {}
def font(sz):
    sz = int(sz)
    if sz not in _F: _F[sz] = ImageFont.truetype(FONTS + "Inter-SemiBold.otf", sz)
    return _F[sz]
def spaced_w(d, txt, f, sp): return sum(d.textlength(c, font=f) + sp for c in txt) - sp
def text_c(d, txt, y, sz, a=1.0, col=WHITE, sp=None, cx=540):
    if a <= 0.01: return
    f = font(sz); sp = sz * 0.08 if sp is None else sp
    x = cx - spaced_w(d, txt, f, sp) / 2
    for c in txt:
        d.text((x, y), c, font=f, fill=col + (int(255 * a),)); x += d.textlength(c, font=f) + sp
def wrap_lines(d, txt, sz, maxw, sp=None):
    f = font(sz); sp = sz * 0.08 if sp is None else sp; out, cur = [], ""
    for wd in txt.split():
        if cur and spaced_w(d, cur + " " + wd, f, sp) > maxw: out.append(cur); cur = wd
        else: cur = (cur + " " + wd).strip()
    return out + [cur]
def big(d, txt, y, sz, a, col=WHITE, maxw=760):
    for i, ln in enumerate(wrap_lines(d, txt, sz, maxw)): text_c(d, ln, y + i * sz * 1.12, sz, a, col)
def pill(d, txt, cy, a=1.0, cx=540, sz=32):
    if a <= 0.01: return
    f = font(sz); sp = 3
    while spaced_w(d, txt, f, sp) > 740 and sz > 18: sz -= 2; f = font(sz)
    w = spaced_w(d, txt, f, sp)
    d.rounded_rectangle([cx - w / 2 - 26, cy - sz * .75, cx + w / 2 + 26, cy + sz * .75], radius=int(sz * .75), fill=(245, 246, 248, int(255 * a)))
    x = cx - w / 2
    for c in txt:
        d.text((x, cy - sz * .62), c, font=f, fill=INK + (int(255 * a),)); x += d.textlength(c, font=f) + sp
def person(d, x, yf, a=1.0, s=1.0, col=WHITE):
    if a <= 0.01: return
    c = col + (int(255 * a),)
    d.ellipse([x - 17 * s, yf - 92 * s, x + 17 * s, yf - 58 * s], fill=c)
    d.rounded_rectangle([x - 22 * s, yf - 52 * s, x + 22 * s, yf], radius=int(16 * s), fill=c)
def check(d, x, y, s, a, p=1.0, col=WHITE):
    p = cl(p)
    if p <= 0 or a <= 0.01: return
    pts = [(x - s * .5, y), (x - s * .15, y + s * .35), (x + s * .55, y - s * .4)]
    w = int(s * .12) + 2; c = col + (int(255 * a),)
    if p < .4:
        q = p / .4; d.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * q, pts[0][1] + (pts[1][1] - pts[0][1]) * q)], fill=c, width=w)
    else:
        q = (p - .4) / .6
        d.line([pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * q, pts[1][1] + (pts[2][1] - pts[1][1]) * q)], fill=c, width=w, joint="curve")
def cross(d, x, y, s, a, p=1.0):
    c = WHITE + (int(255 * a),); p = cl(p); q1, q2 = cl(p * 2), cl(p * 2 - 1)
    if q1 > 0: d.line([x - s, y - s, x - s + 2 * s * q1, y - s + 2 * s * q1], fill=c, width=6)
    if q2 > 0: d.line([x + s, y - s, x + s - 2 * s * q2, y - s + 2 * s * q2], fill=c, width=6)
def ground(d, a): d.line([140, GROUND, 940, GROUND], fill=WHITE + (int(160 * a),), width=3)

def icon(d, name, cx, cy, a):
    c = WHITE + (int(235 * a),)
    if name == "dumbbell":
        d.line([cx - 55, cy, cx + 55, cy], fill=c, width=6)
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * 55 - 10, cy - 30, cx + sx * 55 + 10, cy + 30], radius=5, outline=c, width=5)
            d.rounded_rectangle([cx + sx * 75 - 7, cy - 20, cx + sx * 75 + 7, cy + 20], radius=4, outline=c, width=5)
    elif name == "bars":
        for i, h in enumerate((30, 55, 85)):
            x = cx - 50 + i * 38; d.rounded_rectangle([x, cy + 40 - h, x + 24, cy + 40], radius=4, outline=c, width=5)
        d.line([cx - 60, cy + 44, cx + 66, cy + 44], fill=c, width=4)
    elif name == "sun":
        d.arc([cx - 45, cy - 30, cx + 45, cy + 60], 180, 360, fill=c, width=5)
        d.line([cx - 75, cy + 15, cx + 75, cy + 15], fill=c, width=4)
        for ang in (200, 235, 270, 305, 340):
            r0, r1, a_ = 58, 78, math.radians(ang)
            d.line([cx + math.cos(a_) * r0, cy + 15 + math.sin(a_) * r0, cx + math.cos(a_) * r1, cy + 15 + math.sin(a_) * r1], fill=c, width=4)
    elif name == "heart":
        d.polygon([(cx, cy + 45), (cx - 55, cy - 5), (cx - 40, cy - 40), (cx, cy - 20), (cx + 40, cy - 40), (cx + 55, cy - 5)], outline=c, width=5)
    elif name == "book":
        d.line([cx, cy - 35, cx, cy + 40], fill=c, width=4)
        d.polygon([(cx, cy - 35), (cx - 65, cy - 45), (cx - 65, cy + 30), (cx, cy + 40)], outline=c, width=5)
        d.polygon([(cx, cy - 35), (cx + 65, cy - 45), (cx + 65, cy + 30), (cx, cy + 40)], outline=c, width=5)
    elif name == "phone":
        d.rounded_rectangle([cx - 32, cy - 55, cx + 32, cy + 55], radius=12, outline=c, width=5)
        d.line([cx - 10, cy + 42, cx + 10, cy + 42], fill=c, width=4)
    elif name == "house":
        d.polygon([(cx - 55, cy - 5), (cx, cy - 50), (cx + 55, cy - 5)], outline=c, width=5)
        d.rectangle([cx - 42, cy - 5, cx + 42, cy + 45], outline=c, width=5)
    elif name == "star":
        pts = []
        for i in range(10):
            r = 50 if i % 2 == 0 else 22; ang = math.radians(-90 + i * 36)
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        d.polygon(pts, outline=c, width=5)
    else:   # circle fallback
        d.ellipse([cx - 45, cy - 45, cx + 45, cy + 45], outline=c, width=5)

def tag(d, cx, cy, w, h, a, flip=1.0, txt=None, sz=26, col=WHITE, fill=False):
    if a <= 0.01: return
    c = col + (int(235 * a),); hw = max(3, w / 2 * abs(flip))
    pts = [(cx - hw, cy - h / 2 + h * .22), (cx, cy - h / 2), (cx + hw, cy - h / 2 + h * .22), (cx + hw, cy + h / 2), (cx - hw, cy + h / 2)]
    if fill: d.polygon(pts, fill=col + (int(255 * a),))
    else: d.polygon(pts, outline=c, width=4)
    hole = 9 * abs(flip) + 2
    d.ellipse([cx - hole, cy - h / 2 + h * .14 - 9, cx + hole, cy - h / 2 + h * .14 + 9], outline=(INK + (int(255 * a),)) if fill else c, width=3)
    if txt and flip > 0.35:
        tc = INK if fill else col
        while sz > 16 and any(spaced_w(d, wd, font(sz), sz * .08) > w - 40 for wd in txt.split()): sz -= 2
        lines = wrap_lines(d, txt, sz, w - 40); y = cy + h * .08 - len(lines) * sz * .6
        for i, ln in enumerate(lines): text_c(d, ln, y + i * sz * 1.15, sz, a * cl((flip - .35) / .3), col=tc, cx=cx)
    elif flip < -0.35:
        text_c(d, "?", cy - sz * .2, int(sz * 1.6), a * .55, cx=cx)

rng = np.random.default_rng(5)
PARTS = [(rng.uniform(0, 2 * math.pi), rng.uniform(250, 600)) for _ in range(22)]

# ---------------------------------------------------------------- SHOTS
# Every shot gets (t, d, g, a, s): t = time, d = white layer, g = gold layer, a = shot alpha, s = shot dict.

def shot_window(t, d, g, a, s):
    """shop window: sign, 3 items {label, icon, price}, tags turned away until flip (beat), figure walks up.
    keys: sign, items, flip (beat, default: the silence 16.4 s), light (list of beats when each item lights up),
    walk [from, to] beats, reach [from, to] beats"""
    X0, X1, Y0, Y1 = 160, 920, 560, 1080
    c = WHITE + (int(225 * a),)
    d.rounded_rectangle([X0, Y0, X1, Y1], radius=14, outline=c, width=4)
    for i in range(8):
        x = X0 + i * (X1 - X0) / 8; d.arc([x, Y0 - 46, x + (X1 - X0) / 8, Y0 + 4], 0, 180, fill=c, width=4)
    d.line([X0 - 10, Y0 - 22, X1 + 10, Y0 - 22], fill=c, width=4)
    text_c(d, s.get("sign", "DREAMS"), Y0 - 108, 40, a, sp=14)
    items = s["items"]; n = len(items); cw = (X1 - X0) / n
    flip_t = T(s["flip"]) if "flip" in s else SILENCE
    light = s.get("light", [10 + 2 * k for k in range(n)])
    for k, it in enumerate(items):
        cx = X0 + cw * (k + .5)
        lit = cl((t - T(light[k])) / .15)
        icon(d, it.get("icon", "circle"), cx, Y0 + 120, a * (.35 + .65 * lit))
        text_c(d, it["label"], Y0 + 200, 26, a * (.35 + .65 * lit), sp=3, cx=cx)
        d.line([cx, Y0 + 250, cx, Y0 + 290], fill=c, width=2)
        p = cl((t - flip_t - k * .12) / .7)
        fl = -math.cos(p * math.pi * 3) if p < 1 else 1.0
        if t < flip_t: fl = -1.0
        tag(d, cx + math.sin(t * 2.2 + k) * 4, Y0 + 370, 170, 150, a, fl, it.get("price") if t > flip_t + .5 else None, 24)
    if s.get("walker", True):
        wf, wt = s.get("walk", [8, 16]); walk = ease((t - T(wf)) / max(.1, T(wt) - T(wf)))
        px = 250 + walk * 290; person(d, px, GROUND, a); ground(d, a)
        if "reach" in s:
            rf, rt = s["reach"]; r = ease((t - T(rf)) / .4) * (1 - ease((t - T(rt)) / .5))
            if r > 0: d.line([px + 18, GROUND - 50, px + 18 + 40 * r, GROUND - 50 - 160 * r], fill=WHITE + (int(235 * a),), width=10)

def shot_slam(t, d, g, a, s):
    """big items slam in one per beat (a tag, or a word), plus an optional receipt with checks and a total.
    keys: items [{text, beat, short}], header, style "tag"|"word", receipt true/false, total {label, value, beat}"""
    items = s["items"]; cur = None
    for i, it in enumerate(items):
        if t >= T(it["beat"]): cur = i
    hide_at = T(s["total"]["beat"]) if s.get("total") else 1e9
    if cur is not None and t < hide_at:
        it = items[cur]; dt = t - T(it["beat"]); k = 1 + .35 * math.exp(-dt * 14)
        if s.get("style", "tag") == "tag":
            tag(d, 540, 640, 520 * k, 400 * k, a, 1.0, it["text"], int((54 if len(it["text"]) < 14 else 42) * k))
        else:
            big(d, it["text"], 560, int(110 * k) if len(it["text"]) < 10 else int(80 * k), a)
    if s.get("header"): text_c(d, s["header"], 360, 30, a * .8, sp=8)
    if s.get("receipt", True):
        rx0, rx1, ry = 230, 850, 920
        d.line([rx0, ry, rx1, ry], fill=WHITE + (int(150 * a),), width=2)
        for i, it in enumerate(items):
            if t < T(it["beat"]): continue
            y = ry + 26 + i * 52; al = a * ease((t - T(it["beat"])) / .12); short = it.get("short", it["text"])
            f = font(28); d.text((rx0, y), short, font=f, fill=WHITE + (int(220 * al),))
            for x in range(int(rx0 + d.textlength(short, font=f) + 14), rx1 - 60, 16): d.ellipse([x, y + 20, x + 4, y + 24], fill=WHITE + (int(120 * al),))
            check(d, rx1 - 22, y + 16, 34, al)
        if s.get("total") and t >= T(s["total"]["beat"]):
            tt = s["total"]; al = a * ease((t - T(tt["beat"])) / .15); y = ry + 26 + len(items) * 52 + 16
            d.line([rx0, y - 8, rx1, y - 8], fill=WHITE + (int(200 * al),), width=3)
            f = font(36); d.text((rx0, y + 6), tt.get("label", "TOTAL"), font=f, fill=WHITE + (int(255 * al),))
            tw = d.textlength(tt["value"], font=f); d.text((rx1 - tw, y + 6), tt["value"], font=f, fill=WHITE + (int(255 * al),))

def shot_versus(t, d, g, a, s):
    """A then B: A dims (and is struck through at 'strike'), B lands. keys: a, a_sub, b, b_sub, a_beat, sub_beat, strike, b_beat, b_gold"""
    da = 1 - .55 * cl((t - T(s["b_beat"])) / .2)
    text_c(d, s["a"], 520, 110 if len(s["a"]) < 10 else 84, a * da * ease((t - T(s.get("a_beat", s["from"]))) / .12))
    if s.get("a_sub"): text_c(d, s["a_sub"], 650, 34, a * da * ease((t - T(s.get("sub_beat", s["from"]))) / .2), sp=5)
    if "strike" in s and t > T(s["strike"]):
        q = ease((t - T(s["strike"])) / .3); d.line([180, 585, 180 + 720 * q, 585], fill=WHITE + (int(255 * a),), width=8)
    lay = g if s.get("b_gold") else d; col = GOLD if s.get("b_gold") else WHITE
    text_c(lay, s["b"], 820, 130 if len(s["b"]) < 10 else 96, a * ease((t - T(s["b_beat"])) / .12), col=col)
    if s.get("b_sub"): text_c(lay, s["b_sub"], 970, 40, a * ease((t - T(s["b_beat"]) - .5) / .2), col=col, sp=6)

def shot_steps(t, d, g, a, s):
    """staircase: one step plus a check per word on the beat. keys: words [{text, beat}], base (steps already there)"""
    sx, sy, sw, sh = 190, GROUND, 88, 70; base = s.get("base", 3)
    shown = base + sum(1 for w in s["words"] if t >= T(w["beat"]))
    pts = [(sx, sy)]
    for i in range(shown): x, y = pts[-1]; pts += [(x + sw, y), (x + sw, y - sh)]
    d.line(pts, fill=WHITE + (int(235 * a),), width=4)
    for i, w in enumerate(s["words"]):
        if t >= T(w["beat"]): check(d, sx + (base + i + 1) * sw - sw / 2, sy - (base + i) * sh - 34, 34, a, (t - T(w["beat"])) / .15)
    person(d, sx + max(1, shown) * sw - sw * 1.5, sy - max(0, shown - 2) * sh, a, .8)
    cur = [w for w in s["words"] if t >= T(w["beat"])]
    if cur: text_c(d, cur[-1]["text"], 560, 150, a * ease((t - T(cur[-1]["beat"])) / .08))

def shot_bubble(t, d, g, a, s):
    """a bubble lifts the figure, pops on 'pop' (beat). keys: pop, rise [from, to]"""
    ground(d, a); rf, rt = s.get("rise", [s["from"], s["pop"]])
    rise = ease((t - T(rf)) / max(.1, T(rt) - T(rf))); cy = GROUND - 150 - rise * 520
    if t < T(s["pop"]):
        r = 150 + math.sin(t * 9) * 6 * rise
        d.ellipse([540 - r, cy - r, 540 + r, cy + r], outline=WHITE + (int(235 * a),), width=4)
        d.arc([540 - r + 30, cy - r + 30, 540 + r - 30, cy + r - 30], 200, 250, fill=WHITE + (int(160 * a),), width=4)
        person(d, 540, cy + 70, a)
    else:
        k = t - T(s["pop"])
        for ang, spd in PARTS:
            rr = 150 + spd * ease(k / .7); al = a * cl(1 - k / .9); x, y = 540 + math.cos(ang) * rr, cy + math.sin(ang) * rr
            if al > .02: d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=WHITE + (int(255 * al),))
        person(d, 540, min(GROUND, cy + 70 + 1600 * k * k), a)

def shot_week(t, d, g, a, s):
    """7 day boxes, a check per half beat from 'start'. keys: start, labels"""
    days = s.get("labels", ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]); bw, gap = 96, 14; x0 = 540 - (7 * bw + 6 * gap) / 2
    for i, dd in enumerate(days):
        x = x0 + i * (bw + gap); y = 820
        d.rounded_rectangle([x, y, x + bw, y + bw], radius=12, outline=WHITE + (int(200 * a),), width=3)
        text_c(d, dd, y + bw + 14, 22, a * .7, cx=x + bw / 2, sp=2)
        ts = T(s.get("start", s["from"]) + i * .5)
        if t > ts: check(d, x + bw / 2, y + bw / 2, 52, a, (t - ts) / .18)

def shot_streak(t, d, g, a, s):
    """30 dots lighting up with a DAY counter. keys: start, end (beats)"""
    lit = int(cl((t - T(s.get("start", s["from"]))) / max(.1, T(s.get("end", s["to"])) - T(s.get("start", s["from"])))) * 30)
    for i in range(30):
        r, c = divmod(i, 6); x, y = 300 + c * 96, 720 + r * 96
        if i < lit: d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=WHITE + (int(240 * a),))
        else: d.ellipse([x - 20, y - 20, x + 20, y + 20], outline=WHITE + (int(110 * a),), width=3)
    text_c(d, f"DAY {max(1, lit)}", 480, 120, a)

def shot_bigbar(t, d, g, a, s):
    """one huge bar ("ONE BIG DAY") next to the figure, crossed out at 'cross'. keys: label, cross"""
    ground(d, a); person(d, 300, GROUND, a)
    hgt = 620 * ease((t - T(s["from"]) - .3) / .5)
    d.rounded_rectangle([470, GROUND - hgt, 610, GROUND], radius=10, fill=WHITE + (int(235 * a),))
    text_c(d, s.get("label", "ONE BIG DAY"), GROUND - hgt - 50, 26, a, sp=4)
    if "cross" in s and t > T(s["cross"]): cross(d, 540, GROUND - 330, 150, a, (t - T(s["cross"])) / .35)

def shot_check(t, d, g, a, s):
    """one circle with a check drawn at 'at'"""
    d.ellipse([440, 600, 640, 800], outline=WHITE + (int(220 * a),), width=4)
    check(d, 540, 700, 110, a, (t - T(s.get("at", s["from"]))) / .25)

def shot_tag_finale(t, d, g, a, s):
    """one tag swinging (before), then stamped gold on 'at' with the gold text. keys: before, after, at"""
    ground(d, a); paid = ease((t - T(s["at"])) / .25); sw = math.sin(t * 2) * 5 * (1 - paid)
    person(d, 430, GROUND, a)
    d.line([600, 680, 600 + sw, 760], fill=WHITE + (int(200 * a),), width=2)
    if paid <= 0: tag(d, 600 + sw, 900, 340, 280, a, 1.0, s.get("before", "YOUR DREAM"), 40)
    else:
        k = 1 + .25 * math.exp(-(t - T(s["at"])) * 10)
        tag(g, 600, 900, 340 * k, 280 * k, a * paid, 1.0, s.get("after", "PAID."), int(64 * k), col=GOLD, fill=True)
        g.line([600, 680, 600, 760], fill=GOLD + (int(200 * a * paid),), width=2)
        person(g, 430, GROUND, a * paid, col=GOLD)

def shot_ladder_finale(t, d, g, a, s):
    """a ladder builds, the figure climbs, everything turns gold on 'gold'. keys: gold, label"""
    lx0, lx1, top = 450, 630, 380
    for x in (lx0, lx1): d.line([x, GROUND, x, top], fill=WHITE + (int(230 * a),), width=6)
    for i in range(8):
        y = GROUND - 100 - i * 105; sh = cl((t - T(s["from"]) - i * .28) / .12)
        if sh > 0: d.line([lx0, y, lx0 + (lx1 - lx0) * sh, y], fill=WHITE + (int(230 * a),), width=6)
    gold = ease((t - T(s["gold"])) / .35); climb = ease((t - T(s["from"]) - .6) / 3.5)
    person(d, 540, GROUND - climb * 525, a, .9)
    if gold > 0:
        for i in range(8):
            y = GROUND - 100 - i * 105; g.line([lx0, y, lx1, y], fill=GOLD + (int(255 * gold * cl(1 - i * .06)),), width=7)
        for x in (lx0, lx1): g.line([x, GROUND, x, top], fill=GOLD + (int(200 * gold),), width=6)
        text_c(g, s.get("label", "THE LADDER"), 250, 64, gold, col=GOLD, sp=10)

def shot_figure(t, d, g, a, s):
    """just the ground and the figure (x), optional gold at 'gold'"""
    ground(d, a); gold = ease((t - T(s["gold"])) / .3) if "gold" in s else 0
    person(d, s.get("x", 540), GROUND, a * (1 - gold)); person(g, s.get("x", 540), GROUND, a * gold, col=GOLD)

SHOTS = {k[5:]: v for k, v in globals().items() if k.startswith("shot_")}

# ---------------------------------------------------------------- render
yy, xx = np.mgrid[0:H, 0:W]
_dist = np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 900) / 1100) ** 2)
BG = Image.fromarray(np.clip(22 * (1 - _dist), 0, 22).astype(np.uint8) + 4).convert("RGB")
GRAIN = [Image.fromarray(np.random.default_rng(i).integers(0, 255, (H // 2, W // 2), dtype=np.uint8), "L").resize((W, H)) for i in range(6)]

def draw_text(t, d, g, spec, LEN):
    items = spec.get("text", [])
    for i, it in enumerate(items):
        a0 = T(it["from"]); a1 = T(it["to"]) if "to" in it else LEN + 1
        if not (a0 - .01 <= t < a1): continue
        a = (1.0 if a0 <= 0.05 else ease((t - a0) / .15)) * cl((a1 - t) / .12)
        lay, col = (g, GOLD) if it.get("gold") else (d, WHITE)
        if "big" in it: big(lay, it["big"], it.get("y", 250), it.get("size", 64), a, col)
        elif "pill" in it: pill(lay, it["pill"], it.get("y", 300), a, sz=it.get("size", 32))
        elif "small" in it: text_c(lay, it["small"], it.get("y", 360), it.get("size", 30), a * .85, col, sp=6)

def frame(t, spec, LEN):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
    for s in spec["shots"]:
        t0, t1 = T(s["from"]), T(s["to"]) if "to" in s else LEN + 1
        a = win(t, t0, t1, fi=s.get("fade_in", .03 if t0 > 0 else .01), fo=s.get("fade_out", .12))
        if a > 0: SHOTS[s["type"]](t, d, g, a, s)
    draw_text(t, d, g, spec, LEN)
    lay.alpha_composite(gl)
    glow = lay.resize((W // 2, H // 2)).filter(ImageFilter.GaussianBlur(9)).resize((W, H))
    im = BG.convert("RGBA"); im.alpha_composite(glow); im.alpha_composite(glow); im.alpha_composite(lay)
    gr = GRAIN[int(t * FPS) % 6]
    return Image.blend(im.convert("RGB"), Image.merge("RGB", (gr, gr, gr)), 0.03)

def ensure_kokoro():
    cache = os.path.expanduser("~/.cache/kokoro"); os.makedirs(cache, exist_ok=True)
    base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
    for name, url in (("kokoro.onnx", base + "kokoro-v1.0.int8.onnx"), ("voices.bin", base + "voices-v1.0.bin")):
        p = os.path.join(cache, name)
        if not os.path.exists(p): subprocess.run(["curl", "-sSL", "-o", p, url], check=True)
    try:
        import kokoro_onnx  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "kokoro-onnx", "soundfile", "--break-system-packages"], check=True)
    return os.path.join(cache, "kokoro.onnx"), os.path.join(cache, "voices.bin")

def voice_track(spec, LEN, out_wav):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    from scipy.signal import resample_poly
    m, v = ensure_kokoro(); k = Kokoro(m, v); SR = 44100
    track = np.zeros(int(LEN * SR)); prev = 0; report = []
    for ln in spec["lines"]:
        t0 = float(ln["at"]) if "at" in ln else T(ln["beat"]) + (0.03 if ln.get("beat") == DROP_BEAT else 0)
        a, sr = k.create(ln["text"], voice=spec.get("voice", "am_michael"), speed=spec.get("speed", 1.05), lang="en-us")
        nz = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0] - 150):nz[-1] + 600]; a = resample_poly(a, SR, sr)
        i = int(t0 * SR); j = min(len(track), i + len(a)); track[i:j] += a[:j - i]
        end = t0 + len(a) / SR
        report.append(f"{t0:6.2f}-{end:6.2f} {'OVERLAP ' if t0 < prev - .02 else ''}{'PAST END ' if end > LEN else ''}{ln['text']}")
        prev = end
    raw = out_wav + ".raw.wav"; sf.write(raw, track, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    "highpass=f=80,bass=g=2:f=160,acompressor=threshold=0.08:ratio=4:attack=5:release=150,aecho=0.8:0.25:30:0.06,"
                    "alimiter=limit=0.9", out_wav], check=True)
    os.remove(raw)
    print("\n".join(report))

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; LEN = float(spec.get("length", 44.5))
    for s in spec["shots"]:
        if s["type"] not in SHOTS: sys.exit(f"unknown shot type {s['type']}; use one of {sorted(SHOTS)}")
    if len(sys.argv) > 4 and sys.argv[3] == "--preview":
        for t in [float(x) for x in sys.argv[4].split(",")]: frame(t, spec, LEN).save(out.replace(".mp4", f"_{t:05.2f}.png"))
        return
    wav = out.replace(".mp4", ".voice.wav"); voice_track(spec, LEN, wav)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-t", f"{LEN}", out], stdin=subprocess.PIPE)
    for i in range(int(LEN * FPS)): ff.stdin.write(frame(i / FPS, spec, LEN).tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav); print("done", out)

if __name__ == "__main__":
    main()
