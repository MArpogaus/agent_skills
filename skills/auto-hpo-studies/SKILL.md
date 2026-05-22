---
name: auto-hpo-studies
description: >
  Automated HPO study workflow: phased hyperparameter sweeps via DVC repro,
  MLflow experiment tracking, hpo_study.md logging, per-target config
  management, and one-commit-per-phase conventions.
license: MIT
compatibility: opencode
metadata:
  stack: ml
  audience: researchers
---

## When to use

Load when designing or executing a hyperparameter optimization study
for an ML research project — setting up search phases, running
batched DVC repro sweeps, analyzing results, updating configs,
and logging outcomes in `hpo_study.md`.

---

## Prerequisite skills

- **ml-project** — DVC pipeline structure, per-target configs,
  MLflow tracking, project layout.
- **git-conventions** — two-branch flow, conventional commits,
  pre-commit hooks.

---

## HPO study principles

- **Only** edit `params.yaml` and `params/models/<target>/` —
  no code changes during HPO (bugfixes excepted).
- Start **very small** and only increase capacity when underfitting
  is evident.
- One commit per meaningful iteration documenting `val_loss` diffs.
- Use validation loss (NLL) as the primary selection metric; only
  consult eval metrics at the end.

---

## Study structure

Every HPO study is documented in `hpo_study.md` at the repo root.
Each phase is one numbered section with:

1. **Objective** — what question this phase answers
2. **Hyperparams** — fixed params table
3. **Models tested** — list of model variants
4. **Commands** — `dvc repro` / `nohup` command used
5. **Results table** — markdown with `min_val_loss`, `best_epoch`,
   and optionally eval metrics
6. **Findings** — qualitative summary
7. **Decision** — next step or winner

### Phase naming convention

| Phase | Focus | Typical changes |
|-------|-------|-----------------|
| Phase 1 | Constant LR benchmark | Set all models to identical LR=0.001, constant schedule |
| Phase 2 | Learning rate schedule | Compare constant vs cosine decay |
| Phase 3 | Capacity increase | Raise `num_parameters`, `hidden_units`, `n_bijectors`, `nbins` |
| Phase 3b–3z | Incremental capacity | Stepwise increase until overfitting or diminishing returns |
| Phase N | Export winner | Apply best params to all remaining targets |

---

## Workflow phases

### Phase 1: Define models and baseline

1. List all model variants in `hpo_study.md`.
2. Set identical baseline hyperparameters across all models
   (LR, epochs, batch size, hidden units).
3. Run all models in one batch via DVC:
   ```bash
   nohup dvc repro train@dataset0-<model1> train@dataset0-<model2> ... \
     > phase1_training.log 2>&1 &
   ```
4. Followed automatically by `evaluate@dataset0-*` stages.
5. Collect results from `results/<target>/<model>/metrics.yaml`
   or via MLflow query.

### Phase 2: Analyze and iterate

1. Query MLflow to compare runs:
   ```bash
   uv run python -c "
   import mlflow
   from mlflow.tracking import MlflowClient
   client = MlflowClient()
   exp = client.get_experiment_by_name('<experiment-name>')
   runs = client.search_runs(exp.experiment_id)
   for r in runs:
       print(r.data.metrics.get('min_val_loss'), r.data.params.get('model'))
   "
   ```
2. Identify winners and underperformers.
3. Decide next phase: adjust LR schedule, increase capacity,
   or export winners.

### Phase 3: Modify configs

Edit per-target model configs in `params/models/<target>/<model>.yaml`:

Common changes:

| Field | Example | Effect |
|-------|---------|--------|
| `initial_learning_rate` | `0.001` → `0.0005` | Slower convergence, finer optima |
| `lr_schedule` | `constant` → `cosine_decay` | Better late-stage convergence |
| `num_parameters` | `8` → `12` | More bijector/spline knots |
| `hidden_units` | `[128, 128]` → `[256, 256]` | Wider layers |
| `max_epochs` | `200` → `400` | More training time |
| `early_stopping_patience` | `10` → `50` | Longer plateau tolerance |
| `dropout` | `0.0` → `0.1` | Regularization |
| `batch_norm` | `false` → `true` | Training stability |

Do **not** modify source code during HPO. Constrain changes to
YAML config files only.

### Phase 4: Run sweep and log

```bash
# Run single model
dvc repro train@dataset0-<model>
dvc repro evaluate@dataset0-<model>

# Run batch of models in background
nohup dvc repro train@dataset0-<model_a> train@dataset0-<model_b> ... \
  > phaseN_training.log 2>&1 &

# Monitor progress
tail -f phaseN_training.log
```

After the run completes:

1. Check metrics in `results/<target>/<model>/metrics.yaml` or
   MLflow UI (`mlflow ui`).
2. Update the results table in `hpo_study.md`.
3. Write findings and decision.

### Phase 5: Commit

```bash
# Clean up stale intermediate run directories if any
git rm -r results/*_v2 results/*_v3

dvc commit train@dataset0-<model> evaluate@dataset0-<model>
git add dvc.lock hpo_study.md params/models/<target>/
git commit -m "feat(hpo): <target> Phase <N> -- <summary>"
```

Commit message pattern: `feat(hpo): <target> Phase <N> -- <summary>`

The commit body should include the results table from `hpo_study.md`.

---

## Per-target config conventions

Configs follow this structure:

```yaml
model:
  architecture: "<model_type>"
  bijector: "<bijector_name>"
  bijector_kwargs:
    num_parameters: <N>
    invert: <true|false>
  base_distribution_kwargs:
    distribution_name: "<normal|lognormal>"
  hidden_units: [<int>, <int>]
  dropout: <float>
  batch_norm: <bool>

train:
  max_epochs: <int>
  early_stopping_patience: <int>
  initial_learning_rate: <float>
  lr_schedule: "<constant|cosine_decay>"
  decay_steps: <int>
  batch_size: <int>
```

---

## Common HPO patterns

### NaN loss in lognormal baseline

LogNormal base distributions can produce NaN loss when:

1. The bijector maps data to values near zero (log(0) = -∞).
2. The covariance matrix becomes singular.
3. An `Exp` bijector combined with small-scale data creates
   numerical instability.

**Fixes:** Switch to cosine decay LR schedule, use Scale bijector
as wrapper, or increase `epsilon` in the lognormal parameterization.

### Overfitting on zero-heavy data

When a target has many zero values (e.g. 24% zeros):

1. The model predicts near-zero variance → extremely high NLL.
2. `val_loss` oscillates wildly between positive and negative.

**Fixes:** Add `dropout: 0.1`, enable `batch_norm: true`, reduce
`initial_learning_rate` to `0.0005`.

### Missing `invert: true` in bijectors

Non-Scale bijectors (BernsteinPolynomial, RationalQuadraticSpline)
without `invert: true` apply the forward direction during training,
producing garbage predictions. Scale (wrapper) bijectors are
unaffected because `invert: true` lives inside their
`nested_bijectors` list items.

**Check:** For every non-Scale NF config, ensure `invert: true`
is present at the `bijector_kwargs` level.

### DVC stage naming

DVC stages follow the pattern `<stage_name>@<dataset_id>`:

| Dataset ID | Target |
|------------|--------|
| `dataset0` | Primary target (e.g. DLA) |
| `dataset1` | Secondary target A |
| `dataset2` | Secondary target B |
| `dataset3` | Secondary target C |

---

## Key references

- `hpo_study.md` — study log at repo root
- `params/models/<target>/` — per-target model configs
- DVC pipeline docs: https://dvc.org/doc
- MLflow tracking docs: https://mlflow.org/docs/latest/tracking.html
