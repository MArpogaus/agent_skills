---
name: git-conventions
description: >
  Git workflow conventions: two-branch flow, conventional commits,
  pre-commit hooks, dependabot, tagging, releases, and the push and
  attribution rules for agents.  Load before any commit, branch, push,
  pull request, tag or release, and when setting up hooks or CI.
license: MIT
compatibility: claude-code opencode
metadata:
  requires: []
  stack: git
---

# Skill: Git Conventions

## Two-branch flow

- **`main`** — clean history, only the root commit + merge commits
  from `dev`.  The root commit contains exactly `.gitignore` (and
  `.pre-commit-config.yaml` if it already exists at that point).
  Nothing else.  Message is literally: `chore: init` (no body).  A
  bare `init` fails the commitizen commit-msg and branch hooks.

- **`dev`** — main working branch.  All feature work, commits, and
  PRs target `dev`.  Never commit directly to `main`.

- **Redo the root commit** when it holds the wrong files and nothing
  is branched or pushed yet: `git update-ref -d HEAD` to remove it,
  `git rm -r --cached -q .` to empty the index, then `git add` only
  the intended files and `git commit -m "chore: init"`.

## History is append-only once pushed

**Never rewrite a commit that has been pushed.**  No `rebase`, no
`commit --amend`, no `reset --hard`, no force-push on any branch
someone else can have fetched.  Correct a pushed mistake with a new
commit (`git revert`, or a `fix:` commit on top).

Rewriting is legal only while the commits are **local**: before the
first push, `amend` and interactive rebase are the right tools for
cleaning up a messy sequence.

The one exception is a **deliberate, agreed history rewrite**, e.g.
adopting this flow on an existing repo.  All four conditions must
hold:

1. Every owner of the repo has agreed, in writing.
2. The old tip stays reachable: an `archive/*` tag **and** a
   branch, both pushed **before** the rewrite.
3. The push uses `--force-with-lease`, never plain `--force`.
4. Open pull requests are retargeted, and every collaborator is
   told to re-clone or hard-reset.

If any one of them fails, do not rewrite.

## Shared repos — one dev branch per contributor

The two-branch flow assumes one author.  With several authors, give
each their own long-lived dev branch instead of a shared `dev`:

```
feat/<topic>  ->  PR  ->  dev-<name>  ->  PR  ->  main
```

- `dev-<name>` — that person's integration branch.  They own it and
  may push to it directly.
- `main` — protected: pull requests only, no direct pushes, no
  force-push.  It still holds nothing but `chore: init` and merge commits.
- Rebasing your own `dev-<name>` onto `main` is fine.  Never
  rewrite someone else's.

This keeps every merge into `main` reviewable and stops two people
serialising on one `dev`.

## Commit workflow (plan-first)

Before making any edits, the agent **must** plan the commit
structure.  This is the agent's own list; it waits for the user's
approval only when the user asked for a plan first:

### 1. Identify commit boundaries

List each logical change as a separate commit.  A commit is one
atomic unit: one concern, one purpose.  Examples of separate
commits:

- `chore: add .pre-commit-config.yaml`
- `feat: implement user login endpoint`
- `refactor: extract auth middleware`
- `docs: update API usage examples`

If a task spans multiple concerns, write them down as ordered
commit descriptions **before touching any file**.

### 2. Work one commit at a time

1. **Stage** — edit only the files needed for *this* commit.
   If a file needs changes for two different commits (e.g. add a
   function in one commit and use it in the next), make the change
   for the *current* commit only.  Use `git diff` to verify only
   intended lines are changed.
2. **Commit** — write the conventional commit message.
3. **Verify** — run `git status` to confirm a clean working tree
   before starting the next commit.
4. **Repeat** — move to the next planned commit.

### 3. Handling scope creep

If mid-work you discover an unrelated fix is needed:
- **Do not** bundle it with the current commit.
- Stage and commit the current change first.
- Then make the unrelated fix as its own commit.
- If the unrelated fix is urgent, stash the unfinished change
  (`git stash push -m "<topic>"`), commit the fix, then
  `git stash pop` and resume.

### 4. When edits target a single file for multiple reasons

