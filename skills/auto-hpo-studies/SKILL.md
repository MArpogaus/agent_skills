---
name: auto-hpo-studies
description: >
  Autonomous hyperparameter optimization loop: define target and search
  space, then iterate update-config run monitor log commit until convergence.
  Uses MLflow for tracking, sleep-based polling for long-running tasks.
license: MIT
compatibility: opencode
metadata:
  requires:
    - ml-project
    - git-conventions
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

Before launch, write a row to the study log with status `launched`:

```markdown
| N | Date | <param>: <old>→<new> | <old> | — | — | — | launched |
```

Then start the training pipeline in the background:

```bash
# Write status file for resume detection
echo "running" > /tmp/hpo_<target-id>_status
echo "<target-id>" > /tmp/hpo_<target-id>_target
echo "<N>" > /tmp/hpo_<target-id>_iter
echo "<param-name>:<old-value>-><new-value>" > /tmp/hpo_<target-id>_change

# Launch
nohup <run-command> > logs/iter<N>_<target-id>.log 2>&1 &
PID=$!
echo $PID > /tmp/hpo_iter<N>.pid
```

Record the PID and redirect stdout/stderr to a log file.

If the pipeline has multiple stages (prepare → train → evaluate),
invoke the top-level command that runs all of them.

### 7 — Monitor with sleep-based polling

After launching, poll for completion.  This is the longest step —
the agent must sleep and wait, not spin.

**Shell-based polling (PID available):**

```bash
# Poll until process exits
while kill -0 $PID 2>/dev/null; do
    sleep 30
done

# Check exit code
wait $PID
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Run failed with exit code $EXIT_CODE"
    echo "failed" > /tmp/hpo_<target-id>_status
    # Handle failure: revert config, log error, continue
fi
```

**File-based polling (agent has no PID access):**

The launch command (step 6) already set the status file to
`running`.  The training script must write `completed` on exit:

```bash
# Must be appended to the end of <run-command> or a wrapper:
<run-command> > logs/iter<N>.log 2>&1
echo "completed" > /tmp/hpo_<target-id>_status
```

Poll by reading the status file:

```python
import time
import pathlib

status_file = pathlib.Path("/tmp/hpo_<target-id>_status")
while status_file.read_text().strip() == "running":
    time.sleep(30)
```

**Polling interval:** 30–60 seconds for runs of minutes to hours.
Adjust based on expected duration.

**Stall detection:** check log file growth each cycle:

```python
log_file = pathlib.Path("logs/iter<N>.log")
last_size = log_file.stat().st_size

while status_file.read_text().strip() == "running":
    time.sleep(60)
    current_size = log_file.stat().st_size
    if current_size == last_size:
        # No output appended for 60s — possible stall.
        # Check if process is alive, abort if hung.
        pass
    last_size = current_size
```

On stall suspicion: check exit code, check GPU utilisation with
`nvidia-smi`, check log tail for error messages.  If hung, abort
(`kill <PID>`), write `failed` to status file, revert config,
and try different params.

### 8 — Read new metrics from MLflow

Run the MLflow query from step 2 again.  The newly completed run
should now appear with `start_time` near-now.

Validate the run completed successfully:
- `min_val_loss` is not NaN.
- `best_epoch` is reasonable (> 5, not equal to `max_epochs` if
  early stopping was expected to trigger).
- The run has the expected tags.

If validation fails (NaN, no metrics, wrong tags), write `failed`
to status file and treat as run failure in step 9.

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
(e.g. `git checkout -- <config-file>`), update study log row
status to `reverted`, and try a different param.

After keeping: update the study log row with metrics and status
`committed`:

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
2. Clean up status files: `rm -f /tmp/hpo_<target-id>*`
3. Commit:
   ```
   feat(hpo): <target-id> — optimisation complete (val_loss: <best>)
   ```
4. Report results to the user.

If not met, clean up status files from this iteration and return
to step 2.  The next iteration will write fresh status files.

---

## Resume after interruption

The loop is designed to survive agent interruptions (timeout, session
end, crash).  When the skill loads and finds an existing study, the
first action is to determine the current state and continue from
exactly where it left off.

### State sources

| Source | What it tells you |
|--------|--------------------|
| `hpo_study.md` exists? | Study was started. If missing, ask user for definition (step 1). |
| Git log last commit | `git log --oneline -1 --grep="feat(hpo): <target-id>"` — the last committed iteration number. |
| Status file | `/tmp/hpo_<target-id>_status` — `running`, `completed`, or missing. |
| Working tree diff | `git diff params/` — uncommitted config changes from the current iteration. |
| MLflow last run | Query most recent run for this target — may have metrics from an uncommitted iteration. |

### Resume decision tree

Read the sources in order, then branch:

```
Does hpo_study.md exist?
├── No → study never started. Go to step 1 (ask user for definition).
└── Yes → check status file.
       └── Status file says "running" → training process may still be alive.
            ├── PID exists and process is running → resume monitoring (step 7).
            │    Poll the log file, wait for completion.
            └── PID gone / process dead → run finished or crashed.
                 Check MLflow for new metrics.
                 ├── Metrics found → go to step 8 (read + compare).
                 └── No metrics / NaN → run failed. Revert config,
                      log failure in study log, start new iteration
                      with different params (step 4).

       Status file says "completed" → run finished but loop was interrupted
       before commit.  Go to step 8 (read metrics → compare → commit).

       No status file → loop was interrupted between commit and next launch.
            Check git log for last HPO commit:
            ├── Last row in study log has a commit hash →
            │    previous iteration complete.  Check stopping criteria
            │    (step 10), then start new iteration (step 2).
            └── Study log empty / no commits →
                 study defined but nothing run yet.  Go to step 2.
```

### Status file protocol

Write the status file at every state transition so the resume
logic always has a deterministic signal:

```bash
# In launch (step 6):
echo "running" > /tmp/hpo_<target-id>_status
echo "<target-id>" > /tmp/hpo_<target-id>_target
echo "<N>" > /tmp/hpo_<target-id>_iter
echo "<param-name>:<old-value>-><new-value>" > /tmp/hpo_<target-id>_change

# In monitoring (step 7), on completion:
echo "completed" > /tmp/hpo_<target-id>_status

# In compare (step 9), if NaN/failure:
echo "failed" > /tmp/hpo_<target-id>_status

# Before next launch, clean up:
rm -f /tmp/hpo_<target-id>_status /tmp/hpo_<target-id>_iter \
      /tmp/hpo_<target-id>_change
```

### Restoring the config after crash

If the agent was interrupted mid-iteration (config edited, run not
yet committed), the working tree shows the uncommitted config diff.
Before resuming, check:

```bash
git diff params/
```

- If diff exists and status file says `running` → this config was
  launched, keep it and monitor.
- If diff exists and status file is missing → config was edited
  but never launched.  Revert and start fresh:
  `git checkout -- params/<target>/<model>.yaml`
- No diff → clean state, proceed normally.

### Study log row format

Write the row **before** launch and fill in metrics + commit hash
after the run completes.  This leaves a trace even if interrupted:

```markdown
| # | Date | Param change | Old val | New val | Δ val_loss | Commit | Status |
|---|------|-------------|---------|---------|------------|--------|--------|
| 1 | 2026-05-22 | lr: 0.001→0.0005 | — | — | — | — | launched |
| 1 | 2026-05-22 | lr: 0.001→0.0005 | -98.16 | -130.84 | -32.68 | abc1234 | committed |
```

The `Status` column lets the resume logic immediately identify
incomplete rows.  After interruption, scan the table for the last
row with `Status` ≠ `committed` and decide what to do.

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

The study log (e.g. `hpo_study.md`) is a living document and the
**primary resume source**:

1. **Header** — written once at start: target definition, search
   space, stopping criteria, baseline.
2. **Progress table** — one row per iteration with a `Status`
   column.  The row is written at launch (status: `launched`) and
   updated on completion (status: `committed` or `reverted` or
   `failed`):
   ```
   | # | Date | Param changed | Old val | New val | Δ val_loss | Commit | Status |
   ```
3. **Each iteration is a git commit**, so `git log` alone serves
   as the complete iteration history.  The study log duplicates
   key information for quick human reading and interruption recovery.
4. **On resume**, scan for the last row where `Status` ≠ `committed`
   to determine the next action (see Resume after interruption).

---

## Common patterns

| Situation | Response |
|-----------|----------|
| Run crashes on launch | Check config format, check dependencies, check GPU memory. Fix + re-run as same iteration. |
| Run hangs / no output for 5 min | Abort (`kill <PID>`), note in log, try different params. |
| NaN after 3 different attempts | Declare this model/variant unstable for this target. Document in study log. |
| Δ < 0.1 for 5 consecutive iterations | Plateau reached. Stop optimisation for this target. |
| val_loss improves but train_loss stays flat | Continue — val_loss is the primary metric. |
| Agent interrupted mid-iteration | On reload: check status file → `running`: resume monitoring; `completed`: read metrics + commit; missing: check study log last row status. See "Resume after interruption" section. |
| Study log row has `launched` status from prior session | Check status file → `running`: resume monitoring; `completed`: read MLflow metrics; missing/failed: revert config, mark row `failed`, start new iteration. |
| Study log row has metrics but no commit hash | Run was completed but not committed. Run compare (step 9) and commit. |

---

## Key references

- MLflow Tracking: https://mlflow.org/docs/latest/tracking.html
- `ml-project` skill — project-specific pipeline, config, experiment conventions
- `git-conventions` skill — commit formatting, branching
