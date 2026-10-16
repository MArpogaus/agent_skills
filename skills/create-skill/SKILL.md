---
name: create-skill
description: >
  Create or change an agent skill (skills/<name>/SKILL.md) in this
  collection: determine requirements, domain, workflows and conventions,
  write the SKILL.md, check it against the user's rules, and register
  it. Use when the user asks to add, write, scaffold or change a skill,
  or to apply a skill change that the user agreed to.
license: MIT
compatibility: claude-code opencode
metadata: {stack: meta, requires: [dev-conventions]}
---

# Skill: Create a New Agent Skill

This skill creates a skill: a reusable SKILL.md that agents load on
demand. The result is generic and contains all the specifics that the
domain needs. For a change to an existing skill, edit the file in
place, then do steps 6, 8 and 9. Update its `README.org` row when its
scope changed.

## Hard rules

- The description ends with a trigger sentence that starts with "Use
  when", "Use in" or "Use before". It names the files, commands or user
  words that load the skill.
- `SKILL.md` has at most 1,500 words (`wc -w`); `dev-conventions` is
  exempt. Rare detail (pitfall lists,
  long config files, arithmetic) goes into one `reference.md` beside
  it, or a `reference/` folder when there are several files. One line
  in `SKILL.md` says when to read it.
- Every `SKILL.md` over 600 words has `## Hard rules` as its first H2:
  5 to 10 short imperative bullets with the rules that the agent breaks
  most. The sections below do not restate them.
- Write only what tools do not enforce. Do not restate what a linter,
  formatter or pre-commit hook already checks.
- Do not restate a rule that another skill owns. Point to it by skill
  name and section heading, and check that the heading exists.
- State what is. No history, no incident stories.
- The repo is public. No private paths, hosts, names or project names:
  use the workspace placeholders of `dev-conventions` section 6.

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
agent whether to load the skill. Put routing sentences before the
trigger sentence. Examples:

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

Set these without asking the user. Write `metadata` in flow style:

```yaml
name: <name>
description: >
  <description>
license: MIT
compatibility: claude-code opencode
metadata: {stack: <words>, requires: [<skill>, ...]}
```

- `license: MIT`
- `compatibility`: a space-separated list of harnesses (`claude-code`,
  `opencode`). Start with the harness of this session; add another only
  after the skill loaded there.
- `metadata.stack`: space-separated words for the domain (`python`,
  `org-mode latex beamer`, `meta`).
- `metadata.requires`: the skills this one depends on, as a flow list
  (`requires: [git-conventions, python-dev]`), or `[]`.
- `metadata.audience` (optional): the readers of the output, for
  example `researchers`. Set it only when the skill writes for a fixed
  audience.

### 5. Generate the skill

Create `skills/<name>/SKILL.md` with:

- the YAML frontmatter from steps 1 to 4,
- the H1 `# Skill: <Title>`,
- clear sections (phases, steps, conventions, references),
- placeholders such as `<project>`, `<package>` or `<your-org>` instead
  of paths, project names or environment details,
- code examples that use the agent's tools (Claude Code: Read, Edit,
  Write, Bash),
- a **Required skills** section at the end when `metadata.requires` is
  not empty, after a `---` line. It tells the agent to load each listed
  skill with the skill tool (Claude Code: `Skill`). Copy the format
  from `python-dev`.

### 6. Grow by replacing

A skill competes for the agent's attention with every other loaded
skill. The agent skims a long skill and breaks its rules. When the
user corrects the same thing twice, add the rule, and look for a rule
that it makes redundant.

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

Do this step when you create or change a skill from session
experience. Run the Coverage view (`dev-conventions`, "4.3 Reviewers")
on the change:

1. Read the user's messages of the sessions that led to the change.
2. Read the memory notes that touch the skill's domain.
3. Check that the skill holds each rule that the user stated. Add the
   rules that are missing. Remove the rules that the user withdrew.

### 9. Verification

After writing, check that the hard rules and steps 1 to 5 hold:

- `wc -w skills/<name>/SKILL.md` prints at most 1,500.
- Over 600 words, `grep -n '^## ' skills/<name>/SKILL.md` lists
  `## Hard rules` first.
- The frontmatter has `name` (equal to the directory name),
  `description` (ending with the trigger sentence), `license: MIT`,
  `compatibility` and `metadata` with `stack` and `requires`.
- `grep -n '^# Skill: ' skills/<name>/SKILL.md` finds the H1.
- Each skill in `requires` has a line in the **Required skills**
  section. When the text cites `dev-conventions`, it is in
  `requires`.

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

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: workspace placeholders, the Coverage review
  view, and documentation style.
