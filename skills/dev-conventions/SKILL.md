---
name: dev-conventions
description: >
  How the user and the agent work together on software projects, in any
  language: design principles (simplest thing that works, no
  reinvention, no backwards compatibility before 1.0), when to ask and
  when to act, verification by running and by looking, the continuous
  review loop (a commit monitor starts subagent reviews when enough
  changes pile up), autonomous sessions, sandbox safety, and code,
  comment and documentation style.  Load at the start of any
  development session.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: meta
  requires:
    - git-conventions
---

# Skill: Development Conventions

These rules apply to every project.  A stack skill (`python-dev`,
`ml-project`, `emacs-package`, `emacs-config`,
`org-beamer-presentation`, ...) adds the rules of its stack.  If
a project rule and this skill disagree, the project rule wins.

All git rules (branches, commits, hooks, pushes, attribution, pull
requests, releases) live in the `git-conventions` skill.  Load it
before any git operation and follow it strictly.  This skill does
not repeat them.

## 1. Design principles

- **The simplest thing that works.**  Every file, function, branch,
  option and line must fight for its life.  If it has no clear
  reason to exist, delete it.
- **Do not reinvent.**  Before you write code, look for the feature
  in this order: the repo, the standard library, the platform
  (systemd, the editor, the framework), a stock or upstream module,
  an installed dependency.  A reimplementation of existing machinery
  is a defect, even when it works.
- **No code for rare edge cases.**  Do not re-validate the arguments
  of the library below you; let it fail with its own error.  No
  magic, no hacks, no surprising handling of a misconfiguration.  If
  a rare case seems to need machinery, discuss it with the user
  first and state the cost.
- **Defaults only with a reason.**  Keep defaults few.  Opinionated
  defaults go into the user's configuration, not into the library.
- **Explicit configuration.**  Configs of experiments and deployments
  write every option out, defaults included, so that a reader sees
  the full setup without reading the framework.  Duplication is
  acceptable there.  Keep the number of variants small.
- **No backwards compatibility before 1.0.**  No obsolete aliases, no
  deprecation warnings, no text about earlier versions.  A 1.0 is a
  clean cut.
- **Assume a clean install.**  Write no migration code and no cleanup
  of old state.  List one-off migration steps for the user to do by
  hand.
- **Stay in the idiom of the repo.**  Use the language and file format
  the repo already uses (YAML over JSON, shell with `yq` over a new
  Python script in a shell repo), so that the existing linters cover
  the new file.
- **Contain guesses.**  When code infers data, keep the inferred
  result apart from verified data, mark it, keep it reversible, and
  give a switch to turn it off.  Verified facts always win.
- **Release scope.**  In a polishing or release session, fix only
  bugs, security holes and wrong docs.  Add no features and do not
  refactor working code that nobody asked about.  For each finding
  ask: "Does it break or endanger what exists today?"  If not, put
  it on the list for after the release.

## 2. Asking and acting

- **A question is a question.**  When the user asks "do we need X?",
  answer it and change nothing.
- **"Plan first", "discuss first", "report first"** mean: no edits
  until the user agrees.  Give the plan in the chat, unless the user
  asks for a file.
- **Numbered options.**  Give findings and choices as a numbered
  list.  The user answers in short form (`1: yes, 2: drop, 3:
  explain`).  Keep the numbers stable until the list is done.
- **Interviews.**  When the user says "ask me" or "interview me",
  use the question tool (Claude Code: `AskUserQuestion`), one
  decision at a time, with enough background to decide.
- **Open questions go to the chat**, never into a code comment or a
  doc.
- **Plain explanations.**  When the user does not understand, explain
  the mechanism with a short example, not with more jargon.
- **Outward text is a draft.**  Show issue replies, forum posts,
  emails and pull request texts for other people before you send
  them.  Write natural, simple language: no em or en dashes, no
  emojis, no marketing, no overselling.
- **Plain text deliverables.**  Analyses and reports are Markdown in
  the chat.  No HTML pages, artifacts or charts unless asked.
- **Mixed languages.**  The user writes German, English or both, fast
  and with typos.  Answer in the language of the prompt unless a
  style skill says otherwise.
- **"Sorry, wrong terminal"** means: ignore that prompt and continue
  the earlier task.
