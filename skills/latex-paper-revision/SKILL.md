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

## Phase 1: Initial Analysis and Structural Setup

1. **Identify Missing Information:**
   - Scan the document for placeholders, missing values or incomplete
     sections (for example "xx", "...", comments like
     `% Add figure here`).
   - If the preamble has no `\TODO{}` macro, add the one from
     `paper-writing` ("TODO macros").
   - Insert `\TODO{...}` markers for all missing information.

## Phase 2: Content Generation and Integration

1. **Draft Results Section:**
   - Insert a new subsection or replace a `\TODO{}` marker.

2. **Integrate Figures and Tables:**
   - Figures, tables, labels and `\Cref` follow `paper-writing`
     ("Labels and BibTeX keys").

## Phase 3: Language Polishing and Structural Refinement

1. **Proofread and Polish Language:**
   - Make targeted edits. Before you rewrite a section, estimate the
     share of sentences you will change. Above half, write a new
     version of the section instead.

2. **Enhance Structure and Flow:**
   - Add subsections or reorder content where the argument needs it.

3. **Final Review and Cleanup:**
   - Synchronise Abstract, Research Highlights and Conclusion with
     the main findings.
   - Remove leftover comments, outdated `\TODO{}` markers and
     redundant information.
   - Compile and check the log as `paper-writing` ("Hard rules")
     says.

## Phase 4: Revision cycle

Use this phase when a revised version goes back to a venue.

### latexdiff for change tracking

When the user says the paper is submitted, tag the commit
`submitted-<venue>-<YYYYMMDD>`. The diff base is the newest such tag.
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
