# Emacs Package: reference

Read this before you build or debug an overlay-heavy UI, a pixel test or
a demo recording.

## Display properties and overlay strings

- Display properties do not nest. A `display` string drops the display
  properties of the text inside it, images included. A body with images
  rides an overlay string (`after-string`), not a `display` property.
- A `display` string ignores `(space :align-to (- right ...))`.
  Right-aligned icons work only in `before-string` or `after-string`.
- A display property inside a display string is never read. Put an
  image, a size cap or a hidden delimiter in the text or on a
  before/after-string, never in a nested `display`.
- An overlay string is not drawn when its position is in invisible text.
  An `after-string` draws at the overlay's end, so an invisible overlay
  that starts there hides it. Use the `before-string`, which draws at
  the overlay's start.
- An overlay string without a face inherits the face of the buffer text
  next to it. Give every block a base face with `add-face-text-property`
  APPEND.
- An invisible overlay hides the `display` and the strings of every
  overlay below it, but only when it is wider than that overlay.
- Two overlays of the same priority over the same character: the
  narrower one wins. Give a narrow guide the higher priority.
- `line-prefix` with a number draws nothing. It takes a string or a
  display spec.
- A `line-prefix` with a fringe bitmap applies to the rows of a string
  only when the string carries the property itself. A display property
  carries no fringe.
- An overlay's `line-prefix` stops at the end of the buffer. The
  buffer-local variable reaches the rows below. A glyph for a margin
  renders only where the window has a margin, so a per-window margin
  scopes a buffer-wide prefix.

## Keymaps and clicks

- A keymap on an overlay shadows every keymap inside the string that
  overlay displays, because `get-char-property` reads an overlay before
  a text property. Where the string carries its own keymaps, put none on
  the overlay.
- A keymap in an `after-string` or `before-string` at the overlay's edge
  is not shadowed. The string draws outside the overlay's range.
- Emacs reads a display string's own text properties for a click:
  `posn-string` gives (STRING . INDEX).
- To ask what a click runs, pass the position:
  `(key-binding [mouse-2] nil nil posn)`. Without it the answer is for
  point.

## Widths and alignment

- For the columns of a window row, use `window-max-chars-per-line`, not
  `window-body-width`. It subtracts line numbers and margins and takes a
  WINDOW argument.
- `window-total-width` counts the separator column between side-by-side
  terminal windows. Use the body width plus the margins.
- `(space :align-to (- right N))` needs two columns of slack in a
  terminal. A row that reaches the last column wraps its last glyph.
- In a tab or mode line, `:align-to (- right N)` aligns to the text area
  and leaves out the fringes. A fill over the whole row uses
  `:align-to 10000`.
- Close a row at its right end by aligning to `right`, not to a measured
  width. A glyph can render a pixel wider than `string-pixel-width`
  reports.
- `string-pixel-width` measures right-aligned icon groups. Glyphs render
  wider than `string-width` counts.
- A string built for a window keeps its cuts when the window grows,
  until the builder runs again. Do not measure a window that does not
  show the buffer. With no window, leave the string whole. Pass
  `'visible` as ALL-FRAMES to `get-buffer-window-list`.
- A face `:box` with `(:line-width (1 . 0))` loses its right end to a
  trailing stretch glyph.

## Faces, fringes, margins, header lines

- The `default` face specifies every attribute.
  `(:strike-through t :inherit default)` loses the strike-through.
  Inherit from faces with unspecified attributes, or set an explicit
  color.
- `face-foreground` does not see buffer-local face remaps. Use
  `(:inherit the-face :inverse-video t)` to turn the remapped foreground
  into a background.
- For a row a few pixels high, use a stretch space with `:height (N)` in
  the display spec. A face `:height` below one in a mode line of a side
  window whose header line calls `string-pixel-width` recurses until a
  stack overflow.
- An overline is always one pixel. Draw every edge of a box one pixel
  wide.
- A terminal has no overline. An edge attached to an existing line is
  graphic only. A terminal needs a row of its own.
- Margins draw only along lines of text. Fringes run the full window
  height, in graphic frames only.
- A scroll bar sits outside the fringe, so a fringe border never reaches
  the window's outer edge.
- A header or mode line row reaches past fringes and margins. Close that
  row with a glyph at each end.
- The window parameters `tab-line-format`, `header-line-format` and
  `mode-line-format` override per window. Call `force-mode-line-update`
  after a change.
- `format-mode-line` with a FACE argument attaches no face to the
  returned string. Add the face after the call.
- `char-displayable-p` answers for the character set, not the font. On a
  graphical frame ask `(internal-char-font nil CHAR)` and keep a
  plain-text fallback. Nerd font glyphs always need this.
- Icons in one row have the same weight and size. Prefer thin, unfilled
  glyphs. Give each icon its own plain-text fallback.
- `fringe-bitmap-p` is in fringe.el: `(require 'fringe)`. A build
  without fringes still defines `define-fringe-bitmap`, so a test guard
  asks `(fringe-bitmap-p 'left-arrow)`.
- A theme applies through `enable-theme`. Hook `enable-theme-functions`,
  not advice on `load-theme`.

## Folding and scrolling

- `outline-flag-region` hides up to one character before the newline
  that ends a subtree. A block on that newline survives every fold.
  Advise `outline-flag-region` and hide the block there.
- A window starts only at a buffer position. `next-line` crosses a
  display block in one step. Only `pixel-scroll-precision-mode` moves
  through it in parts.
- A window start cannot be inside an overlay string. Line scrolling
  stops at such a block. A page scroll and `next-line` pass it.
- `make-cursor-line-fully-visible` t and a block taller than the window
  throw the window start back below the block. A package sets no scroll
  options.
