---
name: create-skill
description: >
  Create a new agent skill (skills/<name>/SKILL.md) in this collection:
  determine requirements, domain, workflows and conventions, write the
  SKILL.md, and register it.  Use when the user asks to add, write or
  scaffold a skill.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: meta
---

# Skill: Create a New Agent Skill

This skill guides you through creating a new skill — a reusable
SKILL.md that agents can load on demand. The result must be
generic (no private/project/env-specific details) yet contain
all necessary specifics for the domain.

## Working directory

All skills live in `<repo>/skills/<name>/SKILL.md`.  The checkout is
read in place by both harnesses, so there is nothing to copy or sync —
edit the files in the checkout.

## Procedure

### 1. Determine skill name

Use the question tool (Claude Code: `AskUserQuestion`) to ask the user
for the name. It must:
- Be 1–64 characters
- Be lowercase alphanumeric with single hyphen separators
- Not start or end with `-`
- Not contain consecutive `--`
- Match regex: `^[a-z0-9]+(-[a-z0-9]+)*$`

Validate the name against this regex. If invalid, ask again.

### 2. Determine description

Ask the user for a short description (1–1024 characters). It should
be specific enough that an agent can decide whether to load this
skill. Examples:
- "Linting, formatting, and type-checking Python projects with ruff and mypy"
- "Guide for writing commit messages following conventional commits"

### 3. Gather domain information

Ask the user structured questions about what the skill should
cover. Collect at minimum:

| Question | Purpose |
|----------|---------|
| What task or domain does this skill cover? | Scope definition |
| What tools / runtimes are involved? | e.g. Python, Node, Docker, LaTeX |
| What workflows or step sequences are needed? | Ordered procedure |
| What conventions, style rules, or config files exist? | Precision rules |
| What commands should the skill document? | CLI commands for verification |
| Any key references (docs, standards, repos)? | Sources of truth |

### 4. Set frontmatter

Set these without asking the user:

- `license: MIT`
- `compatibility`: a space-separated list of the harnesses where you
  loaded and used the skill (`claude-code`, `opencode`).  Do not list a
  harness speculatively.
- `metadata.stack`: one short word for the domain (`python`, `git`,
  `meta`, ...).

`metadata` may also hold `requires`, a list of skill names.

If the skill depends on other skills (e.g. requires git or python
conventions), add a `requires` list to metadata:

```yaml
metadata:
  requires:
    - git-conventions
    - python-dev
```

### 5. Generate the skill

Create `skills/<name>/SKILL.md` with:

- Required YAML frontmatter (`name`, `description`)
- Optional frontmatter fields
- Clear sections (phases, steps, conventions, references)
- Generic phrasing — no hardcoded paths, project names, or
  environment-specific details. Use placeholders like
  `<project>`, `<package>`, `<your-org>` where needed.
- Code blocks with examples that use the tools available to
  the agent (Read, Edit, Write, Bash, Glob, Grep, etc.)
- A **Required skills** section at the very end listing every
  skill in `metadata.requires` with an explicit instruction to
  load them via the skill tool (Claude Code: `Skill`; see examples
  in existing skills)

### 6. File structure

Each skill lives in its own directory:

```
skills/<name>/
└── SKILL.md
```

Supporting files (templates, helper scripts) may sit beside it, for
example `templates/` or `tools/`; say in SKILL.md that their paths are
relative to the skill directory.  The directory name must match the
`name` field in frontmatter.

### 7. Verification

After writing, verify:
- [ ] Frontmatter is valid YAML and includes `name` + `description`
- [ ] `name` matches the regex `^[a-z0-9]+(-[a-z0-9]+)*$`
- [ ] `description` is between 1 and 1024 characters
- [ ] No private, project-specific, or environment-specific
      information is hardcoded
- [ ] The skill uses existing patterns from nearby skills
- [ ] The file is named `SKILL.md` (all caps)
- [ ] If `metadata.requires` is non-empty, a **Required skills**
      section exists at the end of the file with explicit
      instructions to load each listed skill via the `skill` tool

### 8. Register in repo

After creating the skill file:
- [ ] Add the skill to the table in `README.org`
- [ ] Check that the descriptions in `.claude-plugin/plugin.json` and
      `.claude-plugin/marketplace.json` still cover the collection
- [ ] Check that the skill loads: in Claude Code,
      `claude plugin details marpogaus-skills@marpogaus-skills`
      lists it
- [ ] `git add` the new skill directory and any changed files
- [ ] Commit with message: `feat: add <name> skill definition`
