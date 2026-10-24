# Chunk 07 — Zero-Input Pantry (P8-07)

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (solo, no subagents)
**Scope (from PLAN §4):** belief chip, quick-checks, per-user opt-out, `/beliefs` — i.e. the belief engine (`pantry_belief.py`), its endpoint, the per-surface overlay (`inference_overlay.py`, FU-653) and the three pages it annotates, the consumption-event leg of the loop, the quick-check suggestion generator, the four Settings → Assistant toggles, and the SPA cache + the four places that render "Dora thinks".
**Boundaries:** the row/picker chrome and the stocktake runner's belief ordering are Chunk 5 (D-1/D-5 of the signal-consolidation plan); the detail-page card is Chunk 6; the buy verdict's *use* of belief (`_need_axis`) is Chunk 6; suggestion *delivery* (dashboard/alerts cards) is Chunk 9; the `/check` endpoint and `last_checked_at` stamping are Chunk 5's stocktake group; Settings page shell is Chunk 13.

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_ZERO_INPUT_PANTRY.md` (§1 shipped, §4 out-of-scope, §5 coverage) · `PROPOSAL_INFERENCE_SURFACES.md` (§2 rule, §3 honesty gates, §5 toggles, §6 cost, §7 open decisions — closed) · `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` §1.2–1.3, D-1, D-5, D-11, D-12 · `HelpPage.vue` L359–362, L426 · `AssistantSettings.vue` L232–330 · feedback `[06-Jun-2026]` L89 (planned meals × stock) · open FUs: FU-683, 686, 695, 684, 654, 851, 525 (resolved precedent), 653 (resolved).

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/stock_items/pantry_belief.py` | 367 | engine: `compute_belief` (pure) + bulk gather |
| `dora_api/features/stock_items/get_pantry_beliefs.py` | 61 | `GET /stock-items/beliefs`, per-user gate |
| `dora_api/features/stock_items/inference_overlay.py` | 261 | FU-653 overlay: divergence + `recipe_hint`, surface flags |
| `dora_api/features/stock_items/_level_access.py` | 62 | R-032-safe level resolver (shared) |
| `dora_api/domain/cadence_math.py` | 58 | `mean_gap_days` chokepoint |
| `dora_api/domain/entities/consumption_event.py` | 59 | the depletion leg (FU-449) |
| `dora_api/features/stock_items/update_stock_item.py` L340–380 | — | `_maybe_record_consumption` |
| `dora_api/features/suggestions/generators.py` L315–420 | — | `generate_pantry_check` (quick-check) |
| `dora_api/features/auth/update_me.py` | 317 | the four toggles' write path |
| `dora_api/domain/entities/user.py` L229–251, L345–349 | — | flags + defaults |
| `dora_api/features/recipes/get_recipes.py` L1340–1385 | — | recipes overlay hydration |
| `dora_api/features/meal_plans/get_meal_plans.py` L575–645 | — | meal-plan overlay hydration |
| `dora_api/features/shopping_lists/get_shopping_list_detail.py` L755–790 | — | "Dora thinks you may be out of…" suggestions |
| `dora_api/features/stocktake/queue_ranking.py`, `session.py`, `stocktake.py` (belief reads) | — | Chunk 5 consumers, read for the gate only |
| `web_app/src/composables/usePantryBeliefs.ts` | 58 | module cache |
| `web_app/src/components/stock/PantryBeliefChip.vue` | 96 | **orphan** (FU-686/695) |
| `web_app/src/components/stock/PantryBeliefCard.vue` | ~130 | detail card (Chunk 6 owns its styling) |
| `web_app/src/components/stock/StockItemRow.vue` L60–100, L380–460 | — | picker ring + menu header |
| `web_app/src/components/recipes/RecipeBeliefChip.vue` | 72 | cookbook chip |
| `web_app/src/composables/useRecipeDisplay.ts` L200–210 | — | cookbook tooltip |
| `web_app/src/components/MealPlanEntryChip.vue` L56–70, L160–167 · `MealPlanRichCard.vue` L52–66, L160–167 | — | planner glyph + tooltip ×2 |
| `web_app/src/pages/ShoppingListDetail.vue` L425–445 | — | believed-out suggestions block |
| `web_app/src/pages/settings/AssistantSettings.vue` L232–330, L672–700 | — | the toggles |
| `web_app/src/models/pantryBelief.ts` (27), `models/auth.ts` L92–106, `models/recipe.ts` L157–161, `models/mealPlan.ts` L31–34, `services/api/authApiService.ts` L52–60, `stockItemApiService.ts` L92–96 | — | types + client |
| tests: `test_pantry_belief.py` (11), `test_inference_overlay.py` (10), `test_cadence_math.py` (9), `test_pantry_beliefs_endpoint.py` (3), `test_suggestion_selection.py` (kind listed), `dto_snapshots.json` (hint fields) | — | coverage inventory |

