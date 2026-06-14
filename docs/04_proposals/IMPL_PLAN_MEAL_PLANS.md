# Implementation Plan — Meal Plans (C-2 impl)

**Status:** Plan for review · **Date:** 2026-06-14 · **No code yet** — phased
plan + first reviewable chunk.
**Source proposal:** `PROPOSAL_MEAL_PLANS.md` (decisions resolved §2;
smaller calls in §11 — defaults adopted below, see §3).
**Adjacent IMPL plans:**
- `IMPL_PLAN_STATE_OWNERSHIP.md` — allocation SSOT (`unallocated_meals`)
  **already landed**; the planner reads it, never recomputes it.
- `IMPL_PLAN_COOKBOOK.md` (C-4) — the **Favourites** / **Haven't had in a
  while** trays here are the same component the cookbook wants (different
  metric); the left-column tag filters land when C-4 ships its tag overhaul.
- `IMPL_PLAN_COOK_MODE.md` (C-3) — the per-entry `Cook now` is a passthrough
  to cook mode; the "how many meals did you save?" framing is C-3's.
- `IMPL_PLAN_CART_BUTTON.md` (C-7) — the sidebar per-item add + the
  "Add to / Generate" choice modal **compose** the cart-button decision tree
  (`AddToListButton` + target-list choice modal already exist). Reuse,
  don't re-implement.
- `IMPL_PLAN_CONFIG_AND_OPTINS.md` (C-cross) — the slot-vocabulary settings
  row lives in `PreferencesSettings.vue` (user-scoped, **not** an install
  catalogue like cuisine/category/tools); the money opt-in gates any cost
  surfacing.
**Phase:** Master plan **Phase 1 (the loop)** — meal plans are the *demand*
side of pantry → recipes → meals → lists. The supply side (recipe pool,
cookability) is owned by C-4/state-ownership and consumed here read-only.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-14 against the live entities, table mappings, the two Vue
surfaces, the store/service, and the backend feature folder. The code matches
the proposal's "Re-grounding" (§1) and has **not** moved toward the solution.

**Scoping (foundational — confirmed 2026-06-14):** meal plans, recipes, and
the recipe/slot vocabularies are all **household-wide (instance-global)** —
`MealPlan` has no `user_id` (`meal_plan.py`), `get_meal_plans.py` returns every
plan, and the vocab tables (Cuisine/Category/Tool) are admin-edited install-wide
via `RecipeVocabSettings.vue` + `VocabListEditor.vue`. Per-user state is limited
to appearance/personal toggles (`PreferencesSettings.vue`). **This plan adds no
per-user meal-plan state** — it corrects the proposal §4 "user-scoped slots"
wording to household-wide (see C-2.A).

