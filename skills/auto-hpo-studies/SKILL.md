---
name: auto-hpo-studies
description: >
  Autonomous hyperparameter optimization loop: define target and search
  space, then iterate update-config run monitor log commit until convergence.
  Uses MLflow for tracking, sleep-based polling for long-running tasks.
license: MIT
compatibility: opencode
metadata:
  stack: ml
  audience: researchers
---

## When to use

Load when running a multi-iteration HPO study where an agent
autonomously iterates: tweak a config parameter, launch a training
run, monitor via sleep-based polling until completion, compare
results via MLflow, commit if improved, and repeat until convergence.

---

## Prerequisite skills

- **ml-project** — provides the project-specific ML conventions:
  pipeline structure, config format, training script interface,
  experiment naming.  Load this skill *first*, then auto-hpo-studies
  on top.
- **git-conventions** — branching, conventional commits.

---

## Overview

The agent runs an autonomous loop after the user defines the target.
No manual intervention between iterations.

```
┌─────────────────────────────────────────────────────────┐
│ 1. Define target (user provides once)                   │
│    - which model/variant to optimise                    │
│    - search space: params, ranges, step sizes           │
│    - stopping criteria                                  │
│    - baseline config + initial run                      │
└──────────────────────────┬──────────────────────────────┘
                           ▼  (loop begins)
┌─────────────────────────────────────────────────────────┐
│ 2. FETCH current metrics from MLflow                    │
│    query the last run for this model+target combination │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 3. DIAGNOSE training state                              │
│    healthy? overfitting? underfitting? NaN? converged?  │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 4. DECIDE next parameter change                         │
│    pick one param, compute new value from search space  │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 5. APPLY change to config                               │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 6. LAUNCH training run                                  │
│    start pipeline / script in background                │
│    capture PID for monitoring                           │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 7. MONITOR with sleep-based polling                     │
│    while process running: sleep(N), check PID,          │
│    tail log for progress, detect stalls                 │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 8. READ new metrics from MLflow                         │
│    query the run that just completed                    │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 9. COMPARE                                               │
│    new vs previous min_val_loss                          │
│    improved? → keep config + commit                     │
│    regressed? → revert config + try different approach  │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 10. CHECK stopping criteria                             │
│     met? → commit final summary, stop                   │
│     not met? → go to step 2                             │
└─────────────────────────────────────────────────────────┘
```

---

## Step-by-step

### 1 — Define target (user provides once)

The user specifies:

- **Target ID** — a short label used in commit messages and
  MLflow tags (e.g. `dla-bernstein-nf`).
- **Model/variant** — which model architecture to optimise.
- **Search space** — a table of tunable parameters, their initial
  values, allowed ranges, and step sizes / strategies.
- **Stopping criteria** — at least two of: target metric value,
  max iterations without improvement, max total iterations,
  search space exhausted signal.
- **Baseline config** — the starting YAML / JSON / TOML config.
- **Run command** — how to launch a training run for this target
  (e.g. `python train.py --config path/to/config.yaml`,
  `dvc repro train@dataset0-<model>`).

The agent stores this in a study log file (e.g. `hpo_study.md`)
at the repo root with a structured header.

### 2 — Fetch current metrics from MLflow

Query MLflow for the most recent run matching this target:

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
exp = client.get_experiment_by_name("<experiment-name>")
runs = client.search_runs(
    experiment_ids=[exp.experiment_id],
    filter_string="tags.target = '<target-id>'",
    order_by=["start_time DESC"],
    max_results=1,
)
run = runs[0]
current_val_loss = run.data.metrics.get("min_val_loss")
current_train_loss = run.data.metrics.get("min_loss")
best_epoch = run.data.metrics.get("best_epoch")
```

If no prior run exists, this is iteration 0 — run the baseline
config first.

### 3 — Diagnose training state

Classify from MLflow metrics:

| Signal | Pattern | Conclusion |
|--------|---------|------------|
| No prior run | — | Run baseline first |
| Losses high (positive) | `min_loss >> 0`, `min_val_loss >> 0` | Not learning |
| Train ≪ val | `min_loss < -100`, `min_val_loss > -50` | Overfitting |
| Both negative, close | `min_loss ≈ min_val_loss < -50` | Healthy |
| Train low, val rising | `final_val_loss > min_val_loss` | Overfitting late |
| NaN | `min_val_loss` is NaN or inf | Numerical instability |

**Action mapping:**

- **Not learning**: reduce learning rate (log-scale, halve), or
  switch to a learning rate schedule (cosine decay).
- **Overfitting**: add regularisation, reduce model capacity,
  increase early stopping patience.
- **Healthy**: cautiously increase capacity to push val_loss lower.
- **NaN training loss**: adjust numerical stabilisation — reduce
  LR, switch schedule, add gradient clipping, change base
  distribution.
- **Converged** (last N iterations Δ < threshold): stop, report
  best config.

### 4 — Decide next parameter change

Change exactly **one** parameter per iteration to isolate cause
and effect.  Exploration order:

1. **Learning regime** — find a working LR and schedule first.
2. **Capacity** — increase model size once LR is settled.
3. **Regularisation** — add only if overfitting appears.
4. **Training budget** — increase epochs/patience last.

Move one step in the search space per iteration.  Never jump
multiple steps — each commit's Δ must be attributable.

### 5 — Apply change to config

Edit the config file(s).  This is project-specific — the
`ml-project` skill defines the exact config format and fields.
Common edits: learning rate, model size params, regularisation
strength, training duration.

### 6 — Launch training run

Start the training pipeline in the background so the agent can
monitor it:

```bash
nohup <run-command> > logs/iter<N>_<target-id>.log 2>&1 &
PID=$!
echo $PID > /tmp/hpo_iter<N>.pid
```

Record the PID and redirect stdout/stderr to a log file.

If the pipeline has multiple stages (prepare → train → evaluate),
invoke the top-level command that runs all of them.

### 7 — Monitor with sleep-based polling

After launching, poll for completion:

```bash
# Basic PID-based polling
while kill -0 $PID 2>/dev/null; do
    sleep 30
