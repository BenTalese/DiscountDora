# Chunk 03 — Shopping Lists

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (single session, no sub-agents)
**Scope (from PLAN §4):** lists overview → detail (three faces: plan / run / receipt), quick-add + the cart button + `AddToListDialog`, auto-generate (`NewListDialog`), templates, finish & restock, move/discard leftovers, trim-to-budget, store ladder + money ladder, store breakdown, receipt attachments, price capture, budget status/history/settings API.
**Boundaries:** `StockOverview.vue`'s bulk add/remove call sites → Chunk 5; `BuyVerdictBadgeInline` / `useBuyVerdict` / `get_buy_verdict.py` → Chunk 6; `LogPriceSheet` + `PriceEntry` → Chunk 10 (price observations); the low-stock auto-add hook (`update_stock_item.py:312–450`) → Chunk 6; inference overlay internals → Chunk 7; `/budget` settings page + dashboard budget card → Chunks 13/8; `data/export_shopping_list` print view → Chunk 18.

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_SHOPPING_LIST_UX_V4.md` (§0–§11), `IMPL_PLAN_SHOPPING_LIST_RECEIPTS.md`, `PROPOSAL_BUDGET_AWARE_LISTS.md` (via FU-448 citations), `SHOPPING_LIST_BASELINE.md`, `MAGIC_BEHAVIOUR_AUDIT.md` F1–F4, F14–F16; feedback `# SHOPPING LISTS` / `# SHOPPING LIST DETAILS VIEW` / `# SHOPPING MODE` (L400–422); open FUs: FU-897, 849, 780, 768, 766, 757, 740, 739, 729, 725, 714, 713, 698, 668, 654, 573, 624, 675, 802/791.

