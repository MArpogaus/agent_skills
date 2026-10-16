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

`.github/workflows/pre-commit.yaml`. Run `pinact` after you copy it
(SKILL.md, "CI workflows").

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

With more than one owner, give each owner a long-lived dev branch
instead of a shared `dev`:

```
feat/<topic>  ->  PR  ->  dev-<name>  ->  PR  ->  main
```

- `dev-<name>` is the integration branch of that owner, who owns it
  and can push to it directly.
- `main` is protected: pull requests only, no direct push, no
  force-push. It holds only `chore: init` and merge commits.
- A rebase of your own `dev-<name>` onto `main` is permitted. Never
  rewrite the branch of another owner.

## Repos you do not own

In a repo of another owner, these conventions are not a mandate.

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
git add .gitignore
[ -f .pre-commit-config.yaml ] && git add .pre-commit-config.yaml
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

Do a rewrite of pushed history only when the user asks for it. In a
repo with more than one owner, all four conditions must be true, else
do not rewrite:

1. Every owner agrees in writing.
2. The old tip stays reachable: an `archive/*` tag and a branch, both
   pushed before the rewrite.
3. The push uses `--force-with-lease`, never plain `--force`.
4. Open pull requests are retargeted, and every collaborator is told
   to re-clone or hard-reset.

A repo with one owner is an exception to the archive rule. Keep a
local `git bundle` as backup, push no archive tag or branch, and push
with `--force-with-lease`.

The procedure below replaces `main` with a `chore: init` commit plus
one squashed snapshot. Do it before any cleanup commits, so that the
snapshot is the unchanged prior state.

Count the unmerged branches first
(`git rev-list --count main..<branch>` for each branch). If more than
two branches carry work, or outside forks exist, tell the user that
the rewrite costs more than it gives.

Merge `dev` into `main` first, or stop when
`git rev-list --count main..dev` is not 0. The procedure never touches
the working tree or the index, so uncommitted edits of the user or
other agents stay. It builds the commits with `git commit-tree` and
moves the branches with `git update-ref`.

```bash
OLD=$(git rev-parse main)

# 1. preserve the old tip
#    more than one owner: push a tag and a branch BEFORE the rewrite
git tag archive/pre-restructure-$(date +%Y%m%d) "$OLD"
git push origin archive/pre-restructure-$(date +%Y%m%d)
git push origin "$OLD":refs/heads/dev-<owner>
#    one owner: keep a local bundle and push nothing
git bundle create ../<repo>-pre-rewrite.bundle --all

# 2. new main: a root with the hook files, then one snapshot commit
#    that records exactly the old tree
I=$(git ls-tree "$OLD" .gitignore .pre-commit-config.yaml | git mktree)
I=$(git commit-tree "$I" -m "chore: init")
S=$(git commit-tree "$OLD^{tree}" -p "$I" -m "chore: import <project> <version> from the prior history")
git branch main-new "$S"

# 3. link the histories once, or each later pull request fails with
#    "refusing to merge unrelated histories"
M=$(git commit-tree "$OLD^{tree}" -p "$OLD" -p "$S" -m "chore: adopt the new main root")
git branch dev-<owner> "$M"

# 4. publish
git update-ref refs/heads/main "$S" "$OLD"
git branch -D main-new
git push --force-with-lease origin main
git push origin dev-<owner>
```

- `git update-ref` also moves a checked-out `main`. Its tree equals the
  old tree, so the working tree and the index still match.
- Existing release tags keep the old commits reachable.
- After the rewrite, retarget open pull requests onto `dev-<owner>`,
  delete merged branches and protect `main`.
- In a repo with one owner, use `dev` in place of `dev-<owner>`. In
  step 3, run `git update-ref refs/heads/dev "$M"` instead of
  `git branch`, because `dev` exists. When `dev` is checked out, first
  check that `git rev-parse dev` prints `$OLD`.
