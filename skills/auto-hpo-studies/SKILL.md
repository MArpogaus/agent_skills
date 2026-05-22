---
name: auto-hpo-studies
description: >
  Long-running autonomous HPO: define plan in hpo_study.md, then loop
  update-params repro commit repeat until validation loss converges.
  Track every iteration as a git commit with val_loss diff.
license: MIT
compatibility: opencode
metadata:
  stack: ml
  audience: researchers
---

## When to use

Load when running a multi-iteration hyperparameter optimisation study
where an agent autonomously iterates: read metrics, diagnose, tweak
config, DVC repro, check result, commit, repeat.  The study plan and
every iteration result live in `hpo_study.md`.

---

## Prerequisite skills

This skill covers the HPO loop.  Load these companion skills for
supporting conventions:

- **ml-project** — DVC `foreach` layout, per-target configs,
  MLflow tracking, `hpo_study.md` as structured log, Feather I/O.
- **git-conventions** — two-branch flow (`main`/`dev`), conventional
  commits (`feat(hpo):` prefix), pre-commit hooks, one-commit-per-step.
- **python-dev** — YAML config editing, ruff formatting, numpy docstrings,
  `uv run` for ad-hoc analysis scripts.

---

## Study plan (written once at the start)

Before the first iteration, write a structured plan at the top of
`hpo_study.md`.  The plan is the agent's brief for the entire run:

```markdown
# HPO Study: <project-name>

## Plan

| Field | Value |
|-------|-------|
| Targets | `dla`, `ofen_g_koks`, `ofen_f_koks`, `pl2` |
| Models | `bernstein_nf`, `spline_nf`, `normal_baseline`, `lognormal_baseline` |
| Base config | `params/models/<target>/<model>.yaml` |
| Metric | `min_val_loss` (lower is better) |
| Direction | minimise NLL (negative → better calibration) |

## Search space (params to vary)

| Param | Initial | Range | Step / strategy |
|-------|---------|-------|-----------------|
| `initial_learning_rate` | `0.001` | `1e-4` – `1e-2` | log-scale halving |
| `lr_schedule` | `constant` | `{constant, cosine_decay}` | binary |
| `num_parameters` | `8` | `4` – `24` | +4 per step |
| `hidden_units` | `[128, 128]` | `[64,64]` – `[256,256]` | widen dims |
| `dropout` | `0.0` | `0.0` – `0.3` | +0.05 per step |
| `batch_norm` | `false` | `{false, true}` | binary |
| `max_epochs` | `200` | `100` – `500` | +100 per step |
| `early_stopping_patience` | `10` | `10` – `50` | +10 per step |

## Stopping criteria (any of)

1. `min_val_loss` target reached (e.g. `-180` for DLA spline).
2. 5 consecutive iterations without `val_loss` improvement.
3. All params at search-space boundary.
4. Clear overfitting (val_loss rising while train_loss still falling).

## Progress

| # | Date | Model | Target | Params changed | Train loss | Val loss | Δ val_loss | Commit |
|---|------|-------|--------|----------------|------------|----------|------------|--------|
|   |      |       |        |                |            |          |            |        |
```

Commit the plan before starting:
```
feat(hpo): <target> -- initial study plan
```

---

## The loop

Each iteration follows the same pattern.  The agent runs this loop
fully autonomously until a stopping criterion triggers.

```
┌─────────────────────────────────────────────────────┐
│ 1. READ current metrics                             │
│    results/<target>/<model>/metrics.yaml            │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 2. DIAGNOSE current state                           │
│    overfitting? underfitting? converged?            │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 3. DECIDE next change                               │
│    pick one param, compute new value                │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 4. EDIT config                                      │
│    params/models/<target>/<model>.yaml              │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 5. REPRO                                             │
│    dvc repro train@datasetX-<model>                 │
│    (wait for completion, check exit code)           │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 6. READ new metrics                                 │
│    results/<target>/<model>/metrics.yaml            │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 7. COMPARE                                           │
│    new_min_val_loss vs old_min_val_loss             │
│    improved? → keep + commit                        │
│    regressed? → revert + try different param        │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 8. LOG to hpo_study.md                              │
│    append row to Progress table                     │
└──────────────────────────┬──────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────┐
│ 9. CHECK stopping criteria                          │
│    met? → stop and commit final summary             │
│    not met? → go to step 1                         │
└─────────────────────────────────────────────────────┘
```

