---
name: paper-writing
description: >
  End-to-end academic paper writing workflow for probabilistic ML research:
  LaTeX project scaffolding, figure generation, writing with
  IEEE/Elsevier/UAI templates, build, and venue submission. Use when
  the user asks to start, write, build or submit a paper. The
  experiment code follows ml-project. A revision of an existing draft follows
  latex-paper-revision.
license: MIT
compatibility: claude-code opencode
metadata: {stack: ml latex, audience: researchers, requires: [git-conventions, python-dev, ml-project]}
---

# Skill: Paper Writing

Load this skill to write a new academic paper: from the finished
experiments through figures, LaTeX writing and the camera-ready
submission. For a revision, use `latex-paper-revision`.

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
├── tex/ or sections/         # Section files
│   ├── 01_introduction.tex
│   ├── 02_method.tex
│   ├── 03_experiments.tex
│   ├── 04_results.tex
│   └── 05_conclusion.tex
├── gfx/ or figures/          # Figures (PDF, PNG, TikZ)
├── csv/                      # Data files for PGFPlots
├── tikz/                     # TikZ figure sources
└── response_to_reviewers.tex # Revision response (optional)
```

### Common document classes by venue

| Venue          | Class                           | Options                              |
|----------------|----------------------------------|--------------------------------------|
| IEEE           | `IEEEtran`                       | `[journal,dvipsnames]`               |
| Elsevier       | `elsarticle`                     | `[final,5p,times,twocolumn]`         |
| UAI            | `uai2025` (custom class file)    | `[accepted]` or blank                |
| ICML           | `article` + `icml2021` package   | `[accepted]` or blind for review     |
| arXiv          | same as main class               | remove copyright lines               |

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

% ---- tables ----
\usepackage{booktabs, multirow, array}

% ---- hyperlinks ----
\usepackage[colorlinks=true, citecolor=blue, linkcolor=blue, urlcolor=blue]{hyperref}
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
\DeclareMathOperator{\Be}{Be}
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
`\printbibliography`. For Elsevier, use `bibtex` with the
`elsarticle-num` style, and remove the `biblatex` block from the
preamble. The two cannot be loaded together:

```latex
\bibliographystyle{elsarticle-num}
\bibliography{mybibfile}
```

### Acronyms (`glossaries.tex`)

```latex
\newacronym{BNF}{BNF}{Bernstein normalizing flow}
\newacronym{CTM}{CTM}{conditional transformation model}
\newacronym{NF}{NF}{normalizing flow}
\newacronym{MLE}{MLE}{maximum likelihood estimation}
\newacronym{CRPS}{CRPS}{continuous ranked probability score}
\newacronym{NLL}{NLL}{negative log-likelihood}
\newacronym{GMM}{GMM}{Gaussian mixture model}
```

Use in text: `\gls{BNF}` (first use expands full form), `\glspl{BNF}`
(plural), `\acrfull{BNF}` (always full form).

## Phase 2: Figure generation

### Python → PDF → LaTeX workflow

Generate publication-quality figures in Python and include the
resulting PDF in LaTeX. Figure scripts follow `python-dev`
("Figures"). `ml-project` says where the scripts and figures live.

### TikZ / PGFPlots for inline figures

For data-driven plots that should match the document font, use
`pgfplots` with CSV data:

```latex
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{pgfplots.dateplot, pgfplots.fillbetween}

\begin{figure}[t]
  \centering
  \definecolor{mpl_blue}{HTML}{1F77B4}
  \begin{tikzpicture}
    \begin{axis}[
      width=\columnwidth,
      height=4cm,
      xlabel={Time},
      ylabel={Load [kW]},
      date coordinates in=x,
    ]
      \addplot[color=mpl_blue, line width=0.8pt]
        table[x=time, y=median, col sep=comma] {csv/forecast.csv};
      \addplot[fill=mpl_blue, fill opacity=0.25]
        table[x=time, y=lower, col sep=comma] {csv/forecast.csv}
        \closedcycle;
    \end{axis}
  \end{tikzpicture}
  \caption{Probabilistic forecast with 90\% prediction interval.}
  \label{fig:forecast}
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

All papers follow the same canonical structure:

```latex
\input{preamble.tex}

\begin{document}

\title{A Descriptive Title: Method for Application}

\author{...}
\maketitle

\begin{abstract}
  ...
\end{abstract}

\section{Introduction}
\label{sec:introduction}
...

\section{Background}
\label{sec:background}
...

\section{Method}
\label{sec:method}
...

\section{Experiments}
\label{sec:experiments}
...

\section{Results}
\label{sec:results}
...

\section{Conclusion}
\label{sec:conclusion}
...

\section*{Acknowledgments}
...

\printbibliography

\end{document}
```

