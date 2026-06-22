# Implementation Plan — "Your Prices" intelligence (Phase F / S2-10)

**Status:** Plan for execution · **Rewritten:** 2026-06-22 after the pricing-system
reassessment (handoff: [`docs/99_scratch/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md`](../99_scratch/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md)).
**Supersedes:** the prior F-1..F-5 chunking in this file (the reshape adds a conversion
helper, a folded observation shape, a shared `PriceEntry`, and a harvest path — the
prior chunks assumed none of these).

---

## 0. Decision record — ratified 2026-06-22 (carry into every chunk)

Lifted verbatim from the handoff doc's §6 / §6a / §6b. Reasoning lives there; this
section is the locked truth for execution.

### Data model
- **A1 — folded `{total_price, total_measure, unit}`** (count is a UI input at entry,
  not stored). One canonical per-unit truth; eliminates the "two 12-packs vs one
  24-pack" ambiguity. The shopping line still carries the count shape; the observation
  is a *price record*, not a purchase record (§6a).
- **A2 — nullable `store_id`** on observations (one-way door). Surface it in the
  widget ("Last seen $5.00 at Coles") and the bottom-sheet history.
- **A3 — `observed_at` user-editable**, default now.
- **A4 (revised) — drop the `source` enum field entirely; add nullable
  `shopping_list_line_id` FK (ON DELETE SET NULL)**. Provenance via FK is strictly
  more information than an enum (line → list → store → product → date all
  transitively available). The `source` field was only ever used for labelling; the FK
  labels better.

### Units & conversion
- **B1 — supported dimensions = volume + mass + count** ("ea"/"pack"/"dozen" with
  fixed factors, no cross-dimension conversion). The count dimension is new — today's
  engine has none.
- **B2 — extract the conversion engine to one shared server-owned domain helper**;
  delete the SPA-side `_UNIT_TABLE` duplication in `doraIntents.ts`. SPA fetches the
  table from the server (or a generated TS file from the Python source) for instant
  entry validation. Single source of truth — no drift.
- **B3 (revised) — flat global unit list grouped by dimension. NO smart per-item
  defaults, ever.** Predictability beats cleverness. **Instead — last-time prefill for
  the unit choice** (if you logged milk in litres last time, the dropdown opens on
  "L" next time), consistent with the rest of the prefill story (F2).
- **B4 — baseline is per-dimension.** "Usual price" uses the dimension of the
  most-recent observation; mixed history is shown but never blended.

### Baseline / "Your prices"
- **C1 — median** (locked) — over the normalized per-unit series.
- **C2 — 1.15× / min 3 samples / trailing 12 months** (locked from the prior brief).
- **C3 + LC-2 — baseline = observations only. UI is source-blind.** The widget says
  "Based on N prices" (one count), not "8 observations · 3 offers" (which makes the
  user ask what counts). For the products minority, offers appear as a **separate
  sidecar** ("Current shelf prices: $4.99 at Coles · $5.20 at Woolworths"), never
  folded into baseline math or count chrome. Rationale: a flash-sale to $3 doesn't
  poison your baseline; enabling products later doesn't unprovokedly shift it.
- **C4 — "$1.30 cheaper than last time · about average"** — show both.
- **C5 (revised) — two scopes, two surfaces, no new route:**
  - **(a) Inline widget** on stock-item detail (money-gated). Shape:
    ```
    Usually $5.20 / L  · about average
    Last seen $5.00 (2d ago, Coles)
    Based on 8 prices
                       [Log a price] [Full history]
    ```
    When `sample_count < 3`: "Not enough price data yet — log a few." with the same
    `[Log a price]` affordance.
  - **(b) "Full history" → bottom-sheet** (Quasar `q-dialog` `position="bottom"`,
    full-width on mobile). Embeds the existing `PriceHistoryChart` scoped to this
    stock-item's unioned series (offers ∪ observations, colour-coded per D2). NOT a
    new route, NOT a drawer. Surface preference is on record:
    [L226](../02_feedback/Feedback%20_%20Fixes%20-%20as%20of%20%5B06-Jun-2026%5D.md).
  - **(c) Existing `/price-history` page stays in its per-product multi-compare role.**
    Picks up F-3 (baseline reference line + above-usual annotation) and H2
    (observation-capable when products off).

### Offers ↔ observations (the union)
- **D1 — Idea A.** Offers and observations are two separate substrates, **unioned
  only at read time, never converted.** No god-object.
- **D2 — colour-coding via theme tokens (R-002):** observations = solid line + dots
  ("your data"); offers = lighter/dashed ("context"). Legend names them. With
  products OFF, observations only.
- **D3 — prefill priority:** most-recent across {observations, your last receipt}; a
  selected offer prefills only when explicitly picked on the line; every prefill
  shows its source.

### Shopping list integration
- **E1 — prefill-and-persist** (no shop-mode bulk copy). Line shows the prefilled
  price (display-only, source-labelled); first edit persists to the line; nav
  away/back reads the persisted value. Replaces the old "copy on shop mode" idea.
- **E2 — prefill hint visible on draft lists too** (money-on); harvest only at
  completion.
- **E3 (revised) — `/finish` is the ONLY completion path.** Code trace confirmed the
  SPA never sends `PATCH status=done`. **Remove the dead branch entirely** (no
  hard-restrict halfway), add a pytest asserting the route now 400s on that input.
  Single source of truth for "list becomes a receipt".
- **E4 — sizeless/product-less line harvest:** count-dimension observation
  ("$X for N ea") when no pack size; measure observation when a sized product is
  selected. B1's count dimension makes this expressible.
- **E5 — user enters total paid for the line at the till**; widget knows count from
  `quantity`; per-unit derived server-side. One number.
