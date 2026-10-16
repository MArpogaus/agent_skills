---
name: dev-conventions
description: >
  How the user and the agent work together on software projects, in any
  language: the simplest solution wins, when to ask and when to act,
  verification by running and by looking, the continuous review loop,
  autonomous sessions, sandbox safety, and code and documentation
  style. Load before the first edit, commit or review in any
  repository, and when the user says "plan first", "ask me", "interview
  me", "review loop", "autonomous" or "where are we".
license: MIT
compatibility: claude-code opencode
metadata: {stack: meta, requires: [git-conventions]}
---

# Skill: Development Conventions

These rules apply to every project. A stack skill adds the rules of
its stack. A project rule wins over this skill.

## 1. Design principles

The simplest solution wins, over taste, habit and "best practice".

- **Justify every addition.** Before you add a file, option, script,
  dependency, stage or code path, name the simpler alternative (delete,
  reuse, a config, one line). Use it unless it fails. State it when the
  choice is not obvious.
- **Deletion beats addition.** Delete what has no clear reason to exist.
- **Do not reinvent.** Look in the repo, the standard library, the
  platform, upstream, the installed dependencies. A reimplementation is
  a defect.
- **No special treatments.** No registries, mixins, plugins, frameworks
  or wrappers for one use, no class where a function does, no generator
  for a file you can write by hand.
- **Scripts stay dumb.** One task, explicit arguments, no mode switches:
  one config or script per variant.
- **No code for rare edge cases,** no re-validation of library
  arguments, no magic, no hacks. Discuss machinery for a rare case with
  the user first.
- **Defaults only with a reason.** Opinionated defaults go into the
  user's configuration, not into the library.
- **Explicit configuration:** experiment and deployment configs list
  every option, defaults included.
- **No backwards compatibility before 1.0.** No obsolete aliases, no
  deprecation warnings, no text about earlier versions. A 1.0 is a
  clean cut.
- **Assume a clean install.** No migration or cleanup code. List
  one-off migration steps for the user.
- **Stay in the idiom of the repo** (its language and formats), so
  that its linters apply.
- **Contain guesses.** Keep inferred data apart from verified data:
  marked, reversible, with an off switch.
- **Release scope:** in a release or polishing session, fix only
  bugs, security holes and wrong docs; defer the rest.

## 2. Asking and acting

**When to ask.** Apply in this order. A stack skill's "ask" means this
rule.

1. A blocker (wrong premise, conflict with a rule or skill, missing
   access, a check you cannot fix, a decision not yours) always stops
   that part of the work. Report it with evidence. Never work around
   it in silence or weaken a test or rule to pass it.
2. Interactive (section 5): ask each decision that is the user's
   (findings, design, scope) with the question tool (Claude Code:
   `AskUserQuestion`), also on "ask me" or "interview me".
   - **Context first.** Each option makes sense without the session
     history: what it changes, where, at what cost. Recommended first.
   - **At most three questions per round,** most important first.
   - **Continue at once** on submit, in the same turn. Read the free
     text: it can change the task.
3. Autonomous: never ask, never wait. Record the blocker as an agenda
   inbox item and a GitHub issue (`gtd` skill, "Capture from another
   repo") with evidence and options. Take the default the stack skill
   names, or work on something else. Do not decide the blocker.

- **Findings and questions.** Put findings in the chat as a numbered
  list with stable numbers. Ask for the decisions with the question
  tool, citing item numbers. A final report's "Open" part lists open
  items, not questions.
- **"Do we need X?" is a question:** answer, change nothing.
- **"Plan first", "discuss first", "report first":** no edits until the
  user agrees. Plan in the chat unless the user asks for a file.
- **Never in code:** no open question in a comment or a doc.
- **Outward text is a draft.** Show issue replies, posts, emails and
  pull request texts to the user before you send them. No em or en
  dashes, no emojis, no marketing.
- **Reports are Markdown in the chat** unless the user asks otherwise.
- **Mixed languages.** The user writes German, English or both, fast
  and with typos. Answer in the language of the prompt unless a style
  skill says otherwise.
- **Language of written text.** Write technical explanations of code,
  models and fixes in English, even when the prompt is German. Use
  German, with German spelling (ß, 15.000), for German notes, agenda
  entries and German decks. Over a notification channel always write
  English.
- **"Sorry, wrong terminal"** means: ignore that prompt and continue
  the earlier task.
- **Be honest and plain.** Give a critical opinion directly. Explain
  with an example, not jargon. When contradicted, check again.

## 3. Verification

- **Run it before you report.** Never report "fixed" on reasoning.
- **Measure every claim** (numbers, citations, "raises X") by running
  code or reading the source (`gh api repos/O/R/contents/PATH`).
- **Install what you need** to test end to end, or name what is not
  verified.
- **Reproduce in the user's real setup** (configuration, window size,
  theme, data shape). Minimal configurations are for demos only.
