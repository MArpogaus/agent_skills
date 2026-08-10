---
name: paper-writing
description: >
  End-to-end academic paper writing workflow for probabilistic ML research:
  project scaffolding, DVC/MLflow experiment pipelines, figure generation,
  LaTeX writing with IEEE/Elsevier/UAI templates, revision cycles, and
  venue submission.
license: MIT
compatibility: claude-code opencode
metadata:
  requires:
    - git-conventions
    - python-dev
    - ml-project
  audience: researchers
  stack: ml+latex
---

## When to use

Load when writing or revising an academic paper — from experiment
completion through figure generation, LaTeX writing, revision cycles,
and camera-ready submission.

---

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
| arXiv          | same as main class               | anonymised, remove copyright lines   |

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

### Bibliography management

Prefer `biblatex` with `biber` backend:

```latex
% In preamble
\usepackage[style=ieee, backend=biber, natbib=true]{biblatex}
\addbibresource{references.bib}

% Where to print
\printbibliography
```

For Elsevier use `bibtex` with the `elsarticle-num` style:

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

---

## Phase 2: Figure generation

### Python → PDF → LaTeX workflow

Generate publication-quality figures in Python and include the
resulting PDF in LaTeX:

```python
"""scripts/plot_reliability.py"""

import matplotlib.pyplot as plt
import numpy as np


def plot_reliability(
    forecasts: np.ndarray,
    observations: np.ndarray,
    *,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot reliability diagram.

    Parameters
    ----------
    forecasts : np.ndarray
        Predictive samples, shape ``(n_samples, n_timesteps)``.
    observations : np.ndarray
        Observed values, shape ``(n_timesteps,)``.
    ax : plt.Axes | None, optional
        Matplotlib axes, by default ``None`` (creates new figure).

    Returns
    -------
    plt.Figure
        The figure object.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure
    # ... plotting logic ...
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    fig = plot_reliability(...)
    fig.savefig("figures/reliability_diagram.pdf", dpi=300)
    fig.savefig("figures/reliability_diagram.png", dpi=150)
    plt.close(fig)
```

### Colour palette for paper consistency

| Role | Colour |
|------|--------|
| Observed data | `#333333` |
| Predicted median | `#1f77b4` |
| Reference / perfect line | `#d62728` |
| Primary CI fill | `#1f77b4` with `alpha=0.25` |
| Secondary CI fill | `#2c8ad4` |
| Histogram bars | `steelblue` with white edge |

### TikZ / PGFPlots for inline figures

For data-driven plots that should match the document font, use
`pgfplots` with CSV data:

```latex
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{pgfplots.dateplot, pgfplots.fillbetween}

\begin{figure}[t]
  \centering
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

Examples: `moons_maf_contour.pdf`, `cer_bnf_calibration.pdf`.

---

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

1. **Draft** — Write each section as a separate file in `tex/` with
   numbered filenames (`01_introduction.tex`, `02_method.tex`, ...).
2. **Cross-references** — Use `\label{sec:...}`, `\label{fig:...}`,
   `\label{tab:...}` consistently. Reference with `\Cref{...}` or
   `\autoref{...}`.
3. **Placeholders** — Mark incomplete sections with `\TODO{...}` for
   easy grep before submission.
4. **Bibliography** — Keep a single `references.bib`. Add entries
   as you write, using BibTeX keys like `author2023title`.
5. **Glossaries** — Define acronyms once in `glossaries.tex` and use
   `\gls{}` throughout.

### Accepted acknowledgments patterns

```latex
\section*{Acknowledgments}

...
During the finalization of this paper, large language models (LLMs)
were used to optimize language and grammar.
```

---

## Phase 4: Build and compilation

### Primary build command

```bash
latexmk -lualatex -shell-escape main.tex
```

For pdflatex-based projects:

```bash
latexmk -pdf main.tex
```

### Clean build for final submission

```bash
git clean -xdf
latexmk -lualatex -shell-escape main.tex
latexmk -c
```

### Compile script template

Create `compile.sh` for one-command camera-ready build:

```bash
#!/bin/bash
set -eux

DEST="./final"

# Clean and prepare
git clean -xdf && git clean -Xdf
mkdir -p "$DEST"
cp -r gfx csv *.bib "$DEST"

# Flatten document (replace \input{} with file contents)
latexdiff --flatten main.tex main.tex |
  sed '/^%DIF PREAMBLE EXTENSION/,/DIF END PREAMBLE EXTENSION/d' \
  > "$DEST/final.tex"

# Zip source
cd "$DEST"
zip -9r final_paper_src.zip *

# Compile
latexmk -lualatex -shell-escape final.tex
latexmk -c

# Finalise
mv final.pdf "FINAL_PAPER.PDF"
zip -9 final_paper_src.zip final.bbl
```

---

## Phase 5: Revision cycle

### latexdiff for change tracking

Compare revised version against the original:

```bash
latexdiff original.tex revised.tex > diff.tex
latexmk -pdf diff.tex
```

Output shows additions in blue underlined and deletions in red
strikethrough.

### Response to reviewers

Structure as a standalone LaTeX document:

```latex
\documentclass[12pt]{article}
\usepackage[colorlinks]{hyperref}

\begin{document}

\section*{Response to Reviewers}

\subsection*{Reviewer 1}

\subsubsection*{Comment:}
...
\subsubsection*{Response:}
...

\subsection*{Reviewer 2}
...

\end{document}
```

### Changelog

Maintain a `changelog.txt` tracking major changes between
versions:

```
v1 — Initial submission
v2 — Revised: expanded method section, added Experiment 3,
     updated figures 2–4
```

---

## Phase 6: Venue-specific submission

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
- **Anonymise:** replace author names with placeholder
- **Required:** source files for full compilation

---

## Key references

- IEEEtran documentation: https://www.ieee.org/conferences/publishing/templates.html
- Elsevier elsarticle: https://www.elsevier.com/researcher/author/packages/elsarticle-template.zip
- UAI 2025 style: provided by conference
- ICML style: https://icml.cc/Conferences/2021/StyleAuthorInstructions
- latexmk: https://mg.readthedocs.io/latexmk.html
- PGFPlots: https://pgfplots.sourceforge.net/
- Existing paper examples:
  - `stplf-bnf` — IEEE TSG paper, latexdiff flatten, PGFPlots data plotting
  - `thermo-forecast-paper` — Elsevier elsarticle, revision cycle with latexdiff
  - `hybrid_flows_paper` — UAI 2025, TikZ overlays, supplementary material
  - `Sylaski_Manuscript` — Elsevier format, changelog tracking

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **git-conventions** — two-branch flow, conventional commits,
  pre-commit hooks, tagging/releases.
- **python-dev** — Python project structure, pyproject.toml, ruff,
  NumPy docstrings, pytest, matplotlib patterns.
- **ml-project** — DVC pipeline orchestration, MLflow experiment
  tracking, HPO study logs, per-target configs, figure generation.
