#!/usr/bin/env python3
"""Tile a deck's pages into numbered sheets, so every page gets looked at.

    tools/contact-sheet.py deck.pdf /tmp/sheet [cols] [rows]

Writes /tmp/sheet-1.png, -2.png … each holding cols*rows pages, framed
and numbered. Read all of them: a clean LaTeX log says nothing about a
legend covering a title or a drawer typeset onto a slide.

Needs pdftoppm (poppler) and Pillow.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

if len(sys.argv) < 3:
    sys.exit(__doc__)

pdf, prefix = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rows = int(sys.argv[4]) if len(sys.argv) > 4 else 3

tmp = Path(tempfile.mkdtemp())
subprocess.run(["pdftoppm", "-r", "55", "-png", pdf, str(tmp / "p")], check=True)
pages = sorted(tmp.glob("p-*.png"))
if not pages:
    sys.exit(f"no pages rendered from {pdf}")

per = cols * rows
for start in range(0, len(pages), per):
    chunk = pages[start : start + per]
    width, height = Image.open(chunk[0]).size
    sheet = Image.new("RGB", (cols * width, rows * height), "white")
    draw = ImageDraw.Draw(sheet)
    for i, page in enumerate(chunk):
        x, y = (i % cols) * width, (i // cols) * height
        sheet.paste(Image.open(page), (x, y))
        draw.rectangle([x, y, x + width - 1, y + height - 1], outline="red")
        draw.text((x + 4, y + 2), str(start + i + 1), fill="red")
    out = f"{prefix}-{start // per + 1}.png"
    sheet.save(out)
    print(out, len(chunk))
