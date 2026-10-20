# Reference: skeletons for unattended pi sessions

## Driver loop

```bash
#!/usr/bin/env bash
# driver.sh - one instance, owns state.txt, ends on two clean passes.
repo=$(pwd); d=$repo/runs; bt=$d/units; state=$d/state.txt; log=$d/log.txt
mkdir -p "$d"
say() { echo "$(date -Is) | $*" >> "$log"; }
nfind() { grep -c '^status: open' "$d/findings.md" 2>/dev/null; true; }
stopped() { grep -q PHASE=done "$state"; }
[ "$(nfind)" ] || : > "$d/findings.md"
say "driver started (pid $$)"
pass=0; clean=0
while ! stopped; do
  pass=$((pass+1)); before=$(nfind); say "pass $pass start (open: $before)"
  for unit in "$bt"/w*.sh; do
    run=$d/run-$pass-$(basename "$unit" .sh).md
    echo "# pass $pass $unit $(date -Is)" > "$run"
    RUN="$run" timeout 1200 bash "$unit" >> "$run" 2>&1
    rc=$?; echo "exit=$rc" >> "$run"
    # same hard failure three times in a row is THE END for the driver
    [ $rc -gt 128 ] && { say "unit $unit killed ($rc)"; fi
    stopped && break
  done
  after=$(nfind); new=$(( ${after:-0} - ${before:-0} ))
  say "pass $pass done: $new new findings (before=$before after=$after)"
  if [ "$new" = 0 ]; then clean=$((clean+1)); [ "$clean" = 2 ] && break
  else clean=0
    # one narrow fix sub-agent per open finding
    while read -r title; do
      say "fix attempt: $title"
      timeout 1800 pi --model <model> -p "In $repo: the finding '$title' in
        $d/findings.md. Fix ONLY if small: <= 1 file, 20 lines, and you can
        write a test that fails without the fix. Run the check pipeline
        before committing. Conventional commit, never push, ignore the build
        directory and the prototype directories. Then set the finding's
        status line to 'fixed in <commit>' or 'open (not small)'." \
        >> "$d/fix.log" 2>&1
      say "fix exit $? for: $title"
    done < <(awk '/^## /{t=$0} /^status: open/{print t}' "$d/findings.md")
  fi
done
{ echo "# Results"; echo "- passes: $pass, clean passes: $clean"; } > "$d/done.md"
sed -i 's/^PHASE=.*/PHASE=done/' "$state"; say "driver ending (pass $pass)"
```

Start detached (there is no cron): `setsid nohup bash driver.sh > driver.out 2>&1 &`

## Heartbeat without cron

The heartbeat only revives the driver script. It must never wake an
agent that reads the task description and "continues" it — that agent
will rewrite the state and end the run.

```sh
#!/bin/sh
# heartbeat.sh - guard for driver.sh
cd <repo> || exit 0
grep -q PHASE=done runs/state.txt 2>/dev/null && exit 0
# pgrep -f <name> fails when the runner's cmdline is bare (pi!) and can
# match PID 1 - kill-loop.py is the exact check:
python3 <skill-dir>/tools/kill-loop.py driver.sh --dry || exit 0
setsid nohup bash driver.sh >> runs/driver.out 2>&1
```

Run it as: `setsid nohup sh -c 'while true; do heartbeat.sh; sleep 1200; done' &`
(`--dry` lists instead of kills: a live driver means exit 0, no restart.)

## kill-loop.py - stop drivers by argv, never match yourself

`pkill -f` matches the calling shell's own command line. Match
`/proc/<pid>/cmdline` instead:

```python
#!/usr/bin/env python3
"""kill-loop.py <name>: end background drivers (driver.sh) without
matching the caller. Exit 1 when nothing matched (use for liveness)."""
import os, signal, sys
name, dry = sys.argv[1], "--dry" in sys.argv
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
            try: os.kill(pid, signal.SIGTERM)
            except OSError: pass
sys.exit(0 if hits else 1)
```

## Transcript audit before accepting a CLEAN

Sessions are JSONL with one record per message; tool calls appear as
`message.content[].type == "toolCall"`. The audit answers: did the
reviewer actually read/diff, and did it touch the repo? Exit code 1 =
mutations = verdict void.

```python
#!/usr/bin/env python3
"""audit.py <session.jsonl>: summary on stdout, exit 1 on mutations."""
import json, re, sys, collections
calls, cmds, files, mut = collections.Counter(), [], [], []
for line in open(sys.argv[1]):
    d = json.loads(line)
    for c in (d.get("message", {}).get("content") or []):
        if not (isinstance(c, dict) and c.get("type") == "toolCall"):
            continue
        n, a = c.get("name", ""), c.get("arguments", {}) or {}
        calls[n] += 1
        if n == "bash":
            cmd = a.get("command", "")
            cmds.append(cmd[:160])
            # writes to /tmp are notes; writes into the repo are mutations
            out = [t for t in re.findall(r"(?<![=<>&])>>?\s*([^\s|;&)]+)", cmd)
                   if not t.startswith(("/tmp", "tmp")) and t != "/dev/null"]
            if out or any(k in cmd for k in (" rm ", " mv ", " git commit",
                    " tee ", "sed -i", " git checkout", " git apply", " git reset")):
                mut.append(cmd[:160])
        elif n == "read":
            files.append(a.get("path", ""))
        elif n in ("write", "edit"):
            mut.append(f"{n}: {a.get('path','')}")
print(dict(calls), "| diffs:", sum("diff" in c for c in cmds),
      "| reads:", len(set(files)), "| MUTATIONS:", len(mut))
for m in mut[:10]: print("  ", m)
sys.exit(1 if mut else 0)
```

## Trap list (each one cost a night)

- `VAR` unset in a child: `>> "$VAR"` becomes `>> ""` and every step of
  the workflow reports a fake failure. Export (`RUN="$run" cmd`).
- `grep -c x f || echo 0` prints `0\n0` on no match; the next
  `$(( ))` syntax error kills the non-interactive script with no log
  line after it. Use `grep -c x f; true`.
- `pkill -f` matches the caller; use `pkill -x` or kill-loop.py.
- `pgrep -f <session name>` never matches runners whose cmdline is bare
  (`pi`); PID 1 can share that name and confuses liveness checks.
- Killing a child under a non-reaping PID 1 leaves permanent zombies —
  cosmetic, do not "fix" them.
- A woken heartbeat agent that reinterprets the state file sets
  `PHASE=done` itself and ends the run while everything looks healthy.
- Two driver instances at once: memory storms, and every finding is
  environment noise. Single instance, guard before start.
- Long headless runs: gate each heavy phase on `MemAvailable`, not on
  wall-clock budget; a thrashing phase produces findings you must
  discard afterwards.
