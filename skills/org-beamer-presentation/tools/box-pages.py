#!/usr/bin/env python3
"""Say which PAGE each overfull box landed on.

    tools/box-pages.py deck.log [threshold-pt]

LaTeX reports a box as "at line N", which is the line of that frame's
.vrb file, not of the .org — useless for finding the slide. This walks
the log and attributes each warning to the last page shipped out before
it. Boxes under the threshold (default 5pt) are dropped as noise.
"""

import re
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)

threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

for log in sys.argv[1:2]:
    print("==", log)
    page, pending = 0, []
    for line in open(log, errors="replace"):
        for shipout in re.finditer(r"\[(\d+)", line):
            page = int(shipout.group(1))
            for kind, size in pending:
                print(f"   page {page:>3}  {kind}box {size:.1f}pt")
            pending = []
        found = re.match(r"Overfull \\(v|h)box \(([0-9.]+)pt", line)
        if found and float(found.group(2)) > threshold:
            pending.append((found.group(1), float(found.group(2))))
