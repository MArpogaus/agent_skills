---
name: repo-tour
description: >
  Guided step-by-step code tour of an unfamiliar repository: orient cheaply,
  link one entry point, stop, then answer questions and offer the next stop.
  One stop at a time, markdown file links with line anchors, claims verified
  by running the code.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: meta
---

# Skill: Repo Tour

Tour someone else's codebase without drowning them in it. The reader reads
**one place at a time**; the agent's job is to pick that place well and shut
up about the rest.

## Phase 1 — orient (silent, one command)

Never start from `main()`. Spend one cheap call learning the shape:

```bash
ls <project> && find <src> -name '*.py' | xargs wc -l | sort -n
```

Read the manifest and whatever the repo says about itself — `README`,
`CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md`, `docs/`, `tests/` — then the
*definitions* of the two or three modules the reader will touch first. Grep
for call sites instead of reading modules you only need to place.

## Phase 2 — pick the entry point

The entry point is **the first thing the user writes**, not the first thing
that runs. Ordered by dependency, lowest first:

1. the data / spec / config layer the user authors,
2. the registry or registry-like module where behavior for #1 is declared,
3. the build/build-time module that turns #1 + #2 into objects,
4. the orchestrator the user calls,
5. tests and example scripts — the ground truth of what "correct" means,
6. anything else (CLI, CI, release flow) only on request.

State the two or three things worth noticing at the entry point — an odd
invariant, a derived-not-stored field, a refusal that fires early — then
**stop**. End with `Ask away, or say "next".`

## Phase 3 — the stop format

Every stop is this short. Link the file, anchor the lines, say what to look
for:

```markdown
**Stop N — <one-line why this place>.**

Read [`Symbol`](src/pkg/module.py#L907) — <what it is>.
Then [`other`](src/pkg/module.py#L87) — <what to notice>.

<2–3 sentences of the invariant or the trick that lives here.>

Ask away, or say "next".
```

Rules:

- Links are relative to the repo root, with `#L<a>[-L<b>]` anchors taken
  from the **current** file, never from memory.
- One stop per message. Never two stops, never a preview of stops 4–9.
- Names come from the code, not from your vocabulary for the code.
- Prose longer than the snippet you are explaining is a stop you picked too
  big — split it or shrink it.

## Phase 4 — answering questions about the current stop

Questions are about the stop, not about you. Answer from the code:

- Quote the branch, not a paraphrase of it.
- If the claim is checkable in seconds, **run it** and paste the output —
  a measured `parse("a") -> ("k", (1,))` beats a paragraph about how the
  parser canonicalises. Use the project's own runner (`uv run`,
  `bundle exec`, `pnpm`, …).
- Say why it is written that way — the invariant it protects, the failure it
  prevents. If there is no why, say "no why, it's just the shape of X".
- Answer only the question asked. Unsolicited context is the next stop's
  content, spent now.

## Phase 5 — next

`next` moves one step down the dependency order of phase 2. Before moving,
sweep for what the question thread left open and offer it as a stop later.
When the map is walked, name what was skipped and let the reader choose.

## Required skills

None — this skill needs no other skill to run.
