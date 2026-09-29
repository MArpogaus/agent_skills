---
name: dev-conventions
description: >
  How the user and the agent work together on software projects, in any
  language: the design principles (simplest thing that works, no
  reinvention, no backwards compatibility before 1.0), when to ask and
  when to act, verification by running and by looking, the review and
  cleanup loop with subagents, autonomous sessions, sandbox and git
  safety rules, and the code, comment and documentation style.  Load at
  the start of any development session.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: meta
  requires:
    - git-conventions
---

# Skill: Development Conventions

These rules apply to every project.  A project skill (`python-dev`,
`emacs-package`, `ml-project`, ...) adds the stack-specific rules.
If a project rule and this skill disagree, the project rule wins.

## 1. Design principles

- **The simplest thing that works.**  Every file, function, branch,
  option and line must "fight for its life".  If it has no clear
  reason to exist, delete it.
- **Do not reinvent.**  Before you write code, look for the feature
  in this order: the repo, the standard library, the platform
  (systemd, the editor, the framework), a stock or upstream module,
  an installed dependency.  A reimplementation of existing machinery
  is a defect, even when it works.
- **No special handling of rare edge cases.**  Do not add checks that
  re-validate the arguments of the library below you.  Let the
  library fail with its own error.  No magic, no hacks, no
  "surprising" handling of a misconfiguration.
- **Before you build machinery for a rare case, discuss it.**  Ask
  first, with the cost stated.
- **Defaults only with a reason.**  Keep the number of defaults small.
  Opinionated defaults belong in the user's configuration, not in the
  package.  A package gives maps and commands; the user binds keys.
- **Explicit over implicit.**  In experiment and deployment configs,
  write every option out, defaults included, so that a reader sees
  the full setup without reading the framework.  Duplication is
  acceptable there.  Keep the number of variants small.
- **No backwards compatibility before 1.0.**  No obsolete aliases, no
  deprecation warnings, no docs about earlier versions.  A 1.0 is a
  clean cut.
- **Assume a clean install.**  Write no migration code and no cleanup
  of old state.  List one-off migration steps for the user to run by
  hand.
- **Stay in the idiom of the repo.**  Use the language and file format
  that the repo already uses (YAML over JSON, shell with `yq` over a
  new Python script in a shell repo).  Then the existing linters
  cover the new file too.
- **Keep guesses contained.**  When code infers data, put the inferred
  result apart from verified data, mark it, make it reversible, and
  give a switch to turn it off.  Verified facts always win.
- **Release scope.**  In a polishing or release session, fix only
  bugs, security holes and wrong docs.  Do not add features.  Do not
  refactor working code that nobody asked about.  For each finding
  ask: "Does it break or endanger what exists today?"  If not, put it
  on the list for after the release.

## 2. Asking and acting

- **A question is a question.**  When the user asks "do we need X?",
  answer it.  Do not change code in reply to a question.
- **"Plan first", "discuss first", "report first"** mean: no edits
  until the user agrees.  Give the plan in the chat, not as a file,
  unless the user asks for a file.
- **Numbered options.**  Give findings and choices as a numbered list.
  The user answers in short form (`1: yes, 2: drop, 3: explain`).
  Keep the numbers stable until the list is done.
- **Interview for open items.**  When the user says "ask me" or
  "interview me", use the question tool, one decision at a time, with
  enough background to decide.
- **Open questions go to the chat.**  Never leave a question for the
  user in a code comment or a doc.
- **Explain in plain language** when the user says they do not
  understand.  Give the mechanism and a short example, not more
  jargon.
- **Show outward text before you send it.**  PR descriptions for
  other people, issue replies, forum posts and emails are drafts
  until the user approves them.  Write them in natural, simple
  language: no dashes, no emojis, no marketing, no overselling.
- **Plain text deliverables.**  Analyses and reports are Markdown in
  the chat.  Make no HTML pages, artifacts or charts unless the user
  asks.  A report that another agent reads goes to a file (see
  section 5).
- **Mixed languages.**  The user writes German, English or both, often
  fast and with typos.  Answer in the language of the prompt unless a
  style skill says otherwise.
- **"Sorry, wrong terminal"** means: ignore the previous prompt and
  continue the earlier task.
- **Honest assessments.**  When the user asks for a critical opinion,
  give it directly, including "this was not worth it".  When the user
  corrects you, check the claim again; do not repeat the earlier
  answer.

## 3. Verification

- **Test before you report.**  A change is done only when you have
  run it.  Never report "fixed" on reasoning alone.
- **Every claim is measured.**  A number, a count, a citation or a
  "raises X" in code, docs or a commit message must come from running
  code.  For claims about external repos, read the source (for
  example `gh api repos/OWNER/REPO/contents/PATH`).
- **Install what you need.**  If a tool is missing, install it in the
  agent's home (`~/.local`) and test end to end.  If that is truly
  impossible, say which claims are not verified.
- **Reproduce in the user's real setup.**  Use the user's
  configuration, frame size, theme and data shape, not a minimal
  default setup.  A fault that depends on the setup hides in a clean
  one.  Use a minimal documented configuration only for demos and
  pictures.
