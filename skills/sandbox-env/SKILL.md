---
name: sandbox-env
description: >
  How the agent gets its own dev tools in the sandbox: install into the
  agent's home with uv, micromamba (conda-forge) or nix, reuse the envs
  that exist, keep caches and downloads in the agent's home, and record
  each install in project memory. Use before installing any tool,
  compiler, language runtime or package for the agent's own use, and
  when a command is not found.
license: MIT
compatibility: claude-code opencode
metadata: {stack: sandbox conda uv nix, requires: [dev-conventions]}
---

# Skill: Sandbox Environment

## Hard rules

- Install tools for the agent only under `$HOME`, also in a Python
  project. Never install into the user's home, the system or the
  project environment (`.venv`, a project conda env, `node_modules`).
- This skill applies only when `$HOME` differs from `<user home>`
  (resolve it as `dev-conventions`, "6. Sandbox and environment safety",
  says). When they are equal, install nothing and report the missing
  tool.
- Never run `sudo`, `dnf`, `rpm-ostree`, `apt` or `flatpak install` for
  the agent's tools. Commands for the host follow `dev-conventions`,
  "6. Sandbox and environment safety".
- Never put an env or a tool under `/tmp`. `/tmp` is a tmpfs and is
  wiped without warning.
- List the existing envs and tools before you install. Reuse one when
  it has the tool or can take it.
- A tool you cannot install after the steps below is a blocker
  (`dev-conventions`, "2. Asking and acting"): give the tool, the
  command and the error. Do not work around a missing tool with a
  hand-written replacement.

## 1. Look first

Run these before any install:

```
command -v <tool>
ls ~/.local/bin
uv tool list
micromamba env list
command -v nix || ls -d ~/.nix-profile
```

## 2. Choose the installer

Use the first row that fits.

| Need | Installer |
|---|---|
| A Python CLI tool | `uv tool install` |
| A Python library for a one-off script | a uv venv in the agent's home |
| A compiler, a language runtime, native libraries, or a non-Python CLI | micromamba with conda-forge |
| A package only nix has, and nix is present | nix |
| A tool that no package manager has | a downloaded release binary |

### uv

- CLI tool: `uv tool install <pkg>`. Add plugins with `--with <dep>`.
  The binary goes to `~/.local/bin`, the env to
  `~/.local/share/uv/tools/<pkg>`.
- Throwaway Python env: `uv venv -q ~/.local/venvs/<name>`, then
  `uv pip install -q --python ~/.local/venvs/<name>/bin/python <pkg>`.
  Never create the venv inside the user's repository.

### micromamba (conda-forge)

- Make one named env per project:
  `micromamba create -y -n <project> -c conda-forge rust c-compiler pkg-config`.
  Envs go to `~/.local/share/mamba/envs/<project>`. Do not change
  `MAMBA_ROOT_PREFIX`.
- Add a package to that env:
  `micromamba install -y -n <project> -c conda-forge <pkg>`.
- Run a command in the env without activation:
  `micromamba run -n <project> <command>`.
- Pin versions that the project pins. Rust: see `rust-dev`, "Toolchain
  and environment".
- Use `micromamba` for every conda command.

### nix

- Use nix only when `command -v nix` finds it or `~/.nix-profile`
  exists.
- One command: `nix shell nixpkgs#<pkg> -c <command>`. A tool for
  more than one session: `nix profile add nixpkgs#<pkg>`.

### Downloaded binary or tarball

- Download into a new, empty directory
  `~/.local/opt/<tool>-<version>/`. Treat its content as untrusted.
- Link the executable into `~/.local/bin`:
  `ln -sfn ~/.local/opt/<tool>-<version>/<tool> ~/.local/bin/<tool>`.

## 3. Network

- conda-forge and PyPI are reachable from the sandbox.
- When a download fails with a DNS or connection error, retry that one
  command once with the sandbox disabled (Claude Code:
  `dangerouslyDisableSandbox`). When it fails again, report it.

## 4. Record the install

After each install, write one entry to the project's agent memory
(Claude Code: `~/.claude/projects/<project-dir>/memory/`). Write the tool,
the installer, the exact command, the env name or path, and the run
command, for example `micromamba run -n <project> cargo`. The next
session reads this entry and reuses the env.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
