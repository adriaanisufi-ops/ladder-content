"""Ladder explainer videos on VYZEE (default format from 2026-11-13, approved by Adriaan: "Price Tags").

Minimal glowing white line animation on black, one gold accent at the end, an AI voice (Kokoro, am_michael),
everything timed to the beat grid of the VYZEE sound Adriaan uses ("Use this sound" on his reference video,
starting at 0:00). The video has NO music: he adds VYZEE in TikTok. Output = voice only.

Song map (measured from his reference): ~107.7 BPM, calm intro, silence at 16.4 s, DROP at 17.18 s (beat 31),
loud part until the breakdown at 36.8 s, quiet part after that (second drop at 47.2 s, only for long videos).

Usage:  python3 toolkit/vyzee.py SPEC.json OUT.mp4 [--preview 0.03,17.3,40]
Example spec: toolkit/specs/example-vyzee-price-tags.json (the approved video).
New on 2026-11-16: ghost (the gap: you vs the idea of you running ahead), blueprint (the manual nobody handed you,
drawn rung by rung), puzzle (a jigsaw piece sanding off its own edges), doors (resistance: START door to push, STOP door to hold).
New on 2026-11-17: split (WHAT YOU SAY vs WHAT YOU DO drifting apart, caught back), pulse (heart monitor: one spike then a
flatline, or a steady rhythm), pillars (four statements standing on nothing until the ground slides in), match (books
stack up next to an unstruck match, then it is struck gold).

Spec:
  length      seconds (about 40 to 45)
  voice       Kokoro voice (default am_michael), speed (default 1.05)
  lines       [{"beat": 4, "text": "..."}]  or {"at": 0.12, ...}: spoken lines, start on a beat of GRID
  text        [{"from": 0, "to": 4, "big": "..."} | {"pill": "..."} | {"small": "..."}, optional "y", "size", "gold"]
              on-screen words; from/to are beat numbers (floats ok) or {"t": seconds}; "to" may be omitted
  shots       graphics, each {"type": ..., "from": beat, "to": beat, ...}; see SHOTS below
  sound       beat profile in toolkit/sounds/<name>.json (default vyzee). New sounds: python3 toolkit/beatmap.py SOUND OUT.json
  punch       "drop" (camera punch on every beat of the loud part) or a list of beats; punch_amount (default .035)
  comment_q   {"from": beat, "text": "WHICH STEP DO YOU SKIP? 1, 2, 3 OR 4?"}: the comment question in big white text at the end (y 560, under the gold line)
  hook_type   claim | stop | question | proof (for the score and the weekly review). Rules: FORMULA.md, check: toolkit/score.py
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

def load_sound(name):
    """switch the beat grid to another sound profile (toolkit/sounds/<name>.json, made with toolkit/beatmap.py)"""
    global GRID, SILENCE, DROP_BEAT, BREAK_T
    pr = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", name + ".json")))
    GRID, SILENCE, DROP_BEAT, BREAK_T = pr["grid"], pr["silence"], pr["drop_beat"], pr["break_t"]
    return pr

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
    end = s["end"] if "end" in s else s["to"]
    lit = int(cl((t - T(s.get("start", s["from"]))) / max(.1, T(end) - T(s.get("start", s["from"])))) * 30)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0; y0 = s.get("y", 720)
    for i in range(30):
        r, c = divmod(i, 6); x, y = 300 + c * 96, y0 + r * 96
        if i < lit:
            d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=WHITE + (int(240 * a * (1 - gold)),))
            if gold > 0: g.ellipse([x - 20, y - 20, x + 20, y + 20], fill=GOLD + (int(255 * a * gold),))
        else: d.ellipse([x - 20, y - 20, x + 20, y + 20], outline=WHITE + (int(110 * a),), width=3)
    if s.get("counter", True): text_c(d, f"DAY {max(1, lit)}", y0 - 240, 120, a)

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

def phone_sq(d, cx, cy, a, k=1.0, fill=True):
    if a <= 0.01: return
    w, h = 54 * k, 92 * k
    if fill: d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=int(10 * k), fill=WHITE + (int(240 * a),))
    else: d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=int(10 * k), outline=WHITE + (int(240 * a),), width=4)

def shot_gaps(t, d, g, a, s):
    """a day as a line with empty gaps; something snaps into every gap. keys: gaps [{label, beat, snap}], rush [from, to] (many small gaps filling fast)"""
    y = 900; d.line([150, y, 930, y], fill=WHITE + (int(150 * a),), width=3)
    gaps = s["gaps"]; xs = [260 + i * (560 / max(1, len(gaps) - 1)) for i in range(len(gaps))]
    for x, gp in zip(xs, gaps):
        r = 70
        d.ellipse([x - r, y - r, x + r, y + r], fill=(8, 8, 10, int(255 * a)), outline=WHITE + (int(230 * a),), width=4)
        text_c(d, gp["label"], y + 100, 26, a * ease((t - T(gp["beat"])) / .15), sp=4, cx=x)
        if t >= T(gp["snap"]):
            k = t - T(gp["snap"]); fl = math.exp(-k * 9)
            phone_sq(d, x, y - 90 * math.exp(-k * 18), a, 1 + .2 * fl)
            if fl > .05: d.ellipse([x - r - 30 * (1 - fl), y - r - 30 * (1 - fl), x + r + 30 * (1 - fl), y + r + 30 * (1 - fl)], outline=WHITE + (int(200 * a * fl),), width=3)
    if "rush" in s:
        rf, rt = T(s["rush"][0]), T(s["rush"][1]); n = 16
        for i in range(n):
            x = 170 + i * (740 / (n - 1)); ts = rf + i * (rt - rf) / n
            if t < rf - .2 or min(abs(x - xx) for xx in xs) < 95: continue
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(8, 8, 10, int(255 * a)), outline=WHITE + (int(200 * a),), width=3)
            if t >= ts: phone_sq(d, x, y, a, .3)

def shot_alarm(t, d, g, a, s):
    """one empty circle (the gap) that alarms on every beat from 'start' until 'stop', then calms down until 'calm'.
    a phone hovers at the edge and gets pulled in on every pulse, drifts away after 'stop'. keys: start, stop, calm"""
    cx, cy, R = 540, 900, 230
    st, sp, ca = s.get("start", DROP_BEAT), s["stop"], s["calm"]
    k = 0.0; last = None
    for b in range(int(st), int(ca) + 1):
        if b > sp and (b - sp) % 2: continue
        tb = T(b)
        if tb <= t: last = (b, tb)
    if last:
        b, tb = last; amp = 1.0 if b < sp else max(0.0, 1 - (b - sp) / max(1, ca - sp)); k = amp * math.exp(-(t - tb) * 5)
        for j in range(2):
            rr = R + (t - tb) * (420 + j * 160); al = a * amp * cl(1 - (t - tb) / .55) * (.8 - j * .3)
            if al > .02: d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=WHITE + (int(255 * al),), width=4)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(250, 250, 252, int(200 * a * k)), outline=WHITE + (int(235 * a),), width=5)
    pull = k if t < T(sp) else 0.0
    away = ease((t - T(sp)) / max(.1, T(ca) - T(sp)))
    px = cx + R + 120 - pull * 110 + away * 260
    phone_sq(d, px, cy, a * (1 - away), 1.0)

def shot_void(t, d, g, a, s):
    """the same empty circle, quiet: stars appear inside from 'stars', the ring turns gold on 'gold'. keys: stars, gold"""
    cx, cy = 540, 900; R = 230 + 25 * ease((t - T(s["from"])) / 6)
    st = ease((t - T(s.get("stars", s["from"]))) / 3)
    for (ang, sp_) in PARTS + PARTS[:10]:
        rr = (sp_ - 250) / 350 * (R - 30); x, y = cx + math.cos(ang * 3.1) * rr, cy + math.sin(ang * 1.7) * rr
        tw = .6 + .4 * math.sin(t * 2.5 + ang * 7)
        if st * tw > .03: d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=WHITE + (int(220 * a * st * tw),))
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=WHITE + (int(235 * a * (1 - gold)),), width=5)
    if gold > 0:
        g.ellipse([cx - R, cy - R, cx + R, cy + R], outline=GOLD + (int(255 * a * gold),), width=7)

def shot_chart(t, d, g, a, s):
    """bar chart of days with a horizontal line (the plan, or the floor).
    keys: bars [{h (0..1), beat, label}], line {level (0..1), label, beat}, snap (beat: the line cracks where a bar is below it),
    checks true (a check above every bar that reaches the line; for a floor: every bar above it), base y, top y"""
    x0, x1, yb, yt = 170, 910, s.get("base", 1180), s.get("top", 640)
    bars = s["bars"]; n = len(bars); cw = (x1 - x0) / n; bw = min(70, cw * .6)
    d.line([x0 - 10, yb, x1 + 10, yb], fill=WHITE + (int(170 * a),), width=3)
    ln = s.get("line"); ly = yb - (yb - yt) * ln["level"] if ln else None
    snap = T(s["snap"]) if "snap" in s else None
    for i, b in enumerate(bars):
        cx = x0 + cw * (i + .5); gr = ease((t - T(b["beat"])) / .2); h = (yb - yt) * b["h"] * gr
        if gr <= 0: continue
        d.rounded_rectangle([cx - bw / 2, yb - h, cx + bw / 2, yb], radius=8, fill=WHITE + (int(225 * a),))
        if b.get("label"): text_c(d, b["label"], yb + 16, 20 if n > 8 else 24, a * .7, sp=2, cx=cx)
        if ln and s.get("checks") and gr >= 1:
            ok = b["h"] >= ln["level"] if not ln.get("floor") else b["h"] >= ln["level"]
            if ok: check(d, cx, yb - h - 40, 30, a, (t - T(b["beat"]) - .2) / .15)
            elif snap is not None and t >= snap: cross(d, cx, yb - h - 46, 18, a, (t - snap) / .3)
    if ln and t >= T(ln.get("beat", s["from"])):
        la = a * ease((t - T(ln.get("beat", s["from"]))) / .2)
        if snap is not None and t >= snap:
            # the line cracks at the first bar that is below it and falls
            bi = next(i for i, b in enumerate(bars) if b["h"] < ln["level"]); cx = x0 + cw * (bi + .5); k = t - snap
            drop = min(260, 900 * k * k); fade = cl(1 - k / .9)
            d.line([x0 - 10, ly, cx - 10, ly + 6], fill=WHITE + (int(240 * la),), width=5)
            if fade > 0: d.line([cx + 10, ly + drop, x1 + 10, ly + drop * .55], fill=WHITE + (int(240 * la * fade),), width=5)
            for j in range(6):
                ang = j * 1.1; rr = 20 + 120 * ease(k / .5); al = la * cl(1 - k / .6)
                if al > .02: d.ellipse([cx + math.cos(ang) * rr - 4, ly + math.sin(ang) * rr - 4, cx + math.cos(ang) * rr + 4, ly + math.sin(ang) * rr + 4], fill=WHITE + (int(255 * al),))
        else:
            col = GOLD if ln.get("gold") else WHITE; lay = g if ln.get("gold") else d
            for x in range(int(x0 - 10), int(x1 + 10), 26): lay.line([x, ly, x + 14, ly], fill=col + (int(240 * la),), width=5)
        if ln.get("label"): pill(d, ln["label"], ly - 34, la, cx=x1 - 70, sz=20)

def shot_numbered(t, d, g, a, s):
    """a numbered method, one step per beat; earlier steps stay (dimmed). keys: items [{text, beat}], y, gap, title"""
    y0, gap = s.get("y", 470), s.get("gap", 150)
    if s.get("title"): text_c(d, s["title"], y0 - 120, 30, a * .85, sp=8)
    cur = max([i for i, it in enumerate(s["items"]) if t >= T(it["beat"])], default=-1)
    for i, it in enumerate(s["items"]):
        if t < T(it["beat"]): continue
        k = t - T(it["beat"]); al = a * ease(k / .12) * (1.0 if i == cur else .55); y = y0 + i * gap
        sc_ = 1 + .25 * math.exp(-k * 14)
        r = 34 * sc_; cx = 210
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=WHITE + (int(240 * al),))
        text_c(d, str(i + 1), y - 26 * sc_, int(40 * sc_), al, col=INK, sp=0, cx=cx)
        lines = wrap_lines(d, it["text"], 40, 640, 2)
        f = font(40)
        for j, l in enumerate(lines):
            x = 270
            for c in l:
                d.text((x, y - 24 - (len(lines) - 1) * 24 + j * 50), c, font=f, fill=WHITE + (int(255 * al),)); x += d.textlength(c, font=f) + 2

def shot_convert(t, d, g, a, s):
    """rows: big goal -> its floor, one row per beat. keys: rows [{a, b, beat}], y, gap, header"""
    y0, gap = s.get("y", 520), s.get("gap", 150)
    if s.get("header"): text_c(d, s["header"], y0 - 140, 30, a * .85, sp=8)
    for i, r in enumerate(s["rows"]):
        if t < T(r["beat"]): continue
        k = t - T(r["beat"]); y = y0 + i * gap; al = a * ease(k / .12)
        text_c(d, r["a"], y - 24, 40, al * .55, cx=300, sp=3)
        ar = ease((k - .1) / .25)
        if ar > 0:
            d.line([440, y, 440 + 90 * ar, y], fill=WHITE + (int(230 * al),), width=4)
            if ar > .9: d.polygon([(530, y), (512, y - 10), (512, y + 10)], fill=WHITE + (int(230 * al),))
        bk = ease((k - .3) / .15)
        if bk > 0:
            sc_ = 1 + .3 * math.exp(-(k - .3) * 14)
            text_c(d, r["b"], y - 28 * sc_, int(46 * sc_), al * bk, cx=740, sp=3)


def shot_edges(t, d, g, a, s):
    """a vague goal is a wobbling cloud; at 'snap' it gets hard edges (a box), pills land on its edges one per beat.
    keys: labels [{text, beat}] (inside text, last one wins), snap, pills [{text, beat, pos "top"|"bottom"|"under"}], fade [from, to] (cloud fades), gold, cy"""
    cx, cy = 540, s.get("cy", 900); hw, hh = 320, 200
    k = ease((t - T(s["snap"])) / .25) if "snap" in s else 0.0
    fa = 1.0
    if "fade" in s and k <= 0: fa = 1 - .75 * ease((t - T(s["fade"][0])) / max(.1, T(s["fade"][1]) - T(s["fade"][0])))
    gold = ease((t - T(s["gold"])) / .35) if "gold" in s else 0
    pts = []
    for i in range(72):
        ang = i / 72 * 2 * math.pi
        r = 1 + .13 * math.sin(3 * ang + t * 1.7) + .08 * math.sin(5 * ang - t * 2.3) + .05 * math.sin(7 * ang + t * 3.1)
        bx, by = math.cos(ang) * hw * .95 * r, math.sin(ang) * hh * 1.1 * r
        m = max(abs(math.cos(ang)) / hw, abs(math.sin(ang)) / hh); rx, ry = math.cos(ang) / m, math.sin(ang) / m
        pts.append((cx + bx + (rx - bx) * k, cy + by + (ry - by) * k))
    if gold < 1: d.polygon(pts, outline=WHITE + (int(235 * a * fa * (1 - gold)),), width=5 if k > .5 else 4)
    if gold > 0: g.polygon(pts, outline=GOLD + (int(255 * a * gold),), width=7)
    labs = [l for l in s.get("labels", []) if t >= T(l["beat"])]
    if labs:
        l = labs[-1]; sc_ = 1 + .2 * math.exp(-(t - T(l["beat"])) * 12)
        lay, col = (g, GOLD) if gold > .5 else (d, WHITE)
        big(lay, l["text"], cy - 40 * sc_ - (20 if len(l["text"]) > 14 else 0), int(l.get("size", 48) * sc_), a * fa * ease((t - T(l["beat"])) / .12), col, maxw=480)
    for pl in s.get("pills", []):
        if t < T(pl["beat"]): continue
        y = {"top": cy - hh, "bottom": cy + hh, "under": cy + hh + 110}[pl.get("pos", "top")]
        sc_ = 1 + .3 * math.exp(-(t - T(pl["beat"])) * 14)
        pill(d, pl["text"], y, a * ease((t - T(pl["beat"])) / .1), sz=int(34 * sc_))

def shot_nail(t, d, g, a, s):
    """a belief is a nail on a board: said once it sits on the surface and tips over at 'tip'; every strike (beat)
    drives it deeper with a hammer flash, taps are small strikes. keys: strikes [beats], taps [beats], tip, stand, gold, label, by (board y)"""
    by = s.get("by", 1180); L = 300; cx = 540
    strikes = s.get("strikes", []); taps = s.get("taps", [])
    depth = sum(.17 for b in strikes if t >= T(b)) + sum(.012 for b in taps if t >= T(b))
    last = max([T(b) for b in strikes + taps if t >= T(b)], default=None)
    if last is not None:
        dk = t - last; depth -= (.17 if last in [T(b) for b in strikes] else .012) * math.exp(-dk * 25)
    depth = min(s.get("max_depth", .72), max(0, depth))
    tip = 0.0
    if "tip" in s and t >= T(s["tip"]): tip = ease((t - T(s["tip"])) / .35)
    if "stand" in s and t >= T(s["stand"]): tip *= 1 - ease((t - T(s["stand"])) / .25)
    gold = ease((t - T(s["gold"])) / .35) if "gold" in s else 0
    c = WHITE + (int(230 * a),)
    d.line([150, by, 930, by], fill=c, width=5)
    for i in range(5):
        y = by + 30 + i * 32; d.line([170 + i * 23, y, 910 - i * 31, y], fill=WHITE + (int(70 * a),), width=2)
    vis = L * (1 - depth); ang = tip * math.radians(78)
    bx, byy = cx, by
    tx, ty = bx + math.sin(ang) * vis, byy - math.cos(ang) * vis
    lay, col = (g, GOLD) if gold > 0 else (d, WHITE); al = a * (gold if gold > 0 else 1)
    if gold > 0 and gold < 1:
        d.line([bx, byy, tx, ty], fill=WHITE + (int(240 * a * (1 - gold)),), width=12)
    lay.line([bx, byy, tx, ty], fill=col + (int(240 * al),), width=12)
    hx, hy = math.cos(ang) * 46, math.sin(ang) * 46
    lay.line([tx - hx, ty - hy, tx + hx, ty + hy], fill=col + (int(250 * al),), width=18)
    if last is not None and t - last < .35 and last in [T(b) for b in strikes]:
        q = (t - last) / .35
        d.rounded_rectangle([cx - 90, ty - 120 - 40 * q, cx + 90, ty - 40 - 40 * q], radius=10, fill=WHITE + (int(240 * a * (1 - q)),))
        for j in range(8):
            an = math.pi + j * math.pi / 7; rr = 60 + 160 * q
            d.line([cx + math.cos(an) * rr * .6, ty + math.sin(an) * rr * .6, cx + math.cos(an) * rr, ty + math.sin(an) * rr], fill=WHITE + (int(200 * a * (1 - q)),), width=4)
    if s.get("label") and tip < .1:
        pill(lay, s["label"], ty - 90, al * (1 - tip * 8), sz=30)

def shot_scale(t, d, g, a, s):
    """a ledger as a balance: blocks drop on the left (MISSING) or right (ALREADY TRUE) on their beat, the beam tilts.
    keys: left [{text, beat}], right [{text, beat}], heads [left, right], gold, cy"""
    cx, cy = 540, s.get("cy", 760)
    nl = sum(1 for b in s.get("left", []) if t >= T(b["beat"])); nr = sum(1 for b in s.get("right", []) if t >= T(b["beat"]))
    tilt = max(-.32, min(.32, (nl - nr) * .09)); gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    c = WHITE + (int(230 * a),)
    d.line([cx, cy, cx, cy + 520], fill=c, width=6); d.line([cx - 110, cy + 520, cx + 110, cy + 520], fill=c, width=6)
    d.polygon([(cx - 22, cy - 6), (cx + 22, cy - 6), (cx, cy - 40)], fill=c)
    arm = 255
    for side, key in ((-1, "left"), (1, "right")):
        ex, ey = cx + side * arm * math.cos(tilt), cy + side * arm * math.sin(tilt)
        py = ey + 170
        lay, col = (g, GOLD) if (gold > 0 and side == 1) else (d, WHITE); al = a * (gold if lay is g else 1)
        if lay is g: pass
        d.line([cx, cy, ex, ey], fill=c, width=6)
        d.line([ex, ey, ex - 105, py], fill=WHITE + (int(170 * a),), width=3); d.line([ex, ey, ex + 105, py], fill=WHITE + (int(170 * a),), width=3)
        lay.line([ex - 125, py, ex + 125, py], fill=col + (int(235 * al),), width=6)
        if s.get("heads"): text_c(d, s["heads"][0 if side < 0 else 1], py + 26, 24, a * .75, sp=4, cx=ex)
        y = py - 4
        for b in s.get(key, []):
            if t < T(b["beat"]): continue
            k = t - T(b["beat"]); fall = (1 - ease(k / .22)) * 260
            f = font(26); w = min(230, spaced_w(d, b["text"], f, 2) + 30)
            box = [ex - w / 2, y - 52 - fall, ex + w / 2, y - fall]
            lay.rounded_rectangle(box, radius=8, outline=col + (int(235 * al * ease(k / .1)),), width=4)
            text_c(lay, b["text"], y - 42 - fall, 26, al * ease(k / .1), col=col, sp=2, cx=ex)
            y -= 58

def shot_house(t, d, g, a, s):
    """the mind as a house: the host (figure) stays inside, thoughts are visitors (words) that come in through the door
    and leave through the roof. keys: visitors [{text, in, out}], light (beat: the windows light up), gold, cy"""
    cx = 540; base = s.get("base", 1260); top = base - 480; x0, x1 = 300, 780
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    lay, col = (g, GOLD) if gold > 0 else (d, WHITE); al = a * (gold if gold > 0 else 1)
    if 0 < gold < 1: lay2 = d
    for L_, C_, A_ in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if A_ <= .01: continue
        c = C_ + (int(235 * A_),)
        L_.line([x0, top, x0, base], fill=c, width=5); L_.line([x1, top, x1, base], fill=c, width=5)
        L_.line([(x0 - 30, top + 10), (cx, top - 200), (x1 + 30, top + 10)], fill=c, width=5, joint="curve")
        L_.line([x0 - 40, base, x1 + 40, base], fill=c, width=4)
        L_.rectangle([cx - 210, base - 170, cx - 120, base], outline=c, width=4)
        person(L_, 660, base, A_, 1.0, C_)
    if "light" in s:
        li = ease((t - T(s["light"])) / .3)
        if li > 0: g.rectangle([cx + 60, top + 60, cx + 170, top + 150], outline=GOLD + (int(220 * a * li),), width=4)
    for vi, v in enumerate(s.get("visitors", [])):
        ti, to = T(v["in"]), T(v["out"])
        if t < ti or t > to + .9: continue
        p_in = ease((t - ti) / .45); p_out = ease((t - to) / .8)
        x = cx - 165 + (cx - (cx - 165)) * p_in; y = base - 60 - (base - 60 - (top + 70 + v.get("slot", 0) * 64)) * p_in
        y -= p_out * 420; al_ = a * cl((t - ti) / .15) * (1 - p_out)
        sz = 36
        while spaced_w(d, v["text"], font(sz), 3) > 440 and sz > 22: sz -= 2
        text_c(d, v["text"], y - sz / 2, sz, al_ * .9, sp=3, cx=x if p_in < 1 else cx)

def shot_replay(t, d, g, a, s):
    """a rehearsal on a loop: a circular arrow spins faster and faster around a counter that counts up (TIMES FELT),
    while the real event is a small circle that has happened 0 times. At 'cut' the loop snaps open and stops.
    keys: cy, r, count [from, to, max], label, cut, real {beat, y, r, label}, gold (the real circle turns gold), dim"""
    cx, cy, R = 540, s.get("cy", 900), s.get("r", 230)
    c0, c1, mx = s.get("count", [0, 20, 40]); tc0, tc1 = T(c0), T(c1)
    cut = T(s["cut"]) if "cut" in s else None
    tt = min(t, cut) if cut is not None and t >= cut else t
    p = cl((tt - tc0) / max(.1, tc1 - tc0)); n = max(1, int(round(1 + (mx - 1) * p ** 1.5)))
    ang = math.degrees(tt * 1.6 + 7 * p * p * (tc1 - tc0) / 4)
    k = ease((t - cut) / .5) if cut is not None and t >= cut else 0.0
    dim = 1 - s.get("dim", .45) * k
    gap = 40 + 110 * k; st = ang + gap / 2; en = ang + 360 - gap / 2
    c = WHITE + (int(235 * a * dim),); off = 26 * k
    box = [cx - R, cy - R + off, cx + R, cy + R + off]
    d.arc(box, st, en, fill=c, width=max(4, int(R * .045)))
    e = math.radians(en); hx, hy = cx + math.cos(e) * R, cy + off + math.sin(e) * R
    tx, ty = -math.sin(e), math.cos(e); nx, ny = math.cos(e), math.sin(e); hs = R * .12
    if k < .5:
        d.polygon([(hx + tx * hs, hy + ty * hs), (hx - tx * hs * .3 + nx * hs * .7, hy - ty * hs * .3 + ny * hs * .7),
                   (hx - tx * hs * .3 - nx * hs * .7, hy - ty * hs * .3 - ny * hs * .7)], fill=c)
    if cut is not None and 0 <= t - cut < .45:
        q = (t - cut) / .45; m = math.radians(ang)
        for j in range(7):
            an = m + (j - 3) * .45; r0, r1 = R + 10 + 40 * q, R + 40 + 120 * q
            d.line([cx + math.cos(an) * r0, cy + math.sin(an) * r0, cx + math.cos(an) * r1, cy + math.sin(an) * r1], fill=WHITE + (int(220 * a * (1 - q)),), width=4)
    sz = int(R * .62); text_c(d, str(n), cy + off - sz * .62, sz, a * dim, sp=2)
    if s.get("label"): text_c(d, s["label"], cy + off + R * .36, max(18, int(R * .1)), a * .75 * dim, sp=5)
    rl = s.get("real")
    if rl and t >= T(rl["beat"]):
        q = t - T(rl["beat"]); rr = rl.get("r", 46) * (1 + .3 * math.exp(-q * 12)); ry = rl.get("y", cy + R + 130)
        gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
        al = a * ease(q / .15)
        d.ellipse([cx - rr, ry - rr, cx + rr, ry + rr], outline=WHITE + (int(235 * al * (1 - gold)),), width=5)
        if gold > 0:
            g.ellipse([cx - rr, ry - rr, cx + rr, ry + rr], fill=GOLD + (int(255 * al * gold),))
        if rl.get("label"): text_c(g if gold > .5 else d, rl["label"], ry + rr + 18, 26, al * .9, col=GOLD if gold > .5 else WHITE, sp=4)

def link(d, x, y, w, h, a, side=False, col=WHITE, thin=False):
    c = col + (int(235 * a),)
    if side: d.rounded_rectangle([x - w / 2, y - h * .16, x + w / 2, y + h * .16], radius=int(h * .16), outline=c, width=3 if thin else 6)
    else: d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=int(h / 2), outline=c, width=3 if thin else 6)

def shot_chain(t, d, g, a, s):
    """a streak as a chain between two posts: one link per day. A skipped day is a dashed empty link (gap beat); at 'break'
    the whole chain falls (DAY 0); at 'fix' it comes back and the smallest, thin link fills the gap.
    keys: links [{beat, gap (beat the dashed hole shows), small}], break, fix, cy, scale, counter ("DAY"), gold"""
    sc = s.get("scale", 1.0); cy = s.get("cy", 900); L = s["links"]; n = len(L)
    sp = 70 * sc; lw, lh = 100 * sc, 54 * sc; x0 = 540 - sp * (n - 1) / 2
    br = T(s["break"]) if "break" in s else None; fx = T(s["fix"]) if "fix" in s else None
    falling = br is not None and t >= br and (fx is None or t < fx)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    pc = WHITE + (int(200 * a),)
    for px in (x0 - sp * .95, x0 + sp * (n - 1) + sp * .95):
        d.line([px, cy - 80 * sc, px, cy + 160 * sc], fill=pc, width=6); d.line([px - 30 * sc, cy + 160 * sc, px + 30 * sc, cy + 160 * sc], fill=pc, width=6)
    for i, lk in enumerate(L):
        x = x0 + i * sp; side = i % 2 == 1
        if "gap" in lk and t >= T(lk["gap"]) and t < T(lk["beat"]) and not falling:
            bl = .55 + .45 * math.sin(t * 9)
            for j in range(10):
                an = j / 10 * 2 * math.pi; an2 = an + .3
                d.line([x + math.cos(an) * lw * .48, cy + math.sin(an) * lh * .5, x + math.cos(an2) * lw * .48, cy + math.sin(an2) * lh * .5], fill=WHITE + (int(200 * a * bl),), width=3)
            continue
        if t < T(lk["beat"]): continue
        if br is not None and T(lk["beat"]) > br and fx is not None and T(lk["beat"]) < fx: continue
        q = t - T(lk["beat"]); al = a if T(lk["beat"]) <= 0 else a * ease(q / .12); pop = 1 + (.3 * math.exp(-q * 14) if T(lk["beat"]) > 0 else 0)
        y = cy
        if falling:
            k = max(0.0, t - br - abs(i - n / 2) * .03); y += min(900, 1400 * k * k); al *= cl(1 - k / .9)
        thin = lk.get("small", False)
        ww, hh = lw * pop * (.8 if thin else 1), lh * pop * (.8 if thin else 1)
        if gold < 1: link(d, x, y, ww, hh, al * (1 - gold), side, thin=thin)
        if gold > 0: link(g, x, y, ww, hh, al * gold, side, col=GOLD, thin=thin)
    if s.get("counter"):
        cnt = 0 if falling else sum(1 for lk in L if t >= T(lk["beat"]) and not (br is not None and fx is not None and br < T(lk["beat"]) < fx))
        lay, col = (g, GOLD) if gold > .5 else (d, WHITE)
        text_c(lay, f"{s['counter']} {cnt}", cy - 170 * sc, int(54 * sc), a, col=col, sp=6)

def barbell(d, x, y, s, a, col=WHITE):
    c = col + (int(240 * a),)
    d.line([x - 95 * s, y, x + 95 * s, y], fill=c, width=max(3, int(6 * s)))
    for sx in (-1, 1):
        d.rounded_rectangle([x + sx * 80 * s - 8 * s, y - 30 * s, x + sx * 80 * s + 8 * s, y + 30 * s], radius=int(4 * s), outline=c, width=max(3, int(5 * s)))

def shot_room(t, d, g, a, s):
    """the room nobody's grading: a figure training (the bar goes overhead on every rep beat) under a spotlight while an
    audience watches; the audience leaves at crowd[1], the light goes out at light[1], the bar goes down at 'down'.
    keys: base, scale, crowd [in, out], light [on, off], reps [beats], down, walls, gold"""
    base = s.get("base", 1150); sc = s.get("scale", 1.5); cx = 540; top = base - 560
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    if s.get("walls", True):
        c = WHITE + (int(150 * a),)
        d.line([190, top, 190, base], fill=c, width=3); d.line([890, top, 890, base], fill=c, width=3)
        d.line([190, top, 890, top], fill=WHITE + (int(70 * a),), width=2)
    d.line([150, base, 930, base], fill=WHITE + (int(190 * a),), width=4)
    if "light" in s:
        on, off = s["light"]; li = ease((t - T(on)) / .2) * (1 - ease((t - T(off)) / .35)) if t >= T(on) else 0
        if li > 0:
            d.polygon([(495, top), (585, top), (720, base), (360, base)], fill=WHITE + (int(34 * a * li),))
            d.ellipse([360, base - 22, 720, base + 22], fill=WHITE + (int(50 * a * li),))
    if "crowd" in s:
        ci, co = s["crowd"]
        for r, (yy, nn) in enumerate(((base + 85, 7), (base + 160, 8))):
            for j in range(nn):
                x = 220 + j * (640 / (nn - 1)) + (0 if r == 0 else 0); k = r * 7 + j
                al = cl((t - T(ci) - k * .03) / .12) * (1 - cl((t - T(co) - k * .07) / .25)); dy = 30 * cl((t - T(co) - k * .07) / .25)
                if al <= .01: continue
                cc = WHITE + (int(150 * a * al),)
                d.ellipse([x - 17, yy - 40 + dy, x + 17, yy - 6 + dy], outline=cc, width=3)
                d.arc([x - 30, yy + dy, x + 30, yy + 50 + dy], 180, 360, fill=cc, width=3)
    reps = [T(b) for b in s.get("reps", [])]; last = max([r for r in reps if r <= t], default=None)
    lift = 0.0
    if last is not None:
        q = t - last; lift = ease(q / .16) if q < .3 else 1 - ease((q - .3) / .28)
    down = T(s["down"]) if "down" in s else None
    on_floor = down is not None and t >= down and (last is None or last < down)
    for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if al <= .01: continue
        person(lay, cx, base, al, sc, col)
        if on_floor:
            barbell(lay, cx + 170, base - 30 * sc * .8, sc * .8, al, col)
        else:
            by = base - 50 * sc - lift * 75 * sc
            barbell(lay, cx, by, sc, al, col)
            for sx in (-1, 1): lay.line([cx + sx * 20 * sc, base - 46 * sc, cx + sx * 50 * sc, by], fill=col + (int(240 * al),), width=max(3, int(6 * sc)))

def shot_seed(t, d, g, a, s):
    """a goal is a seed in a pot: every water drop (beat) makes it grow, every dig (beat) yanks the seed out of the soil
    to check it and kills the growth. keys: waters [beats], digs [beats], start (growth before the first dig), inc (per drop),
    cy (soil y), scale, hold (seconds the seed stays up), gold (a gold flower)"""
    sc = s.get("scale", 1.0); cx, cy = 540, s.get("cy", 1000); inc = s.get("inc", .2); hold = s.get("hold", .9)
    waters = [T(b) for b in s.get("waters", [])]; digs = [T(b) for b in s.get("digs", [])]
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    def growth(at, since):
        gr = s.get("start", 0.0) if since is None else 0.0
        for w in waters:
            if (since is None or w >= since) and at >= w + .3: gr += inc * ease((at - w - .3) / .4)
        return min(1.0, gr)
    ld = max([x for x in digs if x <= t], default=None)
    lift = 0.0; gr = growth(t, ld)
    if ld is not None and t - ld < hold + .5:
        q = t - ld; prev_ld = max([x for x in digs if x < ld], default=None)
        gprev = growth(ld, prev_ld)
        lift = ease(q / .2) if q < hold else 1 - ease((q - hold) / .3)
        if q < hold: gr = gprev * (1 - ease(q / .15))
    c = WHITE + (int(235 * a),)
    pw, pb, ph = 210 * sc, 150 * sc, 220 * sc
    d.line([cx - pw, cy, cx + pw, cy], fill=c, width=6)
    d.line([(cx - pw, cy), (cx - pb, cy + ph), (cx + pb, cy + ph), (cx + pw, cy)], fill=c, width=5, joint="curve")
    sy = cy + 85 * sc - lift * 230 * sc
    lay, col = (g, GOLD) if gold > .5 else (d, WHITE)
    if gr > .01:
        hgt = 40 * sc + gr * 440 * sc; pts = []
        for i in range(13):
            f = i / 12; pts.append((cx + math.sin(t * 1.4 + f * 2) * 8 * gr * f, sy - 10 * sc - f * hgt))
        lay.line(pts, fill=col + (int(240 * a),), width=max(3, int(6 * sc)), joint="curve")
        for k in range(int(gr * 6)):
            f = (k + 1) / 7; bx, byy = pts[int(f * 12)]; sd = 1 if k % 2 else -1; L_ = 84 * sc
            lp = [(bx, byy), (bx + sd * L_ * .45, byy - L_ * .42), (bx + sd * L_, byy - L_ * .22), (bx + sd * L_ * .55, byy + L_ * .1)]
            lay.polygon(lp, fill=col + (int(60 * a),)); lay.line(lp + [lp[0]], fill=col + (int(235 * a),), width=max(3, int(5 * sc)), joint="curve")
        if gold > 0:
            tx, ty = pts[-1]
            for j in range(6):
                an = j / 6 * 2 * math.pi + t * .3; px, py = tx + math.cos(an) * 30 * sc * gold, ty + math.sin(an) * 30 * sc * gold
                g.ellipse([px - 20 * sc, py - 20 * sc, px + 20 * sc, py + 20 * sc], fill=GOLD + (int(255 * a * gold),))
            g.ellipse([tx - 16 * sc, ty - 16 * sc, tx + 16 * sc, ty + 16 * sc], fill=INK + (int(255 * a * gold),))
    lay.ellipse([cx - 24 * sc, sy - 15 * sc, cx + 24 * sc, sy + 15 * sc], fill=col + (int(245 * a),))
    if ld is not None and 0 <= t - ld < .5:
        q = (t - ld) / .5
        for j in range(9):
            an = math.pi + (j + .5) * math.pi / 9; rr = 30 + 170 * q * sc
            d.ellipse([cx + math.cos(an) * rr - 5, cy + math.sin(an) * rr * .7 - 5, cx + math.cos(an) * rr + 5, cy + math.sin(an) * rr * .7 + 5], fill=WHITE + (int(220 * a * (1 - q)),))
    if lift > .8: text_c(d, "?", sy - 140 * sc, int(80 * sc), a * cl((lift - .8) / .2))
    for w in waters:
        q = t - w
        if 0 <= q < .3:
            y = cy - 560 * sc + q / .3 * (560 * sc - 20); r = 16 * sc
            d.ellipse([cx - r, y - r, cx + r, y + r], fill=WHITE + (int(240 * a),)); d.polygon([(cx - r * .9, y - r * .4), (cx + r * .9, y - r * .4), (cx, y - r * 2.6)], fill=WHITE + (int(240 * a),))
        elif .3 <= q < .65:
            k = (q - .3) / .35; rr = 20 + 90 * k * sc
            d.ellipse([cx - rr, cy - rr * .3, cx + rr, cy + rr * .3], outline=WHITE + (int(200 * a * (1 - k)),), width=3)

def person_outline(d, x, yf, a=1.0, s=1.0, col=WHITE):
    if a <= 0.01: return
    c = col + (int(255 * a),); w = max(2, int(4 * s))
    d.ellipse([x - 17 * s, yf - 92 * s, x + 17 * s, yf - 58 * s], outline=c, width=w)
    d.rounded_rectangle([x - 22 * s, yf - 52 * s, x + 22 * s, yf], radius=int(16 * s), outline=c, width=w)

def shot_ghost(t, d, g, a, s):
    """the gap: you (solid figure) and the version of you that only exists as an idea (an outline ghost) running ahead on
    the same ground; a bracket between you is the gap. keys: you (start x), ghost [[beat, x], ...] keyframes,
    ages [{beat, text}] (small label over the ghost), fade (beat the ghost fades), walk [beats] (you take one real step,
    leaving a footprint), step (px per step), scale, label (bracket text), gold, base (ground y)"""
    base = s.get("base", GROUND); step = s.get("step", 60); sc = s.get("scale", 1.0)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    d.line([140, base, 940, base], fill=WHITE + (int(160 * a),), width=3)
    walks = [T(b) for b in s.get("walk", [])]
    yx = s.get("you", 260) + sum(step * ease((t - w) / .35) for w in walks)
    for i, w in enumerate(walks):
        if t >= w + .3:
            fx = s.get("you", 260) + step * i + 10
            lay, col = (g, GOLD) if gold > .5 else (d, WHITE)
            lay.rounded_rectangle([fx - 10, base + 12, fx + 10, base + 18], radius=3, fill=col + (int(200 * a),))
    kf = s.get("ghost", [[0, 560]]); xs = [T(k[0]) for k in kf]
    gx = kf[0][1]
    for (b0, x0), (b1, x1) in zip(kf, kf[1:]):
        if t >= T(b0): gx = x0 + (x1 - x0) * ease((t - T(b0)) / max(.1, T(b1) - T(b0)))
    gf = 1 - ease((t - T(s["fade"])) / .5) if "fade" in s else 1.0
    moving = any(T(b0) <= t < T(b1) and x0 != x1 for (b0, x0), (b1, x1) in zip(kf, kf[1:]))
    bob = abs(math.sin(t * 11)) * 10 if moving else 0
    if gf > .01:
        person_outline(d, gx, base - bob, a * .7 * gf, sc)
        cur = [x for x in s.get("ages", []) if t >= T(x["beat"])]
        if cur:
            lw = spaced_w(d, cur[-1]["text"], font(26), 4); lx = min(max(gx, 150 + lw / 2), 930 - lw / 2)
            text_c(d, cur[-1]["text"], base - 150 * sc, 26, a * .8 * gf * ease((t - T(cur[-1]["beat"])) / .15), cx=lx, sp=4)
        x0, x1, by = yx + 40 * sc, gx - 40 * sc, base - 60 * sc
        if x1 - x0 > 30:
            c = WHITE + (int(200 * a * gf),)
            d.line([x0, by, x1, by], fill=c, width=3)
            for xx in (x0, x1): d.line([xx, by - 14, xx, by + 14], fill=c, width=3)
            if x1 - x0 > 170: text_c(d, s.get("label", "THE GAP"), by - 50, 28, a * gf, cx=(x0 + x1) / 2, sp=6)
    person(d, yx, base, a * (1 - gold), sc); person(g, yx, base, a * gold, sc, col=GOLD)

def shot_blueprint(t, d, g, a, s):
    """the blueprint nobody handed you: a grid sheet with a faint dashed ladder and a '?'; on every rung beat one rung is
    drawn for real (you build it yourself), gold on 'gold'. keys: box [x0, y0, x1, y1], rungs [beats] (max 9),
    wait [from, to] (a WAITING counter counts the years), years (max), figure x (a figure waits on the ground), gold"""
    x0, y0, x1, y1 = s.get("box", [300, 560, 860, 1060]); w, h = x1 - x0, y1 - y0
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    c = WHITE + (int(210 * a),)
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=c, width=4)
    for i in range(1, 8):
        xx = x0 + w * i / 8; d.line([xx, y0 + 6, xx, y1 - 6], fill=WHITE + (int(28 * a),), width=1)
        yy = y0 + h * i / 8; d.line([x0 + 6, yy, x1 - 6, yy], fill=WHITE + (int(28 * a),), width=1)
    ra, rb, top, bot = x0 + w * .33, x0 + w * .67, y0 + h * .08, y1 - h * .06
    rungs = [T(b) for b in s.get("rungs", [])]; n = 9
    built = [r for r in rungs if t >= r]
    rail = cl(len(built) / 2)
    for xx in (ra, rb):
        for k in range(0, int(bot - top), 26):
            d.line([xx, top + k, xx, min(bot, top + k + 12)], fill=WHITE + (int(70 * a * (1 - rail)),), width=3)
    if built:
        fr = ease((t - built[0]) / .4); yb = bot - (bot - top) * fr
        for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
            if al <= .01: continue
            for xx in (ra, rb): lay.line([xx, bot, xx, yb], fill=col + (int(240 * al),), width=6)
            for i, r in enumerate(built[:n]):
                y = bot - (bot - top) * (i + .5) / n; q = ease((t - r) / .2)
                sc_ = 1 + .4 * math.exp(-(t - r) * 12) if lay is d else 1
                lay.line([ra, y, ra + (rb - ra) * q, y], fill=col + (int(240 * al),), width=int(6 * sc_))
    else:
        text_c(d, "?", y0 + h / 2 - 90, 150, a * (.45 + .2 * math.sin(t * 3)))
    if "wait" in s:
        wf, wt = s["wait"]; q = cl((t - T(wf)) / max(.1, T(wt) - T(wf)))
        if t >= T(wf): text_c(d, f"WAITING: {max(1, int(q * s.get('years', 12)))} YEARS", s.get("wait_y", y1 + 40), 30, a * .85, sp=5)
    if "figure" in s:
        ground(d, a); person(d, s["figure"], GROUND, a * (1 - gold)); person(g, s["figure"], GROUND, a * gold, col=GOLD)

def _piece(cx, cy, L, tabs, r):
    """outline points of a jigsaw piece; tabs = 4 sizes (top, right, bottom, left), 1 = knob out, -1 = hole in, 0 = flat"""
    h = L / 2; corners = [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]
    pts = []
    for i in range(4):
        A, B = corners[i], corners[(i + 1) % 4]; ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L; nx, ny = uy, -ux
        k = tabs[i]; pts.append(A)
        if abs(k) > .02:
            R = r * abs(k); sg = 1 if k > 0 else -1; mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
            for j in range(25):
                th = math.radians(-131.4 - 277.2 * j / 24)
                lx, ly = R * math.cos(th), .75 * R + R * math.sin(th)
                pts.append((mx + ux * lx + nx * ly * sg, my + uy * lx + ny * ly * sg))
    return pts

def shot_puzzle(t, d, g, a, s):
    """you as a jigsaw piece sanding off your own edges to fit anywhere: on every sand beat one knob is filed flat (dust,
    its label floats up and fades); on every grow beat a knob comes back; at 'gold' the piece lights gold and the
    picture it belongs in appears around it. keys: cx, cy, L, r, labels [4] (top, right, bottom, left), sand [4 beats],
    grow [4 beats], label_y, gold"""
    cx, cy, L = s.get("cx", 540), s.get("cy", 800), s.get("L", 360); r = s.get("r", L * .16)
    sand = [T(b) for b in s.get("sand", [])]; grow = [T(b) for b in s.get("grow", [])]
    tabs = []
    for i in range(4):
        k = 1.0
        if i < len(sand) and t >= sand[i]: k = 1 - ease((t - sand[i]) / .35)
        if i < len(grow) and t >= grow[i]: k = ease((t - grow[i]) / .3) * (1 + .15 * math.exp(-(t - grow[i]) * 8))
        tabs.append(k)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    if gold > 0:
        for dx, dy, side in ((-L, 0, 1), (L, 0, 3), (0, -L, 2), (0, L, 0)):
            nt = [0, 0, 0, 0]; nt[side] = -1
            np_ = _piece(cx + dx, cy + dy, L, nt, r); g.line(np_ + [np_[0]], fill=GOLD + (int(110 * a * gold),), width=3)
    pts = _piece(cx, cy, L, tabs, r)
    if gold > 0: g.polygon(pts, fill=GOLD + (int(70 * a * gold),))
    for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if al > .01: lay.line(pts + [pts[0]], fill=col + (int(240 * al),), width=5, joint="curve")
    labels = s.get("labels", [])
    centers = [(cx, cy - L / 2), (cx + L / 2, cy), (cx, cy + L / 2), (cx - L / 2, cy)]
    for i, b in enumerate(sand):
        q = t - b
        if 0 <= q < .6:
            ox, oy = centers[i]
            for j, (ang, spd) in enumerate(PARTS[:14]):
                rr = 20 + spd * .35 * ease(q / .6); x, y = ox + math.cos(ang) * rr, oy + math.sin(ang) * rr + 80 * q * q
                d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WHITE + (int(220 * a * (1 - q / .6)),))
        if i < len(labels) and 0 <= q < 1.6:
            al = a * ease(q / .15) * cl((1.6 - q) / .4)
            text_c(d, labels[i], s.get("label_y", cy + L / 2 + r * 2 + 50) - 40 * ease(q / 1.6), 40, al, sp=6)

def door(d, x0, x1, top, base, op, a, col=WHITE, light=0.0):
    """a door frame with a panel hinged on the left; op 0 = shut, 1 = wide open; light = glow through the opening"""
    if a <= .01: return
    c = col + (int(230 * a),); w = x1 - x0
    if light > 0 and op > .02: d.rectangle([x0 + 4, top + 4, x1 - 4, base - 4], fill=WHITE + (int(70 * a * light * op),))
    ang = op * math.radians(78); pw = w * math.cos(ang); sk = 40 * math.sin(ang)
    panel = [(x0, top), (x0 + pw, top - sk), (x0 + pw, base + sk * .3), (x0, base)]
    d.polygon(panel, fill=INK + (int(255 * a),)); d.line(panel + [panel[0]], fill=c, width=4, joint="curve")
    kx = x0 + pw * .82; ky = (top + base) / 2
    d.ellipse([kx - 8, ky - 8, kx + 8, ky + 8], fill=c)
    d.line([x0 - 10, top - 10, x1 + 10, top - 10], fill=c, width=5)
    d.line([x0 - 10, top - 10, x0 - 10, base], fill=c, width=4); d.line([x1 + 10, top - 10, x1 + 10, base], fill=c, width=4)

def shot_doors(t, d, g, a, s):
    """resistance, same muscle in two directions: the left door (START) is heavy and shut, it rattles on 'shake' beats and
    opens a bit on every 'push' beat; the right door (STOP) swings open by itself on 'lure' with light pouring out and pulls
    the figure toward it, every 'hold' beat pushes it further shut. keys: base, top, push, shake, lure, hold, labels, gold"""
    base, top = s.get("base", 1320), s.get("top", 900)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    pushes = [T(b) for b in s.get("push", [])]; holds = [T(b) for b in s.get("hold", [])]
    lop = min(.95, sum(.25 * ease((t - p) / .3) for p in pushes))
    sh = sum(math.sin((t - b) * 60) * 6 * math.exp(-(t - b) * 6) for b in (T(x) for x in s.get("shake", [])) if t >= b)
    lure = ease((t - T(s["lure"])) / .8) * .7 if "lure" in s else 0
    rop = max(0.0, lure - sum(.25 * ease((t - h) / .25) for h in holds))
    labels = s.get("labels", ["START", "STOP"])
    for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if al <= .01: continue
        door(lay, 210 + sh, 430 + sh, top, base, lop, al, col, light=.6)
        door(lay, 650, 870, top, base, rop, al, col, light=1.0 + .3 * math.sin(t * 5))
        lay.line([150, base, 930, base], fill=col + (int(170 * al),), width=3)
        text_c(lay, labels[0], top - 70, 32, al, col=col, cx=320, sp=8); text_c(lay, labels[1], top - 70, 32, al, col=col, cx=760, sp=8)
    pull = rop * 50 * (1 + .15 * math.sin(t * 7))
    for k in pushes:
        q = t - k
        if 0 <= q < .5: pull -= 40 * math.sin(q / .5 * math.pi)
    px = 540 + pull
    person(d, px, base, a * (1 - gold)); person(g, px, base, a * gold, col=GOLD)

def _head(t, kf):
    """x of a moving pen head from keyframes [[beat, x], ...] (eased between keyframes)"""
    x = kf[0][1]
    for (b0, x0), (b1, x1) in zip(kf, kf[1:]):
        if t >= T(b0): x = x0 + (x1 - x0) * ease((t - T(b0)) / max(.1, T(b1) - T(b0)))
    return x

def shot_split(t, d, g, a, s):
    """the lie you tell yourself: two lines drawn side by side, WHAT YOU SAY (straight) and WHAT YOU DO; every slip
    (beat, label) bends the lower line further away, every catch (beat) bends it back with a check, gold on 'gold'
    when they run together. keys: y (story line), head [[beat, x], ...] (pen keyframes), slips [{beat, dy, text}],
    catches [beats], catch_dy, labels [top, bottom], gap (bracket text), gold"""
    y0 = s.get("y", 980); kf = s.get("head", [[s["from"], 170], [s["from"] + 30, 900]])
    slips = s.get("slips", []); catches = [T(b) for b in s.get("catches", [])]; cdy = s.get("catch_dy", 50)
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    def off(tau):
        o = sum(sl.get("dy", 70) * ease((tau - T(sl["beat"])) / .35) for sl in slips)
        return max(0.0, o - sum(cdy * ease((tau - c) / .3) for c in catches))
    t0 = T(kf[0][0]); n = max(2, int((t - t0) * 20))
    taus = [t0 + (t - t0) * i / n for i in range(n + 1)] if t > t0 else [t0]
    xs = [_head(u, kf) for u in taus]; low = [(x, y0 + 36 + off(u)) for x, u in zip(xs, taus)]
    hx = xs[-1]; ly = low[-1][1]
    labels = s.get("labels", ["WHAT YOU SAY", "WHAT YOU DO"])
    for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if al <= .01: continue
        lay.line([kf[0][1], y0, hx, y0], fill=col + (int(240 * al),), width=5)
        if len(low) > 1: lay.line(low, fill=col + (int(240 * al),), width=5, joint="curve")
        for yy in (y0, ly): lay.ellipse([hx - 9, yy - 9, hx + 9, yy + 9], fill=col + (int(255 * al),))
    f = font(28)
    d.text((kf[0][1], y0 - 50), labels[0], font=f, fill=WHITE + (int(200 * a),))
    d.text((kf[0][1], y0 + 56), labels[1], font=f, fill=WHITE + (int(200 * a * cl(1 - (off(t) - 40) / 60) if off(t) > 40 else 200 * a),))
    for sl in slips:
        q = t - T(sl["beat"])
        if q < 0 or not sl.get("text"): continue
        x = _head(T(sl["beat"]), kf); y = y0 + 36 + off(T(sl["beat"]) + .5) + 52
        x = min(max(x, 150 + len(sl["text"]) * 9), 930 - len(sl["text"]) * 9)
        pill(d, sl["text"], y, a * ease(q / .15) * (.6 if q > 1.5 else 1), cx=x, sz=26)
    for c in catches:
        if t >= c: check(d, _head(c + .3, kf), y0 - 40, 34, a, (t - c) / .15, col=GOLD if gold > .5 else WHITE)
    gap = ly - y0
    if gap > 70 and s.get("gap"):
        bx = hx + 30 if hx < 820 else hx - 30; c = WHITE + (int(200 * a),)
        d.line([bx, y0 + 10, bx, ly - 10], fill=c, width=3)
        tw = spaced_w(d, s["gap"], font(26), 4); cx = bx + 20 + tw / 2 if hx < 820 else bx - 20 - tw / 2
        text_c(d, s["gap"], (y0 + ly) / 2 - 16, 26, a * cl((gap - 70) / 40), cx=cx, sp=4)

def shot_pulse(t, d, g, a, s):
    """a heart monitor: the trace is drawn left to right by a scan head; bumps are beats of effort. One huge spike
    (the one big day) followed by a flatline, or a small steady rhythm. keys: box [x0, y0, x1, y1],
    traces [{from, to, end (beat it disappears), bumps [[x, h, label], ...], every [x0, x1, step, h] (a rhythm), gold}],
    label (top left of the monitor)"""
    x0, y0, x1, y1 = s.get("box", [150, 900, 930, 1300]); base = (y0 + y1) / 2 + 60
    c = WHITE + (int(200 * a),)
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, outline=c, width=4)
    for i in range(1, 6):
        yy = y0 + (y1 - y0) * i / 6; d.line([x0 + 8, yy, x1 - 8, yy], fill=WHITE + (int(22 * a),), width=1)
    if s.get("label"): d.text((x0 + 24, y0 + 18), s["label"], font=font(22), fill=WHITE + (int(170 * a),))
    for tr in s.get("traces", []):
        tf, tt = T(tr["from"]), T(tr["to"])
        if t < tf or ("end" in tr and t >= T(tr["end"]) + .3): continue
        fade = cl(1 - (t - T(tr["end"])) / .3) if "end" in tr and t >= T(tr["end"]) else 1.0
        hx = x0 + 20 + (x1 - x0 - 40) * cl((t - tf) / max(.1, tt - tf))
        bumps = [list(b) for b in tr.get("bumps", [])]
        if "every" in tr:
            e0, e1, st, hh = tr["every"]; bumps += [[float(x), hh, None] for x in np.arange(e0, e1, st)]
        def yv(x):
            y = base
            for b in bumps:
                dx = x - b[0]; w = 14 if b[1] > 150 else 10
                y -= b[1] * math.exp(-(dx / w) ** 2) - .35 * b[1] * math.exp(-((dx - 2.2 * w) / w) ** 2)
            return y
        pts = [(x, yv(x)) for x in np.arange(x0 + 20, hx, 3)] + [(hx, yv(hx))]
        gold = ease((t - T(tr["gold"])) / .4) if "gold" in tr else 0
        for lay, col, al in ((d, WHITE, a * fade * (1 - gold)), (g, GOLD, a * fade * gold)):
            if al <= .01 or len(pts) < 2: continue
            lay.line(pts, fill=col + (int(245 * al),), width=5, joint="curve")
            lay.ellipse([hx - 10, pts[-1][1] - 10, hx + 10, pts[-1][1] + 10], fill=col + (int(255 * al),))
        for b in bumps:
            if b[2] and hx >= b[0]:
                k = (hx - b[0]) / 60; text_c(d, b[2], base - b[1] - 60, 30, a * fade * ease(k), cx=min(max(b[0], 260), 820), sp=4)

def shot_pillars(t, d, g, a, s):
    """the fifth statement: a beam on pillars (labels) that stand on nothing and shake; on every 'ground' beat one block of
    the ground slides in under them, when it is complete the shaking stops; gold on 'gold'. keys: labels [{text, beat}],
    shake [from, to] (beats), shake_amp (px, default 7), shake_speed (default 23), ground [beats], ground_label, base, top, gold"""
    base, top = s.get("base", 1260), s.get("top", 960); labs = s.get("labels", [])
    gold = ease((t - T(s["gold"])) / .4) if "gold" in s else 0
    gb = [T(b) for b in s.get("ground", [])]; built = sum(1 for b in gb if t >= b)
    sh = 0.0
    if "shake" in s:
        sf, st_ = T(s["shake"][0]), T(s["shake"][1])
        done = gb and t >= gb[-1]
        if sf <= t < st_ and not done: sh = math.sin(t * s.get("shake_speed", 23)) * s.get("shake_amp", 7) * (1 - built / max(1, len(gb)))
    n = max(1, len(labs)); x0, x1 = 190, 890; cw = (x1 - x0) / n
    for lay, col, al in ((d, WHITE, a * (1 - gold)), (g, GOLD, a * gold)):
        if al <= .01: continue
        c = col + (int(235 * al),)
        shown = [i for i, lb in enumerate(labs) if t >= T(lb["beat"])]
        if shown:
            ba = ease((t - T(labs[0]["beat"])) / .3)
            lay.rounded_rectangle([x0 - 20 + sh, top - 30, x0 - 20 + (x1 - x0 + 40) * ba + sh, top], radius=6, outline=c, width=4)
        for i in shown:
            q = ease((t - T(labs[i]["beat"])) / .25); cx = x0 + cw * (i + .5) + sh * (1.4 if i % 2 else -1.2)
            ph = (base - 30 - top) * q
            lay.rounded_rectangle([cx - 34, top, cx + 34, top + ph], radius=6, outline=c, width=4)
            if q > .8:
                # vertical label inside the pillar
                for j, ch in enumerate(labs[i]["text"]):
                    text_c(lay, ch, top + 24 + j * 34, 28, al * ease((q - .8) / .2), col=col, sp=0, cx=cx)
        # the ground: blocks slide in from the side, one per ground beat
        bw = (x1 - x0 + 80) / max(1, len(gb))
        for k, b in enumerate(gb):
            if t < b: continue
            q = ease((t - b) / .3); bx = x0 - 40 + k * bw
            off = (1 - q) * (-300 if k % 2 == 0 else 300)
            lay.rectangle([bx + off + 3, base - 22, bx + bw + off - 3, base + 22], outline=c, width=4)
        if built == len(gb) and gb and s.get("ground_label"):
            text_c(lay, s["ground_label"], base + 44, 34, al * ease((t - gb[-1] - .3) / .3), col=col, sp=10)
    if built < len(gb) or not gb:
        for x in range(150, 930, 34): d.line([x, base + 30, x + 16, base + 30], fill=WHITE + (int(70 * a),), width=3)
        if built == 0 and labs and t >= T(labs[-1]["beat"]): text_c(d, "?", base + 50, 70, a * (.4 + .2 * math.sin(t * 4)))

def shot_match(t, d, g, a, s):
    """knowledge without action: books stack up one per beat next to an unstruck match; at 'clear' the books fade, at
    'strike' the match is struck and a gold flame burns (sparks). keys: books [{beat, text}], counter (text before the
    count, e.g. "BOOKS READ: "), clear, stand (the match stands up), strike, base, mx (match x)"""
    base = s.get("base", 1280); mx = s.get("mx", 720)
    books = s.get("books", []); clear = T(s["clear"]) if "clear" in s else 1e9
    bf = 1 - ease((t - clear) / .5)
    d.line([150, base, 930, base], fill=WHITE + (int(160 * a),), width=3)
    if bf > .01:
        y = base
        for i, b in enumerate(books):
            if t < T(b["beat"]): continue
            q = ease((t - T(b["beat"])) / .2); h = 54; w = 300 - (i % 3) * 24; x = 330 + ((i * 37) % 3 - 1) * 14
            yy = y - h - (1 - q) * 300
            d.rounded_rectangle([x - w / 2, yy, x + w / 2, yy + h], radius=6, outline=WHITE + (int(230 * a * bf * q),), width=4)
            if b.get("text"): text_c(d, b["text"], yy + 13, 23, a * bf * q, cx=x, sp=3)
            y -= h + 5
        nb = sum(1 for b in books if t >= T(b["beat"]))
        if nb and s.get("counter"): text_c(d, f"{s['counter']}{nb * s.get('per', 1)}", base + 40, 28, a * bf * .85, sp=5, cx=330)
    st = ease((t - T(s["stand"])) / .4) if "stand" in s else 0
    strike = T(s["strike"]) if "strike" in s else 1e9; k = t - strike
    ang = math.radians(-90 * (1 - st) + (25 * math.sin(cl(k / .25) * math.pi) if k >= 0 else 0))
    L = 260; bx, by = mx, base
    tx, ty = bx + L * math.sin(ang), by - L * math.cos(ang)
    lit = k >= .15
    lay, col = (g, GOLD) if lit else (d, WHITE)
    lay.line([bx, by - 4, tx, ty], fill=col + (int(235 * a),), width=10)
    hx, hy = tx + 8 * math.sin(ang), ty - 8 * math.cos(ang)
    lay.ellipse([hx - 16, hy - 20, hx + 16, hy + 20], fill=col + (int(255 * a),))
    if lit:
        fl = ease((k - .15) / .4); fh = (160 + 16 * math.sin(t * 17) + 9 * math.sin(t * 29)) * fl
        cx, cy = hx, hy - 16
        pts = [(cx - 34 * fl, cy), (cx - 24 * fl, cy - fh * .5), (cx + 4 * math.sin(t * 13), cy - fh), (cx + 26 * fl, cy - fh * .45), (cx + 34 * fl, cy)]
        g.polygon(pts + [(cx, cy + 26 * fl)], fill=GOLD + (int(230 * a),))
        g.ellipse([cx - 14 * fl, cy - fh * .35, cx + 14 * fl, cy + 6], fill=(255, 240, 200, int(230 * a)))
        if k < .9:
            for j, (an, sp_) in enumerate(PARTS[:16]):
                rr = sp_ * .5 * ease(k / .9); x, y = cx + math.cos(an) * rr, cy + math.sin(an) * rr * .7
                g.ellipse([x - 5, y - 5, x + 5, y + 5], fill=GOLD + (int(255 * a * (1 - k / .9)),))


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

def punch_beats(spec):
    """camera punches: "punch": "drop" = every beat from the drop until the breakdown, or a list of beats"""
    p = spec.get("punch")
    if p == "drop": return [b for b in range(DROP_BEAT, len(GRID)) if GRID[b] < BREAK_T - .1]
    return list(p or [])

def punch_zoom(t, spec):
    z = 1.0
    for b in punch_beats(spec):
        k = t - T(b)
        if 0 <= k < .5: z = max(z, 1 + spec.get("punch_amount", .035) * math.exp(-k * 9))
    return z

def frame(t, spec, LEN):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
    for s in spec["shots"]:
        t0, t1 = T(s["from"]), T(s["to"]) if "to" in s else LEN + 1
        a = win(t, t0, t1, fi=s.get("fade_in", .03), fo=s.get("fade_out", .12)) if t0 > 0 else cl((t1 - t) / s.get("fade_out", .12))
        if a > 0: SHOTS[s["type"]](t, d, g, a, s)
    draw_text(t, d, g, spec, LEN)
    cq = spec.get("comment_q")
    if cq and t >= T(cq["from"]):
        k = t - T(cq["from"]); sc_ = 1 + .25 * math.exp(-k * 12)
        big(d, cq["text"], cq.get("y", 560), int(cq.get("size", 52) * sc_), ease(k / .15), maxw=780)
    lay.alpha_composite(gl)
    glow = lay.resize((W // 2, H // 2)).filter(ImageFilter.GaussianBlur(9)).resize((W, H))
    im = BG.convert("RGBA"); im.alpha_composite(glow); im.alpha_composite(glow); im.alpha_composite(lay)
    z = punch_zoom(t, spec)
    if z > 1.0005:
        w2, h2 = int(W * z), int(H * z); im = im.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
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
        a, sr = k.create(ln["text"], voice=spec.get("voice", "am_michael"), speed=ln.get("speed", spec.get("speed", 1.05)), lang="en-us")
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
    if spec.get("sound"): load_sound(spec["sound"])
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
