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

- Run every code path with `emacs -Q` defaults, not only with the
  author's configuration.
- A package sets no user options and no key bindings. The README
  recommends them.
- Prefer no dependency: a built-in or a subprocess first, a soft
  dependency for optional features.
- After an extraction, one copy of the code exists: the configuration
  only configures the package.
- Add `;; Assisted-by: <tool name>` to every file of a package that is
  on MELPA or that the user asked to submit to MELPA. Keep it where it
  exists ("File headers").

Read [reference.md](reference.md) before you build or debug overlays,
display properties, margins, fringes, header lines, scrolling over tall
blocks, pixel tests or demo GIFs, and before you review a package that
comes from a configuration.

## Start from the template

`MArpogaus/emacs-package-template` holds the layout every package
follows. Create a repository from it and rename the placeholder:

```shell
name=your-package
git mv my-package.el "$name.el"
git mv test/my-package-test.el "test/$name-test.el"
grep -rl my-package . --exclude-dir=.git | xargs -r sed -i "s/my-package/$name/g"
make
```

Layout, identical in every package:

```
.dir-locals.el              indentation, fill column
.elpaignore                 GNU ELPA leaves these out, package.el skips compiling them; MELPA ignores it
.github/workflows/test.yml  CI, one job per supported Emacs version
.gitignore
COPYING                     GPLv3
Makefile                    compile, lint, relint, test
README.org                  Best-README-Template style, org
docs/implementation.org     mechanism, measurements, test notes
<package>.el
test/<package>-test.el
```

`.dir-locals.el` sets `sentence-end-double-space` to `t` for
`emacs-lisp-mode`, because checkdoc requires two spaces in docstrings.

A multi-file package adds one companion per optional integration next to
the main file (`<package>-<topic>.el`). Each companion needs its own
header block. package-lint checks the symbol prefix against the file
name: `foo-project.el` may only define `foo-project-*`.

README.org sections, in order: About The Project, Getting Started,
Usage, Customization, Known Limits, Comparison with Other Packages, How
It Works, Development, Contributions, License, Contact. Mechanism,
measurements and test notes go to `docs/implementation.org`.

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
;; Assisted-by: <tool name>  (MELPA packages only)

;; This file is not part of GNU Emacs.
;; <GPLv3 blurb, 14 lines>

;;; Commentary:
;; What it does and how to start.  This is what describe-package shows.

;;; Code:
...
(provide 'foo)
;;; foo.el ends here
```

- `<tool name>`: use the value that the package's other files use. In a
  new package, use the harness name (for example `Claude Code`), never a
  model name.
- The email can be ROT13 obfuscated. Keep the form the existing files
  use.
- `Package-Requires` in the main file decides what MELPA installs.
  Nothing installs a companion's requirements, so a companion that needs
  a newer Emacs forces the main file up too.
- `Keywords` contains at least one word from `finder-known-keywords`
  (`convenience`, `tools`, `languages`).
- Put autoload cookies on entry points only: interactive commands, minor
  modes, hook functions in an autoloaded `add-hook`, and variables users
  set before loading.

## The check pipeline

The pipeline has five steps. CI runs `make` and the pre-commit hooks.
`make` runs the four targets. The pre-commit hook `elisp-checkdoc` of
`MArpogaus/emacs-pre-commit-hooks` runs checkdoc. `make` bootstraps its
tools into `.sandbox/`, so a fresh checkout needs only Emacs:

| Step | What it enforces |
|---|---|
| `compile` | byte-compile with `byte-compile-error-on-warn t` |
| checkdoc (hook) | any output fails the hook |
| `lint` | `package-lint`, the rules MELPA applies |
| `relint` | regexps, and `\=` escapes that checkdoc misses |
| `test` | ERT suite in `test/` |

- Put Elisp programs into make variables, not into recipe lines. Inside
  a quoted recipe line the backslash reaches Emacs literally and breaks
  the form.
- `compile`, `lint`, `relint` and `test` depend on `$(STAMP)`, a file
  that the sandbox bootstrap writes last, and `BATCH` calls
  `package-initialize`. Otherwise the dependencies are missing from the
  load path.
- CI matrix: the oldest supported release first, then the current
  releases, then `snapshot` with `continue-on-error`. Use
  `purcell/setup-emacs`. Each job sets `timeout-minutes: 20`.

## Docstrings

checkdoc and package-lint enforce:

- The first line is a complete sentence that ends in a period.
- Sentences end with two spaces.
- Arguments appear in upper case. `_name` is exempt.
- Quote symbols `` `like-this' ``, never `` `like-this` ``.
- A parenthesis at column zero needs `\(`.
- Key sequences use `\\[command]`, not a literal `mouse-1`.
- Ambiguous names need ``the variable `exec-path'``.

Write no `\=` before a closing quote or an apostrophe. Use `\=` only
before a quote that opens a quoted form in an example.

## Tests

The checks above do not test behaviour. Write ERT tests for logic that
the author's configuration covers by accident:

- Every branch that reads a user option, with the Emacs default value.
- Round trips: add and remove advice, enable and disable a mode, comment
  and uncomment.
- Pure helpers: parsing, formatting, string surgery.

Stub with `cl-letf`, use `with-temp-buffer` for buffer logic, and keep
the suite runnable in batch without a window system. Two Elisp traps:

- A stub that records where the real function would act (a tab switch
  that notes the buffer) proves nothing.
- `quit-window` kills the buffer of the selected window. A test that
  works in a buffer it never displayed can kill the next test's buffer.

## Dependencies and user options

- Write a soft dependency as
  `(if (fboundp 'markdown-mode) (markdown-mode) (text-mode))`. A
  subprocess is `call-process-region`.
- For a built-in loaded on demand, use `declare-function` and `defvar`,
  not `require`.
- Call a subprocess once for all items, joined by a marker paragraph.
  Count the pieces that come back. If the count is wrong, fall back to
  one call per item.
- A map that is active only in the package's own temporary buffers
  (`C-c C-c` in an edit buffer) is the exception to the no-key-bindings
  rule.
- No workaround for one configuration. Name the needed setting in the
  README.
- The README has a minimal working configuration. Record the demo
  pictures with it, not with the author's configuration.

## Publishing on MELPA

1. Merge the work branch into the branch MELPA builds. Tag a release for
   MELPA Stable.
2. Fork `melpa/melpa` and add `recipes/<package>`:

   ```elisp
   (foo :fetcher github :repo "<owner>/foo")
   ```

   Add `:branch "main"` when the default branch is the work branch. Add
   no `:files`: the default spec takes the top-level `*.el` (and
   `lisp/*.el`) without `*-test.el`. MELPA does not read `.elpaignore`.

3. In the melpa checkout, run `make recipes/foo` and
   `make sandbox INSTALL=foo`.
4. Open one pull request per package.

## Extracting a package from a configuration

1. Copy the block body out and drop the `use-package` wrapper.
2. Rename the `my/` prefix to the package prefix.
3. Leave keybindings, window placement and personal options in the
   configuration.
4. Add the header block, the requires, the autoload cookies and the
   registration the wrapper did.
5. Replace configuration shortcuts by package-grade equivalents, for
   example a dependency by a subprocess call.
6. Point the configuration at the package.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits, pre-commit
  hooks, push and attribution rules, tagging and releases.
