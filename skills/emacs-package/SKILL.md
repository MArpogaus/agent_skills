---
name: emacs-package
description: >
  Conventions for building, checking and publishing Emacs Lisp packages
  the way MArpogaus does: repository layout, file headers, the make
  based check pipeline, GitHub Actions matrix, ERT tests, and the MELPA
  submission steps.  Use when creating a new package, extracting one
  from a configuration, reviewing one, or preparing a MELPA release.
license: MIT
compatibility: claude-code opencode
metadata:
  requires: [git-conventions, emacs-config]
  stack: emacs
---

# Skill: Emacs Package

## Start from the template

`MArpogaus/emacs-package-template` holds the layout every package
follows.  Create a repository from it and rename the placeholder:

```shell
name=your-package
git mv my-package.el "$name.el"
git mv test/my-package-test.el "test/$name-test.el"
grep -rl my-package . --exclude-dir=.git | xargs sed -i "s/my-package/$name/g"
make
```

Layout, identical in every package:

```
.dir-locals.el              indentation, fill column, double space
.elpaignore                 files MELPA leaves out of the tarball
.github/workflows/test.yml  CI, one job per supported Emacs version
.gitignore
COPYING                     GPLv3
Makefile                    compile, checkdoc, lint, test
README.org                  Best-README-Template style, org
<package>.el
test/<package>-test.el
```

Multi-file packages add companions next to the main file, one per
optional integration (`<package>-<topic>.el`).  Each companion needs
its own header block, and **package-lint checks the symbol prefix
against the file name**: `foo-project.el` may only define `foo-project-*`.

## File headers

Every file, companions and test files included:

```elisp
;;; foo.el --- One line, no trailing period -*- lexical-binding: t; -*-

;; Copyright (C) 2026 Marcel Arpogaus

;; Author: Marcel Arpogaus <znepry.necbtnhf@tznvy.pbz>
;; Version: 0.1
;; Package-Requires: ((emacs "29.1"))
;; Keywords: convenience
;; URL: https://github.com/MArpogaus/foo

;; This file is not part of GNU Emacs.
;; <GPLv3 blurb, 14 lines>

;;; Commentary:
;; What it does and how to start.  This is what describe-package shows.

;;; Code:
...
(provide 'foo)
;;; foo.el ends here
```

- The email is ROT13 obfuscated on purpose; keep it that way.
- `Package-Requires` in the **main file** decides what MELPA installs;
  companions declare their own but nothing installs them, so a
  companion needing a newer Emacs forces the main file up too.
- `Keywords` must contain at least one word from `finder-known-keywords`
  (`convenience`, `tools`, `languages`, …); extra words are allowed.
- Autoload cookies belong on the entry points only: interactive
  commands, minor modes, hook functions referenced by an autoloaded
  `add-hook`, and variables users set before loading.

## The check pipeline

`make` runs the same four steps the CI runs, and it bootstraps its own
tools into `.sandbox/`, so a fresh checkout needs nothing but Emacs:

| Target | What it enforces |
|---|---|
| `compile` | byte-compile with `byte-compile-error-on-warn t` |
| `checkdoc` | any output at all fails the target |
| `lint` | `package-lint`, the rules MELPA applies |
| `test` | ERT suite in `test/` |

Two Makefile details that are easy to get wrong:

- Elisp programs go into **make variables**, not into recipe lines.
  Make joins a variable's continuation lines; inside a quoted recipe
  line the backslash reaches Emacs literally and breaks the form.
- `compile`, `lint` and `test` must all depend on `$(SANDBOX)`, and
  `BATCH` must `package-initialize`, or the dependencies are missing
  from the load path.

CI matrix: the oldest supported release first, then the current ones,
then `snapshot` with `continue-on-error`.  Use `purcell/setup-emacs`.

## What the checks catch, and what they do not

checkdoc and package-lint are strict about form:

- Docstring first line is a complete sentence ending in a period.
- Sentences end with **two** spaces.
- Arguments appear in the docstring in upper case; `_name` is exempt.
- Symbols are quoted `` `like-this' ``, never `` `like-this` ``.
- A parenthesis at column zero inside a docstring needs `\(`.
- Key sequences use `\\[command]`, not literal `mouse-1`.
- Ambiguous names need `the variable `exec-path'` rather than the bare
  symbol.

Nothing checks behaviour.  Write ERT tests for the logic that a
configuration would otherwise cover by accident — a package runs on
other people's defaults:

- Every branch that reads a user option, tested with the **Emacs
  default**, not with the author's setting.  Bugs hide exactly there.
- Round trips: add and remove advice, enable and disable a mode,
  comment and uncomment.
- Pure helpers: parsing, formatting, string surgery.

Use `cl-letf` to stub, `with-temp-buffer` for buffer logic, and keep
the suite runnable in batch without a window system.

Run every new test once against the unfixed code.  A test that passes
either way is worse than none, because it claims cover it does not
give, and the two ways to write one are easy to hit: a stub that
records where the real thing would have acted (a stubbed tab switch
that notes the buffer instead of changing it proves nothing), and an
assertion on state that nothing in the failing path touches.  Watch
what tests do to each other, too: `quit-window' kills the buffer of
the selected window, so a test that commits from a buffer it never
displayed can take the next test's buffer with it.

## Recurring defects in configuration-grown code

Found in review, worth checking in any package extracted from a config:

- **Undeclared buffer-local variables.** `setq-local` on an undeclared
  symbol compiles silently.  Declare with `defvar-local`, and then fix
  the tests: `boundp` and `local-variable-if-set-p` are *always* true
  for a declared automatically-buffer-local variable, so a `cond`
  branch guarded that way starts firing for every buffer.  Test the
  value instead.
- **Bindings that do not reach the else branch.** `if-let*` binds for
  the then branch only; using the variable in the else branch is a
  void-variable error that only fires on the untested path.
- **Options the author always sets.** Code that reads
  `window-sides-slots` and does arithmetic on it breaks on the default
  of nil.  Run every code path with `emacs -Q` values.
- **Advice removed by closure identity.** Each call to an advice
  constructor returns a fresh closure, so `advice-remove` finds
  nothing.  Give the advice a name:
  `(advice-add sym :around fn '((name . my-advice)))`.
- **`(funcall orig-fun args)`** where `(apply orig-fun args)` was
  meant: the argument list arrives as a single argument.
- **Doubled quoting** in a defcustom default, `'(("k" . '(:a 1)))`,
  which puts `(quote (:a 1))` where a plist is expected.
- **Symbols outside the package prefix**, and typos in the prefix
  itself — package-lint catches both, byte-compile does not.
- **`plist-put` on user data.** Normalizing a defcustom value with
  `plist-put` mutates the user's customization in place.  Return a
  fresh list (`append`, `copy-sequence`).  And test every value shape
  the docstring promises: the shape the author never used is the one
  that signals.
- **`(lambda ...)` versus `nlistp`.** An interpreted lambda IS a list,
  so a `listp` type dispatch misroutes function values.  Check
  `functionp` before `listp`.
- **Private API of other packages** (`project--find-in-directory`,
  `tab-bar--load-buttons`).  Use the public entry when one exists;
  when none does, say so in a comment at the call.
- **Minor mode docstrings copied from a sibling mode** — read every
  docstring once as a user would.
- **`copy-marker` on a number** answers for whatever buffer is
  current.  Inside a `with-current-buffer` for another buffer it marks
  a stretch of that one; make the markers before the buffer changes.
- **`comint-last-prompt` while output arrives.**  Comint calls the
  last line without a newline a prompt, so during a running command it
  points inside the output, not at the prompt.  Copy to the end of the
  buffer and strip the prompt from the text instead.
- **A cookie belongs to the form below it.**  A declaration slipped
  between `;;;###autoload` and a definition takes the cookie with it,
  and the definition silently loses its autoload.  Read the generated
  autoloads, not the source, to check.
- **A buffer-local minor mode dies with the major mode.**
  `kill-all-local-variables` clears it like any other local variable.
  Mark it `permanent-local` and re-apply what it set up from
  `after-change-major-mode-hook`, because the face remaps and the
  prefixes do not survive and must be made again.
- **A new window inherits the dressing of the one it was split from.**
  Saving what a window has as "what it had before" then saves the
  package's own fringes or margins and gives them back for good.  Ask
  what the frame or the buffer would have given it.
- **A rule that reads the window reads your own handiwork.**  A margin
  the buffer asks for after the box went up never shows in the window,
  because the package wrote its own width there; ask the buffer as
  well.
- **`(setq some-mode 1)` in documentation.** Setting a minor mode
  variable does not run the mode's body; documentation must call the
  mode function.

## Dependencies

Prefer none.  Before adding one, check whether a subprocess or a
built-in does the job: converting Markdown through `call-process-region`
costs nothing, while depending on `markdown-mode` costs every user an
install.  Use soft dependencies for optional comfort:

```elisp
(if (fboundp 'markdown-mode) (markdown-mode) (text-mode))
```

For a built-in loaded on demand, declare rather than require, so
byte-compile stays quiet:

```elisp
(declare-function org-create-formula-image "org" (string tofile options buffer &optional type))
(defvar org-format-latex-options)
```

A subprocess is cheap once and expensive per item.  Rendering every
cell of a notebook through its own converter cost 44 milliseconds a
cell, two seconds for fifty; the same cells through one call, joined
by a marker that is a plain word in a paragraph of its own, cost 0.06
seconds.  Count the pieces that come back and fall back to one call
per item when the count is wrong, so a converter that reshapes the
marker cannot corrupt the result.

A package must not set user options.  Recommend them in the README and
in the commentary instead.

## Publishing on MELPA

1. Merge the work branch into the branch MELPA builds, and tag a
   release for MELPA Stable.
2. Fork `melpa/melpa`, add `recipes/<package>`:

   ```elisp
   (foo :fetcher github :repo "MArpogaus/foo")
   ```

   Add `:branch "main"` when the default branch is the working branch.
   No `:files` keyword: `.elpaignore` already excludes the tests, the
   Makefile and the CI files.
3. Verify locally in the melpa checkout: `make recipes/foo` and
   `make sandbox INSTALL=foo`.
4. One pull request per package.  Its checklist asks for lint-clean
   code, which `make` already answers.

## Extracting a package from the configuration

The literate configuration keeps features in `emacs.org` blocks (see
the `emacs-config` skill).  When one grows up:

1. Copy the block body out, drop the `use-package` wrapper.
2. Rename the `my/` prefix to the package prefix throughout.
3. Cut what is personal: keybindings, window placement rules, options
   set for the author's setup.  Those stay in the configuration.
4. Add the header block, the requires, the autoload cookies and the
   registration the wrapper used to do.
5. Replace configuration-only shortcuts by package-grade equivalents,
   the way a dependency on another package becomes a subprocess call.
6. Point the configuration at the package afterwards, so there is one
   copy of the code, not two.

## Display engine rules for overlay-heavy UIs

Hard-won facts.  Each one cost a debugging session; do not rediscover
them.

- Display properties do not nest.  A `display` string swallows the
  display properties of the text inside it, images included.  A body
  that carries images must ride an overlay string (`after-string`),
  not a `display` property.
- A `display` string ignores `(space :align-to (- right ...))`.
  Right-aligned icons only work in overlay strings (`before-string`,
  `after-string`), never inside a `display` replacement.
- An overlay string without a face inherits the face of the buffer
  text next to it.  Give every block a base face with
  `add-face-text-property` APPEND, or stray overlines spread.
- An invisible overlay hides the `display` and the strings of every
  overlay below it, but only when it is wider than that overlay.
- `outline-flag-region' hides up to the end of the last line of a
  subtree and stops one character short of the newline that ends it.
  A block that hangs on that newline survives every fold.  Advising
  `outline-flag-region' and hiding the block by hand is the robust
  way; guessing anchor positions is not.
- A window can only start at a buffer position, so `next-line' crosses
  a display block in one step.  Only `pixel-scroll-precision-mode'
  moves through it a part at a time.
- `make-cursor-line-fully-visible' t plus a block taller than the
  window makes redisplay throw the window start back below the block.
  With the default scroll options this resolves itself; do not set
  scroll options from a package.
- `scroll-conservatively' above 100 forbids recentering.  Over two
  blocks taller than the window, redisplay then hands the window from
  one to the other with every scroll event, endlessly.  Keep it at
  100, or set `scroll-margin' to 1 or more.
- A block taller than the window cannot be scrolled past at all: the
  wheel bounces backwards off it and starts over.  Measured in a 437
  pixel text area, 25 pixels an event: a figure at 0.9 of the area
  bounced 40 times in 399 events, one at 0.8 went by without a step
  backwards.  Cap an inline image to a share of the window.
- A window start cannot be put inside an overlay string, so line
  scrolling stops at such a block and stays there.  A page scroll and
  `next-line' get past; the wheel gets past but does not come back to
  the same place.
- Redisplay pays for face runs, not for size.  Forty lines of plain
  output scroll as cheaply as none; twelve lines full of face changes
  cost three times as much, and rendered Markdown carries hundreds of
  runs where code carries a handful.
- A rendering that hangs on the source lines it replaces, a piece to a
  line, costs only what the window shows and keeps the text scrollable
  like ordinary text.  One string for the whole thing is laid out
  whole on every redisplay: the same fixture went from 6.3 to 2.0
  milliseconds an event that way.  Lines with nothing to show go under
  an invisible run, and such a run must start at the end of a visible
  line, never at the start of one, or `scroll-down' answers it with a
  beginning-of-buffer error.
- `char-displayable-p' answers for the character set, not the font:
  it says yes to characters that draw as a hex box.  On a graphical
  frame ask `(internal-char-font nil CHAR)` and keep a plain-text
  fallback.  Nerd font glyphs (private use area) always need this.
- `string-pixel-width' measures right-aligned icon groups; glyphs
  render wider than `string-width' counts.
- The window parameters `tab-line-format', `header-line-format' and
  `mode-line-format' override per WINDOW without touching the buffer.
  Changes only show after `force-mode-line-update'.
- Margins draw only along lines of text; fringes run the full window
  height.  Side borders that must reach the window bottom are fringes
  (graphic only).
- In a tab/mode-line row, `(space :align-to (- right N))' aligns to
  the TEXT area and leaves the fringes out — the right edge misses
  the window edge.  A fill that must span the whole row uses a huge
  align-to (`:align-to 10000'); it clips at the row end exactly.
- The `default' face specifies EVERY attribute, so a face plist like
  `(:strike-through t :inherit default)' loses the strike-through to
  the inherited nil.  Inherit from faces with unspecified attributes,
  or set the attribute to an explicit color.
- `face-foreground' does not see buffer-local face remaps.  To let a
  remap recolor derived UI, let the display engine resolve it:
  `(:inherit the-face :inverse-video t)' turns the (possibly
  remapped) foreground into a background.
- A row of a few pixels: a stretch space with `:height (N)' in the
  display spec.  Do NOT add a face `:height' below one for this: in a
  side window whose header line measures itself (`string-pixel-width'
  re-enters redisplay), a fractional face height in the mode line
  sends Emacs into an endless measuring recursion and it dies of a
  stack overflow.  The display spec alone is safe.  Bisect such
  crashes ingredient by ingredient; the backtrace is unsymbolized,
  but repeating frames mean recursion.
- An overline is always one pixel, so a box built from overlines and
  drawn rows should be one pixel everywhere, or its edges carry
  different weights.
- `window-total-width' counts the column a terminal spends on the
  separator between two windows side by side.  An edge string built
  from it is one column too long and loses its last glyph; use the
  body width plus the margins.
- A scroll bar sits outside the fringe, so a fringe border never
  reaches the window's outer edge.
- A header or mode line row reaches past fringes and margins, so a
  border drawn from those cannot close that row's ends.  Let the row
  close itself with a glyph at each end.

Pixel claims are testable: export the frame with `x-export-frames'
inside Emacs (guard it with `declare-function', console builds lack
it), then read the PNG with pillow and assert the edges' thickness
and position.  Have the Emacs side write the window geometry to a
file, because a frame holds more grey lines than the package draws,
the mode line's own shadow among them.

## Measuring display behavior, and demo recordings

Redisplay claims are testable.  Do not argue from the manual; measure
in a real frame under Xvfb:

    Xvfb :99 -screen 0 1280x900x24 &
    DISPLAY=:99 emacs -Q -l probe.el

- Getting that display in a sandbox is its own exercise.  Emacs, make,
  pandoc and Xvfb come from conda-forge through micromamba, into a
  directory with room (a tmpfs, when the disk is full).  A prebuilt
  Xvfb usually refuses to start there: it wants libraries that are a
  decade older than the environment, `xkbcomp` at a path under
  `/usr/bin` and a writable `/var/lib/xkb`.  The old libraries come
  from CentOS 7 RPMs (`rpm2cpio | cpio -idmu`, then `LD_LIBRARY_PATH`),
  and the two paths from a private mount namespace, which needs no
  root:

      unshare -rm sh -c '
        mount -t overlay overlay -o lowerdir=/usr/bin,upperdir=$U,workdir=$W /usr/bin
        mount -t overlay overlay -o lowerdir=/usr/share/X11,upperdir=$UX,workdir=$WX /usr/share/X11
        mount -t tmpfs none /var/lib; mkdir -p /var/lib/xkb
        exec Xvfb :99 -screen 0 1400x900x24'

  The socket lands in the shared `/tmp/.X11-unix`, so Emacs outside the
  namespace uses `DISPLAY=:99` as usual.  Test the result by starting a
  real frame, not with `emacs --batch`: a batch session opens no
  display connection and answers nil however healthy the server is.
- A probe script drives the session from a timer
  (`run-with-timer 0.5 nil #'main`), never from top-level code: the
  frame is not up while the file loads.  It writes results to a file;
  `message' output is invisible and `send-string-to-terminal' fails
  in a graphical session.
- Scroll correctness is one invariant: while scrolling up, the window
  start must never move down.  Track `(cons (window-start)
  (window-vscroll nil t))` after each event and `redisplay t'.
- Such a test belongs in CI.  The nix builds from purcell/setup-emacs
  have no X, so give the pixel tests their own job on the
  distribution Emacs: `apt-get install xvfb emacs-gtk`, then
  `xvfb-run make scroll`.  In batch the tests `skip-unless
  (display-graphic-p)`.
- Demo GIFs need no screen recorder: `x-export-frames' returns the
  frame as PNG from inside Emacs, without mouse pointer or window
  decoration.  Capture deterministically - one frame per scroll step,
  ten frames per second of hold - and never resample the frame rate
  afterwards (ffmpeg `fps=` drops frames unevenly and the motion
  stutters).  Hold the final view with `tpad` — a short ending makes
  the loop restart read as a jump.  Play the frames back slightly
  fast:

      ffmpeg -framerate 13 -i frames/f%04d.png \
        -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=2.5,\
        scale=820:-1:flags=lanczos,split[a][b];\
        [a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:\
        bayer_scale=3" -loop 0 raw.gif
      gifsicle -O3 --lossy=80 raw.gif -o img/demo.gif

- An overlay's `line-prefix' stops at the end of the buffer, so a box
  built from it leaves the rows below the last line open.  The
  buffer-local variable reaches them.  It is not a loss of window
  precision: a glyph bound for a margin renders only where there is a
  margin, so a per-window margin scopes a buffer-wide prefix.
- A terminal has no overline, so anything that attaches an edge to an
  existing line is graphic-only; a terminal needs a row of its own.
- Close a row at its right end by aligning to `right', not to a
  measured width: a glyph can render a pixel wider than
  `string-pixel-width' reports, and the corner misses by one.  A face
  `:box' with `(:line-width (1 . 0))' draws the left end but its right
  end is eaten by a trailing stretch glyph.
- Record on the default theme, drive prompts with `cl-letf' on
  `completing-read', and keep the driver script in `demo/` in the
  repository, with `demo` and `img` listed in `.elpaignore`.
- For one pixel line art, encode at the frames' own size with
  `paletteuse=dither=none' and no `gifsicle --lossy'.  Scaling turns a
  one pixel line into two grey ones (measured: an edge column of 127
  reads 178 after `scale=820'), and dithering scatters noise that also
  makes the file bigger.  Record at a width the reader will not scale
  either.
- Verify the encoding rather than trusting it: decode the GIF back to
  PNGs and compare a frame against its source, sampling the columns
  the border sits in.
- `gifsicle -O3' collapses identical consecutive frames into one with
  a long delay, so a five frame GIF of a five state demo is fully
  encoded, not truncated.  Count states, not frames.
- A demo that toggles a mode shows every layout change the mode
  makes.  Measure it: the first pixel of a text row before and after
  must be the same column, and the first frame must equal the last.
