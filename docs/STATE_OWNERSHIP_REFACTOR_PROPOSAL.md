# State Ownership Refactor Proposal

**Status:** Draft for discussion
**Date:** 2026-06-04
**Scope:** App-wide. Establishes where derived state lives (server vs. client), pulls cross-entity domain logic back to the server, and fixes the silent-staleness and drift that result from the current split. Companion to `SHOPPING_LIST_REDESIGN_PROPOSAL.md`.

---

## 1. Why

A scan of every major domain (stock, recipes/meals, products/pricing, dashboard) found the *same* root smell named as the worst issue in three of four: **business logic that should be owned by the server is recomputed in the browser**, in multiple places, and silently goes stale. Update a stock level on your phone and your laptop's "cookable tonight" count is wrong until a hard refresh.

But "move client logic to the server" is the wrong blanket prescription. Reading the code closely, what looks like one problem is **four distinct categories with different correct fixes**. Conflating them would produce a bad refactor (e.g. relocating display math that's fine where it is, or shoving sort-order into an API). This proposal triages them.

### The smoking gun

The definition of "out of stock" is the literal string `"Out of Stock"`, hardcoded **independently** on the server and the client:

- Server: `get_dashboard_summary.py:31` — `OUT_OF_STOCK_NAME = "Out of Stock"`, with a comment noting it falls back to count=0 if a level is renamed.
- Client: `RecipesOverview.vue:443` — `stockLevels.value.find((l) => l.name === 'Out of Stock')`, also with fallback logic.

The same domain constant lives in two languages, in ~8 spots, each guarding against the other drifting. Rename a stock level in the UI and the dashboard counts and the "cookable" filters can silently disagree. That is the state-split made tangible — and the contract in §3.1 exists to kill it.

---

## 2. The four categories (verified)

### Type A — Derived domain facts the server doesn't expose *at all*

**Flagship: "cookable / missing ingredients."** The backend has *zero* concept of cookability (confirmed: no `cookable` / `missing` logic anywhere in recipes / meals / dashboard features). So the client reinvented it in **7 locations** (`RecipesOverview.vue`, `RecipeCard.vue`, `RecipeDetailPage.vue`, `MealPlansOverview.vue`, `DashboardPage.vue`, `DoraChat.vue`, `doraContextualActions.ts`). `RecipesOverview.vue:440` literally comments that the duplication is deliberate ("so filter logic doesn't depend on a component being mounted").

To compute it, the client must:
1. fetch every stock item (for `stock_item_id → stock_level_id`),
2. fetch every stock level to find the one named `'Out of Stock'`,
3. walk each recipe's ingredients and join.

The recipe payload carries `stock_item_name` but **not** the stock level, so the join is unavoidable client-side. This is a cross-entity domain rule (recipe × ingredient × stock level) with no business in the browser, let alone in seven copies.

**Fix → full server ownership.** (Detail in §3.)

### Type B — Cross-entity aggregation joined client-side

The dashboard summary DTO deliberately returns *counts* (server-aggregated — this part is correct), but **no money and no deals**. So the dashboard separately fetches the full primary-list detail and sums prices/savings in the browser (`DashboardPage.vue:1190`), and recomputes "best deals on saved products" and "use soon" similarly. Same shape as Type A (the server should own the number) but it's *aggregation*, not a *rule*.

**Fix → extend server aggregation.** Add the derived figures to the relevant summary endpoints.

### Type C — Single-source client logic that's *fine to keep* — but has a real bug

Discount %, unit price, and on-special are **not** sprawled — they're centralized in one helper, `scrapedProductOfferLogic.ts`, used everywhere. Computing a *display* discount on the client from server-provided `price_now` / `price_was` is defensible and not worth relocating.

The genuine defect is elsewhere: a shopping-list line snapshots the offer price on **tick**, not on **add** (`manage_shopping_list_lines.py:117-131`). If a price moves during planning (added Monday, ticked Saturday), the intent is silently lost; if the line is never ticked, both snapshot fields are NULL and "what did I mean to pay?" is unanswerable. That's a **data-model** bug, not a state-location bug.

**Fix → leave the math on the client; fix the server data model** (snapshot at add-time, or store an offer reference on the line at creation).

### Type D — Ephemeral UI state that should *persist* but isn't

Shop-mode skip order, stock-map layout + undo/redo stacks, sort / filter / bulk-selection across stock and recipes — all revert on refresh. But "the server should own this" is mostly **wrong** here. Sort order, expand/collapse, and filters are legitimately client concerns; they need `localStorage` or URL params, not an API. (Encoding filters in the URL also makes filtered views shareable/deep-linkable — a bonus.) Stock-map *layout* is already persisted via a debounced save; only its undo stack is volatile, which is a save-reliability issue, not a state-ownership one.

**Fix → persist locally (localStorage / URL), not server-side.** Lowest priority; the undo-stack persistence may not be worth doing at all.

---

## 3. The Type A fix in full (cookable / missing)

The decision is to go all the way: DTO fields, a shared status contract, *and* a queryable filter.

### 3.1 A single server-owned stock-status contract

Define stock statuses once, server-side, as the authority — replacing the duplicated `"Out of Stock"` string literals on both ends.

- A canonical enum / lookup (`out_of_stock`, `low_stock`, `in_stock`, …) keyed to stock-level identity, **not** to the display name. Renaming a level's label must not change behavior.
- Expose the mapping (or, better, expose only *derived booleans* like `is_out_of_stock` on stock-item DTOs) so the client never matches on a level name again.
- Every server feature that currently hardcodes the name (dashboard buckets, alerts, auto-generate's low/out sources) consumes this one definition.

This is the keystone: it removes the drift risk and gives Type A/B a single source of truth to compute against.

### 3.2 Derived facts on the DTOs

The recipe DTO (and meal DTO) gain server-computed:
- `missing_count: int` — distinct ingredients whose stock item is out of stock.
- `cookable: bool` — `missing_count == 0`.
- optionally `missing_stock_item_names: list[str]` for the "you're missing X, Y" UI.

Computed server-side via the §3.1 contract, in the same query that already loads ingredients. The client deletes all 7 copies and reads the field.

### 3.3 Queryable filter

- `GET /api/recipes?cookable=true` (and the natural inverse / `max_missing=N`) so the overview, dashboard "cookable tonight" card, and Dora chat **query** for cookable recipes instead of fetching *all* recipes + *all* stock items + *all* stock levels and filtering in memory.
- The dashboard summary gains a `cookable_count` so the card shows a number without pulling the full list.

This removes the "fetch everything to filter" pattern, which today couples every cookable surface to a full stock-table download.

---

## 4. Triage summary

| Type | Example | Correct fix | Priority |
|---|---|---|---|
| **A** Derived domain rule, server-absent | cookable / missing (×7) | Server owns: contract (§3.1) + DTO fields (§3.2) + query (§3.3) | **High** |
| **B** Cross-entity aggregation client-side | primary-list $ totals, best deals, use-soon | Extend server summary/aggregation endpoints | High |
| **C** Centralized client math + model bug | discount display OK; offer snapshot timing | Keep client math; fix data model (snapshot at add) | Medium |
| **D** Ephemeral UI state lost on refresh | shop-mode skip, sorts, filters, undo stack | Persist locally (localStorage / URL); not the server | Low |

The principle to encode going forward: **the server owns derived domain facts and cross-entity aggregates; the client owns presentation and ephemeral view state.** A/B are violations of the first half; C/D are not server problems at all.

---

## 5. Risks & trade-offs

- **The contract (§3.1) is load-bearing and touches many features** — dashboard, alerts, auto-generate, and the new recipe fields all depend on it. Land it first, with tests pinning the derived booleans, before migrating consumers.
- **Performance of `cookable` on the server.** Computing `missing_count` per recipe is a join over ingredients × stock items. Fine for one recipe; for the overview it must be a set-based query, not N+1. Worth a single query that buckets stock items once and joins, mirroring how the dashboard already counts buckets.
- **Don't over-correct Type C/D.** Resist the temptation to relocate the discount helper or push sort-order into the API during this sweep — that's scope creep and would make things worse. The triage table is the guardrail.
- **Client deletions are the easy win.** Removing 7 copies of `isMissing` and the `'Out of Stock'` literals is low-risk once the server field exists, and is the most visible "this got simpler" outcome.

---

## 6. Suggested sequencing

1. **Stock-status contract (§3.1)** — server-side canonical statuses + derived booleans on stock-item DTOs; migrate the existing server hardcodes (dashboard, alerts, auto-generate) to consume it. Tests pin behavior under a level rename.
2. **Recipe/meal DTO fields (§3.2)** — `missing_count` / `cookable`, computed via the contract.
3. **Delete the client copies** — remove the 7 `isMissing`/`isCookable` reimplementations and the `'Out of Stock'` literals; read the server fields.
4. **Query support (§3.3)** — `?cookable=true` + `cookable_count` on the dashboard summary; switch the cookable surfaces to query.
5. **Type B aggregates** — add primary-list totals / deals / use-soon figures to server endpoints; drop the client joins.
6. **Type C model fix** — snapshot offer at add-time (own workstream; overlaps the shopping-list redesign's finish/restock transaction).
7. **Type D (optional)** — persist sorts/filters to URL/localStorage where it improves shareability.

---

## 7. Open questions

- Does "missing" mean only *out of stock*, or should *low stock* also count as missing for cookability? The current client code keys strictly on `'Out of Stock'`; the contract should make this an explicit, named policy.
- Should `cookable` account for ingredient *quantity* (enough flour, not just "have flour")? Today neither client nor server does — worth deciding whether the server fix is the moment to introduce it, or explicitly defer.
- For Type B, extend the existing `/dashboard/summary` payload, or add focused endpoints? Bigger summary = one round-trip but a fatter, more coupled DTO.
