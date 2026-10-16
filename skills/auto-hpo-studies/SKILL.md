---
name: auto-hpo-studies
description: >
  Autonomous hyperparameter optimization loop: define target and search
  space, then iterate update-config run monitor log commit until
  convergence. Uses MLflow for tracking and a background watcher for
  long runs. Use when the user asks to tune hyperparameters
  autonomously or to resume an HPO loop, or in a repo whose
  `hpo_study.md` has a row with status `launched`.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ml, requires: [dev-conventions, ml-project, git-conventions]}
---

# Skill: Autonomous HPO Studies

The agent runs the loop after the user defines the target once. The
user does not act between iterations. Each kept iteration is one
commit, as `git-conventions` says.

## Hard rules

- Take the table action of step 3 as one step of one search-space
  parameter. Then each change in `min_val_loss` has one cause. An
  action outside the search space is a blocker (`dev-conventions`,
  "2. Asking and acting").
- Write the study log row before the launch. Update it after the run.
- Run the watcher in the background (the harness monitor tool or a
  background job). Do not sleep in the foreground.
- Keep the state files in `~/.cache/hpo/<target-id>/`, never in
  `/tmp`.
- Stop only on a criterion of step 10, on an invalid baseline run
  (step 8), or on a blocker (first hard rule).

## State

`STATE=~/.cache/hpo/<target-id>` holds one value in each file:

| File | Value |
|---|---|
| `status` | `running`, `completed` or `failed` |
| `iter` | iteration number |
| `change` | `<param>:<old>-><new>`, or `baseline` in iteration 0 |
| `pid` | process group of the run |
| `exit` | exit code of the run |

## Step by step

### 1. Define the target (the user gives it once)

