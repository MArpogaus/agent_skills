---
name: emacs-config
description: >
  Conventions and architecture knowledge for the user's literate Emacs
  configuration (MArpogaus/emacs.d): org-only editing workflow, naming
  schemes, package idioms, the my/pycell notebook layer, header-line
  buttons, display-property rendering lore, and the repo's git flow.
  Use when working in that configuration repository.
license: MIT
compatibility: claude-code opencode
metadata:
  requires: [git-conventions]
  stack: emacs
---

# Skill: Emacs Config (MArpogaus/emacs.d)

## Cardinal rules

- **`emacs.org` is the single source of truth.**  `lisp/*.el`,
  `init.el` and `early-init.el` are tangled artifacts: never edit
  them.  Tangle only when the user asks for it ("retangle", "you may
  tangle").  Otherwise the user tangles.
- **No test files.**  Do not create `test/` or ERT suites.
- **Check what you can, ask for the rest.**  An Emacs in the sandbox
  can byte-compile a tangled block and run batch probes; a claim about
  redisplay needs a real frame (see the `emacs-package` skill for the
  Xvfb recipe).  Where neither is available, validate with a
  paren/string-balance script (mind `?\(` char literals, strings,
  comments) and ask the user to eval and report; debug through targeted
  questions (`C-h f`, `*Messages*`, `M-:` probes), one hypothesis at a
  time.
- **Reproduce in the rig with the user's configuration** before you
  claim a fix (`<test rig>`; see `emacs-package`).  Check that the rig loads
  the same package versions as `~/.emacs.d/elpaca/sources`.
- Org blocks may be evaluated with `:lexical no` — avoid closures
  that capture locals; pass args through `run-with-timer`,
  `apply-partially`, or global/buffer-local state instead.

## Repo layout & style

- Literate config, `#+PROPERTY: header-args :mkdirp yes :comments org`;
  each `***` section sets `:header-args+: :tangle lisp/my-<name>.el`.
  `README.org` is a symlink to `emacs.org`.
- Package manager: elpaca + use-package.  Style: `:preface` for
  defuns/defvars/defaces, `:custom`, `:bind`, `:hook`, `:config`.
  Built-ins get `:ensure nil`; do not add `:ensure t`.
  Generic config lives in `(use-package emacs :ensure nil ...)` blocks.
- Loading: every package loads through its own `use-package` block.
  No `use-package` wrapped in another form, and never a `require` or
  another loading path as a fallback.  Global modes start with
  `:hook (elpaca-after-init . foo-mode)`.  Use `with-eval-after-load`
  only for code that needs a package that is not yet loaded.  A
  window rule stays in the `auto-side-windows` block.
- Naming: commands/helpers `my/...` (internals `my/foo--bar`),
  faces `my/...-face`.
- Modal editing is **meow**; plain single-key bindings in mode maps
  are shadowed by normal state — never define speed keys.  Preferred:
  modified keys (the `<return>` family, `C-<up>/<down>`) plus
  repeat-maps hung off the leader (`my/leader-map`, e.g.
  `SPC j` → `my/code-cells-repeat-map`), pattern as in `my/debug-map`.
  The user dislikes `C-c` prefix bindings.
- Side windows via the user's own `auto-side-windows` package; per-side
  buffer-name/mode lists, window parameter `header-line-format`
  drives the custom header (`my/header-line-format-top`).
- `define-minor-mode` gotcha: if the body starts with a non-keyword
  form, it is eaten as the deprecated positional INIT-VALUE — keep a
  `:lighter` (or another keyword) before the body.

## Display-property rendering lore

Lives in the `emacs-package` skill, under "Display engine rules for
overlay-heavy UIs".  It was learned here and applies to both, so it is
written down once.  The two facts this configuration leans on most:
a `display` property on real buffer text scrolls smoothly where a tall
overlay string jumps, and display specs do not nest, so anything with
images or `(space :align-to ...)` inside has to ride an overlay string.

## Features that grew into packages

Four of them left `emacs.org` and now live on their own, each with its
own README, test suite and CI (see the `emacs-package` skill):

| Package | What the configuration keeps |
|---|---|
| `pycell` | inline results for `# %%` cells; the config sets the hook and the interpreter |
| `auto-side-windows` | which buffers go to which side |
| `auto-tab-groups` | which commands open a tab group |
| `window-box` | a box around the windows the config chooses |

The rule after an extraction is one copy of the code: the org block
becomes a `use-package` block that configures the package, and the
implementation is not carried along.  What stays personal stays in the
configuration — keybindings, window placement, options set for this
setup.

## Git flow (see git-conventions skill)

- Branches: `main` (full old history; a documented exception to
  `git-conventions`, adopted going forward) and `dev` (work).
  Commits go to `dev`; merges to `main` are fast-forward, done when
  stable and after a `chore: tangle` commit brings `lisp/*.el`
  current.  Never rewrite pushed history.
- Conventional commits, one concern each.  Agent commits contain
  **emacs.org only**.  Tangled files are committed in the `chore:
  tangle` commit.
- Splitting mixed changes: reconstruct intermediate `emacs.org`
  states by splicing org subtrees (headline → next `**** `) between
  the committed and working versions, commit each state.

## Hand a fix to the user for testing

The user tests in the running Emacs, which loads packages from
`~/.emacs.d/elpaca`.  "Sync elpaca" means, for each changed package:

1. Commit the fix on the package's `dev` branch.
2. Check out that commit in `~/.emacs.d/elpaca/sources/<pkg>`.
   Look for uncommitted edits there first.
3. Delete `~/.emacs.d/elpaca/builds/<pkg>` and the package's files
   in `~/.emacs.d/eln-cache`, so that elpaca rebuilds it.
4. If the configuration changed too and the user allowed it, tangle.
5. Tell the user what to restart and what to look for.

## Debugging etiquette

- The user tests interactively and reports in short German messages.
  Give precise probes and expected outputs, one hypothesis at a time.
- UI alignment is tuned empirically: change one knob per iteration
  and say which number to tweak in which direction.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions** — two-branch flow, conventional commits,
  pre-commit hooks, push and attribution rules, tagging and releases.
