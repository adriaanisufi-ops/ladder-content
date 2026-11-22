"""Two people talking, ANIMATED in glowing lines (Adriaan 2026-11-22: "maak het geanimeerd", style: glowing lines
like "Price Tags"). Same spec as story.py (names, lines, end, length) plus "scene": bench | kitchen | car.

The scene sits under the dialog: white glowing line figures in the rain, cold and still while the conversation is
stuck. On "warm" (default 17.2 s, the drop, the sting line) the rain stops, the lines turn gold and the one small
gesture happens (a hand on the shoulder, dad turns his head, you walk up to grandma's door). No voice, no music:
a soft rain bed only, Adriaan adds the song in TikTok.

Usage:  python3 toolkit/story_anim.py SPEC.json OUT.mp4 [--preview 0.1,10,17.6,26]
Extra spec keys: scene, warm (seconds, default 17.2), text_y (default 520: dialog above the scene)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vyzee as V
import story as S

W, H, FPS = V.W, V.H, V.FPS
WHITE, GOLD = V.WHITE, V.GOLD
cl, ease = S.cl, S.ease

def mix(c1, c2, k): return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))
def lerp(a, b, k): return a + (b - a) * k
def sm(x): x = cl(x); return x * x * (3 - 2 * x)

def C(w, al): return mix(WHITE, GOLD, w) + (int(255 * cl(al)),)

def seated(d, hip, col, lean=0.0, head_drop=0.0, head_turn=0.0, hand=None, facing=1, s=1.0, w=11):
    """a seated line figure: hip point, torso up, head, thigh forward, shin down, one arm to `hand`"""
    hx, hy = hip
    sh = (hx + (lean * 40 + 6) * facing * s, hy - 118 * s)
    head = (sh[0] + (head_turn * 22 + head_drop * 22) * facing * s, sh[1] - (52 - head_drop * 18) * s)
    knee = (hx + 92 * facing * s, hy + 4 * s); foot = (hx + 96 * facing * s, hy + 104 * s)
    d.line([hip, sh], fill=col, width=w)
    d.line([hip, knee, foot], fill=col, width=w, joint="curve")
    hand = hand or (hx + 70 * facing * s, hy - 30 * s)
    elbow = ((sh[0] + hand[0]) / 2 + 6 * facing, (sh[1] + hand[1]) / 2 + 30 * s)
    d.line([sh, elbow, hand], fill=col, width=w - 1, joint="curve")
    r = 27 * s; d.ellipse([head[0] - r, head[1] - r, head[0] + r, head[1] + r], fill=col)
    return sh, head

def standing(d, x, yf, col, step=0.0, s=1.0, w=11):
    hip = (x, yf - 105 * s); sh = (x, yf - 220 * s); head = (x, yf - 275 * s)
    sw = math.sin(step) * 26 * s
    d.line([hip, sh], fill=col, width=w); d.line([(x - 34, sh[1] + 6), (x + 34, sh[1] + 6)], fill=col, width=w)
    d.line([hip, (x + sw, yf)], fill=col, width=w); d.line([hip, (x - sw, yf)], fill=col, width=w)
    d.line([(x - 36, sh[1] + 8), (x - 44, hip[1] + 10)], fill=col, width=w - 1); d.line([(x + 36, sh[1] + 8), (x + 44, hip[1] + 10)], fill=col, width=w - 1)
    r = 27 * s; d.ellipse([head[0] - r, head[1] - r, head[0] + r, head[1] + r], fill=col)

def rain(d, t, a):
    if a <= .01: return
    rng = np.random.default_rng(7)
    xs = rng.uniform(-100, W + 100, 140); ys = rng.uniform(0, H, 140); sp = rng.uniform(900, 1400, 140); ln = rng.uniform(26, 60, 140)
    for x, y0, v, L in zip(xs, ys, sp, ln):
        y = (y0 + v * t) % (H + 200) - 100; x2 = x - .18 * (y)
        d.line([(x2, y), (x2 - .18 * L, y + L)], fill=(200, 210, 225, int(70 * a)), width=2)

# ------------------------------------------------------------------ scenes
def front(d, x, seat, col, head_dx=0.0, head_dy=0.0, lhand=None, rhand=None, w=11):
    """a seated figure seen from the front: hips on the seat, legs down, shoulders, head (offset by head_dx/dy)"""
    sh_y = seat - 125; hl, hr = (x - 20, seat), (x + 20, seat)
    d.line([(x, seat), (x, sh_y)], fill=col, width=w)
    d.line([(x - 34, sh_y + 6), (x + 34, sh_y + 6)], fill=col, width=w)
    d.line([hl, (x - 24, seat + 105)], fill=col, width=w); d.line([hr, (x + 24, seat + 105)], fill=col, width=w)
    d.line([(x - 36, sh_y + 8), lhand or (x - 14, seat - 22)], fill=col, width=w - 1, joint="curve")
    d.line([(x + 36, sh_y + 8), rhand or (x + 14, seat - 22)], fill=col, width=w - 1, joint="curve")
    hx, hy = x + head_dx, sh_y - 50 + head_dy; r = 28
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=col)
    return (hx, hy)

def scene_bench(t, d, g, w, spec):
    """two friends on a bench under a street lamp, seen from the front. you look down at your phone, the friend
    looks at you. warm: the lamp turns gold, the friend's arm goes around your shoulder, your head comes up"""
    base = 1330; c = C(w, .95)
    d.line([(220, base), (220, 900), (285, 872)], fill=C(w, .8), width=8, joint="curve")
    lamp = (300, 884)
    g.ellipse([lamp[0] - 20, lamp[1] - 8, lamp[0] + 20, lamp[1] + 14], fill=C(w, .9))
    cone = Image.new("L", (W, H), 0); cd = ImageDraw.Draw(cone)
    cd.polygon([(lamp[0] - 18, lamp[1] + 10), (lamp[0] + 18, lamp[1] + 10), (lamp[0] + 330, base), (lamp[0] - 160, base)], fill=int(35 + 45 * w))
    spec["_cone"] = cone.filter(ImageFilter.GaussianBlur(30))
    d.line([(120, base), (960, base)], fill=C(w, .55), width=4)
    seat = 1225
    d.line([(360, seat), (800, seat)], fill=c, width=9)
    d.line([(380, seat), (380, base)], fill=c, width=7); d.line([(780, seat), (780, base)], fill=c, width=7)
    gest = sm((t - spec["_warm"] - .2) / 1.4); up = sm((t - spec["_warm"] - .9) / 1.2)
    # you (right): head bowed over the phone, comes up and leans to the friend on warm
    yx = 640
    ph = (yx, lerp(seat - 40, seat - 30, up))
    yh = front(d, yx, seat, c, head_dx=lerp(0, -14, up), head_dy=lerp(34, 4, up), lhand=(yx - 10, ph[1] + 4), rhand=(yx + 10, ph[1] + 4))
    # friend (left): head turned to you; on warm the right arm goes around your shoulders
    fx = 500
    arm = (lerp(fx + 14, yx + 40, gest), lerp(seat - 22, seat - 128, gest))
    front(d, fx, seat, c, head_dx=10 + 6 * gest, head_dy=4 * gest, rhand=arm)
    pa = (1 - up) * (.8 + .2 * math.sin(t * 2))
    if pa > .02:
        g.rounded_rectangle([ph[0] - 22, ph[1] - 14, ph[0] + 22, ph[1] + 12], radius=5, fill=(150, 190, 255, int(220 * pa)))
        g.polygon([(ph[0] - 20, ph[1] - 14), (ph[0] + 20, ph[1] - 14), (yh[0] + 26, yh[1] + 20), (yh[0] - 26, yh[1] + 20)], fill=(150, 190, 255, int(14 * pa)))