## A. Full Systems Test — Zero-Input Pantry

### A1. Preconditions
- Dense seed (it builds beliefs that *disagree* on purpose: ≥4 unique purchase dates on a few items, one cooked-through item, one freshly-checked item; `seed_dense.py:1156–1190`).
- Signed-in user with all four toggles at their defaults (stock **on**, cookbook / shopping / planner **off**); a second user to prove per-user scoping.
- Household timezone set to something far from UTC (AEST) for the R-021 edge.

### A2. Golden path
1. Stock overview → rows whose belief disagrees with the recorded level wear a **dashed** level box; agreeing rows wear nothing (silence is the default).
2. Open a dashed row's level picker → header *Dora thinks low* + the reason ("Bought 12 days ago, cooked with 2× since; you usually finish in about 14 days.").
3. Pick a level → ring disappears **immediately** (belief now echoes a fresh hard signal: *Updated today*, high confidence, `is_inferred=false`).
4. Open the item → *Dora thinks …* card expanded shows reason, *Confidence: medium*, *This differs / agrees with your recorded level*.
5. Stocktake → the queue is ordered **uncertain → overdue → confident** and Review-phase rows carry *Dora thinks …* in belief's own words; confirm one → belief reads *You confirmed this today*.
6. Cook a recipe to the finish dialog, mark an ingredient down → a `ConsumptionEvent(source='cook')` lands → the item's reason gains ", cooked with 1× since" and its progress advances by 0.34 of a cycle.
7. Settings → Assistant → *Stock overview hints* **off** → every ring, header and card vanishes on the next load; stocktake order becomes pure overdue; `/stock-items/beliefs` answers `{enabled:false}`.
8. *Cookbook hints* **on** → a cookable recipe with a required ingredient Dora believes **out** shows *May be short* (names in the tooltip); a not-cookable recipe whose every missing ingredient is believed back shows *May be cookable*; the cookbook's filters and `missing_count` are unchanged.
9. *Shopping list hints* **on** → an open list gains *Dora thinks you may be out of…* with ≤ N items not already on the list, A–Z; nothing is added for you.
10. *Meal planner hints* **on** → an uncooked planned entry whose recipe is at risk shows the Dora glyph (amber) with "since you planned this"; cooked entries never do.
11. Suggestions (dashboard/alerts surface) → when an in-play item (on an open list, or needed by a meal within 7 days) has a **low**-confidence belief, a *Still have Rice?* quick-check appears, ≤ 3 at a time, least-confident first, deep-linking to the item.
12. Sign in as the second user → their own toggles apply; the first user's choices don't leak.

