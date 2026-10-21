# Proposal — Stock Item Detail polish (C-1b)

**Status:** Draft for discussion · **Date:** 2026-06-15 · Changes NO code.
**Scope:** Tidy and complete the Stock Item Detail surface — the single biggest unsurfaced
user-facing cluster (~30 feedback bullets, no prior design home; COVERAGE_GAPS **A-1**). A
**polish-in-place** redesign (keep the tabbed structure): a clean single-column overview with
inline edits, a pared-down toolbar with everything in the right place, a 50% split-view with
sane min/max, **a layout that's intentional whether Products is on or off**, the **History tab
reworked into an item-lifecycle timeline** (INV-7), Stock Group finally settable, Notes kept but
calm, and the residual dead recipe-tab actions wired up. This brief **creates the design home**
the A-1 cluster was missing.

> **Charter tie-break:** Effortless (P1) + Honest (P3) + Anti-creep (P10). The page today reads
> "messy / things all over the place"; the job is to make it **scannable, directly editable, and
> honest** — show only what's real (no dead buttons, no Products noise for users who turned
> Products off), and don't add surface, *rework* weak surface.

---

## 1. Current state (from live code + investigations, 2026-06-15)

Tabbed page `StockItemDetailPage.vue` — **Overview / Products / Recipes / Substitutes / Lists /
History** — with a toolbar (Mark open · Restock · Set expiry · Find deals · Add-to-list · Show QR
· Delete) and a **58%** resizable split-view "peek" launched from the Stock overview
(`StockOverview.vue`).

**Verify-state-first — much of the original feedback is already fixed or moot:**
- ✅ **Delete cascade** (L135) — `delete_stock_item.py` now blocks delete when the item is a
  recipe ingredient (422 + a "used by these recipes" dialog) instead of a FK 500. (B4.)
- ✅ **PATCH edit** (L140) — `update_stock_item.py` is partial; editing without changing the name
  works. (B3.)
- ✅ **Unlink product** (L119) — safe m2m removal, no exception.
- ✅ **Per-product "add to list"** (L130) — each linked product already has its own add button
  (`onAddProductToList`, sets `selected_product_id`); not just "cheapest." **Satisfied.**