def scene_kitchen(t, d, g, w, spec):
    """grandma alone at the kitchen table by the window, two plates, one empty chair, a phone that lights up and
    goes dark. warm: the room turns gold and you appear in the door"""
    base = 1360; c = C(w, .95)
    # room: window frame on the left, door on the right
    d.rectangle([150, 890, 400, 1130], outline=C(w, .7), width=6)
    d.line([(275, 890), (275, 1130)], fill=C(w, .5), width=4); d.line([(150, 1010), (400, 1010)], fill=C(w, .5), width=4)
    # moon in the window (cold), becomes a warm lamp later
    g.ellipse([320, 915, 360, 955], fill=C(w, .5 * (1 - w)))
    d.rectangle([740, 900, 900, base], outline=C(w, .7), width=6)
    d.line([(120, base), (960, base)], fill=C(w, .55), width=4)
    # door opens on warm, light spills, you stand in it
    op = sm((t - spec["_warm"] - 3.6) / 1.2)
    if op > 0:
        g.polygon([(746, 906), (894, 906), (894, base - 4), (746, base - 4)], fill=GOLD + (int(70 * op),))
        g.polygon([(746, base), (894, base), (950, base + 60), (690, base + 60)], fill=GOLD + (int(40 * op),))
        standing(g, 820, base - 6, GOLD + (int(255 * op),), step=.45, s=.9)
    # table
    d.line([(390, 1180), (670, 1180)], fill=c, width=9)
    d.line([(420, 1180), (420, base)], fill=c, width=7); d.line([(645, 1180), (645, base)], fill=c, width=7)
    # plates
    for px in (470, 610):
        d.ellipse([px - 42, 1162, px + 42, 1176], outline=c, width=4)
    # grandma (left), slightly bent, head a bit down; looks at the door on warm
    look = sm((t - spec["_warm"] - 3.8) / 1.0)
    seated(d, (360, 1240), c, lean=.35, head_drop=.6 * (1 - look), head_turn=.8 * look, hand=(440, 1172), facing=1, s=1.0)
    # empty chair (right)
    ch = C(w, .75)
    d.line([(705, 1250), (630, 1250)], fill=ch, width=7); d.line([(705, 1250), (705, 1080)], fill=ch, width=7)
    d.line([(630, 1250), (630, base)], fill=ch, width=6); d.line([(705, 1250), (705, base)], fill=ch, width=6)
    # phone on the table buzzing at the start (her calling you), then dark
    ring = cl(1 - abs(((t % 3.0) - .4)) / .4) if t < 9 else 0
    if ring > 0:
        jx = math.sin(t * 60) * 3 * ring
        g.rounded_rectangle([540 + jx, 1160, 580 + jx, 1176], radius=4, fill=(150, 190, 255, int(230 * ring)))
    d.rounded_rectangle([540, 1160, 580, 1176], radius=4, outline=c, width=3)