**Files walked (every file opened):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/shopping_lists/get_shopping_list_detail.py` | 798 | detail DTO, both ladders, totals, suggestions |
| `…/manage_shopping_list_lines.py` | 657 | add / update / delete / remove-by-item / quick-add |
| `…/manage_shopping_list.py` | 477 | create / update / delete / finish / copy / start / back-to-draft |
| `…/list_actions.py` | 286 | move lines, clear, discard unticked |
| `…/bulk_operations.py` | 296 | bulk-tick, bulk-add, bulk-remove, reorder |
| `…/trim_to_budget.py` | 617 | five-tier optimiser |
| `…/auto_generate.py` | 484 | multi-source generator |
| `…/_line_price.py`, `_line_defaults.py`, `_line_retention.py`, `_observation_sync.py`, `_frequently_added.py` | 536 | chokepoints |
| `…/get_shopping_lists.py`, `get_membership.py`, `get_list_buy_verdicts.py`, `frequently_added.py`, `quick_add_target_resolver.py` | 474 | reads |
| `…/manage_shopping_list_attachments.py`, `shopping_list_attachment_access.py` | 312 | receipt photos |
| `dora_api/features/shopping_list_templates/manage_templates.py` | 691 | templates CRUD + instantiate + snapshot |
| `dora_api/features/budget/budget.py` | 514 | status / history / settings, `period_headroom` |
| `dora_api/domain/entities/{shopping_list,shopping_list_template,shopping_list_attachment}.py` | 310 | entities |
| `web_app/src/pages/ShoppingListDetail.vue` | 3279 | the page (FU-780) |
| `web_app/src/pages/{ShoppingListsOverview,ShopNowRedirect,ShoppingListTemplates}.vue` | 871 | landing / PWA shortcut / templates |
| `web_app/src/components/shoppingList/{ShoppingListOverviewCard,ShoppingListPlanRow,ShoppingListRunFace,ShoppingListRunRow,ShoppingListReceiptFace,ShoppingListReceiptRow,StoreSpendCard,ShoppingListRailItem,LineChoicePicker,AddToListDialog,AddToListRowItem}.vue`, `addToListTypes.ts` | 3480 | faces, rows, pickers |
| `web_app/src/components/{AddToListButton,QuickAddSheet,LogPriceSheet}.vue`, `components/dialogs/NewListDialog.vue` | 1623 | cart button, sheets, new-list dialog |
| `web_app/src/composables/{useLineSections,useListState,useShoppingListActions,useShoppingListExport,useQuickAdd}.ts` | 510 | composables |
| `web_app/src/stores/shoppingListStore.ts`, `models/{shoppingList,shoppingListTemplate}.ts`, `services/api/{shoppingListApiService,shoppingListTemplateApiService,budgetApiService}.ts`, `css/shoppingList.scss` | 1180 | store, models, API, shared CSS |
| Tests inventoried: `tests/test_shopping_list_totals.py`, `test_shopping_list_store_breakdown.py`, `test_store_ladder.py`, `test_line_price_harvest.py`, `test_trim_to_budget.py`, `test_budget_spend_excludes_unticked.py`, `test_snapshot_offer_price.py`; e2e `test_shopping_list_lifecycle.py`, `test_shopping_list_product_lines.py`, `test_shopping_line_defaults.py`, `test_shopping_line_preferred_buy.py`, `test_shopping_line_survives_delete.py`, `test_shopping_list_attachments.py`, `test_shopping_list_planned_shop_date.py`, `test_shopping_list_remove_by_stock_item.py`, `test_shopping_list_template_choice.py`, `test_copy_shopping_list_unit_of_work.py`, `test_create_shopping_list_template_unit_of_work.py`, `test_instantiate_shopping_list_template_unit_of_work.py`, `test_snapshot_shopping_list_template_unit_of_work.py`, `test_list_buy_verdicts.py`, `test_line_has_substitutes.py`, `test_quick_add_target_inference.py`, `test_budget_router.py`, `test_query_budgets.py`, `test_spend_by_store.py`; vitest `shoppingList.spec.ts`, `shoppingListStore.spec.ts`, `shoppingListRailItem.spec.ts`, `useLineSections.spec.ts`, `useListState.spec.ts`, `addToListButton/Dialog/Rows.spec.ts` | | |

## A. Full Systems Test — Shopping Lists

### A1. Preconditions
- Seeded install with ≥ 2 stores (one with a logo), ≥ 30 stock items (some with `usual_store_id`, some with linked products + offers, some essentials, some low/out), ≥ 2 finished lists in history (so the money ladder's historic rung and "frequently added" have data).
- Run three times: **money off** (default install), **money on, products off** (preferred buys), **money on + products on** (offers). The row's "which one" picker, the price chips, the store breakdown title and the trim banner all change shape per tier.
- Budget set under `/settings/budget` for the trim-to-budget and projection rows.

### A2. Golden path
Persona: **Dense user**, desktop then phone.
1. `/shopping-lists` with lists → route guard lands on the next-up list (live shop > first pending after last completed > earliest pending > latest done); with no lists → empty state + "New list".
2. Rail (desktop) / picker (phone): drafts + shopping + 5 most recent done, newest first; "See older (N)" opens a searchable dialog; "New list" pinned at the top.
3. New list → Start from Empty / Template / Recipe / Meal plan; auto-fill low-or-out (essentials only), all essentials, frequently added; target new (name + shop day) or merge into an existing list → toast with counts; unlinked recipe ingredients named (FU-505).
4. Plan face: overview card (estimated cost or item count · shop day · items; group-by Store/None; **Shop**), toolbar (Add item · Shop day calendar popup · Templates · Print · Save as template).
5. Add item → QuickAddSheet: frequently-added first, then low/out; items already on the target list hidden; one tap = one line, sheet stays open.
6. Row: quantity tile (hover stepper / tap-to-type), name = "which one" picker (offers or preferred buys), Dora's auto-added mark, buy-verdict badge, planned-store caption menu ("Any store" + every store, "(usual)" marked), `~$` estimate, reorder arrows (ungrouped only), delete. Drag to reorder (desktop, ungrouped).
7. Pick an offer → line moves to that store, estimate = offer price; un-pick → historic figure returns. Set planned store → row re-sections under Store.
8. Dora's suggestions strip (inference opted in) → chip adds a line.
9. Over budget → trim banner → "Show what would be cut" → Keep one → Apply → Deferred-to-fit section with reason + Add back.
10. **Shop** → run face: progress bar, "Left to spend", sections with `picked/total`, cleared sections collapse to one line, Collected drawer with trolley total; tap row = picked (toast with Undo); price button → bottom sheet (price each · offers "Seen at" chips · quantity stepper · bought-from); Log price (money) for off-list items; Draft (back to draft, unticks all).
11. **Finish** → dialog lists ticked items (nested lines collapse to the parent); unticked leftovers force a choice: move to existing / move to new / discard; → done, ticked items restocked to Stocked, observations harvested, names snapshotted.
12. Receipt face: card (Shopped date · items bought · You saved), sheet with multiplier · name · leader · amount, "Didn't buy" chips, Total + "N not priced"; Amend → stepper + "Set price" per line; corrections rewrite the observation; Put away checklist.
13. Receipts section (shopping/done): take photo / choose → thumb strip → zoom → delete.
14. Templates page: Use (one tap) / preview / Edit items (picker-based "which one", quantities) / rename inline / delete; Save as template from a list (name + include ticked?).
15. Cart button elsewhere (stock rows, recipe ingredients, product rows): none → add (1 draft silent, 2+ → radio, 0 → "create a list first"); on list → remove; on several → popover.
16. PWA "Shop now" shortcut → `/shopping-lists/shop-now` → the single shopping list, else the single draft, else the overview.

### A3. Edge cases
- Rename to blank → list self-labels from shop day / created date; `display_name` tracks a later shop-day change.
- Deleting the list you're viewing → bounce to `/shopping-lists`.
- Product-only line (no stock item) → sunken row, bag glyph, removal prompts "also remove the stock item?"; **03-R1/R3/R4**: copying, moving or snapshotting such a line is broken (see §C1).
- Deleting a stock item on a draft → its line vanishes; on a done list → the line survives with the frozen name.
- Finish with zero ticked → "nothing is restocked"; finish with everything ticked → plain confirm, no leftovers section.
- Done list: PATCH `status=done` is refused (400); start / back-to-draft on done → 400.
- Template whose items were deleted → instantiate skips them, list still created (possibly empty).
- Quick-add while 2 drafts exist → "which list" radio, pick remembered for the tab.
- Reorder while grouped → arrows/drag hidden; stored group preference pointing at an empty field → falls back to None with a reason in the menu.
- Money off → no price column, card leads with counts, store breakdown says "Where you'll shop", receipt leader hidden.
- Offline → mutations toast "Could not …" and the optimistic flip is reverted.
- Trim with nothing cuttable → "Trimmed everything safe. Still $X over."
- Two lists both planned for today → next-up picks the earlier-created one.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty state → New list) | ✓ | ✓ (money off tier) | ✓ (products + budget + keyboard `n`/space/`u`/arrows) | ✓ (money / products flags) | ✓ (lists are shared; quick-add target is per-tab) | – | – |

### A5. Load-bearing conditions
- **375px phone**: the two-line plan row grid, the picker + rename segment, the run row's 60px target, the bottom price sheet with the keyboard up, the finish dialog at 34vh scroll.
- **1280px**: toolbar scrolls sideways rather than wrapping; rail 300px with ellipsised names (FU-578 #40 family).
- **Themes × dark**: status pills (soft bg + full ink), `.sl-panel--warn` soft wash, gradient band on plan/run vs flat receipt, the `hsla(0,0%,100%,.55)` progress track over the gradient (R-002 carve-out — verify on pesto dark).
- **Reduced motion**: progress bar fill, reveal-on-approach transitions.
- **Touch**: no stepper, arrows always visible, 44px action track.

### A6. Release-gate rows
- Money on + products on: pick an offer → tick → enter a different price at the till → finish → the receipt shows the entered price, "You saved" uses the offer's RRP, and `/budget/status` spent equals the receipt total.
- Finish early with leftovers → "Move to a new list" → the new list carries exactly the unticked lines, the receipt's "Didn't buy" is empty.
- Amend a receipt price → `/stock-items/<id>/detail` "Your prices" reflects the correction (observation rewritten, `observed_at` unchanged).
- Phone: new list from a meal plan → shop → finish, all from the picker.

## B. Help content — Shopping Lists

### B1. Current help audit
- `HelpPage.vue` "Shopping & deals" group holds **one** entry (*Search for products* — the ingestion seam), nothing about lists, faces, quick-add, templates, budget or receipts. The surface the owner spent the most September feedback on has no help at all.
- `app_knowledge.py` L34–38 says *"multiple lists with one marked PRIMARY … Archive completed lists, copy lists … Lists can be marked in-progress while shopping"* — three retired concepts (primary flag, copy, in-progress) and none of the three faces, finish-as-receipt, money/store ladders, trim-to-budget or quick-add inference.
- Inline help that exists and should be *linked*, not repeated: the overview card tooltips (Shop / Finish / Amend / Put away), the plan row's "Any store" rationale, the price sheet's "Price each" wording, the trim banner copy, the `AddToListDialog` unlinked-ingredients footer.

### B2. Help entries

#### One list, three faces
- **Group:** Shopping (new group; rename "Shopping & deals" → "Shopping" and move *Search for products* under Products)
- **What it does:** A list is a draft while you build it, a shop while you're in the store, and a receipt once you finish. Each face shows only what that moment needs: the draft has quantities, stores and reordering; the shop has one big tick per row and a price button; the receipt is a read-only docket you can amend.
- **When it fires / how to trigger it:** **Shop** on the card starts the trip; **Finish** ends it; **Draft** (mid-shop) undoes an accidental start and unticks everything.
- **What it costs / might get wrong:** Finishing is final — a done list can't go back. Ticked items are restocked to Stocked when you finish, never before.
- **Related:** Finish and restock · Amend a receipt
- **Chip:** `ShoppingListOverviewCard.vue:58` beside the status pill → `<HelpHint topic="One list, three faces">`.
- **Source:** `manage_shopping_list.py`, PROPOSAL_SHOPPING_LIST_UX_V4 §4.

#### Which list opens, and which one quick-add uses
- **Group:** Shopping
- **What it does:** `/shopping-lists` opens the list that's up next: a shop in progress, else the first pending list dated on or after your last finished shop, else the earliest pending, else the most recent receipt. Quick-add (the cart button anywhere in Dora) lands on your **only** draft; with two or more drafts it asks once and remembers for the tab; with none it asks you to create one.
- **What controls it:** Nothing to set — there is no "primary list" flag. Shop day (toolbar) is what moves a list in the order.
- **What it costs / might get wrong:** The rail is one timeline, newest first; finished lists older than the five most recent sit behind "See older".
- **Source:** `get_shopping_lists._next_up_list_id`, `quick_add_target_resolver.py`, MAGIC F2/F3/F4.

#### Adding items: Add item, the cart button, and "Add to a list"
- **Group:** Shopping
- **What it does:** **Add item** on a list searches every stock item, frequently-added first, hiding what's already on the list; one tap adds one. The **cart button** on stock rows, recipe ingredients and products adds or removes with one tap (two or more linked products open the sheet so you choose which). Recipe and meal-plan pages use **Add to a list**, which pre-ticks what's missing or low, names what each item is for, and lists ingredients that can't go on a list because they aren't linked to a pantry item.
- **What it costs / might get wrong:** A new line remembers your last choice for that item — the preferred buy or product you picked last time, and its store; clearing a choice is remembered too.
- **Related:** Recipes & lists (Cookbook) · Missing this week (Meal plans)
- **Source:** `QuickAddSheet.vue`, `AddToListButton.vue`, `AddToListDialog.vue`, `_line_defaults.py`.

#### Start a list from stock, a recipe, a plan or a template
- **Group:** Shopping
- **What it does:** **New list** builds a list from what's low or out (optionally essentials only), all your essentials, items you add most often, a recipe's ingredients (minus what's stocked), a meal-plan week, or a saved template — into a new list or topped up onto an existing one. Items are never added twice.
- **What it costs / might get wrong:** Recipe and plan ingredients without a linked stock item are listed for you to add by hand. "Frequently added" counts every line ever written, finished shops included.
- **Source:** `auto_generate.py`, `NewListDialog.vue`, MAGIC F12.

#### Picking which one: offers and preferred buys
- **Group:** Shopping
- **What it does:** The item's name on a row is a menu. With products on, it lists the item's linked offers (price, store, saving); without, it lists the item's preferred buys. Picking an offer moves the line to that store and uses its price as the estimate; picking again clears it.
- **What controls it:** `/settings/admin/system/products` decides which list the menu shows.
- **What it costs / might get wrong:** An offer is an estimate until you enter a price in the shop — nothing is recorded as spend until then.
- **Source:** `LineChoicePicker.vue`, owner 2026-09-17/27.

#### What a line is expected to cost, and where you'll buy it
- **Group:** Shopping (money)
- **What it does:** Each estimate uses the first of: a price you entered · the offer you picked · what you last paid for the item. Each row's store uses the first of: where you bought it · the store you chose for this list · the item's usual store · where you last bought it · the picked offer's store. The card's total and the "Where you'll spend it" split come from those; items with no price are counted but not priced, and the card says so.
- **What controls it:** `/settings/admin/system/money`. Usual stores live on the stock item.
- **Related:** Your prices (Stock)
- **Source:** `get_shopping_list_detail.py` ladders, `_line_price.resolve_store_id`.

#### Entering prices as you shop
- **Group:** Shopping (money)
- **What it does:** Tap a row's price in the shop to record what you actually paid, how many, and where. "Seen at" chips pull an advertised price in with one tap. **Log price** on the toolbar records a shelf price for something that isn't on the list.
- **What it costs / might get wrong:** Only entered prices become spend, savings and purchase history; a list finished with no prices records none. Quantity multiplies the line.
- **Source:** `ShoppingListDetail.vue` price sheet, `_observation_sync.py`.

#### Finish and restock
- **Group:** Shopping
- **What it does:** Finishing marks the shop done: every ticked item's level goes to Stocked, each priced line becomes a purchase in the item's price history, and names are frozen so the receipt survives pantry changes. Anything unticked must go somewhere first — another list, a new list, or the bin.
- **What it costs / might get wrong:** A finished list is a receipt; it can't return to draft. Discarded leftovers are gone from the list, not from your pantry or history.
- **Related:** Stock levels (Stock) · Budget
- **Source:** `FinishShoppingListHandler`, `list_actions.py`, MAGIC F16.

#### Amend a receipt
- **Group:** Shopping
- **What it does:** On a finished list, **Amend** unlocks price, store and quantity per line (never add/remove/reorder). A correction rewrites the purchase record the line created, so a typo stops feeding every future estimate.
- **What it costs / might get wrong:** Your pantry isn't restocked again; the purchase's date stays as first recorded.
- **Source:** FU-726, `UpdateLineHandler` observation sync.

#### Keep a shop under budget (trim to fit)
- **Group:** Shopping (money + budget)
- **What it does:** When a draft is projected over what's left of the budget period its shop day falls in, Dora offers to set lines aside: habit buys that can wait, low items with days of cover left, things above your usual price, out-of-stock items with no meal booked, ingredients for meals five or more days away. Each cut names its reason; **Keep** protects a line; **Add back** restores it later.
- **What controls it:** `/settings/budget`. Never cut: essentials, meals in the next two days, lines under $2, "buy" verdicts on low/out items.
- **Source:** `trim_to_budget.py`, PROPOSAL_BUDGET_AWARE_LISTS.

#### Templates
- **Group:** Shopping
- **What it does:** Save a list as a template (unticked lines by default) and start new lists from it in one tap. Edit a template's items, quantities and "which one" choices at `/shopping-lists/templates`; choices carry onto new lists while they still apply.
- **Source:** `manage_templates.py`.

#### Receipt photos
- **Group:** Shopping
- **What it does:** Attach photos of the till receipt to a list you're shopping or have finished — up to 20, tap to zoom, bin to remove. Record-keeping only: nothing is read from the image.
- **Source:** FU-334.

#### Dora thinks you may be out of…
- **Group:** Shopping / Dora's hunches
- **What it does:** On a draft, a strip of items Dora believes you've run out of (from purchase rhythm and cooking) that aren't on the list yet; tap to add. Nothing is added for you.
- **What controls it:** Settings → Assistant → inference for shopping (off by default).
- **Related:** The "Dora thinks…" hint (Stock)
- **Source:** FU-653, `_inferred_suggestions`.

### B3. DoraBot corpus delta
Replace `app_knowledge.py` L34–38 with:
```
- Shopping Lists: a list is a draft while you build it, a shop while you're in
  the store, and a receipt once finished. Add items from the list (search,
  frequently-added first), from any stock/recipe/product row's cart button, or
  from "Add to a list" on recipes and meal plans; "New list" can fill a list from
  low/out items, essentials, frequent buys, a recipe, a plan week or a template.
  Each row can pick which offer or preferred buy you mean, and which store you
  plan to buy it at; with money on, Dora estimates each line (entered price →
  picked offer → what you last paid) and splits the total by store. In the shop
  you tick rows and can enter what you paid; finishing restocks ticked items,
  records entered prices as purchase history, and asks what to do with anything
  unticked (move or discard). A finished list is a receipt you can amend. Over
  budget, "Trim to fit" sets safe lines aside with a reason. Templates and
  receipt photos round it out. Quick-add targets your only draft and asks if
  there are several.
