# Pricing System Reassessment — Handoff / Next-Task Brief

**Status (2026-06-22): RATIFIED — READY FOR PLAN EXECUTION.** All §6 questions A–K have been
walked with the user; recommendations and revisions are locked. §6a (A1 deep-dive + entry-surface
clarification) and §6b (five locked clarifications) capture decisions made during the lock
session. **No code has been written yet** — the next agent writes the plan/execution doc per §0
and then implements it.
**Created:** 2026-06-19 (initial handoff). **Ratified:** 2026-06-22.
**For:** the next agent picking this up.
**Supersedes-in-progress:** `docs/04_proposals/IMPL_PLAN_YOUR_PRICES.md` (the S2-10 brief assumed an
older shape; this reassessment reshapes it). Read that brief too — its locked decisions (median /
1.15× / min-3 / trailing-12-month) carry forward, but its §S2-10 sequencing is replaced by what's
below.

---

## 0. THE TASK FOR THE NEXT AGENT (do this)

**The §6 question list is fully ratified (2026-06-22).** Skip the Q&A step — go straight to plan
writing, then implementation.

1. **Read this whole doc** + the related docs in §8. Pay attention to §6a (A1 deep-dive + the
   user's row-button-vs-shopping-list intent split) and §6b (the five locked clarifications) —
   these were added during lock and contain decisions you won't see anywhere else.
2. **Write the plan/execution doc** (`docs/04_proposals/IMPL_PLAN_YOUR_PRICES.md` — replace its
   §S2-10, or a new sibling doc) as:
   - A **decision record** at the top, citing the ratified answers from §6 + §6a + §6b verbatim.
   - **Sequenced chunks** using §5 build sequence + §7 impact map so each chunk lists the exact
     file:line consumers it touches.
   - Per-chunk: what changes, why, file:line touches, verification (pytest + vue-tsc + lint +
     browser where applicable), seed-data updates (per §9 seed-data rule), close-gate checklist.
3. **Then implement the chunks in sequence.** Conversion helper first, harvest last (§5 / K3).
4. **Key ratified decisions to carry into the plan** (full reasoning lives in the cited sections):
   - **A1 folded** `{total_price, total_measure, unit}` (§6a deep-dive).
   - **A2 nullable `store_id`** on observations (one-way door, locked).
   - **A4 drop `source` enum entirely; add nullable `shopping_list_line_id` FK**
     (ON DELETE SET NULL; partial UNIQUE per LC-1).
   - **B3 flat global unit list + last-time prefill; NO smart defaults ever**.
   - **C3 baseline = observations only**, with **LC-2 source-blind UI** ("Based on N prices",
     offers as separate sidecar for products users).
   - **C5 inline widget** on stock-item detail + **bottom-sheet** (not new route, not drawer) for
     full history; per-product `/price-history` page stays in its current role.
   - **E3 `/finish` is the only completion path** — remove the dead `PATCH status=done` branch
     entirely; add a pytest asserting the route 400s on that input post-removal.
   - **K4 nothing deferred** — per-store surfacing, full chart colour-by-source (D2),
     and SPA conversion-mirror dedup all in the first build.
   - **LC-1 idempotent harvest** via partial UNIQUE on the FK.
   - **LC-3 cost-output shift absorbed silently** (pre-release, no shim).
   - **LC-4 harvested observations diverge from lines** (FK = provenance only).
   - **LC-5 H1 staging is intra-build chunk ordering**, not a defer.
5. **Standing constraints** apply throughout — see §9. In particular the new **seed-data rule**:
   every chunk that adds/modifies/removes a feature updates dev seed data in the same unit of
   work, exercising the full state matrix (esp. the C5 widget's <3-sample / above-1.15× /
   harvested-from-line / store-tagged variants). At end-of-work close-gate, evaluate the
   seed-data rule for promotion to a new `R-0NN` in `ENGINEERING_STANDARDS.md`.

---

## 1. How we got here (context)

The user is building the "Your prices" intelligence layer (runbook Phase F / S2-10): record what
groceries cost the user, show "your usual price" + "paying more than usual", and let shopping be
fast via prefilled prices. During scoping the user felt lost about **offers vs observations vs
ingestion**, and asked whether the prior intent was "observations are a god object and offers turn
into observations."

**Resolved with the user:** NO god-object. The codebase had TWO contradictory half-built ideas:
- **Idea A** (`PROPOSAL_PRODUCTS_AS_OVERLAY §2.5`): offers + observations stay separate in storage,
  **unioned only at read/display time**. Nothing converts.
- **Idea B** (the `product_offer` value in `PRICE_OBSERVATION_SOURCES` + the ingestion→observation
  path): observations are canonical and offers/receipts get *copied into* observation rows.

**The user chose Idea A, firmly.** Offers and observations are never converted into each other;
they're two labelled **sources** unioned at display time. This kills Idea B (drop the
`product_offer` source value; remove the ingestion→observation path).

---

## 2. Decisions LOCKED so far (user-confirmed across the conversation)

These are ratified — carry them into the plan doc as settled:

- **Idea A**: offers and observations are separate substrates, unioned only at read time, **never
  converted**. No god-object.
- **Observations are in-app user input ONLY.** Two entry modes: (a) what you really paid (receipt /
  shop close-out), (b) what you noticed something priced at (stock-item detail / quick log).
  **Ingestion must NOT write observations.**
- **Offers are ingested ONLY.** Users never hand-enter product offers. (This retracts an earlier
  idea of letting users type "what I paid for a product" as offer data.)
- **Wherever price is analysed or displayed, aggregate `linked-product offers ∪ stock-item
  observations`** (the item-level question "what does THIS cost me").
- **Colour-code source** in visualisations (offer-sourced vs observation-sourced points).
- **Offer-related UI is hidden unless the products feature is on**; observation/"your prices"
  surfaces show whenever money is on, independent of offers.
- Baseline = **median**; "paying more than usual" = current **> 1.15× median**; **min 3 samples**;
  baseline window = **trailing 12 months** (full history still on the chart).
- Price entry = **price + size + quantity** (quantity derived from shopping list where applicable)
  → unit price computed server-side. **Size unit from a fixed supported list** (conversion-backed),
  e.g. 1L or 500ml.
- Prefill data **tells you its source** (observation / last receipt / product offer).
- A **"log price" button on the stock-overview row, left of the expiry button, money-gated**
  (dollar-sign-ish icon).