done

# Check exit code
wait $PID
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Run failed with exit code $EXIT_CODE"
    # Handle failure: revert config, log error, continue
fi
```

For agents with tool-based process control (no shell PID access),
use a file-based handoff:

```bash
# At launch:
echo "running" > /tmp/hpo_<target-id>_status
<run-command> > logs/iter<N>.log 2>&1
echo "done" > /tmp/hpo_<target-id>_status
```

Then poll by reading the status file:

```python
import time
import pathlib

status_file = pathlib.Path("/tmp/hpo_<target-id>_status")
while status_file.read_text().strip() != "done":
    time.sleep(30)
```

**Polling interval:** 30–60 seconds for typical ML training runs
(minutes to hours).  Adjust based on expected run duration.

**Progress check inside the loop:** periodically tail the log file
to detect stalls (no new output after N minutes):

```python
import time

log_file = pathlib.Path("logs/iter<N>.log")
last_size = log_file.stat().st_size

while status_file.read_text().strip() != "done":
    time.sleep(60)
    current_size = log_file.stat().st_size
    if current_size == last_size:
        # No progress for 60s — may be stalled
        # Consider: check process, escalate, or abort
        pass
    last_size = current_size
```

### 8 — Read new metrics from MLflow

Run the MLflow query from step 2 again.  The newly completed run
should now appear with `start_time` near-now.

Validate the run completed successfully:
- `min_val_loss` is not NaN.
- `best_epoch` is reasonable (> 5, not equal to `max_epochs` if
  early stopping was expected to trigger).
- The run has the expected tags.

### 9 — Compare

```python
improvement = old_val_loss - new_val_loss  # negative = better
```

| Condition | Action |
|-----------|--------|
| `improvement > threshold` (e.g. > 0.5) | Keep config, commit |
| `0 < improvement <= threshold` | Keep config, commit (marginal) |
| `improvement <= 0` | Revert config, try different param |
| NaN result | Revert, log issue |

When reverting: restore the config file to its pre-edit state
(e.g. `git checkout -- <config-file>`).

After keeping: commit with message:

```
feat(hpo): <target-id> iter<N> — <param> <old>→<new> (val: <old>→<new>)
```

The commit body may contain notes about the diagnosis that led
to this change.

### 10 — Check stopping criteria

Evaluate against the user-defined criteria.  Typical rules:

1. **Target reached** — `min_val_loss` meets or exceeds the target.
2. **Plateau** — last N iterations (e.g. 5) without improvement.
3. **Max iterations** — total iterations reached limit.
4. **Search space exhausted** — all params at boundaries,
   or all reasonable combinations tried.

If stopping criterion met:
1. Write a summary to the study log: best config, best metric,
   iteration history.
2. Commit:
   ```
   feat(hpo): <target-id> — optimisation complete (val_loss: <best>)
   ```
3. Report results to the user.

If not met, return to step 2.

---

## MLflow tracking conventions

Tag every run with the target ID and iteration number for easy
querying:

```python
mlflow.set_tag("target", "<target-id>")
mlflow.set_tag("hpo_iteration", str(N))
mlflow.log_param("config_file", "<path>")
```

Query pattern for the study log:

```python
runs = client.search_runs(
    experiment_ids=[exp.experiment_id],
    filter_string="tags.target = '<target-id>'",
    order_by=["tags.hpo_iteration ASC"],
)
for r in runs:
    print(
        r.data.tags.get("hpo_iteration"),
        r.data.metrics.get("min_val_loss"),
    )
```

---

## Logging conventions

The study log (e.g. `hpo_study.md`) is a living document:

1. **Header** — written once at start: target definition, search
   space, stopping criteria, baseline.
2. **Progress table** — one row appended per iteration:
   `| # | Date | Param changed | Old val | New val | Δ val_loss | Commit |`
3. **Each iteration is a git commit**, so `git log` alone serves
   as the complete iteration history.  The study log duplicates
   key information for quick human reading.

---

## Common patterns

| Situation | Response |
|-----------|----------|
| Run crashes on launch | Check config format, check dependencies, check GPU memory. Fix + re-run as same iteration. |
| Run hangs / no output for 5 min | Abort (`kill <PID>`), note in log, try different params. |
| NaN after 3 different attempts | Declare this model/variant unstable for this target. Document in study log. |
| Δ < 0.1 for 5 consecutive iterations | Plateau reached. Stop optimisation for this target. |
| val_loss improves but train_loss stays flat | Continue — val_loss is the primary metric. |
| User interrupts the loop | The last commit is the restore point. Resume from `git log` tail. |

---

## Key references

- MLflow Tracking: https://mlflow.org/docs/latest/tracking.html
- `ml-project` skill — project-specific pipeline, config, experiment conventions
- `git-conventions` skill — commit formatting, branching