- **Look at it.** Screenshot what draws (UI, plots, slides, GIFs) in
  every output mode. Measure pixels where alignment matters.
- **Regenerate all pictures** after a change to drawing code, with one
  width and one theme per project.
- **Prove a test red** against the code with the fix removed.
- **Re-verify subagent findings** before you act on them.
- **Results against a reference:** see `ml-project`.
- **Iterate fast, finish complete:** check with reduced sizes, run the
  full version once at the end. Short on time: all edits, one run.

## 4. Continuous review

Review runs all session by default. On "no reviews", "save tokens" or
"no subagents", review your own changes. On review-only requests,
change nothing.

### 4.1 Arm the commit monitor

Before the first commit in any repo except `<agenda repo>`, start one
watcher for all repos of the session: `tools/review-watch.sh REPO...`
(relative to this skill's directory), with the monitor tool (Claude
Code: `Monitor`) or as a polled background job. It watches the current
branch (override: `BRANCH`). Re-arm it when it times out.

- **Trigger:** 100 or more changed lines outside `*.md` and `*.org`, or
  5 or more commits that touch code (`REVIEW_LINES`, `REVIEW_COMMITS`).
  Smaller changes accumulate. Docs-only changes wait for the final
  round.
- Rewritten history, pushed work, state: `reference.md`.

### 4.2 Run a round on each event

On a `REVIEW` line:

1. Continue your own work. No second round on an overlapping range.
2. Spawn the reviewers in parallel, one subagent per view.
3. Verify each finding yourself.
4. Fix in small commits; the monitor sends them into the next round.
5. Keep a "checked and rejected" list with reasons.

### 4.3 Reviewers

One subagent per view. Every round runs the three views marked
"always"; add the others when the range touches their subject.

| View | Looks for | When |
|---|---|---|
| **Bugs** | wrong behaviour, regressions, unhandled real failures, each with a reproduction that runs | always |
| **Simplicity** | the simpler alternative for each addition (section 1); code, files, options and stages to delete; reinvented features; special treatments; code for rare edge cases; backwards compatibility | always |
| **Leftovers and consistency** | dead code, stale files, drifted docs and comments, history in comments, naming, the same thing done two ways, drift between repos | always |
| **Docs** | wrong or incomplete docs, duplication, a README that reads like a manual or an agent rules file, STE wording | docs or public behaviour changed |
| **Security** | secrets, permissions, exposure, hardening | deployment, network, auth or secrets changed |
| **Efficiency** | hot paths, redisplay or UI latency, runtime, deploy time | performance-relevant code changed |
| **Usability** | public API, CLI, configuration, UI and UX, looks in every mode | user-facing surface changed |
| **Results** | numbers against the reference; the data source of every figure and table by file path; labels, sides and groups that match the data | research code, figures or slides changed |
| **Attacker** | tries to break into or bring down a test system | on request only, never against a production host |
| **Coverage** | rules the user stated in past sessions (their messages, memory notes) that the changed skills, AGENTS.md or docs miss, weaken or contradict | a skill, AGENTS.md or another agent rules file changed |

