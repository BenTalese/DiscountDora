# Implementation Plan — Stock Item Detail polish (C-1b impl)

**Status:** Plan for review · **Date:** 2026-06-15 · **No code yet** — phased plan + chunks.
**Source proposal:** `PROPOSAL_STOCK_ITEM_DETAIL.md` (co-designed 2026-06-15; decisions §4).
**Adjacent:**
- **C-1 stock overview (done)** — owns the split-view host (`StockOverview.vue`); the 50% +
  min/max change lands there.
- **C-5 onboarding (designed)** — adds the `products_enabled` flag this page *consumes* (§2.5).
- **FU-182** — implements the app-wide Products-off gating; C-1b designs this surface's on/off.
- **C-7 cart button (done)** — `AddToListButton` + per-product add reused, not re-implemented.
- **INV-7** (History rework spec), **INV-8** (substitute-swap — its "→ Shop Mode" target is
  obsolete; Shop Mode merged into ShoppingListDetail and the swap ships there, FU-407/FU-408),
  **INV-1** (orphaned
  fields), **B8** (recipe-tab dead actions = its residue), **FU-180** (preferred product removed).
**Phase:** Master plan **Phase 1 polish** — the loop's per-item surface; mostly frontend +
read-only DTO threading, no schema change.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-15 (`StockItemDetailPage.vue`, `StockOverview.vue`, `stockItemDetail.ts`,
`get_stock_item_detail.py`, `update_stock_item.py`, `delete_stock_item.py`, the edit dialog,
`RecipeCard.vue`).

**Already true (do NOT rebuild):** delete-cascade safe (B4), partial PATCH edit (B3),
unlink-product safe, **per-product add-to-list exists**, `is_flagged`/`auto_add_when_low`
editable, recipe-row nav fixed, **preferred product removed (FU-180)**, product sort cheapest→name,
per-product price sparkline present, Show-QR gated by `scanning_enabled`.

**Confirmed gaps (this plan delivers):** stock level duplicated (header + overview); toolbar
clutter (Restock here; Delete placement; Find-deals always-on; open/expiry detached); overview
not single-column; location not inline-editable; no clear-expiry "×"; **`stock_group_id` absent
from the detail DTO + form**; split-view 58% default, `[40,100]` (no max); tabs not theme-token
driven; recipe-tab `@toggle-favourite` + `@add-all-to-list` **not listened to** (B8 residue);
Shopping-Lists tab "(primary)" plain text + dead arrow; History tab level-only; no
`products_enabled` consumption.

**Tests:** check `tests/e2e/dora_api/test_stock_item*`; the DTO additions (stock_group, lifecycle
events) get e2e coverage. Mostly frontend chunks → vue-tsc + eslint; no migration expected.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### C-1b.1 — Overview tidy + inline edits + dedupe level + toolbar cleanup ★ FIRST (the bulk of "it's messy")
**Closes:** L121, L122, L123, L124, L127, L128, L112, L115, L114, L120, L126, L129, L113.
- **Backend:** detail DTO + `stockItemDetail.ts` gain `stock_group_id`/`stock_group_name`
  (settable via the existing partial PATCH). No schema change.
- **Frontend:** single-column Overview with **inline editing** per row (level = header chip
  editor, no duplicate row L121; location inline picker L128; expiry value + **"×" clear** +
  ±1/7/14 L112; open toggle + "since" on-row L124; essential + auto-add toggles L114;
  **stock-group inline picker** L115; Notes as a calm/secondary row L129). Toolbar pared to Mark
  open · Set expiry · Add-to-list · (Show QR) · Delete; **remove Restock** (L123); **Delete →
  top-right header** (L122); Find-deals leaves the toolbar (→ C-1b.3). **Theme-aware tabs** via
  A1 tokens (L120). QR-vs-barcode tooltip (L126). Clarify open↔expiry copy (L113).
- **Risk:** Medium (the inline-edit overview is the big refactor; keep each row's edit-in-place
  consistent). **Close-gate:** R-002 (tokens, theme-safe tabs), R-003 (server owns writes; PATCH),
  R-001 (reuse the overview row pattern), R-008 (remove the dead Restock handler). *Acceptance:*
  level shown once; every overview fact editable in place; stock group settable; Delete top-right;
  Restock gone; tabs legible in all themes.

