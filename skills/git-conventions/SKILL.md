---
name: git-conventions
description: >
  Git workflow conventions: two-branch flow, conventional commits,
  pre-commit hooks, dependabot, tagging, and releases.
license: MIT
compatibility: opencode
metadata:
  stack: git
---

# Skill: Git Conventions

## Two-branch flow

- **`main`** — clean history, only `init` + merge commits from `dev`.
  The `init` commit contains exactly `.gitignore` (and
  `.pre-commit-config.yaml` if it already exists at that point).
  Nothing else.  Message is literally: `init` (no body).

- **`dev`** — main working branch.  All feature work, commits, and
  PRs target `dev`.  Never commit directly to `main`.

- **Sketch and redo** when the first attempt gets it wrong:
  `git update-ref -d HEAD` to remove the root commit (only safe
  before any branch/push), then `git add` only the intended files
  and `git commit -m "init"`.

## Commit messages

Conventional commits, small and meaningful:

```
<type>: <short description (max 68 chars)>

[optional body wrapped at 72 chars]
```

| Type       | Usage                           |
|------------|---------------------------------|
| `feat`     | new user-facing feature         |
| `fix`      | bug fix                         |
| `docs`     | documentation only              |
| `style`    | formatting, no logic change     |
| `refactor` | code restructure, no behaviour change |
| `test`     | adding or updating tests        |
| `ci`       | CI / workflow changes           |
| `chore`    | tooling, dependencies, config   |

**Guidelines**:
- **One logical change per commit** — never bundle unrelated
  changes.  If a commit needs "and also" in its message, split it.
- **Keep commits small** — prefer multiple small commits over one
  large one.  A commit should be the smallest meaningful unit of
  work that still passes pre-commit checks and tests.
- **Each commit must be self-contained** — it should make sense
  in isolation and pass CI on its own.
- Description must not exceed 68 characters.
- Body text wrapped at 72 characters.
- Use imperative present tense: "add" not "added" / "adds".

## Pre-commit hooks

### File: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
      - id: check-executables-have-shebangs
      - id: check-merge-conflict
      - id: check-shebang-scripts-are-executable
      - id: check-toml
      - id: check-yaml
      - id: end-of-file-fixer
      - id: mixed-line-ending
      - id: trailing-whitespace

  - repo: https://github.com/macisamuele/language-formatters-pre-commit-hooks
    rev: v2.14.0
    hooks:
      - id: pretty-format-yaml
        args: [--autofix, --indent, "2"]
      - id: pretty-format-toml
        args: [--autofix]
      - id: pretty-format-ini
        args: [--autofix]

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.7.2
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

Run `pre-commit autoupdate` periodically to keep hook revisions
current.

### CI workflow for pre-commit

`.github/workflows/pre-commit.yaml`:

```yaml
name: run pre-commit hooks
on: [push]
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: pre-commit/action@v3.0.1
```

## Dependabot

`.github/dependabot.yml` — target `dev` branch for automated
dependency PRs:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    target-branch: "dev"
```

## Tagging and releases

- **Tags** follow `v<semver>` format (e.g. `v0.1.0`, `v1.2.3`).
- Pushing a tag triggers the release workflow.
- Release commits on `main` are merge commits from `dev`.
- CHANGELOG is auto-generated during the release process (e.g.
  via commitizen or a similar tool).  It is not tracked in the
  repository.

### gh workflow for releases

`.github/workflows/release.yaml` — build, publish to package
index, and create a GitHub Release on tag push.
