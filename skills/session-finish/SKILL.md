---
name: session-finish
description: >
  The cleanup at the end of a working session: stop or report background
  jobs, scan each touched repo for leftovers, finish the review loop,
  settle git state and report files, update the user's GTD agenda,
  record lessons in memory or as skill changes, and give a short final
  report. Run once per session: when the user ends it ("finish", "wrap
  up", "Feierabend", "session beenden", "done for today"), or before the
  last message of an autonomous session. Not after each task.
license: MIT
compatibility: claude-code
metadata:
  stack: meta
  requires: [dev-conventions, git-conventions, gtd]
---

# Skill: Finish a session

Run once per session: when the user ends it ("finish", "wrap up",
"Feierabend", "session beenden", "done for today"), or before the last
message of an autonomous session. Not after each task.

Run the steps in order. Skip a step only when it has nothing to do, and
say so in the report. If a step finds a blocker, report it as
`dev-conventions`, "Asking and acting", says. Do not work around it.

`<start>` is the session's first commit in a repo. Find it with
`git log --since=<session start>` or in `git reflog`.

## 1. Background work

- List the jobs, monitors and subagents you started. Wait for the ones
  that finish within 10 minutes. Stop watchers that have no further use.
- A job can have to keep running (a training run, a deploy). Then write
  in the report what it is, how to check it, and where its output goes.

## 2. Leftovers

For each repo the session touched:

1. `git status --short`: untracked files, scratch scripts, debug
   output, temporary configs. Delete what the session made and no
   longer needs. Never delete the user's files.
2. Read the session's diff (`git diff <start>^..HEAD`). Look for dead
   code, debug prints, commented-out code, unused options and
   arguments, history in comments, and docs that still describe the
   old state.
3. `git worktree list`, `git stash list`, `git branch`: remove the
   worktrees, stashes and branches that you made and that are merged or
   obsolete.
4. Scratch files outside the repos stay in the scratchpad.

## 3. Review

If code changed since the last clean round, run the final round of
`dev-conventions`, "Continuous review". Stop after two clean rounds in
a row. When the user turned reviews off, read your own diff once with
the Simplicity view.

## 4. Git state

- Commit everything that belongs in history, as `git-conventions`
  requires. Report unpushed commits (`git log --oneline @{u}..`).
  Push only when the user asked for it.
- Report and plan files (`findings.md`, see `dev-conventions`,
  "Continuous review", and `HANDOFF.md`) are never committed. Delete
  them when they are done. If work stays open, write `HANDOFF.md` in
  the repo root, listed in `.git/info/exclude`: done, open, next steps,
  where things live.

## 5. Agenda

Follow the `gtd` skill, "Safe edits".

- Find the agenda project of each repo: its name, or the repo link
  under `Information`.
- Set tasks to `DONE` that the session finished and the user
  confirmed. For a finished task without confirmation, list it in the
  report as "to close".
- Add follow-ups, open blockers and filed issues as inbox items, as
  in `gtd`, "Capture from another repo".
- Before you file an issue, check the open issues and the roadmap, so
  you do not file what is already planned.

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
  that skill in the report. Edit the skill only when the user agrees.

## 7. Report

Use these four headings and omit the empty ones. Give one line per
item:

- **Done**: what changed, with commits or files.
- **Running**: jobs from step 1.
- **Open**: blockers, issues, unpushed work, "to close" tasks.
- **Lessons**: proposals from step 6.

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: review loop, report files and the blocker rule.
- **git-conventions**: commits and pushes.
- **gtd**: safe agenda edits and capture.
