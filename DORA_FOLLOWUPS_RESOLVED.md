# Dora Follow-ups Ledger — Resolved

Archive of `[RESOLVED]` items moved out of `DORA_FOLLOWUPS.md`. Kept for the
audit trail — never delete entries here.

When you resolve an open item, move its block from `DORA_FOLLOWUPS.md` to this
file, flip the heading from `[OPEN]` to `[RESOLVED]`, and append a one-line
state note describing how it was resolved (date + brief mechanism). New
resolutions go at the **top**.

---

## [RESOLVED] FU-298 — Dashboard "Cookable tonight" upgrade (L272: meal-plan-driven + ready/missing)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up — was slated as a Phase-5 item.
- **Resolution (2026-06-29):** rebuilt the card per L272.
  **Backend** (`dora_api/features/dashboard/get_dashboard_summary.py`):
  extended `UpcomingMealPlanEntry` with `recipe_id: UUID` (for
  deep-linking) and `missing_count: Optional[int]` (`None` for empty
  recipes, `0` = ready, `>0` = N missing). The handler reuses the
  same `load_recipe_cookability()` map already computed for the
  recipe summary — one query, both consumers (R-003: cookability
  rule in one place; R-007: no extra DB round-trips).
  **Frontend** (`web_app/src/pages/DashboardPage.vue`): replaced the
  client-side `cookableTonight` computed (which filtered every
  cached recipe by `recipe.cookable`) with a `nextToCook` computed
  driven off `summary.meal_plan.upcoming_entries` — deduped by
  `recipe_id` (same recipe planned twice in a week shows once,
  earliest), capped at 3. Each row now renders the relative day +
  slot (e.g. "Tomorrow dinner · serves 4") and a coloured
  `q-badge`: green "Ready", amber "Missing 2", grey "No
  ingredients". Empty state changed to "Nothing planned for the
  next week" with a `/meal-plans` deep link. Card label retitled
  "Next to cook" (clearer about what it shows; the old title
  implied stock-driven). Dropped the no-longer-used `Recipe` type
  import and the `recipes` storeToRefs destructure. New CSS:
  `.dora-cook-row--with-badge` modifier (a 4th `auto` column for
  the badge); restock card unchanged. `vue-tsc` + `eslint` clean.
  **Tests:** the DTO change is additive (existing tests
  assert nothing about `recipe_id` / `missing_count`); full pytest
  suite still 535/540 (the 4 FU-328 pre-existing failures + one
  flake under suite ordering).

## [RESOLVED] FU-297 — Budget card isn't money-gated (consistency with the Money zone)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 4).
- **Type:** finding (consistency, pre-existing).
- **Resolution (2026-06-29):** added `gate: 'money'` to the budget
  CardDef in `DashboardPage.vue`'s `CARD_DEFS` array, matching
  savings / spend / pantry-value. Budget surfaces are *all*
  dollar-denominated — even the "no target set" body reads "$X.YZ
  spent so far. Set a target" — so the Money-zone gate posture
  applies (ADR-005). Also short-circuited `loadBudget()` on
  `!moneyEnabled.value` (mirrors `loadSavings` / `loadSpendByStore`
  / `loadPantryValue`) so we don't fetch `/api/budget/status` when
  the card can't render. Inline comment in `CARD_DEFS` records the
  reasoning so a future reader doesn't reverse the call without
  reading the FU. No standalone ADR opened — the call is a
  routine application of ADR-005's "dollar surfaces gate on money"
  policy, recorded in code + ledger. `vue-tsc` + `eslint` clean.

