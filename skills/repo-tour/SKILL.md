---
name: repo-tour
description: >
  Guided step-by-step code tour of an unfamiliar repository: orient cheaply,
  link one entry point, stop, then answer questions and offer the next stop.
  One stop at a time, markdown file links with line anchors, claims verified
  by running the code. Use when the user asks for a "tour", a
  "walkthrough" or "show me around" a codebase.
license: MIT
compatibility: claude-code opencode
metadata: {stack: meta, requires: []}
---

# Skill: Repo Tour

Tour a codebase that the reader does not know. The reader reads **one place at a time**. The agent picks that place well and leaves the rest for later stops.

## Phase 1: orient (silent, one command)

Never start from `main()`. Spend one cheap call to learn the shape:

```bash
ls <project> && git -C <project> ls-files -z | xargs -0 wc -l | sort -n | tail
```

Read the manifest and what the repo says about itself: `README`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/` and the test directory (`test/` or `tests/`, as the repo has it). Then read the *definitions* of the 2 to 3 modules that the reader touches first. To place a module, grep for its call sites instead of reading it.

## Phase 2: pick the entry point

The entry point is **the first thing a user of the code writes**, not the first thing that runs. In dependency order, lowest first:

1. the data, spec or config layer that a user of the code writes,
2. the registry (or a similar module) that declares the behaviour for #1,
3. the build module that turns #1 and #2 into objects,
4. the orchestrator that a user of the code calls,
5. tests and example scripts: they define what "correct" means,
6. anything else (CLI, CI, release flow), only on request.

At the entry point, state 2 to 3 things to notice. Examples: an odd invariant, a derived field that is not stored, a refusal that fires early. Then **stop**. End with `Ask away, or say "next".`

## Phase 3: the stop format

Every stop is this short. Link the file, anchor the lines and say what to look for:

```markdown
**Stop N: <one-line reason for this place>.**

Read [`Symbol`](src/pkg/module.py#L907): <what it is>.
Then [`other`](src/pkg/module.py#L87): <what to notice>.

<2 to 3 sentences about the invariant or the trick that lives here.>

Ask away, or say "next".
```

Rules:

- Links are relative to the repo root. Take the `#L<a>[-L<b>]` anchors from the **current** file, never from memory.
- Send one stop per message. Never send two stops or a preview of later stops.
- Take names from the code, not from your own words for the code.
- If the prose is longer than the snippet it explains, the stop is too big. Split it or make it smaller.

## Phase 4: answer questions about the current stop

Answer from the code:

- Quote the branch. Do not paraphrase it.
- If a claim takes less than 10 seconds to check, **run it** and paste the output. A measured `parse("a") -> ("k", (1,))` is better than a paragraph about the parser.
- Say why the code has this form: the invariant it protects, the failure it prevents. If there is no reason, say so.
- Answer only the question. Extra context belongs to the next stop.

## Phase 5: next

`next` moves one step down the dependency order of phase 2. Before you move, find what the questions left open and offer it as a later stop. When all stops are done, name what the tour skipped and let the reader choose.
