---
name: emacs-package
description: >
  Conventions for building, checking and publishing Emacs Lisp packages:
  repository layout, file headers, the make based check pipeline, the
  GitHub Actions matrix, ERT tests, recurring defects and the MELPA
  submission steps. Use when creating, extracting, reviewing or
  releasing an Emacs Lisp package, or when editing a repository with a
  `<package>.el` and an `emacs-package-template` layout.
license: MIT
compatibility: claude-code opencode
metadata: {stack: emacs, requires: [git-conventions]}
---

# Skill: Emacs Package

## Hard rules

- Run plain `make` (compile, checkdoc, lint, test) before every push, not a subset.
- Run every code path with `emacs -Q` defaults, not only with the author's configuration.
- Prove each new test red before you call it done.
- A package sets no user options and no key bindings. The README recommends them.
- Prefer no dependency: a built-in or a subprocess first, a soft dependency for optional features.
- After an extraction, one copy of the code exists: the configuration only configures the package.
- Keep the `;; Assisted-by:` header line (see "File headers").

Read [reference.md](reference.md) before you build or debug overlays, display properties, margins, fringes, header lines, scrolling over tall blocks, pixel tests or demo GIFs.

## Start from the template

`MArpogaus/emacs-package-template` holds the layout every package follows. Create a repository from it and rename the placeholder:

```shell
name=your-package
git mv my-package.el "$name.el"
git mv test/my-package-test.el "test/$name-test.el"
grep -rl my-package . --exclude-dir=.git | xargs sed -i "s/my-package/$name/g"
make
```

Layout, identical in every package:

```
.dir-locals.el              indentation, fill column
.elpaignore                 GNU ELPA leaves these out, package.el skips compiling them; MELPA ignores it
.github/workflows/test.yml  CI, one job per supported Emacs version
.gitignore
COPYING                     GPLv3
Makefile                    compile, checkdoc, lint, test
README.org                  Best-README-Template style, org
docs/implementation.org     mechanism, measurements, test notes
<package>.el
test/<package>-test.el
```

`.dir-locals.el` does not set `sentence-end-double-space`. Two spaces after a sentence apply only in Emacs Lisp docstrings and `;;; Commentary:` sections.

A multi-file package adds one companion per optional integration next to the main file (`<package>-<topic>.el`). Each companion needs its own header block. package-lint checks the symbol prefix against the file name: `foo-project.el` may only define `foo-project-*`.

README.org sections, in order: About The Project, Getting Started, Usage, Customization, Known Limits, Comparison with Other Packages, How It Works, Development, Contributions, License, Contact. Mechanism, measurements and test notes go to `docs/implementation.org`.

## File headers

Every file, companions and test files included:

```elisp
;;; foo.el --- One line, no trailing period -*- lexical-binding: t; -*-

;; Copyright (C) <year> <Author Name>

;; Author: <Author Name> <email>
;; Version: 0.1
;; Package-Requires: ((emacs "29.1"))
;; Keywords: convenience
;; URL: https://github.com/<owner>/foo

;; This file is not part of GNU Emacs.
;; <GPLv3 blurb, 14 lines>

;;; Commentary:
;; What it does and how to start.  This is what describe-package shows.

;;; Code:
...
(provide 'foo)
;;; foo.el ends here
```

- Keep the `;; Assisted-by:` header line. MELPA asks for it. git-conventions' no-attribution rule covers commits, tags, pull requests and issues only.
- The email can be ROT13 obfuscated. Keep the form the existing files use.
- `Package-Requires` in the main file decides what MELPA installs. Nothing installs a companion's requirements, so a companion that needs a newer Emacs forces the main file up too.
- `Keywords` contains at least one word from `finder-known-keywords` (`convenience`, `tools`, `languages`).
- Put autoload cookies on entry points only: interactive commands, minor modes, hook functions in an autoloaded `add-hook`, and variables users set before loading.

## The check pipeline

`make` runs the same four steps as CI. It bootstraps its tools into `.sandbox/`, so a fresh checkout needs only Emacs:

| Target | What it enforces |
|---|---|
| `compile` | byte-compile with `byte-compile-error-on-warn t` |
| `checkdoc` | any output fails the target |
| `lint` | `package-lint`, the rules MELPA applies |
| `test` | ERT suite in `test/` |

- Put Elisp programs into make variables, not into recipe lines. Inside a quoted recipe line the backslash reaches Emacs literally and breaks the form.
- `compile`, `lint` and `test` depend on `$(SANDBOX)`, and `BATCH` calls `package-initialize`. Otherwise the dependencies are missing from the load path.
- CI matrix: the oldest supported release first, then the current releases, then `snapshot` with `continue-on-error`. Use `purcell/setup-emacs`. Each job sets `timeout-minutes: 20`.

## Docstrings

checkdoc and package-lint enforce:

