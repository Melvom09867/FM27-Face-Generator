"""Programm-Symbol (Fenster, Taskleiste, .exe): Spielerkopf vor einem Fußball, im Rasengrün.

Wird per Code gezeichnet – keine Bilddatei nötig. Für den Build:  python -m fm27facegen.icon build/icon.ico
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

GREEN_DARK = (20, 83, 45)
GREEN = (34, 139, 64)
WHITE = (255, 255, 255)
INK = (28, 32, 36)


def _ball(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=INK, width=max(1, int(r * 0.09)))
    # mittleres Fünfeck + Ansätze der Nachbarfelder
    pr = r * 0.36
    pts = [(cx + pr * math.cos(math.radians(-90 + 72 * i)), cy + pr * math.sin(math.radians(-90 + 72 * i)))
           for i in range(5)]
    d.polygon(pts, fill=INK)
    for x, y in pts:
        ang = math.atan2(y - cy, x - cx)
        ex, ey = cx + r * 0.97 * math.cos(ang), cy + r * 0.97 * math.sin(ang)
        d.line((x, y, ex, ey), fill=INK, width=max(1, int(r * 0.08)))


def make_icon(size: int = 256) -> Image.Image:
    s = 4 * size  # groß zeichnen, dann glatt verkleinern
    base = Image.new("RGBA", (s, s), GREEN + (255,))
    stripes = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    for i in range(0, 8, 2):  # Rasenstreifen
        sd.rectangle((0, int(s * i / 8), s, int(s * (i + 1) / 8)), fill=GREEN_DARK + (90,))
    base = Image.alpha_composite(base, stripes)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.2), fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(base, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # Kopf + Schultern (Silhouette wie ein FM-Porträt)
    cx = s * 0.45
    head_r = s * 0.17
    head_cy = s * 0.36
    d.ellipse((cx - head_r, head_cy - head_r * 1.1, cx + head_r, head_cy + head_r * 1.1), fill=WHITE)
    d.rectangle((cx - head_r * 0.38, head_cy + head_r * 0.8, cx + head_r * 0.38, head_cy + head_r * 1.45), fill=WHITE)
    d.pieslice((cx - s * 0.33, s * 0.56, cx + s * 0.33, s * 1.18), 180, 360, fill=WHITE)
    # Fußball unten rechts
    _ball(d, s * 0.74, s * 0.74, s * 0.19)
    return img.resize((size, size), Image.LANCZOS)


def save_ico(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    make_icon(256).save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128),
                                                    (256, 256)])
    return path


if __name__ == "__main__":
    print(save_ico(sys.argv[1] if len(sys.argv) > 1 else "build/icon.ico"))