- **"Done" lists relabel to "Receipt" only when the money feature is on** (pure label swap, no
  behaviour change). Confirmed by the user this turn.
- The user's worry about "shop mode copies prices so nav-away doesn't change prefill" → **resolved**:
  use lazy prefill that **persists to the line on first edit** (see §3 finding 3 + question E1). No
  bulk snapshot needed.

---

## 3. CURRENT-STATE MAP (grounded; from 4 parallel code reads, file:line)

### The three substrates (two incompatible shapes)
1. **Offers** — `ProductOffer` (1:1 current) + `ProductHistoricOffer` (append-only), `price_now` /
   `price_was` / `offered_on`, FK→Product→Store. Ingested. Per-unit, store-tagged.
2. **Observations** — `StockItemPriceObservation(price, qty, unit, observed_at, source)`
   (`dora_api/domain/entities/stock_item_price_observation.py:25-31`). `price` = TOTAL paid for
   `qty` of `unit`; **no store**. `PRICE_OBSERVATION_SOURCES = ("manual","shopping_close_out",
   "product_offer")` (line 12) — but **only `manual` is ever written in-app**
   (`price_observations.py:54`); ingestion stamps arbitrary source strings.
3. **Line snapshots** — `ShoppingListLine.picked_offer_price` + `list_price_at_pick` (frozen from a
   linked product's offer at commit-to-offer moment) and `actual_unit_price` (user-typed override).
   These are **per-unit × `quantity` (a count)** — NO size dimension.
   (`dora_api/domain/entities/shopping_list.py:81-91`.)

### Load-bearing holes
1. **No unit normalization.** `get_stock_item_unit_cost_at(observations, when)`
   (`dora_api/domain/stock_status.py:63-81`) = `latest.price / latest.qty` — **latest-entry-only, no
   median, no unit conversion**. Observation `unit` is **free text** (`max_length=50`, placeholder
   "L, kg, ea"; `price_observations.py:31`, `StockItemDetailPage.vue:535-541`). So "1 L" vs
   "500 ml" can't be compared. **This is the prerequisite — nothing works without it.**
2. **Conversion engine exists but is wrong-shaped + duplicated.** `_UNIT_TABLE` +
   `_INGREDIENT_DENSITY_G_PER_ML` + `_normalise_unit` + `convert_measurement` live **inside the
   assistant** (`dora_api/features/assistant/tools.py:1188-1418`), NOT a domain helper. Mirrored
   (hand-synced, minor drift) on the SPA in `web_app/src/services/doraIntents.ts:348-610`.
   Dimensions: volume, mass, temperature, length, energy. **NO count/"each" dimension** — yet the
   price widget needs "ea". Supported unit strings are exhaustive in `_UNIT_TABLE` (volume: ml/l +
   spoons/cups/etc.; mass: mg/g/kg/oz/lb; etc.).
3. **No prefill exists, but persist-on-edit is already the pattern.** The shopping-line price editor
   seeds from `chosenOfferFor(line)` as a *hint* and PATCHes the line on edit
   (`ShoppingListDetail.vue:1918-1983`). There is **no client-side price cache** — the SPA re-reads
   `getDetailAsync` each load. ∴ if prefill persists to the line on first edit, nav-away-and-back
   reads the persisted value, not a recompute — the user's snapshot-copy worry is moot.
4. **Two completion paths.** `FinishShoppingListHandler` (`manage_shopping_list.py:217-290`,
   `POST /shopping-lists/<id>/finish`) loads ticked lines, **backfills** `picked_offer_price`
   snapshots, **bumps stock levels** — but **writes NO observation**. A second plain
   `PATCH /shopping-lists/<id>` can set `status=done` and **bypasses** snapshot+bump
   (`manage_shopping_list.py:120-127`). Harvest-on-completion must choose which path(s) it hooks.
5. **Ingestion observation path** (`submit_ingestion_batch.py:399-455`): `stock_item_ref` branch
   writes a real `StockItemPriceObservation` with an *unvalidated* source string; `product_ref`
   branch actually appends a `ProductHistoricOffer` (NOT an observation). **No tests** exist for
   either branch. Removing the `stock_item_ref→observation` branch is low-blast-radius (the
   `offers[]` array covers the product path; no consumer reads ingest-origin observations
   distinctly). `extra="forbid"` on `IngestBatchRequest` means a producer still sending
   `price_observations[]` would then 400 (a contract change — the user controls the only producer).
6. **Price History is per-PRODUCT, offer-only, bespoke SVG.** `PriceHistoryPage.vue` +
   `dora_api/features/price_history/price_history.py` plot `ProductOffer`/`ProductHistoricOffer`
   only — **no observation data**. Chart = hand-rolled `PriceHistoryChart.vue` (raw SVG, not a
   library). "Your prices" is per-STOCK-ITEM (aggregate linked offers + observations) — different
   scope.
7. **`get_stock_item_unit_cost_at` already has two consumers** that change output if it normalizes:
   stock-value report fallback (`reports.py:225-236`, FU-216) and recipe estimated_cost fallback
   (`get_recipes.py:505-519`). It's the **single R-003 chokepoint** for per-unit cost — good.
8. **The `actual→picked` price ladder is duplicated 4×** — `budget.py:77-84`,
   `assistant/tools.py:2425-2431`, `waste.py:126-132`, `reports.py` (spend/savings). R-003 smell;
   harvest would be the 5th caller. Extract it.
9. **Money gating is inconsistent.** Observation block IS money-gated
   (`StockItemDetailPage.vue:481`, via `useMoneyEnabled` = install `money` AND user
   `money_features_enabled`). But product *offer* prices render `$` with **no** money check
   (ProductChip, MyProductsPage cards). Products feature = **data-presence** (`features.products` =
   `repo.get(Product).count() > 0`, `health_check.py:122`); its per-surface enforcement is
   half-done (FU-182 open). The user's "offer UI hidden unless feature on" is only partly true.

### Stock-overview row (for the price button)
Row button order L→R (`StockItemRow.vue`): bulk checkbox (45-50, Round-18) → image → stock-level
btn → name → spacer → **expiry (RowActionButton, 145-196)** → essential → open → cart. A "log
price" button goes **between the spacer (134) and expiry (145)** as a new `RowActionButton` (the
standardised cluster btn — `RowActionButton.vue`; do NOT hand-roll a q-btn, R-001). Icons via
`src/style/icons.ts` (`ICONS.<key>`). No `currency-usd` key exists; closest are
`price_check`→`mdi-cash-check`, `payments`→`mdi-cash`, `receipt_long`→`mdi-receipt-text`.

