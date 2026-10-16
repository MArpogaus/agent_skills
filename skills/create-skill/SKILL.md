---
name: create-skill
description: >
  Create or change an agent skill (skills/<name>/SKILL.md) in this
  collection: determine requirements, domain, workflows and conventions,
  write the SKILL.md, check it against the user's rules, and register
  it. Use when the user asks to add, write, scaffold or change a skill,
  or when a session proposes a skill change from its lessons.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: meta
  requires: []
---

# Skill: Create a New Agent Skill

This skill creates a skill: a reusable SKILL.md that agents load on
demand. The result is generic, except a skill for one named workspace
(for example the agenda or one config repo), which names its paths. It
contains all the specifics that the domain needs.

## Working directory

All skills live in `<repo>/skills/<name>/SKILL.md`. Both harnesses
read the checkout in place. Edit the files in the checkout. There is
nothing to copy or sync.

## Procedure

### 1. Determine skill name

Use the question tool (Claude Code: `AskUserQuestion`) to ask the user
for the name. The name:

- has 1 to 64 characters,
- matches the regex `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase
  alphanumeric words joined by single hyphens).

If the name does not match, ask again.

### 2. Determine description

Ask the user for a description of 1 to 1024 characters. It tells an
agent whether to load the skill. It ends with a trigger sentence: "Use
when ...", which names the files, commands or user words that load it.
Examples:

- "Linting, formatting, and type-checking Python projects with ruff and
  mypy. Use when a repo has a `pyproject.toml`."
- "Commit messages that follow conventional commits. Use before any
  commit."

### 3. Gather domain information

Ask the user structured questions about the scope. Collect at least:

| Question | Purpose |
|----------|---------|
| What task or domain does this skill cover? | Scope |
| What tools and runtimes are involved? | For example Python, Docker, LaTeX |
| What workflows or step sequences are needed? | Ordered procedure |
| What conventions, style rules or config files exist? | Precision rules |
| What commands does the skill document? | Verification commands |
| What are the key references (docs, standards, repos)? | Sources of truth |

### 4. Set frontmatter

Set these without asking the user:

- `license: MIT`
- `compatibility`: a space-separated list of the harnesses where you
  loaded and used the skill (`claude-code`, `opencode`). Do not list a
  harness speculatively.
- `metadata.stack`: space-separated words for the domain (`python`,
  `org-mode latex beamer`, `meta`).
- `metadata.requires`: the skills this one depends on, as a flow list
  (`requires: [git-conventions, python-dev]`), or `[]`.

### 5. Generate the skill

Create `skills/<name>/SKILL.md` with:

- the YAML frontmatter from steps 1 to 4,
- the H1 `# Skill: <Title>`,
- clear sections (phases, steps, conventions, references),
- placeholders such as `<project>`, `<package>` or `<your-org>` instead
  of paths, project names or environment details (the workspace
  exception is in the introduction),
- code examples that use the agent's tools (Read, Edit, Write, Bash),
- a **Required skills** section at the end when `metadata.requires` is
  not empty. It tells the agent to load each listed skill with the
  skill tool (Claude Code: `Skill`). Copy the format from
  `git-conventions`.

### 6. Size and shape

A skill competes for the agent's attention with every other loaded
skill. The agent skims a long skill and breaks its rules.

- **Budget:** at most about 1,500 words in `SKILL.md`. Rare detail
  (pitfall lists, long config files, arithmetic) goes into one
  `reference.md` beside it, or a `reference/` folder when there are
  several files. One line in `SKILL.md` says when to read it.
- **Hard rules first.** Put the rules that the agent breaks most at the
  top, as short imperative bullets.
- **Only what tools do not enforce.** Do not restate what a linter,
  formatter or pre-commit hook already checks.
- **State what is.** No history, no incident stories.
- **Grow by replacing.** When the user corrects the same thing twice,
  add the rule, and look for a rule it makes redundant.

### 7. File structure

Each skill lives in its own directory. The directory name matches the
`name` field.

```
skills/<name>/
├── SKILL.md
└── reference.md        optional
```

Supporting files (templates, helper scripts) can sit beside it, for
example in `templates/` or `tools/`. Say in SKILL.md that their paths
are relative to the skill directory.

### 8. Review against the user's rules

Do this step (the Coverage view) when you create or change a skill
from session experience:

1. Read the user's messages of the sessions that led to the change.
2. Read the memory notes that touch the skill's domain.
3. Check that the skill holds each rule that the user stated. Add the
   rules that are missing. Remove the rules that the user withdrew.

### 9. Verification

After writing, verify:

- [ ] Frontmatter is valid YAML and includes `name` and `description`
- [ ] `name` matches the regex `^[a-z0-9]+(-[a-z0-9]+)*$`
- [ ] `description` has 1 to 1024 characters and ends with a trigger
      sentence
- [ ] No private or environment detail is hardcoded, except the paths
      of a workspace skill
- [ ] The skill uses the patterns of nearby skills
- [ ] The file is named `SKILL.md` (all caps)
- [ ] `SKILL.md` keeps to the size budget, hard rules first
- [ ] If `metadata.requires` is not empty, a **Required skills**
      section at the end tells the agent to load each listed skill

### 10. Register in repo

After you create the skill file:

- [ ] Add the skill to the table in `README.org`
- [ ] Check that the descriptions in `.claude-plugin/plugin.json` and
      `.claude-plugin/marketplace.json` still cover the collection
- [ ] Check that the skill loads: in Claude Code,
      `claude plugin details marpogaus-skills@marpogaus-skills`
      lists it
- [ ] `git add` the new skill directory and the changed files
- [ ] Commit with the message `feat: add <name> skill definition`