- `scroll-conservatively` above 100 forbids recentering. Over two blocks
  taller than the window, redisplay alternates between them on every
  scroll event. Keep it at 100, or set `scroll-margin` to 1 or more.
- The wheel cannot scroll past a block taller than the window. Cap an
  inline image at 0.8 of the window's text area height.
- Never hide the newline a block hangs on. Put the rows on the
  after-string of an overlay that ends before that newline. With the
  newline replaced by `display ""`, `pixel-scroll-precision-scroll-up`
  stops at the block. Test both scroll directions.
- Redisplay cost grows with face runs, not with text size. Rendered
  Markdown has hundreds of runs.
- Hang a rendering on the source lines it replaces, one piece per line.
  Redisplay then lays out only what the window shows. Put empty lines
  under an invisible run that starts at the end of a visible line, never
  at its start, or `scroll-down` signals beginning-of-buffer.

## Other traps

- The REP function of `replace-regexp-in-string` must keep the match
  data. Wrap a REP that searches in `save-match-data`.

## Measure in a real frame

Test redisplay claims in a graphical frame, not from the manual. In the
sandbox, use `<test rig>/rig gui` (its `README.md` explains it).
Elsewhere:

    Xvfb :99 -screen 0 1280x900x24 & DISPLAY=:99 emacs -Q -l probe.el

- `emacs --batch` opens no display and answers nil to
  `display-images-p`.
- Start the probe from a timer (`run-with-timer 0.5 nil #'main`), not
  from top-level code. Write results to a file: `message` output is
  invisible.
- Export the frame with `x-export-frames` (guard it with
  `declare-function`) and read the PNG with pillow. Have Emacs write the
  window geometry to a file, because the frame holds more grey lines
  than the package draws.
- Scroll invariant: while scrolling up, the window start never moves
  down. Track `(cons (window-start) (window-vscroll nil t))` after each
  event and `redisplay t`.
- In CI, the purcell/setup-emacs builds have no X. Give pixel tests
  their own job: `sudo apt-get install -y xvfb emacs-gtk`, then
  `xvfb-run make <pixel-test target>`. The project's Makefile defines
  that target. In batch the tests `skip-unless (display-graphic-p)`.

## Demo recordings

- Capture frames with `x-export-frames`: one frame per scroll step, ten
  frames per second of hold. Do not resample the frame rate (ffmpeg
  `fps=` drops frames unevenly). Hold the final view with `tpad`:

  ```bash
  ffmpeg -framerate 13 -i frames/f%04d.png -filter_complex \
    "[0:v]tpad=stop_mode=clone:stop_duration=2.5,scale=820:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" \
    -loop 0 raw.gif
  gifsicle -O3 --lossy=80 raw.gif -o img/demo.gif
  ```

- For one-pixel line art, encode at the frames' own size with
  `paletteuse=dither=none` and no `--lossy`. Scaling turns one line into
  two grey lines.
- Decode the GIF back to PNGs and compare a frame against its source, at
  the border columns.
- `gifsicle -O3` merges identical consecutive frames. Count states, not
  frames.
- A demo that toggles a mode shows every layout change. The first pixel
  of a text row is the same column before and after, and the first frame
  equals the last.
- Record on the default theme, drive prompts with `cl-letf` on
  `completing-read`, and keep the driver in `demo/`. List `demo/` and
  `img/` in `.elpaignore`.

## Recurring defects in code grown in a configuration

Check every package that comes from a configuration for these. Run every
path with `emacs -Q` values:

- **Undeclared buffer-local variables.** `setq-local` on an undeclared
  symbol compiles silently. Declare it with `defvar-local`. Then
  `boundp` and `local-variable-if-set-p` are always true for it, so test
  the value instead.
- **`if-let*` in the else branch.** It binds for the then branch only.
  The variable is void in the else branch.
- **Options the author always sets.** Arithmetic on `window-sides-slots`
  fails on its default nil.
- **Advice removed by closure identity.** Each constructor call returns
  a new closure, so `advice-remove` finds nothing. Name the advice:
  `(advice-add sym :around fn '((name . my-advice)))`.
- **`(funcall orig-fun args)`** where `(apply orig-fun args)` is
  correct.
- **Doubled quoting** in a defcustom default: `'(("k" . '(:a 1)))` puts
  `(quote (:a 1))` where a plist belongs.
- **Symbols outside the package prefix**, and typos in the prefix.
  package-lint catches both, byte-compile does not.
- **`plist-put` on user data** mutates the user's customization. Return
  a new list (`append`, `copy-sequence`). Test every value shape the
  docstring promises.
- **`listp` before `functionp`.** An interpreted lambda is a list. Check
  `functionp` first.
- **Private API of other packages** (`project--find-in-directory`). Use
  the public entry. When there is none, say so in a comment at the call.
- **Docstrings copied from a sibling mode.** Read every docstring once
  as a user.
- **`copy-marker` on a number** marks the current buffer. Make markers
  before `with-current-buffer` changes it.
- **`comint-last-prompt` during output** points inside the output. Copy
  to the end of the buffer and strip the prompt from the text.
- **A declaration between `;;;###autoload` and its definition** takes
  the cookie. Check the generated autoloads file.
- **A buffer-local minor mode dies with the major mode**
  (`kill-all-local-variables`). Mark it `permanent-local` and re-apply
  its setup from `after-change-major-mode-hook`.
- **A new window inherits the fringes and margins of its parent
  window.** To restore a window, read the values from the frame or the
  buffer. Do not read them from the window.
- **A rule that reads the window reads the package's own values.** Ask
  the buffer as well.
- **`(setq some-mode 1)` in documentation** does not run the mode body.
  Document the mode function call.