- **Target ID**: a label for commits and MLflow tags. Use the DVC
  `foreach` item of the target (see `ml-project`, "dvc.yaml: foreach
  over targets").
- **Config file**: `params/<target>.yaml` (see `ml-project`,
  "Per-target model configs").
- **Search space**: a table of parameters with initial value, range
  and step.
- **Diagnosis thresholds** for step 3: `overfit_gap` and
  `healthy_loss`. `overfit_gap` is the largest accepted
  `min_val_loss - min_loss`. `healthy_loss` is the `min_val_loss` that
  counts as a good fit.
- **Stopping criteria** for step 10: `target_loss` and `max_iter`.
  `patience` (iterations without improvement, default 5) and
  `min_delta` (default 0.1) are optional.
- **Run command**: for example `dvc repro train@<target>`. For a
  pipeline with more than one stage, use the command that runs all
  stages.

Write this as the header of `hpo_study.md` at the repo root. The log
uses the row format below, not the manual study format of
`ml-project`.

### 2. Fetch the current metrics

```python
import mlflow

runs = mlflow.search_runs(
    search_all_experiments=True,
    filter_string="tags.target = '<target-id>' and tags.kept = '1'",
    order_by=["start_time DESC"],
    max_results=1,
)
row = runs.iloc[0]
min_val_loss = row["metrics.min_val_loss"]
min_loss = row["metrics.min_loss"]
best_epoch = row["metrics.best_epoch"]
```

The training script of `ml-project` ("Logging from a training
script") sets `tags.target`.

If no run exists, this is iteration 0. Iteration 0: skip steps 3 to
5. Launch the unchanged config with `change` = `baseline` and row
`0`. When step 8 finds the run valid, tag it `kept`, set the row to
`committed` and commit `dvc.lock`, `results/<target>/metrics.json`
and `hpo_study.md` as `feat(hpo): <target-id> iter 0: baseline`. When it
is not valid, set the row to `failed`, stop and report.

### 3. Diagnose the training state

`gap = min_val_loss - min_loss`. Use the first row that matches:

| Pattern | Conclusion | Action |
|---|---|---|
| `gap > overfit_gap` | overfitting | add regularisation, reduce capacity, increase `train.patience` |
| `min_val_loss > healthy_loss` | underfitting | change the learning rate or schedule, then increase capacity |
| `min_val_loss <= healthy_loss` | healthy | increase capacity by one step |

### 4. Decide the next change

Step 3 picks the row. Inside that row's action, change the first
parameter that is not settled, in this order: learning rate and
schedule, capacity, regularisation, training budget. A parameter is
settled when its last 2 changes were `reverted`; `failed` rows do not
count. Never repeat a change
that the log shows as `reverted`.

### 5. Apply the change

Edit the config file. `ml-project` defines its fields.

### 6. Launch the run

Take `<N>` as the number of the last log row plus 1 (0 in iteration
0). The new row has status `launched`. Then run:

```bash
STATE=~/.cache/hpo/<target-id>; mkdir -p "$STATE" logs
echo running > "$STATE/status"; echo <N> > "$STATE/iter"
echo "<change>" > "$STATE/change"
nohup setsid sh -c '<run-command> > logs/iter<N>_<target-id>.log 2>&1
                    echo $? > '"$STATE"'/exit' > /dev/null 2>&1 &
echo $! > "$STATE/pid"
```

Each shell call of an agent is a new shell. The state files carry
the state between calls. If the run command contains a `'`, put it
into a script and call that.

### 7. Watch the run in the background

Start this watcher. Continue when it ends:

```bash
STATE=~/.cache/hpo/<target-id>; log=logs/iter<N>_<target-id>.log
last=-1; still=0
until [ -f "$STATE/exit" ]; do
    sleep 30
    kill -0 "$(cat "$STATE/pid")" 2>/dev/null ||
        { [ -f "$STATE/exit" ] || echo 137 > "$STATE/exit"; break; }
    size=$(wc -c < "$log" 2>/dev/null || echo 0)
    if [ "$size" = "$last" ]; then still=$((still + 1)); else still=0; fi
    [ "$still" -ge 10 ] && { echo "STALL: no new output for 10 intervals"; exit 2; }
    last=$size
done
[ "$(cat "$STATE/exit")" = 0 ] && echo completed > "$STATE/status" \
    || echo failed > "$STATE/status"
```

The watcher polls every 30 seconds. It ends when the run ends, also
when the run is killed without an exit code (`exit` = `137`). A
stall is no new output for 10 polls (5 minutes): the watcher then
ends with exit code 2. On a stall, read the log tail and the GPU use
(`nvidia-smi`). If the run continues, start the watcher again. If
the run hangs, abort the process group:

```bash
kill -- -"$(cat "$STATE/pid")"; echo 143 > "$STATE/exit"
```

### 8. Read the new metrics

If `status` is `failed`, go to step 9 (failed run). Else read the new run with the step 2 query without the `kept` filter.
The run is valid when all are true:

- `min_val_loss` is not NaN.
- `best_epoch` is more than 5 and less than `max_epochs - 1`, with
  `max_epochs` = `train.max_epochs` in `params.yaml`.

Else write `failed` to `$STATE/status`. In iteration 0, do what
step 2 says for iteration 0 instead of step 9.

### 9. Compare

`improvement = old_min_val_loss - new_min_val_loss` (positive is
better).

- `improvement > 0`: keep the config and fill in the row with status
  `committed`. Commit `params/<target>.yaml`, `dvc.lock`,
  `results/<target>/metrics.json` and `hpo_study.md` as
  `feat(hpo): <target-id> iter <N>: <param> <old>-><new>`. The body
  gives `min_val_loss <old>-><new>` and the diagnosis. Tag the run as
  kept: `mlflow.MlflowClient().set_tag(run_id, "kept", "1")`.
- `improvement <= 0`: restore the config and the outputs (command
  below). Set the row status to `reverted`.
- Failed run: restore the config and the outputs. Set the row status
  to `failed`, never `reverted`. A `failed` row does not ban the
  change and does not count for "settled" (step 4) or for
  "plateau" (step 10). Restore command:

  ```bash
  git checkout -- params/<target>.yaml dvc.lock \
      results/<target>/metrics.json && dvc checkout train@<target>
  ```

### 10. Check the stopping criteria

Stop when one of these is true:

1. **Target reached**: `min_val_loss <= target_loss`.
2. **Plateau**: the last `patience` iterations each gave
   `improvement < min_delta`. Skip `failed` rows in this count.
3. **Max iterations**: the number of the last log row reaches
   `max_iter`.
4. **Search space exhausted**: all search-space parameters are
   settled or at their bounds.
5. **Unstable**: `min_val_loss` is NaN after 3 different changes in a
   row. Mark this model unstable for this target in the study log.

When a criterion is true, write the best config, the best metric and
the history to the study log. Run `rm -rf "$STATE"`. Commit
`feat(hpo): <target-id> done: best min_val_loss <best>` and report to
the user. Else remove the state files and go to step 2.

## Study log rows

```markdown
| # | Date | Param change | Old min_val_loss | New min_val_loss | Δ min_val_loss | Status |
|---|------|--------------|------------------|------------------|----------------|--------|
| 1 | 2026-05-22 | lr: 0.001->0.0005 | -98.16 | -130.84 | 32.68 | committed |
```

`Δ min_val_loss` is the `improvement` of step 9. Status is
`launched`, `committed`, `reverted` or `failed`. Find the commit of
row `<N>` with `git log --grep "iter <N>:"`.

## Resume after interruption

When the skill loads, check in this order:

1. No `hpo_study.md`: ask the user for the definition (step 1).
2. State files exist and the row of `iter` is `committed`: if
   `git log --grep "iter <N>:"` finds nothing, do the step 9 commit.
   If the run has no `kept` tag, tag it. Then go to step 10.
3. State files exist and the log row of `iter` is not `launched`:
   go to step 10.
4. `status` is `running` and the process in `pid` is alive: start
   the watcher again (step 7).
5. `status` is `running`, the process is gone: read `exit`. `0`: go
   to step 8. Non-zero or missing: treat the run as failed (step 9).
6. `status` is `completed`: go to step 8.
7. `status` is `failed`: go to step 9 (failed run).
8. A `launched` row without state files: set it to `failed`, restore
   `params/`, go to step 2.
9. No state files and `git diff params/` shows a change: the config
   was edited but not launched. Restore it and go to step 2.
10. No state files and no diff: go to step 10, then step 2.

## Common patterns

| Situation | Response |
|---|---|
| The run crashes at launch | Check the config format, the dependencies and the GPU memory. Fix the cause and launch the same change in a new row. |

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **ml-project**: DVC pipeline orchestration, MLflow experiment
  tracking, HPO study logs, per-target configs, figure generation.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
