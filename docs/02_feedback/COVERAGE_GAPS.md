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

> **Update 2026-06-15:** this cluster now HAS a design home —
> `04_proposals/PROPOSAL_STOCK_ITEM_DETAIL.md` (C-1b) + `IMPL_PLAN_STOCK_ITEM_DETAIL.md`.
> The §8 coverage table there maps every L112-140 bullet.
>
> **Update 2026-06-16:** the C-1b stack (`.1 → .5`) is **built**; the design home is now
> the running surface. Cluster flipped to **[COVERED]**; remaining open work is
> browser-verification, tracked under **FU-202** (extended for each .1–.5 chunk). The
> per-bullet status table stays below for the audit trail.

Feedback `§STOCK ITEM DETAIL` has ~30 bullets. The bug-shaped ones were covered by
B-prompts (B3 PATCH, B4 cascade, B8 dead actions); the **layout / button-placement /
open-design** bullets are now all addressed in the C-1b chunks:

- [COVERED] Clear-expiry button affordance (cross mark next to expiry) — **C-1b.1** (× button + ±1/+7/+14).
- [COVERED] No way to set "essential" — **C-1b.1** (toggle row in the inline-edit overview).
- [COVERED] No way to set stock group — **C-1b.1** (DTO thread + inline picker row).
- [COVERED] Split-view at 50% default; sensible min/max splitter distance — **C-1b.2**.
- [COVERED] Tabs hardly visible in some themes — **C-1b.1** (theme-token routing, R-002).
- [COVERED] Stock-level shown twice — **C-1b.1** (header chip is the editor; duplicate row gone).
- [COVERED] Move delete button — **C-1b.1** (top-right, danger-ghost).
- [COVERED] Restock here makes no sense — **C-1b.1** (button + handler removed; belongs to list finalisation).
- [COVERED] Move "Opened" button next to opened info; same for expiry — **C-1b.1** (open toggle + "since" on the row; expiry value + × + quick-set on the row).
- [COVERED] "Find deals" placement — **C-1b.3** (contextual: empty-state CTA + "Link another" in the Products tab; toolbar Find-deals removed in C-1b.1).
- [COVERED] Overview single column tidier — **C-1b.1**.
- [COVERED] Location updated inline without a separate dropdown — **C-1b.1** (searchable path picker inline) / focused FU-202 pass earlier.
- [COVERED] Notes value — **C-1b.1** (kept, de-emphasised at the bottom).
- [COVERED] Add product-of-choice to shopping list (not just cheapest); per-product list-add buttons — already exists (C-7); **C-1b.3** removed the "Get cheapest" toolbar shortcut and emphasises the cheapest card via style, per §2.4.
- [COVERED] Preferred merchant/product behaviour — **FU-180** removed it; **C-1b.3** confirms nothing to design.
- [COVERED] Shopping-lists tab — "(primary)" plain text feels unimaginative; arrow icon non-clickable — **C-1b.4** (styled `q-badge` for Primary; dead arrow removed).
- [COVERED] History tab worth — **C-1b.5** (rebuilt as a unified lifecycle timeline merging level + waste + list-add provenance + synthesised Opened/Checked rows; INV-7).
- [COVERED] Substitute swap-into-list weirdness — **C-1b.4** removed the swap from this surface; relocation owned by **INV-8** (Shop Mode).

**Outstanding gates:** FU-202 browser-verification across all five chunks; everything code-level
+ tsc/eslint/e2e is green.

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
- [COVERED] "Scan" tab under QR codes — useful here vs only on stock overview? → `PROPOSAL_BARCODE_SCANNING.md` §6 (open question; action-scan leans to C-1 Stock Overview, Data tab keeps label printing).
- [COVERED] "Barcodes & QR" → "QR codes" rename → `PROPOSAL_BARCODE_SCANNING.md` §4 (renamed "Scanning & QR labels"; kept "scanning" because real-barcode→navigate survives via ProductBarcode).
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
- [RESOLVED 2026-06-23] Profile picture — set/update; surface on the
  menu-bar avatar. Shipped in `IMPL_PLAN_SETTINGS_REBUILD.md` Phase 4:
  `User.image` column + migration `a4f7c2e9b6d1`, `GET /users/<id>/image`
  bytes endpoint, `image`/`clear_image` on `PATCH /auth/me` (+ admin
  update), `has_image` on the me/list DTOs, and a shared SPA `UserAvatar`
  adopted at the menu bar (fallback icon), the Account header + the Users
  admin rows (fallback initials), with the upload picker on Account.
  Backend static-only this session (no Python env) — pytest round-trip
  added; run + browser walk pending (see `DORA_FOLLOWUPS.md`).

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
- [COVERED] **QR codes with the Dora logo in the middle** (D/D simple one). → `PROPOSAL_BARCODE_SCANNING.md` §6 (noted nice-to-have, opportunistic during label-render work).
- [OPEN] **Real ALDI / IGA logos** — asset request (user said "remind me to provide"; this file is the reminder).
- [COVERED] **QR scanning → quick-actions modal** for the scanned item. → `PROPOSAL_BARCODE_SCANNING.md` §5.3 (deferred to C-1 Stock Overview overhaul, where item context exists; today scan → result dialog → open detail).
- [OPEN] **General UI consistency** — cross-cutting Wave A and the design-pass above.

---

## Bucket D — Bullets covered elsewhere (recorded so the audit is reproducible)

Surfaces verified covered by existing prompts/proposals — listed so the
next reviewer can fast-skip them.