### Feature flags
- `useMoneyEnabled` = install `money` (`/api/health`) AND user `money_features_enabled`
  (`/api/users/me`). Both true → dollar surfaces render.
- `features.products` = data-presence (`Product` rows exist), server-derived via `/api/health`.
- They're independent. `useFeatureFlags.ts` / `useMoneyEnabled.ts`.

---

## 4. THE MENTAL MODEL (teach this to the user if they're still fuzzy)

Two storage tables, never merged in storage:
```
ProductOffer / ProductHistoricOffer   →  "what a STORE advertises"   (ingested, external, per-unit, store-tagged)
StockItemPriceObservation             →  "what the USER recorded"    (manual log OR shop close-out; item-level)
```
At read time, for a stock item, **union** its linked-product offers + its observations into one
series → compute the median baseline + "above usual" signal. Each point keeps a **source label**
(offer vs observation) → that's the colour-coding. Offers join only when the products feature is on.
The shopping line just needs (a) a prefill number and (b) a source label; it doesn't care which
table it came from.

---

## 5. SUGGESTED BUILD SEQUENCE (refine after the user answers §6)

1. **Shared unit-conversion domain helper + a count/"each" dimension.** Extract `_UNIT_TABLE` etc.
   out of the assistant into a domain module both the assistant and pricing use. *Nothing works
   without this.*
2. **Observation model reshape + migration** (shape per A1; optional `store_id` per A2; constrain
   `unit` to the supported list). Pre-release → non-preserving migration OK.
3. **Shared `PriceEntry` component** (price + size + unit-dropdown + count → derived per-unit) +
   the stock-overview row "log price" button + the stock-item-detail surface. (R-001: one component
   everywhere — this is what bit the round-2/3 button drift.)
4. **Baseline/median + "your prices"** on stock-item detail (server-derived; "usual price",
   "cheaper than last time", "paying more than usual").
5. **Shopping-line prefill (persist-on-edit) + harvest-on-completion** + "Receipt" relabel.
6. **Price-History observation series** (colour-by-source; make it observation-capable so it's
   useful with products off).
7. **Remove the ingestion→observation path** + drop the `product_offer` source value.
8. **Verify** (pytest — see §9 note — + vue-tsc + lint + grep).

Also fold in (any chunk): **extract the duplicated `actual→picked` ladder** into one helper.

---

## 6. OPEN QUESTION LIST (get the user's answers, then write the plan doc)

Each has my **[Rec]**. The user may "agree to all except…". Sections A–K.

### A. Observation data model
- **A1.** Persist `{total_price, total_measure, unit}` (count folded; UI does size×count) vs
  `{price, pack_size, unit, count}` (count stored)? **[Rec: `{total_price, total_measure, unit}` —
  simplest normalizable truth; count is a UI input, not stored.]** ⚠ one-way door on captured data.
- **A2.** Add nullable `store_id` to observations now? Model is item-level "what it costs me" (no
  store), but a receipt is from one store and without it you can never answer "cheaper at Aldi" from
  your own data. **[Rec: add nullable `store_id` now to future-proof; don't surface per-store
  analysis yet.]** ⚠ one-way door.
- **A3.** `observed_at` user-editable (back-date a receipt) vs always-now? **[Rec: editable,
  default now.]**
- **A4.** Post-work `source` enum = `manual`, `shopping_close_out`; **drop `product_offer`**.
  **[REVISED Rec (2026-06-22, user-agreed): drop the `source` enum field entirely.** Replace with
  nullable `shopping_list_line_id` FK on `StockItemPriceObservation` (ON DELETE SET NULL).
  Provenance comes from the FK: `line_id IS NULL` → user typed it; `line_id IS NOT NULL` →
  harvested from a line. Strictly more information than an enum (which line, which list, which
  store transitively, what product was selected, when). Dedup-on-harvest becomes a uniqueness
  constraint on `line_id`. Display gets a real chip ("from Wed's shopping list") instead of a vague
  enum. The `source` field is not load-bearing: it doesn't drive baseline math (C3 is
  observations-only, not within-observation), chart colour-coding (D2 splits offer-vs-observation,
  not within), validation, or business rules — only display labelling, which the FK does better.
  Charter check: drops a field, gains expressiveness → Effortless + Anti-creep both pull this way.
  Caveat: if a future third entry mode appears that isn't "typed" or "from a line", provenance
  needs re-adding — acceptable given ingestion explicitly does NOT write observations (J1).**

### B. Units & conversion
- **B1.** Supported dimensions for price entry: volume + mass + a **count** dimension (ea/pack/dozen)
  — count has no engine today. **[Rec: volume + mass + count (base "each", members ea/pack/dozen
  with fixed factors, no cross-dimension).]**
- **B2.** Extract conversion to one shared server-owned domain helper (fix front/back duplication);
  SPA keeps a thin mirror only for instant entry validation. **[Rec: yes.]**
- **B3.** Unit picker = flat global list grouped by dimension, vs per-item-typed. **[REVISED Rec
  (2026-06-22, user-agreed): flat global list grouped by dimension — and explicitly NO "per-item
  smart defaults later".** Auto-guessing units per-item is exactly the "app tries to be smart and
  gets it wrong" trap the user wants to avoid. Predictability beats cleverness.
  **Instead — last-time prefill for the unit choice**, consistent with the rest of the prefill
  story (F2). If you logged milk in litres last time, the unit dropdown opens on "L" next time.
  This is concrete, predictable, user-driven, and reuses the same "latest observation" lookup the
  widget already does for price/size — no extra inference logic, no domain heuristics, no failure
  mode where the app guesses wrong.]**
- **B4.** Mixed-dimension history for one item (logged "1 L" then "2 ea") — what wins the baseline?
  **[Rec: baseline per-dimension; "usual price" uses the dimension of the most-recent observation;
  mixed history shown but not blended.]**

### C. Baseline / "Your prices"
- **C1.** Median (locked) — confirm over the normalized per-unit series. **[Rec: yes.]**
- **C2.** 1.15× / min 3 / trailing 12mo (locked) — still good as tunable module constants.
  **[Rec: yes.]**