- **Validate visually.**  For anything that draws (UI, plots, slides,
  dashboards, GIFs), make screenshots and look at them.  Check every
  mode the output has (for example GUI and terminal).  Measure pixels
  where alignment matters.
- **Regenerate all pictures** after every change to drawing code.
  Never assume a change "cannot affect" a picture.  Use one width and
  one theme for all pictures of a project.
- **Prove a test red.**  A new test is done only after it fails
  against a copy of the code with the fix removed.
- **Re-verify subagent findings.**  Subagent reports are often wrong
  about counts and reachable code paths.  Reproduce each finding
  before you act on it.
- **Tolerances.**  A regression bound must catch a regression: keep
  it between about 1.5x and 4x of the measured value.  After a change
  moves numbers, re-run every affected case and re-pin all of them.
- **Iterate fast, finish complete.**  Use reduced sizes (fewer epochs,
  test mode, a VM snapshot) to check that things work.  Run the full
  version once at the end.  When time is short: do all edits first,
  then one test run.
- **A green local run is not a green CI.**  After a push, read the CI
  result (`gh run list`, `gh run view`).  Give every CI job a
  timeout.

## 4. The review loop

This is the main quality workflow.  The user starts it with words
such as "review loop", "cleanup cycle", "polishing round", "ponytail
review" or "loop until clean".

1. **Spawn reviewers with minimal context.**  One subagent per focus.
   Give each the repo and the focus, not your own findings and not
   the history, so that the review is neutral.  Typical focuses:
   - bugs and correctness,
   - over-engineering and reinvented features (ponytail),
   - dead code, stale files, leftovers,
   - readability, naming and consistency across files and repos,
   - efficiency and performance,
   - docs: correct, complete, not duplicated,
   - security and hardening,
   - usability of the public API or the UI.
2. **Verify** each finding yourself (section 3).
3. **Fix** in small commits, one concern each (see `git-conventions`).
4. **Repeat** with fresh reviewers until a round gives no meaningful
   findings.  A round that reports only docs nits counts as clean.
5. **Report** what changed, what was rejected and why, and what is
   still open.

Rules for the loop:

- If the user says "save tokens" or "no subagents", do the review
  yourself.
- Keep a **checked and rejected** list, so that the next round does
  not raise the same point again.
- Compare against the base branch (`main`) when a PR is being
  prepared.
