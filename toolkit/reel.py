"""Ladder Reel builder: night footage + small left aligned text on a 60 BPM grid.

Usage:  python3 reel.py specs/my_video.json
Output: ../out/<name>.mp4  (inside ladder-content/out)

Spec (JSON):
{
  "name": "ladder-reel-17",
  "clip": "clips/ladder-src-13.mp4",      # path relative to ladder-content, or absolute
  "mode": "loop",                         # loop | book | pingpong
  "y0": 560,                              # y of the first text line (1920 tall frame)
  "top": true,                            # darken the top of the frame (good for skies)
  "blob": 0.45,                           # strength of the soft dark patch behind the text
  "pre": "",                              # optional extra ffmpeg filter, e.g. "eq=gamma=0.75,"
  "minlen": 4,                            # minimum beats per block
  "blocks": [
    [["Everyone wants the result."], ["Almost no one wants the price.", "gold"]],
    [["You priced the destination"], ["but never the road.", "gold"]]
  ]
}
Each block is one screen of text. The line marked "gold" is the punch line: it lands one beat later,
in yellow, and the lines above it dim. The last block holds until the loop restarts.
"""
import json, os, subprocess, sys

TK = os.path.dirname(os.path.abspath(__file__))
LC = os.path.dirname(TK)                      # ladder-content
FPS, XF, OUTRO = 30, 0.6, 7
FONTS = os.path.join(TK, "fonts")

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
    m, sec = divmod(s, 60)
    return f"0:{int(m):02d}:{sec:05.2f}"

def script(blocks, y0=560, minlen=5):
    ev, t, plans = [], 0.0, []
    for bi, blk in enumerate(blocks):
        times, beat = [], 0
        for ln in blk:
            if len(ln) > 1:
                beat += 1
            times.append(beat); beat += 1
        gold_t = times[-1]
        length = max(minlen, gold_t + 2) + (1 if bi == len(blocks) - 1 else 0)
        plans.append((blk, times, gold_t, length))
    total = sum(p[3] for p in plans)
    for bi, (blk, times, gold_t, length) in enumerate(plans):
        last = bi == len(plans) - 1
        y = y0
        for i, (ln, bt) in enumerate(zip(blk, times)):
            gold = len(ln) > 1
            if i > 0:
                y += 92 if gold else 62
            s, e = t + bt, t + length
            fin = 0 if (bi == 0 and i == 0) else 250
            fout = 0 if last else 300
            tags = f"\\pos(96,{y})\\fad({fin},{fout})"
            if not gold:
                a = int((t + gold_t - s) * 1000)
                tags += f"\\t({a},{a+400},\\1a&H60&\\4a&HB0&)"
            ev.append((s, e, "Gold" if gold else "Body", tags, ln[0]))
        t += length
    return ev, total

def grade(pre="", blob=0.55, by=690, top=True):
    topf = "(0.66+0.34*min(1,max(0,(Y-200)/900)))" if top else "1"
    return (f"{pre}eq=saturation=0.3:contrast=1.08:brightness=-0.01,"
            f"geq=lum='lum(X,Y)*{topf}*(1-{blob}*exp(-2*(pow((X-420)/560,2)+pow((Y-{by})/260,2))))':cb='cb(X,Y)':cr='cr(X,Y)',"
            "vignette=PI/6,noise=alls=3:allf=t")

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)

def build(spec_path):
    v = json.load(open(spec_path))
    name = v["name"]
    clip = v["clip"] if os.path.isabs(v["clip"]) else os.path.join(LC, v["clip"])
    L = v.get("len") or duration(clip)
    mode = v.get("mode", "loop")
    y0, minlen = v.get("y0", 560), v.get("minlen", 5)
    GRADE = grade(v.get("pre", ""), v.get("blob", 0.55), y0 + 130, v.get("top", True))
    ev, T = script(v["blocks"], y0, minlen)
    total = T + (OUTRO if mode == "book" else 0)
    if mode == "book":
        ev += [(T + 1, total, "CBody", "\\pos(540,250)\\fad(500,0)", "The book behind these words."),
               (T + 3, total, "CGold", "\\pos(540,1390)\\fad(300,0)", "Comment BOOK"),
               (T + 4, total, "CBody", "\\pos(540,1466)\\fad(300,0)", "and I'll send it to you.")]
    os.makedirs(os.path.join(LC, "out"), exist_ok=True)
    ass = os.path.join(LC, "out", f"{name}.ass")
    lines = [f"Dialogue: 0,{ts(s)},{ts(e)},{st},,0,0,0,,{{{tg}}}{tx}" for s, e, st, tg, tx in ev]
    open(ass, "w").write(HEAD + "\n".join(lines) + "\n")

    prep = "[0:v]scale=1080:1920:flags=lanczos,setsar=1"
    if mode == "pingpong":
        slow = max(1.0, T / (2 * L))
        fc = (f"{prep},setpts={slow:.4f}*PTS,framerate={FPS},split[f][r];[r]reverse[rv];"
              f"[f][rv]concat=n=2:v=1:a=0,trim=0:{T},setpts=PTS-STARTPTS,{GRADE}[v]")
    elif mode == "loop":
        slow = max(1.0, (T + XF) / (L - 0.1))
        fc = (f"{prep},setpts={slow:.4f}*PTS,framerate={FPS},trim=0:{L * slow - 0.05:.3f},setpts=PTS-STARTPTS,split[a][b];"
              f"[a]trim={XF}:{XF + T},setpts=PTS-STARTPTS[m];[b]trim=0:{XF},setpts=PTS-STARTPTS[h];"
              f"[m][h]xfade=transition=fade:duration={XF}:offset={T - XF},{GRADE}[v]")
    else:
        need = T + 1.0
        slow = max(1.0, need / (L - 0.1))
        fc = (f"{prep},setpts={slow:.4f}*PTS,framerate={FPS},trim=0:{need},setpts=PTS-STARTPTS,"
              f"{GRADE},fade=t=out:st={T}:d=1,format=yuv420p[foot];"
              f"[1:v]trim=0:{OUTRO - 1.0},setpts=PTS-STARTPTS,"
              f"zoompan=z='1+0.05*on/({OUTRO}*{FPS})':x='iw/2-(iw/zoom/2)':y='max(0,min(ih-ih/zoom,1650-ih/zoom/2))':d=1:s=1080x1920:fps={FPS},"
              f"noise=alls=2:allf=t,fade=t=in:st=0.1:d=1.0,format=yuv420p[o];[foot][o]concat=n=2:v=1:a=0[v]")
    fc += f";[v]ass='{ass}':fontsdir='{FONTS}',format=yuv420p[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", clip]
    if mode == "book":
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", os.path.join(TK, "assets", "outro_still.png")]
    out = os.path.join(LC, "out", f"{name}.mp4")
    cmd += ["-filter_complex", fc, "-map", "[out]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.2",
            "-maxrate", "8M", "-bufsize", "16M", "-r", str(FPS), "-g", "60", "-an", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"{name}: mode {mode}, text {T}s, total {total}s -> {out}", flush=True)

if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