- **C3.** Does the baseline union offers + observations, or **observations only**? **[Rec:
  baseline = observations only (what you actually paid/saw); offers shown as context but don't move
  *your* baseline — keeps "your prices" honestly yours.]**
- **C4.** "$1.30 cheaper than last time" compares vs previous observation or vs median? **[Rec:
  show both — "$1.30 cheaper than last time · about average".]**
- **C5.** Per-item baseline on detail/row/line; Price-History *page* stays per-product. **[REVISED
  Rec (2026-06-22, user-ratified): yes — two scopes — and here is the display shape:**

  **(a) Inline "Your prices" widget on stock-item detail** (money-gated, always visible when on):
  ```
  ┌─ Your prices ─────────────────────────────────────┐
  │ Usually $5.20 / L  · about average                │   baseline + signal chip (D2 tokens)
  │ Last seen $5.00 (2d ago, Coles)                   │   most-recent point w/ source + store
  │ 8 observations · 3 offers                         │   sample counts
  │                       [Log a price] [Full history]│
  └────────────────────────────────────────────────────┘
  ```
  When `sample_count < 3`: "Not enough price data yet — log a few." with the same `[Log a price]`
  affordance (same shared `PriceEntry` component, F1).

  **(b) "Full history" → bottom-sheet, NOT a new route, NOT a drawer, NOT nav-away.** Quasar
  `q-dialog` with `position="bottom"`, full-width on mobile, embeds the existing
  `PriceHistoryChart` component scoped to this stock-item's unioned series (offers ∪ observations,
  colour-coded per D2). **Why bottom-sheet specifically:** the user's own feedback
  ([Feedback _ Fixes - as of [06-Jun-2026].md L226](docs/02_feedback/Feedback%20_%20Fixes%20-%20as%20of%20%5B06-Jun-2026%5D.md))
  already wrote: *"Would be better shown from the bottom I think rather than the right side because
  of the direction of the graph. Quasar has a special component for this … a type of dialogue that
  takes full width and drags up from the bottom."* Surface preference is on record.

  **(c) Existing `/price-history` page stays as-is in scope.** It keeps its per-product
  multi-compare role (compare up to 5 products). It also picks up F-3 (baseline reference line +
  above-usual annotation) and H2 (observation-capable when products off). Bug fixes from L218-L225
  feedback are **separate** — covered by FU-214.

  **Staging — strict anti-creep:**
  1. **Land the inline widget first.** It probably answers the everyday "is this expensive?"
     question on its own.
  2. **Bottom-sheet full history second**, only after the widget is in the wild and you can tell
     whether it's needed. May turn out unnecessary.
  3. **Per-product `/price-history` page bug fixes — separate FU.**

  **Charter check:** Effortless (one chip answers the question) + Anti-creep (full history is
  pull, not push).]**

### D. Offers ↔ observations (the union)
- **D1.** Confirm: never converted; unioned only at read time; every point source-labelled.
  **[Rec: yes — Idea A.]**
- **D2.** Colour-coding: observations = solid line + dots (your data); offers = lighter/dashed
  (context); legend names them. With products OFF, observations only. **[Rec: yes.]**
- **D3.** Prefill priority when both exist: most-recent across {observations, your last receipt};
  a selected offer prefills only when explicitly picked on the line; each prefill shows its source.
  **[Rec: yes.]**

### E. Shopping list integration
- **E1.** Prefill-and-persist (no shop-mode bulk copy): line shows prefilled price (display-only,
  labelled); first edit persists to the line; nav away/back reads persisted value. **[Rec: yes —
  replaces the "copy on shop mode" idea.]**
- **E2.** Prefill visible on draft lists too, or only shopping mode? **[Rec: show hint always
  (money-on), harvest only at completion.]**
- **E3.** Harvest one observation per ticked priced line via `/finish` only, or also raw
  `PATCH status=done`? **[REVISED Rec (2026-06-22, user-ratified): `/finish` is the ONLY pathway
  — and remove (or hard-restrict) the dead PATCH-status-done branch entirely.** Code-trace
  (2026-06-22) confirmed the SPA's `shoppingListApiService.updateAsync` is **only** used for
  `planned_shop_date` and `name` updates — **no UI surface ever sends `status: 'done'` via PATCH**.
  The handler branch at `manage_shopping_list.py:120-127` is dead from the user's perspective
  (probably API-parity completeness; possibly a curl/admin escape hatch). User confirmed: in their
  mental model there is ONE pathway — "I'm shopping, now I'm finished → finalise the list into a
  receipt." Implications:

  1. **Remove the dead branch** OR hard-restrict the PATCH handler to non-`done` transitions
     (allow `draft` ↔ `shopping`; reject `done` with "use POST /finish"). Cleaner: remove. No risk
     of bypass-via-curl that skips snapshot+harvest+restock.
  2. Single source of truth for "list becomes a receipt": `FinishShoppingListHandler`.
  3. Snapshot + harvest + restock + status-transition all live in one transaction in one place.
  4. R-007 (scope) — this is a dead-code prune the pricing work uncovered, so it lands here rather
     than as a separate FU.

  Verify after removal: pytest finds no test asserting PATCH-status-done behaviour (and write a
  pytest asserting the route now 400s on that input).]**
- **E4.** Sizeless / product-less line harvest: what `total_measure`+`unit`? **[Rec: harvest a
  count-dimension observation ("$X for N ea") when no pack size; a measure observation when a sized
  product is selected. The count dimension (B1) makes the sizeless case expressible.]**
- **E5.** During shopping the user enters per-unit or total-for-line? **[Rec: total paid for the
  line; widget knows count from `quantity`; per-unit derived — one number at the till.]**
- **E6.** Product-less line UI (products OFF): name, qty, preferred-buy hint, prefilled editable
  price. **[Rec: yes.]**

### F. The price-entry widget (shared component)
- **F1.** One shared `PriceEntry` component across stock-row quick-log, stock-item detail,
  quick-add, shopping line (R-001). **[Rec: yes.]**
- **F2.** Fields: total price + size + unit (supported list) + count, derived per-unit live; every
  field prefilled from latest observation so the common case is "confirm one number". **[Rec:
  yes.]**
- **F3.** "%+/-" + "usually costs / cheaper than last time" inline on change (C4). **[Rec: yes.]**

### G. Stock-overview row button
- **G1.** Icon: add `mdi-cash-plus` ("add a price") vs reuse `price_check` (`mdi-cash-check`).
  **[Rec: add `mdi-cash-plus`; fall back to `price_check` if avoiding a new icon.]**