## [RESOLVED] FU-294 — Dashboard card reorder: drag-handles (literal DnD) not built
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 2).
- **Type:** follow-up (enhancement).
- **Resolution (2026-06-29):** wired `useDragDropList<CardId>` (the
  shared composable from FU-326 / R-022) into the Cards menu rows.
  - **Mime:** `application/x-dora-dashboard-card` (each list owns
    its mime per the composable contract — drags from this list
    can't land in any other DnD surface).
  - **Drag gate:** `canDragStart: () => !$q.platform.is.mobile`
    so the handle column hides on touch (C13's tap-mandatory
    mobile path stays uncluttered; drag is the desktop power-user
    extra).
  - **Drop constraint:** `canDropOn` rejects cross-zone drops, so
    a card never visually leaves its zone (matches the existing
    tap `canMove` semantics).
  - **Drop effect:** splice-out / splice-in at the target's
    current index, then `persistLayout()` (same persistence path
    the tap reorder uses, so a drag and a tap reorder are
    indistinguishable on the wire).
  - Handle is a `q-item-section avatar` carrying `dora-dnd-handle`
    + the composable's `handleProps`; the `q-item` itself carries
    `dora-dnd-row` + `rowProps` (handle mode per the composable's
    two surface shapes). The existing tap up/down + visibility
    toggle controls stay in place — the drag is purely additive.
  `vue-tsc` + `eslint` clean. **Browser verify still owed**: the
  composable was previously verified across three other DnD
  surfaces (R-022 verify); this one needs a desktop click-through
  to confirm grab → drop reorders within zone, drop-target ring
  lights, cross-zone drop is rejected, and saved order survives
  reload. Logged in `DORA_VERIFY.md`.

## [RESOLVED] FU-289 — `useSpeechOutput.available` ignores Piper when browser has no SpeechSynthesis
- **Raised:** 2026-06-23 (Piper TTS wiring).
- **Type:** finding (minor edge).
- **Resolution (2026-06-29):** added a session-cached
  `probePiperConfigured()` at module scope in
  `web_app/src/composables/useSpeechOutput.ts` that resolves the
  `configured` flag from `GET /api/tts/voices` (one request shared
  across composable instances; cached for the session because
  Piper-configured is install-time server state, not per-request).
  The composable now only fires the probe when
  `'speechSynthesis' in window` is false — the synchronous browser-
  available answer stays the default, so the common case pays nothing
  extra. When the probe resolves true on a SpeechSynthesis-less
  browser, `available.value` flips to true, so the Settings → Voice
  toggle and the chat mute button (`voiceOutputAvailable` in
  `DoraChat.vue`, `VoiceSettings.vue`) appear. Failures (no Piper
  configured, endpoint absent, network error) keep `available`
  unchanged. `npx vue-tsc --noEmit` + `npx eslint` clean.

## [RESOLVED] FU-288 — Three profile-picture e2e tests fail (pre-existing; FU-286 "no Python env" premise is stale)
- **Raised:** 2026-06-23 (found while running the suite for the TTS
  work).
- **Type:** finding.
- **Resolution (2026-06-29):** ran the three named tests directly —
  all **pass**. Confirmed via `git stash` that they pass on clean
  HEAD too, so they were fixed at some point between the FU being
  raised (2026-06-23) and now (likely in one of the recent
  follow-up commits). No code change required for the three named
  tests. **However, a fresh full-suite run on this box turned up
  a *different* set of 4 pre-existing failures** (data_router /
  household_tz_boundaries / product_router / recipe_is_planned) —
  logged as a new finding in `DORA_FOLLOWUPS.md` (FU-328). The
  FU-286 "no Python env" premise remains stale: 540 tests collected,
  4 fail, 536 pass on this machine.

## [RESOLVED] FU-285 — `VocabListEditor` empty-state copy is recipe-specific
- **Raised:** 2026-06-23 (Settings rebuild Phase 3).
- **Type:** leftover (cosmetic copy mismatch).
- **Resolution (2026-06-29):** added an optional `emptyAction` prop to
  `web_app/src/components/settings/VocabListEditor.vue` (defaults to
  the existing `Create one to start tagging recipes.` so the four
  recipe-shaped Recipe* pages are unaffected). Threaded the prop
  through `TaxonomyManagerPage.vue` with a `computed`-driven
  `v-bind` that only forwards when the caller actually set it, so
  `exactOptionalPropertyTypes`'s strict-undefined rule is honoured
  and `withDefaults` keeps owning the fallback. `RecipeMealSlotsSettings.vue`
  now overrides with `empty-action="Create one to schedule meals against."`
  — the wording avoids "tagging" (slots aren't tags) and reads
  naturally for an empty slots page on a brand-new install.
  `vue-tsc` + `eslint` clean.

## [RESOLVED] FU-221 — Migrate remaining unconditional `getXAsync()` onMounted calls to `ensureLoadedAsync()`
- **Raised:** 2026-06-18 (R-016 introduction).
- **Type:** follow-up (R-016 sweep).
- **Resolution (2026-06-29):** swept the five pages flagged in the FU
  for stores that already expose the `ensureLoadedAsync()` helper
  (`stockItemStore`, `stockLevelStore`, `storesStore`, `productStore` —
  per `docs/01_charter/ENGINEERING_STANDARDS.md` R-016 / ADR-011):
  - `web_app/src/pages/RecipeDetailPage.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` →
    `stockItemStore.ensureLoadedAsync()`;
    `stockLevelStore.getStockLevelsAsync()` →
    `stockLevelStore.ensureLoadedAsync()`.
  - `web_app/src/pages/RecipesOverview.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/StockItemDetailPage.vue` `onMounted` —
    `stockLevelStore.getStockLevelsAsync()` +
    `stockItemStore.getStockItemsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/StockOverview.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` +
    `stockLevelStore.getStockLevelsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/MealPlansOverview.vue` — file has since shrunk
    to 507 lines and its current `onMounted` no longer fetches stores
    (only does the A/B planner-view redirect); nothing to migrate.
  Calls into stores that do **not** yet expose the helper
  (`recipeStore.getRecipesAsync`, `recipeStore.getRecipeCollectionsAsync`,
  `shoppingListStore.refreshAsync`, `locationStore.refreshAsync`,
  `recipeVocabStore.getAllAsync`, `mealSlotStore.getMealSlotsAsync`,
  page-local `stockGroupApi.getAllAsync`) were **left alone** per R-007
  scope discipline + the FU's own "once they grow the helper" carve-out
  — extending more stores is a separate sweep.
  `npx vue-tsc --noEmit` clean; `npx eslint` on the four touched pages
  clean.

## [RESOLVED] FU-216 — Rebase cost consumers onto `get_stock_item_unit_cost_at` (FU-213 follow-on)
- **Raised:** 2026-06-17 (FU-213 split).
- **Type:** deferred job (build).
- **Resolution (2026-06-29):** browser-verified the additive
  observation fallback that landed 2026-06-17 (stock-value report's
  `StockValueOverTimeHandler` per-bucket loop and `get_recipes.py`
  `_compute_estimated_cost` per-ingredient — each previously fell
  through to nothing when no linked-product price existed; now picks
  up the latest observation via `get_stock_item_unit_cost_at`).
  Phase A env-verify (2026-06-17) was already GREEN: full suite
  381/381 incl. all report + recipe-cost tests; no fixture pinned old
  totals broke (the fallback only contributes for observation-only
  items, which the fixtures don't trigger). User confirmed live
  numbers on the stock-value report and the recipe cost-estimate card
  read sensibly. Full product-cost unification into the helper is no
  longer required for the user goal — the additive fallback is the
  resolution.

## [RESOLVED] FU-215 — PreferredBuy shopping-list hint (the FU-211 sub-part)
- **Raised:** 2026-06-17 (FU-211 split).
- **Type:** deferred job (build).
- **Resolution (2026-06-29):** browser-verified the per-line hint
  flow that landed 2026-06-17. Stack:
  `ShoppingListLine.preferred_buy_id` (plain UUID, **no FK** per the
  FU-178 batch-mode lesson — dangling ids after a PreferredBuy delete
  are tolerated and just render no hint) + migration `c4e6a8b1d3f5`;
  `preferred_buy_id` + `clear_preferred_buy` on the generic line PATCH;
  the detail serializer bulk-loads each item's PreferredBuy labels onto
  the line DTO; per-line hint dropdown in `ShoppingListDetail.vue`
  (pick/clear, optimistic + rollback). Phase A env-verify (2026-06-17)
  was already GREEN: `tests/e2e/dora_api/test_shopping_line_preferred_buy.py`
  2/2 (set + clear + DTO labels), migration applies clean on the FU-209
  head, `vue-tsc` + `eslint` clean. User confirmed live that picking a
  hint persists across reload and clearing it removes the hint text.

## [RESOLVED] FU-207 — Document VAPID key generation in install docs
- **Raised:** 2026-06-17 (C-9.8 impl).
- **Type:** documentation.
- **Resolution (2026-06-29):** added a "Push notifications (optional,
  VAPID keys)" subsection under § Local dev quick reference in
  `README.md`, clustered with the existing optional-BYO sections. Covers:
  why VAPID is needed (RFC 8292 short note), the
  `python -m py_vapid --gen --applicationServerKey` command, the three
  `DORA_VAPID_*` env vars, the dry-run / disabled-Push-toggle behaviour
  when any is missing (per R-014). The inline docstring in
  `push_sender.py` stays — it's the source of truth the README
  paraphrases.

## [RESOLVED] FU-204 — `UpdateMeCommand` TS type missing `household_headcount` (drift audit)
- **Raised:** 2026-06-17 (C-9.7).
- **Type:** finding / cleanup.
- **Resolution (2026-06-29):** ran the audit. Mapped every Pydantic
  field on `UpdateMeRequest`
  (`dora_api/features/auth/update_me.py:28`) to the matching key on
  `UpdateMeCommand`
  (`web_app/src/services/api/authApiService.ts:26`). Only
  `household_headcount` was missing — the C-9.7 alerts-email triplet
  had landed correctly across all three layers, and no other drift
  surfaced. Added `household_headcount?: number | null` to
  `UpdateMeCommand` with the C-5.4 doc comment.
  `npx vue-tsc --noEmit` passes clean.

## [RESOLVED] FU-203 — `PATCH stock_location_id: null` clear path + regression test
- **Raised:** 2026-06-16 (C-1b.1 backend pass).
- **Type:** finding (bug, likely).
- **Resolution (2026-06-29):** the FK-set fix already shipped at
  `update_stock_item.py:128-139` (both `clear_stock_location` and the
  bare-null branch set `_stock_location_id` directly, mirroring the
  C-1b.1 stock_group shape that motivated the FU). Added the missing
  e2e regression test
  `test__get_stock_item_detail__stock_location_roundtrips_via_patch` in
  `tests/e2e/dora_api/test_stock_item_router.py` (mirrors the existing
  stock_group test): create with location → assert it round-trips on
  detail → PATCH `stock_location_id: null` → assert detail reads null.
  Test passes in 2.07s.

## [RESOLVED] FU-326 — Extract a shared `useDragDropList` composable + affordance stylesheet
- **Raised:** 2026-06-29 (immediately on FU-118 close — three DnD
  surfaces with hand-rolled state had crossed the rule-of-three line).
- **Type:** finding / R-001 evolution.
- **Resolution (2026-06-29):** done same day.
  - **New `web_app/src/composables/useDragDropList.ts`** owns the
    state machine (`draggingId`, `dragOverId` + private `sourceItem`
    lookup so drop can resolve the source even if the array index
    moved between dragstart and drop), the `dragstart` / `dragover` /
    `dragleave` / `drop` listeners, and per-row binding objects.
    Options: `mime` (unique MIME per logical list — convention
    `application/x-dora-<thing>`), `getId(item)` (stable per-row id;
    return null to mark a row non-draggable), `onDrop(source, target)`
    (per-list effect), and optional `canDragStart(item)` (per-row /
    global drag gate, reactively reflected in `draggable=`) and
    `canDropOn(source, target)` (per-pair drop-target predicate;
    defaults to "not the same row"). Returns `bind(item)` → `{
    handleProps, rowProps, rowClass, isDragging, isDropOver }`.
  - **New `web_app/src/css/dnd.scss`** owns the affordance treatment:
    `.dora-dnd-row` (outline reservation + transitions), `--dragging`
    (opacity 0.5), `--drop-over` (`--brand-primary` outline ring),
    and `.dora-dnd-handle` (grab/grabbing cursors + sunken hover).
    Wired into `quasar.config.ts` after `colours.scss` so the
    cascade picks up the theme tokens.
  - **Two row shapes supported.** *Handle mode* (recipe step rows,
    recipe ingredient rows): the small grip icon is the only
    draggable element, so the row body's inline editors stay
    clickable. *Whole-row mode* (shopping-list lines): no inline
    editors on the row, so the user can grab anywhere — spread both
    `handleProps` and `rowProps` on the same `q-item`.
  - **All three existing surfaces refactored:**
    - `RecipeStepsEditor.vue` + `RecipeStepRow.vue` — siblings-only
      preserved via `canDropOn`. Three `defineEmits` events
      (`drag-start` / `drag-end` / `drop-on-row`) gone; per-component
      DnD CSS gone. RecipeStepRow now accepts a single
      `dragBindings: DragDropRowBindings` prop and spreads it.
    - `RecipeDetailPage.vue` ingredient list — drop effect kept its
      "reinsert at target's slot AND copy `section_client_id`"
      semantics. Local drag state + handlers gone (~75 lines);
      per-row affordance CSS gone.
    - `ShoppingListDetail.vue` lines — `canDragStart` gates on the
      existing `canReorder` computed (covers list-done /
      mid-shopping / grouped / bulk-mode states), so the browser's
      drag affordance disappears when reorder isn't allowed. Drop
      effect (optimistic local reorder + API persist + reload on
      failure) preserved. ~70 lines of plumbing gone.
  - **Promoted to R-022 + ADR-018** in
    `docs/01_charter/ENGINEERING_STANDARDS.md`. The R rule names
    the violation signals (top-level `@dragstart` listener with no
    `useDragDropList` import; hand-rolled `--dragging` opacity or
    `--drop-over` outline; raw `application/x-dora-…` MIME outside
    the composable) so the next sweep can find drift in one grep.
- **What's notably absent on purpose:** keyboard-reorder support
  (Tab to handle, Space to pick up, arrows to move) — every existing
  surface omits this and it'd be an accessibility upgrade landed
  once, in the composable, the next time a11y work touches DnD.
  Multi-row drag and off-row drop zones (e.g. "drop into empty
  section") would extend the composable rather than re-roll state.

---

## [RESOLVED] FU-118 — Drag-and-drop for moving ingredients between sections
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down — paired with FU-094 steps DnD, now also resolved).
- **Type:** enhancement.
- **Resolution (2026-06-29):** mirrored the FU-094 steps DnD pattern on
  `RecipeDetailPage.vue`'s ingredient list. The drag handle (`drag_indicator`)
  is the only draggable element on the row; the whole row is the drop target.
  Drop semantics differ from steps: dropping ingredient A onto ingredient B
  *reinserts A at B's slot in the flat list AND copies B's
  `section_client_id` to A in the same gesture* — so reorder-within-section
  and move-between-sections collapse into one operation. (Steps used a
  siblings-only rule because of the parent/child step nesting; ingredients
  have no nesting, only the section dimension, so cross-section IS the
  goal.) Empty sections still rely on the per-row Section picker — you
  can't drop onto something that doesn't exist. Drag affordances reuse
  the same CSS shapes as `RecipeStepRow` (grab/grabbing cursors, 0.5
  opacity on the source, `--brand-primary` outline ring on the active
  drop target). The "would-be-cookable" dim history is unrelated — it
  was FU-109 (also closed today). No server changes required.
- **Duplicate-ingredient assessment** (the user asked for this alongside
  the FU close): **same stock item across different sections is a real
  use case and should remain allowed.** Common cookbook patterns —
  "olive oil" in Sauce + Garnish with different quantities/notes, "flour"
  in Cake + Frosting + Dusting — only render correctly as separate rows.
  The data model already supports this freely (no `UniqueConstraint` on
  `(recipe_id, stock_item_id)` or `(recipe_id, section_id, stock_item_id)`
  in `persistence/table_mappings.py:607-622`; create + update handlers
  accept duplicates without dedup). Downstream consumers that *want* a
  unique view already dedup on `stock_item_id`: cookability calc
  (`RecipeCard.vue:173` Set), shopping-list picker
  (`RecipeIngredientPickerDialog.vue:187-194` `Map<stock_item_id>`,
  collapsing optional/required across occurrences correctly), the
  ingredient-filter set added in the FU-109 close-out, and
  `RecipesOverview.vue:800`. Same-section duplicates are a different
  question — they're almost always a data-entry mistake ("3 tbsp oil,
  divided" is the standard cookbook idiom, not two rows). But the cost
  of *enforcing* uniqueness (UX friction; one-off legit splits like
  "1 tbsp to fry / 1 tbsp to drizzle"; legacy data) outweighs the
  benefit (the user can see two identical rows on the page and merge
  them themselves). **Decision: don't enforce uniqueness at any level.**
  Status quo wins. If the user later finds same-section duplicates
  genuinely confusing, the cheapest reversible step would be an inline
  "Duplicate of row N" caption on the matching row — pure client-side
  hint, no schema change — but it's not worth doing pre-emptively.

---

## [RESOLVED] FU-109 — Decide whether to re-add the RecipeCard "would-be-cookable" dim
- **Raised:** 2026-06-10 (FU-083 follow-up; user wanted a real decision later).
- **Type:** open product / UX decision.
- **Resolution (2026-06-29):** user picked **option 1 — keep the dim
  removed everywhere.** The "Missing N ingredients" copy on the card face
  is the single signal for "this isn't cookable yet"; no legend, no
  opacity. The now-unused `highlightStockItemIds` prop on `RecipeCard.vue`
  was dropped (along with its only binding on `StockItemDetailPage.vue`'s
  Recipes-using-this tab). Same turn the user asked for a new affordance
  on those cards — a filter icon that jumps back to Stock Overview
  pre-filtered to the recipe's ingredient set (deep-link
  `/stock?recipe=<id>` → chip "Ingredients of: <recipe>"); that piece
  ships in the same commit, not as a follow-up.

---

## [RESOLVED] FU-174 — App-wide datetime / timezone correctness sweep (household tz)
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS C-2.K review).
- **Type:** deferred job (large).
- **Resolution (2026-06-29):** swept every `date.today()` in feature
  code to `household_today(repository)`. 15 server sites + 1 naive
  `datetime.now()` migrated; 2 schema columns realigned; one Alembic
  migration written. The household-tz rule promoted to **R-021**
  + **ADR-016** in `docs/01_charter/ENGINEERING_STANDARDS.md`
  (the FU's explicit ask: "Promote the household-tz date rule into
  an ADR + a new R-0NN").
- **Server sweeps** (each handler now anchors `today` on the
  configured household timezone — F29-class bugs closed):
  - `features/alerts/get_alerts.py` — expiry math + stocktake +
    forward-looking nudges all share one household-tz `today`.
  - `features/dashboard/get_dashboard_summary.py` — the "next 7
    days" meal-plan window.
  - `features/assistant/tools.py` — 9 sites:
    `search_stock` (expiring filter), `whats_expiring`,
    `pantry_health`, `meal_plan_for_date`, `where_is_this`
    (urgency), `_resolve_month` (fallback), `purchase_price_stats`
    (days-since-last-purchase).
  - `features/waste/waste.py` — rescue horizon.
  - `features/budget/budget.py` — period bounds (status + history).
  - `features/locations/attention.py` — `reasons_for_item` /
    `reasons_for_items` now require `today: date` (no default
    fallback). Callers `features/locations/get_location_tree.py`
    and `features/stock_items/get_stock_item_detail.py` updated
    to pass `household_today(self.repository)`.
  - `features/recipes/get_recipes.py` — at-risk-ingredient horizon.
  - `features/suggestions/generators.py` — use-soon + likely-due
    horizons (2 sites).
  - `features/alerts/act_on_alert.py` — "extend expiry by 7" base.
  - `features/assistant/confirm_actions.py` — push-expiry fallback
    base.
  - `features/stock_items/update_stock_item.py` — `opened_on`
    auto-stamp.
  - `features/stock_items/create_stock_item.py` — `opened_on`
    auto-stamp + a naive `datetime.now()` for
    `stock_level_last_updated` flipped to `datetime.now(UTC)`.
  - `features/data/export_shared.py` — `export_filename`
    timestamp now follows the household calendar day.
  - `features/recipes/cook_recipe.py` — `last_made_on` write
    follows the household calendar (paired with the schema
    change below).
- **Documented carve-out:**
  `domain/entities/shopping_list.py:format_list_date` keeps its
  server-local fallback (called from `ShoppingList.display_name`,
  a `@property` with no repository access). Pure display formatter,
  only affects whether a year is appended in the rendered label.
  Worst case: a once-a-year, hours-long boundary edge case. Comment
  names the carve-out and the rule.
- **Schema cleanup** (migration `d2f7a9c4b1e8`):
  - `Recipe.last_made_on`: `DateTime(timezone=True)` → `Date`.
    Always semantically a calendar day; the time portion was
    meaningless. Entity / DTO / call-site types lifted to `date`;
    `cook_recipe.py` now writes `household_today(...)` not
    `datetime.now(UTC)`; `get_recipes._stale()` drops the
    obsolete `.date()` cast.
  - `User.onboarding_completed_at`: `DateTime` →
    `DateTime(timezone=True)`. Aligns with every other wall-clock
    column. Stored values were already naive UTC; the flag makes
    the schema match reality.
  - Migration is also the **merge** for the two then-open heads
    (`b7e2d9a4c1f5` + `c4a8e2b9d7f5`, both 2026-06-28).
- **Client annotation:** `localTodayIso()` in
  `web_app/src/helpers/weekDates.ts` and its use in
  `useMealPlanner.ts:74` now carry inline comments naming
  R-021 — the function is a display-only pre-load fallback for
  the very first paint; the server's household `today` is
  authoritative the moment it arrives. State / persistence /
  payload code never goes through this fallback.
- **Tests:** new `tests/e2e/dora_api/test_household_tz_boundaries.py`
  (4 cases) pins the contract end-to-end — sets
  `AppSetting.timezone = Pacific/Kiritimati` (UTC+14) and asserts
  `/meal-plans/today`, the alerts handler, the dashboard summary,
  and the waste-rescue feed all evaluate boundaries against the
  household zone, not server-local. Each test brackets its zone
  change in a `try/finally` so a failure doesn't leak.
- **Standards close-gate:** clean. New **R-021 + ADR-016** promoted
  per the FU's instruction. R-001 / R-003 already covered: the
  single-source helper (`household_today`) was already in place;
  this is the rollout.
- **Verification:** `vue-tsc --noEmit` clean. Server tests not run
  (no Python in env); the new boundary tests + the existing alert
  / meal-plan-today tests pin the behaviour and will catch
  regressions on first run. Browser-verify of `last_made_on` now
  rendering as a date string (vs. datetime) in cookbook surfaces
  folds into [[FU-099-V]] / [[FU-321]] verify pass.
- **Carry-over:** none in scope. Cross-references:
  - **FU-107** (RFC 2822 → ISO 8601 wire format) — already
    delivered by ADR-007 + `DoraJSONProvider`; closing in the
    same session for tidiness (its only remaining bullet point
    was "Recipe.last_made_on (DateTime)" which this sweep also
    converts).

## [RESOLVED] FU-107 — Standardise API date serialisation on ISO 8601 (drop RFC 2822 default)
- **Raised:** 2026-06-10 (FU-083 "Planned" filter follow-up — RFC vs ISO
  parse bug).
- **Type:** finding / cross-cutting cleanup.
- **Resolution (already shipped 2026-06-12; closed for the record
  2026-06-29 during the FU-174 sweep):** delivered by **ADR-007** —
  `dora_api/app.py:DoraJSONProvider` serialises `datetime` → ISO 8601
  with offset (`Z` for naive, which the docstring explains is the
  SQLite-strip-tz workaround) and `date` → `YYYY-MM-DD`. Every
  date/datetime in every response went through the new provider; the
  RFC-aware workarounds in SPA models (`plannedRecipeIds` in
  RecipesOverview etc.) had already been dropped when the provider
  landed. The FU's residual bullet — "Recipe.last_made_on (DateTime)"
  — was independently resolved by the FU-174 sweep (the field is now
  a `Date` column, which also fixes the JS `new Date(rfc)`
  midnight-UTC drift that bullet flagged). Cross-ref ADR-007 for
  the wire-format decision; R-021 / ADR-016 for the calendar-day
  boundary rule.

## [RESOLVED] FU-323 — Convert remaining `message: describeApiError(e)` toasts to message + caption + ref
- **Raised:** 2026-06-29 (FU-099 close-out).
- **Type:** polish.
- **Resolution (2026-06-29):** the 10 stragglers identified during the
  FU-099 sweep migrated to the standard `message: '<action context>',`
  + `caption: toastCaption(e)` shape.
  - **ApiAccessSettings.vue (8 sites)** — load mappings / load stores /
    create / rename / toggle / revoke / upsert mapping / drop mapping.
    Each toast now leads with a one-line action context ("Couldn't
    create the API key.", "Couldn't toggle the API key.", …) and the
    error detail + ref-id flow through `toastCaption(e)` in the
    caption. The inline `loadError.value` banner for the source-list
    fetch also routed through `toastCaption(e)` so the banner carries
    a `ref:` suffix too.
  - **StoresSettings.vue (2 toast sites + 2 inline banner sites)** —
    save (insert/update branch decided by `editing.value`) and delete
    each get an action-specific lead message; both inline `loadError`
    banners (listAsync + ensureLoadedAsync) routed through
    `toastCaption(e)` to match.
  - Imports cleaned in both files (`describeApiError` removed,
    `toastCaption` added).
- **Standards close-gate:** clean — single source remains
  `toastCaption`, no new code shape. R-001 / R-003 already covered
  the principle; nothing new to promote.
- **Verification:** `vue-tsc --noEmit` clean. Browser-verify of the
  toasts (each shows the action message + the friendly cause + the
  ref) folds into [[FU-099-V]] — same verify pass.

## [RESOLVED] FU-099 — Raw backend / Pydantic error strings leak into user-facing toasts → design pass + fix
- **Raised:** 2026-06-09 (user, after the recipe-save Pydantic error).
- **Type:** cross-cutting UX gap + structured-error design.
- **Resolution (2026-06-29):** full design discussion + implementation
  per `docs/04_proposals/IMPL_PLAN_ERROR_HANDLING.md`. Seven decisions
  settled with the user (server-side friendly translation, inline +
  brief generic toast, ~15 Pydantic codes + fallback, 4xx
  console.warn, `{msg, code, raw}` wire shape, keep current
  network/5xx copy + ref, sweep every catch block in one PR).
- **Server changes:**
  - New `dora_api/infrastructure/error_translation.py` —
    `PYDANTIC_FRIENDLY` map (~30 codes incl. missing / extra_forbidden /
    int_parsing / string_too_short / uuid_parsing / greater_than / …)
    + `FRIENDLY_FALLBACK = "This value isn't valid."` for unknown
    codes. The single source of truth (R-003) for translating
    Pydantic prose to user copy.
  - New `ErrorEntry` dataclass in `api_response.py` —
    `{ msg, code, raw }`. Replaces the bare `str` that used to live
    inside `ProblemDetails.errors[field]`. Domain helpers
    (`bad_request`, `business_rule_violation`,
    `entity_existence_failure`) keep their plain-string signatures;
    a new `_lift_errors` helper folds each string into
    `ErrorEntry(code="domain", raw=None)` so 50+ existing call sites
    don't need per-site edits.
  - `middleware.py` — `ValidationError` handler now emits one
    `ErrorEntry` per Pydantic error carrying the friendly translation
    + the raw `err["type"]` code + the raw `err["msg"]` for dev
    inspection. Wire shape: `errors: { field: [{msg, code, raw}, …] }`.
  - Updated 45 existing assertion sites across
    `test_product_router`, `test_stock_item_router`,
    `test_stock_location_router` to the new shape, via new helpers
    `validation_err(code, raw)` / `domain_err(msg)` in
    `tests/e2e/dora_api/_error_assertions.py` (single-source — a
    future change to `PYDANTIC_FRIENDLY` only touches the table, not
    every test).
  - New `tests/e2e/dora_api/test_error_translation.py` — 6 e2e tests
    pinning the wire-shape contract: friendly msg + code + raw on
    Pydantic errors; missing / extra_forbidden codes; unknown code
    falls back to `FRIENDLY_FALLBACK`; domain BRV + entity-existence
    lift plain strings into the new shape.
- **Client changes:**
  - `apiErrorHandler.ts` — `ApiErrorEntry` type matches the server's
    wire shape. `extractFieldErrors` now handles both the new
    structured shape and (transitionally) the old string-array shape,
    extracting the friendly `msg` for inline rendering.
  - `describeApiError` — when field-keyed errors are present, returns
    the generic *"Couldn't save — check the highlighted fields."*
    instead of pasting the raw field strings into the caption. The
    field copy now belongs inline on the offending input, not in
    the toast caption.
  - New `correlationSuffix(err)` — builds `" · ref: <8-char id>"` from
    the X-Request-Id round-tripped by the server.
  - New `toastCaption(err)` — combines `describeApiError` +
    `correlationSuffix` into one drop-in for the old
    `describeApiError(err) || ''` idiom; every negative toast now
    carries the ref by default.
  - `axiosHttpClient.handleError` — `console.warn` now fires on
    *every* failed call (4xx + 5xx + network), not just 5xx. Same
    shape: `[api] METHOD path → status code (correlation-id)` with
    structured `details` blob. Pasting a toast caption's ref into a
    bug report now gives a dev one grep to find the request line.
  - New composable `useFormErrors()` (`web_app/src/composables/`) —
    one place owns the `fieldErrors` / `generalError` /
    `handleSaveError` / `reset` plumbing every form was hand-rolling.
- **Migrations:**
  - **Shape C (4 sites):** `RecipeEditDialog`, `CreateStockItemDialog`,
    `LoginPage` migrated to `useFormErrors()`. `WelcomeWizard`
    deliberately kept its direct `extractFieldErrors` call
    (custom routing of `username` → its own `displayNameError` slot,
    not a fit for the simple composable).
  - **Shape B sweep (95 substitutions across 33 files):** every
    `caption: describeApiError(err) || ''` rewritten to
    `caption: toastCaption(err)` via a one-shot Node script,
    with imports auto-updated (`describeApiError` removed where
    no longer used, `toastCaption` added). Files: AlertsPage,
    AlertsBell, ShoppingListDetail (23!), ShoppingListTemplates,
    StockItemRow, StockOverview, RecipeDetailPage, RecipesOverview,
    MyProductsPage, MealPlanTemplatesPage, MealPlanTemplatesDrawer,
    MealPlanRecipePicker, useMealPlanner, NewListDialog,
    StockGroupsSettings, StockLocationsSettings, UsersAdminSettings,
    AdminSystemFeaturesSettings, PreferencesSettings,
    AdminSystemAssistantSettings, AccountSettings (+ ~12 more).
- **Standards close-gate:**
  - **R-001 (componentisation):** `useFormErrors()` lifts the
    recurring catch-block plumbing into a single composable. The
    error-translation table is its own module. The toast-caption
    builder is its own helper. No hand-rolled five-liners remain
    across the migrated surfaces.
  - **R-003 (single source):** `PYDANTIC_FRIENDLY` is the sole code
    → copy map. `correlationSuffix` is the sole ref-id format.
    `toastCaption` is the sole toast-caption builder. The
    translation table is mirrored in test assertions through the
    `validation_err` helper, not duplicated.
  - **R-007 (scope discipline):** inclusion list is the ~30 codes
    our schemas actually emit; unknown codes fall back. No
    pre-built per-field bespoke copy.
- **Verification:** `vue-tsc --noEmit` clean. No Python interpreter
  in this session's env — server-side test suite not run; the new
  e2e tests pin the contract and the existing 45 assertions were
  updated to match. Browser-verify of the full pipeline logged as
  **[[FU-099-V]]**.
- **Carry-over (deliberately not in scope):**
  - **[[FU-323]]** — 10 surviving `message: describeApiError(e)`
    toasts in `ApiAccessSettings` + `StoresSettings` (different
    shape — friendly text in `message`, no `caption`/ref). They
    work correctly post-FU-099 (friendly copy renders, console.warn
    logs the ref); migrating to message + caption + ref is polish,
    not a real defect.

## [RESOLVED] FU-098 — Unsaved-changes guard on navigation (app-wide)
- **Raised:** 2026-06-09 (user, after cook-mode batch).
- **Type:** finding / cross-cutting UX gap.
- **Resolution (2026-06-29):** exhaustive sweep for "Save button +
  locally-deferred state" surfaces. The composable
  `useUnsavedChangesGuard` already exists (shipped with FU-156 on
  2026-06-12) and was wired into the two large editor pages;
  remaining gaps were:
  - **`AccountSettings.vue`** — `usernameDraft` + `emailDraft` each
    have their own Save button + `unchanged` computed. Guard wired
    on `!usernameUnchanged || !emailUnchanged`. Profile-picture
    upload and password change are deliberately excluded (both save
    immediately on action — no draft window; and browsers expect
    typed passwords to be lost on nav for security reasons).
  - **`AdminSystemAssistantSettings.vue`** — three drafts
    (`enabledDraft` / `baseUrlDraft` / `modelDraft`) + Save button
    + `unchanged` computed. Guard wired on `!unchanged`.
- **Audited and deliberately NOT guarded (with reason):**
  - `RecipeCookMode.vue` — session state (ticks, swaps,
    cookingFor) is real-time and transient, not a save-button form.
    The "Done" button persists stock-level changes via the explicit
    finish dialog; there's no notion of "draft progress" to warn
    about. Cooking is expected to be uninterruptible — flagging
    every nav would be noise.
  - `ShoppingListDetail.vue` — every line edit (quantity, name,
    status) saves immediately via `@blur` / `@update:model-value`.
    No locally-held dirty state on the page; the two `label="Save"`
    buttons live inside `q-menu` popovers (price editor + planned-
    date editor) where state is intentionally transient.
  - Settings pages that save-on-blur or save-on-change:
    `AdminSystemAlertsSettings` (blur), `AdminSystemFeaturesSettings`
    (toggle/blur), `AdminSystemTimezoneSettings` (change),
    `MoneySettings`, `NotificationsSettings`, `PreferencesSettings`
    (theme — live-applied + persisted), `NutritionSettings`,
    `VoiceSettings` — no Save button, no draft window.
  - Settings pages whose only `label="Save"` is inside an
    add/edit/rename `BaseDialog`: `StoresSettings`,
    `StockGroupsSettings`, `StockLocationsSettings`,
    `RecipeCategoriesSettings`, `RecipeCuisinesSettings`,
    `RecipeDietaryTagsSettings`, `RecipeMealSlotsSettings`,
    `RecipeToolsSettings`, `UsersAdminSettings`,
    `ApiAccessSettings`. Dialog state is intentionally transient —
    cancelling closes; route nav would close the parent component
    and lose the dialog along with it, but that's modal-close,
    not "discard your half-typed essay" territory. Out of scope
    for this FU.
  - `MealPlansBoardPage.vue`, `MealPlansOverview.vue`,
    `MealPlanTemplatesPage.vue` — no page-level draft (board
    mutations write immediately; the `label="Save template"`
    button on each is inside a `v-close-popup` dialog).
  - `RecipeEditDialog.vue`, `SubstituteMetadataDialog.vue`,
    `MealPlanTemplatesDrawer.vue` — dialogs/drawers, not pages.
- **Standards close-gate:** clean.
  - **R-001 (componentisation):** no new components — the existing
    `useUnsavedChangesGuard` was reused with no copy-paste.
  - **R-003 (single source):** the guard's policy (the confirm
    dialog copy, the `beforeunload` shape, the
    `onBeforeRouteLeave`/`onBeforeRouteUpdate` pair) lives in one
    file; each call site only supplies the dirty predicate.
  - **New rule promoted:** **R-020 + ADR-015** — "Deferred-save
    surfaces wire the unsaved-changes guard." Two events in six
    weeks (FU-156 + this sweep) where a new editor page forgot the
    guard is rule-worthy recurrence; the rule pins the predicate
    shape, names the four standing exclusion categories (inline
    save, real-time session, dialog-only, password field), and
    gives reviewers a one-line grep target for new diffs. Comments
    on the four already-wired sites updated to reference `R-020`
    so the rule's discoverable from the call site.
- **Verification:** `vue-tsc --noEmit` clean. Browser verify (the
  two new sites' nav prompts fire when dirty, suppress when clean)
  logged as **[[FU-322]]** for the next verify-pass.
- **Carry-over:** none in scope. Cook-mode session-state guarding
  was considered and rejected as out-of-scope for this FU (rationale
  above) — if a future user report flags lost cook sessions on
  accidental nav, that becomes its own follow-up.

## [RESOLVED] FU-097 — Roll out `formatQuantity()` to recipes/shopping-list surfaces
- **Raised:** 2026-06-09 (Cook Mode Chunk 2)
- **Type:** finding / R-001 + R-003 cleanup
- **Resolution (2026-06-29):** quantity-spacing sweep — `formatQuantity`
  is now the only place that knows the DEC-3 rule. Surfaces audited
  against the FU's original list:
  - **`MealPlanShoppingSummary.vue`** — switched the `needs {{ qty }} {{ unit }}`
    inline to `formatQuantity(ing.total_quantity, ing.unit)`.
  - **`SequentialBuilderDialog.vue`** — same pattern (kept the `round()`,
    just routed the result through `formatQuantity`).
  - **`RecipeCookMode.vue` substitute-ratio caption** and
  - **`StockItemDetailPage.vue` substitute-ratio caption** — both built
    `${qty} ${unit} → ${qty} ${unit}` by hand; now each half goes through
    `formatQuantity`. Safe because FU-034 canonicalises the ratio unit on
    persist (`"tablespoons"` → `"tbsp"`), so the lowercased no-space
    inclusion list catches every form. Cook mode's own ingredient-row
    display path was already on `displayQuantity` → `formatQuantity` from
    Chunk 2.
  - **Print view (`dora_api/features/data/export_recipe.py`)** — the
    server-rendered Jinja template was emitting `{{ quantity }} {{ unit }}`
    with an always-on space. Added a Python mirror **`format_quantity`** in
    `dora_api/domain/units.py` (R-003: the no-space inclusion list lives
    next to `UNIT_TABLE`, the existing single source of truth for units)
    and the template now calls it via a passed kwarg. Server + client
    spacing are guaranteed identical.
  - **FU items now N/A:** `RecipeDetailPage.vue` and `RecipeEditDialog.vue`
    use **separate** qty + unit `q-input`s (no concatenation to format);
    `RecipeCard.vue` and the cookbook overview don't render `qty + unit`
    at all (just name, time, servings, tags). The shopping-list bullet was
    already marked N/A by the FU's own 2026-06-12 update. The "Print/export
    view" item pointed at the SPA hub page (`ExportPrint.vue`) which is a
    list of export actions — the actual recipe print template was the
    server-side Jinja, fixed above.
- **Bound to:** the unit-canonicalisation work in `dora_api/domain/units.py`
  + FU-034 substitute ratios — canonical forms feed naturally into the
  formatter because matching is case-insensitive and the inclusion list
  covers every canonical "tight" unit (ml, g, kg, L, mg, oz, lb, fl oz,
  pt, qt). No drift risk between server-canonicalised units and
  client-side formatting.
- **Standards close-gate:**
  - **R-003 (single source)** — the rule is now stated **once per language**
    (TS `formatQuantity.ts`, Python `units.py:format_quantity`); inclusion
    lists are mirrored by intent (5-line frozenset / 1-line `ReadonlySet`)
    with a comment on each side flagging the sync requirement. No call
    site re-implements the rule.
  - **R-001 (componentisation)** — no new components; surfaces routed
    through the existing helper.
- **Verification:** `vue-tsc --noEmit` clean. Python compile not run
  (no interpreter in this session's env); the only Python change is a
  small pure helper + a Jinja `{% set %}`, both syntactically trivial.
  Browser verify of the print view + meal-plan summary + substitute
  ratio captions deferred — captured below if you'd like a verify pass.
- **Carry-over:** spawned a new [[FU-321]] — browser-verify the four
  routed display surfaces in a real Quasar build before trusting that
  every spacing case lands the right way ("1L" / "1 tbsp" / unitless
  fallbacks / ratios in both directions).

## [RESOLVED] FU-092 — Audit ALL implicit / automatic / "magic" behaviour
- **Raised:** 2026-06-09 (user, during C-7 cart-button design — started
  as the "preferred product" worry, broadened to every automatic
  behaviour).
- **Type:** open question / app-wide UX assessment.
- **Resolution (2026-06-28):** ran the full audit. Output at
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` — 18 behaviours
  catalogued, each with a current-state pointer, a surprise-risk read,
  and a recommended verdict. User reviewed every one and gave per-
  finding verdicts; results table at § Verdicts in the audit doc.
  Outcome: **13 of 18 already in the right shape** (alerts, suggestions,
  explicit endpoints, visible-by-design surfaces, FU-114-style
  visible-default flows) — no action. **4 small (b) follow-ups**
  spun off as [[FU-315]] (auto-add toast/chip verify),
  [[FU-316]] (remembered-list toast + "always ask" setting),
  [[FU-318]] (cheapest chip), [[FU-319]] (inline-pantry toast). **1
  plan-first follow-up** spun off as [[FU-317]] — F5 past-day
  meal-plan auto-drain wants a designed manual-reconcile feature
  (stocktake-mode-for-meals: dedicated page, alert, indication of
  what should have been consumed) plus an opt-in setting for the
  current auto-drain. Per the user's call, **no code touches the
  reconcile path before that proposal lands.** R-019 (no magic) is
  the standing rule going forward; this audit is the one-time backlog
  sweep that ratified what was already correct.

## [RESOLVED] FU-160 — Shopping-list "shopping day" alert (feedback L403)
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** deferred job
- **What:** Feedback L403 asked for an alert when a list's planned shop
  date is today / imminent / overdue.
- **Resolution (2026-06-28):** confirmed already shipped end-to-end.
  Server: `dora_api/features/alerts/get_alerts.py:391`
  (`_shopping_day_alerts`) — pulls every not-yet-done `ShoppingList`
  whose `planned_shop_date` falls within the next 3 days
  (`SHOPPING_DAY_WINDOW_DAYS`) or has already passed. Overdue lists
  bump to `SEVERITY_MEDIUM` ("Shopping day was yesterday / N days
  ago"); upcoming use `SEVERITY_LOW` with "today" / "tomorrow" /
  "in N days" wording. Kind `shopping_day` lives in
  `dora_api/features/alerts/alert_kinds.py:30` at `TIER_FYI`. Alerts
  ride the shared bell + snooze pipeline via `list_alert_key(...)` so
  user dismiss/snooze persists as the date rolls. Frontend renders +
  deep-links in `web_app/src/models/alert.ts` (kind union at L19,
  icon/label/route switches at L138/168/190/222/237) and
  `web_app/src/pages/AlertsPage.vue:265` (filter chip) /
  `:302` (deep-link target). Closing the FU to match reality —
  someone shipped this between when the FU was raised and now without
  closing it.

## [RESOLVED] FU-084 — Promoted to R-019 / ADR-014 ("no magic: explicit, verbose, consistent")
- **Raised:** 2026-06-09 (Chunk 2)
- **Type:** finding / engineering-standards
- **What:** Originally proposed promoting the SQLAlchemy
  `lazy="selectin"` shortcut on `Recipe.cuisine`/`.category` into a
  standing rule for "small always-wanted lookups".
- **Resolution (2026-06-28):** user re-scoped the FU from the narrow
  selectin recommendation to a top-line value: prefer **verbose,
  explicit, locally-readable code**; reject **magic** (AutoMapper-shaped
  reflection, decorator behaviour-mutation, convention-over-configuration
  past the framework, per-entity loading-strategy overrides that hide
  what runs at the call site); reject **inconsistent local patterns** ("most
  of the codebase does X but here we did Y because it felt right"). Added
  **R-019 — No magic: explicit, verbose, consistent** to
  `docs/01_charter/ENGINEERING_STANDARDS.md`, with **ADR-014** recording
  the decision and the FU-084 reframing. R-019 explicitly notes that
  per-entity SQLAlchemy `lazy="..."` overrides are themselves a flavour
  of magic and should be retired in favour of explicit call-site loading;
  the existing `Recipe.cuisine`/`.category` selectin opt-ins are
  grandfathered for R-007 reasons and flagged as [[FU-314]] for an
  opportunistic cleanup chunk.

## [RESOLVED] FU-140 — Sweep Cart Button Chunk 3 typing fallout (nullable `stock_item_id`)
- **Raised:** 2026-06-12 (State Ownership Chunk 4 typecheck)
- **Type:** finding / cleanup
- **What:** Cart Button Chunk 3 made `ShoppingListLine.stock_item_id`
  nullable; the audit was to catch consumers that compiled only
  because no other change had triggered re-checking.
- **Resolution (2026-06-28):** ran `npx vue-tsc --noEmit` from
  `web_app/` — exits clean under `exactOptionalPropertyTypes`. Then
  hand-audited every `ShoppingListLine.stock_item_id` reader:
  - `ShoppingListDetail.vue` — `openFinishReview` filters nulls
    out of the dedupe set and keeps them as "Not stock-tracked"
    rows in the finish modal (UI guarded by `v-if="entry.stock_item_id"`);
    `confirmFinish` narrows via typed `.filter` predicate before
    sending `FinishLevelOverride[]`; `onSwapSubstitute` early-returns
    on null and filters the on-list dedupe set through
    `(id): id is string => !!id`; `onRemoveLine` (the FU-131 rule-4
    path) checks `!before.stock_item_id` before triggering the
    extra remove; template guards `<router-link :to="/stock/{id}">`
    behind `!isNestedChild(line) && line.stock_item_id`.
  - `NewListDialog.vue` (lines 284, 374, 396) — all three id
    extractions use the typed filter predicate.
  - `StockOverview.vue:759` — `(l) => l.stock_item_id && selected.has(l.stock_item_id)`
    relies on TS narrowing within `&&`, type-checks.
  - The `removeByStockItemFromListAsync` call in `onRemoveLine`
    only fires when `alsoRemoveStockItemId` is non-null.
  Two collateral TS errors from FU-117's step-editor work surfaced
  during the audit and were fixed in the same pass:
  `RecipeDetailPage.vue:1914` (the import-recipe step factory now
  sets `section_client_id: null`) and `RecipeStepsEditor.vue:8`
  (passes `sectionOptions ?? []` so the optional prop doesn't
  leak `undefined` to the row under `exactOptionalPropertyTypes`).

## [RESOLVED] FU-139 — Finish migrating `getStockLevelColour(name)` callers to `colourForSequence(seq)`
- **Raised:** 2026-06-12 (State Ownership Chunk 4)
- **Type:** follow-up / cleanup
- **What:** Chunk 4 introduced `colourForSequence(seq)` and migrated
  the decision-driving call sites, leaving the legacy
  `getStockLevelColour(name)` as a soft-fallback on six display-only
  surfaces.
- **Resolution (2026-06-28):** confirmed already shipped — no code
  changes needed. The legacy `getStockLevelColour` no longer exists
  in `web_app/src/helpers/stockLevelLogic.ts`; the file now only
  exports `colourForSequence`, and a `grep -r getStockLevelColour
  web_app/src` returns just the historical mention in the
  `colourForSequence` doc-comment. Every named call site
  (`StockItemDetailPage.vue`, `RecipesOverview.vue`,
  `RecipeDetailPage.vue`, `QuickAddSheet.vue`,
  `CreateStockItemDialog.vue`, `MyProductsPage.vue`) routes through
  `colourForSequence(level.sequence)` / `colourForSequence(item.
  stock_level_sequence)`. Closing the FU to match reality.

## [RESOLVED] FU-138 — Query-count test for `GET /recipes` (no N+1)
- **Raised:** 2026-06-12 (State Ownership Chunk 2 close-gate)
- **Type:** deferred job (test infra)
- **What:** Pin the recipe-list endpoint's SELECT count so the
  batched cookability / missing-names aggregations can't silently
  regress into N+1 lazy loads.
- **Resolution (2026-06-28):** added a minimal `SelectCounter`
  context manager at `tests/e2e/dora_api/_query_counter.py` that
  listens on SQLAlchemy's `Engine.before_cursor_execute` and
  records every SELECT during its scope. New test
  `tests/e2e/dora_api/test_recipes_query_count.py` runs a ratio
  check rather than a hard ceiling: baseline `GET /recipes`,
  insert 10 throw-away recipes via `POST /api/recipes`, re-hit
  `GET /recipes`, assert the per-recipe SELECT delta stays under
  0.5 (cleanup deletes the probe recipes in the `finally`).
  Passes today with a delta of 0; an honest N+1 regression on
  cookability/ingredients/tags/tools/sections/plan-rollups would
  add ≥1 SELECT per recipe and blow the budget. Test fixture
  matches the existing e2e shape — uses `requests` rebound to the
  Flask test client by `tests/e2e/dora_api/conftest.py`. Kept the
  harness intentionally tiny (single class, ~50 LOC); resist
  growing it into shared infra until a second consumer shows up.

## [RESOLVED] FU-131 (original) — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 deliberate scope-down)
- **Type:** rollout
- **What:** Backend rules 1–3 + schema + DTO landed in the chunk
  itself; the UI side (rule 4 confirm modal, inline-product variant,
  nested display) plus a backup/restore round-trip were carved out.
- **Resolution (2026-06-28):**
  - **Rule 4 modal, inline-product variant, nested display** —
    confirmed already shipped (likely as part of a later FU-131
    follow-on session that didn't close the parent entry). Live in
    [ShoppingListDetail.vue:2132](web_app/src/pages/ShoppingListDetail.vue:2132)
    (`onRemoveLine` prompts "Also remove the stock item?" when the
    deleted line is product-only and its linked stock item is on
    the list as a separate row), [AddToListButton.vue:21](web_app/src/components/AddToListButton.vue:21)
    (`variant="inline-product"` + `productId` anchor path —
    wired into [MyProductsPage.vue:349](web_app/src/pages/MyProductsPage.vue:349) as
    "Add as product"), and [ShoppingListDetail.vue:1362](web_app/src/pages/ShoppingListDetail.vue:1362)
    (`nestedLinesFor` reorders child product lines immediately
    under their parent stock-item line; `isProductOnly` drives the
    `shopping-bag` chip + "Product only — no linked stock item on
    this list" tooltip).
  - **Backup / restore round-trip** — actual gap fixed this session.
    `restore_shared.py` left the new nullable `product_id` column
    unclassified, so a partial restore that included shopping lists
    but not `saved_products` would silently drop product-only lines
    (or null `product_id` on nested children, then crash the new
    `ck_shopping_list_line_anchor` CHECK on product-only rows).
    Added `("shopping_list_items", "product_id"): "saved_products"`
    to `HARD_FK_PULL_IN` so the referenced Product is auto-included,
    and added `("shopping_list_items", "product_id")` to
    `REQUIRED_FKS` so the row is dropped (with a warning) rather
    than silently re-shaped when the Product truly is missing.
    Annotated the existing `stock_item_id` REQUIRED entry to make
    the nullable-but-must-resolve semantics explicit.
- **Browser verification of the three UI pieces remains tracked
  as [[FU-145]].** Product-anchored cart-state membership is
  separately tracked as [[FU-144]].

## [RESOLVED] FU-117 — `RecipeStepsEditor` should let you pick a step's section
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Chunk 10 wired `section_id` on `RecipeStep` end-to-end
  but the steps editor lacked a section picker; hand-entered steps
  shipped with `section_id = NULL`.
- **Resolution (2026-06-28):** added `section_client_id: string | null`
  to `EditableStep` and a new `SectionOption` type in
  `recipeStepEditorTypes.ts`. `RecipeStepsEditor` now takes an
  optional `sectionOptions` prop and forwards it to each row;
  `RecipeStepRow` renders a compact `q-select` in the row header
  **only at `depth === 0`** and only when more than one option
  exists (the implicit `(Main)` plus at least one named section) —
  sub-steps inherit visually as the FU prescribed. `RecipeDetailPage`
  reuses its existing `sectionOptions` computed (already
  `[{value: null, label: '(Main)'}, …]`), passes it to the editor,
  hydrates `section_client_id` from `s.section_id` on load, and
  rides it through `stepsToSend` on save. `removeSection` now also
  detaches step references in addition to ingredient ones (parity
  with the existing ingredient-row picker). New-step factories in
  the editor initialise `section_client_id: null`. Importer left
  unchanged — `HowToSection` detection in the URL importer is a
  separate concern.


- **Raised:** 2026-06-11 (Cookbook Chunk 9 impl)
- **Type:** finding / cleanup
- **What:** Chunk 9 stopped rendering/editing the freeform
  `recipe.nutrition` text column in favour of the structured
  `kcal: int | None` field. The column survived in the DB + on the
  DTO + in the form's hydrate/save plumbing pending a prod audit.
- **Resolution (2026-06-28):** pre-release — no production data to
  preserve, so the column was dropped outright rather than audited.
  Migration `b7e2d9a4c1f5_20260628_drop_recipe_nutrition.py` drops
  `Recipe.nutrition`; the field was removed from the `Recipe`
  entity (incl. `Fields.NUTRITION`), `table_mappings.py`, the
  create/update request models + their entity assignments,
  `RecipeDto` + assignment in `get_recipes.py`,
  `new_recipe_version.py` clone, `import_recipe_from_url.py`
  (including `_coerce_nutrition` and the `ImportedRecipeDto`
  field), the export-recipe Jinja template, the seed factory, the
  `test_recipe_cookability` stub, and from the SPA
  (`recipe.ts`, `recipeApiService.ts` × 3, `RecipeDetailPage.vue`
  hydrate/empty/save-diff/import paths, `RecipesOverview.vue` import
  call, `RecipeEditDialog.vue` template input + form + create/update
  payloads).


- **Raised:** 2026-06-10 (Cookbook Chunk 7 impl)
- **Type:** R-001 cleanup
- **What:** Chunk 7 added a second "Import from URL" dialog
  (`RecipesOverview.vue`); the detail page already had one
  (`RecipeDetailPage.vue`). The two duplicated the dialog chrome, copy,
  URL input, `importFromUrlAsync` call, loading + error states.
- **Resolution (2026-06-28):** new `web_app/src/components/recipes/RecipeImportDialog.vue`
  owns:
  - the dialog chrome (`BaseDialog`, title, schema.org caption, URL input,
    Cancel + Import action),
  - the `url` / `error` / `importing` state,
  - the `importFromUrlAsync` call,
  - and resets its draft on every open via a `watch` on the v-model.

  Per the FU's recommendation, picked the **events** shape over a `mode`
  prop. The component emits `@imported(dto: ImportedRecipe)` and lets each
  caller decide what to do — no shared knowledge of `form`, `createAsync`,
  navigation, or `markDirty`. A single optional `degraded-hint` prop lets
  the detail surface append "Your existing recipe will be overwritten with
  the imported fields." to the caption without forking the dialog.

  **Callers updated:**
  - `RecipesOverview.vue` — handler `onRecipeImported` now just builds
    the create payload, POSTs it, navigates to the new recipe, and toasts.
    Dropped local `importUrl` / `importError` / `importing` refs (+ a
    now-unused `BaseDialog` import).
  - `RecipeDetailPage.vue` — handler `onRecipeImported` does the
    confirm-overwrite `$q.dialog`, patches the form fields, and toasts.
    Same local-state cleanup. Side fix: if the user cancels the
    confirm-overwrite, the import dialog now closes (previously stayed
    open on cancel — minor pre-existing bug).

  **Verification:** `vue-tsc` clean. Full e2e + unit suite **442/442
  passing.**

## [RESOLVED] FU-094 — Steps editor: drag-and-drop reorder (replaces up/down)
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The structured-steps editor shipped with up/down arrow
  buttons instead of the drag-handle pattern from shopping-list lines.
  Replace once the editor is in real use.
- **Resolution (2026-06-28):** drag-and-drop landed.
  - **`RecipeStepRow.vue`** — added a drag handle (`drag_indicator`
    icon) that's the only `draggable="true"` element on the row, so
    textareas + selects stay normally clickable. The whole row is the
    drop target (`@dragover` / `@drop`); `setDragImage` points at the
    row's outer div so the visual preview is the whole row. Up/down
    arrow buttons removed.
  - **`RecipeStepsEditor.vue`** — owns the drag state
    (`draggingClientId` + `draggingParentId`) so every row decides
    whether *it* is a valid drop target. Reorder logic mirrors
    `ShoppingListDetail.onLineDrop`'s "insert at the target's slot"
    pattern; sequences re-packed through the existing
    `repackSequences`.
  - **Siblings-only constraint** (per the FU): `dragover` only allows
    `preventDefault` when the source's `parent_client_id` matches the
    target's. A top-step can't become a sub-step via drag and vice
    versa — that promotion/demotion is its own affordance and
    deliberately out of scope. Validation re-checked at drop time as
    belt-and-braces.
  - **Visual feedback** — dragging row gets `opacity: 0.5`; the
    hovered-valid drop target gets a 2px `var(--brand-primary)`
    outline. Handle has `cursor: grab`/`grabbing`, token-only colours
    (R-002).
  - **No backend change** — the persisted shape (parent + sequence) is
    what the editor already emits.
  - **Verification:** `vue-tsc` clean. Full e2e + unit suite
    **442/442 passing**. The DnD itself is browser-level; suite acts
    as a regression guard on the surrounding code.

## [RESOLVED] FU-081 — Move "Planned in" filter from client-side to server-derived Recipe.is_planned
- **Raised:** 2026-06-09 (Cookbook Chunk 1)
- **Type:** finding / state-ownership
- **What:** Cookbook overview was walking `mealPlanStore.mealPlans[].entries[]`
  client-side to build the "planned recipes" set — a cross-entity rule
  (recipes × meal plans × today) that R-003 says belongs on the server.
- **Resolution (2026-06-28):** moved to the server + added a tri-state UI on
  the same trip.
  - **Backend:** `RecipeDto.is_planned: bool` derived in
    `_hydrate_unallocated` from the already-running future-unconsumed
    `MealPlanEntry` query — zero extra round-trip.
  - **Pre-existing bug surfaced and fixed:** `_hydrate_unallocated`'s
    raw `text()` query bound stringified UUIDs against the `UUIDType`
    BLOB columns on SQLite (string-vs-BLOB never matches), so
    `committed_meals`, `unallocated_meals`, `plan_count` had been
    silently 0 for any future-planned recipe. Hidden by the seed
    (no future entries) and only surfaced today because the new
    `is_planned` test forced a future entry. Switched the derivation
    to ORM `select()` against the mapped table so SQLAlchemy applies
    the UUIDType bind-processor; portable across SQLite + Postgres.
  - **Frontend:** Recipe model + `is_planned` field; new
    `TriStateFilterChip.vue` (cycles `off → include → exclude → off`
    on each click, with swappable label/icon/colour per state);
    `RecipesOverview.vue` swaps `plannedInOnly: boolean` for a
    `plannedFilterState: TriState` and binds the new chip
    ("Planned" → click → "Not planned" → click → off). Predicate +
    active-filter count + Clear filters all updated.
  - **Round-trip eliminated:** the cookbook page no longer needs to
    `await mealPlanStore.getMealPlansAsync()` on mount; the
    `mealPlanStore` import + ref are gone from `RecipesOverview.vue`.
    Saves one network call per cookbook visit.
  - **Tests:** new `tests/e2e/dora_api/test_recipe_is_planned.py`
    (3 cases): toggles true when a future un-consumed entry is
    created, flips back to false on deletion, present on every DTO.
    Full suite **442/442**. `vue-tsc` clean.

## [RESOLVED] FU-075 — Run the new `test_shopping_list_planned_shop_date` e2e
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up (verification gap)
- **What:** Pure runtime-verify of the four cases in
  `tests/e2e/dora_api/test_shopping_list_planned_shop_date.py`
  (create-with-date, create-without, PATCH set-and-clear-with-null,
  PATCH preserves-the-date-when-not-sent). Deferred because the original
  implementation session had no live Python env.
- **Resolution (2026-06-28):** ran the file on this session's working
  venv with migration `e1a4c7b2f9d0` (and every subsequent migration)
  applied. **4/4 passing** — the planned-shop-date wire-up survives
  every later schema and DTO change unchanged. Nothing to fix.

## [RESOLVED] FU-056 (slice 1b) — `UNIQUE(StockItemProduct.product_id)`, kill `product_multi_linked`
- **Raised:** 2026-06-28 (user pushed back on the multi-linked lookup kind)
- **Type:** model simplification — same FU.
- **What:** the user noticed `product_multi_linked` modelled a case that has
  no real semantic justification: a specific Product SKU (e.g. "Vitasoy
  Oat Milky 1L") satisfies one pantry slot, not many. The case only
  existed because the `StockItemProduct` join was symmetric m:n when the
  truth is asymmetric: many Products can satisfy one StockItem (different
  brands of milk all map to "Milk"), but a Product satisfies exactly one.
- **Resolution (2026-06-28):**
  - Migration `c4a8e2b9d7f5` — `UNIQUE(product_id)` on
    `StockItemProduct`. Seed already conformed (verified: 0 multi-linked
    products) so no backfill needed.
  - `barcode_lookup` simplified from 5 kinds to 4 — dropped
    `product_multi_linked`; barcode → Product → at most one stock item
    is structurally guaranteed.
  - Frontend types + `BarcodesQR.vue` dialog branches + `StockOverview.vue`
    scan handler + an existing e2e expectation all updated to the
    simpler shape.
  - **vue-tsc clean. Full suite 439/439.**

## [RESOLVED] FU-056 (slice 1) — Hybrid Barcode model + register-against-stock-item UI
- **Raised:** 2026-06-07 (P6-02 deferral); slice 1 shipped 2026-06-28.
- **Type:** deferred job
- **What:** P6-02 had explicitly dropped `StockItem.barcode` and routed
  every real EAN through `ProductBarcode → Product → StockItem`. That
  was conceptually correct for catalogued installs but broke scanning
  entirely for lightweight installs (FU-209 data-presence overlay
  → zero `Product` rows → no place to register an EAN).
- **Resolution (2026-06-28, slice 1):** discussed the design tension
  with the user; agreed on a **hybrid `Barcode` model** that keeps the
  "barcode = SKU" semantics when a Product exists AND lets a barcode
  attach directly to a stock item when one doesn't.

  **Schema (migration `b7f3a2c8d5e1`):**
  - Renamed `ProductBarcode` → `Barcode`.
  - `product_id` made NULLable + UNIQUE (enforces "one Product = one
    EAN"; UNIQUE-with-multi-NULLs is portable to both SQLite and PG).
  - `stock_item_id` added, NULLable, not unique (a stock item can carry
    many direct EANs).
  - CHECK constraint: at least one of the two FKs must be set.
  - `created_at` column added (mirrors other entities).
  - Restore-backup section + cross-table FK rules updated.

  **Backend (`features/data/barcodes.py`):**
  - **Lookup precedence:** dora:// QR → direct stock-item linkage →
    Product traversal (single linked / multi linked / no link). Five
    lookup kinds returned, each with the IDs the caller needs.
  - **`POST /api/data/barcodes`** — single registration endpoint;
    body has `barcode` + at least one of `product_id` /
    `stock_item_id`. Both is allowed. Pre-flight uniqueness check,
    DB UNIQUE as the real backstop, per-product UNIQUE catches "this
    Product already has a barcode".
  - **`DELETE /api/data/barcodes/<id>`** — remove a registration.
  - The old `/barcodes/register-against-product` route is collapsed
    into the new shape.

  **Stock-item detail (`get_stock_item_detail.py`):**
  - New `StockItemBarcodeDto` carrying `barcode_id`, `barcode`,
    `source` (`'direct' | 'via_product'`), and the product
    id/name for via-Product rows.
  - Handler derivation walks every `Barcode`, splits into direct vs
    via-Product (using `_StockItem.products` for the linked-Product
    set), sorts direct rows first.

  **Frontend:**
  - `models/stockItemDetail.ts` — new `StockItemBarcode` type +
    `barcodes` field.
  - `services/api/barcodeApiService.ts` — `registerAsync` /
    `deleteAsync` + the new five-kind `BarcodeLookupResult`.
  - `StockItemDetailPage.vue` — new **Barcodes** section under the
    Substitutes tab, gated on `features.scanning`. Lists direct +
    via-Product rows; "+ Add barcode" opens a small dialog
    (textbox-only for now; camera button is a future polish slot).
    Direct rows have a remove button; via-Product rows are read-only
    here (edit on the Product).
  - `BarcodesQR.vue` (Data → Scanning surface) — scan result dialog
    handles all five kinds; on `unknown` a register-now flow appears
    (stock-item picker → register via the new endpoint, with the
    barcode value coming from the scan).
  - `StockOverview.vue` scan integration — every result kind that
    resolves to a single stock item routes straight to it;
    Product-derived branches without a unique target surface a
    descriptive toast.

  **Tests (`test_data_router.py`):**
  - 6 new e2e cases (notes-only, ratio direction inversion, update-
    clears, half-filled rejection, qty=0, unknown unit) — sorry,
    wrong FU; for FU-056 the new tests are: register-against-product
    + lookup traversal, same-barcode-twice = 409, direct-stock-item +
    lookup returns `stock_item`, per-product UNIQUE = 409,
    neither-target = 400, delete round-trip.
  - Test fixture `_next_unused_product_id()` added because every test
    now consumes a Product (per-product UNIQUE forces it).
  - Full e2e + unit suite: **439/439 passing** post-landing. `vue-tsc`
    clean.

  **What stayed deferred (FU-056 stays OPEN at smaller scope):**
  - **Ingestion auto-populate** — Phase 2 work; endpoint already in
    place, ingestion just calls it.
  - **Product detail EAN field** — slot into the Products UI when
    that surface is touched; uses the same endpoint.

## [RESOLVED] FU-050 — Broader `'Out of Stock'` name-match smell beyond the 7 cookability copies
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** Chunk 3 removed the 7 recipe-cookability client copies, but a
  grep showed `'Out of Stock'` / `'Low Stock'` name-matching still living
  in non-recipe surfaces (`needToBuy`, restock sources, cook-mode
  availability, etc.), plus the legacy name-keyed
  `getStockLevelColour` helper that its own docstring marked for
  retirement.
- **Resolution (2026-06-27):** investigated; the **specific call sites
  the FU flagged were already migrated** — `needToBuy` now goes through
  the shared `useStockStatus().needsBuying` composable (sequence-keyed),
  and cook mode + ShoppingLists overview already key off
  `OUT_OF_STOCK_SEQUENCE` constants. The real remaining smell was the
  **legacy `getStockLevelColour(name)` helper** still being called from
  6 files (16 call sites). Swept all of them:
  - `CreateStockItemDialog.vue` — passes `scope.opt.sequence` to
    `colourForSequence`.
  - `QuickAddSheet.vue` — looks up `sequence` from the level store, not
    name.
  - `StockItemDetailPage.vue` — added a `detailLevelColour` computed
    that resolves the level's sequence via the store and routes through
    `colourForSequence`; per-level menu items use `level.sequence`
    directly. Also retired a suspicious `?? 'Well-Stocked'` default that
    was rendering untracked items in the success-green tone.
  - `MyProductsPage.vue`, `RecipeDetailPage.vue`, `RecipesOverview.vue` —
    same shape; the per-page colour computeds now key off
    `stock_level_sequence` (already on the StockItem model).
  - `helpers/stockLevelLogic.ts` — **legacy `getStockLevelColour`
    function deleted**, docstring updated to record the retirement.
  - **Bonus R-003 fix surfaced in the same area** —
    `services/doraIntents.ts` was carrying its **own copies** of
    `LOW_STOCK_SEQUENCE = 2` and `OUT_OF_STOCK_SEQUENCE = 3`,
    duplicating the canonical constants in `helpers/stockStatus.ts`.
    Deleted the duplicates and imported the shared ones.
- **Verification:** `vue-tsc --noEmit` clean. Full backend suite
  **435/435 — zero failures.** Final grep: every remaining
  `'Out of Stock'` / `'Low Stock'` literal in the codebase is in a
  comment / docstring describing the vocabulary; zero name-match code
  paths remain. The accepted carve-outs (`stockLevelLogic.ts` source,
  comment-only references in models) stay per the FU's original
  guidance.

## [RESOLVED] FU-049 — RecipeDetailPage cookability reflects saved recipe, not live edits
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** The recipe-detail sidebar "Cookable now / Missing N" reads
  `recipe.value` (the server-computed values on the loaded DTO) rather
  than recomputing live from `form.ingredients` while the user edits. So
  while adding/removing ingredients pre-save, the sidebar aggregate
  doesn't react until save reloads the DTO. The per-ingredient editor
  badge does update live (stock store boolean).
- **Resolution (2026-06-27):** user accepted on condition that the state
  refreshes after save. Verified end-to-end: `onSave()` at
  `RecipeDetailPage.vue:1703-1704` does
  `await updateRecipeAsync(command); await loadRecipe();`, and
  `loadRecipe()` (line 1601) re-fetches the full server DTO so the
  sidebar's `missing_count`, `cookable`, and `missing_stock_item_names`
  come back fresh. The same `loadRecipe()` runs after every other
  mutation that could affect cookability (favourite toggle, ingredient
  ops at lines 1729/1984/2004/2028/2144). Steady-state is correct;
  the temporary staleness during edit is the deliberate trade-off
  Chunk 3 made to avoid the client-recomputed stock-join duplication
  it removed (R-003). No code change.

## [RESOLVED] FU-310 — Four pre-existing e2e failures on `prototype/claude-upgrades`
- **Raised:** 2026-06-26 (surfaced during FU-082 test sweep)
- **Type:** finding (pre-existing test rot)
- **What:** Four `tests/e2e/dora_api` failures had drifted since the
  Settings rebuild Phase 4 / Dashboard rebuild Phase 2 work added new
  fields to the auth/user surface.
- **Resolution (2026-06-27):** root-caused and fixed.
  - **Real bug found** — `POST /api/auth/register` returned an ad-hoc
    dict (`user_id`, `username`, `email`, `is_admin`, `email_verified`,
    `verification_sent`) instead of the full `AuthenticatedUserDto`
    that `/login` and `/me` both return. The SPA's `registerAsync`
    already typed the response as `AuthenticatedUser`, so the auth
    store was being hydrated with `undefined` for every missing field
    (`has_image`, `dashboard_layout`, `theme`, `voice_engine`,
    `nutrition_mode`, etc.) — silent breakage masked by Vue
    permissiveness.
  - **Fix:** `register_user.py` now returns
    `dataclasses.asdict(AuthenticatedUserDto.from_entity(new_user))`
    plus the `verification_sent` extra. Mirrors `/login` and `/me` so
    the SPA can fully hydrate from any of the three.
  - **Two stale test assertions fixed:**
    - `test_user_router.py::test__get_users__GettingUsers__GetsAllExpectedAttributes`
      — added `'has_image'` to the expected key set (Settings rebuild
      Phase 4 added it to `UserDto` and bulk-stamps it via
      `_stamp_has_image`).
    - `test_auth_flows.py::test__profile_picture__rejects_oversize_data_url`
      — changed expected status from 422 to 400 (the codebase's
      convention for pydantic ValidationError, per
      `middleware.deserialise_web_request`; 84 other tests already
      use 400, only the one outlier used 422).
  - **Verification:** the 4 originally-failing tests now pass; full
    e2e + unit suite **435/435 — zero remaining failures.** Frontend
    `vue-tsc` clean.

## [RESOLVED] FU-034 — Wire up `StockItemSubstitute.notes` (substitution notes)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItemSubstitute.notes` existed but was never wired. User
  confirmed the feature shape on 2026-06-27: **hybrid** — free-text note
  for any substitute, plus an **optional structured ratio** (e.g. "1 tsp
  → 1 tsp", "1 cup → 226 g") so the cook-mode swap picker can show the
  hint front-and-centre without forcing structure on swaps that don't
  need it.
- **Resolution (2026-06-27):** shipped end-to-end.
  - **Migration `a1c5e7d4f2b9`** — adds 4 ratio columns
    (`ratio_quantity_in`, `ratio_unit_in`, `ratio_quantity_out`,
    `ratio_unit_out`) and an `all-or-none` CHECK constraint so a
    half-filled ratio is rejected at the DB layer.
  - **Schema** — `table_mappings.py` `stock_item_substitute_table`
    grew the 4 columns + the constraint. No new entity class (the
    pair stays a bare association table, mirroring the existing
    pattern).
  - **Direction handling** — `dora_api/features/substitutes/metadata.py`
    (new) owns validation + direction-flip. Pairs are stored
    canonically (`a < b`); callers always think in "from THIS item to
    the substitute" terms. `build_metadata()` swaps in↔out at
    persist time when needed; `get_stock_item_detail` swaps at read
    time so consumers always see the ratio oriented "this → that".
  - **API:**
    - `POST /stock-items/<id>/substitutes` now accepts `notes` +
      `ratio_quantity_in` / `_unit_in` / `_quantity_out` / `_unit_out`
      (Pydantic 255-char cap on notes, 32-char cap on unit strings).
    - **New `PATCH /stock-items/<id>/substitutes/<sub_id>`** —
      replaces the metadata bundle; empty body clears it. Direction
      from the caller's POV; server flips into canonical storage.
    - **`SubstituteDto`** in `get_stock_item_detail.py` exposes the
      5 fields, ratio already oriented "this → that".
  - **Validation (R-003 — one source):** all-or-none ratio, qty > 0,
    units present in `dora_api.domain.units.UNIT_TABLE`. Unit strings
    are canonicalised on persist ("tablespoons" → "tbsp") so display
    is stable.
  - **Frontend:**
    - `Substitute` model + `notes` / ratio fields.
    - `services/api/stockItemApiService.ts` — `addSubstituteAsync`
      gained an optional `SubstituteMetadataInput` argument;
      `updateSubstituteAsync` is new.
    - **`SubstituteMetadataDialog.vue`** (new, ~250 lines) —
      textarea + "Add a ratio" toggle that reveals qty+unit pickers
      on each side, labelled "of {fromName}" / "of {toName}".
      `q-select` with `use-input` filters the UNIT_TABLE aliases so
      typing "tablespoons" finds tbsp.
    - **`StockItemDetailPage.vue`** substitutes tab — each row now
      shows the ratio caption + note caption inline under the
      substitute name; pencil icon next to the unlink icon opens
      the edit dialog.
    - **`RecipeCookMode.vue`** swap picker — chips replaced by a
      `q-list` so each substitute can carry its ratio caption + note
      below the name (same layout as the detail-page list, so the
      user reads the swap the same way in both places). Cook mode
      does NOT auto-compute the swap quantity in this phase — it
      surfaces the hint; the cook applies it. Per Anti-creep,
      structured auto-compute is a future-phase call.
  - **Tests:** new `tests/e2e/dora_api/test_substitute_metadata.py`
    (6 cases) — notes-only round-trip, ratio round-trip with
    direction inversion verified by viewing from the other side,
    update-clears-on-empty-body, half-filled rejection,
    non-positive quantity rejection, unknown unit rejection. **All
    6 pass.** Full e2e suite: **431/435** (4 pre-existing FU-310
    failures, unrelated).
  - **Frontend:** `vue-tsc --noEmit` clean.
- **Standards close-gate:**
  - **R-001 (Componentisation)** — new dialog is its own component
    (~250 lines, single responsibility); not inlined into the already-
    large detail page.
  - **R-003 (single source)** — `metadata.py` owns validation +
    direction flip; both `add_substitute` and `update_substitute` call
    it. No duplicated unit checks.
  - **R-005 (portable data access)** — migration uses portable types
    (Float, String, CheckConstraint with portable SQL), no engine-
    specific tricks; `build_metadata` is pure-Python.
  - **R-006 (clean migrations)** — non-idempotent add-with-CHECK,
    no guards.
- **Carry-over (deliberately not in scope):**
  - **Auto-compute swap quantity at cook time** using the ratio +
    `UNIT_TABLE`'s conversion factors. Considered; deferred per
    Anti-creep — the cook reads the ratio and applies, same as
    today. Revisit if usage shows a clear "I keep wishing the
    system did the maths" signal.
  - **Cross-dimension density tables** ("1 cup butter ≈ 226 g
    coconut oil") — currently allowed in the UI (just store what the
    user typed); not converted by any client code. Same future-phase.

## [RESOLVED] FU-046 — A1 theme chunks D–F regressed since "done"; CHANGELOG over-claims
- **Raised:** 2026-06-06 (A1 STEP 2 Chunk D verify/finish)
- **Type:** finding
- **What:** Quasar palette literals (`grey-N`, `red-N`, `orange-N`, etc.) had
  crept back into the codebase after the A1 work was declared done. ~12+
  surfaces had drifted off theme-token compliance.
- **Resolution (2026-06-26):** "A1c regression re-sweep" run.
  **Files touched: 16+.** Pattern applied per R-002's apply rule:
  - **Helpers + composables retyped to `string | null`** —
    `stockLevelLogic.ts`, `useStockStatus.ts`, the per-page colour
    computeds in `RecipesOverview`, `MyProductsPage`,
    `MealPlanShoppingSummary`, `SequentialBuilderDialog`,
    `PageErrorState`, `ShoppingListRailItem`, `ShoppingListDetail`,
    `DataImport`, `TriStateFilter`. Neutral / out-of-stock branches
    return `null`; templates handle `null` by dropping `:color` and
    adding `class="dora-text-muted"` (q-icon) or
    `class="dora-bg-sunken dora-text-secondary"` (q-chip / q-avatar).
  - **Clean semantic swaps** — `notifyTypeRegistration.ts` `'red-5'` →
    `'negative'`; `StockItemRow` expiry `'soon'` `'orange-9'` →
    `'warning'`; `AlertsPage` `dismissed` and `AuditLogSettings`
    `info`/`debug` → `'info'`; `DoraChat` inactive tab chip switched
    from `grey-4`/`grey-9` to `dora-bg-sunken` + `dora-text-secondary`
    classes.
  - **Dropped redundant props** — `ShoppingListDetail`'s two
    `track-color="grey-4"` `q-linear-progress` props removed (Quasar
    default track is theme-acceptable).
  - **R-002 carve-outs preserved** — `ScanOverlay.vue:59` `grey-4`
    (DEC-4 camera rings) untouched, as designed.
  - **Deferred to FU-313** — graduated severity / heatmap palettes
    (`models/alert.ts` 144-169, `models/location.ts` 41-45,
    `AlertsPage.vue` snoozed/read ladder, `AddToListButton.vue:247`
    `amber-9`, `StockItemDetailPage.vue:1640` `amber-9`). These need
    a designed token ladder (`--severity-N` / `--heatmap-N` in
    `tokens.scss`/`themes.scss`), not a mechanical swap. FU-313
    logged with the recommendation.
  - **Final inventory** (`grep` for any palette literal): 21 matches
    total — 1 carve-out (ScanOverlay/DEC-4), 20 deferred to FU-313.
    Zero unaccounted-for regressions.
  - **Verification:** `vue-tsc --noEmit` clean. Eslint shows one
    error in `StockItemRow.vue:644` — that's the pre-existing FU-312
    `no-misused-promises` issue on the waste-undo handler, not
    introduced by this sweep.

## [RESOLVED] FU-042 — Alerts bell count ≠ list count (badge excludes low + ignores snooze)
- **Raised:** 2026-06-06 (C-9 brief; feedback L438)
- **Type:** finding (reported bug — root cause found statically)
- **What:** Bell badge showed fewer than the dropdown lists. Two causes:
  (1) badge = `high_count + medium_count`, excluding low; (2) badge read raw
  backend counts while list filtered client-snoozed alerts.
- **Resolution (2026-06-26):** code fix landed in C-9.1 (2026-06-15); the
  in-browser smoke that gated the close was confirmed today via the
  invariant e2e, which is the binding contract.
  - **Server (`get_alerts.py`):** one canonical count per request —
    `actionable_count = len(active items in the actionable tier)`,
    returned alongside `items[]` / `snoozed[]` / `fyi_count` /
    `snoozed_count`. Snooze + dismiss are server-owned via
    `AlertInteraction`, pre-filtered into the right buckets, so they
    apply everywhere by construction.
  - **Client (`alertStore.ts:32`, `AlertsBell.vue:27`):**
    `badgeCount = computed(() => data.value.actionable_count)` — direct
    read, zero recompute. R-003 single source.
  - **Locked by passing e2e** —
    `test__alerts__actionable_count_equals_high_plus_medium_in_items`
    asserts `actionable_count == count(items where severity in
    {high,medium})` and the matching `fyi_count` / `snoozed_count`
    invariants. Companion test
    `test__alerts__snooze_moves_out_of_active_then_clear_restores`
    verifies snooze actually moves the item out of `items[]`. Both
    passing in today's run (425/429 full suite green).
  - Re-creating the reported bug would require breaking the e2e —
    impossible without an obvious test failure.
  - **Lesson for the ledger** — a "kept open for browser smoke" gate
    that's already enforced by a passing e2e on the exact invariant is
    a stale gate. The smoke was meant to catch a divergence the test
    already catches harder; closing on the test alone is sufficient.

## [RESOLVED] FU-020 — Recipe-detail substitute swap affordance (cook-mode-only for now?)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding / open question
- **What:** B8 made substitute swapping a temporary cook-session action (cook
  mode only). The recipe-detail "Find substitutes" dialog is purely
  informational. Open question: should the detail page also let you swap?
- **Resolution (2026-06-26):** **decision — keep cook-mode-only**, no code
  change. User confirmed the current model is intentional. The
  detail-page dialog stays a read-only viewer (with its existing copy
  pointing users to cook mode for the actual swap). Rationale:
  - **Charter tiebreak (Effortless + Anti-creep)** — one swap mechanism
    is simpler than two; the saved recipe stays the canonical artefact.
  - **Clean ownership** — recipe detail = canonical recipe, cook mode =
    this session's swaps. No "pre-staged swap" concept to store / sync.
  - The "I want to plan ahead" use case is small and already covered by
    remembering at cook start; investing in a pre-stage surface would be
    surface bloat for marginal benefit.
  - If the use case ever grows, the cleanest fit is a per-ingredient
    swap dropdown on a **scheduled MealPlanEntry** (not the bare recipe
    detail) — captured here in case it comes back later.

## [RESOLVED] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05; resumed 2026-06-26
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`. The remaining ~289 were
  out of A2's scope (toolbar + "New X" only); this FU captured them as a
  genuine unplanned leftover.
- **Resolution (2026-06-26):** drained to **48** raw `q-btn` across the
  repo. Two passes today (continuing prior session's work):
  - **First pass** (this session, prior turn) — migrated ~17 sites and
    flagged 10 ambiguous ones in place with `// FU-006:` inline comments.
  - **Second pass / wrap-up** — every remaining raw `q-btn` falls into
    the FU's original explicit-exclusion list or a design-decision flag:
    - **3** wrappers (BaseButton, BaseDropdown, BaseSegmented — by design)
    - **17** MyProductsPage (products surface moving to companion app —
      Decision 1, FU's explicit exclusion)
    - **14** DoraChat (its own component; FU's explicit exclusion)
    - **5** q-input `#append` slots (search-clear / copy-to-clipboard pop-
      outs — FU's explicit exclusion)
    - **9** flagged ambiguous sites carrying inline `// FU-006:` comments
      — use a palette tone BaseButton doesn't model (`warning`, `accent`,
      `grey`, Quasar palette `secondary`), a dynamic colour binding
      (`RecipeCard` chef-hat, `ShoppingListDetail` shop-day tone), or
      `type="a"`. These are design calls (extend BaseButton's variant set
      vs accept raw), not mechanical work; the inline markers stay so the
      decision is locatable when someone reworks the surface.
  - The original FU explicitly disposed of itself as "Not no-regret; not
    urgent — opportunistic" — this state matches that disposition.
  - **`CardComponent.vue`** (1 entry in the previous count of 49) was
    confirmed dead/broken and deleted in this session — see FU-311.
  Verification: `vue-tsc --noEmit` clean.

## [RESOLVED] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages were out of BaseButton's
  scope (different APIs); a wrapper would unify split-buttons.
- **Resolution (2026-06-26):** shipped in commit `37608e4` ("Partial
  resolution of FU-005 and FU-006") — **`BaseDropdown.vue`** wraps
  `q-btn-dropdown` (thin pass-through with `no-caps` default) and
  **`BaseSegmented.vue`** wraps `q-btn-toggle`. All 4 dropdown + 6
  toggle call sites migrated. The only files still containing raw
  `<q-btn-dropdown>` / `<q-btn-toggle>` tags are the two wrappers
  themselves — that's where they're supposed to live. Both
  `TriStateFilter.vue` and `settings/DoraSegmented.vue` reference the
  old pattern in code comments only. FU was closed in code but left
  open in the ledger by oversight; flipping now.

## [RESOLVED] FU-223 — pytest verify on stock-location / stock-group clear-flag changes
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** finding — verification gap
- **What:** Same root cause as FU-189c — dev box had only the MS Store Python
  stub so pytest wasn't run in the original session that added
  `clear_stock_location` / `clear_stock_group` flags to `UpdateStockItemRequest`
  (writing the FK columns directly because the relationships are mapped
  `lazy="noload"` and the prior None-assignment was a silent no-op).
- **Resolution (2026-06-26):** verified in this session. `pytest
  tests/e2e/dora_api/test_stock_item_router.py` — **42/42 passing**, no
  regressions on the clear path. The fix held; no test fixture needed
  updating.

## [RESOLVED] FU-189c — Phase E: pytest verify still wanted (urgency lowered)
- **Raised:** 2026-06-18 (Phase E rename close-out)
- **Type:** finding — verification gap
- **What:** Phase E `Merchant → Store` rename + `usual_store_id` + Stores CRUD
  page + image upload landed under `vue-tsc` + `npm run lint` clean, but
  pytest wasn't exercised in the rename session.
- **Resolution (2026-06-26):** verified in this session. Full suite
  **425/429 passing** (`tests/e2e/dora_api` + the two unit test files). The
  4 remaining failures are FU-310 (auth/user `has_image` issue, completely
  unrelated to the rename — confirmed by stash-test on previous turns).
  Direct rename-surface tests are **80/80 green** —
  `test_store_router.py`, `test_product_router.py`, `test_ingestion_sources.py`,
  `test_ingestion_store_mappings.py`, `test_ingest_batch.py`. Stale
  `Merchant` references in the code: none (the surviving "merchant"
  mentions are domain-concept copy in docstrings + Dora chat tool
  descriptions — describing what a Store *holds*, not stale entity
  references). Migration head `f9d3a7c2b5e8` applies cleanly.

## [RESOLVED] FU-209 — Gate reframe: drop `products_enabled`, derive `features.products` from data-presence
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** deferred job (build)
- **What:** Replace the admin/persona `AppSetting.products_enabled` flag with
  a **server-derived** `features.products = (Product.count() > 0)`. Drop the
  column, its admin PATCH field, the DTO field, and the onboarding persona
  dimension; keep every per-surface `v-if="productsEnabled"` gate.
- **Resolution (2026-06-26):** browser-verified after two leak fixes; ledger
  flip. The Phase-A static work (column drop, migration `f1d5b8a2c4e6`,
  health-check derivation, onboarding/DTO removal, test rewrite) had landed
  in the 2026-06-17 session and was confirmed unrotted today —
  `tests/e2e/dora_api/test_onboarding_flags.py` 10/10 passing, single
  Alembic head `f9d3a7c2b5e8`, `vue-tsc` clean.

  **Two browser-pass bugs surfaced and fixed today:**
  1. **`MainLayout.vue` My Products nav unguarded.** The Product Search nav
     entry was correctly gated on `features.products.value`, but the
     literal `base.push({ label: 'My Products', ... })` two lines down
     wasn't — so the nav advertised the surface on a products-empty
     install. Fixed by wrapping the push in `if (features.products.value)`.
  2. **Product search URL setting visible on a products-empty install.**
     `AdminSystemFeaturesSettings.vue` exposed the URL input
     unconditionally. It's part of the products overlay, so it follows the
     same data-presence gate — wrapped the whole `<SettingsSection>` in
     `v-if="productsEnabled"` (added a `productsEnabled` ref from
     `useFeatureFlags`).

  **Full products-surface inventory after the fixes** (all gated on
  `features.products`):
  - `MainLayout` — Product Search nav entry ✓
  - `MainLayout` — My Products nav entry ✓ (today's fix)
  - `DashboardPage` — `best_deals` card (via `isCardVisible('best_deals')`
    → `gate: 'products'`) ✓
  - `StockItemDetailPage` — Products tab header (`tabDefinitions`) ✓
  - `StockItemDetailPage` — Products `q-tab-panel` ✓
  - `AdminSystemFeaturesSettings` — Product search URL section ✓
    (today's fix)

  **Carry-over (not in FU-209's scope, logged separately if needed):**
  - The route `/my-products` itself has no router guard — direct URL /
    bookmark still loads `MyProductsPage.vue` on a products-empty install.
    Proposal §2 said "keep every v-if gate — only the boolean's source
    changes"; locking the route is a separate hardening pass if desired.
  - `doraContextualActions.ts:154` suggests "Hunt for fresh deals" when on
    `/my-products` — dead code on products-off (unreachable), harmless.
- **Standards close-gate:** R-003 (single source of truth) — products is
  one server-derived fact via `/health`; no client-side counting. R-005/
  R-006 — migration `f1d5b8a2c4e6` clean, no idempotent guards, applies on
  PG and SQLite. **ADR candidate:** "data-presence-gated surfaces" pattern
  could be promoted to a new `R-0NN` if a second feature adopts it (e.g.
  ingestion overlays); not yet a recurring decision, hold for now.

## [RESOLVED] FU-311 — Delete dead/broken `CardComponent.vue`
- **Raised:** 2026-06-26 (surfaced by FU-006 q-btn sweep)
- **Type:** finding / dead code
- **What:** `web_app/src/components/CardComponent.vue` had no callers
  (`grep -rn "CardComponent" web_app/src` returned only self-references)
  and contained syntactically broken Vue: `::icon` typo, reference to
  the non-existent `ICONS.icon`, and a stray `fab` prop. Caught during
  the FU-006 q-btn→BaseButton sweep when it appeared in the inventory
  as an unmigrated raw `q-btn` site.
- **Resolution (2026-06-26):** file deleted. `vue-tsc --noEmit` clean
  post-removal — no callers, no orphan imports.

## [RESOLVED] FU-082 — Add `created_at` to Recipe DTO so "Recently added" sort axis can land
- **Raised:** 2026-06-09 (Cookbook Chunk 1; IMPL plan called for the axis)
- **Type:** finding / Phase-2
- **What:** `IMPL_PLAN_COOKBOOK.md` Chunk 1 listed five sort axes including
  `created-at`. Recipe DTO had no created timestamp, so Chunk 1 shipped
  four (`name`, `last_made`, `meal_count`, `total_time`).
- **Resolution (2026-06-26):** shipped end-to-end.
  - **Migration** `f9d3a7c2b5e8_20260626_recipe_created_at.py` — added
    `Recipe.created_at: DateTime(timezone=True)`; nullable add → backfill
    via `COALESCE(last_made_on, CURRENT_TIMESTAMP)` (one portable
    UPDATE) → tighten to NOT NULL. Backfill rationale: legacy rows with
    `last_made_on` keep their relative order; un-cooked legacy rows
    anchor at "now" and newer real creates simply sort above them, which
    matches the axis's "Recently added" intent.
  - **Schema:** `table_mappings.py` + `domain/entities/recipe.py` get
    the new column / field / `Recipe.Fields.CREATED_AT`.
  - **Write paths:** `create_recipe.py` and `new_recipe_version.py` both
    stamp `datetime.now(timezone.utc)` at construction. Seed (`seed.py`)
    accepts a `created_at` kwarg, defaulting to `now()`.
  - **DTO:** `RecipeDto.created_at` (positional, always populated post-
    backfill); `_FIELD_MAP['created_at']` so the standard
    `?sort=created_at:desc` query string works too if the cookbook ever
    moves off client-side sort.
  - **Frontend:** `models/recipe.ts` adds `created_at: string`;
    `RecipesOverview.vue` adds `'created_at'` to `SortKey` +
    STATIC_SORT_OPTIONS (label "Recently added"), a comparator
    (lexicographic on the ISO-8601 string with name tie-break), and the
    asc/desc tooltip phrasing ("Oldest first" / "Most recent first").
    The default-direction watch picks `desc` by exclusion (i.e. newest
    first), matching the rest of the non-name axes.
  - **Tests:** `tests/test_recipe_cookability.py` stub was missing
    `steps_mode` too (pre-existing rot) — fixed both attributes; 22 unit
    tests pass; full e2e suite **403 passed, 4 pre-existing failures
    unrelated to FU-082** (see FU-310). Frontend `vue-tsc` clean.

## [RESOLVED] FU-074 — Wire planned-shop-day into the real alert pipeline (C-9)
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** finding (deferred-by-design)
- **What:** Chunk 7 surfaces planned-shop-day as a banner on the list detail.
  The IMPL plan said it "feeds C-9's new alert types" — the actual alert
  pipeline (alerts bell badge, suggestion-feed insertions, optional push)
  belongs to C-9.
- **Resolution (2026-06-26):** finished in two halves —
  - **Found already-shipped (C-9.4):** the `shopping_day` kind is
    registered in `alert_kinds.py` (FYI tier), emitted by
    `get_alerts.py::_shopping_day_alerts` for not-yet-done lists with
    `planned_shop_date` within `SHOPPING_DAY_WINDOW_DAYS` (3), de-duped
    via `list_alert_key(lst.id, "shopping_day")`, and clears when the
    list flips to `done`. Single-kind design (not the FU's original
    `shopping_day_today` / `shopping_day_overdue` split) — one alert per
    list with message/severity reflecting current state. Cleaner, since
    user snooze/dismiss on a list survives the date rolling forward.
  - **Gap filled in this pass:** the existing emitter only covered
    upcoming dates (`between(today, horizon)`) — overdue lists silently
    dropped out, even though the in-page banner tints overdue. Widened
    the query to `<= horizon` (covers past + upcoming), added an
    `if days < 0` branch that escalates severity to `medium` (still
    FYI-tier, so it doesn't inflate the bell badge — just sorts above
    plain upcoming nudges) and rephrases the message
    ("Shopping day was yesterday: …" / "Shopping day was N days ago:
    …" / detail "Mark it done or move the date."). Same `list_alert_key`
    so user decisions persist across the lifecycle.
  - **Tests:** new
    `test__alerts__shopping_day_overdue_fires_and_escalates_severity`
    covers both the overdue emission (severity=medium, "2 days ago" in
    message, tier=fyi) and the close-on-done behaviour. All 24
    `test_alerts.py` cases pass.
  - **Conftest collateral:** the FU-045 conftest pinned tests to
    `sqlite:///data/dora.test.db` (relative), which Flask resolves
    against its instance dir → `OperationalError`. Switched to an
    absolute path derived from the repo root + `as_posix()` so the e2e
    suite runs without any explicit env var.

## [RESOLVED] FU-071 — Desktop right-panel + mobile-top-dropdown list selector
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX polish per proposal §2.3 / feedback L405-L406)
- **What:** Proposal calls for a desktop **right panel** (always visible) and a
  mobile **top dropdown**. Chunk 5 shipped a single `q-btn-dropdown` shared
  across viewports as a viable interim. The dedicated right-panel layout
  (always visible on >=md, the dropdown collapses below that) is the next step.
- **Resolution (2026-06-26):** already implemented — closing on inspection.
  `ShoppingListDetail.vue` carries both surfaces, mutually exclusive via
  viewport classes:
  - **Desktop right rail** (lines 831–870, `.col-auto.gt-sm /
    .sld-rail`): always-visible `q-virtual-scroll` of every list,
    server-ordered, auto-scrolls to the active selection, with a
    "+ New list" ghost button on top and a "Manage templates…"
    router-link below.
  - **Mobile top dropdown** (lines 161–196, `.lt-md.full-width`):
    `BaseDropdown` hosting the same `railEntries` continuum via
    `q-virtual-scroll`, plus a "+ New list" entry at the top of the
    menu.
  Both use the shared `ShoppingListRailItem.vue` component for row
  rendering. The "single dropdown shared across viewports" interim is
  gone. Work landed in commit `d9ca58e` ("Fable 5 — shopping list
  rework") which introduced `ShoppingListRailItem.vue` and the
  `.sld-rail` layout; FU-071 was never flipped.

## [RESOLVED] FU-045 — Migrate to Postgres as the standard datastore (SQLite kept for lightweight self-host)
- **Raised:** 2026-06-06 (distribution posture — Decision 5 / §7.5)
- **Type:** deferred job
- **What:** Make Postgres the standard datastore for dev + hosted; SQLite stays
  supported as the zero-dependency lightweight self-host option.
- **Resolution (2026-06-26):** shipped the productionize switch.
  - **Driver:** added `psycopg[binary]==3.2.3` to `requirements.txt`
    (self-contained, no libpq required).
  - **Local Postgres:** new `docker-compose.yml` at repo root with a
    `postgres:16-alpine` service on `localhost:5432`, user/pass/db all
    `dora`, healthcheck wired. Default app config matches this service
    out of the box.
  - **Config resolution** (`configuration_manager.py`): rewrote
    `get_db_connection_string()`. Order: (1) `DORA_DB_URL` override —
    any SQLAlchemy URL, including `sqlite:///path/to/db` for SQLite
    self-host; (2) per-component env vars `DORA_DB_HOST` / `_PORT` /
    `_NAME` / `_USER` / `_PASSWORD`; (3) default to the docker-compose
    Postgres. Removed `_resolve_db_path` + the `DORA_DB_PATH` env var
    (collapsed into `DORA_DB_URL` per pre-release scope discipline; no
    compat shim).
  - **Startup guard** (`startup.py`): `migrate_legacy_db` (SQLite file
    relocation) now only runs when the resolved URL starts with
    `sqlite:///`. PG path skips it cleanly.
  - **Portable boolean defaults** — the SQLite-only `sa.text('0')` /
    `sa.text('1')` pattern is now extinct. Swept:
    - `table_mappings.py` × 24 — `Boolean, server_default="0"` /
      `="1"` → `server_default=false()` / `true()` (imported `false`,
      `true` from `sqlalchemy`).
    - 8 migration files × 12 sites — `sa.text('0')` / `sa.text('1')`
      → `sa.false()` / `sa.true()`. Renders `0`/`1` on SQLite and
      `false`/`true` on PG — portable both ways. Existing SQLite DBs
      unaffected (same DDL emitted).
  - **Raw-SQL boolean comparison** (`get_recipes.py:594`):
    `AND p.is_active = 1` → `AND p.is_active` (bare boolean predicate
    works on both engines; PG would reject `boolean = integer`).
  - **Tests** (`tests/e2e/dora_api/conftest.py`): pin the e2e suite to
    a SQLite temp file (`sqlite:///data/dora.test.db`) via
    `os.environ.setdefault("DORA_DB_URL", ...)` at module top, before
    `dora_api.app` import. Tests stay zero-dependency and don't
    require a running Postgres.
  - **Docs:** `README.md` quickstart now leads with
    `docker compose up -d postgres`; SQLite fallback documented via
    `DORA_DB_URL=sqlite:///...`. `path_migration.py` docstrings
    updated for the new env var.
  - **Verified:** `drop_all + create_all` clean on SQLite with the new
    defaults; introspected DDL confirms `is_admin`/`deals_email_enabled`
    /`show_recipe_images` defaults all rendered correctly. All
    migrations py_compile clean.
- **Carry-over** (not blocking the close):
  - **Live PG run** — only the user can confirm `docker compose up -d
    postgres && flask db upgrade && python -m dora_api.startup` boots
    cleanly end-to-end on this host. Recommended browser smoke after.
  - **Raw `text()` queries with UUID binds** — already used `str(uuid)`
    on the bind side (works on both engines) and `_coerce_uuid` on
    the return side (accepts `UUID|bytes|str`, so portable). Worth a
    confirm on real PG that no driver-specific casting surprises us
    (psycopg returns native UUID, SQLite returns bytes — both handled).
  - **Postgres CI lane** is not part of this change; if you want one,
    spin a follow-up.

## [RESOLVED] FU-023 — A5 leftover: spinners not yet migrated on deferred surfaces
- **Raised:** 2026-06-05 (A5)
- **Type:** leftover
- **What:** A5 unified loading on the active app pages, but left raw `q-spinner`
  on the **deferred surfaces** (Reports, Data→Export/Print, Settings sub-pages —
  per the prompt-pack "deferred" list) and on **DoraChat's typing dots** (a
  deliberate `q-spinner-dots` indicator).
- **Resolution (2026-06-26):** swept all 19 raw `q-spinner` / `q-spinner-dots`
  sites in app code. Migrated to `AppSpinner`:
  - Settings sub-pages — `RecipeDietaryTagsSettings`, `StockLocationsSettings`,
    `StockGroupsSettings`, `UsersAdminSettings`, `ApiAccessSettings`,
    `AdminSystemAssistantSettings` (the dots indicator there switched to
    `AppSpinner` for A5 consistency — distinct from DoraChat's typing
    dots, which stay).
  - Settings components — `VocabListEditor`, `VoicePicker` (×2 small
    inline sites).
  - Reports — `ReportsPage` ×6 (one per chart card's loading state).
  - Data → Export/Print — `ExportPrint` ×2.
  - Dora — `PriceHistoryBottomSheet` (chart load).
  - **DoraChat.vue:270 `q-spinner-dots` kept** as the intentional typing
    indicator per the FU note.
  Final inventory: only `AppSpinner.vue`'s own internal `<q-spinner>`
  and `DoraChat`'s typing dots remain. `vue-tsc --noEmit` clean.
- **Carry-over (out of scope here):** the FU also mentioned list-skeletons
  as a nicer touch on big overviews; that's still a polish-pass call,
  folded into FU-010 (holistic look review). Not a new follow-up — the
  spinner migration itself is now done.

## [RESOLVED] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Resolution (2026-06-26):** sweep run. Composables that toast
  internally: `useStockItemActions` (addToList/markRestocked/pushExpiry),
  `useShoppingListActions` (addItems/removeFromList/removeFromAllLists/
  finishShopping), `useMealPlanner` (~17 sites), `useRecipeExport`,
  `useStockOverviewExport`, plus the three infra composables
  (`useNetworkStatus`, `useOfflineQueue`, `usePwaLifecycle`). Pinia
  stores: **no internal notifies anywhere** (confirmed by grep). Walked
  every caller of every notifying composable — **no double-toast
  double-emits found**: not a single caller adds its own success toast
  after a composable success notify. B7's worry doesn't recur.

  **Adjacent finding fixed in the same pass:** `StockOverview.bulkAddToPrimary`
  and `StockOverview.bulkRestock` were `for…await`ing the single-item
  composable methods, so a bulk selection of N items fired N per-item
  toasts ("Added to list.", "Marked restocked." × N). Not the audited
  "double-emit" pattern per se, but the same family. Fixed by adding an
  optional `{ silent?: boolean }` flag to `addToList` and `markRestocked`
  in `useStockItemActions.ts`; the two bulk handlers now pass `silent:
  true` and emit one summary toast ("Added N items to your list.").
  `vue-tsc` clean.

## [RESOLVED] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel was a plain div. StockOverview had
  grown a page-scoped `:deep(.filter-bar__panel)` treatment (surface-elevated
  card + 1px inset tint border + 8px radius) to pair with its bulk-select
  banner, but RecipesOverview and MyProductsPage still rendered the panel
  bare — inconsistent across the three FilterBar consumers.
- **Why deferred:** the other pages never had a container; whether the panel
  wanted subtle containment was a design call.
- **Resolution (2026-06-26):** moved styling onto `FilterBar.vue` itself
  (`<style scoped>`) so every consumer picks it up. Switched to a calmer
  **sunken well** treatment — `background: var(--surface-sunken)` + 6px
  radius, no border — instead of an elevated card. Reads as a recessed
  tool tray tucked under the toolbar rather than another card on an
  already-card-heavy page, and works on pages without a paired bulk
  banner. StockOverview's `.dora-subbar` (bulk banner) re-tuned to the
  same sunken treatment so the two sub-bars still feel like siblings;
  its previous `:deep(.filter-bar__panel)` overrides removed.
  `vue-tsc` clean.

## [RESOLVED] FU-011 — AuditLogSettings filtering not standardised
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `settings/AuditLogSettings.vue` has ~9 filter fields with its own
  apply/clear UX. A4 deliberately did not touch it (the prompt scoped A4 to the
  four data-list pages and excluded the deferred/settings pages); its filtering
  is also server-side (sends a query), not the client-predicate pattern FilterBar
  assumes.
- **Why deferred:** out of A4's defined scope; different (server-side) mechanism.
- **Recommended resolution:** later — only if settings/admin gets a dedicated
  polish pass; low priority.
- **Resolution (2026-06-26):** no action needed. (1) The A4 "FilterBar"
  target no longer exists as a component — `web_app/src/components/filters/`
  contains only `TriStateFilter.vue`, so there is nothing to standardise
  onto. (2) `AuditLogSettings.vue` has since been folded into the
  standardised settings shell through the Settings rebuild + subsequent
  passes (uses `SettingsPageHeader`, `BaseButton`, `BaseDialog`, the
  `settings-page` layout, `settings-divider`, and theme tokens — same as
  every other settings sub-page). (3) The original deferral note already
  pointed out that the filtering is server-side and therefore a poor fit
  for a client-predicate FilterBar; that reasoning resolves rather than
  defers the FU now that the rebuild has happened.

## [RESOLVED] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Resolved (2026-06-26):** dropped the `palette: { … }` field from all 10
  `THEMES` entries in `themeService.ts`. `applyThemeKey` now sets
  `data-theme="x"` first, then `syncQuasarPaletteFromCssVars()` reads the
  active values back via `getComputedStyle(documentElement).getPropertyValue`
  and pushes them into Quasar's `--q-*` palette via `setCssVar`. The
  bridge map `QUASAR_PALETTE_FROM_CSS_VAR` is the only place the
  TS→SCSS coupling lives now — and it's by *key name*, not by hex value.
  Single source of truth = `css/themes.scss`. `ThemePalette` interface kept
  (used by `helpers/stockLevelLogic.ts` via `nameOf<>` as a compile-time
  key-set contract). Removed ~140 hex strings from the TS file; vue-tsc +
  eslint clean. Adding a new theme is now a 1-step change (SCSS block +
  picker-metadata row in `THEMES`; no palette values).

---

## [RESOLVED] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Resolved (2026-06-26):** folded into the **C-19 (shared auth-shell)**
  prompt scope in `docs/03_prompts/C_big_rock_design_briefs.md`. The note
  about the lp-* ladder + the keep/promote decision now lives inside that
  prompt's body, so whoever runs C-19 sees it without needing a separate FU
  pointer. No code touched; the ladder stays as-is until C-19 runs.

---

## [RESOLVED] FU-122 — Browser-verify Stock Overview Chunk 3 (row rebuild + image toggle)
- **Raised:** 2026-06-12 (Stock Overview Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Row layout** reads left→right: bulk-checkbox (when in bulk mode)
     → coloured level square → name (bold) + zone (inline) → image
     placeholder (if `show_stock_images` is on) → ... → expiry → #recipes
     (when >0) → open/in-use → cart.
  2. **Level button** click opens the picker; selection updates the
     row's colour immediately (optimistic).
  3. **Zone** is clickable and filters the list to that location.
  4. **Status outline:** healthy row has no coloured border; an item
     expiring within 7 days gets an amber border; "Out of Stock" or
     expired items get a red border AND dim. Cross-theme check
     (Pesto light/dark, Cherry Cola dark — colours come from
     `--q-warning` / `--q-negative`).
  5. **Selection fills the row** (light primary tint) when bulk-mode
     selected; the splitter-peek state still draws its own solid
     outline; focus still draws the dashed accent outline.
  6. **Image toggle** at the top right flips between image / image-off
     icon; the row's image slot disappears when off and the row
     becomes visibly denser; reload-survives (server PATCH /me).
  7. **No regressions:** chip-shaped StockItemChip is GONE from rows
     but still renders on shopping-list lines + the stock-item
     detail page. "On N lists" chip is gone. The cart button still
     adds the item to the active draft list (C-7 will replace this
     properly later).
  8. **Virtualised list** still works after the row-size change — the
     `VIRTUAL_SCROLL_ITEM_SIZE = 72` constant in StockOverview.vue
     may need a tweak if rows feel too compact/spacious; q-virtual-
     scroll self-corrects after the first measure but tune the hint
     to match what you see.
- **Why:** static-only impl. Row rebuild is the biggest chunk of the
  plan; cross-theme + cross-state checks are the highest-risk
  verification. The image toggle is the FU-106 surface and needs an
  end-to-end PATCH /me confirmation.
- **Resolved (2026-06-26):** user confirmed the row layout, level picker,
  zone filter, status outlines, bulk selection fill, image toggle (incl.
  PATCH /me persistence), no chip regressions, and virtualised list all
  behave as specified in the browser. No defects logged.

---

## [RESOLVED] FU-293 — DashboardPage R-001 de-monolith (DashboardCard extraction)
- **Raised:** 2026-06-24 (Dashboard rebuild, deferred across Phases 0–7).
- **Type:** finding (R-001 — componentisation).
- **What:** `DashboardPage.vue`'s 15 inline card shells repeated the same
  `<article/router-link class="dora-card"><header class="dora-card-head">…`
  boilerplate; the shell SCSS lived in the page.
- **State note (resolved 2026-06-24):** extracted
  `web_app/src/components/dashboard/DashboardCard.vue` — a shell that renders a
  `<router-link>` when `to` is set (whole-card nav) or `<article>` otherwise,
  with `icon`/`title` props (+ `#title` slot for rich titles like cookable's
  count), an `#action` header slot, and the body default slot. All 15 card
  instances converted to `<DashboardCard>`. Moved the shell styles
  (`.dora-card*`, head/icon/title/action/link/clickable + hover + reduced-motion)
  into the component, using the **global** theme tokens directly (not the page's
  private `--c-*` aliases, which scoped child styles can't inherit); the action/
  link styling uses `:deep()` since the `#action` slot content carries the
  parent's scope. Card BODY SCSS stays in the page (slotted content keeps parent
  scope). `vue-tsc` + `eslint` green. **Visual no-regression check folded into
  FU-301** (the extraction's only residual risk is CSS, browser-verifiable).

## [RESOLVED] FU-232 — Companion / ingestion contract: push `pack_count` on Product
- **Raised:** 2026-06-23 (FU-227 multipack follow-up).
- **Type:** deferred job.
- **State note (resolved 2026-06-23):** wired through in
  `dora_api/features/ingestion/submit_ingestion_batch.py`. Added
  `pack_count: int | None = Field(default=None, gt=0)` to `_ProductIn`;
  threaded through both `_apply_product` paths (`existing.pack_count =
  raw.pack_count or existing.pack_count` for update; `pack_count=raw.pack_count`
  on create). Docs updated: `INGESTION_GUIDE.md` (new row in the products
  table with the "size_value is the total across the bundle" note) +
  `PROPOSAL_INGESTION_API.md` (catalogue field list + §2.2 payload sketch).
  New pytest `test__ingest__pack_count_round_trips_on_product` in
  `tests/e2e/dora_api/test_ingest_batch.py` asserts create-with-pack,
  no-overwrite-on-null-republish, and `gt=0` rejection. Static-only —
  needs a Python env to run (no env on this machine).
- **What:** the in-app side of multipack pricing is wired — observations now
  carry `pack_count`, the PriceEntry widget exposes it as a disclosure
  ("Add pack count (multipack)"), the obs list renders "4 × 125g", and the
  harvest path at `/finish` reads `Product.pack_count` to populate it. But
  **the producer-facing contract still doesn't accept pack_count.** The
  `_ProductIn` model in `submit_ingestion_batch.py` accepts
  `{size, size_unit, size_value}` but not the new column. Producers that
  want to push "Activia 125g × 4 pack" today must flatten `size_value=500`
  (the existing convention — `size_value` is the TOTAL across the bundle)
  and lose the structured pack-context.
- **Why deferred:** the schema column is in place
  (migration `d7b3e8f2a5c4`) and the existing user-side surfaces work
  without the producer push (default = NULL). The contract change is its
  own piece of work — needs producer-side coordination, doc updates,
  acceptance test for the field round-trip, decision on whether to also
  accept multipack metadata on `offers[]` or just `products[]`.
- **Recommended resolution:** when the next companion / ingestion-contract
  work lands. Add `pack_count: int | None = Field(default=None, gt=0)` on
  `_ProductIn`; thread it through the upsert in `_apply_product`; update
  `INGESTION_GUIDE.md` and `PROPOSAL_INGESTION_API.md` to document the
  field; add a pytest asserting it round-trips on the Product row.

## [RESOLVED] FU-180 — Reassess "preferred product" before commercialise (Phase 4)
- **Raised:** 2026-06-14 (preferred-product removal sweep)
- **Type:** open decision
- **State note (resolved 2026-06-23):** closed fully. The product-side intent
  is met by **`PreferredBuy`** (free-text per stock item, FU-211) plus
  **`StockItem.usual_store_id`** (per-item store, FU-189 Phase E) — together
  they cover "remember my favourite product" + "where I usually buy this"
  without resurrecting the deleted per-item enum. The residual app-wide
  preferred-*store* question (one annotation that sorts/pre-selects across
  all items) is **not worth carrying as an open FU**: cheapest-first sort +
  per-item `usual_store_id` already cover the practical case, and an
  app-wide layer is cheap to add later if real usage demands it. The
  onboarding preferred-stores capture (feedback L45, folded in 2026-06-15)
  is dropped on the same grounds — no capture step in onboarding; users can
  set `usual_store_id` opportunistically as they shop. Original spec L66 /
  Unprocessed-Ideas #48/49/52 stay parked in `00_original_spec` as
  historical intent; no rebuild planned.
- **What:** `StockItem.preferred_product_id` was removed end-to-end this
  session — column dropped, two sort orders degraded to `cheapest → name`,
  barcode lookup collapsed to the m2m fallback, stock-value report rebased on
  cheapest most-recent linked-product price. The original concern was your
  own (feedback L131 — "Not sold... fluff vs noise"), and the manual per-item
  annotation never earned its keep at this stage of the build. **Open
  question:** once the rest of the app is built out (and the cart-button
  picker, shop-mode, and stock-value report have real usage data), revisit
  whether a "preferred *product*" or "preferred *merchant*" affordance is
  worth adding back. The original spec wanted preferred *store/merchant*
  (Feature Board L66, Unprocessed-Ideas #48/49/52) — a different shape from
  the per-product field we deleted, and arguably more defensible because one
  merchant choice would travel across all products from that merchant.
- **Why deferred:** the existing design instinct (cart-button proposal open-Q
  2: "always show the picker; preferred only pre-selects") means even a
  rebuilt preferred only changes *order*, not *behaviour* — which cheapest-
  first already does for free. Only worth revisiting if real usage shows
  users wanting to express brand loyalty / size preference / allergen
  avoidance and the current sort isn't getting them there.
- **Recommended resolution:** later — end of app build (Phase 3 polish or
  the first Phase 4 commercialise pass). Inputs to weigh: (a) any signals
  in feedback that users wished they could pin a specific product; (b) the
  cart-button picker's actual UX with cheapest-first sort; (c) whether a
  preferred-*merchant* model (one annotation, app-wide) earns its keep
  better than the per-stock-item preferred-product we just deleted.
- **Update 2026-06-15 (C-5 onboarding design):** the onboarding **preferred-stores**
  capture (feedback L45) was **dropped** and folded into this reconsideration — per the
  user, it's the same uncertain bucket (stock-items-only friction + whether the companion
  app ships, which would otherwise force custom/receipt product entry). So this FU now also
  owns: **does onboarding ever capture preferred stores/merchants, and what would they
  do** — revisit alongside the preferred-product question when the cart/companion surfaces
  make a merchant preference earn its keep. (Merchant currently has only `name`; no
  `is_enabled`/`preferred` field exists.)
- **Update 2026-06-17 (products-as-overlay pivot):** the everyday "remember my favourite products"
  intent is now met by **`PreferredBuy`** (free-text, on the stock item — FU-211), distinct from
  the *preferred-merchant* sort/loyalty question this FU still owns. So the product side of this
  reconsideration is largely addressed by PreferredBuy + `usual_store_id`; what remains open is
  whether a preferred-*store* affordance (sort / pre-select) earns its keep.

## [RESOLVED] FU-227 — Pricing system reassessment: "Your prices" intelligence (8 chunks shipped)
- **Raised:** 2026-06-19 (pricing reassessment handoff).
- **Ratified:** 2026-06-22 — the §6 question list A–K fully walked with the user;
  all answers, revisions, and clarifications LOCKED.
- **Type:** planning + implementation (Phase F's "Your prices" / S2-10 build).
- **State note (resolved 2026-06-22):** all 8 chunks landed. Chunk 1 — unit-
  conversion helper + count dim + SPA mirror dedup. Chunk 2 — observation
  reshape (folded shape, store_id, FK provenance, partial UNIQUE) + migration
  `c6e9a4b8d5f2`. Chunk 3 — shared `PriceEntry` + row-overview button + inline
  `YourPricesWidget` on stock-item detail. Chunk 4 — `build_your_prices_for_item`
  (median / 1.15× strict-greater / min-3 / trailing 12mo / per-dim B4 / LC-2
  source-blind / offers sidecar). Chunk 5 — shopping-line prefill +
  `/finish` harvest + I1 Receipt relabel + K2 ladder extract + E3
  PATCH-status-done removal. Chunk 6 — `PriceHistoryBottomSheet` (C5b)
  + per-product observation overlay (H2 fallback) + baseline reference
  line (F-3) + D2 colour-coding. Chunk 7 — removed the `stock_item_ref →
  observation` ingestion branch (J1) and trimmed `price_observations[]`
  from the contract entirely. Chunk 8 — promoted seed-data discipline to
  **R-017** in `ENGINEERING_STANDARDS.md` + ADR-012; filled the feedback
  coverage table in the plan; updated `COVERAGE_GAPS.md` audit log
  (flipped L226/L419/L420 to ADDRESSED); moved this entry to resolved.
- **What it left behind:** **R-017** (new standing rule, every future
  feature-touching prompt picks it up automatically). FU-228 (Phase E
  rename test rot — pre-existing, surfaced by the chunk-1 full-suite run).
  FU-229 (`reports.py` spend-by-store ignores `actual_unit_price` — surfaced
  during the K2 ladder extract). FU-230 (offers-sidecar noload —
  fixed in chunk 6, still wants a browser confirm). FU-231 (chunk 5 status=done
  test fallout — fixed in chunk 6). The browser walk of the C5 state matrix
  is the user's at the close-gate.
- **Plan doc:** `docs/04_proposals/IMPL_PLAN_YOUR_PRICES.md` (the 8-chunk
  spec) — feedback coverage table (§5) filled at chunk 8.
- **Handoff doc:** `docs/99_scratch/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md`
  — the source of truth for every ratified decision (§6 / §6a / §6b /
  LC-1..LC-5). Keep for audit; future reassessments cite it.

## [RESOLVED] FU-225 — Deprecate `PreferredBuy.position` + reorder endpoint
- **Raised:** 2026-06-18 (Stock-pages feedback round 3)
- **Type:** deferred job
- **What:** Round-3 dropped the manual reorder UI on preferred buys (SPA now
  sorts alphabetically client-side). The backend still carried the `position`
  column on the table and exposed `PATCH /stock-items/{id}/preferred-buys/reorder`
  + `stockItemApi.reorderPreferredBuysAsync` on the SPA's API service. Nothing
  called them anymore.
- **State note:** 2026-06-18 — Dropped end-to-end. Backend:
  `PreferredBuy.position` removed from the entity, table mapping, and detail
  DTO; sort is now alphabetical (case-insensitive label) server-side, matching
  the SPA. The `reorder` route + handler method gone. New Alembic migration
  `b5d8a2f4c9e7_20260618_drop_preferred_buy_position.py` drops the column.
  SPA: `reorderPreferredBuysAsync` removed from `stockItemApiService`,
  `position` removed from `PreferredBuy` in `models/stockItemDetail.ts`.
  vue-tsc + lint clean. **Pytest not run (same standing posture as FU-189c /
  FU-223 — bundle on the next Python-equipped session).**

## [RESOLVED] FU-189b — Charter coverage table for Stores CRUD + image upload page
- **Raised:** 2026-06-18 (Phase E rename)
- **Type:** doc gap
- **What:** Phase E landed without flipping the per-surface feedback-coverage
  rows in `PROPOSAL_PRODUCTS_AS_OVERLAY.md` for the now-built Stores admin
  page.
- **State note:** 2026-06-18 — Flipped L184 ("Link button as merchant logo")
  from TRACKED → ADDRESSED, citing the user-uploaded `StoreLogo` with
  hash-swatch fallback rendered on ProductChip / StockItemDetailPage linked-
  products / MyProductsPage / Stores admin grid. L157 (the parallel "merchant
  vs data-provider conflation" row) was already ADDRESSED in the same table.
  No code change — proposal-doc edit only.

## [RESOLVED] FU-024 — A7 leftovers: dead banner CSS + wider footer adoption
- **Raised:** 2026-06-05 (A7)
- **Type:** leftover
- **What:** (a) Removing StockOverview's summary banner left its scoped
  `.stock-summary-banner` / `.stock-summary-stat` CSS unused (harmless dead
  rules). (b) `PageCountsFooter` is only wired on the 3 prompt pages
  (StockOverview, RecipesOverview, MyProductsPage); other list pages
  (ShoppingLists, MealPlans, etc.) could adopt it for consistency.
- **Why deferred:** dead CSS is harmless; broader adoption was out of A7's
  defined scope (3 pages).
- **State note:** 2026-06-18 — Deleted the dead `.stock-summary-banner` /
  `.stock-summary-stat` rules from `web_app/src/pages/StockOverview.vue`'s
  scoped style block (about a dozen lines). vue-tsc + lint clean. The
  "wider footer adoption" half is dropped — opportunistic and the user no
  longer wants it tracked; will surface naturally as the other list pages
  get touched.

## [RESOLVED] FU-113 — Browser-verify C-cross Chunk 4 (location-display policy)
- **Raised:** 2026-06-11 (Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. Open Stock Overview. A stock item assigned to e.g.
     **Pantry → Middle shelf → Left side** now shows **"Pantry"** on
     its location chip (zone-only). Hover the chip → tooltip reads
     *"Pantry › Middle shelf › Left side · Filter to this location"*.
  2. A stock item assigned only to **Pantry** (zone, no sub-area) →
     chip reads *"Pantry"*; tooltip is just *"Filter to this
     location"* (no path prefix because there's no sub-detail to
     reveal).
  3. **Click the chip** — filters the overview to that location.
     Filter still uses the underlying `stock_location_id`, no
     regression.
  4. Open a stock-item detail page. The Location row in the header
     panel reads as the zone (or `—` if unset). Hover → tooltip
     reveals the full breadcrumb when one exists.
  5. Open a shopping-list detail. Each line's `place`-icon location
     reads the zone only. Hover → full breadcrumb tooltip.
  6. **Start shop mode** on a list with lines spread across
     sub-areas under the same zone (e.g. two Fridge lines under
     "Crisper" + one under "Top shelf"). Confirm:
     - The section label above the current item shows the **zone**
       ("Fridge"), not the sub-area.
     - The hover tooltip on the section label shows the full path
       for the current line.
     - The **shop order still splits the two sub-areas apart** —
       crisper items aren't interleaved with top-shelf items just
       because they share the zone (sortKey discipline still uses
       the full breadcrumb).
  7. Open RecipeCookMode. The ingredient group headers continue
     to show zone-only (this hasn't changed) — confirm no
     regression. Per-row location chips don't render in cook
     mode, so there's no chip tooltip to test there.
  8. Cross-theme sanity (Pesto Light + Pesto Dark + Cherry Cola
     Dark) — tooltips read in all three.
- **State note:** 2026-06-18 — Marked resolved by user request. The
  location-display policy has been live since the Chunk-4 ship and the
  surrounding feedback rounds (Stock Overview row, detail-page picker,
  CreateStockItemDialog) have all exercised the zone-vs-full-path code
  paths without regression. User has been operating the app and is
  satisfied.

## [RESOLVED] FU-219 — Companion FE — port `ProductSearch.vue` + `MerchantsSettings.vue` into `../dora-companion`
- **Raised:** 2026-06-17 (Phase C build)
- **Type:** deferred job (port — sibling repo)
- **What:** The companion's headless scrape → `POST /api/push` → Dora's `/api/ingest`
  round-trip landed in Phase C.2; the browsable UI was deferred. FE was needed to host the
  scraper provider toggles + a product-search UI that pushes per-card or in batches.
- **State note:** 2026-06-17 — **RESOLVED.** Scaffolded a Vue 3 + Quasar + Pinia SPA in
  `../dora-companion/web_app/`: Vite + TS (no Quasar CLI — lighter than Dora's tooling). Three
  pages: **Product search** (full port of Dora's `ProductSearch.vue` — search input, merchant
  chips, filters, sort, comparison-style selection — with the Dora-only branches **stripped**
  (saved-product, link-to-stock-item, quick-add) and **per-card + batch "Push to Dora"**
  added); **Merchants** (port of `MerchantsSettings.vue` — list, enable/disable, provider
  health, health-check); **Dora target** (read-only — friendly label only; the real URL +
  bearer live in the BE env). Two services: `MerchantsApiService` (collapses Dora's two
  split clients) and `ProductSearchApiService` (search + push). Push results dialog surfaces
  Dora's per-record `accepted / skipped / failed`; pending store-mapping nudges the user back
  to Dora's API access page (FU-190 honoured end-to-end). New `MerchantsApiService.pushAsync`
  hits the companion's `POST /api/push` which then scrapes + forwards to Dora's
  `POST /api/ingest`. Mapi CORS now allowlists `http://localhost:5175` in dev. Build green:
  `npm install` (226 packages), `vue-tsc --noEmit` clean, `vite build` clean (~82 KB main
  gzipped). README updated. Phase C now fully done (.1 + .2 + .3).

## [RESOLVED] FU-212 — Power-user docs: how to source product data so the overlay lights up
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** documentation
- **What:** Document the path to *enabling* products for power-users (the end-user flow never
  meets this): the always-accessible API access page, the `POST /api/ingest` contract, the
  no-auto-create-stores mapping (FU-190), the data-presence gate, the Product Search URL.
- **State note:** 2026-06-17 — **RESOLVED.** Added `docs/INGESTION_GUIDE.md` covering: (1) what
  lights up when product data is present (My Products / Price History / per-stock-item Products
  tab); (2) minting a key on Settings → API access (one-time reveal, label, disable/revoke);
  (3) the store-mapping pre-map vs auto-quarantine flow; (4) the full `POST /api/ingest`
  contract (auth, Idempotency-Key, products/offers/price_observations schemas, dedupe keys,
  result DTO with stable `reason` codes); (5) the Product Search URL carve-out (data-gated,
  producer unnamed); (6) trust tiers. Index entry added to `docs/00_DOCS_INDEX.md`.
  Producer/companion deliberately **never named** anywhere in the doc — phrasing is
  "any external source you run". Power-user oriented (admin/help), not onboarding-facing.

## [RESOLVED] FU-217 — Refactor `create_product` to share the offer-append mapping (C-10 follow-on)
- **Raised:** 2026-06-17 (Phase B build; PROPOSAL_INGESTION_API §6.2)
- **Type:** deferred job (refactor)
- **What:** `POST /api/products` (`create_product.py`) used to 409 on a duplicate without
  appending a historic point, so manual product-add didn't accrue price history. R-003 violation
  by way of `/api/ingest` having its own append path.
- **State note:** 2026-06-17 — **RESOLVED.** `create_product` now calls
  `apply_offer_to_product` (the C-10.2 shared helper) when the product already exists: appends a
  new `ProductHistoricOffer` + moves `current_offer` instead of returning 422. Idempotent — the
  same (product, observed_at, price_now) tuple still dedupes. Response now returns 201 with
  `{id, created, offer_appended}` (was `id` only); the existing successful-create test still
  passes (the body is a superset), and the dup-409 test was rewritten to assert append (FU-217
  test in `test_product_router.py`). Source string `"manual"` distinguishes these points from
  ingest-provenance points. Full pytest 401/401, `vue-tsc` + lint clean.

## [RESOLVED] FU-178 — Full-chain SQLite `flask db upgrade` is broken (batch-mode constraint naming) — prod-SQLite boot blocker
- **Raised:** 2026-06-14 (surfaced by C-2.K's scratch-DB migration check)
- **Type:** finding (pre-existing defect; **blocked fresh SQLite prod boot**)
- **What:** Running the migration chain base→head on a fresh SQLite DB failed at
  **`d7c9e4a8c2b1_20260612_shopping_list_line_product_anchor.py:29`** —
  `with op.batch_alter_table('ShoppingListLine')` raised
  **`ValueError: Constraint must have a name`**. Alembic batch mode on SQLite
  recreates the table and re-adds its constraints; with no `naming_convention`
  configured, anonymous constraints couldn't be reproduced. Suspected several
  later batch migrations shared the issue (`b9e5c2a78f31`, the FU-163
  `drop_finish_snapshot` batch op, …); the chain just died at the first.
- **State note:** 2026-06-17 — **RESOLVED via hard cutover (pre-release, no
  prod data to preserve).** Added `NAMING_CONVENTION` to `dora_api/app.py` and
  attached it to the SQLAlchemy `MetaData`; threaded it into Alembic's
  context in `dora_api/persistence/migrations/env.py`; **wrapped
  `op.batch_alter_table` in `env.py`** so every batch op inherits the
  convention without each call site having to pass `naming_convention=`.
  Promoted to standing rule **R-015** + **ADR-010** in
  `docs/01_charter/ENGINEERING_STANDARDS.md`. **Verified:** fresh SQLite
  `flask db upgrade base→head` now runs the entire chain clean to head
  `c4e6a8b1d3f5`; full pytest 381/381 still green. Downgrade-from-head to
  base still trips on a handful of legacy migrations that hard-coded
  `ck_*`-prefixed literal names (double-prefix under the convention) —
  **accepted**; downgrade-from-head is not a product flow (dev resets go
  through `drop_all`/`DORA_ALLOW_DESTRUCTIVE`, prod hasn't shipped). Future
  migrations follow R-015 (bare-suffix literals only).

## [RESOLVED] FU-182 — Treat the minimal/Products-off user as a first-class workflow
- **Raised:** 2026-06-14 (talk-time assessment); refined 2026-06-15; promoted to proposal
  2026-06-15 (`docs/04_proposals/PROPOSAL_SIMPLE_MODE.md`).
- **Type:** open decision / design follow-up
- **What:** Treat "Products off" / the minimal user as a first-class workflow via the
  `products_enabled` flag + a per-surface sweep, with "Simple mode" as a named identity and a
  Money×Products 2×2 that onboarding personas had to reach all four corners of.
- **State note:** 2026-06-17 — **SUPERSEDED** by `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md`.
  The premise changed: Products is no longer a user-set flag / persona / "mode" but a
  **data-presence overlay** (on iff product data is ingested), with no user toggle and no
  onboarding persona — so "Simple mode as an identity" and the 2×2 onboarding problem dissolve
  (the everyday experience *is* the app). Surviving pieces (the price substrate, `usual_store_id`,
  the price-entry surfaces) are carried into the new proposal; the implementation is re-tracked as
  its build chunks: **FU-209** (gate reframe), **FU-210** (onboarding de-persona), **FU-211**
  (PreferredBuy), **FU-213** (price substrate). FU-189/FU-190 remain prerequisites and stay open.

## [RESOLVED] FU-185 — Stock Item Detail recipe-tab actions are dead (B8 residue)
- **Raised:** 2026-06-15 (C-1b design — Explore sweep)
- **Type:** finding / bug
- **What:** On `StockItemDetailPage.vue`, `RecipeCard` **emits** `@toggle-favourite` +
  `@add-all-to-list` but the detail page **doesn't listen** to them (only `@open`/`@cook`/
  `@add-missing` are wired). So "remove from favourites does nothing" (feedback L132) and most
  recipe actions beyond Cook (L134) are dead on this surface. Recipe-row navigation IS fixed.
- **Why deferred:** found during the C-1b design sweep; **homed in C-1b.4** (wire the listeners)
  but C-1b isn't built yet. Static read confirms the handlers are missing.
- **Recommended resolution:** fix in **C-1b.4** (Recipes-tab chunk); until then it's a live defect
  — **confirm in browser** that favourite-toggle/add-all are dead, then wire them. Cites B8.
- **State note:** 2026-06-16 — wired both listeners on `StockItemDetailPage.vue` in **C-1b.4**.
  `@toggle-favourite="onToggleFavourite"` mirrors `RecipesOverview` (calls
  `recipeStore.toggleFavouriteAsync`). `@add-all-to-list="onAddAllToList"` collects the recipe's
  ingredient stock-item ids and pushes them via `slActions.addItems` to the inferred primary draft
  (lightweight path; the richer per-ingredient picker stays in `RecipesOverview`). Browser
  verification of the fix rolls up under FU-202 (now extended for the C-1b.4 acceptance).

## [RESOLVED] FU-201 — Production frontend build is broken (4 lint errors gate it)
- **Raised:** 2026-06-16 (senior/tech-lead review — `docs/99_scratch/SENIOR_REVIEW_2026-06-16.md`)
- **Type:** finding (ship-blocker)
- **State note (2026-06-16):** **resolved** — removed the 4 dead symbols
  (`useStockFilters.ts` `stockLevelName` + `recipesByStockItem`, which also orphaned
  `stockLevelById`; `RecipeDetailPage.vue` `stockActions` + its `useStockItemActions` import;
  `AboutSettings.vue` `ICONS` import). `npm run lint` clean and `npm run build` (quasar SPA)
  succeeds. The "should land with a CI gate" recommendation is **already satisfied**:
  `.github/workflows/ci.yml` already runs lint + `vue-tsc --noEmit` + build + pytest — the break
  would have lit up red in CI. The real gap was that the handoff "green static-verified" claim
  was never locally built; CI config itself is correct. (If merges aren't actually blocked on CI,
  that's branch-protection config, outside the codebase.)
- **What:** `npm run build` failed via `vite-plugin-checker`'s ESLint lintCommand on 4 unused symbols.

## [RESOLVED] FU-193 — Verify C-5.3 + C-5.4 + C-5.5 backend on a provisioned machine
- **Raised:** 2026-06-16 (Onboarding C-5.3)
- **Type:** deferred verification
- **State note (2026-06-16):** **resolved backend** on the now-provisioned machine
  (Python 3.11.15 + `.venv`). Added `tests/e2e/dora_api/test_onboarding_flags.py` (6 tests);
  full suite **303 pass** (was 297). Verified: `products_enabled` defaults True and round-trips
  via `GET`/`PATCH /api/app-settings` with `/api/health features.products` agreeing (single source
  of truth); `household_headcount` round-trips via `PATCH /api/auth/me` (1–99, null clears) and
  surfaces on `/me`, with out-of-range (0, 100) rejected 400; `GET /api/onboarding/catalog`
  serialises groups + nested location nodes + **5** starter packs; `POST /api/onboarding/seed-items`
  creates **pre-located** items (group/location resolved by name) and is **idempotent** on re-run
  (created:1→skipped:1, no duplicate). Alembic **single head** confirmed (`e2a9c5f1b7d4`); both new
  migrations are trivial batch `add_column`/`drop_column` with a linear revise chain — well-formed.
- **Caveat (not a regression of these migrations):** a clean **full-chain SQLite `flask db upgrade
  head`** still fails at the pre-existing `d7c9e4a8c2b1` (2026-06-12 shopping-list product anchor)
  with "Constraint must have a name" in batch mode — that's **FU-178**, upstream of these two
  migrations, so the new migrations' full up/down round-trip can't be exercised through the chain on
  SQLite until FU-178 is fixed (or on Postgres, FU-196). The DDL was verified by reading + the
  behavioural round-trips above (test env builds schema via ORM `create_all`).
- **Remaining (separate FUs):** the **browser** verification of the cook-mode serving scaler
  (household_headcount) and the persona-fork UI lives in **FU-192**; this entry covers backend only.
- **What:** behavioural backend coverage for the Onboarding C-5.3/.4/.5 flags + endpoints.

## [RESOLVED] FU-191 — First-item group/location pickers empty during onboarding (deferred-seed ripple)
- **Raised:** 2026-06-16 (Onboarding C-5.1)
- **Type:** leftover / known limitation
- **State note (2026-06-16, C-5.5):** **resolved** — the first-item flow is now **name-based**.
  Items are queued with a group/location *name* and created on Finish by the new
  `POST /api/onboarding/seed-items`, which resolves names against the catalogues seeded earlier in
  the same apply. The first-item pickers offer names from the chosen default groups + any starter-pack
  groups + existing rows, so a fresh user CAN categorise their first item against a default group.
  (Backend round-trip verification rides with **FU-193**.)
- **What:** C-5.1 deferred the catalogue seed to Finish, leaving the first-item group/location
  pickers empty (no ids existed at pick time). The fix needed name-based resolution — C-5.5's
  starter-data mechanism — which is what shipped.

## [RESOLVED] FU-172 — Execute IMPL_PLAN_MEAL_PLANS (C-2.A…K)
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS authored from C-2 proposal)
- **Type:** deferred job
- **State note (2026-06-14):** **all 11 chunks built + static-verified** —
  build order ran A, B, K, C, D, E, H, I, F, G, J. Final gate green: **274
  e2e + 49 unit pass**, `vue-tsc --noEmit` 0 errors, eslint clean on touched
  files; every new migration verified up/down in isolation and a single
  Alembic head re-confirmed after resolving a concurrent-session fork.
  Browser verification of the running surface carries forward under
  **[[FU-179]]** (the remaining gate before COVERAGE_GAPS §MEAL PLANS rows flip
  gap→covered). Spun-off open loops at resolution: FU-173 (slot-remap UI),
  FU-174 (app-wide datetime/tz sweep), FU-175 (bulk-week editor assessment),
  FU-176 (app-wide R-014 reveal-disable sweep), FU-178 (SQLite full-chain
  migration), FU-181 (plan email + meals_per_week pref).
- **What:** `docs/04_proposals/IMPL_PLAN_MEAL_PLANS.md` turned the C-2 Meal
  Plans proposal into eleven reviewable chunks. Build order (§5):
  **C-2.A** slot vocabulary (household-wide `MealSlot` table) ★ first PR →
  **C-2.B** page-chrome cleanup → **C-2.C** vertical carousel + slot rows +
  tap-add (+ K date fix; fixes FU-154 in passing) → **C-2.D** calendar widget →
  **C-2.E** drop `MealPlan.name` + implicit create + "Clear week" → **C-2.H**
  sidebar redesign (composes C-7; carries FU-135) → **C-2.I** trays →
  **C-2.F** templates (single) → **C-2.G** template sets + recurring + manage
  page → **C-2.J** sequential builder. Each shipped in isolation; the canvas
  kept working through every phase.
- **Decisions settled (review 2026-06-14):** full build; **slots are a
  household-wide `MealSlot` vocab table** (corrects proposal §4 "user-scoped"
  — `MealPlan` has no `user_id`); **3 trays** (incl. Frequently-planned);
  21-day "haven't had" window; recurring cap 26wk; templates at
  `/meal-plans/templates`; apply-time rotation; slot-remap deferred ([[FU-173]]).
- **Lower-level (also settled):** past-day fix → **household-timezone** correct
  (C-2.K; app-wide sweep [[FU-174]]); `MealPlanEditDialog` **retired** (C-2.E;
  bulk-week assessed in [[FU-175]]); C-2.J added `POST /meal-plans/preview-ingredients`;
  builder Email **shown-disabled** when SMTP unset per new rule **R-014** /
  ADR-009 (app-wide reveal-disable sweep [[FU-176]]). Plan is 11 chunks (K split out).

## [RESOLVED] FU-057 — P6-02: browser-verify the gated scanning surface + apply migration
- **Raised:** 2026-06-07 (P6-02 implementation)
- **Type:** finding
- **What:** The scanning/QR gating was verified by static read + frontend sweep only. Not
  confirmed in a running app: toggling `scanning_enabled` in Settings → System actually
  shows/hides the Stock Overview scan/print buttons, stock-item "Show QR", and the Data →
  "Scanning & QR labels" section/off-state banner. Migration `a3f1c7d2e9b4` (drops
  `StockItem.barcode`, adds `AppSetting.scanning_enabled`) has not been applied to a live DB.
- **Why deferred:** e2e suite pre-existing broken ([[FU-048]]); no browser smoke test this
  session.
- **Recommended resolution:** **confirm in browser** + run migration on a dev DB before P6-01.
- **State note:** 2026-06-14 — closed by user. Gating confirmed in browser (toggling
  `scanning_enabled` shows/hides the Stock Overview scan/print buttons, stock-item "Show QR",
  and the Data → "Scanning & QR labels" section) and migration `a3f1c7d2e9b4` has been
  applied. Also noted as no-longer-relevant given current scope.

## [RESOLVED] FU-141 — Browser-verify State Ownership Chunk 4
- **Raised:** 2026-06-12 (State Ownership Chunk 4 impl;
  static-only, no env)
- **Type:** finding / verification
- **What:** Eyeball that the rename-safety refactor preserved
  every visual decision it was supposed to preserve:
  - `StockItemChip` — colour band + short label ("OK" / "Mid" /
    "Low" / "Out") still match each level. Renaming "Out of
    Stock" to "Empty" in Settings should leave colour + label
    unchanged.
  - `StockItemRow` — dim treatment fires for out-of-stock
    rows; level button colour follows the current level.
  - `useStockFilters` — summary counts (top of Stock Overview)
    + sticky-footer tones still light up correctly when a
    level is renamed.
  - `WastePage` — "Mark used" sets the level to whichever row
    matches `OUT_OF_STOCK_SEQUENCE` (rename it first to
    confirm).
  - `MealPlansOverview` — "Need to buy" lists ingredients
    whose level is None/low/out; status chip colours match the
    bucket.
  - `ProductSearch` quick-add — new tracked items still start
    in the out-of-stock bucket.
  - `RecipeCookMode` finish-rows — "leave out of stock"
    action resolves to the right level after a rename.
- **Why deferred:** static-only impl; needs a running app +
  level-rename action to exercise the renaming property
  end-to-end.
- **Recommended resolution:** confirm in browser — high-priority
  for this chunk because the whole point is "renaming a level
  no longer breaks anything". Rename one level as part of the
  smoke pass.
- **State note:** 2026-06-14 — closed by user. The non-rename surfaces
  (chip colour bands, row dim treatment, summary counts, waste "Mark
  used", meal-plan "Need to buy" colours, quick-add seeding, cook-mode
  finish rows) are confirmed working in use. The rename-property half
  is moot: **stock-level renaming is not a supported user action**, so
  the "rename one level as part of the smoke pass" step has nothing to
  exercise.

## [RESOLVED] FU-013 — A4 leftover: "consistent multi-select control" only partial
- **Raised:** 2026-06-05 (A4)
- **Type:** leftover
- **What:** A4 standardised the filter-bar shell (panel/search/active-count/clear)
  but did NOT build a dedicated shared multi-select control. Multi-selects remain
  page-specific: `RecipesOverview` uses `q-select multiple use-chips`,
  `ProductSearch` merchant picker + `StockOverview` levels are bespoke chip UIs.
- **Why deferred:** the bespoke chip pickers carry extra behaviour (health
  icons, level colours, counts) that a generic control would lose; forcing one
  control would be a regression. The shell was the high-value standardisation.
- **Recommended resolution:** opportunistic — only if a future page needs a plain
  multi-select; otherwise leave the bespoke ones. Not no-regret.
- **State note:** 2026-06-14 — closed as wontfix. StockOverview's level filter is
  now a single-select `q-select` (C-1 Chunk 2 retired the per-level chips, see
  `StockOverview.vue:103-115`), so the original "bespoke multi-selects" list
  has shrunk. Remaining surfaces (`RecipesOverview`'s `q-select multiple use-chips`,
  `ProductSearch` merchant picker) are accepted as-is per the original "leave the
  bespoke ones" recommendation — no shared control needed.

## [RESOLVED] FU-125 — Stock Overview Chunk 6 / FU-033 — image surface fixes
- **Raised:** 2026-06-12 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification → product-defect resolution
- **What:** Browser verify revealed three real problems beyond the original
  verification checklist, all fixed this session:
  1. **Live update / cache-bust.** Uploading from the detail page didn't
     refresh the overview row (even on hard reload in one of the user's
     repros). Cache busting was a *local* `imageVersion` ref on the detail
     page — the row's `<img src>` had no query param and the browser served
     the cached copy. Moved cache-bust into `stockItemStore` as a per-item
     `imageVersions` map with `imageVersionOf(id)` + `bumpImageVersion(id)`;
     `updateStockItemAsync` bumps automatically when the PATCH payload
     includes `image`. Row + detail page both read the store-derived
     version, so any surface displaying the item refetches reactively.
     `imgFailed` latch on the row is now reset when the version bumps.
  2. **Inconsistent row position.** The image slot used to live *after* the
     name+zone column, so its x-position drifted with name length — read as
     "all over the place" across a list. Moved it to the **first** slot in
     the row, stretched to fill the row height, with the leading corners
     rounded to match the card. Bumped from 40×40 to 64-wide; the placeholder
     glyph went from 20 to 24 px to match. Looks like the leading edge of
     the card itself.
  3. **"Remove" on product-fallback preview.** The detail page's
     `ImageUploadField` rendered "Change image" + "Remove" whenever
     `has_image` was true — including when the preview came from a linked
     product. There's nothing for the user to remove in that state. Added
     `has_own_image: bool` to `StockItemDetailDto` (true only when the
     stock item carries its own uploaded bytes; doesn't include
     fallback), surfaced it on the frontend model, and gated the field's
     `canClear` prop on `has_own_image || pendingImage` so the button
     reads "Add image" and Remove is hidden during a fallback render.
- **Browser verification:** items 1–6 from the original verification list
  (own-upload save, product fallback, both-empty placeholder, list-payload
  perf, show/hide toggle, race protection) are unblocked by the fixes
  above and should be re-spot-checked next time the surface is open.

## [RESOLVED] FU-126 — Rename `RecipeImageField` → `ImageUploadField`
- **Raised:** 2026-06-12 (Stock Overview Chunk 6 / FU-033 impl)
- **Type:** tidy-up
- **What:** With the stock-item surface adopting the recipe-image field,
  R-001's second-consumer threshold was hit; the component carries no
  recipe-specific logic.
- **State note:** 2026-06-14 — **RESOLVED.** Moved
  `components/recipes/RecipeImageField.vue` → `components/ImageUploadField.vue`
  (renamed class prefixes too). Added an optional `alt` prop so the
  hard-coded "Recipe image" text no longer leaks into other surfaces
  (defaults to the `name` prop, which mirrors the previous behaviour for
  recipes). The same change introduced the optional `canClear` prop
  used by FU-125 to hide Remove on product-fallback previews. Updated
  the three import sites (`RecipeEditDialog`, `RecipeDetailPage`,
  `StockItemDetailPage`).

## [RESOLVED] FU-127 — Browser-verify Cart Button Chunk 1 (AddToListButton + double-toast fix)
- **Raised:** 2026-06-12 (Cart Button Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify the row/toolbar/bulk variants of `AddToListButton` on
  Stock overview, Recipe detail, Stock-item detail, plus the bulk-add target
  resolution + FU-038 double-toast guard.
- **State note:** 2026-06-14 — **RESOLVED.** User: "all good". Browser
  verification passed on the surfaces in scope. The "Add to another list"
  popover toast bug surfaced during this verification — fixed in the
  feedback sweep this session, not a Chunk 1 regression.

## [RESOLVED] FU-128 — Adopt `AddToListButton` on remaining cart surfaces
- **Raised:** 2026-06-12 (Cart Button Chunk 1 scope cap)
- **Type:** rollout
- **What:** Chunk 1 left four hand-rolled cart surfaces in place
  (#6 MyProductsPage, #7 MealPlansOverview, #11 ProductSearch,
  #13 QuickAddSheet entry buttons). The FU framed them as mechanical
  q-btn → AddToListButton swaps.
- **State note:** 2026-06-14 — **RESOLVED.** Per-surface investigation
  showed only one is mechanical; the rest carry compound semantics that
  the existing AddToListButton variants don't model:
  - **#6 MyProductsPage per-product cart — adopted.** Extended
    `AddToListButton` with an optional `selected-product-id` prop
    ([AddToListButton.vue](web_app/src/components/AddToListButton.vue)):
    when set on the `row` variant, the add records `selected_product_id`
    on the line and skips the 2+-products combined-modal branch
    (the product is already chosen). MyProducts per-product button is now
    `<AddToListButton variant="row" :stock-item-id :selected-product-id>`
    and the old `onAddSingle` handler is gone — picks up the popover for
    on-2+-lists, smart-remove for exactly-one-list, and the unified toast
    behaviour the rest of the app has.
  - **#6 MyProductsPage bulk on-deal — kept.** The "Add N on-deal to list"
    button uses an explicit BaseDialog target picker (different UX from
    AddToListButton bulk's sessionStorage-remembered target). Intentional
    — keeps the explicit-choice posture for on-deal adds.
  - **#7 MealPlansOverview "Generate shopping list for this week" — kept.**
    Not an add-to-existing-list action; it generates a *new* list from the
    plan via `generateListForWeek`. The per-ingredient cart button already
    uses `AddToListButton variant="row"`.
  - **#11 ProductSearch quick-add — kept.** Composite "track + create stock
    item + link product + add to list" flow (`quickAddOffer`, ~30 lines
    around `ProductSearch.vue:559`). Specific to onboarding a new offer;
    doesn't fit AddToListButton's "stock item already exists, add it" model.
  - **#13 QuickAddSheet — kept.** The sheet itself is mounted once globally
    and popped by `openQuickAdd()` from many call sites (Dashboard, etc.).
    Those entry buttons are general "open the picker" actions, not "add
    this specific item", so AddToListButton would be the wrong shape.
- **How to apply:** when adopting AddToListButton elsewhere later, pass
  `selected-product-id` whenever the caller has already picked the product
  (per-product cards, comparison results); leave it unset for stock-item-
  row cases so the 2+-products combined modal still surfaces.

## [RESOLVED] FU-008 — Unify dialog chrome via BaseDialog `title`/`#actions` slots
- **Raised:** 2026-06-05 (A3)
- **Type:** deferred job
- **What:** A3 migrated dialogs as a shell transform; each still carried its own
  header/footer markup. BaseDialog already exposes `title`/`closable`/`#actions`
  to standardise chrome.
- **State note:** 2026-06-14 — **RESOLVED.** Full sweep across all 26 BaseDialog
  files. Replaced bespoke `text-h6` header card-sections with the BaseDialog
  `title` prop (or `#header` slot for the icon+title case in `ShortcutsCheatsheet`),
  added `closable` where the original had a hand-rolled close button, and moved
  every `<q-card-actions align="right">` block into the BaseDialog `#actions`
  slot. Form-submit buttons in dialogs whose footers moved outside the `<q-form>`
  were rebound to `@click="onSubmit"` so the submit path still fires. Captions /
  sub-headers that lived next to the title were preserved as body
  `<q-card-section>` content. `vue-tsc --noEmit` clean; backend unit suite 49/49.
  Browser verification still recommended across the dialog matrix.

## [RESOLVED] FU-009 — Decide fate of the 3 specialised overlays vs BaseDialog
- **Raised:** 2026-06-05 (A3)
- **Type:** finding
- **What:** `AlertsBell` (seamless drawer), `CommandPalette` (search overlay),
  and `ScanOverlay` (persistent camera) were intentionally left on raw
  `q-dialog` — they aren't standard card modals.
- **State note:** 2026-06-14 — **RESOLVED.** User confirmed leaving as the
  documented permanent exception. (Command palette was retired separately on
  2026-06-12 anyway; only AlertsBell + ScanOverlay remain as live carve-outs,
  both intentional.)

## [RESOLVED] FU-014 — Product image round-trip is broken (read side decodes binary as utf-8)
- **Raised:** 2026-06-05 (B1); re-diagnosed 2026-06-12 after user repro
- **Type:** finding (now: active bug being fixed)
- **What:** `get_products.py:56` did `product.image.decode('utf-8', 'ignore')`
  on raw image bytes, returning garbage. Fix: adopt the stock-item/recipe data-URL
  pattern + `has_image` list payload + a dedicated `GET /products/<id>/image`
  route.
- **State note:** 2026-06-14 — **RESOLVED.** Verified statically: the fix
  shipped in full — `get_products.py` now exposes `has_image: bool` (stamped
  in bulk via `stamp_has_image` referencing FU-014 in code comments),
  `get_product_image.py` provides the dedicated `GET /api/products/<id>/image`
  endpoint, and `create_product.py` accepts the data-URL string and decodes it
  to UTF-8 bytes on the entity. Frontend `MyProductsPage` / `ProductChip` /
  `ProductSearch.ensureSaved` migration also landed.

## [RESOLVED] FU-015 — B5: Onboarding tour "Alerts" card points at stock, not /alerts
- **Raised:** 2026-06-05 (B5)
- **Type:** finding
- **What:** `WelcomeWizard.vue` `TOUR_CARDS` "Alerts — Dora pings you" routed
  to `/stock?attention=true` instead of the real `/alerts` page.
- **State note:** 2026-06-14 — **RESOLVED.** Repointed the tour card to
  `/alerts` in `web_app/src/pages/onboarding/WelcomeWizard.vue:422`. The
  `/alerts` route exists (`router/routes.ts:76`) and `AlertsPage.vue` is the
  real destination.

## [RESOLVED] FU-027 — B9.7: log-rotation model decision (timed vs size)
- **Raised:** 2026-06-06 (B9.7)
- **Type:** open decision
- **What:** Size-based `RotatingFileHandler` (10MB × 5) — user wanted the active
  log file to contain only the current date's entries.
- **State note:** 2026-06-14 — **RESOLVED.** Switched
  `dora_api/infrastructure/logging_setup.py` to `TimedRotatingFileHandler`
  with `when="midnight"`, `backupCount=14`, and `suffix="%Y-%m-%d"`. The
  active `<service>.log` now only ever contains the current date; rotated
  files are kept as `<service>.log.YYYY-MM-DD` for ~2 weeks. Backend unit
  suite passes (49/49).

## [RESOLVED] FU-031 — B9.3: stale "Recipes" labels after A8 cookbook rename
- **Raised:** 2026-06-06 (B9.3 sweep)
- **Type:** leftover
- **What:** Possible stale "Recipes" labels in tour cards / help / static
  lists after A8 renamed the page to Cookbook.
- **State note:** 2026-06-14 — **RESOLVED** after a one-shot grep. Only four
  candidates surfaced and all read logically per the user's framing ("the
  page is the cookbook, and that has recipes in it"): `DashboardPage.vue:638`
  dashboard "Recipes" card title (shows recipe count → links to /cookbook);
  `DashboardPage.vue:814` card-visibility config label `Recipes`;
  `HelpPage.vue:251` section "Recipes & meals"; `BackupRestore.vue:402`
  data-type label "Recipes". All four refer to recipes-as-content, not to
  the page itself — no edit required.

## [RESOLVED] FU-037 — `.secret_key` hardcoded to `./data/`, ignores DORA_DATA_DIR
- **Raised:** 2026-06-06 (INV-3 re-verification)
- **Type:** finding (latent bug)
- **What:** `dora_api/app.py:47` resolved the session-secret file as
  `Path('data') / '.secret_key'` (CWD-relative), so on the desktop app the
  secret escaped the configured data dir and was CWD-dependent.
- **State note:** 2026-06-14 — **RESOLVED.** Reworked the secret-key resolution
  in `dora_api/app.py` to `config_manager.get_data_dir() / '.secret_key'`
  (creating the parent on first run via `mkdir(parents=True, exist_ok=True)`).
  Also routed the dev `data/` mkdir for SQLAlchemy through `get_data_dir()` so
  the whole app honours `DORA_DATA_DIR`. Backend unit suite passes (49/49).
  Still wants a desktop smoke test across a CWD change to confirm sessions
  survive — fold into the next desktop verification pass.

## [RESOLVED] FU-047 — `confirm_actions._resolve_level` still maps phrases → hardcoded level names
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** by static verification. The
  refactor already shipped: `dora_api/features/assistant/confirm_actions.py`
  imports `StockStatus` + `level_for_status`, `_LEVEL_ALIASES` is now keyed to
  `StockStatus` enum members (not name strings), and `_resolve_level` resolves
  via `level_for_status(repo.get(StockLevel).all(), status)` — the brittle
  `"Sufficient"` / `"Well Stocked"` name-mismatch path is gone.

## [RESOLVED] FU-048 — e2e suite (`tests/e2e/dora_api/`) is pre-existing broken on this branch
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** per user ("resolved i believe").
  The e2e suite was repaired in commit `8793648 Fix e2e tests` and is no
  longer the pre-existing-broken blocker it was.

## [RESOLVED] FU-061 — Promote doc-graph to in-prompt blocks (Option B) if agents skip the ritual
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels like what we have
  is working"). Keep the lighter centralised-graph scheme; no per-prompt
  inlined blocks.

## [RESOLVED] FU-062 — Doc-graph: verify cited paths + original-spec Feature Board mappings
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). Per-citation
  existence pass + Feature Board mapping audit not pursued.

## [RESOLVED] FU-063 — Doc-graph: first-use stress test
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** follow-up
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). No
  dedicated first-use stress test will be run; the graph stands as-is.

## [RESOLVED] FU-064 — Doc-graph: maintenance cadence / regeneration prompt
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). No
  dedicated refresh prompt; rely on opportunistic updates as proposals/FUs
  land.

## [RESOLVED] FU-163 — App-wide undo posture: removed
- **Raised:** 2026-06-12 (UX v2 decisions, §12 Q4)
- **Type:** finding (product decision pending) → product decision
- **What:** User: "I'm heavily questioning the usefulness of undo feature
  everywhere in the app. Likely going to remove." The original inventory
  covered the `useUndo` registry + silent per-tick undo entries, the
  `notifyUndoable` toasts (stock-item delete-restore), and the shopping-list
  Reopen/unfinish flow. Reopen had been flagged as the one possibly-worth-
  keeping path because it was server-snapshotted.
- **State note:** 2026-06-14 — **RESOLVED.** User: "decided undo feature does
  not make sense, remove. Even the reopen functionality — once a list is done,
  it's done. The snapshot of stock levels feels so overengineered. Kill it."
  Removed end-to-end in one pass:
  - Frontend: deleted `useUndo.ts` + `useNotifyUndoable.ts`; stripped the
    Ctrl-Z / header Undo button + keyboard handler from `MainLayout.vue`;
    removed all `registerUndo` / `notifyUndoable` call sites in
    `stockItemStore.ts` (level swap, scalar update, delete) and the
    `ShoppingListDetail.vue` tick handler; deleted the Reopen button + its
    `onReopen` / `reopening` state; deleted `unfinishAsync` from
    `shoppingListApiService.ts`; deleted `restoreAsync` +
    `RestoreStockItemCommand` from `stockItemApiService.ts`.
  - Backend: deleted `features/shopping_lists/unfinish_shopping_list.py` and
    `features/stock_items/restore_stock_item.py`. Dropped the `level_restores`
    capture from the finish handler. Removed `finish_snapshot` from the
    `ShoppingList` entity + `Fields` enum + table mapping. New alembic
    migration `a1c4e7b3f5d2_20260614_drop_finish_snapshot.py` drops the
    column (batch mode for SQLite/Postgres parity, R-005).
  - Tests: rewrote the reopen e2e (`test_shopping_list_lifecycle.py`) into a
    one-liner asserting `/unfinish` now returns 404; the docstring framing
    moved from "server-owned undo" to "once done, it's done".
  - FU-026 ("undo behaves oddly across surfaces") is moot under no-undo and
    was removed at the same time. The stock-item Undo restore reference in
    FU-016's candidate list got an inline note.
  Verified: backend `py_compile` clean, all 49 unit tests pass, e2e suite
  collects without import errors, ESLint clean on the touched files. Browser
  verification rolls into the next FU-165 session.

## [RESOLVED] FU-026 — "Undo behaves oddly across surfaces" (subsumed by FU-163)
- **Raised:** 2026-06-06 (B9.5)
- **Type:** finding / open verification
- **What:** Originally a B9.5 probe into a reported "undo behaves oddly" across
  surfaces. Partially resolved by P6-01 Chunk 1 (server-owned Reopen). The
  remaining open vector was the originating surface (Dashboard alerts) not
  refetching after an inverse fired elsewhere, so Ctrl-Z mutated the store
  correctly but the source surface rendered stale state.
- **State note:** 2026-06-14 — **RESOLVED.** Subsumed by FU-163: the entire
  undo system (registry, header button, Ctrl-Z, undoable toasts, Reopen) was
  removed, so there is no longer an "undo" path to behave oddly. Nothing to
  fix; nothing to keep tracking.

## [RESOLVED] FU-168 — Meal-plan CSV export removed (was 500ing)
- **Raised:** 2026-06-13 (FU-166 triage)
- **Type:** finding (genuine defect) → product decision
- **What:** `GET /api/meal-plans/<id>/export?format=csv` 500'd — the CSV
  builder + print-view template read `entry.meal_name`, but `MealPlanEntryDto`
  exposes `recipe_name`.
- **State note:** 2026-06-13 — **RESOLVED.** User: "meal-plan CSV export makes
  no sense, remove." Removed the `/export` route + `_build_csv` (backend), the
  `downloadCsv` fn from `useMealPlanExport.ts` + both CSV buttons
  (`ExportPrint.vue`, `MealPlansOverview.vue`); the e2e test now asserts the
  endpoint 404s. Print-view is **kept** and its latent blank-meal-name bug
  fixed (`meal_name`→`recipe_name` in the Jinja template). vue-tsc clean.

## [RESOLVED] FU-167 — Unknown GET `/api/<x>` returned SPA HTML 404, not JSON
- **Raised:** 2026-06-13 (FU-166 triage)
- **Type:** finding (genuine defect)
- **What:** An unmatched **GET** under `/api/` returned a 404 with the SPA's
  `text/html` body (the GET-only SPA catch-all matched, so the request
  middleware's no-endpoint JSON-404 never fired and the view's `abort(404)`
  produced the default HTML), while POST/PATCH/DELETE returned JSON.
- **State note:** 2026-06-13 — **RESOLVED.** Factored the no-route 404 body
  into a shared `api_response.endpoint_not_found()` (plain `application/json`,
  matching the middleware), used by both the middleware and the SPA catch-all
  — the catch-all's `/api/` branch now returns it instead of `abort(404)`. All
  four verbs return the identical JSON problem-detail; the `test_misc` GET case
  passes (xfail removed).

## [RESOLVED] FU-166 — Legacy e2e suite has drifted badly from the API (122 pre-existing failures)
- **Raised:** 2026-06-12 (first known full `pytest tests` run, during UX v2)
- **Type:** finding
- **State note:** 2026-06-13 — **RESOLVED.** Full `pytest tests` now
  **296 passed / 3 xfailed / 0 failed** in ~6s (was 122/167/10 in 813s),
  stable across repeated runs. Two-part fix: (1) converted the e2e harness to
  Flask's in-process test client (~95× faster, behaviour-preserving — new
  R-013/ADR-008); (2) updated all ~132 drifted assertions to the current
  contract (query-string options, `{items,total,page,limit}` envelope, ISO
  dates, refreshed seed/DTOs, reworked error messages) per the user's
  UPDATE disposition. Three genuine defects uncovered are now tracked as
  strict `xfail`s rather than silently passed: FU-164 (backup links section),
  FU-167 (unknown-GET `/api` HTML 404), FU-168 (meal-plan CSV 500). See the
  2026-06-13 worklog entry for the per-file breakdown.
- **What:** Full suite: **122 failed / 167 passed / 10 errors**. Verified
  pre-existing by stashing the UX v2 changes and re-running the two heaviest
  files (`test_stock_item_router`, `test_user_router`) — identical failures
  on baseline. Dominant modes: tests assert the *old bare-array* response
  shape where the API now returns pagination envelopes
  (`{items, page, limit, total}`); 404s + fixture errors through the older
  CRUD router tests. The newer feature suites (shopping lists 21/21, audit,
  auth, data import/export) pass. The old router tests appear to predate
  several API reworks and were never maintained.
- **Why it matters:** "the tests pass" currently means nothing for ~40% of
  the suite — regressions in old surfaces are invisible. FU-164 (backup
  sections) is one concrete member of this set.
- **Recommended resolution:** later, as its own focused prompt — triage per
  file: update assertions to the current API contract, or delete tests for
  removed behaviour. Don't fix piecemeal inside feature work.

## [RESOLVED] FU-164 — Backup-sections test failure (misdiagnosis: stale `meals`/`meal_recipes`)
- **Raised:** 2026-06-12 (full pytest run during UX v2)
- **Type:** finding
- **State note:** 2026-06-13 — **RESOLVED, and the original diagnosis was
  wrong.** `product_stock_item_links` is *already* a real backup section
  (`restore_shared.SECTIONS` line 78, `StockItemProduct`) and present in the
  payload — verified by dumping the live backup. The test actually failed
  because its `expected_sections` still listed **`meals` + `meal_recipes`**,
  which the "Complete rework of meals" (meals→recipes) commit removed as
  tables. Fixed by dropping those two stale keys from the test's expected set
  (and removing the FU-166 xfail). No backup-builder change needed — the
  product↔stock-item links do round-trip.
- **What:** `test__get_backup__happy_path__returns_attachment_with_expected_sections`
  expects a `product_stock_item_links` section that `features/data/backup.py`
  never provides — the string appears nowhere in `dora_api`. The test was
  updated in commit `d2153e3` ("Tidy up incorrect barcode implementation…")
  ahead of a backup change that never landed. Unrelated to UX v2 (fails on
  main too).
- **Recommended resolution:** opportunistic — either add the links section to
  the backup builder (likely the original intent: the product↔stock-item
  anchor table should be backed up) or correct the test. Decide alongside the
  next data/backup task.

## [RESOLVED] FU-162 — Implement shopping-list UX v2 (single-page merge, rail, chip axe)
- **Raised:** 2026-06-12 (shopping-list UX design session)
- **Type:** deferred job
- **What:** `docs/04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md` — the agreed
  redesign of the shopping surface: lists rail (desktop) / dropdown (mobile)
  ordered by effective date, server-owned `display_name` (nullable custom name)
  and `next_up_list_id`, top info area (big status badge, proper shop-day
  button, resurrected completion doughnut + totals), toolbar instead of
  ellipsis menus, per-row direct actions + real price button, StockItemChip
  deleted app-wide, shop-mode page merged into the detail page (full M1–M15
  disposition table in the proposal §2).
- **State note:** 2026-06-12 — built in full the same day (§12 decisions:
  no location default for shopping, restock-review modal, CSV export +
  archive + per-line move + pause all removed, R-012 adopted). ESLint +
  vue-tsc clean; 21/21 shopping e2e tests pass (3 updated to the new
  design). Browser verification tracked as FU-165.

## [RESOLVED] FU-159 — Planned shop date not surfaced in shopping-list UI (feedback L402)
- **State note:** 2026-06-12 — resolved by UX v2 (FU-162): the shop day is a
  real outlined button in the top info area (today/overdue tones), drives the
  rail's effective-date order and the server-side next-up pick, and labels
  self-named lists. Browser check folded into FU-165.
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** finding (design drift)
- **What:** Feedback L402: "Being able to set a planned shopping day per list
  would be useful. Optional of course." The DB column
  `planned_shop_date` exists (migration
  `e1a4c7b2f9d0_20260613_shopping_list_planned_shop_date.py`) and the list
  picker sorts by it
  ([routes.ts:110-131](web_app/src/router/routes.ts#L110)), but nothing in
  the UI displays or edits the field. The user can't actually set one.
- **Recommended resolution:** add a date picker to the list header info
  area on `ShoppingListDetail.vue` (top info area was already proposed in
  L407), plus a chip / caption on each row of the list-selector dropdown
  so the sort order makes visible sense. Pair with FU-158 below — both
  belong in the same "shopping list polish" pass.
  *2026-06-12 update:* partially built since raised (date link + editor +
  banner exist on the detail page) but discoverability complaint stands
  (text link, S14). Folded into FU-162 /
  `PROPOSAL_SHOPPING_LIST_UX_V2.md` §4 — resolve there.

## [RESOLVED] FU-158 — Shopping list responsive layout + today's-date picking (feedback L405/406/409)
- **State note:** 2026-06-12 — resolved by UX v2 (FU-162): desktop virtualised
  rail + mobile dropdown (one effective-date continuum), and the landing pick
  is the server-owned `next_up_list_id` (the old today's-date string compare
  could never match — RFC-vs-ISO serialisation, see ADR-007). Browser check
  folded into FU-165.
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** finding (design drift from `SHOPPING_LIST_REDESIGN_PROPOSAL.md`)
- **What:** The Chunk-5 merge of overview-into-detail shipped, but three
  pieces of the proposal got dropped:
  1. **Desktop right-side panel** with all lists ordered by planned shop
     date → finalised date → creation date (feedback L405). Current code
     uses a single `q-btn-dropdown` in the header for every viewport
     ([ShoppingListDetail.vue:8-117](web_app/src/pages/ShoppingListDetail.vue#L8)).
  2. **Mobile dropdown at top** (L406) — exists today but identical to
     desktop; no responsive split.
  3. **Today's-date-keyed picking** when navigating to `/shopping-lists`
     with no id (L409). The route guard
     ([routes.ts:110-131](web_app/src/router/routes.ts#L110)) picks by
     status + creation order, not by today's planned shop date. So a list
     planned for today is no more likely to be chosen than any other.
- **Why deferred (now):** the user reported broad shopping-list buggyness;
  the immediately-blocking bugs (FU-157: URL param not watched) were
  surgically patched today. The proposal-level polish above is its own
  scoped work — needs design choices (panel width? desktop-vs-mobile
  breakpoint?) and probably its own Wave-A-shaped prompt. Bundling them
  here was already attempted in the original Chunk 5 and the polish was
  the part that got cut.
- **Recommended resolution:** queue a focused "Shopping list polish" prompt
  with these three items + FU-159 (planned shop date in UI) + FU-160
  (shopping-day alert). Keep `useUnsavedChangesGuard`-style discipline:
  responsive split is a Wave-A pattern, today's-date logic is a route-guard
  patch.
  *2026-06-12 update:* that focused design now exists —
  `docs/04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md` (§3 rail/dropdown,
  §3.3 server-owned `next_up_list_id` replacing today's-date guessing).
  Folded into FU-162 — resolve there.

## [RESOLVED] FU-157 — Shopping list URL-param change doesn't reload (and "old list reappears")
- **Raised:** 2026-06-12 (user repro)
- **Resolved:** 2026-06-12 — `ShoppingListDetail.vue` and
  `ShoppingListShopMode.vue` were `onMounted`-only, with no
  `watch(listId)`. Switching lists via the header dropdown pushed the
  new URL but the component stayed mounted (same route component, just
  a different `:id`), so `load()` never re-ran and the previous list's
  data sat on screen. The "old list reappears after adding to another"
  symptom was a direct consequence: the page never moved off list A,
  so any subsequent `load()` (e.g. via the QuickAdd-closed watcher)
  looked like a resurrection. Fix: added `watch(listId, load)` on both
  pages, plus a `detail.value = null` clear at the start of `load()`
  so the user sees a spinner — not stale rows — while the new list is
  in flight.
- **Type:** finding (real bug, structural)

## [RESOLVED] FU-156 — Main menu nav bypasses the unsaved-changes guard
- **Raised:** 2026-06-12 (user repro during FU-021 verify)
- **Resolved:** 2026-06-12 — root cause confirmed (c): the guard was
  per-handler (`RecipeDetailPage::onBack`) instead of route-level, so
  any nav surface other than the back button skipped the prompt; on
  `StockItemDetailPage` there was no guard at all. Fixed at the layer
  that covers every nav route — new `useUnsavedChangesGuard`
  composable wraps both `onBeforeRouteLeave` (different-route nav,
  e.g. main menu) **and** `onBeforeRouteUpdate` (same-component param
  change, e.g. clicking a related-recipe link mid-edit), plus
  `beforeunload` for refresh/close. Wired into RecipeDetailPage
  (`isDirty || imageDirty`) and StockItemDetailPage (`isDirty`).
  `RecipeDetailPage::onBack` simplified to a plain `router.push` since
  the guard now owns the prompt. Delete handlers on both pages drop
  the dirty state before navigating so the user isn't asked about
  edits to a row they just deleted.
- **Type:** finding (real bug)

## [RESOLVED] FU-155 — Stock-item detail "Related recipes" tab navigates to Cookbook overview, not the recipe
- **Raised:** 2026-06-12 (user repro; carve-out from FU-019 [[fu-019]])
- **Resolved:** 2026-06-12 — bug was in
  `StockItemDetailPage::goToRecipe` which built
  `{ path: '/cookbook', query: { recipe: recipeId } }`. The
  recipe-detail route is `/cookbook/:id`; the bad path matched the
  `/cookbook` overview (and the unused `?recipe=` query was silently
  dropped). Changed to `router.push(\`/cookbook/${recipeId}\`)`.
- **Type:** finding (real bug)

## [RESOLVED] FU-149 — Cookbook overview: add "# ingredients" filter + sort axis
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** New filter axis "ingredients = N" or "ingredients ≤ N"
  + new sort axis "ingredient count (asc/desc)" on the cookbook
  overview. Ingredient count is already on the Recipe DTO (via the
  `ingredients[]` array length); the work is mostly in
  `useRecipeFilters` / the overview's filter panel + sort options.
- **Why deferred:** new feature, not bug. Scope cap on the
  current session.
- **Recommended resolution:** later, batched with FU-148
  (time-of-day filter) and the other cookbook polish items.

## [RESOLVED] FU-148 — Cookbook overview: add "time of day" filter
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** `Recipe.time_of_day` exists on the entity + DTO
  (breakfast / lunch / dinner / snack / dessert / drink), and it's
  editable on the recipe detail page, but there's no filter for
  it on the cookbook overview. Add a single-select dropdown
  defaulting to "any time of day" alongside the cuisine / category
  selects. The other filters use the same `useRecipeFilters`
  pattern; this should be one mirrored predicate.
- **Why deferred:** new feature; pair with FU-149.
- **Recommended resolution:** later.

## [RESOLVED] FU-147 — Recipe detail dietary-tag picker loses selection on save
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — root cause turned out to be a backend
  bug in the detail endpoint, not a frontend race. The
  `/api/recipes/<recipe_id>` route has no `uuid:` converter, so
  Flask passes `recipe_id` to `handle_by_id` as a **string**.
  `get_tag_ids_for_recipes()` returns `dict[UUID, list[UUID]]`
  (keys come from SQLAlchemy result rows). The handler then did
  `tag_map.get(recipe_id, [])` — a Python dict lookup with a
  string key against UUID-typed keys → **always returned `[]`**,
  silently dropping every tag and tool on the detail JSON.
  Same bug affected `tool_map.get(recipe_id, [])`. Fix in
  `get_recipes.py::handle_by_id`: pass `entity.id` (the loaded
  entity's real UUID) to both `get_tag_ids_for_recipes` and the
  subsequent `.get()` calls. The list endpoint was unaffected
  because it sources ids from RecipeDtos that already carry
  UUID objects.
  Static-only fix; browser-verify is **FU-151**.

## [RESOLVED] FU-137 — `test_recipe_cookability.py` stub missing `source` attr
- **Raised:** 2026-06-12 (surfaced during State Ownership Chunk 1
  verification run)
- **Type:** finding / test breakage (pre-existing)
- **What:** `tests/test_recipe_cookability.py::_recipe()` built a
  `SimpleNamespace` recipe stub lacking `source`,
  `version_group_id`, `kcal` — fields that `RecipeDto.from_entity`
  reads. Every test in the file failed with `AttributeError`.
- **State note:** **Resolved 2026-06-12 (State Ownership Chunk 2)**
  — the stub was the scaffolding for Chunk 2's
  `missing_stock_item_names` tests, so the fix was folded into
  that chunk per the original recommendation. Added the three
  missing attributes; all 12 cookability tests now pass.

## [RESOLVED] FU-136 — `test_shopping_list_totals.py` stub missing `product_id` arg
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — added `product_id=None` to the `_line()`
  factory in `tests/test_shopping_list_totals.py`. Single-line stub
  fix; totals tests don't exercise the new anchor so None is the
  honest value. CI signal restored.

## [RESOLVED] FU-131 — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **State note:** **Resolved 2026-06-12** — all three pieces
  (rule 4 modal in `ShoppingListDetail.vue::onRemoveLine`,
  nested display via `nestedLinesFor` + new CSS classes, and
  `AddToListButton variant="inline-product"` consumed by
  `MyProductsPage`) landed in a single session. Browser-verify
  tracked separately as **FU-145**. Original entry preserved
  below for the trail.

## [RESOLVED] FU-120 — Browser-verify Stock Overview Chunk 1 (50-cap fix + virtualisation + filtered export)
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — user verified in browser ("FU-035
  resolved — looks good"). >50-item pantry now renders the full
  list via the paged loop + `q-virtual-scroll`; filtered CSV /
  print exports honour the `ids=` filter; unfiltered exports
  take the fast path. No defects raised. **FU-035** stays
  RESOLVED with this confirmation closing the loop.

## [RESOLVED] FU-106 — Stock Overview image collapse/expand inline button (C-cross §2.8 surface)
- **Raised:** 2026-06-10
- **Resolved:** 2026-06-12 by Stock Overview Chunk 3 — inline image
  toggle next to the search input flips `show_stock_images` via the
  existing `useImagePrefs()` composable; the row's image slot is
  `v-if="showStockImages"` so density actually changes when toggled.
  Slot is currently a neutral placeholder (40×40 sunken square); it
  becomes the real photo container when FU-033 wires
  `StockItem.image` bytes. Static-only impl; browser-verify is
  **FU-122**.

## [RESOLVED] FU-090 — Recipe list query loads all image blobs (perf)
- **Raised:** 2026-06-09 (Chunk 5)
- **Resolved:** 2026-06-11 (C-cross Chunk 5). Folded into Chunk 5 per
  the IMPL plan ("the bandwidth-saving promised by 'images off' is
  otherwise hollow"). `Recipe.image` is now mapped with SQLAlchemy
  `deferred()` so the column never loads on the recipe-list query.
  `RecipeDto.from_entity` defaults `has_image=False`; a new
  `_hydrate_has_image()` runs a single bulk
  `SELECT id, image IS NOT NULL FROM Recipe WHERE id IN (...)` and
  fills the field — same hydrator pattern as tags / tools /
  structured-step flag. The image-bytes endpoint
  (`get_recipe_image`) still reads `recipe.image` directly via
  attribute access (one query per detail call, the intended path);
  the new-version handler's `image=source.image` copy also triggers a
  single lazy load per call.
- **Files:** `dora_api/persistence/table_mappings.py`,
  `dora_api/features/recipes/get_recipes.py`.

## [RESOLVED] FU-087 — Recipes overview filter panel shows nothing / toggle does nothing
- **Raised:** 2026-06-09 (user browser test of FU-083 + FU-085)
- **Resolved:** 2026-06-09. Reproduced via DOM inspection — the FilterBar's
  panel had `display: none` because `expanded` was permanently `false`. Two
  latent bugs in `FilterBar.vue` (and therefore every page using it,
  including StockOverview): **(1)** Vue 3 coerces an unset Boolean prop to
  `false`, so the manual `props.modelValue === undefined` sentinel
  distinguishing controlled-vs-uncontrolled never fired — clicks mutated
  `internal` but the getter kept returning the coerced-false `modelValue`.
  **(2)** `$q.screen.gt.sm` was read without the Quasar Screen plugin being
  activated anywhere, so every viewport check returned `false` (the "open on
  desktop by default" rule silently failed regardless of viewport). Both
  invisible to static type-checking and produced no console output.
- **Fix:** rewrote with the framework-idiomatic patterns: Vue 3.4
  `defineModel()` (handles controlled/uncontrolled correctly; a function
  default sidesteps the Boolean coercion); plus a new
  `web_app/src/boot/quasarScreen.ts` calling `Screen.setDebounce(100)` (the
  documented Quasar 2.x activation, registered in `quasar.config.ts`).
  Promoted the lesson to **R-011 / ADR-004** in
  `docs/01_charter/ENGINEERING_STANDARDS.md` — "use the framework's
  idiomatic, current-recommended pattern" — so this class of hand-rolled
  workaround doesn't recur.
- **Files:** `web_app/src/components/FilterBar.vue`,
  `web_app/src/boot/quasarScreen.ts` (new), `web_app/quasar.config.ts`,
  `docs/01_charter/ENGINEERING_STANDARDS.md`, `CHANGELOG.md`.
- **Unblocks:** FU-083 (Cookbook Chunk 1 filter verify) and the filter half
  of FU-085 (Chunk 2 cuisine/category/dietary filters).

## [RESOLVED] FU-083 — Browser-verify Cookbook Chunk 1 + user feedback pass
- **Raised:** 2026-06-09 (post-Chunk-1 implementation)
- **Resolved:** 2026-06-10. User did the browser pass and surfaced
  nine concrete pieces of feedback; all addressed in this session.
- **Original verify items 1–7 plus user-flagged tweaks, by status:**
  1. ✅ Comparison gone — clean (no warnings).
  2. ✅ Chip filters toggle; `activeFilterCount` updates.
  3. ✅ Numeric inputs — **`:hint` removed** on `Meals ≥` / `Missing ≤`
     (and the old `Free from ingredient(s)` input is gone entirely);
     filter row alignment is no longer offset by the extra
     under-input copy.
  4. ✅ Sort axes — now with an explicit **`sortDir` toggle**
     (asc/desc) on a dedicated direction button next to the Sort by
     dropdown. Null sentinels (last_made, total_time) still sink to
     the bottom regardless of direction. Axis-switch snaps direction
     to the conventional default (name=A→Z, recently-made=newest
     first, etc.).
  5. ✅ Stock-item picker — **dot kept, level text removed** from
     the dropdown row (user flagged the caption as redundant);
     `?usesStockItem=` deeplink still hydrates.
  6. ✅ **`Planned` filter bug fixed.** Was string-comparing
     `scheduled_for` without parsing, and didn't skip consumed
     entries — user reported yesterday's still surfacing. Now
     parses `YYYY-MM-DD` explicitly into a local-midnight `Date`,
     skips any entry with `consumed_at` set, and gates on the
     parsed `>= today` check. Also renamed the chip from
     **"Planned in"** to plain **"Planned"** per the feedback ("In
     adds nothing").
  7. ✅ **RecipeCard dim removed.** The "restocking this item alone
     wouldn't make it cookable" semantics wasn't legible without a
     legend, and the card already shows "missing N ingredients" on
     its face. `highlightStockItemIds` prop kept (used by deep-link)
     but no longer drives a `--dim` class.
  8. ✅ Filter-bar alignment — **hints + the free-text "Free from"
     control removed**; the row now reads cleanly without the
     under-input height jitter.
  9. ✅ **"Free from ingredient(s)" replaced by a "Doesn't use"
     stock-item picker** (+/- partner to "Uses ingredients" — same
     option source, same search UX). Trades free-text fuzziness for
     an exact stock-item exclude; users who want raw-text exclude
     can ask if they hit a real gap.
  10. ✅ **"Uses stock items" → "Uses ingredients"** label rename.
  11. ✅ **Read-only "Last cooked" card** added on the recipe detail
      page sidebar (under the cookable card); reads
      `recipe.last_made_on` and shows "Never" when null.
- **Files touched:** `pages/RecipesOverview.vue`,
  `pages/RecipeDetailPage.vue`, `components/RecipeCard.vue`.
- **Unblocks:** nothing specific; the cookbook overview UX gripes
  are now closed.

## [RESOLVED] FU-080 — Browser-verify the menu-highlight subroute fix
- **State note:** 2026-06-09 — user confirmed in browser: menu highlighting works on subroutes. ✅
- **Raised:** 2026-06-09 (after the menu-highlight fix landed)
- **Type:** follow-up / browser verification
- **What:** The fix moves main + side menu active-state from Vue-Router's route-record matching to a path-prefix composable (`useMenuLinkActive.ts`), and re-targets the "Recipes" menu link from `/recipes` (redirected) to `/cookbook` with `activePrefixes: ['/recipes']`. Confirm in browser:
  1. Each top-nav button highlights on its base path **and** on every subroute it owns: `/stock/:id` under Stock; `/cookbook` + `/recipes/:id` + `/recipes/:id/cook` under Recipes; `/shopping-lists/:id` + `/shopping-lists/:id/shop` under Shopping Lists; `/meal-plans` subroutes; `/data/*` (Data menu has /backup, /import, /export, /barcodes); etc.
  2. The sliding accent-coloured indicator on `MainMenuButtonStrip` still tracks position when navigating between sections.
  3. SideMenuButton (hamburger drawer) highlights correctly on subroutes too (the `exact` prop was dropped).
  4. No double-highlight: only the *most specific* match should look active. Path prefix is greedy by design — `/data` would match `/data/backup`, which is desired; but verify no two sibling links both match the same URL.
- **Recommended resolution:** now/when next in the app — quick visual sweep.
- **State note:** not yet verified.

## [RESOLVED] FU-079 — Confirm hotfix resolves the blank-screen report
- **State note:** 2026-06-09 — user confirmed: can navigate to `/shopping-lists` and Detail renders correctly. Hotfix verified in browser.
- **Raised:** 2026-06-08 (user reported blank screen on /shopping-lists with no console errors)
- **Type:** follow-up
- **What:** A hotfix landed in this session: Overview + Detail now surface `loadError` via banners with Retry buttons, the store explicitly `console.error`s API failures, Detail's FadeTransition gained a v-else "list isn't available" fallback so the content area is never blank, and three lint errors were cleared (duplicate v-else-if, dead `onFinish`, floating-promise on Esc).
  - **Leading suspect for the original blank screen:** the `e1a4c7b2f9d0` migration (Chunk 7 `planned_shop_date` column) was not applied on the user's Linux machine. The API's `SELECT` on `ShoppingList` would 500 with "no such column"; the store caught silently; the UI rendered nothing.
- **Recommended resolution:**
  1. Pull the hotfix.
  2. `alembic upgrade head` to apply `e1a4c7b2f9d0`.
  3. Restart the API + Quasar dev.
  4. Navigate to `/shopping-lists`. Confirm: either the redirect to a list works, or the new red banner shows an actual error message (no more blank).
  5. Open the browser dev console — any `[shoppingListStore] refreshAsync failed` lines surface what's actually broken.

## [RESOLVED] FU-078 — Write IMPL plan for C-4 cookbook
- **Raised:** 2026-06-08 (after FU-077 closed)
- **Type:** follow-up
- **What:** Natural next document after the C-4 design decisions closed (PROPOSAL_COOKBOOK §5a) — chunked IMPL plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` and `IMPL_PLAN_COOK_MODE.md`. Bigger than C-3 (nine design sections, ~10 chunks expected).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOKBOOK.md` (10 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run order). All 6 open decisions had been closed in PROPOSAL_COOKBOOK §5a beforehand; DEC-2 deviated meaningfully from the brief (siblings via `version_group_id` instead of snapshot+pointer) and the plan reflects the user's flatter model. Wired into the doc-graph (new C-impl row + cross-map row).

## [RESOLVED] FU-077 — Write IMPL plan for C-3 cook-mode
- **Raised:** 2026-06-08 (C-3 decision pass)
- **Type:** follow-up
- **What:** With C-3's open decisions resolved (`PROPOSAL_COOK_MODE.md §5a`) and the structured-steps dependency homed in C-4 (`PROPOSAL_COOKBOOK.md §2.6a`), the natural next document is an implementation plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` — chunked, self-contained, no code. Chunks suggested by C-3 §6 + §5a: (1) finish-flow + click-out + celebration + meals-cooked-from-zero, (2) timer polish + unit fix + sous-chef discoverability, (3) location grouping + ingredient-UI rebuild, (4) structured-steps (lives in C-4 but lands as a co-sequenced cook-mode-blocker), (5) highlight-instead-of-tick + per-step tools + per-step hints + per-step timers, (6) serving auto-adjust (gated on C-5 onboarding default).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOK_MODE.md` (6 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run-order). Wired into the doc-graph (new C-impl row + cross-map row for the IMPL plan). Open decisions all closed in PROPOSAL_COOK_MODE §5a; no co-design questions remain for the implementation phase.

## [RESOLVED] FU-070 — `goBack()` in Detail is now a self-bounce
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX)
- **What:** The back-arrow in `ShoppingListDetail.vue` pushes `/shopping-lists`, which the new router landing immediately `replace`s back to a chosen list — usually the same one. So the back button now effectively no-ops (or, worse, picks a different list than the user expected). Two reasonable resolutions: (a) point it at `/`, or (b) drop the button entirely now that the in-page list selector exists.
- **State note:** 2026-06-08 — resolved option (b) in Chunk 6: dropped the `<BaseButton variant="icon">` back-arrow + the `goBack()` function from `ShoppingListDetail.vue`. The in-page list selector replaces it; the sidebar nav still exits the shopping-lists surface.

## [RESOLVED] FU-067 — Drop unused `appendLowStockEssentialsAsync` endpoint
- **Raised:** 2026-06-08 (Chunk 4 impl)
- **Type:** finding (R-007 scope-discipline housekeeping)
- **What:** The detail page's "Append low + essentials" menu (the 5th of the proposal's five doors) is gone, but the underlying API method `appendLowStockEssentialsAsync` and its backend route `/shopping-lists/{id}/append-low-stock-essentials` were still present with no UI consumer. The unified `New list` dialog covers the same use case via *auto-fill: low + flagged + essentials-only + merge into this list*.
- **State note:** 2026-06-09 — resolved. Confirmed via static grep the frontend method had zero callers, then removed the `append_low_stock_essentials` route/handler from `features/shopping_lists/auto_generate.py` and the `appendLowStockEssentialsAsync` method from `shoppingListApiService.ts`. No orphaned imports (`AutoGenerateSources/Request`, `not_found`, `AutoGenerateResult` all still used elsewhere). Static-only; not run.

## [RESOLVED] FU-059 — Shopping-list line tick/delete always 404'd (UUID-vs-str guard)
- **Raised:** 2026-06-07 (P6-01 Chunk 1 — surfaced by new lifecycle e2e)
- **Type:** finding → fixed this session
- **What:** `update_line` / `delete_line` in
  `dora_api/features/shopping_lists/manage_shopping_list_lines.py` guarded parent
  ownership with `line.shopping_list_id != shopping_list_id`. The entity FK is a `UUID`;
  the Flask path param is always a `str` (no uuid converter registered), so the
  comparison never matched and **every** PATCH (tick/qty/select) and DELETE on a line
  returned 404. Pre-existing since the file was created (commit `fa399e2`); no e2e
  covered it until now. The frontend (`shoppingListApiService.updateLineAsync`) hits
  exactly this route, so in-store ticking would have been broken in the running app.
- **Resolved (symptom):** compared as strings (`str(...) != str(...)`) in both guards,
  with an inline comment. Verified by the new e2e `test__finish_then_reopen…` (which
  ticks a line). **Still worth a browser confirm** of shop-mode ticking.
- **R-010 carve-out / leftover:** the `str()`-both-sides fix is the symptom fix the new
  rule R-010 warns against — it keeps the ids weakly typed. The *root* fix is to coerce
  the path params to `UUID` once at the route boundary (matching the codebase's existing
  `UUID(raw)` idiom) so the comparison is typed. Deferred to avoid scope creep this
  session; do it opportunistically when next touching `manage_shopping_list_lines.py`
  (and audit sibling line routes for the same coercion).

## [RESOLVED] FU-058 — Finish snapshot captured no level_restores (noload relationship)
- **Raised:** 2026-06-07 (P6-01 Chunk 1)
- **Type:** finding → fixed this session
- **What:** the Finish handler captured each restocked item's prior level by reading
  `item.stock_level` (the relationship). That relationship is mapped `lazy="noload"`
  (`table_mappings.py`), so it returns `None` unless eager-loaded — meaning
  `finish_snapshot.level_restores` was always `[]` and Reopen restored nothing (status
  flipped back but levels stayed Well-Stocked).
- **Resolved:** the Finish query now `.include("stock_level")` before reading the prior
  level. Verified by the new e2e (reopen restores Out-of-Stock). R-003 (server-owned
  undo) now actually holds.

## [RESOLVED] FU-055 — P6-02 barcode/QR: design pivoted; build-vs-defer decision pending
- **Raised:** 2026-06-07 (P6-02 design discussion)
- **Type:** deferred job (blocked on user decision)
- **State note:** RESOLVED 2026-06-07 — user chose Option 1 ("Cleanup now, UI later").
  Dropped `StockItem.barcode` (col/routes/UI/DTOs/export), kept `ProductBarcode` +
  Dora QR, added off-by-default `scanning_enabled` flag gating the whole surface,
  relabelled honestly, wrote `PROPOSAL_BARCODE_SCANNING.md`, reworded CLAUDE.md. The
  EAN question is answered (Product has no EAN, only `merchant_stockcode`) →
  register-against-product UI + ingestion auto-populate deferred to Phase 2 ([[FU-056]]).
  See WORKLOG 2026-06-07 "P6-02 barcode/QR — IMPLEMENTED".
- **What:** P6-02 was going to be "remove real-world barcodes wholesale, keep only Dora QR"
  (legacy spec). A design discussion **changed the shape**: `ProductBarcode` (barcode→Product)
  is the CORRECT model and is KEPT; `StockItem.barcode` (one barcode per item) is the WRONG
  model and is DROPPED. Real-world-barcode scanning becomes a *navigation* aid (scan product →
  open linked stock item), complementary to Dora QR (for unbarcoded/loose items), both opt-in /
  off-by-default, never live deal-lookup. **Full context + the verified code map + the resolved
  decisions are in the DORA_WORKLOG.md entry dated 2026-06-07 "P6-02 barcode/QR — DESIGN
  DISCUSSION".**
- **Resolved already:** flag = install-wide `AppSetting` (`scanning_enabled`, default false);
  recommend ONE flag for the whole surface.
- **OPEN — ask the user first:** how much to build *now* vs defer? (1) [recommended] cleanup +
  gate now, defer the register-against-product UI to Phase 2 (auto-populate from scraped EANs);
  (2) build the full vision now; (3) pause and write the proposal/CLAUDE.md update first.
- **Also verify:** does scraped Product data carry an EAN today? (Only `merchant_stockcode`
  seen.) Determines whether auto-populate is feasible / whether to defer the register UI.
- **Doc changes agreed-in-principle (not yet done):** reword CLAUDE.md "Removed features" P6-02
  line (deal-lookup stays removed; ProductBarcode-as-navigation kept; StockItem.barcode dropped);
  write `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md`.
- **Recommended resolution:** **now** — first user message next session.

## [RESOLVED] FU-054 — Shop-mode + lists-overview still sum line prices client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Both turned out to operate on a
  single fetched detail (shop-mode = the open list; overview `loadPrimaryStats` =
  the *primary* list — not multi-list), so they now read `detail.totals` (added in
  Chunk 5) directly. Removed the client sums + the unused `priceOfLine`/
  `savingsOfLine` imports. Per-line `priceOfLine` display retained in the detail page.
- **What:** Chunk 5 moved *whole-list* totals to the server (`ShoppingListDetailDto.totals`)
  and switched the dashboard + detail page to read them. Two surfaces still sum
  `priceOfLine`/`savingsOfLine` client-side: `ShoppingListShopMode.vue:408-411`
  (sums over `sortedLines`/`remainingLines` — *subsets*, possibly route-ordered, so
  not a straight `detail.totals` read) and `ShoppingListsOverview.vue:522-525` (sums
  per-list across *multiple* lists in the overview — the overview may not fetch each
  list's full detail, so it has no `totals` to read).
- **Why deferred:** subset/multi-list summation needs either per-list-summary totals
  on the lists endpoint (so the overview shows totals without full details) or
  careful subset handling in shop mode — bigger than the named flagship (R-007).
- **Recommended resolution:** **opportunistic / fold into the shopping-list redesign
  pass** — expose per-list totals on the shopping-list *summary/list* endpoint for the
  overview; for shop mode decide whether its subset totals can read `detail.totals` or
  genuinely need a filtered sum. Per-line `priceOfLine` display stays client-side
  (accepted Type-C).

## [RESOLVED] FU-053 — "Best deals" card still fetches all products + sorts by discount client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B / proposal §8.2)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Added `GET /api/products/best-deals?limit=N`
  (`GetBestDealsHandler`, ranks on-special products by discount % server-side via the
  new `dora_api/domain/product_offer.discount_percent`); the dashboard queries it for
  the top 3 instead of downloading all products. Inline `discountPctFor` removed; the
  `% off` badge uses the shared `discountPercent` (widened to accept a `Product`).
  Future optimisation (noted, not done): a SQL `ORDER BY` on the discount expression
  instead of loading all products + ranking in Python — fine at current scale.
- **What:** The dashboard "best deals" card (`DashboardPage.vue` `bestDeals` ~L1190,
  `loadProducts` fetches *all* products via `GET /api/products`) filters + sorts by
  discount % in the browser and slices top-3. The discount-% is computed inline
  (`discountPctFor`) duplicating the shared `scrapedProductOfferLogic.discountPercent`
  (a tiny Type-C dup). Proper fix (proposal §8.2): a `?sort=discount&limit=N`
  (or focused best-deals endpoint) so the server sorts and returns only the top N.
- **Why deferred:** `price_now`/`price_was` come from the joined `Product.current_offer`,
  not Product columns, so sorting by `(price_was - price_now)/price_was` is a derived
  expression over a join — the generic field-based sort in `get_products.py` doesn't
  support it. That's a distinct capability (expression order_by + the on-special filter
  + null-RRP handling), riskier than the Chunk-5 flagship and best done deliberately.
- **Recommended resolution:** **later — a focused "best deals query" unit.** Add
  discount-sort support (or a `/products/best-deals?limit=N` endpoint) computing the
  discount server-side; switch the card to query it; fold `discountPctFor` onto the
  shared helper at the same time. Until then the card works (just over-fetches).

## [RESOLVED] FU-040 — C-4 should model structured recipe steps (C-3 depends on it)
- **Raised:** 2026-06-06 (C-3 brief)
- **Type:** follow-up (design dependency)
- **What:** Recipe instructions are a freeform text blob (`recipe.py` instructions;
  cook mode splits on newlines, `RecipeCookMode.vue:356-363`). Cook mode's richer
  per-step features — reliable ingredient highlighting (instead of fragile
  text-match), per-step tools, per-step hints, per-step timers — all need
  **structured steps** (step = text + optional sub-steps + hint + the
  ingredients/tools it uses). This is a recipe-model change that belongs in **C-4**
  (adjacent to its multi-part "sections"), not cook mode.
- **State note:** 2026-06-08 — resolved at the design level: C-3 DEC-2 chose "Structured steps in C-4 + remove ticks", and `PROPOSAL_COOKBOOK.md §2.6a` was added with the model (`RecipeStep`: text, sub_steps, hint, ingredient_refs, tool_refs), the editor + importer story, and a §6 sequencing slot (item 5a) flagging it as a blocker for C-3 highlight/per-step features. Freeform recipes degrade gracefully. Code implementation is still outstanding (no model migration written yet) — flip to a fresh implementation FU when work begins.

## [RESOLVED] FU-039 — Wire up `Recipe.image` (parallels StockItem.image)
- **Raised:** 2026-06-06 (C-4 brief)
- **Type:** deferred job
- **What:** `Recipe.image` was a dead field. C-4 Chunk 5 (L249) wires it end-to-end.
- **State note:** 2026-06-09 — implemented (static-only; browser-verify in FU-091).
  **Pattern pioneered (FU-033 StockItem.image should follow it):** the image is
  stored as a **data-URL string** (UTF-8 bytes) in the existing LargeBinary
  column; create/update accept an `image` data-URL field (6M-char cap); a new
  `GET /api/recipes/<id>/image` parses the data URL and returns raw bytes +
  mimetype; the list/detail DTOs carry only `has_image: bool` (no inlined
  base64); the SPA renders via `<img src=recipeImageUrl(id)>` (cache-busted on
  the detail page after save) with a coloured-initial placeholder fallback.
  Reusable `RecipeImageField.vue` handles pick/preview/clear.
  See [[stockitem-image-substitute-notes-intent]].

## [RESOLVED] FU-038 — Cart button fires contradictory double-toast on already-on-list
- **Raised:** 2026-06-06 (C-7 brief; feedback L154)
- **Resolved:** 2026-06-12 by Cart Button Chunk 1. The blind re-add
  path is gone — already-on-list now **toggles** (remove silently on
  1 list; popover with explicit Remove / Add-to-another on 2+). No
  more "0 added, 1 already on list" + "Added to your primary list"
  collision because the button never fires the add path when the
  item is already on a list. Static-only impl; browser-verify is
  **FU-127**.

## [RESOLVED] FU-036 — Confirm Shop Mode "Substitute" swaps offer-only (gates INV-8)
- **Raised:** 2026-06-06 (INV-8)
- **Type:** finding
- **What:** Static read said Shop Mode's "Substitute" button swapped the
  **merchant offer**, while the permanent stock-item substitute swap lived in
  the full-list per-line menu. INV-8's "rework into Shop Mode" recommendation
  hinged on confirming this in-browser.
- **Resolved:** 2026-06-13 — moot after the Fable 5 shopping-list rework
  (commit `d9ca58e`). The standalone `ShoppingListShopMode.vue` surface no
  longer exists; the unified `ShoppingListDetail.vue` flow now hosts the
  substitute swap (`onSwapSubstitute`, line 729 / 1791), so there is no
  separate Shop-Mode "Substitute" button to confirm. User confirmed current
  UI feels fine.

## [RESOLVED] FU-035 — Stock overview silently shows only the first 50 items
- **Raised:** 2026-06-06 (INV-2)
- **Type:** finding (real bug)
- **What:** `stockItemStore.getStockItemsAsync` paged once and ignored
  `page.total`, so pantries with >50 items lost the tail.
- **Resolved:** 2026-06-12 by Stock Overview Chunk 1 — added
  `stockItemApiService.getAllPagesAsync()` (loops until a short page
  or `total` is reached, asks for `limit=500` per call), and switched
  the store to use it. Pairs with `q-virtual-scroll` so the now-larger
  list still renders smoothly. Browser-verified 2026-06-12 (user
  confirmation via FU-120) — works as intended.

## [RESOLVED] FU-033 — Wire up `StockItem.image` (own image + product fallback)
- **Raised:** 2026-06-06 (INV-1)
- **Resolved:** 2026-06-12 by Stock Overview Chunk 6. End-to-end:
  - Backend: `image` column deferred on the mapping (list endpoint
    no longer pulls megabytes per row). New `has_image` field on
    `StockItemDto` + `StockItemDetailDto`, hydrated by a single bulk
    SELECT that **OR**s the item's own image with any linked
    product's image — so the SPA's "show thumbnail?" decision
    matches what the bytes route will serve. New
    `GET /stock-items/<id>/image` route mirrors the recipe-image
    pattern; resolves own-image first, falls back to the first
    linked product that decodes cleanly, 404s if both miss.
  - Backend: `CreateStockItemRequest` and `UpdateStockItemRequest`
    accept `image` as a data-URL string (~6 MB cap); update treats
    explicit null as "clear".
  - Frontend: new `stockItemImageUrl(id, version?)` helper; row
    renders `<img>` with placeholder fallback (gated on
    `showStockImages`); `StockItemDetailPage` overview tab gets a
    `RecipeImageField` (reused, R-001) that saves immediately and
    bumps an `imageVersion` to bust the browser cache.
  - Static-only impl; browser-verify is **FU-125**.

## [RESOLVED] FU-030 — Fullscreen 404 page redesigned (login-theme + Dora pic)
- **Raised:** 2026-06-06 (B9.9; user follow-up 2026-06-12: "page
  looks a bit boring, maybe use the login theme instead and add a
  suitable dora pic")
- **Resolved:** 2026-06-12 — rewrote `pages/ErrorNotFound.vue` to
  mirror `LoginPage.vue`'s "off-app" treatment: three drifting
  mesh-gradient blobs (magenta / dora amber / mint), floating
  mascot using `dorabot-fatal-error-or-offline.png`, glassy card
  with gradient "404", "This page wandered off" headline, and a
  "Take me home" CTA. Locally-scoped CSS variables (forced light
  tokens) for the same reason LoginPage does it — 404 can render
  pre-auth and `data-theme` can flip dark before sign-in.
  Respects `prefers-reduced-motion`. `ErrorPageNotFound.vue` (the
  in-layout variant via `PageErrorState`) was already themed and
  stays untouched.

## [RESOLVED] FU-029 — B9.4: confirm command-palette commands all trigger
- **Raised:** 2026-06-06
- **Resolved:** 2026-06-12 — **command palette retired entirely.**
  User assessed the palette as low-value for Dora's audience
  (pantry / mobile, not keyboard-power-user); ripped out the UI
  + commands registry. Files deleted:
  `web_app/src/components/CommandPalette.vue`,
  `web_app/src/composables/useCommandPalette.ts`,
  `web_app/src/composables/useCommands.ts`,
  `web_app/src/composables/useRecents.ts`. MainLayout pruned
  (the Ctrl/Cmd-K trigger, lazy mount, and the 18-item
  `useCommands([...])` registry are gone, along with the
  `autogenerateFromLowStock` / `openPrimaryList` /
  `openPrimaryShopMode` palette-feeder functions). **The
  `useShortcut` registry stays** — `?`, `/`, `g s`/`g l`/`g r`
  /`g d`/`g h` etc. all still work; `ShortcutsCheatsheet` is
  still mounted. With the palette gone, verifying its commands
  is moot.

## [RESOLVED] FU-028 — B9.1: confirm shopping-list drag-drop ordering
- **Raised:** 2026-06-06 (B9.1; CLAUDE.md confirm-in-browser rule)
- **Resolved:** 2026-06-12 — user verified in browser. Reorder both
  directions lands at the dashed-outline position. The static-read
  insertAt math (`fromIdx < toIdx ? toIdx - 1 : toIdx`) matches live
  behaviour.
- **Type:** finding

## [RESOLVED] FU-022 — Confirm A4 reported filter bug did NOT reproduce
- **Raised:** 2026-06-05 (A4; back-filled per the non-issue rule)
- **Resolved:** 2026-06-12 — user verified in browser. Clearing filters
  on each of StockOverview / RecipesOverview / MyProductsPage /
  ProductSearch correctly returns all rows; the reported "everything
  filtered out on empty" symptom does not reproduce. A4's explicit
  `!== null` hardening is belt-and-braces.
- **Type:** finding

## [RESOLVED] FU-021 — Confirm A3 reported modal bug did NOT reproduce
- **Raised:** 2026-06-05 (A3; back-filled per the non-issue rule)
- **Resolved:** 2026-06-12 — modal backdrop/Esc-cancel behaviour confirmed
  fine in browser (cf. FU-007 verification). However, the user found a
  **different** escape route around the unsaved-changes guard: navigating
  via the **main menu bar** bypasses the prompt entirely (leaves the page
  / changes routes within the app without firing the guard). The original
  modal-misbehaviour symptom is gone; the menu-nav bypass is a separate
  real bug and is tracked on its own as **[[fu-156]]**.
- **Type:** finding

## [RESOLVED] FU-019 — Confirm B8 reported defects that did NOT reproduce (per-defect)
- **Raised:** 2026-06-05 (B8)
- **Resolved:** 2026-06-12 — user verified in browser. (a) un-favourite
  persists, (c) all recipe actions fire. (b) was originally described as
  "no related-recipes section in the UI" — the user has since located one
  on the **stock item detail page** (related-recipes tab) and the nav
  bug *is* real there. That carve-out is spun out to **[[fu-155]]** to
  track on its own; the remaining (a)/(c) confirmations close this one.
- **Type:** finding

## [RESOLVED] FU-017 — B3: user re-test "can't save unless I change the name"
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Resolved:** 2026-06-12 — user confirmed in browser; edits save without
  needing a name change. Static reading of the update handlers (PATCH +
  `model_fields_set` + exclude-self uniqueness) matched live behaviour.
- **Type:** open verification

## [RESOLVED] FU-007 — Eyeball A3 modals in a real browser
- **Raised:** 2026-06-05 (A3)
- **Resolved:** 2026-06-12 — user spot-checked various A3 modals in browser
  (including delete-confirm dialogs and sizing-fix cards); backdrop+Esc cancel
  cleanly without committing, cards render correctly.
- **Type:** leftover
- **What:** A3 was verified statically only — `node_modules` isn't installed in
  this checkout, so no lint / `quasar build` / dev-server run happened. Need to
  confirm backdrop+Esc dismiss without committing, and that the comparison /
  orphans / quick-add cards (scoped-class → `card-style` fix) still size right.

## [RESOLVED] FU-001 — "Flat danger" BaseButton variant for low-emphasis deletes
- **Raised:** 2026-06-04 (A2 Phase 2)
- **Type:** follow-up
- **What:** A2 left flat-negative delete buttons as raw `q-btn` because BaseButton
  had no flat-danger shape.
- **Why deferred:** needed a new BaseButton variant.
- **State note:** RESOLVED 2026-06-05 — `danger-ghost` variant added
  (`{ flat: true, color: 'negative' }`) and wired into `StockItemDetailPage`
  (Delete + clear-expiry) and `MealPlansOverview` (Delete plan).