- **E6 — product-less line UI (products OFF):** name, qty, preferred-buy hint,
  prefilled editable price.

### Price-entry widget (shared)
- **F1 — ONE shared `PriceEntry` component** across the row quick-log, stock-item
  detail, quick-add, and the shopping line (R-001). Two modes, one persisted shape:
  - *Shelf-price mode* (row button): `price + size + unit` only. Count not rendered.
    Three inputs, one preview ("$5/L").
  - *Harvest mode* (shopping line at completion): `total_price + size + unit`; count
    comes from the line's `quantity`; size from the selected product (or `ea` for
    sizeless). One number at the till.
  - Both write the folded `(total_price, total_measure, unit)` shape.
- **F2 — fields prefill from latest observation** so the common case is "confirm one
  number". Source label visible per prefill.
- **F3 — inline % +/- + "usually costs / cheaper than last time"** on change (C4).

### Row button
- **G1 — `mdi-cash-plus`** ("add a price"). Fall back to `price_check`
  (`mdi-cash-check`) only if avoiding a new icon.
- **G2 — left of expiry, money-gated, `RowActionButton`** (R-001 — no hand-rolled
  `q-btn`).
- **G3 — tap → full `PriceEntry` popover prefilled, one visible "Log".**

### Visualisation
- **H1 — staged inside the first build** (LC-5): chunk 3 lands the inline widget;
  chunk 6 lands the bottom-sheet + per-product `/price-history` work.
- **H2 — Price History observation-capable** with products OFF (today it's
  offer-only → empty when no products exist).

### Feature gating & naming
- **I1 — "Receipt" relabel money-gated.** "Done" lists relabel to "Receipt" only
  when money feature is on. Pure label swap, no behaviour change.
- **I2 — defer the offer-prices-without-money-check inconsistency to FU-182**
  (R-007 scope). Do not expand this work into a products-gating sweep.
- **I3 — observation endpoints stay UI-gated only**, per today's posture.

### Ingestion
- **J1 — remove the `stock_item_ref → observation` ingestion branch** (observations
  in-app only). Keep `product_ref`/`offers[]`. A producer still sending
  `price_observations[]` then 400s (the user controls the only producer).

### Migration & scope
- **K1 — wipe/rebuild existing free-text-unit observations** (pre-release;
  non-preserving migration is fine — user memory + R-006).
- **K2 — extract the duplicated `actual→picked` ladder** while here. 4× duplicated
  today (`budget.py:80`, `assistant/tools.py:2425`, `waste.py:127`, `reports.py`
  spend/savings); harvest would be the 5th caller. Extract to one helper (R-003).
- **K3 — build sequence per §5** (conversion helper first, harvest last).
- **K4 (revised) — NOTHING deferred.** Per-store surfacing, full chart
  colour-by-source (D2), and SPA conversion-mirror dedup all land in the first
  build. No follow-up basket.

### Locked clarifications (§6b)
- **LC-1 — idempotent `/finish` harvest** via partial UNIQUE on
  `StockItemPriceObservation.shopping_list_line_id WHERE NOT NULL`. Double-tap → no
  duplicates.
- **LC-2 — baseline obs-only; UI source-blind** (see C3 above; LC-2 also gates the
  products-on sidecar shape).
- **LC-3 — silently absorb cost-output shifts** in `reports.py:225-236` (FU-216) +
  `get_recipes.py:505-519`. K1 wipes obs data, so no production data shifts. No
  back-compat shim.
- **LC-4 — editing a harvested observation does NOT propagate back to the line.** FK
  is provenance only, not a sync link. Lines are frozen at `status=done`; observations
  are the price record. The two diverge after harvest.
- **LC-5 — H1 staging is intra-build chunk ordering**, not a defer.

### Standing constraints (§9 of the handoff — apply throughout)
- **R-003** chokepoint stays `get_stock_item_unit_cost_at` for per-unit cost. New
  baseline math is server-derived; client renders only. No domain constant
  duplicated across languages (the SPA mirror is being deleted, per B2).
- **R-001** — `PriceEntry`, `RowActionButton`, `PriceHistoryChart` are the canonical
  primitives. No hand-rolled `q-btn`/`q-dialog`.
- **R-002** — chart colours, source chips ride semantic tokens.
- **R-005 / R-006 / R-015** — new migrations Postgres-portable, single head,
  deterministic constraint names, batch-mode-safe. Head as of plan-writing:
  `b5d8a2f4c9e7` (off Phase E `a3e9f6c2d8b4`).
- **R-007** — out-of-scope: FU-182 products-gating sweep, FU-214 history-page bug
  fixes, FU-216 stock-value rebase (covered indirectly by LC-3 absorption).
- **Pre-release** — non-preserving migrations OK; no shims.
- **Pytest gap** — this machine has only the MS Store Python stub (FU-189c / FU-223).
  Backend chunks are pytest-verified on a Python-equipped env; SPA chunks verified
  here via `vue-tsc -p tsconfig.json --noEmit` + `npm run lint`.
- **Seed-data discipline (new standing rule)** — every chunk that adds/modifies/
  removes a feature updates dev seed in the **same unit of work** so a fresh dev env
  yields plentiful test data exercising the full state matrix (esp. the C5 widget's
  <3-sample / above-1.15× / harvested-from-line / store-tagged variants). Promote to
  `R-017` in `ENGINEERING_STANDARDS.md` at chunk 8's close-gate.

---

## 1. Chunk sequence

Eight chunks; conversion helper first, harvest last (§K3). Each chunk is a complete
reviewable unit with backend + SPA + seed + verification. Bracketed numbers like
`[FU-227.1]` are stable chunk ids for cross-reference in worklog/changelog.

