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

On a stall, start the watcher again. At the third stall end without log
growth, the watcher kills the run and the run ends `failed`.

## Resume

When the skill loads, check in this order before step 1. `<N>` is the
value in `$STATE/iter`.

0. If `git log --grep "<target-id> done:"` finds a commit, report the
   study as finished and stop.
1. No `hpo_study.md`: ask the user for the definition (step 1).
2. State files exist and row `<N>` is `committed`. If
   `git log --grep "<target-id> iter <N>:"` finds nothing, make the
   commit of step 9, or of step 2 in iteration 0. If the run has no
   `kept` = `1` tag, tag it as kept with the step 9 call
   (`set_tag(run_id, "kept", "1")`). Then go to step 10.
3. State files exist and row `<N>` is not `launched`: go to step 10.
4. `status` is `running` and a non-zombie process is in the session
   of `pid`: start the watcher again (step 7).
5. `status` is `running` and no non-zombie process is in the session
   of `pid`: read `exit`. `0`: go to step 8. Non-zero or missing:
   write `failed` to `status` and follow item 7.
6. `status` is `completed`: go to step 8.
7. `status` is `failed`: in iteration 0, follow the iteration 0 rule
   of step 2. Else go to step 9 (failed run).
8. A `launched` row without state files: set it to `failed`, stash
   `params/` with a message (`dev-conventions`, "Hard rules"), go to
   step 2.
9. No state files and `git diff params/` shows a change: stash it
   with a message and go to step 2.
10. No state files and no diff: go to step 10.
