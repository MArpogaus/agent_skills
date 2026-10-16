---
name: paper-writing
description: >
  End-to-end academic paper writing workflow for ML research:
  LaTeX project scaffolding, figure generation, writing with
  IEEE/Elsevier/UAI templates, build, and venue submission. The
  experiment code follows ml-project. A revision of an existing draft
  follows latex-paper-revision. Use when the user asks to start,
  write, build or submit a paper, or in a repo with `main.tex` and
  `references.bib`.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ml latex, audience: researchers, requires: [dev-conventions, git-conventions, ml-project, python-dev]}
---

# Skill: Paper Writing

Load this skill to write a new academic paper: from the finished
experiments through figures, LaTeX writing and the camera-ready
submission. For a revision, use `latex-paper-revision`.

## Hard rules

- Every number, result and citation in the text comes from data or
  sources the user provided. Never invent one. Mark a gap with
  `\TODO{...}`.
- A new paper puts sections in `tex/` and figures in `gfx/`. An
  existing draft keeps its directory names.
- Before `compile.sh` or a submission, build `main.pdf` with `latexmk`.
  Then `pdftotext main.pdf - | grep -c 'TODO:'` prints `0`.
- Load `biblatex` or `\bibliography`, never both.
- Take the class options from the venue template. Never guess them.
- Compile before each commit and check that the log has no undefined
  references or citations.

## Phase 1: LaTeX project scaffolding

### Directory structure

```
<paper>/
├── main.tex                  # Root document
├── references.bib            # Bibliography
├── compile.sh                # Build / submission script (optional)
├── latexmkrc                 # latexmk config (optional)
├── preamble.tex              # Packages, macros, operators (\input'ed)
├── glossaries.tex            # \newacronym definitions (\input'ed)
├── tex/                      # Section files
│   ├── 01_introduction.tex
│   ├── 02_background.tex
│   ├── 03_method.tex
│   ├── 04_experiments.tex
│   ├── 05_results.tex
│   ├── 06_conclusion.tex
│   └── 07_acknowledgments.tex
├── gfx/                      # Figures (PDF, PNG)
├── csv/                      # Data files for PGFPlots (optional)
└── tikz/                     # TikZ figure sources (optional)
```

### Preamble template

Include the preamble as a separate file (`preamble.tex`) and
`\input` it in the main document.

#### Required packages

```latex
% ---- math ----
\usepackage{amsmath, amssymb, amsfonts, mathtools, bm}

% ---- graphics ----
\usepackage{graphicx}
\graphicspath{{./gfx/}}
\usepackage[font=small, labelfont=bf]{caption}
\usepackage[font=small, labelfont=bf]{subcaption}

% ---- plots ----
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepgfplotslibrary{dateplot, fillbetween}

% ---- tables ----
\usepackage{booktabs, multirow, array}

% ---- hyperlinks ----
\usepackage[colorlinks=true, citecolor=blue, linkcolor=blue,
            urlcolor=blue]{hyperref}
\usepackage[nameinlink, capitalize]{cleveref}

% ---- colours ----
\usepackage[dvipsnames]{xcolor}

% ---- bibliography ----
\usepackage[
  style=ieee,           % or authoryear-comp
  dashed=false,
  hyperref=true,
  url=true,
  backend=biber,
  natbib=true,
]{biblatex}
\addbibresource{references.bib}

% ---- algorithms ----
\usepackage{algorithm, algpseudocode}

% ---- glossaries ----
\usepackage[acronym]{glossaries}
\makeglossaries
\input{glossaries.tex}
```

#### Standard math operators (canonical across papers)

```latex
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\nll}{NLL}
\DeclareMathOperator*{\ecdf}{ECDF}
\DeclareMathOperator{\softmax}{softmax}
\DeclareMathOperator{\softplus}{softplus}
```

#### Standard notation conventions

