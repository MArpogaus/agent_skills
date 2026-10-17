---
name: latex-paper-revision
description: >
  LaTeX paper revision workflow: structural analysis, content generation,
  language polishing, figure/table integration, final cleanup, latexdiff
  and the response to reviewers. A new paper follows paper-writing.
  Use when the user asks to revise, polish or resubmit an existing
  LaTeX draft, or to answer reviewer comments.
license: MIT
compatibility: claude-code opencode
metadata: {stack: latex, requires: [paper-writing]}
---

# Skill: LaTeX Paper Revision and Enhancement

New text follows the rule on numbers, results and citations in
`paper-writing` ("Hard rules"). The build commands are in
`paper-writing` ("Phase 4: Build and compilation").

## 1. Revision

1. Mark each placeholder, missing value or incomplete section (for
   example "xx", "...", `% Add figure here`) with `\TODO{...}`. If the
   preamble has no `\TODO{}` macro, add the one from `paper-writing`
   ("TODO macros").
2. Figures, tables, labels and `\Cref` follow `paper-writing`
   ("Labels and BibTeX keys").
3. Before you rewrite a section, estimate the share of sentences you
   will change. Above half, write a new version of the section.
4. Before hand-back, synchronise Abstract, Research Highlights and
   Conclusion with the main findings. Remove leftover comments and
   outdated `\TODO{}` markers. Compile as `paper-writing` ("Hard
   rules") says.

## 2. Revision cycle

Use this section when a revised version goes back to a venue.

### latexdiff for change tracking

When the user says the paper is submitted, tag the commit
with an annotated tag: `git tag -a submitted-<venue>-<YYYYMMDD> -m
"Submitted to <venue>"`. The diff base is the newest such tag.
`--flatten` follows the `\input` files of both versions. `<engine>` is
the build flag of the venue (`-lualatex` or `-pdf`):

```bash
latexdiff-vc --git --flatten -r <tag> main.tex   # writes main-diff<tag>.tex
latexmk <engine> -shell-escape main-diff<tag>.tex
```

The output shows additions in blue underline and deletions in red
strikethrough.

### Response to reviewers

Write `response_to_reviewers.tex` as a standalone LaTeX document:

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

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **paper-writing**: LaTeX project layout, build and compilation,
  venue-specific submission.