### A3. Edge cases
- No purchases, no checks → *Not sure yet. No purchases or checks on record.* (confidence 0.1, never a ring).
- One purchase only → thin-data path: *Based on the last recorded level (last known 9 days ago). Not enough history yet.* — confidence ≤ 0.4, halves every 30 stale days, never differs.
- Belief can never reach **high** on *Out* (ceiling 0.525) — so the overlay never remarks "out" with high confidence; the recipe hint's medium gate still lets it through.
- Level changed **this morning** in AEST → `_as_date` takes the **UTC** date of the timestamp while `today` is household-local → "Updated 1 day ago" / a check made today not pinning (07-R1).
- Recorded level missing (item with no level) → thin path needs `recorded is not None`; falls to *Not sure yet*.
- Duplicate same-day purchases → `mean_gap_days` ignores zero gaps (pinned by `test_cadence_math`).
- Recipe with an **unlinked** required ingredient → no hint ever (honest `None` stays `None`).
- Recipe where one of three missing ingredients is believed back → no *May be cookable* (all-or-nothing).
- Shopping surface on a **done** list → no suggestions; candidates exclude items already on the list.
- Toggle flipped mid-session → the SPA cache holds the old beliefs until the next `loadAsync(force)` — the overview reloads on mount, the detail page refetches on level change only (FU-851 class).
- `GET /beliefs` with no session user (shouldn't happen behind auth) → `{enabled:false}`.
- Pantry of 400 items → still 3 queries for the gather; the shopping surface gathers for **every** item not on the list by design (§6 of the proposal).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (all *Not sure yet*, no rings) | ✓ (A2) | ✓ (purchases via finished lists only; no cooking → calendar-only decay) | ✓ (all four surfaces on) | – (no install-wide flag; D-12 made it per-user) | ✓ (step 12) | – | – |

### A5. Load-bearing conditions
- `compute_belief` is pure; every threshold is a module constant; the safety envelope in the impl plan §1.3 is derived from exactly those constants — change one and the "Out can't be high" guarantee may fall (07-R10 proposes a test that pins it).
- `gather_beliefs_for_items` resolves levels by FK (`_level_access`) — but `inference_overlay.divergent_items` reads `item.stock_level` off the relationship (07-R2).
- `_HARD_SIGNAL_FRESH_DAYS = 3` and the "confirmed today" wording both depend on `_as_date` agreeing with `household_today` (07-R1).
- Every consumer gates through `inference_overlay.surface_enabled` / `SURFACE_FLAGS` — the one map from surface to column.

### A6. Release-gate rows
- In an AEST household, change a level at 08:00 local → picker header reads *Updated today* and the ring is gone.
- Toggle *Stock overview hints* off → `/stock-items/beliefs` → `{enabled:false, beliefs:{}}` and no row is dashed.
- Cookbook hints on + the dense seed's at-risk recipe → *May be short* chip names the right ingredient; `missing_count` unchanged.
- Cook-mode finish marking an item down → one `ConsumptionEvent` row, `source='cook'`, `from_sequence < to_sequence`.

## B. Help content — Zero-Input Pantry

### B1. Current help audit
*The "Dora thinks…" hint* (HelpPage L359) is accurate for the stock surface (dashed ring, picker header, silence on agreement, Settings → Assistant). The stocktake guide (L426) explains belief-ordered walks. Nothing explains: the three **other-surface hints** and their wording (*May be short* / *May be cookable* / "you may be out of…"), that they default **off**, the **quick-check** suggestion, what *confidence* means and why *Out* is never confident, or how cooking feeds the belief. The Settings InfoTips are good one-liners and stay. DoraBot's corpus has **zero** mentions of inference.

### B2. Help entries
Group **Stock** (new; sentence-case; `path: '/stock'` unless noted):

1. **How Dora works out what you have** — "Dora's guess is a *band* — out, low or stocked — never a count. She starts the clock at your last purchase (a ticked line on a finished list with a price), estimates how long a buy lasts from the usual gap between your purchases, and moves the clock forward faster each time you cook with the item. Three-quarters of the way through a usual cycle she thinks *low*; past it, *out*. Confidence comes from how much history there is and how far she is extrapolating — she can be sure you're stocked or low, but she is deliberately never *sure* you're out, because an unlogged top-up is always possible. A level you set or confirm in the last three days wins outright: she echoes it and says *Updated today* instead of guessing."
2. **Hints on other pages** (`path: '/settings/assistant'`) — "By default Dora's opinion shows only on the Stock pages. Three more switches under Settings → Assistant → Zero-Input Pantry put the same opinion where stock items turn up: **Cookbook** flags a recipe *May be short* when it reads cookable but a required ingredient is believed out, and *May be cookable* when everything recorded as missing is believed back; **Shopping list** adds a *Dora thinks you may be out of…* list beside an open list — nothing is added for you; **Meal planner** marks an uncooked planned meal whose ingredient has probably run out since you planned it. These only ever add a remark: cookability, your lists and your plan's shopping figures are unchanged. They are off until you turn them on, because they annotate pages you opened for something else."
3. **Quick checks** — "Dora never asks you to count the pantry. When a decision is about to rest on an item she is unsure of — it's on a list you're building, or a meal in the next week needs it — she asks one question: *Still have Rice?*, at most three at a time, least-certain first. Open the item and set or confirm the level; that pins her belief and the question goes away."
4. Extend *The "Dora thinks…" hint* with one sentence: "Confidence is shown as high / medium / low; only a medium-or-better disagreement is ever remarked on outside the Stock pages."

### B3. DoraBot corpus delta
Add to `app_knowledge.py` after the Stock paragraph: *"Zero-Input Pantry: Dora infers each item's level (out / low / stocked, with a confidence and a one-line reason) from purchases on finished shopping lists, the usual gap between buys, and cook-mode consumption. The recorded level is always the source of truth; the inference is a remark. It shows on the stock rows and item page by default and, if the user turns them on in Settings → Assistant, as hints on the cookbook ('May be short' / 'May be cookable'), shopping lists ('you may be out of…') and the meal planner. A low-confidence belief on an item a pending shop or planned meal depends on produces a 'Still have X?' quick-check suggestion."*

## C. Senior review — Zero-Input Pantry

Verdict key: **execute** · **FU** · **waive** · **conditional**. Sizes S/M/L.

### C1. Bugs (verified or high-confidence latent)
- **07-R1** · R-021 — `pantry_belief._as_date` (L284–290) takes `datetime.date()` of UTC-stored `stock_level_last_updated`, `last_checked_at`, list `completed_at` and consumption `occurred_at`, while `today` is `household_today()`. In any household east of UTC a morning level change dates to **yesterday**: *Updated 1 day ago*, and a check that should pin the belief for three days pins for two; purchase dates and cook dates shift the same way (the `FU-525` class `get_buy_verdict._local_date` already fixed for the verdict). · **Exact change:** `_as_date(value, tz)` → `value.astimezone(tz).date()` (naive values assumed UTC), with `tz = household_timezone(repository)` resolved once in `gather_beliefs_for_items`; add the test in §D. · S · **execute**.
- **07-R2** · R-032 / FU-684 — `inference_overlay.divergent_items` (L147–149) reads `is_missing(item.stock_level)` off the `noload` relationship; the three callers each `.include(STOCK_LEVEL)` to make it work, and `_level_access`'s docstring records that an include can still return an identity-mapped instance with the relationship unset — exactly how `/buy-verdict` once answered *unsure* for everything. `gather_beliefs_for_items` already resolves the levels by FK one line earlier and throws them away. · **Exact change:** have the gather return (or expose) `levels_by_item`; `divergent_items` computes `recorded_missing` from `is_missing(levels_by_item[id])`; drop the three now-unneeded includes (`get_recipes.py:1352`, `get_shopping_list_detail.py:769`, `get_meal_plans.py:593–594`'s `then_include(STOCK_LEVEL)`) and the "theatre" includes in `get_pantry_beliefs.py:54` and `generators.py:379`. · S · guard: `test_inference_overlay.py` + an e2e that asserts a hint with the include removed · **execute**.
- **07-R3** · `PantryBeliefChip.vue` has no importer (grep `PantryBeliefChip` → only comments in `PantryBeliefCard.vue:5,82`, `StockItemRow.vue:401`, `StockItemDetailPage.vue:196`, `StocktakeRunner.vue:503`) and still received a DR-8 fade fix after it died (FU-686 / FU-695). · **Exact change:** delete the file; reword the five comments to name the live form (the picker's ring + menu header). · S · **execute (resolves FU-686 and FU-695; the owner's "is the row chip coming back?" is answered by D-5 — one dashed marker on the level box)**.