- **Honest assessments.**  Give a critical opinion directly when asked,
  including "this was not worth it".  When the user contradicts a
  claim, check it again instead of repeating it.

## 3. Verification

- **Test before you report.**  A change is done only when you ran it.
  Never report "fixed" on reasoning alone.
- **Measure every claim.**  A number, a count, a citation or a
  "raises X" in code, docs or a commit message comes from running
  code.  For claims about another repo, read its source (for example
  `gh api repos/OWNER/REPO/contents/PATH`).
- **Install what you need** in the agent's home (`~/.local`) and test
  end to end.  If that is impossible, say which claims are not
  verified.
- **Reproduce in the user's real setup**: their configuration, window
  size, theme and data shape.  A fault that depends on the setup
  hides in a clean one.  Use a minimal documented configuration only
  for demos and pictures.
- **Look at it.**  For anything that draws (UI, plots, slides,
  dashboards, GIFs), make screenshots and look at them, in every mode
  the output has (for example GUI and terminal).  Measure pixels where
  alignment matters.
- **Regenerate all pictures** after every change to drawing code.
  Never assume a change cannot affect a picture.  Use one width and
  one theme for all pictures of a project.
- **Prove a test red.**  A new test is done only when it fails against
  a copy of the code with the fix removed.
- **Re-verify subagent findings.**  Subagent reports are often wrong
  about counts and reachable code paths.  Reproduce each finding
  before you act on it.
- **Results against a reference.**  Research code is checked against
  known ground truth; the `ml-project` skill has the rules for
  references and tolerances.
- **Iterate fast, finish complete.**  Check with reduced sizes (fewer
  epochs, test mode, a VM snapshot).  Run the full version once at the
  end.  When time is short, make all edits first, then one test run.

## 4. Continuous review

Review is not a phase at the end.  It runs during the whole session:
a monitor watches the commits, and when enough unreviewed change has
piled up, a round of reviewers starts on that range.  **This is the
default.**  Turn it off only when the user says so ("no reviews",
"save tokens", "no subagents"); then review your own changes before
you report.  When the user asks for a review only ("report back,
change nothing"), change nothing.

### 4.1 Arm the commit monitor

At the start of a session that will commit, start one watcher for all
repos of the session.  Run it with the harness's monitor tool (Claude
Code: `Monitor`), or as a background job that you poll.  Write the
script to the agent's cache, not into the repo:

```bash
#!/bin/bash
# review-watch.sh REPO...: print one REVIEW line when the unreviewed
# range on $BRANCH crosses the threshold, then mark it as handed out.
BRANCH=${BRANCH:-dev} REVIEW_LINES=${REVIEW_LINES:-100} REVIEW_COMMITS=${REVIEW_COMMITS:-5} EVERY=${EVERY:-300}
STATE=${STATE:-$HOME/.cache/review-watch}; mkdir -p "$STATE"
while true; do
  for r in "$@"; do
    f=$STATE/$(realpath "$r" | tr / _)
    head=$(git -C "$r" rev-parse -q --verify "$BRANCH") || continue
    [ -s "$f" ] || { echo "$head" > "$f"; continue; }
    last=$(cat "$f")
    [ "$head" = "$last" ] && continue
    git -C "$r" merge-base --is-ancestor "$last" "$head" || last=$(git -C "$r" merge-base "$last" "$head")
    n=$(git -C "$r" rev-list --count "$last..$head" -- . ':!*.md' ':!*.org')
    code=$(git -C "$r" diff --numstat "$last" "$head" -- . ':!*.md' ':!*.org' | awk '{s+=$1+$2} END {print s+0}')
    if [ "$code" -ge "$REVIEW_LINES" ] || [ "$n" -ge "$REVIEW_COMMITS" ]; then
      echo "REVIEW $r ${last:0:7}..${head:0:7} commits=$n code_lines=$code"
      echo "$head" > "$f"
    fi
  done
  sleep "$EVERY"
done
```

- **Trigger:** 100 or more changed lines outside docs, or 5 or more
  commits that touch code.  Smaller changes accumulate until they
  cross the line.  Changes to docs only wait for the final round.
  Tune `REVIEW_LINES` and `REVIEW_COMMITS` per project.
- **Rewritten history** (an amend or rebase of local commits) resets
  the range to the merge base, so the rewritten commits are reviewed
  again.
