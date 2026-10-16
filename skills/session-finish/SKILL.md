---
name: session-finish
description: >
  The cleanup to run at the end of every working session: stop or
  report background jobs, scan each touched repo for leftovers, finish
  the review loop, settle git state and report files, update the
  user's GTD agenda, record lessons in memory or as skill changes, and
  give a short final report.  Use before you say "done", hand over or
  end a session, and when the user says "finish", "wrap up",
  "cleanup", "Feierabend" or "session beenden".
license: MIT
compatibility: claude-code
metadata:
  stack: meta
  requires: [dev-conventions, git-conventions, gtd]
---

# Skill: Finish a session

Run the steps in order.  Skip a step only when it has nothing to do,
and say so in the report.  If a step finds a blocker, report it
(`dev-conventions` section 2) instead of working around it.

## 1. Background work

- List the jobs, monitors and subagents you started.  Wait for the ones
  that finish soon.  Stop watchers that have no further use.
- For a job that must keep running (a training run, a deploy), write
  in the report what it is, how to check it, and where its output goes.

## 2. Leftovers

For each repo the session touched:

1. `git status --short`: untracked files, scratch scripts, debug
   output, temporary configs.  Delete what the session made and no
   longer needs.  Never delete the user's files.
2. Read the session's diff (`git diff <start>..HEAD`).  Look for dead
   code, debug prints, commented-out code, unused options and
   arguments, history in comments, and docs that still describe the
   old state.
3. `git worktree list`, `git stash list`, `git branch`: remove the
   worktrees, stashes and branches that you made and that are merged or
   obsolete.
4. Scratch files outside the repos stay in the scratchpad.

## 3. Review

If code changed since the last clean round, run the final round of
`dev-conventions` section 4.4 until it comes back clean twice in a row.
When the user turned reviews off, read your own diff once with the
Simplicity view.

## 4. Git state

- Everything that belongs in history is committed as `git-conventions`
  requires.  Report unpushed commits (`git log --oneline @{u}..`).
  Push only when the user asked for it.
- Report and plan files (`findings.md`, `HANDOFF.md`) are never
  committed.  Delete them when they are done.  If work stays open,
  write `HANDOFF.md` in the repo root, listed in `.git/info/exclude`:
  done, open, next steps, where things live.

## 5. Agenda

Follow the `gtd` skill, section 1, for safe edits.

- Find the agenda project of each repo: its name, or the repo link
  under `Information`.
- Set tasks to `DONE` that the session finished and the user
  confirmed.  For a finished task without confirmation, list it in the
  report as "to close".
- Add follow-ups, open blockers and filed issues as inbox items, as
  in `gtd` "Capture from another repo".
- Before you file an issue, check the open issues and the roadmap, so
  you do not file what is already planned.

## 6. Lessons

Read back the user's messages of this session and look for
corrections, repeated instructions and frustration.

- A fact about how the user works goes into memory, unless a skill
  already says it.
- A rule that a skill already has but you broke: say so in the report.
  Do not repeat it in memory.
- A rule that a skill lacks or gets wrong: propose the exact change to
  that skill in the report.  Edit the skill only when the user agrees.

## 7. Report

Keep it short.  Use these four headings and omit the empty ones:

- **Done**: what changed, with commits or files.
- **Running**: jobs from step 1.
- **Open**: blockers, issues, unpushed work, "to close" tasks.
- **Lessons**: proposals from step 6.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions** — review loop and the blocker rule.
- **git-conventions** — commits, pushes and report files.
- **gtd** — safe agenda edits and capture.