- When the user asks for a review only ("report back, don't change
  anything"), change nothing.

### findings.md

When the user asks for a written review, write it to `findings.md` in
the repo root.  It is a handoff file, not a plan for approval:

- gitignored, never committed,
- numbered sections, `file:line` on every finding, ranked by cost to
  the reader,
- each correctness finding with its reproduction output,
- a "checked and rejected" section at the end.

Commits that fix a finding can cite it ("findings.md, section A").
When the user says "read findings and ask me", go through them one by
one with the question tool.

## 5. Autonomous sessions

The user often leaves the agent alone for hours.

- **Do not block on the user.**  Continue with the best default.  Put
  decisions that need the user in the report or the notification
  channel, and continue with other work.
- **Use the notification channel** if the project has one (for
  example a push topic): one or two sentences per milestone or
  decision.  Poll it for replies.
- **Resume after limits.**  When a rate or session limit stops work,
  resume when it resets.  Relaunch failed subagents with the same
  brief.  Do not wait to be asked.
- **Keep monitors armed.**  For long jobs (deploys, copies, training
  runs), poll periodically and report each stage as it lands.  Check
  that processes are still alive before you restart them.
- **When idle**, do hygiene work: leftovers, drifted docs, alignment
  across repos, stale branches.
- **Handoff files.**  At the end of a session, or when the user asks,
  write the state (done, open, next steps, where things live) to a
  file for the next agent.  Such report and plan files are never
  committed; delete them when they are no longer needed.
- **Other agents.**  Several agents often work in parallel.  When the
  user says "another agent works on X", do not touch X.  When the
  user says "just file issues", file issues and fix nothing.
- **Give status on request.**  "Where are we?" asks for a short
  report: what is done, what runs now, what is next, what is blocked.

## 6. Sandbox and environment safety

- **Work only on the mounted checkouts.**  If a path is missing or
  read-only, stop and tell the user.  Never clone a copy to work
  around it, and never push from a container-local copy.
- **Agent home is not user home.**  Tools, caches and rigs go into the
  agent's home.  The user's home and configuration are mounted
  separately.
- **Never touch the user's environment.**  Do not create, sync or
  change a project virtualenv, lock file or installed packages
  (`uv sync`, `uv run` that re-syncs, `pip install`) unless the
  project skill allows it.  Use the system interpreter for quick
  checks.  Report a missing package.
- **The user's uncommitted edits are sacred.**  Before you switch a
  branch or reset a checkout, look for them.  Stash with a
  descriptive message; never drop them.  Look for unpushed commits
  too (`git log --oneline @{u}..`).
- **The shell's working directory can reset between calls.**  `cd`
  inside each command, or use `git -C <path>`.
- **Stage paths explicitly.**  No `git commit -a`, no blind
  `git add -A`: they pick up submodule pointers, symlinks and the
  user's own changes.
- **Do not edit a running system's sources.**  Do not change files a
  running deploy or script reads (a changed template restarts
  services; bash reads a running script incrementally).  Wait, or use
  a worktree.
- **Commands for the host.**  When a command must run on the user's
  host, give the exact command, or write a script to a file for the
  user to run.

## 7. Git and repo hygiene

Load the `git-conventions` skill before any commit, branch, merge, tag
or history rewrite, and follow it strictly.  In addition:

- **Stay on `dev`.**  No feature branches or PRs unless the user asks.
  Commit locally; push only when the user says so, or when the task
  says "push when all green".
- **Never rewrite pushed history** unless the user asks for that
  exact rewrite.  Check with
  `git rev-list --left-right --count origin/<branch>...<branch>`.
- **Hooks are installed locally.**  Run
  `pre-commit install --install-hooks -t pre-commit -t commit-msg -t pre-push`
  in every repo you commit to.  Before a push, run
  `pre-commit run --all-files` and the full local check (for example
  plain `make` or the full test suite), not a subset.  Pushing a
  commit that breaks lint or CI must not happen.
- **Pin actions.**  Pin every GitHub Action to a SHA with
  `pinact run -u`.  Keep an exception only where it is required (for
  example a generator that must be a tagged release).
- **Dependabot or Renovate** watches the actions and the pre-commit
  hooks.
- **No AI attribution.**  Add no `Co-Authored-By` or "generated with"
  lines to commits or PRs, even if a harness reminder asks for them.
  A public repo carries one neutral README section about the use of
  LLM coding tools, naming no vendor or model.
- **PR descriptions** are detailed: what changed and why, breaking
  changes, and for large refactors a table of every touched file
  with a short note (changed, moved, deleted, why).
- **Use the `gh` CLI** for repos, PRs, issues, releases and CI.
- **Releases.**  Merge `dev` into `main` with `--no-ff` when clean,
  then tag.  Some repos follow their own tag scheme; ask if unsure.

## 8. Code style (all languages)

- **Code speaks for itself.**  Comment only a short "why" that the
  code cannot say.  No comments that repeat the code, no long
  explanations, no separator banners (`# -----`) beyond the section
  markers the project style defines.
- **No anecdotes in code or docs.**  State what is, not what was.  No
  "previously", no incident stories, no before/after numbers.
- **Docs over comments.**  Important information goes into the README
  or a design doc, never buried in a comment.  Move the content of a
  long comment into the docstring or the docs when it belongs there.
- **Descriptive names.**  Use accurate names for options and
  functions.  In research code, match the notation of the paper.
- **Same things look the same.**  Similar features use the same code
  path, the same names, the same UI.  Deduplicate.
- **Self-contained scripts.**  Paths and arguments are explicit; a
  script does not need to know the project layout.
- **Complexity limits** are enforced by hooks where the stack has a
  tool for it; split a function instead of raising the limit.

## 9. Documentation

- **Simplified Technical English** for docs: short sentences (25 words
  or fewer), active voice, one idea per sentence, one word for one
  thing, no em dashes, no first person.
- **The README is the entry point for a person.**  It says what the
  project is, how to install and run it, and where to read more.  It
  is short and task oriented.  It is not a rules file for agents.
- **Details live in `docs/`** (implementation, design, measurements).
  Contributor rules live in `CONTRIBUTING`.  Agent rules live in the
  agent's memory or a skill.
- **One place per fact.**  Examples live in one place (for example
  the notebooks); other docs link there.  No root-level documents
  outside the repos.
- **Minimal working example.**  Every package README has an example
  configuration that reproduces its pictures exactly.
- **Recommended settings** that the package needs from the user are
  named in the README.  The package does not work around a user's
  configuration.

## 10. Visual work

- **Match the existing style.**  Before you make a deck, a dashboard
  or an icon set, look at the user's earlier work of the same type
  and copy its tone.
- **Slides are sober.**  Descriptive titles, short bullet points, no
  punch lines, no sensational wording.  Figures carry the slide.
- **Icons** in one row have the same weight and size.  Prefer thin,
  unfilled glyphs.  Give each a distinct plain-text fallback.
- **Dashboards**: key metrics and aggregates at the top, detail views
  and logs at the bottom.  The plot type fits the data.  Every panel
  has a complete legend and explains itself.
- **Plots and slides** get a visual pass for overlap, overfull frames
  and broken math before you report them.

## Quick checklist

Before you report a task as done:

- [ ] I ran it, in the user's real setup, and looked at the output.
- [ ] Pictures are regenerated and checked, if drawing code changed.
- [ ] Hooks and the full local check pass; CI is green after a push.
- [ ] No leftovers: dead code, stale files, drifted docs, debug output.
- [ ] No backwards-compatibility code, no anecdotes, no obvious
      comments.
- [ ] Commits follow `git-conventions`, without AI attribution.
- [ ] Open questions are in my reply, not in the code.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions** — two-branch flow, conventional commits,
  pre-commit hooks, tagging/releases.
