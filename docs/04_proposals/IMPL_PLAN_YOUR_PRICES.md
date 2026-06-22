# Implementation Plan — "Your Prices" intelligence (S2-10 / Phase F)

**Status:** Plan for review · **Date:** 2026-06-18 · **No code yet** — brief + chunks.
**Source proposals:**
- `PROPOSAL_INGESTION_API.md` §2.5 ("Your prices" intelligence layer) + §6 step 4.
- `IMPL_PLAN_PRODUCTS_AS_OVERLAY.md` §S2-10.
- `PRODUCTS_OVERLAY_RUNBOOK.md` Phase F.
**Adjacent:**
- **C-1b (Stock Item Detail)** — `price_observations` + `unit_cost` already on the DTO
  (FU-213 / S1-7). Your-prices baseline + signal slot in alongside them.
- **Price History page** — currently surfaces per-product `ProductHistoricOffer` + current
  `ProductOffer`. The series gains a baseline reference line and an "above usual"
  annotation per product.
- **Phase E (DONE 2026-06-18, pytest-pending FU-189c)** — `Store` rename + `usual_store_id`
  + Stores admin in place; `Product.store` (was `merchant`) is what we join through.
- **R-016 (lazy store hydration)** — any new Pinia store this needs.
- **R-003 (server owns derived domain facts)** — the baseline + signal are server-derived;
  client renders only.