```

## C. Senior review — Shopping Lists

### C1. Bugs (verified or high-confidence latent)

- **03-R1** · latent, high-confidence · `manage_shopping_list.py:344–352` `CopyShoppingListHandler` copies `stock_item_id/quantity/selected_product_id/sequence` only. A **product-only line** (`stock_item_id` NULL, `product_id` set — `test_shopping_list_product_lines.py` proves they exist) is copied with **both anchors NULL**, violating `ck_shopping_list_line_anchor` → 500 on the whole copy. It also drops `product_id`, `preferred_buy_id`, `planned_store_id`, `added_at` and skips `apply_line_defaults`, so the copy forgets every "which one"/store choice. · **Exact change:** copy `product_id`, `preferred_buy_id`, `planned_store_id`, set `added_at=now`, call `apply_line_defaults`. **However** the client has no caller (`copyAsync` removed; `shoppingListApiService.ts:231`) and the endpoint is pinned only by `test_copy_shopping_list_unit_of_work.py` + `test_api_fuzz.py:222` → the better fix is **delete the endpoint + its test** (FU-766 shape; "Save as template" replaced it). · S · **execute (delete)** — owner may veto; if kept, apply the field fix instead.
- **03-R2** · latent, high-confidence · `manage_templates.py:647, 662–669` `SnapshotFromListHandler`: (a) `f"Template from {source.name}"` → "Template from None" for a self-labelled list (`display_name` exists — the SPA pre-fills its own name so it only shows when the prompt is blanked); (b) a product-only source line yields `ShoppingListTemplateLine(stock_item_id=None)` on a NOT NULL column → IntegrityError → 500 for any list carrying one. · **Exact change:** `source.display_name`; skip lines with `stock_item_id is None` (templates are item-anchored by design) and report `skipped_product_lines` in the response. · S · guard: `test_snapshot_shopping_list_template_unit_of_work.py` + new case · **execute**.
- **03-R3** · latent · `list_actions.py:116–130` `MoveLinesHandler` de-dupes on `stock_item_id` alone: `target_item_ids` contains `None` whenever the target has a product-only line, so **every** product-only movable line is "skipped as duplicate"; and the first product-only line moved adds `None`, skipping the rest. · **Exact change:** key on `(stock_item_id, product_id)` via a small `line_anchor_key(line)` helper shared with `AddLineHandler`'s dedupe (03-R5). · S · guard: `test_shopping_list_lifecycle.py` move case + new product-only case · **execute**.
- **03-R4** · latent · `get_membership.py:76–79` buckets `per_item[line.stock_item_id]` — product-only lines land under key `None` and are serialised as `StockItemMembershipDto(stock_item_id=None)`; the client's `cartStateFor` never matches it but the DTO lies about its type. · **Exact change:** `if line.stock_item_id is None: continue`; also push `shopping_list_id in active_ids` into the query (`in_(active_ids)`) instead of loading every unticked line ever (done lists included). · S · guard: `test_quick_add_target_inference.py` · **execute**.
- **03-R5** · duplication-with-drift · `QuickAddToPrimaryHandler.handle` (`manage_shopping_list_lines.py:593–618`) re-implements `AddLineHandler`'s dedupe (without the `product_id is None` guard, so a nested product line counts as "already on list"), sequence and construction. · **Exact change:** delegate: `AddLineHandler(self.repository).handle(AddLineRequest(stock_item_id=…), target.id)`. · S · guard: `test_quick_add_target_inference.py` · **execute**.
- **03-R6** · R-032 latent · `frequently_added.py:51–60` loads `StockItem.all()` **without** `.include("stock_level")` and reads `item.stock_level` → `stock_level_id` is **always None**. Harmless only because `QuickAddSheet` reads nothing but `stock_item_id` from the payload (grep L167). · **Exact change:** fold into 03-R14 — the endpoint returns ranked ids from `_frequently_added.rank_frequently_added_ids`; drop `name/stock_level_id/add_count` from the DTO and `FrequentlyAddedItem`. · S · **execute**.
- **03-R7** · bug (template) · `QuickAddSheet.vue:22` `prepend-:icon="ICONS.search"` is not a Vue binding (the attribute is literally named `prepend-:icon`), so the search field has no icon. · **Exact change:** `<template #prepend><q-icon :name="ICONS.search" /></template>` (as `ShoppingListDetail.vue:829` does). · S · **execute**.
- **03-R8** · R-021/R-056 · `auto_generate.py:236` and `manage_templates.py:539` name new lists with `now.strftime('%a %d %b')` — server-local date, a second and third copy of `format_list_date`'s format. · **Exact change:** `format_list_date(household_today(self.repository))`; or (cleaner, UX-v2) leave `name=None` for the auto list and let it self-label — propose the latter for instantiate (`name = request.name or template.name`). · S · guard: `test_instantiate_shopping_list_template_unit_of_work.py` · **execute**.