- **G2.** Left of expiry, money-gated, `RowActionButton`. **[Rec: yes.]**
- **G3.** Tap → full `PriceEntry` popover prefilled, one visible "Log". **[Rec: yes.]**

### H. Visualisation / Price History
- **H1.** Add observation series to the per-product Price-History page AND a per-item mini-chart on
  detail? **[Rec: both, staged — per-item baseline text/chip on detail first (cheap, high value),
  chart work after.]**
- **H2.** With money ON / products OFF, make Price History observation-driven (today offer-only →
  empty) or keep hidden until products exist? **[Rec: observation-capable so it's useful without
  products.]**

### I. Feature gating & naming
- **I1.** "Receipt" relabel money-gated; "Done" when money off; pure label swap. **[Rec: yes
  (user confirmed).]**
- **I2.** Fix the money-gating inconsistency (offer prices showing `$` without money check) in this
  work or defer? **[Rec: defer — it's FU-182 (products-gating sweep) territory; don't expand
  scope.]**
- **I3.** Observation endpoints stay UI-gated only (not hard-gated server-side), per today's
  posture. **[Rec: yes.]**

### J. Ingestion
- **J1.** Remove `stock_item_ref → observation` ingestion branch (observations in-app only); keep
  `product_ref`/`offers[]`. Producer sending `price_observations` then 400s. **[Rec: yes — user
  controls the only producer.]**

### K. Migration, consumers, scope
- **K1.** Wipe/rebuild existing free-text-unit observations (pre-release, non-preserving migration)?
  **[Rec: yes.]**
- **K2.** Extract the duplicated `actual→picked` ladder into one helper while here? **[Rec: yes —
  4× dup, R-003; harvest is the 5th caller.]**
- **K3.** Confirm build sequence §5. **[Rec: yes — conversion helper first, harvest last.]**
- **K4.** Anything explicitly **out of scope** for the first build (per-store analysis,
  Price-History chart colour work, SPA conversion-mirror dedup)? **[REVISED (2026-06-22,
  user-ratified): NOTHING deferred — keep everything within scope.** All three previously-suggested
  deferrals land in the first build:
  - **Per-store analysis surfacing** — capture store_id on observations (A2) AND surface it (the
    "last seen at Coles" line in the C5 widget, store chip on history points, per-store grouping
    where it makes sense).
  - **Price-History chart colour-by-source visual polish** — full D2 treatment (observations =
    solid+dots, offers = dashed/lighter, theme-token-based legend) lands as part of F-3.
  - **SPA conversion-mirror dedup** — B2's "SPA keeps a thin mirror only" → actually delete the
    SPA-side `_UNIT_TABLE` duplication in `doraIntents.ts`; SPA fetches the conversion table from
    the server (or a generated TS file from the Python source) for instant entry validation.
    Single source of truth, no drift.

  More work in the first build but cohesively complete; no follow-up basket.]**

---

## 6a. A1 DEEP-DIVE — folded vs separate observation shape (for reference)

Captured verbatim from the working session — the user asked for a proper walk-through of A1 (the
folded `{total_price, total_measure, unit}` vs separate `{price, pack_size, unit, count}` decision)
before ratifying. **Recommendation unchanged: go folded.** This section is the reasoning trail.

