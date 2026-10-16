---
name: auto-hpo-studies
description: >
  Autonomous hyperparameter optimization loop: define target and search
  space, then iterate update-config run monitor log commit until
  convergence. Uses MLflow for tracking and a background watcher for
  long runs. Use when the user asks to tune hyperparameters
  autonomously, or when the repo has an `hpo_study.md` with an open
  study.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ml, requires: [ml-project, git-conventions]}
---

# Skill: Autonomous HPO Studies

The agent runs the loop after the user defines the target once. The
user does not act between iterations. Each kept iteration is one
commit, as `git-conventions` says.

## Hard rules

- Change exactly one parameter by one step of the search space in
  each iteration, so that each change in `val_loss` has one cause.
- Write the study log row before the launch. Update it after the run.
- Run the watcher in the background (the harness monitor tool or a
  background job). Do not sleep in the foreground.
- Keep the state files in `~/.cache/hpo/<target-id>/`, never in
  `/tmp`.
- Stop only on a criterion of step 10.

## State

`STATE=~/.cache/hpo/<target-id>` holds one value in each file:

| File | Value |
|---|---|
| `status` | `running`, `completed` or `failed` |
| `iter` | iteration number |
| `change` | `<param>:<old>-><new>` |
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
- **Stopping criteria**: at least two of step 10, with values for
  `target_loss`, `min_delta`, `patience` and `max_iter`.
- **Run command**: for example `dvc repro train@<target>`. For a
  pipeline with more than one stage, use the command that runs all
  stages.

Write this as the header of `hpo_study.md` at the repo root. The
autonomous loop uses its own row format (below) and commits once for
each iteration. While it runs, this skill wins over the manual study
format of `ml-project`.

### 2. Fetch the current metrics

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
exp = client.get_experiment_by_name("<experiment-name>")
runs = client.search_runs(
    experiment_ids=[exp.experiment_id],
    filter_string="tags.target = '<target-id>'",
    order_by=["start_time DESC"],
    max_results=1,
)
m = runs[0].data.metrics  # min_val_loss, min_loss, best_epoch, val_loss
```

`val_loss` is the last logged value of the run. If no run exists,
this is iteration 0: run the baseline config.

### 3. Diagnose the training state

| Pattern | Conclusion | Action |
|---|---|---|
| `min_loss >> 0` and `min_val_loss >> 0` | not learning | halve the learning rate, or use cosine decay |
| `min_loss < -100`, `min_val_loss > -50` | overfitting | add regularisation, reduce capacity, increase patience |
| `val_loss > min_val_loss` | late overfitting | same as overfitting |
| `min_loss ≈ min_val_loss < -50` | healthy | increase capacity by one step |
| `min_val_loss` is NaN or inf | unstable | reduce the learning rate, change the schedule, add gradient clipping, change the base distribution |

### 4. Decide the next change

Explore in this order:

1. Learning rate and schedule.
2. Capacity, after the learning rate is settled.
3. Regularisation, only when overfitting appears.
4. Training budget (epochs, patience), last.

### 5. Apply the change

Edit the config file. `ml-project` defines its fields.

### 6. Launch the run

Write the row with status `launched`, then:

```bash
STATE=~/.cache/hpo/<target-id>; mkdir -p "$STATE" logs
echo running > "$STATE/status"; echo <N> > "$STATE/iter"
echo "<param>:<old>-><new>" > "$STATE/change"
nohup setsid sh -c '<run-command> > logs/iter<N>_<target-id>.log 2>&1
                    echo $? > '"$STATE"'/exit' > /dev/null 2>&1 &
echo $! > "$STATE/pid"
```

Each shell call of an agent is a new shell. The state files carry
the state between calls. If the run command contains a `'`, put it
into a script and call that.

### 7. Watch the run in the background

Start this watcher in the background. Continue when it ends:

```bash
STATE=~/.cache/hpo/<target-id>; log=logs/iter<N>_<target-id>.log
last=-1; still=0
until [ -f "$STATE/exit" ]; do
    sleep 30
    size=$(wc -c < "$log" 2>/dev/null || echo 0)
    if [ "$size" = "$last" ]; then still=$((still + 1)); else still=0; fi
    [ "$still" -eq 10 ] && echo "STALL: no new output for 5 minutes"
    last=$size
done
[ "$(cat "$STATE/exit")" = 0 ] && echo completed > "$STATE/status" \
    || echo failed > "$STATE/status"
```

Set the interval to 30 to 60 seconds. On a stall, read the log tail
and the GPU use (`nvidia-smi`). If the run hangs, abort the process
group. This also ends the watcher:

```bash
kill -- -"$(cat "$STATE/pid")"; echo 143 > "$STATE/exit"
```

### 8. Read the new metrics

Run the query of step 2 again. The run is valid when all are true:

- `min_val_loss` is not NaN.
- `best_epoch` is more than 5, and less than `max_epochs` when early
  stopping must trigger.
- The run has the tags `target` and `hpo_iteration`.

Else write `failed` to `$STATE/status`.

### 9. Compare

`improvement = old_val_loss - new_val_loss` (positive is better).

- `improvement > 0`: keep the config, fill in the row with status
  `committed` and commit:
  `feat(hpo): <target-id> iter <N>: <param> <old>→<new>`. The subject
  has at most 68 characters. The body gives `val_loss <old>→<new>`
  and the diagnosis.
- `improvement <= 0` or failed run: restore the config
  (`git checkout -- params/<target>.yaml`), set the row status to
  `reverted` or `failed`, and try a different parameter.

### 10. Check the stopping criteria

Stop when one of these is true:

1. **Target reached**: `min_val_loss <= target_loss`.
2. **Plateau**: the last `patience` iterations (default 5) each gave
   `improvement < min_delta` (default 0.1).
3. **Max iterations**: the iteration count reaches `max_iter`.
4. **Search space exhausted**: all parameters are at their bounds.
5. **Unstable**: `min_val_loss` is NaN after 3 different changes. Mark
   this model unstable for this target in the study log.

When a criterion is true: write the best config, the best metric and
the history to the study log, run `rm -rf "$STATE"`, commit
`feat(hpo): <target-id> done: best val_loss <best>` and report to the
user. Else remove the state files and go to step 2.

## Study log rows

```markdown
| # | Date | Param change | Old val | New val | Δ val_loss | Commit | Status |
|---|------|--------------|---------|---------|------------|--------|--------|
| 1 | 2026-05-22 | lr: 0.001→0.0005 | -98.16 | -130.84 | -32.68 | abc1234 | committed |
```

Status is `launched`, `committed`, `reverted` or `failed`.

## MLflow tags

Tag each run so that step 2 finds it:

```python
mlflow.set_tag("target", "<target-id>")
mlflow.set_tag("hpo_iteration", str(N))  # tags are text: sort with int()
mlflow.log_param("config_file", "params/<target>.yaml")
```

## Resume after interruption

When the skill loads, check in this order:

1. No `hpo_study.md`: ask the user for the definition (step 1).
2. `status` is `running` and the process in `pid` is alive: start
   the watcher again (step 7).
3. `status` is `running`, the process is gone: read `exit`. `0`: go to
   step 8. Non-zero or missing: treat the run as failed (step 9).
4. `status` is `completed`: go to step 8.
5. `status` is `failed`: go to step 9 (failed run).
6. No state files and `git diff params/` shows a change: the config
   was edited but not launched. Restore it and go to step 2.
7. No state files and no diff: go to step 10, then step 2.

## Common patterns

| Situation | Response |
|---|---|
| The run crashes at launch | Check the config format, the dependencies and the GPU memory. Fix and run the same iteration again. |
| NaN after 3 different changes | Stop (step 10, criterion 5). |
| `val_loss` improves, `train_loss` stays flat | Continue. `val_loss` is the primary metric. |

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **ml-project**: DVC pipeline orchestration, MLflow experiment
  tracking, HPO study logs, per-target configs, figure generation.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