Read `reference.md`, "Reviewer brief", before you spawn.

The Simplicity reviewer loads the `ponytail-review` skill when it is
available and challenges every decision, also agreed ones.

Each brief includes the rules of section 1 and the hard rules of the
stack skill, but not your findings, the session history or your memory.

- **breaks**, **endangers**: verify, then fix.
- **simplifies**: verify, then apply, unless it changes behaviour the
  user asked for; then ask (section 2).
- **nit**: fix only as a one-line change in a file you touch anyway.
  Nits never keep a loop going.

### 4.4 Final round

Before a merge, a release or the end of the session, and on "review
loop", "cleanup cycle", "polishing round" or "loop until clean", review
the whole range from the commit where the last final round came back
clean, or the session's first commit:

1. Spawn all views that apply, with fresh reviewers.
2. Verify, fix, commit.
3. Repeat until **two rounds in a row** are clean: no breaks, endangers
   or simplifies finding survives verification.
4. Report what changed, what was rejected and why, what is open.

There is no round limit. When rounds keep finding things, fix the
upstream pattern (fixes add code, a view drifts). A written review:
`reference.md`, "findings.md".

## 5. Interactive and autonomous sessions

A session is autonomous only when the user says so ("I'm away", "work
alone", "autonomous", "bis später", "über Nacht", "loop until clean"
while away), or when it runs without a user (headless, scheduled, a
notification channel only). Silence alone never makes a session
autonomous. Every other session is interactive.

Autonomous:

- **Arm a watchdog:** a wake-up at a fixed interval (Claude Code:
  `ScheduleWakeup` or a cron or loop) that resumes the work until it is
  done.
- **Report on your own:** post one line when a background job ends or a
  milestone lands; do not wait for "status?". Poll the notification
  channel for replies.
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
- **End of session.** Run the `session-finish` skill once per session:
  when the user ends the session ("finish", "wrap up", "Feierabend",
  "session beenden", "done for today"), or before the last message of an
  autonomous session. Not after each task.

## 6. Sandbox and environment safety

- **Work only on the mounted checkouts.** Report a missing or
  read-only path. Never clone around it or push from a local copy.
- **Install tools for yourself** as the `sandbox-env` skill says.
- **Never touch the user's environment:** no project environment, lock
  file or package changes; report a missing package. Safe commands:
  the stack skill (`python-dev`, "uv and the environment").
- **The user's uncommitted edits are sacred.** Check for them and for
  unpushed commits (`git log --oneline @{u}..`) before a branch switch
  or a reset. Stash with a message; never drop.
- **The working directory can reset:** `cd` per command or `git -C`.
- **Do not edit what a running job reads.** Wait, or use a worktree.
- **Commands for the host:** give the exact command or a script file.

Pin GitHub Actions: see `git-conventions`, "CI workflows".

## 7. Style

- **Naming.** Use the most obvious name that matches the code. Use the
  same name in code, configs, stages, plot labels and slides. Do not
  invent terms.
- **Spacing.** One space after a sentence. Only Emacs docstrings and
  `;;; Commentary:` keep two spaces.
- **Simplified Technical English** in docs: at most 25 words per
  sentence, active voice, one word for one thing, no em or en dashes,
  no first person.
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

- **The README is for a person:** what it is, how to install and run
  it, where to read more. Details go to `docs/`, contributor rules to
  `CONTRIBUTING`, agent rules to a skill.
- **One place per fact.** Other docs link there. No documents outside
  the repos.

- **Match the existing style** of the user's earlier work of the same
  kind (decks: `org-beamer-presentation`).
- **Before you report**, check plots and slides for overlaps.

## Checklist before "done"

- [ ] Each addition has a reason why no simpler form works.
- [ ] The change ran in the user's real setup; the output was inspected.
- [ ] Every `REVIEW` range got its round; the final round was clean
      twice in a row.
- [ ] Blockers are reported, or recorded in the agenda and as issues.
- [ ] At the end of the session, `session-finish` ran.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, push and attribution rules, tagging and releases.
