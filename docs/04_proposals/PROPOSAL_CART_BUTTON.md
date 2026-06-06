# Proposal — The Shopping-Cart Button (C-7)

**Status:** Draft for discussion · **Date:** 2026-06-06 · Changes NO code.  
**Scope:** Unify every "add to shopping list" / cart control across the app into
**one componentised button with a defined decision tree.** Folds in the
products-without-stock-items rule. Aligns with `SHOPPING_LIST_REDESIGN_PROPOSAL.md`
(target-list inference) and underpins C-1 (stock overview), recipe detail, and My
Products.

> **Charter tie-break for every decision below:** Effortless (P1) + Anti-creep
> (P10), with Fast UX (P11). The button should ask the *minimum* number of
> questions the situation genuinely requires — and nothing when it doesn't.

---

## 1. The problem

"Add to list" has accreted into **~13 different controls** with at least two
incompatible paradigms and inconsistent behaviour. Mapped from the live code:

| # | Surface | File:line | What it does today |
|---|---|---|---|
| 1 | Stock overview — row cart | `StockItemRow.vue:171-181` | State-aware icon (`cartStateFor`), click → quick-add to **primary** |
| 2 | Stock overview — bulk add | `StockOverview.vue:187-192` | Adds selection to **primary**, no list choice |
| 3 | Stock detail — toolbar | `StockItemDetailPage.vue:53` | Quick-add to **primary** |
| 4 | Stock detail — "Add cheapest" | `StockItemDetailPage.vue:319-328` | Adds line with cheapest product pre-selected; falls back to primary |
| 5 | Stock detail — Lists tab | `StockItemDetailPage.vue:394` | "Add to primary" if not on any list |
| 6 | Stock item chip menu | `StockItemChip.vue:59-62` | Menu item → quick-add to **primary** |
| 7 | Recipe detail — per ingredient | `RecipeDetailPage.vue:357-363` | Quick-add that ingredient to **primary** |
| 8 | Recipe detail — add all missing | `RecipeDetailPage.vue:473-492` | Opens a **list picker** modal, bulk-adds |
| 9 | My Products — bulk add on-deal | `MyProductsPage.vue:67-73` | Bulk-add linked stock items to **primary** |
| 10 | Meal plans — generate for week | `MealPlansOverview.vue:267-277` | Auto-generates a **new** list (no choice) |
| 11 | Product search — create + add | `ProductSearch.vue:582` | Creates stock item, then quick-add to primary |
| 12 | Quick Add Sheet | `QuickAddSheet.vue` | Full flow: pick list + quantity + product offer |
| 13 | Recipe card "add missing" | `StockItemDetailPage.vue:347,804` | Bulk-add missing ingredients |

**The three diseases:**

1. **Everything hardcodes "primary."** 11 of 13 controls ignore the existence of
   other lists. Bulk-add doesn't even ask which list when there are several
   (feedback L108).
2. **State-blindness + double toasts.** Only the overview row reflects whether an
   item is already on a list; the rest blindly re-add, producing the contradictory
   *"0 added, 1 already on list"* **and** *"…added to your primary list"* pair
   (L154).
3. **Products can't stand alone.** A shopping-list line **requires a
   `stock_item_id`** (`shoppingList.ts` line model; `AddLineCommand` in
   `shoppingListApiService.ts:19`). A product with no linked stock item simply
   cannot go on a list — directly contradicting the My Products requirement that
   the products side be usable on its own (L191).

