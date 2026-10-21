# Implementation Plan — State Ownership Refactor (C-impl)

**Status:** Plan for review · **Date:** 2026-06-06 · **No code yet** — phased plan + first chunk.  
**Source proposal:** `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (2026-06-04).  
**Phase:** Master plan **Phase 1 enabler — land before/with the shopping-list +
cook-mode work** (it gives them a single source of truth to compute against).

---

## 0. Verify-state-first: drift since the proposal

Re-checked the code 2026-06-06. The proposal's diagnosis is ~95% accurate, with
two material drifts that **shrink the early work**:

- **Recipe ingredient DTO already carries `stock_level_id`**
  (`get_recipes.py` `RecipeIngredientDto`). The proposal said the payload lacked
  the stock level — no longer true. The §3.2 foundation is half-built.
- **A sequence-based status notion already exists server-side** —
  `attention.py` `LOW_STOCK_SEQUENCE = 2` / `OUT_OF_STOCK_SEQUENCE = 3`, consumed
  by `get_alerts.py`. But it's **scattered and re-defined** (`attention.py`,
  `assistant/tools.py`, and client `doraIntents.ts` all redeclare the constants),
  and the **client still can't see sequence/booleans** on the DTOs it gets, so it
  string-matches `'Out of Stock'`.
- **`?cookable=true` is already referenced by the client**
  (`doraContextualActions.ts`) but **not implemented server-side** — a dangling
  contract to honour.
- The `"Out of Stock"` literal is in **~28 spots** (server + client), not ~8.
- **No `cookable` / `missing_count`** on the recipe DTO (accurate).
- All **7 client cookable/missing reimplementations still live**.

Net: the keystone (§3.1) is *partially present but un-consolidated*; the first
chunk is "finish + unify what's started," not "build from zero."

---

## 1. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Canonical stock-status contract  ★ FIRST REVIEWABLE CHUNK
The keystone (§3.1). Load-bearing; land first with tests.
- **One server module** owns the status definition, keyed to **`StockLevel.sequence`
  (identity), never the name.** Consolidate the scattered constants
  (`attention.py`, `assistant/tools.py`) into it; it's the single import site.
- A function `status_of(stock_level) → {out_of_stock | low_stock | in_stock}` (+
  helpers `is_out_of_stock` etc.), with an explicit **"missing" policy** (out-only
  vs out+low — open decision §3.1).
- **Migrate the server name-hardcodes to consume it:** `get_dashboard_summary.py`
  (`OUT_OF_STOCK_NAME`), `waste.py:259`, `reports.py:459`, `assistant/confirm_actions.py`.
  (Seed/migration `StockLevel(name=…)` rows stay — they define the levels.)
- **The contract also owns thresholds** (the audit addendum §8.2): fold
  `EXPIRING_SOON_WINDOW_DAYS` (and the low/out sequence constants re-declared in
  `assistant/tools.py` + client `doraIntents.ts`) into this one module, so there's
  a single source for both statuses *and* their windows. (Exposing the window to
  the client is Chunk 2/3's DTO/`/config` work — Chunk 1 just consolidates.)
- **Tests pin behaviour under a level rename** — renaming "Out of Stock" must not
  change any count or bucket. This test is the whole point.
- **No client change, no DTO change yet** — pure server consolidation.
- *Risk:* touches dashboard/alerts/waste/reports; the rename-test is the guard.
- *Acceptance:* all server "out/low" decisions flow through one module; rename
  test green; no behaviour change.

### Chunk 2 — Derived status on DTOs + cookable/missing (§3.2)
- Add **derived booleans (or a `status` enum)** to the stock-item DTO and the
  recipe **ingredient** DTO (which already has `stock_level_id` — add the booleans
  so the client stops needing the stock-level table at all).
- Add to **`RecipeDto`**: `missing_count`, `cookable` (= `missing_count == 0`),
  and `missing_stock_item_names` — computed **set-based** in `get_recipes.py` (it
  already loads ingredients + `stock_level_id`): bucket stock items once, join,
  **no N+1** (proposal §5 perf note).
- *Risk:* overview perf — must be the single-query bucket approach, mirroring how
  the dashboard already counts. Pin with a query-count test on the list endpoint.

### Chunk 3 — Query support (§3.3)
- Implement **`GET /api/recipes?cookable=true`** (+ inverse / `max_missing=N`) —
  honour the contract the client already calls (`doraContextualActions.ts`).
- Add **`cookable_count`** to the dashboard summary so "cookable tonight" shows a
  number without pulling the full list.

### Chunk 4 — Delete the client copies  (the visible "it got simpler" win)
- Remove the **7** `isMissing`/`isCookable` reimplementations and the **~14 client
  `'Out of Stock'` literals** (RecipesOverview, RecipeCard, RecipeDetailPage,
  MealPlansOverview, DashboardPage, DoraChat, doraContextualActions, + the
  string-match spots). Read the server fields / query instead.
- *Risk:* low once Chunks 2-3 land; high visibility. Do surface-by-surface.

### Chunk 5 — Type B server aggregates
- Add primary-list **$ totals / savings**, **best deals**, **use-soon** figures to
  the dashboard summary (or focused endpoints — open §3.3); delete the client
  joins (`DashboardPage.vue` `primaryListStats`).
- Per the audit addendum (§8.2): the **budget card** must stop re-fetching the
  primary list + re-summing what `budget.py:183-196` already computes — expose the
  totals; and **"best deals"** becomes a `?sort=discount&limit=N` (or focused
  endpoint) instead of downloading all products to sort client-side
  (`DashboardPage.vue:1198-1212`). Also fold the inline discount-% copy back onto
  the shared helper (tiny Type-C dedup).

### Chunk 6 — Type C: snapshot offer at ADD (data-model fix)
- Snapshot the offer (or store an offer ref) **when a line is added**, not only on
  tick (`manage_shopping_list_lines.py`). **Overlaps the shopping-list finish/
  restock transaction** — coordinate with `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 1 so
  the snapshot/audit story is built once.

