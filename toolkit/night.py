"""Night footage videos with the warm voice (2026-11-18, Adriaan: "make it more realistic", night footage, no AI video yet).

Real night clips from clips/ cut on the VYZEE beat grid, the warm voice (vyzee.voice_track) and the same big glowing
text as vyzee.py. Intro desaturated and dark, colour comes back on the drop, a gold line at the end.

Usage:  python3 toolkit/night.py SPEC.json OUT.mp4 [--preview 0.5,17.3,30]
Spec: everything vyzee.py takes for "lines", "text", "length", "sound", "speed", "pitch", "voice_fx", plus
  cuts   [{"from": beat, "clip": "pex-35147217.mp4", "start": seconds into the clip (default 1), "sat": 0..1 (colour,
          default 1), "dark": 0..1 (default 0), "speed": playback speed (default 1)}]  each cut runs until the next one
  shade  how dark the top band behind the text is (default .75)
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vyzee as V

LC = os.path.dirname(V.TK)

def build_base(spec, LEN, out):
    cuts = spec["cuts"]; tmp = tempfile.mkdtemp(); parts = []
    for i, c in enumerate(cuts):
        t0 = V.T(c["from"]); t1 = V.T(cuts[i + 1]["from"]) if i + 1 < len(cuts) else LEN
        dur = t1 - t0; sp = c.get("speed", 1.0); sat = c.get("sat", 1.0); dark = c.get("dark", 0.0)
        src = os.path.join(LC, "clips", c["clip"]); p = os.path.join(tmp, f"{i:02d}.mp4")
        vf = (f"setpts=PTS/{sp},scale={V.W}:{V.H}:force_original_aspect_ratio=increase,crop={V.W}:{V.H},fps={V.FPS},"
              f"eq=saturation={sat}:brightness={-0.08 * dark}:gamma={1 - 0.2 * dark}:contrast=1.08,"
              f"trim=duration={dur:.3f},setpts=PTS-STARTPTS")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c.get("start", 1.0)), "-i", src, "-an", "-vf", vf,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)

def shade_layer(k):
    """dark band at the top behind the text plus a soft vignette"""
    yy, xx = np.mgrid[0:V.H, 0:V.W]
    top = np.clip(1 - (yy - 150) / 650, 0, 1) * k
    vig = np.clip(np.sqrt(((xx - 540) / 760) ** 2 + ((yy - 960) / 1250) ** 2) - .55, 0, 1) * .8
    a = np.clip(np.maximum(top, vig), 0, .92)
    return Image.fromarray((a * 255).astype(np.uint8), "L")

def overlay(t, base, spec, LEN, shade):
    im = base.convert("RGBA")
    im = Image.composite(Image.new("RGBA", im.size, (0, 0, 0, 255)), im, shade)
    lay = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    gl = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
    V.draw_text(t, d, g, spec, LEN)
    lay.alpha_composite(gl)
    glow = lay.resize((V.W // 2, V.H // 2)).filter(ImageFilter.GaussianBlur(8)).resize((V.W, V.H))
    im.alpha_composite(glow); im.alpha_composite(lay)
    return im.convert("RGB")

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; LEN = float(spec.get("length", 30))
    if spec.get("sound"): V.load_sound(spec["sound"])
    base = out.replace(".mp4", ".base.mp4"); build_base(spec, LEN, base)
    shade = shade_layer(spec.get("shade", .75))
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = int(LEN * V.FPS); fsz = V.W * V.H * 3
    prev = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[3] == "--preview" else None
    if prev:
        want = {int(p * V.FPS): p for p in prev}
        for i in range(n):
            buf = rd.stdout.read(fsz)
            if len(buf) < fsz: break
            if i in want:
                fr = Image.frombytes("RGB", (V.W, V.H), buf)
                overlay(i / V.FPS, fr, spec, LEN, shade).save(out.replace(".mp4", f"_{want[i]:05.2f}.png"))
        rd.kill(); os.remove(base); return
    wav = out.replace(".mp4", ".voice.wav"); V.voice_track(spec, LEN, wav)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{V.W}x{V.H}", "-r", str(V.FPS),
                           "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k", "-af", "apad", "-t", f"{LEN}", out],
                          stdin=subprocess.PIPE)
    last = None
    for i in range(n):
        buf = rd.stdout.read(fsz)
        if len(buf) == fsz: last = buf
        fr = Image.frombytes("RGB", (V.W, V.H), last)
        ff.stdin.write(overlay(i / V.FPS, fr, spec, LEN, shade).tobytes())
    ff.stdin.close(); ff.wait(); rd.kill(); rd.wait(); os.remove(wav); os.remove(base); print("done", out)

if __name__ == "__main__":
    main()
