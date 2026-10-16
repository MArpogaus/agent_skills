---
name: rust-dev
description: >
  Rust project conventions: toolchain in the agent's home, the cargo
  check pipeline (fmt, clippy with -D warnings, test, deny, all
  --locked), workspace layout, MkDocs docs with decision records and a
  roadmap. Use in any repo with `Cargo.toml`, before cargo, clippy or
  Rust edits.
license: MIT
compatibility: claude-code opencode
metadata: {stack: rust, requires: [dev-conventions, git-conventions]}
---

# Skill: Rust Development

## Toolchain and environment

- Install the toolchain and the native build dependencies (`pkg-config`,
  C compiler, system libraries) in the agent's home, never in the user's
  environment. The `sandbox-env` skill owns how.
- Run cargo through that env, for example
  `micromamba run -n <env> cargo build --workspace --locked`.
- Only rustup reads `rust-toolchain.toml`. With conda-forge or nix,
  install that version explicitly (`rust=<ver>`), or use rustup in the
  agent's home. A newer clippy can add lints that CI does not have yet.
- The user runs the debug build from the repository's `target/`, for
  example `target/debug/<bin>`. Build the binary the user runs into that
  directory. A build in a separate `CARGO_TARGET_DIR` leaves the user on
  a stale binary.

## Check pipeline

Run the checks for each crate you change before you commit:

```
cargo fmt --all -- --check
cargo clippy -p <crate> --all-targets --locked -- -D warnings
cargo test -p <crate> --locked
```

- Always pass `--locked`. `Cargo.lock` is committed.
- Before a push, run the workspace form:
  `cargo clippy --workspace --all-targets --locked -- -D warnings`,
  `cargo test --workspace --locked`, `cargo deny check`.
- Pre-commit runs `cargo-fmt` and `cargo-clippy` hooks. These hooks need
  `cargo` on `PATH`, so run pre-commit inside the toolchain env.
- Workspace lints live in `Cargo.toml`: the rustc lint `unsafe_code`
  denied, and the clippy lints `pedantic`, `cognitive_complexity` and
  `excessive_nesting`. `clippy.toml` sets the limits.
- `deny.toml` lists the allowed licenses and checks advisories.
- CI runs clippy and tests with `--locked` in a container of the target
  distribution, and `cargo deny` in a separate job.
- `.github/dependabot.yml` adds the `cargo` ecosystem (git-conventions,
  "Dependabot").

## Workspace layout

- Use one workspace with as few crates as possible.
- A module becomes its own crate only when a second consumer needs it.
- Keep the data model in a core crate without heavy dependencies, so
  that its tests need no runtime (no GPU, no external services).
- `clippy.toml`, `deny.toml` and the workspace `Cargo.toml` with the
  lints live at the root.

Example layout:

```
crates/<core-model>/   data model and API types; no heavy dependencies
crates/<binary>/       the program
crates/<cli>/          command-line client
<extension>/           reference extension, a workspace member
docs/  mkdocs.yml      MkDocs site
```

## Documentation and decisions

- The docs are a MkDocs site in `docs/`.
- `docs/decisions.md` holds numbered decision records (`D1`, `D2`, ...).
  The roadmap and the other docs refer to decisions by number.
- A project can keep `docs/ideas.md` as design notes.
- `docs/roadmap.md` has milestones. Each milestone has a goal, a scope
  and an exit criterion. A milestone is done when its exit criterion
  holds.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review loop,
  code and documentation style.
- **git-conventions**: two-branch flow, conventional commits, pre-commit
  hooks, tagging and releases.
