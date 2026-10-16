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
metadata: {stack: ml, audience: researchers, requires: [git-conventions, python-dev]}
---

# Skill: ML Research Projects

## Project structure

```
<project>/
├── data/                    # DVC-tracked input data
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
│       ├── __init__.py      # Package docstring + optional monkey-patches
│       ├── data.py          # Data loading / preprocessing
│       ├── distributions.py # Custom distribution definitions
│       ├── models.py        # Model builders
│       └── utils.py         # I/O helpers, logging, config
├── test/
│   ├── README.md            # what the tests guarantee + where truth comes from
│   ├── conftest.py
│   ├── test_data.py
│   └── test_models.py
├── simulations/             # in-package: numpy-only DGPs with known truth
├── params/
│   ├── target_a.yaml        # Per-target hyperparameters
│   └── target_b.yaml
├── params.yaml              # Global DVC pipeline params
├── dvc.yaml                 # DVC pipeline definition
├── dvc.lock                 # Locked pipeline (committed)
├── hpo_study.md             # HPO phase log
├── pyproject.toml            # (see python-dev skill)
├── .pre-commit-config.yaml  # (see git-conventions skill)
└── README.org               # Paper reference + reproduction guide
```

### Package philosophy

Keep `src/<package>/` to at most 5 modules. Scripts are thin CLI
wrappers that call package functions. Shared logic lives in the
package.

Scripts read CLI arguments only, never `params.yaml`. DVC passes
the parameters as `--<key>=<value>` flags.

### `__init__.py` for monkey-patching

Register custom distributions or layers into third-party libraries
in `__init__.py`, so that the patch runs once at import, before any
model code:

```python
""".. include:: ../../README.md"""

from <package> import distributions as _distributions

# Register the custom parameterisation into the upstream package
import <upstream-package>.distributions  # noqa: F401
```

## DVC pipeline design

### params.yaml: global configuration

```yaml
targets: [<target-a>, <target-b>]

data:
  raw_path: "data/raw"
  processed_path: "data/processed"
  file_format: "feather"

split:
  train_ratio: 0.7
  val_ratio: 0.15
  test_ratio: 0.15
  shuffle: true
  seed: 42

train:
  max_epochs: 500
  patience: 50
  learning_rate: 0.001
  batch_size: 256
```

### dvc.yaml: foreach over targets

Use DVC `foreach` to parallelise across targets or datasets:

```yaml
stages:
  prepare_features:
    foreach: ${targets}
    do:
      cmd: python scripts/prepare_features.py --target ${item}
        --input data/raw --output data/processed/${item}
      deps:
        - data/raw
        - scripts/prepare_features.py
      params:
        - data
      outs:
        - data/processed/${item}/features.feather

  train:
    foreach: ${targets}
    do:
      cmd: >-
        python scripts/train.py --target ${item}
          --config params/${item}.yaml
          --train-data data/processed/${item}/train.feather
          --val-data data/processed/${item}/val.feather
          --outdir results/${item}
      deps:
        - data/processed/${item}
        - params/${item}.yaml
        - scripts/train.py
        - src/<package>/models.py
      params:
        - train
      outs:
        - results/${item}/model
      metrics:
        - results/${item}/metrics.json:
            cache: false
```

### Stage conventions

| Stage | Purpose | Outputs |
|-------|---------|---------|
| `prepare_features` | Load raw data, engineer features, save as Feather | `features.feather` |
| `split_data` | Train/val/test split | `{train,val,test}.feather` |
| `train` | Fit model, save weights + metrics | `model/`, `metrics.json` |
| `evaluate` | Compute eval metrics + plots | `figures/`, `eval_metrics.json` |

Intermediate pipeline outputs are Feather files
(`pd.read_feather`, `DataFrame.to_feather`).

### Per-target model configs

Place dataset-specific hyperparameters in `params/<target>.yaml`:

```yaml
model:
  architecture: "maf"
  n_bijectors: 4
  hidden_units: [64, 64]
  activation: "relu"
  dropout_rate: 0.1

train:
  learning_rate: 0.001
  lr_schedule: "cosine_decay"
  optimizer: "adam"
```

## Experiment tracking with MLflow

Add `mlruns/` to `.gitignore`. Use `mlflow ui` to inspect runs.

### Logging from a training script

```python
import mlflow

def train(...) -> dict[str, float]:
    """Run training and return metrics dict."""
    mlflow.log_params(config["model"])
    mlflow.log_param("target", target)

    for epoch in range(n_epochs):
        loss = train_step(...)
        val_loss = validation_step(...)
        mlflow.log_metrics(
            {"loss": loss, "val_loss": val_loss},
            step=epoch,
        )

    mlflow.log_artifact(f"{outdir}/learning_curve.png")
    mlflow.log_artifact(f"{outdir}/model_weights")
    return {"val_loss": val_loss}
```

## HPO study structure

