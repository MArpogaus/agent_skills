#!/usr/bin/env python3
"""kill-loop.py <name> [--dry]: end background driver scripts by matching
argv from /proc, without ever matching the calling shell.
Exit 1 when nothing matched (usable as a liveness check)."""
import os
import signal
import sys

name = next((a for a in sys.argv[1:] if not a.startswith("--")), "driver.sh")
dry = "--dry" in sys.argv
me = os.getpid()
hits = 0
for pid in (int(p) for p in os.listdir("/proc") if p.isdigit()):
    if pid in (me, 1, os.getppid()):
        continue
    try:
        args = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
    except OSError:
        continue
    if len(args) >= 2 and args[0].endswith(b"bash") and args[1].endswith(name.encode()):
        hits += 1
        print("killing", pid, args[:3])
        if not dry:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

sys.exit(0 if hits else 1)