### C2. Redundancy / DRY (R-001, R-003)

- **03-R9** · `DeleteLineHandler` (L432–447) and `RemoveLineByStockItemHandler` (L495–509) carry the same 15-line nested-product-line cascade. · **Exact change:** `_remove_nested_product_lines(repository, list_id, stock_item_id)`; both call it. · S · guard: `test_shopping_list_product_lines.py`, `test_shopping_list_remove_by_stock_item.py` · **execute**.
- **03-R10** · `trim_to_budget._current_user_id` (L564) and `budget._current_user_id` (L314, which also uses the literal `"user_id"` instead of `SESSION_USER_ID_KEY` — R-019) — copies 16/17 of **FU-654** (02-R12). · **execute (FU-654)**.
- **03-R11** · `getattr(offer, "_product_id", None) or getattr(offer, "product_id", None)` ×2 (`trim_to_budget.py:205`, `budget.py:286`) and `getattr(e, "_recipe_id") or getattr(e, "recipe_id")` ×3 (`trim_to_budget.py:327, 342, 349`) — defensive dual reads of a column the mapping always installs as `_product_id` / `_recipe_id` (`auto_generate.py:370` reads it directly). · **Exact change:** direct attribute reads. · S · **execute**.
- **03-R12** · `auto_generate._collect_recipes` (L312–346) and `_collect_meal_plan_week` (L378–412) are the same 35-line ingredient→stock-item block, each issuing one `Recipe.by_id` **per recipe** plus one `StockItem.all(in_)` per recipe; `_collect_meal_plan_week` also loads **every** `MealPlan` with entries to filter 7 days in Python. · **Exact change:** `_collect_from_recipe_ids(candidates, recipe_ids, unlinked_skipped)` with one `Recipe.include(INGREDIENTS).all(in_(ids))` and one `StockItem` load; the plan week reads `MealPlanEntry` by `scheduled_for` range (as `trim_to_budget._load_meal_demand` does). · M · guard: `test_shopping_list_lifecycle.py` auto-generate cases (add a recipe + plan-week case if absent) · **execute**.
- **03-R13** · `auto_generate.py:47–50` `SEQ_STOCKED/LOW/OUT = 0/1/2` + `getattr(item.stock_level, "sequence", -1)` hard-codes level identity by sequence, while `domain.stock_status` exports `is_low_stock / is_out_of_stock / is_missing` and `trim_to_budget` already uses them (R-003/R-019). · **Exact change:** `is_low_stock(level)` / `is_out_of_stock(level)`; delete the constants. · S · **execute**.
- **03-R14** · `frequently_added.GetFrequentlyAddedHandler` runs its own GROUP BY (L41–46) that `_frequently_added.rank_frequently_added_ids` already owns (that module's docstring claims "both now come here" — the public endpoint never did). · **Exact change:** endpoint = `rank_frequently_added_ids(session, limit)` → `[{"stock_item_id": id}]`; see 03-R6. · S · guard: add a 5-line e2e case to `test_shopping_list_lifecycle.py` · **execute**.
- **03-R15** · `budget.GetBudgetHistoryHandler` (L409–431) re-implements the per-line sum that `period_spent` does (L145–153). · **Exact change:** `_spend_of(lines) -> float` used by both (history keeps its single fetch and buckets by period). · S · guard: `test_budget_router.py`, `test_budget_spend_excludes_unticked.py` · **execute**.
- **03-R16** · `get_shopping_list_detail._chosen` (L593–596) re-implements `_chosen_offer` (L226–233) inline. · **Exact change:** `_first_or_selected(offers)` helper used by both; delete the `_chosen_offer(line)` wrapper if unused after. · S · **execute**.
- **03-R17** · `GetTemplatesHandler` (manage_templates L92–95) loads every template line to count — same shape as 02-R30. · **Exact change:** `select(template_id, count()).group_by`. · S · **execute**.
- **03-R18** · `manage_shopping_list_attachments.py:39–41, 174–181` data-URL regex + base64 decode = the 5th site of **01-R7** (`infrastructure/data_url.py`). · **execute (01-R7)**.
- **03-R19** · `ShoppingListDetail.vue` three near-identical optimistic price/store writers — `savePriceEditor` (L2423), `saveStoreOnly` (L2511), `clearPriceOverride` (L2571) — each snapshot/restore the same three fields and toast. · **Exact change:** `writeLinePurchase(line, { price, storeId }, command, failMessage)` with one rollback path; the three become one-liners. · S · **execute** (inside FU-780's eventual split).
- **03-R20** · `useShoppingListActions.notifyOk/notifyErr` and the page's 30+ `$q.notify({type, position:'bottom-right', …})` blocks — **FU-624** (toast helper) owns this; no new finding. `useShoppingListActions.finishShopping` has **zero callers** (the page has its own `confirmFinish`) → **03-R24**.

### C3. Dead code / unused fields / unread endpoints

- **03-R21** · `manage_shopping_list_lines.snapshot_offer_price` (L207–232) — no callers (grep: only tests `test_snapshot_offer_price.py` and a comment). Kept "because the columns hold history" — deleting a *writer* doesn't delete data, and the column comments already carry the history. · **Exact change:** delete the function + `test_snapshot_offer_price.py`; move its rationale paragraph onto `ShoppingListLine.picked_offer_price`'s comment (which currently still says the snapshot is taken at add/select time — stale since 2026-09-17, 03-R28). · S · **execute**.
- **03-R22** · **FU-766**: `has_substitutes` + its raw `StockItemSubstitute` SQL block (`get_shopping_list_detail.py:446–467`, with `from dora_api.app import db` and `from sqlalchemy import …` *inside* the handler — R-008) and `POST …/lines/bulk-tick` (`bulk_operations.py:44–92`) have no client reader/caller. · **Exact change:** delete both + `test_line_has_substitutes.py` + the bulk-tick cases; drop `has_substitutes` from `models/shoppingList.ts:163`. · S · **execute (FU-766)** — owner directive needed only if INV-8's swap is revived; the FU says "owner's call", recommend delete.
- **03-R23** · `POST …/lines/move-to/<target>` (`list_actions.py:162–182`) and `moveLinesToAsync` (`shoppingListApiService.ts:339`) — the bulk-select bar that called it is gone (page comment L199–204); grep → no caller. · **Exact change:** delete client method; delete server route + `MoveLinesRequest` (keep the `line_ids` parameter on the handler — it's one filter and tested) and the move-to e2e case. · S · **execute**.
- **03-R24** · `useShoppingListActions.finishShopping` (L158–172) — zero callers. · **Exact change:** delete. · S · **execute**.
- **03-R25** · `models/shoppingList.ts`: `savingsOfLine` (L336), `isListDone`, `isListShopping` (L10–16) — zero callers (`savingsOfLine` also re-implements a ladder the server owns, so it's an R-003 trap waiting). · **Exact change:** delete all three. · S · guard: `shoppingList.spec.ts` (drop their cases) · **execute**.
- **03-R26** · Detail DTO fields with **no SPA reader**: `prefill_unit_price` (the price sheet seeds from `estimated_unit_price`; `prefill_source_label` *is* read by `ShoppingListReceiptRow`), `last_paid_unit_price` (only `last_paid_store_*` are read), `stock_level_name`, `stock_location_id`, `added_at`. · **Exact change:** drop `prefill_unit_price`, `last_paid_unit_price`, `stock_level_name`, `stock_location_id`, `added_at` from `ShoppingListLineDto` + the TS type; keep `prefill_source_label` and the breadcrumb. · S · guard: `test_shopping_list_lifecycle.py` (field assertions) · **execute (conditional on grep at execution — PutAwayDialog reads `stock_location_id`? It reads from `lines` prop — check)**.
- **03-R27** · `FinishShoppingListRequest` (empty model) + `@has_request_body` + `get_request_body() or FinishShoppingListRequest()` and `FinishShoppingListCommand = Record<string, never>` — vestiges of the cut per-item level picker (FU-582). · **Exact change:** drop the request class/decorator/command type; `finishAsync(id)` posts `{}`. · S · **execute**.
- **03-R28** · stale comments/docstrings describing retired behaviour: `shopping_list.py:16–17` ("matching the ADDED_VIA_* convention above" — deleted 2026-09-19), `:70–79` (`picked_offer_price` "captured at commit-to-offer" — not written since 2026-09-17), `_line_price.py:30` ("snapshot taken at commit-to-offer time"), `budget.py:15–17, 123–125` (two contradictory accounts of when `picked_offer_price` is written), `get_shopping_list_detail.py:5–6` ("Totals are computed client-side" — server-owned since state-ownership chunk), `models/shoppingList.ts:168–174` (ladder order "actual → last paid → offer" vs server "actual → picked offer → historic"), `budgetApiService.ts:4–6` ("settings live on the User row" — moved to AppSetting), `useLineSections.ts:155` ("`manual` is always in"), `ShoppingListPlanRow.vue:405` + `ShoppingListReceiptRow.vue:82` (`shoppingRow.scss` → file is `shoppingList.scss`). · **Exact change:** reword each to the current contract (one sweep). · S · **execute**.
- **03-R29** · `ShoppingListReceiptFace` prop `completedLabel` + the page's `completedLabel` computed (L1806) — the face no longer renders a header (its own comment L29–34), so the prop is dead. · **Exact change:** delete prop + computed + `formatDate` if then unused on the page. · S · **execute**.
- **03-R30** · `useQuickAdd.QuickAddOptions.stockItemId` doc says "skips straight to the offer/list step" — the step is gone; the preset now adds and closes. Doc fix only (fold into 03-R28).

### C4. Componentisation opportunities (R-001)

- **03-R31** · `ShoppingListDetail.vue` is 3,279 lines (**FU-780**). The natural seams are already visible in the script: trim-to-budget (L1629–1781), price capture (L2296–2622), finish & leftovers (L1316–1481), lists rail/picker (L1866–1988), receipts (L2949–3019). · **Exact change (FU-780 plan):** `useTrimToBudget(listId, detail, baseLines)`, `useLinePriceCapture(listId, detail)`, `useFinishShopping(...)`, `ShoppingListsPicker.vue` (rail + mobile dropdown + "See older"), `ShoppingListReceipts.vue`; page keeps routing/loading/face switch. · L · guard: vue-tsc + drive all three faces once · **FU-780** (keep as the tracker; sequence after the small items above).
- **03-R32** · `plannedStoreOptionsFor` / `storeOptionsFor` / price-sheet store select (page L2364–2421) are three shapes of "store options for a line" — the first two differ by design (all stores vs. stores touching the line); the third is `allStoreOptions`. · **waive** (documented, intentional).
- **03-R33** · `NewListDialog.bulkAddToList` (L303–319) loops `addLineAsync` per id, and the merge-a-template path instantiates a temp list, reads it, loops, deletes it (L369–381). · **Exact change:** use `bulkAddLinesAsync` (one round-trip; FU-714's shape) and add `merge_into_list_id` to `InstantiateTemplateRequest` so a template can top up a list server-side (one handler path, no temp list). · M · guard: `test_instantiate_shopping_list_template_unit_of_work.py` new case · **execute** (FU-714 partial; the rest of FU-714's 16 call sites stay with that FU).
- **03-R34** · `BulkAddLinesHandler` / `BulkRemoveByStockItemHandler` call the single-line handlers per item, each of which `save_changes()` — N commits per bulk request (**FU-713**). · **Exact change:** `commit: bool = True` on the inner handlers (or a `_add_line(...)` core they share); bulk saves once. · S · guard: `test_shopping_list_lifecycle.py` bulk cases · **execute (FU-713)**.

### C5. Placement / layering (R-003, R-005, R-008)

- **03-R35** · `get_shopping_list_detail.GetShoppingListDetailHandler.handle` is a 340-line method. · **Exact change:** `_load_context(list_id, lines) -> _DetailContext` (items, prior purchases, stores, preferred buys) + `_line_dto(line, ctx)`; `handle` becomes ~30 lines. · M · guard: `test_shopping_list_totals.py`, `test_shopping_list_store_breakdown.py`, `test_shopping_list_lifecycle.py` · **execute** (do together with 03-R22, which removes the raw-SQL block).
- **03-R36** · `_inferred_suggestions` loads **every** stock item with its level on every detail read **before** `resolve_divergence` checks the surface flag (L768–772; the gate is inside `resolve_divergence`). · **Exact change:** check `surface_enabled(current_user(repo), SURFACE_SHOPPING)` first; load candidates only when on. · S · **execute**.
- **03-R37** · `shopping_list_attachment_access.py` uses raw `db.metadata.tables["ShoppingListAttachment"]` Core statements although `ShoppingListAttachment` is a mapped entity (`table_mappings.py:1816`) — R-005 (repository-routed access) and the only module in the feature importing `db` directly besides the 03-R22 block. · **Exact change:** `repository.get(ShoppingListAttachment).all(EntityField(...).eq(list_id))` etc.; bytes endpoint reads `.image`. · S · guard: `test_shopping_list_attachments.py` · **execute**.
- **03-R38** · `trim_to_budget.py` imports the private `_gather_inputs` from `get_buy_verdict` and runs it lazily **per item** (`_verdict_inputs_for`), while `get_list_buy_verdicts` uses the public bulk `gather_verdict_inputs_for_items` (fixed query count). · **Exact change:** gather once for all candidate items up front with the bulk helper; drop `_Ctx.repository` + the `assert`. · S · guard: `test_trim_to_budget.py` · **execute**.
- **03-R39** · `trim_to_budget.handle(..., user_id)` loads a `User` row only to return `None` if missing — the route already 401s; `user_id` is otherwise unused. · **Exact change:** drop the parameter and the `User` import. · S · **execute**.
- **03-R40** · `trim_to_budget.py:606` returns a raw `{"error": …}, 400` tuple instead of `api_response.bad_request`; `mode` should be `Literal["preview","apply"]` on the pydantic model (the comment's "clearer error" claim is moot — `has_request_body` already formats validation errors). · S · **execute**.
- **03-R41** · local imports inside handlers that have no cycle to break: `manage_shopping_list.py:76, 242, 275`, `bulk_operations.py:130, 191`, `_line_retention.py:103–104`, `budget.py:437` (duplicate `from flask import request`). R-008. · **Exact change:** hoist. · S · **execute**.
- **03-R42** · `bulk_operations.py:118–122, 237–243` `failed_ids: List[UUID] = None  # type: ignore` + `__post_init__` → `field(default_factory=list)`. · S · **execute**.
- **03-R43** · `manage_shopping_list_attachments.py:151, 171` `UUID(str(shopping_list_id))` on `<uuid:>` path params; bytes route params untyped. · S · **execute**.
- **03-R44** · `compute_list_totals` local names `_Buckets/_Key/_Bucket/_Colours/_ByStore` inside a pure function (the `_Name` style is the codebase's route-local convention). · S · **waive** (style only; tidy if the function is touched).

### C6. Naming & idiom
- **03-R45** · `QuickAddToPrimaryHandler` / `quickAddToPrimaryAsync` — "primary" was retired in P6-01 chunk 2; the handler's own docstring says so. · **Exact change:** `QuickAddToDraftHandler` / `quickAddAsync`. · S · **execute**.
- **03-R46** · `AddLineRequest.quantity ge=1` vs template `ge=0` (templates allow "–" = unspecified). Intentional per `onTemplateQtyBlur`; · **waive**.

### C7. Efficiency
- 03-R4, 03-R12, 03-R17, 03-R34, 03-R36, 03-R38 above.
- **03-R47** · `get_shopping_list_detail` loads **all** `StockLocation` rows when any item has a location (L487–490) — bounded and shared with the breadcrumb helper; · **waive**.
- **03-R48** · `_PriorPurchaseByItem` loads every ticked line ever for the list's items, then their lists, to find the latest done purchase (L522–553). Correct; grows with history. A `MAX(completed_at)` join would be the fix but the repository port has no join — · **FU** (bundle with FU-725's historic-rung e2e coverage: pin the behaviour first, then optimise).

### C8. Design-level findings — out of Stage-2 scope
- **03-D1** · Templates are stock-item-anchored only; product-only lines are silently dropped by snapshot (after 03-R2) and can't be templated. Owner call: is that fine, or should `ShoppingListTemplateLine` gain a nullable `product_id`?
- **03-D2** · `MoveLinesHandler` never merges quantities on a duplicate (comment L123–125 "separate UX decision") — the finish dialog says "Anything already on that list is skipped", so the behaviour is at least honest. Record for the owner.
- **03-D3** · Quick-add target memory is per-tab `sessionStorage` while lists are household-shared — fine for now; note for `MULTI_USER_READINESS.md`.
- **03-D4** · `shopping_lists` has three list-creation paths that name lists three ways (create: NULL/self-label; auto-generate: "Auto N · date"; instantiate: "Template · date"; copy: "Copy of …"). After 03-R8 the remaining question is whether *any* server path should invent a name now that lists self-label (UX-v2). Recommend: none do — owner confirm.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useDragDropList` whole-row DnD (R-022) | pointer drag-reorder | `vuedraggable` / SortableJS | **keep** | — | Already the app-wide shared affordance (ADR-018); touch uses arrows by design. |
| `useLineSections` bucketing | grouping + ordering | lodash `groupBy` | **keep** | — | Pure, spec'd, carries domain rules (Unsorted bucket, availability). |
| `trim_to_budget` tier classifier | rules engine | — | **keep** | — | Five explicit tiers with constants; a rules library would obscure it. |
| `attachment_access` raw Core | ORM bypass | the mapped entity | **replace** (03-R37) | S | Same engine; just use the repository. |
| `budget.period_bounds` | week/month windows | `dateutil.relativedelta` | **keep** | — | Two branches; R-021 handled at the caller. |
| `QuickAddSheet` / `LogPriceSheet` search + rank | client filter | fuse.js | **keep** | — | `includes()` over ≤ a few hundred names; ranking is the point, not fuzziness. |
| `useListState` module cache | nav-state persistence | pinia + `sessionStorage` | **keep** | — | Deliberately reset-on-reload (A8 §3). |

### C10. Standards drift (R-0NN)
- **R-005** · 03-R22 (raw `db` in a feature handler), 03-R37 (Core on a mapped table) — fix.
- **R-008** · 03-R11, 03-R41, 03-R42, 03-R43 — fix.
- **R-019 / R-003** · 03-R13 (level sequence literals), 03-R10 (`"user_id"` literal) — fix.
- **R-021 / R-056** · 03-R8 — fix.
- **R-032** · 03-R6 — fix.
- **R-039** · every `$q.dialog` on this surface carries `noCaps` (page L1954, 2739–2740, 2815, 2844, 2885, 2902–2903; templates L380, 433; `AddToListButton` L397–398, 592–593) — **clean**.
- **R-045** · `useShoppingListExport.openPrintView` uses `window.open(baseUrl…)` — the third of **FU-682**'s three (same as 02-R36). · **execute (FU-682)**; add `useShoppingListExport.spec.ts` mirroring the recipe one.
- **D-010** · `ShoppingListOverviewCard.vue:649` `width 320ms ease-out`, `ShoppingListTemplates.vue:671` `120ms ease` ×2 → `var(--motion-*)` tokens (the plan row already uses them). · S · **execute**.
- **R-002 carve-outs** present and explained: progress track `hsla(0,0%,100%,.55)` (card L634–642), receipt thumb `rgba(0,0,0,0.15)` fallback (`ShoppingListDetail.vue:3243` — has a token first; fine).
- **D-003/D-004** · receipt row amend stepper uses `size="sm"` icon buttons (44px only under `pointer: coarse` via BaseButton) — OK by the shared rule.
- **FU-624 / FU-675** · raw `$q.notify` ×30+, raw `q-select` ×6 (`AddToListDialog.vue:17`, `NewListDialog.vue:28/40/52/114`, `ShoppingListTemplates.vue:194`) — tracked.
- **Owner directive 2026-08-27 (help modals)** · no `(?)` modals on this surface — clean; help chips to add per §B2.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `AddToListButton.iconColour` uses `'accent'` for on_other and `'severity-attention'` for on_multiple — the accent-as-state usage FU-224 is auditing.
- `ShoppingListRailItem.active-class="dora-bg-info-soft"` vs the overview pill's `--semantic-info` — two info tints in one surface.
- Gradient band (`--hero-gradient`) on plan/run faces + the white-veil progress track — check pesto dark and high-contrast.
- `.sl-rail-item-done { opacity: .6 }`, `.sl-row--ticked * { opacity: .6 }`, `.sl-store-chip--none { opacity: .75 }` — opacity dimming over muted ink (D-002 floor) as in 02-C11.

## D. Test plan — Shopping Lists

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__snapshot_template__skips_product_only_lines_and_uses_display_name` | pytest e2e | **must-write-before-ship** | 03-R2 — pins the 500 → skip behaviour and the "Template from None" fix. |
| `test__move_unticked__product_only_lines_move` | pytest e2e | **must-write-before-ship** | 03-R3 — the anchor-key dedupe; the finish dialog's "move to new list" relies on it. |
| `test__membership__ignores_product_only_lines_and_done_lists` | pytest e2e | nice-to-have | 03-R4. |
| `test__quick_add__delegates_to_add_line_dedupe` | pytest e2e | nice-to-have | 03-R5 — nested product line must not count as "already on list". |
| `test__frequently_added__returns_ranked_ids` | pytest e2e | nice-to-have | 03-R6/R14 — replaces the field-shape assertions. |
| `test__instantiate_template__merge_into_list` | pytest e2e | nice-to-have | 03-R33 — new server path. |
| `test__bulk_add__single_commit` | pytest unit | nice-to-have | 03-R34 — count `save_changes` calls on a spy repository. |
| `useShoppingListExport.spec.ts` | vitest | nice-to-have | R-045 fix — mirror `useRecipeExport.spec.ts`. |
| `test__historic_rung__latest_done_purchase_wins` | pytest e2e | nice-to-have | FU-725 — pin before 03-R48 is attempted. |

Not proposed: component tests for the 3,279-line page (drive the three faces once after Stage 2); Playwright flows (owner stance).

## E. Proposed follow-ups (orchestrator allocates ids)

- type=finding · *`POST /shopping-lists/<id>/copy` has no client caller and 500s on product-only lines* (03-R1) — recommended: delete endpoint + unit-of-work test this run; FU only if the owner wants it kept.
- type=follow-up · *Historic-rung lookup loads every ticked line for the list's items* (03-R48) — bundle with **FU-725** (pin first, then optimise); no new entry if FU-725 absorbs it.
- type=finding · *Templates can't carry product-only lines* (03-D1) — owner decision.
- type=finding · *Three server paths still invent list names; lists self-label since UX-v2* (03-D4) — owner confirm "none do".
- type=finding · *Move never merges duplicate quantities* (03-D2) — record only.
- Existing FUs this chunk executes against (tick, don't duplicate): **FU-766** (bulk-tick + has_substitutes), **FU-713** (bulk commits), **FU-714** (partial — NewListDialog), **FU-654** (two more `_current_user_id`), **FU-682** (print view), **FU-780** (page split — plan recorded in 03-R31, execution stays with the FU).

## F. Summary for the register

- FST rows: 16 golden + 13 edge + 4 gate · Help entries: 13 new (group renamed "Shopping"; DoraBot paragraph rewritten — current one names three retired concepts) · Review findings: 48 (execute 38 / FU 3 / waive 5 / conditional 2) · Tests: 9 (must-write 2) · Bugs: 8 (3 product-only-line 500s/skips in copy·snapshot·move, membership None key, quick-add dedupe drift, R-032 null level, template-binding typo, server-local list names)
- One-line: the shopping-list domain is the most carefully reasoned in the app (two documented ladders, one chokepoint per rule, honest money) and the September redesign left it well-componentised on the SPA side — but **product-only lines were bolted on after the list-level operations were written**, so copy, template snapshot, move and membership each still assume `stock_item_id` is set; two unread endpoints and five dead DTO fields linger from the bulk-select bar; the help surface for the whole area is one entry about product search.