### The two models on one line
| | Folded (rec) | Separate |
|---|---|---|
| Fields stored | `total_price`, `total_measure`, `unit` | `price`, `pack_size`, `unit`, `count` |
| Per-unit derivation | `total_price / total_measure` | `price / pack_size` |
| Count visible later? | No (UI computed at entry, didn't persist) | Yes (stored field) |

Both are normalizable; the choice is about what context the row remembers vs. what's only used to
compute the canonical truth.

### Worked example: "I bought 2 bottles of 1L olive oil for $14"
- **Folded.** Widget shows `Price $14 · Pack size 1 L · Count 2`, previews `Total measure 2 L` and
  `Unit price $7.00/L`. Persists `(total_price=14, total_measure=2.0, unit="L")`. The "two bottles"
  framing is gone.
- **Separate.** Widget shows `Price per pack $7 · Pack 1 L · Count 2`, total $14, unit $7/L.
  Persists `(price=7.00, pack_size=1, unit="L", count=2)`. The "two bottles" survives in the row.

Both produce the same `$7/L` data point for the baseline. Differences only show up in display,
editing, and edge cases below.

### Surface-by-surface trace

**1. Row-button logging.** Same widget either way. Folded writes 3 fields; separate writes 4.
Functionally identical at write.

**2. Harvest from a finished line** (`quantity=2`, selected_product = "Pauls Lite 1L Milk",
`actual_unit_price=$3.50`):
- Folded: `total_price = 2 × $3.50 = $7`, `total_measure = 2 × 1.0 = 2 L`. Per-unit: $3.50/L ✓
- Separate: `(price=3.50, pack_size=1.0, unit="L", count=2)`. Per-unit: $3.50/L ✓ — and "2 × 1L"
  shape preserved.

**3. Sizeless line — "$9 for 3 punnets of unknown-sized strawberries"** (count dimension from B1):
- Folded: `(9, 3, "ea")` → $3/ea ✓
- Separate: `(3, 1, "ea", 3)` → $3/ea ✓ (`pack_size=1`, `count=3`)

Both work, become near-identical here.

**4. The ugly case — "Two 12-packs of eggs, $10 total"**:
- Folded: `(10, 24, "ea")` → $0.417/each. "12-packs" framing gone; row says "24 eggs for $10".
- Separate: `(5, 12, "ea", 2)` → $0.417/each. "Two 12-packs" survives.
- **But separate is ambiguous here.** The same purchase could equally be persisted as
  `(10, 24, "ea", 1)` — "one bundle of 24 for $10". Same per-each, different representation. The
  widget has to pick a canonical form, and two are equally valid. **Folded forces one truth:
  24 eggs cost $10. No ambiguity to resolve.**

**5. Baseline median.** Three milk obs: $7/2L, $3.80/1L, $3.50/1L:
- Folded reads `(7, 2, L), (3.80, 1, L), (3.50, 1, L)`. Per-unit: 3.50, 3.80, 3.50. Median $3.50/L ✓
- Separate reads `(3.50, 1, L, 2), (3.80, 1, L, 1), (3.50, 1, L, 1)`. Same median ✓
- Subtle difference: separate makes count-weighted median trivially possible. Folded folds weight
  into `total_measure` implicitly (bigger purchases contribute proportionally bigger evidence).
  **Median is meant to be robust to outliers, not weight-aware — so this is a non-argument for
  separate.** If you wanted weighting, you'd use a weighted mean.

**6. Observation history on detail page.**
- Folded renders naturally: `Mon — Paid $7 for 2 L (≈$3.50/L)`.
- Separate renders more conversationally: `Mon — 2 × 1L bottles, $3.50 each`.
- Folded can reconstruct "$7 for 2 L"; it **cannot** reconstruct "2 × 1L bottles" (could equally
  have been 1 × 2L bottle).
- **Counter-point that lands hard:** the ShoppingListLine *already* records "2 × Pauls Lite 1L".
  The observation doesn't need to duplicate it. Two records, two purposes — **lines are the
  shopping record, observations are the price record.** Cleanest framing.

**7. Editing an existing observation** ("actually that olive oil was $12, not $14"):
- Folded: edit `total_price` from 14 to 12. Done.
- Separate: edit `price` from 7 to 6 — but the user has to know which of 4 fields changed. Higher
  cognitive load.
- Inverse: if the original typo was `count=3` (should be 2), separate lets you fix count alone and
  per-unit stays right. Folded forces a `total_measure` recompute mentally.
- **Read:** editing is slightly worse for folded only in pure-count cases (eggs); for sized cases,
  editing a total is fine because receipts show totals.

**8. Mixed-history (1L once, 500ml later).** Conversion helper normalizes both to $5/L either way.
No difference.

**9. The hybrid (`total_price + total_measure + unit + count_for_display`).** Don't. Extra field
read only for display, has to be kept consistent — worst of both. Commit one way.

### The trade-off table

| Dimension | Folded | Separate |
|---|---|---|
| Schema simplicity | 3 fields | 4 fields |
| Canonical per-unit at read | one division, no ambiguity | one division per row |
| Baseline math | trivial | trivial |
| Display "2 × 1L" history | impossible (gone) | natural |
| Two-12-packs ambiguity at write | none | two valid representations |
| Edit ergonomics — counts | mediocre | natural |
| Edit ergonomics — totals | natural | mediocre |
| Harvest from a line | derive `total_measure` from qty×size | one-to-one mapping |
| Sizeless / count-only lines | clean (`total_measure=N, unit="ea"`) | adds `count=N, pack=1` redundancy |

### Why the rec is folded (in order of weight)

1. **One canonical truth.** Separate has the "2 × 12-packs vs 1 × 24-pack" ambiguity for any
   `count > 1` purchase. Same actual purchase can land as different rows. Folded eliminates this —
   "what's it cost per unit?" has exactly one answer the moment you log.
2. **The shopping line already carries the shape.** `quantity=2, selected_product.size_value=1,
   size_unit="L"` lives on the line. The observation doesn't need to duplicate it. **Lines are the
   shopping record, observations are the price record.**
3. **Baseline math reads exactly the shape it needs.** No per-row "what's this row's per-pack
   again?" branch — `latest.total_price / latest.total_measure` is the value.

### What you give up going folded (eyes-open)

- **History rendering loses count framing.** "$7 for 2 L (~$3.50/L)" not "2 × 1L bottles for $7".
  If you want the latter, it comes from the line (when harvested) or via lossy item-pack-size
  heuristics.
- **Editing counts is slightly clunky.** "I bought 4 not 3" forces a `total_measure` edit, not a
  count edit. Entry widget can mitigate by re-deriving under the hood.
- **The persisted row is a step removed from the user's mental model.** Users think in packs and
  counts at the till. Real cost — but forcing the canonical form at write is what makes the rest of
  the system honest; the widget can still speak the user's language.

### Override criteria — choose separate instead if **either** is true
1. Observation history needs to surface "2 × 1L" as first-class info, distinct from what the line
   records (e.g. observations frequently logged **without** a line — spotted a shelf price without
   buying — and pack/count context matters there).
2. Users will frequently re-edit observations and count should be a directly editable field.

If neither bites, **folded wins.**

### User clarification (2026-06-22) — the two entry surfaces have different intents

The user clarified the mental model split between the two observation-entry surfaces. This **does
not change the rec — it strengthens it.**

- **Row-button (stock overview)** = "I **saw** milk for $5/L [optionally — at Coles]." A shelf
  price record. **No count concept at all** — purely (price, size, unit).
- **Shopping list completion** = "I **bought** 3 cartons of milk for $5 each [optionally — at
  Coles]" OR "I bought 3 cartons of milk for $15 total." A purchase record harvested into a price
  record.

**Implications for the design:**

1. **Folded wins more clearly.** The row-button surface has no count semantics. Folded persists
   `(price, size, unit)` directly. Separate would invent a vestigial `count=1` to fill the schema
   — a data-shape-vs-intent mismatch.
2. **The shared `PriceEntry` component (F1) wants two modes, one persisted shape:**
   - *Shelf-price mode* (row button): `price + size + unit` only. Count field literally not
     rendered. Three inputs, one preview ("$5/L").
   - *Harvest mode* (shopping line at completion): `total_price + size + unit`; count comes from
     the line's `quantity`; size from the selected product (or stays `ea`/count-dim for sizeless).
     User enters total at the till — one number.
   - Both write `(total_price, total_measure, unit)` rows. Folded supports this asymmetry cleanly;
     separate would force a `count=1` default in shelf-price mode and explain itself.
3. **Reinforces reason #2 of the rec** ("lines carry the shopping shape; observations carry the
   price record"). The row-button surface never had a shopping shape to begin with — it's purely a
   price record. Observations should be a price-record shape, not a purchase-record shape.
4. **A2 confirmation.** The "[optionally — at Coles]" in *both* entry modes confirms the nullable
   `store_id` rec: populated when the user picks a store on the widget (shelf-price mode) or from
   the line's store association if any (harvest mode); null otherwise.

---

## 6b. LOCKED CLARIFICATIONS (2026-06-22, user-ratified) — read before writing the plan

Five spec-tightening points raised at lock time. None change the design — they nail down details
the A–K answers leave open. Plan-writer: treat these as ratified constraints.

### LC-1 — Idempotency of `/finish` + harvest

