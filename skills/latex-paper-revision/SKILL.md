---
name: latex-paper-revision
description: >
  LaTeX paper revision workflow: structural analysis, content generation,
  language polishing, figure/table integration, and final cleanup.  Use
  when revising an existing draft; a new paper follows paper-writing.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: latex
---

# Skill: LaTeX Paper Revision and Enhancement

This skill provides a structured workflow for revising, polishing, and
enhancing academic papers or reports written in LaTeX.

Every number, result and citation in new text comes from data or
sources the user provided.  Never invent one; mark a gap with
`\TODO{...}` instead.  Build and check commands are in the
`paper-writing` skill, Phase 4.

## Phase 1: Initial Analysis and Structural Setup

Goal: Understand the paper's scope and identify high-level structural
improvements.

1.  **Full Document Read:**
    -   Use `Read` to load the main `.tex` file (e.g., `main.tex`).
    -   Assess the overall structure, argumentation flow, and completeness.
    -   Identify the main sections: Abstract, Introduction, Methodology,
        Results, Discussion, Conclusion.

2.  **Identify Missing Information (Macro Insertion):**
    -   Scan the document for placeholders, missing values, or incomplete
        sections (e.g., "xx", "...", comments like `% Add figure here`).
    -   Define a `\TODO{}` macro in the preamble if one does not exist.
    -   Use `Edit` to insert `\TODO{...}` markers for all missing information.

## Phase 2: Content Generation and Integration

Goal: Turn raw data and results into clear, scientifically sound text.

1.  **Interpret Data and Results:**
    -   Analyze key trends, comparisons, and significant findings from
        provided data (tables of metrics, numerical outputs).

2.  **Draft Results Section:**
    -   Use `Edit` to insert a new subsection or replace a `\TODO{}` marker.
    -   Formulate concise, objective descriptions. Refer to tables and
        figures using `\ref{}` or `\autoref{}`.

3.  **Integrate Figures and Tables:**
    -   Use standard LaTeX environments (`figure`, `table`).
    -   Ensure each has a descriptive `\caption{}` and a unique `\label{}`.
    -   Use `booktabs` for professional table formatting.

## Phase 3: Language Polishing and Structural Refinement

Goal: Elevate manuscript quality through professional language and
consistent formatting.

1.  **Proofread and Polish Language:**
    -   Review section-by-section for clarity, conciseness, scientific
        tone, and grammar.
    -   Use targeted `Edit` calls; rewrite entire sections for large
        revisions.

2.  **Enhance Structure and Flow:**
    -   Assess logical transitions between sections.
    -   Introduce new subsections or reorder content as needed.
    -   Ensure consistent terminology and notation.

3.  **Final Review and Cleanup:**
    -   Synchronise Abstract, Research Highlights, and Conclusion with
        main findings.
    -   Remove leftover comments, outdated `\TODO{}` markers, and
        redundant information.
    -   Verify all cross-references and citations resolve correctly.
    -   Compile, and check that the log has no undefined references or
        citations and that `pdftotext main.pdf - | grep -c '??'`
        prints 0.
