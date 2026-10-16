---
name: org-beamer-presentation
description: >
  Author Beamer talks as Org mode files exported to LaTeX and PDF, in the
  user's sparse, figure-first style: metropolis-dark design, denote file
  names with a sidecar figure folder, global biblatex citations, headless
  export and page-by-page verification. Use when the user says
  slides, Folien, Vortrag, talk or Beamer, or when an `.org` file with
  `#+LATEX_CLASS: beamer` changes.
license: MIT
compatibility: claude-code opencode
metadata: {stack: org-mode latex beamer, requires: [dev-conventions, git-conventions]}
---

# Skill: Org mode Beamer presentations

A presentation is one Org file plus a sidecar folder of figures.
`org-beamer-export-to-pdf` (`C-c C-e l P`) writes the `.tex` and the
`.pdf` next to it. Fewer words make a better deck. The figures carry the
message.

## Hard rules

- Budget: at most one frame per minute of talk. A talk of 15 minutes or
  less has no section, TOC or agenda frames. A longer talk may use the
  section TOC stanza from `templates/header-extras.org`. One closing
  frame is allowed. No appendix unless the user asks for one.
- Figure first. A figure frame has at most 2 lines, each at most 12
  words. A text frame has at most 3 bullets, each at most 2 lines at
  full width. Never put more than 2 text-only frames in a row.
- A title has at most 8 words, a plain statement. No marketing, no
  teasers, no punch lines.
- Colours: theme foreground plus one accent. One colour per meaning:
  the same dataset has the same colour on every frame.
- Show at most 2 examples, the two with the largest contrast.
- No semicolons, arrow characters in text, one-item lists or version
  history. Show the current state only.
- No overlay reveals of text or punch lines. A step-by-step build of one
  figure with its math (`\multiinclude`, `<2->`) is allowed when the user
  asks for an animation.
- No rhetorical bold lead-ins and no bold on conclusions. Field labels in
  an entity grid (for example `*Idea:*`, `*Status:*`) stay bold.
- Never invent content. Mark schematic numbers as schematic on the
  slide. No code or math for a non-specialist audience. Spell out
  jargon.
- When content does not fit, cut it or split the frame. Never shrink
  fonts, spacing or figures to make it fit.

## 1. Before writing

Read two or three of the user's earlier decks in `<presentations dir>`,
the newest first, plus one of the same talk type. Their density is the
target: about 20 words per frame, one figure and 1 or 2 short bullets.

Ask for the talk length and the audience when the request does not
state them. Autonomous default (see `dev-conventions`, "5. Interactive
and autonomous sessions"): 15 minutes, specialist audience, slug from
`#+title:`, tag `presentation`. Calculate the frame budget from the length.

## 2. Design

Use metropolis-dark. `templates/header.org` carries it as the active
stanza. Use Szeged/dolphin or SimplePlus only when the user asks for
them. The other two stanzas in the header show the lines to change.
SimplePlus is not part of TeX Live. The user installs it from
`github.com/pm25/SimplePlus-BeamerTheme` and puts it on `TEXINPUTS`
(stanza "Local package on TEXINPUTS" in `header-extras.org`).

The header is bare. `templates/header-extras.org` holds the optional
stanzas, each with its trigger. Add a stanza only when a frame needs it.
`templates/layouts.org` holds the frame layouts. Read it before you write
a frame.

## 3. Structure, files, citations, export

**Structure.** `#+OPTIONS: H:2`: `* Section` groups frames, `** Title` is
one frame, `***` headings are columns or blocks inside the frame. The
title frame comes from `#+title:`, `#+subtitle:` and `#+author:`.
Order the deck for a listener without prior knowledge. Introduce each
model, data set and setup before its results. Add one step of
complexity per frame. A frame is mostly figure or mostly text. For a
figure beside text, use a 0.55/0.45 or 0.5/0.5 column split with the
figure on the left. Text does not repeat numbers that the figure
shows. Use `:noexport:` to park a frame. Lines that start with `# `
inside a frame are the user's speaker prose: do not change them. A
German deck writes ß, not ss.

**Scope.** The hard rules apply to talks. An internal fact deck that
the user asks for is exempt from the time budget and may hold up to 6
bullets per frame. Every deck is self-contained with its own sidecar
folder. Copy a figure from another deck when necessary.

**File name.** Denote convention, in the presentations directory:

```
<YYYYMMDDTHHMMSS>--<title-slug>__<tag1>_<tag2>.org
<YYYYMMDDTHHMMSS>--<title-slug>__<tag1>_<tag2>/      sidecar folder
```

The identifier matches `#+identifier:`, the tags match `#+filetags:`.
Ask the user for slug and tags (autonomous default in section 1). Put
figures in the sidecar folder as vector PDF where possible, and set
`\graphicspath` to it. Never edit the `.tex`.

**Citations.** `#+CITE_EXPORT: biblatex ieee`, cited as `[cite:@Key]`.
Use the global `org-cite-global-bibliography` only, never a per-talk
`.bib`. A figure from a paper names its source in the caption.

**Numbers from data.** Read numbers from a data file in the sidecar with
a `#+MACRO` (stanza in `header-extras.org`) and write
`{{{num(model.auc)}}}` in the text. Never generate an Org file from
another Org file.

**Export in the agent sandbox.** `emacs` and `lualatex` are not on
`PATH`. Use `<test rig>`. Put TeX
first, so that its `kpsewhich` wins:

```bash
export PATH=<test rig>/tex/bin/x86_64-linux:<test rig>/env/bin:$PATH
```

If `<test rig>/env/bin/emacs` does not start, run `<test rig>/rig setup`.
`<test rig>/rig tex` reinstalls TeX Live. Then:

```bash
emacs -Q --batch -l org -l ox-beamer \
  --eval '(setq enable-local-variables :all
                org-latex-remove-logfiles nil
                org-latex-packages-alist
                (quote (("" "xcolor" t)
                        ("AUTO" "polyglossia" t ("xelatex" "lualatex"))))
                org-latex-pdf-process
                (list "latexmk -f -pdf -%latex -interaction=nonstopmode \
                       -output-directory=%o %f"))' \
  "<file>.org" -f org-beamer-export-to-pdf
```

When the export fails, or before frames with code, tables, math or
generated figures, read `reference/pitfalls.md`.

## 4. Verification

Run these with the `PATH` of section 3 (`<test rig>`). Tool paths are
relative to this skill's directory. A clean log does not prove a
correct deck. Do steps 1 to 4 after each build. Do step 5 once, before
you report.

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

In each review round whose range changes a deck, add these views to
those in `dev-conventions`, "4.3 Reviewers":

- Density and budget: frame count, words per frame, text-only runs.
- Consistency with the user's style: tone, titles, colours, the decks
  in section 1.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `skill` tool to load them before using this one:

- **dev-conventions**: autonomous defaults and the review loop.
- **git-conventions**: commits when the deck lives in a tracked repo.