| Notation | Meaning |
|----------|---------|
| `Y` | Random variable (capital Latin) |
| `y` | Realisation (lowercase Latin) |
| `\mathbf{y}` | Vector |
| `\vartheta`, `\theta` | Scalar parameters |
| `\bm{\theta}` | Parameter vector |
| `F_{Y \mid \mathbf{X} = \mathbf{x}}` | Conditional distribution |

#### TODO macros

```latex
\newcommand{\TODO}[1]{\textcolor{red}{\textbf{(TODO: #1)}}}
```

### Bibliography

The preamble loads `biblatex` with `biber`. Print with
`\printbibliography`. Elsevier uses `bibtex`: remove the `biblatex`
block from the preamble and use the `elsarticle-num` style:

```latex
\bibliographystyle{elsarticle-num}
\bibliography{references}
```

### Acronyms (`glossaries.tex`)

```latex
\newacronym{MLE}{MLE}{maximum likelihood estimation}
\newacronym{NLL}{NLL}{negative log-likelihood}
```

Use in text: `\gls{MLE}` (the first use expands the full form),
`\glspl{MLE}` (plural), `\acrfull{MLE}` (always the full form).

## Phase 2: Figure generation

### Python → PDF → LaTeX workflow

Generate publication-quality figures in Python and include the
resulting PDF in LaTeX. Figure scripts follow `python-dev`
("Figures"). `ml-project` says where the scripts and figures live.
Copy the PDFs from the `figures/` directory of the experiment repo
into `gfx/`.

### TikZ / PGFPlots for inline figures

For data-driven plots that should match the document font, use
`pgfplots` with CSV data. The `fill between` plot needs the
`fillbetween` library in the preamble (see "Required packages"):

```latex
\begin{figure}[t]
  \centering
  \definecolor{mpl_blue}{HTML}{1F77B4}
  \begin{tikzpicture}
    \begin{axis}[
      width=\columnwidth,
      height=4cm,
      xlabel={Time},
      ylabel={<quantity> [<unit>]},
      date coordinates in=x,
    ]
      \addplot[color=mpl_blue, line width=0.8pt]
        table[x=time, y=median, col sep=comma] {csv/<series>.csv};
      \addplot[name path=up, draw=none]
        table[x=time, y=upper, col sep=comma] {csv/<series>.csv};
      \addplot[name path=lo, draw=none]
        table[x=time, y=lower, col sep=comma] {csv/<series>.csv};
      \addplot[fill=mpl_blue, fill opacity=0.25]
        fill between[of=up and lo];
    \end{axis}
  \end{tikzpicture}
  \caption{Median and 90\% interval of <quantity>.}
  \label{fig:<series>}
\end{figure}
```

### Figure file naming convention

```
<dataset>_<method>_<plot_type>.pdf
```

A figure names its own experiment, for example
`synth_baseline_contour.pdf` or `synth_baseline_calibration.pdf`.

## Phase 3: LaTeX writing

### Section structure

All papers follow the same canonical structure. Each section file
starts with its heading and label, for example
`\section{Introduction}\label{sec:introduction}` in
`tex/01_introduction.tex`:

```latex
\documentclass[journal]{IEEEtran}
\input{preamble.tex}

\begin{document}

\title{A Descriptive Title: Method for Application}

\author{...}
\maketitle

\begin{abstract}
  ...
\end{abstract}

\input{tex/01_introduction}
\input{tex/02_background}
\input{tex/03_method}
\input{tex/04_experiments}
\input{tex/05_results}
\input{tex/06_conclusion}
\input{tex/07_acknowledgments}

\printbibliography

\end{document}
```

### Labels and BibTeX keys

Label with `sec:`, `fig:` and `tab:` prefixes and reference with
`\Cref{...}`. BibTeX keys follow `author2023title`.

### Accepted acknowledgments patterns (`tex/07_acknowledgments.tex`)

```latex
\section*{Acknowledgments}

...
During the finalization of this paper, large language models (LLMs)
were used to optimize language and grammar.
```

## Phase 4: Build and compilation

### Primary build command

The engine follows the venue (Phase 5): `-lualatex` or `-pdf`.

```bash
latexmk -lualatex -shell-escape main.tex
latexmk -pdf main.tex
```

