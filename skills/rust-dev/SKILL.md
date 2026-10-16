---
name: rust-dev
description: >
  Rust project conventions: toolchain in the agent's home, the cargo
  check pipeline (fmt, clippy with -D warnings, test, deny, all
  --locked), workspace layout with crates/ and plugins/, MkDocs docs
  with decision records and a roadmap.  Use when building, changing or
  reviewing a Rust project of the user.
license: MIT
compatibility: claude-code opencode
metadata:
  requires:
    - dev-conventions
    - git-conventions
  stack: rust
---

## When to use

Load this skill before you build, change or review a Rust project of
the user.  The design principles are in `dev-conventions`: the
simplest thing that works, no reinvention.

## Toolchain and environment

- Install the toolchain in the agent's home, never in the user's
  environment.  Use a micromamba or conda env (conda-forge `rust`),
  or nix.
- Install the native build dependencies (`pkg-config`, C compiler,
  system libraries) into the same env.
- Run cargo through the env, for example
  `micromamba run -n <env> cargo build --workspace --locked`.
- Set `CARGO_HOME` to the agent's home.
- When the repository has `rust-toolchain.toml`, use that version.
  A newer clippy can add lints that CI does not have yet.
- The user runs the debug build from the repository's `target/`, for
  example `target/debug/<bin>`.  Build the binary the user runs into
  that directory.  A build in a separate `CARGO_TARGET_DIR` leaves the
  user on a stale binary.

## Check pipeline

Run the checks for each crate you change before you commit:

```
cargo fmt --all -- --check
cargo clippy -p <crate> --all-targets --locked -- -D warnings
cargo test -p <crate> --locked
```

- Always pass `--locked`.  `Cargo.lock` is committed.
- Before a push, run the workspace form:
  `cargo clippy --workspace --all-targets -- -D warnings`,
  `cargo test --workspace`, `cargo deny check`.
- Pre-commit runs `cargo-fmt` and `cargo-clippy` hooks.  These hooks
  need `cargo` on `PATH`, so run pre-commit inside the toolchain env.
- Workspace lints live in `Cargo.toml`: clippy `pedantic`,
  `cognitive_complexity`, `excessive_nesting`, and `unsafe_code`
  denied.  `clippy.toml` sets the limits.
- `deny.toml` lists the allowed licenses and checks advisories.
- CI runs clippy and tests with `--locked` in a container of the
  target distribution, and `cargo deny` in a separate job.

## Workspace layout

```
crates/<core-model>/   data model and API types; no heavy dependencies
crates/<binary>/       the program
crates/<name>ctl/      CLI over the IPC socket
plugins/<plugin>/      reference plugins as workspace members
docs/  mkdocs.yml      MkDocs site
clippy.toml  deny.toml  Cargo.toml (workspace, lints)
```

- Use one workspace with as few crates as possible.  A module moves
  into its own crate only when a second consumer needs it.
- Keep the data model in a crate without the heavy runtime
  dependencies, so its tests need no GPU and no compositor.
- Reference plugins live in the repository as workspace members, so
  they keep the API honest.

## Documentation and decisions

- The docs are a MkDocs site in `docs/`.
- `docs/decisions.md` holds numbered decision records (`D1`, `D2`,
  ...).  The roadmap and the other docs refer to decisions by number.
- `docs/ideas.md` is the backlog.  An idea moves to the decisions or
  leaves the list.
- `docs/roadmap.md` has milestones.  Each milestone has a goal, a
  scope and an exit criterion.  A milestone is done when its exit
  criterion holds.
- Before you file an issue or plan a feature, read the roadmap.  Do
  not report what it already plans.
- Commitizen writes the changelog.  Dependabot updates Cargo
  dependencies.

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging/releases.