### Chunk 7 — Type D (optional, lowest priority)
- Persist sorts/filters to **URL/localStorage** where it improves shareability;
  **don't** push them server-side. The undo-stack persistence is likely not worth
  doing.

---

## 2. First reviewable chunk — definition of done

**Chunk 1 (canonical stock-status contract).**
- New server status module; `attention.py` + `tools.py` constants collapsed into it.
- `get_dashboard_summary`, `waste`, `reports`, `confirm_actions` consume it (no
  more `== "Out of Stock"` on the server).
- Tests: (a) rename a stock level's `name` → all counts/buckets unchanged; (b) the
  "missing" policy (out-only vs out+low) is asserted explicitly.
- Zero client change, zero DTO change, zero behaviour change. Pure, safe keystone.

---

## 3. Risks & open decisions

**Risks** (proposal §5 + drift):
- The contract is load-bearing — Chunk 1 first, with the rename test, before any
  consumer migrates.
- `cookable` perf — set-based query only (Chunk 2); pin query count.
- **Don't over-correct Type C/D** — resist relocating the discount helper or
  pushing sort-order into the API. The triage table is the guardrail.
- Drift cleanup: fold the scattered-constants consolidation into Chunk 1 rather
  than leaving a fourth copy.

**Open decisions** (proposal §7):
1. **"Missing" = out-only, or out+low?** (Today client keys strictly on out; but
   `MealPlansOverview`/`RecipeCookMode` already also count low — so the codebase is
   inconsistent. Pick one named policy in Chunk 1.)
2. **Does `cookable` consider quantity** (enough flour, not just "have flour")?
   Today neither side does — decide whether Chunk 2 introduces it or explicitly
   defers (recommend defer; note it).
3. **Type B:** extend `/dashboard/summary` (one round-trip, fatter DTO) vs focused
   endpoints?

---

## 4. Coverage & motivation

Architecture/plan-motivated (the "single source of truth, more in the backend"
technical-considerations bullet, and the silent-staleness behind the stock-overview
nav-lag coupling), not a per-surface feedback list. Relevant inputs:

| Input | Where |
|---|---|
| "Single source of truth, more in the backend" (Technical Considerations) | The whole plan; Chunks 1-4 |
| Stock-overview "fetch everything to filter" coupling (INV-2 mount fan-out) | Chunk 3 (query instead of fetch-all) |
| Offer-snapshot "what did I mean to pay?" (INV-1 backend-only fields) | Chunk 6 (Type C) |
| Recipe cookable/missing surfaces (C-4 card/detail) | Chunks 2-4 (server-owned, client deletes copies) |