| # | Chunk | Why this order | LOC est |
|---|---|---|---|
| 1 | Unit-conversion helper + count dimension + SPA dedup | Nothing else works without normalized per-unit math; SPA mirror is replaced in the same chunk so we never build on the duplicate | B 300 / S 100 |
| 2 | Observation model reshape + migration | Folded shape + FK + store_id underpin every later chunk's reads/writes | B 250 / S 80 |
| 3 | Shared `PriceEntry` + row button + detail inline widget | The user-visible MVP; lands the "Your prices" widget on stock-item detail | B 100 / S 400 |
| 4 | Baseline math (`build_your_prices_for_item`) | Powers the widget chunk 3 ships in skeleton form | B 200 / S 60 |
| 5 | Shopping-line prefill + harvest + Receipt relabel + ladder extract | Depends on chunks 1–4 (conversion, observation shape, baseline for the prefill source-labelling) | B 250 / S 200 |
| 6 | Bottom-sheet + per-product Price-History (D2 + H2) | Builds on the chart already used by `/price-history`; needs unioned series from chunk 4 | B 80 / S 300 |
| 7 | Remove ingestion→observation path | Last because it deletes the only writer outside in-app surfaces; doing it earlier strands ingested seed data | B 100 / S 0 |
| 8 | Verify + seed refresh + promote R-017 | Close-gate | — |

---

## 2. Per-chunk specs

### Chunk 1 — Unit-conversion domain helper + count dimension + SPA mirror dedup

**Delivers:** server-owned conversion module + `count` dimension; SPA mirror gone.

**Backend:**
- New module `dora_api/domain/units.py` (or `dora_api/domain/conversion.py`) housing:
  - `UNIT_TABLE` (volume, mass, **count**, temperature, length, energy — copy
    existing dims as-is, add count).
  - `INGREDIENT_DENSITY_G_PER_ML` (move as-is).
  - `normalise_unit(unit: str) -> CanonicalUnit | None`.
  - `convert_measurement(amount, from_unit, to_unit, *, density=None) -> float | None`.
  - `Dimension` enum or string constants: `"volume" | "mass" | "count" | …`.
  - Count dimension: base `ea`, members `ea`/`pack`/`dozen` with fixed factors
    (`pack` = configurable later; for now `pack=1×ea`, `dozen=12×ea`). No
    cross-dimension conversion (`ea` ↔ `L` returns None).
- Delete the originals from `dora_api/features/assistant/tools.py:1188-1418`;
  `tools.py` imports the new module instead.
