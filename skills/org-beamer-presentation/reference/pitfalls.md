# Org Beamer pitfalls

Technical facts for the export. Some errors stop the compile. Others
compile cleanly and put the wrong thing on the slide, so look at the
pages too.

## Org markup

- **No `babel`.** Under lualatex the user's Emacs loads `polyglossia`
  from `#+language:`. An added `babel` stops the export with
  `Command \defineshorthand already defined`. An `emacs -Q` export hides
  this, so the headless command sets the package list.
- **Math is LaTeX.** `unicode-math` makes a Unicode math character in
  text mode (β, ≈, →, ≤, ×, −, ²) fail with `Missing $ inserted`. Write
  `$\beta$`, `$\approx$`, `$1.5\times$`, and an ASCII `-` for a minus.
  Outside code blocks, only umlauts, dashes and quotes may be non-ASCII.
- **Display math** is a `#+begin_export latex` block, never an Org
  `equation` environment.
- **A property drawer touches its heading.** A blank line between
  heading and `:PROPERTIES:` typesets the drawer as body text. It
  compiles, so only the page shows it.
- **Never write `\%`.** Org escapes `%` itself. A hand-escaped one
  comments out the rest of the line. In a table the next row then merges.
- **Verbatim is `~code~` or `=verbatim=`.** Backticks export literally.
  Org bold is `*bold*`, not `**bold**`. Nested emphasis such as `*~x~*`
  does not parse.
- **Markup needs a border.** `~…~` opens after whitespace, `(`, `{`, `"`
  or a line start, and closes before whitespace or punctuation.
  `~SI~/~CI~` fails, `~SI~ / ~CI~` works. The same holds for `=`, `*`, `/`.
- **Underscores are verbatim.** In prose or table cells, `_` outside
  `~…~`, `=…=` or `$…$` becomes a subscript. In a block title
  (`:options {…}`) write `\_`, because that text is raw LaTeX.
- **A line that starts with a number and a period becomes a list item.**
  Reflow so no wrapped line starts with `1435. The`.
- **List options.** ox-beamer reads only `:environment`, `:overlay` and
  `:options` on a list. `:options` does not set spacing.
- **Frame text after an in-frame block** must not be a child of the
  block heading. Use a `#+begin_block` special block instead of a `***`
  heading.
- **Fragile frames.** ox-beamer marks a frame with a `src` block, an
  example block or `~code~` as fragile by itself. Add `:BEAMER_OPT:
  fragile` only for raw verbatim (`\verb`, `verbatim`, `lstlisting`)
  inside a `#+begin_export latex` block.
- A `.bbl-SAVE-ERROR` file is an interrupted biber run. Delete it.

## Code frames

- Pin the backend at the end of the file with a local-variables block:
  `# org-latex-listings: listings`.
- A headless export needs `#+LATEX_HEADER: \usepackage{listings}`.
  Without it every code frame fails with `Environment lstlisting
  undefined`.
- listings knows `python` and `bash`. It has no `toml`, `yaml`, `json`
  or `text`. Put those into `#+begin_example`.
- Put each code example in a `#+begin_block` special block with
  `#+ATTR_LATEX: :options {<title>}`, as in `templates/layouts.org`. Text
  after it stays at frame level.
- At `aspectratio=169, smaller` a line holds about 60 monospace
  characters.

## Tables

- No `*bold*` in a `p{}` column. Org exports bold as `\alert{}`, and
  beamer starts it on a new line there. Use an `l` column or no
  emphasis.
- Width budget at `aspectratio=169, smaller`: `\textwidth` is 13.99cm,
  and each column adds 0.42cm of `\tabcolsep`. The sum of the `p{}`
  widths must be at most `13.99 - 0.42 × ncols`: 13.1cm for two columns,
  12.7cm for three, 12.3cm for four. In a column of width `f`, use
  `f × 13.99` instead of 13.99. An overflow shows only as
  `Overfull \hbox` in the log.
