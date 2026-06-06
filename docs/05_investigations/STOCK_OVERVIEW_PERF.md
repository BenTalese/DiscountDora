# STOCK_OVERVIEW_PERF — INV-2

**Date:** 2026-06-06  
**Type:** Read-only investigation. No code changes.  
**Purpose:** Explain (a) what makes the stock overview slow to mount, and
(b) what the "DS4 animations" task changed about *perceived* performance.

---

## TL;DR

- **The premise "it loads all 500+ items" is wrong — the opposite is true.**
  The frontend fetches only **page 1 (≤50 items)** and never loops. With >50
  stock items the overview silently drops the rest. This is a latent
  **correctness bug**, logged as a follow-up.
- The real mount cost is **7 parallel API calls** plus **per-row O(N) lookups**
  (recipe usage + shopping-list membership computed inside every row), not a
  giant item fetch.
- **DS4 did not make anything faster.** It added enter/leave transitions, hover
  motion, and loading-state fades that make the same latency *read* as
  deliberate motion instead of a stuck screen. Perceived-perf masking —
  confirmed.

---

## (a) What actually happens on mount

### The fetch fan-out — `StockOverview.vue:647-656`

Mount fires **7 calls in parallel** via `Promise.all` (good — not a waterfall):

| Call | Endpoint |
|---|---|
| `stockItemStore.getStockItemsAsync()` | `/stock-items` (page 1, **limit 50**) |
| `stockLevelStore.getStockLevelsAsync()` | `/stock-levels` |
| `stockLocationStore.getStockLocationsAsync()` | `/stock-locations` |
| `shoppingListStore.refreshAsync()` | `/shopping-lists` + `/shopping-lists/membership` (2 calls) |
| `recipeStore.getRecipesAsync()` | `/recipes` |
| `loadStockGroups()` | `/stock-groups` |
| `loadStocktakeCount()` | stocktake queue endpoint |

So it's really **8 HTTP requests**. Time-to-interactive is gated by the slowest,
and several of these (recipes, membership) exist only to power per-row badges.

### The silent 50-item cap — **the real correctness finding**

- Backend `get_stock_items.py:79-82` paginates correctly:
  `handle()` → `.paginate(options, …)` returns a `Page[StockItemDto]`.
- Defaults (`query_options.py:24-25`): `DEFAULT_LIMIT = 50`, `MAX_LIMIT = 500`.
- Frontend `stockItemApiService.ts:39-40`: `getAllAsync()` hits `/stock-items`
  **with no query string** → page 1, limit 50.
- Store `stockItemStore.ts:48-53`: takes `page.items` and sorts them. **It does
  not read `page.total`, does not loop subsequent pages.**

**Consequence:** a pantry with >50 items shows only the first 50 alphabetically.
The rest are invisible to filters, counts, and the list. This is almost
certainly not intended and is a bug independent of perf.

> This also means the "slow because it renders 500 rows" theory doesn't hold —
> at most 50 rows render today. The lag comes from the fan-out + per-row compute,
> not list size.

### Backend query cost — fine

`get_stock_items.py:70-77` eager-loads level/location/group via the repository's
`contains_eager` path (`sqlalchemy_repository.py`). **No N+1.** The query is
cheap; it's not the bottleneck.

### Per-row compute — the genuine client cost

Each `StockItemRow.vue` and the `useStockFilters.ts` composable compute, per
item:
- recipe-usage lookup (scans `recipes.value` for matches),
- shopping-list membership (scans the membership payload),
- expiry/colour state,
- level-sequence ordering.

When these are recomputed per row (rather than from a prebuilt `Map`), the cost
is O(items × recipes) and O(items × membership) on every filter keystroke. At 50
items this is tolerable; it's the part that would actually bite if the 50-cap
were lifted naively.

---

## (b) What DS4 changed — perceived, not real

DS4 (commit ~`2e7c30b`, "DS4 animations") added motion, not speed:

- `web_app/src/css/motion.scss` — motion tokens (`--motion-fast: 120ms`,
  `--motion-normal: 200ms`, `--motion-slow: 320ms`).
- New transition components: `ListTransition.vue`, `FadeTransition.vue`,
  `ScaleTransition.vue`, `SlideUpTransition.vue`.
- `StockOverview.vue` — item list wrapped in `<ListTransition>`; items now fade +
  slide in (`opacity` + `translateY(12px)`, 200ms) instead of snapping in.
- `StockItemRow.vue` — hover transition retimed to `--motion-fast` with a
  `translateY(-1px)` lift.
- Dashboard etc. — `FadeTransition mode="out-in"` on loading states,
  `AnimatedNumber` for value changes.

**Effect:** before DS4, the page rendered instantly but data arrived 1–3s later,
so the gap read as *broken/stuck*. After DS4, the same gap is bridged by a
loading fade and the items *glide in* when data lands — the motion reads as
*intentional*, so it "no longer feels laggy." The underlying latency is
unchanged.

---

## Optimisation options (prioritised)

### Correctness first (no-regret)
1. **Fix the 50-item cap** (`stockItemStore.ts:48`). Options, cheapest first:
   - request `?limit=500` to match `MAX_LIMIT` (one-line, unblocks most users);
   - or loop pages until `page.items.length < limit`;
   - or move to real infinite-scroll/virtualised paging (best long-term, more work).
   Pick based on expected pantry size. **This is a bug fix, not just perf.**

### Real latency (no-regret / low cost)
2. **Defer secondary loads.** Paint the item list as soon as items + levels land;
   load recipes, groups, and stocktake count in a second wave
   (`StockOverview.vue:647-656`). Improves time-to-interactive.
3. **Prebuild lookup maps once.** Ensure `recipesByStockItem` and `cartStateById`
   in `useStockFilters.ts` are `Map`-based O(1) lookups built once per data
   change, not recomputed per row/keystroke.

### Bigger
4. **Server-side aggregation** (per the State-Ownership proposal): return
   recipe-usage and cart-state flags in the `StockItemDto` so the client doesn't
   join client-side at all. Removes the recipes + membership fetches from the
   mount fan-out entirely.
5. **Virtualise the list** (`q-virtual-scroll`) — only worth it *after* the
   50-cap is lifted and large pantries actually render many rows.

---

## Key file references

| Concern | File | Lines |
|---|---|---|
| Mount fan-out (8 requests) | `web_app/src/pages/StockOverview.vue` | 647-656 |
| List render (transition wrap) | `web_app/src/pages/StockOverview.vue` | 238-258 |
| Frontend fetch (no params) | `web_app/src/services/api/stockItemApiService.ts` | 39-40 |
| Store takes page 1 only | `web_app/src/stores/stockItemStore.ts` | 48-53 |
| Backend pagination (correct) | `dora_api/features/stock_items/get_stock_items.py` | 79-82 |
| Pagination defaults | `dora_api/infrastructure/query_options.py` | 24-25 |
| Per-row / filter compute | `web_app/src/composables/useStockFilters.ts` | ~165-245 |
| Per-row badges | `web_app/src/components/stock/StockItemRow.vue` | ~232-253 |
| DS4 motion tokens | `web_app/src/css/motion.scss` | 1-88 |
| List transition | `web_app/src/components/transitions/ListTransition.vue` | — |

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "1–3s nav lag, worst on stock overview" | Caused by the 8-request mount fan-out + per-row O(N) lookups; **not** large list size (capped at 50). Fix: defer secondary loads + prebuilt lookup maps. |
| "no longer feels laggy after DS4" | Confirmed perceptual: DS4 added fade/slide + hover motion + loading fades that mask unchanged latency. |
| (discovered) Overview silently shows only 50 items | New correctness bug — `getStockItemsAsync` never pages past the first 50. Logged as a follow-up. |
