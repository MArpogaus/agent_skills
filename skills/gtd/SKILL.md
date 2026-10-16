---
name: gtd
description: >
  The user's GTD routine in the Org agenda at <agenda repo>: capture
  ("gtd: ..." and "<project>: ..."), the day review ("Tagesreview"),
  inbox triage one project at a time, the retro with its journal entry,
  the weekly review, and how an agent in another repo records a blocker
  or follow-up there. Use in the agenda workspace, when the user says
  "gtd", "Tagesreview", "Retro", "Wochenreview" or "inbox", and when a
  session must leave a task for the user.
license: MIT
compatibility: claude-code
metadata:
  stack: org
  requires: [git-conventions]
---

# Skill: GTD agenda

The agenda is a git repository of Org files at `<agenda repo>`. Its
`AGENTS.md` holds the data model: the files, the heading template,
the keywords, the sort order, the day frame and the Org bookkeeping.
This skill holds the procedures. Read `AGENTS.md` before the first
edit in a session. If the two disagree, `AGENTS.md` wins for the data
model and this skill wins for the procedures.

Notes live in the Denote silos `<notes dir>/work` (default) and
`<notes dir>/private`. The agenda links to a note; it never copies
its content.

## 1. Safe edits

Other writers change the same files: the phone sync and open Emacs
buffers.

- Run `git -C <agenda repo> status --short` before each edit. If a
  file you want to change has uncommitted changes that you did not
  make, stop and tell the user. They can be a stale sync or an
  unsaved buffer. Never revert or overwrite them.
- Stage only the files you changed (`git add FILE`). Commit on the
  agenda repo's current branch (`main`). Commit each change at once with
  a short conventional message in English.
- Write entries in the language of the entries around them.

## 2. Capture

- **`gtd: <text>`** adds an inbox item to `inbox.org`.
- **`<project>: <text>`** adds a task or a check box to that project in
  `gtd.org`. Match the name against the existing projects first,
  including short and old names. Make a new project only when the
  user says so and no existing project fits.
- A task that spans projects goes to the inbox or to
  `Miscellaneous`, never under one of the projects.
- A small step inside a task is a check box, not a task.
- Ask before you set `DONE` or `KILL` and before you delete text.
  "X is done" from the user is the consent; do not ask again.

### Capture from another repo

An agent in another workspace records a blocker or a follow-up for
the user like this:

1. Check the agenda state as in section 1.
2. Add `* TODO <project>: <one-line summary>` to `inbox.org` with the
   `/Entered on/` line. Below it, one or two lines: what blocks, and
   a link to the issue or the commit.
3. Commit in the agenda repo with `git -C <agenda repo>`.

Keep the details in the issue. The inbox item is a pointer.

## 3. Day review ("Tagesreview")

The agent shell sends "Tagesreview nach AGENTS.md." as its first message
when the agenda session starts.

1. Read the last journal entry, especially "Morgen".
2. Read the calendar for today and the next 14 days, and the mail
   since the last review (mail and calendar connector, read only).
3. Report in at most 30 lines: today's appointments, deadlines and
   scheduled tasks; the `NEXT` tasks; the inbox count; the mail that
   asks for an action.
4. Propose at most three tasks for the day.

Mail drafts go into a code block for the user to copy. Never send
mail.

## 4. Inbox triage

Go through the inbox one project at a time. For each project, show a
table of its items with one proposal beside each. A proposal is one
of: move to the project, single task, `WAIT`, `KILL`, or a note in the
Denote silo.
Wait for the user's decision, apply it, commit, then go to the next
project.

## 5. Retro ("Retro")

1. Ask what is done and set it `DONE`, with `CLOSED` and the project
   cookie.
2. Carry meeting notes into their Denote notes and new tasks into the
   projects. Triage what is left in the inbox (section 4).
3. Read today's agent sessions: the transcripts under
   `~/.claude/projects/` changed today. Extract the user's messages
   and look for what went well, what went badly, and decisions.
4. Write the journal entry in the date tree of `journal.org` with
   these five fields, one line each:

   ```
   - Erledigt :: ...
   - Gut :: ...
   - Schlecht :: ...
   - Entscheidungen :: ...
   - Morgen :: ...
   ```

5. Commit.

## 6. Weekly review ("Wochenreview")

1. List projects without a `NEXT` task. A project with "Das Projekt
   ruht seit DATUM." under `Notes` is resting, not stuck.
2. List `WAIT` entries older than 14 days.
3. List deadlines in the next 14 days.
4. Move `DONE` and `KILL` entries to the archive file beside their
   file, whole subtrees only. Commit.

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions**: commit messages and the attribution rule.