### C-1b.2 — Split-view 50% + sensible min/max
**Closes:** L117, L118. In `StockOverview.vue`: default the peek to **50%**, clamp the splitter to
`[40%, ~65%]` so neither pane is squished. **Risk:** Low. **Close-gate:** R-007 (touch only the
splitter config). *Acceptance:* peek opens at 50%; can't drag either pane to an unusable width.

### C-1b.3 — Products tab + contextual Find-deals + Products-off design
**Closes:** L125, L130 (emphasis), L131 (closed), §2.5.
- **Find-deals contextual:** empty Products tab → "Find & link a product" CTA; non-empty → quiet
  "link another." Remove the always-on toolbar button. Emphasise the cheaper product (style), keep
  per-product add (exists). Preferred product gone (FU-180).
- **Products-off (consumes `products_enabled`):** when off, **hide** the Products tab + price
  sparklines + Find-deals entirely (no empty state) — the page reads as a clean cooking detail.
  **C-1b designs both; FU-182 owns the app-wide gating** (R-007).
- **Risk:** Low-medium. **Close-gate:** R-007 (don't start FU-182's sweep), feature-flag via
  `useFeatureFlags`. *Acceptance:* products-on shows the tab with contextual find/link; products-off
  hides the whole product side cleanly; cheaper option visually emphasised.

### C-1b.4 — Recipe-tab dead actions (B8 residue) + Shopping-Lists tab + Substitutes chip
**Closes:** L132, L133 (confirm), L134, L138, L136 (cross-ref), L137.
- **Recipes:** listen to `RecipeCard`'s `@toggle-favourite` + `@add-all-to-list` (dropped today);
  confirm row nav. **Shopping-Lists tab:** clickable list rows → the list, "primary" as a styled
  badge, drop the dead arrow. **Substitutes:** chip = level indicator + substitute outline only
  (L137); the *swap* lives on the shopping list, not here. **[Updated 2026-07-09, FU-408:**
  Shop Mode was merged into `ShoppingListDetail` (UX v2), and the substitute swap **is** built
  there — a per-line "Swap for a substitute item" action, gated on `has_substitutes` (FU-407/RD-18).
  The original "cross-ref to Shop Mode (INV-8), not built here" wording is obsolete.**]**
- **Risk:** Low. **Close-gate:** R-001 (reuse list/badge components), R-008. *Acceptance:* favourite
  toggle + add-all work; list rows navigate; substitute chips show level + outline.

### C-1b.5 — History → item lifecycle timeline (INV-7)
**Closes:** L139.
- **Backend:** detail DTO gains recent `StockItemWasteEvent` + recent `ShoppingListLine` add-events
  for the item (read-only; no schema change). **Frontend:** one timeline merging level changes
  (with inferred context) + waste + list-add provenance + open/expiry/check context, date-sorted.
- **Risk:** Medium (DTO additions + merge/sort + labelling). **Close-gate:** R-003 (server
  aggregates the events; client renders), e2e for the new DTO fields. *Acceptance:* the tab shows a
  multi-event lifecycle (created/restocked/low/added-why/wasted/opened) from existing data.

---

## 2. Sequencing & cross-cutting close-gate
Order = §1 (C-1b.1 → .5); .1 is the marquee tidy, .5 the meatiest backend-touch. Cross-cutting:
A1 tokens (R-002); reuse over duplication (R-001); server owns writes/aggregates (R-003); scope
discipline — **Products-off app-wide sweep is FU-182, substitute-swap ships on the shopping list**
(no longer "Shop Mode"; FU-407/FU-408) (R-007);
no dead code (R-008); CHANGELOG + worklog + follow-ups per chunk; e2e + vue-tsc + eslint green.
Most "✅ already fixed" rows in the proxy table are **confirm-in-browser** items — verify, don't
re-fix.

## 3. Feedback coverage
Inherits the proposal's **§8 table** (L112-140). After build + the browser-confirms, flip the
**A-1** cluster in `docs/02_feedback/COVERAGE_GAPS.md` gap → covered.
