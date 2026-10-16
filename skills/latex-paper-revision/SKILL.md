---
name: latex-paper-revision
description: >
  LaTeX paper revision workflow: structural analysis, content generation,
  language polishing, figure/table integration, final cleanup, latexdiff
  and the response to reviewers. Use when the user asks to revise,
  polish or resubmit an existing LaTeX draft, or to answer reviewer
  comments. A new paper follows paper-writing.
license: MIT
compatibility: claude-code opencode
metadata: {stack: latex, requires: [paper-writing]}
---

# Skill: LaTeX Paper Revision and Enhancement

A structured workflow to revise, polish and enhance academic papers
or reports written in LaTeX.

Every number, result and citation in new text comes from data or
sources the user provided. Never invent one. Mark a gap with
`\TODO{...}` instead. The build and check commands are in
`paper-writing` ("Phase 4: Build and compilation").

## Phase 1: Initial Analysis and Structural Setup

Goal: understand the scope of the paper and find high-level
structural improvements.

1. **Full Document Read:**
   - Read the main `.tex` file (for example `main.tex`) and each file
     it includes.
   - Assess the overall structure, argumentation flow and
     completeness.
   - Identify the main sections: Abstract, Introduction, Methodology,
     Results, Discussion, Conclusion.

2. **Identify Missing Information:**
   - Scan the document for placeholders, missing values or incomplete
     sections (for example "xx", "...", comments like
     `% Add figure here`).
   - Define a `\TODO{}` macro in the preamble if none exists.
   - Insert `\TODO{...}` markers for all missing information.

## Phase 2: Content Generation and Integration

Goal: turn raw data and results into clear, scientifically sound text.

1. **Interpret Data and Results:**
   - Analyse the trends, comparisons and significant findings in the
     data the user provided (tables of metrics, numerical outputs).

2. **Draft Results Section:**
   - Insert a new subsection or replace a `\TODO{}` marker.
   - Write concise, objective descriptions. Refer to tables and
     figures with `\ref{}` or `\autoref{}`.

3. **Integrate Figures and Tables:**
   - Use the standard LaTeX environments (`figure`, `table`).
   - Give each a descriptive `\caption{}` and a unique `\label{}`.
   - Use `booktabs` for tables.

## Phase 3: Language Polishing and Structural Refinement

Goal: improve the language and make the formatting consistent.

1. **Proofread and Polish Language:**
   - Review each section for clarity, conciseness, scientific tone
     and grammar.
   - Make targeted edits. Rewrite a full section only when more than
     half of it changes.

2. **Enhance Structure and Flow:**
   - Assess the transitions between sections.
   - Add subsections or reorder content where the argument needs it.
   - Keep terminology and notation consistent.

3. **Final Review and Cleanup:**
   - Synchronise Abstract, Research Highlights and Conclusion with
     the main findings.
   - Remove leftover comments, outdated `\TODO{}` markers and
     redundant information.
   - Compile, and check that the log has no undefined references or
     citations and that `pdftotext main.pdf - | grep -c '??'`
     prints 0.

## Phase 4: Revision cycle

Use this phase when a revised version goes back to a venue.

### latexdiff for change tracking

Compare the revised version against the submitted one:

```bash
latexdiff original.tex revised.tex > diff.tex
latexmk -pdf diff.tex
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

### Changelog

Keep a `changelog.txt` with the major changes between versions:

```
v1: initial submission
v2: revised, expanded method section, added Experiment 3,
    updated figures 2 to 4
```

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **paper-writing**: LaTeX project layout, build and compilation,
  venue-specific submission.
