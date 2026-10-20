#!/usr/bin/env python3
"""audit.py <session.jsonl>: what did a sub-agent actually do?
Prints tool-call counts, diff/read evidence and every mutating action.
Exit 1 if the session mutated the repo (verdict void)."""
import json, re, sys, collections

p = sys.argv[1]
calls = collections.Counter()
cmds, files, mut = [], [], []
first = last = None
for line in open(p):
    d = json.loads(line)
    ts = d.get("timestamp")
    if isinstance(ts, str):
        first = first or ts
        last = ts
    for c in (d.get("message", {}).get("content") or []):
        if not (isinstance(c, dict) and c.get("type") == "toolCall"):
            continue
        name, a = c.get("name", ""), c.get("arguments", {}) or {}
        calls[name] += 1
        if name == "bash":
            cmd = a.get("command", "")
            cmds.append(cmd[:160])
            # writes to /tmp are notes, writes into the repo are mutations
            targets = re.findall(r"(?<![=<>&])>>?\s*([^\s|;&)]+)", cmd)
            outside = [t for t in targets
                       if not t.startswith(("/tmp", "tmp")) and t != "/dev/null"]
            if (any(k in cmd for k in (" rm ", " mv ", " git commit", " tee ",
                                       "sed -i", " git checkout", " git apply",
                                       " git reset"))
                    or outside):
                mut.append(cmd[:160])
        elif name == "read":
            files.append(a.get("path", ""))
        elif name in ("write", "edit"):
            mut.append(f"{name}: {a.get('path','')}")

diff = [c for c in cmds if "diff" in c]
print(f"session: {p}")
print(f"time:    {first} .. {last}")
print(f"tools:   {dict(calls)}")
print(f"git diff calls: {len(diff)}")
for c in diff[:3]:
    print(f"  {c}")
print(f"files read: {len(files)} distinct {len(set(files))}")
print(f"MUTATING actions: {len(mut)}")
for c in mut[:10]:
    print(f"  {c}")
sys.exit(1 if mut else 0)