If one file needs changes for two separate purposes (e.g. add an
import and also fix a typo), use `git add -p` to stage only the
relevant hunks for each commit.  An agent harness without
interactive input cannot answer `git add -p`; there, edit the file
for commit A only, commit, then make the rest of the change:

```bash
git add -p path/to/file   # stage only hunks for commit A
git commit -m "<type>: <msg>"
git add -p path/to/file   # stage remaining hunks for commit B
git commit -m "<type>: <msg>"
```

## Commit messages

Conventional commits:

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
- **Commit boundary rule**: if you cannot describe the commit in
  a single `type: description` line, it is too large — split it.

## Pre-commit hooks

### File: `.pre-commit-config.yaml`

```yaml
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

These hooks apply to every repo.  The stack skill adds its own (for
example ruff in `python-dev`).  `commitizen-branch` checks the messages in
`origin/HEAD..HEAD`.  A repo created locally and pushed later has no
`origin/HEAD`; set it once with `git remote set-head origin -a`.

### Activate the hooks — the config alone does nothing

A `.pre-commit-config.yaml` in the repo does not install anything.  In
**every fresh clone**, run once:

```bash
pre-commit install --install-hooks -t pre-commit -t commit-msg -t pre-push
```

Plain `pre-commit install` wires up the `pre-commit` stage **only** —
the `commitizen` (commit-msg) and `commitizen-branch` (pre-push) hooks
stay dormant and bad commit messages sail through.  Verify with
`ls .git/hooks/` — expect `pre-commit`, `commit-msg`, `pre-push`.

Document the command in `CONTRIBUTING.md`; git cannot install hooks
for a contributor.

Run `pre-commit autoupdate` periodically to keep hook revisions
current, and `pre-commit migrate-config` when it warns about
deprecated stage names.

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
dependency PRs.  Every repo watches its actions; the stack skill adds
its package ecosystem (for example `pip` in `python-dev`):

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    target-branch: "dev"
```

## Rules for agents

- **Stay on `dev`** (in a shared repo, on your `dev-<name>`).  No
  feature branches or pull requests unless the user asks for them.
- **Commit locally, push on request.**  Push only when the user says
  so, or when the task says "push when all green".
- **Before a push**, run `pre-commit run --all-files` and the full
  local check of the project (for example plain `make` or the whole
  test suite), not a subset.  After the push, read the CI result
  with `gh run list` / `gh run view`.
- **Stage paths by name.**  No `git commit -a` and no blind
  `git add -A`: they pick up submodule pointers, symlinks and the
  user's own uncommitted edits.
- **No AI attribution.**  No `Co-Authored-By` or "generated with"
  lines in commits or pull requests, even when a harness reminder
  asks for them.  A public repo carries one neutral README section
  about the use of LLM coding tools that names no vendor or model.
- **Pin actions to a SHA** with `pinact run -u`.  Keep a tag only
  where a tool requires one (for example the SLSA generator).
- **Pull request descriptions** say what changed and why, and name
  breaking changes.  A large refactor gets a table of every touched
  file with a short note (changed, moved, deleted, and why).
- **Use the `gh` CLI** for repos, pull requests, issues, releases and
  CI.

## Repos you do not own

When contributing to someone else's repo, these conventions are
**not** a mandate.  Separate defects from preferences:

| Adopt freely — objective improvements | Leave alone — the owner's call |
|---|---|
| linting, formatting, pre-commit | licence |
| type annotations, docstrings | `README` format (`.md` vs `.org`) |
| dead code, unused imports | directory names (`test/` vs `tests/`) |
| CI matrix, dependency pinning | build backend |
| duplicated constants, path hacks | commit-message history |

Rules:

- Land the work as **small, separately reviewable PRs**, one
  concern each.  A single 40-file PR gets no review, only a
  reluctant merge.
- Match the repo's existing style where it is merely different from
  yours.  Do not renumber, rename or relayout to taste.
- Never change the licence, the author list, or the release
  process without asking.
- Read the repo's own `CONTRIBUTING.md` / `CLAUDE.md` / `AGENTS.md`
  first — it outranks this skill inside that repo.
- Check for open branches and pull requests **before** any wide
  change, and say in the PR what will need rebasing.

