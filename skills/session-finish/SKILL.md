---
name: session-finish
description: >
  The cleanup at the end of a working session: stop or report background
  jobs, scan each touched repo for leftovers, finish the review loop,
  settle git state and report files, update the user's GTD agenda,
  record lessons in memory or as skill changes, and give a short final
  report. Run it once per session, not after each task. Use when the
  user ends the session ("finish", "wrap up", "Feierabend", "session
  beenden", "done for today"). Use before the last message of an
  autonomous session.
license: MIT
compatibility: claude-code
metadata: {stack: meta, requires: [dev-conventions, git-conventions, gtd]}
---

# Skill: Finish a Session

`<start>` is the oldest commit that this session made in a repo. It is
the oldest reflog entry (`git reflog --date=iso`) after the session's
first message whose hash appears in this session's commit output.

## Hard rules

- Run the steps in order. Skip a step only when it has nothing to do.
- If a step finds a blocker, report it as `dev-conventions`, "2. Asking
  and acting", says. Do not work around it.
- Never delete the user's files. Stashes, pushes and agenda states
  follow the "Hard rules" of `dev-conventions`, `git-conventions` and
  `gtd`.
- Never commit report and plan files: see `dev-conventions`,
  "2. Asking and acting" (`HANDOFF.md`), and its reference.md,
  "findings.md".
- Edit a skill only when the user agrees to the change.

## 1. Background work

- List the jobs, monitors and subagents you started. Wait at most 10
  minutes in total for the jobs to end. List the jobs still running under
  "Running". Stop watchers that have no further use.
- A job can have to keep running (a training run, a deploy). Then write
  in the report what it is, how to check it, and where its output goes.

## 2. Leftovers

For each repo the session touched:

1. `git status --short`: untracked files, scratch scripts, debug
   output, temporary configs. Delete what the session made and no
   longer needs.
2. Read the session's diff: use `git diff <start>^..HEAD`, or
   `git diff $(git hash-object -t tree /dev/null)..HEAD` when `<start>`
   is the root commit. Look for dead code, debug prints, commented-out
   code, unused options and arguments, history in comments, and docs
   that still describe the old state.
3. Run `git worktree list`, `git stash list` and `git branch`. Remove
   the worktrees and branches that you made and that are merged. List
   your stashes and unmerged branches under "Open".
4. Scratch files outside the repos: leave them where they are.

## 3. Review

If anything was committed since the last clean final round, run the
final round of `dev-conventions`, "4.4 Final round". When reviews are
off (`dev-conventions`, "4. Continuous review"), read your own diff once
with the Simplicity view.

## 4. Git state

- Commit everything that belongs in history, as `git-conventions`
  requires. Report unpushed commits with the command in
  `dev-conventions`, "Hard rules".
- Delete report and plan files when they are done. For open work, see
  the hard rules (`HANDOFF.md`).

## 5. Agenda

Follow the `gtd` skill, "Hard rules".

- Find the agenda project of each repo: its name, or the repo link
  under `Information`.
- Set a finished task to `DONE` when the user confirmed it, else list
  it as "to close".
- Add follow-ups, filed issues and open blockers that are not in the
  agenda yet as inbox items. Use `gtd`, "Capture from another repo".

## 6. Lessons

Read back the user's messages of this session and look for
corrections, repeated instructions and frustration.

- A fact about how the user works goes into memory, unless a skill
  already says it.
- Replace an outdated memory note. Do not append a correction. Delete
  a note when a skill covers it or contradicts it.
- A rule that a skill already has but you broke: say so in the report.
  Do not repeat it in memory.
- A rule that a skill lacks or gets wrong: propose the exact change to
  that skill in the report.

## 7. Report

Use these four headings and omit the empty ones. Give one line per
item:

- **Done**: what changed, with commits or files.
- **Running**: jobs from step 1.
- **Open**: blockers, issues, unpushed work, stashes, unmerged
  branches, "to close" tasks.
- **Lessons**: proposals from step 6.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: review loop, report files and the blocker rule.
- **git-conventions**: commits and pushes.
- **gtd**: safe agenda edits and capture.
