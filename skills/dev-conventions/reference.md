# dev-conventions: reference

Read "Reviewer brief" when you spawn reviewers. Read "findings.md" for
a written review.

## Reviewer brief

For the Simplicity view, add: "A report without a concrete deletion
says for each addition why no simpler form works."

```
You are a read-only, sceptical reviewer. Repo: <path>. Range:
<old>..<new> (read the diff and the files it touches). View: <view
and its "looks for" text>.
Rules: do not read agent memory or handoff files unless your view says
so; question every decision in the range. Change no file; run no git
command that changes state; contact no host; run no deploy. Report each
finding with file:line, severity (breaks / endangers / simplifies / nit)
and how to reproduce or what to delete. Do not report rare cases
that the code does not cover: the agent asks the user on those. If you
find nothing that matters, answer "clean".
```

The brief contains no findings of yours, no session history and no
memory of yours.

## findings.md

When the user wants the review written down, write `findings.md` in
the repo root. It is a report file, not a plan that waits for approval:

- Never commit it: list it in `.git/info/exclude` (or in the repo's
  `.gitignore` if that file already ignores it).
- Use numbered sections, `file:line` on every finding, ranked by cost
  to the reader.
- Give the reproduction output for each correctness finding.
- End with a "checked and rejected" section.

Commits that fix a finding can cite it ("findings.md, section A"). When
the user says "read the findings and ask me", go through them one at a
time with the question tool.
