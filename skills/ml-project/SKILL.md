---
name: ml-project
description: >
  Research ML project conventions: DVC pipeline orchestration,
  MLflow experiment tracking, HPO study logs, paper-oriented
  code structure, per-target model configs, and reproducible
  figure generation. Use when setting up or changing the experiment
  code of a research project, or in a repo with `dvc.yaml`,
  `params.yaml` or an `mlruns/` directory.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ml, audience: researchers, requires: [dev-conventions, git-conventions, python-dev]}
---

# Skill: ML Research Projects

## Hard rules

- Scripts read CLI arguments only, never `params.yaml`. Interpolate
  each global parameter into `cmd`, for example
  `--max-epochs ${train.max_epochs}`. The per-target file is the one
  exception. Pass it as `--config params/${item}.yaml`. List it under
  `params:` (`- params/${item}.yaml:`), not under `deps:`.
- `params.yaml` and `dvc.yaml` are the single source of truth. Write
  no wrapper scripts (`train.sh`) around them.
- Never tune the seed. Keep it fixed and fix a bad fit with the
  hyperparameters.
- Never delete an experiment variant (a `dvc.yaml` entry or its config
  file) or change what its name means. Tuning the values in
  `params/<target>.yaml` is allowed.
- Never regenerate `data/` to make a failing test pass.
- Docs describe the method and how to run it. Results live in result
  files, reports and slides, not in docs.

## Project structure

```
<project>/
├── data/
│   ├── raw/                 # DVC-tracked input (`dvc add data/raw`)
│   └── processed/           # pipeline stage outputs
├── results/                 # DVC-tracked experiment outputs
├── figures/                 # Paper figures (committed)
├── logs/                    # Training logs (gitignored)
├── mlruns/                  # MLflow runs (gitignored)
├── scripts/                 # CLI entry points
│   ├── prepare_features.py
│   ├── split_data.py
│   ├── train.py
│   ├── evaluate.py
│   └── hpo.py
├── src/
│   └── <package>/
│       ├── __init__.py      # docstring + monkey-patches
│       ├── data.py          # Data loading / preprocessing
│       ├── distributions.py # Custom distribution definitions
│       ├── models.py        # Model builders
│       ├── simulations.py   # numpy-only DGPs with known truth
│       └── utils.py         # I/O helpers, logging, config
├── test/
│   ├── README.md            # what the tests guarantee + where truth comes from
│   ├── conftest.py
│   ├── test_data.py
│   └── test_models.py
├── params/
│   ├── target_a.yaml        # Per-target hyperparameters
│   └── target_b.yaml
├── params.yaml              # Global DVC pipeline params
├── dvc.yaml                 # DVC pipeline definition
├── dvc.lock                 # Locked pipeline (committed)
├── hpo_study.md             # HPO phase log
├── pyproject.toml           # (see python-dev skill)
├── .pre-commit-config.yaml  # (see git-conventions skill)
└── README.org               # Paper reference + reproduction guide
```

### Package philosophy

Keep `src/<package>/` to at most 5 modules besides `__init__.py`.
Scripts are thin CLI wrappers that call package functions.

### `__init__.py` for monkey-patching

Register custom distributions or layers into third-party libraries
in `__init__.py`, so that the patch runs once at import, before any
model code:

```python
"""<One-line package summary>."""

# Importing the module registers the custom distributions upstream.
from <package> import distributions  # noqa: F401
```

## DVC pipeline design

### params.yaml: global configuration

```yaml
targets: [<target-a>, <target-b>]

data:
  raw_path: "data/raw"
  processed_path: "data/processed"

split:
  train_ratio: 0.7
  val_ratio: 0.15
  test_ratio: 0.15
  seed: 42

train:
  max_epochs: 500
  patience: 50
  batch_size: 256
```

The per-target values live only in
`params/<target>.yaml`.

### dvc.yaml: foreach over targets

Run each stage per target with DVC `foreach`:

```yaml
stages:
  prepare_features:
    foreach: ${targets}
    do:
      cmd: >-
        python scripts/prepare_features.py --target ${item}
        --input ${data.raw_path} --output ${data.processed_path}/${item}
      deps:
        - ${data.raw_path}
        - scripts/prepare_features.py
      params:
        - data
      outs:
        - ${data.processed_path}/${item}/features.feather

  split_data:
    foreach: ${targets}
    do:
      cmd: >-
        python scripts/split_data.py
        --input ${data.processed_path}/${item}/features.feather
        --outdir ${data.processed_path}/${item}
        --train-ratio ${split.train_ratio} --val-ratio ${split.val_ratio}
        --test-ratio ${split.test_ratio} --seed ${split.seed}
      deps:
        - ${data.processed_path}/${item}/features.feather
        - scripts/split_data.py
      params:
        - split
      outs:
        - ${data.processed_path}/${item}/train.feather
        - ${data.processed_path}/${item}/val.feather
        - ${data.processed_path}/${item}/test.feather

  train:
    foreach: ${targets}
    do:
      cmd: >-
        python scripts/train.py --target ${item}
        --config params/${item}.yaml
        --train-data ${data.processed_path}/${item}/train.feather
        --val-data ${data.processed_path}/${item}/val.feather
        --max-epochs ${train.max_epochs} --patience ${train.patience}
        --batch-size ${train.batch_size}
        --outdir results/${item}
      deps:
        - ${data.processed_path}/${item}/train.feather
        - ${data.processed_path}/${item}/val.feather
        - scripts/train.py
        - src/<package>/models.py
      params:
        - train
        - params/${item}.yaml:
      outs:
        - results/${item}/model
      metrics:
        - results/${item}/metrics.json:
            cache: false
```

### Stage conventions

