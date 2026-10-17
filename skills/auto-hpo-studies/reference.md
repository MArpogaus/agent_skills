# Auto HPO studies: reference

Read the section that a step of `SKILL.md` names. Run each snippet
from the repo root.

## Launch

Step 6 runs this block. Replace `<target-id>`, `<N>`, `<change>` and
`<run-command>`:

```bash
STATE=~/.cache/hpo/<target-id>; mkdir -p "$STATE" logs
rm -f "$STATE/exit" "$STATE/pid" "$STATE/stalls" "$STATE/stall_size"
echo running > "$STATE/status"; echo <N> > "$STATE/iter"
echo "<change>" > "$STATE/change"
nohup setsid sh -c 'echo $$ > '"$STATE"'/pid
                    { <run-command>; } > logs/iter<N>_<target-id>.log 2>&1
                    echo $? > '"$STATE"'/exit' > /dev/null 2>&1 &
```

Each shell call of an agent is a new shell. The state files carry the
state between calls. The run writes its own process group to `pid`.
If the run command contains a `'`, put it into a script and call that.

## Watcher

Step 7 starts this watcher in the background:

```bash
STATE=~/.cache/hpo/<target-id>; log=logs/iter<N>_<target-id>.log
alive() { ps -o stat= -s "$(cat "$STATE/pid")" | grep -qv '^Z'; }
size() { { wc -c < "$log"; } 2>/dev/null || echo 0; }
last=$(size); still=0
until [ -f "$STATE/exit" ]; do
    sleep 30
    alive || { [ -f "$STATE/exit" ] || echo 137 > "$STATE/exit"; break; }
    now=$(size)
    if [ "$now" = "$last" ]; then still=$((still + 1)); else still=0; fi
    if [ "$still" -ge 10 ]; then
        n=1; [ "$now" = "$(cat "$STATE/stall_size" 2>/dev/null)" ] \
            && n=$(($(cat "$STATE/stalls") + 1))
        echo "$now" > "$STATE/stall_size"; echo "$n" > "$STATE/stalls"
        [ "$n" -ge 3 ] && { kill -- -"$(cat "$STATE/pid")"; continue; }
        echo "STALL $n: no new output for 10 polls"; exit 2
    fi
    last=$now
done
[ "$(cat "$STATE/exit")" = 0 ] && echo completed > "$STATE/status" \
    || echo failed > "$STATE/status"
```

The watcher polls every 30 seconds. The run is alive while a
non-zombie process is in the session of `pid`. The watcher ends when
the run ends. When the run ends without an exit code, the watcher
writes `exit` = `137`.

A stall is no new output in 10 polls in a row (5 minutes). Only log
growth counts as progress. GPU load alone never counts. The watcher
writes the `wc -c` size of the log to `$STATE/stall_size`. It writes the
count of stalls at that size to `$STATE/stalls`, so the count survives
a resume. At the first and the second stall, the watcher ends with exit
code 2 and prints `STALL <n>`.

On a stall, start the watcher again. At the third stall at the same
log size, the watcher kills the run, and the run ends `failed`.

## Resume

When the skill loads, check in this order before step 1. `<N>` is the
value in `$STATE/iter`.

1. `git log --grep "<target-id> done:"` finds a commit: report the
   study as finished and stop.
2. `hpo_study.md` has no `## <target-id>` section: go to step 1. Ask only for the items of step 1
   that the user did not give.
3. No state files and no `launched` row, or row `<N>` is `committed`,
   `reverted` or `failed`: go to step 10.
4. `status` is `running` and a non-zombie process is in the session
   of `pid`: start the watcher again (step 7).
5. `status` is `running` and no such process exists: write
   `completed` to `status` when `exit` is `0`, else `failed`. Go to
   step 8.
6. `status` is `completed` or `failed`: go to step 8.
7. Any other state: read the state files, the log and
   `git status`, then ask the user (autonomous: record a blocker,
   `dev-conventions`, "2. Asking and acting").