Double-tapping the "Finish & restock" button (slow mobile network) MUST NOT create duplicate
observations. Achieved via the revised A4 FK: a **UNIQUE constraint on
`StockItemPriceObservation.shopping_list_line_id` WHERE NOT NULL**. Second harvest write on the
same line becomes a no-op (or a constraint violation the handler catches and ignores). Single line
→ exactly one harvested observation, ever. Manual observations are unaffected (their FK is null,
so the partial-unique-on-not-null is satisfied trivially).

### LC-2 — Baseline = observations only; UI is source-blind

**Policy unchanged:** baseline math (median, "above usual" signal, sample count) reads from
**observations only**, not the unioned series. Confirmed during lock review — even though offers
exist in the unioned series for display, they don't contribute to the median.

**UI framing — make the rule invisible to the user.** The original confusion fear ("what counts in
the baseline?") came from the widget draft showing `8 observations · 3 offers` as a count line,
which makes the user ask what's in vs out. **Drop the dual-count framing.** The widget says:

```
Usually $5.20 / L  · about average                  
Last seen $5.00 (2 days ago, Coles)                 
Based on 8 prices                                    
```

- **For the stock-only majority** (the vast majority of users — no products at all): "Based on 8
  prices" is unambiguous — there's only one source of data, no question can arise. The
  observations-only rule is invisible implementation detail.
- **For the products minority:** "Based on 8 prices" still refers to observations. Offers are
  surfaced **separately as a sidecar**, NOT folded into the baseline math or count. A small
  "Current shelf prices: $4.99 at Coles · $5.20 at Woolworths" subsection below the baseline
  widget — clearly framed as "what stores are listing right now" — distinct from "your baseline".
  In the bottom-sheet full history, offers appear as their own dashed series (per D2), visually
  separate. The two things never combine in math or in count chrome.

**Why this is the cleaner call** (rather than unioning baseline):
- A products user whose store flash-sales to $3 doesn't see their baseline poisoned.
- A stock-only user who later enables products sees their baseline stay stable (no unprovoked
  shift); products just adds the sidecar.
- The mental model is uniform across the user base: "your baseline = the median of what you
  recorded". Products users get extra context (shelf snapshot) on top, not a different baseline.

**Implementation notes:**
- The `your_prices` DTO (per existing `IMPL_PLAN_YOUR_PRICES.md`) computes baseline from
  observations only. Server-side filter is `source-equivalent IS observation-row`, which post-A4
  is just "all observation rows" (since `product_offer` source is dropped and ingestion no longer
  writes observations — every observation IS user-recorded).
- The widget never shows an offer count next to the observation count. If offers are surfaced,
  it's as a clearly separate UI region.

### LC-3 — Stock-value report + recipe cost outputs WILL shift; absorb silently

`get_stock_item_unit_cost_at` consumers — stock-value report fallback
(`reports.py:225-236`, FU-216) and recipe estimated_cost fallback (`get_recipes.py:505-519`) —
will produce **different numbers** post-normalization (today: `latest.price / latest.qty` with no
unit conversion; tomorrow: properly normalized per-unit cost). Pre-release, K1 wipes/rebuilds
observation data anyway, so there's no production-data shift to manage.

**Decision: document the shift in the plan; no special UI shim; no back-compat path.** The plan
notes the consumers as affected and the verification step confirms they render sensibly with the
new normalized data (no negatives, no zero-cost mis-displays, no division-by-zero on a 0-measure
edge case).

### LC-4 — Editing a harvested observation does NOT propagate back to the line

Once an observation is harvested from a line (at `/finish` time), the two records **diverge**.
The FK `shopping_list_line_id` is **provenance only, not a sync link**. Specifically:

- Editing the observation's `total_price` / `total_measure` / `unit` later DOES NOT rewrite the
  line's `actual_unit_price` or `picked_offer_price`. The line is `status=done` (frozen receipt
  per the receipt-naming model) — it stays as a historical record of what the user paid.
- Editing the line is moot anyway because lines on a done list are disabled in the SPA (see
  `ShoppingListDetail.vue:426,527,571,609,620,633,646,750,762` — all gated on
  `detail.status === 'done'`).
- Deleting the line (ON DELETE SET NULL on the observation FK) preserves the observation; only
  provenance is lost.
- Deleting the observation does nothing to the line.

**Plan implication:** the harvest path writes one observation linked to the line; no further
coupling. Two records, two purposes (line = shopping record; observation = price record).

### LC-5 — H1 "staging" is within the first build, not a defer

H1's "stage them — per-item baseline text/chip on detail first, chart work after" is **chunk
ordering inside the first build**, not pushing chart work to a later build. K4 stays consistent
("nothing deferred"). The chunk sequence inside §5:

- Chunk 3 (PriceEntry + row button + detail surface) lands the **inline widget** (LC-2 framing,
  text/chip first).
- Chunk 6 (Price-History observation series) lands the **bottom-sheet full history**
  (per C5-revised) and the per-product `/price-history` page baseline-line + observation-capable
  treatment (per F-3 / H2).

Both ship in the first build. The plan-writer should NOT read H1 as "defer the chart".

---

## 7. IMPACT MAP (consumers each change touches — use for the plan doc's per-chunk scope)

### (a) Unit normalization in per-unit cost
- Chokepoint: `get_stock_item_unit_cost_at` (`stock_status.py:63-81`). Free pickups (signature
  preserved): `reports.py:231` (stock-value fallback), `get_recipes.py:517` (recipe cost fallback),
  `get_stock_item_detail.py:386` (`unit_cost`). **But output changes for existing data.**
- NOT auto-normalized (separate math): `get_recipes.py:500` (`price/size_value` from offers); the
  whole line ladder (`budget.py:77-101`, `tools.py:2425-2431`, `waste.py:126-132`, `reports.py`
  spend/savings) which is per-unit×count with NO size — decide explicitly whether normalization
  touches the ladder or only observations/offers.
- Needs a unit taxonomy — today none; reuse the extracted conversion helper (B2).

### (b) Observation model reshape — every read/write site
- Entity+Fields `stock_item_price_observation.py:25-40`; migration (new); table mapping
  `table_mappings.py` (observation columns); helper `stock_status.py:63-81`; in-app write+validation
  `price_observations.py:26-33,48-56`; detail DTO `get_stock_item_detail.py:111-118,375-386`;
  ingestion DTO+writer `submit_ingestion_batch.py:101-118,412-420` (gone if (c) done); frontend
  `web_app/src/models/stockItemDetail.ts` + `StockItemDetailPage.vue` price section; test
  `tests/e2e/dora_api/test_price_observations.py:34-59` (rewrite).