### Compile script template

Create `compile.sh` for one-command camera-ready build:

```bash
#!/bin/bash
set -eux
shopt -s nullglob  # an unmatched *.cls or *.bst expands to nothing

DEST="./final"
ENGINE="-lualatex"  # the venue build flag of Phase 5: -lualatex or -pdf

# Clean (latexmk -C removes only LaTeX output, never sources)
latexmk -C
rm -rf "$DEST"
mkdir -p "$DEST"
cp -r gfx *.bib *.cls *.bst "$DEST"  # venue class and style files
[ -d csv ] && cp -r csv "$DEST"

# Flatten document (replace \input{} with file contents)
latexdiff --flatten main.tex main.tex |
  sed '/^%DIF PREAMBLE EXTENSION/,/DIF END PREAMBLE EXTENSION/d' \
  > "$DEST/final.tex"

# Zip source
cd "$DEST"
zip -9r final_paper_src.zip *

# Compile, and add the .bbl before the cleanup can remove it
latexmk "$ENGINE" -shell-escape final.tex
zip -9 final_paper_src.zip final.bbl
latexmk -c

# Finalise
mv final.pdf "FINAL_PAPER.PDF"
```

## Phase 5: Venue-specific submission

### IEEE (IEEEtran)

- **Build:** `latexmk -lualatex -shell-escape`
- **Source package:** flattened `.tex` + `gfx/` + `csv/` (if
  present) + `.bib` + `.bbl`
- **Packages:** do not load `caption`: it conflicts with IEEEtran.
  Remove the `caption` and `subcaption` lines from the preamble
  (`subcaption` loads `caption`).
- **Keywords:** `\begin{IEEEkeywords}...\end{IEEEkeywords}`
- **Author bios:** `\begin{IEEEbiography}[<photo>]{<name>}...\end{IEEEbiography}` (camera-ready only)
- **Review:** `\IEEEpeerreviewmaketitle` for the anonymised review
  version. It needs the `peerreview` class option:
  `\documentclass[peerreview]{IEEEtran}`.

### Elsevier (elsarticle)

- **Build:** `latexmk -pdf`
- **Front matter:** `\begin{frontmatter}` with `\begin{abstract}`,
  `\begin{keyword}`, `\journal{...}`
- **Source package:** `.tex` + all figures + `.bib` + class file

### UAI (uai<year>)

- **Build:** `latexmk -pdf`
- **Accepted option:** `\documentclass[accepted]{uai<year>}`
- **Supplementary:** use `\onecolumn` after references for appendix
- **License:** signed PMLR license form required
- **Packaging:** `Paper.pdf` + `Supplementary Material.pdf`

### ICML (icml<year>)

- **Build:** `latexmk -pdf`
- **Options:** `\usepackage[accepted]{icml<year>}` for the camera-ready
  version. Without an option, the package builds the anonymous review
  version. The options can change each year.
- **Opening:** `\twocolumn[` for title block + abstract

### arXiv

- Use the same class file as the published version
- **Remove:** copyright notice, IEEE DOI, `\markboth` headers
- **Required:** source files for full compilation

## Key references

- IEEEtran documentation: https://www.ieee.org/conferences/publishing/templates.html
- Elsevier elsarticle: https://www.elsevier.com/researcher/author/packages/elsarticle-template.zip
- UAI style: provided by the conference each year
- ICML style: the author instructions of the current year on https://icml.cc/
- latexmk: https://mg.readthedocs.io/latexmk.html
- PGFPlots: https://pgfplots.sourceforge.net/
- An earlier paper that used the target class is the best reference
  for a venue: ask the user for one and copy its setup. Autonomous:
  use the class defaults without options and record the question
  (`dev-conventions`, "2. Asking and acting").

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: design principles, verification, review
  loop, code and documentation style.
- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
- **ml-project**: experiment repo layout, DVC pipeline, MLflow
  tracking, figure scripts.
- **python-dev**: Python project conventions and matplotlib figure
  patterns.
