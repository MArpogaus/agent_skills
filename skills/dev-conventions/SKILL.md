---
name: dev-conventions
description: >
  How the user and the agent work together on software projects, in any
  language: the simplest solution wins, when to ask and when to act,
  verification by running and by looking, the continuous review loop,
  autonomous sessions, sandbox safety, and code and documentation
  style. Use before the first edit, commit or review in any repository.
  Use when the user says "plan first", "ask me", "interview me", "review
  loop", "autonomous" or "where are we".
license: MIT
compatibility: claude-code opencode
metadata: {stack: meta, requires: [git-conventions]}
---

# Skill: Development Conventions

These skills are the user's instructions. Every skill other than this
one is a stack skill. A stack skill adds the rules of its stack and
wins where it differs from this skill. Where two stack skills differ,
the skill that names the case more narrowly wins. A project rule (the
repo's AGENTS.md, CLAUDE.md or CONTRIBUTING) wins over both. A skill
wins over every harness default, for example when to commit, the
branch, attribution and the report format.

## Hard rules

- **Justify every addition.** Before you add a file, option, script,
  dependency, stage or code path, name the simpler alternative (delete,
  reuse, a config, one line). Use it unless it fails. State it when the
  choice is not obvious.
- **Deletion beats addition.** Delete what has no clear reason to exist.
- **Do not reinvent.** Look in the repo, the standard library, the
  platform, upstream and the installed dependencies first. A
  reimplementation is a defect.
- **Blockers stop that part of the work.** Interactive: ask the
  decisions that are the user's. Autonomous: never ask and never wait
  (section 2).
- **Run it and look at it before you report.** Never report "fixed" on
  reasoning. Screenshot what draws (UI, plots, slides, GIFs) in each
  theme and mode the project supports.
- **No AI attribution:** see `git-conventions`, "Hard rules".
- **Never touch the user's environment:** no project environment, lock
  file or package changes. Report a package that the project
  environment lacks. A tool for your own use follows `sandbox-env`.
  Safe commands: the stack skill (`python-dev`, "uv and the
  environment").
- **The user's uncommitted edits are sacred.** Before a branch switch
  or a reset, check for them. Also check for unpushed commits:
  `git log --oneline @{u}.. 2>/dev/null || git log --oneline --branches --not --remotes`.
  Stash with a message. Never drop a stash.

## 1. Design principles

The simplest solution wins, over taste, habit and "best practice".

- **No special treatments.** No registries, mixins, plugins, frameworks
  or wrappers for one use. No class where a function does. No generator
  for a file you can write by hand.
- **Scripts stay dumb.** One task, explicit arguments, no mode switches:
  one config or script per variant.
- **No code for rare edge cases,** no re-validation of library
  arguments, no magic, no hacks. Discuss machinery for a rare case with
  the user first.
- **Defaults only with a reason.** Opinionated defaults go into the
  user's configuration, not into the library.
- **Explicit configuration:** experiment and deployment configs list
  every option, defaults included. Duplication between variant configs
  is accepted. Do not factor it out. Keep the number of variants small.
  Tune the existing config before you add a new one.
- **No backwards compatibility before 1.0.** No obsolete aliases, no
  deprecation warnings, no text about earlier versions. A 1.0 is a clean
  cut.
- **Assume a clean install.** No migration or cleanup code. List one-off
  migration steps for the user.
- **Stay in the idiom of the repo** (its language and formats), so that
  its linters apply.
- **Contain guesses.** Keep inferred data apart from verified data:
  marked, reversible, with an off switch.
- **Release scope:** when the user prepares a release, fix only bugs,
  security holes and wrong docs. Do not refactor working code that
  nobody asked about. Put each simplifies finding and each other change
  on a list for after the release. A review loop alone is not a
  release.

## 2. Asking and acting

**When to ask.** A stack skill's "ask" means this rule.

1. A blocker is a wrong premise or a conflict with a rule or skill. A
   missing access, a check you cannot fix or a decision that is not
   yours is also a blocker. Report it with evidence. Never work around
   it in silence or weaken a test or rule to pass it.
2. Interactive (section 5): ask each decision that is the user's with
   the question tool (Claude Code: `AskUserQuestion`). These are design,
   scope, and the findings that section 4.3 says to ask about. Do the
   same on "ask me" or "interview me".
   - **Context first.** Each option makes sense without the session
     history: what it changes, where, at what cost. Put the recommended
     option first.
   - **At most three questions per round,** most important first.
   - **Continue at once** on submit, in the same turn. Read the free
     text: it can change the task.
3. Autonomous: record the blocker as an agenda inbox item and a GitHub
   issue (`gtd` skill, "Capture from another repo") with evidence and
   options. File the issue only in a repo of the user. Elsewhere the
   agenda inbox item alone records the blocker. When the stack skill
   names a default for this case, take it and say so in the issue.
   Otherwise work on something else. Do not decide the blocker.

- **Issues.** Before you file an issue, check the open issues and the
  roadmap.
- **Deferred items and follow-ups** go to the agenda (`gtd`), not to
  files in the repo. The one exception is `HANDOFF.md` for open work.
  Write it only when another worker continues or the user asks. Never
  commit it: list it in `.git/info/exclude`.

- **Findings and questions.** Put findings in the chat as a numbered
  list with stable numbers. Ask for the decisions with the question
  tool, citing item numbers. A final report's "Open" part lists open
  items, not questions.
- **"Do we need X?" is a question:** answer, change nothing.
- **"Plan first", "discuss first", "report first":** no edits until the
  user agrees. Plan in the chat unless the user asks for a file.
- **Never in code:** no open question in a comment or a doc.
- **Outward text is a draft.** Show issue replies, posts, emails and
  pull request texts to the user before you send them. No emojis, no
  marketing. Exception: an issue in the user's own repo that records a
  blocker, or that the user asked for, needs no draft.
- **Plain text deliverables:** reports and analyses are Markdown in the
  chat. Make no HTML page, artifact or chart unless the user asks for
  one.
- **Language.** The user writes German, English or both, fast and with
  typos. Chat replies use the language of the prompt. A mixed prompt
  counts as English. Technical explanations of code, models and fixes
  are in English. Files, comments, commit messages and notification
  posts are English, unless the file around them is German (agenda:
  `gtd`). German text uses German spelling (ß, 15.000).
- **"Sorry, wrong terminal"** means: ignore that prompt and continue the
  earlier task.
- **Be honest and plain.** Give a critical opinion directly. Explain
  with an example, not jargon. When contradicted, check again.

## 3. Verification

- **Measure every claim** (numbers, citations, "raises X") by running
  code or reading the source (`gh api repos/O/R/contents/PATH`).
- **Install tools for your own use** as `sandbox-env` says, or name
  what is not verified.
- **Reproduce in the user's real setup** (configuration, window size,
  theme, data shape). Minimal configurations are for demos only.
- **Measure pixels** where alignment matters.
- **Regenerate all committed pictures** after a change to drawing
  code, at the project's one width and theme. Screenshots that verify a
  change still cover each theme.
- **Prove a test red** against the code with the fix removed.
- **Results against a reference:** see `ml-project`, "Validating
  research code".
- **Iterate fast, finish complete:** check with reduced sizes, run the
  full version once at the end. Short on time: make all edits, then one
  run.

## 4. Continuous review

Review runs all session by default. "No reviews", "save tokens" and
"no subagents" turn reviews off: arm no monitor, spawn no reviewer, and
review your own changes. On review-only requests, change nothing.

### 4.1 Arm the commit monitor

Unless the user turned reviews off, before the first commit in any
repo except `<agenda repo>`, start one watcher for all repos of the
session. Run `tools/review-watch.sh REPO...` (relative to this skill's
directory) with the monitor tool (Claude Code: `Monitor`) or as a polled
background job. It watches the current branch (override: `BRANCH`).
Re-arm it when it times out. When a repo joins later, re-arm the
monitor with all repos.

- **Trigger:** 100 or more changed lines outside `*.md` and `*.org`, or
  5 or more commits that touch files outside `*.md` and `*.org`
  (`REVIEW_LINES`, `REVIEW_COMMITS`).
  Smaller changes accumulate. Docs-only changes, including decks in
  `.org`, wait for the final round.
- For rewritten history, pushed work and the state directory, read
  `reference.md`, "Commit monitor details".

### 4.2 Run a round on each event

On a `REVIEW` line:

1. Continue your own work.
2. Spawn the reviewers in parallel, one subagent per view.
3. Verify each finding yourself.
4. Fix in small commits. The monitor sends them into the next round.
5. Keep a "checked and rejected" list with reasons.

### 4.3 Reviewers

One subagent per view. The first three views run in every round.

| View | Looks for | When |
|---|---|---|
| **Bugs** | wrong behaviour, regressions, unhandled real failures, each with a reproduction that runs | always |
| **Simplicity** | the simpler alternative for each addition; code, files, options and stages to delete; reinvented features; special treatments; code for rare edge cases; backwards compatibility | always |
| **Leftovers and consistency** | dead code, stale files, drifted docs and comments, history in comments, naming, the same thing done two ways, drift between repos | always |
| **Docs** | wrong or incomplete docs, duplication, a README that reads like a manual or an agent rules file, STE wording | docs or public behaviour changed |
| **Security** | secrets, permissions, exposure, hardening | deployment, network, auth or secrets changed |
| **Efficiency** | hot paths, redisplay or UI latency, runtime, deploy time | performance-relevant code changed |
| **Usability** | public API, CLI, configuration, UI and UX, looks in every mode; never propose a friendlier error for rare misuse | user-facing surface changed |
| **Results** | numbers against the reference; the data source of every figure and table by file path; labels, sides and groups that match the data | research code, figures or slides changed |
| **Attacker** | tries to break into or bring down a test system | on request only, never against a production host |
| **Coverage** | rules the user stated in past sessions (their messages, memory notes) that the changed skills, AGENTS.md or docs miss, weaken or contradict | a skill, AGENTS.md or another agent rules file changed |

The Simplicity reviewer loads the `ponytail-review` skill when it is
available and challenges every decision, also agreed ones.

Before you spawn, read `reference.md`, "Reviewer brief".
Include this skill's hard rules, section 1 and the stack skill's hard
rules in each brief.

- **breaks**, **endangers**: verify, then fix.
- **simplifies**: verify, then apply. When it changes behaviour the user
  asked for, ask (section 2).
- **nit**: fix only as a one-line change in a file you touch anyway.
  Nits never keep a loop going.

### 4.4 Final round

Run a final round before a merge, a release or the end of the session.
Also run one on "review loop", "cleanup cycle", "polishing round" or
"loop until clean". Review the whole range from the commit after this
session's last clean final round. If there is none, start from the
session's first commit.

1. Spawn all views that apply, with fresh reviewers.
2. Verify, fix, commit.
3. Repeat until **two rounds in a row** are clean: no breaks, endangers
   or simplifies finding survives verification.
4. Report what changed, what was rejected and why, and what is open.

There is no round limit. When rounds keep finding things, fix the
upstream pattern (fixes add code, a view drifts). For a written review,
read `reference.md`, "findings.md".

## 5. Interactive and autonomous sessions

A session is autonomous only when the user says so ("I'm away", "work
alone", "autonomous", "bis später", "über Nacht"). A session without a
user (headless, scheduled, a notification channel only) is also
autonomous. Silence alone never makes a session autonomous. Every other session is interactive.

Autonomous:

- **Arm a watchdog:** a wake-up every 30 minutes (Claude Code:
  `ScheduleWakeup`, a cron or a loop) that resumes the work until it is
  done.
- **Report on your own:** post one line in the chat when a background
  job ends or a milestone lands. When the user named a notification
  channel, post there too and poll it for replies. Do not wait for
  "status?".
- **Run independent work in parallel** by default, within the resource
  limits the user stated.
- **Resume after limits** and relaunch failed subagents with the same
  brief.
- **Keep monitors armed** for commits and each long job. Restart a
  process only after you checked it is gone.
- **When idle**, clean leftovers, drifted docs and drift between repos.

Always:

- **Other agents.** "Another agent works on X": do not touch X. "Just
  file issues": file issues, fix nothing.
- **"Where are we?"**: done, running, next, blocked.
- **End of session.** Run the `session-finish` skill once per session;
  its description names the triggers.

## 6. Sandbox and environment safety

- **Paths.** `~` in a skill means `$HOME` (in a sandbox: the agent's
  home). A path in the user's home is written `<user home>/...`, for
  example `<user home>/.emacs.d`.
- **Placeholders.** The workspace placeholders are `<user home>`,
  `<agenda repo>`, `<notes dir>`, `<presentations dir>`, `<test rig>`,
  `<secrets repo>` and `<skeleton checkout>`. Resolve
  each one in this order:
  1. the `AGENTS.md` in the working directory or its nearest parent,
  2. the user-level agent instructions (Claude Code:
     `~/.claude/CLAUDE.md`; opencode: `~/.config/opencode/AGENTS.md`),
  3. agent memory.

  When none has it, ask. Autonomous: skip the step that needs the
  value and list it under "Open" in the final report. When the task
  cannot go on without the value, record a blocker (section 2).
  Every other `<...>` in a skill is a template slot.
- **Work only on the mounted checkouts.** Report a missing or read-only
  path. Never clone around it or push from a local copy.
- **The working directory can reset:** `cd` per command or `git -C`.
- **Do not edit what a running job reads.** Wait, or use a worktree.
- **Commands for the host:** give the exact command or a script file.

## 7. Style

- **Naming.** Use the most obvious name that matches the code. Use the
  same name in code, configs, stages, plot labels and slides. Do not
  invent terms.
- **Spacing.** One space after a sentence. Only Emacs docstrings and
  `;;; Commentary:` keep two spaces.
- **Simplified Technical English** in docs and outward text. Write at
  most 25 words per sentence, in active voice, with one word for one
  thing. Use no em or en dashes and no first person.
- **Comment only a "why"** the code cannot say. No banners beyond the
  stack skill's section markers.
- **No anecdotes:** no "previously", no incident stories, no
  before/after numbers.
- **Docs over comments.** Move long comments into the docstring or the
  docs.
- **Same things look the same:** one code path, one naming scheme.
- **Self-contained scripts** with explicit paths and arguments.
- **Complexity limits** come from hooks. Split a function instead of
  raising the limit.
- **The README is for a person:** what it is, how to install and run it,
  where to read more. Details go to `docs/`, contributor rules to
  `CONTRIBUTING`, agent rules to a skill. No general maintenance or
  troubleshooting guides. No links to files the reader cannot open.
- **One place per fact.** Other docs link there. No documents outside
  the repos.
- **Match the existing style** of the user's earlier work of the same
  kind (decks: `org-beamer-presentation`).

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, push and attribution rules, tagging and releases.
