# Implementation Plan — The Shopping-Cart Button (C-7)

**Status:** Plan for review · **Date:** 2026-06-09 · **No code yet** — phased
plan + first reviewable chunk.
**Source proposal:** `PROPOSAL_CART_BUTTON.md` (2026-06-06; decisions resolved
§7a 2026-06-09).
**Adjacent work:** `SHOPPING_LIST_REDESIGN_PROPOSAL.md` + `IMPL_PLAN_SHOPPING_LISTS.md`
(status model + draft-list inference — **landed**, P6-01); `IMPL_PLAN_STOCK_OVERVIEW.md`
(C-1 row hosts this button); `IMPL_PLAN_COOKBOOK.md` / `IMPL_PLAN_COOK_MODE.md`
(ingredient-row + finish add-to-list consumers).
**Phase:** Master plan **Phase 1** — Charter P1 Effortless · P10 Anti-creep ·
P11 Fast UX. One component, minimum prompts.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-09 against the live code:

- **Add-to-list is ~13 hand-rolled controls** (proposal §1 table) across
  `StockItemRow.vue`, `StockOverview.vue`, `StockItemDetailPage.vue`,
  `StockItemChip.vue`, `RecipeDetailPage.vue`, `MyProductsPage.vue`,
  `MealPlansOverview.vue`, `ProductSearch.vue`, `QuickAddSheet.vue`. Most
  hardcode "primary"; only the overview row is state-aware (`cartStateFor`,
  `shoppingList.ts`). Shared add logic lives in `useShoppingListActions.ts` /
  `useQuickAdd.ts`.
- **Axis B is ready:** the shopping-list **status model landed** (P6-01) —
  `ShoppingListStatus = draft/shopping/done` and the store already exposes an
  inferred single-DRAFT quick-add destination (`quickAddTargetListId`). So
  draft-list inference is usable **today**; the `is_primary` adapter the proposal
  hedged on is unnecessary.
- **Standalone products are blocked:** `ShoppingListLine.stock_item_id` is
  **non-nullable** and there's no `product_id` anchor (`shopping_list.py`;
  `AddLineCommand` in `shoppingListApiService.ts`). §3 needs schema work.
- **The double-toast bug (L154 / FU-038)** is live — a blind re-add still fires
  the contradictory pair. Chunk 1 makes the right behaviour the only behaviour.

Re-verify exact paths/lines at the start of each chunk.

---

## 1. Resolved decisions driving this plan (proposal §7a)

1. Already-on click = **toggle**: 1 list → remove silently; 2+ → popover.
2. 2+ products → **always the choice modal** (cheapest highlighted).
3. Standalone line → **nullable `product_id` on the line** + cascade rules.
4. Remember list pick → **app-wide for the session**.
5. Quantity → **never in quick paths**; only the combined modal.
6. Bulk → **one summary toast**.
7. Swipe → **deferred** (popover/tap only).

---

## 2. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — `AddToListButton` component + state-aware toggle ★ FIRST CHUNK
**Closes:** L83 / L154 / L196 / L288 / L380 / L381 + **FU-038** (double toast).
**No schema change.**

The whole value of C-7 with none of the migration risk — ship the component and
adopt it on the no-model-change surfaces.

- **`AddToListButton.vue`** — self-contained, owns the decision tree, calls the
  shopping-list store, shows the right toast. `variant="row | toolbar | menu |
  bulk"` (chrome only; behaviour identical). Props: `stock-item-id` (anchor),
  `membership` (for state-aware render), `items[]` (bulk).
- **Axis A (product resolution):** 0 products → stock-item line; 1 → preselect
  it; **2+ → always the choice modal** (cheapest highlighted, per-product pick;
  preselect `preferred_product_id` if set but still show it).
- **Axis B (target):** use the **existing draft inference** — 0 drafts → create +
  drop silently; 1 → use silently; 2+ → pick, then **remember app-wide for the
  session** ("adding to <list> ▾" switcher). New tiny session store/composable
  (`useCartTarget`) for the remembered list.
- **State-aware render** (generalise `cartStateFor`): not-on / on-one / on-2+ /
  ticked.
- **Already-on click = toggle** (decision 1): on exactly **1** list → **remove
  silently**; on **2+** → **popover** (which list / Add to another / Remove).
  Remove path (§9.1): 1 → silent; 2+ → "Remove from <list> / Remove from all".
  This *replaces* the blind re-add + kills the double toast.
- **Bulk variant:** resolve the target **once** for the batch, add all, **one
  summary toast** ("5 added, 2 already on list") (decision 6).