**Already built (reuse, don't rebuild):**
- **Meals→recipes merge complete.** `Recipe.available_meals` is the on-hand
  pool; `POST /api/recipes/{id}/cook` (`cook_recipe.py:44`) adds + stamps
  `last_made_on`; `POST /api/recipes/{id}/adjust-meals`
  (`adjust_recipe_meals.py:46`) ±deltas, floored at 0.
- **B6 allocation works server-side.** `_hydrate_unallocated`
  (`get_recipes.py:597-639`) computes `committed_meals` +
  `unallocated_meals = max(available_meals − Σ future un-consumed servings, 0)`
  in one GROUP BY. **SSOT lives on the server — the planner must read it, never
  re-sum on the client (R-003).** Browser confirm is **FU-032**.
- **Reconcile hook.** `reconcile_consumed_meals.py:8-61` runs as a Flask
  `before_request` on the dashboard / meal-plan / recipe routers
  (`startup.py:122-123`), marks past-day entries `consumed_at` and decrements
  the pool. Idempotent (conditional UPDATE), separate connection.
- **Shortfall endpoint.** `GET /api/meal-plans/shortfall` (`get_shortfall.py:69`)
  → `Shortfall[]` (`available_meals`, `committed_meals`, `shortfall`,
  `earliest_needed`).
- **Ingredient demand.** `GET /api/meal-plans/{id}/ingredients`
  (`get_meal_plan_ingredients.py:93`) aggregates ingredients across un-consumed
  future entries, grouped by stock item, scaled by `entry.servings /
  recipe.servings`. (F34 math = **new verification FU**, §9.)
- **CRUD.** `POST` / `PATCH` / `DELETE` / `GET /api/meal-plans`
  (`create_meal_plan.py:87`, `update_meal_plan.py:113`, `delete_meal_plan.py:36`,
  `get_meal_plans.py:88`). Backend **already refuses `scheduled_for < today`**
  on create + update, and preserves consumed entries during a future replace
  (`update_meal_plan.py`, `confirm_clear_entries` flag).
- **Frontend surface.** `MealPlansOverview.vue` (~800 LOC) — draggable recipe
  palette + 7-day horizontal grid + drop zones + per-entry menu + shortfall
  banner (L25-50) + ingredient sidebar (L228-289) + `generateListForWeek`
  (L674-715, already routes through `autoGenerateAsync({ sources:
  { meal_plan_week } })`). `MealPlanEditDialog.vue` (~219 LOC) edits
  name/start_date/entries via modal. `useMealPlanExport.openPrintView`
  (CSV already removed, FU-168). Store `mealPlanStore.ts`, service
  `mealPlanApiService.ts`, model `models/mealPlan.ts`.
- **Slot vocabulary mirrored both sides** but **hard-coded**:
  `dora_api/domain/entities/recipe.py:22` and
  `web_app/src/helpers/recipeVocabulary.ts:20-27` both define
  `DEFAULT_MEAL_SLOTS = (Breakfast, Lunch, Dinner, Snack, Dessert)`.
  `MealPlanEntry.slot` is free-text `String(50)`, NOT NULL, no vocab
  constraint (`table_mappings.py:466-475`).

**Not built (this plan delivers it):**
- No templates, template sets, recurring apply, or `source_template*`
  provenance. No `MealPlanTemplate*` entities/tables/routes.
- No vertical week carousel, no named slot rows, no cell-targeted tap-add
  (slot is currently typed in the edit dialog; the dialog hard-codes only
  4 slots, dropping "Dessert" — `MealPlanEditDialog.vue:59`).
- No custom calendar widget — week selection is the "Active plan" dropdown
  (`MealPlansOverview.vue:12-22`).
- No Favourites / Haven't-had-in-a-while trays.
- No sequential builder.
- No **editable** slot vocabulary — it's a hard-coded constant. Meal slots
  should *join* the existing install-wide vocab-table pattern
  (Cuisine/Category/Tool + `VocabListEditor` + `RecipeVocabSettings.vue`) as a
  household-wide table, not a new per-user store (C-2.A).
- `MealPlan.name` is required (`VARCHAR(255) NOT NULL`,
  `table_mappings.py:459-464`); the planner has no concept of "drop the name,
  show Week starting X".

**Live bugs confirmed in-code (folded in below):**
- **Past-day drop 400 (F29).** `MealPlansOverview.vue` `toIso`/`todayIsoLocal`
  (L425-432) and `isPastDay` (L434-436) build the ISO string in a way that
  drifts from the backend's server-local `date.today()`. The classic culprit
  is `toISOString()` (UTC) vs local Y/M/D — at 8am AEST, UTC is still
  "yesterday". Fix in **C-2.K**.
- **R-003 smell (FU-154).** `MealPlansOverview.vue` keeps page-local
  `ingredients`/recipe refs populated by direct API calls in `onMounted`
  (L720-781) instead of fully going through the stores. The C-2.C rebuild is
  the right moment to route these through Pinia. Flag, don't silently re-copy.

**Tests:** no dedicated meal-plan CRUD/reconcile test file exists; meal plans
appear only in `test_data_router.py` (backup/restore sections) and
`test_auto_generate_priority.py` (list-generation context). Every chunk that
touches the backend adds an e2e test under `tests/e2e/dora_api/`.

So the work falls into the proposal's eleven phases (C-2.A…K). Below they are
elaborated into reviewable chunks and **re-sequenced by dependency/risk** in §5
(the proposal's A→K order is conceptual; the build order differs slightly).

---

## 1. Chunked plan (each chunk = one reviewable PR)

### C-2.A — Meal-slot vocabulary (household-wide) ★ FIRST REVIEWABLE CHUNK
**Closes:** §4 + F49 + F35 (partial — the always-"Dinner" bug fully dies in
C-2.C when slot derives from the tapped row; A makes the vocabulary editable
and correct first).

**Scope correction — supersedes the proposal's "user-scoped" wording (§4).**
Verified in code + confirmed with the user (2026-06-14): meal plans are
**household-wide, not per-user** — `MealPlan` has no `user_id`
(`meal_plan.py`; `get_meal_plans.py` returns every plan in the instance), and
the household mental model is "mum plans for a family of 4". So the slot
vocabulary is an **install/household-wide vocabulary edited by admins**,
exactly like the **Cuisine / Category / Tool** vocabularies the cookbook work
already shipped — **not** a per-user preference. This is also the natural home
because `Recipe.time_of_day` already *is* the slot vocabulary. (A dated note
is added to proposal §4.)

Lowest-risk starting point: it's a copy of an existing, recently-built pattern,
and it independently fixes the "Dessert missing in the planner" gap.

- **Backend (mirror `dora_api/features/cuisines/manage_cuisines.py` +
  `domain/entities/cuisine.py`):**
  - New **`MealSlot`** entity + table `{id, name, sequence}`, install-wide.
    **Seed** migration creates the table *and* inserts the five
    `DEFAULT_MEAL_SLOTS` (Breakfast/Lunch/Dinner/Snack/Dessert). Batch-mode,
    reversible (R-005/R-006).
  - New feature `dora_api/features/meal_slots/manage_meal_slots.py` →
    `MEAL_SLOT_ROUTER`: `GET/POST/PATCH/DELETE /api/meal-slots`
    (list ordered + usage count, create with case-insensitive dup-check +
    auto-sequence, rename, delete). **Add a reorder affordance** (sequence in
    the PATCH body or a small reorder verb) — slot order is user-facing
    (the other vocabs don't expose reorder yet; this is a small additive
    extension, not a divergence).
  - **Key difference from Cuisine** (which is an FK on `Recipe`):
    `MealPlanEntry.slot` and `Recipe.time_of_day` **stay free-text strings
    holding the slot *name*** — no FK churn (proposal §4). They validate the
    name against the `MealSlot` table at write-time (R-010; off-vocab rejected
    on *new* writes). **Deleting a slot nulls nothing** — existing entries keep
    their label and simply become "off-vocab" (rendered in the "Other" row,
    C-2.C). The delete-confirm warns "N entries use this slot; they'll keep the
    label."
  - `recipe.py::DEFAULT_MEAL_SLOTS` becomes the **seed** for the table; after
    seeding, the table is the source of truth.
- **Frontend:**
  - Add a 4th **`<VocabListEditor title="Meal slots" …/>`** card to the
    existing **`RecipeVocabSettings.vue`** (alongside Cuisines / Categories /
    Tools) — **no new settings page** (R-001 reuse, R-007). Add a
    `mealSlotStore` + service mirroring the cuisine store/service; wire
    create / rename / delete (+ reorder if `VocabListEditor` supports it, else
    a small up/down control).
  - Slot dropdowns read the `MealSlot` list via the store (fallback to
    `DEFAULT_MEAL_SLOTS` only before first load): fix `MealPlanEditDialog.vue:59`
    (hard-coded 4 → the household list, restoring "Dessert"); the recipe
    `time_of_day` pickers (`RecipeEditDialog.vue`, `RecipeDetailPage.vue`,
    `RecipesOverview.vue`) switch from the bare constant to the same list.
  - **Off-vocabulary historical strings preserved.** A slot value not in the
    current list still displays; in C-2.C it lands in the day's "Other" row.
- **Slot remap UI (§11.4):** **deferred** — [[FU-173]].
- **Ripple (note, don't build):** C-5 onboarding seeds the table (its chunk);
  `Recipe.time_of_day` now shares a real table, consistent with the other
  recipe vocabularies.

**Risk:** Low — it's the well-trodden Cuisine/Tool vocab pattern (entity +
`manage_*.py` + a `VocabListEditor` card) plus the seed migration and the
name-validation-not-FK twist. Sharpest edges: making every slot read-site
reactive to the store, and preserving off-vocab labels on delete.

**Engineering close-gate:** R-001 (reuse `VocabListEditor`, no new page),
R-003 (one household vocab, server-owned; the client never re-defines the
list or its validation), R-005/R-006 (portable, reversible, **seeding**
migration), R-010 (slot name validated at write; off-vocab preserved),
R-007 (one editor card, no redesign), R-011 (mirror the existing vocab idiom).

*Acceptance:* an admin edits the meal-slot list in Recipe Vocab settings
(add / rename / reorder / delete, Dessert present); the planner edit dialog +
recipe `time_of_day` pickers show the household list; deleting a slot leaves
existing entries' labels intact (they move to "Other"); a fresh install is
seeded with the five defaults; a new write with an off-vocab slot is rejected.

---

### C-2.B — Page chrome cleanup (removals + entry-chip relayout)
**Closes:** §3.6 + §3.7 + F3 + F4 + F36 + F40 + F45 + F27 (partial) + F41
(partial).

Removals + a self-contained chip relayout. Scoped to changes that **don't**
depend on the carousel (C-2.C) or the calendar widget (C-2.D) so it ships in
isolation.

- **Remove now (no replacement dependency):**
  - **"Suggest meals I can cook now" CTA + modal** and its `cookableRecipes`
    / `recipeCookable` computeds (`MealPlansOverview.vue:412, 512-515`) —
    cookable cues belong on Cookbook (Decision 7). Drop the `suggestOpen` ref
    and the modal template.
  - **Page-level shortfall banner** (L25-50). Keep the **per-entry warning
    icon** and add a single **sidebar summary line** ("2 to cook by Fri",
    chef-hat icon, not the warning triangle — F4). The earliest deadline word
    comes from `Shortfall.earliest_needed`.
  - **"Week of <date>" page title** (L57) — the calendar widget will be the
    title; the carousel breathes (F40, F44).
  - **CSV export** — confirm already gone (FU-168); remove any dead handler /
    import if a stub remains.
- **Swap the page icon** to the chef-hat (`ICONS.chef_hat` if present in the
  MD icon set, else `mdi-pot-mix`) — F3 / §3.7. One-line nav-registration
  change; check the route meta + `SettingsShell`/sidebar entry.
- **Entry-chip relayout** (F27 / F41 — fixes "icons/text overflow card"):
  two horizontal regions inside the chip — left = recipe name (wraps to 2
  lines), right = a small numeric pill `×{servings}` on `--surface-elevated`
  with heavier numeric weight. **At most one status icon at a time**:
  shortfall icon *only* when in shortfall, check chip *only* when consumed,
  never both. A1 tokens only (R-002) — no raw colour.
- **Defer (replacement lands in a later chunk, don't remove yet):**
  - "Active plan" dropdown (L12-22) → removed by **C-2.D** (calendar widget
    is its replacement).
  - "Edit entries" button + the entry-editing path of `MealPlanEditDialog` →
    removed by **C-2.C** (inline servings/slot edit is its replacement).
  - "Delete plan" → "Clear week" rename + behaviour → **C-2.E** (needs
    week-scoping + the name drop).

**Risk:** Low (removals + one chip restyle). The trap is removing the "Active
plan" dropdown or the edit modal here before their replacements exist — don't.

**Engineering close-gate:** R-002 (tokens), R-007 (only remove what has no
live dependency this chunk), R-001 (extract the entry chip as a component if
the carousel will re-mount it many times — likely yes, so do it here).

*Acceptance:* no "Suggest meals" affordance; no page-top shortfall banner (a
sidebar line carries the chef-hat summary); no "Week of…" title; chef-hat
page icon; entry chips show name + `×servings` pill with no icon overflow and
never two status icons.

---

### C-2.C — Vertical carousel + named slot rows + cell-targeted tap-add
**Closes:** §3.1 (left column) + §3.2 + F8 + F9 + F16 + F20 + F21 + F22 +
F35 (fully) + F42 + F46 + F47 + F48. **Folds in C-2.K** (past-day date fix —
same tap-add/drop path).

The largest interaction chunk. Replaces the horizontal 7-day grid **and** the
entry-editing modal. Treat as its own PR.

- **Left column — recipe list (§3.1):**
  - A4 **FilterBar**: free-text search + `planned within next N weeks`
    (default 1). **No** cookable / in-stock filter (Decision 7). Tag filters
    are a stub slot that lights up when C-4 ships its tag overhaul (note,
    don't build).
  - **All recipes** virtualised (`q-virtual-scroll`), row shape identical to
    `RecipesOverview` so users don't relearn (trays come in C-2.I above this
    list).
  - **Row shape:** recipe name + a single small **`(unallocated / pool)` count
    chip** at the right edge — the *number* is the emphasised element; **no
    green-check, no cookability colour** (Decision 7). The chip reads the
    server's `unallocated_meals` (R-003 — never re-sum on the client; this is
    the FU-154 fix — route through `recipeStore`, drop the page-local refs).
  - **Inline pool stepper (FU-088 preference):** an inline `[ − N + ]` on the
    row driving `adjust-meals` / `cook`, preferred over the
    `+1 cooked / −1 cooked / log cook…` menu. Ship inline; fall back to the
    menu only if it crowds the row on narrow widths.
  - **Drag = desktop pointer only** (`@pointerdown` guarded on
    `event.pointerType === 'mouse'`); touch users get tap-to-add (F8/F9).
- **Main column — vertical week carousel (§3.2):**
  - Up-arrow **above** = previous week; down-arrow **below** = next week.
    Up/down keyboard, swipe on mobile. Quasar `slide-up`/`slide-down`
    transition, **respect `prefers-reduced-motion`** (A6/accessibility). No
    "Week of…" title (removed in C-2.B; the calendar widget in C-2.D is the
    source of truth).
  - **Slot rows per day** — each day is a vertical stack of named slot rows
    from the user's vocabulary (C-2.A). An empty slot row is its own
    tap/drop target. **The slot is auto-derived from the row tapped** — no
    slot picker on add. This is what kills the always-"Dinner" bug **by
    construction** (F35). Off-vocab historical slots render in an "Other" row
    at the bottom.
  - **Tap-add:** tap a slot row to focus it, tap a left-column recipe → entry
    added with `servings = 1` and `slot =` the row. Desktop drag does the
    same. **Same recipe → same (day, slot)** increments the existing entry's
    servings (F47); **same recipe → same day, different slot** = two entries.
  - **Inline per-entry edit** replaces the modal: per-entry menu = view recipe
    / cook now (→ C-3 passthrough) / **`Servings: ± n` inline adjuster** (F48)
    / remove. No "Edit entries" button (remove it + the modal's entry path
    here; the create-new-plan flow no longer needs the modal — §3.4 implicit
    create lands in C-2.E, so in this chunk creation still works via the
    existing path until E rewires it — keep a thin bridge, documented).
  - **Past days** render dimmed (`opacity: 0.6`), **no add/drop target**;
    consumed entries show a check chip.
  - A5 skeleton for carousel cells while a week's entries load.
- **Date correctness (F29) is its own chunk now — C-2.K** (the user wants
  household-timezone-correct dates, not a local patch). C-2.C **consumes** the
  server-provided household "today": past-day dimming + the drop guard read it
  instead of recomputing from `toISOString()`. Sequence C-2.K with/just before
  C-2.C so the carousel has a correct "today" to render against.

**Risk:** Med — biggest interaction surface; the tap-add slot-derivation +
increment-vs-new rules + drag-gating are all new. Wire the data round-trip
(add/increment/remove/servings) first, then the carousel animation, then the
filter strip. Keep entry writes going through `mealPlanStore` (FU-154).

**Engineering close-gate:** R-001 (carousel, slot-row, entry-chip, and
left-row are components), R-003 (read `unallocated_meals`; no client re-sum),
R-002 (tokens), R-007 (don't pull C-2.D/E scope in — keep the create bridge
thin), R-011 (idiomatic Quasar transitions + `q-virtual-scroll`).

*Acceptance:* vertical carousel scrolls weeks (keyboard + swipe + arrows,
reduced-motion honoured); tapping a Breakfast row then a recipe creates a
Breakfast entry (never "Dinner"); re-adding the same recipe to the same slot
increments servings; servings edit inline; drag works on mouse only; past
days are dimmed and reject drops; the Thu-8am-AEST repro no longer 400s.

---

### C-2.D — Custom calendar widget (replaces "Active plan" dropdown)
**Closes:** §3.3 (calendar) + F13 + F14 + F15 + F17 + F28.

New right-column component; **no backend impact** (reads existing plan +
shortfall data).

- ≈6 weeks at a time, vertical stack of week-rows. **Replaces** the "Active
  plan" dropdown (`MealPlansOverview.vue:12-22` — remove it here).
- **Month banner** at the top (e.g. `JUNE`), updates as the focused week's
  month changes.
- Each week-row: 7 small rounded squares (Mon-Sun). **Only the first square
  carries text** — the date as `DD`. The other six are silent rounded blocks.
- **Status underlines** (A1 tokens, R-002): empty = none; planned (≥1 entry,
  not short) = solid `--semantic-positive`; short (any entry that day in
  shortfall) = solid `--semantic-warning`; all-consumed = dotted
  `--text-muted`.
- **Focused week** = `--brand-primary` **border** (not a fill). **Today's
  square** = small accent dot (F15).
- Clicking a week-row focuses that week in the carousel (smooth-scroll, synced
  with C-2.C).
- **URL carries `?monday=YYYY-MM-DD`** so refresh resumes on the focused week
  (F28). Use the same local-date helper from C-2.C (no `toISOString()` drift).

**Risk:** Med — new component, but pure presentation over data the page
already holds. The sync between calendar focus and carousel position is the
fiddly part; make the focused-Monday a single source of truth (a ref/route
param both read).

**Engineering close-gate:** R-001 (the widget is its own component, candidate
for cookbook reuse later), R-002 (tokens for every underline/border/dot),
R-003 (status is derived from server shortfall data, not re-judged on client).

*Acceptance:* the widget shows ~6 weeks with correct status underlines; the
focused week is outlined; today has a dot; clicking a week scrolls the
carousel; reloading the page with `?monday=` restores the focused week; the
old "Active plan" dropdown is gone.

---

### C-2.E — Drop `MealPlan.name` from UI + "Week starting X" + "Clear week"
**Closes:** §3.4 + §3.5 + F10 + F11 + F37.

- **Backend:** make `MealPlan.name` **nullable** (`table_mappings.py:459-464`;
  batch-mode migration, R-005/R-006). `create_meal_plan.py` accepts a missing
  name and writes `NULL`; `get_meal_plans.py` keeps emitting the stored value
  (ignored by the new UI) for log/back-compat readability. Templates keep
  `name` (added in C-2.F) — only **instances** drop it.
- **Implicit create (§3.4):** the first tap-add on a day in an **unplanned**
  week silently `POST`s a nameless `MealPlan` for that week's Monday, then
  adds the entry. No date picker, no modal. This removes the thin "create
  bridge" left in C-2.C. **`MealPlanEditDialog` is retired entirely** (confirmed
  in review 2026-06-14 — inline edit + implicit create cover its jobs; confirm
  no other caller before deleting). A purpose-built "bulk edit the whole week"
  power-user action (which may not even need a modal) is assessed separately —
  [[FU-175]] — not rebuilt here.
- **Display:** always "Week starting `<Monday date>`" (computed); the stored
  name is never surfaced.
- **"Delete plan" → "Clear week" (F37):** clears the focused week's entries;
  if that empties a plan row that isn't part of a live recurring set window,
  delete the `MealPlan` row (reuse `DELETE /api/meal-plans/{id}` once empty,
  or a scoped clear on `PATCH` with `confirm_clear_entries`). Rename the
  button + confirm copy.

**Risk:** Low-Med. The nullable-name migration is trivial; the sharp edge is
the implicit-create race (two quick taps before the plan exists) — debounce /
await the create before the second add, and route both through the store.

**Engineering close-gate:** R-006 (nullable migration, reversible, no data
loss), R-003 (week→plan resolution is a single owned operation), R-007 (don't
physically drop the column — Anti-creep, we just stop surfacing it).

*Acceptance:* tapping into an empty week creates a plan with no name and adds
the entry; the UI shows "Week starting …" everywhere; "Clear week" empties
the focused week and removes the now-empty plan; existing named rows still
load.

---

### C-2.F — Templates (single): save + apply-one-week
**Closes:** §5 (single-template half) + §3.3 templates + F12 + F2 (partial).

First new-entity chunk. Migration + new feature folder.

- **Backend:**
  - **`MealPlanTemplate`** entity/table: `{id, name (NOT NULL), description
    (NULL)}` + **`MealPlanTemplateEntry`** `{id, template_id FK CASCADE,
    recipe_id FK, offset_from_monday (0..6), slot (String(50)), servings}`.
    Mirror the `MealPlanEntry` mapping shape (`table_mappings.py:466-475`).
    Batch-mode migration (R-005/R-006).
  - **`MealPlan.source_template_id: UUID | null`** column (provenance;
    nullable, batch migration). Set on a single-template fork.
  - New feature folder `dora_api/features/meal_plan_templates/`:
    - `POST /api/meal-plan-templates` — save the focused week as a template
      (server reads the week's entries, stores `offset_from_monday =
      scheduled_for − monday`). `slot` validated against the user's slot list
      at save-time; legacy values preserved (R-010 boundary check).
    - `GET /api/meal-plan-templates` — paginated list.
    - `PATCH /api/meal-plan-templates/{id}` — edit (name/description/entries).
      **Does NOT propagate to existing plans** (Decision 1 — forked at apply).
    - `DELETE /api/meal-plan-templates/{id}`.
    - `POST /api/meal-plans/from-template` — body `{ template_id,
      monday_of_week }`. Server forks a `MealPlan`, computes `scheduled_for =
      monday + offset`, **skips any offset whose date < today** (Decision 2),
      sets `source_template_id`. Returns the new/updated plan.
  - e2e tests: save→list→apply round-trip; apply skips past offsets;
    template edit doesn't touch an already-applied plan.
- **Frontend:**
  - Right-column **`Save this week as a template`** (visible when the focused
    week has entries) → A3 `BaseDialog` asking name (prefilled `Week of
    <date>`) + optional description.
  - **`Apply a template…`** dropdown → chooser, **One week** tab: pick a
    template; when the current week is non-empty, the warning names the count
    ("Will replace 3 future entries in this week. Continue?").
  - New `mealPlanTemplateStore` + `mealPlanTemplateApiService`; TS models.

**Risk:** Med (new entity + migration + fork logic). Keep the recurring/set
machinery out (C-2.G) so this PR stays reviewable.

**Engineering close-gate:** R-005/R-006 (portable, reversible migration),
R-010 (slot validated at save), R-003 (offset/skip-past logic is server-owned),
R-001 (template chooser + save dialog are components).

*Acceptance:* a week saves as a template; the template lists; applying forks a
plan and skips past days; editing a template leaves already-applied plans
untouched; deleting a template doesn't break plans that came from it.

---

### C-2.G — Template sets + recurring apply + provenance
**Closes:** §5 (sets/recurring half) + §11.5 + F2 (fully) + F24 + F25 (with
Decision 1) + Manage-Templates page.

- **Backend:**
  - **`MealPlanTemplateSet`** `{id, name, description (NULL)}` +
    **`MealPlanTemplateSetItem`** `{id, set_id FK CASCADE, template_id FK,
    position (0..n)}`. Batch migration.
  - **`MealPlan.source_template_set_id: UUID | null`** + **`rotation_index:
    int | null`** columns (which template in the set applied to this week).
  - `POST/GET/PATCH/DELETE /api/meal-plan-template-sets` (PATCH = reorder /
    rename).
  - `POST /api/meal-plans/from-template/recurring` — body `{ template_id` *or*
    `template_set_id, start_monday, end_monday }` (whole weeks). Server
    **per-week forks**; for a set, `position = week_index mod len(items)`
    (apply-time anchor, §11.5 default). Each forked week still **skips
    past-day offsets** (Decision 2). Range **cap = 26 weeks** (§11.1 adopted);
    validated server-side (R-010) → 400 over cap.
  - e2e: recurring single-template over N weeks; set rotation cycles modulo
    length; cap rejection.
- **Frontend:**
  - `Apply a template…` gains a **Recurring** tab: pick a single template OR a
    set → whole-week range picker (default end = +4 weeks; hard cap 26) →
    apply.
  - **Manage Templates page** at **`/meal-plans/templates`** (§11.3 adopted —
    templates live in the planner mental model): lists templates + sets,
    edit / delete / clone, reorder set items (DnD). Reached from a
    right-column `Templates…` button so it doesn't clutter the planner.

**Risk:** Med — rotation math + the manage page. The rotation anchor is
apply-time (simpler, §11.5); document it so a future "fixed calendar-year
cycle" is a known alternative, not a silent assumption.

**Engineering close-gate:** R-005/R-006, R-010 (cap + slot validation
server-side), R-003 (rotation/skip logic server-owned), R-001 (manage page +
range picker components), R-007 (no speculative per-set scheduling features).

*Acceptance:* a rotating set applied over a date range forks one plan per
week, cycling templates by position; provenance columns populate; over-cap
ranges are rejected; the manage page edits/clones/deletes templates and sets.

---

### C-2.H — Sidebar redesign (shopping summary + per-item add + choice modal)
**Closes:** §3.3 (shopping summary) + F7 + F30 + F31 + F32 + F33 +
F45 (sidebar line). **Composes C-7** (cart button + target-list choice modal
already exist — reuse).

- **One-line headline:** **`N to buy`** (counts `needToBuy.length`).
- **`N to cook by <day>`** — the moved shortfall summary, chef-hat icon
  (F4/F45), earliest `earliest_needed` as the deadline word.
- **Per-stock-item list** now shows each item's **shopping-list status**
  (already on list X / not yet — F31). Two affordances:
  - per-row **add** (F32) → reuse `AddToListButton` / the existing target-list
    choice modal (C-7); opens the choice modal only when there are multiple
    candidate lists.
  - bottom CTA **`Add to / Generate list`** (single button → choice modal,
    Decision 6 / F33): pick an existing list (default = primary) or create
    new; adds everything not already on the chosen list; **won't double-add**.
    This replaces the old standalone `generateListForWeek` CTA — keep the
    underlying `autoGenerateAsync({ sources: { meal_plan_week } })` call
    (L674-715) behind the choice modal.
- **Token unification (F7):** the sidebar `stockStatusColour`
  (`MealPlansOverview.vue:481-498`) switches from its one-off palette to the
  central `getStockLevelColour` / `colourForSequence` helper the rest of the
  app uses (A1, R-002, R-003 — one stock-level→token mapping, not two). Note
  FU-139 migration direction (prefer `colourForSequence(seq)`).
- **Hover-to-highlight (F30, desktop only):** hovering a stock-item row
  highlights the day cells whose recipes used it (`used_in_recipe_ids` is
  already on `MealPlanIngredient`). Mobile keeps the list, no hover.

**Risk:** Med (composes C-7's button/modal; touches the live generate path).
**Don't re-implement** the choice modal — wire the existing one. **FU-135**
(browser-verify the meal-plan generate-via-Axis-B 4-state matrix) is the
verification gate for this chunk — fold its checklist into acceptance.

**Engineering close-gate:** R-001/R-007 (reuse `AddToListButton` + choice
modal, don't fork them), R-002/R-003 (unify the stock-level token mapping),
R-011 (idiomatic Quasar hover/`q-list`).

*Acceptance:* sidebar shows "N to buy" + chef-hat "cook by" line; each item
shows its list status; per-item add works (choice modal on multi-list);
"Add to / Generate" adds non-duplicates to a chosen/new list; stock colours
match the rest of the app; desktop hover highlights the right day cells; the
FU-135 4-state matrix passes.

---

### C-2.I — Trays (Favourites · Haven't-had · Frequently planned) in left column
**Closes:** §3.1 trays + Decision 5 + §11.2 (3rd tray, opted in 2026-06-14) +
F18 + F19 (ripple note).

- **Left-column trays above All-recipes** (Decision 5 — keeps the page from
  going horizontally heavy), four collapsible sections top→bottom:
  Favourites · Haven't had in a while · **Frequently planned** · All recipes.
  - **Favourites** — `Recipe.is_favourite`, pinned.
  - **Haven't had in a while** — `last_made_on IS NULL OR < today − 21d`,
    oldest-first, **cap 10**.
  - **Frequently planned** (the 3rd tray, per user) — recipes ranked by how
    often they appear across meal plans (count of `MealPlanEntry` rows
    referencing the recipe), most-frequent first, **cap 10**. The household's
    go-to meals. (All-time count to start; a trailing-window variant is a
    cheap later tweak — note, don't build.)
- **R-003 — both the 21-day window AND the frequency ranking are domain
  logic; neither may live in two languages.** Define them **server-side** —
  derived flags/buckets on the recipe list DTO, or `?tray=stale|frequent`
  query params on `get_recipes.py`. The client only renders + sorts.
- Same row shape + DnD/tap behaviour as the All-recipes list (C-2.C). The tray
  component is parameterised (metric in, rows out) so **C-4 can reuse it on the
  cookbook** with a different metric (F19 ripple — the cookbook plan owns that
  reuse).

**Risk:** Low — composition over C-2.C's row + two small server-side buckets.
The only real calls are keeping both windows server-owned and the frequency
metric definition.

**Engineering close-gate:** R-003 (window + ranking server-side), R-001 (one
parameterised tray component, now feeding 3 trays), R-007 (the three agreed
trays; no speculative 4th).

*Acceptance:* the three trays render above All-recipes, collapsible; the stale
+ frequency buckets use server-defined logic; rows behave like All-recipes
rows; the tray component is reusable (no planner-only assumptions).

---

### C-2.J — Sequential builder (alt path for fresh-cookers)
**Closes:** §6 + F1 + F26 (fresh persona).

Three-step A3-modal from a small `Plan step-by-step` CTA in the page header.
Modal-only; doesn't replace the canvas; **cancel = no writes** (nothing
commits before step 3).

1. **Pick meals** — recipe list (same shape as the left column) with a
   selection counter (default target = user's `meals_per_week` if set, else 7).
2. **Required stock** — derived (recipe → ingredients) in-stock vs need-to-buy,
   item-by-item; user can deselect recipes here without going back a step.
   Reads `get_meal_plan_ingredients`-style aggregation (may need a
   preview/ad-hoc variant that takes a recipe+servings set rather than a saved
   plan — add a small `POST /api/meal-plans/preview-ingredients` if the
   existing endpoint can't serve unsaved selections; keep the scaling math
   identical, F34).
3. **Build & finish** — one click writes the plan entries **and** generates a
   new list or adds-to-existing (the **same choice modal as C-2.H**, reuse).
   Last screen offers **print** (`useMealPlanExport.openPrintView`) + **email**.
   The Email button follows **R-014 (reveal-and-disable)**: when SMTP is
   unconfigured for the install (INV-4 detection — surface it via a capability
   flag), the button is **shown but disabled** with a "Set up emailing in
   Settings" hint, **not hidden**. Print is always available.

**Backend:** add `POST /api/meal-plans/preview-ingredients` (confirmed in
review) — takes the unsaved `{recipe_id, servings}[]` set and returns the same
aggregation as `GET /{id}/ingredients`, so step 2 needs no throwaway plan. The
scaling math stays **one shared server function** (R-003) used by both the
saved-plan and preview paths.

**Risk:** Low-Med — one new (thin) endpoint; everything else composes existing
pieces. Keep the preview math identical to the saved-plan path.

**Engineering close-gate:** R-003 (ingredient/scaling math server-owned, one
function shared by preview + saved paths), R-001 (each step is a component;
reuse the choice modal + recipe row), R-014 (Email shown-disabled when SMTP
unset), R-007 (no new persistence beyond ordinary entries).

*Acceptance:* the builder picks meals → shows buy-vs-have → builds the plan +
list in one finish; cancelling writes nothing; email + print work from the
last screen; the buy-vs-have math matches the canvas sidebar.

---

### C-2.K — Date-boundary correctness (household timezone) + past-day drop fix
**Closes:** §13 C-2.K + F29.

The reported bug (Thu 8am AEST, dropped on Wed → 400) is a timezone mismatch:
the client builds "today" with `toISOString()` (UTC) while the backend uses
server-local `date.today()`. The requirement (review 2026-06-14) is stronger
than a local patch — date boundaries must be correct **for the household,
anywhere in the world, independent of where the server is hosted.**

- **Mechanism (server-owned, household-tz):**
  - Add **`AppSetting.timezone`** (IANA string, e.g. `Australia/Sydney`),
    household-wide. Default sensibly (offer to set it from the browser's
    detected IANA tz on first run / in System settings; fall back to server tz
    or UTC). Batch migration (R-005/R-006), R-010-validated IANA value.
  - The server evaluates the "today" boundary **in the household timezone**,
    not server-local: the meal-plan past-day refusal (`create_meal_plan.py` /
    `update_meal_plan.py`) and the reconcile hook
    (`reconcile_consumed_meals.py`) test "is this in the past?" against
    `now(household_tz).date()`.
  - Expose the household "today" on the meal-plans response so the **client
    trusts the server's date** rather than recomputing it — past-day dimming,
    the calendar "today" dot, and the drop guard all read it (R-003 — one owner
    of "what day is it for this household").
- **Scope:** this chunk lands the mechanism **for the meal-plan surface only**.
  Applying the same household-tz date logic everywhere else dates matter
  (alerts, shortfall deadlines, dashboard, every other `date.today()`) is a
  **large app-wide sweep** — [[FU-174]] — and the place to promote this into an
  ADR/R-rule once the mechanism is proven here. (R-007: the timezone setting is
  the minimum needed to do *this* fix correctly; the sweep is flagged, not done
  inline.)

**Risk:** Med — introduces a timezone setting + shifts the date-boundary source
of truth. Keep it scoped to the meal-plan paths; the sweep is separate.

**Engineering close-gate:** R-003 (one server-owned household "today"; client
reads it), R-005/R-006 (portable, reversible migration), R-010 (IANA tz
validated at the boundary), R-007 (mechanism only; sweep flagged).

*Acceptance:* a household in `Australia/Sydney` on a US-hosted server sees the
correct local date; the Thu-8am-AEST-dropped-on-Wed repro no longer 400s; the
calendar "today" dot + past-day dimming match the household date.

---

## 2. First reviewable chunk — definition of done

**C-2.A (meal-slot vocabulary, household-wide).**

- `MealSlot` `{id, name, sequence}` table created **and seeded** with the five
  `DEFAULT_MEAL_SLOTS` via a batch-mode, reversible migration.
- `GET/POST/PATCH/DELETE /api/meal-slots` (+ reorder) mirror the cuisine vocab
  CRUD: list ordered with usage counts, create with dup-check, rename, delete
  (no cascade — labels preserved).
- A 4th `VocabListEditor` card on `RecipeVocabSettings.vue` edits the list
  (add / rename / reorder / delete, Dessert present) — **no new settings page**.
- Slot dropdowns (planner edit dialog + recipe `time_of_day`) read the
  household list via the store.
- New writes validate the slot name against the table; off-vocab / legacy
  strings are preserved on delete (move to "Other", not nulled).
- Tests: e2e for the meal-slots CRUD round-trip + the write-time name
  validation + delete-preserves-label.
- Engineering close-gate clean: R-001 (reuse `VocabListEditor`), R-003
  (household vocab server-owned), R-005/R-006 (portable seeding migration),
  R-010 (validated), R-007 (one editor card), R-011 (mirror the vocab idiom).
- **Slot remap UI deferred** → [[FU-173]].

---

## 3. Risks & open decisions

**Risks:**
- **C-2.C is the load-bearing chunk** (carousel + slot rows + tap-add + the
  entry-edit replacement). Wire data round-trips before animation. It consumes
  the server "today" from C-2.K and retires the edit modal's entry path — keep
  a thin create-bridge until C-2.E lands implicit-create, and don't let that
  bridge leak scope.
- **Migrations:** C-2.A/E/F/G/K each add columns/tables (A seeds the `MealSlot`
  defaults; K seeds a timezone default). Every one is batch-mode (SQLite +
  Postgres parity, R-005) and reversible (R-006).
- **Compose, don't fork (C-2.H/J):** the cart button + target-list choice
  modal already exist (C-7). Re-implementing them is the most likely drift.
- **State ownership (R-003):** temptations to push back to the server — the
  `unallocated` count (already server-owned; just read it, FU-154), the 21-day
  "haven't had" window + the "frequently planned" ranking (C-2.I), and the
  meal-slot list + its name-validation (C-2.A — a **household vocab table**,
  server-owned). Don't copy any of them into the client, and don't reintroduce
  per-user scoping anywhere in the planner.
- **FU-154** (page-local collections bypassing stores) is fixed *opportunistically*
  during the C-2.C rebuild — call it out in that PR rather than leaving the
  refs in place.

**Decisions settled in review (2026-06-14):**
- **Scope** → **full build** (all 11 chunks).
- **Slot scoping** → **household-wide vocab table** (`MealSlot`), correcting
  the proposal §4 "user-scoped" wording — meal plans have no `user_id`; the
  household is the unit (C-2.A).
- **Trays** → **3** (Favourites + Haven't-had-in-21-days + Frequently-planned)
  — user opted into the 3rd tray (§11.2; C-2.I).
- **"Haven't had" window** → **21 days** (§3.1; C-2.I).
- **Recurring window cap** → **26 weeks** (§11.1). Server-validated.
- **Templates page route** → **`/meal-plans/templates`** (§11.3 — planner
  mental model).
- **Slot remap UI** → **deferred** ([[FU-173]]); Anti-creep.
- **Set rotation anchor** → **apply-time** (position 0 = first applied week),
  §11.5; the fixed calendar-year cycle is the documented alternative.

**Lower-level calls — settled in review (2026-06-14):**
- Past-day fix → **household-timezone-correct, server-owned** (C-2.K); the
  app-wide datetime sweep is [[FU-174]].
- `MealPlanEditDialog` → **retired** (C-2.E); a purpose-built bulk-week action
  is assessed separately ([[FU-175]]).
- C-2.J → **adds `POST /meal-plans/preview-ingredients`** for unsaved
  selections.
- Builder Email button → **shown-disabled** when SMTP unset (new rule
  **R-014** / ADR-009); the app-wide reveal-and-disable sweep (scanning button,
  etc.) is [[FU-176]].
- Interaction defaults confirmed: inline `[−N+]` pool stepper, drag
  desktop-only, entry chip = name + ×servings, H/I sequenced ahead of F/G.

**Verification gates carried (per CLAUDE.md MANDATORY rule):**
- **FU-032** — B6 allocation end-to-end (the `unallocated_meals` chip in the
  C-2.C left column is the surface to confirm).
- **FU-135** — meal-plan generate via the Axis-B choice modal (C-2.H 4-state
  matrix).
- **New FU (to log)** — F34 ingredient "needs x" math for multi-recipe weeks
  with mixed units/quantities (eyeball `get_meal_plan_ingredients` scaling).
- **New FU (to log)** — F29 past-day drop fix browser-verify post C-2.C/K.

**Cross-refs:** A1 tokens · A2 BaseButton · A3 BaseDialog · A4 FilterBar ·
A5 skeleton · A6 text scale · C-3 cook-mode passthrough · C-4 trays/tags reuse ·
C-7 cart button + choice modal · C-cross slot-settings home + money opt-in ·
state-ownership (allocation SSOT, landed).

---

## 4. Feedback coverage

Maps every `§MEAL PLANS` bullet (proposal §13 F1–F49) to the chunk that lands
it. A reviewer should be able to audit "is anything missing?" at a glance.

| # | Feedback | Chunk |
|---|---|---|
| F1 | Sequential builder (pick → stock → list → email/print) | C-2.J |
| F2 | Templates, rotating, auto-add tie-in | C-2.F (single) + C-2.G (sets/recurring) + C-2.H (auto-add) |
| F3 | Page icon (chef-hat, not calendar) | C-2.B |
| F4 | Shortfall = chef's hat, not warning triangle | C-2.B (sidebar line) + C-2.H |
| F5 | Allocation broken | Already works (server SSOT) — **FU-032** browser-confirm |
| F6 | "I'm a notification!" placeholder | B7 — already fixed (out of scope) |
| F7 | Ingredient demand colour consistency | C-2.H (token unification) |
| F8 | Drag/drop disabled on mobile | C-2.C |
| F9 | Tap/click anywhere drag/drop exists | C-2.C |
| F10 | Plan instance name useless | C-2.E (dropped) |
| F11 | Date picker for new plan wrong | C-2.E (implicit create) |
| F12 | Template management (save/create-from/toolbar) | C-2.F + C-2.G (manage page) |
| F13 | Calendar widget design | C-2.D |
| F14 | Widget above shopping info | C-2.D + C-2.H layout |
| F15 | Current day marked | C-2.D (accent dot) |
| F16 | Vertical carousel (up/down + animation) | C-2.C |
| F17 | Calendar changes with carousel | C-2.D (synced focus) |
| F18 | Trays Favourites + Haven't-had + drag | C-2.I |
| F19 | Reusable on cookbook (different metric) | C-2.I component / C-4 ripple |
| F20 | Main working area centring | C-2.C layout |
| F21 | All-recipes filterable, vertical, left | C-2.C |
| F22 | Add without drag | C-2.C (tap-add) |
| F23 | Dora assistant "Italian week" etc. | Out of scope — SLM assistant work (proposal §9) |
| F24 | Recurring; history not stuffed; past = read-only | C-2.G + backend rules (Decision 1) |
| F25 | Recurring × editing coexistence | Decision 1 (fork at apply) — C-2.F/G |
| F26 | Batch vs fresh personas | C-2.C (batch) + C-2.J (fresh) |
| F27 | Meal cards don't fit | C-2.B (entry-chip relayout) |
| F28 | Refresh resumes on focused week | C-2.D (`?monday=` URL) |
| F29 | Past-day drop 400 bug | C-2.K (folded into C-2.C) |
| F30 | Hover stock item → highlight day cells | C-2.H |
| F31 | Shopping-list status per stock item | C-2.H |
| F32 | Individual add | C-2.H |
| F33 | "Generate" → add-to/existing-or-new | C-2.H (choice modal, Decision 6) |
| F34 | "Needs x" math correctness | **New FU** (verification) — math in `get_meal_plan_ingredients` |
| F35 | Slot always "Dinner" bug | C-2.A (vocab) + C-2.C (auto-derives from row) |
| F36 | "Edit entries" button shows gap | C-2.C (inline edit replaces modal) |
| F37 | "Delete plan" → "Clear week" | C-2.E |
| F38 | Theme-aware page elements | All chunks (A1 tokens, R-002) |
| F39 | Remove CSV button | Already removed (FU-168) — C-2.B confirms no stub |
| F40 | Remove "Week of…" title | C-2.B |
| F41 | Colour/icon overload | C-2.B (chip) + C-2.H (token unification) |
| F42 | On-hand display in palette better | C-2.C (row count chip + inline stepper) |
| F43 | Drop "cookable now" cues / "Suggest meals" CTA | C-2.B (Decision 7) |
| F44 | Squishing horizontally | Decisions 5 + 7 (light right column, trays left) — C-2.C/H/I |
| F45 | Shortfall banner redundant | C-2.B (removed) + C-2.H (sidebar line) |
| F46 | Time of day as rows | C-2.C (slot rows) |
| F47 | Same recipe same slot → increment | C-2.C |
| F48 | Don't drag one by one | C-2.C (per-entry Servings ±n) |
| F49 | Slots configurable + defaults | C-2.A |

Out-of-scope-here (with reason): **F6** (fixed in B7); **F23** (Dora plan
synthesis — SLM assistant work, proposal §9). Everything else lands in a chunk
above. After this plan is approved, flip the relevant `§MEAL PLANS` rows in
`docs/02_feedback/COVERAGE_GAPS.md` from gap → covered.

---

## 5. Suggested run order

Re-sequenced from the proposal's conceptual A→K by dependency + risk:

1. **C-2.A — slot vocabulary.** Data foundation for the slot rows; independently
   fixes the Dessert/always-Dinner vocab gap. Lowest risk. **First PR.**
2. **C-2.B — page chrome cleanup.** Pure removals + chip relayout; no deps.
3. **C-2.K — household-timezone date correctness.** `AppSetting.timezone` +
   server-owned "today"; lands before/with C so the carousel renders against a
   correct date. (Mechanism only; app-wide sweep is FU-174.)
4. **C-2.C — carousel + slot rows + tap-add.** The load-bearing interaction
   chunk; depends on A (vocab), B (chip), K (server "today"). Fixes FU-154 in
   passing.
5. **C-2.D — calendar widget.** Depends on C (focused-week sync); removes the
   "Active plan" dropdown.
6. **C-2.E — drop name + implicit create + "Clear week".** Depends on C/D
   (week-scoping + retires the edit modal).
7. **C-2.H — sidebar redesign.** Composes C-7; can interleave after C (carousel
   cells exist for hover-highlight). Carries FU-135.
8. **C-2.I — trays.** Composition over C's left-column row + a server bucket.
9. **C-2.F — templates (single).** First template entity/migration; independent
   of the calendar internals — can start in parallel with the C→E line once A
   lands.
10. **C-2.G — template sets + recurring + manage page.** Depends on F.
11. **C-2.J — sequential builder.** Composes C's recipe row + H's choice modal;
    last because it reuses the most.

**Parallel-safe picks** (if a second agent helps): **C-2.A** (self-contained
data + settings) and **C-2.F** (new isolated entity/feature folder) are the
two with the least overlap with the C→E interaction line.