### C2. Redundancy / DRY (R-001, R-003)
- **07-R4** · Five identity maps band → word (`{out:'out', low:'low', stocked:'stocked'}`): `PantryBeliefCard.vue:69`, `PantryBeliefChip.vue:46`, `StockItemRow.vue:412`, `StocktakeReviewPhase.vue:161`, `StocktakeRunner.vue:505`. Each maps a string to itself and falls back to the input. · **Exact change:** delete all five; render `belief.believed_band` directly (05-R24's `helpers/beliefBand.ts` is only needed if a *different* word is ever wanted — today none is). · S · **execute**.
- **07-R5** · Three copies of the hint tooltip: `MealPlanEntryChip.vue:162–167` and `MealPlanRichCard.vue:162–167` are byte-identical; `useRecipeDisplay.ts:204–210` differs only in the leading clause. The `at_risk → text-warning / else → text-positive` class pick is also written twice. · **Exact change:** `helpers/inferenceHint.ts` exporting `inferenceTooltip(hint, names, surface: 'recipe' | 'plan')` and `inferenceTone(hint)`; three callers import it. · S · **execute**.
- **07-R6** · `usePantryBeliefs.ts` and `usePlannedDemand.ts` (Chunk 6) are the same 58-line module-cache shape (`loaded/loading`, `loadAsync(force)`, `xFor(id)`, `invalidate`). The second was copied from the first "on purpose". · **Exact change:** `composables/createOverlayCache<T>(fetch: () => Promise<{enabled?: boolean; map: Record<string,T>}>)`; both become 10-line instantiations. FU-851's invalidation bus then has one subscriber type. · S · **execute**.
- **07-R7** · Two `IngredientRow` constructions from two different shapes (`get_recipes.py:1361–1370` from the DTO; `get_meal_plans.py:611–622` from entities, re-deriving `is_missing` and `missing_count_for`/`unlinked_count_for` inline). · **Exact change:** `IngredientRow.from_dto(dto)` and `IngredientRow.from_entity(ingredient, levels_by_item)` classmethods in `inference_overlay.py`; the meal-plan path reads levels through 07-R2's map. · S · **execute**.
- **07-R8** · FU-654 / 02-R12 — `get_pantry_beliefs._current_user_id` (L32–39), `inference_overlay.current_user` (L112–124) and `generate_pantry_check`'s `repository.get(User).by_id(user_id)` gate are three of the **31** `session.get("user_id")` / `SESSION_USER_ID_KEY` copies now in `dora_api` (29 files). · **Exact change:** 02-R12's `infrastructure/auth_helpers.current_user_id()` + `current_user(repo)`; the two local helpers go. · S (given 02-R12) · **execute**.
- **07-R9** · `gather_beliefs_for_items(..., _return_inputs=True)` returns a dict of `BeliefInputs` *or* `PantryBelief` depending on a private flag (L298–368), typed `-> dict`. · **Exact change:** `gather_belief_inputs_for_items(repo, items) -> dict[UUID, BeliefInputs]` + `gather_beliefs_for_items` = `{k: compute_belief(v) for …}`; `gather_belief_inputs` (single) calls the former. · S · **execute**.

### C3. Dead code / unused fields / unread endpoints
- **07-R10** · `ConsumptionEvent.from_sequence / to_sequence` are written (`update_stock_item.py:371–380`, seeds) and **never read** (grep `from_sequence|to_sequence` outside entity/mapping/writer/seed/tests → none); the entity docstring promises the belief "can weight a drop-to-out more heavily", which `compute_belief` doesn't do. · **Exact change:** either (a) use them — a weight by `to_sequence` in `_CONSUMPTION_WEIGHT` — or (b) drop the columns. (a) is a model change (owner call; it also moves the §1.3 envelope); (b) is a migration for two nullable ints. · **FU** (decision), with the envelope test below as the guard either way.
- **07-R11** · `CONSUMPTION_SOURCE_MANUAL` / `_WASTE` are accepted by `_VALID_CONSUMPTION_SOURCES` but the SPA only ever sends `'cook'` (`RecipeCookMode.vue:1559`); the proposal §4 records manual-drop recording as deliberately out of scope. · **waive** (documented sentinel; the TS union `'cook' | 'manual' | 'waste'` at `stockItemApiService.ts:312` stays honest about the contract).
- **07-R12** · `PantryBelief.believed_sequence` travels on the DTO but no SPA reader (grep `believed_sequence` in `web_app/src` → `models/pantryBelief.ts` only); `confidence` (the float) likewise — every surface reads `confidence_band`. · **Exact change:** drop both from `asdict` output (keep on the dataclass for the ranking's `sort_key`) via a `_to_dto` that picks the five rendered fields; drop the TS members. · S · **execute**.

### C4. Componentisation opportunities (R-001)
- **07-R13** · The three Zero-Input sections of `AssistantSettings.vue` (L232–330) are four near-identical `SettingsRow inline` + `InfoTip` + `q-toggle` blocks bound to `currentUser.<flag>` with an `onSurfaceChange` map. · **Exact change:** a `UserFlagToggleRow` (label, tip, flag) driven by a small array — Chunk 13's settings-shell pass should own it; record here, execute there. · S · **conditional** (execute if Chunk 13 doesn't already propose a generic flag row).

### C5. Placement / standards (R-002, R-005, R-008, D-rules)
- **07-R14** · `inference_overlay.py` imports `flask.session` to find the user — a domain-ish rule module reaching into the web layer (R-004/R-008 layering; the belief module itself is clean). Fixed by 07-R8 (helper in `infrastructure`). · **execute via 07-R8**.
- **07-R15** · `MealPlanEntryChip.vue:65` / `MealPlanRichCard.vue:61` colour the Dora glyph with Quasar `text-warning` / `text-positive` palette classes while `RecipeBeliefChip` uses the house `dora-chip--warning/--positive` tokens (R-002; FU-777 class). · **Exact change:** token classes via 07-R5's `inferenceTone`. · S · **execute**.
- **07-R16** · `PantryBeliefChip.vue` `font-size: 0.72rem`, `border-radius: 10px`, `padding: 1px 7px` — moot after 07-R3.
- **07-R17** · `get_pantry_beliefs.py` returns `asdict(belief)` per item — a dataclass→dict at the edge rather than a DTO; fine, but 07-R12's `_to_dto` is where the contract should live.

### C6. Naming & idiom
- **07-R18** · `_as_date` becomes `_household_date(value, tz)` with 07-R1 so the name says which calendar it answers in.
- **07-R19** · `generators.py:379 items = … .include(STOCK_LEVEL)` + `name_by_id` — after 07-R2 the include goes; keep `name_by_id`.

### C7. Efficiency
- **07-R20** · `get_shopping_list_detail._inferred_suggestions` gathers beliefs for **every** stock item not on the list on every detail read when the surface is on (03-R36 flagged the same block for loading all items before the gate). The proposal §6 accepts this; the gate (`surface_enabled`) runs **after** the `StockItem.all()` fetch (L768–770). · **Exact change:** check `surface_enabled(current_user(repo), SURFACE_SHOPPING)` before fetching candidates (3-line reorder; `resolve_divergence` keeps its own gate). · S · **execute (with 03-R36)**.
- **07-R21** · `get_meal_plans` hydration loads every pending recipe with ingredients→stock item→level via `then_include` chains just to build rows; after 07-R2/07-R7 it needs ingredients + FK ids only. · **execute via 07-R2/R7**.
- **07-R22** · `generate_pantry_check` loads all open lists' lines and all week's `MealPlanEntry` rows per suggestion run; the run is on-demand and capped — fine. · **waive**.

### C8. Design-level findings — out of Stage-2 scope
- **07-D1** · Belief has no quantity awareness (impl plan §1.3) — one tin and twelve tins are the same signal. Recorded; the §4 out-of-scope list owns it.
- **07-D2** · Consumption weighting by band (07-R10) is a model decision.
- **07-D3** · The shopping-surface suggestion block and the planner glyph have no "dismiss"; §7 of the inference proposal closed this as *No*. Nothing to do.
- **07-D4** · FU-851 — overlay caches go stale after plan edits / cooks / finished shops; one invalidation bus for `usePantryBeliefs` + `usePlannedDemand` + `useBuyVerdict` (07-R6 makes them one shape first).

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `compute_belief` | hand-rolled depletion model | a forecasting lib | **keep** | — | Coarse-by-design (Charter P2); a library would add precision the product refuses. |
| `mean_gap_days` | arithmetic | `statistics.fmean` over diffs | **keep** | — | The sorting/zero-gap rule is the point. |
| module caches (`usePantryBeliefs`, `usePlannedDemand`) | cache | Pinia store / TanStack Query | **wrap** (07-R6) | S | One factory, not a dependency. |
| `SURFACE_FLAGS` string map | config | enum | **keep** | — | Closed set, R-010 carve-out documented. |

### C10. Standards drift (R-0NN)
- **R-021** · 07-R1 — fix (the FU-525 precedent).
- **R-032 / FU-684** · 07-R2 — fix; removes five includes that existed only to make a relationship read work.
- **R-003** · 07-R4, 07-R5, 07-R7, 07-R9 — fix.
- **R-001** · 07-R6 — fix; 07-R13 → Chunk 13.
- **R-002 / FU-777** · 07-R15 — fix.
- **R-004/R-008** · 07-R14 (`flask.session` in a rule module) — fix via 07-R8 / FU-654.
- **R-010** · closed-set strings (`believed_band`, hint kinds, surfaces) documented as carve-outs — clean.
- **R-027** · pure composer + repo gather split — exemplary; the chunk's shape to copy elsewhere.

### C11. Ride-along signals for FU-010 / FU-224
- Dora glyph tinted `--semantic-warning` on `--semantic-warning-soft` across chip/card/row/planner — consistent; the planner's `text-warning` (07-R15) is the one stray.
- The dashed `--accent-mark` ring (D-5) vs the amber belief tint in the picker header: two hues for one uncertainty — intentional per D-5 (accent = "metadata about the level"), note for FU-224.

## D. Test plan — Zero-Input Pantry

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__gather__dates_bucket_in_household_zone__not_utc` (level changed 22:00 UTC = 08:00 AEST next day → `days_since_hard == 0`, *Updated today*) | pytest unit (gather with a stub repo) or e2e via `/beliefs` with `timezone=Australia/Sydney` | **must-write-before-ship** | 07-R1 — the FU-525 shape, for belief. |
| `test__belief_envelope__out_is_never_high_confidence` (property over the constants) | pytest unit (hypothesis or a grid) | **must-write-before-ship** | pins impl-plan §1.3's guarantee that every overlay gate relies on; guards 07-R10 either way. |
| `test__recipes__inference_hint__with_no_relationship_include` | pytest e2e | nice-to-have | 07-R2 — proves the FK path hydrates the hint. |
| `test__beliefs_dto__renders_five_fields_only` | pytest e2e (`test_pantry_beliefs_endpoint.py`) | housekeeping | 07-R12. |
| `inferenceHint.spec.ts` | vitest | housekeeping | 07-R5. |

Not proposed: e2e for the shopping / planner hints (drive once with the dense seed); anything for the settings toggles beyond the existing `test__beliefs__per_user_opt_out__gates_and_persists`.

## E. Proposed follow-ups (orchestrator allocates ids)

- type=finding · *`ConsumptionEvent.from_sequence/to_sequence` are written and never read — weight them or drop them* (07-R10 / 07-D2) — owner decision; opportunistic.
- **Resolve:** FU-686 and FU-695 (07-R3 deletes the chip and rewords the five comments).
- Existing FUs this chunk executes against: **FU-684** (07-R2 — the belief/overlay slice of the R-032 sweep), **FU-654 / 02-R12** (07-R8 — three more copies), **03-R36** (07-R20), **05-R24** (07-R4 supersedes the need for `beliefBand.ts`), **FU-777 class** (07-R15).
- Existing FUs referenced, unchanged: FU-683 (plan done; browser-verify owed), FU-851 (07-D4), FU-525 (precedent).

## F. Summary for the register

- FST rows: 12 golden + 13 edge + 4 gate · Help entries: 3 new + 1 extended · Review findings: 22 (execute 15 / FU 1 / waive 3 / conditional 1 / design-record 4 / fold 2) · Tests: 5 (must-write 2) · Bugs: 3 (belief dates taken in UTC against a household-local today — "Updated 1 day ago" for this morning's change and a shortened pin window; the overlay reads the `noload` level relationship that five includes exist only to prop up; the orphaned `PantryBeliefChip` still maintained)
- One-line: the flagship is the cleanest module in the app — a pure composer, one cadence chokepoint, one surface→flag map, honest gates — and its two real defects are both *calendar* ones: belief dates its hard signals in UTC while comparing to a household-local today, and the overlay still reads the level off the relationship the rest of the group learned not to trust.

### Feedback coverage — Zero-Input Pantry is a champion-plan invention; the bullets it touches

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| ZP1 | L89 — combine planned meals with stock level; "Milk is low and on 5 planned meals"; distinguish going-to-cook vs already-cooked | `planned_demand.py` (needed vs covered meals, Out > Low urgency) + `PlannedDemandCard` / verdict plan reason (Chunk 6) + `generate_pantry_check`'s cook-decision trigger | ✅ done (Chunk 6 owns the card; the alert form is FU-849's shopping-list half) |
| ZP2 | STOCKTAKE §150 — marking down should prompt to add to list | auto-add-when-low hook (`update_stock_item._try_auto_add`), unchanged by inference | ✅ complementary |
| ZP3 | Owner 2026-08-17 (Settings batch) — show Dora's belief where stock items turn up, not only where they're managed | FU-653 → `inference_overlay.py` + three toggles | ✅ done (FU-653 resolved) |
| ZP4 | Owner 2026-08-16 — always show Dora's opinion on the item page, including when she agrees | `PantryBeliefCard` | ✅ done |
| ZP5 | Owner 2026-08-15 / D-5 — one uncertainty marker on the level box, hint rides the picker | `StockItemRow` dashed ring + menu header | ✅ done (chip orphaned → 07-R3) |