def scene_car(t, d, g, w, spec):
    """dad and you in a parked car outside the house at night, both looking ahead. warm: dad turns his head to you
    and puts his hand on your head, the porch light turns gold"""
    base = 1360; c = C(w, .95)
    # house behind with a porch light
    d.line([(620, 1010), (620, 930), (740, 860), (860, 930), (860, 1010)], fill=C(w, .45), width=5, joint="curve")
    pl = .5 + .5 * w
    g.ellipse([725, 950, 755, 980], fill=C(w, .5 * pl + .2))
    # car body (side view), windows
    d.line([(165, 1290), (165, 1210), (250, 1190), (335, 1010), (690, 1010), (790, 1180), (915, 1200), (915, 1290)],
           fill=c, width=8, joint="curve")
    d.line([(165, 1290), (915, 1290)], fill=c, width=8)
    for wx in (290, 785):
        d.ellipse([wx - 62, 1238, wx + 62, 1362], outline=c, width=8); d.ellipse([wx - 18, 1282, wx + 18, 1318], fill=c)
    d.line([(510, 1018), (510, 1190)], fill=C(w, .6), width=5)
    d.line([(345, 1024), (680, 1024)], fill=C(w, .3), width=3)
    # you (left seat, back), dad (right seat, driver, facing right = forward)
    turn = sm((t - spec["_warm"] - .1) / 1.1); reach = sm((t - spec["_warm"] - 1.6) / 1.3)
    you_head_turn = sm((t - spec["_warm"] - 2.2) / 1.0)
    _, yh = seated(d, (390, 1250), c, lean=.05, head_drop=.5, head_turn=-.5 * you_head_turn, hand=(460, 1210), facing=1, s=.95)
    dad_hand = (lerp(700, yh[0] + 30, reach), lerp(1150, yh[1] - 16, reach))
    seated(d, (600, 1250), c, lean=.1, head_turn=lerp(.4, -1.0, turn), hand=dad_hand, facing=1, s=1.05)
    d.line([(690, 1130), (705, 1185)], fill=C(w, .6), width=6)   # steering wheel

