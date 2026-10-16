---
name: python-dev
description: >
  Python project conventions: skeleton-based setup, setuptools with
  one version source, uv without touching the user's environment,
  NumPy docstrings, pytest-xdist, CI matrix, MkDocs + mkdocstrings +
  mike docs, commitizen, README.org and matplotlib figures. Use in
  any repo with `pyproject.toml` or Python sources, before editing
  Python code, tests, docs, CI or uv settings.
license: MIT
compatibility: claude-code opencode
metadata: {stack: python, requires: [dev-conventions, git-conventions]}
---

# Skill: Python Development

## When to use

Load this skill before you create or change a Python project of the
user: `pyproject.toml`, source, docstrings, tests, CI, docs or
configuration. Also load it to port a generic improvement back to
the skeleton.

This skill holds only what no tool enforces. Ruff and pre-commit
enforce quotes, line length, import order, formatting and whitespace.
Do not hand-check these rules; run the hooks.

Read [reference.md](reference.md) when you write the pre-commit, test or docs configuration.

## Design

These rules extend the principles in `dev-conventions`.

- Write functions. Write a class only when state and behaviour
  really belong together.
- Use built-ins before custom machinery. Select an implementation
  with `getattr` or an `importlib` dotted path, not a registry.
  Check subclasses with `__init_subclass__`, not with a metaclass.
- Do not accept a keyword argument that the function does not use.
  Do not add `**kwargs` "for later".
- Scripts have no mode switches. Write one config file for each
  variant. Duplication between configs is acceptable.
- Annotate every function signature. Use `X | None` and `list[X]`.
- Do not use `ty`.

## Project setup

New projects start from the skeleton
<https://github.com/MArpogaus/minimal_python_project_skeleton>.
When the skeleton and this skill disagree, this skill is correct.
Fix the skeleton in the same pass.

1. Clone the skeleton and remove its `.git` folder.
2. Run `git init` and make the root commit and the `dev` branch as
   `git-conventions` says ("Two-branch flow").
3. Adapt the metadata, the package directory and the dependencies.
   Commit on `dev`.

When you make a generic config change (hook revisions, CI, ruff
rules), apply the same change to the skeleton. Commit it there
separately, for example `chore: bump pre-commit ruff rev`.

Layout:

```
.github/workflows/   test, pre-commit, docs, release (+ example)
src/<package>/       __init__.py has a one-line docstring
test/                conftest.py, test_<module>.py
docs/                index.md, api/<module>.md
notebooks/           jupytext py:percent files
README.org           source; README.md is exported and committed
CHANGELOG.md         written by `cz bump` only
pyproject.toml  mkdocs.yml  uv.lock  .envrc  .pre-commit-config.yaml
```

Source modules use `# %%` cell markers for sections: description,
imports, globals, private helpers, public functions.

## pyproject.toml

Use setuptools. Do not use hatchling.

```toml
[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools >= 61", "setuptools_scm>=7"]

[project]
name = "<hyphenated-name>"
dynamic = ["version"]
requires-python = ">=3.11"
readme = "README.md"
dependencies = []  # keep minimal

[project.optional-dependencies]
test = ["pytest", "pytest-xdist"]
docs = ["mkdocs-material", "mkdocstrings[python]", "mike"]
develop = ["<package>[test]", "commitizen", "pre-commit", "ruff"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools_scm]
local_scheme = "no-local-version"

[tool.ruff.lint]
select = ["I", "E", "F", "D", "UP"]

[tool.ruff.lint.pydocstyle]
convention = "numpy"

[tool.pytest.ini_options]
addopts = ["-v", "--tb=short", "-n", "auto", "--dist=loadfile"]
testpaths = ["test"]

[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "scm"
version_scheme = "pep440"
tag_format = "v$version"
annotated_tag = true
major_version_zero = true
update_changelog_on_bump = true
```

Always set `convention = "numpy"`. Without it, ruff reports rules
that NumPy style does not use.

### One version source

The version is in git tags only. Never write a literal version into
`pyproject.toml` or `__init__.py`. When the package needs
`__version__`, read the installed metadata:

```python
from importlib.metadata import version

__version__ = version("<hyphenated-name>")
```

### Pre-commit

Use the base hooks from `git-conventions` ("Pre-commit hooks"),
plus ruff (`--fix`) and ruff-format. Exclude `uv.lock` from
`pretty-format-toml`, because uv owns that file. The additions are
in [reference.md](reference.md).

## uv and the environment