The user's own words (L83-84): *"the main shopping list button should cover
everything (it's multi-purpose)… I can foresee lots of complexity… Number of
shopping lists, presence of products, etc."* That complexity is real — so the fix
is **one component that encapsulates the decision tree once**, not 13 hand-rolled
variants.

---

## 2. The model: two orthogonal questions

Every add-to-list action answers at most two questions. Keeping them separate is
what makes the tree tractable:

- **Axis A — WHAT line to create** (product resolution)
- **Axis B — WHICH list to put it on** (target resolution)

Most real clicks collapse both to a no-prompt path. A prompt appears **only** in
proportion to genuine ambiguity (P1).

### 2.1 Axis A — what to add

| Anchor | Linked products | Behaviour |
|---|---|---|
| Stock item | 0 | Add a **stock-item line**, no offer. User picks the offer at shop time. (L84: "no products → add by list logic.") |
| Stock item | 1 | Add line, **pre-select that product**. No prompt. |
| Stock item | 2+ | **Product choice modal** — cheapest highlighted/styled, but every product has its own pick affordance (L130). If a `preferred_product_id` is set, pre-select it; still let the user change. |
| **Standalone product** (My Products, unlinked) | — | Add a **product-only line** (new — §3). |

### 2.2 Axis B — which list (adopt the redesign's inference, no stored "primary")

`SHOPPING_LIST_REDESIGN_PROPOSAL.md §2.4` already replaces the stored `is_primary`
with **contextual inference over DRAFT lists.** The cart button is the primary
*consumer* of that rule, so it uses it verbatim:

| DRAFT lists | Behaviour |
|---|---|
| 0 | Create one, drop the item in, silently |
| 1 | Use it, silently (the common case) |
| 2+ | Ask which; **remember the pick** as a session default ("adding to Groceries ▾" with a switcher) |

### 2.3 Combine, never stack

When **both** axes are ambiguous (2+ products *and* 2+ draft lists), show **one**
combined sheet (the existing `QuickAddSheet` is exactly this — list + offer +
quantity in a single surface). Never open two modals back-to-back. So the modal
policy is:

- 0 prompts: ≤1 product **and** ≤1 draft list (the overwhelming common case).
- 1 prompt: exactly one axis ambiguous → minimal targeted picker.
- 1 combined prompt: both ambiguous → the full QuickAddSheet.

---

## 3. The products-without-stock-items rule (L191) — a model change

This is the heaviest part and the only one needing schema work. The feedback spells
out the exact behaviour:

> *"if a product is added to the shopping list, and no linked stock item is already
> on the list, the product displays on its own line… If later a stock item is
> linked, the stock item is automatically added and the product is nested under it…
> If a stock item is removed, its products are too (cascade). If a product is
> removed, a modal asks if the stock item should also be removed."*

**Current blocker:** `ShoppingListLine.stock_item_id` is non-nullable; there is no
`product_id` anchor on a line.

**Proposed line anchoring:** a line is anchored by **either** a `stock_item_id`
**or** a `product_id` (standalone), and may carry both when a product is nested
under a stock item.

| Line shape | Means |
|---|---|
| `stock_item_id` set, `product_id` null | Stock-item line; offer chosen later (today's default) |
| `stock_item_id` set, `selected_product_id` set | Stock-item line with a chosen offer (today's "add cheapest") |
| **`product_id` set, `stock_item_id` null** | **Standalone product line** (new) |

**Behavioural rules to implement (all from L191):**
1. Add product whose linked stock item isn't on the list → standalone product line; UI badges it "product only."
2. Link a stock item to that product later → auto-add the stock item line; nest the product under it (today's nested display).
3. Remove a stock-item line → cascade-remove its nested product lines.
4. Remove a product line → **modal**: "Also remove the stock item from this list?"

This unlocks the "products side is usable on its own" requirement and the My
Products link affordance (L195) ties into rule 2.

---

## 4. State awareness — kill the blind re-add (L83, L154, L380)

Generalise the existing `cartStateFor` (`shoppingList.ts:96-105`) so **every**
instance of the button reflects membership:

| State | Affordance |
|---|---|
| Not on any list | Outline cart, "Add to list" |
| On one (draft) list | Filled cart, tooltip "On <list name>" |
| On 2+ lists | Checkout cart, "On N lists" |
| Already ticked / purchased | Distinct muted state |

**Clicking when already-on-list is idempotent and informative, not a silent
re-add.** Instead of today's double toast, a click on an already-on item opens a
tiny popover: *"On Groceries · Add to another list · Remove."* One action, one
clear message. This directly resolves L154 (state-blindness + contradictory
toasts) and L380 (see each item's list status).

> The contradictory-toast bug itself (L154) can be fixed independently/sooner; the
> component just makes the right behaviour the only behaviour.

---

## 5. The unified component

```
<AddToListButton
  :stock-item-id="…"        // anchor (one of)
  :product-id="…"           //   these two
  :membership="…"           // for state-aware rendering
  variant="row | toolbar | menu | bulk | inline-product"
  :items="[…]"              // bulk variant only
/>
```

- Self-contained: owns the decision tree, calls the shopping-list store, shows the
  right toast. Parents don't reimplement logic.
- One **variant** prop covers the visual contexts (icon-only row button, labelled
  toolbar button, a `q-item` menu row, a bulk-bar button, the My-Products
  product-line button). Behaviour is identical; only chrome differs — that's the
  whole point of componentising (L196, L288).
- The bulk variant runs the same Axis-A/Axis-B resolution **once** for the batch
  (resolve the target list once, then add all; one summary toast).

### Surfaces, remapped

| Old surface (§1 #) | New |
|---|---|
| 1, 3, 6, 7 (single quick-adds) | `variant="row/toolbar/menu"` |
| 2, 9, 13 (bulk) | `variant="bulk"` |
| 4 ("add cheapest") | folds into Axis-A: 2+ products → choice modal with cheapest highlighted (L130) |
| 8 (recipe add-all-missing) | `variant="bulk"` with the missing set; target via Axis B |
| 11 (product search create+add) | after create, same button path |
| 12 (QuickAddSheet) | **becomes** the "both axes ambiguous" combined modal |
| 10 (meal-plan "generate for week") | **stays a distinct action** (bulk create-from-source) **but** routes its target through Axis B — offer "add to existing ▾ / new" instead of always-new (L382) |

---

## 6. Alignment, sequencing & ripple

- **Depends on the shopping-list status model.** Axis B's "count DRAFT lists" is
  only a clean query once `SHOPPING_LIST_REDESIGN §2.1` lands (status enum). Build
  the button's target-resolution behind a small `resolveTarget()` seam so it works
  with today's `is_primary` as a temporary adapter and flips to draft-counting
  later without touching call sites.
- **Underpins C-1.** Stock overview removes the chip and its embedded cart icon
  (L82-83); the row's *focus* action becomes the stock-level button (C-1), and this
  unified cart button is the secondary action. C-1 should consume this component,
  not define its own.
- **My Products link affordance (L195)** is a sibling, not this button — but rule 2
  of §3 (link → auto-add + nest) couples them; co-design.
- **Ripple to note (do not build here):** stocktake-completion "add everything I
  marked out/low?" prompt (L150) and cook-mode finish add-to-list (C-3) are
  *flows* that should reuse this component's add path, not new cart logic.
- **Out of scope (covered elsewhere):** the "Extra inputs not permitted" save/link
  errors (L167-168 → B1); preferred-product worth (L131 → its own call); the chip
  teardown and "planned meals" metric (L82,85,89 → C-1).

---

## 7. Open decisions (for co-design)

1. **Already-on-list click** — popover with *Add-to-another / Remove* (proposed), or
   simpler no-op-with-hint? (§4)
2. **>1 product** — always show the choice modal, or auto-pick `preferred_product_id`
   silently when set (with a "change" affordance)? Ties to the unresolved
   preferred-product question (L131).
3. **Standalone-product line model** — nullable `product_id` on the line (proposed)
   vs a separate line type; and confirm the exact L191 cascade wording for rules
   3–4.
4. **"Remember the list pick"** — does the session default span the whole app, or
   reset per surface? (Mirrors `SHOPPING_LIST_REDESIGN` open-Q on session vs
   persist.)
5. **Quantity** — does the unified button ever ask quantity, or always default 1 and
   edit on the list (only the full combined modal asks)? Proposed: never ask in the
   quick paths; quantity is a list-detail concern.
6. **Bulk mixed-state reporting** — one summary toast ("5 added, 2 already on
   list") confirmed as the pattern?
7. **Swipe-to-choose-list** (from the original spec, §9) — add swipe-right on the
   row cart button to open the list picker (tap = inferred target), plus a
   success animation? Or keep touch interactions to the popover only?

---

## 8. Suggested sequencing

1. **State-aware idempotent button (no model change):** ship `AddToListButton` with
   Axis A (product resolution) + Axis B against the temporary `is_primary` adapter;
   replace surfaces 1-9, 11, 13; fix the double-toast. Immediate, high-value, low
   risk.
2. **Combined modal:** route the "both ambiguous" path through the existing
   QuickAddSheet; retire bespoke pickers.
3. **Standalone-product model (§3):** the line-anchoring migration + nesting/cascade
   rules + My Products link coupling. The big rock; do after 1-2 prove the
   component.
4. **Flip Axis B** to draft-list inference when `SHOPPING_LIST_REDESIGN §2.1` lands.

---

## 9. From the original spec (historical — `docs/00_original_spec/`)

The author's first spec (pre-~100k-LOC) has several cart-button Feature Notes.
**Non-authoritative** — included only where they add something the brief above
missed. Each is tagged keep / consider / superseded; weigh that these notes
pre-date the charter, the shopping-list redesign, and the current feedback.

| Original note | Verdict | Effect on this proposal |
|---|---|---|
| *"I can swipe right on the shopping cart button to bring up shopping-list selection"* (+ "likely want a success animation") | **consider** | A touch affordance for Axis B: swipe-right opens the list picker; plain tap takes the inferred target. Good mobile complement to §2.2. Add the success animation to §4. New open decision (§7.7). |
| *"I am prompted to choose which lists to **remove** from … options: remove from primary / remove from all"* | **keep (gap!)** | The brief only designed **add**. The button is also the **remove** affordance, and removal has its own multi-list branch. See §9.1. (Reframe "remove from primary" → "remove from this list / remove from all" under the no-stored-primary model.) |
| *"'create new' and 'move to existing' can be the same action — the list picker's last option is a green-plus 'create new'"* | **keep** | Folds cleanly into the Axis-B picker and L382: the picker's final row is always **+ New list**. One surface for add-to-existing and add-to-new. |
| *"I can add a product directly to the cart from saved products — make it the **same button** as the stock-item overview"* | **keep (corroborates)** | Independent confirmation of the unify mandate (§5) and the standalone-product line (§3). The My-Products product button is the same component, `variant="inline-product"`. |
| *"I track 5 ice-cream products, I just want whatever is cheapest this week"* | **keep (corroborates)** | The rationale for cheapest-highlighted in the >1-product modal (§2.1 / L130). |
| *"When I link a product to a stock item, if the item has no picture it takes the product's picture; else a 'no pic' fallback"* | **keep (cross-ref)** | Not a cart concern, but this is the **original-spec evidence for the `StockItem.image` intent** flagged in INV-1 / **FU-033** — confirms it's a designed feature, not dead code. |
| *"I can quick-add a product so it also creates + links a stock item"* | **superseded** | The author's own later note already softens this ("possibly not necessary… products and stock items are separate"), and current feedback L191 treats them as independent. Do **not** auto-create a stock item on product add. |
| Heavy reliance on a stored *"primary/default shopping list"* throughout the old notes | **superseded** | `SHOPPING_LIST_REDESIGN §2.4` replaces stored `is_primary` with DRAFT-count inference (Axis B). The old "quick-add to primary default" framing is the pre-redesign model; don't resurface it. |

### 9.1 Remove path (the gap the original spec surfaced)

Mirror Axis B for removal. Clicking the cart button on an already-on item (§4)
exposes **Remove**, and removal resolves which list(s):

| Lists the item is on (unticked) | Remove behaviour |
|---|---|
| 1 | Remove from it, silently |
| 2+ | Modal: **Remove from <list> / Remove from all** |

This makes the component symmetric (add **and** remove) and replaces today's
absent multi-list remove logic.

---

## 10. Feedback coverage

Maps every cart/add-to-list feedback bullet for the surfaces this brief targets.
Source: `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`.

| Bullet (line) | Summary | Where addressed |
|---|---|---|
| L83 | One multi-purpose shopping-list button; cart icon in chip is wrong/useless | §1, §5 (unified component); chip teardown → C-1 |
| L84 | Complexity: # lists, presence of products; no products → list logic; products → choice modal if >1 | §2 (both axes), §2.1 |
| L108 | Bulk add doesn't confirm WHICH list when >1 | §2.2, §5 (bulk resolves target once via Axis B) |
| L130 | Add product of choice, not just cheapest; highlight cheaper; per-product add button | §2.1 (2+ products → choice modal, cheapest highlighted) |
| L154 | Button not aware of item's list state; contradictory double toasts | §4 (state-aware + idempotent, single toast) |
| L191 | Products usable standalone; nesting/cascade rules | §3 (model change + 4 behavioural rules) |
| L195 | My Products link affordance (grey/green link toggle) | §6 (sibling; coupled via §3 rule 2) — primarily My-Products scope |
| L196 | Componentise the cart button across screens | §5 (one component, variants) |
| L288 | Stock-row cart button: componentise + standardise | §5 |
| L380 | See each stock item's shopping-list status | §4 (state-aware affordance) |
| L381 | Add items individually or all at once | §5 (single + bulk variants) |
| L382 | "Generate" vs "add"; everywhere → option of to-existing-or-new | §5 (#10 routes meal-plan generate through Axis B) |
| L150 | Stocktake-end "add everything I marked?" prompt | §6 ripple — reuse add path; flow built in stocktake/C-3, not here |
| L167-168 | "Extra inputs not permitted" on quick-add/link | Out of scope — **B1** |
| L131 | Preferred-merchant/product worth | Out of scope — informs open decision 2; own call |
| L82, L85, L89, L90 | Chip status indicator / "on X lists" chip / recipes→planned-meals / ellipsis noise | Out of scope — **C-1** stock overview |