Intermediate pipeline outputs are Feather files
(`pd.read_feather`, `DataFrame.to_feather`).

### Per-target model configs

Place dataset-specific hyperparameters in `params/<target>.yaml`:

```yaml
model:
  architecture: "mlp"
  n_layers: 4
  hidden_units: [64, 64]
  activation: "relu"
  dropout_rate: 0.1

train:
  learning_rate: 0.001
  lr_schedule: "cosine_decay"
  optimizer: "adam"
```

## Experiment tracking with MLflow

### Logging from a training script

`outdir` is `results/<target>`. The logged artifacts are the stage
`outs` of `dvc.yaml`.

```python
import mlflow
import numpy as np


def train(
    target: str, config: dict, n_epochs: int, outdir: str
) -> dict[str, float]:
    """Train and return the metrics."""
    mlflow.set_tag("target", target)
    mlflow.log_params(config["model"])

    losses, val_losses = [], []
    for epoch in range(n_epochs):
        losses.append(train_step(...))
        val_losses.append(validation_step(...))
        mlflow.log_metrics(
            {"loss": losses[-1], "val_loss": val_losses[-1]},
            step=epoch,
        )

    best_epoch = int(np.argmin(val_losses))
    metrics = {
        "min_val_loss": val_losses[best_epoch],
        "min_loss": min(losses),
        "best_epoch": best_epoch,
    }
    mlflow.log_metrics(metrics)
    mlflow.log_artifacts(f"{outdir}/model", artifact_path="model")
    return metrics
```

## HPO study structure

Document hyperparameter optimisation as a structured log in
`hpo_study.md`. The autonomous loop uses `auto-hpo-studies`.

### Template

```markdown
# HPO Study: `<model-type>` on `<dataset>`

## Phase 1: Constant LR sweep

**Objective:** Find optimal learning rate for the base architecture.

| Run | learning_rate | n_layers    | val_loss | Notes |
|-----|---------------|-------------|----------|-------|
| 1   | 1e-2          | 4           | 0.452    | diverges after 100 epochs |
| 2   | 3e-4          | 4           | **0.198** | best so far               |

**Winner:** `learning_rate = 3e-4`

## Phase 2: ...
```

### Conventions

- Manual studies: one phase per commit with message
  `feat(hpo): <target> phase <N>: <summary>`.
- The commit body includes the markdown table from `hpo_study.md`.
- Delete the outputs of discarded runs (`rm -r results/<target>_v2`).
  Their `dvc.yaml` entry and config file stay (hard rules).
  Run `dvc gc -w` only after the user agrees.

## Validating research code

"It runs without error" is not a test. Research code needs a
reference to be wrong against. Build one.

### Simulate with known ground truth

Write the data-generating process yourself, in **numpy only**, with
no import of the model under test. Ship each frozen dataset with the
truth beside it:

```
data/raw/<dgp-name>/
├── obs.csv        # frozen sample
└── truth.json     # the true parameters / effects of the generator
```

Give every generator a CLI that regenerates its own folder from a
fixed seed. Tests and scripts look a DGP up by name with
`getattr(<package>.simulations, name)`.

### Frozen data is a contract

- Tests assert each CSV regenerates **bit-identically** from its
  stored seed. Else the data drifts away from `truth.json`.
- A new seed or changed equations means a **new folder**, never an
  in-place edit. Old results keep pointing at old data.

### Order tests by how much trust they carry

1. **Mathematical identities**: must hold by the maths, with no
   reference implementation: a transform inverts, a likelihood
   decomposes, a distributional claim survives a KS test.
2. **Equivalence to independent implementations**: when a special
   case *is* a classical model, it must match software by other
   authors in another language (`statsmodels`, R). Commit the reference
   output so the suite runs without R installed.
3. **Known-truth recovery**: the generator's true parameters,
   effects and counterfactuals.
4. **Frozen-data contracts**: the regeneration checks above.
5. **Stability guards**: one test for each fixed regression, with
   the symptom in a comment.

### Tolerances that catch regressions

A ground-truth bound is for regressions, not for precision claims.

- Set a bound to 1.5 to 4 times the error measured on this machine.
  Below 1.5 times, it fails on another machine for no reason. Above 4
  times, it catches nothing. A deliberately wide bound carries a
  `"why"` note.
- After a change that moves numbers, re-run **every** affected
  variant. Re-pin all centres from that run, not only the ones that
  failed.
- Put a precision claim into its own tight metric.

### Configs and names

- Experiment configs write every option out (see `dev-conventions`,
  "1. Design principles").
- Names follow the notation of the paper.

### test/README.md

Document what the suite guarantees, not how to run it. List the
five kinds of test and a file-by-file table. State **how each
reference number was obtained**: by construction, analytically,
by Monte Carlo from the generator, or from other software.

## Paper-oriented code structure

### Figures

All paper figures live in `figures/` at the repo root. Each figure
has a script in `scripts/` that follows `python-dev` ("Figures").
Its `__main__` block saves the figure into `figures/`.

### README.org for paper reproduction

```org
* <Paper Title>

Summary and BibTeX reference.

** Reproducing results

#+begin_src bash
  dvc pull
  dvc repro
#+end_src
```

## Script conventions

### CLI interface

Use `argparse`. Scripts never import from other scripts. They have
no mode switches (`dev-conventions`, "1. Design principles").
Each variant gets its own config file or `dvc.yaml` entry.

```python
import argparse
from pathlib import Path

from <package>.data import prepare_features


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare_features(args.input, args.output, target=args.target)


if __name__ == "__main__":
    main()
```

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
- **python-dev**: Python project structure, pyproject.toml, ruff,
  NumPy docstrings, pytest, figures.