### (c) Remove ingestion→observation path
- `submit_ingestion_batch.py`: delete `_PriceObservationIn` (101-118), `price_observations` field on
  `IngestBatchRequest` (126), `_apply_observation` (399-455), its call site (201), the
  `"price_observation"` `kind` literals (133,142,150); unused `StockItemPriceObservation` import
  (49-50). Docs: `docs/INGESTION_GUIDE.md`, `PROPOSAL_INGESTION_API.md`, `IMPL_PLAN_INGESTION_API.md`
  (contract change). Tests: none exist; consider adding one asserting the field now 400s.

### (d) Harvest observation on completion
- Write site: `FinishShoppingListHandler` (`manage_shopping_list.py:~233-270`, after the existing
  `snapshot_offer_price` loop; status→done at 267-268). Decide whether the raw `PATCH status=done`
  (120-127) also harvests.
- Source per line: the duplicated ladder (extract per K2). `source="shopping_close_out"` (declared
  but currently written nowhere).
- qty/unit mapping collides with (b) + E4 (count dimension for sizeless lines).
- Downstream lights up (the point): stock-value fallback, recipe cost fallback, detail `unit_cost`
  start showing values for purchased items that had none → update the stale "estimate, not
  accounting" caveat (`reports.py:316-319`).

### Cross-cutting
- Line ladder reimplemented ≥4× (`budget.py:77-84`, `tools.py:2425-2431`, `waste.py:126-132`,
  `reports.py`) — extract. Per-unit observation cost is correctly single-sourced via
  `get_stock_item_unit_cost_at` — the one safe chokepoint.

---

## 8. RELATED DOCS (read these)

- `docs/04_proposals/IMPL_PLAN_YOUR_PRICES.md` — the in-flight brief (locked decisions §"Decisions
  locked"; §S2-10 sequencing to be replaced by this reassessment).
- `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §2.5 ("Your prices" union), §3.2 (price
  observations substrate), §3.1 (`PreferredBuy`).
- `docs/04_proposals/PROPOSAL_INGESTION_API.md` §2.5 (intelligence layer), §6 (sequencing).
- `docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md` Phase F (the basket: this work is the "Your
  prices" item; siblings FU-210 tail, FU-214, FU-212, FU-180 are separate).
- `DORA_FOLLOWUPS.md` — FU-213 (price substrate), FU-216 (stock-value rebase), FU-180 (preferred
  store — now informed by `usual_store_id` + this work), FU-226 (stocktake rule assessment, unrelated).

---

## 9. STANDING CONSTRAINTS (apply throughout)

- **R-003** (single source of truth): per-unit cost stays server-derived through ONE helper; the
  baseline/threshold are server-computed; the client renders `baseline`/`current`/`above_baseline`,
  never re-derives. No domain constant duplicated across languages (the conversion-table front/back
  duplication is an existing smell to resolve via B2).
- **R-001** (componentisation): ONE shared `PriceEntry` component + `RowActionButton` for the row
  button. Do not hand-roll.
- **R-002** (theme tokens): chart colours / chips ride semantic tokens (the source colour-coding
  must be token-based, not hex).
- **R-005 / R-006 / R-015**: new migration Postgres-portable, single head, deterministic constraint
  names, batch-mode-safe. Current migration head: `b5d8a2f4c9e7` (after the Phase E head
  `a3e9f6c2d8b4`).
- **R-007** (scope): keep the products-gating-inconsistency fix (I2) OUT — it's FU-182.
- **Pre-release / breaking changes OK** (user memory): non-preserving migrations are fine; no
  back-compat shims needed.
- **PYTEST GAP**: this machine has only the MS Store Python stub — **pytest cannot run here**
  (standing FU-189c / FU-223). Backend changes here must be pytest-verified on a Python-equipped
  env before shipping. `vue-tsc -p tsconfig.json --noEmit` + `npm run lint` DO run here (note:
  `node_modules` keeps getting wiped between turns — `npm install` regenerates `.quasar/` first).
- **Charter tiebreak**: Effortless + Anti-creep. The whole point of prefill is speed; don't let the
  data model bloat the entry UX.
- **Seed-data discipline (new standing rule, 2026-06-22)**: any code change that adds, modifies, or
  removes a feature **MUST also update the dev seed data** in the same unit of work so that running
  a fresh dev environment yields reliable, plentiful test data for trying the new/changed features.
  This means: new entities get seed rows (enough variety to play with edge cases); modified entities
  get updated seed values (no orphaned `status="legacy_value"` rows that the new code can't render);
  removed entities/columns get their seed references cleaned. **Pricing build implications:** the
  observation reshape (A1) + `shopping_list_line_id` FK (A4-revised) + store_id (A2) + `/finish`
  becoming the sole completion path (E3-revised) all need seed-data updates so that on a fresh dev
  env you get: stock items with 3+ observations crossing the median threshold, a few above-baseline
  items, a few below-3-sample items, a few harvested-from-line observations, a few store-tagged and
  a few null-store observations, finished lists that exercise the harvest path. The seed should
  exercise the C5 widget's full state matrix.
- **Promote to engineering standards (close-gate ADR action)**: at end-of-work, evaluate the
  seed-data rule for promotion to a new `R-0NN` in
  `docs/01_charter/ENGINEERING_STANDARDS.md` so every future prompt picks it up automatically (not
  just the pricing build). This is the kind of recurring decision the ADR evaluation rule in
  CLAUDE.md is meant to catch.

---

## 10. ONE-PARAGRAPH TL;DR FOR THE PICKING-UP AGENT

The user wants a clean "Your prices" system: **observations** (what the user recorded, in-app only)
and **offers** (ingested only) are two separate substrates **unioned at display time, never
converted** (Idea A). The blockers are (1) there's no unit normalization and the conversion engine
is assistant-trapped, duplicated, and lacks a count dimension; (2) the observation model can't hold
price+size+count cleanly; (3) prefill/harvest into the shopping flow isn't built; (4) ingestion
wrongly can write observations. Get the user's answers to the §6 question list (recommendations
already attached), then write the plan/execution doc using the §5 sequence and §7 impact map. Don't
code until ratified. Conversion helper first, harvest last.