- SPLASH, CANNOT CONNECT, LOGIN/REGISTER/FORGOT — A1, B9.8, INV-4.
- ONBOARDING — `04_proposals/PROPOSAL_ONBOARDING.md` (C-5, written 2026-06-06;
  maps L24-46); dead-nav was B5; feature-flags → `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  §2.6 (C-cross); headcount → C-3. **Update 2026-06-17:** personas + the `products_enabled` flag
  are retired and L46 (stock-vs-product explainer) is dropped — onboarding is one un-personalized
  "show everything" path. See `04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §5.
- DASHBOARD — deferred per master plan.
- STOCK OVERVIEW — `04_proposals/PROPOSAL_STOCK_OVERVIEW.md` (C-1, written
  2026-06-06; maps L63-99). Cart bullets → C-7; planned-meals metric → C-2;
  location display → `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` §2.5 (C-cross);
  images → FU-033.
- STOCKTAKE MODE — B9 fixes.
- PRODUCT SEARCH — `C_big_rock_design_briefs.md §C-6` (companion-scope, not
  written as Dora-core). The Dora-core seam it targets is
  `04_proposals/PROPOSAL_INGESTION_API.md` (C-10, written 2026-06-06).
- MY PRODUCTS / CART BUTTON — `04_proposals/PROPOSAL_CART_BUTTON.md` (C-7,
  written 2026-06-06: unified button, decision tree, standalone-product rule).
  Note: My-Products link affordance (L195) + custom products (L192) still its own
  scope; the cart/standalone-product bullets (L83-84,108,130,154,191,196,288,
  380-382) are now covered. **Update 2026-06-17:** My Products + Price History + the stock-item
  Products tab **stay in Dora, data-gated**; only Product Search moves to the companion. Custom
  products (L192) is **by-design refused** (no manual product entry); the everyday substitute is
  `PreferredBuy`. The My-Products link affordance is repaired (FU-208). See
  `04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.
- PRODUCT HISTORY — B9.6.
- RECIPES OVERVIEW / RECIPE DETAIL — `04_proposals/PROPOSAL_COOKBOOK.md` (C-4,
  written 2026-06-06; maps L228-315). Comparison CUT per INV-6; cost/nutrition/
  tag-taxonomy settings → `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (C-cross);
  cart → C-7; allocation → C-2/B6.
- COOK MODE — `04_proposals/PROPOSAL_COOK_MODE.md` (C-3, written 2026-06-06;
  maps L317-338). Tools/structured-steps → C-4; headcount → C-5; finish add-to-
  list → C-7.
- MEAL PLANS — `04_proposals/PROPOSAL_MEAL_PLANS.md` (F1..F49 table).
- SHOPPING LISTS / DETAILS / MODE — `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`
  + `04_proposals/IMPL_PLAN_SHOPPING_LISTS.md` (C-impl phased plan, written
  2026-06-06; maps L401-422), B9.1. **UX layer superseded 2026-06-12 by
  `04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md`** (S1-S18 session bullets +
  re-maps L402-421; shop-mode page merged away, rail/dropdown, chip axe).
- REPORTS / WASTE — feedback empty; deferred.
- ALERTS — `04_proposals/PROPOSAL_ALERTS.md` (C-9, written 2026-06-06; maps
  L437-441 + dashboard alert bullets L57/L60). Dashboard card = contract only
  (deferred); price/back-in-stock subscriptions folded into central management.
- SETTINGS / CONFIG (cross-cutting) — `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  (C-cross, written 2026-06-06): money opt-in (L254), nutrition off/simple/complex
  (L262-263,287), tag/cuisine/category/tools taxonomy editors (L235,238,255,260,
  264,283-284,310), location-display zone policy (L81,107,321), feature-flag panel
  (L42). Settings-shell redesign itself stays deferred.
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
| 2026-06-06 | C-cross written | `PROPOSAL_CONFIG_AND_OPTINS.md` (C-cross) lands the cross-cutting config layer. Flipped money/nutrition/tag-taxonomy/location/feature-flag bullets from "→ C-cross (TBD)" to a written home. Completes the Wave-C design briefs (companion C-6/C-8 remain out of Dora-core scope). |
| 2026-06-17 | Products-as-overlay pivot | Wrote `04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` (Products gated on data-presence not a flag; new `PreferredBuy` everyday construct; onboarding personas removed; Product Search → companion behind a configured URL). Superseded the spine of `PROPOSAL_SIMPLE_MODE.md`; reshaped `PROPOSAL_INGESTION_API.md` + onboarding docs + RECONCILED §7. Re-homed L42/L45/L46/L84/L131/L191/L192/L226/L254. |
| 2026-06-22 | FU-227 "Your prices" landed | `04_proposals/IMPL_PLAN_YOUR_PRICES.md` shipped all 8 chunks (unit-conversion helper → observation model reshape → shared `PriceEntry` + row button + widget → baseline math → shopping-line prefill + harvest + Receipt relabel → bottom-sheet history + per-product observation overlay → ingest-obs path removal → close-gate + R-017). Flipped L226 (bottom-sheet for Price History — ADDRESSED, `PriceHistoryBottomSheet.vue`); L419 (shopping line price entry as receipt — ADDRESSED, prefill-and-persist + I1 Receipt relabel); L420 (close the loop / list-becomes-receipt — ADDRESSED, harvest-on-/finish + LC-1 idempotent + E3 dead-branch removal). Also addressed implicit "what does this usually cost me" + "warn me when something jumped" (the C5 widget + above-1.15× chip, observations-only baseline per LC-2). L225 (Price-History box-fit bug) stays OUT OF SCOPE → FU-214. |