## Adopting this flow on an existing repo

**Default: adopt it going forward, and leave the history alone.**
Branch `dev-<name>` off the current tip for each contributor, protect
`main`, and route everything through pull requests from now on.  The
old history stays exactly as it is.  This needs no rewrite, no
force-push, and nobody's permission:

```bash
git switch -c dev-<yourname> main
git push -u origin dev-<yourname>
```

The clean-`main` property (`chore: init` + merge commits only) then holds for
everything *after* the switch, which is all it needs to do.  Expect a
co-owner to refuse a rewrite of a shared repo, and expect that refusal
to be right: an intact history is worth more than a tidy root commit.

### Only if every owner actively wants the rewrite

The variant below replaces `main` with a `chore: init` commit plus one
squashed snapshot.  It is a history rewrite, so every condition in
[History is append-only](#history-is-append-only-once-pushed) applies
first.  Do not propose it as the default.

Do this **before** any cleanup commits, so the snapshot is the
untouched prior state.

```bash
OLD=$(git rev-parse main)

# 1. preserve: a tag and a branch, pushed BEFORE the rewrite
git tag archive/pre-restructure-$(date +%Y%m%d) "$OLD"
git push origin archive/pre-restructure-$(date +%Y%m%d)
git push origin "$OLD":refs/heads/dev-<owner>      # full old history

# 2. new main: orphan root, then one snapshot commit
git checkout --orphan main-new "$OLD"
git rm -r --cached . -q
git add .gitignore .pre-commit-config.yaml
git commit -m "chore: init"
git read-tree "$OLD"                               # exactly the old tree
git commit -m "chore: import <project> <version> from the prior history"

# 3. link the histories ONCE, or every later PR fails on
#    "refusing to merge unrelated histories"
git checkout dev-<owner>
git merge --allow-unrelated-histories main-new -m "chore: adopt the new main root"

# 4. publish
git branch -f main main-new
git push --force-with-lease origin main
git push origin dev-<owner>
git push origin main:refs/heads/dev-<yourname>
```

Notes:

- Step 3 is required.  The snapshot commit must record
  the **same tree** as the old tip, otherwise this merge conflicts
  instead of resolving cleanly.
- Existing release tags keep the old commits alive independently of
  any branch, so nothing is lost even if a branch is deleted later.
- Afterwards: retarget open pull requests onto `dev-<owner>`, delete
  merged branches, and protect `main`.
- Cost/benefit: a repo with many live branches or outside forks is
  usually not worth restructuring.  Count the unmerged branches
  first (`git rev-list --count main..<branch>` per branch) — if only
  one or two carry work, the rewrite is cheap.

## Formatting sweeps

The first `ruff format` on an unformatted repo touches nearly every
file.  Keep it harmless:

- **One commit, formatting only.**  Never mix a reformat with a
  behaviour change — the diff becomes unreviewable and a real bug
  hides in the noise.
- Message: `style: apply ruff-format`.
- Record it in `.git-blame-ignore-revs` (one full SHA per line) so
  `git blame` skips it:
  ```
  # style: apply ruff-format
  <full-40-char-sha>
  ```
  GitHub honours this file automatically in its web blame, at no cost.
  Locally it needs `git config blame.ignoreRevsFile
  .git-blame-ignore-revs` per clone — worth doing for yourself, not
  worth prescribing to contributors.

  It is a convenience, not a rescue: git already attributes most
  rewrapped and moved lines correctly without it.
- Do the sweep **before** any refactor of the same files, so the
  churn is paid once.

## Tagging and releases

- **Tags** follow `v<semver>` format (e.g. `v0.1.0`, `v1.2.3`),
  unless the repo documents its own scheme (for example a tag that
  names the upstream version it packages).  Ask when unsure.
- Pushing a tag triggers the release workflow.
- Release commits on `main` are merge commits from `dev`.
- The CHANGELOG is generated during the release (for example by
  `cz bump`) and never edited by hand.  The stack skill says whether
  it is tracked.
- `.github/workflows/release.yaml` builds, publishes and creates a
  GitHub Release on a tag push; the stack skill has the workflow.