Document hyperparameter optimisation as a structured log in
`hpo_study.md`. A manual study commits once per phase. The
autonomous loop (`auto-hpo-studies`) commits once per iteration
instead, in its own format. That skill wins while it runs.

### Template

```markdown
# HPO Study: `<model-type>` on `<dataset>`

## Phase 1: Constant LR sweep

**Objective:** Find optimal learning rate for the base architecture.

| Run | learning_rate | n_bijectors | val_loss | Notes |
|-----|---------------|-------------|----------|-------|
| 1   | 1e-2          | 4           | 0.452    | diverges after 100 epochs |
| 2   | 1e-3          | 4           | 0.231    | stable, underfits slowly  |
| 3   | 3e-4          | 4           | **0.198** | best so far               |
| 4   | 1e-4          | 4           | 0.212    | converges too slowly      |

**Winner:** `learning_rate = 3e-4`

## Phase 2: ...
```

### Conventions

- Manual studies: one phase per commit with message
  `feat(hpo): <target> phase <N>: <summary>`.
- The commit body includes the markdown table from `hpo_study.md`.
- File results from intermediate runs are cleaned up:
  `git rm -r results/*_v2 results/*_v3` before committing.
- Only the final configs for each phase remain in the repo.

## Validating research code

"It runs without error" is not a test. Research code needs a
reference to be wrong against. Build one.

### Simulate with known ground truth

Write the data-generating process yourself, in **numpy only**, with
no import of the model under test. This independence makes it a
reference. Ship each frozen dataset with the truth beside it:

```
data/<dgp-name>/
├── obs.csv        # frozen sample, committed
└── truth.json     # the true parameters / effects of the generator
```

Give every generator a CLI that regenerates its own folder from a
fixed seed, and a `REGISTRY` dict so tests and scripts look DGPs up
by name.

### Frozen data is a contract

- Tests assert each CSV regenerates **bit-identically** from its
  stored seed. Without that, the data silently drifts away from
  `truth.json` and every number in the paper is unverifiable.
- A new seed or changed equations means a **new folder**, never an
  in-place edit. Old results keep pointing at old data.
- Never regenerate `data/` to make a failing test pass.

### Order tests by how much trust they carry

1. **Mathematical identities**: must hold by the maths, with no
   reference implementation: a transform inverts, a likelihood
   decomposes, a distributional claim survives a KS test.
2. **Equivalence to independent implementations**: the strongest
   external check. Where a special case of your model *is* a
   classical model, it must match software written by other people
   in another language (`statsmodels`, R). Commit the reference
   output so the suite runs without R installed.
3. **Known-truth recovery**: the generator's true parameters,
   effects and counterfactuals, which no real dataset exposes.
4. **Frozen-data contracts**: the regeneration checks above.
5. **Stability guards**: one test for each fixed regression, with
   the symptom in a comment.

### Tolerances that catch regressions

A ground-truth bound is for regressions, not for precision claims.

- Keep a bound between about **1.5x and 4x** of its measured value.
  Below 1.5x it fails on another machine for no reason. Above 4x it
  catches nothing. A deliberately wide bound carries a `"why"` note.
- After a change that moves numbers, re-run **every** affected variant
  and re-pin all centres from that run, not only the ones that failed.
- Put a precision claim into its own tight metric.

### Configs and names

- Experiment configs write every option out (see `dev-conventions`,
  section 1, "Explicit configuration").
- Never replace an existing variant or change what it means. Add a
  new config for a new idea. Existing configs get only hyperparameter
  changes and fixes.
- Names follow the notation of the paper.

### test/README.md

Document what the suite guarantees, not how to run it: the five
kinds of test, the file-by-file table, and **how each reference
number was obtained** (by construction, analytically,
Monte Carlo from the generator, or other software).

Mark anything that trains `@pytest.mark.slow` (see `python-dev`,
"Tests").

## Paper-oriented code structure

### figures/ directory

All paper figures live in `figures/` at repo root. Each figure
has a script in `scripts/` that regenerates it.

### Figure scripts

Each figure script follows `python-dev` ("Figures"), and its
`__main__` block saves the figure into `figures/`.

### README.org for paper reproduction

```org
* <Paper Title>

Summary and BibTeX reference.

** Reproducing results

#+begin_src bash
  dvc checkout
  dvc repro
#+end_src

** Citation
#+begin_src bibtex
  @inproceedings{...}
#+end_src
```

## Script conventions

### CLI interface

Use `argparse`. Scripts receive all inputs as CLI flags and never
import from other scripts. Scripts stay dumb: no
mode switches such as `--outcome` or `--variant`. Each variant gets
its own config file or `dvc.yaml` entry, and the duplication is fine.
`params.yaml` and `dvc.yaml` are the single source of truth. Write
no wrapper scripts such as `train.sh` around them.

```python
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

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
- **python-dev**: Python project structure, pyproject.toml, ruff,
  NumPy docstrings, pytest, figures.