- **Pushed work in several repos:** the same loop can read the remote
  instead: `gh api repos/OWNER/REPO/commits/BRANCH -q .sha` for the
  tip and `gh api repos/OWNER/REPO/compare/OLD...NEW` for the files
  and lines.
- **Re-arm** the monitor when it times out.  Keep the state directory,
  so that no range is lost or reviewed twice.

### 4.2 Run a round on each event

When a `REVIEW` line arrives:

1. **Continue your own work.**  The reviewers run in the background.
   Start no second round on an overlapping range while one runs.
2. **Spawn the reviewers** for that range (section 4.3), one subagent
   per view, in parallel.
3. **Verify** each finding yourself (section 3).
4. **Fix** in small commits, as `git-conventions` requires.  The fixes
   are new commits, so the monitor sends them into the next round.
   That is intended: a second round often catches regressions in the
   fixes of the first.
5. **Keep a "checked and rejected" list** with the reason for each
   item, so that later rounds do not raise it again.

### 4.3 Reviewer views

Every round uses the three core views.  Add the others when the range
touches their subject.

| View | Looks for | When |
|---|---|---|
| **Bugs** | wrong behaviour, regressions, unhandled real failures; each with a reproduction | always |
| **Simplicity** (ponytail) | over-engineering, reinvented features, code for rare edge cases, backwards compatibility, dead flexibility | always |
| **Leftovers and consistency** | dead code, stale files, drifted docs and comments, obvious or anecdotal comments, naming, the same thing done two ways, drift between repos | always |
| **Docs** | wrong or incomplete docs, duplication, README scope, STE wording | docs or public behaviour changed |
| **Security** | secrets, permissions, exposure, hardening | deployment, network, auth or secrets changed |
| **Efficiency** | hot paths, redisplay or UI latency, runtime, deploy time | performance-relevant code changed |
| **Usability** | public API, CLI, configuration, UI and UX, looks in every mode | user-facing surface changed |
| **Results** | numbers against the reference (paper, ground truth, earlier run) | research or experiment code changed |
| **Attacker** | tries to break into or bring down a test system | on request only, never against a production host |

Brief each reviewer with **minimal context**: the repo path, the
range, the view, and the rules below.  Do not give it your own
findings or the session history, so that it looks with fresh eyes.

```
You are a read-only reviewer. Repo: <path>. Range: <old>..<new>
(read the diff and the files it touches). View: <view and its
"looks for" text>.
Rules: change no file; run no git command that changes state; contact
no host; run no deploy. Report each finding with file:line, severity,
and how to reproduce it. If you find nothing that matters, answer
"clean".
```

### 4.4 Final round

Before a merge, a release or the end of the session, and when the
user says "review loop", "cleanup cycle", "polishing round" or "loop
until clean", review the whole range since the last clean state,
whatever its size:

1. Spawn all views that apply, with fresh reviewers.
2. Verify, fix, commit.
3. Repeat until a round gives no meaningful findings.  A round with
   only docs nits counts as clean.
4. Report what changed, what was rejected and why, and what is open.

### 4.5 findings.md

When the user wants the review written down, write `findings.md` in
the repo root.  It is a handoff file, not a plan waiting for
approval:

- never committed: list it in `.git/info/exclude` (or the repo's
  `.gitignore` if it already ignores it),
- numbered sections, `file:line` on every finding, ranked by cost to
  the reader,
- the reproduction output for each correctness finding,
- a "checked and rejected" section at the end.

Commits that fix a finding can cite it ("findings.md, section A").
When the user says "read the findings and ask me", go through them
one at a time with the question tool.

## 5. Autonomous sessions

The user often leaves the agent alone for hours.

- **Do not block on the user.**  Continue with the best default.
  Collect decisions for the user in the report or the notification
  channel, and work on something else meanwhile.
- **Notification channel.**  If the project has one (for example a
  push topic), post one or two sentences per milestone or decision,
  and poll it for replies.
- **Resume after limits.**  When a rate or session limit stops work,
  resume when it resets and relaunch failed subagents with the same
  brief.  Do not wait to be asked.
- **Keep monitors armed**: the commit monitor (section 4.1) and one
  for each long job (deploy, copy, training run).  Report each stage
  as it lands.  Check that a process is still alive before you
  restart it.
- **When idle**, do hygiene work: leftovers, drifted docs, alignment
  across repos.
