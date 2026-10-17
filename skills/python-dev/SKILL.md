---
name: python-dev
description: >
  Python project conventions: skeleton-based setup, setuptools with
  one version source, uv without touching the user's environment,
  NumPy docstrings, pytest-xdist, CI matrix, MkDocs + mkdocstrings +
  mike docs, commitizen, README.org and matplotlib figures. Use in
  any repo with `pyproject.toml` or Python sources, before editing
  Python code, tests, docs, CI or uv settings, or to port a change
  to the skeleton.
license: MIT
compatibility: claude-code opencode
metadata: {stack: python, requires: [dev-conventions, git-conventions]}
---

# Skill: Python Development

This skill holds only what no tool enforces. Ruff and pre-commit
enforce quotes, line length, import order, formatting and whitespace.
Do not hand-check these rules. Run the hooks.

Read [reference.md](reference.md) when you write the pre-commit, test
or docs configuration.

## Hard rules

- Run no `uv sync`, `uv run`, `uv add`, `uv remove` or `uv lock`
  unless the user asks (section "uv and the environment").
- Never write a literal version into `pyproject.toml` or
  `__init__.py` (section "One version source").
- Usage examples live only in notebooks. Docstrings are API reference
  only. The README shows no code beyond the install command
  `uv add <package>` (`ml-project` adds the reproduction commands).
- Do not run a notebook unless the user asks. Edit its `.py` file
  only, and say that the edit did not run.
- Use setuptools. Do not use hatchling.
- Do not accept a keyword argument that the function does not use.
  Do not add `**kwargs` "for later".
- Apply each config change that fits every project (hook revisions,
  CI, ruff rules) to `<skeleton checkout>` too (section "Project
  setup").

## Design

These rules extend the principles in `dev-conventions`.

- Select an implementation with `getattr` or an `importlib` dotted
  path. Check subclasses with `__init_subclass__`, not with a
  metaclass.
- Annotate every function signature. Use `X | None` and `list[X]`.
- Do not use `ty`.

## Project setup

New projects start from the skeleton
<https://github.com/MArpogaus/minimal_python_project_skeleton>.
When the skeleton and this skill disagree, this skill is correct.

1. Clone the skeleton and remove its `.git` folder.
2. Run `git init` and make the root commit and the `dev` branch as
   `git-conventions` says ("Two-branch flow").
3. Adapt the metadata, the package directory and the dependencies.
   Commit on `dev`.

Make each skeleton change (hard rules) a separate commit in
`<skeleton checkout>`, with a message such as
`chore: bump pre-commit ruff rev`.

Layout:

```
.github/workflows/   test, pre-commit, docs, release (+ example)
src/<package>/       __init__.py has a one-line docstring
test/                conftest.py, test_<module>.py
docs/                index.md, api/<module>.md
notebooks/           jupytext py:percent files
README.org           source; README.md is exported and committed
CHANGELOG.md         written by `cz bump` only, tracked
pyproject.toml  mkdocs.yml  uv.lock  .envrc  .pre-commit-config.yaml
```

Source modules use `# %%` cell markers for sections: description,
imports, globals, private helpers, public functions.

## pyproject.toml

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
docs = ["mkdocs-material", "mkdocstrings[python]", "mike", "mkdocs-bibtex"]
develop = ["<hyphenated-name>[test]", "commitizen", "pre-commit", "ruff"]

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
markers = ["slow: trains or fits; CI runs it nightly only"]

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

The version is in git tags only. When the package needs
`__version__`, read the installed metadata:

```python
from importlib.metadata import version

__version__ = version("<hyphenated-name>")
```

### Pre-commit

Use the base hooks from `git-conventions` ("Pre-commit hooks"),
plus ruff (`--fix`) and ruff-format. The additions are in
[reference.md](reference.md).

### Formatting sweeps

- Make the first `ruff format` of a repo one commit with formatting
  only, message `style: apply ruff-format`.
- Add its full SHA to `.git-blame-ignore-revs`, one SHA per line.
- Do the sweep before a refactor of the same files.

## uv and the environment

The environment and the lock file belong to the user. `uv run` and
`uv sync` re-sync `.venv` and can replace the interpreter under a
running kernel.

- Run code and tests with `.venv/bin/python`. Without `.venv`, use
  the system `python3`.
- A tool for your own use follows `sandbox-env`.
- `uv.lock` is committed. `.envrc` holds `source .venv/bin/activate`,
  so direnv activates the uv `.venv`. Do not use `layout python`: the
  released direnv creates a second venv in `.direnv/`.

## Docstrings

Every public module, class, function and method gets a NumPy
docstring. Ruff `D` checks presence and form.

- The summary line is one sentence that ends with a period.
- Sections, in this order when needed: `Parameters`, `Returns`,
  `Raises`, `Attributes`, `References`, `Notes`.
- An underline of dashes has the same length as its header.
- A parameter entry is `name : type`. For an optional parameter,
  write `type, optional` and end with `by default <value>.`
- Write mathematics in LaTeX: `:math:` inline, `.. math::` for a
  block.

## Notebooks

Notebooks are jupytext `py:percent` files. The `.py` file is the
source. Ignore `notebooks/*.ipynb` in git. Regenerate a notebook
with `uvx jupytext --to ipynb <name>.py`.

A notebook with a Colab badge is the one exception. Track its
`.ipynb` without output. Regenerate it in the same commit as its
`.py`.

## Tests

- Tests live in `test/`, one `test_<module>.py` for each module.
  Each function or logical unit gets one `class Test<Unit>`.
- pytest-xdist runs the suite in parallel (`-n auto`). Tests must
  not depend on order or shared state.
- Use `pytest.raises(..., match=...)`, `np.testing.assert_allclose`
  and `pd.testing.assert_frame_equal`.
- Mark each test that trains or fits a model `@pytest.mark.slow`.

## CI

| Workflow | Trigger | Job |
|---|---|---|
| `test.yaml` | push, PR | ubuntu, windows, macos, each with the oldest supported Python (`requires-python`) and the newest Python release; `-m "not slow"` |
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
- Keep one `.bib` file, `docs/references.bib`, rendered by
  `mkdocs-bibtex`. Its `csl_file` option takes an author-year CSL style.
  Cite in a docstring only when the function implements that
  reference. Put no citations in configs. Background and references
  go to the guide pages in `docs/`.

## README.org

- `README.org` is the source. Export `README.md` with Emacs and
  commit both in the same commit. `pyproject.toml` reads
  `README.md`.
- Structure, after the Best-README-Template: badges, title, local
  TOC, About The Project, Getting Started (Installation, Usage),
  Contributing, License, Contact. Then add "Use of LLM Coding Tools" (`git-conventions`,
  "Rules for agents").
- Usage holds no code. It links to the demo notebook.

## Figures

- A plot function accepts an optional `ax`, creates a figure only when
  `ax` is `None`, and returns the `plt.Figure`.
- The caller saves PDF and PNG and then calls `plt.close(fig)`.
- Put a shared legend above the axes with `fig.legend`, never inside
  an axes.
- Write labels with mathematics in LaTeX, for example
  `r"$\sigma^2$"`.
- Across one project, use one colour for each meaning. Define the
  colours once and import them.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, CI workflows, tagging and releases.
