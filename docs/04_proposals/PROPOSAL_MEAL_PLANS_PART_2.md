# Meal Plans — redesign proposal, Part 2: **Cook batches** (one cook, several days)

**Status:** proposal · changes **no code** · design brief for a build agent.
**Extends:** [`PROPOSAL_MEAL_PLANS.md`](PROPOSAL_MEAL_PLANS.md) (Wave C-2). Part 1
redesigned the meal-plan *surface* and defined the **batch-cooker vs fresh-cooker**
personas (Part 1 §7). It never built the batch-cooker's core *planning* mechanic —
"cook one thing once, eat it across several days." **This is that mechanic.**

**Motivating feedback:** `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`
line 371 (bullet **F26** in Part 1's coverage table): *"It is absolutely essential to
ensure the UX works for both groups of people: those who batch cook (store meals) and
those who cook only fresh… it should feel useful and informative for those who like to
prep and plan ahead."* Part 1 addressed the *persona framing*; the actual "plan ahead
by cooking once" primitive was left unbuilt. Part 2 closes it.

**Reads from (verified live, file:line in §2):**
`dora_api/domain/entities/{meal_plan_entry,meal_plan,cook_event,meal_plan_reconcile_receipt}.py`,
`dora_api/persistence/table_mappings.py`,
`dora_api/features/meal_plans/{create_meal_plan,update_meal_plan,build_week,get_meal_plan_ingredients,get_shortfall,reconcile,reconcile_consumed_meals,swap_suggestions}.py`,
`dora_api/features/recipes/{pool,cook_recipe,adjust_recipe_meals,get_recipes}.py`,
`dora_api/features/shopping_lists/auto_generate.py`,
`web_app/src/pages/MealPlansOverview.vue`,
`web_app/src/components/{MealPlanWeekDayCard,MealPlanEntryChip,MealPlanRichCard,MealPlanMobileFocus,MealPlanBuilderDialog}.vue`,
`web_app/src/composables/{useCookingPolicy,useBatchEnabled}.ts`,
`web_app/src/pages/settings/AdminSystemCookingSettings.vue`.

**Governing principles:** Dashy Dora Decision Charter — every section checked against
**Effortless** (Dora proposes; the user rarely touches a control) and **Anti-creep**
(fold into what exists; reuse the pool/shortfall/highlight plumbing; no new page, no new
concept where an existing one can be promoted). Engineering: `ENGINEERING_STANDARDS.md`
R-003 (single source of a domain fact), R-005/R-006 (portable, additive migrations),
and the state-ownership rule (server owns derived cross-entity facts).

---

## 0. TL;DR for a build agent

1. Add a **first-class `CookBatch`** entity (a side-table beside `MealPlanEntry`, exactly
   like `MealPlanReconcileReceipt`/`MealPlanSwapLedger`) + a nullable
   `MealPlanEntry.cook_batch_id` FK. A `CookBatch` groups **≥2 entries that share one
   recipe and one slot, on distinct days** — "cook X once on the earliest day, eat it on
   each linked day."
2. **The demand math needs NO changes** (§6, corrected 2026-08-11). Under the chosen
   Σ-yield model (`total_yield = Σ entries' servings`), a batch of 6 portions needs
   6-portions-of-ingredients whether cooked once or three times, and the existing per-recipe
   servings-sum already equals total_yield. Ingredients / cost / shortfall / pool-drain are
   all provably batch-invariant (pinned by an e2e test). The backend delta is *only* the
   grouping data model + read view (Phase 1). **There is no "demand-collapse" phase.**
3. **Derive, don't store**, cook-day (= earliest linked day) and span. The entity is thin
   on purpose; it's first-class for *identity, integrity, the demand-collapse, and future
   cross-week*, not for its column count.
4. **Fold into the existing "Batch" cook-style** (`AppSetting.batch_features_enabled`):
   when the household is Batch, the builder proposes cook-batches and manual linking is
   available; when Fresh, none of it appears. No new setting, no new use of the word
   "batch" in the UI.
5. **UI = a per-entry "linked cook" marker** (reusing the existing left-accent + the
   highlight-a-set-of-entries plumbing), **not** a spanning bracket — the planner is
   day-major and a spanning visual would need a layout it deliberately retired.
6. The one real refactor: the meal-plan **update flow destroys and recreates all forward
   entries** (`update_meal_plan.py:117-134`). Extend the save payload so entries carry an
   optional **`cook_key`** grouping token; the server recreates entries *and* their
   `CookBatch` rows together atomically. This sidesteps the "entries have no stable
   identity" problem without a risky identity-preserving rewrite.

---

## 1. The three "cook/batch" things — do not conflate (naming)

The codebase already overloads these words. A build agent MUST keep them distinct:

| Name | Kind | Meaning | Direction |
|---|---|---|---|
| **`CookEvent`** (`cook_event.py:8-38`) | existing log | "I cooked recipe X today, N portions." One POST → one row. | retrospective |
| **`batch_features_enabled`** (`AppSetting`, FU-615) | existing flag | Install "Batch vs Fresh" cook-style. Today it only *reveals the pool tools*. | setting |
| **`Recipe.available_meals`** (the "pool", `recipe.py:29`) | existing count | Portions of a recipe **already cooked and on hand now**. | retrospective / inventory |
| **`CookBatch`** (NEW, this doc) | new entity | A **planned** cook that fills several **future** slots. | prospective / planning |

**User-facing copy never says "batch."** Use *"Cook once"* / *"cook once, eat Mon–Wed"* /
a link affordance. "Batch" stays the name of the cook-style setting only. See §4 for why
`CookBatch` is folded *under* that setting rather than given its own.

---

## 2. Re-grounding (verified against live code)

### 2.1 The meal-plan data model
- **`MealPlanEntry`** (`meal_plan_entry.py:8-21`; table `table_mappings.py:898-907`):
  `id`, `recipe` (rel, `lazy="noload"`, mapped `:1501`), `scheduled_for: date`,
  `servings: int` (default 1), `slot: str` (free-text, validated against the `MealSlot`
  vocabulary at the write boundary — **not** an FK), `consumed_at: datetime | None`. FKs:
  `recipe_id`→Recipe (CASCADE), `meal_plan_id`→MealPlan (CASCADE). **No** `created_at`, **no**
  owner, **no** grouping/cook column today.
- **`MealPlan`** (`meal_plan.py:10-25`; table `:846-856`): the per-week parent —
  `entries` (cascade all/delete-orphan, `:1519-1524`), nullable `name`, `start_date`, and
  three provenance-only plain-id fields (`source_template_id`, `source_template_set_id`,
  `rotation_index` — no DB FK).
- **Side-table precedent:** `MealPlanReconcileReceipt` (`:876-896`) and
  `MealPlanSwapLedger` (`:859-875`) already sit beside entries as their own tables. **This
  is the pattern `CookBatch` follows.**
- **`CookEvent`** (`cook_event.py:8-38`): `recipe_id`, `recipe_name`, `meals_cooked`,
  `cooked_by_user_id`, `occurred_at`. Its docstring already frames the batch case: *"a
  household that batch-cooks Sunday and reheats through the week leaves a single event on
  Sunday."* It is the retrospective analog of what we're building forward.

### 2.2 The pool (retrospective) — must not be touched at plan time
- `Recipe.available_meals` is the on-hand cooked-portion count. One write authority:
  `pool.py:bump_pool()` (`:50`, floor-at-zero `:79-90`).
- Cook mode's "how many meals did you cook?" → `cook_recipe.py` bumps the pool **up**
  (`:62`), stamps `last_made_on` (`:64`), logs a `CookEvent` when `>0` (`:70-76`).
- `_hydrate_unallocated` (`get_recipes.py:803`, `:873`):
  `unallocated = max(available_meals − Σ future un-consumed committed servings, 0)`. So
  planning a meal already *subtracts from the displayed pool* — a **pull** model.
- **`get_shortfall.py:44-56`**: `SUM(servings) … HAVING SUM > available_meals` → "you must
  cook N by <day>." **This is the inverse of a cook-batch** — it detects a needed cook;
  a `CookBatch` is the user planning that cook up front. Design `CookBatch` as a *peer*
  of shortfall, sharing this plumbing, not a competitor.

### 2.3 Reconcile (consumption) — drains per entry
- Daily sweep `reconcile_consumed_meals.py` (gated by `AppSetting.auto_drain_past_meals`,
  `:46-51`): auto-drain ON stamps past entries `consumed_at` and decrements the pool by
  summed servings (`bump_pool(-…)`, `:106`); OFF writes manual-confirm receipts only.
- Per-entry verbs `reconcile.py` (`:97-103`): cooked / cooked_adjusted / cooked_later /
  not_cooked / skip. Pool math is a *reconciliation delta* (`:601`, `:604`), not a fresh
  drain. **FU-594 quirk:** `skip` is pool-neutral; `not_cooked` is the verb that *reverses*
  a sweep drain (`:479-485`).

### 2.4 Ingredient/cost aggregation — one primitive, several feeders
- **Single scaling primitive:** `aggregate_meal_plan_ingredients()`
  (`get_meal_plan_ingredients.py:29-77`) takes a `{recipe_id: total_servings}` map and
  scales each ingredient by `servings / recipe.servings` (`:51-52`), summing per stock item
  (`:60-63`). Agnostic to how the map was built — **this function needs no change.**
- Feeders that build the map by **summing servings across entries** (these are where a
  batch would double-count — see §6): preview `:135-139` (`+= r.servings` `:138`),
  saved-plan `:94-104` (`+= _Entry.servings` `:100-102`), shortfall SQL SUM `:44-56`,
  budget cost `swap_suggestions.py:271-278` (+`_entry_cost :102-112`), pool drain
  `reconcile_consumed_meals.py:97-106`, generated-plan cost preview `build_week.py:478-479`.
- **Already batch-safe:** the shopping-list generator (`auto_generate.py`
  `_collect_meal_plan_week :408-480`, `_collect_recipes :351-406`) is *presence-based* —
  dedupes to one line per stock item, `quantity=1` (`:246`), never scales by servings.

### 2.5 The write path (the refactor hinge)
- No per-entry CRUD. Entries are written as a whole-plan replacement: create
  `POST /api/meal-plans` (`create_meal_plan.py:106`, payload `:26-42`), update
  `PATCH /api/meal-plans/<id>` (`update_meal_plan.py:140`) which **preserves past/consumed
  entries and destroys + recreates the entire forward portion** (`:117-134`).
- Auto-build `POST /api/meal-plans/auto-build` (`build_week.py:521`) is **preview-only,
  never persists**; the client commits via create/update.
- **Consequence:** forward entries have *no stable identity across edits*. §7 resolves this.

### 2.6 The UI (day-major everywhere)
- `MealPlansOverview.vue`: desktop 3-column row (`:72`) — left recipe list (`col-md-3`),
  **middle week body** (`col-md-6`, `:95`), right calendar/shopping (`col-md-3`). Middle is a
  **vertical stack of day cards** (`v-for` day → `MealPlanWeekDayCard`, `:188-208`), Mon→Sun,
  up/down carousel (`:182` transition). Hard `$q.screen.lt.md` fork (`:31` vs `:58`) → mobile
  swaps to `MealPlanMobileFocus` (single focused day).
- `MealPlanWeekDayCard.vue`: one day; **slot-rows inside** (`:12-49`), label column `:182-188`,
  entries `:28-48`, empty slots collapse (`visibleSlots :133-135`).
- `MealPlanEntryChip.vue` (desktop entry): full-width button `:2`, **3px `border-left`
  accent** `:121-153` (brand / amber-shortfall / neutral-consumed), `--highlight` outline
  `:154-157`, slot eyebrow `:162-168`.
- `MealPlanRichCard.vue` (mobile entry): thumb + name + slot-tag `:224-233`, same left-accent
  `:143`/`:164-174`, highlight `:171-174`.
- **Highlight-set plumbing (reuse this):** `hoveredRecipeIds`/`shortfallRecipeIds` sets flow
  down to per-entry booleans (`MealPlanWeekDayCard.vue:198-199`). A "highlight all entries in
  this cook" indicator is the same mechanism.
- **Layout verdict:** a literal spanning bar across Mon/Tue/Wed dinner is *hard* — the three
  entries live in separate, non-aligned day cards (and on mobile the other days aren't even
  rendered). It would need a slot-major grid (deliberately retired, Part 1 §3.2 / FU-304).
  A **per-entry marker fits the current DOM with no restructuring** (§8).

---

## 3. The concept

A **cook batch** is one cooking session whose output is eaten across several scheduled
meals. v1 scope (locked with the owner):

- **Same recipe, same slot, distinct days.** e.g. "Chicken curry, dinner, Mon+Tue+Wed."
  (Cross-slot — a pot that does lunch *and* dinner — is **out of scope**; the user's escape
  is "leave lunch empty and eat the leftovers off-plan," which we don't model.)
- **Cook-day = the earliest linked day** (derived, automatic). The remaining linked days are
  **leftover days** (reheat, no cook prompt).
- **A single cook** produces the whole batch; **total yield = Σ the linked entries'
  servings** (which already default to the household headcount, FU-615).
- **≥2 entries.** A one-day "batch" is just a normal meal — no `CookBatch` row.

This is the missing **middle** between Part 1's two extremes: today the builder offers only
*all-distinct* (default) or *identical every day* ("repeat same day"). "Cook once for these
three days" is the controlled-overlap the owner asked for — and it's distinct from *identical
every day* (which is **re-cook fresh** N times; a batch is **cook once**, leftovers after).

---

## 4. Fold into the "Batch" cook-style (naming + gating decision)

**Decision (owner-agreed):** `CookBatch` is what the existing **Batch** cook-style unlocks —
not a new, separately-gated feature.

- Today `batch_features_enabled` (Admin → Settings → System → Cooking,
  `AdminSystemCookingSettings.vue:51-57`, served via `/api/health.cooking_policy`, read by
  `useCookingPolicy.ts:36` / `useBatchEnabled.ts`) is a thin "show the pool tools" flag.
- **Promote it:** *Batch* household ⇒ the pool tools **and** cook-batch planning (builder
  proposes cooks; manual linking available). *Fresh* household ⇒ neither; the planner stays
  pure scheduling (Charter P10 anti-creep, unchanged).
- This dissolves the naming collision: there is exactly one "Batch" concept in the UI (the
  cook-style), and `CookBatch` is its internal machinery. No second user-facing "batch."

**Why this is on-charter (Anti-creep):** we are not inventing a concept — the app already has
the *retrospective* version of "one cook feeds many meals" (cook → pool → `unallocated`
earmarks future meals → `shortfall` warns). `CookBatch` promotes that implicit mechanic to an
explicit, *prospective* planning primitive, reusing the same pool/shortfall/highlight plumbing.

---

## 5. Data model (first-class `CookBatch`)

### 5.1 Entity + table
New entity `CookBatch` (`dora_api/domain/entities/cook_batch.py`), side-table
`CookBatch` in `table_mappings.py` beside the existing meal-plan side-tables:

| Column | Type | Note |
|---|---|---|
| `id` | UUID PK | |
| `meal_plan_id` | UUID FK→MealPlan (CASCADE) | **plan-scoped in v1** (see §5.3) |
| `recipe_id` | UUID FK→Recipe (CASCADE) | the one recipe all linked entries share — integrity anchor + the recipe the single cook produces |

New column on `MealPlanEntry`: **`cook_batch_id: UUID | None`** FK→CookBatch
(`ondelete=SET NULL`), nullable — null ⇒ a standalone meal (today's behaviour, unchanged).
Add the FK covering index (R-034).

**That's the whole schema.** Everything else is derived (§5.2). The entity is intentionally
thin; it earns "first-class" through **identity** (entries know they share a cook),
**integrity** (real FK, not a loose group-id the destroy/recreate flow can't validate — §7),
the **demand-collapse** (§6), and **room to grow** (§5.3, §9). A bare `cook_batch_id`-only
grouping (no table) was rejected: it has nowhere to hold batch-level facts without
denormalising them across rows (violates R-003 / state-ownership), can't enforce integrity,
and can't span weeks.

### 5.2 Derived, never stored (state-ownership / R-003)
Computed server-side from the batch's entries, exposed on the read DTO:
- **`cook_day`** = `min(entry.scheduled_for)` over the batch's entries.
- **`total_yield`** = `Σ entry.servings` — the servings the single cook must produce, and the
  figure ingredient/cost demand uses (§6).
- **`span_days`** = `max(scheduled_for) − min(scheduled_for)`.
- **`keeps_ok`** = `span_days ≤ freshness_horizon` (§10).

Never persist these — they're pure functions of the entries (R-003: one source of truth).

### 5.3 Scope decision: plan-scoped v1, cross-week later
v1 `CookBatch.meal_plan_id` ties a batch to one week's plan (cascades with it). "Cook Sunday,
eat into next week" (cross-`MealPlan`) is a **documented future extension** the first-class
model *allows* without a remodel (drop `meal_plan_id`, or make it the cook-day's plan) —
explicitly **not** built now (Anti-creep). Recorded as a future extension, not an open fork.

---

## 6. The servings split — why the demand math is already correct (CORRECTED 2026-08-11)

> **CORRECTION (verified during the Phase-1 build).** An earlier draft of this section
> claimed six summation feeders would "double-count" a batch and needed a collapse helper.
> **That was wrong** — it assumed a *single-yield* model (a batch cooks one day's servings,
> leftover days are "free"). The proposal committed to the **Σ-yield model** instead
> (`total_yield = Σ the linked entries' servings`), and under it the demand math is already
> correct with **no code change**. Confirmed by an e2e test
> (`test_cook_batches.py::test__ingredient_demand__is_identical_linked_vs_unlinked`): the
> ingredient demand for a linked batch equals the demand for the same entries unlinked.

**Principle (holds, but needs no new code):** the **batch** is the unit of *demand*; the
**entry** is the unit of *consumption*. Under the Σ-yield model these coincide numerically —
because a batch of Mon/Tue/Wed dinner at 2 servings each is a single cook of **6 portions**,
and 6 portions need 6-portions-of-ingredients whether you cook once or three times. Batching
changes **cook count and waste, not quantity**. `aggregate_meal_plan_ingredients` already
sums servings *per recipe* and scales once, which already equals `total_yield` — so:

| # | Feeder (file:line) | Status under Σ-yield |
|---|---|---|
| A | Builder preview `get_meal_plan_ingredients.py:135-139` (client `MealPlanBuilderDialog.vue:534-536`) | **already correct** — sends `{recipe_id, servings}` per day, summed = total_yield. The preview endpoint doesn't even need `cook_key`. |
| B | Saved-plan `/ingredients` `get_meal_plan_ingredients.py:94-104` | **already correct** — sums `servings` per recipe; never references `cook_batch_id`. Pinned by the invariance test. |
| C | Shortfall `get_shortfall.py:44-56` | **already correct** — committed portions to cook = Σ servings regardless of how many cook sessions produce them. |
| D | Budget cost `swap_suggestions.py:271-278` (+`_entry_cost:102-112`) | **already correct** — the week's food cost is the cost of Σ servings; batching doesn't change what you buy. |
| E | Pool drain `reconcile_consumed_meals.py:97-106` | **already correct** — each past day drains its own servings (2+2+2=6); the pool was bumped +6 by the one cook (cook mode), so it nets out. Reconcile never *bumps* on cook, so there's no N× cook-bump to collapse. |
| F | Generated-plan cost preview `build_week.py:478-479` | **already correct** — sums proposed-entry cost = total_yield cost. |

So **there is no Phase-2 "demand-collapse" work.** The backend delta for this feature is
entirely the **grouping data model + read view (Phase 1, DONE)**; the numbers take care of
themselves. `aggregate_meal_plan_ingredients` stays agnostic, as do the shopping-list
generator, dashboard "Next to cook", and alerts (all confirmed batch-safe).

**Reconcile/pool (no change needed either).** The pool (`available_meals`) is bumped only by
cook mode's "how many did you cook" — the user logs the whole batch once (e.g. +6). Reconcile
only *drains* consumption per past day. Neither references batching, so both are correct as-is.
A *nice-to-have* (not v1-required): when the user reconciles/cooks the cook-day of a batch,
prompt "cook the whole batch (6)?" so the single bump is one tap — pure UX sugar on top of
already-correct math, deferred (§12).

---

## 7. Write-path change (the hinge) — grouping token, not identity rewrite

The forward-replace flow (`update_meal_plan.py:117-134`) destroys and recreates entries, so
they have no stable identity. Rather than a risky identity-preserving rewrite, **extend the
payload to express grouping and recreate cooks + entries together atomically:**

- Add an optional **`cook_key: str | null`** to the entry payload shape
  (`CreateMealPlanEntryRequest` `create_meal_plan.py:26-32`, `UpdateMealPlanRequest` entries
  `update_meal_plan.py:26-45`). It is a **transient client token** (e.g. `"c1"`), not a DB id.
- Server groups incoming forward entries by `cook_key`; for each group it **validates**
  (§ below), creates one `CookBatch` (`recipe_id` from the group, `meal_plan_id` = this plan),
  and sets each entry's `cook_batch_id`. Entries with no `cook_key` are standalone (today's
  path). Past/consumed entries are still preserved untouched.
- Because the whole forward structure (entries **and** their grouping) is replaced together,
  the destroy/recreate model stays — the client is already the source of the desired
  end-state; it now just also declares the grouping. No entry-identity continuity needed.

**Server-side validation of a `cook_key` group (reject with 400 on violation):** all entries
same `recipe_id`; all same `slot`; `scheduled_for` distinct; ≥2 entries; none in the past.
Freshness span is a **warning, not a rejection** (§10).

Auto-build (`build_week.py`, preview-only) gains the ability to *emit* grouped proposed
entries (each carrying a `cook_key`) when the household is Batch (§9); the client renders them
linked and commits them through the same payload.

---

## 8. UI spec (per-entry linked marker — no layout restructure)

Reuse the existing per-entry channels; do **not** attempt a spanning bracket (§2.6 verdict).

- **Linked marker on each entry in a cook:** a distinct treatment on the existing 3px
  `border-left` accent (`MealPlanEntryChip.vue:130`, `MealPlanRichCard.vue:143`) — a dedicated
  linked-cook colour/pattern — plus a small **link glyph** and an eyebrow caption reusing the
  slot-eyebrow pattern (`MealPlanEntryChip.vue:162-168`, `MealPlanRichCard.vue:224-233`):
  - cook-day entry: **"Cook · serves N total"** (the day you actually cook).
  - leftover-day entries: **"Leftovers · cooked <weekday>"** (reheat, no cook).
- **Group affinity on hover/focus:** drive the existing highlight-set plumbing
  (`hoveredRecipeIds`-style set → per-entry boolean, `MealPlanWeekDayCard.vue:198-199`;
  `entry-chip--highlight :154-157`, `rich-card--highlight :171-174`) with the batch's entry
  ids, so hovering one linked entry outlines all of them. This is the association cue that
  replaces a physical connector, and it works identically on desktop and **mobile** (where a
  connector is impossible — only one day renders, `MealPlanMobileFocus.vue:89-100`).
- **Creating a link (manual):** on an entry's existing `q-menu` action popup, add **"Cook once
  for more days →"** → a day multiselect (same slot, upcoming days). Confirm ⇒ the selected
  days get entries sharing this entry's `cook_key`. Gated on `batchEnabled`.
- **Unlinking:** "Separate this cook" on any linked entry → clears the group (entries become
  standalone). Removing the cook-day entry promotes the next-earliest to cook-day (derived, so
  automatic).
- **Fresh cook-style:** none of the above renders; entries show exactly as today.

**No middle-area restructure.** If a true slot-major week grid is ever reintroduced for other
reasons, a spanning bar becomes possible — noted, not planned.

---

## 9. Builder integration (Effortless default)

When the household is **Batch**, "Build my week" (`MealPlanBuilderDialog.vue`, `build_week.py`)
should *propose* cook-batches so the median user never links anything by hand:

- After selecting recipes, group a chosen recipe across the run of days in a slot into one
  cook where sensible (bounded by the freshness horizon §10 and headcount yield), emitting
  grouped proposed entries (`cook_key`). This is also the natural, honest answer to Part 1's
  FU-611 shortfall ("your cookbook is smaller than the grid") — fewer *distinct* cooks, each
  feeding more days, instead of blank days.
- The Review step shows the proposed cooks with the §8 markers; the user can split/relink
  before saving.
- **Fresh** cook-style: unchanged — one distinct recipe per cell, no proposals.

This is the "cohesion" end of the axis discussed in design (fewer distinct cooks ⇒ tighter
shopping), now concrete. The separate *ingredient-overlap ranking* preference (bias distinct
cooks toward shared ingredients) is **out of scope for Part 2** — logged as a future
extension (§12); Part 2 is the batching primitive only.

---

## 10. Freshness horizon

Cooked food doesn't keep forever, so a cook's `span_days` is bounded.

- **v1: a single global default horizon** (proposed **4 days**), a named constant server-side.
  A cook whose span exceeds it gets a **non-blocking warning** at link/build time ("most
  cooked meals keep ~4 days — that's a long stretch for one cook") — never a hard reject
  (owner controls their own kitchen). Dora already owns expiry/freshness, so this is in
  character.
- **Future extension (not built):** a per-recipe `keeps_days` override (some dishes freeze,
  some don't). Noted in §12; a global default is enough for v1 (Anti-creep).

---

## 11. Charter & standards check

- **Effortless:** Batch households get auto-proposed cooks (one tap); manual linking is the
  power layer, not a required step. Fresh households see nothing new.
- **Anti-creep:** no new page, no new setting, no new user-facing word — folds into the
  existing Batch cook-style and reuses pool/shortfall/highlight plumbing; promotes an
  already-implicit mechanic rather than inventing one.
- **State-ownership / R-003:** `cook_day`/`total_yield`/`span` are server-derived, never
  duplicated; demand math stays in the one aggregation primitive.
- **R-005/R-006 (portable, additive migration):** one new table + one nullable FK column +
  its index — additive, no table rewrite, SQLite + Postgres safe. Pre-release, so no data to
  preserve.
- **R-034:** the new table + index are declared in the ORM model, and the FK column carries a
  covering index.
- **Distribution/tenancy:** no tenancy assumptions; repository-routed like its siblings.

---

## 12. Future extensions (explicitly not built in Part 2)
- Cross-week cooks (cook Sunday, eat into next week) — §5.3.
- Per-recipe `keeps_days` freshness override — §10.
- Ingredient-overlap **ranking** preference for distinct cooks (tighter shopping among
  non-batched meals) — §9.
- Cross-slot cooks (one pot → lunch + dinner) — §3 (owner deferred).
- A slot-major week grid enabling a literal spanning-bar visual — §8.

---

## 13. Sequencing (updated 2026-08-11 with build progress)
1. **Backend model + write path** (the hinge, §5 + §7): `CookBatch` entity/table,
   `MealPlanEntry.cook_batch_id`, migration, `cook_key` grouping + validation in
   create/update, read DTO with derived fields. — ✅ **DONE + tested** (`test_cook_batches.py`,
   8 tests: grouping, all four validation rejections, derived view, forward-replace lifecycle,
   demand-invariance; schema-match test green; migration chain single-head).
2. ~~Demand-collapse~~ — **removed.** §6 correction: batch-invariant under the Σ-yield model,
   no code change. Pinned by the invariance test.
3. ~~Reconcile/pool execution~~ — **removed** for v1 (§6): pool bump is cook-mode-driven and
   already once; reconcile drains per day, already correct. The "cook the whole batch?" prompt
   is deferred UX sugar (§12).
4. **UI (§8):** per-entry linked markers + the link/unlink menu + day-picker, gated on
   `batchEnabled`; desktop + mobile. — ✅ **DONE + verified live** (markers correct, unlink
   dissolves the batch). *(Highlight-set hover affinity dropped as unnecessary — the persistent
   per-entry marker already associates a cook; noted as a possible future polish.)*
5. **Builder proposals (§9):** `place_entries_batched` + `_batch_cook_span` in `build_week.py`,
   `ProposedEntry.cook_key`, review markers + defensive `validCookKey`, commit sends `cook_key`.
   — ✅ **DONE + verified live** ("Build my week" → 18 markers → 6 CookBatch rows). Ties off FU-611.
6. **Verification** — ✅ backend gate 59 green; Phases 4 + 5 driven live. One light owner-walk
   (the manual "Cook once for more days" *picker dialog*) queued in `DORA_VERIFY.md`.

**FEATURE COMPLETE (FU-617 → RESOLVED, 2026-08-11).** Built end-to-end; Phases 2/3 dropped as
no-ops (§6). Future extensions in §12.

---

## 14. From the original spec
Skimmed `docs/00_original_spec/` (Feature Boards/Meals.md, Feature Notes/Automated meal
plans.md). Nothing substantive to extract: the original meal-plan intent there is
**nutrition-driven** automated planning (out of scope — nutrition is off+simple only per
`RECONCILED_FINISHING_PLAN.md §7`), and the only prep-adjacent line is "I can see the
ingredients required for the next week of meal prep" (already delivered by the
ingredient-demand surface). The batch-cooking intent this doc serves comes from the
**feedback** (F26 / line 371), not the original spec. **(no keep/consider items)**

---

## 15. Open decisions — all closed inline
Per the CLAUDE.md close-out rule, every fork is resolved in-doc (no live "open decisions"):
1. Separate feature vs fold into Batch cook-style → **fold in** (§4). *(owner-agreed)*
2. First-class entity vs `cook_batch_id`-only grouping → **first-class `CookBatch`** (§5). *(owner-agreed; code-confirmed)*
3. Write-path: identity-preserving rewrite vs grouping token → **`cook_key` grouping token, recreate together** (§7).
4. Cook-day stored vs derived → **derived (earliest day)** (§5.2). *(owner-agreed)*
5. Freshness source → **global default (4 days), warn-not-block** (§10); per-recipe override deferred (§12).
6. Batch scope → **plan-scoped v1**, cross-week deferred (§5.3).
7. UI: spanning bar vs per-entry marker → **per-entry marker** (§8). *(code-confirmed feasible)*
8. Linking axis → **same slot, multiple days** (§3). *(owner-agreed)*

Build tracking spawned as **[[FU-617]]** (`DORA_FOLLOWUPS.md`) — implement Part 2 when
prioritised.

---

## 16. Coverage table (feedback bullets → sections)
Part 2 is a **deepening of one Part-1 bullet**, plus the ripple it implies. Per the CLAUDE.md
rule, mapped against `Feedback _ Fixes - as of [06-Jun-2026].md §MEAL PLANS`:

| Bullet | Where |
|---|---|
| **F26** — "essential the UX works for batch cook (store meals) *and* fresh… useful for those who prep and plan ahead" (line 371) | **The whole of Part 2** — §3 concept, §4 fold-in, §9 builder proposals. Part 1 §7 framed the persona; Part 2 builds the batch-cooker's planning mechanic. |
| F1 / FU-611 — sequential builder leaving days blank when cookbook < grid | §9 — cook-batches are the honest fix (fewer distinct cooks feeding more days) |
| F47 — "same recipe same slot → increment" (Part 1 §3.2) | Adjacent but distinct: F47 is *stacking servings in one cell*; a `CookBatch` is *one cook across cells*. Part 2 doesn't change F47. |
| All other F1–F49 | **Out of scope** — owned by Part 1; Part 2 adds no surface that touches them. |

No feedback bullet for this surface is newly *stranded* by Part 2. After merge, check
`docs/02_feedback/COVERAGE_GAPS.md` and flip F26 from persona-framing to *mechanic-built* once
Part 2 ships.
