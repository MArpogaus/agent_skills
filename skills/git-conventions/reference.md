# git-conventions reference

Rare procedures for the rules in [SKILL.md](SKILL.md).

## Base pre-commit config

```yaml
default_install_hook_types: [pre-commit, commit-msg, pre-push]
repos:
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
      - id: commitizen-branch
        stages: [pre-push]
```

## pre-commit workflow

`.github/workflows/pre-commit.yaml`. Run `pinact` after you copy it (SKILL.md, "CI workflows").

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

`.github/dependabot.yml` keeps the action pins current. The stack
skill adds its package ecosystem (for example `pip` in `python-dev`):

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    target-branch: "dev"
```

## Shared repos: one dev branch per contributor

With more than one author, give each author a long-lived dev branch
instead of a shared `dev`:

```
feat/<topic>  ->  PR  ->  dev-<name>  ->  PR  ->  main
```

- `dev-<name>` is the integration branch of that author, who owns it
  and can push to it directly.
- `main` is protected: pull requests only, no direct push, no
  force-push. It holds only `chore: init` and merge commits.
- A rebase of your own `dev-<name>` onto `main` is permitted. Never
  rewrite the branch of another author.

## Repos you do not own

In a repo of another owner, these conventions are not a mandate. The
repo's own `CONTRIBUTING.md`, `CLAUDE.md` or `AGENTS.md` outranks this
skill. Read it first.

| Adopt freely: objective improvements | Leave alone: the owner's call |
|---|---|
| linting, formatting, pre-commit | licence |
| type annotations, docstrings | `README` format (`.md` vs `.org`) |
| dead code, unused imports | directory names (`test/` vs `tests/`) |
| CI matrix, dependency pinning | build backend |
| duplicated constants, path hacks | commit-message history |

- Land the work as separately reviewable pull requests, one concern
  each.
- Match the existing style where it is only different from yours. Do
  not rename or change the layout to your taste.
- Never change the licence, the author list or the release process
  without asking.
- Before a change to more than 10 files, check for open branches and
  pull requests, and say in the pull request what needs a rebase.

## Redo the root commit

Use this when the root commit holds the wrong files and nothing is
branched or pushed yet:

```bash
git update-ref -d HEAD        # remove the root commit
git rm -r --cached -q .       # empty the index
git add .gitignore .pre-commit-config.yaml
git commit -m "chore: init"
```

## Adopt this flow on an existing repo

**Default: adopt the flow from now on, and do not change the
history.** Branch `dev-<name>` off the current tip for each
contributor, protect `main`, and route all changes through pull
requests. This needs no rewrite and no force-push:

```bash
git switch -c dev-<yourname> main
git push -u origin dev-<yourname>
```

The clean-`main` rule then applies to all commits after the switch.

## Rewrite `main` to the flow

Do this only when the user asks for it, and only when the conditions
in SKILL.md ("History is append-only once pushed") are true. It
replaces `main` with a `chore: init` commit plus one squashed
snapshot. Do it before any cleanup commits, so that the snapshot is
the unchanged prior state.

Count the unmerged branches first
(`git rev-list --count main..<branch>` for each branch). If more than
two branches carry work, or outside forks exist, tell the user that
the rewrite costs more than it gives.

Merge `dev` into `main` first, or stop when
`git rev-list --count main..dev` is not 0. When other agents or the
user have uncommitted edits, rewrite with `git commit-tree` and
`git update-ref`, so the working tree stays untouched.

```bash
OLD=$(git rev-parse main)

# 1. preserve the old tip
#    more than one owner: push a tag and a branch BEFORE the rewrite
git tag archive/pre-restructure-$(date +%Y%m%d) "$OLD"
git push origin archive/pre-restructure-$(date +%Y%m%d)
git push origin "$OLD":refs/heads/dev-<owner>
#    one owner: keep a local bundle and push nothing
git bundle create ../<repo>-pre-rewrite.bundle --all

# 2. new main: orphan root, then one snapshot commit
git checkout --orphan main-new "$OLD"
git rm -r --cached . -q
git add .gitignore .pre-commit-config.yaml
git commit -m "chore: init"
git read-tree "$OLD"                               # exactly the old tree
git commit -m "chore: import <project> <version> from the prior history"

# 3. link the histories once, or each later pull request fails with
#    "refusing to merge unrelated histories"
git switch -c dev-<owner> "$OLD"
git merge --allow-unrelated-histories main-new -m "chore: adopt the new main root"

# 4. publish
git branch -f main main-new
git push --force-with-lease origin main
git push origin dev-<owner>
```

- Step 3 is necessary. The snapshot commit must record the same tree
  as the old tip, else the merge conflicts.
- Existing release tags keep the old commits reachable.
- After the rewrite, retarget open pull requests onto `dev-<owner>`,
  delete merged branches and protect `main`.
- In a repo with one owner, use `dev` in place of `dev-<owner>`. In
  step 3, run `git switch dev` and `git merge --ff-only "$OLD"`
  instead of `git switch -c`, because `dev` exists.
