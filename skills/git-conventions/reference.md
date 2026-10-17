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
    args: [--autofix, --indent, '2']
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
skill adds its package ecosystem (for example `cargo` in `rust-dev`):

```yaml
version: 2
updates:
- package-ecosystem: github-actions
  directory: /
  schedule:
    interval: weekly
  target-branch: dev
```

## Shared repos: one dev branch per contributor

With more than one owner, give each owner a long-lived dev branch
instead of a shared `dev`:

```
feat/<topic>  ->  PR  ->  dev-<owner>  ->  PR  ->  main
```

- `dev-<owner>` is the integration branch of that owner, who owns it
  and can push to it directly.
- `main` is protected: pull requests only, no direct push, no
  force-push. It holds only `chore: init`, merge commits and, after a
  rewrite, the one import snapshot.
- Never rewrite the branch of another owner.

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

## Adopt this flow on an existing repo

**Default: adopt the flow from now on, and do not change the
history.** With more than one owner, branch `dev-<owner>` for each
contributor, protect `main` and route all changes through pull
requests. With one owner, branch `dev` and merge it as SKILL.md,
"Two-branch flow", says. This needs no rewrite and no force-push.

More than one owner:

```bash
git switch -c dev-<owner> main
git push -u origin dev-<owner>
```

One owner:

```bash
git switch -c dev main
git push -u origin dev
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

Stash uncommitted edits with a message
(`git stash push -m "rewrite main"`). Check out `main`
(`git switch main`). When `dev` exists
(`git rev-parse -q --verify dev`), run `git merge --no-ff dev`, and
continue only when `git rev-list --count main..dev` prints 0. After
that, the procedure changes neither the working tree nor the index. It
builds the commits with `git commit-tree` and moves the branches with
`git update-ref`.

```bash
OLD=$(git rev-parse main)
D=$(date +%Y%m%d)
T=archive/pre-restructure-$D  # tag
B=archive/$D                  # branch, a different name than the tag

# 1. preserve the old tip
#    more than one owner: push a tag and a branch BEFORE the rewrite
git tag "$T" "$OLD"
git push origin "refs/tags/$T"
git push origin "$OLD:refs/heads/$B"
#    one owner: keep a local bundle and push nothing
git bundle create ../<repo>-pre-rewrite.bundle --all

# 2. new main: a root with the hook files, then one snapshot commit
#    that records exactly the old tree
I=$(git ls-tree "$OLD" .gitignore .pre-commit-config.yaml | git mktree)
I=$(git commit-tree "$I" -m "chore: init")
S=$(git commit-tree "$OLD^{tree}" -p "$I" -m "chore: import <project> <version> from the prior history")

# 3. link the histories once, or each later pull request fails with
#    "refusing to merge unrelated histories"
M=$(git commit-tree "$OLD^{tree}" -p "$OLD" -p "$S" -m "chore: adopt the new main root")
git branch dev-<owner> "$M"

# 4. publish; until main contains $M, each range holds the old messages
git update-ref refs/heads/main "$S" "$OLD"
uvx --from commitizen cz check --rev-range "$OLD..$M"
git push --no-verify --force-with-lease origin main
git push --no-verify origin dev-<owner>

# 5. merge dev-<owner> into main at once
git merge --no-ff dev-<owner>
uvx --from commitizen cz check --rev-range "$OLD..HEAD"
git push --no-verify origin main
```

Run step 5 at once after step 4. Push the merge with `--no-verify`
only after `cz check --rev-range "$OLD..HEAD"` passes.

- `git update-ref` also moves a checked-out `main`. Its tree equals the
  old tree, so the working tree and the index still match.
- Existing release tags keep the old commits reachable.
- After the rewrite, retarget open pull requests onto `dev-<owner>`
  and delete merged branches. With more than one owner, protect
  `main`.
- In a repo with one owner, use `dev` in place of `dev-<owner>`. When
  `dev` exists, run `git update-ref refs/heads/dev "$M"` in step 3
  instead of `git branch`.
- Last step: switch back to `dev` (or `dev-<owner>`), and run
  `git stash pop` when you stashed.