- **Handoff files.**  At the end of a session, or when asked, write
  the state (done, open, next steps, where things live) to
  `HANDOFF.md` in the repo root, listed in `.git/info/exclude`.
  Report and plan files are never committed; delete them when they
  are no longer needed.
- **Other agents.**  When the user says "another agent works on X",
  do not touch X.  When the user says "just file issues", file issues
  and fix nothing.
- **Status on request.**  "Where are we?" asks for a short report:
  done, running, next, blocked.

## 6. Sandbox and environment safety

- **Work only on the mounted checkouts.**  If a path is missing or
  read-only, stop and tell the user.  Never clone a copy to work
  around it, and never push from a container-local copy.
- **Agent home is not user home.**  Tools, caches and test rigs go
  into the agent's home.  The user's home and configuration are
  mounted separately.
- **Never touch the user's environment.**  Do not create, sync or
  change a project environment, lock file or installed packages.
  Report a missing package.  The stack skill says which commands are
  safe (for Python see `python-dev`, "UV environment").
- **The user's uncommitted edits are sacred.**  Look for them before
  you switch a branch or reset a checkout.  Stash with a descriptive
  message; never drop them.  Look for unpushed commits as well
  (`git log --oneline @{u}..`).
- **The working directory can reset between shell calls.**  `cd`
  inside each command, or use `git -C <path>`.
- **Do not edit what a running job reads.**  A deploy renders the live
  working tree, and bash reads a running script as it goes.  Wait for
  the job to end, or edit in a worktree.
- **Commands for the host.**  When a command must run on the user's
  host, give the exact command, or write a script to a file for the
  user to run.

## 7. Code style (all languages)

- **Code speaks for itself.**  Comment only a short "why" that the
  code cannot say.  No comments that repeat the code, no long
  explanations, no separator banners beyond the section markers the
  stack skill defines.
- **No anecdotes.**  Code and docs state what is, not what was: no
  "previously", no incident stories, no before/after numbers.
- **Docs over comments.**  Important information goes into the README
  or a design doc, never buried in a comment.  Move a long comment
  into the docstring or the docs where it belongs.
- **Descriptive names** for options, functions and files.
- **Same things look the same.**  Similar features share one code path,
  one naming scheme and one look.  Deduplicate.
- **Self-contained scripts.**  Paths and arguments are explicit; a
  script does not need to know the project layout.
- **Complexity limits** are enforced by hooks where the stack has a
  tool for it.  Split a function instead of raising the limit.

## 8. Documentation

- **Simplified Technical English**: sentences of 25 words or fewer,
  active voice, one idea per sentence, one word for one thing, no em
  or en dashes, no first person.
- **The README is the entry point for a person.**  It says what the
  project is, how to install and run it, and where to read more.  It
  is short and task oriented.  It is not a rules file for agents.
- **Details live in `docs/`** (implementation, design, measurements).
  Contributor rules live in `CONTRIBUTING`.  Agent rules live in the
  agent's memory or in a skill.
- **One place per fact.**  Examples live in one place (for example the
  notebooks); other docs link there.  No documents outside the repos.

## 9. Visual work

- **Match the existing style.**  Before you make a deck, a dashboard
  or an icon set, look at the user's earlier work of the same kind and
  follow its tone.
- **Slides are sober**: descriptive titles, short bullet points, no
  punch lines.  Figures carry the slide.  See
  `org-beamer-presentation`.
- **Icons** in one set have the same weight and size.
- **Dashboards** put key metrics and aggregates at the top, detail
  views and logs at the bottom.  The plot type fits the data, and
  every panel has a complete legend and explains itself.
- **Before you report**, check plots and slides for overlaps, overfull
  frames and broken math.

## Checklist before "done"

- [ ] I ran it in the user's real setup and looked at the output.
- [ ] Pictures are regenerated and checked, if drawing code changed.
- [ ] The commit monitor is armed, and every `REVIEW` range got its
      round.
- [ ] The final review round came back clean.
- [ ] No leftovers: dead code, stale files, drifted docs, debug output.
- [ ] No backwards-compatibility code, no anecdotes, no obvious
      comments.
- [ ] Git work follows `git-conventions`.
- [ ] Open questions are in my reply, not in the code.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions** — two-branch flow, conventional commits,
  pre-commit hooks, push and attribution rules, tagging and releases.