- The first line is a complete sentence that ends in a period.
- Sentences end with two spaces.
- Arguments appear in upper case. `_name` is exempt.
- Quote symbols `` `like-this' ``, never `` `like-this` ``.
- A parenthesis at column zero needs `\(`.
- Key sequences use `\\[command]`, not a literal `mouse-1`.
- Ambiguous names need ``the variable `exec-path'``.

Write no `\=` before a closing quote or an apostrophe. Use `\=` only before a quote that opens a quoted form in an example.

## Tests

The checks above do not test behavior. Write ERT tests for logic that the author's configuration covers by accident:

- Every branch that reads a user option, with the Emacs default value.
- Round trips: add and remove advice, enable and disable a mode, comment and uncomment.
- Pure helpers: parsing, formatting, string surgery.

Stub with `cl-letf`, use `with-temp-buffer` for buffer logic, and keep the suite runnable in batch without a window system. Prove each new test red (dev-conventions, "3. Verification"). Two Elisp traps:

- A stub that records where the real function would act (a tab switch that notes the buffer) proves nothing.
- `quit-window` kills the buffer of the selected window. A test that works in a buffer it never displayed can kill the next test's buffer.

## Recurring defects in code grown in a configuration

Check every package that comes from a configuration for these:

- **Undeclared buffer-local variables.** `setq-local` on an undeclared symbol compiles silently. Declare it with `defvar-local`. Then `boundp` and `local-variable-if-set-p` are always true for it, so test the value instead.
- **`if-let*` in the else branch.** It binds for the then branch only. The variable is void in the else branch.
- **Options the author always sets.** Arithmetic on `window-sides-slots` fails on its default nil. Run every path with `emacs -Q` values.
- **Advice removed by closure identity.** Each constructor call returns a new closure, so `advice-remove` finds nothing. Name the advice: `(advice-add sym :around fn '((name . my-advice)))`.
- **`(funcall orig-fun args)`** where `(apply orig-fun args)` is correct.
- **Doubled quoting** in a defcustom default: `'(("k" . '(:a 1)))` puts `(quote (:a 1))` where a plist belongs.
- **Symbols outside the package prefix**, and typos in the prefix. package-lint catches both, byte-compile does not.
- **`plist-put` on user data** mutates the user's customization. Return a new list (`append`, `copy-sequence`). Test every value shape the docstring promises.
- **`listp` before `functionp`.** An interpreted lambda is a list. Check `functionp` first.
- **Private API of other packages** (`project--find-in-directory`). Use the public entry. When there is none, say so in a comment at the call.
- **Docstrings copied from a sibling mode.** Read every docstring once as a user.
- **`copy-marker` on a number** marks the current buffer. Make markers before `with-current-buffer` changes it.
- **`comint-last-prompt` during output** points inside the output. Copy to the end of the buffer and strip the prompt from the text.
- **A declaration between `;;;###autoload` and its definition** takes the cookie. Check the generated autoloads file.
- **A buffer-local minor mode dies with the major mode** (`kill-all-local-variables`). Mark it `permanent-local` and re-apply its setup from `after-change-major-mode-hook`.
- **A new window inherits the fringes and margins of the window it was split from.** To restore a window, ask what the frame or the buffer gives it, not what the window has now.
- **A rule that reads the window reads the package's own values.** Ask the buffer as well.
- **`(setq some-mode 1)` in documentation** does not run the mode body. Document the mode function call.

## Dependencies and user options

- A subprocess (`call-process-region`) or a built-in costs users no install. Use soft dependencies for optional features: `(if (fboundp 'markdown-mode) (markdown-mode) (text-mode))`.
- For a built-in loaded on demand, use `declare-function` and `defvar`, not `require`.
- Call a subprocess once for all items, joined by a marker paragraph. Count the pieces that come back. If the count is wrong, fall back to one call per item.
- Recommend user options and key bindings in the README and the commentary. A map that is active only in the package's own temporary buffers (`C-c C-c` in an edit buffer) is the exception.
- No workaround for one configuration. Name the needed setting in the README.
- The README has a minimal working configuration. Record the demo pictures with it, not with the author's configuration.

## Publishing on MELPA

1. Merge the work branch into the branch MELPA builds. Tag a release for MELPA Stable.
2. Fork `melpa/melpa` and add `recipes/<package>`:

   ```elisp
   (foo :fetcher github :repo "<owner>/foo")
   ```

   Add `:branch "main"` when the default branch is the work branch. Add no `:files`: the default spec takes the top-level `*.el` (and `lisp/*.el`) without `*-test.el`. MELPA does not read `.elpaignore`.
3. In the melpa checkout, run `make recipes/foo` and `make sandbox INSTALL=foo`.
4. Open one pull request per package.

## Extracting a package from a configuration

1. Copy the block body out and drop the `use-package` wrapper.
2. Rename the `my/` prefix to the package prefix.
3. Leave keybindings, window placement and personal options in the configuration.
4. Add the header block, the requires, the autoload cookies and the registration the wrapper did.
5. Replace configuration shortcuts by package-grade equivalents, for example a dependency by a subprocess call.
6. Point the configuration at the package, so one copy of the code exists.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits, pre-commit hooks, push and attribution rules, tagging and releases.
