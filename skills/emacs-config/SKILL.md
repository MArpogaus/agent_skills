---
name: emacs-config
description: >
  Conventions and architecture of the user's literate Emacs
  configuration (MArpogaus/emacs.d): the org-only editing workflow,
  naming schemes, package idioms, header-line buttons, the features
  that became packages, the hand-off of a fix through elpaca, and the
  repo's git flow. Use in the `<user home>/.emacs.d` repository or
  when editing emacs.org.
license: MIT
compatibility: claude-code opencode
metadata: {stack: emacs, requires: [dev-conventions, emacs-package, git-conventions]}
---

# Skill: Emacs Config (MArpogaus/emacs.d)

## Hard rules

- **`emacs.org` is the single source of truth.** `lisp/*.el`, `init.el`
  and `early-init.el` are tangled artifacts: never edit them. Tangle
  only when the user asks for it ("retangle", "you may tangle").
  Otherwise the user tangles.
- **No test files.** Do not create `test/` or ERT suites.
- **Check what you can, ask for the rest.** An Emacs in the sandbox can
  byte-compile a tangled block and run batch probes. A claim about
  redisplay needs a real frame (`<test rig>/rig gui`). Where neither is
  available, validate with a paren and string balance script (mind `?\(`
  char literals, strings, comments). Then ask the user to eval and
  report. Debug through targeted questions (`C-h f`, `*Messages*`, `M-:`
  probes), one hypothesis at a time.
- **Reproduce in the rig with the user's configuration** before you
  claim a fix. `<test rig>` is a conda env with Emacs 31 and a copy of
  the user's tangled config and elpaca. Its `README.md` explains the
  commands. Run `<test rig>/rig sync` first, and check that the rig
  loads the same package versions as
  `<user home>/.emacs.d/elpaca/sources`.
- Org blocks can be evaluated with `:lexical no`. Avoid closures that
  capture locals. Pass arguments through `run-with-timer`,
  `apply-partially`, or global or buffer-local state.

## Repo layout and style

- Literate config, `#+PROPERTY: header-args :mkdirp yes :comments org`.
  Each `***` section sets `:header-args+: :tangle lisp/my-<name>.el`.
  `README.org` is a symlink to `emacs.org`.
- Package manager: elpaca and use-package. Style: `:preface` for defuns,
  defvars and defaces, then `:custom`, `:bind`, `:hook`, `:config`.
  Built-ins get `:ensure nil`. Do not add `:ensure t`. Generic config
  lives in `(use-package emacs :ensure nil ...)` blocks.
- Loading: every package loads through its own `use-package` block. No
  `use-package` inside another form, and never a `require` or another
  loading path as a fallback. Global modes start with
  `:hook (elpaca-after-init . foo-mode)`. Use `with-eval-after-load`
  only for code that needs a package that is not loaded yet. A window
  rule stays in the `auto-side-windows` block. A hook that needs a depth
  keeps `add-hook` in `:init`.
- Naming: commands and helpers `my/...` (internals `my/foo--bar`), faces
  `my/...-face`.
- Modal editing is **meow**. Normal state shadows plain single-key
  bindings in mode maps, so never define speed keys. Use modified keys
  (the `<return>` family, `C-<up>/<down>`) and repeat-maps under the
  leader (`my/leader-map`, for example `SPC j` →
  `my/code-cells-repeat-map`), as in `my/debug-map`. Do not add `C-c`
  prefix bindings.
- Side windows come from the user's `auto-side-windows` package:
  buffer-name and mode lists per side. The window parameter
  `header-line-format` drives the custom header
  (`my/header-line-format-top`).
- `define-minor-mode`: a body that starts with a non-keyword form loses
  that form as the deprecated positional INIT-VALUE. Keep a `:lighter`
  (or another keyword) before the body.

Display engine rules (overlays, display properties, scrolling): read
`emacs-package` [reference.md](../emacs-package/reference.md) before you
change rendering code.

## Features that became packages

These features live in their own repositories, each with README, tests
and CI (see the `emacs-package` skill):

| Package | What the configuration keeps |
|---|---|
| `pycell` | inline results for `# %%` cells; the config sets the hook and the interpreter |
| `auto-side-windows` | which buffers go to which side |
| `auto-tab-groups` | which commands open a tab group |
| `window-box` | a box around the windows the config chooses |

Keep one copy of the code. The org block is a `use-package` block that
configures the package and holds no implementation. Personal settings
stay in the configuration: keybindings, window placement, options for
this setup.

Work on each package in `<user home>/.emacs.d/packages/<name>`, the
user's checkout. Make no other clone.

## Git flow

- Branches, merges and commit messages follow `git-conventions`.
- Agent work commits contain **emacs.org only**, except the
  `chore: tangle` commit.
- Tangled files go into a separate `chore: tangle` commit. When the user
  allowed tangling, the agent makes this commit. Otherwise the user
  does.
- To split mixed changes, build intermediate `emacs.org` states by
  splicing org subtrees (headline to next `*** `) between the committed
  and the working version. Commit each state.

## Hand a fix to the user for testing

Do this only when the user says "sync elpaca" or "delete builds", or
asks to test the fix in the running Emacs. It is the one exception to
the rule never to touch the user's environment (`dev-conventions`, "Hard
rules"). The running Emacs loads packages from
`<user home>/.emacs.d/elpaca`. The elpaca source clone does not have the
work commit. For each changed package:

1. Commit the fix on the package's `dev` branch.
2. Set `src=<user home>/.emacs.d/elpaca/sources/<pkg>`. Run
   `git -C "$src" status --short`. If it shows uncommitted edits, stop
   and ask the user.
3. Fetch and check out the fix:

   ```bash
   src=<user home>/.emacs.d/elpaca/sources/<pkg>
   git -C "$src" fetch <user home>/.emacs.d/packages/<pkg> dev
   git -C "$src" checkout FETCH_HEAD
   ```

4. Delete `<user home>/.emacs.d/elpaca/builds/<pkg>` and the package's
   files in `<user home>/.emacs.d/eln-cache`, so that elpaca rebuilds
   it.
5. If the configuration changed too and the user allowed it, tangle.
6. Tell the user what to restart and what to look for.

## Debugging etiquette

- The user tests interactively and reports in short messages. Give exact
  probes and expected outputs.
- Tune UI alignment by trial: change one value per iteration and say
  which number to change in which direction.

---

## Required skills

This skill assumes the following prerequisite skills are loaded. Use the
`skill` tool to load them before using this one:

- **dev-conventions**: design principles, verification, review loop,
  code and documentation style.
- **emacs-package**: display engine rules and the conventions of the
  packages the configuration uses.
- **git-conventions**: two-branch flow, conventional commits, pre-commit
  hooks, push and attribution rules, tagging and releases.