- New endpoint `GET /api/units/conversion-table` returning the table as JSON for the
  SPA to consume (or a build-time `scripts/dump-units.py` writing a generated TS
  file — pick whichever lands cleaner; SPA's `useUnits` reads the generated source).

**SPA:**
- `web_app/src/services/doraIntents.ts:348-610` — **delete** the local
  `_UNIT_TABLE` + helpers. Replace with a thin wrapper around the server-supplied
  table (lazily fetched once, cached in a Pinia store per R-016).
- Update `doraIntents.ts` callers to await the table once before normalising.

**Tests (pytest, run on Python env):**
- Count dimension: `convert_measurement(2, "dozen", "ea") == 24`; `("ea", "L")` → None.
- Existing volume/mass conversions still pass (snapshot the assistant tests' values).
- `normalise_unit("L") == normalise_unit("litre") == normalise_unit("litres")`.

**Verify here:** `vue-tsc -p tsconfig.json --noEmit` + `npm run lint`. Cold-load the
SPA, exercise the assistant's old code paths (recipes scaling, ingredient totals) to
confirm the new fetched table works.

**Seed:** none needed (pure helper change).

**Close-gate:** R-003 (one conversion source), R-001 N/A, R-007 (don't bloat into a
units admin UI).

---

### Chunk 2 — Observation model reshape + migration

**Delivers:** folded shape, store_id, FK to line, drop source enum, partial UNIQUE.

**Backend:**
- `dora_api/domain/entities/stock_item_price_observation.py:15-40` — rewrite:
  ```python
  @dataclass
  class StockItemPriceObservation(BaseEntity):
      stock_item_id: UUID
      total_price: float       # what was paid in total
      total_measure: float     # how much you got, in `unit`
      unit: str                # member of the supported list
      observed_at: datetime
      store_id: UUID | None
      shopping_list_line_id: UUID | None
      created_at: datetime
  ```
  Drop `price`, `qty`, `source`. Drop `PRICE_OBSERVATION_SOURCES` constant entirely.
- New Alembic migration off `b5d8a2f4c9e7` (Postgres-portable, batch-mode, named
  constraints per R-015). Non-preserving — drop the table and recreate (K1
  pre-release). New table:
  - `total_price NUMERIC NOT NULL CHECK (total_price > 0)`
  - `total_measure NUMERIC NOT NULL CHECK (total_measure > 0)`
  - `unit VARCHAR(32) NOT NULL` (check constraint against supported list, or rely on
    app-layer validation — decide at migration write time)
  - `store_id UUID NULL REFERENCES store(id) ON DELETE SET NULL`
  - `shopping_list_line_id UUID NULL REFERENCES shopping_list_line(id) ON DELETE SET NULL`
  - **Partial UNIQUE** `WHERE shopping_list_line_id IS NOT NULL` per LC-1.
    Postgres: `CREATE UNIQUE INDEX … WHERE shopping_list_line_id IS NOT NULL`.
    SQLite: same syntax works (partial indexes supported since 3.8).
- `dora_api/persistence/table_mappings.py` — re-map columns to the new shape.
- `dora_api/domain/stock_status.py:63-81` — `get_stock_item_unit_cost_at` updated:
  the existing fallback math (`latest.price / latest.qty`) becomes
  `latest.total_price / latest.total_measure`, but **also** unit-normalised: per LC-3
  it can now divide a normalised measure (e.g. 500 ml → 0.5 L) so callers get true
  per-unit cost. Keep the function name (consumers at `reports.py:231`,
  `get_recipes.py:517`, `get_stock_item_detail.py:386` are signature-stable).
- `dora_api/features/stock_items/price_observations.py:26-56` — request DTO + write
  path rewritten for the folded shape. Unit field validated against the supported
  list (chunk-1 helper). `source="manual"` line at :54 deleted. Add the FK as None
  on the manual write path.
- `dora_api/features/stock_items/get_stock_item_detail.py:111-118,375-386` — DTO
  + read mapping for the new shape; surface `store_id` (resolved to store name) and
  `shopping_list_line_id` (resolved to a line label like "from Wed's shopping list")
  when set.

**SPA:**
- `web_app/src/models/stockItemDetail.ts` — `PriceObservation` interface re-shaped.
  Add `store_name?: string | null`, `from_shopping_list?: { id, name, date } | null`.
- `web_app/src/pages/StockItemDetailPage.vue` price-observations list — render the
  new shape, show store chip + provenance chip when set.

**Tests:**
- Rewrite `tests/e2e/dora_api/test_price_observations.py:34-59` for the folded
  shape; assert partial UNIQUE rejects a duplicate FK insert.
- Migration up/down test (or document the non-preserving wipe in the migration
  docstring per R-006).

**Verify here:** `vue-tsc` + `lint`. Reset dev DB (DORA_ALLOW_DESTRUCTIVE drop_all
per the migrations-schema memory), run a fresh seed, hit the page in the browser.

**Seed:** the observation reshape is the first chunk that needs seed updates. New
seed data:
- ≥3 stock items with 3+ observations each (drives the baseline-ready widget state).
- ≥1 with <3 observations (drives the "not enough data" state).
- ≥1 with a current price > 1.15× median (drives the above-usual chip).
- ≥1 with a `store_id` set, ≥1 without (drives the "Last seen at Coles" line).
- For chunk 5: a couple of `shopping_list_line_id`-linked observations will be
  added then; chunk 2 ships them as `None` for now.

**Close-gate:** R-005/R-006/R-015 (named constraints, partial unique, Postgres-
portable). R-007 — do not touch the `actual→picked` ladder yet (chunk 5).

---

### Chunk 3 — Shared `PriceEntry` + row button + detail inline widget

**Delivers:** the visible "log a price" loop end-to-end, even though the baseline
chip will read placeholder values until chunk 4 lights it up.

**SPA — new components:**
- `web_app/src/components/dora/PriceEntry.vue` — the shared widget. Props:
  ```ts
  mode: 'shelf' | 'harvest'
  stockItemId: UUID
  prefill?: { total_price?, total_measure?, unit?, store_id?, source_label? }
  // 'shelf': renders price + size + unit + (optional) store. No count field.
  // 'harvest': renders total_price + size + unit. Count comes from the line.
  ```
  Emits `submit({ total_price, total_measure, unit, store_id })`. Live "$X / L"
  preview. Uses the chunk-1 conversion helper for client-side validation only.
  Unit picker = flat global list grouped by dimension (B3); last-time prefill from
  the latest observation (F2).
- `web_app/src/components/dora/YourPricesWidget.vue` — the C5 inline widget. Reads
  `your_prices` block from `StockItemDetailDto` (chunk 4 wires the real data; until
  then accept a placeholder shape and render the empty state). Two buttons:
  `[Log a price]` opens `PriceEntry` in shelf mode; `[Full history]` opens the
  chunk-6 bottom-sheet (chunk 3 ships a stub that disables this button).
- `web_app/src/components/stock/StockItemRowPriceButton.vue` — thin wrapper around
  `RowActionButton` for the row-overview button (icon `mdi-cash-plus`, money-gated).
  Tap opens `PriceEntry` in shelf mode prefilled from latest observation.

**SPA — touches:**
- `web_app/src/components/stock/StockItemRow.vue` — insert the new button between
  the spacer (~line 134) and the expiry button (~line 145). Wired only when
  `useMoneyEnabled` is true.
- `web_app/src/pages/StockItemDetailPage.vue:903-1300` — replace the existing
  inline observation entry block with `<PriceEntry mode="shelf" />` + the
  `<YourPricesWidget />`. The plain observation list stays below the widget.
- `web_app/src/style/icons.ts` — add `cash_plus: 'mdi-cash-plus'` to `ICONS`.

**Backend:** none of substance this chunk (the existing POST endpoint already takes
a folded shape from chunk 2). Add a `latest_observation_prefill` field on
`StockItemDetailDto` (or a sibling endpoint) that returns the prefill source for
the widget. Source label resolution lives server-side per R-003.

**Verify here:** `vue-tsc` + `lint`. Browser: open stock overview, tap the new
button on a money-on item, log a price; navigate to detail, see the widget render
and the observation list update.

**Seed:** ensure the latest-observation-prefill flow has good data (chunk 2's seed
already covers this).

**Close-gate:** R-001 (one `PriceEntry`, one `RowActionButton`, no hand-rolled
chrome). R-002 (button colours via tokens). R-014 (the < 3-sample state is the
visible empty state, not a hidden widget).

---

### Chunk 4 — Baseline math + `build_your_prices_for_item`

**Delivers:** server-derived `your_prices` block; widget chunk 3 lights up.

**Backend:**
- New module `dora_api/features/stock_items/your_prices.py`:
  ```python
  @dataclass(frozen=True, slots=True)
  class YourPrices:
      baseline: float | None       # median per unit, in baseline_unit
      baseline_unit: str | None    # the dimension the baseline is in (B4)
      current: float | None        # latest observation per-unit
      above_baseline: bool
      sample_count: int            # observation count only (LC-2)
      first_observed_at: datetime | None
      last_observed_at: datetime | None
      last_seen_store_name: str | None    # A2 surfacing
      offers_sidecar: list[OfferSidecarEntry]  # LC-2 products sidecar (empty unless products on)

  MIN_SAMPLES = 3
  ABOVE_THRESHOLD = 1.15
  BASELINE_WINDOW = timedelta(days=365)

  def build_your_prices_for_item(repo, stock_item_id, *, now=None) -> YourPrices: ...
  def build_your_prices_for_product(repo, product_id, *, now=None) -> YourPrices: ...
  ```
- **Per-dimension baseline (B4):** group observations by `dimension(unit)` from the
  chunk-1 helper. Pick the dimension of the most-recent observation as the active
  one; baseline computed over **observations in that dimension within the trailing
  12 months**, normalised to a canonical unit (L for volume, kg for mass, ea for
  count).
- **Source-blind count (LC-2):** `sample_count` counts observations only; offers
  never contribute, regardless of `features.products`.
- **Offers sidecar (LC-2 products minority):** when `features.products` is on,
  populate `offers_sidecar` with current `ProductOffer.price_now` per linked
  product, normalized to baseline_unit. UI renders this as a *separate* region; not
  folded into baseline or count.
- `dora_api/features/stock_items/get_stock_item_detail.py:111-118` — add
  `your_prices: YourPricesDto | None` to `StockItemDetailDto`; populate via
  `build_your_prices_for_item`.

**SPA:**
- `web_app/src/models/stockItemDetail.ts` — add the `your_prices` shape.
- `web_app/src/components/dora/YourPricesWidget.vue` — read real data: render the
  baseline line, "Last seen $X (Nd ago, Store)", `Based on N prices` line, the
  above-usual warning chip when `above_baseline` is true. The products-on sidecar
  ("Current shelf prices: …") is a separate `<section>` below the main block;
  always rendered when `offers_sidecar.length > 0`.

**Tests:**
- 0/1/2-sample cases → `baseline=None`, `current=latest if any`,
  `above_baseline=False`.
- 3+ samples, median correctness (odd + even).
- Threshold edge: `current == baseline * 1.15` is **not** above; strictly greater.
- Mixed-dimension history: per-dimension grouping picks the active dim correctly.
- 12-month window: a 13-month-old observation is excluded from baseline but still
  on the chart series.
- `sample_count` ignores offers even when products are on.

**Verify here:** vue-tsc + lint; widget renders real numbers in the browser.

**Seed:** none new (chunk 2 seeded the matrix).

**Close-gate:** R-003 (no client-side median, no client-side threshold compare;
server-derived `above_baseline` boolean). R-007 (don't extend the unioned-series
shape into the chart yet — chunk 6).

---

### Chunk 5 — Shopping-line prefill + harvest + Receipt relabel + ladder extract

**Delivers:** the closed loop. Prefill while shopping → user edits at the till →
`/finish` snapshots the line + harvests one observation per priced line + bumps
stock + transitions to receipt.

**Backend:**
- New helper `dora_api/features/shopping_lists/_line_price.py`:
  ```python
  def line_paid_unit_price(line: ShoppingListLine) -> float | None:
      """The actual→picked ladder: prefer actual_unit_price; fall back to
      picked_offer_price; None if neither. R-003 chokepoint (K2)."""
  ```
- Update consumers to use it (K2 extract):
  - `dora_api/features/budget/budget.py:80-83`
  - `dora_api/features/assistant/tools.py:2425-2431`
  - `dora_api/features/waste/waste.py:127-129`
  - `dora_api/features/reports/reports.py` spend/savings (lines ~359, ~725, ~750).
- `dora_api/features/shopping_lists/manage_shopping_list.py`:
  - **Delete** the `status=done` branch in the PATCH handler (`update_shopping_list`,
    ~138-146). Reject `done` with a 400 telling clients to use `POST /finish`.
  - `FinishShoppingListHandler` (~217-290): after the existing
    `snapshot_offer_price` loop and before the stock-level bump, harvest one
    observation per ticked priced line:
    ```python
    for line in ticked_lines:
        unit_price = line_paid_unit_price(line)
        if unit_price is None or line.stock_item_id is None:
            continue
        # E4: sized product → measure obs; sizeless → count obs.
        size = line.selected_product.size_value if line.selected_product else None
        unit = line.selected_product.size_unit if line.selected_product else "ea"
        if size and unit != "ea":
            total_measure = float(size) * line.quantity
            total_price = unit_price * total_measure
        else:
            total_measure = float(line.quantity)
            total_price = unit_price * line.quantity
        obs = StockItemPriceObservation(
            stock_item_id=line.stock_item_id,
            total_price=total_price, total_measure=total_measure, unit=unit,
            observed_at=now, store_id=line.shopping_list.store_id,
            shopping_list_line_id=line.id,
        )
        # Partial UNIQUE on line FK (LC-1) makes this idempotent: catch
        # IntegrityError and skip.
        ...
    ```
  - Add `prefill_unit_price` resolver to the shopping-list detail DTO so the SPA
    shows a prefilled (display-only, source-labelled) price on each line per D3:
    most-recent observation for `line.stock_item_id` else last receipt else
    selected offer.

**SPA:**
- `web_app/src/pages/ShoppingListDetail.vue:1918-1983` — replace the local
  `chosenOfferFor(line)` hint with the server's `prefill_unit_price` field. First
  edit PATCHes the line (existing pattern — keep). Show a small source chip beside
  the prefilled value ("from your last receipt" / "from your last log" / "from
  Coles offer").
- `ShoppingListDetail.vue` — strip any code path that ever sends `status: 'done'`
  via `updateAsync` (per the E3 trace it's already absent — verify and assert in
  the diff).
- **"Done" → "Receipt" label swap (I1):** wherever a list with `status="done"` is
  labelled "Done" in the SPA, route the label through a helper that returns
  "Receipt" when `useMoneyEnabled.value` is true, "Done" otherwise. Likely spots:
  `ShoppingListsOverview.vue`, the detail page header, the badge component for
  list status. Pure label swap, no behaviour change.

**Tests:**
- Pytest: `POST /finish` on a list with 2 priced ticked lines writes 2
  observations; second call on the same list (double-tap) writes 0 (LC-1 partial
  UNIQUE).
- Pytest: `PATCH /shopping-lists/<id>` with `{"status": "done"}` returns 400 with
  an error message pointing to `/finish` (E3 dead-branch removal).
- Pytest: sized product line → measure observation; sizeless → count observation
  with `unit="ea"`.
- Pytest: ladder helper — covers all three branches (actual / picked / None).

**Verify here:** vue-tsc + lint; browser: build a shopping list, finish it, see
observations show up on the relevant stock-item detail pages and on the
`YourPricesWidget`.

**Seed:** add ≥1 fully-finished shopping list whose ticked lines have produced
harvested observations on chunk-2-seeded stock items. Mix sized + sizeless so the
detail-page provenance chip is exercised.

**Close-gate:** R-003 (single ladder helper; no client-side math on prices), R-007
(don't change the snapshot/bump behaviour — only add harvest), R-001 (relabel via
helper, not scattered ternaries).

---

### Chunk 6 — Bottom-sheet (C5) + per-product Price-History (D2 + H2)

**Delivers:** the [Full history] button works; the per-product `/price-history`
gets observation series + baseline line.

**Backend:**
- `dora_api/features/price_history/price_history.py` — extend the per-product
  endpoint to return:
  - `series[].your_prices: YourPricesDto` via `build_your_prices_for_product`.
  - When `features.products` is off OR the product has no offers, fall back to
    observations linked via stock items (H2). The exact mapping: per-product means
    "all stock items linked to this product, unioned" — preserve the existing
    semantics, just add the observation rows alongside offer rows.
- New endpoint `GET /api/stock-items/<id>/price-history` returning the
  per-stock-item unioned series (offers ∪ observations) the bottom-sheet renders.
  Each point has `{ observed_at, unit_price, source: 'observation' | 'offer',
  store_name? }`.

**SPA:**
- `web_app/src/components/dora/PriceHistoryBottomSheet.vue` — Quasar `q-dialog`
  with `position="bottom"`, `full-width` on mobile breakpoints. Embeds the
  existing `PriceHistoryChart` scoped to the per-stock-item series. Footer has a
  close button (`BaseButton` per R-001).
- `web_app/src/components/dora/YourPricesWidget.vue` — wire `[Full history]` to
  open the bottom-sheet (no longer disabled).
- `web_app/src/components/PriceHistoryChart.vue` — accept observation points as a
  second series; render observations = solid line + dots (theme token
  `--semantic-positive` or a new `--semantic-your-data`), offers = dashed +
  lighter (`--semantic-context`). Legend names them. **All colours via tokens
  (R-002).** Add the baseline reference line at `your_prices.baseline` when
  present; "above usual" chip in the series header when `above_baseline` is true.
- `web_app/src/pages/PriceHistoryPage.vue` — show the new observation series and
  baseline line per product. Treat empty-offers-but-has-observations as a valid
  render (H2).

**Tests:**
- Pytest: per-product endpoint returns observation rows linked transitively.
- Pytest: stock-item history endpoint returns unioned series sorted by
  `observed_at`; source tag correct per point.

**Verify here:** vue-tsc + lint; browser: bottom-sheet opens, chart renders both
series colour-coded, baseline line visible, dark theme honoured.

**Seed:** none new (chunks 2 + 5 cover the matrix).

**Close-gate:** R-002 (zero hex in this chunk's diff), R-001 (one chart component,
one bottom-sheet primitive — extract `BaseBottomSheet` if a second use appears).

---

### Chunk 7 — Remove ingestion → observation path (J1)

**Delivers:** observations are in-app input only; ingestion never writes them.

**Backend:**
- `dora_api/features/ingestion/submit_ingestion_batch.py`:
  - Delete `_PriceObservationIn` (lines 101-118).
  - Delete `price_observations: list[…]` field on `IngestBatchRequest` (line 126).
  - Delete `_apply_observation` method (lines 399-455) and its call site
    (line 201).
  - Drop `"price_observation"` from the `kind` literals at lines 133, 141, 148.
  - Remove the unused `StockItemPriceObservation` import (lines 49-50).
- `IngestBatchRequest` has `extra="forbid"` so a producer still sending
  `price_observations[]` then 400s automatically. No extra rejection wiring.

**Docs (update in this chunk):**
- `docs/INGESTION_GUIDE.md` — remove the `price_observations[]` section; add a
  paragraph: "Observations are now in-app only — use the price-entry widget."
- `docs/04_proposals/PROPOSAL_INGESTION_API.md`
  + `docs/04_proposals/IMPL_PLAN_INGESTION_API.md` — mark the observations
  ingestion path as **removed**, with a forward pointer to this plan.

**Tests:**
- Pytest: `POST /api/ingest` with a `price_observations: [{...}]` field returns
  400 (extra="forbid" rejection).
- Pytest: an ingest payload without `price_observations` still 200s (smoke).

**Verify here:** vue-tsc unaffected; lint unaffected.

**Seed:** if any seed/dev fixture was using the ingestion path to seed
observations, switch it to direct repo writes through the new shape.

**Close-gate:** R-007 (don't touch other ingestion branches — products/offers stay).
R-003 (the in-app POST endpoint is now the sole observation writer).

---

### Chunk 8 — Verify + seed refresh + close-gate ADR (R-017)

**Delivers:** the work unit closes cleanly with everything checked.

**Verification:**
- Backend pytest **on the Python-equipped env** (FU-189c / FU-223 — can't run here).
  All new tests from chunks 1, 2, 4, 5, 6, 7 must pass. Note in the worklog which
  machine ran it.
- Here: `vue-tsc -p tsconfig.json --noEmit`, `npm run lint` (note: `node_modules`
  may need an `npm install` first per the standing constraint).
- Browser walkthrough covering the C5 full state matrix:
  - Item with 0 observations → "Not enough price data yet — log a few."
  - Item with 1-2 observations → same empty-state copy with a current price chip.
  - Item with 3+ observations, current ≈ median → "about average".
  - Item with current > 1.15× median → "paying more than usual" warning chip.
  - Item with `store_id` set → "Last seen $X at Coles" line visible.
  - Item with a harvested-from-line observation → provenance chip "from <list>"
    visible in the observation list / bottom-sheet.
  - With products feature off → no sidecar. With products on → sidecar visible,
    sample_count unchanged.
  - Bottom-sheet from `[Full history]` opens, both series colour-coded, baseline
    reference line visible, dark theme honoured.
  - Shopping list: prefill visible on a draft line with a source chip, persists on
    first edit, `/finish` produces observations idempotently on double-tap, status
    label flips to "Receipt" when money is on.

**Seed refresh (final pass):**
- Run the full destructive seed; confirm each of the matrix states above is
  present without manual setup.

**Engineering standards close-gate (CLAUDE.md mandatory):**
- Walk the diff against `docs/01_charter/ENGINEERING_STANDARDS.md` R-001..R-016.
  Any violation fixed/commented/logged per the explain-or-flag rule.
- **Promote seed-data discipline to R-017** in
  `docs/01_charter/ENGINEERING_STANDARDS.md`:
  - **Rule:** any code change that adds, modifies, or removes a feature must also
    update dev seed data in the same unit of work so a fresh dev environment
    yields plentiful, varied test data exercising the change's state matrix.
  - **Why:** repeatedly, a feature lands but a fresh dev env has no rows that
    trigger the new code paths — the next agent can't see/test it without manual
    setup, slowing every review.
  - **Apply:** new entities → seed rows; modified entities → updated seed values
    (no orphans the new code can't render); removed entities → seed references
    cleaned. Cover edge cases (empty/low/threshold/over).
  - **Violation signal:** a chunk's diff touches a feature but seed data is
    untouched, or fresh-env testing requires hand-clicking through the app to
    create the state.
  - **Carve-outs:** pure helpers / non-feature refactors don't need seed
    movement.
  - **Source:** 2026-06-22 pricing-system reassessment, ratified during FU-227.

**Ledger:**
- Move FU-227 from `DORA_FOLLOWUPS.md` to `DORA_FOLLOWUPS_RESOLVED.md` with a
  state note citing the chunks landed + the new R-017.
- New `[OPEN]` FUs for anything spun off (e.g. `[Full history]` bottom-sheet UX
  polish if browser testing surfaces issues; FU-182 reminder if the
  products-gating inconsistency turned out to bite).
- `CHANGELOG.md` user-visible entry.
- `DORA_WORKLOG.md` close entry.

---

## 3. State-ownership posture (R-003)

| Concern | Lives on | Notes |
|---|---|---|
| Per-unit cost from `(total_price, total_measure, unit)` | Server (`get_stock_item_unit_cost_at`) | Existing chokepoint, reshaped in chunk 2. |
| Unit-conversion table | Server (`domain/units.py`) | SPA fetches once; no second source (B2). |
| Median baseline, threshold compare | Server (`build_your_prices_for_item`) | Client renders the boolean + numbers; never re-derives. |
| 12-month window | Server | Module constant `BASELINE_WINDOW`. |
| `actual→picked` ladder | Server (`line_paid_unit_price`) | K2 extract; 4× duplication collapsed. |
| Source provenance label | Server (resolves the FK to "from <list>" or "from Coles") | Client renders a string + chip; doesn't compose the label. |
| Chart x/y rendering, chip presentation | Client | Pure presentation. |

---

## 4. Distribution & tenancy posture (§7.5)

- No new env vars; no new auth surface; no `tenant_id`.
- Postgres-portable: partial unique index is supported on both Postgres + SQLite ≥
  3.8; FK constraints use `ON DELETE SET NULL` (both engines).
- Degrades gracefully: zero observations + zero offers → widget shows empty state,
  zero crashes.
- The conversion-table endpoint is read-only, anonymous-cacheable, no PII.

---

## 5. Feedback coverage (CLAUDE.md cross-check rule)

Mapped against [`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`](../02_feedback/Feedback%20_%20Fixes%20-%20as%20of%20%5B06-Jun-2026%5D.md).
A flat table — every bullet that motivated the FU-227 work, plus the explicit
out-of-scope deferrals so a reviewer can audit "is anything missing?" at a glance.

| Bullet | Status | Chunk(s) | Notes |
|---|---|---|---|
| **L226** — "chart from bottom not side" (bottom-sheet for Price History) | ADDRESSED | 6 | `PriceHistoryBottomSheet.vue` (Quasar `q-dialog position="bottom"`, full-width on mobile). Opens from the YourPricesWidget's `[Full history]` button — exactly the surface the user described. |
| **L225** — "Price history graph does not extend all the way to the edge of the box" | OUT OF SCOPE | — | Per the plan §6, this is FU-214 (Price-History page bug pass). Not regressed by chunk 6 (we added series + baseline-line; the box-fit bug is separate). |
| **L226 (related)** — recipe estimated cost via product + receipt reconciliation | PARTIAL | 5 | Chunk 5 ships the harvest path (line → observation), which is the *data layer* L254 wants for downstream recipe-cost numbers. The recipe-cost rebase itself is FU-216 (LC-3 absorbs the silent shift). |
| **L419** — "Shopping mode should allow you to optionally add or edit pricing as you go. The shopping list BECOMES the receipt." | ADDRESSED | 5 + I1 | Chunk 5 ships prefill-and-persist (the line shows the prefilled price labelled with its source; first edit persists) + the "Receipt" relabel (I1, money-gated). |
| **L420** — "close the loop: completing a shopping list (after review) should allow you to quickly restock all items… treating the shopping list as the receipt" | ADDRESSED | 5 + I1 | Chunk 5 lands the harvest-on-`/finish` path: ticked priced lines → one observation per line on the linked stock item, idempotent via LC-1 partial UNIQUE. The Receipt relabel (I1) reframes "Done" as "Receipt" once money is on. **E3 revised** also removed the dead `PATCH status=done` branch so `/finish` is the only completion path. |
| **L226 (graph orientation)** — already a feedback chip-favoured pattern | ADDRESSED | 6 | Bottom-sheet uses `position="bottom"`, drags up; legend reads top-down. The widget's `[Full history]` is the discoverability entry point. |
| **L130** — "highlight/style the cheaper option" | NOT THIS WORK | — | FU-227 doesn't touch the linked-products tab's pricing visuals; that's owned by the products/cart proposal. Mentioned here so a reviewer doesn't flag the omission. |
| (implicit "what does this usually cost me?") | ADDRESSED | 3 + 4 | The C5 inline widget ("Usually $X / L · about average"), chunk-4 baseline math (median, 1.15×, min-3, trailing 12 months), LC-2 source-blind framing. |
| (implicit "warn me when something jumped") | ADDRESSED | 4 | The above-1.15× chip on the widget — strictly greater than `baseline × 1.15`; for the seed dataset, olive oil's $12/500ml latest fires it (`$24/L > $17.50/L × 1.15`). |
| (implicit "log what I paid quickly") | ADDRESSED | 3 + 5 | Shared `PriceEntry` widget (F1) — shelf-price mode on the row button + detail; harvest mode at `/finish`. Last-time prefill (F2). |

**Charter check (Effortless + Anti-creep, the tiebreak):** the visible
affordance is **one row button + one widget**; the rest is invisible
plumbing. No new pages, no new routes, no new tabs. The bottom-sheet is
*pull, not push*. Above-usual chip is *one chip, one threshold*, never
adjustable per item.

`docs/02_feedback/COVERAGE_GAPS.md` will be updated separately by this
chunk's seed/coverage sweep to flip the L420/L419/L226 entries from
gap → covered.

---

## 6. Dependencies & cross-cutting notes

- **FU-189c (pytest gap)** — backend chunks must be pytest-verified on a
  Python-equipped env; note which machine ran tests in the worklog.
- **FU-216 (stock-value rebase)** — LC-3 silently absorbs the cost-output shift in
  `reports.py:225-236`. No separate work this build; FU-216 stays open until the
  next stock-value reassessment.
- **FU-180 (preferred-store)** — informed by chunks 2 + 4 (store_id on observations
  + per-store surfacing in the widget). After chunk 4 lands, re-evaluate whether
  FU-180 closes as "covered" or stays open.
- **FU-214 (price-history bugs L218-L225)** — explicitly OUT of scope (R-007).
  Chunk 6 only adds observation series + baseline line, not bug fixes to the
  existing chart.
- **FU-182 (products-gating inconsistency)** — explicitly OUT of scope (I2 / R-007).

---

## 7. Risk + open items

- **B2 SPA-mirror dedup** — picking between a runtime fetch and a build-time dump.
  Runtime fetch is simpler; build-time dump avoids a network round-trip on cold
  app load. Decide at chunk 1 implementation time; default to runtime fetch
  unless cold-load perf bites.
- **B4 mixed-dimension UX** — when an item has both a count obs and a measure obs
  in history, the widget shows the most-recent-dimension baseline and a small
  "also logged in N other dims — view full history" affordance. Spec lives in
  chunk 4; if it gets gnarly, opportunistically simplify to "show baseline only
  for the active dimension; secondary dimensions visible in the bottom-sheet".
- **B1 count factors** — `pack=1×ea` is a placeholder; long-term a pack is N
  items, but without a per-product pack size we can't know N. Acceptable: "pack"
  in the UI just means "thing the price is per", and the baseline is per-pack.
  Don't fold in a per-product pack-size lookup this build (R-007).
- **Migration of existing observations** — wiped (K1). If a user has the dev DB
  populated from the old shape, the destructive migration drops it; documented in
  the migration docstring.

---

## 8. TL;DR for execution

Eight chunks. Conversion helper, then observation reshape, then the visible
widget + row button, then the math that lights it up, then shopping prefill +
harvest + Receipt relabel + ladder extract, then bottom-sheet + price-history
extension, then ingestion path removal, then verify + R-017 promotion. Each chunk
ships seed updates exercising the new state matrix. Pytest verified on
Python-equipped env; vue-tsc + lint + browser verified here.