The environment and the lock file belong to the user. Do not run
`uv sync`, `uv run`, `uv add`, `uv remove` or `uv lock` unless the
user asks. `uv run` and `uv sync` re-sync `.venv` and can replace
the interpreter under a running kernel.

- Use the existing `.venv/bin/python` read-only. For a quick check,
  use the system `python3`.
- Report a missing package. Do not install it.
- `uv.lock` is committed. `.envrc` holds `layout python` for direnv.
- When in doubt, ask.

## Docstrings

Every public module, class, function and method gets a NumPy
docstring. Ruff `D` checks presence and form.

- The summary line is one sentence that ends with a period.
- Sections, in this order when needed: `Parameters`, `Returns`,
  `Raises`, `Attributes`, `References`, `Notes`.
- An underline of dashes has the same length as its header.
- A parameter entry is `name : type`. For an optional parameter,
  write `type, optional` and end with ``by default ``value``.``.
- Write mathematics in LaTeX: `:math:` inline, `.. math::` for a
  block.
- Docstrings are API reference only. Do not put examples, tutorials
  or background in a docstring or on an API page.
- Usage examples live only in notebooks.

## Notebooks

Notebooks are jupytext `py:percent` files. The `.py` file is the
source. Ignore `notebooks/*.ipynb` in git. Regenerate a notebook
with `uvx jupytext --to ipynb <name>.py`. A notebook with a Colab
badge is the one exception: track that single `.ipynb` without
output and regenerate it in the same commit as its `.py`.

For a change to a notebook plot, edit the `.py` file only. Do not
run the notebook unless the user asks. Say that the edit did not
run.

## Tests

- Tests live in `test/`, one `test_<module>.py` for each module, one
  `class Test<Unit>` for each function or logical unit.
- pytest-xdist runs the suite in parallel (`-n auto`). Tests must
  not depend on order or shared state.
- Use `pytest.raises(..., match=...)`, `np.testing.assert_allclose`
  and `pd.testing.assert_frame_equal`.
- Mark each test that trains or fits a model `@pytest.mark.slow`.

## CI

| Workflow | Trigger | Job |
|---|---|---|
| `test.yaml` | push, PR | ubuntu, windows, macos, each with the oldest and newest supported Python (now 3.11 and 3.14); `-m "not slow"` |
| `test.yaml` | nightly cron, `workflow_dispatch` | full suite, `timeout-minutes` set |
| `pre-commit.yaml` | push | `pre-commit/action` |
| `docs.yaml` | push to `main`, `dev`, `dev-*` | MkDocs with mike to `gh-pages` |
| `release.yaml` | `main`, `v*` tags | TestPyPI from `main`; PyPI and GitHub Release from tags |

Pin the actions as `git-conventions` says ("CI workflows").

## Documentation

The docs are a MkDocs Material site. mkdocstrings renders the API
from the NumPy docstrings. mike publishes one version for each
branch to `gh-pages`.

- `main` deploys as `latest`, the default version. Each dev branch
  deploys under its own name.
- `mkdocs.yml` sets `strict: true`.
- `docs/index.md` holds only `--8<-- "README.md"`.
- Write README links to repository files as full GitHub URLs.
  Relative links break the strict build and PyPI.
- Each module gets one page `docs/api/<module>.md` with
  `::: <package>.<module>`.
- Set GitHub Pages to branch `gh-pages`, path `/ (root)`. A `/docs`
  path fails the build.

## Changelog and releases

Commitizen writes `CHANGELOG.md` during `cz bump`. Never edit the
changelog by hand. The release flow is in `git-conventions`.

## README.org

- `README.org` is the source. Export `README.md` with Emacs and
  commit both in the same commit. `pyproject.toml` reads
  `README.md`.
- Structure, after the Best-README-Template: badges, title, local
  TOC, About The Project, Getting Started (Installation, Usage),
  Contributing, License, Contact.
- Install instructions use `uv add <package>`.
- Code blocks use `:session`, a `#+NAME:` and an `:exports` value.
  Use `code` for imports and plots, `both` when the output helps,
  `nil` for install blocks.
- Blocks with the same `:tangle` target become one runnable script.

## Figures

- A plot function accepts an optional `ax`, creates a figure only when
  `ax` is `None`, and returns the `plt.Figure`.
- The caller saves PDF and PNG and then calls `plt.close(fig)`.
- Write labels with mathematics in LaTeX, for example
  `r"$\sigma^2$"`.
- Colours follow the target medium. For a slide deck, use the theme
  foreground and accent colours.
- Across one project, use one colour for each meaning. Define the
  colours once and import them.

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, CI workflows, tagging and releases.