### Step-by-step details

#### 1 — Read current metrics

```bash
cat results/<target>/<model>/metrics.yaml
```

Expected output:
```yaml
best_epoch: 125
final_train_loss: 233.57
final_val_loss: -98.11
min_loss: 233.87
min_val_loss: -98.16
```

Keys to read: `min_val_loss` (primary), `min_loss` (training),
`best_epoch` (convergence speed).

#### 2 — Diagnose

Classify the training state from the loss values:

| Signal | Pattern | Conclusion |
|--------|---------|------------|
| Both losses high (positive) | `min_loss > +50`, `min_val_loss > +50` | Model not learning |
| Train low, val high | `min_loss << min_val_loss` | Overfitting |
| Both low but val > train | `min_loss < -100`, `min_val_loss > -100` | Overfitting |
| Both decreasing together | `min_loss ≈ min_val_loss`, both negative | Healthy |
| Val loss rising over epochs | `final_val_loss > min_val_loss` | Overfitting / plateau |

**Diagnosis → action mapping:**

- **Not learning**: reduce `initial_learning_rate`, or switch from
  `constant` to `cosine_decay` schedule.
- **Overfitting (train ≪ val)**: add `dropout`, enable `batch_norm`,
  reduce `hidden_units`, or increase `early_stopping_patience`.
- **Underfitting (both high, stable)**: increase `num_parameters`,
  widen `hidden_units`, increase `max_epochs`.
- **Healthy (both negative, close)**: try increasing `num_parameters`
  or `hidden_units` to push val_loss lower; watch for overfitting.
- **NaN**: lognormal base → switch to cosine decay LR, or add Scale
  bijector.  Spline with tight bins → reduce `num_parameters`.

#### 3 — Decide next change

Change exactly **one** param per iteration (isolate cause and effect).

Order of exploration:
1. **LR regime first** — find a working learning rate and schedule
   before touching capacity or regularisation.
2. **Capacity second** — increase `num_parameters` or `hidden_units`
   once LR is settled.
3. **Regularisation third** — add `dropout` / `batch_norm` only if
   overfitting appears after capacity increase.
4. **Training budget last** — increase `max_epochs` or patience only
   when the model consistently underfits with current budget.

Estimate the new value: always move one step in the search space,
never jump multiple steps.  This makes each commit's Δ attributable.

#### 4 — Edit config

Modify `params/models/<target>/<model>.yaml`.

Only touch these fields (example with typical starting values):

```yaml
model:
  hidden_units: [128, 128]
  dropout: 0.0
  batch_norm: false

train:
  max_epochs: 200
  early_stopping_patience: 10
  initial_learning_rate: 0.001
  lr_schedule: constant
  batch_size: 256
```

Do **not** modify source code (`.py` files).  If a bug surfaces,
load the `python-dev` skill and fix it as a separate commit with
`fix:` prefix before resuming the HPO loop.

#### 5 — Repro

Run the DVC stage for the model being optimised:

```bash
dvc repro train@dataset<X>-<model>
```

- Output goes to stdout/stderr; pipe to a log file if the
  iteration will take long: `nohup dvc repro ... > iterN.log 2>&1 &`
- Wait for completion: poll with `tail -f iterN.log` or
  check process status with `ps`.
- Verify exit code is 0 before reading metrics.
- The evaluate stage runs automatically if `dvc.yaml` defines it
  as a downstream dependency.  If not, run it separately:

  ```bash
  dvc repro evaluate@dataset<X>-<model>
  ```