**Decisions locked (2026-06-18 brief — user-confirmed):**
- **Baseline = median** of the unified series (robust to outliers — a single mistyped
  "$99 milk" can't poison the baseline).
- **Threshold = > 1.15 × baseline** for the "paying more than usual" flag.
- **Min samples = 3** before a baseline is computed (below that → "not enough data yet").
- **Baseline window = trailing 12 months**; the full history still renders on the chart.
- **Two pricing data classes, hard distinction (Q4):**
  - **Offers = ingested ONLY.** `ProductOffer` / `ProductHistoricOffer` come exclusively
    through `/api/ingest`. The user does **not** type product offers. (This retracts the
    earlier idea of letting users enter "what I paid for a product" as offer data.)
  - **`StockItemPriceObservation` = the user's real pricing input.** Manually logged on
    stock-item detail, and (pending the Q5 fork below) emitted from shopping close-out.
  - **Everywhere price is analysed or displayed, aggregate `linked-product offers ∪
    stock-item observations`** — the stock-item-level question "what does THIS cost me".
  - **Colour-code source in visualisations** (e.g. Price History): offer-sourced points vs
    observation-sourced points are visually distinct.
  - **Offer-related UI is hidden unless the feature is on** (money/products gating via
    `useMoneyEnabled` + the products data-presence overlay). Observation-sourced "your
    prices" can show whenever money is on, independent of whether any offers exist.
**Phase F basket — what this plan does NOT cover:** FU-210 tail (delete persona preview),
FU-214 (product-surface verify + bulk-select + hard-delete), FU-212 (ingestion docs), FU-180
(preferred-store reassessment). Each gets its own work unit.

---

## 0. Verify-state-first scan (no drift)

Re-checked 2026-06-18:
- **`Product` ↔ `Store` join** via `Product._store_id` (Phase E). `Product.current_offer` +
  `Product.historic_offers` exist and round-trip in get_products / get_stock_item_detail.
- **`StockItemProduct` m2m** is the linked-product join used by stock-item detail.
- **`StockItemPriceObservation`** (FU-213) — per-stock-item rows with `price`, `qty`, `unit`,
  `observed_at`, `source`. Server already exposes `get_stock_item_unit_cost_at()` — the
  single canonical per-unit cost helper (R-003). **Reuse this** for the receipts half of the
  union; never re-derive `price/qty` on the client.
- **`ShoppingListLine`** snapshots — `picked_offer_price` (commit-to-offer moment) +
  `actual_unit_price` (override at tick / receipt entry). Both are **per-unit** for the
  product on `selected_product_id`. Tied to a stock-item via `ShoppingListLine.stock_item_id`.
- **`get_stock_item_detail`** already pre-loads linked products with `current_offer` (Phase E
  changed `merchant` → `store`); the union helper can lean on the same fetch.
- **`price_history.py`** raw-SQL endpoint already joins `Product` → `Store`; it returns per-
  product series. Baseline will hang off this endpoint *per product*.
- **No code today computes a baseline or "above usual" anywhere.** No `your_prices` DTO; no
  median helper.

**Already true (reuse):** `get_stock_item_unit_cost_at`; the Phase E rename means no FK
remapping inside this work; deferred image blobs unaffected.

**Not true yet (build):** unified-series helper; median + signal helpers; new DTO blocks on
stock-item detail + price-history per-product series; SPA surfaces.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### F-1 — Server union helper + median + signal (no UI yet) ★ FIRST
**Delivers:** the canonical `build_your_prices_for_item(stock_item_id)` server helper +
unit-tested baseline/signal math. Nothing user-visible.

- **Backend:**
  - New module `dora_api/features/stock_items/your_prices.py` exposing two functions:
    - `build_your_prices_for_item(repo, stock_item_id) → YourPrices` — unions:
      1. `ProductOffer.price_now` + `ProductHistoricOffer.price_now` for products linked to
         this stock item (via `StockItemProduct`).
      2. `get_stock_item_unit_cost_at(observations)` per `StockItemPriceObservation` row
         for this stock item (reuse the existing helper — R-003).
      3. `ShoppingListLine.actual_unit_price` else `picked_offer_price`, for any line where
         `stock_item_id` matches.
      Yields `(observed_at, unit_price, source_tag)` tuples; sorts ascending.
    - `build_your_prices_for_product(repo, product_id) → YourPrices` — same shape, but
      per-product (no observation join — those are item-level only). Used by Price History.
  - `YourPrices` dataclass:
    ```python
    @dataclass(frozen=True, slots=True)
    class YourPrices:
        baseline: float | None           # median; None when < MIN_SAMPLES
        current: float | None            # latest point's unit_price
        above_baseline: bool             # current > baseline * THRESHOLD (False when either is None)
        sample_count: int
        first_observed_at: datetime | None
        last_observed_at: datetime | None
    ```
  - Constants on the module (so they're discoverable, not stringly-buried):
    `_MIN_SAMPLES = 3`, `_THRESHOLD = 1.15`. **Open** — see §4.
  - Median: `statistics.median(unit_prices)` (Python stdlib; handles odd/even cleanly).
- **Tests** (most important chunk for unit tests):
  - 0 samples → baseline/current None, `above_baseline=False`, `sample_count=0`.
  - 1–2 samples → baseline None (< MIN_SAMPLES), current = latest.
  - 3+ samples — median correct (odd/even); above_baseline correct at the threshold edge.
  - Union dedupe semantics: same `(observed_at, price)` from two sources doesn't get
    double-counted (sources are *additive* per the proposal — no dedupe; document this).
  - Ignores nulls (line with no price snapshot is silently skipped).
- **Risk:** Low. Pure functions over already-loaded entities; no schema change.
- **Close-gate:** R-003 (single canonical per-item helper; never derived client-side); R-007
  (no new tables, no migration).
- **Acceptance:** unit tests pass; `vue-tsc + lint` unaffected (backend-only chunk).

### F-2 — Surface on Stock Item Detail (DTO + SPA)
**Delivers:** `your_prices` block on `StockItemDetailDto`; renders alongside `unit_cost` on
the detail page's price section.

- **Backend:**
  - Add `your_prices: YourPricesDto | None` to `StockItemDetailDto` (alongside the existing
    `unit_cost`). Populated via `build_your_prices_for_item`.
  - DTO mirrors the dataclass (server-derived ISO strings for the dates).
- **SPA:**
  - `models/stockItemDetail.ts` — add the matching `your_prices` field.
  - `StockItemDetailPage.vue` price section — render the "Your usual price" line and, when
    `above_baseline` is true, a small "paying more than usual" warning chip
    (`color="warning"`). Money-gated (consistent with `unit_cost`'s posture).
  - When `baseline === null`: render "Not enough price data yet — log a few receipts" hint
    (R-014 reveal-and-disable: visible state, not a hidden feature).
- **Risk:** Low. Additive on the DTO.
- **Close-gate:** R-002 (Quasar `warning` semantic colour; no hex); R-014 (visible empty
  state copy rather than hiding the row).

### F-3 — Surface on Price History (per-product baseline + chart annotation)
**Delivers:** the existing per-product Price History series gains a baseline reference line
+ "paying more than usual" annotation when the latest point is above 1.15 × baseline.

- **Backend:**
  - `dora_api/features/price_history/price_history.py` — current endpoint already returns
    `series[].current`, `series[].all_time_low`. Add `series[].your_prices: YourPricesDto`
    using `build_your_prices_for_product`.
- **SPA:**
  - `models/priceHistory.ts` (or wherever the SPA-side `PriceHistorySeries` shape lives) —
    add `your_prices`.
  - Price History chart (`PriceHistoryPage.vue`) — overlay a horizontal reference line at
    `your_prices.baseline` when present; show "above usual" chip in the per-series header
    when `above_baseline` is true.
- **Risk:** Low. Additive payload; chart change is one option override on the echarts series.
- **Close-gate:** R-002 (chart line uses theme tokens, not hex); R-003 (baseline value
  comes from the server helper, never recomputed in JS).

### F-4 — Onboarding "Insight" stage (cross-ref FU-184)
**Delivers:** the `OnboardingLoop.vue` (kept post-FU-210-revisit) Insight stage finally has
real content: pull a sample stock item's `your_prices` and render it as the example.

- **SPA only.** No new endpoint — reuses F-2.
- **Risk:** Low. Soft-fails when the install has no data (renders a generic example).
- **Close-gate:** R-014 (visible "data builds up over time" copy when empty).

### F-5 — Verify + log
- Pytest (FU-189c gate + this work's new unit tests). Vue-tsc + lint.
- Coverage-table flip on `PROPOSAL_PRODUCTS_AS_OVERLAY.md`: the L (TBD) feedback bullets
  about "show me how much I usually pay" → ADDRESSED.
- Worklog + CHANGELOG.

---

## 2. State-ownership posture (R-003 check)

| Concern | Where it lives | Notes |
|---|---|---|
| Per-unit cost derivation from `(price, qty, unit)` | Server (`get_stock_item_unit_cost_at`) | Existing. Reuse, don't reimplement. |
| Union of pushed + receipt + observation data | Server (`build_your_prices_for_item`) | New. Single source. |
| Median computation | Server (Python `statistics.median`) | New. Client never sees raw samples for the purpose of computing baseline. |
| "Above usual" decision | Server (`above_baseline` boolean on DTO) | New. Client doesn't apply the threshold; the server tells it yes/no. |
| Chart x/y rendering, chip presentation | Client | Presentation, fine. |
| Threshold value (1.15) | Server (module constant) | Not a domain constant the SPA needs; not duplicated. |

**No client domain math.** The SPA never divides, never compares to a threshold, never
medianses — it reads `baseline`, `current`, `above_baseline` straight from the DTO and
renders.

---

## 3. Distribution & tenancy posture (§7.5 check)

- No new env vars.
- No new auth surface.
- Postgres-portable: no new tables in F-1/F-2/F-3. All queries are on existing tables (which
  already work on Postgres per R-005).
- Degrades gracefully: with zero linked products + zero observations + zero receipts, the
  helper returns a `YourPrices` with `sample_count=0` and the SPA shows the empty-state
  copy. No 500s, no missing-data crashes.

---

## 4. Open questions (decide before F-1 lands)

1. **Threshold value.** Brief locks in **1.15** (15% above median = "above usual"). Real-
   world groceries can swing ~10–20% between weeks. Alternatives: 1.10 (more chatty), 1.20
   (quieter). **Recommend: 1.15** — keep until a real install gives feedback. **Logged as
   FU-226 if changed later.**
2. **Minimum sample count.** Brief locks in **3** (anything less is noise). Alternative: 2
   (more eager). **Recommend: 3.**
3. **Time window.** Should the baseline include data from > 1 year ago? Two cases:
   - **Include all:** truer long-run median; ignores price inflation.
   - **Trailing window (e.g. last 12 months):** more current; needs to be explicit in copy
     ("usual price over the past year").
   **Recommend: trailing 12 months for the baseline; full history visible on the chart.**
4. **Per-product vs per-stock-item series for the chart.** Today the Price History page is
   per-product. Should the baseline line on the *stock-item detail* surface aggregate
   across linked products, or pick a "primary" product? **Recommend: aggregate across all
   linked products + own observations on the stock-item detail surface (it's the
   item-level question — "what does THIS item usually cost me"). Price History stays
   per-product.**
5. **Receipt snapshot priority.** When a `ShoppingListLine` has both `actual_unit_price` and
   `picked_offer_price`, the proposal already favours `actual_unit_price` (the "what I
   actually paid" wins over "what I planned to pay"). The union helper should match.
   **No change from the proposal.**

---

## 5. Sub-chunk size / order

| Chunk | Backend LOC | SPA LOC | Risk | Tests |
|---|---|---|---|---|
| F-1 (helper + math) | ~150 | 0 | Low | High value — unit tests |
| F-2 (stock-item detail surface) | ~30 | ~80 | Low | Backend mostly covered by F-1 |
| F-3 (Price History surface) | ~30 | ~60 | Low | Same |
| F-4 (Onboarding stage) | 0 | ~60 | Low | UI smoke only |
| F-5 (verify + log) | 0 | 0 | — | Pytest + lint pass |

**Suggested order:** F-1 standalone (gets the math reviewed in isolation), then F-2 + F-3 in
either order, F-4 last (depends on F-2's DTO shape stabilising). F-5 wraps each session.

---

## 6. Feedback coverage (per CLAUDE.md cross-check rule)

| Bullet | Source | Status under this plan | Notes |
|---|---|---|---|
| L-?? "show me how much I usually pay" | (TBD — confirm in `Feedback _ Fixes - as of [DATE].md`) | ADDRESSED by F-2 | The user-facing "Your usual price ~$X" line |
| L-?? "warn me when something jumped" | (TBD — confirm) | ADDRESSED by F-2 + F-3 | The "paying more than usual" chip |
| FU-184 (onboarding Insight stage placeholder) | DORA_FOLLOWUPS | ADDRESSED by F-4 | The stage has real data backing it |

**Open before F-1:** find the exact L-numbers in `docs/02_feedback/Feedback _ Fixes - as of
[DATE].md` that this addresses and fill the rows. (Currently coded as TBD; not blocking the
backend chunk.)

---

## 7. Dependencies + sequencing notes

- **FU-189c (Phase E pytest)** — recommended to land BEFORE F-1's pytest run, so any Phase E
  fallout is visible in isolation. If pytest hits Phase E fixtures that need the new `Store`
  shape, F-1's tests would inherit a misleading red.
- **No dependency on FU-190** (ingestion store-mapping enforcement) — F-1 reads from already-
  ingested rows; it doesn't care how they got there.
- **FU-180** (preferred-store reassessment) is now informed by this work: if `usual_store_id`
  + `your_prices` together cover what a "preferred store" affordance would offer, FU-180
  closes as "covered". Worth revisiting after F-2 lands.
