---
name: tax-return-de
description: >
  Prepare the documents for a German income tax return
  (Einkommensteuererklärung) of an employee: collect receipts from the
  mail archive, payment provider mails and booking mails, check them
  against the employer's reimbursements, ask for the facts that no
  receipt shows, build one overview per year from a LaTeX template
  that follows the checklist, and stage the folders for an upload
  portal such as DATEV MyTax. Use when the user says Steuer,
  Steuererklärung, Belege, Werbungskosten, DATEV or Steuerberater, or
  asks what is missing for a tax year.
license: MIT
compatibility: claude-code
metadata: {stack: tax latex, requires: [dev-conventions]}
---

# Skill: German Tax Return Documents

The skill collects and orders documents. It does not give tax advice
and does not file the return. Values that change by year (allowances,
rates, deadlines) are in `reference.md`; read it before you estimate
amounts. The checklist and the LaTeX templates are in `templates/`,
relative to this skill directory.

## Hard rules

- Never write tax documents into a git repository or a synced folder.
  Work in a scratch folder the user names, and delete it, and every
  temporary copy of attachments, when the user agrees at the end.
- Read the mail read only. Never move, delete or send mail. Report
  misfiled mails as a list for the user.
- Open each receipt before you count it. A shop name says nothing:
  novels, leisure trips and private subscriptions are not deductible.
- Check the employer's travel reimbursements (Reisekostenabrechnung)
  before you count a business trip. A reimbursed trip is not
  deductible; only a difference to the legal allowances is.
- A donation counts only when the receiver is a tax-privileged
  organisation (gemeinnützig). Sponsoring a person or paying a company
  is no donation.
- Ask the user for every fact that no document shows: family status,
  addresses and moving dates, first workplace, commute days, home
  office days. Mark estimates as estimates in the overview.
- The overview for the advisor holds no internal notes, no source
  remarks ("from the calendar", "check this") and no refund estimate.
- Render every generated PDF to an image and look at it before you
  hand it over.

## 1. Scope

Ask which tax years, which employers, and whether an advisor or a
portal gets the documents. The voluntary return for a year is due four
years after its end (`reference.md`): name the oldest open year first.

## 2. Collect

1. List the mail folders. Fetch the headers of all mail since the
   first open year into one table (date, sender, subject, folder, id);
   page through large folders and save each page to a file.
2. Filter the table per year with keywords: Rechnung, Invoice,
   Receipt, Beleg, Quittung, Bescheinigung, Steuer, Spende,
   Zuwendungsbestätigung, Beitrag, Police, Abrechnung,
   Buchungsbestätigung. Group by sender domain to find the vendors.
3. Payment provider receipts ("Beleg für Ihre Zahlung an …") name the
   payee. Read the receipts without a payee in the subject; a
   sub-agent can extract payee, amount and purpose into one table.
4. Rail and travel bookings: the booking mail holds route, date and
   price. Tickets often come as an attached PDF in the raw source only.
5. Employer mails: search Reisekosten, Reisekostenabrechnung,
   Dienstreise. List every reimbursed trip.
6. The calendar shows the days at the workplace, the business trips
   and the moving date. Use it for the commute and home office
   estimates, not as a receipt.
7. Search the advisor's earlier mails for a checklist and use its
   order. `templates/checkliste.md` is the generic fallback.

Attachments: a mail client tool may save attachments in a folder the
sandbox cannot see. Then read the raw message source and decode the
PDF parts with Python's `email` package (run Python with `-I`).

## 3. Classify

Sort every item into the checklist sections: income, commute, public
transport, home office, work equipment and software, literature,
further training, moving, travel (reimbursed or not), capital income,
insurance, donations, household services. For each year, list:

- what is there, with date, vendor and amount,
- what is missing and where the user can get it (customer account,
  portal, bank),
- the questions only the user can answer.

Show this per year and wait. Apply the user's rules (for example
"every trip from the workplace town counts") and write them into the
overview's assumptions, not into chat only.

## 4. Overview per year

Copy `templates/uebersicht.tex` per year and fill it. Its sections
follow the checklist: general data, employment income, expenses
(summary first, then commute, public transport, home office, work
equipment, moving, reimbursed trips, not applicable), capital income,
special expenses, household services. Copy `templates/fahrtkosten.tex`
when a year has more than three tickets.

- Build with `pdflatex` (packages: geometry, helvet, booktabs,
  tabularx, xcolor). Write `EUR` for €, `$\times$` for ×, `--` for −;
  T1 encoding has no glyph for them.
- Keep each year on at most two pages. Add `\nopagebreak` after a
  section heading so it stays with its table.
- Recompute every sum from the item rows and compare it with the
  receipts. Summary, section sums and file names must agree.

## 5. Stage the upload

Create one folder per year with the portal's categories (DATEV MyTax:
`Employee`, `Investments`, `Insurance policies`,
`Special expenses & donations`, …). Put the overview first as
`00_Uebersicht_<year>.pdf`. Name receipts
`YYYY-MM-DD_vendor_number.pdf`. Leave out what the overview does not
claim, for example insurance documents when the cap is reached.

Then draft the cover mail to the advisor in a code block: the years,
the folder layout, the totals, and the open points (estimates,
borderline items, missing certificates). The user sends it.

## 6. Finish

Ask before you delete the scratch folder. Point the user to temporary
attachment folders you cannot reach. Record the follow-ups in the
user's agenda (`gtd` skill, "1. Capture"): missing certificates,
misfiled mails, the deadline of the oldest year.

---

## Required skills

This skill assumes the following prerequisite skills are loaded.
Use the `Skill` tool (opencode: `skill`) to load them before using this one:

- **dev-conventions**: asking and acting, verification by looking,
  documentation style.
