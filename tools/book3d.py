"""Build assets/outro_still.png: the 3D book on black with a soft gold glow.
Run once (or whenever the cover changes):  python3 -I tools/book3d.py <repo_root>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
A = os.path.join(ROOT, "assets")
SS = 2

cover = Image.open(os.path.join(A, "cover.jpg")).convert("RGB")
# author name removed from the cover (Adriaan asked for this)
ImageDraw.Draw(cover).rectangle([0, 1424, cover.width, 1486], fill=(250, 245, 239))


def coeffs(dst, src):
    M, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        M.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        M.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(M, float), np.array(B, float)).tolist()


def warp(img, quad, size):
    w, h = img.size
    out = img.convert("RGBA").transform(size, Image.PERSPECTIVE,
                                        coeffs(quad, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(quad, fill=255)
    out.putalpha(mask)
    return out


CW, CH = 1000 * SS, 1300 * SS
s = lambda pts: [(x * SS, y * SS) for x, y in pts]
front = s([(250, 120), (810, 165), (810, 1105), (250, 1150)])
spine = s([(186, 150), (250, 120), (250, 1150), (186, 1120)])

book = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
sh = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(sh).ellipse(s([(170, 1110), (880, 1200)]), fill=190)
sh = sh.filter(ImageFilter.GaussianBlur(28 * SS))
book.paste((0, 0, 0, 255), (0, 0), sh)

sp = Image.new("RGB", (120, 2550), (214, 206, 194))
ImageDraw.Draw(sp).rectangle([0, 980, 120, 1100], fill=(150, 58, 40))
grad = np.linspace(0.62, 0.86, 120)[None, :, None]
sp = Image.fromarray((np.asarray(sp, float) * grad).clip(0, 255).astype("uint8"))
book.alpha_composite(warp(sp, spine, (CW, CH)))

c = np.asarray(cover, float)
x = np.linspace(0, 1, c.shape[1])[None, :, None]
c = c * (1.0 - 0.10 * x) * (1.0 - 0.22 * np.exp(-((x - 0.035) / 0.012) ** 2)) * (1.0 + 0.06 * np.exp(-((x - 0.16) / 0.05) ** 2))
book.alpha_composite(warp(Image.fromarray(c.clip(0, 255).astype("uint8")), front, (CW, CH)))
ImageDraw.Draw(book).line(s([(810, 165), (810, 1105)]), fill=(200, 192, 180, 255), width=2 * SS)
book = book.resize((CW // SS, CH // SS), Image.LANCZOS)
book = book.crop(book.getbbox())

# compose on a 1080x1920 black frame; book between the top line (y 250) and "Comment BOOK" (y 1390)
frame = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([190, 420, 890, 1220], fill=(245, 197, 66, 70))
frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
bw = 640
bh = int(book.height * bw / book.width)
if bh > 980:
    bh = 980; bw = int(book.width * bh / book.height)
bk = book.resize((bw, bh), Image.LANCZOS)
frame.alpha_composite(bk, ((1080 - bw) // 2, 340 + (980 - bh) // 2))
frame.convert("RGB").save(os.path.join(A, "outro_still.png"))
print("outro_still.png", bw, bh)
