---
name: local-pi-session
description: >
  Unattended pi work in the sandbox: a single-instance background
  driver, a heartbeat without cron, review and fix sub-agents with
  transcript audit, and the shell traps that silently kill detached
  scripts. Use before starting any overnight or autonomous loop that
  runs pi or background shell work, and when a driver or heartbeat
  misbehaves.
license: MIT
compatibility: pi
metadata: {stack: meta, requires: [dev-conventions, sandbox-env]}
---

# Skill: Local pi Sessions

The shape of unattended work: a driver script loops over units of work,
spawns pi sub-agents for fixes and reviews, a heartbeat revives a dead
driver, and an audit keeps sub-agent verdicts honest. Skeletons of every
piece: [reference.md](reference.md).

## Hard rules

- One driver instance. Kill leftover drivers by matching argv from
  `/proc/<pid>/cmdline` before starting; `pkill -f` also matches the
  calling command line and kills yourself.
- Only the driver writes the state file. A heartbeat (or an agent it
  wakes) that re-interprets or completes the state ends the run early.
  It restarts the driver script, nothing else.
- Never accept a sub-agent verdict without an audit. Sub-agents run
  with a session; `--no-session` leaves no evidence and produced fake
  CLEANs.
- Export every variable a subprocess needs (`RUN="$run" cmd ...`). An
  unset variable in a redirect means `>> ""`: every step "fails" and
  the tool looks broken.
- Kill processes by exact name (`pkill -x <name>`), never by pattern.
- `grep -c pat file || echo 0` prints `0\n0` when nothing matches, and
  the next `$(( ))` kills a non-interactive bash script silently.
  Write `grep -c pat file; true` instead.
- Every unit of work gets a `timeout`; the driver stops after the same
  failure three times; every pass writes its own report file.
- State and reports live outside anything a build or disk cleanup may
  wipe (`target/` is not a place for an audit trail).

## Driver

One line of state: `PHASE=<phase> ROUND=<n> CLEAN=<k>` in
`state.txt`; one `log.txt` line per step (`date -Is | what happened`);
one report per unit; a `done.md` written on exit. The loop: while not
`PHASE=done` (only the driver sets it), run each unit with
`RUN="$run" timeout 1200 bash "$unit" >> "$run" 2>&1`. Count findings
by their status line (`^status: open`), not by heading count, so closed
findings stop counting. Start it detached:
`setsid nohup bash driver.sh > driver.out 2>&1 &`. No crontab, no
systemd in the sandbox: `setsid` plus a `while true; sleep` wrapper is
the scheduler.

## Heartbeat

A short shell script on a sleep loop. It exits when `PHASE=done`, exits
when a live driver exists, else restarts the driver script. It must not
wake an agent that reads the TODO and "continues" — that agent will
reinterpret state. Trap: pi's cmdline is bare `pi`; the session name
from `-n` is not in it, so `pgrep -f <session-name>` never matches, and
PID 1 may also be named `pi` — exclude it when checking for a live
driver.

## Sub-agents

Call with `timeout 1800 pi -p "<prompt>" >> agent.log 2>&1`, at most
two in parallel (RAM is the limit, not the CPU). The prompt contains:
repo path, exactly one task, named scope exclusions ("ignore the build
directory and the prototype directory <x>"), a size cap ("only fix if
at most 1 file, 20 lines, and you can write a failing test first"),
the verification pipeline to run before committing, the commit
conventions, and the exact status line to write into the findings file
(`fixed in <sha>` / `open (not small)`). The driver then reads only
`^status: open`.

## Audit before CLEAN

A review round counts only if its session transcript shows the work.
The session JSONL records every tool call; check that the reviewer ran
its diffs and reads and that it mutated nothing: writes outside
`/tmp` and `/dev/null`, plus `rm`, `mv`, `tee`, `sed -i`,
`git commit/checkout/apply/reset` count as mutations. Store the verdict
as `<round>.audit` beside the round report. Two more rules for review
loops: the review target is a fixed diff range, never "since the last
round" (an empty diff buys the second CLEAN for free); and CLEAN
detection demands a dedicated exact line (`grep -qx CLEAN`), because a
report may contain the word anywhere.

## Sandbox

Toolchain locations, installs and cache hygiene follow `sandbox-env`;
binaries often are not on `PATH`, call the env's bin directory. With
`PI_OFFLINE` nothing can be installed mid-run. PID 1 may not reap
children: thousands of zombies are cosmetic, not a leak. Gate heavy
phases on `MemAvailable` before starting them, and watch disk — debug
builds reach tens of GB and a cleanup then destroys whatever else lived
next to them.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `Skill`) to load them before using this one:

- **dev-conventions**: asking and acting, commit rules, review loop.
- **sandbox-env**: where tools live and how to install them.