SCENES = {"bench": scene_bench, "kitchen": scene_kitchen, "car": scene_car}

# ------------------------------------------------------------------ render
yy, xx = np.mgrid[0:H, 0:W]
_dist = np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 1000) / 1100) ** 2)
BG_COLD = Image.fromarray(np.dstack([np.clip(22 * (1 - _dist), 0, 22) + 4, np.clip(24 * (1 - _dist), 0, 24) + 5,
                                     np.clip(30 * (1 - _dist), 0, 30) + 8]).astype(np.uint8))
BG_WARM = Image.fromarray(np.dstack([np.clip(46 * (1 - _dist), 0, 46) + 6, np.clip(30 * (1 - _dist), 0, 30) + 4,
                                     np.clip(12 * (1 - _dist), 0, 12) + 3]).astype(np.uint8))

def frame(t, spec, LEN):
    warm = spec["_warm"]; w = sm((t - warm) / .8)
    bg = Image.blend(BG_COLD, BG_WARM, w).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
    spec["_cone"] = None
    SCENES[spec["scene"]](t, d, g, w, spec)
    rain(d, t, 1 - sm((t - warm) / 1.5))
    lay.alpha_composite(gl)
    # slow push in on the scene (the text stays put)
    z = {"bench": 1.18, "kitchen": 1.06, "car": 1.0}[spec["scene"]] + .05 * t / LEN; w2, h2 = int(W * z), int(H * z); cy = 1390
    lay = lay.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, int(cy * z - cy), (w2 - W) // 2 + W, int(cy * z - cy) + H))
    if spec.get("_cone") is not None:
        cone = spec["_cone"]
        bg = Image.composite(Image.new("RGBA", (W, H), mix((180, 190, 210), GOLD, w) + (255,)), bg, cone)
    # dialog
    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    S.draw(t, ImageDraw.Draw(tl), ImageDraw.Draw(tg), spec, LEN)
    tl.alpha_composite(tg); lay.alpha_composite(tl)
    glow = lay.resize((W // 2, H // 2)).filter(ImageFilter.GaussianBlur(9)).resize((W, H))
    bg.alpha_composite(glow); bg.alpha_composite(glow); bg.alpha_composite(lay)
    gr = V.GRAIN[int(t * FPS) % 6]
    return Image.blend(bg.convert("RGB"), Image.merge("RGB", (gr, gr, gr)), 0.03)

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; LEN = float(spec.get("length", 27))
    spec["_warm"] = float(spec.get("warm", 17.2)); spec.setdefault("text_y", 560)
    if len(sys.argv) > 4 and sys.argv[3] == "--preview":
        for t in [float(x) for x in sys.argv[4].split(",")]: frame(t, spec, LEN).save(out.replace(".mp4", f"_{t:05.2f}.png"))
        return
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.02:d={LEN},lowpass=f=900,volume={spec.get('rain', .45)},afade=t=in:d=1,"
                           f"afade=t=out:st={spec['_warm']}:d=1.5",
                           "-map", "0:v", "-map", "1:a", "-vf", "hqdn3d=3:3:6:6", "-c:v", "libx264", "-preset", "medium", "-crf", "24",   # rain + grain blow up the size (60 MB at crf 21)
                            "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", "-t", f"{LEN}", out], stdin=subprocess.PIPE)
    for i in range(int(LEN * FPS)): ff.stdin.write(frame(i / FPS, spec, LEN).tobytes())
    ff.stdin.close(); ff.wait(); print("done", out)

if __name__ == "__main__":
    main()