### Writing workflow

1. **Draft**: write each section as a separate file in `tex/` with
   numbered filenames (`01_introduction.tex`, `02_method.tex`, ...).
2. **Cross-references**: use `\label{sec:...}`, `\label{fig:...}`,
   `\label{tab:...}` consistently. Reference with `\Cref{...}` or
   `\autoref{...}`.
3. **Placeholders**: mark incomplete sections with `\TODO{...}` for
   easy grep before submission.
4. **Bibliography**: keep a single `references.bib`. Add entries
   as you write, using BibTeX keys like `author2023title`.
5. **Glossaries**: define acronyms once in `glossaries.tex` and use
   `\gls{}` throughout.

### Accepted acknowledgments patterns

```latex
\section*{Acknowledgments}

...
During the finalization of this paper, large language models (LLMs)
were used to optimize language and grammar.
```

## Phase 4: Build and compilation

### Primary build command

```bash
latexmk -lualatex -shell-escape main.tex
```

For pdflatex-based projects:

```bash
latexmk -pdf main.tex
```

### Compile script template

Create `compile.sh` for one-command camera-ready build:

```bash
#!/bin/bash
set -eux

DEST="./final"

# Clean and prepare (latexmk -C removes only LaTeX output, never sources)
latexmk -C
rm -rf "$DEST"
mkdir -p "$DEST"
cp -r gfx csv *.bib "$DEST"

# Flatten document (replace \input{} with file contents)
latexdiff --flatten main.tex main.tex |
  sed '/^%DIF PREAMBLE EXTENSION/,/DIF END PREAMBLE EXTENSION/d' \
  > "$DEST/final.tex"

# Zip source
cd "$DEST"
zip -9r final_paper_src.zip *

# Compile, and add the .bbl before the cleanup can remove it
latexmk -lualatex -shell-escape final.tex
zip -9 final_paper_src.zip final.bbl
latexmk -c

# Finalise
mv final.pdf "FINAL_PAPER.PDF"
```

## Phase 5: Venue-specific submission

### IEEE (IEEEtran)

- **Build:** `latexmk -lualatex -shell-escape`
- **Source package:** flattened `.tex` + `gfx/` + `csv/` + `.bib` + `.bbl`
- **Keywords:** `\IEEEkeywords{...}`
- **Author bios:** `\IEEEbiography{...}` (camera-ready only)
- **Review:** `\IEEEpeerreviewmaketitle` for anonymised review version

### Elsevier (elsarticle)

- **Build:** `latexmk -pdf` (uses `bibtex` backend, not `biber`)
- **Front matter:** `\begin{frontmatter}` with `\begin{abstract}`,
  `\begin{keyword}`, `\journal{...}`
- **Bibliography:** `\bibliographystyle{elsarticle-num}` +
  `\bibliography{...}`
- **Source package:** `.tex` + all figures + `.bib` + class file

### UAI (uai2025)

- **Build:** `latexmk -pdf`
- **Accepted option:** `\documentclass[accepted]{uai2025}`
- **Supplementary:** use `\onecolumn` after references for appendix
- **License:** signed PMLR license form required
- **Packaging:** `Paper.pdf` + `Supplementary Material.pdf`

### ICML (icml2021)

- **Build:** `latexmk -pdf`
- **Options:** `\usepackage[accepted]{icml2021}` or blind for review
- **Anonymised:** use `[blind]` option during review phase
- **Opening:** `\twocolumn[` for title block + abstract

### arXiv

- Use the same class file as the published version
- **Remove:** copyright notice, IEEE DOI, `\markboth` headers
- **Required:** source files for full compilation

## Key references

- IEEEtran documentation: https://www.ieee.org/conferences/publishing/templates.html
- Elsevier elsarticle: https://www.elsevier.com/researcher/author/packages/elsarticle-template.zip
- UAI 2025 style: provided by conference
- ICML style: https://icml.cc/Conferences/2021/StyleAuthorInstructions
- latexmk: https://mg.readthedocs.io/latexmk.html
- PGFPlots: https://pgfplots.sourceforge.net/
- An earlier paper that used the target class is the best reference
  for a venue: ask the user for one and copy its setup.

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions**: two-branch flow, conventional commits,
  pre-commit hooks, tagging and releases.
- **python-dev**: Python project structure, pyproject.toml, ruff,
  NumPy docstrings, pytest, figures.
- **ml-project**: DVC pipeline orchestration, MLflow experiment
  tracking, HPO study logs, per-target configs, figure generation.
