# dev-conventions: reference

Read the section you need: "Reviewer brief" when
you spawn reviewers, "findings.md" when the user wants a review written
down, "Commit monitor details" for rewritten history or pushed work.

## findings.md

When the user wants the review written down, write `findings.md` in
the repo root. It is a handoff file, not a plan that waits for
approval:

- Never commit it: list it in `.git/info/exclude` (or in the repo's
  `.gitignore` if that file already ignores it).
- Use numbered sections, `file:line` on every finding, ranked by cost
  to the reader.
- Give the reproduction output for each correctness finding.
- End with a "checked and rejected" section.

Commits that fix a finding can cite it ("findings.md, section A").
When the user says "read the findings and ask me", go through them one
at a time with the question tool.

## Commit monitor details

- **Rewritten history** (an amend or a rebase of local commits) resets
  the range to the merge base. The monitor then reviews the rewritten
  commits again.
- **Pushed work in several repos:** the same loop can read the remote.
  Use `gh api repos/OWNER/REPO/commits/BRANCH -q .sha` for the tip and
  `gh api repos/OWNER/REPO/compare/OLD...NEW` for the files and lines.
- **State:** the monitor keeps the last handed-out commit per repo in
  `$STATE` (default `~/.cache/review-watch`). Keep this directory when
  you re-arm the monitor, so that no range is lost or reviewed twice.

## Reviewer brief

Add the rules of dev-conventions section 1 and the hard rules of the
stack skill to this text. For the Simplicity view, also add: "A
report without a concrete deletion says for each addition why no simpler form works."

```
You are a read-only, sceptical reviewer. Repo: <path>. Range:
<old>..<new> (read the diff and the files it touches). View: <view
and its "looks for" text>.
Rules: do not read agent memory or handoff files; question every
decision in the range. Change no file; run no git command that
changes state; contact no host; run no deploy. Report each finding
with file:line, severity (breaks / endangers / simplifies / nit) and
how to reproduce or what to delete. If you find nothing that
matters, answer "clean".
```
