# Feedback coverage gaps

A living list of bullets in
`02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` (and any later
revisions) that **do not yet have a home** in the prompt set
(`03_prompts/`), a proposal (`04_proposals/`), or an investigation
report (`05_investigations/`).

**How to use this:**
- Add an item here when a feedback bullet is identified during audit
  and no existing brief covers it.
- Strike through / mark `[RESOLVED]` when the bullet gets folded into
  a brief or proposal. Don't delete — the trail matters.
- When writing a new Wave-C brief or INV report, scan this file first;
  every bullet you cover here moves to the brief's coverage table.

The CLAUDE.md "Cross-checking against the original feedback" rule
points at this file.

---

## Bucket A — Whole surfaces with no dedicated brief

### A-1 STOCK ITEM DETAIL polish

Feedback `§STOCK ITEM DETAIL` has ~30 bullets. The bug-shaped ones are
covered by B-prompts (B3 PATCH, B4 cascade, B8 dead actions). The
**layout / button-placement / open-design** bullets have no brief:

- [OPEN] Clear-expiry button affordance (cross mark next to expiry)
- [OPEN] No way to set "essential" — see also `INV-7` (added).
- [OPEN] No way to set stock group — surfaced UI question (entity exists; INV-1 catches the field, this is the UX side).
- [OPEN] Split-view at 50% default; sensible min/max splitter distance.
- [OPEN] Tabs hardly visible in some themes — likely A1 ripple but not explicitly scoped there.
- [OPEN] Stock-level shown twice — remove the duplicate next to name.
- [OPEN] Move delete button (bottom-left below tabs, or top-right inline).
- [OPEN] Restock here makes no sense — move to shopping-list finalisation.
- [OPEN] Move "Opened" button next to opened info; same for expiry.
- [OPEN] "Find deals" placement — move into Linked Products tab as a contextual CTA when empty.
- [OPEN] Overview single column tidier.
- [OPEN] Location updated inline without a separate dropdown.
- [OPEN] Notes value — `[INV-1]` orphaned-fields catches; the *worth* call separate.
- [OPEN] Add product-of-choice to shopping list (not just cheapest); per-product list-add buttons.
- [OPEN] Preferred merchant/product behaviour — `[INV-1]` catches existence; worth call open.
- [OPEN] Shopping-lists tab — "(primary)" plain text feels unimaginative; arrow icon non-clickable.
- [OPEN] History tab worth — see `INV-7` (added).
- [OPEN] Substitute swap-into-list weirdness — see `INV-8` (added).

**Recommended home:** a new Wave-C brief (`C-1 ripple` or a dedicated
`C-1b STOCK_ITEM_DETAIL` proposal). The C-1 brief currently mentions
"row click → detail" but doesn't redesign the detail surface itself.

### A-2 DATA page

Feedback `§DATA` has 10 bullets. Currently zero coverage in the
prompts or proposals.

- [OPEN] Move under Settings → "My Data" (not a top-level nav item).
- [OPEN] Multiple export formats (json, csv, …).
- [OPEN] Page formatting overhaul — margins, alignment, headings, font/type.
- [OPEN] Card layout with checkboxes.
- [OPEN] Drop the breadcrumb fluff ("Data / Backup & restore — Backup, import, export and barcode tools for your Dora data").
- [OPEN] Schema-driven import templates (download, fill, upload).
- [OPEN] Export & print tab utility — drop or rework.
- [OPEN] "Scan" tab under QR codes — useful here vs only on stock overview?
- [OPEN] "Barcodes & QR" → "QR codes" rename (paired with A8 rename trail and the P6-02 removal trail).
- [OPEN] Decide whether the optional/collapsed section should be the main view.

**Recommended home:** new Wave-C brief `C-DATA — Data Management
redesign`.

### A-3 DORA BOT (assistant chat) polish

Feedback `§DORA BOT` has 6 bullets, scattered across multiple owners:

- [OPEN] Text size not honouring user settings (a bug).
- [OPEN] Basic/AI chip squished/small.
- [OPEN] Make basic/AI chip a toggle slider (slanted thick, glow on slide).
- [OPEN] DS4 animation flashing on hover — regression to investigate.
- [OPEN] Don't show "Hi I'm Dora, click me…" every login (once-per-user acknowledge).
- [OPEN] Turn the bot off completely in settings.
- ~~[RESOLVED] D.O.R.A. acronym — covered by the 2026-06-05 acronym pass.~~

**Recommended home:** a small Wave-C brief or fold into the existing
`DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` as a UI-polish appendix.

### A-4 HELP content