- A table that does not fit gets fewer columns or fewer words.

## Log and boxes

- The log's `at line N` refers to the frame's `.vrb` file, not to the
  `.org`. `tools/box-pages.py` maps each warning to its page.
- `Overfull \vbox` means content runs past the bottom of the slide. Cut
  a line or split the frame.
- The metropolis title page always reports about 13.8pt of `\vbox`.
  Ignore it.
- If `biber` does not run, add `org-cite-biblatex-options
  "backend=bibtex"` to the `setq` and put TeX Live before any conda
  environment on `PATH`. The generic `There were undefined references`
  line is then harmless when `pdftotext … | grep -c '??'` prints `0`.

## Literate deck

A deck can compute its figures and tables in Python `src` blocks.

- Header: `#+PROPERTY: header-args:python :python <venv>/bin/python
  :eval never-export :exports results :results output drawer :noweb yes`.
  Shared imports go in a `#+name: setup` block with `:eval no`, pulled
  in with `<<setup>>`. Run `org-babel-execute-buffer` before the export.
- A headless run needs `-l ob-python`.
- Never use `:results file` for a figure. Org writes the return value
  into the file and replaces the PDF. Print the link instead:
  `print("[[file:<path>]]")`. Tables work the same way.
- A failed block leaves a half-filled drawer. Look for `code 1` and for
  a table header with no rows.
- A block must never print an Org heading. The heading ends the drawer,
  and the next run appends a second copy. Print `\begin{columns}` export
  blocks instead.
- A column called `iat` is reachable only as `frame["iat"]`.
  `frame.iat` is the pandas indexer.
- Cache the run's numbers as CSV or JSON in the sidecar. All other
  blocks read only the cache, so the deck rebuilds without the run.

## Figures for the dark 16:9 deck

- **Colours.** Foreground `#E8EDEE`, accent `#EB811B`, surface
  `#23373B`. Use line style and marker for further distinctions.
- **Transparent figures.** Set `savefig.transparent`,
  `figure.facecolor`, `axes.facecolor` and `savefig.facecolor` to
  `"none"`. Set `text.color`, `axes.labelcolor`, `axes.edgecolor`,
  `axes.titlecolor`, `xtick.color` and `ytick.color` to the foreground.
  Then remove explicit dark or white colours that rcParams do not reach:
  grid `color=`, marker `mec`, `bbox` facecolor.
- **Library figures** need recolouring. Walk the axes, remove patch
  facecolors, lift dark artists, and clear each text's
  `get_bbox_patch()`.
- **Fills** must be lighter than the `#23373B` surface.
- **Sizes.** Full-width strip about 5.5 × 1.3 to 2.2 in. Figure beside
  text about 5.2 to 6.4 × 3.3 to 3.9 in. No text under about 6.5 pt after
  scaling.
- **Scaling shrinks text.** A 1200pt-wide graphviz graph at `\linewidth`
  scales to 0.33, so 11pt labels become 4pt. Shorten the labels or raise
  the font size.
- **Legends.** Put a shared legend in figure coordinates with
  `bbox_transform=fig.transFigure`. In a per-axis loop, add the label on
  the first axis only. An empty artist such as `ax.bar([], [])` draws no
  key colour, so use `matplotlib.patches.Patch` proxies.
- **Overlap.** Never overlay two translucent histograms. Draw them side
  by side on shared bins. Give series that coincide their own offset
  lane.
- **Reference lines** get their label off the line, with a solid
  `bbox`.
- **Log axes** need a clip floor for zeros. Label that tick for what it
  is, not `0`.
- **Comparable values only.** Do not sum losses over models with
  different node counts. Plot one node instead.
- **Noisy series.** Show the full range in one panel, often on a log
  axis, and the settled range with a rolling mean in a second panel.
- **Explain marks in the figure.** Label what a band or a dot is.
- Render each generated figure on its own at 120 dpi or more and look
  at it.