#### 6 — Read new metrics

Same as step 1.  Read `results/<target>/<model>/metrics.yaml`.

#### 7 — Compare

```python
improvement = old_min_val_loss - new_min_val_loss  # negative = better
```

| Condition | Action |
|-----------|--------|
| `improvement > 0.5` (val_loss dropped by >0.5) | Keep config, commit |
| `0 < improvement <= 0.5` | Keep config, commit (marginal) |
| `improvement <= 0` (val_loss stayed same or rose) | Revert config change, try different param |
| `new_min_val_loss` is NaN | Revert, try different approach |

When reverting: `git checkout -- params/models/<target>/<model>.yaml`

#### 8 — Log to hpo_study.md

Append one row to the Progress table in the study plan:

```markdown
| # | Date | Model | Target | Params changed | Train loss | Val loss | Δ val_loss | Commit |
|---|------|-------|--------|----------------|------------|----------|------------|--------|
| 1 | 2026-05-22 | bernstein_nf | dla | lr: 0.001→0.0005 | -140.86 | -130.84 | -32.70 | abc1234 |
```

Always include the short commit hash so each iteration is traceable.

#### 9 — Check stopping criteria

Evaluate against the criteria from the study plan.  Also visual:
if the last 3 iterations show diminishing Δ (e.g. -0.1, -0.05, -0.02),
the model is near its optimum for the current search space.

If stopping criterion met:
1. Write a summary paragraph in `hpo_study.md` with the best config
   found and its metrics.
2. Commit:
   ```
   feat(hpo): <target> -- <model> optimised (val_loss: <best>)
   ```

If not met, go to step 1.

---

## Commit conventions

Every iteration gets its own commit on the `dev` branch:

```
feat(hpo): <target> iter<N> -- <model>: <param> <old>→<new> (val: <old>→<new>)
```

Examples:

```
feat(hpo): dla iter3 -- bernstein_nf: lr 0.001→0.0005 (val: -98→-131)
feat(hpo): dla iter4 -- bernstein_nf: dropout 0.0→0.1 (val: -131→-129, revert)
feat(hpo): ofen_g_koks iter1 -- spline_nf: nbins 8→12 (val: -45→-52)
```

Body (if helpful): a one-line note like "overfitting on zero-heavy
data — adding regularisation" or "healthy convergence, increasing
capacity".

After committing, push when convenient — the commit log itself is
the progress tracker.

---

## Multi-target strategy

Optimise one target completely before moving to the next.
Typical order: primary target (most data, cleanest signal) →
secondary targets.

When switching targets, update the `hpo_study.md` plan header and
create a new Progress section.  The commit prefix changes to the
new target name.

---

## Common pitfalls

| Problem | Detection | Action |
|---------|-----------|--------|
| NaN loss | `metrics.yaml` has `nan` | Revert, try cosine decay LR or add Scale bijector |
| val_loss oscillates | `final_val_loss > min_val_loss` | Add dropout, enable batch_norm, reduce LR |
| Model never learns | `min_loss` stays positive | Reduce LR (log-scale), try cosine decay |
| No improvement after N=3 iter | Δ < 0.1 per step | Stop this model, declare optimum reached |
| `invert: true` missing | val_loss >> 0 for NF models | Add to `bijector_kwargs` (non-Scale only) |
| Pre-commit hook fails | Commit rejected | Fix formatting, re-commit |

---

## Key references

- `hpo_study.md` — study plan + progress at repo root
- `params/models/<target>/<model>.yaml` — per-target model config
- `results/<target>/<model>/metrics.yaml` — per-run metrics
- `dvc repro <stage>` — DVC pipeline execution
- `ml-project` skill — DVC `foreach` layout, MLflow, project structure
- `git-conventions` skill — branching, commit messages, pre-commit
- `python-dev` skill — YAML editing, uv, analysis scripts
