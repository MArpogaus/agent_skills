---
name: org-beamer-presentation
description: >
  Author Beamer talks as Org mode files exported to LaTeX and PDF, in the
  user's sparse, figure-first style.  Hard rules: at most one frame per
  minute, figure frames with at most two short lines, at most four short
  bullets on a text frame, theme colours only, no overlays, no marketing,
  cut or split instead of shrinking.  Covers the default metropolis-dark
  design, denote file naming with a sidecar figure folder, global biblatex
  citations, headless export and page-by-page verification.  Use when
  making or revising a slide deck.
license: MIT
compatibility: claude-code opencode
metadata:
  stack: org-mode latex beamer
  requires:
    - git-conventions
---

# Skill: Org mode Beamer presentations

A presentation is one Org file plus a sidecar folder of figures.
`org-beamer-export-to-pdf` (`C-c C-e l P`) writes the `.tex` and the
`.pdf` next to it. Fewer words make a better deck. The figures carry the
message.

## 1. Hard rules

- Budget: at most one frame per minute of talk.
- A talk of 15 minutes or less has no section, TOC or agenda frames.
  A longer talk may use the section TOC stanza from
  `templates/header-extras.org`.  One closing frame is allowed.  No
  appendix unless the user asks for one.
- Figure first. A figure frame has at most 2 lines of at most 12 words.
- A text frame has at most 4 bullets of at most 10 words. Never put more
  than 2 text-only frames in a row.
- Titles are short plain statements. No marketing, no teasers, no
  punch lines.
- Colours: theme foreground plus one accent. One colour per meaning:
  the same dataset has the same colour on every frame.
- Show at most 2 examples, the two with the largest contrast.
- No overlays, semicolons, arrows, one-item lists or version history.
  Show the current state only.
- Never invent content. Mark schematic numbers as schematic on the
  slide.
- No code or math for a non-specialist audience. Spell out jargon.
- When content does not fit, cut it or split the frame. Never shrink
  fonts, spacing or figures to make it fit.
- A collection of facts goes into a Denote note, not into a deck.
- Every deck is self-contained with its own sidecar folder. Copy a
  figure from another deck when necessary.

## 2. Before writing

Read 1 or 2 of the user's own decks in
`<presentations dir>/` and follow their tone:

- `<recent deck>.org`:
  the accepted model, about 20 words per frame, one figure and two short
  bullets.
- `<conference deck>.org`:
  a conference talk.
- `<older conference deck>.org`:
  a conference talk.
- `<workshop deck>.org`: a project workshop.

Ask for the talk length and the audience when the request does not
state them. Calculate the frame budget from the length.

## 3. Design

Use metropolis-dark. `templates/header.org` carries it as the active
stanza. Use Szeged/dolphin or SimplePlus only when the user asks for
them. The other two stanzas in the header show the lines to change.

The header is bare. `templates/header-extras.org` holds the optional
stanzas, each with its trigger. Add a stanza only when a frame needs it.
`templates/layouts.org` holds the frame layouts. Read it before you write
a frame.

## 4. Structure, files, citations, export

**Structure.** `#+OPTIONS: H:2`: `* Section` groups frames, `** Title` is
one frame, `***` headings are columns or blocks inside the frame. The
title frame comes from `#+title:`, `#+subtitle:` and `#+author:`. A
frame is mostly figure or mostly text. For a figure beside text, use a
0.55/0.45 or 0.5/0.5 column split with the figure on the left. Text does
not repeat numbers that the figure shows. Use `:noexport:` to park a
frame. Lines that start with `# ` inside a frame are the user's speaker
prose: do not change them. A German deck writes ß, not ss.

**File name.** Denote convention, in the presentations directory:

```
<YYYYMMDDTHHMMSS>--<title-slug>__<tag1>_<tag2>.org
<YYYYMMDDTHHMMSS>--<title-slug>__<tag1>_<tag2>/      sidecar folder
```

The identifier matches `#+identifier:`, the tags match `#+filetags:`.
Ask the user for slug and tags. Put figures in the sidecar folder as
vector PDF where possible, and set `\graphicspath` to it. Never edit the
`.tex`.

**Citations.** `#+CITE_EXPORT: biblatex ieee`, cited as `[cite:@Key]`.
Use the global `org-cite-global-bibliography` only, never a per-talk
`.bib`. A figure from a paper names its source in the caption.

**Numbers from data.** Read numbers from a data file in the sidecar with
a `#+MACRO` (stanza in `header-extras.org`) and write
`{{{num(model.auc)}}}` in the text. Never generate an Org file from
another Org file.

**Export in the agent sandbox.** `emacs` and `lualatex` are not on
`PATH`. Use the test rig in `<test rig>`. Put TeX first, so that its
`kpsewhich` wins:

```bash
export PATH=<test rig>/tex/bin:<test rig>/env/bin:$PATH
```

If `<test rig>/env/bin/emacs` does not start, run `<test rig>/rig setup`.
`<test rig>/rig tex` reinstalls TeX Live. Then:

```bash
emacs -Q --batch -l org -l ox-beamer \
  --eval '(setq enable-local-variables :all
                org-latex-remove-logfiles nil
                org-latex-packages-alist
                (quote (("" "xcolor" t) ("" "listings" t)
                        ("AUTO" "polyglossia" t ("xelatex" "lualatex"))))
                org-latex-pdf-process
                (list "latexmk -f -pdf -%latex -interaction=nonstopmode \
                       -output-directory=%o %f"))' \
  "<file>.org" -f org-beamer-export-to-pdf
```

When the export fails, or before frames with code, tables, math or
generated figures, read `reference/pitfalls.md`.

## 5. Verification

A clean log does not prove a correct deck. Do all steps after each
build:

1. Build the PDF. `pdftotext <file>.pdf - | grep -c '??'` prints `0`.
2. Count frames with `pdfinfo` and compare with the budget.
3. Run `tools/contact-sheet.py <file>.pdf <scratch>/sheet` and look at
   every page. `tools/box-pages.py <file>.log` maps overfull boxes to
   pages.
4. Check the semantics of each figure. Find its data source by file
   path. Check that axes, sides, labels and colours show what the text
   says.
5. Report a numbered list of problems, one line each, so the user can
   accept items by number.

For a review with subagents, give each reviewer one view:

- Density and budget: frame count, words per frame, text-only runs.
- Figure correctness and provenance: data source, axes, colours,
  legends.
- Consistency with the user's style: tone, titles, colours, the decks
  in §2.

## 6. Checklist

- [ ] Frame count is within the budget
- [ ] Every frame obeys the hard rules in §1
- [ ] Tone matches the user's decks in §2
- [ ] Filename, `#+identifier:` and `#+filetags:` agree, sidecar exists
- [ ] Header carries no package that the frames do not use
- [ ] Every number comes from a source, schematic numbers are marked
- [ ] PDF builds, no `??`, every page looked at
- [ ] Numbered problem list handed over

## Required skills

Load with the `skill` tool before acting on this one:

- `git-conventions`: when the presentation lives in a tracked repo and
  changes have to be committed.
