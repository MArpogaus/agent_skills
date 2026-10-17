---
name: gtd
description: >
  The user's GTD routine in the Org agenda at `<agenda repo>`: capture
  ("gtd: ..." and "<project>: ..."), the day review ("Tagesreview"),
  inbox triage one project at a time, the retro with its journal entry,
  the weekly review, and how an agent in another repo records a blocker
  or follow-up there. Use when the session runs in the agenda workspace
  or must leave a task for the user. Use when the user says "gtd",
  "Tagesreview", "Retro", "Wochenreview" or "inbox".
license: MIT
compatibility: claude-code opencode
metadata: {stack: org, requires: [dev-conventions, git-conventions]}
---

# Skill: GTD Agenda

The agenda is a git repository of Org files at `<agenda repo>`. Its
`AGENTS.md` holds the data model: the files, the heading template, the
keywords, the sort order, the day frame and the Org bookkeeping. This
skill holds the procedures.

Notes live in the Denote silos under `<notes dir>`: the notes silos the
`AGENTS.md` names. This skill gives permission to commit on the agenda
repo's `main`.

## Hard rules

- Read `AGENTS.md` before the first edit in a session.
- Run `git -C <agenda repo> status --short` before each edit. A sync
  client and open Emacs buffers also write these files. Never revert
  or overwrite changes that you did not make. When a file you want to
  change has such changes, stop and tell the user.
- Ask before you set `DONE` or `KILL` and before you delete text. "X is
  done" from the user is the consent. Do not ask again. Autonomous:
  skip the edit and list the item under "Open" in the final report.
- Archiving (section 5) is a move and needs no question.
- Never send mail. Mail drafts go into a code block for the user to
  copy.
- The agenda links to a note. It never copies the content of the note.
- Write entries in the language of the entries around them.

## 1. Capture

- **`gtd: <text>`** adds an inbox item to `inbox.org`.
- In the agenda workspace, **`<project>: <text>`** adds a task or a
  check box to that project in `gtd.org`. Match the name against the
  existing projects first, including short and old names. Make a new
  project only when the user says so and no existing project fits.
- A task that spans projects goes to the inbox or to
  `Miscellaneous`, never under one of the projects.
- A small step inside a task is a check box, not a task.

### Capture from another repo

An agent in another workspace records a blocker or a follow-up for
the user like this:

1. Check the agenda state as the hard rules say.
2. Add `* TODO <project>: <one-line summary>` to `inbox.org` with the
   `/Entered on/` line. Below it, one or two lines: what blocks, and
   a link to the issue or the commit.
3. Commit in the agenda repo with `git -C <agenda repo>`.

Autonomous: when `<agenda repo>` is missing or read-only, or `inbox.org`
has changes you did not make, do not edit it. List the item under
"Open" in the final report, and in the GitHub issue when
`dev-conventions` section 2 allows one.

Keep the details in the issue. The inbox item is a pointer.

## 2. Day review ("Tagesreview")

The agent shell sends "Tagesreview nach AGENTS.md." as its first message
when the agenda session starts.

1. Read the last journal entry, especially its field for tomorrow.
2. Read the calendar for today and the next 14 days. Read the mail
   since the date of the last journal entry. Use the mail and calendar
   connector, read only.
3. Report in at most 30 lines: today's appointments, deadlines and
   scheduled tasks; the `NEXT` tasks; the inbox count; the mail that
   asks for an action.
4. Propose at most three tasks for the day.

## 3. Inbox triage

Group the inbox items by the `<project>:` prefix in the title. Items
without one come last. Go through the groups one project at a time.
For each project, show a table of its items with one proposal beside
each. A proposal is one of: move to the project, single task, `WAIT`,
`KILL`, or a note in the Denote silo. Wait for the user's decision,
apply it, commit, then go to the next project.

## 4. Retro ("Retro")

1. Ask what is done and set it `DONE`, with `CLOSED` and the project
   cookie.
2. Carry meeting notes into their Denote notes and new tasks into the
   projects. Triage what is left in the inbox (section 3).
3. Read today's agent sessions. All of the user's sessions share one
   agent home. Read the transcripts that changed today in
   `~/.claude/projects/` of that home (opencode: the sessions in
   `~/.local/share/opencode/opencode.db`). Extract the user's messages
   and look for what went well, what went badly, and decisions.
4. Write the journal entry in the date tree of `journal.org` with the
   fields `AGENTS.md` names, one line each. They cover what is done,
   what went well, what went badly, decisions and tomorrow.
5. Commit.

## 5. Weekly review ("Wochenreview")

1. List projects without a `NEXT` task. A project with "Das Projekt
   ruht seit DATUM." under `Notes` is resting, not stuck.
2. List the tasks whose `WAIT` entry names a date more than 14 days
   ago.
3. List deadlines in the next 14 days.
4. Move `DONE` and `KILL` entries to the archive file beside their
   file, whole subtrees only. Commit.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: asking and acting, blockers, autonomous
  sessions.
- **git-conventions**: commit messages and the attribution rule.