- **Adopt on surfaces** (proposal §1 #): 1, 3, 5, 6, 7, 11 → row/toolbar/menu;
  2, 9, 13 → bulk. Each call site drops its hand-rolled logic and renders the
  component.

**Risk:** behaviour parity across many call sites; do them in one PR so the old
paths all die together. Keep `StockItemChip`'s cart usage swapped here even
though the chip itself is torn down later in C-1. *Acceptance:* every adopted
surface uses the component; clicking an on-list item toggles/popovers (never
double-toasts); bulk gives one summary.

### Chunk 2 — Combined modal via QuickAddSheet
**Closes:** §2.3 + L84 (both-ambiguous path) + quantity (decision 5).

- When **both** axes are ambiguous (2+ products **and** 2+ draft lists), open the
  existing `QuickAddSheet` as the single combined surface (list + offer +
  quantity). Never stack two modals.
- **Quantity** lives only here; quick paths stay qty-1.
- Retire any remaining bespoke pickers (surface 12 *becomes* this path).

*Acceptance:* the only place two prompts could appear now shows one combined
sheet; quantity is editable there and nowhere else in the quick paths.

### Chunk 3 — Standalone-product line model (the big rock, §3)
**Closes:** L191 + L130 (product-only) + couples L195. **Schema change.**

- **Backend line anchoring:** make `ShoppingListLine.stock_item_id` **nullable**;
  add nullable **`product_id`** (FK→Product). A line is anchored by
  `stock_item_id` **or** `product_id`, and may carry both when a product is
  nested under a stock item. Migration (pre-release → clean, non-preserving OK).
  `AddLineCommand` / DTOs gain `product_id`.
- **Behavioural rules (L191):**
  1. Add a product whose linked stock item isn't on the list → **standalone
     product line**, badged "product only".
  2. Link a stock item to that product later → **auto-add the stock line + nest**
     the product under it.
  3. Remove a stock-item line → **cascade-remove** its nested product lines.
  4. Remove a product line → **modal**: "Also remove the stock item from this
     list?".
- **Frontend:** nested display on the shopping-list detail; `AddToListButton`
  gains `variant="inline-product"` + a `product-id` anchor path (My Products).
- Couples with the My Products **link affordance** (L195) — co-design that
  sibling so rule 2 wires up.

**Risk:** the heaviest part — line model touches the list detail, dedupe/merge,
and restore/backup. Do it after Chunks 1–2 prove the component. *Acceptance:*
products add/stand alone, nest on link, cascade on stock-line removal, prompt on
product-line removal.

### Chunk 4 — Meal-plan "generate" routes through Axis B
**Closes:** L382.

- Surface 10 ("generate for week") stays a distinct bulk create-from-source
  action, but offers **add-to-existing ▾ / new** via Axis B instead of always
  creating a new list.

*Acceptance:* generating offers an existing draft target.

---

## 3. Suggested run order

1 (component + toggle, no schema) → 2 (combined modal) → 3 (standalone-product
model) → 4 (meal-plan generate target). Chunks 1–2 are no-schema and high value;
3 is the migration rock; 4 is small.

---

## 4. Cross-cutting notes

- **Axis B uses draft inference now** — no `is_primary` adapter (status model
  landed). The remembered-target session default is app-wide (decision 4).
- **C-1 stock overview consumes this component** for the row's secondary action
  (its `StockItemRow` cart placeholder, IMPL_PLAN_STOCK_OVERVIEW Chunk 3).
- **Cook-mode finish add-to-list** (C-3) and **stocktake-end add** (L150) should
  **reuse this add path**, not new cart logic — flows built in their own prompts.
- **Out of scope:** "Extra inputs not permitted" link/save errors (L167-168 →
  B1); preferred-product worth (L131 → own call; informs decision 2); chip
  teardown / planned-meals metric (L82/85/89 → C-1); swipe gesture (deferred).
- **State-ownership (R-003):** membership/`cartStateFor` is a server-derived
  cross-entity fact; the component renders it, doesn't recompute thresholds.
- Wave-A standards: `BaseButton`, theme tokens, `BaseDialog` for the popover/
  modals.

---

## 5. Feedback coverage (cart / add-to-list bullets)

Mirrors `PROPOSAL_CART_BUTTON.md §10`, mapped to chunks.

| Line | Summary | Chunk |
|---|---|---|
| L83 | One multi-purpose button; chip cart icon wrong | 1 (chip teardown → C-1) |
| L84 | Complexity: #lists, products; choice modal if >1 | 1 (+ 2 combined) |
| L108 | Bulk must confirm which list when >1 | 1 (bulk resolves target once) |
| L130 | Choose product, not just cheapest; highlight cheaper | 1 (2+ → choice modal) |
| L154 | State-blind + contradictory double toasts | 1 (toggle + single toast) |
| L191 | Products standalone; nest/cascade | 3 |
| L195 | My Products link affordance | 3 (coupled; primarily My-Products scope) |
| L196 | Componentise the cart button | 1 |
| L288 | Stock-row cart: componentise + standardise | 1 |
| L380 | See each item's list status | 1 (state-aware) |
| L381 | Add individually or all at once | 1 (single + bulk variants) |
| L382 | Generate vs add; everywhere to-existing-or-new | 4 |
| L150 | Stocktake-end "add everything I marked?" | reuse add path (stocktake/C-3) |
| L167-168 | "Extra inputs not permitted" | out of scope — B1 |
| L131 | Preferred product worth | out of scope — own call |
| L82/L85/L89/L90 | Chip status / on-X-lists / metric / ellipsis | out of scope — C-1 |