- ✅ **Essential settable** (L114) — `is_flagged` + `auto_add_when_low` are editable in the edit
  form. (Confirm-in-browser it's discoverable.)
- ✅/⚠️ **Recipe nav** (L133) — clicking a recipe routes correctly now; **but** the recipe tab's
  **favourite toggle + "add all to list"** are emitted by `RecipeCard` and **not listened to** on
  this page → "remove from favourites does nothing" (L132) and most recipe actions beyond Cook
  (L134) are still dead. **B8 residue — fix here.**
- **Preferred merchant/product** (L131) — **resolved by removal** this session (FU-180); product
  sort degraded to cheapest → name. Nothing to design.

**Still rough (this brief addresses):**
- **Stock level shown twice** (L121 — header chip + overview row); **toolbar clutter** (Restock
  makes no sense here L123; Delete placement L122; Mark-open/expiry detached from their info
  L124); **Find deals always-on** (L125); **tabs hard to see in some themes** (L120, A1 ripple);
  **QR vs register-barcode** unclear (L126).
- **Overview messy** (L127, wants single column); **location not inline-editable** (L128);
  **clear-expiry not obvious** (L112, wants a cross); **Stock Group can't be set here** (L115 —
  the field exists but isn't in the detail DTO/form; the "forgotten field," + the L116 "what else
  is like this" audit).
- **Split-view** defaults 58% with only a min (40%); feedback wants **50% + sensible min *and*
  max** so neither side is squished (L117, L118).
- **Shopping Lists tab lacklustre** — "(primary)" plain text, non-clickable go-to arrow (L138).
- **History tab weak** — level-changes only; INV-7 → **REWORK** (L139).
- **Substitutes** — the curated per-item list is kept; the *swap-into-list* (L136) is mispositioned
  (INV-8 → move into Shop Mode, out of this surface); chip should keep the level indicator +
  substitute outline (L137).
- **Open ↔ expiry relationship** (L113) — unanswered question; clarify.

**The heading that reshapes this page:** the new `products_enabled` flag (onboarding C-5) +
**scraping divorced from the app** make this the **#1 "Products off" surface** (FU-182): for the
Cooking persona the entire Products tab + price sparklines + Find-deals are dead weight. The
redesign must look intentional in **both** states.

---

## 2. The redesign (polish-in-place — keep the tabs)

### 2.1 Header + toolbar cleanup
- **Stock level shown once** (L121) — keep the level **chip in the header**; remove the duplicate
  "Stock level" row from Overview (the chip becomes the inline editor, §2.2).
- **Toolbar pared to real, always-relevant actions:** Mark open · Set expiry · Add-to-list ·
  (Show QR, if scanning) · Delete. **Remove "Restock"** (L123 — belongs to shopping-list
  finalisation, not here). **Move "Find deals"** out of the toolbar into the Products tab (§2.4).
- **Delete placement** (L122) — move to **top-right, inline with the header** (away from the
  primary actions, danger-styled), consistent across embedded + full-page.
- **Mark-open & Set-expiry** (L124) — keep a toolbar affordance, but the **primary edit point
  lives next to the info** it changes in Overview (§2.2), so the control and its data are
  together.
- **Theme-aware tabs** (L120) — route the tab colours through A1 tokens so they're legible in
  every theme (R-002).
- **QR vs barcode** (L126) — "Show QR" (Dora's own per-item label, scanning-gated) is the only
  QR affordance here; **register-barcode lives on the Data → Barcodes page** (a real EAN→Product
  link, different feature). Add a one-line tooltip so they're not conflated. Both stay behind
  `scanning_enabled`.

### 2.2 Overview — single column, directly editable (L127, L128, L112, L115, L114)
One tidy single column of fact rows, each **editable in place** (no separate dropdowns floating
beside a read-only value):
- **Stock level** — the header chip is the editor (click → level menu); no duplicate row.
- **Location** — **inline edit** (click the value → location picker), not a separate dropdown
  beside the display (L128).
- **Expiry** — value + a **clear "×" affordance** right on the row (L112), plus the +1/+7/+14/clear
  quick-set (mirrors the Stock-overview expiry control). "Set expiry" toolbar button opens the
  same editor.
- **Open / in-use** — toggle + "since <date>" **on the same row** (L124).
- **Essential** (`is_flagged`) + **Auto-add when low** — toggles on their own rows (confirm
  discoverable, L114).
- **Stock group** — **new, settable here** (L115): thread `stock_group_id` through the detail DTO
  + an inline picker. (The L116 "what else exists-but-unsettable" audit → INV-1 cross-ref, §5.)
- **Notes** — kept but **calm/de-emphasised** (L129): a quiet, collapsible/secondary row, not a
  headline. Cheap to keep, occasionally useful; not promoted.
- **Open ↔ expiry** (L113) — clarify in copy: opening doesn't change the expiry date, but an
  *opened* perishable is the cue to set/shorten one. If we want, surface a gentle "opened — set a
  use-by?" nudge (optional; note, don't force).

### 2.3 Split-view defaults (L117, L118)
Default the peek to **50%** (not 58%), and clamp the splitter to a **sensible min *and* max**
(e.g. detail in `[40%, 65%]`) so neither the list nor the detail is squished to an unusable
width. (Today: 58% default, `[40, 100]`.)

### 2.4 Products tab (L125, L130, L131)
- **Find deals → contextual, in the Products tab:** when the item has **no linked products**, the
  empty state is the CTA — **"Find & link a product"** (→ product search) — instead of an
  always-on toolbar button. When products exist, a quieter "link another / find more."
- **Per-product add** (L130) already exists — keep it; ensure the cheaper option is **visually
  emphasised** (style, not a separate "add cheapest" button), each product carrying its own
  add-to-list.
- Price **sparkline per product** stays (read-only trend). **Preferred product is gone** (FU-180);
  sort is cheapest → name.

### 2.5 Products-off state (FU-182) — design both, gating is FU-182
When `products_enabled` is **off** (Cooking persona), this page must look **complete, not
gutted**:
- **Hidden, not greyed:** the **Products tab**, per-product price sparklines, and the Find-deals
  CTA disappear entirely. No "you haven't linked any products" empty state — **no surface at
  all** (FU-182's principle).
- The page then reads: header + Overview + **Recipes / Substitutes / Lists / History** — a clean
  pantry-and-cooking detail. Add-to-list still works (checklist-mode list).
- C-1b **designs both layouts**; **FU-182 implements the flag-gating** (R-007 — don't fork the
  app-wide sweep here, just make this surface's on/off design exist).

### 2.6 Recipes tab (L132, L133, L134) — wire the dead actions (B8 residue)
Listen to `RecipeCard`'s `@toggle-favourite` + `@add-all-to-list` on this page (they're emitted
but dropped today), so favourite-toggle and add-missing-ingredients work; confirm recipe-row
navigation. Bug-shaped — fold the fix into this surface's work, citing B8.

### 2.7 Substitutes tab (L136, L137)
- **Keep the curated per-item substitutes list** (this is the source surface — kept per the
  charter's "basic per-stock-item substitutes" carve-out; the deleted *graph page* is not
  revived).
- **Chip design** (L137) — the substitute chips keep a **stock-level indicator + the substitute
  outline/highlight**; drop anything beyond name + level state.
- **The swap-into-list** (L136) is **out of scope here** — INV-8 relocates it into **Shop Mode**
  (the real "this is out at the shelf" moment) and disambiguates the two "Substitute" buttons.
  Cross-referenced, not built in C-1b.

### 2.8 Shopping Lists tab (L138)
Make it earn its place: show **which lists the item is on** with a real **clickable** row → the
list (drop the dead go-to arrow), and render **"primary"** as a proper styled badge, not plain
text. Quiet add-to-list affordance reuses the C-7 button.

### 2.9 History tab → item lifecycle timeline (L139, INV-7)
**Rework** the level-only log into a **unified lifecycle timeline** — merge, all from existing
data (no schema change):
- level changes (with inferred context: "→ Low", "restocked"),
- **waste/spoilage** events (`StockItemWasteEvent`: when, reason, ~value),
- **list-add provenance** (`ShoppingListLine.added_at` + `added_via`: "added to Primary — auto:
  low stock"),
- open / expiry-set / last-checked context.
Needs the detail DTO to include waste events + recent list-adds (read-only; §3). Turns a dead tab
into the one place an item's purchase→use→waste→restock loop is visible (P5).

### 2.10 Notes
Kept, de-emphasised (see §2.2). Not cut — cheap, sometimes useful; just not a headline.

---

## 3. Data model / backend touches
- **No schema change.** Threading only:
  - Detail DTO (`get_stock_item_detail.py` + `stockItemDetail.ts`) gains **`stock_group_id` /
    `stock_group_name`** (settable via the existing partial PATCH), plus the **lifecycle inputs**
    for §2.9 (recent `StockItemWasteEvent` rows + recent `ShoppingListLine` add-events for this
    item).
  - Reuse the existing partial-update PATCH for stock group + the inline edits (R-003 — server
    owns the writes; client edits in place).
- `products_enabled` is read via the existing `useFeatureFlags` (C-5 adds the flag); this page
  *consumes* it (§2.5).

---

## 4. Resolved decisions (co-design 2026-06-15)
- **Polish-in-place** (keep the tab structure; tidy within it) — not a hero/single-scroll teardown.
- **Design both products-on/off states here**; FU-182 wires the gating.
- **History → lifecycle timeline** (INV-7 rework).
- **Keep Notes (calm) + make Stock Group settable.**
- (Carried) preferred-product gone (FU-180); substitute *swap* → Shop Mode (INV-8); recipe-tab
  actions are a B8-residue fix folded in.

---

## 5. Ripple & dependencies
- **FU-182 (Products-off):** C-1b designs this surface's on/off; FU-182 implements gating + the
  app-wide sweep. This page is FU-182's headline example.
- **FU-180:** preferred product removed — nothing to design (L131 closed).
- **C-7 cart button (done):** the Add-to-list + per-product add reuse it (don't re-implement).
- **INV-7:** the History rework spec. **INV-8:** the substitute-swap relocation to Shop Mode.
- **INV-1 (orphaned fields):** the L116 "what else exists-but-unsettable" audit — stock group is
  the example fixed here; the broader audit stays INV-1's.
- **B8:** the recipe-tab dead actions (§2.6) are its residue.
- **A1 theme tokens:** the tab-visibility fix (§2.1).
- **`scanning_enabled`:** gates Show-QR (§2.1).
- **C-1 stock overview (done):** owns the split-view host; the min/max/default change (§2.3)
  lands in `StockOverview.vue`.

---

## 6. From the original spec (historical — `docs/00_original_spec/`)
The Stock Items board anticipated per-item detail (levels, locations, expiry, open-marker,
substitutes) — all present. The lifecycle-timeline, the inline-edit overview, and the
products-off intentional-collapse are newer (feedback + the scraping-divorce); nothing in the
original spec to extract or that it supersedes. (Skim confirmed no dropped intent for this
surface.)

---

## 7. Suggested sequencing (→ IMPL_PLAN_STOCK_ITEM_DETAIL)
1. **Overview tidy + inline edits + dedupe level + toolbar cleanup** (§2.1, §2.2) — the bulk of
   the "it's messy" feedback; mostly frontend + the `stock_group_id` DTO thread.
2. **Split-view 50% + min/max** (§2.3) — small `StockOverview.vue` change.
3. **Products tab + Find-deals contextual + products-off design** (§2.4, §2.5) — consumes the
   `products_enabled` flag; the off-state design.
4. **Recipes-tab dead actions** (§2.6, B8 residue) + **Shopping-Lists tab polish** (§2.8) +
   **Substitutes chip** (§2.7).
5. **History → lifecycle timeline** (§2.9, INV-7) — detail-DTO additions + render.

---

## 8. Feedback coverage

Maps `§STOCK ITEM DETAIL` (L112-140).

| Bullet (line) | Summary | Where |
|---|---|---|
| L112 | Clear-expiry not obvious (add cross) | §2.2 |
| L113 | Expiry ↔ open relationship | §2.2 (clarify) |
| L114 | No way to set "essential" | §1 (✅ settable; confirm) |
| L115 | No way to set stock group | §2.2 + §3 |
| L116 | What else is exists-but-unsettable | §5 (INV-1) |
| L117 | Split-view at 50% default | §2.3 |
| L118 | Splitter sensible min/max | §2.3 |
| L119 | Unlink product exception | §1 (✅ fixed; confirm) |
| L120 | Tabs hard to see in some themes | §2.1 (A1 tokens) |
| L121 | Stock level shown twice | §2.1 |
| L122 | Move delete button | §2.1 |
| L123 | Restock makes no sense here | §2.1 (remove) |
| L124 | Move Opened/expiry next to their info | §2.1 / §2.2 |
| L125 | Find-deals placement → contextual | §2.4 |
| L126 | QR vs register-barcode clarity | §2.1 |
| L127 | Overview single column | §2.2 |
| L128 | Location inline update | §2.2 |
| L129 | Notes worth | §2.2 / §2.10 (keep, calm) |
| L130 | Add product-of-choice (per-product add) | §1 (✅ exists) + §2.4 (emphasise cheaper) |
| L131 | Preferred merchant/product | §1 / §5 — **removed (FU-180)** |
| L132 | Remove-from-favourites does nothing | §2.6 (B8 residue) |
| L133 | Clicking recipes navigates wrong | §2.6 (✅ nav fixed; confirm) |
| L134 | Recipe actions do nothing except Cook | §2.6 (B8 residue) |
| L135 | Delete FK error | §1 (✅ fixed B4; confirm) |
| L136 | Substitute swap-into-list weird | §2.7 → **Shop Mode (INV-8)**, out of scope here |
| L137 | Substitute chip design (level + outline) | §2.7 |
| L138 | Shopping-lists tab lacklustre | §2.8 |
| L139 | History tab unuseful | §2.9 (INV-7 rework) |
| L140 | Edit must be PATCH not PUT | §1 (✅ fixed B3; confirm) |

After acceptance + the browser-confirms (the ✅ rows), flip the **A-1** cluster in
`docs/02_feedback/COVERAGE_GAPS.md` from gap → covered, and this brief becomes the surface's
design home the gap doc asked for.
