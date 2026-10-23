"""Render The Ladder reels from a day spec.

    python3 -I tools/render.py <repo_root> <spec.json> <out_dir> [id ...]

spec.json is a list of videos:
  {"id": "2026-10-24-1",
   "clip": "clips/night-highway-36601677.mp4",
   "mode": "loop" | "book",
   "y0": 330,            # y of the first line (330 = upper sky, 1180 = lower third)
   "blob": 0.45,         # how much the text area is darkened (0.3 for dark clips, 0.55 for bright)
   "pre": "",            # optional extra ffmpeg filters before the grade, e.g. "eq=gamma=0.72:brightness=-0.06,"
   "minlen": 4,          # minimum seconds per block
   "blocks": [[["line"], ["line"], ["gold line", true]], ...]}

Style (agreed with Adriaan): 1080x1920, 30 fps, desaturated night footage, small Inter text
left aligned at x=96, the last line of every block in gold and one beat later, earlier lines dim
when the gold line lands, 60 BPM grid (1 beat = 1 second), no audio (music is added in the app).
loop = text then a seamless crossfade back into the first frame.
book = text, fade to black, 3D book outro with "Comment BOOK".
"""
import json, os, subprocess, sys

ROOT, SPEC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ONLY = set(sys.argv[4:])
FPS, XF, OUTRO = 30, 1.0, 6.0
A = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Body,Inter Medium,48,&H00E1E6E8,&H00E1E6E8,&H00000000,&H50000000,0,0,0,0,100,100,0.4,0,1,0,3,7,96,96,0,1
Style: Gold,Inter SemiBold,48,&H0042C5F5,&H0042C5F5,&H00000000,&H50000000,0,0,0,0,100,100,0.4,0,1,0,3,7,96,96,0,1
Style: CGold,Inter SemiBold,56,&H0042C5F5,&H0042C5F5,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,8,60,60,0,1
Style: CBody,Inter Medium,36,&H00A0A4A6,&H00A0A4A6,&H00000000,&H00000000,0,0,0,0,100,100,0.5,0,1,0,0,8,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(s):
    m, sec = divmod(max(0.0, s), 60)
    return f"0:{int(m):02d}:{sec:05.2f}"


def script(blocks, y0=560, minlen=5):
    """Lay lines on the 60 BPM grid. Returns (events, text_length)."""
    plans = []
    for bi, blk in enumerate(blocks):
        times, beat = [], 0
        for ln in blk:
            gold = len(ln) > 1 and ln[1]
            if gold:
                beat += 1          # gold line lands one beat later
            times.append(beat); beat += 1
        gold_t = times[-1]
        length = max(minlen, gold_t + 2) + (1 if bi == len(blocks) - 1 else 0)
        plans.append((blk, times, gold_t, length))
    ev, t = [], 0.0
    for bi, (blk, times, gold_t, length) in enumerate(plans):
        last = bi == len(plans) - 1
        y = y0
        for i, (ln, bt) in enumerate(zip(blk, times)):
            gold = len(ln) > 1 and ln[1]
            if i > 0:
                y += 92 if gold else 62
            s, e = t + bt, t + length
            fin = 0 if (bi == 0 and i == 0) else 250   # first frame already shows the hook
            fout = 0 if last else 300
            tags = f"\\pos(96,{y})\\fad({fin},{fout})"
            if not gold:
                a = int((t + gold_t - s) * 1000)
                tags += f"\\t({a},{a + 400},\\1a&H60&\\4a&HB0&)"
            ev.append((s, e, "Gold" if gold else "Body", tags, ln[0]))
        t += length
    return ev, t


def grade(pre="", blob=0.55, y0=560):
    cy = y0 + 130
    return (f"{pre}eq=saturation=0.3:contrast=1.08:brightness=-0.01,"
            f"geq=lum='lum(X,Y)*(0.66+0.34*min(1,max(0,(Y-200)/900)))*(1-{blob}*exp(-2*(pow((X-420)/560,2)+pow((Y-{cy})/260,2))))':cb='cb(X,Y)':cr='cr(X,Y)',"
            "vignette=PI/6,noise=alls=3:allf=t")


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout.strip())


def build(v):
    key, mode = v["id"], v.get("mode", "loop")
    y0 = v.get("y0", 330)
    ev, T = script(v["blocks"], y0, v.get("minlen", 4))
    total = T + (OUTRO if mode == "book" else 0)
    if mode == "book":
        ev += [(T + 1, total, "CBody", "\\pos(540,250)\\fad(500,0)", "The book behind these words."),
               (T + 3, total, "CGold", "\\pos(540,1390)\\fad(300,0)", "Comment BOOK"),
               (T + 4, total, "CBody", "\\pos(540,1466)\\fad(300,0)", "and I'll send it to you.")]
    ass = os.path.join(OUT, f"{key}.ass")
    with open(ass, "w") as f:
        f.write(HEAD + "\n".join(f"Dialogue: 0,{ts(s)},{ts(e)},{st},,0,0,0,,{{{tg}}}{tx}" for s, e, st, tg, tx in ev) + "\n")

    src = os.path.join(ROOT, v["clip"])
    L = duration(src)
    G = grade(v.get("pre", ""), v.get("blob", 0.45), y0)
    prep = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1"
    if mode == "loop":
        need = T + XF
        slow = max(1.0, need / (L - 0.1))
        sl = L * slow
        fc = (f"{prep},setpts={slow:.4f}*PTS,framerate={FPS},trim=0:{sl - 0.05:.3f},setpts=PTS-STARTPTS,split[a][b];"
              f"[a]trim={XF}:{XF + T},setpts=PTS-STARTPTS[m];[b]trim=0:{XF},setpts=PTS-STARTPTS[h];"
              f"[m][h]xfade=transition=fade:duration={XF}:offset={T - XF},{G}[v]")
    else:
        need = T + 1.0
        slow = max(1.0, need / (L - 0.1))
        fc = (f"{prep},setpts={slow:.4f}*PTS,framerate={FPS},trim=0:{need},setpts=PTS-STARTPTS,"
              f"{G},fade=t=out:st={T}:d=1,format=yuv420p[foot];"
              f"[1:v]trim=0:{OUTRO - 1.0},setpts=PTS-STARTPTS,"
              f"zoompan=z='1+0.05*on/({OUTRO}*{FPS})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
              f"noise=alls=2:allf=t,fade=t=in:st=0.1:d=1.0,format=yuv420p[o];[foot][o]concat=n=2:v=1:a=0[v]")
    fc += f";[v]ass={ass},format=yuv420p[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
    if mode == "book":
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", os.path.join(A, "outro_still.png")]
    out = os.path.join(OUT, f"{key}.mp4")
    cmd += ["-filter_complex", fc, "-map", "[out]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high", "-level", "4.2",
            "-maxrate", "8M", "-bufsize", "16M", "-r", str(FPS), "-g", "60", "-an", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    os.remove(ass)
    print(key, mode, f"{total:.1f}s", out, flush=True)


for v in json.load(open(SPEC)):
    if not ONLY or v["id"] in ONLY:
        build(v)
