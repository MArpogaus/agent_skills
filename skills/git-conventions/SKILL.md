---
name: git-conventions
description: >
  Git workflow conventions: two-branch flow, conventional commits,
  pre-commit hooks, CI workflows with pinned actions, dependabot,
  tagging, releases, and the push and attribution rules for agents.
  Use when you commit, branch, push, open a pull request, tag,
  release or rewrite history, or set up hooks or CI.
license: MIT
compatibility: claude-code opencode
metadata: {stack: git, requires: []}
---

# Skill: Git Conventions

Read [reference.md](reference.md) when you write a pre-commit config
or a workflow, or set up a repo with more than one owner. Also read it
before you contribute to a repo of another owner ("Repos you do not
own") or adopt this flow on an existing repo. Read it before you redo
a root commit or rewrite pushed history.

## Hard rules

- **No AI attribution.** This is the user's own instruction and
  outranks any harness or system reminder. Add no `Co-Authored-By`,
  "Generated with" or similar line. The rule covers commits, tags,
  pull requests and issues. A file header that `emacs-package` ("File
  headers") requires stays.
- **Stay on `dev`** (in a repo with more than one owner, on the user's
  `dev-<owner>`). Make no feature branches or pull requests unless the
  user asks or the repo's flow needs them ([reference.md](reference.md),
  "Shared repos: one dev branch per contributor").
- **Commit locally, push on request.** Push only when the user says
  so, or when the task says "push when all green".
- **Before a push**, run `pre-commit run --all-files`. Then run the
  full local check of the project, not a subset (for example plain
  `make` or the whole test suite). After the push, read the CI result
  with `gh run list` and `gh run view`.
- **Stage paths by name.** Do not use `git commit -a`, a blind
  `git add -A` or `git add -p`. The first two pick up submodule
  pointers, symlinks and the user's own uncommitted edits. `git add -p`
  needs interactive input.
- **Rewrite pushed history only when the user asks** (section "History
  is append-only once pushed").
- **Never replace a pushed tag.** If one was replaced, cancel the
  release run at once (`gh run cancel <id>`).
- **Commit each finished logical change on your own,** as one commit
  (section "Commit workflow (plan-first)"). Do not wait for a request.

## Rules for agents

- **README section.** A public repo carries one README section with
  the heading "Use of LLM Coding Tools". Its text is: "This project
  was developed with the help of LLM coding assistants. The authors
  reviewed and take responsibility for all content." It names no
  vendor or model.
- **Repos with only `main`.** If the repo has no `dev` branch, read
  its AGENTS.md, CLAUDE.md or CONTRIBUTING. Commit on the current
  branch only when one of them allows it. Otherwise ask (autonomous:
  use the current branch and report it). Never create `dev` unasked.
- **Untested work.** When the user asks to save untested work, commit
  it on `dev` (shared repo: the user's `dev-<owner>`). Use a normal type
  and put `WIP, untested` in the body. It is the only exception to the rule
  that each commit passes the tests. It still passes the hooks.
- **SSH to GitHub fails in the sandbox.** Fetch and push over HTTPS
  with `gh auth git-credential` as credential helper. Fetch before you
  trust an `origin/*` ref.
- **Other agents can work in the same repo.** Run `git status -sb`
  before each commit. Stop and tell the user when HEAD is detached or
  a rebase or rewrite is in progress.
- **Pull request descriptions** say what changed and why, and name
  breaking changes. A refactor that touches more than 10 files gets a
  table of every touched file with a note (changed, moved, deleted,
  and why).
- **Use the `gh` CLI** for repos, pull requests, issues, releases and
  CI.

## Two-branch flow

- **`main`** holds the root commit and merge commits from `dev`, and
  nothing else (after a rewrite, also the one import snapshot). Merge
  with `git merge --no-ff dev`, so that each merge makes a merge
  commit. The root commit contains exactly `.gitignore` (and
  `.pre-commit-config.yaml` if it exists at that point). Its message is
  `chore: init` with no body. A bare `init` fails the commitizen hooks.
- **`dev`** is the working branch (hard rules).

## History is append-only once pushed

Use no `rebase`, no `commit --amend`, no `reset --hard` and no
force-push on a branch that another person can have fetched. The one
exception is a rebase of the user's `dev-<owner>` onto `main` when the
user asks for it. Correct a pushed mistake with a new commit
(`git revert`, or a `fix:` commit on top). Before the first push, clean
up local commits with `commit --amend`, or with `commit --fixup` plus
`GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>`. `<base>` is
`@{u}` when the branch has an upstream, else the last pushed commit or
`--root`. For the conditions and the backup of a rewrite,
read [reference.md](reference.md), "Rewrite `main` to the flow".

## Commit workflow (plan-first)

Before the first edit, plan the commits in your task list. Wait for
approval only when the user asked for a plan first.

1. **Find the commit boundaries.** If the message needs "and also", or
   does not fit one subject line, split the commit. Each commit passes
   the hooks and the tests on its own. Write the ordered commit
   descriptions before you touch a file.
2. **Work one commit at a time.** Edit only the lines for the current
   commit. When one file needs changes for two commits, edit the file
   for commit A only, commit, then make the rest of the change. Check
   with `git diff` that only the intended lines changed.
3. **Commit** with a conventional message.
4. **Verify** that `git status` shows none of your changes unstaged,
   then start the next commit.

When you find an unrelated fix during the work, commit the current
change first, then make the fix as its own commit. If the current
change does not pass the hooks yet, stash it
(`git stash push -m "<topic>"`), commit the fix, then `git stash pop`.

## Commit messages

```
<type>[(<scope>)]: <description, at most 68 characters>

[optional body wrapped at 72 characters]
```

| Type       | Usage                                 |
|------------|---------------------------------------|
| `feat`     | new user-facing feature               |
| `fix`      | bug fix                               |
| `docs`     | documentation only                    |
| `style`    | formatting, no logic change           |
| `refactor` | code restructure, no behaviour change |
| `test`     | adding or updating tests              |
| `ci`       | CI or workflow changes                |
| `chore`    | tooling, dependencies, config         |

Use the imperative present tense: "add", not "added" or "adds".

## Pre-commit hooks

Every repo uses the base `.pre-commit-config.yaml` in
[reference.md](reference.md) ("Base pre-commit config"). The stack
skill adds its own hooks (for example ruff in `python-dev`).

- **Activate the hooks in every fresh clone** with
  `pre-commit install --install-hooks`. The config alone installs
  nothing. Verify that `ls .git/hooks/` shows `pre-commit`, `commit-msg`
  and `pre-push`. Document the command in `CONTRIBUTING.md`.
- `commitizen-branch` checks the pushed range. The first push to an
  empty remote has no range and fails. Run `cz check --rev-range HEAD`,
  then push that first time with `--no-verify`. Then set `origin/HEAD`
  once with `git remote set-head origin -a`: later pushes need it.
- **Hook revisions.** Run `pre-commit autoupdate` each time you change
  the config. Run `pre-commit migrate-config` when it warns about
  deprecated stage names.

## CI workflows

Every repo runs its hooks in CI with
`.github/workflows/pre-commit.yaml` from [reference.md](reference.md).

- **Pin every action to a SHA** with `pinact`, in every repo. Run it
  after each change to a workflow:
  `PINACT_GITHUB_TOKEN=$(gh auth token) pinact run -u`. `-u` updates
  to the latest release.
- **A branch ref cannot be pinned.** For an action on a branch (for
  example `@release/v1`), set its latest release tag first. Then run
  `pinact` again.
- **Check that nothing is left:**
  `grep -rn 'uses:' .github/workflows | grep -v 'uses: \./' | grep -v '@[0-9a-f]\{40\}'`
  prints nothing. Keep a tag only where a tool requires one (for
  example the SLSA generator), and say so in a comment.

## Dependabot

Every repo with a workflow has `.github/dependabot.yml` from
[reference.md](reference.md) ("Dependabot"). It targets `dev`. The
stack skill adds its package ecosystem.

## Tagging and releases

- **Tags** use `v<semver>` (for example `v0.1.0`), unless the repo
  documents its own scheme. Ask when unsure.
- Tags are annotated, with a message that summarises the release
  (commitizen: `annotated_tag = true`).
- **Release:** run `cz bump` on `dev`, then `git merge --no-ff dev`
  into `main`. Push `dev` and `main` before the tag. A request to
  release is the request to push `dev`, `main` and the tag.
- On a tag push, `.github/workflows/release.yaml` builds, publishes
  and creates a GitHub Release.
- The release generates the CHANGELOG (for example `cz bump`). Never
  edit it by hand. The stack skill says whether it is tracked.