Feedback `§HELP` has 5 bullets — all about content (detailed help per
feature, guides, FAQ, navigability, diagrams). No brief.

- [OPEN] Help content overhaul: detailed per-feature help, guides,
  FAQ, easy navigability, UI screenshots / diagrams.

**Recommended home:** content task, post-launch. Either a dedicated
`HELP_CONTENT_PLAN.md` proposal or fold into the existing HelpPage
implementation work.

### A-5 SETTINGS deferred bullets

Deferred area per master plan, but the bullets are actionable.

- [OPEN] Theme **type** (system / light / dark) separated from theme
  **identity** (pesto, lemon, …) — two dropdowns, not coloured
  light/dark buttons on each theme card.
- [OPEN] Profile picture — set/update; surface on the menu-bar avatar.

**Recommended home:** small additions to a deferred-Settings polish
prompt (or fold into Wave A theme work).

---

## Bucket B — Open assessment-style questions

Bullets phrased "is this worth it / should we keep / let's assess".
These map cleanly to INV prompts.

- [OPEN] **History tab worth** on stock item detail. Added as `INV-7`.
- [OPEN] **Substitute swap-into-list** behaviour. Added as `INV-8`.
- [OPEN] **Command palette assess** — "How useful really? Let's assess." Added as `INV-9`.
- [OPEN] **`essential` flag** on stock items — UI + value. Added as `INV-10`.

---

## Bucket C — Cross-cutting / niche / future

No clean per-surface home; mostly future or "nice-to-have".

- [OPEN] **Full systems QA test document** — manual walkthrough of every feature for final regression. The user wants this done last so it captures the final product. No plan yet; add when the implementation waves are mostly done.
- [OPEN] **Usage analytics / telemetry** — "I'd like to know how people are using my app." Privacy-conscious approach needed (Charter P8).
- [OPEN] **UI uniqueness / polish design pass** — "looks just okay, not polished/unique." Cross-cutting.
- [OPEN] **Push notifications between users** (new-feature idea — alert another user, share a shopping list via notify).
- [OPEN] **Kivy P2P sync branch** — does the user's prior experiment have a home in current Dora? Architectural question.
- [OPEN] **Main menu bottom border** — micro polish.
- [OPEN] **QR codes with the Dora logo in the middle** (D/D simple one).
- [OPEN] **Real ALDI / IGA logos** — asset request (user said "remind me to provide"; this file is the reminder).
- [OPEN] **QR scanning → quick-actions modal** for the scanned item — currently scan does what?
- [OPEN] **General UI consistency** — cross-cutting Wave A and the design-pass above.

---

## Bucket D — Bullets covered elsewhere (recorded so the audit is reproducible)

Surfaces verified covered by existing prompts/proposals — listed so the
next reviewer can fast-skip them.

- SPLASH, CANNOT CONNECT, LOGIN/REGISTER/FORGOT — A1, B9.8, INV-4.
- ONBOARDING — `03_prompts/C_big_rock_design_briefs.md §C-5`; B5 nav wiring.
- DASHBOARD — deferred per master plan.
- STOCK OVERVIEW — `C_big_rock_design_briefs.md §C-1`.
- STOCKTAKE MODE — B9 fixes.
- PRODUCT SEARCH — `C_big_rock_design_briefs.md §C-6` (companion).
- MY PRODUCTS — `C_big_rock_design_briefs.md §C-7` (cart-button decision tree).
- PRODUCT HISTORY — B9.6.
- RECIPES OVERVIEW — `C_big_rock_design_briefs.md §C-4`.
- RECIPE DETAIL — B8 + C-4.
- COOK MODE — `C_big_rock_design_briefs.md §C-3`.
- MEAL PLANS — `04_proposals/PROPOSAL_MEAL_PLANS.md` (F1..F49 table).
- SHOPPING LISTS / DETAILS / MODE — `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`,
  B9.1, `03_prompts/C_big_rock_design_briefs.md §C-impl` shopping-list IMPL.
- REPORTS / WASTE — feedback empty; deferred.
- ALERTS — `C_big_rock_design_briefs.md §C-9`.
- MOBILE VIEW — empty in feedback.
- NO AREA / MISC — most bullets covered by B9 + INV-3; the unresolved
  ones are itemised in Bucket C above.
- Technical Considerations — `04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`
  covers the "single source of truth, more backend" bullet.

---

## Audit log

| Date | Pass | Notes |
|---|---|---|
| 2026-06-06 | Initial pass | Created this file as part of the docs reorg. Buckets A/B/C reflect a full walk of `Feedback _ Fixes - as of [06-Jun-2026].md`. INV-7..10 added to `03_prompts/INV_investigations.md`. |
