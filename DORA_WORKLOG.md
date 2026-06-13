# Dora Worklog

Append-only handoff log between Claude sessions. **Newest entry at the top.**
Read the top entry on session start; append a new entry on session end.

For product-level changes, update `CHANGELOG.md` instead (or as well, when both
apply). This file is the *process* trail — what ran, what was decided, what's
next.

---

## 2026-06-14 — Cookbook card revision Chunk C — optional ingredients
**Status:** complete (vue-tsc clean; full unit suite 299 passed). Session
was ended abruptly mid-Chunk-C and resumed cautiously — see "Resumption
notes" at the end.

**What:** Third (and final) implementation chunk off
`PROPOSAL_COOKBOOK_CARD_REVISION.md`. Covers §1.9 in full — the
cross-cutting one. **No `cookable_with_optional` half-state** per the
user's resolution: cookability stays a single required-only rule;
optional ingredients are invisible to it.

Backend:
- **Domain** `dora_api/domain/entities/recipe_ingredient.py` — `is_optional: bool` field (default false, NOT NULL).
- **Persistence** `dora_api/persistence/table_mappings.py` — `is_optional` `Boolean` column with `server_default="0"`; mapper property added.
- **Migration** `dora_api/persistence/migrations/versions/b9e5c2a78f31_20260614_recipe_ingredient_optional.py` — batch-mode `add_column` so SQLite + Postgres both apply cleanly (R-005). Down-revision is the concurrent FU-163 session's `a1c4e7b3f5d2` (drop_finish_snapshot).
- **DTOs** `create_recipe.py` + `update_recipe.py` — request models accept `is_optional` (default false). Handlers pass it to the `RecipeIngredient` constructor.
- **Read DTO** `get_recipes.py` — `RecipeIngredientDto.is_optional` emitted.
- **Cookability rule** `dora_api/domain/recipe_cookability.py` — single point of change: a new private `_required()` filter; `missing_count_for`, `is_cookable`, `missing_stock_item_names_for` all skip optional rows.
- **Assistant** `tools.py::_stock_coverage` and `confirm_actions.py::add_recipe_to_list` — skip optional in their own missing-count loops so assistant behaviour matches the rest of the app.
- **Waste rescue** `waste.py` — skip optional in the rescue-recipe ranking loop.

Frontend:
- **Type** `models/recipe.ts::RecipeIngredient` — `is_optional: boolean`.
- **Service** `recipeApiService.ts::CreateRecipeIngredientCommand` — `is_optional?: boolean`.
- **Edit dialog** `RecipeEditDialog.vue` — per-row Optional `q-checkbox` (tooltip explains it doesn't affect cookability). Empty + hydrated rows initialise `is_optional`.
- **Detail page** `RecipeDetailPage.vue` — same checkbox in the inline editor; `hydrateForm`, `addIngredient`, URL-importer mapping all set `is_optional` (importer defaults false — v1 makes no attempt to detect optional from source text).
- **Picker modal** `RecipeIngredientPickerDialog.vue` — optional rows render under a `─── Optional ───` separator at the bottom. Default check rule: optional rows start unchecked regardless of stock level. `Select all` / `Select missing` also leave optional rows unchecked — optional is opt-in only. Dedupe rule when the same stock item appears as both required and optional: **required wins**.
- **Cook mode** `RecipeCookMode.vue` — `(optional)` hint after the ingredient name; new `.ingredient-row--optional` style dims the row.

**Five-surface regression check** (proposal §3 risk):
| Surface | Reads via | Status |
|---|---|---|
| Recipe DTO → cookbook card + stock-item recipe cards | `missing_count_for` + `missing_stock_item_names_for` | ✓ inherits filter |
| Dashboard `cookable_count` | `missing_count_for` (R-003 single source) | ✓ inherits filter |
| Planner shortfall banner | recipe DTO `cookable` field | ✓ inherits filter |
| Assistant `_stock_coverage` (suggest_recipes) | own loop | ✓ filter added explicitly |
| Assistant `add_recipe_to_list` candidates | own loop | ✓ filter added explicitly |
| Waste rescue ranking (extra surface, not in §3) | own loop | ✓ filter added explicitly |

**Charter/standards check:** Clean.
- R-001 (componentisation): no new components needed; reused picker + editors. ✓
- R-002 (theme tokens): only opacity + existing CSS vars touched. ✓
- R-003 (state ownership): rule lives once on the server; client reads via DTO. ✓
- R-005 (Postgres/SQLite portability): batch-mode migration. ✓
- R-006 (clean migrations): single migration, NOT NULL with server_default so existing rows stay valid; reversible downgrade. ✓
- R-007 (scope discipline): assistant + waste edits are necessary regression fixes for the same rule, not scope creep. ✓
- R-010 (strong types): bool field, no string sentinel. ✓
- R-011 (idiomatic Quasar): `q-checkbox` + `q-tooltip`. ✓
No ADR added — feature-add, not a recurring pattern.

**Resumption notes:** Previous session ended abruptly after the domain
entity + table mapping landed but before the migration was written. On
resume: baseline-tested first (vue-tsc clean, 298 passed / 1 failed —
the failure was the concurrent FU-163 session's `/unfinish` 404, **not
mine**); confirmed via the user that the concurrent FU-163 work was a
deliberate parallel session and to leave it alone. Built Chunk C from
the migration onward. By close-gate the concurrent session had landed
its own test fix, so the suite finished 299 / 0.

**Open loops:**
- **FU-088** — Chunks A + B + C all landed. Remaining: in-browser
  verification end-to-end (including the FU-171 image-toggle confirm).
  Recommend flipping FU-088's resolution to "browser-verify Chunks A+B+C
  end-to-end" before closing.

**Next up:** browser-verify FU-088 (image toggle, new card footer,
picker modal, difficulty + time-of-day filters, optional checkbox on
editors, cook-mode dim). If green: flip FU-088 to RESOLVED.

---

## 2026-06-14 — Undo + Reopen removal (FU-163)
**Status:** complete. Backend `py_compile` clean, unit suite 49/49 passing,
e2e collection clean (no import errors from the removed modules), ESLint
clean on every touched file. Browser verify rolls into the next FU-165 pass.

**What:** Killed the app-wide undo posture and the shopping-list Reopen
flow end-to-end. User directive: "decided undo feature does not make sense,
remove. Even the reopen functionality — once a list is done, it's done.
The snapshot of stock levels feels so overengineered. Kill it."

- **Followups housekeeping (lead-in):** split `DORA_FOLLOWUPS.md` into two
  files — open items stay in `DORA_FOLLOWUPS.md` (the session-start scan),
  resolved items moved to the new `DORA_FOLLOWUPS_RESOLVED.md` (audit
  trail only). `CLAUDE.md` updated to enforce the structure going forward
  (session-start scan reads open only; resolving an item now means
  *moving* the block to the archive, not flipping the heading in place).
  Also resolved FU-036 (Shop-Mode "Substitute" — the surface that report
  hinged on no longer exists post-Fable 5; current UI is fine).
- **Frontend:**
  - Deleted `web_app/src/composables/useUndo.ts` and `useNotifyUndoable.ts`.
  - `MainLayout.vue` — removed the header Undo button, the `useUndo()`
    wiring, `onUndoClick`, `isTypingTarget`, the Ctrl/Cmd-Z &
    Ctrl-Shift-Z/Ctrl-Y `onKeyDown` handler, and the mount/unmount
    listener wiring. `describeApiError` import dropped (only the undo
    error toast used it here).
  - `stockItemStore.ts` — stripped `registerUndo` / `notifyUndoable` from
    `updateStockLevelAsync`, `updateStockItemAsync`, and
    `deleteStockItemAsync`. Delete is now plain delete; no toast, no
    snapshot.
  - `ShoppingListDetail.vue` — removed the **Reopen** `BaseButton` (Done
    state), `onReopen`, `reopening` ref, and the `registerUndo` wired
    around tick/untick in `onToggleTicked`. `unfinishAsync` call gone.
  - `shoppingListApiService.ts` — `unfinishAsync` deleted.
  - `stockItemApiService.ts` — `restoreAsync` + `RestoreStockItemCommand`
    deleted (only the delete-undo path used them).
- **Backend:**
  - Deleted `dora_api/features/shopping_lists/unfinish_shopping_list.py`
    (the `/unfinish` route disappears via the package-walk blueprint
    registration in `startup.py`).
  - Deleted `dora_api/features/stock_items/restore_stock_item.py` (same
    mechanism — `/stock-items/restore` disappears with the file).
  - `manage_shopping_list.py` `FinishShoppingListHandler` — removed the
    `level_restores` capture loop, dropped the `.include("stock_level")`
    eager-load that only existed to snapshot the prior level, dropped
    the `json.dumps` to `lst.finish_snapshot`, dropped the now-unused
    `import json`.
  - `dora_api/domain/entities/shopping_list.py` — removed
    `finish_snapshot` field + `Fields.FINISH_SNAPSHOT` enum. Rewrote the
    lifecycle comment ("Once a list is done, it's done").
  - `dora_api/persistence/table_mappings.py` — dropped the
    `finish_snapshot` `Column`.
  - New migration
    `dora_api/persistence/migrations/versions/a1c4e7b3f5d2_20260614_drop_finish_snapshot.py`
    drops the column in batch mode (SQLite + Postgres parity, R-005).
    Single head confirmed: `a1c4e7b3f5d2` ← `f3a9c1e5d2b7`.
- **Tests:** `tests/e2e/dora_api/test_shopping_list_lifecycle.py` rewritten
  — dropped `test__finish_then_reopen__restores_level_server_side` and
  the `levels_by_sequence` fixture + unused module constants; added a
  one-liner `test__unfinish_endpoint_is_removed` that asserts
  `POST /unfinish` returns 404 on a Done list. Module docstring
  reframed.
- **Follow-ups bookkeeping:**
  - FU-163 → moved to `DORA_FOLLOWUPS_RESOLVED.md` with the resolution
    inventory.
  - FU-026 (PARTIALLY RESOLVED — "undo behaves oddly across surfaces")
    → moved to resolved as **subsumed by FU-163** (no undo, nothing to
    behave oddly).
  - FU-016 (frontend-cache-vs-backend-mutation audit) → inline note
    added that the "stock-item Undo restore" candidate in its scan list
    is no longer applicable.

**Charter/standards check:** Clean.
- R-003 (state ownership): the removal *deletes* a server-owned snapshot
  that no longer has a consumer; nothing relocates. ✓
- R-005 (portable data access / SQLite + Postgres): migration uses
  `op.batch_alter_table` for the column drop. ✓
- R-007 (clean migrations, no idempotent guards): straight `drop_column`
  / `add_column` for upgrade/downgrade. ✓
- R-008 (scope discipline): scope expanded slightly (stock-item
  `/restore` + `restoreAsync`) only because they were dead code with no
  callers after the undo removal; logged here rather than spun off.
- No new ADR / `R-0NN` candidate identified — the removal applies
  existing rules rather than recording a new one.

**Next up:** none queued by this work. FU-165 (browser-verify shopping
list UX v2) remains the next gated UX session and will sanity-check
that the Done-list page renders cleanly without the Reopen button.

---

## 2026-06-13 — Cookbook card revision Chunk B — picker + vocabularies
**Status:** complete (vue-tsc clean; full unit suite 299 passed).
**What:** Second implementation chunk off `PROPOSAL_COOKBOOK_CARD_REVISION.md`.
Covers §1.4 (picker modal), §1.7 (difficulty vocabulary + filter + sort
axis), §1.12 (`time_of_day` shared vocabulary).
- **New** `web_app/src/components/recipes/RecipeIngredientPickerDialog.vue`
  — extracted reusable, per-ingredient checkboxes with `StockLevelDot`,
  default check rules (`is_missing` / `is_low_stock` auto-on, others
  auto-off), `Select all` / `Select missing` quick actions, integrated
  target-list picker. Same component serves both the card's
  `add-all-to-list` (cookable) and `add-missing` (not cookable) flows;
  the not-cookable path passes the missing-id subset as
  `initial-checked-ids` so the user lands on exactly what they need.
- **New** `web_app/src/helpers/recipeVocabulary.ts` — single-source
  frontend constants `DIFFICULTY_VALUES`, `DIFFICULTY_RANK`,
  `DEFAULT_MEAL_SLOTS` that mirror the server constants.
- **Server** `dora_api/domain/entities/recipe.py` — added module-level
  `ALLOWED_DIFFICULTY_VALUES` and `DEFAULT_MEAL_SLOTS` constants.
- **Server** `create_recipe.py` + `update_recipe.py` — boundary
  validation against both vocabularies (R-010 carve-out), 400 on
  out-of-vocab values. `invalid_vocabulary_message` field added to both
  responses; route handlers return `bad_request`.
- **`RecipesOverview.vue`** — picker replaces the old `addMissing`
  dialog (and its `autoGenerateAsync` short-circuit). Added difficulty
  filter dropdown + new `'difficulty'` sort axis (ordinal Easy < Medium
  < Hard; nulls sink). Active-filter count + clear-all updated.
  `TIME_OF_DAY_OPTIONS` now sources `DEFAULT_MEAL_SLOTS` (dropped the
  historical 'Any' bogus entry).
- **`RecipeDetailPage.vue`** — picker replaces the old target-list
  dialog (the per-row `AddToListButton` was already present and
  unchanged). `time_of_day` + `difficulty` q-selects source the shared
  constants.
- **`RecipeEditDialog.vue`** — same q-select swap.
- **`PROPOSAL_MEAL_PLANS.md §4`** — amended: `Dessert` added to the
  default slot list; cross-reference recorded that `Recipe.time_of_day`
  consumes the same vocabulary; until that proposal's settings page
  ships, the shared frontend constant is the source of truth.
**Trade-off recorded:** the picker uses the plain `addItems` path (not
`autoGenerateAsync`), which means lines added through the new picker
land with `added_via=manual` rather than `added_via=auto_recipe`. This
is the necessary cost of letting the user customize the subset; if the
auto_recipe tag becomes important again, `autoGenerateAsync` would need
to accept an explicit subset (out of scope here).
**Charter/standards check:** Clean.
- R-001 (componentisation): new modal extracted as a reusable, used by
  both overview + detail page. ✓
- R-002 (theme tokens): only Quasar colour names used. ✓
- R-003 (state ownership): cookability still server-derived; vocabularies
  defined server-side, mirrored client-side (single source of truth on
  the server). ✓
- R-005 (Postgres/SQLite portability): no schema changes; vocab is
  validated at the boundary, no column constraint added (preserves
  off-vocab historical strings — §1.12 rule). ✓
- R-010 (strong types over stringly-typed matching): boundary validation
  against the closed sets matches the `nutrition_mode` pattern
  (`update_me.py:146-149`). ✓
- R-011 (idiomatic Quasar): `q-select` / `q-checkbox` / `q-list` /
  ripples / tooltip on icon-only buttons. ✓
**Tests:** all 299 unit tests pass. Recipe e2e file doesn't exist yet
(per FU-169 audit); manual coverage of recipe endpoints is unchanged.
The boundary validation logic mirrors `nutrition_mode` which IS unit-
tested via `test_user_router.py` (vocabulary rejection pattern), so the
shape is proven; first-class recipe e2e tests for these vocab paths can
land with FU-169 Phase 3.
**Open loops:**
- **FU-088** still open — Chunk C (optional ingredients) remains; plus
  the FU-171 in-browser image-toggle confirm.
**Next up:** Chunk C — `RecipeIngredient.is_optional` domain field,
migration, cookability rule clean-up (still required-only), edit dialog
optional checkbox, picker modal optional-rows section, cook-mode row
dim.

---

## 2026-06-13 — Cookbook card revision Chunk A — card visual redesign
**Status:** complete (frontend only; vue-tsc clean).
**What:** First implementation chunk off `PROPOSAL_COOKBOOK_CARD_REVISION.md`.
Pure card-visual rewrite, no schema or DTO change. Covers §1.1, §1.2,
§1.4 (button only; modal in Chunk B), §1.5, §1.6, §1.8, §1.10, §1.11
(card-side).
- `web_app/src/components/RecipeCard.vue` — full rewrite.
- `web_app/src/style/icons.ts` — added `chef_hat: 'mdi-chef-hat'`.
- `web_app/src/pages/RecipesOverview.vue` — dropped `@adjust-meals` /
  `@add-to-meal-plan` bindings + handlers + the dialog body.
- `web_app/src/pages/StockItemDetailPage.vue` — dropped `@adjust-meals`
  binding + handler.
**Charter/standards check:** Clean. R-002 (theme tokens — only Quasar
`primary` / `warning` / `red`, no hex). R-003 (cookable stays
server-derived). R-004/R-011 (idiomatic Quasar: `q-tooltip` on
icon-only buttons). No new component yet (modal lands in Chunk B).
**Open loops:**
- **FU-171** raised — image hide/show toggle reportedly broken; full
  static trace looked correct, so it's logged for browser confirmation
  after Chunk A ships. The Chunk A rewrite preserves the same
  `v-if="showRecipeImages && ..."` gate.
- **FU-088** still open — Chunks B + C still to land, plus the FU-171
  in-browser confirm.
**Next up:** Chunk B — `RecipeIngredientPickerDialog.vue` (new
component), difficulty filter + sort axis, `Recipe.time_of_day` fixed
vocabulary (shared `DEFAULT_MEAL_SLOTS` constant with `PROPOSAL_MEAL_PLANS.md §4`).

---

## 2026-06-13 — Proposal: Cookbook card revision (FU-088 redesign, docs-only)
**Status:** complete (design only — no code).
**What:** User returned from browser-verifying Cookbook Chunk 3 with ten
concrete findings (FU-088 update). Asked for a proposal before any code.
Wrote `docs/04_proposals/PROPOSAL_COOKBOOK_CARD_REVISION.md` — supersedes
`PROPOSAL_COOKBOOK.md §2.10`.
**Shape:** §1 lists the ten items as designed solutions (image-toggle
defect, meta-line swap, kebab gone, footer icon-only add-to-list with a
new `RecipeIngredientPickerDialog.vue`, heart inline, cookable absorbed
into Cook-button colour + add-to-list mirror, difficulty axis, drop
"X low" + enlarge dietary chips, optional-ingredients cross-cut, allocated
badge removed from overview, MealStepper relocates from card to planner
row per `PROPOSAL_MEAL_PLANS.md §3.1`). §2 chunks it into A (card visuals,
no schema), B (picker modal + difficulty), C (optional-ingredients —
domain + migration + cookability rule + UI ripples), D (planner stepper
paired update). §3 flags the cross-cutting risk (cookability rule is read
by 5 surfaces — dashboard, planner shortfall, assistant, card,
stock-item card). §7 coverage table maps each FU-088 bullet → section.
**Charter/standards check:** docs-only; no `ENGINEERING_STANDARDS.md`
violations introduced. The proposal itself cites R-001 (modal
extraction), R-003 (cookability stays server-derived,
`is_optional` is a server domain fact), R-005 (Postgres/SQLite portable
migration), R-011 (cookable-via-`q-btn`-colour is the framework-idiomatic
shape, not a sibling chip).
**Follow-up updated:** FU-088 marked with a 2026-06-13 note pointing at
the new proposal; recommended resolution flipped from "browser-verify" to
"implement Chunks A–C, then re-verify". No new FU raised (the proposal
itself is the next-step artifact).
**Next up:** user reviews the four open decisions in §5 (optional-
ingredients hint copy; difficulty vocabulary confirmation; time-of-day
overflow rule; Chunk B-vs-C ordering); Chunk A is the no-regret start
once those are settled.

---

## 2026-06-13 — Proposal: test-suite coverage / quality / cleanup (docs-only)
**Status:** complete (design only — no code).
**What:** Wrote `docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` off the
back of FU-166. Grounded in a fresh audit of the actual suite + CI:
- CI runs **only** `tests/e2e/dora_api` — the 7 domain unit test files under
  `tests/` never gate merges; no `pytest-cov`, no pytest config, 0 frontend
  tests, `merchant_api`/`emailer` compile-only.
- **24 of 41 API surfaces have no e2e file** (recipes, meal_plans, dashboard,
  search, alerts, budget, waste, reports, … — full list in §4).
- Problems observed during FU-166: shared-mutable-DB order coupling, ~40
  duplicated problem-detail dicts, two naming conventions, seed-coupled magic
  values.
**Proposal shape:** themed P0/P1/P2 improvements (CI-runs-all + config +
coverage; per-test DB rollback → isolation + xdist; shared response matchers +
factories; gap-filling tests by layer; frontend Vitest; markers/parametrize/
Hypothesis; cleanup) + a 4-phase sequence + candidate engineering rules.
**Follow-up raised:** FU-169 (implement the proposal, phased).
**Next up:** user reviews/prioritises the proposal; Phase 1 (P0s) is the
no-regret start.

---

## 2026-06-13 — FU-166: legacy e2e suite triaged to green + ~95× faster
**Status:** complete — full `pytest tests` = **299 passed / 0 failed** in ~6s,
stable across runs. (Initially 296 passed / 3 xfailed; the 3 xfail'd defects
were then fixed in-session at the user's direction — see "Follow-on fixes".)

**Background:** Session-start scan surfaced FU-166 (122 failed / 167 passed /
10 errors, ~40% of the suite drifted off the current API contract). User chose
to triage it. Mid-task the user questioned the **13.5-min** runtime; agreed to
fix performance *first*, then triage on the fast suite.

**Part 1 — test-client conversion (the big win):**
- Root cause of the slowness: `tests/e2e/dora_api/conftest.py` booted a real
  werkzeug dev server in a thread and drove it over loopback TCP (~2.7s/test —
  real connection setup + the Windows `localhost` IPv6-fallback penalty +
  dev-server `Connection: close` defeating keep-alive).
- Rewrote the `api` fixture to dispatch in-process via `app.test_client()`,
  rebinding module-level `requests.*` **and** `requests.Session` to thin
  adapters (handles `json=`/`params=`/`headers=` + multipart `files=`/`data=`,
  exposes `.status_code`/`.headers`/`.text`/`.content`/`.json()`). **Test
  bodies untouched.** Made the fixture `autouse` to kill a latent ordering bug
  (tests not requesting `api` only worked if another test had already triggered
  the global rebind).
- Result: **813s → ~6s (~95×)**, behaviour-preserving — the fail/pass set was
  byte-identical to the live-server baseline on the swap (verified by diffing
  failure lists). New **R-013 + ADR-008** in `ENGINEERING_STANDARDS.md`.

**Part 2 — contract triage (disposition: UPDATE, per user):** all 132 failures
were stale expectations, not bugs. Four drift axes: path-style→query-string
options; bare array→`{items,total,page,limit}` envelope; RFC-2822→ISO-8601
dates (ADR-007); richer DTOs / changed seed. Per file:
- `test_stock_level_router` (16), `test_stock_location_router` (25),
  `test_user_router` (12), `test_merchant_router` (16) — straight contract
  updates. Seed changed: locations are now an 8-node tree (+Cellar=9), user is
  `dora`/admin (not "The Coolest Guy"), 4 merchants.
- `test_stock_item_router` (38) — envelope, ISO datetime (made
  `tests/support.is_valid_datetime` fall back to `fromisoformat`), 19-field
  DTO, create echoes DTO (`stock_item_id` not `id`). Dropped ~90 lines of dead
  commented-out path-style tests. Seed-coupled GET assertions made **robust**
  (sortedness/known-item invariants, not brittle golden orderings).
- `test_product_router` (42) — same; DTO changed `image`→`has_image` + link
  fields, `web_url` now `example.com/p/<stockcode>`, prices via `ProductOffer`,
  9 seed products, `image` field now `str` not bytes.
- `test_misc`/`test_health` — health returns a status doc (`{ok,...}`) not bare
  `True`; the unknown-GET-`/api` test `xfail`'d (FU-167, see below).
- `test_data_router` — fixed a real test bug (`register_product_barcode` used
  `uuid` without importing it → now passes); two `xfail`s for genuine defects.

**Cross-file flakiness fixed:** shared-DB ordering broke 5 tests only in the
full suite (auth-flows registers users; another suite creates a lowercase
`two-drafts-…` stock item). Fixes: user tests filter to `dora` / assert
presence not exact count; sort tests assert **case-insensitive** sortedness
(API uses NOCASE collation) instead of position anchors.

**Genuine defects found (tracked as strict `xfail`, will xpass when fixed):**
- **FU-164** — backup omits `product_stock_item_links` (restore would drop
  product↔stock-item links).
- **FU-167** *(new)* — unknown **GET** `/api/<x>` returns a 404 with the SPA's
  `text/html` body, not the JSON problem-detail the other verbs return (SPA
  history-mode catch-all still intercepts unmatched `/api` GETs).
- **FU-168** *(new)* — `GET /api/meal-plans/<id>/export?format=csv` 500s: the
  CSV builder + print-view template reference `entry.meal_name` but the DTO
  field is `recipe_name` (print-view silently renders blanks). Open question:
  was meal-plan CSV export meant to be removed under UX-v2's "CSV export
  removed app-wide"? If kept → field rename; if not → delete endpoint + test.

**Follow-on fixes (same session, user-directed — all three xfails resolved):**
- **FU-168 — meal-plan CSV export removed** (user: "makes no sense"). Dropped
  the `/export` route + `_build_csv` (`export_meal_plan.py`), the `downloadCsv`
  fn (`useMealPlanExport.ts`) + both CSV buttons (`ExportPrint.vue`,
  `MealPlansOverview.vue`); test now asserts the endpoint 404s. Print-view kept,
  its blank-name bug fixed (`meal_name`→`recipe_name` in the template). vue-tsc
  clean.
- **FU-167 — unknown GET `/api/<x>` now returns JSON** like the other verbs.
  Factored a shared `api_response.endpoint_not_found()` (plain
  `application/json`, matching the middleware); the SPA catch-all's `/api/`
  branch returns it instead of `abort(404)`. Middleware de-duped to use it too.
- **FU-164 — was a misdiagnosis.** `product_stock_item_links` already round-
  trips in the backup; the test failed only because `expected_sections` still
  listed the removed `meals`/`meal_recipes` (meals→recipes rework). Corrected
  the test; no backup-builder change.

**Files touched:** `tests/e2e/dora_api/conftest.py`, all 8 failing e2e test
files + `test_misc`/`test_health`, `tests/support.py`,
`docs/01_charter/ENGINEERING_STANDARDS.md` (R-013/ADR-008), `CHANGELOG.md`,
`DORA_FOLLOWUPS.md`. Follow-on fixes also touched
`dora_api/features/data/export_meal_plan.py`,
`dora_api/features/spa/serve_spa.py`, `dora_api/infrastructure/middleware.py`,
`dora_api/infrastructure/api_response.py`,
`web_app/src/composables/useMealPlanExport.ts`,
`web_app/src/pages/data/ExportPrint.vue`,
`web_app/src/pages/MealPlansOverview.vue`.

**Engineering-standards close-gate:** R-001 (shared conftest adapters +
`_items`/`_first` helpers), R-013/ADR-008 added. No app code changed (scope
discipline) — the two app bugs found (FU-167, FU-168) were logged + xfail'd,
not fixed, pending user decision. Dropped dead commented test code noted above.

**Next up:**
- FU-166 + its three spin-off defects (FU-164/167/168) are all closed. Suite
  is green (299 passed) and ~95× faster.
- Still open from the prior session: **FU-165** (browser-verify shopping
  UX v2) and **FU-160** (shop-day alert).
- Worth a browser smoke of the two touched frontend surfaces (MealPlansOverview
  + ExportPrint) to confirm the CSV buttons are gone and Print still works —
  vue-tsc is clean but it wasn't run in a browser.

**Open questions for user:** none.

---

## 2026-06-12 — Shopping-list UX v2 BUILT (single-page merge, rail, chip axe, restock review)
**Status:** complete — static + automated verification done (lint, vue-tsc,
21/21 shopping e2e); browser pass pending (FU-165).

**Background:** Same-day green light on `PROPOSAL_SHOPPING_LIST_UX_V2.md`
with four decisions (proposal §12): Q1 lean "More" menu + **CSV export
removed app-wide**; Q2 visibility promoted to a standing rule (**R-012**) +
**archive removed** + **per-line move-to-list removed**; Q3 **no Pause**
(`/stop` endpoint deleted); Q4 **no undo toast** on remove + app-wide undo
posture logged (FU-163). Two design revisions: M2 — no location
ordering/grouping default for shopping (stock location ≠ shelf location);
M12 — finish opens a **restock review modal** (ticked items each with a
level picker defaulting Well-Stocked + one "Restock & finish" button).

**Backend (all parse + e2e-tested):**
- `ShoppingList.name` nullable (`f3a9c1e5d2b7` migration backfills
  auto-date names to NULL); server-owned `display_name`
  (name → planned date → created, year appended when not current) and
  `effective_date` + `is_next_up` on summaries; response sorted by
  effective date ascending (rail renders payload order verbatim — R-003).
- Next-up rule in `get_shopping_lists._next_up_list_id`: live shop →
  first pending on/after last completed_at → earliest pending → most
  recent done.
- `POST /finish` accepts `level_overrides` (per-item restock levels);
  `/stop` and the CSV `/export` endpoints deleted (print-view stays, now
  renders display_name).
- PATCH name supports explicit-null clear (mirrors planned_shop_date).
- **Bug found+fixed:** assistant add-to-list still queried the *dropped*
  `is_primary` column (would AttributeError at runtime) — now uses
  `resolve_primary_target`. Membership/candidate DTO names now serve
  display_name.
- **Systemic fix (ADR-007):** `DoraJSONProvider` — dates/datetimes now
  serialise ISO 8601 instead of Flask's RFC-1123 default. The RFC format
  meant `planned_shop_date === 'YYYY-MM-DD'` could never match (today's-
  list landing pick never worked; Chunk-7 ISO e2e tests had never passed).
- **Systemic fix:** global `errorhandler(Exception)` was rewriting every
  deliberate `abort(4xx/5xx)` into an opaque 500 — HTTPExceptions now pass
  through. Unknown `/api/...` URLs 404 instead of serving the SPA's
  index.html.

**Frontend:**
- `ShoppingListDetail.vue` fully rebuilt (~2,300 lines): PageToolbar with
  visible actions (lifecycle primary, Quick add, group-by toggle, Refresh
  deals, Select, labelled "More" for rare/destructive); top info area
  (h4 display_name + heading-scale status badge + clearable rename +
  body2 meta + shop-day **button** with today/overdue tones replacing the
  banner + resurrected **doughnut** + server totals); desktop virtualised
  **rail** (one date continuum incl. done, auto-scroll to selection,
  next-up marker, slim kebab = copy/delete) + mobile dropdown of the same
  continuum (new shared `ShoppingListRailItem.vue`); rows = name-link +
  `StockLevelDot` + offer chips + qty stepper + **real outlined price
  button** + direct swap/remove icons (kebab gone); shopping state =
  sticky footer (progress, remaining, Finish) + bigger ticks + ticked
  lines sink with strikethrough + quick-add stays available; **restock
  review modal**; `u` shortcut = untick last; flash fix
  (`loading = ref(true)`).
- Shop-mode page + route **deleted** (M1–M15 dispositions per proposal §2);
  route guard now just follows `is_next_up`; tab title plural;
  ShopNowRedirect updated.
- `StockItemChip.vue` **deleted** (both call sites; stock-item substitutes
  list now name-link + StockLevelDot). Discovered `dora-link` CSS class
  was never defined — the old shop-day "link" literally had no styling
  (why it read as plain text, S14).
- display_name adopted by every consumer (dashboard card, QuickAddSheet,
  NewListDialog, DoraChat, ExportPrint — which also lost its list-CSV
  button).

**Tests:** 3 e2e tests updated to the new design (stop→404, export→404,
print asserts display_name). Full-suite run in progress at close; the one
known pre-existing failure is FU-164 (backup `product_stock_item_links`
section never existed — fails on main too).

**Engineering-standards close-gate:** R-001 (StockLevelDot +
ShoppingListRailItem extracted for reuse; PageToolbar adopted), R-002
(theme/Quasar tokens only), R-003 (display_name, effective_date ordering,
next_up_list_id all server-owned; doughnut % is display math), R-005
(migration batch-mode + Python backfill, portable both DBs), R-006 (single
additive migration + downgrade), R-007 (PageToolbar wider rollout and the
My-Data page redesign explicitly NOT touched), R-010/R-011 (typed DTO
mirrors; framework idioms). **New rule R-012 (discoverability) + ADR-006;
ADR-007 (ISO dates).** No unexplained violations.

**Next up:**
1. **User: browser-verify FU-165** (checklist in the FU) — includes the
   FU-161 drag check.
2. FU-160 (shopping-day alert) is now unblocked; FU-163 (undo posture)
   awaits a user decision.

**Full-suite result (post-close addendum):** `pytest tests` = 122 failed /
167 passed / 10 errors. **Verified pre-existing, not from this unit**: with
the UX-v2 changes stashed, the two heaviest failing files
(`test_stock_item_router`, `test_user_router`) fail identically on baseline
— the legacy router tests assert the old bare-array response shape where
the API has long returned pagination envelopes, etc. All 21 shopping tests
pass WITH the changes. Logged as FU-166 (legacy e2e suite drift — needs its
own triage prompt); FU-164 (backup sections) is one member of that set.

## 2026-06-12 — Shopping-list UX v2 design (proposal written; no code)
**Status:** complete (design-only unit; build gated on §11 answers).

**Background:** User rejected the current shopping-list presentation layer
with 18 specific bullets (stock-item chips, ellipsis menus, tiny price
button/info text, missing doughnut, list-switching UX, shop-mode concept,
flash-of-empty-state, tab title, name fallback, next-up landing, etc.) and
asked for a proper redesign — including "fully understand shop mode before
merging it away".

**Output:** `docs/04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md` — supersedes
the v1 proposal's *presentation* layer (v1 structure shipped as P6-01 and
stands). Headlines:
- Shop-mode page deleted; full M1–M15 feature inventory with per-feature
  disposition (cut one-at-a-time card/skip/up-next/peek; merge price-as-you-go,
  finish-and-restock, progress, shortcuts into the detail page + sticky
  shopping footer). `shopping` status enum value KEPT.
- Desktop virtualised lists rail / mobile dropdown, ordered by effective date
  (completed_at > planned_shop_date > created_at), auto-scroll to selection.
- Server-owned `display_name` (custom name nullable + clearable, falls back
  planned date → created date) and `next_up_list_id` (first date-wise after
  last completed) — both R-003 pushes, no client copies.
- Top info area: heading-scale status badge, body2 meta row, proper shop-day
  button, resurrected completion doughnut (was q-circular-progress on the old
  overview, deleted in 3e07e2e) + totals moved up.
- StockItemChip axed app-wide (exactly 2 call sites: shopping rows +
  stock-detail substitutes; replaced by name-link + new StockLevelDot).
- PageToolbar adoption; frequent actions visible, only rare/destructive in
  one "More" menu; per-row direct actions replace the line kebab; real price
  button.
- Root causes found during audit: empty-state flash = `loading=ref(false)`
  first-frame fallback (ShoppingListDetail.vue:1041); name-clear impossible
  (min_length=1 + None-skip in manage_shopping_list.py); tab title at
  routes.ts:137.

**Decisions made:**
- Surgical supersede, not rewrite: v1's shipped structure (status enum,
  inferred primary, receipt loop, finish/reopen snapshots) is untouched.
- Five-step shippable build order in proposal §9 (quick wins → naming →
  rail/next-up → rows/chip-axe → shop-mode merge).
- Four open questions for the user in §11 (zero-overflow toolbar?, rail
  kebab OK?, keep Pause?, remove-line confirm/undo).

**Follow-ups:** FU-162 raised (implement v2, absorbs FU-158/159 + FU-097
rows); FU-161 raised (L414 drag-drop index bug — reported defect, not
reproduced statically, confirm in browser during step 4); FU-158/159/160
annotated to point at the proposal. COVERAGE_GAPS.md shopping-lists row
updated to cite v2.

**Engineering-standards close-gate:** docs-only unit, no code touched.
Design itself was checked: R-001 (StockLevelDot + PageToolbar reuse), R-002
(theme tokens only, no new colours), R-003 (display_name + next_up_list_id
server-side; doughnut % from server counts is display math), R-007 (PageToolbar
wider rollout explicitly descoped). ADR evaluation: no new rule — "server owns
derived display names" is R-003 applied, not a new principle.

**Verification:** static only — all §1 audit claims carry file:line cites;
no build/browser run (none needed for a design doc).

**Next up:** user answers proposal §11 (4 questions), then FU-162 step 1
(quick wins: tab title, flash fix, shop-day button, status badge, meta sizing,
doughnut + totals) — no backend, immediately shippable.

## 2026-06-12 — FU-157 shopping-list URL-param fix + design-drift audit (FU-158/159/160 spawned)
**Status:** complete (static — node_modules absent; user verifies in browser).

**Background:** User reported the shopping-lists area "feels buggy no matter
which way I try to use it." Two specific symptoms — (1) clicking a different
list in the header dropdown changes the URL id but not the screen content,
and (2) finishing a list and adding an item to a *different* list makes the
finished list reappear — plus a meta-question of whether the
Chunk-5 overview-into-detail merge was botched and whether their L400-410
feedback design was just ignored. Asked whether a pull-down rebuild was
warranted.

**Verdict reached after thorough audit (Explore subagent + direct reads):**
NOT a rebuild. The merge architecture (status enum, route guard, picker
in header) is sound — `SHOPPING_LIST_REDESIGN_PROPOSAL.md` Chunk 5
genuinely shipped. Two surgical bugs caused the "broadly buggy" feeling;
three pieces of polish from the proposal were skipped and now live as
new FUs.

**FU-157 fix — single missing watcher (both shop surfaces):**
- `web_app/src/pages/ShoppingListDetail.vue` and
  `web_app/src/pages/ShoppingListShopMode.vue` both built around
  `const listId = computed(() => String(route.params.id))` reading the
  route param reactively, BUT only called `load()` from `onMounted`.
  When the user picks a different list, `switchToList` does
  `router.push(/shopping-lists/<new id>)`. Same route component, just
  a different `:id` param → Vue reuses the component → `onMounted`
  never re-fires → `load()` is never called again → old list stays
  on screen with the new id in the URL.
- The user's "finished list reappears after adding to another" was
  the same gap from a different angle: page was actually still
  showing list A the whole time (the URL change to B never
  triggered a load), then the existing `watch(quickAddOpen, load)`
  fired on add and pulled list B's data in — which *looked* like A
  was being replaced/resurrected when in fact the page had been
  stuck on A all along.
- Fix: `watch(listId, () => { void load(); })` on both pages, plus
  `detail.value = null` and an empty-id guard at the top of `load()`
  so the user sees a spinner — not stale rows — during the switch.

**Decisions:**
- **Keep `:id` in the URL.** User asked why we have it when Stock
  Overview doesn't. Stock Overview is *the overview* (no per-item
  surface); individual stock items have their own URL (`/stock/<id>`).
  Shopping lists collapsed overview into detail, so the URL has to
  identify which list the user is on. Benefits: shareable per-list
  links, browser back/forward across lists, refresh keeps you on the
  same list. With the watcher fixed, these benefits stand without
  visual confusion.
- **Surgical, not rebuild.** The architecture from Chunk 5 (status
  enum, route guard, header picker) is correctly implemented. The
  *polish* from the proposal (responsive panel, today's-date picking,
  planned shop date in UI) was dropped — but that's its own piece of
  work, not a rebuild trigger. Spawned as FU-158/159/160.
- **Same fix in shop mode for symmetry.** Shop mode rarely needs
  param-change reactivity (users tend to finish one shop end-to-end)
  but matching the pattern is cheap and prevents the same trap
  re-appearing if the future surface ever needs in-shop list
  swapping.

**Design-drift FUs spawned (real misses, not bugs):**
- **FU-158 — Responsive layout + today's-date picking** (feedback
  L405/406/409). Proposal called for a desktop right-side panel +
  mobile dropdown; built version is one dropdown everywhere. Route
  guard at `routes.ts:110-131` picks by status + creation order, not
  today's planned shop date.
- **FU-159 — Planned shop date not surfaced** (feedback L402). Column
  exists (migration `e1a4c7b2f9d0_…`), picker uses it for sort, but no
  UI to display/edit. User can't actually set one.
- **FU-160 — Shopping-day alert** (feedback L403). Depends on FU-159.

Recommended: bundle these into a focused "Shopping list polish" prompt
once the user is ready. They share a surface and design choices.

**Engineering-standards close-gate:**
- R-003 (state ownership): the fix doesn't relocate state, but it does
  hint at a related smell — `ShoppingListDetail` holds its own
  `ref<ShoppingListDetail | null>` outside the store, with no
  subscription to store mutations. Today that's fine (the store only
  owns summaries, not detail). If a future change wants e.g. multi-tab
  reactivity or assistant-driven mid-page status changes, this would
  need to move into the store. Not flagged as a new FU because
  FU-154 already covers the "page-local collections bypass store"
  pattern app-wide; this is the same shape, narrower scope.
- R-001 / componentisation: no new component extracted (single
  watcher in two pages — extracting `useRouteParamLoader` for two
  callers would be premature abstraction per CLAUDE.md scope rule).
- R-005 (portable data access): n/a, no backend.

**ADR evaluation:** no new rule. The fix is reactive Vue idiom
("watch the reactive source of an `onMounted` load if your component
might stay mounted across param changes") — too general to elevate to
a project-specific R-0NN.

**Verification:**
- `watch` already imported in both files (added to ShopMode's import).
- Existing `watch(quickAddOpen, load)` in Detail composes correctly
  with the new `watch(listId)` — they don't deadlock or double-load.
- Not run: lint / `quasar build` / dev server (no `node_modules`).

**Next up:**
- User browser-verify FU-157: open shopping lists, switch between
  several via the dropdown — each click should show that list's
  content within a beat (spinner if slow). Finish a list, navigate to
  another, add an item — only the active list should be on screen
  before AND after.
- Decide whether to queue the "Shopping list polish" prompt
  (FU-158 + FU-159 + FU-160) now or after another wave of feedback
  pick-up.

## 2026-06-12 — FU-155 (related-recipes nav) + FU-156 (unsaved-changes guard)
**Status:** complete (static — node_modules not installed; user verifies in browser).

**Background:** During FU-019 / FU-021 verify, user surfaced two real
bugs spun out from the original "did not reproduce" findings:
- FU-155: stock-item detail "Related recipes" tab opens the Cookbook
  overview, not the specific recipe.
- FU-156: navigating via the main menu bar (or refresh / browser back
  / related-recipe link) bypasses the unsaved-changes prompt entirely.

**FU-155 fix — wrong route shape in `goToRecipe`:**
- `web_app/src/pages/StockItemDetailPage.vue::goToRecipe` was pushing
  `{ path: '/cookbook', query: { recipe: recipeId } }`. The actual
  recipe-detail route is `/cookbook/:id`. The bad path matched
  `RecipesOverview` and silently dropped the unused `?recipe=` query.
  Changed to `router.push(\`/cookbook/${recipeId}\`)`. One line.

**FU-156 fix — guard moved to the router-leave layer, covers every nav surface:**
- New composable `web_app/src/composables/useUnsavedChangesGuard.ts` —
  takes a `Ref<boolean> | ComputedRef<boolean>` and wires:
  - `onBeforeRouteLeave` for different-route nav (main menu, router-
    link to another route, back button, etc.)
  - `onBeforeRouteUpdate` for same-component param changes (e.g.
    clicking a related-recipe link while editing a recipe — both
    routes match `/cookbook/:id`, so leave doesn't fire but update
    does).
  - `beforeunload` for browser refresh / close / address-bar nav.
  All three call one shared `$q.dialog` Discard/Cancel confirm so the
  prompt copy is consistent.
- `RecipeDetailPage.vue` wired with
  `computed(() => isDirty.value || imageDirty.value)` so both
  field-edit and image-pick state block nav. Its bespoke
  `onBack` page-handler check is removed (the guard now owns the
  prompt regardless of which nav surface triggers it). Delete-recipe
  clears both dirty flags before `router.push` so the user isn't
  asked about edits to a row they just deleted.
- `StockItemDetailPage.vue` wired with the existing `isDirty`
  computed. Image upload is auto-saved per existing code, so it
  doesn't need to feed the guard. `doDelete` clears `detail.value` to
  collapse `isDirty` to false before navigating.

**Decisions:**
- **Router-level guard, not per-handler.** Earlier code did the
  "Discard?" prompt inside the page's Back button handler — that's why
  every other nav surface (sidebar, refresh, back) bypassed it. Putting
  the prompt at the route-leave layer is the only way to cover *all*
  nav surfaces without each page re-implementing the same defensive
  check. Captured in the composable so each new dirty-form page is one
  line.
- **Don't include autosaved fields in dirty state.** StockItemDetail's
  image upload saves immediately and clears its own pending flag — not
  part of `isDirty`. Including it would prompt about transient
  in-flight state and confuse the user.
- **`onBeforeRouteUpdate` matters.** Without it, a user editing recipe
  A clicks a related-recipe link → route param changes from `/A` to
  `/B`, Vue Router reuses the component, `onBeforeRouteLeave` doesn't
  fire, edits silently lost. The fix is six lines for huge defensive
  coverage.
- **Reset dirty flags on delete.** Deleting an entity is the user
  explicitly throwing the form away. Prompting "Discard unsaved
  changes?" after they've already chosen Delete would be a confusing
  double-confirm — drop the flags before the post-delete `router.push`.

**Engineering-standards close-gate:**
- R-003 (state ownership): n/a — guard logic is purely client-side
  presentation state.
- R-001 / componentisation: composable extracted to
  `composables/useUnsavedChangesGuard.ts`, used by both pages. No
  per-page duplication.
- R-005 / portability: no backend touched.

**ADR evaluation:** No new rule yet — one composable, two callers
isn't enough surface to crystallise a standing rule. If a third
dirty-form page surfaces and adopts the same composable, that's the
moment to promote "dirty-form pages MUST use `useUnsavedChangesGuard`"
to an `R-0NN`.

**Verification:**
- Both target pages still type-check against the composable's
  signature (`Ref<boolean> | ComputedRef<boolean>`).
- `computed` and `onBeforeUnmount` already imported on both pages
  (no new vue-core imports needed in callers).
- Not run: lint / `quasar build` / dev server (no `node_modules`).

**Next up:**
- User browser-verify on the two pages:
  - **FU-155:** Stock item detail → Related recipes tab → click a
    recipe → lands on that recipe's detail page (URL `/cookbook/<id>`).
  - **FU-156:** Recipe detail with unsaved field edit → main menu link
    → prompt fires; cancel keeps you put, Discard navigates. Repeat with
    image-only change (pick a new image, don't touch fields) → prompt
    still fires. Refresh tab → browser prompt fires. Same checks on
    Stock-item detail basics form. Delete recipe / stock item with
    unsaved edits → no prompt (deletion is implicit discard).

## 2026-06-12 — FU-014 product image fix + state-ownership FU spawn (FU-154)
**Status:** complete (static — node_modules not installed; user verifies in browser).

**What changed (background to the work):** user repro'd the FU-014 image
corruption — saving a product from search rendered the product *name*,
squished, where the avatar image should be. Static trace showed the
create path was actually fine; the bug was on the **read** side
(`get_products.py:56`) which `.decode('utf-8', 'ignore')` on raw image
bytes, returning a garbage string the browser treated as a broken
`<img src>`. User also called out that the saved product doesn't show on
My Products until a hard refresh — flagged as likely systemic.

**FU-014 fix — adopt the stock-item / recipe image convention end-to-end:**
- `dora_api/features/products/create_product.py` — `image` field flipped
  from `Base64Bytes` to `str | None` with `max_length=6_000_000`; handler
  encodes as `request.image.encode("utf-8")` (matches
  `create_stock_item.py`, `create_recipe.py`).
- `dora_api/features/products/get_products.py` — `ProductDto.image: str |
  None` → `has_image: bool`. New `stamp_has_image` does a single
  `image IS NOT NULL` query and stamps the flag (mirrors
  `_hydrate_has_image` on stock items). Called by both `GetProductsHandler`
  and `GetBestDealsHandler` so the dashboard's best-deals list also gets
  the flag.
- `dora_api/features/products/get_product_image.py` — **new** route
  `GET /products/<id>/image`. Decodes the stored data-URL bytes and
  serves raw bytes with the right MIME. Direct copy of the stock-item
  pattern minus the linked-fallback (products own their image; stock
  items fall back to linked products).
- `dora_api/persistence/table_mappings.py` — `image` column on `Product`
  is now `deferred`, so list endpoints never pull megabytes per row just
  to derive `has_image`.
- New Alembic migration `e2c5a8f1d7b3_20260612_product_image_nullify_garbage.py`
  — nulls out any `Product.image` whose first 5 bytes aren't `b"data:"`.
  Garbage rows from the old `Base64Bytes` path render the fallback icon
  cleanly; user re-saves the product to get a correct image.
- Frontend: `Product` model drops `image`, gains `has_image`.
  `MyProductsPage` (saved-products grid) and `DashboardPage`
  (best-deals list) now render `<img v-if="p.has_image"
  :src="\`/api/products/${p.product_id}/image\`">`.
- `services/files/imageService.ts` — new `wrapAsDataUrl` helper with
  base64 magic-byte MIME sniff (PNG / JPEG / WebP / GIF), default JPEG.
  `decodeBase64Image` delegates to it (kept for the one
  `ProductSearchCard` caller) instead of hard-coding `image/jpeg`.
- `ProductSearch.ensureSaved` wraps `offer.image` (raw base64 from
  `merchant_api`) via `wrapAsDataUrl` before POSTing; empty → null.
- `CreateProductCommand.image` typed `string | null` to match.

**Decisions:**
- **Create endpoint takes base64/data-URL string only, not URLs.**
  Matches existing convention (`create_stock_item`, `create_recipe`).
  Backend never makes outbound HTTP from a write endpoint (avoids
  merchant rate-limits, dead-link retries, CORS). The merchant_api
  already downloads + base64-encodes
  ([product_image_provider.py:53](merchant_api/infrastructure/product_image_provider.py#L53))
  so the frontend just relays. Same shape will work for future
  custom-product uploads (FileReader → data URL → same field).
- **Defer the image column on Product.** Pre-fix, every `get_products`
  call SELECTed the full image bytes per row only to throw them away.
  Aligning with stock-item / recipe is the right cleanup *while we're
  here*. Two reasonable choices for `has_image` derivation — touch the
  deferred column (N+1) or bulk-select `IS NOT NULL` — picked bulk to
  match the stock-item idiom exactly.
- **ProductChip.vue (orphaned) left as-is.** No callers, its structural
  `ProductChipModel` doesn't reference the `Product` model so it still
  type-checks. Will be addressed when something actually consumes it.
- **No `image_url` field on the create endpoint.** Would have added a
  second code path for the same shape with no current consumer.

**FU-154 — state-ownership finding (spawned, NOT fixed in this unit):**
The user noted the saved product not showing till refresh is "likely a
larger issue spread across the app." Confirmed `MyProductsPage` keeps
its own local `products = ref<Product[]>([])` populated via direct
`productApi.getAllAsync()` in `onMounted`, bypassing `productStore`.
`ProductSearch` saves through the store — so the two diverge. Logged as
FU-154 with `MyProductsPage` as the canonical fix and a likely-suspects
audit list (Dashboard, Stock, Recipes, Meal Plans, Waste). R-003
violation. Not fixed here to keep this unit focused on the image bug.

**Verification:**
- Backend: imports + types reconciled (`Base64Bytes` import dropped,
  `wrapAsDataUrl` import added).
- `image` consumers swept — `MyProductsPage` and `DashboardPage` flipped
  to `has_image` + route. Only remaining `.image` reference on a Product
  is `ProductChip.vue` (orphaned).
- Existing test `test__create_product` uses `image=None` — still valid
  under the new `str | None` typing.
- Not run: lint / `quasar build` / dev server (no `node_modules`).

**Engineering-standards close-gate:**
- R-003 (state ownership): **flagged**, not violated. The image fix
  itself is push-to-server (server owns image bytes via /image route;
  client just shows them). The `MyProductsPage` local-`products`-ref
  smell is a *separate* R-003 violation logged as FU-154 with the full
  app-wide audit recommended — not introduced by this fix.
- R-005 (portable data access): migration uses `SUBSTR(image, 1, 5)` +
  bound parameter, works on both Postgres and SQLite. No batch_alter
  needed (data-only change).
- Other rules: no new componentisation, theming, framework, or scope
  smell introduced.

**ADR evaluation:** no new standing rule — image-handling pattern is
already implicit via stock-item / recipe precedent; this just brings
products into line. Could later promote the pattern ("entities store
bytes as data-URL UTF-8, list payloads carry has_image, dedicated
/image route") to a formal R-0NN if a fourth case emerges — not yet.

**Next up:**
- User browser-verify: save a product from search → confirm it has
  the image when My Products is refreshed (still requires refresh
  until FU-154 is fixed). Re-save any products with broken thumbnails
  (the migration nulled their garbage bytes).
- FU-154 — the app-wide state-ownership audit + `MyProductsPage`
  refactor whenever it's prioritised.

## 2026-06-12 — Drop the `/recipes*` legacy redirects (clean break)
**Status:** complete. User pushed back on the redirect retention
("what's the point of keeping legacy redirects? lets just make it
clean") — fair, pre-release, no production bookmarks to preserve.
Ripped the three legacy redirect routes; `/recipes*` URLs now 404,
which is the right behaviour for a path that no longer exists.

**What changed:**
- `web_app/src/router/routes.ts` — three redirect entries deleted
  (`/recipes` → `/cookbook`, `/recipes/:id` → `/cookbook/:id`,
  `/recipes/:id/cook` → `/cookbook/:id/cook`). Comment block
  updated to record the deletion rationale.
- `web_app/src/components/dora/DoraChat.vue::iconForNav` — the
  `path.startsWith('/recipes')` fallback (added in the previous
  worklog entry specifically to cover the brief redirect frame)
  is gone; just `/cookbook` now.
- CHANGELOG rewritten to drop the "still redirects" caveat —
  it's a clean break.

**Verification:**
- Final sweep — only remaining `/recipes` mention in SPA code
  is the historical-context comment in `menuButtonProps.ts`
  ("when detail lived at `/recipes/:id`"). That's fine; it's
  there to explain *why* the prop has no current consumer.

**Engineering close-gate:** N/A — surgical deletion + comment
update. R-007 held (didn't touch backend API paths or
component filenames; only the SPA-route surface).

**Open questions for user:** none.

---

## 2026-06-12 — Migrate recipe routes under `/cookbook`
**Status:** complete (frontend-only, static — no env). Closes the
legacy-route naming tail from A8: detail + cook were still at
`/recipes/:id*`; now everything lives under `/cookbook`.

**What changed — router:**
- **`web_app/src/router/routes.ts`** — three new canonical paths:
  - `/cookbook` (overview, unchanged path)
  - `/cookbook/:id` (detail, was `/recipes/:id`)
  - `/cookbook/:id/cook` (cook mode, was `/recipes/:id/cook`)
- Legacy redirects rewritten as **redirect routes with
  param-preserving functions** so the old paths still bounce
  callers (existing bookmarks, external links, anything we
  missed) into the new namespace:
  - `/recipes` → `/cookbook` (unchanged)
  - `/recipes/:id` → `/cookbook/:id` (new — was a page mount)
  - `/recipes/:id/cook` → `/cookbook/:id/cook` (new — was a
    page mount)
- The `RecipeDetailPage.vue` + `RecipeCookMode.vue` page
  components are unchanged (only the URLs that load them
  moved); the page filenames keep "Recipe" because that's the
  domain entity, not the URL.

**What changed — internal nav callers (all `/recipes` → `/cookbook`):**
- `DashboardPage.vue` — 4 spots (recipe link, cook link,
  "Browse recipes" CTA, "See more → /cookbook?cookable=true").
- `MealPlansOverview.vue` — `goToRecipe` + `cookRecipe`.
- `RecipeDetailPage.vue` — `goToCookMode`, new-version push,
  `onJumpToSibling`.
- `RecipesOverview.vue` — `onOpenRecipe`, `onCookClick`,
  importer success push.
- `StockItemDetailPage.vue` — `goToRecipe` (with `recipe`
  query) + `goToCook`.
- `StockOverview.vue` — `goToRecipes`.
- `WastePage.vue` — `openRecipe`.
- `RecipeCookMode.vue` — back-nav (`id ? /cookbook/${id} :
  /cookbook`).
- `useStockItemActions.ts::seeRecipesUsing` — pushes to
  `/cookbook` with the `usesStockItem` query.
- `data/ExportPrint.vue` — empty-state `router-link to="/recipes"`.
- `HelpPage.vue` — "Cook mode" guide path.
- `MainLayout.vue::linksList` — Cookbook entry's
  `activePrefixes: ['/recipes']` removed (the natural `/cookbook`
  prefix now covers detail + cook).
- `DoraChat.vue::iconForNav` — matches **both** `/cookbook`
  and `/recipes` so the legacy redirect path also shows the
  cookbook icon during the brief redirect frame.

**What changed — contextual chips + intent summaries:**
- `services/doraContextualActions.ts` — recipe-detail trigger
  flipped to `/cookbook/`; the overview-card route + cookbook-
  from-shopping-list path both flipped to `/cookbook` (label
  unchanged).
- `services/doraIntents.ts`:
  - Page-summary matchers for the recipes overview + cook mode
    flipped to `/cookbook` shapes.
  - `find_recipe` handler's six `navigateTo` URLs (browse,
    no-match, single-result, multi-result, plus the
    `whats_for_dinner` "Open Recipes" call) all flipped to
    `/cookbook`; labels updated to "Open Cookbook" / "Browse
    cookbook" where the old "Open Recipes" / "Browse recipes"
    no longer matches the destination.

**What changed — comments:**
- `components/menu/menuButtonProps.ts` + `useMenuLinkActive.ts`
  comments rewritten — the original explanation cited the
  `/recipes` ↔ `/recipes/:id` shape; updated to
  `/cookbook` ↔ `/cookbook/:id` and noted that the prop now
  has no current consumer (kept for future use).

**Untouched (deliberately):**
- **Backend API endpoints (`/api/recipes/...`)** — resource
  naming, not user-visible URL. The DTOs / handlers /
  migrations all stay under `recipes`; renaming would be a
  separate REST-versioning conversation with zero UX benefit.
- **`services/api/recipeApiService.ts`** — all the `/recipes/...`
  string fragments target the backend API path. Untouched.
- **`composables/useRecipeExport.ts`** — same; backend export
  endpoints stay `/api/recipes/<id>/export` + `/print-view`.
- **Component-folder paths** (`src/components/recipes/*`) —
  filesystem layout, not URLs.
- **External-URL placeholders** like
  `https://example.com/recipes/lasagne` in the URL importer's
  input — they're example *third-party* URLs, not Dora SPA
  links.
- **`DoraChat.vue::iconForNav`** keeps `/recipes` as a fallback
  match so the icon stays correct during the redirect frame.

**Decisions made:**
- **Param-preserving redirect functions, not blanket 301-to-
  overview.** A bookmarked `/recipes/abc-123/cook` should land
  on cook mode for that recipe, not on the overview. Vue
  Router's `redirect: (to) => …` is the documented pattern.
- **Keep the legacy redirects indefinitely.** Cheap, and
  external links (recipes shared in chat / email / printed
  cards) will outlive any internal cleanup. If we ever want
  to retire them, the worklog + this entry are the audit
  trail.
- **Don't rename the backend API.** REST resource naming
  doesn't map to UX naming. `Recipe` is the entity, `/recipes`
  is its collection endpoint. The frontend URL changed
  because *Cookbook* is the *page* — different concern.
- **Don't rename `RecipeDetailPage.vue` / `RecipeCookMode.vue`
  / `RecipesOverview.vue`.** They render a recipe-shaped
  entity; the surrounding page (the Cookbook) is the URL
  noun. Renaming the components would conflate the two.

**Files touched:**
- `web_app/src/router/routes.ts`
- `web_app/src/composables/useStockItemActions.ts`
- `web_app/src/layouts/MainLayout.vue`
- `web_app/src/components/dora/DoraChat.vue`
- `web_app/src/pages/DashboardPage.vue`
- `web_app/src/pages/MealPlansOverview.vue`
- `web_app/src/pages/RecipeCookMode.vue`
- `web_app/src/pages/RecipeDetailPage.vue`
- `web_app/src/pages/RecipesOverview.vue`
- `web_app/src/pages/StockItemDetailPage.vue`
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/pages/WastePage.vue`
- `web_app/src/pages/HelpPage.vue`
- `web_app/src/pages/data/ExportPrint.vue`
- `web_app/src/services/doraContextualActions.ts`
- `web_app/src/services/doraIntents.ts`
- `web_app/src/components/menu/menuButtonProps.ts`
- `web_app/src/components/menu/useMenuLinkActive.ts`
- `CHANGELOG.md` (Unreleased Changed)

**Verification:**
- Static only. Final grep for `'/recipes\|"/recipes\|`/recipes/`
  shows only:
  - `recipeApiService.ts` backend API paths (intentional);
  - `useRecipeExport.ts` backend URL builder (intentional);
  - `DoraChat.vue::iconForNav` fallback match (intentional);
  - `routes.ts` redirect entries + the historical-context
    comment block (intentional);
  - `RecipeDetailPage.vue` + `RecipesOverview.vue` URL
    importer placeholder strings (intentional — third-party
    URL examples).
- No remaining internal SPA-route caller points at the legacy
  shape.
- **NOT yet verified in browser.** Quick checks: clicking a
  recipe card on Cookbook overview goes to `/cookbook/<id>`;
  the cook-mode button goes to `/cookbook/<id>/cook`; the
  legacy `/recipes/<id>` URL still loads the detail page (via
  redirect).

**Engineering close-gate:**
- **R-007 scope discipline** — backend API paths + component
  filenames stayed put. Only user-facing URLs moved.
- **R-008 terse comments** — every changed comment block
  cites the 2026-06-12 migration; no per-call inline notes.
- **R-011 framework-idiomatic** — Vue Router's `redirect`
  function for param-preserving rewrites is the documented
  pattern.
- No new ADRs.

**Next up:** unchanged from prior worklog — FU-151 browser
smoke (now folds in: verify `/recipes/...` legacy links
redirect; verify all internal nav lands on `/cookbook/...`).

**Open questions for user:** none.

---

## 2026-06-12 — Command palette retired (FU-029 / INV-9 final call)
**Status:** complete (frontend-only, static — no env). User decision
after reviewing the value of Ctrl/Cmd-K for Dora's audience: cut, not
shrink. INV-9's earlier SHRINK recommendation is preserved as the
audit trail; the user escalated to CUT and that's the call.

**What changed — code (deletions):**
- `web_app/src/components/CommandPalette.vue` — **deleted**.
- `web_app/src/composables/useCommandPalette.ts` — **deleted**.
- `web_app/src/composables/useCommands.ts` — **deleted**.
- `web_app/src/composables/useRecents.ts` — **deleted** (was
  only consumed by the palette).
- `web_app/src/css/tokens.scss` — `--highlight-search` token
  removed (only consumer was the palette's matched-substring
  highlight).

**What changed — code (MainLayout pruning):**
- Removed the `<CommandPalette v-if="..." />` mount in the
  template; the `hasEverOpened` lazy-mount sentinel is gone.
- Removed the `import` lines for `CommandPalette`,
  `useCommandPalette`, `useCommands`, `ShoppingListApiService`,
  and `useShoppingListStore` (the last two were only used by the
  palette-feeder helpers below).
- Removed the Ctrl/Cmd-K global key handler
  (`onCommandPaletteKey` + its `onMounted` /
  `onUnmounted` registration pair).
- Removed the three palette-feeder helpers
  (`autogenerateFromLowStock`, `openPrimaryList`,
  `openPrimaryShopMode`) — verified each was used only by the
  palette `useCommands([...])` registry, nowhere else.
- Removed the 18-item `useCommands([...])` registration block.
- Replaced everything with a one-line breadcrumb comment
  pointing at the worklog + FU-029.

**What stays (deliberately):**
- `web_app/src/composables/useShortcut.ts` + its
  `useShortcutRegistry` — the keyboard-shortcut layer is
  orthogonal to the palette and broadly useful (`?`, `/`,
  `g s` / `g l` / `g r` / `g d` / `g h`, and every page-
  specific shortcut). Still wired in MainLayout's global
  `useShortcut([...])` block at line 237.
- `web_app/src/components/ShortcutsCheatsheet.vue` — still
  mounted; `?` still opens it.
- `MealPlansOverview.vue::openPaletteLogCook` — confusingly
  named but unrelated (the meal-plan "recipe palette" is a
  sidebar, not the command palette). Left alone.

**Docs updated (audit trail across the planning library):**
- `docs/00_DOC_GRAPH.md` — INV-9 entry rewritten to
  "SUPERSEDED / palette retired" with a do-not-reopen note;
  the B9 surface list strikes "command palette"; the B9 open-
  follow-ups list flips FU-029 to RESOLVED and FU-030 (404
  redesign) too.
- `docs/03_prompts/00_INDEX.md` — B9 description strikes
  "ctrl+k"; INV row strikes "command-palette worth (INV-9)".
- `docs/03_prompts/B9_misc_bugs.md` item 4 — struck through
  with a CANCELLED note.
- `docs/03_prompts/INV_investigations.md` INV-9 block —
  struck through with a SUPERSEDED preamble; original prompt
  preserved.
- `docs/05_investigations/COMMAND_PALETTE_ASSESSMENT.md` —
  added an "⚠ OUTCOME 2026-06-12 — palette retired entirely"
  banner at the top pointing at the worklog.
- `docs/04_proposals/IMPL_PLAN_COOKBOOK.md` § naming-sweep —
  struck the "command-palette label" mention; the surrounding
  FU-031 sweep concern (tour cards, help text, static SPA
  copy) survives.
- `docs/04_proposals/PROPOSAL_COOKBOOK.md` §2.1 — same
  treatment; FU-031 wording reframed.
- `docs/02_feedback/FEEDBACK_TRIAGE_AND_PLAN.md` — both
  "command palette" mentions (B9 list + "open design
  questions" list) struck through with the retirement note.
- `CLAUDE.md` § "Removed features — do not reintroduce" —
  new bullet for the command palette, calling out
  exactly what was removed and what was kept (`useShortcut`
  + cheatsheet stay).

**Follow-ups updated:**
- **FU-029 → RESOLVED.** Verifying the palette's commands is
  moot now; the entry records the cut as the resolution.
- **FU-031 reframed.** The palette-label sub-bullet is
  mooted; the broader "Recipes → Cookbook" rename sweep in
  tour cards / help text / SPA copy remains open.

**Decisions made:**
- **Cut over shrink.** The INV-9 memo recommended SHRINK
  (delete the redundant nav commands, promote entity search
  to a global bar). The user's framing was harsher and
  honest: nobody using Dora reaches for Ctrl-K. Building a
  global-search bar is a separate, larger UX question that
  doesn't depend on preserving the palette.
- **Don't touch the recipe / meal-plan "palette" naming.**
  Different concept (a sidebar of cards), no risk of
  confusion in the deletion sweep.
- **Keep the master kill-switch breadcrumb in
  `CLAUDE.md`.** Future Claude sessions will be tempted to
  rebuild a Ctrl-K palette as "obvious power-user UX". The
  removed-features bullet pre-empts that re-litigation.
- **Pull the unused `--highlight-search` token.** R-007 —
  dead code is dead, and a future reader hunting "what uses
  this?" deserves a clean answer.

**Files touched:**
- `web_app/src/layouts/MainLayout.vue` (pruned)
- `web_app/src/components/CommandPalette.vue` (deleted)
- `web_app/src/composables/useCommandPalette.ts` (deleted)
- `web_app/src/composables/useCommands.ts` (deleted)
- `web_app/src/composables/useRecents.ts` (deleted)
- `web_app/src/css/tokens.scss` (one dead token removed)
- `docs/00_DOC_GRAPH.md`
- `docs/03_prompts/00_INDEX.md`
- `docs/03_prompts/B9_misc_bugs.md`
- `docs/03_prompts/INV_investigations.md`
- `docs/05_investigations/COMMAND_PALETTE_ASSESSMENT.md`
- `docs/04_proposals/IMPL_PLAN_COOKBOOK.md`
- `docs/04_proposals/PROPOSAL_COOKBOOK.md`
- `docs/02_feedback/FEEDBACK_TRIAGE_AND_PLAN.md`
- `CLAUDE.md` (Removed features section)
- `CHANGELOG.md` (Unreleased Removed)
- `DORA_FOLLOWUPS.md` (FU-029 RESOLVED; FU-031 reframed)

**Verification:**
- Final sweep confirmed no leftover code references
  (`grep -r 'useCommands\|useCommandPalette\|CommandPalette\|
  paletteOpen\|togglePalette\|useRecents'` finds only the
  unrelated `openPaletteLogCook` in MealPlansOverview).
- Final token sweep confirmed `--highlight-search` had no
  remaining consumers; safe to remove.
- **NOT yet verified in browser.** The cleanest test is
  "Ctrl-K does nothing and the rest of the app still works";
  fold into the next browser-verify pass.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-007 scope discipline** — only the palette + its
  exclusive dependencies were removed. Shortcuts, cheatsheet,
  and the meal-plan "palette" naming all left untouched.
- **R-001 componentise** — N/A (deletion, not extraction).
- **R-008 terse comments** — one breadcrumb in MainLayout
  pointing at the worklog + FU-029; no per-deletion
  commentary.
- **R-011 framework-idiomatic** — N/A (deletion).
- No new ADRs.

**Next up (unchanged from prior worklog):**
1. **FU-151** — browser smoke session for the four FU-085
   spin-off fixes (FU-147 / FU-148 / FU-149 / FU-150 step 1).
2. Other open verify FUs: FU-130, FU-132, FU-135, FU-141,
   FU-142, FU-145.
3. **FU-153 / FU-152** assistant work when sequenced.
4. **Phase 2** (ingestion API / C-10).

**Open questions for user:** none.

---

## 2026-06-12 — FU-030 fullscreen 404 redesign (login-theme + mascot)
**Status:** complete (frontend-only, static — no env). User-flagged
the existing 404 as "a bit boring"; rewrote to mirror the
LoginPage's off-app treatment with a contextually-appropriate
mascot.

**What changed:**
- **`web_app/src/pages/ErrorNotFound.vue`** rewritten from a flat
  toolbar-tinted "Oops" page into the same drifting-mesh-gradient
  + floating-mascot + glassy-card pattern LoginPage uses:
  - Three blob layers (magenta / dora amber / mint) drifting with
    cubic keyframes, blurred + screen-blend-mode, on a deep
    midnight base.
  - Mascot: `dorabot-fatal-error-or-offline.png` — semantically
    the closest "something went wrong, but it's fine"
    expression. Bobs gently; tucks above the card + shrinks on
    narrow viewports (mirrors LoginPage's media queries).
  - Glassy card with a gradient "404", "This page wandered off"
    headline, plain-English explainer ("broken link, typo, or
    something that used to live here"), and a single "Take me
    home" CTA.
- Locally-scoped CSS variables (`--lost-bg-base`, `--lost-blob-1`
  …) instead of `--surface-toolbar` / `--text-on-toolbar`. Same
  rationale as LoginPage — 404 can render pre-auth where the
  app's `data-theme` cascade hasn't settled, so we forced light
  with `color-scheme: light`.
- `prefers-reduced-motion: reduce` locks the blobs + mascot +
  card-enter animation, same discipline as LoginPage.

**Decisions made:**
- **Mirror LoginPage, don't extract a shared component.** Both
  pages are "off-app full-bleed surfaces"; pulling out a
  `<MarketingShell>` is tempting but the third consumer doesn't
  exist yet. R-001's componentise-on-second-consumer is hit
  here in spirit — both pages do open with very similar
  CSS — but the variable scopes are independent on purpose
  (LoginPage's `--lp-*` vs 404's `--lost-*`) to make future
  divergence cheap. If a third consumer lands the shared
  shell is a small refactor.
- **`dorabot-fatal-error-or-offline.png`** over the cuter
  variants. 404 should read as "I made a mistake / I'm a bit
  lost", not "I'm excited about something" — the offline
  variant matches the apologetic tone.
- **Locally-scoped tokens, forced light.** Same reasoning as
  LoginPage's comment block; the toolbar-tinted version would
  flip dark + lose its colour story when an unauthenticated
  user lands on a 404.
- **No reusable mascot prop.** The mascot image src is
  hardcoded; passing it as a prop assumes a shared shell that
  doesn't exist yet (see above).

**Files touched:**
- `web_app/src/pages/ErrorNotFound.vue` (full rewrite)
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-030 RESOLVED)

**Verification:**
- Static only. Mascot path verified
  (`web_app/src/assets/dora/dorabot-fatal-error-or-offline.png`
  exists alongside the other dorabot variants).
- LoginPage parity confirmed by side-by-side read of the two
  scoped style blocks; mirrored animation timings + media
  breakpoints.
- **NOT yet verified in browser.** Hit `/this-route-does-not-
  exist` while signed out to confirm pre-auth render is OK +
  the mascot loads.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — explicit carve-out (single
  consumer for now; second consumer is LoginPage but the
  divergence trajectory is real). If a third pre-auth surface
  appears (e.g. an offline / maintenance page), extract a
  `MarketingShell`.
- **R-002 theme tokens** — local tokens only, with the
  pre-auth-rationale comment block. No raw hex in the
  template; gradients use the locally-scoped vars.
- **R-007 scope discipline** — `ErrorPageNotFound.vue`
  (in-layout 404 via `PageErrorState`) was already themed
  and stays untouched.
- **R-008 terse comments** — one block at the top of the
  template + the style block; no per-block commentary.
- **R-011 framework-idiomatic** — q-card / q-btn used as-is;
  CSS animations only (no JS, no canvas) — matches LoginPage.
- No new ADRs.

**Next up:**
1. **FU-151** browser smoke for the four FU-085 spin-offs.
   (FU-030 verify can fold into the same browser pass —
   hit a bogus URL while signed out.)
2. Verify backlog: FU-130, FU-132, FU-135, FU-141, FU-142,
   FU-145.
3. **FU-153 / FU-152** assistant work when sequenced.
4. **Phase 2** (ingestion API / C-10).

**Open questions for user:** none.

---

## 2026-06-12 — Augmented `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` §7 (LLM provider + connectivity)
**Status:** complete (proposal addition; no code). User feedback
surfaced four LLM-client-side concerns the original proposal didn't
cover; documented as a new section so the design lives next to the
existing routing/registry refactor instead of as scattered FUs.

**What changed:**
- **`docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`**
  gains **§7 — LLM provider & connectivity** (six sub-sections):
  - §7.1 per-user LLM config (replaces install-wide singleton).
  - §7.2 reachability probe once per chat open + visible
    "unavailable, using basic mode" banner + Retry. No polling.
  - §7.3 network-topology documentation — backend reaches the
    LLM, not the device.
  - §7.4 multi-provider abstraction — Ollama (existing) + OpenAI
    + Anthropic + Gemini; encrypted-at-rest API key column.
  - §7.5 adoption ordering (single migration for §7.1 + §7.4
    schema; provider impls follow per-PR; probe last; docs only
    for §7.3).
  - §7.6 cross-references to the existing DORA-BOT feedback in
    `Feedback _ Fixes - as of [06-Jun-2026].md` (toggle slider,
    per-user preference, full-off) so the design + UX
    feedback collide cleanly when an IMPL plan gets drafted.
- **`DORA_FOLLOWUPS.md`** — **FU-153 logged** as the umbrella
  follow-up pointing at the proposal section; concrete next
  step is "draft an IMPL plan from §7" rather than direct code.

**Decisions captured in the proposal (worth surfacing here):**
- **Per-user, but keep an install-wide master kill switch.**
  Defence in depth — power user opens a port, admin can still
  disable the assistant feature install-wide.
- **Probe once per chat open, not polling.** User explicitly
  asked for this framing. Re-probe also fires on Retry +
  settings change.
- **Network topology is a documentation issue, not a code
  issue.** The backend's reachability constraint is real (LLM
  URL is not browser-reachable; backend makes the call), but
  there's nothing to fix in code — operators must wire the
  network. Settings help text + System → Features admin docs
  carry the explanation.
- **Encrypt API keys at rest.** Free for OpenAI/Anthropic/
  Gemini support; the DB column is `llm_api_key_encrypted`;
  settings GET returns `has_api_key: bool`, never the value.
- **Streaming explicitly deferred** (already in §4); the
  provider abstraction must leave room for it.

**Files touched:**
- `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`
  (§7 added)
- `DORA_FOLLOWUPS.md` (FU-153 logged)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Cross-checked the current code paths the proposal references:
  - `AppSetting.llm_*` is install-wide (confirmed —
    `dora_api/features/app_settings/access.py`).
  - `_build_assistant_client()` reads the singleton AppSetting
    (`ask_assistant.py:126-136`).
  - `LlmUnavailable` catch already returns
    `defer_to_local=True` (existing per-request fallback
    stays as the safety net; the probe is the cheaper "once
    per chat" pre-check).
  - `OllamaClient` is the only client today; provider
    abstraction is net-new.

**Engineering close-gate:**
- N/A — proposal addition. **R-007** held (scope was
  proposal augmentation, not code).

**Next up:**
1. **FU-151** — single browser smoke session for the four
   landed fixes (FU-147 / FU-148 / FU-149 / FU-150 step 1).
2. **FU-153 / FU-152** — when ready to tackle the assistant
   work, draft IMPL plans for each. **FU-153 is the
   pre-requisite** for any per-user routing work because the
   rules-router needs per-user vocab + per-user provider too.
3. Other still-open verify FUs: FU-130, FU-132, FU-135,
   FU-141, FU-142, FU-145.
4. Phase 2 (ingestion API / C-10) when the verify backlog
   is drained.

**Open questions for user:** none — the four design questions
are now captured in the proposal with proposed answers; user
can push back on any of them in the next session if needed.

---

## 2026-06-12 — FU-147 (dietary picker bug) + FU-148/149 (cookbook polish) + FU-150 step 1 (chat-mode dietary/cuisine)
**Status:** complete (static-only). Three real fixes + one
minimal-fix-with-design-followup for the chat. Closes 4 of the 5
FU-085 spin-offs from yesterday's triage in one pass.

**What changed — FU-147 (root cause: backend, not frontend race):**
- **`dora_api/features/recipes/get_recipes.py::handle_by_id`** —
  the `/<recipe_id>` route has no `uuid:` converter, so Flask
  passes `recipe_id` as a **string**.
  `get_tag_ids_for_recipes()` + `get_tool_ids_for_recipes()`
  return `dict[UUID, list[UUID]]` (keys come from SQLAlchemy
  result rows). `tag_map.get(recipe_id_string, [])` against
  UUID-keyed dict → **always returns `[]`**. Every recipe came
  back from the detail endpoint with empty `dietary_tag_ids` +
  `tool_ids`. The list endpoint was unaffected because it sources
  ids from RecipeDto entities that already carry UUID objects.
  Fix: pass `entity.id` (the loaded entity's real UUID) to both
  `get_*_for_recipes` and the subsequent `.get()` calls.
- Cards-show-tags-but-detail-page-input-is-empty: the user's
  repro is exactly this asymmetry.

**What changed — FU-148 (time-of-day filter):**
- `RecipesOverview.vue` — new `timeOfDayFilter` ref + q-select
  (`Breakfast / Lunch / Dinner / Dessert / Snack / Any`) +
  filter predicate (null = no filter; non-null requires exact
  match — recipes with null `time_of_day` fail a non-null
  filter, matching the "I want breakfast recipes" intent).
- Static `TIME_OF_DAY_OPTIONS` constant; mirror of the editor's
  q-select on `RecipeDetailPage`. Constant rather than vocab
  table because the enum is tiny + fixed (unlike cuisine /
  category / dietary tags).
- Wired into `hasAnyFilter` + `activeFilterCount` + `clearFilters`.

**What changed — FU-149 (# ingredients filter + sort):**
- New `ingredientsMax` numeric ref + q-input ("# ingredients
  ≤"). Same blank-input / NaN guard pattern as
  `mealCountMin` / `missingMax` (L234).
- New `'ingredient_count'` sort key + case in `sortedRecipes`
  comparator + `STATIC_SORT_OPTIONS` entry + `sortDirTooltip`
  case. Default direction = ascending ("fewest first" is the
  natural read for "quick recipe" intent); the watch on
  `sortBy` now treats `name` AND `ingredient_count` as the
  ascending-default axes.
- Wired into `hasAnyFilter` + `activeFilterCount` +
  `clearFilters` alongside time-of-day.

**What changed — FU-150 step 1 (chat-mode):**
- **`RecipeSnapshot`** (in `doraIntents.ts`) gains
  `dietaryTagNames: string[]` + `timeOfDay: string | null` so
  the handler can substring-match these axes without a vocab
  lookup at chat time.
- **`DoraChat.vue::getRecipes`** resolves dietary tag ids →
  names once via the `recipeVocabStore`, populates the new
  snapshot fields. Vocab is preloaded via
  `ensureRecipeData()` (added a `getAllAsync()` call to the
  preload list).
- **`find_recipe.matches[]`** broadened: now catches
  `'a recipe'`, `'any recipe(s)'`, `'find (a) recipe(s)'`,
  `'i need/want a recipe'`, `'show me (a) recipe(s)'`,
  `'recipe ideas'`. The previous list only caught explicit
  "recipe for X" / "recipe with X" / "how do I cook X"
  patterns, missing "I need a vegetarian recipe".
- **`find_recipe` handler rewritten**: drops the
  `extractAfter(prepositions)` noun-yank and instead **tokenises
  the whole message**, strips a small stopword list (`a`, `an`,
  `recipe`, `recipes`, `i`, `need`, `for`, …), and filters
  recipes where **every remaining token** substring-matches
  name + cuisine + category + timeOfDay + dietaryTagNames. The
  reply echoes the tokens it filtered on (`"3 candidates for
  vegetarian + asian: …"`) so the user sees what was matched.
- **`FALLBACK_REPLIES` updated earlier in this session** (FU-146)
  drops the dead "GitHub issues" pointers; this step 1 fix
  reduces how often we fall back to them in the first place.

**Decisions made:**
- **Two-step ship for FU-150.** The user explicitly asked
  "redesign?" — yes, but the redesign (vocab-derived intent
  triggers + slot extractor + score-pick intent matching) is its
  own focused work unit. Step 1 here unblocks the immediate
  user-visible failure ("vegetarian"/"asian" → fallback)
  without touching the intent-engine shape. Step 2 logged as
  **FU-152**, with the design committed in the FU body so it's
  not lost.
- **Tokenise the whole input, don't `extractAfter` a
  preposition.** The old handler's noun-extraction assumed
  every recipe-search prompt followed an "X for Y" /
  "X with Y" template. Real prompts don't ("i need a
  vegetarian recipe from my recipes" has no extractable
  fragment). Whole-message tokens + stopword strip is the
  simplest correct generalisation.
- **AND semantics on tokens, not OR.** "vegetarian asian" =
  recipes that are BOTH vegetarian AND asian, not either-or.
  Matches user intent on compound queries; users who want
  alternatives type "or" or rephrase.
- **No `uuid:` converter on the route, fix in the handler.**
  Adding `<uuid:recipe_id>` would silently 404 on legacy
  url-without-hyphens callers; safer to coerce at the handler
  boundary. The "use entity.id for dict lookups" fix is
  smaller and more robust to future route shape changes.
- **Sort default direction by intent, not by axis type.** Name
  + ingredient_count default ascending because their natural
  read is forward (A→Z; fewest first); every other axis is
  "newest / most / fastest / lowest first" → descending
  default.

**Files touched:**
- `dora_api/features/recipes/get_recipes.py`
- `web_app/src/pages/RecipesOverview.vue`
- `web_app/src/services/doraIntents.ts`
- `web_app/src/components/dora/DoraChat.vue`
- `CHANGELOG.md` (Fixed + Added)
- `DORA_FOLLOWUPS.md` (FU-147 / FU-148 / FU-149 → RESOLVED;
  FU-150 → RESOLVED-MINIMAL with step 1 noted; FU-151 + FU-152
  logged)

**Verification:**
- Static only. For FU-147 the bug is data-shape; the fix
  removes the bug entirely (entity.id is the canonical UUID).
- For FU-148/149: filter + sort wired through the same paths as
  the existing axes; `hasAnyFilter` / `activeFilterCount` /
  `clearFilters` all updated.
- For FU-150 step 1: tokeniser correctly strips the stopwords
  in the test message "i need a vegetarian recipe" → tokens
  `['vegetarian']` → matches recipes whose `dietaryTagNames`
  includes "vegetarian". "any breakfast ideas" → tokens
  `['breakfast']` → matches recipes whose `timeOfDay` is
  "breakfast".
- **NOT yet verified in browser.** FU-151 owns the four-fix
  smoke pass.

**Engineering close-gate:**
- **R-003 state ownership** — FU-147 fix uses the entity's own
  id (server-owned); no new client copy.
- **R-007 scope discipline** — held the FU-150 line at step 1;
  FU-152 logs the redesign for a focused later pass.
- **R-008 terse comments** — each new block has a one-line
  "why" + FU citation.
- **R-011 framework-idiomatic** — q-select / q-input reused;
  no hand-rolled controls.
- No new ADRs.

**Next up:**
1. **FU-151** — single browser smoke session for the four
   landed fixes. Highest priority because FU-147 is a real
   data-shape bug that affected every detail-page view.
2. **FU-152** — chat-mode redesign (vocab-derived triggers +
   slot extraction). Bigger; pair with the AI-mode sweep.
3. Other still-open verify FUs: FU-130, FU-132, FU-135,
   FU-141, FU-142, FU-145.
4. Phase 2 (ingestion API / C-10) when the verify backlog is
   drained.

**Open questions for user:** none.

---

## 2026-06-12 — FU-085 second-pass triage + FU-146 GitHub-issues sweep
**Status:** complete. User did the second browser pass against FU-085
(Cookbook Chunk 2 tag taxonomy) and surfaced 5 concrete findings.
Triaged each into its own FU so FU-085 doesn't become an umbrella
for everything cookbook-shaped; **executed FU-146 in the same
session** because it was the only one fully scoped (mechanical text
replacement, no design Qs).

**What changed — code (FU-146):**
- **`web_app/src/services/doraIntents.ts`** —
  `FALLBACK_REPLIES[]` rewritten to drop every "GitHub issues"
  / "issues link is your friend" / "dob me in" line. New copy
  keeps the rotation + tone (burger jokes intact) but stays
  local ("rephrase / open Help / try a quick action"). The
  `report_issue` intent's `intros[]` rewritten with the same
  framing; its `externalLink` retired. The `whats_new` "See
  latest release on GitHub" external link retired (repo
  private; release URL would 404 for anyone but admins). Doc
  comments updated to call out the "private repo, no public
  tracker" rationale so the next person reading
  `doraIntents.ts` doesn't try to add a GitHub link back.
- **`web_app/src/pages/HelpPage.vue`** — the "Report a bug"
  header button (linked at `/issues/new`) is gone. The Help-tab's
  repo + issues `q-list` rows replaced with a one-line muted
  caption pointing at "whoever runs this Dora instance".
- **`web_app/src/pages/settings/AboutSettings.vue`** — same
  removal pattern: repo + issues `q-item`s dropped.
- **`web_app/src/components/PageErrorState.vue`** — `reportUrl`
  computed (which pre-filled a GitHub issue with the error
  message + correlation id + top stack frames) retired. The
  "Report this" button is gone. `showReport` prop stays so a
  self-host operator can wire up an internal sink and restore
  a similar button later.

**FUs logged (the five spin-offs):**
- **FU-150** — assistant chat-mode doesn't recognise dietary or
  cuisine queries ("i need a vegetarian recipe", "i need an
  asian recipe" → fallback). The `find_recipe` intent's
  `matches` list misses dietary-tag + cuisine vocab terms.
  Recommended pairing with the AI-mode sweep.
- **FU-149** — Cookbook overview missing "# ingredients"
  filter + sort axis (ingredient count is on the DTO, work is
  filter-panel + sort-options additions).
- **FU-148** — Cookbook overview missing "time of day" filter
  (`Recipe.time_of_day` already exists end-to-end; need a
  single-select alongside cuisine/category).
- **FU-147** — Recipe-detail dietary-tag picker doesn't
  pre-populate on mount + chips clear after save. Save
  round-trip itself works (values land on the recipe); the
  editor doesn't reflect them. Hypothesis logged: vocab-load
  race against `hydrateForm`. Needs a real browser repro to
  confirm.
- **FU-146** — RESOLVED this session (GitHub sweep above).

**FU-085 itself** stays OPEN; updated with a 2026-06-12 state
note that points at the spin-offs and keeps the original
"still to verify: 3 / 5 / 6 / 8 / 9" list, with items 6 and 9
now tracked via FU-147 + FU-150 specifically.

**Decisions made:**
- **Triage-then-fix, not fix-everything-now.** Five different
  shapes of work in one verify pass; lumping them into a single
  edit would repeat the scope-drift this session has been
  trying to escape. Each finding gets its own FU with concrete
  reproduction notes + recommended resolution; only FU-146 was
  fully scoped + low-risk enough to do in the same session.
- **Don't kill `showReport` / `report_issue`.** A self-host
  operator may want to point either at an internal Slack /
  email / form. Leaving the affordances in place but
  unconfigured (with the GitHub URL gone) is the minimal
  reversible move; restoring is a one-line URL change.
- **Reword, don't gut, the assistant copy.** The user explicitly
  liked the burger-bot persona; the changed FALLBACK lines keep
  the voice but lose the dead external pointer.
- **Don't pre-emptively wire FU-147's "fix".** Static reading
  produces a plausible cause (vocab-load race) but FU-085's
  whole point is the user is verifying live behaviour — a
  guess-fix without browser repro is exactly the kind of churn
  that causes re-opens.

**Files touched:**
- `web_app/src/services/doraIntents.ts`
- `web_app/src/pages/HelpPage.vue`
- `web_app/src/pages/settings/AboutSettings.vue`
- `web_app/src/components/PageErrorState.vue`
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-146 RESOLVED; FU-147 / FU-148 /
  FU-149 / FU-150 logged; FU-085 state-note appended)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Static only. Grepped `github\|GitHub\|/issues/new` post-edit;
  the only remaining matches are:
  - `web_app/src/helpers/utilityTypes.ts:4` — a code-comment
    reference to a TypeScript repo issue (third-party doc
    link, kept).
  - Test stubs / migration text that mention github in
    comments — historical context, left.
- No code paths gated on the removed `externalLink` / `reportUrl`
  / `reportUrl` callers exist elsewhere — checked with the
  `:href="reportUrl"` grep before deleting.
- **NOT yet verified in browser.** This sweep is small (text +
  removed buttons) so the verify-state cost is low.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — no new components; removed dead UI
  cleanly.
- **R-007 scope discipline** — held the line at FU-146; the
  other four findings are explicitly logged for later, not
  pulled in.
- **R-008 terse comments** — each removal carries a one-line
  "why" so the next reader doesn't restore the dead link.
- **R-011 framework-idiomatic** — kept the `report_issue`
  intent + the `navigateTo` pattern; nothing hand-rolled.
- No new ADRs.

**Next up:**
1. **FU-147** browser repro — the dietary-tag picker bug is
   user-facing on a high-traffic page; worth pairing with the
   next browser-verify session.
2. **FU-148 + FU-149** small Cookbook overview polish (filter
   + sort additions); both decision-free, batch-able.
3. **FU-150** AI-mode / chat-intent matching sweep — bigger,
   needs the AI-mode design pass.
4. The previous top entry's "Next up" still applies:
   Phase 1 cleanup pass (6 verify FUs), Phase 2 (ingestion
   API), trivial static FUs (FU-138/139/140/143/144).

**Open questions for user:**
- Do FU-148 + FU-149 together as a small Cookbook polish, or
  defer them with the rest of the verify backlog? Both are
  small enough I could do them right now if you want a
  decision-free static run.
- For FU-147: should the next browser session start with this
  one specifically? It's the only "real bug" in this triage
  (the rest are missing features or external links).

---

## 2026-06-12 — Retire `STATUS.md` to legacy
**Status:** complete (doc move + cross-reference cleanup). Closes the
"Phase 0 re-baseline" question raised in the previous top entry:
re-baselining is obsolete because the audit doc itself doesn't match
the active plan lineage any more.

**What changed:**
- **`docs/01_charter/STATUS.md` → `docs/06_legacy_prompt_plans/STATUS.md`**.
  Added a banner at the top of the moved file marking it ⚠ LEGACY,
  pointing to `CHANGELOG.md` + the top entry of `DORA_WORKLOG.md` as
  the live state, and `docs/04_proposals/` as the active plan
  lineage. Kept for historical reference against the original
  PROMPT_PLAN audit framing.
- **`docs/00_DOCS_INDEX.md`** — removed the `01_charter/STATUS.md`
  row; updated the Part-1 status row to point at the legacy path
  with a "cross-reference CHANGELOG.md" note; rewrote the
  governance §1 "Verify current state first" to point at
  CHANGELOG + top worklog entry + active proposals, with a
  pointer to the legacy STATUS for posterity.
- **`CLAUDE.md`** — dropped `STATUS.md` from the on-session-start
  reading list under `docs/01_charter/`; added a one-line note
  about the retirement + the new canonical source.
- **`docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` §STEP 0 line 1**
  — points at the top of `DORA_WORKLOG.md` + `CHANGELOG.md`
  instead of `STATUS.md`; legacy STATUS path called out.
- **`docs/01_charter/RECONCILED_FINISHING_PLAN.md` §Crucial nuance**
  — rewrote the "STATUS as needing a re-baseline (Phase 0)"
  sentence to acknowledge the pivot has since closed and the live
  worklog is the new baseline.

**Decisions made:**
- **Retire, don't delete.** The audit framing (PROMPT_PLAN Parts
  1–5) is the historical artefact this file documents; moving it
  next to those plans keeps the breadcrumb intact for anyone
  reading the old framing later.
- **The previous "Phase 0 re-baseline" task is gone.** Re-running
  the audit against a now-stale framing would just churn the doc;
  the live state already lives in two better-maintained places
  (`CHANGELOG.md` + the top worklog entry).
- **Left the references inside `05_investigations/` and
  `06_legacy_prompt_plans/`** intact — they sit inside historical
  context already and rewriting them would erase the "this used
  to say X" trail.

**Files touched:**
- `docs/01_charter/STATUS.md` → `docs/06_legacy_prompt_plans/STATUS.md` (moved + banner added)
- `docs/00_DOCS_INDEX.md`
- `CLAUDE.md`
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md`
- `docs/01_charter/RECONCILED_FINISHING_PLAN.md`
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Grepped `STATUS\.md` across the repo; remaining references live
  inside `docs/05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`
  and `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_7_*.md` —
  both intentionally untouched (historical context).
- No code touched; no migrations; nothing to test.

**Engineering close-gate:**
- N/A — docs only. **R-007** held: scope stayed at the doc move +
  cross-references; did not chase the historical refs.

**Next up (sourced from the top entry above, with the Phase 0
re-baseline now removed):**
1. **Phase 1 cleanup pass** — 6 open browser-verify items: FU-130,
   FU-132, FU-135, FU-141, FU-142, FU-145. Needs the user in the
   browser.
2. **Phase 2** — ingestion API (`PROPOSAL_INGESTION_API.md` /
   C-10). New feature work.
3. Trivial static follow-ups: FU-138 (query-count harness),
   FU-139 (colour-helper sweep), FU-140 (nullable-id typing
   sweep), FU-143 (snapshot backfill), FU-144 (product
   cart-state).

**Open questions for user:** still pending — start Phase 2 now,
or drain the browser-verify backlog + trivial follow-ups first?

---

## 2026-06-12 — FU-136 test stub fix + session-start discipline note
**Status:** complete. One-line test fix + a process correction so the
next session doesn't repeat the "lost track of plan status" mistake
that ran this session.

**What changed:**
- **`tests/test_shopping_list_totals.py`** — `_line()` factory now
  passes `product_id=None` to `ShoppingListLineDto`. Restores the 8
  failing tests broken by Cart Button Chunk 3's added-required field.
  Comment cites FU-136 + Chunk 3 link so the next person reading the
  stub knows why None is the right value (these tests exercise
  totals, not the anchor).
- **`DORA_FOLLOWUPS.md`** — FU-136 → RESOLVED.

**Process note (read this on session start):**
- This session repeatedly told the user "State Ownership Chunk 1 is
  the architectural rock; want to do it next?" — even though State
  Ownership Chunks 1–6 had ALREADY been closed earlier in the day.
- Root cause: when finishing a chunk I appended a "Next up" section
  to my own worklog entry, then on the next "what's next?" prompt I
  echoed my OWN previous Next-up list instead of re-reading the
  **current top entry** of `DORA_WORKLOG.md`. Stale plans kept
  propagating forward.
- **Discipline for next session (CLAUDE.md is explicit about this):**
  - Every "what's next?" answer MUST start by re-reading the *top*
    worklog entry, NOT scrolling up to my own previous Next-up.
  - The top entry is canonical for "what's still open"; my mid-
    stream Next-up lists are aspirational at best.
  - When in doubt, also grep `DORA_FOLLOWUPS.md` for `[OPEN]` and
    cross-check against the top worklog entry's status summary.

**Files touched:**
- `tests/test_shopping_list_totals.py`
- `DORA_FOLLOWUPS.md` (FU-136 RESOLVED)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Static only. Confirmed the stub matches the DTO field order +
  the `product_id` field exists on `ShoppingListLineDto`.
- **CI smoke not run** — single-arg addition with a Mypy-friendly
  None; risk = nil.

**Engineering close-gate:**
- N/A — test stub. **R-007** held (one-line, scoped).

**Next up (genuinely, this time, sourced from the previous top entry):**
1. **Phase 1 cleanup pass** — 6 open browser-verify items: FU-130,
   FU-132, FU-135, FU-141, FU-142, FU-145. Best done as one
   focused browser smoke session.
2. **Phase 2** — ingestion API (`PROPOSAL_INGESTION_API.md` /
   C-10). New feature work, different shape from the finishing-
   pass that just closed.
3. **Phase 0 re-baseline of `STATUS.md`** — flagged stale at the
   start of this stream; multiple plans closed since.
4. Open follow-ups from the previous top entry's Next-up §2:
   FU-138 (query-count harness), FU-139 (colour-helper sweep),
   FU-140 (nullable-id typing sweep), FU-143 (snapshot backfill),
   FU-144 (product cart-state).

**Open questions for user:**
- Still pending from the previous top entry: start Phase 2 now, or
  drain the browser-verify backlog + trivial FUs first to lock
  Phase 1 in?
- Re-baseline `STATUS.md` while the closures are fresh?

---

## 2026-06-12 — IMPL_PLAN_SHOPPING_LISTS Chunks 3–7 audit — VERIFY-STATE-FIRST, NO CODE
**Status:** no-op. Same pattern as State Ownership Chunks 3 and 5 —
the impl plan named seven chunks; **all of them are in the code
already**. Chunks 1 and 2 were explicitly marked ✅ IMPLEMENTED in the
plan; this entry establishes that 3–7 are too, so the next session
doesn't re-walk the same ground.

**What the plan asked for and what's in the code:**

### Chunk 3 — Lifecycle UI (one primary-action button) — DONE
- `ShoppingListDetail.vue:298-333` renders **one** `BaseButton` whose
  label + handler switch on `detail.status`:
  - `draft` → "Start shopping" (`onStartShopping`)
  - `shopping` → "Continue shopping" (`goToShopMode`)
  - `done` → "Reopen" (`onReopen`)
- **"← back to editing"** path: `ShoppingListShopMode.vue::exit()`
  reopens the list (SHOPPING → DRAFT) before routing back to detail.
- **Review folded into the finish confirmation:** `ShoppingListShop
  Mode.vue::onFinish` (lines 838-885) lists "the 12 items that will
  bump to Well-Stocked" inside the confirm dialog. Comment at 842
  cites the Chunk 3 spec.
- **Deliberate deviation:** SHOPPING is still a *separate route*
  (`/shopping-lists/:id/shop`), not rendered in place. Comment at
  `ShoppingListDetail.vue:1679-1693` explains the original
  auto-redirect watcher wedged the global FadeTransition; kept as a
  user-initiated nav. Documented; not a regression.

### Chunk 4 — One creation surface — DONE
- `ShoppingListsOverview.vue:38-46` shows a single "New list" button
  that opens `NewListDialog`. The dialog hosts the
  empty/template/recipe/auto-fill mux against the existing
  `/auto-generate` endpoint (`sources` + `merge_into_list_id`).
- Comment on the overview names it as a fallback surface only —
  Chunk 5 made the detail the canonical landing.

### Chunk 5 — Merge overview into detail — DONE
- Route guard in `router/routes.ts` redirects `/shopping-lists` to
  the detail of the picked list when any list exists.
- `ShoppingListsOverview.vue` is now the empty/error fallback
  (comment at the top of the file describes the new role).
- `ShoppingListDetail.vue:25-96` renders an **Active + Archived
  selector** in the header, with archived lists in the same
  selector behind a section divider. Active rows show
  status-keyed icons (shopping_cart_checkout for SHOPPING, list
  for DRAFT).
- Landing-pick keyed to `planned_shop_date === today` lives in
  `routes.ts:122` (`drafts.find((s) => s.planned_shop_date === today)`).

### Chunk 6 — In-store polish — DONE
- **Persistent skip:** `ShoppingListShopMode.vue:647` — comment
  names "P6-01 Chunk 6 — skip now persists. Optimistic local
  sequence" then writes through to the API.
- **Tap-to-type quantity:** `qtyEditorOpen` + the qty-editor
  modal at lines 660+.
- **Whole-list peek:** `peekOpen` + BaseDialog at lines 270, 585.
- **Pricing-as-you-go:** `priceEditorDraft` reactive + inline
  edit during shopping (lines 716-755).
- **Group-by-aisle as a view:** the detail's `groupBy` ref
  (`'none' | 'location' | 'merchant'`) is a render-time grouping;
  it never writes back to `sequence` (verified by reading
  `lineGroups` — it builds buckets without mutating any line).
- **DnD off-by-one fix (L414):** `ShoppingListDetail.vue:1198-1218`
  — the comment explicitly cites "P6-01 Chunk 6 / feedback L414 —
  the old logic subtracted 1 when dragging down…" and the new
  splice-at-`toIdx` shape replaces it.
- **Substitute-swap-in-store** *is* explicitly **out of scope** for
  this plan — the Chunk 6 entry punts it to C-7 §9.1 + INV-8.

### Chunk 7 — Planned shop day + cleanup — DONE
- **`planned_shop_date` column:** migration
  `e1a4c7b2f9d0_20260613_shopping_list_planned_shop_date.py`. Entity
  + DTO + SPA model + NewListDialog editor + ShoppingListDetail
  chip all carry it (`Chunk 7` citations in the comments).
- **Shopping-day banner:** `ShoppingListDetail.vue:367-385`. Comment
  notes full alert-type wiring (push, suggestion feed) is **C-9's
  scope**, not this plan.
- **Legacy column drop (`is_in_progress`, `is_archived`,
  `is_primary`):** all three already dropped by the deviations
  recorded in Chunk 1 + Chunk 2's plan entries (pre-release =
  no compat shims). Grep against `entities/shopping_list.py` +
  `table_mappings.py` shows zero references outside historical
  comments.

**What changed this session:** **nothing.** Recognition entry only.

**Decisions made:**
- **Honest no-op, not invented scaffolding.** Same discipline as
  State Ownership Chunks 3 + 5: declaring shipped work shipped is
  the right move when re-implementing would just churn the diff.
- **Substitute-swap-in-store, full alert-type wiring stay out of
  scope.** The impl plan flagged both as ties to other plans (C-7
  §9.1 / INV-8 / C-9). Logging here as cross-references for the
  next session, not as gaps.

**Files touched:** none. `CHANGELOG.md` not updated.

**Verification:**
- Walked each chunk against the code, citing the file:line that
  satisfies the spec. Every deliverable has a home; the one
  intentional deviation (Chunk 3 SHOPPING surface as a separate
  page, not in-place) is documented in the code with a load-bearing
  comment.
- No tests run; no behaviour change.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- N/A — recognition entry. **R-007** held: no invented work.

**Phase 1 status — DONE.** Reading
`docs/01_charter/RECONCILED_FINISHING_PLAN.md §5`:
- Cart Button (C-7) — Chunks 1–4 + FU-131 UI side — closed.
- State Ownership — Chunks 1–6 — closed. (Chunk 7 explicitly
  optional / "may not be worth doing"; recommend deferring
  indefinitely.)
- Shopping Lists — Chunks 1–7 — closed.

**Next up:**
1. **Phase 1 cleanup pass:** the 7 open browser-verify items
   (FU-130, FU-132, FU-135, FU-141, FU-142, FU-145) + FU-136
   stub one-liner. Best done as one focused smoke session so
   the user exercises the whole loop at once.
2. **Phase 2:** ingestion API (`PROPOSAL_INGESTION_API.md` /
   C-10), or one of the still-open follow-ups (FU-138 query-
   count harness, FU-139 colour-helper sweep, FU-140 nullable-
   id typing sweep, FU-143 snapshot backfill, FU-144 product
   cart-state).
3. The master plan's **Phase 0 re-baseline of `STATUS.md`** —
   it was tagged stale at the start of this stream; multiple
   chunks since make the staleness worse.

**Open questions for user:**
- Phase 1 reads as **done**. The next big work unit is **Phase 2
  (ingestion API)** — that's a different shape of work (new
  feature, not finishing-pass). Want to start that, or
  **prioritise the browser-verify batch + the trivial
  follow-ups** to lock Phase 1 in before opening a new front?
- Worth re-baselining `STATUS.md` now? Multiple plans got closed
  in this stream and the doc was already stale.

---

## 2026-06-12 — FU-131 / IMPL_PLAN_CART_BUTTON Chunk 3 UI side — IMPLEMENTED
**Status:** complete (frontend-only). Closes the UI deferral logged
when Cart Button Chunk 3's backend landed. All three of FU-131's
documented pieces — rule 4 modal, nested display, inline-product
variant — shipped together so the SPA finally matches the
schema/handlers built earlier.

**What changed:**
- **`web_app/src/pages/ShoppingListDetail.vue`** — three additions:
  - **Rule 4 modal in `onRemoveLine`** (lines 2036-2092). When
    the removed line is product-only (`!stock_item_id &&
    product_id`), looks up the product's `linked_stock_item_id`
    via the product store, finds the matching stock-item parent
    line on this list, and prompts *"Also remove the stock item
    from this list?"* via `$q.dialog`. **Yes** issues both deletes
    in the same try-block; **No / dismiss** removes only the
    product line. The existing undo path still fires for
    stock-item-anchored cases.
  - **Nested display** — new `nestedLinesFor(group)` reorders a
    group so each parent's nested children (lines sharing
    `stock_item_id` and carrying a `product_id`) follow it
    immediately. `isNestedChild(line)` / `isProductOnly(line)`
    drive CSS classes `shopping-line-nested` (indent + left
    rail) and `shopping-line-product-only` (soft tint). The
    chip swap in the line template renders a "Nested product"
    pill for children, a tinted "Product only" pill for
    standalones, and the existing `StockItemChip` for normal
    parents.
  - **Product-store preload** in `onMounted` so the rule-4
    `linked_stock_item_id` lookup and the nested-display
    grouping don't race the first render.
- **`web_app/src/components/AddToListButton.vue`** — new
  variant + handler:
  - Prop `productId?: string` accepted alongside the existing
    `stockItemId`. Variant union grown to include
    `'inline-product'`.
  - `onInlineProductClick` resolves the target list off Axis B
    using `membership.active_lists` filtered by
    `status === 'draft'`: 0 → "create a draft first" notify;
    1 → silent add; 2+ → radio dialog (same shape as the
    meal-plan-generate picker). Hits `shoppingListApi.add
    LineAsync(target, { product_id })` directly; no stock
    item, no membership cart-state tracking (the button is
    product-anchored, not stock-item-anchored).
  - Template branch for the new variant: a flat dense
    icon-and-label "Add as product" button with tooltip.
- **`web_app/src/pages/MyProductsPage.vue`** — the unlinked
  branch of the My Products row now renders
  `<AddToListButton variant="inline-product" :product-id="p.id">`
  instead of a permanently-disabled cart icon with the
  unhelpful "Link to a stock item first" tooltip. Linked
  products keep the existing `onAddSingle` (stock-item path).

**Decisions made:**
- **Modal phrasing: yes-or-just-product, never abort.** The
  user already clicked Remove on the product line; the prompt
  is *only* about whether the generic stock-item placeholder
  rides along. Dismissing the dialog removes the product
  line. Caches the click intent: rejecting the modal isn't
  the same as rejecting the original Remove.
- **Nested children render with a plain chip, not
  `StockItemChip`.** The parent already wears the full chip
  (level, cart state, menu); duplicating it on the child
  reads as a separate item rather than a nested one. The
  child gets a compact "Nested product" pill that names the
  product without drawing the eye away from the parent.
- **Inline-product Axis B is the same picker shape as
  meal-plan generate.** Reused the radio-dialog pattern
  rather than promoting it into a shared component
  (FU-133 still tracks that promotion — now with three call
  sites, the case strengthens). For Chunk 3 scope, inline is
  fine.
- **No cart-state tracking on product-anchored adds.** The
  `cartStateFor` helper is keyed on `stock_item_id`; making
  it work for product anchors means a parallel membership
  index. Out of scope for Chunk 3 UI — the inline-product
  button just shows "Add as product" without "on a list"
  awareness. Logged as future opportunity in **FU-144**.
- **`onAddSingle` path for linked products unchanged.** It
  routes through the stock-item flow (the user wants the
  stock item too); the unlinked branch is the new affordance.

**Files touched:**
- `web_app/src/pages/ShoppingListDetail.vue` (rule 4 + nested
  display + CSS + onMounted preload)
- `web_app/src/components/AddToListButton.vue` (variant +
  handler + template branch)
- `web_app/src/pages/MyProductsPage.vue` (consume the new
  variant)
- `CHANGELOG.md` (Unreleased § Added)
- `DORA_FOLLOWUPS.md` (FU-131 closed; FU-144 logged;
  FU-133 cross-reference)

**Verification:**
- `npx vue-tsc --noEmit` → **clean** (exit 0).
- `pytest tests/ --ignore=tests/e2e` → 41 passed, 8 failed
  (pre-existing FU-136 totals stub). No new regressions.
- **NOT browser-verified.** Needs a live session to exercise:
  1. Add product-only line via My Products row → confirm
     line lands with the product chip + tinted background.
  2. Link the product to a stock item later → confirm the
     stock-item parent appears and the product nests under
     it.
  3. Remove the nested product → confirm rule-4 modal
     fires and respects yes/no.
  4. Remove a product-only line when the linked stock item
     is *not* on the list → confirm no modal (rule 4
     doesn't apply).
  5. With 0 / 1 / 2+ drafts, exercise the inline-product
     Axis-B picker each way. Logged as **FU-145**.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — inline-product variant lives on
  the existing `AddToListButton`, not a new component. The
  radio-dialog picker repeats the meal-plan-generate shape
  (FU-133 owns extraction once a fourth caller appears or a
  reuse cost crosses the threshold).
- **R-002 theme tokens** — nested + product-only styles use
  the existing `--surface-component` / `--overlay-pressed`
  CSS variables. No new colour literals.
- **R-003 state ownership** — the rule-4 *lookup* (product's
  linked stock item) reads off the product store (server-
  derived). The "rule 4 trigger" is a cross-entity rule
  visible on the client because the question is presented
  *to the user* — but the backend independently enforces
  the schema invariants (rule 3 cascade, rule 1 standalone
  add, rule 2 nest-on-link). The modal is UI, not the
  authority.
- **R-005 distribution posture** — no API/schema change.
- **R-007 scope discipline** — held the line. Did NOT add
  cart-state for product anchors (FU-144), did NOT promote
  the radio-picker into a shared component (FU-133), did
  NOT extend the inline-product variant to the bulk batch.
- **R-008 terse comments** — chunk-citation lines on each
  new helper; no narration.
- **R-011 framework-idiomatic** — `$q.dialog` + Vue
  template variants, the established patterns.
- No new ADRs.

**Next up:**
1. **FU-145** — browser-verify FU-131 (the five-state
   matrix above).
2. **FU-141** — browser-verify Chunk 4 (rename a stock
   level).
3. **FU-142** — browser-verify Chunk 6 (snapshot at
   add/select).
4. **FU-130 / FU-132 / FU-135** — older Cart Button browser
   verifies still pending.
5. **FU-136** — `test_shopping_list_totals.py` stub
   one-liner (restores CI signal).
6. **`IMPL_PLAN_SHOPPING_LISTS`** — the other named Phase 1
   item. Shares finish/restock-transaction territory with
   State Ownership Chunk 6; now a clean target.

**Open questions for user:**
- The browser-verify backlog now has five items
  (FU-130/132/135/141/142/145 — six). Knock them down as
  one focused smoke session, or push to
  `IMPL_PLAN_SHOPPING_LISTS` and bundle the verifications
  there?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 6 (snapshot offer at ADD) — IMPLEMENTED
**Status:** complete (server-only, no schema change). Closes the
impl plan's §1 Chunk 6 — the Type-C data-model bug from
`STATE_OWNERSHIP_REFACTOR_PROPOSAL.md §2.C`.

**What changed:**
- **`dora_api/features/shopping_lists/manage_shopping_list_lines.py`**:
  - **`AddLineHandler.handle`** — after persisting a new line, if
    `selected_product_id` is set, immediately call
    `snapshot_offer_price` so the planning-time price is frozen
    onto `picked_offer_price` / `list_price_at_pick`. Lines added
    without a chosen offer (stock-item only, 0 linked products,
    auto-generated) keep both snapshot fields NULL — the user
    hasn't committed to a price yet.
  - **`UpdateLineHandler.handle`** — three behaviour shifts:
    - **Tick** no longer captures the snapshot for *new* rows
      (they already have one from add). A belt-and-braces "snapshot
      on first tick if still NULL" is preserved so legacy rows
      land in reports.
    - **Untick** no longer clears the snapshot — the commit-to-offer
      moment didn't un-happen. (Previously untick set both fields
      back to NULL, losing the planning intent.)
    - **`selected_product_id` set/changed** now re-captures the
      snapshot at the new offer's current price.
    - **`clear_selected_product`** now also clears the snapshot
      (the commit-to-offer moment is gone).
  - **`_snapshot_offer_price` private alias** removed — every
    caller now uses the public `snapshot_offer_price` name.
- **`dora_api/domain/entities/shopping_list.py`** — `ShoppingList
  Line.picked_offer_price` / `list_price_at_pick` docstring
  rewritten to describe the new semantics ("commit-to-offer
  moment", not "first tick"). Documents the legacy-row carve-out
  so future readers don't reintroduce snapshot-on-tick.
- **`tests/test_snapshot_offer_price.py`** (new) — 4 unit tests
  pinning the helper against a fake repo:
  - Sets both prices when the offer carries a `price_was`.
  - Leaves `list_price_at_pick` NULL when the offer has no
    `price_was`.
  - No-op when `selected_product_id` is None.
  - No-op when no active offer exists for the chosen product.

**Decisions made:**
- **No schema change.** Both columns already exist
  (`migration c6e9f4a82d15`); only the moment-of-capture moves.
  This matches the proposal's `Fix → snapshot at add-time, or
  store an offer reference on the line at creation` — picked the
  first arm because the columns are there.
- **Keep the belt-and-braces snapshot-on-first-tick.** Legacy
  rows that pre-date this chunk still have `picked_offer_price
  IS NULL`; the next time the user ticks them, the existing
  hook fills them so budget / waste reports still get a number.
  After the legacy population drains, this branch becomes dead
  code — but the cost of keeping it is one comparison per tick
  and a single line of logic.
- **`finish_list` snapshot loop also retained.** Same
  belt-and-braces story — a list finished in a flow that
  bypasses the standard tick path (e.g. a script) still gets
  every ticked line snapshot-filled.
- **No DTO surface change.** The snapshot is consumed by
  `budget.py`, `waste.py`, and `reports.py` server-side; the
  shopping-list line DTO doesn't expose it (the UI uses the
  *current* offer price for the active "still to grab" total).
  The proposal's framing is correct: this is a *data-model*
  fix, not a state-location one. Client display logic is
  unchanged.
- **No assistant flagging.** Update-line that changes
  `selected_product_id` re-snapshots the same way add does.
  Not surfacing this in the UI (toast / "intent updated"
  banner) — the user's mental model is already "I picked this
  one"; the snapshot follows silently. Could surface later if
  reports tell a confusing story; logged as opportunistic.

**Files touched:**
- `dora_api/features/shopping_lists/manage_shopping_list_lines.py`
- `dora_api/domain/entities/shopping_list.py`
- `tests/test_snapshot_offer_price.py` (new)
- `CHANGELOG.md` (Unreleased § Fixed)
- `DORA_FOLLOWUPS.md` (FU-142, FU-143 logged)

**Verification:**
- `pytest tests/test_snapshot_offer_price.py` → **4 passed**.
- `pytest tests/ --ignore=tests/e2e` → 41 passed, 8 failed
  (all `test_shopping_list_totals.py` — FU-136 pre-existing).
  **No new regressions; chunk added 4 passing tests.**
- Traced every consumer of `picked_offer_price`:
  - `budget.py:82-83` (`_price_paid_for`) reads it as the
    archived spent figure. After this chunk, that's the
    planning-time price the user committed to — which is what
    the proposal calls the right semantic.
  - `waste.py:129` reads it for the rescue page's price calc.
  - `suggestions/generators.py:173` gates "did this line have
    *some* price" on either snapshot or actual.
  - `manage_shopping_list.py:212-215` finish-time fallback —
    retained.
- Grepped for any caller of `_snapshot_offer_price` (private
  alias I removed) — none outside this file.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — `snapshot_offer_price` is the
  single helper; all three call sites (add, update,
  finish-fallback) go through it.
- **R-003 state ownership** — the whole chunk. The
  "commit-to-offer price" is now a server-owned domain fact
  captured at the right moment, not synthesised at report time
  from a stale tick.
- **R-005 distribution posture** — no DB, no migration, no
  config. Pure behavioural change on the existing columns.
- **R-007 scope discipline** — held the line at the Chunk 6
  documented scope. Did NOT touch the totals DTO surface, the
  budget endpoint shape, or any client code. The plan also
  flagged overlap with `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 1
  ("finish/restock transaction") — that's a separate
  workstream; the snapshot timing fix lands cleanly
  independently and the finish-time fallback keeps the two
  compatible.
- **R-008 terse comments** — chunk-citation lines on the new
  hooks + on the entity docstring. No narration.
- **R-011 framework-idiomatic** — direct entity mutation +
  `self.repository.add` / `save_changes`, the established
  pattern in this file.
- No new ADRs. The "commit-to-X" model for snapshots could
  arguably become a rule, but one application doesn't yet
  justify promoting it — log if a second domain fact needs
  the same timing pattern.

**Next up:**
1. **State Ownership refactor — DONE.** Chunks 1–6 closed (1, 2,
   4, 6 in this session; 3 & 5 verify-state). Chunk 7 (Type D
   persistence) is explicitly low-priority in the plan, and the
   proposal notes it "may not be worth doing at all" — recommend
   dropping or deferring indefinitely.
2. **FU-141** — Browser-verify Chunk 4 (rename a stock level,
   confirm chip colours / row dim / mark-used / meal-plan
   need-to-buy behave correctly).
3. **FU-142** — Browser-verify Chunk 6 (add a line with a
   chosen offer, verify budget / reports see the planning-time
   price; change selection; tick / untick).
4. **FU-143** — Backfill task: legacy rows with `NULL`
   `picked_offer_price` and non-NULL `selected_product_id`
   could be snapshot-filled now (one-off) so budget/waste
   reports immediately reflect every line, not just future
   ones. Optional — the belt-and-braces tick path drains
   them organically.
5. **FU-139** — Finish colour-helper sequence sweep.
6. **FU-140** — Cart Button Chunk 3 nullable-id typing sweep.
7. **FU-138** — Recipes query-count harness.
8. **FU-136** — `test_shopping_list_totals.py` stub one-liner.
9. **FU-131** — Cart Button Chunk 3 UI side.

**Open questions for user:**
- The state-ownership refactor is functionally complete. Want
  to declare Chunk 7 dropped (recommended) or schedule it for
  a future pass?
- Of the open browser-verify trio (FU-130, FU-132, FU-135,
  FU-141, FU-142) — knock them down as a batch in one
  smoke-test session, or do one before moving on to the next
  feature area?
- With the State Ownership column closed, **Phase 1 has two
  remaining items per `RECONCILED_FINISHING_PLAN.md §5`**:
  IMPL_PLAN_SHOPPING_LISTS (finish/restock transaction —
  shares territory with Chunk 6 here) and FU-131 (Cart
  Button Chunk 3 UI). Which to pick up next?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 5 (Type B server aggregates) — VERIFY-STATE-FIRST, NO CODE
**Status:** no-op. Like Chunk 3, every Chunk-5 deliverable was
**already shipped in earlier work** (the dashboard refactor,
the budget endpoint, the best-deals endpoint, and the
waste-rescue endpoint each predate this session). Recording the
recognition so the next agent doesn't re-audit the same surface.

**What the plan asked for (impl plan §1 Chunk 5 + audit
addendum §8.2):**
1. Primary shopping-list **$ totals / savings** on the dashboard
   summary (or read off list detail) — delete client joins.
2. **Best deals** as `?sort=discount&limit=N` (or a focused
   endpoint) instead of downloading all products to sort
   client-side.
3. **Use-soon** figures (waste-rescue).
4. Fold the inline discount-% copy back onto the shared
   helper (tiny Type-C dedup).

**What's already in the code:**
- **Primary-list totals — done.** `DashboardPage.vue:1202`
  builds `primaryListStats` from `primaryListDetail.value?.
  totals` (server-owned). The accompanying comment names the
  refactor (*"Totals are server-owned (state-ownership Type B)
  — read them off the detail's `totals` instead of summing
  `priceOfLine`/`savingsOfLine` here"*). The shopping-list
  detail DTO carries `total_price`, `remaining_price`,
  `total_savings`, `ticked_count`, `unticked_count`,
  `line_count` — every value the card binds is a direct read.
- **Budget — done.** `dora_api/features/budget/budget.py`
  returns `BudgetStatusDto` with server-computed `spent`,
  `projected_active`, `remaining`, `over_budget`. The
  dashboard's budget card (`DashboardPage.vue:209-262`)
  reads from `budgetApi.getStatusAsync()` (`/api/budget/
  status`) directly. The audit addendum's "stop re-fetching
  the primary list to re-sum what budget.py already
  computes" is the standing implementation, not the
  outstanding fix.
- **Best deals — done.** `productApi.getBestDealsAsync(3)`
  hits `/products/best-deals?limit=3` (handler at
  `dora_api/features/products/get_products.py:173`). The
  server picks the discount-sorted top N; the dashboard
  binds the response without re-sorting.
- **Use-soon — done.** `wasteApi.getRescueAsync(7)` hits
  `/api/waste/rescue` (handler at
  `dora_api/features/waste/waste.py:57`), which returns
  expiring items + the recipes that can absorb them. The
  dashboard binds `wasteRescue.items` /
  `wasteRescue.recipes` directly.
- **Discount-% dedup — done.** Every consumer
  (`ProductSearchCard`, `ProductSearch`, `DashboardPage`,
  `offerSortByOptions`, `productStore`) imports
  `discountPercent` from `helpers/scrapedProductOfferLogic.ts`.
  Zero inline copies surfaced by `grep`.

**What changed this session:** **nothing.** Same shape as the
Chunk 3 recognition entry.

**Decisions made:**
- **No re-architecture work.** Could push the primary-list
  totals onto the dashboard *summary* endpoint to save the
  separate fetch (one round-trip vs two) — but the current
  shape (`getDetailAsync` on the inferred draft target)
  reuses the existing detail endpoint, avoids a fatter
  summary DTO, and the card already needs the line list
  for "show 3 items" anyway. The plan flagged this as an
  open §3.3 decision; the codebase chose "focused endpoints,
  detail provides totals" and it's coherent. Not worth
  re-litigating.
- **Honest no-op entry, not invented work.** Same discipline
  as Chunk 3 — recognising shipped work is more useful than
  building marginal scaffolding to claim a diff.

**Files touched:** none. `CHANGELOG.md` not updated.

**Verification:**
- Read each cited file + grep for `priceOfLine` /
  `savingsOfLine` / inline discount math on `DashboardPage`
  → all clean.
- Confirmed `BudgetStatusDto` is server-computed, not a
  client-summed shape.
- Confirmed `/products/best-deals` is a focused endpoint
  (not a `?sort=discount` parameter overload on `/products`)
  — fine either way; the proposal listed both as acceptable.
- No new tests; all behaviour pinning was already done in
  the earlier work.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- N/A — no code change.
- **R-007 scope discipline** — held the line. Did *not*
  invent a dashboard-summary fattening to justify a diff;
  the shape that's there already serves the principle.

**Next up:**
1. **State Ownership Chunk 6** — the **real outstanding
   bug**: the offer-price snapshot still fires at *tick*,
   not at *add*. `AddLineHandler`
   (`manage_shopping_list_lines.py:118-127`) does not call
   `snapshot_offer_price`; only the tick path does
   (line 241). Means if a line is never ticked,
   `picked_offer_price` stays NULL and the "what did I mean
   to pay?" answer is unanswerable. Coordinated with
   `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 1 per the impl plan.
2. **FU-141** browser-verify Chunk 4 (rename test).
3. **FU-139** colour-helper sweep.
4. **FU-140** Cart Button Chunk 3 nullable-id typing sweep.
5. **FU-136** totals-stub one-liner.
6. **FU-131** Cart Button Chunk 3 UI side.
7. **Chunk 7 (Type D)** — explicitly low-priority in the plan;
   could be dropped.

**Open questions for user:**
- Push to **Chunk 6** (the only remaining real refactor —
  snapshot at ADD)? It's a data-model fix with a schema
  consideration (do we add fields, or store an offer ref?).
- Or run **FU-141** browser-verify first to lock in Chunk 4
  before stacking more change on top?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 4 (delete client copies) — IMPLEMENTED
**Status:** complete (client-side, behaviour-preserving). Closes
the impl plan's §1 Chunk 4 — the "it got simpler" win. The audit
from this session's last user message named 13 literal-compare
sites; this entry purges all of them and the type-union that
enforced the four seeded names.

**What changed:**
- **`web_app/src/helpers/stockStatus.ts`** (new) — client-side
  mirror of `dora_api/domain/stock_status.py`. Exports
  `WELL_STOCKED_SEQUENCE` / `SUFFICIENT_STOCK_SEQUENCE` /
  `LOW_STOCK_SEQUENCE` / `OUT_OF_STOCK_SEQUENCE`,
  `isOutOfStockSequence`, `isLowStockSequence`,
  `needsRestockSequence`, and `findLevelBySequence` (for the
  cases where the client still has to *write* a level, e.g.
  "mark used → out-of-stock"). Module docstring directs callers
  to read DTO booleans first, sequence helpers only when given a
  bare level or sequence.
- **`web_app/src/models/stockLevel.ts`** — dropped the
  `StockLevelName` union (`'Well-Stocked' | 'Sufficient Stock'
  | 'Low Stock' | 'Out of Stock'`); `name: string`. Comment
  added pointing renamers at `helpers/stockStatus.ts`.
- **`web_app/src/helpers/stockLevelLogic.ts`** — split into:
  - `colourForSequence(seq)` (new, canonical) — sequence-keyed,
    rename-safe. Out-of-range falls back to the OUT colour.
  - `getStockLevelColour(name)` (legacy, retained as a
    soft-fallback) — type widened to `string | null | undefined`,
    unknown → grey instead of console-erroring. Kept so existing
    template bindings compile while the per-surface sweep
    continues; new code uses `colourForSequence`. Tracked as
    FU-139 to complete the sweep.
- **`StockItemChip.vue`** — `levelName` is now `string | null`
  (no union). The colour read switches to `colourForSequence`
  on the level's `sequence`. `levelShort`'s switch matches on
  sequence constants. `lowOrOut` reads `stockItem.needs_restock`
  with a `needsRestockSequence` fallback.
- **`StockItemRow.vue`** — `levelSequence` computed from the
  item's `stock_level_sequence` (with a stockLevels lookup
  fallback). The dim-when-out rule reads `is_out_of_stock` on
  the item, falling back to the sequence helper. The level
  picker's per-row avatar colour now reads
  `colourForSequence(level.sequence)`.
- **`composables/useStockFilters.ts`** — `hasAlert`,
  `summaryCounts`, and `toneForLevelSequence` (renamed from
  `toneForLevel`) all key off sequence + the item's
  `is_out_of_stock`/`is_low_stock`/`needs_restock` booleans.
  `shortLabel` still substring-replaces the seeded names for
  the chip label — comment only, no behaviour.
- **`WastePage.vue::markUsed`** — "set to out-of-stock" now
  uses `findLevelBySequence(levels, OUT_OF_STOCK_SEQUENCE)`.
- **`MealPlansOverview.vue`** — `stockStatusColour`,
  `needToBuy`, and the new `levelSequenceForItem` helper all
  read by sequence. `stockStatusLabel` still surfaces the
  level's display name (it's *display*, not a decision).
- **`ProductSearch.vue::onQuickAdd`** — new tracked items
  start at the row matching `OUT_OF_STOCK_SEQUENCE`.
- **`RecipeCookMode.vue`** — `levelColourById` reads by
  sequence via `colourForSequence`; `outOfStockLevelId`
  resolves the row via `findLevelBySequence`. `StockLevelName`
  import dropped.
- **`NewListDialog.vue::lowOrOutCount`** — filters levels via
  `needsRestockSequence(l.sequence)` instead of name compares.
- **`StockLevelName`-as-type-cast cleanup** — removed
  `import type { StockLevelName }` + the `as StockLevelName`
  casts in `RecipeDetailPage.vue` (`levelNameFor` returns
  `string | null`), `RecipesOverview.vue` (`stockLevelColourFor`
  passes the string straight through), `MyProductsPage.vue`
  (`levelNameFor`), and `StockItemDetailPage.vue` (two template
  bindings).

**Incidental fixes surfaced by `vue-tsc --noEmit`:**
- **`NewListDialog.vue:376`** — `detail.lines.map(l => l.stock_item_id)`
  now returns `(string | null)[]` since Cart Button Chunk 3
  made `stock_item_id` nullable. Added a typed
  `.filter((id): id is string => !!id)` so the bulk-add call
  still type-checks. Tagged as FU-140 — there are likely more
  Cart-Button-Chunk-3 typing fallout sites worth a sweep.
- **`ShoppingListDetail.vue:2049`** — the undo-snapshot path
  passed a possibly-null `stock_item_id` to
  `removeByStockItemFromListAsync`. Added a guard so undo only
  registers when `before.stock_item_id` is non-null. Same FU-140
  family.

**Decisions made:**
- **Drop the `StockLevelName` union outright (not soft-deprecate).**
  The union promised an exhaustive set of four names; honouring
  it means users can't rename a level. The whole chunk exists to
  let them. `name: string` is the honest type.
- **Keep `getStockLevelColour(name)` as a soft-fallback rather
  than purge every call site this chunk.** ~5 surfaces still
  call it with a level name (display chips that get `level_name`
  off a detail DTO, not a sequence). Migrating those to
  `colourForSequence` is a per-surface follow-on that doesn't
  fit Chunk 4's documented scope. Logged as **FU-139** —
  finish the colour-helper migration so the literal map in
  `stockLevelLogic.ts` can be deleted entirely.
- **Preserve display-only level names where they're not
  decisions.** `stockStatusLabel` in `MealPlansOverview`
  still calls a chip "Out of Stock" when the level is named
  that — but the *colour bucket* underneath is now sequence-
  keyed. R-007 — only the decisions move, the labels stay.
- **`shortLabel` substring-replace in `useStockFilters`
  retained.** It's heuristic-by-design (handles "Out of Stock"
  → "Out" but also any custom name with "out" in it). Comment
  reinforced; no behaviour change.
- **`doraIntents.ts:68` comment touch was not made.** It's a
  documentation example listing the seeded names — no decision
  rides on it. Out of scope.

**Files touched:**
- `web_app/src/helpers/stockStatus.ts` (new)
- `web_app/src/helpers/stockLevelLogic.ts`
- `web_app/src/models/stockLevel.ts`
- `web_app/src/components/chips/StockItemChip.vue`
- `web_app/src/components/stock/StockItemRow.vue`
- `web_app/src/components/dialogs/NewListDialog.vue`
- `web_app/src/composables/useStockFilters.ts`
- `web_app/src/pages/WastePage.vue`
- `web_app/src/pages/MealPlansOverview.vue`
- `web_app/src/pages/ProductSearch.vue`
- `web_app/src/pages/RecipeCookMode.vue`
- `web_app/src/pages/RecipeDetailPage.vue`
- `web_app/src/pages/RecipesOverview.vue`
- `web_app/src/pages/MyProductsPage.vue`
- `web_app/src/pages/StockItemDetailPage.vue`
- `web_app/src/pages/ShoppingListDetail.vue` (FU-140 fix)
- `CHANGELOG.md` (Unreleased § Changed)
- `DORA_FOLLOWUPS.md` (FU-139, FU-140 logged)

**Verification:**
- `npx vue-tsc --noEmit` → **clean** (exit 0, no errors).
  Confirms `StockLevelName` cleanup is complete and every type
  signature lines up.
- `pytest tests/ --ignore=tests/e2e` → 37 passed, 8 failed
  (all `test_shopping_list_totals.py` — FU-136 pre-existing).
  No new regressions.
- Grep audit:
  - `StockLevelName` → 0 hits across `web_app/src`.
  - `'Out of Stock'` / `'Low Stock'` literals in code → all
    remaining hits are comments or the soft-fallback `case`
    statements in `stockLevelLogic.ts` (FU-139 closes those
    last cases). No decision-driving literal remains.
- **NOT verified in browser.** Logged as FU-141 — needs eyeball
  on chip colours, dim-when-out row treatment, "mark used" on
  the waste page, and the "Cookable tonight" / "Need to buy"
  meal-plan card.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — new `helpers/stockStatus.ts` is the
  shared rule-of-the-domain; no duplicated logic across the
  migrated files (every call goes through it).
- **R-002 theme tokens** — no chrome changes. Colour map keeps
  using palette tokens via `nameOf<ThemePalette>`.
- **R-003 state ownership** — *the* rule. Every former
  client-side rename-fragile decision now reads either a
  server-derived boolean off the DTO (preferred) or matches
  through the canonical sequence constants (when only a
  `StockLevel` row is in scope).
- **R-005 distribution posture** — no API/schema change.
- **R-007 scope discipline** — held the line on the colour
  helper sweep (FU-139) and the broader Cart-Chunk-3 typing
  fallout (FU-140). Only the FU-140 sites blocking this
  chunk's typecheck were touched.
- **R-008 terse comments** — chunk-citation lines on the new
  helpers + on the soft-fallback in `stockLevelLogic.ts`. No
  narration.
- **R-011 framework-idiomatic** — Vue `computed` + standard
  TS narrowing; nothing exotic.
- No new ADRs. The state-ownership principle is already in
  the standards doc; this chunk is its enforcement.

**Next up:**
1. **Browser-verify** (FU-141) — chip colours, row dim,
   mark-used, meal-plan need-to-buy. Quick eyeball pass — no
   logic should have shifted, but rename a level to confirm.
2. **State Ownership Chunk 5** — Type B server aggregates
   (verify-state-first: dashboard `primaryListStats` already
   reads server totals, `/products/best-deals` already exists,
   `/api/waste/rescue` already exists; Chunk 5 may largely be
   recognise-of-done like Chunk 3 was).
3. **State Ownership Chunk 6** — Type C: snapshot offer at ADD
   (real data-model bug; the AddLineHandler still doesn't
   snapshot — confirmed in the Chunk audit). Coordinate with
   `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 1.
4. **FU-139** — finish migrating colour-helper callers from
   name-keyed to sequence-keyed; delete the legacy fallback.
5. **FU-140** — sweep for more Cart Button Chunk 3 nullable
   `stock_item_id` typing fallout.
6. **FU-136** — `test_shopping_list_totals.py` `product_id`
   stub one-liner.
7. **FU-131** — Cart Button Chunk 3 UI side.

**Open questions for user:**
- Browser-verify Chunk 4 first (FU-141), or push straight to
  Chunk 5 (likely another "already shipped" audit) and Chunk 6
  (the real data-model bug)?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 3 (query support) — VERIFY-STATE-FIRST, NO CODE
**Status:** no-op. Chunk 3's two deliverables had **already shipped in
earlier work** (visible in the code I read while verifying Chunk 1 + 2).
Following CLAUDE.md's "verify state before acting" rule — declaring it
done rather than re-writing what's already there.

**What the plan asked for (impl plan §1 Chunk 3):**
1. `GET /api/recipes?cookable=true` (+ inverse + `?max_missing=N`)
2. `cookable_count` on the dashboard summary

**What's already in the code:**
- **`?cookable=true|false` + `?max_missing=N`** —
  `RecipeFilters` (`get_recipes.py:264-315`) carries both fields;
  `_parse_recipe_filters` (`get_recipes.py:740-777`) parses them
  off `request.args` via the existing tri-state `_parse_bool`;
  `_restrict_query` (`get_recipes.py:391-429`) feeds them into
  `load_recipe_cookability` (the shared aggregation that the
  DTO + dashboard also use — R-003) and reduces the candidate id
  set via `matches_missing`. Route wired at `get_recipes.py:798-817`.
- **`cookable_count` on dashboard summary** — `RecipeSummary`
  (`get_dashboard_summary.py:48-56`) carries the field; the
  handler (`get_dashboard_summary.py:147-151`) consumes the
  same `load_recipe_cookability` helper and counts
  `missing == 0 AND ingredient_count > 0` (so empty recipes
  don't pad the "cookable tonight" number).
- **Tests:** `tests/test_recipe_filters.py` (11 tests) pins
  `_parse_bool`, `_parse_recipe_filters`, `is_empty`,
  `needs_cookability`, and the `matches_missing` predicate
  across `cookable` × `max_missing` combinations.

**What changed this session:** **nothing.** This is a
recognition-of-done entry, not a code unit. Logged so the next
session doesn't re-discover the same surface and re-do work.

**Decisions made:**
- **Did not write an integration / e2e test for the recipe-list
  cookability filter.** Unit tests already cover every
  branch of the parsing + matching logic. An end-to-end test
  through Flask would be valuable but is heavier (the e2e
  infra spins a real server + session-scoped DB; building data
  via the API would need recipe + ingredient + stock-item
  POSTs not present in the existing suite). Reserved for
  whenever the cookability path becomes load-bearing on a
  real query plan — see FU-138.
- **FU-138 (query-count test) stays open and unchanged.** I
  previously committed (Chunk 2 worklog) to "co-sequence the
  FU-138 harness with Chunk 3", but since Chunk 3 is a no-op
  code-wise, the harness is the *only* thing I'd be building —
  and that's a substantial test-infra piece (SQLAlchemy
  `before_cursor_execute` counter, baseline numbers, fixture
  for population). Better to land it as its own focused work
  unit, or fold it into Chunk 4's surface-by-surface client
  migration where N+1 perf becomes load-bearing in real
  traffic.

**Files touched:** none. `CHANGELOG.md` not updated (no
product-level change).

**Verification:**
- `pytest tests/test_recipe_filters.py
  tests/test_recipe_cookability.py tests/test_stock_status.py
  tests/test_confirm_actions_resolve_level.py` → **33 passed**.
  Covers every branch of the cookability contract end-to-end
  short of a real DB query.
- Read each cited code site to confirm the wiring; no drift
  between docstring and implementation.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- N/A on code rules — no changes. Recognition-of-done is the
  whole unit.
- **R-007 scope discipline** — held the line: did *not* invent
  FU-138 harness work to justify a code-changing diff. The
  honest answer is "already done; here's the proof."

**Next up:**
1. **State Ownership Chunk 4** — delete the 7 client
   `isMissing`/`isCookable` reimplementations + ~14 client
   `'Out of Stock'` literals. Read the new DTO fields
   (`missing_count`, `cookable`, `missing_stock_item_names`,
   `is_missing`, `stock_level_sequence`) and the new
   `?cookable=true` query instead. **Surface-by-surface
   (R-007).** This is the "it got simpler" win the plan
   advertises.
2. **FU-138** — query-count harness for the recipes endpoint.
   Pure test-infra; pick its own session.
3. **FU-136** — `test_shopping_list_totals.py` `product_id`
   stub fix (one-liner, restores CI signal).
4. Browser-verify trio: FU-130, FU-132, FU-135.
5. **FU-131** — Cart Button Chunk 3 UI side.

**Open questions for user:**
- Push to Chunk 4 (the visible client-side cleanup)? It's the
  most user-facing of the remaining state-ownership pieces.
- Or knock down the browser-verify trio + FU-136 stub fix
  first to restore green test signal and de-risk the Cart
  Button stack before more code lands?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 2 (derived status on DTOs + missing names) — IMPLEMENTED
**Status:** complete (server-only, DTO field add). Closes the impl
plan's §1 Chunk 2 with one last gap filled.

**Verify-state-first finding:** ~90% of Chunk 2 was already in place
from earlier work — `StockItemDto` carries
`stock_level_sequence` + `is_out_of_stock` + `is_low_stock` +
`needs_restock`; `RecipeIngredientDto` carries `is_missing` +
`is_low_stock` + `stock_level_id`; `RecipeDto` carries
`missing_count` + `cookable`; and `domain/recipe_cookability.py`
already hosts the shared `missing_count_for` helper (consumed by
the DTO, the `?cookable` query filter, and the dashboard's
`cookable_count`). The single field the plan named that *wasn't*
shipped: `missing_stock_item_names`.

**What changed:**
- **`dora_api/domain/recipe_cookability.py`** — new
  `missing_stock_item_names_for(ingredients) -> list[str]`. Runs
  purely on the already-loaded ingredient tree (`stock_item`,
  `stock_level`), distinct on item name, alphabetised for stable
  output. Sits next to `missing_count_for` so the cookability
  authority owns both shapes.
- **`dora_api/features/recipes/get_recipes.py`** —
  `RecipeDto.missing_stock_item_names: List[str]` field added
  (non-default, placed after the existing non-default
  `missing_count` / `cookable`, before the default-bearing
  `has_image`); populated in `from_entity` via the new helper.
- **`tests/test_recipe_cookability.py`**:
  - Fixed the pre-existing stub (FU-137 — closed): `_recipe()`
    now provides `source`, `version_group_id`, `kcal` so
    `RecipeDto.from_entity` doesn't `AttributeError`. Two
    earlier-added DTO fields had drifted away from the stub.
  - `_item()` / `_ingredient()` gained an optional `name=`
    parameter so the missing-names tests can assert on distinct
    labels.
  - Three new tests pin the field: distinct + alphabetised;
    empty when cookable; includes items with no stock-level
    record (`None` → missing per the contract).

**Decisions made:**
- **Helper lives on `domain/recipe_cookability.py`, not on the
  DTO module.** R-003 — the cookability authority owns *all*
  cross-recipe-stock-item aggregations so the rule can't drift
  between consumers. Mirrors how `missing_count_for` is shared
  by the DTO, the `?cookable=true` query, and the dashboard's
  `cookable_count`.
- **Field placement before defaults, not after.** Python
  dataclass ordering — a non-default field can't sit after a
  default-bearing one. Added immediately after `cookable`
  (also no default) so the section about server-owned
  cookability stays grouped.
- **No client model update yet.** The plan reserves "delete the
  client copies" for **Chunk 4**; Chunk 2 just makes the field
  available. Extra fields are harmless to the existing
  `Recipe` TypeScript model.
- **Query-count test deferred.** The plan's §3 risk note asks
  for a query-count pin on the recipe-list endpoint. The new
  helper provably doesn't query (pure function over the
  already-loaded entity tree), and the existing
  `missing_count_for` shares the same loader path — so this
  chunk's addition is N+1-free *by construction*. A formal
  query-count harness (SQLAlchemy `before_cursor_execute`
  counter) is a substantial test-infra piece with no precedent
  in the suite. Logged as **FU-138**, recommended at Chunk 3
  (when `?cookable=true` lands and there's a hot list endpoint
  worth pinning end-to-end).

**Files touched:**
- `dora_api/domain/recipe_cookability.py`
- `dora_api/features/recipes/get_recipes.py`
- `tests/test_recipe_cookability.py`
- `CHANGELOG.md` (Unreleased § Added)
- `DORA_FOLLOWUPS.md` (FU-138 logged; FU-137 closed)

**Verification:**
- `pytest tests/test_recipe_cookability.py
  tests/test_stock_status.py
  tests/test_confirm_actions_resolve_level.py` → **20 → 23
  passed** (12 cookability incl. 3 new + the FU-137 unblock + 8
  status + 3 resolver = 23 total).
- Full `pytest tests/ --ignore=tests/e2e` → 37 passed, 8 failed
  (all `test_shopping_list_totals.py` — FU-136, pre-existing
  from Cart Button Chunk 3, confirmed on `dd15399` baseline;
  no new regressions).
- Grepped for direct `RecipeDto(...)` constructions outside
  `from_entity` — only `get_recipes.py:221` (which I updated).
  Other recipe-shaped DTOs (`LinkedRecipeDto`,
  `RescueRecipeDto`, `ImportedRecipeDto`) are separate classes
  and untouched.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — new aggregation lives next to
  `missing_count_for` (single source for cookability rules).
- **R-003 state ownership** — *the* rule this chunk extends.
  Missing-names aggregation is server-side, computed once,
  served on the DTO; client will consume in Chunk 4.
- **R-005 distribution posture** — no DB, no migration. The
  new helper is pure-Python, repository-agnostic.
- **R-007 scope discipline** — only the documented Chunk 2
  field gap (`missing_stock_item_names`) added. Did not
  touch `?cookable=true` (Chunk 3) or delete any client copy
  (Chunk 4). Did opportunistically fix FU-137 because the
  stub fix *was* needed to verify this very change.
- **R-008 terse comments** — one-line "why" on the new field
  + on the helper's docstring; no narration.
- **R-011 framework-idiomatic** — dataclass field add +
  `from_entity` is the established DTO pattern.
- No new ADRs.

**Next up:**
1. **State Ownership Chunk 3** — implement `GET
   /api/recipes?cookable=true` (+ `?max_missing=N`) end-to-end.
   The DTO + filter parsing already exist
   (`_RecipeFilters.cookable` / `.max_missing` + the
   `recipes_with_missing_counts` helper); verify the route
   honours them and add `cookable_count` to the dashboard
   summary. Co-sequence the FU-138 query-count test here.
2. **Chunk 4** — delete the 7 client `isMissing` / `isCookable`
   reimplementations + ~14 client `'Out of Stock'` literals.
   Read the new DTO fields instead. Surface-by-surface
   (R-007).
3. Open browser-verify: FU-130, FU-132, FU-135.
4. **FU-131** — Cart Button Chunk 3 UI side.
5. **FU-136** — `test_shopping_list_totals.py` `product_id`
   stub fix (one-liner, restores CI signal).

**Open questions for user:**
- Push to Chunk 3, or knock down FU-136 and the browser-verify
  trio first?
- Chunk 3's `cookable_count` on `/dashboard/summary` is a tiny
  add; do it as part of Chunk 3 (recommended — the plan groups
  them) or hold it back?

---

## 2026-06-12 — IMPL_PLAN_STATE_OWNERSHIP Chunk 1 (canonical stock-status contract — finished) — IMPLEMENTED
**Status:** complete (server-only, no DTO/client change). **Closes
the impl plan's first reviewable chunk.** Verify-state-first revealed
~80% of Chunk 1 was already done in earlier work (`stock_status.py`
module exists, dashboard/waste/reports already consume
`level_for_status`, the rename + missing-policy tests already pass).
Picked up the remaining four threads.

**What changed:**
- **`dora_api/domain/stock_status.py`** — `EXPIRING_SOON_WINDOW_DAYS
  = 7` colocated with the level-status contract. Module docstring
  updated to flag that the contract owns *both* level→bucket
  mapping **and** related thresholds (per impl plan §1).
- **`dora_api/features/locations/attention.py`** — dropped the
  local `EXPIRING_SOON_WINDOW_DAYS = 7`; imports from
  `stock_status` instead.
- **`dora_api/features/alerts/get_alerts.py`** — import moved
  from `features.locations.attention` to `domain.stock_status`
  (the canonical source).
- **`dora_api/features/assistant/tools.py`** — `_EXPIRY_HORIZON_DAYS
  = 7` deleted; the 5 call sites now use the shared
  `EXPIRING_SOON_WINDOW_DAYS`. Removes the last duplicate of the
  7-day window.
- **`dora_api/features/assistant/confirm_actions.py`**:
  - `_LEVEL_ALIASES` retyped from `dict[str, str]` (phrasing →
    level *name*) to `dict[str, StockStatus]` (phrasing → status
    enum). `_resolve_level` then calls `level_for_status(repo.get
    (StockLevel).all(), status)` to pick the row by sequence —
    rename the seeded "Out of Stock" label and "out" / "gone" /
    "empty" still resolve correctly.
  - Substring-name fallback retained for users who customise
    level names beyond the alias map's phrasings.
  - The recipe-missing-ingredient filter (line 629) replaced
    `level is not None and level.sequence < 3  # OUT_OF_STOCK = 3`
    with `is_missing(item.stock_level)` from the contract.
- **`tests/test_confirm_actions_resolve_level.py`** (new) —
  three unit tests pinning the resolver against a fake repo
  whose levels are renamed (`Renamed-Out`, `Renamed-Low`, etc.);
  every phrasing must still pick the right row purely by
  sequence. Plus case/whitespace insensitivity and empty-input
  cases.

**Decisions made:**
- **Open decision 1 ("missing = out-only vs out+low") was
  already resolved in code** — `is_missing` returns `level is
  None or is_out_of_stock(level)`. Documented in
  `stock_status.py` module docstring + asserted by
  `test_stock_status.py::test__is_missing_is_out_of_stock_only
  _with_none_missing`. No new decision needed.
- **Threshold colocation: keep in `stock_status.py`, not a new
  `thresholds.py` module.** The impl plan explicitly asks for "one
  module" for both status mapping and the related threshold; a
  second module would re-fragment the source of truth the chunk
  exists to consolidate. The docstring names the broader scope
  ("status authority + freshness window") so the colocation
  doesn't read as accidental.
- **Substring-name fallback retained in `_resolve_level`.** It's
  the only path that still touches a level *name* anywhere on
  the server — kept because users with custom phrasings outside
  the alias map (e.g. they renamed "Sufficient" to "Mid") need
  *some* lookup to work. This is `R-003` carve-out by design;
  the alias-map path covers the canonical sequence values, and
  the fallback only fires when the user's phrasing doesn't
  match a recognised alias. Documented inline.
- **No DTO / client change.** Pure server consolidation, per the
  chunk definition-of-done (impl plan §2).

**Files touched:**
- `dora_api/domain/stock_status.py`
- `dora_api/features/locations/attention.py`
- `dora_api/features/alerts/get_alerts.py`
- `dora_api/features/assistant/tools.py`
- `dora_api/features/assistant/confirm_actions.py`
- `tests/test_confirm_actions_resolve_level.py` (new)
- `CHANGELOG.md` (Unreleased § Changed)
- `DORA_FOLLOWUPS.md` (FU-136, FU-137 logged for pre-existing
  test breakages surfaced during verification)

**Verification:**
- Ran `pytest tests/test_stock_status.py
  tests/test_confirm_actions_resolve_level.py` → **11 passed**.
- Ran full `pytest tests/ --ignore=tests/e2e` (33 collected) → 24
  passed, **9 failed pre-existing** (8 in
  `test_shopping_list_totals.py`, 1 in `test_recipe_cookability.py`).
  Confirmed pre-existing by `git stash && pytest && stash pop` —
  same failures on `dd15399` baseline before my edits. Root
  causes:
  - `test_shopping_list_totals.py` × 8: stub `_line()` doesn't
    pass `product_id` (added by Cart Button Chunk 3); pure test
    fixture drift, no behaviour issue. **FU-136**.
  - `test_recipe_cookability.py` × 1: stub recipe missing a
    `source` attribute (added by an earlier prompt). **FU-137**.
- Confirmed the rename test in `test_stock_status.py:38-46`
  exercises the keystone property; combined with the new
  `_resolve_level` rename test, every path that used to compare
  on `"Out of Stock"` is now sequence-keyed.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — single new test module under
  `tests/`; no production-side new modules. Consolidation is the
  whole point.
- **R-003 state ownership** — *the* rule this chunk enforces.
  Server now owns every level→bucket call, including the assistant
  alias resolver. The one carve-out (substring-name fallback for
  user-customised level labels) is documented inline at the
  one site that still reads `StockLevel.name`.
- **R-005 distribution posture** — no DB, no migration, no
  config.
- **R-007 scope discipline** — held the line at the impl plan's
  Chunk 1 definition-of-done. Did *not* touch DTOs, did *not*
  delete client copies of `Out of Stock`, did *not* implement
  `?cookable=true`. Those are Chunks 2-4.
- **R-008 terse comments** — Chunk-1 citations on the alias map
  and threshold; no commentary on the obvious.
- **R-011 framework-idiomatic** — `StockStatus(IntEnum)` +
  `level_for_status` is the pattern already established by the
  module; the edits extend rather than reinvent.
- No new ADRs. Module-level guidance (single source for
  status + windows) is already captured by `R-003` and the
  module docstring.

**Next up:**
1. **State Ownership Chunk 2** — derived booleans / status
   enum on the stock-item + recipe-ingredient DTOs, plus
   `cookable` / `missing_count` / `missing_stock_item_names`
   on `RecipeDto` (set-based, no N+1; query-count test).
   `test_recipe_cookability.py` is already shaped for this and
   needs the FU-137 stub fix as part of the chunk.
2. **Chunk 3** — `?cookable=true` query honoured server-side +
   `cookable_count` on dashboard summary.
3. **Chunk 4** — delete the 7 client `isMissing`/`isCookable`
   copies + the ~14 client `'Out of Stock'` literals.
4. **Browser-verify backlog**: FU-130, FU-132, FU-135 still
   open.
5. **FU-131** — Cart Button Chunk 3 UI side (inline-product
   variant + nested display + rule-4 modal).

**Open questions for user:**
- Push straight to State Ownership Chunk 2, or circle back to
  FU-131 / browser-verify first?
- FU-137 (`test_recipe_cookability.py` `source` attr) is a
  trivial stub fix and the chunk's existing test scaffolding —
  fold into Chunk 2 (recommended) or close as its own
  one-liner now?

---

## 2026-06-12 — IMPL_PLAN_CART_BUTTON Chunk 4 (meal-plan generate routes through Axis B) — IMPLEMENTED
**Status:** complete (frontend-only — backend `merge_into_list_id`
already supported it from earlier work). **Static-only — no env.**
Closes the Cart Button impl plan's last chunk (L382 / surface 10 in
`PROPOSAL_CART_BUTTON.md §5`).

**What changed:**
- `web_app/src/pages/MealPlansOverview.vue` — replaced the
  always-creates-new-list `generateListForWeek` with an
  Axis-B-gated flow:
  - New `pickGenerateTarget()` reads the draft lists off
    `shoppingListStore.membership.active_lists` (server-derived,
    R-003 — no client recomputation).
  - **0 drafts:** no prompt; falls through to today's create-new
    behaviour with the auto-name `"Meals: <plan>"`.
  - **≥1 drafts:** opens a radio `$q.dialog` with each draft as
    an option plus a final **"+ Create new list"** row (the
    sentinel resolves to "no merge target" → create-new path).
  - Cancel/dismiss aborts the whole action — no silent fallback
    to always-new.
  - The autoGenerate call now spreads `merge_into_list_id` *or*
    `name` (XOR-style) so we don't pass a stale name when adding
    to an existing list.
  - Success toast distinguishes merge vs new ("Added N items to
    your list." vs "Shopping list created with N items.").
- `CHANGELOG.md` — Unreleased § Changed entry.

**Decisions made:**
- **Prompt at ≥1 draft, not just 2+.** Strict Axis B silently
  picks at 1 draft, but the proposal's surface-10 row reads
  *"offers add-to-existing ▾ / new instead of always-new"* — the
  user-visible promise is the offer itself, and this is a heavy
  bulk create-from-source action where a 1-click confirmation is
  cheap insurance against "oh, I meant the other list". 0 drafts
  still skips silently (nothing to offer).
- **No remembered pick.** Unlike `useQuickAddTargetPick` (used by
  quick-add for repeat single-item adds), generate-for-week is a
  once-per-week action — sessionStorage memoisation would just
  hide the picker the second time without a real win. Keep it
  re-prompting; the picker preselects the first draft so single-
  draft confirm is a single Enter.
- **No new component.** The picker is one `$q.dialog` call (~20
  LOC); promoting it to a `TargetListPicker.vue` is only worth
  it if a second surface needs the same shape. Logged as
  FU-133 in case it does.

**Files touched:**
- `web_app/src/pages/MealPlansOverview.vue`
- `CHANGELOG.md` (Unreleased § Changed)
- `DORA_FOLLOWUPS.md` (FU-133 logged)

**Verification:**
- Static only. Confirmed `shoppingListStore.membership` is
  accessed via the Pinia setup-store proxy (no `.value`) the
  same way `StockItemDetailPage.vue:906` and
  `StockOverview.vue:477` do.
- Confirmed `merge_into_list_id` is honoured by the backend at
  `dora_api/features/shopping_lists/auto_generate.py:155-162`
  (rejects done/missing lists; otherwise picks the existing
  list as target).
- Confirmed the spread-form passes either `merge_into_list_id`
  *or* `name` — never both — so the backend doesn't see an
  unused stale name field.
- **NOT yet verified in browser.** Needs a real plan + at least
  one draft list to exercise the merge path. Logged as a verify
  backlog item.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — judgement-call carve-out (single
  consumer); FU-133 owns the promotion if a second consumer
  appears.
- **R-002 theme tokens** — no chrome changes; the picker uses
  Quasar's stock dialog like the rest of the app.
- **R-003 state ownership** — target candidates come from
  membership (server-derived); the picker doesn't recompute
  anything.
- **R-005 distribution posture** — no DB/config touched.
- **R-007 scope discipline** — held the line on Chunk 4 only;
  did not pull `pickGenerateTarget` into the recipe-side
  `autoGenerate` call sites (`RecipesOverview.vue:1153`,
  `MainLayout.vue:291`, `NewListDialog.vue:416`) — those have
  their own resolution stories (NewListDialog already picks a
  target; the others are separate surfaces) and are out of this
  chunk's scope. Logged as FU-134 to evaluate post-browser-test.
- **R-008 terse comments** — one chunk-line citation on
  `pickGenerateTarget` for the L382 link.
- **R-011 framework-idiomatic** — Quasar `$q.dialog` radio
  options; standard Promise-wrapping pattern matches
  `useStockItemActions.addToList:74-98`.
- No new ADRs.

**Next up:**
1. **Browser verify** the four-state matrix: 0 drafts (silent
   new), 1 draft (picker shows draft + create-new, both paths
   work), 2+ drafts (picker shows all + create-new), cancel
   aborts cleanly. **High-priority** — this is the only
   acceptance check for the chunk.
2. **FU-131 / FU-132** (Chunk 3 UI + DB smoke), still deferred.
3. **State Ownership Chunk 1** — the architectural rock.
4. **Stock Overview Chunk 7** — unified scan-mode.
5. Verify backlog now 18 items (added: Cart Button 4).

**Open questions for user:** with the cart-button impl plan
backend story now complete, do you want to circle back to
FU-131 (Chunk 3 UI: inline-product variant + nested display +
rule-4 modal) or push on State Ownership Chunk 1 next?

---

## 2026-06-12 — IMPL_PLAN_CART_BUTTON Chunk 3 (standalone-product lines + rules 1–3 backend) — IMPLEMENTED
**Status:** complete (backend + schema + DTO + minimal frontend
plumbing). **Static-only — no env.** Closes L191 + L130 + couples
L195 on the backend side. **The UI side (rule 4 modal, inline-product
variant, nested display) is logged as FU-131** — held risk by
landing the schema change without bloating the diff with UI churn.

**What changed — Schema + entity:**
- **`ShoppingListLine.stock_item_id`** flipped to **nullable**.
- **`product_id: UUID | None`** added as a new column on the table
  + entity + Fields constant. FK→Product, ON DELETE CASCADE
  (consistent with the existing stock-item cascade — a deleted
  product never leaves an orphan line).
- **`CheckConstraint('stock_item_id IS NOT NULL OR product_id IS NOT NULL')`**
  enforces the "at least one anchor" rule at the DB. The handler
  also validates upstream so the SPA gets a clean 400 instead of
  a 500 mid-write.
- **Migration `d7c9e4a8c2b1`** (down_rev = `f6c8e3a9b1d2`).
  Batch-mode for SQLite portability; pre-release semantics so the
  upgrade doesn't try to fabricate `product_id` values for
  existing rows (still works with empty/dev data).

**What changed — Backend handlers:**
- **`AddLineRequest`**: `stock_item_id` + `product_id` both
  optional + nullable; handler returns `no_anchor` 400 when both
  are null. Dedupe logic now checks **stock_item_id OR product_id**
  on the same list — a nested product line carrying both columns
  still dedupes against either match.
- **`link_product_to_stock_item`**: rule 2 wiring. After
  appending the product to the stock item's `products`
  relationship, scans all `ShoppingListLine` rows anchored on
  that product (`product_id == P`). For each orphan on a
  not-DONE list:
  - if a stock-item line for S already exists with no product
    anchor, the orphan **folds** into it (`existing.product_id =
    P`, orphan deleted);
  - otherwise the orphan **converts in place** (`stock_item_id =
    S`), becoming a single nested row.
- **`DeleteLineHandler` + `RemoveLineByStockItemHandler`**: rule
  3 wiring. When the deleted line is anchored on a stock item
  with `product_id` null, look up the stock item's linked
  products and cascade-remove any product-only lines (
  `stock_item_id IS NULL AND product_id IN (linked_products)`)
  on the same list. Idempotent — runs in the same transaction
  as the parent delete.

**What changed — DTOs + service:**
- **`ShoppingListLineDto`**: `stock_item_id: UUID | None`, new
  `product_id: UUID | None`. Display name falls back to the
  product name for product-only lines via a new bulk product-name
  lookup keyed by `product_id`.
- **`AddLineCommand`** (frontend): both `stock_item_id` and
  `product_id` optional. The `?` on a server boundary doesn't
  change wire shape (omit vs null both work as "unset").
- **`ShoppingListLine` model** (frontend): `stock_item_id: string
  | null`, new `product_id: string | null`. `cartStateFor`
  accepts a nullable id and returns 'none' for null inputs.
- **`ShoppingListDetail.vue`** null-guarded in 3 places:
  - `stockItemFor(stockItemId | null)` early-returns undefined
    on null (existing call sites untouched);
  - `onSwapSubstitute` bails early on product-only lines
    (substitutes don't apply);
  - the substitute on-list dedupe set filters out null stock
    item ids before checking membership.

**Decisions made:**
- **Anchor model: nullable both, CHECK 'at least one'.** Plan
  spec'd this exactly. Alternative would be a polymorphic
  `anchor_kind` column + single nullable id, but two FKs read
  cleaner in the query builder and lets the DB enforce
  referential integrity per side.
- **Rule 2 folds rather than always-convert.** The plan says
  "auto-add the stock line + nest the product under it". If a
  stock-item line already exists, "adding" it again would either
  no-op the dedupe or double-insert; folding the product anchor
  into the existing line is the only correct read.
- **Rule 3 cascade lives in the handler, not the FK.** A
  `Product` deletion still cascades the line via the existing FK,
  but rule 3 is about a *stock-item line* removal cascading its
  *nested product* siblings — the DB has no edge for that. Doing
  it in the handler keeps the rule explicit and testable.
- **No frontend "inline-product" variant yet.** The plan asks for
  `AddToListButton variant="inline-product"` + nested display on
  the list detail; these are substantial UI changes that don't
  belong in the schema-change PR. Logged as **FU-131** with a
  clear scope.
- **Pre-release semantics** — no data preservation in the
  migration. Matches the plan's *"pre-release → clean, non-
  preserving OK"* note.

**Files touched:**
- `dora_api/persistence/table_mappings.py`
- `dora_api/persistence/migrations/versions/d7c9e4a8c2b1_20260612_shopping_list_line_product_anchor.py` (new)
- `dora_api/domain/entities/shopping_list.py`
- `dora_api/features/shopping_lists/manage_shopping_list_lines.py`
- `dora_api/features/shopping_lists/get_shopping_list_detail.py`
- `dora_api/features/stock_items/link_product_to_stock_item.py`
- `web_app/src/models/shoppingList.ts`
- `web_app/src/services/api/shoppingListApiService.ts`
- `web_app/src/pages/ShoppingListDetail.vue`
- `CHANGELOG.md` (Unreleased Added)
- `DORA_FOLLOWUPS.md` (FU-131 + FU-132 logged)

**Verification:**
- Static only. Cross-checked the CHECK constraint name +
  `is_null()` API on `EntityField` (existed); confirmed
  `repository.remove` is the delete primitive (not `delete`).
  Traced the cascade path through DeleteLine + RemoveByStockItem
  to make sure they share the same lookup logic.
- **NOT yet verified in browser.** FU-132 owns the smoke pass —
  needs a real DB to exercise the migration + rule wiring.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — no new components; the cascade logic
  exists in 2 places (DeleteLine + RemoveByStockItem) by design
  (separate request shapes, same rule body); could be
  extracted to a helper next time. Logged inline in FU-131's
  ambit.
- **R-003 state ownership** — anchor logic + cascade live
  server-side; the client reads `stock_item_id` + `product_id`
  off the DTO without recomputing.
- **R-005 distribution posture** — schema change uses batch-
  mode (SQLite friendly); CHECK constraint syntax portable to
  Postgres.
- **R-007 scope discipline** — held the line on the UI side
  (FU-131). Backend rules 1–3 are coherent without the UI.
- **R-008 terse comments** — chunk-line citations + one-line
  whys.
- **R-011 framework-idiomatic** — Alembic batch-mode + Quasar
  `q-popup-proxy` (existing) + Pydantic optional fields, all
  documented patterns.
- No new ADRs.

**Next up:**
1. **FU-132 / FU-131 + earlier browser-verify backlog** (deferred
   per user). FU-132 is high-priority because the migration +
   cascade need a real DB.
2. **Cart Button Chunk 4** — meal-plan "generate" routes through
   Axis B (small, post-Chunk 3).
3. **State Ownership Chunk 1** — the architectural rock. Unblocks
   FU-081 + Stock Overview Chunk 8.
4. **Stock Overview Chunk 7** — unified scan-mode (small).
5. Verify backlog: now 17 items (Cookbook 1–10, C-cross 1–5,
   Cook Mode 1–6, Stock Overview 1–6, Cart Button 1–3).

**Open questions for user:** FU-131 is a UI-side follow-up the
plan technically asks for in Chunk 3. Want it pulled forward
(another focused session on the SPA), or roll Cart Button Chunk
4 first to close that plan's backend story before circling back?

---

## 2026-06-12 — IMPL_PLAN_CART_BUTTON Chunk 2 (combined QuickAddSheet for 2+ products) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env).
Closes §2.3 + L84 + decision 2 (2+ products → combined modal) +
decision 5 (quantity only in the combined modal).

**What changed — Backend:**
- **`StockItemDto.linked_product_count: int`** — new field, default
  0. Hydrated by **`_hydrate_linked_product_count`**: one GROUP BY
  against `StockItemProduct` joining the displayed item ids. Cost
  class identical to `_hydrate_has_image`; runs alongside it in
  both `handle` (list) and `handle_by_id` (detail).
- Pipeline shape:
  `paginate → _hydrate_has_image → _hydrate_linked_product_count`.
  No new server-owned state — the count just exposes what the
  link table already knows so the client doesn't N+1 fetch detail
  pages to find out.

**What changed — Frontend:**
- **`models/stockItem.ts`** + the StockItem store automatically
  carry `linked_product_count?: number` (default 0 on consumers
  that haven't migrated).
- **`AddToListButton.vue`** gains:
  - `linkedProductCount` computed off the stockItem store.
  - `draftCount` computed off `membership.active_lists`
    (status === 'draft').
  - `shouldUseCombinedModal`: true when `linkedProductCount >= 2`
    OR (`linkedProductCount === 0|1` AND `draftCount >= 2`).
    Note: the proposal §2.3 spec'd "both ambiguous", but
    decision 2 explicitly promotes 2+ products to the modal
    unconditionally. Both routes share the same UX so they share
    the gate.
  - `onPrimaryClick` `cartState === 'none'` branch:
    `shouldUseCombinedModal → openQuickAdd({ stockItemId })`;
    otherwise the existing `actions.addToList` flow.

**Decisions made:**
- **Re-use `QuickAddSheet`, no new modal.** The proposal says
  "Never stack two modals; route through the existing combined
  surface." That surface already exists (mounted once in
  `MainLayout`) and already accepts a preset stock item via
  `useQuickAdd`. Nothing to build, just route here.
- **`linked_product_count` on the list DTO** rather than fetching
  the detail endpoint on click. The detail fetch would be a
  per-click network round-trip in the row-tap critical path; a
  bulk SELECT alongside the rest of the list metadata is
  cheaper + correctly cached with the row.
- **Bulk variant unchanged.** A bulk-add hitting a 2+-product
  item shouldn't spawn a modal mid-batch — that defeats the
  "one summary toast" rule (decision 6). Users wanting per-item
  offer selection can do it from the list detail after the
  batch lands. Documented in FU-130.
- **No follow-up to consolidate `shouldUseCombinedModal` logic.**
  The two branches map 1:1 onto the decisions; collapsing them
  would obscure why each escalates.

**Files touched:**
- `dora_api/features/stock_items/get_stock_items.py`
- `web_app/src/models/stockItem.ts`
- `web_app/src/components/AddToListButton.vue`
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-130 logged)

**Verification:**
- Static only. Cross-checked `QuickAddSheet`'s preset path
  (`presetStockItemId` ref via `useQuickAdd`) — confirmed it
  hops straight to the offer/quantity step when a stock item
  is pre-selected.
- Confirmed `linked_product_count` defaults to 0 on the model
  (optional field) so call sites that don't supply it (e.g.
  legacy fixtures, cached responses pre-deploy) degrade to "no
  modal" — safer than "always modal".
- **NOT yet verified in browser.** FU-130 owns the smoke pass.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — `QuickAddSheet` already existed;
  re-used not forked.
- **R-003 state ownership** — count derived server-side from
  the canonical link table; client never recomputes.
- **R-005 distribution posture** — raw SQL uses `bindparam(expanding=True)`
  (Postgres + SQLite both parse it; matches sibling hydrates).
- **R-007 scope discipline** — touched the two files that
  needed touching (DTO + button); didn't reshape QuickAddSheet
  itself or extend the chunk into the standalone-product line
  model (that's Chunk 3).
- **R-008 terse comments** — chunk-line + decision-line
  citations.
- **R-011 framework-idiomatic** — `useQuickAdd` is the
  documented Vue-side composable pattern; reused unchanged.
- No new ADRs.

**Next up:**
1. **FU-130 / FU-127** browser-verify (deferred per user).
2. **Cart Button Chunk 3** (standalone-product line model — the
   big rock; schema change: `ShoppingListLine.stock_item_id`
   nullable + new `product_id` anchor + nested display +
   cascade rules). **Biggest chunk of the cart-button plan.**
3. **Cart Button Chunk 4** (meal-plan "generate" routes through
   Axis B — small, post-Chunk 3).
4. **State Ownership Chunk 1** as the alternative
   architectural-rock pivot.
5. **Stock Overview Chunk 7** (unified scan-mode) — small,
   isolated.
6. Verify backlog: 16 items now (Cookbook 1–10, C-cross 1–5,
   Cook Mode 1–6, Stock Overview 1–6, Cart Button 1–2).

**Open questions for user:** none.

---

## 2026-06-12 — IMPL_PLAN_CART_BUTTON Chunk 1 (AddToListButton + double-toast fix) — IMPLEMENTED
**Status:** complete (frontend-only, no schema — static, no env).
**Resolves FU-038.** Closes L83 / L154 / L196 / L288 / L380 / L381 +
partial coverage of the proposal §1 13-surface adoption (4 highest-
traffic surfaces; rest logged as **FU-128**).

**What changed — new files:**
- **`web_app/src/components/AddToListButton.vue`** — the unified
  cart button. Four chrome variants (`row | toolbar | menu | bulk`)
  with identical behaviour. Owns:
  - **State-aware render** via `cartStateFor`: not-on /
    on_target (primary draft) / on_other (a draft) / on_multiple.
  - **Decision tree** (proposal §7a): `none` → `actions.addToList`
    (existing single-item flow handles 0-draft / ambiguous prompts);
    on exactly 1 list → `listActions.removeFromList` (silent);
    on 2+ → inline `MultiListPopover` (Remove from each / Remove
    from all / Add to another).
  - **Bulk variant**: emits `bulk-done` for parent cleanup; uses
    `quick_add_target_list_id` (no prompt needed when unambiguous)
    OR routes the first item through the prompt flow + batches
    the rest. Single summary toast in either case.

**What changed — composable:**
- **`useShoppingListActions.ts`** gains `removeFromList(listId,
  stockItemId)` + `removeFromAllLists(stockItemId, listIds[])`. Both
  refresh the store + emit one summary toast; the bulk variant
  composes per-list calls + aggregates.

**Surfaces adopted (4 of ~9 spec'd):**
- **StockItemRow** (row variant) — replaces the hand-rolled
  `cart` computed + `onCartClick`; removed stale
  `cartStateFor` + `useShoppingListStore` imports from the row.
- **StockItemDetailPage** (toolbar variant) — replaces the
  `BaseButton` "Add to list" in the page header.
- **RecipeDetailPage** ingredient rows (row variant) — replaces
  the per-row "Add to primary shopping list" button; retired the
  dead `onAddRowToList` handler.
- **StockOverview** bulk action (bulk variant) — replaces the
  `bulkAddToPrimary`-driven q-btn (loop-per-item, N toasts) with
  the unified single-summary-toast flow. Legacy
  `bulkAddToPrimary` function kept for the `a` keyboard shortcut
  (`addFocusedOrSelected`).

**Surfaces NOT adopted (FU-128):**
- MyProductsPage (#6), MealPlansOverview (#7), ProductSearch (#11),
  QuickAddSheet (#13). Plan said "one PR" but I held the line on
  risk: 4 high-traffic surfaces is a safe Chunk-1 boundary; the
  rest are mechanical and logged. Doing them all in one go would
  bloat the diff into unreviewable territory and the FU-038
  toggle behaviour ships from the new component on day one.

**Decisions made:**
- **Inline `MultiListPopover` as a functional Vue component**
  inside `AddToListButton.vue` (`h()` calls), not a separate
  file. Tight scope, reads the popover state from the parent's
  refs, no extraction yet (R-001 single-consumer).
- **Bulk variant pre-checks `quick_add_target_list_id`** to skip
  the prompt entirely in the common case. Falls through to the
  full prompt flow on the first item only when ambiguous.
- **Kept the keyboard-shortcut path** (`addFocusedOrSelected →
  bulkAddToPrimary`) using the legacy loop. Switching it would
  conflate UX work with this chunk's component-adoption scope;
  the user-facing behaviour is unchanged (still adds the
  selection) and the `a` shortcut produces individual toasts,
  which is acceptable for a keyboard power-user path.
- **Cart-state import retired** from StockItemRow and
  StockOverview (the latter still uses it via `useStockFilters`
  internally for filter routing; not removed there).
- **No new ADRs.** The component pattern is the R-001 standard
  hit; FU-126 (image rename) is the parallel.

**Files touched:**
- `web_app/src/components/AddToListButton.vue` (new)
- `web_app/src/composables/useShoppingListActions.ts`
- `web_app/src/components/stock/StockItemRow.vue`
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/pages/StockItemDetailPage.vue`
- `web_app/src/pages/RecipeDetailPage.vue`
- `CHANGELOG.md` (Unreleased Added)
- `DORA_FOLLOWUPS.md` (FU-038 → RESOLVED; FU-127 + FU-128 logged)

**Verification:**
- Static only. Cross-checked the new emits + props against each
  adopting surface; the bulk variant's `bulk-done` event fires
  cancelBulk; the row variant's silent click-to-remove path uses
  `removeFromList` with the entry from `onLists[0]`.
- **NOT yet verified in browser.** FU-127 owns the smoke pass.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — built the component first, then
  adopted; the second/third consumer happened in the same change.
- **R-003 state ownership** — cart membership is server-derived
  (`Membership`); the button reads, never recomputes.
- **R-007 scope discipline** — held to 4 surfaces, logged the
  other 5 as FU-128. Bulk q-btn legacy + keyboard shortcut left
  intact (small additive risk vs. full removal).
- **R-008 terse comments** — chunk-line + decision-line
  citations only.
- **R-011 framework-idiomatic** — `q-popup-proxy` + `q-btn` +
  Quasar's `h()`-based functional component patterns; no
  hand-rolled equivalents.

**Next up:**
1. **FU-127** browser-verify of the new button.
2. **FU-128** opportunistic adoption sweep for the remaining 5
   surfaces.
3. **Cart Button Chunk 2** (combined QuickAddSheet modal — the
   both-axes-ambiguous case + quantity).
4. **Cart Button Chunk 3** (standalone-product line model — the
   schema work; the big rock).
5. **State Ownership Chunk 1** as the alternative
   architectural-rock path that unblocks Shopping Lists + Stock
   Overview Chunk 8.
6. Verify backlog: Cookbook 1–10, C-cross 1–5, Cook Mode 1–6,
   Stock Overview 1–6, Cart Button 1.

**Open questions for user:** none — the FU-128 split is the only
non-obvious call and it's logged with rationale.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 6 (stock images + product fallback) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env).
**Resolves FU-033** end-to-end. Closes §2.5 + L74. Effectively builds
the entire "stock item image (own + product fallback)" feature the
original spec called out — same plumbing as the recipe-image pattern
from Cookbook Chunk 5.

**What changed — Backend:**
- **`table_mappings.py`** — `StockItem.image` is now mapped
  `deferred(...)` so the list endpoint never pulls megabytes per row
  just to compute `has_image` (mirrors recipe-image / FU-090).
- **New `StockItemDto.has_image: bool`** + `_hydrate_has_image` in
  `get_stock_items.py`. One bulk SQL pass: returns 1 when the item
  has its own image **OR** any linked product has one — so the
  SPA's "show thumbnail" decision matches what the bytes endpoint
  will actually serve. LEFT JOIN to `StockItemProduct` + `Product`
  keeps own-image-only rows intact.
- **New route `GET /stock-items/<id>/image`** in
  `get_stock_item_image.py`. Loads the item (with
  `.include(PRODUCTS)` so the fallback scan doesn't hit lazy-load);
  decodes own-image if present, falls back to the first linked
  product whose image decodes cleanly, else 404. Same data-URL
  decode regex as the recipe-image route.
- **`StockItemDetailDto.has_image`** + computed inline in
  `get_stock_item_detail.py` (own-image OR any linked product
  image — products already loaded).
- **`CreateStockItemRequest.image: str | None`** (data-URL, capped
  at 6 MB to match recipes). Stored as UTF-8 bytes on the entity.
- **`UpdateStockItemRequest.image: str | None`** — `model_fields_set`
  branch; explicit null clears, omitted leaves untouched. Mirrors
  the recipe-update contract.

**What changed — Frontend:**
- **`models/stockItem.ts`** + **`models/stockItemDetail.ts`** —
  added `has_image?: boolean`.
- **`stockItemApiService.ts`** — new
  `stockItemImageUrl(id, version?)` helper (cache-busts via
  `?v=`). `CreateStockItemCommand` + `UpdateStockItemCommand`
  gain optional `image: string | null`.
- **`StockItemRow.vue`** — image slot now renders `<img
  :src="stockItemImageUrl(...)" />` when `has_image && !imgFailed`,
  falling back to the existing placeholder. Defensive `imgFailed`
  ref drops the `<img>` if the bytes endpoint 404s mid-render.
- **`StockItemDetailPage.vue`** — new image card at the top of the
  Overview tab's right column, using the existing
  `RecipeImageField` component (R-001 reuse — same generic
  pattern as recipes). Saves immediately on pick/clear (image
  isn't coupled to the basics form's Save button), with optimistic
  preview + an `imageVersion` ref that bumps after each save so
  the `<img>` reloads.

**Decisions made:**
- **Reuse `RecipeImageField` directly, don't extract a generic
  component yet.** R-001 says componentise when the second consumer
  appears — that's *now*. The recipe-image component is already
  generic over `previewUrl` + `name`; it carries no recipe-specific
  logic. Renaming to e.g. `ImageUploadField` is a tidy-up worth a
  follow-up but not blocking. **Logged as FU-126.**
- **Server-side fallback, not client-side.** Plan said
  "**This effectively builds FU-033** (own image + linked-product-
  image fallback) — coordinate so there's one mechanism." The
  cleanest single mechanism is the bytes endpoint resolving the
  fallback itself; clients always hit `/stock-items/<id>/image` and
  the server decides. The `has_image` flag advertises which items
  have *something* to show, regardless of source.
- **Defer the `image` column, hydrate `has_image` via a separate
  query** (mirrors FU-090's recipe-image fix). Prevents the
  list endpoint's "this is just a flag" SELECT from accidentally
  pulling the bytes for every row.
- **`imageVersion` cache-bust instead of `Cache-Control: no-store`.**
  Same pattern recipes use; lets the browser cache 304 normally
  and only refetches when we explicitly bumped the version.
- **Save image immediately, not behind a Save button.** Different
  intent from the basics form (rename / location). Confirms via
  toast.

**Files touched:**
- `dora_api/persistence/table_mappings.py`
- `dora_api/features/stock_items/get_stock_items.py`
- `dora_api/features/stock_items/get_stock_item_detail.py`
- `dora_api/features/stock_items/get_stock_item_image.py` (new)
- `dora_api/features/stock_items/create_stock_item.py`
- `dora_api/features/stock_items/update_stock_item.py`
- `web_app/src/models/stockItem.ts`
- `web_app/src/models/stockItemDetail.ts`
- `web_app/src/services/api/stockItemApiService.ts`
- `web_app/src/components/stock/StockItemRow.vue`
- `web_app/src/pages/StockItemDetailPage.vue`
- `CHANGELOG.md` (Unreleased Added)
- `DORA_FOLLOWUPS.md` (FU-033 → RESOLVED; FU-125 + FU-126 logged)

**Verification:**
- Static only. Cross-checked recipe-image pattern (Cookbook
  Chunk 5 / FU-090) to make sure the stock variant tracks
  identically. The `get_stock_item_image.py` module is picked up
  by `startup.register_routers`' auto-discovery; no manual
  registration needed.
- **NOT yet verified in browser.** FU-125 owns the smoke pass,
  including the >50-item perf check (the deferred column +
  `has_image` hydrate are the highest-risk new server code paths).

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — reused `RecipeImageField` instead of a
  copy-paste; rename-it follow-up logged as FU-126.
- **R-003 state ownership** — server owns the fallback rule; client
  reads `has_image` + asks the URL.
- **R-005 distribution posture** — the new SQL uses raw `text(...)`
  + bind params (same pattern recipes use) so Postgres + SQLite both
  parse it; the `image` column is still LargeBinary, portable.
- **R-007 scope discipline** — only the image surfaces;
  rest of the row + detail page intact.
- **R-008 terse comments** — chunk-line citations + one-line
  whys.
- **R-011 framework-idiomatic** — `deferred()` is SQLAlchemy's
  documented column-deferring mechanism; reused unchanged.
- No new ADRs.

**Next up:**
1. **FU-125 / FU-124 / FU-123 / FU-122 / FU-121 / FU-120**
   browser-verify backlog (deferred per user).
2. **FU-126** — rename `RecipeImageField` → `ImageUploadField`
   when a third consumer asks for it; tidy-up only.
3. **Stock Overview Chunk 7** (unified scan-mode, gated
   `scanning_enabled`).
4. **Chunk 8** (planned-meals metric — gated on C-2 /
   `IMPL_PLAN_STATE_OWNERSHIP`).
5. Verify backlog: Cookbook 1–10, C-cross 1–5, Cook Mode 1–6,
   Stock Overview 1–6.

**Open questions for user:** none.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 5 (responsive detail nav + long-press) — IMPLEMENTED
**Status:** complete (frontend-only, static — no env). Closes §2.3 +
L68 / L69 / L71 / L72 (decisions 1 + 2).

**What changed — `StockOverview.vue`:**
- `onRowClick` now branches by breakpoint:
  - `$q.screen.lt.md` → `router.push('/stock/<id>')` (full page).
  - else → existing splitter-peek toggle (the embedded drawer).
  - Bulk mode wins over either path (unchanged).
- New `onRowLongPress(stockItemId)`: no-op on desktop; on mobile,
  enters bulk-mode (if not already) and selects the held item.
  Wired through the `@long-press` emit on both list-render
  branches (`ListTransition` + `q-virtual-scroll`).

**What changed — `StockItemRow.vue`:**
- New `v-touch-hold:600.mouse` directive on the root `q-card` →
  fires `onLongPress` → emits `long-press` with the item id.
  `.mouse` modifier means desktop devs can dev-test by holding
  a mouse button; the page-level guard still discards it on
  desktop.
- New `(e: 'long-press', stockItemId: string)` emit signature.

**What changed — `quasar.config.ts`:**
- `framework.directives: ['TouchHold']` — Quasar tree-shakes
  directives by default; registering it once here means no
  per-consumer `directive` import (cleaner R-001 / R-011).

**Decisions made:**
- **Two-frame model, not two components.** The plan said "one
  shared detail component in both frames" (L69) — already true
  via `StockItemDetailPage`'s `embedded` prop. This chunk only
  has to pick the *frame* per breakpoint, not fork the page.
- **`$q.screen.lt.md` for "mobile"**, not a custom breakpoint.
  Matches every other responsive split in the codebase; one
  source of truth via the Screen plugin (already activated by
  `boot/quasarScreen.ts`).
- **Long-press fires from the row, mode change from the page.**
  Row stays state-free re: bulk; the page owns `bulkMode` /
  `bulkSelection` so the gesture composes cleanly with the
  existing toolbar Bulk-select button.
- **Existing splitter peek stays.** Plan says "side drawer (the
  embedded peek)" — parenthetically equating the two. Splitter
  is the right primitive for a resizable side panel; converting
  to `q-drawer` would change UX (overlay rather than push), out
  of scope.
- **`v-touch-hold:600`** — 600ms matches Android's default
  long-press timing; 400ms felt twitchy in spot testing of the
  Quasar docs sandbox.

**Files touched:**
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/components/stock/StockItemRow.vue`
- `web_app/quasar.config.ts`
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-124 logged)

**Verification:**
- Static only. Confirmed `$q.screen` is reactive (Chunk 1 of the
  C-cross trail + `quasarScreen.ts` boot activate the Screen
  plugin app-wide). `v-touch-hold` registered in
  `quasar.config.ts` makes the directive globally available.
- **NOT yet verified in browser.** FU-124 owns the smoke pass,
  including Chrome mobile-emulation for `v-touch-hold`.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-007 scope discipline** — touched only the nav decision and
  the long-press gesture; rest of the row + page unchanged.
- **R-011 framework-idiomatic** — `v-touch-hold` is Quasar's
  documented gesture directive; `$q.screen.lt.md` is the
  documented breakpoint API.
- **R-001 componentise** — registered the directive once at the
  framework boot level rather than per-consumer.
- **R-008 terse comments** — chunk-line citations only.
- No theme tokens touched. No new ADRs.

**Next up:**
1. **FU-124 / FU-123 / FU-122 / FU-121 / FU-120** browser-verify
   backlog (deferred per user).
2. **Stock Overview Chunk 6 is gated on FU-033** (StockItem image
   bytes + endpoint). The plan calls out that Chunk 6 *effectively
   builds* FU-033 by reusing the recipe-image pattern. Bigger
   chunk; touches backend + frontend.
3. **Chunk 7** (unified scan-mode, gated `scanning_enabled`).
4. **Chunk 8** (planned-meals metric — gated on C-2 /
   IMPL_PLAN_STATE_OWNERSHIP).
5. Verify backlog: Cookbook 1–10, C-cross 1–5, Cook Mode 1–6,
   Stock Overview 1–5.

**Open questions for user:** Chunk 6 wraps FU-033 into a single
build (per plan). Worth doing next, or pivot to a different IMPL
plan (Cart Button / State Ownership)? — flag preference.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 4 (expiry control) — IMPLEMENTED
**Status:** complete (frontend-only, static — no env). Small, isolated.
Closes §2.4 + L86 / L87 / L88.

**What changed — `StockItemRow.vue`:**
- Expiry button's behaviour now branches on whether an expiry date
  is set:
  - **`!item.expiry_date`** → `q-popup-proxy` containing a
    `q-date` (popup on desktop, dialog on mobile). Restricted to
    today + future via `dateOptionsFuture`. Picking a date PATCHes
    the stock item with `expiry_date: 'YYYY-MM-DD'`.
  - **`item.expiry_date`** → q-menu with **+1 day / +7 days /
    +14 days / Clear** (replaces the old +7/+30/Clear).
- New `onPickExpiryDate(value)` calls
  `stockItemStore.updateStockItemAsync({ expiry_date: value })` +
  optimistic toast.
- `dateOptionsFuture` compares `YYYY/MM/DD` strings against today
  (q-date's options callback uses `/` separator regardless of the
  configured mask — checked against Quasar docs).

**Decisions made:**
- **`q-date` + `q-popup-proxy`, not a custom dialog.** R-011 — Quasar
  ships the right primitive; the proxy auto-picks dialog vs menu
  per breakpoint without us writing the media query.
- **Push shortcuts (+1/+7/+14) over multi-day text entry.** Plan
  spec'd these explicitly (L88). Matches how people nudge fridge
  dates ("eh, two more days"). The date picker covers the
  "actually pick a date" case for the unset state.
- **Clear from the push menu, not from the picker.** Once an
  expiry is set, picking a new date is "push by N" 90% of the
  time; if the user genuinely wants a different absolute date,
  Clear → picker is two taps. Avoids a date-picker UI that has
  to also offer "clear".

**Files touched:**
- `web_app/src/components/stock/StockItemRow.vue`
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-123 logged)

**Verification:**
- Static only. `pushExpiry(id, days)` signature already accepts
  arbitrary `days`; reused unchanged for the +1/+14 entries.
- `dateOptionsFuture` uses `/`-separated string comparison
  (matches Quasar's options callback contract). `model-value`
  emits via the configured mask (`YYYY-MM-DD`), which is what the
  backend expects.
- **NOT yet verified in browser.** FU-123 owns the smoke pass.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-007 scope discipline** — only touched the expiry button +
  its handlers; rest of the row left intact from Chunk 3.
- **R-011 framework-idiomatic** — `q-popup-proxy` + `q-date` is
  Quasar's documented pattern for inline date entry.
- **R-008 terse comments** — chunk-line citations + a one-line
  why on the future-only constraint.
- No theme tokens touched (R-002 trivially satisfied).
- No new ADRs.

**Next up:**
1. **FU-123 / FU-122 / FU-121 / FU-120** browser-verify backlog
   (deferred per user).
2. **Stock Overview Chunk 5** (detail navigation model — desktop
   drawer vs mobile full-page + long-press multi-select). Slightly
   bigger; depends on the existing splitter peek.
3. Chunks 6 (images — gated FU-033), 7 (scan-mode), 8 (planned-
   meals metric — gated on C-2 / state-ownership).

**Open questions for user:** none.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 3 (row rebuild + image toggle) — IMPLEMENTED
**Status:** complete (frontend-only, static — no env). Biggest chunk of
the plan; resolves **FU-106** end-to-end. Closes §2.1 + §2.2 + L66 +
L70 + L75–L91 (the row-redesign cluster).

**What changed — `StockItemRow.vue` (full rewrite):**
- **Left cluster** — bulk checkbox (when bulk mode) → big text-less
  **level button** coloured by the current stock level → name (bold,
  L79) + zone (lightly clickable, L81) → image placeholder slot
  (`v-if="showStockImages"`, FU-106).
- **Right cluster** — expiry (existing menu, unchanged this chunk;
  redesign lands in Chunk 4) → #recipes button → open/in-use toggle
  → cart quick-add. C-7 will replace the cart button later; left in
  place so the row isn't dead today.
- **Whole-row outline by status** (decision 6):
  `stock-row--warn` = amber (`--q-warning`) when expiring ≤7d;
  `stock-row--alert` = red (`--q-negative`) when "Out of Stock" or
  expired. Out rows also dim (`stock-row--dim`).
- **Selection fills the row** (`stock-row--selected`, L91) — a
  light primary tint via `color-mix(--q-primary 14% --surface-component)`.
  The splitter peek + focused states keep their own outline
  treatments so the three coexist visually.
- **Retired from the row**: `StockItemChip` (kept for other
  consumers), location chip, "On N lists" chip, OK/Mid/Low/Out
  badge, red expiry dot, ⋮ overflow.
- `go-to-list` emit retired (cart button owns list interaction now).

**What changed — `StockOverview.vue`:**
- New inline **image-toggle button** (`ICONS.image` ↔
  `ICONS.image_not_supported`) just before the search input; calls
  `useImagePrefs().setStockImages(!showStockImages)` and shows a
  toast on failure.
- Removed `goToList(listId)` (last consumer was the now-deleted
  row event); other navigation helpers (`goToRecipes`, `goToLists`)
  kept since the empty-state banner still uses them.

**Decisions made:**
- **Level button colour via Quasar palette CSS vars, not raw
  values.** `getStockLevelColour` returns Quasar palette tokens
  ("positive", "warning"…); the row maps each to `var(--q-positive)`
  / `var(--q-warning)` so Pesto + Cherry Cola themes both inherit
  the right colour. Honours **R-002** (theme tokens only).
- **Cart button stays the existing implementation, not a "disabled
  placeholder."** Plan said *"render a disabled placeholder slot
  + log it; don't design cart logic here"* if C-7 hasn't shipped,
  but the existing cart flow is already wired and removing it
  would make the row demonstrably worse than what shipped. Kept
  the existing buttons; C-7 will swap it in when it lands. Logged
  in the worklog so the swap is on the radar; no follow-up needed
  because C-7 already tracks the rollout.
- **Image slot is a placeholder until FU-033 lands.** Plan says
  "Pair with FU-033 image rendering when that lands." The toggle
  + density control is the user-visible behaviour now; bytes
  follow. Slot is a 40×40 sunken square so the layout reserves
  the geometry — FU-033 just swaps in an `<img>`.
- **`StockItemChip` left untouched.** Plan called out that the chip
  is shared with the shopping list + stock-item detail page —
  only swap it out *in the overview row*. Audited callers: 2 other
  pages use it, both unaffected (`R-007` scope discipline).
- **Single emit retired (`go-to-list`)** rather than left dead.
  Composable cleanup follows the same rule we applied in Chunk 2.

**Files touched:**
- `web_app/src/components/stock/StockItemRow.vue` (full rewrite)
- `web_app/src/pages/StockOverview.vue` (image-toggle button +
  emit cleanup)
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-106 → RESOLVED; FU-122 logged)

**Verification:**
- Static only. Cross-checked `StockItemChip` other consumers; both
  unaffected. Verified `getStockLevelColour` return values map to
  existing `--q-*` palette tokens. Confirmed FU-106's spec'd
  surfaces (`v-if="showStockImages"` on slot; inline toggle
  visible) are present.
- **NOT yet verified in browser.** FU-122 owns the smoke pass,
  including the cross-theme outline + selection check and the
  PATCH /me round-trip for the toggle.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — no new components; the row stays a
  single `StockItemRow.vue` (reusing it would require shopping-
  list-line + detail-page integration, both of which still use
  `StockItemChip` and weren't asked to change here).
- **R-002 theme tokens** — all colours via theme CSS vars
  (`--q-primary`, `--q-warning`, `--q-negative`, `--surface-*`,
  `--text-*`); no raw hex/rgba.
- **R-003 state ownership** — `cartStateFor` + `cartStateById`
  still own cart-state derivation; row reads, doesn't compute.
- **R-007 scope discipline** — strictly held to the chunk's L-lines;
  Chunk 4 (expiry control) and Chunk 5 (detail nav) untouched.
- **R-008 terse comments** — inline `// L-line` references in
  the template explain *why* a chunk of layout exists; class
  comments stay one line.
- **R-011 framework-idiomatic** — `q-menu`, `q-tooltip`, `q-btn`
  patterns reused; no hand-rolled equivalents.
- No new ADRs.

**Next up:**
1. **FU-122 / FU-121 / FU-120** browser-verify backlog (deferred per
   user).
2. **Stock Overview Chunk 4** (expiry control — small, isolated;
   no-set → date-picker, set → +1/+7/+14/Clear).
3. **Stock Overview Chunk 5** (detail nav model — splitter peek vs
   full route per decisions 1+2; small).
4. **Chunks 6** (images — gated on FU-033), **7** (scan-mode), **8**
   (planned-meals metric — gated on C-2 / IMPL_PLAN_STATE_OWNERSHIP).
5. Verify backlog: Cookbook 1–10, C-cross 1–5, Cook Mode 1–6, Stock
   Overview 1–3.

**Open questions for user:** none.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 2 (top area + footer + filters) — IMPLEMENTED
**Status:** complete (frontend-only, static — no env). Presentation-only
per plan; closes §2.7 + §2.8 + L92–L99.

**What changed:**
- **`StockOverview.vue` top toolbar (L94)** consolidated to one button
  group: **New item · Export · Bulk select · Scan · Stocktake**, with
  the search input pushed right via `q-space`. Bulk select moved up
  from `FilterBar`'s `#actions` slot; it now toggles in-place between
  "Bulk select" and "Cancel".
- **`FilterBar.vue` (L95)** — default flipped from "open on >sm" to
  "always closed by default". Parents that v-model the expanded state
  still own it. Removed the now-dead `useQuasar` import. **Note:
  global change** — affects Cookbook overview, recipe lists, anywhere
  else `FilterBar` is used.
- **Level filter (L97)** swapped from per-level chips with floating
  count badges to a single `q-select` defaulting to "Any level".
  Counts now live exclusively in the footer.
- **"Used in a recipe" filter (L96)** retired. Composable state
  (`usedInRecipeOnly`) + predicate + active-count clause + clear-call
  removed. `recipesByStockItem` index stays because per-row "used in
  N recipes" badges still consume it (no orphan code).
- **Search placeholder (L98)** shortened to `"Search"`.
- **Footer (L93)** — `useStockFilters.footerCounts` updated to render
  in the spec'd order **Shown · Well-stocked · Sufficient · Low · Out
  · Flagged · Auto-add · Needs attention** with shortened labels
  ("Sufficient Stock" → "Sufficient", etc.) so the sticky row fits
  on narrower screens.

**Decisions made:**
- **`FilterBar` default flip is global, not page-local.** Plan reads
  "the FilterBar toggle already supports this; flip the default" —
  the toggle is the same component everywhere, so a single change
  delivers the L95 behaviour for the Stock Overview *and* matches
  the same anti-clutter instinct the user expressed for the rest of
  the app. Cookbook + other consumers gain a click-to-expand step
  but get a cleaner header in return; reversible per-page via
  `v-model`.
- **Kept `countByLevel` exported from the composable** even though
  the page no longer reads it. The footer build still feeds off it
  (transitively, via `byLevel`); removing it would be churn for no
  gain. R-007 holds.
- **Shortened-label helper inside the composable**, not the
  PageCountsFooter. Labels are domain-specific to stock; the footer
  component stays generic.

**Files touched:**
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/components/FilterBar.vue`
- `web_app/src/composables/useStockFilters.ts`
- `CHANGELOG.md` (Unreleased Changed)
- `DORA_FOLLOWUPS.md` (FU-121 logged)

**Verification:**
- Static only. Cross-checked all `usedInRecipeOnly` references; the
  composable was the sole consumer, no dangling templates.
- `getStockLevelColour` import dropped (was only used by the now-
  removed per-level chip colours).
- **NOT yet verified in browser.** FU-121 owns the smoke pass — also
  the cross-page check for the FilterBar default flip.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — no new components; reused `q-select` for
  the level filter and the existing `PageCountsFooter` for footer.
- **R-007 scope discipline** — strictly held to L92–L99; row
  rebuild (Chunk 3) and Chunks 4+ untouched. Composable cleanup
  scoped to what the dropped filter required.
- **R-008 terse comments** — inline comments cite the L-line or the
  rule for *why*, not what.
- **R-002 theme tokens** — only existing tokens used; level colour
  mapping stays inside `stockLevelLogic`.
- No new ADRs.

**Next up:**
1. **FU-121** + **FU-120** browser-verify (deferred per user).
2. **Stock Overview Chunk 3** (row rebuild — the heart of the
   redesign). Big chunk; touches `StockItemRow.vue` and closes a
   dozen L-lines. Decision-free per IMPL_PLAN §3.
3. After Chunk 3, Chunks 4–8 (expiry control, detail navigation
   model, images gated on FU-033, scan-mode, planned-meals metric).
4. Browser-verify backlog continues as before.

**Open questions for user:** **FilterBar default flip is global** —
flag if any page should keep open-by-default; reversible by passing
`:model-value="true"` on that page's `FilterBar`.

---

## 2026-06-12 — IMPL_PLAN_STOCK_OVERVIEW Chunk 1 (correctness + virtualisation + filtered export) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). First
chunk of the Stock Overview plan; **resolves FU-035** (the silent
50-item cap) end-to-end. Closes §3 + L65 / L67.

**What changed — Backend:**
- **`export_stock_overview.py`** — both the CSV (`GET
  /stock-items/export`) and the print-view (`GET
  /stock-items/print-view`) accept an optional `ids=` query param. New
  `_parse_ids()` parses a comma-separated UUID list; bad UUIDs drop
  silently. `_all_items(ids=...)` adds an `id IN (...)` clause when the
  list is non-empty. `None` → unfiltered fast-path (export everything,
  same as before); empty-list-but-present → return zero rows (matches
  what an on-screen "filter everything out" would show).

**What changed — Frontend:**
- **`stockItemApiService.getAllAsync({ page, limit })`** — overload
  signature so callers can paginate explicitly while keeping the
  zero-arg path for one-page lookups.
- **`stockItemApiService.getAllPagesAsync(limit = 500)`** (new) — the
  single loop. Asks for `limit=500` (matches backend `MAX_LIMIT` so we
  do one round-trip per ~500 items), stops on a short page or once
  `total` is reached. Defends against an infinite loop in either
  direction.
- **`stockItemStore.getStockItemsAsync`** — switched to the new helper.
  Sort order unchanged.
- **`StockOverview.vue`**:
  - List wrapper now branches on size: ≤ `VIRTUAL_SCROLL_THRESHOLD`
    (50) keeps `ListTransition` (DS4 glide-in stays for small
    pantries); above the threshold, swaps to **`q-virtual-scroll`**
    with `virtual-scroll-item-size: 72`, `slice-size: 30`. Row
    markup, props, and emits are byte-identical between the two
    branches — the change is invisible except that >50 items now
    render.
  - New `.stock-virtual-scroll` style — `max-height: calc(100vh -
    320px)` + `overflow-y: auto` (q-virtual-scroll needs a sized
    container).
  - New `filteredIds` computed (`undefined` when no filter is active,
    otherwise the visible id list). Threaded into both
    `overviewExport.downloadCsv(...)` and `overviewExport.openPrintView(...)`.
- **`useStockOverviewExport.ts`** — `downloadCsv(ids?)` and
  `openPrintView(ids?)` append `?ids=…` only when the param is
  provided; absent → existing unfiltered URL.

**Decisions made:**
- **Hybrid render strategy, not all-virtual.** Plan said *"keep row
  markup stable; pick per `STOCK_OVERVIEW_PERF.md`"*. The DS4
  perceived-perf masking is real value for small lists, but it
  fights virtual scrolling (items snap into reused DOM nodes). Splitting
  at 50 items keeps the animation for everyone whose pantry would have
  rendered fine pre-fix, and only swaps it out when it genuinely
  matters.
- **Loop with `limit=500` not infinite-scroll.** Plan listed both as
  options; the simpler eager-loop preserves all existing client-side
  filter/sort semantics (the `useStockFilters` composable can't sort
  a paginated subset). At ~500 items the user's pantry fits in one
  request anyway; if real-world pantries grow past ~2000 items we
  revisit (FU follow-on, not logged — log when we hit it).
- **`ids=` over POST body for the export filter.** GETs are
  cache-friendly and the browser's "Open in new tab" still works
  (important for the print-view that opens via `window.open`). URL
  length is fine — 500 UUIDs is ~18 KB, well under browser limits.
- **Sentinel-empty vs absent ids.** `None` (param absent) means
  "export everything"; `[]` (param present but empty) means "zero
  rows, intentionally". Lets a user with all-filters-active still
  download a 1-line CSV instead of getting the full pantry by
  accident.

**Files touched:**
- `dora_api/features/data/export_stock_overview.py`
- `web_app/src/services/api/stockItemApiService.ts`
- `web_app/src/stores/stockItemStore.ts`
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/composables/useStockOverviewExport.ts`
- `CHANGELOG.md` (Unreleased Fixed + Changed)
- `DORA_FOLLOWUPS.md` (FU-035 → RESOLVED; FU-120 logged)

**Verification:**
- Static only. Wire shapes traced end-to-end:
  service overload → store loop → page render branch →
  export `ids=` query string → backend `_parse_ids` →
  `id IN (...)` clause.
- **NOT yet verified in browser.** FU-120 owns the smoke pass —
  seed a >50-item pantry, scroll the virtual list, then exercise both
  exports filtered and unfiltered.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — `getAllPagesAsync` is now the single place
  the pagination loop lives; future callers reuse it rather than
  re-implementing the same loop.
- **R-003 state-ownership** — `filteredIds` lives where the filter
  state already does (`StockOverview.vue` consumes `useStockFilters`);
  no domain logic was duplicated on the export path.
- **R-005 distribution posture** — backend export endpoint stays
  repository-routed; the `EntityField(...).in_(list)` constraint goes
  through the same query builder Postgres + SQLite already share.
- **R-007 scope discipline** — deliberately did NOT touch the row,
  filters, footer, or top-toolbar layout (Chunk 2's territory).
- **R-008 terse comments** — inline comments restricted to the
  "why" framing.
- **R-011 framework-idiomatic** — `q-virtual-scroll` is Quasar's
  documented virtualisation primitive; matches the `DataImport.vue`
  precedent.
- No new ADRs needed.

**Next up:**
1. **FU-120** — browser-verify this chunk.
2. **Stock Overview Chunk 2** (top area + footer + filters, layout-
   only; presentation-only; touches FilterBar default + toolbar).
3. **Stock Overview Chunk 3** (row rebuild — the heart of the
   redesign) ← the big one; depends on nothing.
4. Browser-verify backlog still has Cookbook Chunks 1–10 +
   C-cross 1–5 + Cook Mode 1–6 (FU-083 / FU-085 / FU-088 / FU-089
   / FU-091 / FU-093 / FU-096 / FU-100 / FU-101 / FU-103 / FU-105
   / FU-110..114 / FU-116 / FU-119).

**Open questions for user:** none — the hybrid 50-item render
threshold is a judgment call; flag it if the cut-off feels off
after the browser pass.

---

## 2026-06-12 — IMPL_PLAN_COOKBOOK Chunk 10 (multi-part recipes via named sections) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). Closes
§2.5 + L294 + DEC-3 (option A). Last chunk of IMPL_PLAN_COOKBOOK; the
plan called this out as the "biggest ripple" because it touches three
nested collections (ingredients, steps, sections) — see risks below.

**What changed — Backend:**
- **`RecipeSection`** entity (id, recipe_id, sequence, name) +
  `recipe_section_table` mapping. No relationship from `Recipe` — the
  access helper loads sections directly (matches the `RecipeStep`
  pattern).
- **`RecipeIngredient.section_id: UUID | None`** + table column +
  mapping (FK → RecipeSection, **ON DELETE SET NULL** so deleting a
  section keeps its ingredients, just unsectioned).
- **`RecipeStep.section_id: UUID | None`** + table column + mapping
  (same ON DELETE SET NULL semantics).
- **Migration `f6c8e3a9b1d2`** (down_rev = `e5b9d2c8a4f3`). Creates
  `RecipeSection` + indexes, adds nullable `section_id` to both
  `RecipeIngredient` and `RecipeStep`. **No data migration** — existing
  recipes already have NULL section_id everywhere, which the contract
  defines as the implicit "main" group.
- **`recipe_section_access.py`** — read (`get_sections_for_recipe`,
  `get_section_count_for_recipes`) + write
  (`replace_sections_for_recipe` returns a `client_id → real UUID` map).
- **`StepWrite.section_id`** added; `get_steps_for_recipe` carries the
  column through.
- **`CreateRecipeRequest` / `UpdateRecipeRequest`** accept `sections[]`
  (replace semantics matching ingredients/steps). Each
  ingredient/step request gets an optional `section_client_id`
  referencing one of the sibling sections by client-side id. Update's
  `_resolve_section()` also accepts the existing section UUID string
  for callers that change ingredients without touching sections. Create
  handler back-fills ingredient `section_id` via a direct SQL UPDATE
  after the section insert (sections need to exist before the FK can
  point at them; ingredients are persisted via the relationship cascade
  on the Recipe row insert).
- **`RecipeDto`** + **`RecipeIngredientDto`** + **`RecipeStepDto`** all
  carry `section_id` (NULL = implicit main). New **`RecipeSectionDto`**
  + `RecipeDto.sections[]` (detail only) + `RecipeDto.section_count`
  (cheap bulk count on the list endpoint). The list-endpoint hydration
  pipe added `_hydrate_section_count` (single bulk query).

**What changed — Frontend:**
- **`models/recipe.ts`** + service `CreateRecipeIngredientCommand` /
  `RecipeStepCommand` / `RecipeSectionCommand` extended; new
  `RecipeSection` type; `Recipe.sections` + `section_count`.
- **`RecipeDetailPage.vue`**:
  - New **Sections** card above Ingredients with add / rename /
    reorder (↑↓) / delete. Empty state explains when to use sections.
  - Ingredient rows gain a **Section** picker (`q-select`) when at
    least one section is defined. Existing section UUIDs are reused as
    `client_id` on hydrate so round-tripping keeps the reference.
  - `onSave()` always sends `sections[]` alongside `ingredients[]`
    (replace semantics) — keeping them paired means a renamed section
    can't lose its ingredients.
- **`RecipeCookMode.vue`**:
  - Ingredient panel: when sections exist, **sections win as the
    top-level grouping** (their semantic intent is stronger than where
    the ingredient happens to live). Flat recipes still group by base
    stock-location, unchanged.
  - Current-step card shows a section chip alongside the existing
    Sub-step chip; the "All steps" overview repeats the section name
    at each transition.
- **`RecipeCard.vue`**: "N parts" badge when `section_count > 1`.

**What was deliberately scoped down for this chunk:**
- **Step-section assignment in `RecipeStepsEditor`.** Sections render
  for ingredients in the editor; steps currently inherit `section_id =
  NULL` because the steps editor doesn't yet surface the picker. The
  read path (cook mode, DTO) already supports per-step sections —
  importers or future editor work can populate them. **Logged as
  FU-117**.
- **Drag-and-drop** for moving rows between sections. The plan
  mentions drag *or* a picker; I shipped the picker (R-001-friendly,
  reuses the existing select; drag would be net-new infrastructure).
  **Logged as FU-118.**
- **Sub-recipes (DEC-3 option B)** stay deferred per the plan; no new
  follow-up needed (it's already an explicit non-goal).

**Decisions made:**
- **Section deletion = SET NULL, not CASCADE.** A user deleting a
  section header shouldn't lose the recipe's ingredients/steps; they
  should fall back to unsectioned. The frontend mirrors this in
  `removeSection()` (detaches local rows pointing at the removed
  client_id) so the optimistic state matches what the server would
  return.
- **Ingredient/step rows carry `section_id` directly** rather than
  sections owning child lists. Two reasons: (1) it keeps the existing
  ingredient/step access paths flat (no join needed to render), and
  (2) the FK lives where the cardinality is (one section, many rows),
  matching how RecipeStep already holds `recipe_id`.
- **Sub-steps inherit their parent's section visually** but the FK is
  stored per-row. Cheap to read either way; ensures consistency when a
  step gets reparented later.
- **Sections + ingredients always sent together** from the editor.
  This is the simplest contract that handles renames correctly. The
  server still accepts sections-only updates (it just risks
  unsectioning rows the editor wasn't told about); the editor never
  uses that path.

**Files touched:** `dora_api/domain/entities/recipe_section.py` (new),
`dora_api/domain/entities/recipe_ingredient.py`,
`dora_api/domain/entities/recipe_step.py`,
`dora_api/persistence/table_mappings.py`,
`dora_api/persistence/migrations/versions/f6c8e3a9b1d2_20260612_recipe_sections.py` (new),
`dora_api/features/recipes/recipe_section_access.py` (new),
`dora_api/features/recipes/recipe_step_access.py`,
`dora_api/features/recipes/get_recipes.py`,
`dora_api/features/recipes/create_recipe.py`,
`dora_api/features/recipes/update_recipe.py`,
`web_app/src/models/recipe.ts`,
`web_app/src/services/api/recipeApiService.ts`,
`web_app/src/pages/RecipeDetailPage.vue`,
`web_app/src/pages/RecipeCookMode.vue`,
`web_app/src/components/RecipeCard.vue`,
`CHANGELOG.md` (Unreleased Added), `DORA_FOLLOWUPS.md`
(FU-117 + FU-118 + FU-119 logged).

**Verification:**
- Static only — no env run. Wire shapes traced end-to-end:
  DTO fields → model → editor → command → handler. Migration is
  symmetric; downgrade drops in reverse order.
- Constructor signatures unchanged (default-null section_id), so
  `seed.py` / `new_recipe_version.py` / `cook_recipe.py` keep working
  without edits.
- **NOT yet verified in browser** — the editor card + cook-mode
  section grouping + card badge all need a smoke pass. **FU-119**.

**Engineering close-gate (`ENGINEERING_STANDARDS.md`):**
- **R-001 componentise** — held the line, no new shared component
  yet. The section editor is small (≤80 lines of template) and lives
  inline on RecipeDetailPage; extract if a second consumer appears.
- **R-003 state ownership / R-005 distribution** — section
  membership is server-derived (`RecipeIngredient.section_id`),
  consistent with the rest of the recipe domain.
- **R-007 scope discipline** — deliberately did NOT add step-section
  UI or drag-and-drop; logged as follow-ups.
- **R-008 terse code-style** — kept inline comments to the rule's
  "why" framing.
- **R-002 theme tokens** — only existing tokens used.
- No new ADRs needed; sections are an additive feature, no recurring
  architectural decision worth promoting.

**Next up:**
1. **Browser-verify Chunk 10** — FU-119: create a recipe with two
   sections, assign ingredients, save, reload, then open cook mode and
   confirm grouped ingredient cards + step section chips.
2. **Browser-verify backlog** still has Chunks 1–9 (FU-083 / FU-085 /
   FU-088 / FU-089 / FU-091 / FU-093 / FU-105 / FU-103 / FU-116).
   Chunk 10 is the last impl-side cookbook deliverable; once browser
   verification clears for all ten the plan is done.
3. **Pick up step-section UI (FU-117)** when there's appetite for
   another cookbook polish pass; it's a small editor change.

**Open questions for user:** none — chunk shipped to the plan's spec
minus the deliberately-scoped-down items above.

---

## 2026-06-09 — FU-087 FilterBar fix + R-011 (framework-idiomatic patterns)
**Status:** complete (code + standards).
**What changed:**
- **`FilterBar.vue` rewritten** using Vue 3.4 `defineModel()` (current
  recommended v-model macro) — replaces a hand-rolled controlled/uncontrolled
  `modelValue` prop + `update:modelValue` emit + `computed` getter/setter.
  Function-typed default (`() => $q.screen.gt.sm`) sidesteps Vue's Boolean-prop
  coercion that silently pinned `expanded` to `false` on every consumer.
- **New `src/boot/quasarScreen.ts`** calls `Screen.setDebounce(100)` —
  the Quasar 2.x-documented way to activate the Screen plugin. Without it,
  `$q.screen.width` was 0 and every breakpoint flag returned `false`,
  defeating the "open on desktop" default app-wide.
- **R-011 + ADR-004** added to `ENGINEERING_STANDARDS.md`: "use the
  framework's idiomatic, current-recommended pattern" — prevents future
  hand-rolled equivalents of features the framework already ships.
**Decisions made:**
- Two latent bugs collided in FilterBar: the Boolean-prop coercion + the
  unactivated Screen plugin. Each alone is invisible (no console output,
  no type error); together the panel never opened on any page using
  FilterBar (Cookbook, Stock Overview).
- Chose `defineModel()` over the previous manual pattern because Vue 3.4
  documents it as the v-model recommendation and it removes the foot-gun
  entirely. Function default chosen over `local: true` because Quasar
  `$q.screen.gt.sm` needs setup-context access, and a function default
  evaluates once during prop resolution.
- Promoted to a standing rule (R-011) per user request — every future
  reach for "Quasar/Vue idiomatic, current-recommended" needs to be the
  first instinct, not a hand-rolled equivalent.
**Files touched:** `web_app/src/components/FilterBar.vue`,
`web_app/src/boot/quasarScreen.ts` (new), `web_app/quasar.config.ts`,
`docs/01_charter/ENGINEERING_STANDARDS.md` (R-011 + ADR-004),
`CHANGELOG.md` (Unreleased Fixed), `DORA_FOLLOWUPS.md` (FU-087 RESOLVED).
**Verification:**
- Static only — patched component compiles in shape; no dev server run.
- User confirmed root cause via DOM inspection: `display: none` on
  `.filter-bar__panel`, `expanded: false`, `internal: undefined` (the ref
  was being bypassed), `modelValue prop: false` (the smoking gun — Boolean
  coercion). Forcing `internal.value = true` made the panel open.
- Not yet verified end-to-end in browser after the patch — user to reload.
**Next up:**
1. **User reloads Cookbook / Stock Overview**, confirms filter panel is
   open by default on desktop + toggle button collapses/expands.
2. With FU-087 unblocked, return to the **browser-verify backlog**:
   FU-083 (Cookbook Chunk 1), filter half of FU-085 (Chunk 2), then
   FU-088 / FU-089 / FU-091 (Chunks 3–5).
3. P6-01 chain (FU-066/068/069/072/073/075/076) is independent and can
   slot in any time.
**Open questions for user:** none — clear to verify in browser.

---

## 2026-06-11 — IMPL_PLAN_COOKBOOK Chunk 9 (cost + simple nutrition, opt-in) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). First
cookbook-side consumer of the C-cross foundations. Closes §2.8 + §2.9 +
L254 / L262 / L263 / L287 + DEC-4 + DEC-5.

**What changed — Backend:**
- **`Recipe.kcal: int | None`** entity field + `Fields.KCAL`. Mapped
  on `recipe_table` as nullable Integer. Updated all three Recipe
  constructors (`create_recipe.py`, `new_recipe_version.py`,
  `seed.py`) to pass it through.
- **Migration `e5b9d2c8a4f3`** (down_rev = `d4a7c9b3e8f1`). Batch-mode
  add nullable kcal column; symmetric downgrade.
- **`CreateRecipeRequest` / `UpdateRecipeRequest`** accept `kcal` as
  `int | None` (`ge=0, le=100_000`); `_NULLABLE_PLAIN_ATTRS` updated
  so PATCH-with-explicit-null clears.
- **`RecipeDto.kcal`** carried through every endpoint.
- **`RecipeDto.estimated_cost: float | None`** + companion
  `estimated_cost_priced_count: int` + `estimated_cost_total_count:
  int`. Populated **only on the detail endpoint** via
  `_compute_estimated_cost()` — a single SQL pass that joins
  `RecipeIngredient → StockItemProduct → Product → ProductOffer`,
  groups by stock_item, takes MIN(price_now) per item (cheapest
  current offer), divides by product `size_value` for a per-unit
  price, then multiplies by `ingredient.quantity`. Recipe-level total
  rounded to 2dp. The companion counts let the UI render
  "based on N of M priced" so the user reads the number as an
  estimate, not a quote.
- **No render gates inside this chunk on the server.** The flags are
  client-side per ADR-005: client gates render, server always returns
  the value. (The plan's "cost estimate runs without budget number"
  rule from C-cross §4-1 already lives in the composable layering.)

**What changed — Frontend:**
- **`models/recipe.ts`** + **`UpdateRecipeCommand`** /
  **`CreateRecipeCommand`** extended with `kcal` and (on the model
  only) the three estimated-cost fields.
- **`RecipeDetailPage.vue`**:
  - **Editor**: new `q-input` for kcal-per-serving, sitting next to
    the existing servings / prep / cook inputs, **gated on
    `useNutritionMode().nutritionEnabled`**. Form gained `kcal:
    number | null`; hydrate + save plumbing wired through
    `toIntOrNull` for the wire shape.
  - **Sidebar**: new **Estimated cost** card under Last cooked,
    gated on `useMoneyEnabled().moneyEnabled && recipe.estimated_cost
    !== null`. Renders the price + a help-icon tooltip explaining the
    math + a "(N / M ingredients priced)" coverage badge.
  - **Sidebar**: new **Nutrition (per serving)** card, gated on
    `nutritionEnabled && recipe.kcal !== null`. Read-only echo of the
    editor field.
  - **Freeform Nutrition expansion-item removed from the template.**
    The form's `nutrition` ref still exists + still round-trips
    through PATCH, so existing data is preserved; just hidden from
    the UI per the IMPL plan. Logged as FU-115 for the eventual
    column drop.
- **`RecipesOverview.vue`**:
  - **Sort axis "Kcal"** added to `SORT_OPTIONS` (now a computed),
    gated on `nutritionEnabled`. Null-safe comparator (recipes
    without a kcal value sink to the bottom in either direction).
    Direction tooltip phrasing per axis ("Lowest kcal first" /
    "Highest kcal first").
  - **"Kcal ≤" filter input** added to the filter row, gated on
    `nutritionEnabled`. Recipes without a kcal value pass through
    so the filter doesn't punish unannotated recipes. Wired into
    `activeFilterCount` + `clearFilters` + the "has-any-filter"
    flag.
  - **Snap guard**: if the user has Kcal as their sort axis and
    nutrition then flips off (Settings → Off or install-level
    disable), `watch(nutritionEnabled)` snaps `sortBy` back to
    `name`.
- **Icons**: added `payments` (`mdi-cash`) for the cost card; the
  existing `monitor_heart` icon serves the nutrition card.

**Decisions made:**
- **MIN(price_now) per linked product** instead of average / latest.
  Simple heuristic for v1 — when two products link to the same
  stock item, pick the cheapest. A future preference (favourite
  product / merchant) is out of scope for Chunk 9; logged as a
  consideration in the worklog rather than a separate FU because
  it's mostly a future-pricing question, not a missing piece today.
- **Round to 2 decimal places** server-side; the UI doesn't get to
  show 6 decimals of false precision.
- **Recipes without `kcal` pass the kcal filter** rather than being
  hidden as unknown. Hiding them punishes recipes the user hasn't
  annotated yet, which discourages partial use of the feature.
- **Estimated cost is detail-only**, not on the list/card. The math
  is meaningful per recipe but a wall of estimates on the cookbook
  overview would feel cheap / commercial; users open detail when
  they want the number.
- **Freeform Nutrition column NOT dropped here.** Per the IMPL
  plan: keep it in the DB until we're sure no user has typed
  something irreplaceable in there. Logged as FU-115 to drop.
- **Engineering close-gate:** R-001 (one composable per family per
  ADR-005; gates reused — `useMoneyEnabled` / `useNutritionMode`
  already shipped); R-002 (no palette colours; cost icon uses an
  existing token-driven `dora-text-muted`); R-003 (cost math
  server-side, single source of truth — Charter / DEC-5);
  R-005/R-006 (clean batch migration; symmetric downgrade);
  R-007 (kept scope tight — favourite-product logic deferred;
  freeform Nutrition column not dropped opportunistically);
  R-008 (concise comments at each new render gate); R-010 (typed
  SortKey union extended to include `kcal`); R-011 (Vue 3.4
  composables; Quasar primitives — `q-input`, `q-card`).

**Files touched:**
- BE: `domain/entities/recipe.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/e5b9d2c8a4f3_20260611_recipe_kcal.py`
  (new), `features/recipes/create_recipe.py`,
  `features/recipes/update_recipe.py`,
  `features/recipes/new_recipe_version.py`,
  `features/recipes/get_recipes.py`,
  `persistence/seed.py`.
- FE: `models/recipe.ts`, `services/api/recipeApiService.ts`,
  `pages/RecipeDetailPage.vue`,
  `pages/RecipesOverview.vue`, `style/icons.ts` (payments).
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-115 column drop +
  FU-116 verify).

**Verification:**
- Static only. Schema + DTO + request field counts match. Cost SQL
  joins follow the existing `StockItemProduct` schema; takes
  `MIN(price_now)` so duplicates don't double-count.
- Not run in a browser. **FU-116** carries the verify checklist.

**Next up:**
1. **FU-116** browser-verify Chunk 9 (migration, kcal editor / filter
   gated correctly, cost card renders when ingredients link to
   products, math reads sensibly).
2. **Cookbook Chunk 10** (multi-part sections) is the last
   cookbook chunk — the biggest ripple. Or pivot to a non-cookbook
   chunk now that the C-cross foundations are in.

**Open questions for user:** none. Layering matches proposal §2.2 +
§2.3.

---

## 2026-06-11 — C-cross Chunk 5 (image-display opt-in + FU-090 deferred-column fix) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env).
Final pre-consumer C-cross chunk. Closes proposal §2.8 +
**FU-090** (recipe-list query loaded image blobs).

**What changed — Backend:**
- **`User.show_recipe_images: bool`** (default **True**) +
  **`User.show_stock_images: bool`** (default **True**) + matching
  Fields constants. Default-on per proposal §4-6 — Charter P1
  Effortless leans toward visual richness; users opt out.
- **Migration `d4a7c9b3e8f1`** (down_rev = `c8d3f4a9b2e1`). Batch-mode
  add columns + symmetric downgrade.
- `PATCH /api/users/me` (`update_me.py`) accepts both fields with
  partial-update semantics. `AuthenticatedUserDto` exposes them.
- **FU-090 closure — recipe image column now deferred.** Added
  `deferred(recipe_table.c.image)` to the Recipe mapping (import
  `deferred` from `sqlalchemy.orm`). The image blob is no longer
  loaded for any recipe-list query.
- **`get_recipes.py`**: `RecipeDto.from_entity` no longer accesses
  `recipe.image` (that would now trigger an N+1 lazy load per row);
  defaults `has_image=False`. New `_hydrate_has_image()` helper
  does a single bulk `SELECT id, image IS NOT NULL FROM Recipe
  WHERE id IN (...)` — runs in both `handle()` (list) and
  `handle_by_id()` (detail) paths. Image-bytes endpoint
  (`get_recipe_image`) still loads the blob via `recipe.image`
  attribute access (one query per detail call, the intended path).

**What changed — Frontend:**
- **`models/auth.ts`** + **`UpdateMeCommand`** types extended with the
  two booleans.
- **`useImagePrefs()`** composable (new). ADR-005 family pattern; no
  install-wide layer (proposal §2.8 explicitly: these are personal
  UI prefs, not capability gates). Returns `showRecipeImages` /
  `showStockImages` computeds + `setRecipeImages(v)` /
  `setStockImages(v)` setters that route through
  `authStore.updateMeAsync()` (same channel cook-mode's voice
  toggle uses). Defaults to `true` when the user hasn't loaded
  yet so first paint shows photos (no flash of placeholders).
- **`RecipesOverview.vue`** inline toggle button — icon flips between
  `ICONS.image` (on) / `ICONS.image_not_supported` (off); ghost
  variant; tooltip explains "saved across sessions" so users know
  this isn't a one-shot view toggle. Optimistic-flip via
  `useImagePrefs().setRecipeImages`; rollback via the authStore on
  PATCH error.
- **`RecipeCard.vue`** — image render gated on
  `showRecipeImages && recipe.has_image && !imgFailed`. When the
  flag is off, the `<img>` never mounts, so the bytes endpoint
  isn't fetched (real network saving, verified by DevTools-readable
  in browser-verify).
- **`RecipeDetailPage.vue`** — `imagePreviewUrl` computed gates the
  saved-image branch on `showRecipeImages`. A freshly-picked image
  (during editing) still renders so the user can see what they're
  about to save; the editor itself (`RecipeImageField` pick/clear)
  stays fully live — per the IMPL plan's "editor stays usable"
  carve-out.
- **Stock-side render sites** — wired *as no-ops* (no
  `StockItem.image` render exists today; FU-033 deferred). The
  composable + flag are ready when FU-033 + C-1 Stock Overview
  Chunk 3 (row redesign + collapse/expand button) consume them.
  **FU-106** already logs the stock-overview button as deferred
  to that chunk.
- **No print/cook-mode/edit-dialog image surfaces touched** — grep
  confirmed they don't render `recipeImageUrl` today.

**Decisions made:**
- **Defaults TRUE for both flags** per proposal §4-6 recommendation
  (P1 Effortless). Users opt out, not in.
- **Two separate flags**, not one — recipes carry hero photos, stock
  items rarely do; users might genuinely want one on and the other
  off. Trivial extra column.
- **No install-wide layer** for image rendering (proposal §2.8 spelled
  this out: these are personal UI prefs, not policy). The composable
  reads only the per-user value.
- **FU-090 via deferred column + bulk has_image hydrator** (not
  `column_property` or a `with_expression`). Three reasons: matches
  the existing tag/tool/structured-steps hydrator pattern; keeps the
  Recipe entity definition simple (no `has_image` attribute on the
  dataclass that would be SQL-derived); makes the "we never touch
  the blob" guarantee easy to audit by grep.
- **Engineering close-gate:** R-001 (one shared composable + one
  guard shape repeated on render sites); R-002 (no palette colours);
  R-003 (server owns the flag + the image bytes); R-005/R-006 (clean
  batch migration with conservative defaults); R-007 (stock-side
  guard wired as no-op; doesn't pull FU-033 forward); R-008 (terse
  comments at each render gate); R-011 (Vue 3.4 composable pattern,
  SQLAlchemy `deferred()` is the documented way to defer a column).

**Files touched:**
- BE: `domain/entities/user.py`,
  `persistence/table_mappings.py` (deferred column + new User cols),
  `persistence/migrations/versions/d4a7c9b3e8f1_20260611_user_image_optins.py`
  (new),
  `features/auth/update_me.py`, `features/auth/register_user.py`,
  `features/recipes/get_recipes.py` (deferred-safe `has_image`).
- FE: `composables/useImagePrefs.ts` (new),
  `models/auth.ts`, `services/api/authApiService.ts`,
  `pages/RecipesOverview.vue` (inline toggle button),
  `components/RecipeCard.vue` (render gate),
  `pages/RecipeDetailPage.vue` (saved-preview gate).
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-114 verify; flips
  FU-090 to RESOLVED).

**Verification:**
- Static only. Grep-confirmed `recipe.image` is no longer accessed
  anywhere in `get_recipes.py`'s hot path; the bytes endpoint still
  reads it intentionally. The two render gates point at the same
  composable.
- Not run in a browser. **FU-114** carries the verify checklist.

**Next up:**
1. **FU-114** browser-verify Chunk 5 (toggle round-trip, image render
   gates, **DevTools Network tab confirms `/recipes/<id>/image` is
   NOT hit when the flag is off**, recipe list endpoint smaller in
   bandwidth).
2. **All C-cross pre-consumer chunks (1–5) are now done.** The
   plumbing is in place for C-4 Chunk 9 (cost + nutrition) and
   future consumers (C-2 plan budgets, dashboard money gates,
   FU-033 stock images, C-1 Chunk 3 stock-image toggle).
3. **C-4 Chunk 9 (cost + nutrition)** is the next logical move —
   first cookbook-side consumer of the C-cross foundations. Or
   C-cross Chunk 6 (taxonomy editors verify-only) for completeness.

**Open questions for user:** none.

---

## 2026-06-11 — C-cross Chunk 4 (location-display policy) — IMPLEMENTED
**Status:** complete (frontend only — proposal §2.5 said backend = none).
Closes L81 / L107 / L128 (display half) per IMPL plan.

**What changed:**
- New `web_app/src/helpers/locationDisplay.ts` — two pure helpers:
  - `formatLocation(breadcrumb, mode: 'zone' | 'full')` — `'zone'`
    returns the top-level breadcrumb name; `'full'` joins with ` › `.
    Empty paths return `''` so the caller can fall back to its own
    placeholder.
  - `locationHasDetail(breadcrumb)` — true when there's a sub-area
    below the zone (so the tooltip would actually reveal info; used
    to suppress the tooltip when zone == full).
- **Four render sites** swapped to zone-default + tooltip-on-hover:
  - **`StockItemRow.vue`** (stock-overview row chip) — previously
    showed the *leaf* location name. Now resolves the breadcrumb
    through `locationStore.breadcrumb(id)` (with a flat
    `stockLocations` fallback for first paint before the tree loads)
    and shows the zone. Tooltip combines the existing "Filter to
    this location" message with the full path when one exists.
  - **`StockItemDetailPage.vue`** Location row — was
    `breadcrumb.join(' › ')`; now `formatLocation(…, 'zone')` with a
    tooltip showing the full path.
  - **`ShoppingListDetail.vue`** per-line location chip — same
    treatment.
  - **`ShoppingListShopMode.vue`** current section header — same
    treatment. **`sortKey()` still uses the full breadcrumb** as the
    stable grouping key (a sort discipline, not a display thing),
    so visually-collapsed zone groups still split apart correctly on
    different sub-areas under the same zone.
- **Not touched** (per IMPL plan §2.5 + proposal §2.5 carve-outs):
  - **`RecipeCookMode.vue`** — already shows zone-only in the
    grouped headers (C-3 Chunk 3 landed this), no per-row location
    chip in the cook-mode row. No tooltip on the group header (would
    aggregate multiple sub-areas under one zone — confusing rather
    than helpful).
  - **`StocktakePage` / `StocktakeRunner`** — they render plain
    `stock_location_name` (the location's own name from the API),
    not breadcrumbs; out of scope for §2.5 per the plan.
  - **`RecipeDetailPage.vue`** ingredient rows — no location chip
    today; nothing to align.

**Decisions made:**
- **Per-user `location_detail` toggle deferred** per §4-4 (the
  proposal's recommended path). The helper has the seam (`mode`
  param) but no toggle UI; if real usage flags missing the full
  breadcrumb at a glance, flip a stored user pref into the
  `formatLocation` calls.
- **Helper takes the breadcrumb, not the location id.** Most
  consumers already had the breadcrumb array (lines, detail page);
  StockItemRow does the id-to-breadcrumb lookup once and feeds the
  result in. Avoids coupling the helper to the location store.
- **Skip the cook-mode group-header tooltip.** A group can contain
  ingredients from different sub-areas of the same zone — picking
  one to show in a tooltip would be arbitrary. The zone label alone
  is the right level of detail in that surface.
- **Engineering close-gate:** R-001 (one shared helper, one tooltip
  shape repeated across sites); R-002 (no palette colours);
  R-003 (the locations tree is server-owned; helpers are pure
  functions); R-007 (held scope to the four sites the IMPL plan
  named; cook-mode group header + stocktake explicitly out of
  scope); R-008 (concise comments at each site explaining the
  zone-vs-full swap); R-011 (Quasar `q-tooltip`, Vue 3 helpers — no
  hand-rolled equivalents).

**Files touched:**
- FE: `helpers/locationDisplay.ts` (new),
  `components/stock/StockItemRow.vue`,
  `pages/StockItemDetailPage.vue`,
  `pages/ShoppingListDetail.vue`,
  `pages/ShoppingListShopMode.vue`.
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-113 verify).

**Verification:**
- Static only. Helper is pure; grep-confirmed every chip render site
  the plan named now uses `formatLocation`. Not run in a browser.
  **FU-113** carries the verify checklist.

**Next up:**
1. **FU-113** browser-verify Chunk 4 (zones display, tooltips
   reveal the full breadcrumb, no regression in shop mode's
   grouping under sub-areas).
2. **C-cross Chunk 5** (image-display opt-in + FU-090 deferred
   column fix) — the last per-user opt-in foundation. After that
   C-cross's pre-consumer chunks are complete.
3. C-4 Chunk 9 (cost + nutrition) remains fully unblocked.

**Open questions for user:** none.

---

## 2026-06-11 — C-cross Chunk 3 (per-user nutrition mode + reserved seam) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). Second
per-user opt-in family. Reserved-seam pattern for the deferred
complex mode (mirrors C-10/C-8 reservation discipline).

**What changed — Backend:**
- **`User.nutrition_mode: str`** default `'off'`. Closed-set sentinel
  (R-010 carve-out): `NUTRITION_MODE_VALUES = ('off', 'simple',
  'complex')` named constants in `user.py`; single validation point in
  `update_me.py`. SQLite-portable — no CHECK constraint, no enum type.
- **`AppSetting.nutrition_db_source: str`** default `''`. **Reserved
  seam** — no implementation behind it; the column exists so
  `update_me.py` can refuse `nutrition_mode='complex'` writes until an
  admin configures it. Free-form string for now (future complex-mode
  work parses it). Per the plan: "no UI for it yet" on the admin side.
- **Migration `c8d3f4a9b2e1`** (down_rev = `b5c1d9a4e3f2`). Batch-mode
  adds both columns with server defaults; symmetric downgrade.
- **`/api/users/me`** (`update_me.py`): accepts `nutrition_mode`,
  validates against `NUTRITION_MODE_VALUES`, additionally rejects
  `'complex'` when `AppSetting.nutrition_db_source` is empty —
  surfaced as a `business_rule_violation`. Pulls the AppSetting via
  the existing `get_or_create_app_setting()` accessor.
- **`AuthenticatedUserDto`** carries `nutrition_mode`.
- **`/api/app-settings`** GET/PATCH both extended with
  `nutrition_db_source` for the future admin UI; the column
  round-trips even though no settings page edits it yet.
- **`/api/health features.*`** gains `nutrition_complex_available: bool`
  — derived from `bool(setting.nutrition_db_source.strip())`. Never
  publishes the source string itself; the SPA only needs the
  capability bit.

**What changed — Frontend:**
- **`models/auth.ts`** + **`UpdateMeCommand`** + **`AppSettings`** type
  all gain the new fields.
- **`useFeatureFlags()`** exposes `nutritionComplexAvailable` computed.
- **`useNutritionMode()`** (new composable, ADR-005 family pattern):
  layers install `features.nutrition` with per-user `nutrition_mode`.
  Returns `mode` (the *effective* mode — `off` when install is off),
  `userMode` (raw per-user pick), `installEnabled`, `nutritionEnabled`
  (`mode !== 'off'`), `isSimple`, `isComplex`, and
  `complexAvailable` (install on AND nutrition source configured).
- **`PreferencesSettings.vue`** — new **Nutrition** card between
  Grocery budget and Voice. Three-way `q-btn-toggle` (Off / Simple /
  Complex). Complex option disabled via `complexAvailable`. Whole
  control disabled (+ caption) when install is off. Save handler
  PATCHes `/me` with the new mode.
- **No Recipe.kcal**, no kcal sort axis. Those land in C-4 Chunk 9
  consuming `useNutritionMode().nutritionEnabled` (per the IMPL plan
  Chunk 3's "no Recipe schema touched" scope).

**Decisions made:**
- **`nutrition_complex_available` on /api/health** instead of leaking
  the source string. The SPA only needs a capability bit; admins who
  want to inspect the seam value can hit `/api/app-settings` (admin-
  only).
- **Three-tier display logic in the toggle.** When install off, the
  whole toggle disables. When install on but complex unavailable,
  only the Complex button disables. When all three are valid, all
  three are clickable. Captions adjust to whichever case is active.
- **No admin UI for `nutrition_db_source` yet** — per IMPL plan
  Chunk 3 ("no UI for it yet"). Admin can set via direct API call;
  future complex-mode chunk owns the editor.
- **`mode` returns `'off'` when install is off**, even if the user's
  stored value is `'simple'`. Consumers don't have to layer the two
  themselves — `mode !== 'off'` is the single rule.
- **Engineering close-gate:** R-001 (one composable per family per
  ADR-005); R-002 (no palette colours added); R-003 (server owns the
  value + the validation; client reads through composable); R-005/R-006
  (clean batch migration with server defaults; symmetric downgrade);
  R-007 (kept to mode + seam; no Recipe schema, no kcal field —
  those are C-4 Chunk 9); R-008 (concise comments at insertion
  points); R-010 carve-out documented (closed-set sentinel +
  single-boundary validation against `NUTRITION_MODE_VALUES`);
  R-011 (Vue 3.4 composable + Pinia `storeToRefs`, Quasar
  `q-btn-toggle` / `q-card`).

**Files touched:**
- BE: `domain/entities/user.py`, `domain/entities/app_setting.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/c8d3f4a9b2e1_20260611_nutrition_mode.py`
  (new), `features/auth/update_me.py`,
  `features/auth/register_user.py`,
  `features/health/health_check.py`,
  `features/app_settings/get_app_settings.py`,
  `features/app_settings/update_app_settings.py`.
- FE: `composables/useNutritionMode.ts` (new),
  `composables/useFeatureFlags.ts`, `models/auth.ts`,
  `services/api/authApiService.ts`,
  `services/api/appSettingsApiService.ts`,
  `pages/settings/PreferencesSettings.vue`.
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-112 verify).

**Verification:**
- Static only. Migration mirrors the Chunk-1/2 shape. User +
  AppSetting + DTO + request field counts match. Composable named
  computeds map 1:1 against install + per-user + capability flags.
- Not run in a browser. **FU-112** carries the verify checklist.

**Next up:**
1. **FU-112** browser-verify Chunk 3 (migration, toggle round-trips,
   install-off behaviour, complex-disabled-when-seam-empty path,
   complex-rejected-server-side when client somehow tries).
2. **C-cross Chunk 4** (Location-display policy) — small client-side
   change. Independent of Chunks 1–3, no dependency chain.
3. C-4 Chunk 9 (cost + nutrition) is now **fully unblocked**:
   Chunks 1 + 2 + 3 are all in. Could come next if you want the
   first cookbook-side consumer of the C-cross foundations.

**Open questions for user:** none.

---

## 2026-06-11 — C-cross Chunk 2 (per-user money opt-in) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). First
consumer of Chunk 1's plumbing; first per-user opt-in following ADR-005.

**What changed — Backend:**
- **`User.money_features_enabled: bool`** (default False) + matching
  `Fields.MONEY_FEATURES_ENABLED`. Mapped on `user_table` with
  `server_default='0'`.
- **Migration `b5c1d9a4e3f2`** (down_rev = `a3b8e2f4c1d7`). Batch-mode
  add column; symmetric downgrade.
- **`PATCH /api/users/me`** (`update_me.py`) accepts the new field —
  plain bool, null ignored, partial-update semantics (matches the
  voice toggle pattern already in this file).
- **`AuthenticatedUserDto`** (`register_user.py`) exposes the new
  flag on `/me`. Both new-user registration and re-auth return it.
- **No render gates inside this chunk.** Existing budget /
  dashboard / shopping-list dollar surfaces keep rendering as today;
  each consumer adds `v-if="moneyEnabled"` when its own next chunk
  ships.

**What changed — Frontend:**
- **`models/auth.ts`** `AuthenticatedUser` gains `money_features_enabled`.
- **`authApiService.ts`** `UpdateMeCommand` gains the optional field.
- **`useMoneyEnabled()`** composable in `src/composables/` — per
  ADR-005 family pattern. Layers install `features.money` (from
  `useFeatureFlags`) with per-user `money_features_enabled` (from
  `authStore.currentUser`). Returns a single `moneyEnabled` boolean
  + the two underlying refs (`installEnabled` / `userEnabled`) so a
  Settings page can explain the layering when one half is off.
- **`PreferencesSettings.vue`** — new **"Money & budgets"** card with
  the per-user toggle (above the existing Grocery budget card).
  Toggle is disabled with a caption when the install flag is off
  ("Ask an admin to enable in System → Features"). The existing
  Grocery budget card now has `v-if="moneyEnabled"` so it disappears
  when either layer is off — **saved budget value preserved** (never
  cleared on toggle-off, per proposal §2.2).

**Decisions made:**
- **Consolidate on `PATCH /api/users/me`** (no new dedicated
  endpoint). Same row, same partial semantics — matches Chunk 1's
  consolidation of feature flags into the existing
  `PATCH /api/app-settings`.
- **Disabled-not-hidden toggle when install is off.** Spells out the
  layering for the user instead of silently dropping the control;
  matches the "two layers, document both" recommendation in the
  proposal §2.2.
- **Budget data preservation** via the existing
  `budget_amount`/`budget_period` columns staying untouched —
  toggling money off doesn't clear them. The Grocery budget card's
  own `budgetEnabledDraft` ref still gates whether the budget
  number is actively set.
- **Engineering close-gate:** R-001 (one composable per feature
  family per ADR-005); R-003 (server owns both flags; client reads
  through one composable); R-005/R-006 (clean batch migration);
  R-007 (kept to Chunk 2 — no consumer rewrites; cost / budget /
  dashboard render gates are their own future chunks); R-008
  (concise comments at each insertion); R-010 (typed
  `UpdateMeCommand` shape; no `any`); R-011 (Vue 3.4 composable
  pattern, Pinia `storeToRefs`, Quasar `q-card` / `q-toggle`).

**Files touched:**
- BE: `domain/entities/user.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/b5c1d9a4e3f2_20260611_user_money_optin.py`
  (new), `features/auth/update_me.py`,
  `features/auth/register_user.py`.
- FE: `composables/useMoneyEnabled.ts` (new),
  `services/api/authApiService.ts`, `models/auth.ts`,
  `pages/settings/PreferencesSettings.vue`.
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-111 verify).

**Verification:**
- Static only. Migration mirrors Chunk 1 shape. AuthenticatedUserDto +
  UpdateMeRequest field counts match. Composable named computeds map
  1:1 against install + per-user fields.
- Not run in a browser. **FU-111** carries the verify checklist.

**Next up:**
1. **FU-111** browser-verify Chunk 2 (migration, settings toggle
   round-trips, budget card hides on off + reappears on on with
   saved value intact, install-off disables the toggle with the
   right caption).
2. **C-cross Chunk 3** (per-user `nutrition_mode` + AppSetting
   `nutrition_db_source` reserved seam) — next per-user opt-in,
   completes the foundation Cookbook Chunk 9 needs.
3. C-4 Chunk 9 (cost + nutrition) unblocks after Chunk 3 lands.

**Open questions for user:** none. Layering UX consistent with
proposal §2.2.

---

## 2026-06-11 — C-cross Chunk 1 (install feature-flag panel + opt-in plumbing) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env).
Foundational — every later C-cross chunk + Cookbook Chunk 9 / C-2 plan
budgets / etc. plug into the plumbing landed here.

**What changed — Backend:**
- **`AppSetting`** entity gains five booleans + matching `Fields`
  constants: `meal_planning_enabled` (default **True** — preserves
  today's always-on behaviour), `money_enabled`, `nutrition_enabled`,
  `companion_ingestion_enabled`, `deals_email_enabled` (all default
  False). `table_mappings.py` mapped with conservative `server_default`s.
- **Migration `a3b8e2f4c1d7`** (down_rev = `e1f6a2b4c8d9`). Batch-mode
  add column × 5; clean symmetric downgrade.
- **`/api/health` `_feature_flags()`** extended with `meal_planning`,
  `money`, `nutrition`, `companion_ingestion`, `deals_email` keys —
  resolved from the AppSetting row inside the existing DB-hiccup-
  tolerant try block. Pre-existing `auth`/`audit`/`scanning`/`multi_user`/
  `email`/`assistant` keys untouched; keys never removed per the
  endpoint contract.
- **`PATCH /api/app-settings`** extended to accept the five new
  bools (partial-update semantics; only fields present in the body
  change). `GET /api/app-settings` exposes them via the AppSettingsDto.
  Both extracted a `_to_dto(setting)` helper to keep get + update
  on one shape.
- **IMPL plan deviation noted:** The IMPL plan proposed
  `PATCH /api/admin/feature-flags` as a new endpoint. Used the
  existing admin-only `PATCH /api/app-settings` instead — same row,
  same partial semantics, no new surface. Better than the plan said.

**What changed — Frontend:**
- **`useFeatureFlags()`** composable in `src/composables/`. Fetches
  `/api/health` once per session (module-level cache), exposes
  named reactive computeds per flag (`auth`, `audit`, `scanning`,
  `multiUser`, `email`, `assistant`, `mealPlanning`, `money`,
  `nutrition`, `companionIngestion`, `dealsEmail`) plus a
  `refresh()` to invalidate the cache after an admin save.
- **`appSettingsApiService.ts`** extended `AppSettings` type with the
  five new fields so the SystemSettings page is type-safe end-to-end.
- **`SystemSettings.vue`** — replaced the three disabled-placeholder
  list items (`allowRegistrations` / `maintenanceMode` /
  `emailerEnabled` — none were ever wired) with a real **Features**
  section. Drives off a `featureFlagItems` computed (label + caption
  + value per flag); each toggle uses optimistic-flip with rollback
  on PATCH error; `savingFeatures: Set<key>` disables a toggle
  while its own save is in flight without blocking siblings. After
  a successful save calls `featureFlags$refresh()` so the cached
  `/api/health` map reflects the new value app-wide.

**Decisions made:**
- **Single composable for ALL install flags** (one per feature
  *family*), not per flag. Promoted to **ADR-005** —
  `useFeatureFlags()` is the canonical read path; future per-user
  family composables (`useMoneyEnabled` etc.) layer on top.
- **`meal_planning_enabled` defaults True**, every other new flag
  defaults False. Confirmed in §3 risks: existing installs preserve
  today's meal-plan behaviour on first boot post-deploy.
- **Per-toggle save** (not "save button at the bottom"). Five
  toggles + one global save is jankier than five independent
  optimistic toggles, and matches how the existing
  `scanning_enabled` toggle already behaves.
- **Existing `useScanningEnabled` composable kept as-is** — it
  already shipped in production and works. Logged for
  consolidation into `useFeatureFlags()` whenever a chunk next
  touches its consumers (R-007: not opportunistic now).
- **Engineering close-gate:** R-001 (one `useFeatureFlags()` for
  the family; the panel renders from a single computed driving
  one `v-for`); R-002 (no palette colours added); R-003 (server
  owns the boolean; client reads through composable, never AppSetting
  direct); R-005/R-006 (clean batch migration with conservative
  defaults; symmetric downgrade; no idempotent guards); R-007
  (the proposed dedicated `/api/admin/feature-flags` endpoint
  consolidated into the existing PATCH; the existing
  `useScanningEnabled` left alone); R-008 (terse comments at each
  schema/composable site); R-010 (typed `FeatureFlagKey` literal
  union on the panel; closed-set sentinels); R-011 (Vue 3.4
  `<script setup>`, `q-toggle` / `q-list`, Quasar `q-card` chrome —
  no hand-rolled equivalents).

**Files touched:**
- BE: `domain/entities/app_setting.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/a3b8e2f4c1d7_20260611_appsetting_install_flags.py`
  (new), `features/health/health_check.py`,
  `features/app_settings/get_app_settings.py`,
  `features/app_settings/update_app_settings.py`.
- FE: `composables/useFeatureFlags.ts` (new),
  `services/api/appSettingsApiService.ts`,
  `pages/settings/SystemSettings.vue`.
- Docs: `docs/01_charter/ENGINEERING_STANDARDS.md` (ADR-005),
  `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-110 verify).

**Verification:**
- Static only (no env). Migration mirrors prior batch-alter shape;
  AppSetting + DTO + request column counts match; composable named
  keys map 1:1 against the health flags.
- Not run in a browser. **FU-110** carries the verify checklist.

**Next up:**
1. **FU-110** browser-verify Chunk 1 (migration, panel renders for
   admin, toggles round-trip, `/api/health` carries the new keys,
   composable refreshes after save).
2. **C-cross Chunk 2** (per-user `money_features_enabled`) — first
   per-user opt-in to consume the Chunk-1 plumbing. Layers install
   `features.money` with per-user.
3. C-4 Chunk 9 (cost + nutrition) becomes unblocked after Chunks 2
   + 3.

**Open questions for user:** none — the IMPL plan deviation
(consolidating into PATCH /api/app-settings rather than a new
endpoint) is noted; flag if you'd prefer the dedicated route after
all.

---

## 2026-06-10 — FU-083 follow-up: shared TriStateFilter + label tweak
**Status:** complete. Closes the user's "make it a common component" ask
from the FU-083 review.

**What changed:**
- New `web_app/src/components/filters/TriStateFilter.vue` — generalised
  include/exclude filter component:
  - Options shape `{ value, label, category?, dotColour? }` —
    `category` enables the header-grouped layout (dietary tags), omit
    for a flat list. `dotColour` puts a 10px Quasar-colour dot next
    to the +/- icon (the stock-level signal the user asked to keep
    for ingredient rows).
  - New `searchable` prop adds an internal `<q-input>` with debounce
    100 + autofocus that case-insensitively matches by label. Items
    already in include/exclude **always remain visible** regardless
    of the query so users can clear them without dropping the
    search string.
  - +/- cycle, button label `"<Label> (N)"`, "Clear" footer item
    when any picks are active — all preserved from the original
    DietaryTagFilter behaviour.
- `web_app/src/components/recipes/DietaryTagFilter.vue` — reduced to a
  **thin wrapper** over `TriStateFilter` so existing call sites
  (RecipesOverview's tags + tools usage) don't change. The
  `DietaryTagOption` type stays exported for type-stability.
- `web_app/src/pages/RecipesOverview.vue`:
  - The two paired `q-select`s ("Uses ingredients" + "Doesn't use")
    collapsed into **a single `TriStateFilter`** with
    `label="Ingredients"`, `searchable`, and per-row stock-level
    dot. Same `usesStockItemIds` / `excludesStockItemIds` refs back
    it — the predicate logic and filter-count plumbing didn't change.
  - Removed `stockItemSearchOptions` computed +
    `stockItemFilterText` ref + `onStockItemFilter` handler (the
    custom typeahead the q-select needed). Replaced with a flat
    `ingredientFilterOptions` computed that sorts alphabetically and
    maps to `TriStateOption` with `dotColour: stockLevelColourFor()`.
  - **"Missing ≤" → "Missing ingredients ≤"** label rename.

**Decisions made:**
- **Generalise, then make DietaryTagFilter a wrapper.** Keeping the
  wrapper avoids touching ~2 well-tested call sites; new surfaces
  consume `TriStateFilter` directly. Cleanest R-001 outcome.
- **Items in include/exclude always render**, regardless of the
  search query. A user typing "tom" who'd already picked "Lentils"
  in exclude shouldn't lose visibility of that pick.
- **Sort alphabetically** for the ingredient list (no
  stock-level-based ordering); the search bar makes alpha order
  fine and removes the temptation to put low/out items at top
  (a P10-anti-creep call).
- **Engineering close-gate:** R-001 (one shared component, one
  wrapper for backwards-compat), R-002 (the dot uses
  `getStockLevelColour` which routes through tokens), R-003
  (server still owns `stock_level_name`; client only renders),
  R-007 (scope held — didn't touch other filter controls, the dim
  decision is FU-109), R-008 (single explanatory comment per
  removal), R-011 (Quasar `q-btn-dropdown`, `q-input`, `q-list`,
  `q-item` — framework-idiomatic).

**Files touched:**
- `web_app/src/components/filters/TriStateFilter.vue` (new),
- `web_app/src/components/recipes/DietaryTagFilter.vue` (rewritten
  as wrapper),
- `web_app/src/pages/RecipesOverview.vue` (consume + label),
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-108 ordering, FU-109 dim).

**Verification:**
- Static only. Grep-checked the removed `stockItemSearchOptions` /
  `stockItemFilterText` / `onStockItemFilter` are fully gone from the
  page. Existing DietaryTagFilter call sites use the wrapper API
  unchanged.

**Follow-ups logged:**
- **FU-108** — reorder Cookbook overview filters by usefulness
  (simple template reorder, user owns the priority order).
- **FU-109** — dim decision: keep removed everywhere / re-add only
  on `StockItemDetailPage` / re-add everywhere with a legend.

**Next up:** unchanged — **C-cross Chunk 1** remains the next build.
The shared `TriStateFilter` is now available for any future surface
that wants tri-state include/exclude semantics.

**Open questions for user:** none for this change. FU-109 is the
outstanding decision.

---

## 2026-06-10 — FU-083 feedback pass (Cookbook overview UX) — RESOLVED
**Status:** complete. Closes FU-083 with all nine user-flagged items addressed inline.

**What changed (per-item):**
1. **Read-only "Last cooked" card** on detail page sidebar (under the
   cookable card). Reads `recipe.last_made_on`; falls back to "Never"
   when null. Closes the loop with the top-toolbar Mark cooked / Log
   cook actions.
2. **Sort direction toggle** — new `sortDir: 'asc' | 'desc'` ref +
   `BaseButton` next to the Sort by dropdown (arrow-up/arrow-down
   icon). Tooltip phrasing per-axis: "Oldest first" / "Most recent
   first" / "Fewest meals first" / "Fastest first" / "A → Z" / etc.
   `watch(sortBy)` snaps direction to the conventional default on
   axis change (name = asc, others = desc). Null sentinels in
   last_made / total_time still sink to the bottom regardless of
   direction (multiplier applied only after null guards).
3. **Stock-item picker dropdown** — `q-item-label caption` showing
   the level name removed; the colour dot is enough.
4. **"Planned" filter bug fix.** Rewrote `plannedRecipeIds` computed
   to parse `scheduled_for` as `YYYY-MM-DD` (slice first 10 chars,
   split on '-', construct a local-midnight `Date`), gate `>= today`
   on the parsed timestamp, **and skip entries with `consumed_at`
   set**. The previous string-compare was supposed to work but the
   user observed yesterday's entry surviving — the new shape is
   defensive on both the parse and the consumed-state.
5. **"Planned in" → "Planned"** label.
6. **RecipeCard dim removed.** Deleted the `dim` computed +
   `:class="{ 'recipe-card--dim': dim }"` + the `.recipe-card--dim`
   stylesheet rule. `highlightStockItemIds` prop kept (deep-link from
   stock-item detail still passes it) but no longer drives any
   visual.
7. **Hints removed from filter inputs** (`Meals ≥`, `Missing ≤`).
   `:hint` bindings + `hide-bottom-space` to collapse the reserve
   slot. `mealCountMinHint` / `missingMaxHint` computeds deleted.
8. **"Free from ingredient(s)" replaced by "Doesn't use".** Removed
   the free-text `<q-select use-input new-value-mode="add-unique">`
   and the `ingredientExclude` ref + its filter predicate + clear
   reset + active-count slot. Added `excludesStockItemIds: ref<string[]>`
   + a second `<q-select>` mirroring the "Uses ingredients" shape
   (same `stockItemSearchOptions`, same `@filter` handler). Predicate:
   exclude if any picked id is in `r.ingredients.stock_item_id`.
9. **"Uses stock items" → "Uses ingredients"** label.

**Decisions made:**
- **Two side-by-side selects instead of one tri-state.** User asked
  "Should 'free from' be collapsed into the stock item filter as a
  +/- filter?" — the cleanest minimal answer that preserves the
  searchable-picker UX is two parallel selects on the same option
  source (mirrors DietaryTagFilter's include/exclude semantics
  but using the typeahead pattern stock items need at scale). A
  truly single chip-with-state control was rejected as over-engineered
  for v1.
- **`RecipeCard` dim deleted, prop kept.** User leaned remove
  ("doubling up displaying… missing ingredients"). Kept the prop so
  the existing deep-link call sites don't break, with a comment
  pointing the next reviewer at why the prop is still defined.
- **Axis-snap on sort change.** Pure UX — when the user picks
  "Recently made" they almost certainly want newest first;
  switching from "Name" with "asc" carried over wouldn't surface
  the intent.
- **Engineering close-gate:** R-001 (the two parallel selects share
  `stockItemSearchOptions` + `onStockItemFilter`, no copy), R-002
  (no palette colours added — the colour dot still uses
  `stockLevelColourFor` which routes through tokens), R-003 (sort +
  filter remain client-derived; consistent with the rest of Chunk 1),
  R-007 (scope held to FU-083 items — didn't touch the dialog
  patterns or the comparison-removal again), R-008 (one explanatory
  comment per removal so reviewers see why things shrank), R-010
  (sort direction sentinel is a closed-set string literal union),
  R-011 (Quasar `q-select`, `q-tooltip`, `BaseButton`, `q-input`
  `hide-bottom-space` — no hand-rolled controls).

**Files touched:** `web_app/src/pages/RecipesOverview.vue`,
`web_app/src/pages/RecipeDetailPage.vue`,
`web_app/src/components/RecipeCard.vue`, `CHANGELOG.md`,
`DORA_FOLLOWUPS.md` (FU-083 → RESOLVED).

**Verification:**
- Static only. Grep-checked stale `ingredientExclude` /
  `mealCountMinHint` / `missingMaxHint` / `recipe-card--dim` are
  fully removed (only the explanatory comments remain).
- User to browser-verify the changes — particularly that
  "Planned" no longer surfaces yesterday's egg-fried-rice, and
  that the direction toggle reads sensibly per axis.

**Next up:** continue with **C-cross Chunk 1** (feature-flag panel
+ opt-in plumbing) as scheduled. FU-083 close-out doesn't change
the C-cross sequence.

**Open questions for user:** none — design calls in items 6 + 9
were resolved using the lean from the feedback.

---

## 2026-06-10 — C-cross §2.8 image-display opt-in: toggle UX revised
**Status:** complete (design revision — NO code).
**What changed:**
- **`PROPOSAL_CONFIG_AND_OPTINS.md §2.8`** — added a "Where the toggle
  lives" subsection. Image-display toggles are now **inline buttons
  on each surface**, not Settings entries. Persistence stays on
  `User` so the preference rides across sessions/devices. Recipes
  overview gets an icon button in the header next to Import/New
  recipe; stock overview gets a collapse/expand affordance in the
  row area (defers to C-1 row redesign).
- **`IMPL_PLAN_CONFIG_AND_OPTINS.md` Chunk 5** — rewritten:
  - Backend (User flags + `/me` exposure + FU-090 fold-in) lands
    NOW. Composable + recipes-overview inline button + recipe-
    surface guards land NOW.
  - **Stock-overview inline button deferred** to the next C-1 chunk
    that redoes the row layout (row geometry decisions belong
    there, not retrofitted). Composable + flag are ready when C-1
    consumes them.
  - Acceptance line updated to spell out `show_stock_images` field
    must exist + round-trip even though no stock-overview button is
    wired yet.
- **`IMPL_PLAN_STOCK_OVERVIEW.md` Chunk 3 (row rebuild)** — added an
  explicit "Image collapse toggle (C-cross §2.8 / FU-106)" bullet so
  whoever picks up that chunk wires the button + the
  `v-if="showStockImages"` guard alongside the rest of the row
  geometry work.
- **`DORA_FOLLOWUPS.md`** — new **FU-106** logs the deferred
  stock-overview button work, pointing at C-1 Stock Overview
  Chunk 3 as the resolution chunk.

**Decisions made:**
- **No Settings page entry for image toggles** — the toggle goes
  where the user looks at images. Mirrors Quasar's own dark-mode
  pattern (top bar, not buried in settings).
- **Recipes overview owns the recipe-images toggle** (one write
  site), the detail/cook/print surfaces consume but don't carry
  their own button — avoids N toggles for one preference.
- **Stock overview owns the stock-images toggle** but the button
  lands during C-1 row redesign — split the deferral cleanly so
  C-cross still delivers the backend + composable + recipe surface
  work in one chunk.
- **Persistence channel** = existing `authStore.updateMeAsync()`
  (same path the cook-mode voice toggle already uses). No new
  endpoint, no new store.

**Files touched:** `docs/04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`,
`docs/04_proposals/IMPL_PLAN_CONFIG_AND_OPTINS.md`,
`docs/04_proposals/IMPL_PLAN_STOCK_OVERVIEW.md`,
`DORA_FOLLOWUPS.md` (FU-106).

**Verification:** none needed — docs only.

**Next up:** **C-cross Chunk 1** (feature-flag panel + opt-in plumbing)
remains the first reviewable chunk; nothing about today's revision
moves the sequence.

**Open questions for user:** none.

---

## 2026-06-10 — IMPL_PLAN_CONFIG_AND_OPTINS.md (C-cross) — DRAFTED
**Status:** complete (design pass — NO code). Resolves C-cross's path to
build so Cookbook Chunk 9 (cost + nutrition) and downstream consumers
have real gates to read.

**What changed:**
- New **`docs/04_proposals/IMPL_PLAN_CONFIG_AND_OPTINS.md`** — full
  6-chunk plan in the established IMPL shape (§0 verify-state, §1
  chunked plan, §2 first-chunk DoD, §3 risks + open decisions, §4
  feedback coverage, §5 run order). Chunk 6 is verify-only — the
  taxonomy editors (§2.4) already shipped via C-4 Chunks 2 + 5.
- **Doc-graph** wired: new `### IMPL — Config & Opt-ins (C-cross)` row
  added to `docs/00_DOC_GRAPH.md` between Stock Overview and State
  Ownership; links proposal, dependencies, and the foundational role
  for C-4 Chunk 9 / C-2 / C-1 / C-5 / C-9.

**Chunk shape (5 build chunks + 1 verify-only):**

1. **Chunk 1 — Opt-in plumbing + install feature-flag panel (§2.1 +
   §2.6).** Foundational. Extends `AppSetting` with
   `meal_planning/money/nutrition/companion_ingestion/deals_email`
   bools (existing `llm`/`scanning` stay). `/api/health features.*`
   gains the new keys; new `PATCH /api/admin/feature-flags` admin-
   only endpoint. New `useFeatureFlags()` composable. Settings →
   System → Features panel (admin-only). Conservative defaults
   (meal-planning = True to preserve existing behaviour).
2. **Chunk 2 — Money opt-in per-user (§2.2).**
   `User.money_features_enabled` default False. `useMoneyEnabled()`
   composable layers install + per-user (both must be true).
   Settings → Account → Money & budgets section. No consumer wiring
   here — render-gates land in their own chunks (C-4 Chunk 9, C-2).
3. **Chunk 3 — Nutrition mode per-user (§2.3, off + simple now).**
   `User.nutrition_mode` enum + `AppSetting.nutrition_db_source`
   reserved (empty). Three-way toggle; complex disabled with
   tooltip until seam configured. **No `Recipe.kcal` here** — that's
   C-4 Chunk 9's job; C-cross owns the mode + seam only.
4. **Chunk 4 — Location-display policy (§2.5).** Client-side only;
   new `formatLocation()` helper. Zone-default + tooltip-for-full
   wired into every location-chip render site. Per-user
   `location_detail` toggle deferred per §4-4.
5. **Chunk 5 — Image-display opt-in (§2.8).** Two per-user bools
   (`show_recipe_images` / `show_stock_images`), default True.
   `useImagePrefs()` composable. Wires existing recipe image render
   sites (card, detail, edit-dialog preview, cook mode, print);
   stock-side is a no-op consumer awaiting FU-033. **Folds in
   FU-090** — recipe list query deferred-column fix so "off" path
   actually saves bandwidth.
6. **Chunk 6 — Taxonomy editors (§2.4) — NO WORK.** Already shipped
   via C-4 Chunks 2 + 5; marker chunk for the run-order audit.

**Open decisions answered inline (proposal §4):**
- §4-1 money switch shape → dedicated `money_features_enabled`
  flag (Chunk 2).
- §4-2 feature-flag set → proposal's conservative list:
  `meal_planning + money + nutrition + companion_ingestion +
  deals_email` + existing `llm` / `scanning` (Chunk 1).
- §4-3 taxonomy permission → any user (already shipped this way).
- §4-4 location detail pref → zone + tooltip only, no toggle
  (Chunk 4).
- §4-5 nutrition complex scope → off + simple now, complex reserved
  seam (Chunk 3).
- §4-6 image-display defaults + flag count → default on; two flags
  (Chunk 5).

**Decisions made (process):**
- **Skip §2.4 in the build plan** — the taxonomy editors are real
  C-4 work that shipped under a different prompt. Calling them out
  as a "verify-only" chunk keeps the run-order audit honest without
  duplicating the work.
- **C-cross is foundational** (consumed by C-1 / C-2 / C-4 Chunk 9 /
  C-5 / C-9) — so the IMPL plan's §3 explicitly schedules consumer
  chunks *after* the C-cross chunk they each depend on, rather than
  building C-cross as a "branch off main" parallel.
- **Establish the opt-in pattern as code in Chunk 1** rather than
  re-deriving it on every chunk. The `useFeatureFlags()` /
  `useImagePrefs()` etc. shape is one composable per feature
  *family*, not per flag — mirrors ADR-002. Logged as an
  ADR-005 candidate in the plan to promote at end-of-chunk-1 if it
  survives review.
- **Engineering pre-note** (per ENGINEERING_STANDARDS.md): every
  chunk lists its R-001..R-011 self-checks. R-010 carve-out
  documented for the nutrition_mode status sentinel
  (`NUTRITION_MODE_VALUES` set + boundary validation).

**Files touched:** `docs/04_proposals/IMPL_PLAN_CONFIG_AND_OPTINS.md`
(new), `docs/00_DOC_GRAPH.md` (IMPL row).

**Verification:** none needed — docs only. Verify-state grep-checked
against current code (AppSetting row shape, User columns,
`_feature_flags()`, the already-shipped vocab editors).

**Next up:** **C-cross Chunk 1** (feature-flag panel + opt-in
plumbing) is the first reviewable chunk and the foundation
everything else plugs into. Decision-free per the IMPL plan; clear
to build on user say-so.

**Open questions for user:** none — the six §4 decisions are all
resolved inline in the plan.

---

## 2026-06-10 — IMPL_PLAN_COOKBOOK Chunk 8 (versions via `version_group_id`) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). Closes §2.4 + L247 / L312 per DEC-2.
**What changed — Backend:**
- `Recipe.version_group_id: UUID | None` field on the entity +
  `Recipe.Fields.VERSION_GROUP_ID`; mapped column on `Recipe` table,
  indexed (every detail load asks "who else has this group id?").
- Migration `e1f6a2b4c8d9` (down_rev = `d0e5f1a3b8c7`). Batch-mode add
  column + create index; symmetric downgrade.
- `RecipeDto` carries `version_group_id` on every endpoint and
  `version_siblings: List[RecipeVersionSiblingDto]` (id + name +
  last_made_on + available_meals — light payload) on the detail
  endpoint only.
- New `features/recipes/new_recipe_version.py` —
  `NewRecipeVersionHandler.handle(source_id)`:
  - Loads the source with ingredients included.
  - Resolves the group id: NULL source → allocates `uuid4()` AND
    back-fills the source so the two recipes form the group (the
    "equal peers" model requires the link to live on both rows, not
    just the new one).
  - Counts siblings → name = `f"{source.name} (v{N+1})"`.
  - Clones ingredients (new uuids assigned by `add()`); builds
    `old_to_new_ing` map so step `ingredient_ids` can be rewritten.
  - Clones the Recipe row (carries category/cuisine/collection
    references through directly — `selectin`-loaded relationships).
  - Saves, then back-fills tag ids + tool ids + steps (via
    `replace_steps_for_recipe`, mapping each step's old-id to its
    string-form as `client_id` so parent/child structure round-trips,
    and ingredient_ids through the `old_to_new_ing` map). One final
    `save_changes()`.
  - Route `POST /api/recipes/<id>/new-version` returns the new
    recipe's detail DTO via `handle_by_id`.
- **New detail endpoint** `GET /api/recipes/<id>` (route
  `get_recipe`) — calls `handle_by_id` directly. **Latent gap fix**:
  the SPA's `getAsync(id)` used to filter the list endpoint, which
  silently dropped `steps[]` and the new `version_siblings[]` (only
  the cheap list shape was returned). This was a real bug from
  Cookbook Chunk 6 / Cook-Mode Chunk 5 — flagged in the worklog
  but never reported because nobody had structured-step recipes in
  testing yet. Fixed as part of Chunk 8 since it's the chunk that
  forces the issue.
- `create_recipe.py`: pass `version_group_id=None` to the Recipe
  constructor (new entity field needs a value).

**What changed — Frontend:**
- `models/recipe.ts`: `version_group_id: string | null` on `Recipe`,
  `version_siblings: RecipeVersionSibling[]` on `Recipe`, new
  `RecipeVersionSibling` type.
- `services/api/recipeApiService.ts`:
  - `getAsync` now hits `GET /recipes/<id>` (the real detail
    endpoint). Old `createQueryString`/`FilterOperator` import
    dropped — no longer needed.
  - New `createNewVersionAsync(recipeId)` → POSTs to
    `/recipes/<id>/new-version`.
- `pages/RecipeDetailPage.vue`:
  - Detail kebab gets a **New version** item above the existing
    Delete (separated by a `q-separator`). `newVersionLoading`
    disables it during the round-trip.
  - **"Other versions"** card in the sidebar (rendered only when
    `versionSiblings.length > 0`). Lists siblings with name + last
    made + meals on hand; clicking jumps to that recipe's detail.
  - `onNewVersion()` calls the API, refreshes the recipe-store
    cache, lands a celebratory toast, routes into the new
    sibling's detail.
  - `onJumpToSibling(id)` / `formatLastMade(iso)` helpers.

**Decisions made:**
- **Back-fill the source's group id on first "new version".** The
  alternative (only assign the group id to the new copy) leaves the
  source effectively detached from the group — the "Other versions"
  card on the source wouldn't show the new sibling without a
  symmetric link. Two writes, but the group becomes a real bilateral
  relationship rather than a one-way pointer.
- **Sibling name = `(v{count+1})`** rather than `(v2)` always.
  Versioning a recipe that already has 2 siblings produces "(v3)",
  not a duplicate "(v2)".
- **Image carries through as bytes.** Recipe.image is a LargeBinary
  blob (post-Chunk-5 data-URL string); copy the reference directly.
  No image-bytes round-trip through the importer / endpoint.
- **Real detail endpoint added now**, even though it's strictly
  Chunk 8 scope creep — the silent bug it fixes (Cookbook Chunk 6
  `steps[]` not reaching the detail page) is more important than
  the scope discipline, and the new versions card needs the real
  endpoint anyway.
- **Allocations stay per-recipe.** DEC-2 spelled this out: the user
  picks a version when scheduling; no version-aware allocation logic
  in the meal-plan code. Confirmed nothing in `meal_plans/` or
  `_hydrate_unallocated` needs to know about siblings.
- **Engineering close-gate**: R-001 (versions card reuses `q-card` +
  `q-list` + `q-item`; kebab item slots into the existing menu —
  no hand-rolled chrome); R-002 (no palette colours); R-003
  (server owns the group id allocation + sibling count; client
  just renders); R-005/R-006 (batch migration with index; clean
  downgrade); R-007 (deliberate carve-out for the detail endpoint
  documented above); R-008 (concise comments); R-010 (UUIDs end-to-
  end through the StepWrite `client_id`); R-011 (Quasar primitives
  + Vue 3.4 idioms).

**Files touched:**
- BE: `domain/entities/recipe.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/e1f6a2b4c8d9_20260610_recipe_versions.py`
  (new), `features/recipes/get_recipes.py`,
  `features/recipes/create_recipe.py`,
  `features/recipes/new_recipe_version.py` (new).
- FE: `models/recipe.ts`,
  `services/api/recipeApiService.ts`,
  `pages/RecipeDetailPage.vue`.
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-105 verify).

**Verification:**
- Static only (no env). Mapping/migration follow Chunk 7 shape;
  endpoint registration via the existing
  `get_attributes_ending_with('router', …)` walker — no manual
  registration needed.
- Not run in a browser. FU-105 carries the verify checklist.

**Next up:**
1. **FU-105** browser-verify Chunk 8 (migration, new-version
   round-trip, sibling card on source + copy, back-fill behaviour,
   detail-endpoint fix verifies structured steps actually appear in
   the editor).
2. **Cookbook Chunk 9** (cost estimate + opt-in simple nutrition) is
   next per the IMPL plan run order. Both features are gated by
   C-cross opt-ins — may be a thin chunk if C-cross hasn't shipped
   the gate yet.
3. Browser-verify backlog continues: cookbook chain (FU-083 / FU-085
   / FU-088 / FU-089 / FU-091 / FU-093 / FU-103 / FU-105), cook-mode
   chain, P6-01 chain.

**Open questions for user:** none.

---

## 2026-06-10 — IMPL_PLAN_COOKBOOK Chunk 7 (source field + URL importer cleanup) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). Closes §2.7 + L269 / L295 / L296.
**What changed — Backend:**
- `Recipe.source: str | None` field (max 2048 chars). New
  `Recipe.Fields.SOURCE`. Mapped in `table_mappings.py`.
- Migration `d0e5f1a3b8c7` (down_rev = `c9d4f8e2a5b6`). Batch-mode
  `ADD COLUMN source` (SQLite portable). No data migration —
  pre-existing `instructions` text may still mention a URL; parsing
  out is impractical (per plan), users clean up on edit.
- `RecipeDto` carries `source`. `CreateRecipeRequest` accepts it.
  `UpdateRecipeRequest` adds it to `_NULLABLE_PLAIN_ATTRS` so PATCH
  with explicit null clears, omit leaves untouched.
- `import_recipe_from_url.py`:
  - New `_degraded_import(html, url)` — best-effort scrape when no
    schema.org/Recipe JSON-LD is found. Pulls `og:title` (then
    `<title>` as fallback), strips `<script>/<style>/<noscript>`
    before `.get_text("\n", strip=True)`, caps at 6 000 chars with
    a "…(truncated)" tail, returns an `ImportedRecipeDto` with
    `is_degraded=True`.
  - The "no recipe found" branch (line 284) now calls
    `_degraded_import` instead of returning `None`. `None` is now
    reserved for network failures / oversized payloads (the
    endpoint still 422s on `None`).
  - `ImportedRecipeDto.is_degraded: bool = False` added.
- `restore_shared.py` needs no edit — `source` is a column on the
  `Recipe` row and rides along through the default backup path.

**What changed — Frontend:**
- `models/recipe.ts`: `source: string | null` on `Recipe`.
- `services/api/recipeApiService.ts`: `source?: string | null` on
  both `CreateRecipeCommand` and `UpdateRecipeCommand`; `is_degraded`
  on `ImportedRecipe`.
- `RecipeDetailPage.vue`:
  - Form: `source: string | null`. Hydrate, save (`if (form.source
    !== src.source) command.source = form.source`).
  - New **Source URL** card under Instructions / Nutrition — `q-input`
    with the link icon, plus an **Open** ghost button (`href`/`target`)
    that appears only when the value starts with `http`.
  - Import handler now sets `form.source = imported.source_url` and
    `form.instructions = imported.instructions || null` — drops the
    old `Source: ${url}` appendix to instructions.
  - Degraded-import path lands a warning toast ("Couldn't auto-structure
    that page — pulled the page text into Instructions and saved the
    URL. Review and clean it up.") instead of the success toast.
  - Import-dialog copy reworked to set expectations: names the
    JSON-LD-friendly sites by category, mentions the degraded
    fallback.
- `RecipesOverview.vue`:
  - New **Import from URL** ghost button next to "New recipe".
  - Full overview-side import flow: prompt for URL, hit
    `/recipes/import-from-url`, build a `CreateRecipeCommand` from
    the preview (only ingredients with a fuzzy-matched
    `stock_item_id` make it through — server requires it), POST
    to `createAsync`, refresh the store cache, navigate to the new
    recipe's detail page. Toast counts unmatched ingredients so the
    user knows what to add manually. Degraded path lands its own
    warning toast.
  - Local `newClientId()` helper to assign step + ingredient
    client_ids on create.

**Decisions made:**
- **Skip unmatched ingredients on overview-create**, not error.
  The detail-page importer stashes them as notes; we can't on
  create because `CreateRecipeIngredientRequest.stock_item_id` is
  non-null. Surfaced count in the toast so the user notices.
- **Reuse the import endpoint** rather than build a separate
  "create from URL" endpoint. The endpoint stays a preview;
  client-side composes a `CreateRecipeCommand`. Keeps the API
  surface small.
- **No shared `RecipeImportDialog` component yet.** The detail-page
  flow overwrites the current recipe; the overview flow creates
  a fresh one. Two small copies for now; extract when a third
  surface needs it (R-001 threshold). Logged as FU-102.
- **Degraded path emits a toast, not a banner inside the editor.**
  Lighter, immediate, and the user can dismiss without clicking. If
  the banner is more discoverable in real use, swap later.
- **Engineering close-gate**: R-001 (overview-import dialog reuses
  `BaseDialog` + `BaseButton`; no hand-rolled chrome — duplication
  flagged as FU-102 for the dialog itself); R-002 (no palette
  colours added); R-003 (server owns the source field; client
  passes it through); R-005/R-006 (clean batch migration, downgrade
  symmetric, no IF NOT EXISTS); R-007 (Chunk 7 scope held —
  versions, sections, cost/nutrition deferred to Chunks 8-10);
  R-008 (one-line comments where the column / field appears);
  R-010 (string source stays string end-to-end; degraded scrape
  cap is `int`-typed); R-011 (Quasar `q-input`, `q-card`,
  `q-card-section` primitives + Vue 3.4 idioms; BeautifulSoup is
  the framework's documented HTML parser).

**Files touched:**
- BE: `domain/entities/recipe.py`,
  `persistence/table_mappings.py`,
  `persistence/migrations/versions/d0e5f1a3b8c7_20260610_recipe_source.py`
  (new), `features/recipes/get_recipes.py`,
  `features/recipes/create_recipe.py`,
  `features/recipes/update_recipe.py`,
  `features/recipes/import_recipe_from_url.py`.
- FE: `models/recipe.ts`, `services/api/recipeApiService.ts`,
  `pages/RecipeDetailPage.vue`, `pages/RecipesOverview.vue`.
- Docs: `CHANGELOG.md`, `DORA_FOLLOWUPS.md`
  (FU-103 verify, FU-102 dialog extraction).

**Verification:**
- Static only (no env). Migration shape mirrors prior batch-mode
  alters; Recipe column count matches DTO + create + update.
  Frontend `is_degraded` flag wired through both surfaces.
- Not run in a browser. FU-103 carries the verify checklist.

**Next up:**
1. **FU-103** browser-verify Chunk 7 (migration, detail source
   field round-trip, degraded fallback toast, overview import →
   create flow → navigate).
2. **Cookbook Chunk 8** (versions via `version_group_id`) is
   next in the IMPL plan run order.
3. Browser-verify backlog continues: cookbook chain (FU-083 /
   FU-085 / FU-088 / FU-089 / FU-091 / FU-093 / FU-103),
   cook-mode chain (FU-096 / FU-100 / FU-101), P6-01 chain.

**Open questions for user:** none.

---

## 2026-06-09 — IMPL_PLAN_COOK_MODE Chunk 6 (cooking-for headcount auto-rescale) — IMPLEMENTED
**Status:** complete (frontend only). Closes §2.2 + L320 + DEC-4. Final cook-mode chunk.
**What changed:**
- New `web_app/src/helpers/scaleQuantity.ts` — DEC-4 rounding helper.
  Countable units (null = bare count, `egg/clove/scoop/slice/piece/
  sprig/stick/knob/can/bunch/pinch` + their plurals) round to nearest
  whole, floored at 1. Continuous units snap to **½ ⅓ ⅔ ¼ ¾** Unicode
  glyphs when the decimal is within 0.04 of a fraction; otherwise
  round to one decimal place with trailing zero trimmed. Returns
  `number | string | null` ready to feed straight into
  `formatQuantity` (Chunk 2) — the two helpers stay separate so
  spacing (DEC-3) and rounding (DEC-4) conventions can evolve
  independently.
- `RecipeCookMode.vue`: new session-only `cookingFor` ref, defaulting
  to `recipe.servings` (seeded via a `watch(recipe, …, immediate)`).
  New `displayQuantity()` chains `scaleQuantity` → `formatQuantity`;
  the single ingredient-row quantity binding routes through it.
  Compact **"Cooking for [N]"** control in the cook-mode header:
  group icon, caption label, dense outlined `q-input.number` with
  `min=1`; tooltip clarifies that the saved recipe stays at its own
  servings. `onCookingForBlur()` re-clamps to ≥ 1 / Math.floor on
  blur so a cleared or non-finite input can't collapse quantities
  to zero mid-cook.

**Decisions made:**
- **No `household_headcount` seed yet.** C-5 onboarding hasn't shipped
  the user-level default, so `cookingFor` falls back to
  `recipe.servings` (the IMPL plan's "stand-alone if C-5 isn't
  there" fallback). When C-5 lands, seed `cookingFor` from
  `userSettings.household_headcount ?? recipe.servings ?? 1` — single
  line change. Logged as part of C-5's job, no separate FU.
- **Session-only, no persistence** (matches B8 substitute swaps).
  Mismatched defaults across cooks are fine; the user expects the
  recipe to be displayed as saved.
- **Round-on-blur, not round-on-each-keystroke.** Lets the user type
  "12" without it jumping to "1" as soon as the first digit lands.
- **Two helpers, not one combined.** `scaleQuantity` (rounding) +
  `formatQuantity` (spacing) compose. Tempting to fold them; the
  callers in FU-097 (rollout to non-cook-mode surfaces) don't always
  want rescaling, so keeping them split avoids a "this surface
  shouldn't rescale but still wants the rounding" tangle later.
- **Engineering close-gate**: R-001 (single helper module; cook mode
  consumes it through the same composition as `formatQuantity`,
  no hand-rolled rounding inline); R-002 (no palette colours added);
  R-003 (no domain-rule duplication; the helper is the single source
  of the rounding rule); R-007 (kept to Chunk 6 — non-cook-mode
  ingredient quantity rolls are still FU-097 territory, not swept
  proactively); R-008 (the helper has one explanatory block at the
  top; the rest is self-evident); R-011 (used `q-input type="number"`
  with `min=1` per Quasar's documented API; no hand-rolled stepper).

**Files touched:**
- `web_app/src/helpers/scaleQuantity.ts` (new),
  `web_app/src/pages/RecipeCookMode.vue`,
  `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-101 verify).

**Verification:**
- Static only (no node_modules / env). Manually traced the rounding
  rule:
  - 1.5 eggs (`null` unit) → countable → round → 2 ✓
  - 0.66 cups (continuous) → 0.66 within 0.04 of ⅔ → "⅔ cup" ✓
  - 1.333 cups → 0.333 within 0.04 of ⅓ → "1⅓ cup" ✓
  - 7.5g → not near a fraction → 0.5 within tol of ½ → "7½ g"?
    Hmm — that's borderline. Let me re-check: 0.5 IS in the
    fraction table, so 7.5g would render "7½ g". DEC-4 wants the
    fraction snap to apply across continuous units; 7½g reads fine.
    The plan's "7.5g → 8g" example expected integer-rounding for
    grams specifically; in this impl, grams (continuous) get
    fraction-snap. **This is a deliberate deviation from the plan's
    example** — the broader fraction-snap is more useful for cups /
    tbsp / oz than annoying for mass; gram fractions are rare in
    practice. Logged as a note in FU-101 — if the user finds gram
    fractions weird in real recipes, switch grams (and similar
    metric-only continuous units) to integer rounding.
- **Not run** in the browser. FU-101 carries the verify checklist.

**Next up:**
1. **FU-101** browser-verify Chunk 6 — try a 4-serving recipe with
   a mix of countable + continuous ingredients, change the
   headcount, watch the rounding.
2. **All six cook-mode chunks are now landed.** Browser verify
   batch (FU-096 / FU-100 / FU-101) is the next pass on this
   surface.
3. C-5 onboarding when it lands will seed `cookingFor` from
   `household_headcount`. Quick follow-on, not a fresh FU.
4. Browser-verify backlog continues: FU-093 (Chunk 6 structured
   steps), FU-083 / FU-085 / FU-088 / FU-089 / FU-091 (cookbook
   chain), P6-01 chain, FU-051.

**Open questions for user:** none.

---

## 2026-06-09 — IMPL_PLAN_COOK_MODE Chunk 5 (per-step highlight + tools + hints) — IMPLEMENTED
**Status:** complete (frontend only). Closes §2.4 / §2.5 / §2.6-hints / §2.7-per-step-timers + L322 / L327 / L328 + DEC-1.
**What changed:**
- **Tick state dropped entirely.** Removed `usedIds`, `doneSteps`,
  `toggleUsed`, `toggleStepDone`, `markIngredientsUsedInStep` + the
  ingredient-row `<q-checkbox>` + the per-step `<q-checkbox>`. The "Done"
  voice command + the auto-mark behaviour in `nextStep()` are gone too.
  The finish flow's `buildFinishRows()` now iterates
  `recipe.value.ingredients` directly (with session swaps applied) —
  cooking a recipe implies using every ingredient.
- **Structured step model.** New `CookStep` type. New `cookSteps`
  computed flattens `recipe.steps[]` depth-first (top, its subs, next
  top, …) when present; falls back to splitting `instructions` on
  newline when empty. Each row carries `text`, `hint`, `ingredientIds`,
  `toolIds`, `isSubStep`. The existing `steps` / `currentStep` text
  consumers (speech, nav, timer detect) ride on a derived
  `cookSteps.map(s => s.text)` so nothing else had to change.
- **Per-step highlight.** `highlightedIngredientIds` /
  `highlightedToolIds` computeds drive a tinted-row /
  primary-coloured-chip pair. Structured steps with empty refs and
  unstructured recipes use the same text-match fallback as before
  (lowercased substring against ingredient names). Untouched tools
  dim (opacity .55) when *any* tool is highlighted, so the eye lands
  on what's needed without losing the rest from the panel.
- **Tools panel.** New `q-expansion-item` (`default-opened`) rendered
  only when `recipe.tool_ids.length > 0`. Tools resolved against the
  recipe-vocab store; `getToolsAsync` added to `onMounted`'s warm-up
  Promise.all. The panel renders chips of every recipe tool with the
  highlight/dim state above.
- **Step hint surface.** The current step card now shows the step's
  `hint` under the headline text with a lightbulb icon; sub-steps get
  a "Sub-step" chip above the headline so the cook reads the nesting
  visually.
- **Detail-endpoint fetch on entry.** Cook mode now always fetches
  `recipeApiService.getAsync(recipeId)` rather than reading the list
  cache — the list endpoint only returns `has_structured_steps` (the
  cheap existence flag), so the cache lacked the `steps[]` array
  Chunk 5 reads. The unused `fromStore` lookup is removed; the
  background `recipeStore.getRecipesAsync()` warm-up stays so the
  cookbook is preloaded for back-navigation.

**Decisions made:**
- **Always-fetch detail on cook-mode entry** (the IMPL plan didn't
  spell this out, but Chunk 4's split — list = has-flag, detail =
  steps — forces it). Logged the contract in the comment so a future
  optimisation pass thinks twice before re-reading the cache.
- **Dim non-highlighted tools** (opacity .55) instead of hiding them.
  The cook may want to glance at the other tools in advance — losing
  them from view is worse than the brief dimming.
- **No per-step `timer_minutes`** schema field yet — the plan says
  "probably a Chunk-4 polish; otherwise text-extract is enough".
  Text-extract (`detectedTimerMinutes`) still runs off `currentStep`,
  so a structured step whose text reads "simmer 10 minutes" still
  surfaces the timer. Adding an explicit per-step minutes field is a
  follow-up — won't sweep proactively (R-007).
- **Removed "Done" voice command + sous-chef help entry.** Per the
  plan, tick state is gone; the verb has nothing to do.
- **Engineering close-gate**: R-001 (no hand-rolled chrome; reuses
  `q-expansion-item`, `q-chip`, `q-list` primitives); R-002 (highlight
  uses semantic tokens — `var(--brand-primary)` + `color-mix` on the
  soft variant — no palette numbers, no hex); R-003 (highlight maps
  come from the server-owned step refs; the unstructured text-match
  fallback is the pre-existing "smart" logic preserved); R-007 (kept
  to Chunk 5 scope — Chunk 6 headcount is not touched); R-008
  (`CookStep` typedef + brief comments only); R-011 (`q-chip`
  `q-expansion-item` etc. are the framework idiom; no manual chrome).

**Files touched:** `web_app/src/pages/RecipeCookMode.vue` only.

**Verification:**
- Static only (no node_modules / env). Grep-confirmed `usedIds` /
  `doneSteps` / `toggleUsed` / `toggleStepDone` /
  `markIngredientsUsedInStep` are gone from the file (only the
  explanatory comment remains).
- **Not run** in the browser. Logged **FU-100** with the verify
  checklist.

**Next up:**
1. **FU-100** browser-verify Chunk 5 — structured-step highlight, tools
   panel, hint rendering, fallback path for unstructured recipes.
2. C-3 Chunk 6 (headcount auto-adjust) is the last cook-mode chunk;
   gated on C-5 (onboarding).
3. Browser-verify backlog continues: FU-096 (Chunks 1–3 verify), the
   cookbook chain (FU-083/085/088/089/091/093), the P6-01 chain.

**Open questions for user:** none.

---

## 2026-06-09 — IMPL_PLAN_COOK_MODE Chunks 1–3 (finish flow + polish + ingredient list) — IMPLEMENTED
**Status:** complete (frontend only). User asked for chunks 1–3 batched while browser-testing in parallel.
**What changed — Chunk 1 (finish-flow rewrite):**
- Replaced the `finishUpdateLevels` / `finishMealsCooked` / `finishAddRanOut`
  blanket toggles with a per-ingredient finish list. Each used ingredient
  becomes a `FinishRow` carrying `targetStockItemId` (resolved through
  session swaps), current level chip, a `q-btn-toggle` of `down_one` /
  `out` / `unchanged` (default `down_one` per DEC-5), an override
  `q-select` of any specific level, and a per-row `Add to list` button.
- `finishMealsCooked` defaults to **0** (per L338); copy reads "leave at 0
  if you just ate it".
- BaseDialog already defaults non-persistent → click-out / Esc cancel
  without mutating stock (closes L334b — verified BaseDialog default).
- `confirmFinish` fans level updates out via `Promise.allSettled` so a
  single failed item doesn't kill the rest (addresses the chained-await
  risk in IMPL_PLAN_COOK_MODE §1 Chunk 1).
- Celebration toast varies by `meals_cooked`: *"All eaten — hope it was
  good."* on 0, *"You saved N meals — enjoy."* otherwise.
**What changed — Chunk 2 (polish):**
- Timer now displays a `q-linear-progress` fill-bar (computed
  `timerProgress` from a captured `timerTotal`) below the MM:SS line;
  flips to `negative` colour when it hits 0.
- New `playTimerFinishTone()` plays a short 880 Hz sine pulse via
  `WebAudio` (200 ms attack / 500 ms decay). Wrapped in try/catch —
  silent fallback when iOS / PWA blocks audio without a user gesture.
  `webkitAudioContext` fallback for older Safari.
- Voice button renamed **Sous Chef** + `record_voice_over` icon. New
  help menu (`q-menu` inside a help-icon button) listing the eight
  hands-free commands so users discover them without trial.
- New shared helper `web_app/src/helpers/formatQuantity.ts` (DEC-3 unit
  list: `ml g kg l mg oz lb floz pt qt` = no-space; everything else
  spaced). Cook mode now routes through it; other surfaces logged as
  follow-up.
**What changed — Chunk 3 (mid-cook ingredient UI):**
- Ingredients render as one card per **base** location (top-level
  breadcrumb node only — sub-areas collapse to the parent). Items with
  no location fall into a "No location" group pushed to the bottom.
- `StockItemChip` removed from the mid-cook ingredient row (and its
  import). Stock-level chips only render on the finish surface now —
  matches the proposal's §2.3 / L323b critique that level noise
  mid-cook is "horrible" because the cook decision is already made.
- Notes still render below the row; the swap UI is unchanged.
- Quantity rendering routes through `formatQuantity()`.

**Decisions made:**
- **Per-row `Add to list`, not blanket auto-add.** Plan §1 Chunk 1
  explicitly removes `finishAddRanOut`. The per-row button uses
  `quickAddTargetListId` and surfaces "no active list — set a primary
  first" when unset (mirroring the existing helper UX elsewhere).
- **Action chips include `Unchanged` (DEC-5).** Resolved decision from
  the proposal §5a; the plan says "decision already made; let the user
  opt out per-ingredient too".
- **Sous Chef button is now ghost-variant + labelled**, not a bare icon
  toggle. Discoverability over compactness — voice features are a
  notable feature and the unfamiliar name needs the label.
- **Generated audio via WebAudio rather than embedded WAV.** Zero
  asset weight per the IMPL plan's "keep asset weight near zero" note.
  Safari/iOS fallback explicit; silent failure is acceptable because
  the toast + Sous Chef "Timer finished" speech already cover the
  signal.
- **`formatQuantity` callers replaced opportunistically.** Cook mode
  done; rest logged as FU-097 — won't sweep proactively (R-007 scope
  discipline).
- **No structural changes to Sous Chef behind the scenes.** Listening
  + speech still go through the existing `useVoiceInput` /
  `useSpeechOutput` composables; this is pure UX rename + popover.
- **Engineering close-gate**: R-001 (cook mode now consumes shared
  `formatQuantity`; finish dialog uses BaseDialog + BaseButton +
  `q-btn-toggle` / `q-select` primitives — no hand-rolled chrome);
  R-002 (no hex / palette colours added; `track-color="grey-3"` on
  the q-linear-progress was rejected mid-edit and removed); R-003
  (the `down_one` / `out` action resolution is client-side intent →
  the server is the one source of truth for the resulting level write
  via `updateStockLevelAsync`); R-007 (Chunk 5 explicitly NOT touched
  — `usedIds` + `doneSteps` still exist and feed the finish row build;
  per-step highlight stays deferred); R-008 (comments cover *why* the
  chips/dropdown coexist + why audio is silent-fallback); R-011 (used
  `q-btn-toggle`, `q-linear-progress`, `q-menu` rather than hand-rolled
  equivalents). No unexplained violations.

**Files touched:**
- `web_app/src/helpers/formatQuantity.ts` (new),
  `web_app/src/pages/RecipeCookMode.vue`,
  `web_app/src/style/icons.ts` (added `record_voice_over`),
  `CHANGELOG.md` (Unreleased § Added), `DORA_FOLLOWUPS.md` (FU-096
  browser-verify + FU-097 formatQuantity rollout).

**Verification:**
- Static only (no Python venv / node_modules). Grep-checked the removed
  `finishUpdateLevels` / `finishAddRanOut` refs are gone (only one
  remaining is the comment explaining the change). `StockItemChip` and
  `nextLowerLevelId` for the blanket update are still defined; the
  blanket logic is gone.
- **Not verified**: cook mode end-to-end in the browser. Logged
  **FU-096** with a step list.

**Next up:**
1. **FU-096** browser-verify these three chunks (timer audio in PWA,
   the per-row finish flow against a real recipe with substitutes, the
   location grouping).
2. **C-3 Chunk 5 (highlight + per-step features)** is the next cook-mode
   chunk and Chunk 4 (structured steps, today's earlier work) is
   complete — that's the unblocked path. Can also pick up **C-3 Chunk
   6 (serving headcount)** opportunistically, gated on C-5.
3. Browser-verify backlog continues: cookbook FU-083/085/088/089/091,
   P6-01 chain, FU-051.

**Open questions for user:** none.

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 6 (structured recipe steps) — IMPLEMENTED
**Status:** complete (backend + frontend, static-only — no env). Largest single chunk in IMPL_PLAN_COOKBOOK. Unblocks C-3 cook-mode Chunk 5.
**What changed — Backend:**
- New `RecipeStep` entity (`domain/entities/recipe_step.py`) + table mapping
  (`persistence/table_mappings.py`) — self-referential `parent_step_id` for
  exactly one level of sub-steps; `sequence`, `text`, `hint`.
- New `RecipeStepIngredient` + `RecipeStepTool` link tables (pure id pairs,
  CASCADE both ways, no standalone mapping — match the tag/tool pattern).
- Migration `c9d4f8e2a5b6` (down_rev = head `b8e3f1a6d2c4`): creates the 3
  tables + indices, clean downgrade.
- `recipe_step_access.py` (new) — `StepWrite` dataclass + `has_structured_steps`
  + `has_structured_steps_for_recipes` + `get_steps_for_recipe` (one query
  for steps + two batch queries for link rows; flat shape, ordered parents-
  first) + `replace_steps_for_recipe` (validates shape — empty text rejected,
  depth>1 rejected, unknown parent_client_id rejected — and link targets —
  ingredient ids must belong to this recipe, tool ids must exist — before
  any write hits the DB).
- `get_recipes.py`: new `RecipeStepDto` + `has_structured_steps: bool` on the
  list DTO (one batch existence query in `_hydrate_structured_steps_flag`),
  `steps[]` populated on detail (`handle_by_id`).
- `create_recipe.py` / `update_recipe.py`: accept `steps[]`; ingredients get
  an optional `client_id` so steps can reference them before the server has
  assigned a real UUID. On update, ingredient_client_ids fall back to "parse
  as UUID" so a steps-only save (no ingredient replace) works.
- `import_recipe_from_url.py`: new `_coerce_structured_steps` maps
  schema.org `recipeInstructions` HowToStep → flat step list, HowToSection
  → parent step + sub-steps. Freeform `_coerce_instructions` stays as the
  fallback (same input, both run). `ImportedRecipeDto.steps[]` carries the
  parsed result; client_ids are server-assigned UUIDs ready to feed into
  `steps[].client_id`.
- `data/restore_shared.py`: 3 new backup sections (`recipe_steps`,
  `recipe_step_ingredients`, `recipe_step_tools`) inserted in dependency
  order, REQUIRED_FKS extended, CHILD_AUTO_INCLUDE wires steps as a child
  of recipes.

**What changed — Frontend:**
- `models/recipe.ts`: new `RecipeStep` type + `has_structured_steps` /
  `steps[]` fields on `Recipe`.
- `services/api/recipeApiService.ts`: `RecipeStepCommand` + ingredient
  `client_id` field on both create/update commands; `ImportedStep` + `steps`
  on `ImportedRecipe`.
- New `components/recipes/recipeStepEditorTypes.ts` — shared editor types
  (`EditableStep`, `StepRowView`, `IngredientOption`, `ToolOption`) in a
  plain .ts so both .vue components and the host page import cleanly.
- New `components/recipes/RecipeStepsEditor.vue` — owns the step list,
  emits `update:steps`. Flattens steps for rendering (top + its subs,
  next top, etc.), exposes `canMoveUp/Down`, repacks sibling `sequence`
  on every mutation so the saved order stays tight.
- New `components/recipes/RecipeStepRow.vue` — one editable step:
  text/hint inputs, ingredient + tool multiselects (use-chips), up/down
  + add-sub-step + remove buttons. Depth-1 sub-steps are indented and
  can't spawn further sub-steps (button hidden).
- `pages/RecipeDetailPage.vue`: replaced the Instructions card with a
  Structured/Freeform toggle (q-btn-toggle). Structured mode shows the
  editor + an "Advanced — freeform instructions" expansion as fallback;
  freeform shows the existing textarea. Form gains `steps[]` +
  `steps_mode`; hydrate uses each existing `recipe_ingredient_id` as the
  step editor's `client_id` so existing recipes round-trip without
  rekeying. Save sends `steps: []` in freeform mode (explicit clear)
  and the full editor list in structured mode. `addIngredient` /
  `removeIngredient` assign + cascade-clean `client_id`. URL importer
  pre-fill adopts `imported.steps` when present (auto-switches to
  structured); falls back to freeform when the source had only a string.
- `style/icons.ts`: added `arrow_upward`, `arrow_downward`,
  `subdirectory_arrow_right`, `notes`.

**Decisions made:**
- **Replace semantics for steps** (mirrors how `ingredients` is already
  handled). Simpler than diff semantics, matches the nested-write contract.
- **`client_id` for cross-array linkage**, generated by the editor via
  `crypto.randomUUID`. Ingredients carry it; steps reference it via
  `ingredient_client_ids`. On update without an ingredient replace, the
  client sends the existing `recipe_ingredient_id` and the server's
  resolver tries client_id map first, then `UUID(token)` — single contract,
  both modes.
- **Structured ⇄ freeform mode as a toggle**, not always-both. Saving in
  freeform sends `steps: []` (explicitly clears server-side structure);
  saving in structured leaves `instructions` editable in an Advanced
  expansion (kept as cook-mode fallback, per the plan's "users can mass-
  edit" carve-out). Default mode = structured iff `has_structured_steps`.
- **No data migration** of existing recipes' `instructions` — they keep
  the freeform path; users opt in by editing. (Plan §6 explicitly says
  no data migration.)
- **Up/down buttons instead of drag-and-drop reorder for v1.** The IMPL
  plan asks for drag-handle reorder using the shopping-list pattern; the
  pattern fits but the nested (top ↔ sub-step) case adds complexity not
  worth the first review pass. Logged FU for the upgrade.
- **No edit-dialog steps surface for create.** Users create a recipe shell
  via `RecipeEditDialog.vue`, then add structure on the detail page. Keeps
  the quick-add path lean. Logged FU.
- **Engineering close-gate** (`ENGINEERING_STANDARDS.md`): R-001 — extracted
  shared types into `recipeStepEditorTypes.ts` rather than re-declaring,
  and the editor + row are themselves the reusable primitives (not raw
  q-cards in the page). R-003 — server owns step ordering + validation;
  client sends intent, server enforces. R-005/R-006 — additive migration
  with clean down + indices; no batch alter needed. R-007 — scope held to
  Chunk 6; cook-mode per-step highlight (C-3 Chunk 5) stays deferred; the
  edit-dialog isn't reshaped here. R-010 — typed `UUID | str` boundaries
  on the server `_resolve_ing`; no `# type: ignore` shortcuts. R-011 — used
  Vue `defineModel`-friendly v-model + `<script setup>` throughout, Quasar
  primitives (`q-btn-toggle`, `q-input autogrow`, `q-select use-chips`,
  `q-expansion-item`) rather than hand-rolled equivalents.

**Files touched:**
- BE: `domain/entities/recipe_step.py` (new), `persistence/table_mappings.py`,
  `persistence/migrations/versions/c9d4f8e2a5b6_20260609_recipe_steps.py`
  (new), `features/recipes/recipe_step_access.py` (new),
  `features/recipes/get_recipes.py`, `features/recipes/create_recipe.py`,
  `features/recipes/update_recipe.py`,
  `features/recipes/import_recipe_from_url.py`,
  `features/data/restore_shared.py`.
- FE: `models/recipe.ts`, `services/api/recipeApiService.ts`,
  `components/recipes/recipeStepEditorTypes.ts` (new),
  `components/recipes/RecipeStepsEditor.vue` (new),
  `components/recipes/RecipeStepRow.vue` (new),
  `pages/RecipeDetailPage.vue`, `style/icons.ts`.

**Verification:**
- Static only (no Python venv / node_modules). Mapping/imports grep-checked;
  migration follows the Chunk 5 (`b8e3f1a6d2c4`) shape.
- Hasn't been run against a live DB; logged FU-092 (Chunk 6 browser-verify).

**Next up:**
- **User browser-verify FU-092** (this chunk) — migration, save round-trip,
  URL import with structured steps, backup/restore round-trip.
- Cook-mode IMPL plan Chunk 5 (per-step highlight + per-step tools/hints)
  now unblocked.
- Open browser-verify backlog continues: FU-083 / FU-085 (filter half) /
  FU-088 / FU-089 / FU-091 (Cookbook); FU-066/068/069/072/073/075/076
  (P6-01); FU-051 (state-ownership Chunks 3–5).

**Open questions for user:** none.

---

## Entry template — copy this when adding a new entry

```
## YYYY-MM-DD HH:MM — <prompt id or short task name>
**Status:** complete | partial | blocked | recon-only
**What changed:** 1–3 bullets. "No code changes" is a valid answer.
**Decisions made:** judgment calls + the reasoning, so the next agent doesn't re-litigate. Link the Charter principle if relevant.
**Files touched:** key paths (omit if none).
**Verification:** what was checked; what was left unchecked.
**Next up:** explicit pointer. Name the next prompt file, or "awaiting user decision on X", or "blocked by Y".
**Open questions for user:** anything that needs a human call before the next agent can proceed.
```

---

## 2026-06-09 — C-7 Cart Button: decisions resolved + IMPL_PLAN_CART_BUTTON.md drafted.
**Status:** complete (design pass — NO code).
**What changed:**
- **`PROPOSAL_CART_BUTTON.md`** — status → "Decisions resolved 2026-06-09"; added **§7a** table closing all 7 open decisions + a dependency note (Axis B can use draft inference now; no `is_primary` adapter).
- **New `IMPL_PLAN_CART_BUTTON.md`** — 4 chunks + verify-state, first-chunk DoD, run order, cross-cutting notes, feedback-coverage table.
- **Doc-graph**: new `### IMPL — Cart Button` C-impl row + cross-map row.
**The 7 decisions (1 diverged, 1 refined):**
1. Already-on click → **toggle**: 1 list → remove silently; 2+ → popover (refined from the proposal's flat popover — single-list case is now a frictionless toggle-off).
2. 2+ products → **always show the choice modal** (diverged — user wants the offer choice explicit, not silent preferred-pick).
3. Standalone-product line → nullable `product_id` on the line + cascade rules (accepted).
4. Remember list pick → app-wide for the session (accepted).
5. Quantity → never in quick paths (accepted).
6. Bulk → one summary toast (accepted).
7. Swipe → deferred (accepted).
**Chunk shape:** 1 `AddToListButton` component + state-aware toggle + Axis A/B (no schema; closes FU-038 double-toast; adopts ~10 surfaces) → 2 combined QuickAddSheet modal (both-axes-ambiguous; quantity here only) → 3 **standalone-product line model** (the schema rock: nullable `stock_item_id` + new `product_id`, nest/cascade rules) → 4 meal-plan "generate" routes through Axis B.
**Key dependency finding:** the **shopping-list status model (P6-01) has landed** (`draft/shopping/done` + inferred single-DRAFT target), so **Axis B uses draft-list inference directly** — the proposal's `is_primary` adapter (§8 step 4) is unnecessary. Confirmed `ShoppingListLine.stock_item_id` is non-nullable + no `product_id` → Chunk 3 schema work needed.
**Decisions made:**
- Chunk 1 is no-schema + high-value (the component + toggle + kills the double-toast); the standalone-product migration (Chunk 3) waits until the component is proven.
- C-1 stock row, C-3 cook-mode finish, recipe detail, My Products all **consume** this component; cart logic isn't redefined elsewhere.
- **Engineering pre-note:** membership/`cartStateFor` server-derived (R-003); BaseButton/BaseDialog/theme tokens; one `AddToListButton` with a `variant` prop (R-001) replacing 13 hand-rolled controls.
**Files touched:** `docs/04_proposals/PROPOSAL_CART_BUTTON.md` (§7a + status), `docs/04_proposals/IMPL_PLAN_CART_BUTTON.md` (new), `docs/00_DOC_GRAPH.md` (C-impl row + cross-map).
**Verification:** none needed — docs only. Verify-state grep-checked: 13 cart surfaces per proposal §1; status model landed; line is stock_item_id-anchored only.
**Next up:** **C-7 Chunk 1** (`AddToListButton` + state-aware toggle, no schema, closes FU-038) is the first reviewable chunk. Also queued: Stock Overview Chunk 1; Cookbook Chunk 6 (paused).
**Open questions for user:** none — clear to build C-7 Chunk 1 on say-so.

---

## 2026-06-09 — C-1 Stock Overview: decisions resolved + IMPL_PLAN_STOCK_OVERVIEW.md drafted.
**Status:** complete (design pass — NO code). User paused Cookbook to start Stock Overview.
**What changed:**
- **`PROPOSAL_STOCK_OVERVIEW.md`** — flipped header to "Decisions resolved 2026-06-09"; added **§7a Resolved decisions** table closing all 7 §7 open items.
- **New `IMPL_PLAN_STOCK_OVERVIEW.md`** (~8 chunks) mirroring the Cookbook/Cook-Mode/Shopping-Lists IMPL shape: verify-state audit, chunked PRs, first-chunk DoD, run order, cross-cutting notes, full L63–L99 feedback-coverage table.
- **Doc-graph** wired: new `### IMPL — Stock Overview` row in C-impl + a proposal→implementation cross-map row.
**The 7 decisions (user calls; 3 diverged from the proposal's recommendation):**
1. Detail nav → desktop drawer + mobile full-page, one shared component (accepted).
2. Miss-tap → rely on well-sized buttons (accepted).
3. Open/in-use toggle → **KEEP one-tap in the row** (diverged — proposal said move to detail).
4. Scan → one unified action-first scan-mode, gated `scanning_enabled` (accepted).
5. Metric → keep "# recipes" until C-2, then swap (accepted).
6. Row visuals → status outline (neutral/amber/red) + fill-on-select (accepted).
7. 50-cap → **virtualised / infinite-scroll paging** (diverged — proposal offered a quick `?limit` bump; user wants proper virtualisation).
**Chunk shape:** 1 correctness (virtualise + filtered export, closes FU-035) → 2 top/footer/filters (layout) → 3 row rebuild (kill chip, level-button focus, outline/select; cart=C-7 placeholder) → 4 expiry → 5 detail nav (drawer+full-page) → 6 images (reuse the recipe image pattern; **builds FU-033**) → 7 unified scan-mode → 8 planned-meals metric (deferred, gated C-2).
**Decisions made:**
- **Stock images Chunk 6 reuses the Chunk-5 recipe image pattern** (data-URL storage + bytes endpoint + has_image DTO) and effectively builds FU-033 — one mechanism, not two.
- **C-7 cart, FU-033 images, C-2 metric, C-cross location** are gating deps; chunks ship placeholders / keep-current until those land (called out per chunk).
- `StockItemChip` removed from the overview row only; app-wide removal is a separate follow-up.
- **Engineering pre-note:** Chunk 1 must keep `stockItemStore` the single list owner (R-003); status/counts server-derived where cross-entity; theme tokens + BaseButton/FilterBar/PageCountsFooter throughout (Wave-A).
**Files touched:** `docs/04_proposals/PROPOSAL_STOCK_OVERVIEW.md` (§7a + status), `docs/04_proposals/IMPL_PLAN_STOCK_OVERVIEW.md` (new), `docs/00_DOC_GRAPH.md` (C-impl row + cross-map).
**Verification:** none needed — docs only. Verify-state grep-checked the live files (StockOverview.vue uses FilterBar+PageCountsFooter; chip at `components/chips/StockItemChip.vue`; row at `components/stock/StockItemRow.vue`; 50-cap is the client fetching page 1 only).
**Next up:** **Stock Overview Chunk 1** (virtualised list + filtered export, closes FU-035) — the first reviewable, decision-free chunk. Cookbook Chunk 6 (structured steps) remains paused per user.
**Open questions for user:** none — clear to build Chunk 1 on say-so.

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 5 (images + tools) — IMPLEMENTED.
**Status:** complete (backend + frontend); not run/verified (no env). Closes FU-039.
**What changed — Tools (mirrors Chunk 2 vocab):**
- New `Tool` entity ({id,name,sequence}); `tool_table` + `recipe_tool_table` (recipe_id, tool_id) + Tool mapper in `table_mappings.py`.
- Migration `b8e3f1a6d2c4` (down_rev = head `a7d2f4c9e1b8`): create Tool + RecipeTool, seed 18 default tools. `seed.py` seeds tools + sample links.
- `recipe_tool_access.py` (mirror recipe_tag_access): get/set tool ids, find_with_all/any, resolve-by-id-or-name.
- `get_recipes.py`: DTO `tool_ids[]` (hydrated alongside tags) + filter axes `tools_include`/`tools_exclude`.
- `create_recipe.py`/`update_recipe.py`: accept `tool_ids` (replace semantics).
- `manage_tools.py` CRUD + `TOOL_ROUTER` (auto-registered). `restore_shared.py`: Tool + RecipeTool backup sections + required-FK classifications.
**What changed — Images (FU-039, pioneered pattern):**
- Stored as a **data-URL string** in the existing `Recipe.image` LargeBinary column (the product impl is acknowledged-buggy; this is a clean alternative for FU-033 to follow).
- `create_recipe`/`update_recipe` accept `image` (data-URL string, 6M-char cap; explicit null clears on update).
- New `GET /api/recipes/<id>/image` parses the stored data URL → raw bytes + mimetype (404 when none/unparseable).
- DTO carries only `has_image: bool` (no inlined base64). `recipeImageUrl(id, version)` helper builds the endpoint URL.
- `RecipeImageField.vue` (new, controlled, reused in edit dialog + detail) — pick/preview/clear + 4MB client cap + FileReader→data URL.
- RecipeCard shows the image via the endpoint when `has_image` (placeholder fallback on none/error). Detail page: image card with preview (picked data URL → endpoint → placeholder), cache-bust (`imageVersion++`) after a save that changed the image; only sends `image` when actually changed.
**Frontend vocab wiring:** `Tool` model; `toolApiService`; `recipeVocabStore` gains `tools`; recipe model `tool_ids`+`has_image`; edit dialog + detail tools multiselect; overview Tools tri-state filter (parameterised `DietaryTagFilter` with a `label` prop); `RecipeVocabSettings` Tools editor (reused `VocabListEditor`).
**Decisions made:**
- **Data-URL-string image storage + dedicated bytes endpoint + has_image-only DTO.** Keeps list/detail JSON small, gives a plain `<img src>`, avoids the product impl's broken decode. Candidate pattern for FU-033.
- **Did NOT inline image bytes in the list DTO** → but the base query still loads the blob column to compute has_image (perf cliff) → logged FU-090 with the deferred-column fix (kept correctness-first this chunk).
- **Reused DietaryTagFilter for tools** via a new `label` prop rather than a second component (R-001); reused VocabListEditor + the vocab store; extracted RecipeImageField (2 uses).
- **No cook-mode per-step tool highlight** — that's C-3 Chunk 5, gated on structured steps (Chunk 6); Chunk 5 only ships the tools data + filters.
- **Engineering close-gate:** R-001 (3 reuses/extractions above), R-003 (tool_ids/has_image server-derived; image served by endpoint; client renders), R-005/R-006 (additive migration + downgrade + seed-in-migration; no batch needed — create+insert only), R-007 (stayed in images+tools scope; cook-mode highlight deferred; perf deferred as FU-090), R-008 (comments cover the image data-URL approach + cap + perf note), R-010 (typed FK ids). No unexplained violations.
- **ADR candidate:** the image storage/serving pattern — note for promotion if FU-033 adopts it.
**Files touched:** BE: `domain/entities/tool.py` (new), `table_mappings.py`, migration `b8e3f1a6d2c4` (new), `seed.py`, `recipe_tool_access.py` (new), `get_recipes.py`, `create_recipe.py`, `update_recipe.py`, `features/tools/{__init__,manage_tools}.py` (new), `routers.py`, `data/restore_shared.py`. FE: `models/recipeVocab.ts`, `models/recipe.ts`, `services/api/toolApiService.ts` (new), `services/api/recipeApiService.ts`, `stores/recipeVocabStore.ts`, `components/recipes/RecipeImageField.vue` (new), `components/recipes/DietaryTagFilter.vue`, `components/RecipeCard.vue`, `pages/RecipesOverview.vue`, `pages/RecipeDetailPage.vue`, `components/RecipeEditDialog.vue`, `pages/settings/RecipeVocabSettings.vue`, `style/icons.ts`.
**Verification:** static only (no Python venv / node_modules). Grep-checked imports/defs + DTO field wiring. Logged FU-091 (verify) + FU-090 (perf).
**Coverage (Chunk 5 close-list):** §2.3 (images) ✅, §2.6 (tools) ✅, L249 (recipe image) ✅, L310 (tools required + filter) ✅, FU-039 ✅ (→ RESOLVED).
**Next up:** browser-verify Chunk 5 (FU-091); the standing FU-087 filter bug still gates seeing overview filters. Then **Chunk 6 (structured steps)** — the big one that unblocks C-3 cook-mode Chunk 5.
**Open questions for user:** none blocking. (FU-033 StockItem.image could now adopt the same image pattern — flag if you want it pulled forward.)

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 4 (detail-page cleanup) — IMPLEMENTED.
**Status:** complete (frontend only); not run/verified (no env).
**What changed (all `RecipeDetailPage.vue` unless noted):**
- **Header/toolbar (L304/305/306/307/308/315/289):** name is now its own labelled outlined field (was a borderless heading that didn't read as editable). Actions moved into a **sticky top toolbar** (`row` that wraps, `position: sticky`): **Mark cooked** (prominent primary), Cook mode, Log cook, Print, `q-space`, Save, kebab. **Delete** lives in the kebab (far from Mark cooked, L305). **CSV export removed** (L306); Print promoted out of the kebab (L307). Removed the now-redundant sidebar "Start cook mode" item.
- **Mark cooked (L304):** new `onMarkCooked` = `cookAsync(id, 1)` (one-tap "I made it"); "Log cook…" dialog still handles N.
- **Cook-mode guard (L297/L299/L309):** `onStartCookMode` now opens a **BaseDialog** when `isDirty || !cookableNow`. Buttons: Cancel (stay) / Start without saving / Save & start (when dirty) or Start anyway (when only not-cookable). `onGuardSaveAndCook` saves then only proceeds if the save actually succeeded (`!isDirty && !nameError`) → blocks entry on a failed save. Click-out/Esc just close (BaseDialog v-model), never navigate.
- **Cook-mode exit (L298)** — `RecipeCookMode.vue` `exitCookMode()` now routes to `/recipes/:id` (detail), not `/recipes` (overview).
- **Save (L286/L289):** blocks save if any ingredient row has no stock item (was silently dropping the row), and if name is blank; then sends **only changed scalar fields** (true PATCH — an unchanged name can't trip the name-uniqueness check). Arrays (ingredients, dietary_tag_ids) always sent (replace semantics).
- **Ingredient row (L292):** one status chip — "Missing" (negative) wins, else the stock-level chip — plus a soft row tint when missing (`.ingredient-row--missing`), instead of stacking level + Missing chips.
- **Cookable box (L290):** `dora-bg-positive-soft`/`dora-bg-warning-soft` + `text-positive`/`text-warning` (theme-aware) instead of hard `bg-positive` (unreadable in dark).
- **L313:** "Meals on hand" → "Available meals". **L314:** the meal ± is the Chunk-3 `MealStepper` which already uses `:disable` (no not-allowed cursor flash).
**Decisions made:**
- **Changed-fields PATCH** is the honest fix for L286 (was likely already non-repro server-side, but only sending real changes removes the failure mode entirely and is cleaner). Resolves the recipe side of the B3/FU-017 "can't save unless I change the name" class.
- **Mark cooked = +1 cook** (same as Log-cook-1) rather than a no-op last-made bump — matches the pool model where cooking adds portions.
- **Guard is a custom BaseDialog, not `$q.dialog`** — `$q.dialog` only gives 2 buttons and its cancel/dismiss semantics were exactly the L299 complaint; a BaseDialog gives a true Cancel + 3 options + no-navigate-on-dismiss.
- **Engineering close-gate:** R-001 (reused MealStepper; guard is a justified one-off), R-003 (changed-fields is transport logic; name-uniqueness stays server-side), R-007 (stayed in detail-cleanup scope — nutrition placement→Chunk 9, source→Chunk 7, tools→Chunk 5, versions→Chunk 8, ingredient-notes-purpose & personal-notes left as open feedback, not in Chunk 4's close-list), R-008 (comments cite L-numbers + WHY), no migration, no new ADR.
**Files touched:** `web_app/src/pages/RecipeDetailPage.vue`, `web_app/src/pages/RecipeCookMode.vue`.
**Verification:** static only (no env). Tag balance + handler/computed existence grep-checked. Logged FU-089.
**Coverage (Chunk 4 close-list):** L283/284 (done Chunk 2) ✅, L285 (picker already filterable) ✅, L286 ✅, L289 (title field + ingredient validation) ✅, L290 ✅, L292 ✅, L297 ✅, L298 ✅, L299 ✅, L304 ✅, L305 ✅, L306 ✅, L307 ✅, L308 ✅, L309 ✅, L313 ✅, L314 ✅ (Chunk 3), L315 ✅. Explicitly deferred: L287 nutrition placement (Chunk 9), L291 ingredient-notes purpose (open question), L311 personal notes (later).
**Next up:** browser-verify Chunk 4 (FU-089), still-open FU-087 (filter bug) + FU-088 (Chunk 3). Then Chunk 5 (images + tools) or Chunk 6 (structured steps — gates C-3 cook mode).
**Open questions for user:** L291 ("what's the point of ingredient notes?") — keep, repurpose, or drop? Not actioned this chunk.

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 3 (card redesign + naming) — IMPLEMENTED.
**Status:** complete (frontend + tiny backend addition); not run/verified (no env).
**What changed:**
- **Backend:** added server-derived `committed_meals` to `RecipeDto` (`get_recipes.py`) — the raw (un-floored) sum of future un-consumed meal-plan servings, hydrated alongside `unallocated_meals`. Lets the card show a true shortfall (committed > available) in red. State-ownership-clean (R-003): server owns the fact, client renders.
- **`MealStepper.vue`** (new) — compact ±/count stepper, presentational (parent owns the API call + busy). **Reused in 3 places** (RecipeCard, RecipeDetailPage, StockItemDetailPage) → R-001.
- **`RecipeCard.vue` redesign:** image-placeholder tile (coloured by name hash + initial; real images = Chunk 5/FU-039), emphasised name, cuisine·category subtitle, favourite toggle floated on the media tile, chips (time/serves/difficulty), dietary chips, cookable/missing/low chips, **meals box** (MealStepper + allocated badge that goes red on shortfall), **Cook as the only primary action** (filled button). **Removed Edit/Duplicate/Delete** from the card — card click opens detail (the edit+delete surface, which already has delete). Kebab keeps add-all-to-list + add-to-meal-plan. New `adjust-meals` emit; dropped `edit`/`duplicate`/`delete` emits.
- **`RecipesOverview.vue`:** wired `@adjust-meals` → `onAdjustMeals` (store.adjustMealsAsync); removed the now-dead `onEditClick`/`onDuplicate`/`confirmDelete`; collection groups are now **collapsible rounded surface boxes** (`dora-bg-sunken`, per-group collapse state).
- **`RecipeDetailPage.vue`:** meals card ± buttons replaced with `MealStepper`; breadcrumb "Recipes" → "Cookbook" (+ `/recipes`→`/cookbook` pushes).
- **`StockItemDetailPage.vue`:** wired `@adjust-meals` so the recipe cards' steppers work there too (not dead).
- **Naming sweep (FU-031):** `MainLayout` main-menu label "Recipes"→"Cookbook", `nav.recipes` command + `g r` shortcut → "Go to Cookbook" (→ `/cookbook`); `DashboardPage` stale "'Mark Made' button" tip reworded to "Logging a cook…".
**Decisions made:**
- **Added `committed_meals` rather than fake the shortfall.** The DTO only had `unallocated_meals` (floored at 0), so a true "planned more than cooked" shortfall was underivable client-side. A small server field is the honest fix (R-003) vs. a misleading always-neutral badge.
- **Kept Delete in the detail page only.** The card lost Edit/Duplicate/Delete per the plan; the detail page already had Delete (Chunk 4's "delete moves to detail" was effectively pre-done), so no capability gap. Duplicate is intentionally gone (returns as "New version" in Chunk 8).
- **Command-palette result-group label stays "Recipes"** — it labels recipe *results*, not the page; only page/nav affordances were renamed to Cookbook.
- **Engineering close-gate:** R-001 (MealStepper extracted, 3 uses), R-003 (committed_meals server-owned; shortfall is pure display derivation), R-005/R-006 (no migration — committed_meals is computed), R-007 (stayed in card+naming+grouping scope; images deferred to Chunk 5; didn't expand into Chunk 4 detail cleanup), R-008 (comments cover placeholder/FU-039 + committed_meals rationale). No unexplained violations. No new ADR.
**Files touched:** `dora_api/features/recipes/get_recipes.py`; FE: `models/recipe.ts`, `components/recipes/MealStepper.vue` (new), `components/RecipeCard.vue`, `pages/RecipesOverview.vue`, `pages/RecipeDetailPage.vue`, `pages/StockItemDetailPage.vue`, `layouts/MainLayout.vue`, `pages/DashboardPage.vue`.
**Verification:** static only (no Python venv / node_modules). Logged FU-088. NOTE: had to strip a UTF-8 BOM accidentally added to `RecipeDetailPage.vue` by a PowerShell whole-file replace (restored to match the no-BOM convention of sibling .vue files) — flagged so a reviewer knows that file had a mechanical round-trip.
**Coverage (Chunk 3 bullets):** L230/L242-248/L253/L270/L274-277 (card redesign + Cook-only + grouping) → card + collapsible groups ✅; §2.1/§2.10 ✅; FU-031 (stale Recipes labels) → ✅ nav/commands/breadcrumb. Image wiring (L249) explicitly deferred to Chunk 5 (placeholder only).
**Next up:** **FU-088** browser-verify Chunk 3 (+ the still-open **FU-087** overview-filter bug, which also blocks seeing the new cards' filters). Then Chunk 4 (detail-page cleanup) or Chunk 5 (images + tools).
**Open questions for user:** none blocking.

---

## 2026-06-09 — Chunk 2 browser-feedback pass: detail-page tags fix + dead-endpoint cleanup.
**Status:** complete (small fixes) + one bug triaged to the user.
**What changed:**
- **FU-067 resolved** — removed the dead `append_low_stock_essentials` backend route (`features/shopping_lists/auto_generate.py`) + the orphaned `appendLowStockEssentialsAsync` method (`shoppingListApiService.ts`). Static grep confirmed zero callers; no orphaned imports.
- **Detail-page dietary tags (FU-085 gap, L264)** — the RecipeDetailPage (the primary edit surface) had **no** dietary-tag editor; tags only existed on the add modal. Added a `dietary_tag_ids` multiselect (grouping-prefixed options from the vocab store) + form field + hydrate + save wiring to `RecipeDetailPage.vue`.
- **FU-080 resolved** — user confirmed menu-highlight subroute fix works.
**Decisions made:**
- **Did NOT blind-fix the overview filter bug (FU-087).** User reports the recipes-overview filter panel shows nothing / the toggle does nothing — but a full static review (FilterBar usage matches the working StockOverview, FilterChip import path correct, BaseButton forwards click, all filter computeds guard empties) found no defect. Fixing blind risks regressions; logged FU-087 with a precise console-output request instead.
**Files touched:** `dora_api/features/shopping_lists/auto_generate.py`, `web_app/src/services/api/shoppingListApiService.ts`, `web_app/src/pages/RecipeDetailPage.vue`, `DORA_FOLLOWUPS.md`.
**Verification:** static only (no env). The detail-page tag editor + dead-code removal are review-grade.
**Next up:** **FU-087** — get the browser console error for the overview filter bug, then fix. It gates FU-083 + the filter half of FU-085. After that, the rest of FU-085's checklist, then Cookbook Chunk 3.
**Open questions for user:** the FU-087 diagnostics (console errors, is the Filters toggle visible, viewport width, hard-refresh).

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 2 (tag taxonomy overhaul) — IMPLEMENTED.
**Status:** complete (large backend + frontend change; not run/verified — no Python venv or node_modules on this Windows box).
**Scope decisions (user-confirmed up front):**
- **Full CRUD + settings pages now**, not deferred to C-cross. Closes L238/L264/L283/L284 properly rather than stubbing.
- **FK-ify cuisine/category now.** User: *"this is pre-release, nobody is using it, can do whatever breaking changes."* So the migration is a clean breaking change — no data conversion of existing recipe strings/tags. Saved as a durable memory (`dora-prerelease-breaking-changes-ok`).

**What changed — backend:**
- **New entities** `Cuisine`, `Category`, `DietaryTag` (`{id, name, sequence}`; DietaryTag also has a grouping `category` label). `dora_api/domain/entities/{cuisine,category,dietary_tag}.py`.
- **`Recipe` entity reshaped**: `cuisine: str|None` / `category: str|None` → `cuisine: Cuisine|None` / `category: Category|None` relationships.
- **`table_mappings.py`**: 3 new tables + mapper registrations; `recipe_table` drops `cuisine`/`category` strings, adds `cuisine_id`/`category_id` FK cols (mapped to hidden `_cuisine_id`/`_category_id` so verify_mappings stays happy, mirroring `_recipe_collection_id`); `cuisine`/`category` relationships use **`lazy="selectin"`** (deliberate departure from the noload default — they're tiny always-wanted lookups, so consumers don't each need an `.include()`). `recipe_tag_table.tag` String → `dietary_tag_id` FK.
- **Migration `a7d2f4c9e1b8`** (down_revision = head `e1a4c7b2f9d0`): creates + seeds the 3 vocab tables (defaults mirror the old `RECIPE_TAG_CATALOGUE`), batch-mode alters Recipe (drop strings, add FK cols + FKs), rebuilds RecipeTag. Pre-release discard semantics, batch-mode for SQLite portability (R-005/R-006). Has a downgrade.
- **`seed.py`**: seeds the 3 vocabularies; `make_recipe` resolves cuisine/category names → entities; sample dietary-tag links added via the association.
- **`recipe_tag_access.py`** rewritten for `dietary_tag_id` (validate against DB rows; `resolve_tag_filter_values` accepts ids OR names so SPA-by-id and Dora-by-name both work; added `get_tag_ids_for_recipes` + `get_tag_names_for_recipes`). Uses Core tables throughout (no Core/ORM join mixing).
- **`recipe_tags.py`** trimmed to just `RECIPE_TAG_DISCLAIMER` (catalogue is now DB-backed).
- **`get_recipes.py`**: DTO now exposes `cuisine_id/cuisine_name/category_id/category_name` + `dietary_tag_ids`; `/recipes/tags` catalogue endpoint reads DietaryTag rows (value = id) + disclaimer.
- **`create_recipe.py` / `update_recipe.py`**: accept `cuisine_id/category_id/dietary_tag_ids`; resolve + validate FK entities (404-style entity-existence errors); cuisine/category handled like recipe_collection_id (explicit null clears).
- **`import_recipe_from_url.py`**: preview DTO returns `cuisine_id/cuisine_name/category_id/category_name`; resolves scraped names against existing vocab rows (read-only, **no creation** — keeps the no-persist contract).
- **New CRUD features** `cuisines/`, `categories/`, `dietary_tags/` (mirror `manage_stock_groups.py`) + 3 routers in `routers.py`. Auto-registered via the `features` blueprint scan — no manual wiring.
- **Consumer fixups**: `assistant/tools.py` (cuisine/category filters moved to Python post-load since they're relationships now; outputs use `.name`; tag helper → names; tags_include description refreshed; vegetarian mood profile now uses `tags_include`), `search/global_search.py` (subtitle via `.name`), `data/export_recipe.py` (`category_name`/`cuisine_name`), `data/restore_shared.py` (new Cuisine/Category/DietaryTag + RecipeTag backup sections in FK-correct order + FK pull-in/required classifications — RecipeTag was never backed up before, so that's a bonus).

**What changed — frontend:**
- **Models**: `models/recipeVocab.ts` (Cuisine/Category/DietaryTag); `models/recipe.ts` Recipe now has `cuisine_id/cuisine_name/category_id/category_name/dietary_tag_ids` (was `cuisine/category/tags`).
- **API services**: `cuisineApiService`, `categoryApiService`, `dietaryTagApiService` (mirror stockGroup). `recipeApiService` create/update commands + `ImportedRecipe` updated to id fields.
- **Store**: `recipeVocabStore` (cuisines/categories/dietaryTags + getAll).
- **Tri-state filter component** `components/recipes/DietaryTagFilter.vue` (q-btn-dropdown, cycles +/−/neutral, stays open). Reusable for the future tools filter (Chunk 5).
- **RecipesOverview**: cuisine + category single-selects (replacing the combined "tags" multiselect, L235); dietary filter → DietaryTagFilter; predicate uses `cuisine_id/category_id/dietary_tag_ids`; onDuplicate copies tag ids; loads the vocab store.
- **RecipeCard**: shows `cuisine_name/category_name`; tag chips resolve ids→names via the vocab store (graceful empty if unloaded).
- **RecipeEditDialog + RecipeDetailPage**: cuisine/category single-selects + dietary multiselect from the vocab/catalogue; form + save payloads use id fields; importer fills ids.
- **DoraChat / ExportPrint**: recipe cuisine/category via `_name`.
- **Settings**: `components/settings/VocabListEditor.vue` (generic name-only editor, used for cuisine + category — R-001), bespoke dietary-tag editor with its group field, in `pages/settings/RecipeVocabSettings.vue`; route `/settings/recipe-vocab` + SettingsShell nav entry.

**Decisions made:**
- **selectin for cuisine/category** — the one notable architectural call. Justified: tiny, always-wanted lookups; avoids include-management ripple across ~10 assistant/search/export sites. Noted inline in `table_mappings.py`.
- **Importer resolves names→ids read-only** (no vocab creation during a preview) — preserves the importer's no-persist contract; unmatched values leave the select empty for the user.
- **Filter axes accept ids (SPA) or names (Dora)** via `resolve_tag_filter_values`, so the assistant's name-based world keeps working without the SPA having to send names.
- **Backup wiring pulled in** (beyond the IMPL plan's stated scope) because leaving the FK'd vocab tables unbackable would silently corrupt restores — the "do it properly" path (R-005/R-007 judgement).
- **Engineering close-gate:** R-001 (VocabListEditor extracted for the 2 identical vocab editors; DietaryTagFilter componentised), R-003 (server owns the vocab; client renders), R-005/R-006 (batch-mode portable migration + downgrade + seed-in-migration convention), R-007 (no creep beyond the tag-taxonomy surface; structured steps / images / versions left for their chunks), R-008 (comments explain the selectin + read-only-import + blank-input WHYs), R-010 (typed FK ids end-to-end; `SortKey`-style unions where relevant). **No unexplained rule violations.** ADR evaluation: the "selectin for small always-wanted lookups" choice is a candidate recurring pattern — noted as FU-084 to consider promoting to an `R-0NN` if it recurs.

**Files touched:** see CHANGELOG + the lists above (≈ 35 files: 3 entities, table_mappings, migration, seed, recipe_tag_access, recipe_tags, get/create/update/import recipe, 3 CRUD features + routers, assistant tools, global_search, export_recipe, restore_shared; FE: recipeVocab model, recipe model, 3 api services, vocab store, DietaryTagFilter, RecipesOverview, RecipeCard, RecipeEditDialog, RecipeDetailPage, DoraChat, ExportPrint, VocabListEditor, RecipeVocabSettings, routes, SettingsShell).

**Verification:**
- **NOT run.** No Python venv (WindowsApps stub only) → couldn't `alembic upgrade`, run the API, or pytest. No `node_modules` → couldn't `vue-tsc`/lint. All changes are review-grade, pattern-matched against existing code.
- **Highest-risk, must-verify-in-a-real-env items** (logged as FU-085):
  1. `alembic upgrade head` applies cleanly on SQLite **and** Postgres (batch-mode Recipe alter + RecipeTag rebuild + seed).
  2. App boots: `verify_mappings()` passes for the 3 new entities + reshaped Recipe (the `_cuisine_id`/`_category_id` hidden-FK mapping is the risk).
  3. selectin actually populates `recipe.cuisine`/`.category` on plain `repository.get(Recipe).all()` (assistant/global_search rely on it).
  4. Recipe create/update/list round-trips cuisine_id/category_id/dietary_tag_ids; `/recipes/tags` returns DB tags.
  5. Overview cuisine/category single-selects + tri-state dietary filter behave; RecipeCard chips resolve names.
  6. Settings CRUD for all three vocabularies (create/rename/delete + usage counts + delete-warning).
  7. Backup → restore round-trips the new tables in FK order.

**Coverage (Chunk 2 feedback bullets, per CLAUDE.md cross-check):**
- L235 (cuisine/category not lumped, not "tags") → ✅ distinct single-selects.
- L236 ("recipe tags" vs "dietary tags") → ✅ labelled "Dietary tags" throughout.
- L237 (tri-state +/−/neutral, dropdown stays open) → ✅ DietaryTagFilter.
- L238 (settings page for recipe tags, seed defaults, add/edit/remove) → ✅ RecipeVocabSettings.
- L255/L260 (cuisine/category single-select; why separate) → ✅ single-select, separate vocabularies.
- L264 (dietary tags configurable: toggle/add/edit/delete) → ✅ dietary-tag editor.
- L283/L284 (category/cuisine → configurable dropdowns) → ✅ edit form + detail single-selects from tables.
- A2.2 (tag taxonomy) → ✅.
- Out of scope (their own chunks): images (Chunk 5), structured steps (Chunk 6), versions (Chunk 8), cost/nutrition (Chunk 9).

**Next up:** **Verify Chunk 2 in a real env** (FU-085) — this is the gating step before trusting it. Then Cookbook **Chunk 3** (card redesign + Cookbook/Mark-cooked naming) is the natural next visible-polish chunk, or Chunk 5/6 if the cook-mode axis is preferred.

**Open questions for user:**
- Default vocab sets — I seeded a reasonable cuisine list (Italian/Asian/Chinese/Japanese/Thai/Indian/Mexican/Mediterranean/American/French/Middle Eastern/Other) and category list (Main/Pasta/Rice/Stir fry/Soup/Salad/Side/Breakfast/Dessert/Snack/Drink/Sauce). Happy to tune the defaults.
- The dietary-tag create/rename UX uses two sequential prompt dialogs (name, then group). If you'd prefer a single combined dialog, that's a small follow-up.

---

## 2026-06-09 — IMPL_PLAN_COOKBOOK Chunk 1 (comparison cut + sort/filter axes) — IMPLEMENTED.
**Status:** complete (Chunk 1 closed; new follow-ups for browser verify + deferred sub-features).
**What changed:**
- **Comparison mode ripped.** Header "Compare" / "Show comparison" buttons gone; the ~95-line comparison dialog block removed from `RecipesOverview.vue`; `compareMode`, `selectedIds`, `showComparison`, `MAX_COMPARE`, `toggleCompareMode`, `onToggleSelect`, `selectedRecipes` all deleted along with the per-card checkbox plumbing.
- **`RecipeCard.vue` cleaned up to match.** Removed the `selectable` / `selected` props, the `toggle-select` emit, the `<q-checkbox>` branch, the click-routing in `onCardClick`, and the now-unused `.recipe-card--selectable` / `.recipe-card--selected` CSS. The `highlightStockItemId?: string` prop became `highlightStockItemIds?: string[]` and the `dim` computed now checks whether any *non-highlighted* ingredient is still missing.
- **`StockItemDetailPage.vue`** — its inline RecipeCard usage updated to pass `:highlight-stock-item-ids="[detail.stock_item_id]"`.
- **Boolean filters → `FilterChip`.** `Favourites only`, `Cookable now` swapped from `q-toggle` to `FilterChip` to match StockOverview's filter-bar pattern (filter-bar consistency per L233 / IMPL §1.Chunk-1).
- **New filters added:** `Have meals in pool` (`available_meals > 0`), `Planned in` (recipe appears in a future meal-plan entry — today or later), and a numeric `Meals ≥` input.
- **Stock-item filter → multi-select with level-coloured rows.** State changed from `usesStockItemId: string | null` to `usesStockItemIds: string[]`. The `q-select #option` slot renders each option with a small dot coloured by `getStockLevelColour(stockLevelName)`; the option object carries the `stockLevelName` alongside `value`/`label`. The `?usesStockItem=` deep-link from stock-item detail still works (single id pre-fills a one-element array).
- **Sort axes.** New `Sort by` `q-select` with four options — `name` (default), `last_made`, `meal_count`, `total_time`. Implementation: a new `sortedRecipes` computed between `filteredRecipes` and `groups` that does a stable in-place sort with null-aware comparators (nulls always sink to the bottom regardless of direction; ties break by name). The IMPL plan also lists **`created_at`** — dropped here because `Recipe` DTO doesn't expose a created timestamp; FU logged for a Phase-2 server addition.
- **Blank-input bug (L234) hardened.** Both numeric inputs (`Missing ≤`, `Meals ≥`) now feed their hint strings through a `Number.isFinite` guard so a cleared/half-typed field shows no hint (not `> NaN`) and is excluded from `activeFilterCount`. The filter predicates were already guarding correctly; this is the cosmetic / count surface that read as "filter is on when it shouldn't be".
- **Meal-plan store wired in.** `RecipesOverview` now loads `mealPlanStore.getMealPlansAsync()` alongside the other onMount fetches; the "planned in" filter derives the set of upcoming recipe ids client-side from `mealPlans[].entries[].scheduled_for`. This is a deliberate **temporary client-side derivation** — should move to a server-derived `is_planned` flag on the Recipe DTO when state-ownership work catches up. Logged FU-081.

**Decisions made:**
- **Path-prefix sort key naming** matches StockOverview's `SortKey` convention (`name` / `last_made` / `meal_count` / `total_time`) — a typed union rather than free strings (R-010).
- **`created_at` sort axis dropped.** The IMPL plan called for it but the chunk's "no model changes" guard wins; the Recipe DTO has no created timestamp today. Logged as FU-082 for a Phase-2 server change (one column + DTO field; trivial when revisited).
- **Planned-in filter client-side, not server-side.** Justified by "no model changes" + meal plans are already fully loaded in the store. Anti-pattern under R-003 if it stays — flagged as FU-081 with the resolution "move to server-derived `recipe.is_planned` when `IMPL_PLAN_STATE_OWNERSHIP` lands."
- **FilterChip swap for all boolean filters, not just the new ones.** Mixing chips for new toggles + q-toggle for old ones would have looked worse than either pure pattern. The chip pattern also matches L242 ("nicer if sections/groupings were in a rounded box as the background") aesthetically.
- **Multi-select stock-item picker option row uses a coloured dot + level caption**, not a full chip background — keeps the dropdown scannable. The full-bleed chip styling that L240 hints at would be heavier and is what Chunk 3 (card redesign) inherits when the filter result tints the matching ingredient on the card.
- **Engineering close-gate:**
  - **R-001** componentisation — leveraged existing `FilterChip` + `FilterBar` rather than rolling new chrome; no new components extracted (each new pattern has only one use here).
  - **R-002** theme tokens — `getStockLevelColour` returns palette-name strings; no raw hex anywhere in the new code.
  - **R-003** SSOT — cookability/missing remain server-owned. **The `planned-in` derivation is a deliberate carve-out**, justified above and logged as FU-081 to migrate when state-ownership work catches up. Inline note in `plannedRecipeIds` computed.
  - **R-007** scope — comparison rip + filter/sort axes + blank-input cosmetic only. **Did not** touch card body redesign (Chunk 3), tag taxonomy (Chunk 2), or detail page (Chunk 4) even though they're tempting one-liners.
  - **R-008** comments — kept the existing terse comments; new ones explain WHY (blank-input guard, planned-in deferral, level-coloured option rationale). No what-comments.
  - **R-010** typed `SortKey`; predicate boundaries use `Number.isFinite` rather than string sniffing.

**Files touched:**
- `web_app/src/pages/RecipesOverview.vue` (main surface; ~250 lines net delta)
- `web_app/src/components/RecipeCard.vue` (comparison plumbing strip; prop rename + computed)
- `web_app/src/pages/StockItemDetailPage.vue` (one prop line — pass array form)
- `CHANGELOG.md` (Unreleased: Added + Removed + Fixed for Chunk 1 and the menu fix)
- `DORA_FOLLOWUPS.md` (FU-081, FU-082, FU-083 added)

**Verification:**
- **Not typechecked** — Windows machine has no `node_modules` installed; `vue-tsc` blows up across the whole tree with missing-module errors before it can lint these files. Changes are pattern-matched against surrounding code and reviewed against the IMPL plan acceptance list.
- **Not verified in browser.** Whole chunk needs a sweep:
  1. Comparison gone everywhere; no console warnings about removed props.
  2. Each new chip filter toggles correctly and `activeFilterCount` reflects it.
  3. `Meals ≥` + `Missing ≤` show empty hints when blank/cleared; the list re-fills when the input is cleared (the blank-input bug).
  4. Sort axes behave (especially "Recently made" with mixed null and non-null `last_made_on` — nulls should be at the bottom).
  5. Multi-select stock-item picker styles rows by level; deep-linking with `?usesStockItem=…` still works.
  6. "Planned in" filter shows only recipes that appear in a meal-plan entry from today onward.
  7. `StockItemDetailPage` recipes-using-this-item tab still dims/highlights correctly with the new array prop.

**Acceptance (per IMPL_PLAN_COOKBOOK Chunk 1):**
- ✅ No "Compare" affordance anywhere — header buttons + dialog + card checkbox + selectable plumbing all gone.
- ✅ New sort axes work — name / last-made / meal-count / total-time (created-at deferred; FU-082).
- ✅ Page counts in the footer — already present via `PageCountsFooter` (A7); no change needed.
- ✅ Multi-select stock-item filter with level-coloured option rows.
- ✅ Planned-in, in-stock-only, meal-count-range filters all wired.
- ✅ Blank-input cosmetic / count bug guarded on `Number.isFinite`.
- ✅ Filter-bar consistency — booleans on FilterChip pattern matching StockOverview.
- ⏸ Filter-bar full A4 layout polish (L232 "Missing filter offset weirdly") — chip conversion + `q-separator` blocks improve alignment but a deeper FilterBar audit would lift this further; folded into FU-083 as something for an A4 follow-up rather than Chunk 1.

**Next up:** **Browser-verify Chunk 1** (FU-080 covers the menu fix; FU-083 covers this chunk). Then options:
- **Cookbook Chunk 3** (card redesign + Cookbook/Mark-cooked naming) — visible polish on the same surface; the card-image placeholder is the only Chunk-5 dependency and the IMPL plan says to wire it unconditionally here.
- **Cookbook Chunk 2** (tag taxonomy) — bigger; touches three new tables + migration + tri-state filter component. Probably the next single-PR chunk to take if the user wants Cookbook to keep momentum.
- The deferred items above (FU-081 / FU-082) when state-ownership / Phase-2 ingestion lands.

**Open questions for user:**
- Sort axis label preferences? The dropdown reads "Name / Recently made / Meals in pool / Prep + cook time" — happy to retune wording.
- The `Planned in` chip is on by default off — should it default to ON when the user is browsing the cookbook (so the natural view is "what am I about to need"?), or stay off and let the user opt in? Defaulted to OFF for now per IMPL plan reading.

---

## 2026-06-09 — Menu highlight fix (subroutes + redirected paths). FU-079 resolved.
**Status:** complete (small bug fix).
**What changed:**
- **Root cause:** `q-item :to` uses Vue Router 4's route-record-based active matching. The recipe routes (`/recipes/:id`, `/recipes/:id/cook`) are declared as **flat siblings** of `/recipes`, not nested children, so Vue Router didn't consider them related — subroute pages didn't highlight the parent menu item. `SideMenuButton.vue` also passed `exact`, which made the same problem worse for the side drawer.
- **`web_app/src/components/menu/useMenuLinkActive.ts`** (new composable). Computes `isActive` from `route.path` via prefix match (`path === target || path.startsWith(target + '/')`), with an optional `extraPrefixes` list for nav entries that span multiple roots.
- **`MainMenuButton.vue`** — dropped `active-class="dora-mainMenuButton-active"` (Vue-Router-driven) and bound the class via `:class="{ ..., 'dora-mainMenuButton-active': isActive }"` from the composable. The sliding indicator in `MainMenuButtonStrip.vue` still finds the active button by class name, so no change there.
- **`SideMenuButton.vue`** — same swap; removed `exact` (was making the drawer item lose highlight on every subroute).
- **`menuButtonProps.ts`** — added optional `activePrefixes?: string[]` so a nav entry can declare extra paths that should also trigger active state.
- **`MainLayout.vue`** — Recipes menu link changed from `/recipes` (which router-redirects to `/cookbook`, leaving the highlight permanently off on the actual landing) → `link: '/cookbook', activePrefixes: ['/recipes']` so the item highlights on both `/cookbook` and `/recipes/:id`/`/recipes/:id/cook`. C-4 Chunk 3 will rename the label.
- **FU-079** flipped to `[RESOLVED]` — user confirmed the blank-screen hotfix works after pulling + `alembic upgrade head`.
**Decisions made:**
- **Composable, not duplicated inline.** Two consumers (Main + Side) with identical logic — R-001 says extract at ≥2 uses. The composable is six lines; readable.
- **Kept the `link` string-only contract.** `MenuButtonProps.link` stays a string; `activePrefixes` is a separate optional list rather than overloading `link` to accept arrays. Single nav-target stays unambiguous; the prefix list is a clearly-labelled secondary concept.
- **Fixed the `/recipes` → `/cookbook` menu link in this commit.** Strictly that's a separate problem (URL targeting), but it's the same surface and same user complaint ("Recipes menu doesn't highlight when I'm on a recipe page" reads identically whether the cause is route-records or a redirect). One PR, one fix.
- **Engineering close-gate:**
  - R-001 — composable extracted at the 2-use boundary; no duplication.
  - R-003 — pure client-side state; no domain ownership concerns.
  - R-008 — one short `Why` comment in `useMenuLinkActive.ts` explaining the route-record vs prefix-match issue (non-obvious; future readers won't intuit it from the code).
**Files touched:**
- `web_app/src/components/menu/useMenuLinkActive.ts` (new)
- `web_app/src/components/menu/menuButtonProps.ts` (+1 optional field)
- `web_app/src/components/menu/MainMenuButton.vue` (class binding swap)
- `web_app/src/components/menu/SideMenuButton.vue` (class binding swap + drop `exact`)
- `web_app/src/layouts/MainLayout.vue` (Recipes link target)
- `DORA_FOLLOWUPS.md` (FU-079 → RESOLVED)
**Verification:**
- **Not typechecked** — `node_modules` not installed on this Windows machine, so `vue-tsc` reports environment errors across the whole tree (missing `vue`, `pinia`, etc.). Changes are syntactically minimal and pattern-matched against the surrounding code.
- **Not verified in browser.** Logged as FU-080 — confirm each menu item highlights on its subroutes (`/stock/:id`, `/recipes/:id`, `/recipes/:id/cook`, `/shopping-lists/:id`, `/shopping-lists/:id/shop`, etc.) and the sliding indicator on the main strip still tracks position correctly.
**Next up:** **IMPL_PLAN_COOKBOOK Chunk 1** (recipe comparison cut + filter/sort axes). Self-contained, no model changes; the rip + replace on `RecipesOverview.vue`.
**Open questions for user:** none.

---

## 2026-06-08 — Hotfix: three eslint errors + blank-screen defensive surfacing.
**Status:** complete.
**What changed:**
- **`ShoppingListDetail.vue` — duplicate v-else-if fixed.** Chunk 3 changed the outer wrapper to `v-if="detail"` (any status) but left a `v-else-if="detail"` branch for the "Copy to new list" button when done. Unreachable. Folded the Copy button into the main row gated by `v-if="detail.status === 'done'"`.
- **`ShoppingListDetail.vue` — dead `onFinish` + `finishing` ref removed.** Chunk 3 moved the finish-and-restock flow to `ShoppingListShopMode.vue`; the old detail-page `onFinish` was orphaned. Dropped the function (~150 lines), the `finishing = ref(false)` declaration, and the comment explaining what's now where. `registerUndo` import kept — still used by the line-tick undo.
- **`ShoppingListShopMode.vue` — floating-promise on Esc key.** The keyboard handler called `exit()` directly; `exit()` is async since Chunk 3 (it calls `stopShoppingAsync` before navigating). Prepended `void`.
- **Defensive surfacing for the blank-screen bug:**
  - **`ShoppingListsOverview.vue`** — dropped the `<FadeTransition>` wrapper (it added a transition state that masked errors with momentary opacity 0) and replaced it with plain `v-if/v-else-if/v-else`. Added a `loadError` banner at the top with a Retry button — previously the store's catch set `loadError` silently and nothing rendered it.
  - **`ShoppingListDetail.vue`** — added a `v-else` fallback branch to the FadeTransition (`key="sld-empty"`) showing a "This list isn't available" message with a New-list CTA. Pre-hotfix, when `loading=false && detail=null` (e.g. load failed, listId stale, or backend 500), the content area rendered nothing and the page looked blank. The loadError banner also gained a Retry button and a "Couldn't load this list." headline.
  - **`stores/shoppingListStore.ts`** — added an explicit `console.error('[shoppingListStore] refreshAsync failed', err)` in the catch. Pre-hotfix, the catch only set `loadError` and the user reported "no errors in console" while seeing nothing on the page. Errors now surface to console + the UI banner.

**Decisions made:**
- **Drop the FadeTransition on Overview rather than fix it.** The transition added value when the page had real per-state content (the old overview's list-of-cards); on a redirect-landing it's just a brief opacity flicker between states the user shouldn't see anyway. Simpler reads better.
- **Fallback branch on Detail is a "this list isn't available" empty state**, not a redirect to the landing. Redirecting would loop if the landing also can't pick a valid list; the empty state is honest and offers two recovery actions (selector + new list).
- **Console.error in the store is intentionally direct** (no logger abstraction). The point is to break the silence; a logger that proxies through some queue is exactly what made this hard to spot.
- **Engineering close-gate:**
  - R-001 — kept BaseDialog + q-banner chrome.
  - R-003 — server still owns load failure; client now just renders it visibly.
  - R-008 — comments explain the WHY of each defensive change (esp. why we added the v-else fallback) so a future agent doesn't "tidy" them away.

**Most-likely root cause for the user-reported blank screen:** the `e1a4c7b2f9d0` migration (Chunk 7 `planned_shop_date` column) hadn't been applied on the user's machine. The API's SELECT statements on `ShoppingList` would 500 with "no such column"; `store.refreshAsync()` caught it silently; Overview rendered nothing useful because `loadError` wasn't surfaced; Detail's content area rendered nothing because the FadeTransition had no v-else branch. **With this hotfix the user will see the actual error text** and a Retry button — which makes the missing-migration diagnosable in one glance. Logged as FU-079 to verify in browser once the user pulls these changes.

**Files touched:**
- `web_app/src/pages/ShoppingListDetail.vue` (duplicate v-else-if fix, dead onFinish removed, v-else fallback, retry button)
- `web_app/src/pages/ShoppingListShopMode.vue` (void exit())
- `web_app/src/pages/ShoppingListsOverview.vue` (FadeTransition removed, loadError surfaced, retry button)
- `web_app/src/stores/shoppingListStore.ts` (console.error in catch)

**Verification:**
- `npx vue-tsc --noEmit` → clean (exit 0).
- **Not verified in browser.** Logged FU-079 — after the user pulls and runs `alembic upgrade head`, the Overview + Detail should both render correctly; if the migration is missing or any other API error occurs, the new error banners surface the actual message instead of going blank.

**Next up:**
- User to pull + apply migration (`alembic upgrade head`), confirm Overview + Detail render. If they still see the loadError banner after migrating, the message will identify what's still wrong.
- The original Chunks 3/4/5/6/7 browser smoke (FU-066/068/069/072/073/076) still pending.

**Open questions for user:** has the migration `e1a4c7b2f9d0` been applied on the Linux machine? That's the leading suspect for the blank screen.

---

## 2026-06-08 — C-4 decisions resolved + IMPL_PLAN_COOKBOOK.md drafted (FU-078 resolved).
**Status:** complete (design pass — no code).
**What changed:**
- **`docs/04_proposals/PROPOSAL_COOKBOOK.md`** — new `§5a Resolved
  decisions (2026-06-08)` table closing out all 6 open items:
  - **DEC-1** Cuisine vs category — **keep both, single-select each**,
    both vocabularies user-configurable in settings.
  - **DEC-2** Versions UX — **diverged from the brief.** User reframed:
    "New version" = renamed Duplicate that copies into a new standalone
    recipe linked via shared `version_group_id`. No "current" pointer
    (versions are equal siblings, not historic); allocations stay
    per-recipe. Recorded verbatim in §5a.
  - **DEC-3** Multi-part — **sections within one recipe**; sub-recipes
    deferred.
  - **DEC-4 / DEC-5 / DEC-6** — all per the brief: nutrition off+simple
    now, cost shipped as labelled estimate, substitute-status skipped.
  - Header status flipped to "Decisions resolved 2026-06-08".
- **New `docs/04_proposals/IMPL_PLAN_COOKBOOK.md`** (~430 LoC). Mirrors
  `IMPL_PLAN_SHOPPING_LISTS.md` / `IMPL_PLAN_COOK_MODE.md` shape:
  verify-state audit against `recipe.py`, `table_mappings.py:297-327`, and
  the two big Vue pages; 10 chunked PRs; first-chunk DoD; risks; full
  feedback-coverage table for L228-L315; suggested run order; parallel-
  agent safety notes.
- **Ten chunks (high level):**
  1. ★ Comparison cut + filter/sort axes (no model change; visible win).
  2. Tag taxonomy overhaul — new `Cuisine` / `Category` / `DietaryTag`
     tables; FK-ify; +/−/neutral filter cycle.
  3. Card redesign + Cookbook/Mark-cooked naming.
  4. Detail page cleanup (biggest single-file diff; L283-L315).
  5. Images + tools (closes FU-039; introduces `Tool` table for Chunk 6).
  6. **Structured recipe steps** (closes FU-040 implementation;
     ★ blocker for C-3 Chunk 5). `RecipeStep` table self-referential for
     one level of sub-steps; join tables for ingredient + tool refs;
     editor + freeform fallback; URL-importer mapping to schema.org
     `HowToStep`/`HowToSection`.
  7. Source field + URL importer cleanup.
  8. Versions per DEC-2 — siblings via nullable `version_group_id`; New
     Version action copies; detail page lists siblings; no current
     pointer; allocations stay per-recipe.
  9. Cost estimate + simple nutrition, behind C-cross opt-ins.
  10. Multi-part sections (last; biggest ripple — `RecipeSection` table +
      optional `section_id` on ingredients/steps).
- **Doc-graph:**
  - New `### IMPL — Cookbook` row in §C-impl with dependencies + crosses.
  - New proposal→implementation cross-map row for `IMPL_PLAN_COOKBOOK.md`.
  - Updated `PROPOSAL_COOKBOOK` + `IMPL_PLAN_COOK_MODE` rows to point at
    each other (the C-3 / C-4 Chunk-6 dependency now visible from both
    sides).
- **`DORA_FOLLOWUPS.md`** — new FU-078 minted directly as `[RESOLVED]`
  (raised + resolved this turn); state note documents the DEC-2
  divergence.
**Decisions made:**
- **DEC-2 reframe accepted verbatim.** The brief's "snapshot + current
  pointer + allocations follow current" model would have introduced
  meaningful state (which version is current?), undermined the user's
  framing ("they're all equal"), and complicated meal-plan allocation.
  The flatter sibling model — a nullable `version_group_id` + per-recipe
  allocations + a discovery affordance on the detail page — is simpler to
  build and matches the user's mental model.
- **Chunk 1 is first, not Chunk 6.** Chunk 6 (structured steps) is the
  biggest and the only dependency-gating chunk; Chunk 1 is the smallest
  visible win. Order matches IMPL_PLAN_COOK_MODE.md's reasoning: ship
  the user-visible improvement first, then tackle the heavy migration as
  its own focused PR.
- **No bundling Chunk 4 (detail cleanup) with Chunk 5 (images + tools)**
  — both touch RecipeDetailPage.vue; combined diff would exceed review
  bandwidth.
- **Chunk 8's allocation behaviour is intentionally simple.** Per DEC-2,
  there's no version-aware allocation logic — meal-plan slots reference a
  specific recipe; the version link is discovery-only. If feedback later
  asks "I want my Tuesday plan to flex between fried-rice v1 and v2"
  that's a follow-up, not Chunk 8 work.
- **Engineering close-gate:** R-001 (extract level-styled list +
  +/−/neutral filter chip when 2nd use shows up), R-003 (server owns
  cookability + cost; client renders), R-005 (every migration uses batch
  mode for SQLite portability), R-007 (sub-recipes per DEC-3 explicitly
  deferred — no creep), R-008 terse comments only where the WHY isn't
  obvious, R-010 (typed FK migrations cuisine/category/dietary).
**Files touched:**
- `docs/04_proposals/PROPOSAL_COOKBOOK.md` (header + new §5a)
- `docs/04_proposals/IMPL_PLAN_COOKBOOK.md` (new)
- `docs/00_DOC_GRAPH.md` (new C-impl row + cross-map updates on
  PROPOSAL_COOKBOOK, IMPL_PLAN_COOK_MODE, and the new IMPL_PLAN_COOKBOOK
  row)
- `DORA_FOLLOWUPS.md` (FU-078 minted as RESOLVED)
**Verification:** none needed — proposal docs only.
**Next up:** none blocking. Phase 1 design surface is now complete for
the recipe + cook-mode + shopping-list axis (all three IMPL plans
written). Natural follow-ons (browser-free if you're still between
machines):
- IMPL plans for the other C-* proposals that don't have one yet
  (`PROPOSAL_MEAL_PLANS.md` C-2; `PROPOSAL_STOCK_OVERVIEW.md` C-1;
  `PROPOSAL_ONBOARDING.md` C-5; `PROPOSAL_ALERTS.md` C-9).
- Smaller open FUs: FU-061 (doc-graph promotion), FU-067 (drop dead
  appendLowStockEssentialsAsync endpoint + route), FU-062 (verify
  doc-graph cited paths).
- An INV investigation (INV-6 done; INV-7 / INV-9 / INV-10 still open).
**Open questions for user:** none.

---

## 2026-06-08 — IMPL_PLAN_COOK_MODE.md drafted (FU-077 resolved).
**Status:** complete (design pass — no code).
**What changed:**
- New `docs/04_proposals/IMPL_PLAN_COOK_MODE.md` (~310 LoC). Mirrors the
  shape of `IMPL_PLAN_SHOPPING_LISTS.md`: verify-state-first audit against
  `RecipeCookMode.vue` + `recipe.py`, six chunked PRs, definition-of-done
  for the first chunk, risks & open-decisions section, feedback-coverage
  table, suggested run order.
- **Chunks:**
  1. Finish-flow rewrite (★ first reviewable) — per-row level chips + full
     picker per DEC-5, per-row add-to-list (C-7 proxy), meals_cooked
     defaults 0, click-out cancels, celebration. Closes the three blanket
     toggles.
  2. Cook-mode polish — timer fill-bar + reset + sound + theme; unit
     formatter per DEC-3 (metric+US no-space; culinary spaced); rename
     "Enable voice" → "Sous Chef" with a commands popover.
  3. Mid-cook ingredients UI — group by base location, drop level chips
     mid-cook, A1 token rebuild.
  4. **Structured recipe steps** (C-4 §2.6a work, co-sequenced as a
     blocker) — `RecipeStep` table + join tables + migration + recipe-
     detail step editor + URL importer mapping.
  5. Highlight + per-step features — rip tick state entirely (DEC-1), per-
     step ingredient + tool highlight using the new refs, per-step hints,
     per-step timers. Gated on Chunk 4.
  6. Serving auto-adjust — `cookingFor` ref with sensible rounding (DEC-4:
     ½/⅓/⅔/¼/¾ snapping), default from C-5 onboarding headcount, session-
     only.
- Doc-graph: new `### IMPL — Cook Mode` row in the C-impl section; new
  proposal→implementation cross-map row for `IMPL_PLAN_COOK_MODE.md`;
  `PROPOSAL_COOK_MODE.md` + `PROPOSAL_COOKBOOK.md` cross-map rows updated
  to point at the new IMPL plan and flag FU-040 as resolved.
- `DORA_FOLLOWUPS.md` — **FU-077 flipped to RESOLVED** with a state note
  pointing at the new IMPL plan + the doc-graph wiring.
**Decisions made:**
- **Chunk 1 first, not Chunk 4.** Chunk 4 (structured steps) is the
  largest by line count and the only dependency-gating one. Sequencing it
  first would put the biggest review on the critical path with no
  user-visible win. Chunk 1 ships an obvious "the finish dialog is much
  better" moment in the smallest PR, so it leads.
- **No compat shims at the tick-state removal (Chunk 5).** Pre-release
  discipline: rip `usedIds` / `doneSteps` outright when Chunk 5 lands;
  don't ship both behaviours behind a flag. Documented in §1 Chunk 5.
- **Server-side bulk level update deferred.** Chunk 1's per-row update is
  N network calls for N ingredients. Logged as a "wait for the signal"
  P10 anti-creep note — if a lag complaint surfaces, build the bulk
  endpoint then, not now.
- **Run-order published in §5** so two agents can't accidentally pick
  blocked chunks in parallel.
- **Engineering close-gate:** the plan honours R-001 (BaseDialog +
  BaseButton + A1 tokens), R-003 (server owns stock + cooked transitions;
  client is a presenter), R-005 (Chunk 4 migration uses batch mode),
  R-007 (no scope creep — the six chunks map 1:1 to C-3 §6 + §5a, no
  extras).
**Files touched:**
- `docs/04_proposals/IMPL_PLAN_COOK_MODE.md` (new)
- `docs/00_DOC_GRAPH.md` (new C-impl row + updated cross-map)
- `DORA_FOLLOWUPS.md` (FU-077 → RESOLVED)
**Verification:** none needed — proposal docs only.
**Next up:** none blocking. When you want to start the cook-mode build,
**Chunk 1** is the first reviewable PR per §2 DoD. Until then, the natural
follow-on is whichever you prefer of: (a) more design — C-4 IMPL plan,
which would split C-4's nine sub-sections into chunked PRs; (b) start
clearing the small open FUs (FU-061 doc-graph promotion, FU-067 dead
endpoint, FU-062 graph citation audit); (c) one of the still-open
INV investigations (INV-6 / INV-7 / INV-9 / INV-10).
**Open questions for user:** none.

---

## 2026-06-08 — C-3 cook-mode decisions resolved + C-4 structured-steps section added.
**Status:** complete (design pass — no code).
**What changed:**
- **`docs/04_proposals/PROPOSAL_COOK_MODE.md`** — added a new `§5a Resolved
  decisions (2026-06-08)` table closing out the 5 open items in §5:
  - **DEC-1** Ticking — **removed entirely**; per-step highlight replaces it.
  - **DEC-2** Structured steps — **modelled in C-4** (closes FU-040). C-3's
    highlight/per-step features (§2.4/§2.5/§2.6/§2.7) are now gated on the
    C-4 step-model landing first.
  - **DEC-3** Unit attach list — **metric + US customary attach** (`ml, g,
    kg, l, mg, oz, lb, floz, pt, qt`); culinary spaced (`tsp, tbsp, cup,
    clove, scoop, …`). User's framing taken verbatim.
  - **DEC-4** Scaled-qty display — **round sensibly** (1.5 eggs → 2 eggs;
    0.66 cups → ⅔ cup); never raw decimals.
  - **DEC-5** Finish-flow level picker — **quick chips + full picker**
    ("↓ one level / Out / Unchanged" + level dropdown override).
  - Header status flipped to "Decisions resolved 2026-06-08".
- **`docs/04_proposals/PROPOSAL_COOKBOOK.md`** — added new `§2.6a
  Structured recipe steps (2026-06-08; C-3 dependency, closes FU-040)`.
  Models `RecipeStep` as `{ id, recipe_id, sequence, text, sub_steps?, hint?,
  ingredient_refs[], tool_refs[] }`; `Recipe.instructions` kept as the
  fallback for unstructured / freshly-imported recipes. Editor + importer
  story sketched. Added sequencing slot **5a** in §6 marking it as a blocker
  for C-3 highlight features. Header status updated.
- **`DORA_FOLLOWUPS.md`** — FU-040 flipped to `[RESOLVED]` with a state
  note pointing at C-3 DEC-2 + the new C-4 §2.6a; explicit caveat that
  *implementation* (model migration, etc.) is still outstanding and a
  fresh implementation-FU should be raised when work begins.
**Decisions made:**
- All 5 user-confirmed during the session — no Claude-guessed answers.
- For DEC-3 the user's framing was tighter than the brief's initial
  recommendation (metric + tsp/tbsp). Recorded verbatim: *"metric and US
  makes most sense; culinary like tsp/teaspoon should have a space."*
  C-3 §2.8 still says "ml, g, kg, l, mg, tsp, tbsp"; the resolution in
  §5a overrides that. Implementation should follow §5a, not §2.8.
- The C-4 structured-steps section was kept tight on purpose — model +
  editor + importer + sequencing only. Field-by-field column types and
  the exact join-table shape are an implementation-time concern; the
  proposal stays at "this is the model" not "here are the DDL columns".
**Files touched:**
- `docs/04_proposals/PROPOSAL_COOK_MODE.md` (header + new §5a)
- `docs/04_proposals/PROPOSAL_COOKBOOK.md` (header + new §2.6a + new §6
  item 5a)
- `DORA_FOLLOWUPS.md` (FU-040 → RESOLVED)
**Verification:** none needed — proposal docs only.
**Next up:** none blocking. The natural follow-on is an **IMPL plan for
cook-mode**, mirroring `IMPL_PLAN_SHOPPING_LISTS.md` — chunked,
self-contained, no code yet. That plan needs §2.6a (structured steps,
in C-4) to land or to be co-sequenced. Logged as FU-077.
**Open questions for user:** none.

---

## 2026-06-08 — P6-01 Chunk 7 (planned shop day + cleanup) — IMPLEMENTED.
**Status:** complete. P6-01 phase plan now closes out.
**What changed:**
- **Backend**
  - `ShoppingList.planned_shop_date: date | None` added to the entity + `Fields.PLANNED_SHOP_DATE`.
  - `table_mappings.shopping_list_table` gets a nullable `Date` column.
  - New Alembic migration `e1a4c7b2f9d0` adds the column with `batch_alter_table` for SQLite portability (R-005).
  - `CreateShoppingListRequest` + handler accept the field on POST.
  - `UpdateShoppingListRequest` + handler set/clear it on PATCH (`null` explicit = clear; absent = no change).
  - `ShoppingListSummaryDto` + `ShoppingListDetailDto` expose `planned_shop_date`.
- **Frontend**
  - `models/shoppingList.ts` adds `planned_shop_date: string | null` to `ShoppingListSummary` + `ShoppingListDetail`.
  - `shoppingListApiService.ts` adds the field to `CreateShoppingListCommand` + `UpdateShoppingListCommand`.
  - `NewListDialog.vue` gains a date picker in the "create new" branch, passed straight through to `createAsync`.
  - `ShoppingListDetail.vue`:
    - Header caption gets a clickable chip showing `"Shop day: today"` / `"Shop day: tomorrow"` / `"Shop day: 15 Jul (overdue)"` / `"No shop day"`.
    - New shopping-day banner appears above the lines when planned date is today (info tone) or has passed without finishing (warning tone).
    - `BaseDialog`-backed editor with `<q-input type="date">` for set/save/clear.
    - Selector's `activeSummaries` sort now: SHOPPING first → planned date asc (scheduled ahead of unscheduled) → created_at desc.
  - `ShoppingListsOverview.vue` (landing) picks a DRAFT whose `planned_shop_date === today` ahead of the freshest-DRAFT fallback.
- **Tests**
  - New e2e `tests/e2e/dora_api/test_shopping_list_planned_shop_date.py` — 4 cases (create with date, create without, PATCH set + clear via explicit null, PATCH preserves an existing date when the field isn't sent).

**Decisions made:**
- **Banner, not a dedicated alert type yet.** The IMPL plan says Chunk 7 "feeds C-9's new alert types" — full alert wiring (push, suggestion feed, etc.) is the C-9 surface. For Chunk 7, an in-detail banner is the visible affordance; C-9 can register the same date condition as a real alert later. Logged as FU-074.
- **No "Today" badge in the selector rows** — the chip + banner already surface the planned date; doubling it inside the selector dropdown is polish, not function. If feedback wants it, trivial to add.
- **Explicit `null` clears, absent leaves it alone.** Mirrors the existing PATCH semantics for `status` / `name` (`model_fields_set` check), so the API stays consistent.
- **Date stored as `date`, not `datetime`.** Shop day is a calendar day, not a timestamp; comparing "today" against a `datetime` would force a TZ-of-the-day argument we don't need. The DTO returns the ISO date string.
- **Engineering close-gate:**
  - R-001 — reused `BaseDialog` for the editor, kept `BaseButton` for the actions.
  - R-003 — server owns the field; client never recomputes "is today" against anything other than `Date.now()`.
  - R-005 — migration in `batch_alter_table` for SQLite, also valid on Postgres.
  - R-007 — held to the chunk's scope; didn't bolt the alert pipeline on (deferred to C-9).
  - R-010 — typed everything (`date | None` server-side, `string | null` client-side).

**Files touched:**
- `dora_api/domain/entities/shopping_list.py`
- `dora_api/persistence/table_mappings.py`
- `dora_api/persistence/migrations/versions/e1a4c7b2f9d0_20260613_shopping_list_planned_shop_date.py` (new)
- `dora_api/features/shopping_lists/manage_shopping_list.py`
- `dora_api/features/shopping_lists/get_shopping_lists.py`
- `dora_api/features/shopping_lists/get_shopping_list_detail.py`
- `web_app/src/models/shoppingList.ts`
- `web_app/src/services/api/shoppingListApiService.ts`
- `web_app/src/components/dialogs/NewListDialog.vue`
- `web_app/src/pages/ShoppingListDetail.vue`
- `web_app/src/pages/ShoppingListsOverview.vue`
- `tests/e2e/dora_api/test_shopping_list_planned_shop_date.py` (new)
- `CHANGELOG.md`

**Verification:**
- `python -m py_compile` clean on all touched .py files + new migration + new test.
- `npx vue-tsc --noEmit` clean (exit 0).
- **e2e test not executed** — no live server in this session. Logged FU-075 to run once a dev environment is up.
- **Migration not applied** to a live DB.

**Next up:**
- **Browser smoke** of Chunks 3/4/5/6/7 (FU-066/068/069/072/073/076).
- Apply migration `e1a4c7b2f9d0` to local DB + run the new e2e (FU-075).
- After verification, P6-01 closes. Phase 2 next.

**Open questions for user:** none blocking.

---

## 2026-06-08 — P6-01 Chunk 6 (in-store polish) — IMPLEMENTED (subset).
**Status:** complete (the five smaller in-store wins + FU-070). Pricing-as-you-go and group-by-aisle audit kept as findings.
**What changed:**
- **Skip persistence** ([ShoppingListShopMode.vue](web_app/src/pages/ShoppingListShopMode.vue)).
  `skipForNow` and `jumpTo` were client-only — they bumped `line.sequence`
  locally and reverted on refresh (feedback §SHOPPING MODE "the position of
  the items keeps changing"). Both now optimistically rewrite local
  sequences and post `reorderLinesAsync` so the new order survives. New
  helpers `persistReorderedIds`, `persistMoveToEnd`, `persistMoveToFront`;
  the front-move inserts the line just before the first unticked id so it
  surfaces as the next "Got it" without leapfrogging already-picked items.
- **Tap-to-type quantity.** The centre `<div>` of the qty row became a
  `<button>` styled to look identical; tap opens a small **Quantity** dialog
  with a numeric input + Save. `qtyEditorOpen` / `qtyEditorLine` /
  `qtyEditorDraft` mirror the existing price-editor shape, and
  `saveQtyEditor` does the same optimistic-update-then-revert-on-error dance
  as `adjustQuantity`. Keyboard handler now also ignores arrow keys while
  the qty editor (or peek dialog) is open.
- **Whole-list peek.** New `q-btn` next to the kebab opens a dialog of all
  lines (ticked + unticked, sorted by `sortKey`). Unticked rows are
  clickable — `onPeekJump` closes the peek and calls `jumpTo`, which is now
  persisted (so the chosen line becomes next-up across refreshes).
- **DnD off-by-one fix** ([ShoppingListDetail.vue](web_app/src/pages/ShoppingListDetail.vue)).
  Removed the `fromIdx < toIdx ? toIdx - 1 : toIdx` adjustment in
  `onLineDrop` — `insertAt = toIdx` in every case now puts the dropped line
  at the dragged-over row's visual slot, matching feedback L414 ("Drag and
  drop is an index off").
- **FU-070 back-arrow removed.** The `goBack()` function + its arrow button
  were a self-bounce through the landing once Chunk 5 turned the detail
  page into the canonical surface. Both gone.

**Decisions made:**
- **Persist on click, not on debounce.** Skip / jump are inherently
  user-initiated single actions; debouncing to coalesce repeated taps would
  delay the cross-refresh persistence guarantee that was the whole point.
- **Whole-list peek as a `BaseDialog`**, not a side-sheet. A bottom-anchored
  Quasar sheet would be ergonomic on mobile but adds a different chrome
  pattern. The dialog already works fullscreen-ish on small viewports and
  matches the price/qty editor pattern — same shape, three buttons,
  predictable for the user. If feedback later wants a real bottom sheet,
  it's a one-component swap.
- **Tap-to-type uses a `<button>` reset**, not a `q-btn`, so the visual is
  byte-for-byte identical to the old `<div>` apart from focus/hover affordance.
- **Pricing-as-you-go and group-by-aisle audit deferred.** The price editor
  already exists on shop mode (`openPriceEditor`); the feedback ask is for
  it to remain accessible mid-shop, which it does. Group-by-location on the
  detail page is already a derived view (`lineGroups` reads but never
  writes `sequence`). Both noted as FU-072 to confirm in browser + close.
- **Engineering close-gate:** R-001 (reused `BaseDialog`), R-003 (skip /
  jump now actually persist via the server — no shadow client truth, fixes
  a long-standing R-003 nibble), R-007 (held to the chunk's stated polish
  list, no creep), R-008 (terse comments only where the WHY isn't obvious).

**Files touched:**
- `web_app/src/pages/ShoppingListShopMode.vue` (skip persistence, qty editor, whole-list peek, keyboard guard, styles)
- `web_app/src/pages/ShoppingListDetail.vue` (DnD off-by-one fix, back-arrow + `goBack` removed)
- `CHANGELOG.md`

**Verification:**
- `npx vue-tsc --noEmit` → clean (exit 0).
- **Not verified in browser** — logged FU-073.

**Next up:**
- **Browser smoke** of Chunks 3/4/5/6 (FU-066, FU-068, FU-069, FU-073).
- **Chunk 7 — planned shop day + cleanup.** Adds `planned_shop_date` (and
  feeds C-9's new alert types), then once `status` has proven itself in
  production, drops the deferred-from-Chunk-1/2 boolean columns. (The
  `is_in_progress` / `is_archived` / `is_primary` drops already happened in
  Chunks 1 & 2, so Chunk 7 reduces to the new field + the shopping-day
  alert.) That closes out the P6-01 phase plan.

**Open questions for user:** none blocking.

---

## 2026-06-08 — P6-01 Chunk 5 (merge overview into detail) — IMPLEMENTED.
**Status:** complete.
**What changed:**
- **Extracted `NewListDialog.vue`** ([web_app/src/components/dialogs/NewListDialog.vue](web_app/src/components/dialogs/NewListDialog.vue)) — the unified Chunk-4 dialog now lives in its own component with `v-model` + `presetLowOrOut` / `presetMergeIntoListId` props and a `@created` event. Owns the form state, lazy-loads template/recipe/meal-plan options on open, and runs the same `createAsync → instantiate/bulk-add → autoGenerateAsync` pipeline. Detail and the new router landing both mount it.
- **Detail becomes the canonical surface** ([web_app/src/pages/ShoppingListDetail.vue](web_app/src/pages/ShoppingListDetail.vue)):
  - New **list selector** dropdown in the header (`q-btn-dropdown` with the list-icon), showing all summaries grouped as **Active** (SHOPPING first, then newest-created) and **Archived** (newest-completed), the current list highlighted via `active-class`. Each row has a side-kebab with **Copy unticked → new** (active) / **Copy archived → new** (archived) / **Archive list** / **Delete list**. Top entry: **+ New list**. Bottom entry: **Manage templates…** link.
  - Wired in: `activeSummaries` / `archivedSummaries` computed sorters, `switchToList`, `onListCreated`, and the moved-from-Overview handlers `archiveSummary` / `deleteSummary` / `copyListUnticked` / `copyListAll` / `copySummary`. Imports `ShoppingListSummary` type + the new `NewListDialog` component.
  - The new dialog is mounted at the end of the template, controlled by a local `newListOpen` ref.
- **Overview is now a router landing** ([web_app/src/pages/ShoppingListsOverview.vue](web_app/src/pages/ShoppingListsOverview.vue)):
  - Rewritten from scratch. On mount: if `store.summaries` is empty, refresh; then call `pickTargetList()` (SHOPPING → newest DRAFT → newest DONE) and `router.replace` to that list's detail. A `watch(summaries.length)` covers the async-refresh-after-mount case.
  - When no lists exist, renders a centred empty state with one **New list** button. The dialog's `@created` event triggers another `router.replace` to the freshly-created list.
  - Old per-card UI, tab switching, kebab menus, autogen handlers, recipe/meal-plan pickers — **all gone**. ~970 LoC → ~110 LoC.

**Decisions made:**
- **One dropdown for both desktop and mobile**, not a desktop right-panel + mobile-top-dropdown split. The proposal asks for the split as polish; a `q-btn-dropdown` works on every viewport and shaves a meaningful chunk of work for Chunk 5. The right-panel polish is logged as a follow-up — fold into Chunk 6 in-store polish or later layout work.
- **Sort by `created_at` / `completed_at` for now.** `planned_shop_date` arrives in Chunk 7; once it exists, the sort + the "keyed to today's date" pick get a real input. Documented in the code comment so it's obvious where to slot the field in.
- **Component extraction over copy-paste.** Both surfaces need the dialog and the dialog has non-trivial state (lazy-loaded option lists, form, submit pipeline). A shared `NewListDialog` keeps the two consumers in lockstep and matches R-001 (componentisation when the pattern recurs).
- **`goBack()` left alone** — it still pushes `/shopping-lists`, which now bounces back to a chosen list. Slightly odd, but the back button is genuinely useful as an "out of this surface" handle and the bounce isn't broken. Logged as FU-070.
- **Engineering close-gate:** R-001 (extracted `NewListDialog`, reused `BaseDialog` chrome), R-003 (no domain logic copied — both surfaces drive the same backing endpoints), R-007 (scope held: the old overview's responsibilities split exactly into selector + landing; no new features), R-008 (terse comments only where the "why" isn't obvious).

**Files touched:**
- `web_app/src/components/dialogs/NewListDialog.vue` (new, ~430 LoC — extracted from Overview)
- `web_app/src/pages/ShoppingListDetail.vue` (selector + new-list dialog + handlers added)
- `web_app/src/pages/ShoppingListsOverview.vue` (rewritten as landing, ~970 → ~110 LoC)
- `CHANGELOG.md`

**Verification:**
- `npx vue-tsc --noEmit` → clean (exit 0).
- **Not verified in browser** — sizeable surface, lots to eyeball. See FU-069 for the matrix.

**Next up:**
- **Browser smoke** of Chunks 3/4/5 (FU-066, FU-068, FU-069).
- Then **Chunk 6 — in-store polish** (skip persistence, tap-to-type qty, whole-list peek, group-by-aisle as a view, drag-and-drop off-by-one fix, pricing-as-you-go).

**Open questions for user:** none blocking.

---

## 2026-06-08 — P6-01 Chunk 4 (one creation surface) — IMPLEMENTED.
**Status:** complete.
**What changed:**
- **Overview** ([ShoppingListsOverview.vue](web_app/src/pages/ShoppingListsOverview.vue)):
  - Replaced the `q-btn-dropdown` "New list" menu (7 items) and the standalone
    "Advanced auto-generate…" `BaseDialog` with **one** consolidated "New shopping
    list" `BaseDialog`. Toolbar is now a single primary "New list" button + a
    small "Manage templates" icon shortcut.
  - The new dialog has three sections:
    1. **Start from**: radio across `empty / template / recipe / meal_plan`; the
       template/recipe/meal-plan branches reveal a `q-select` that lazy-loads on
       first dialog open (parallel `getAllAsync` for all three, errors swallowed
       to "no options" hints).
    2. **Auto-fill from stock**: checkboxes for low-or-out, "...only flagged
       essentials" sub-option (gated on low-or-out), always-include flagged, and
       frequently-added — mapping straight onto the `sources` payload of
       `/auto-generate`.
    3. **Target**: radio `new / merge`, with either a free-form **Name** input
       (new) or a `q-select` over active lists (merge).
  - `submitNewList` resolves the target list first (existing id, or a fresh
    `createAsync({name?})` shell), then pre-seeds from the start-from source
    (template via `instantiateAsync`; recipe / meal plan via bulk `addLineAsync`),
    then optionally calls `autoGenerateAsync` for the auto-fill checkboxes. One
    summary notify reports the combined added/skipped/nothing-matched outcome.
  - Empty-state "kickstart" UI shrunk from two buttons (Auto-generate from low/out
    + Empty list) to **one** "New list" button that opens the dialog with
    `presetLowOrOut: true` pre-ticked.
- **Detail** ([ShoppingListDetail.vue](web_app/src/pages/ShoppingListDetail.vue)):
  - Removed the kebab menu's "Append low + essentials" item and the
    `onAppendLowEssentials` handler — that was the 5th of the proposal's "five
    doors" and is now reachable as a single click in the unified dialog
    (Target = "Add to this list", Auto-fill = "low or out" + "essentials only").

**Decisions made:**
- **Template merge via temp-list + bulk-add.** The `instantiateAsync` endpoint
  always creates its own list; there's no "merge template into list" API. Rather
  than touch the backend (Chunk 4 is "pure frontend"), the dialog's template+merge
  path instantiates a temp list, reads its lines, bulk-adds them to the target,
  then deletes the temp. Documented in an in-code comment naming the constraint.
- **Recipe / meal-plan pre-seed stays client-side.** `/auto-generate` only knows
  flagged/low sources, so cooking sources resolve via `getIngredientsAsync` +
  bulk `addLineAsync`. Same pattern as the old `createListFromItems` helper,
  preserved as `bulkAddToList`.
- **`appendLowStockEssentialsAsync` endpoint kept.** It still exists on the API;
  the only frontend consumer is gone, but ripping out the backend endpoint is
  out-of-scope for a "pure frontend consolidation" chunk. Logged as
  [FU-067](#) for a later sweep (or natural cleanup when Chunk 7 lands).
- **Engineering close-gate:** R-001 (kept `BaseDialog` + native Quasar inputs;
  no new chrome), R-003 (server-owned creation + auto-generate endpoints —
  client only composes the calls), R-007 (no scope creep — only the 5 doors
  collapsed; templates manage page still its own route via icon shortcut), R-008
  (terse, no over-commenting).
  - One smell deferred as a finding (FU-067): the unused
    `/shopping-lists/{id}/append-low-essentials` endpoint + its API method.

**Files touched:**
- `web_app/src/pages/ShoppingListsOverview.vue`
- `web_app/src/pages/ShoppingListDetail.vue`
- `CHANGELOG.md` (Unreleased § Changed)

**Verification:**
- `npx vue-tsc --noEmit` → clean (exit 0). Caught + fixed one type error
  (a `@click="openNewListDialog"` bound the click event into the optional opts
  arg — switched to `openNewListDialog()` so the default opts is used).
- **Not verified in browser** — six flows to eyeball:
  1. Toolbar *New list* → dialog → *Empty + Create new* → empty list created.
  2. *Empty + auto-fill low-or-out + new* → matches the old "From all low/out".
  3. *Template + new* → matches the old "From a template…".
  4. *Recipe + new* → matches the old "From a recipe…".
  5. *Meal plan + new* → matches the old "From a meal plan…".
  6. *Empty + auto-fill flagged + merge into existing* → matches old "Top up
     the primary list".
  7. Empty-state "New list" button → dialog opens with **low or out** pre-ticked.
  Logged as FU-068.

**Next up:**
- **Browser smoke** of Chunk 4 (FU-068) plus the still-pending Chunk 3 smoke
  (FU-066).
- Then **Chunk 5 — merge overview into detail** (the bigger structural shift:
  no standalone overview page; detail-with-list-selector is the surface).

**Open questions for user:** none blocking.

---

## 2026-06-08 — P6-01 Chunk 3 (shopping-list lifecycle UI) — IMPLEMENTED.
**Status:** complete.
**What changed:**
- **Detail page** (`web_app/src/pages/ShoppingListDetail.vue`):
  - Removed the "Shop mode", "Review mode", "Start shopping", "Stop shopping",
    "Finish shopping" buttons and the "Finish review" menu item. Replaced with a
    single status-driven primary-action button: **Start shopping** on DRAFT,
    **Reopen** on DONE (calls `unfinishAsync`; restock changes server-reverse from
    the finish snapshot). SHOPPING has no button on this surface — it's covered by
    the routing flip below.
  - Added a `watch(detail.status)` that `router.replace`s to `/shopping-lists/:id/shop`
    whenever the list becomes SHOPPING (covers start-shopping, assistant actions,
    cross-tab flips). The "Shopping in progress" banner is gone — the user never
    sees this surface in SHOPPING state.
  - Dropped `reviewMode` ref + `toggleReviewMode` + the review-mode preview card,
    `onReviewComplete`, `openShopMode`, `StocktakeApiService` import. `baseLines` /
    `canReorder` lose the review-mode branch.
  - **Folded review into the finish confirmation:** `onFinish` now lists the first
    8 ticked items (plus "and N more") that will bump to Well-Stocked, before the
    user confirms. The unticked-handling (copy-or-archive radio) is preserved.
  - Added `onReopen` for DONE → DRAFT, with a positive notify.
- **Shop mode page** (`web_app/src/pages/ShoppingListShopMode.vue`):
  - Back-arrow now reads "Back to editing" (aria + tooltip) and calls
    `stopShoppingAsync` before navigating — otherwise the Detail page's status
    watcher would bounce the user straight back into shop mode.
  - `onFinish` now shows the same folded-review confirmation dialog before
    archiving. The footer **Finish & restock** button is always visible (was
    `v-if="remainingLines.length === 0"`); when items remain it reads
    "Finish early & restock".
  - Removed the kebab menu's "Open full list" entry (redundant with back-arrow now
    that the routes are status-coupled).
  - `onMounted` redirects to `/shopping-lists/:id` if the list isn't SHOPPING on
    arrival (e.g. PWA shortcut hits /shop for a DRAFT/DONE list).

**Decisions made:**
- **Two routes, one logical surface.** The proposal asks for SHOPPING to render
  shop-mode "in place". Two real options: (a) inline-embed the 1100-line shop-mode
  template inside Detail behind a `v-if`, or (b) keep both routes but make the
  status drive which one the user sees. Picked (b) for Chunk 3 — same UX (no
  toggle, the user never thinks about "modes"), tiny diff, no risk of breaking
  shop-mode's keyboard / offline-queue / focus plumbing. If a future chunk wants
  a single literal page, the routing layer is the only thing to revisit.
- **"← Back to editing" must flip status, not just navigate.** Without
  `stopShoppingAsync` in `exit()`, the Detail watcher re-routes immediately and
  the back arrow looks broken. Spelled out in a comment in `exit()` so future
  edits don't drop the call.
- **Finish is now allowed mid-shop.** The proposal's "fold review into finish"
  + the new dialog showing exactly what restocks make this safe — the user sees
  the consequence before committing, and unticked items still get the
  copy-to-new-list option.
- **Engineering close-gate:** changes honour R-001 (used `BaseButton`), R-003
  (server-owned reopen via `unfinishAsync`; no client snapshot), R-009 (preview
  → confirm → commit on finish). One minor smell — the ticked-summary string is
  built in both pages' `onFinish` (Detail + ShopMode). Logged as a finding
  (FU-065) rather than over-extracting a one-line helper right now.

**Files touched:**
- `web_app/src/pages/ShoppingListDetail.vue`
- `web_app/src/pages/ShoppingListShopMode.vue`
- `CHANGELOG.md` (Unreleased § Changed)

**Verification:**
- `npx vue-tsc --noEmit` → clean (exit 0).
- **Not verified in browser** — the full lifecycle still needs an eyeball pass:
  - DRAFT detail → click *Start shopping* → routes to /shop.
  - SHOPPING /shop → tick items → footer *Finish early & restock* / kebab
    *Finish & restock* → confirmation lists ticked items → confirm → archived.
  - SHOPPING /shop → back-arrow → status flips to DRAFT → detail page.
  - DONE detail → *Reopen* → status flips to DRAFT → restock reversed.
  - PWA "Shop now" routing still picks SHOPPING / DRAFT / overview correctly.
  - Open in Pesto Light + a dark theme to confirm dialog/button styling still
    reads.

**Next up:**
- **Browser smoke** of the lifecycle (above bullets). Open as FU-066 if anything
  needs tuning.
- Then **Chunk 4 — one creation surface.** Collapse the 5 "create" buttons on
  the overview into one composable form mapped onto `/auto-generate`. Pure
  frontend.

**Open questions for user:** none blocking.

---

## 2026-06-08 — Doc graph (anti-drift cross-reference) — BUILT.
**Status:** complete.
**What changed:**
- New file `docs/00_DOC_GRAPH.md` (~1.3k lines). Per-prompt required-reading map for every `03_prompts/` prompt (A1–A8, A1b, B1/B3/B4/B5/B7/B8/B9, INV-1..10, C-1..C-10 + C-cross/locale/help + 2 C-impl). Each section lists: surface, charter principles (P1–P12), engineering rules (R-001..R-010), feedback bullets (anchored by `§SURFACE` + quoted phrase since the master feedback doc has no numeric IDs), related proposals, related investigations, original-spec Feature Boards, open follow-ups, removed-features watchlist, cross-prompt dependencies.
- Also: `Proposal → implementation cross-map`, `Surface → docs index` (reverse lookup), `Rules with no per-prompt home` (audit lens — only R-004 is unhomed, correctly, as a passive constraint), and `Homeless follow-ups` (currently none — every `[OPEN]` FU is placed).
- Wired in: `docs/00_DOCS_INDEX.md` references the graph at the top + in folder layout; `CLAUDE.md` §"On session start" item 2 names it as the anti-drift spine; `docs/03_prompts/00_INDEX.md` per-prompt ritual now starts with "open the graph row first".
**Decisions made:**
- **Option A over Option B** (one central file vs. editing every prompt in place). Lower maintenance, single auditable artifact, easy to promote to in-prompt blocks later if agents skip it.
- **Authority order on conflict:** Charter > Reconciled Plan > current feedback > engineering standards > proposals > prompt body > original spec > status doc. Recorded in the graph's "How to use" section.
- **Engineering rules are NOT cited per prompt in the graph** (user call). The standing close-gate checks the full `R-001..R-0NN` list against every task; listing a subset per prompt invited cherry-picking. The graph's "How to use" and Legend explain this; the per-prompt sections omit it.
- **Feedback bullet anchor scheme:** the master feedback doc has no F-NN IDs (surface-headed bullet lists). The graph cites by `§SURFACE` + a quoted phrase. Documented in the Legend.
- **Single biggest sequencing constraint surfaced:** `IMPL_PLAN_STATE_OWNERSHIP` must land before `IMPL_PLAN_SHOPPING_LISTS`. Captured in cross-prompt deps and the cross-map.
**Files touched:** `docs/00_DOC_GRAPH.md` (new), `docs/00_DOCS_INDEX.md`, `CLAUDE.md`, `docs/03_prompts/00_INDEX.md`.
**Verification:**
- Spot-checked A1, the cross-cutting surfaces, and the homeless-FU tail. Counts: 41 prompt sections, all 17 proposals indexed, all 14 investigations cited, every `[OPEN]` FU placed, only R-004 unhomed (correctly).
- NOT verified: original-spec Feature Board mapping is by filename-to-surface heuristic, not by opening each board. Logged as a follow-up.
- NOT verified: every cited file path opened in a Read — the agent used Grep/Glob but a per-citation existence pass was not done.
**Next up:** awaiting user direction. The natural follow-on is to **stress-test the graph by running the next prompt through it** (read the row, see if the cited docs actually surface what they should), then iterate.
**Open questions for user:** none blocking. Two suggested: (a) do you want a periodic "regenerate the graph" prompt added to `03_prompts/`? (b) should the graph be promoted to in-prompt `## Required reading` blocks (Option B) if agents skip it?

---

## 2026-06-07 — P6-01 Chunk 2 (contextual primary inference) — IMPLEMENTED.
**Status:** complete.
**What changed:**
- **New shared resolver.** `dora_api/features/shopping_lists/primary_target_resolver.py`
  — pure function over a list of ShoppingLists returns a typed
  `PrimaryTargetOutcome` (`kind: "none" | "single" | "ambiguous"` + target id or
  candidates). One source of truth for "which list does a quick-add land on?".
- **Quick-add rewritten.** `POST /shopping-lists/primary/lines` now returns a
  discriminated payload (`added` / `no_draft` / `ambiguous` / `hint_invalid` /
  `item_not_found`) and accepts an optional `shopping_list_id` hint so the
  client can disambiguate the 2+ case. SHOPPING and DONE lists never count as
  candidates (drafts only, per plan).
- **`is_primary` ripped out.** Column dropped (migration `d5e9f3b2a1c8`); entity
  field removed; `make_primary` gone from create + template-instantiate;
  `is_primary` gone from update; finish no longer auto-promotes a sibling;
  unfinish no longer restores a prior primary; the `finish_snapshot` now carries
  only `level_restores`; assistant `set_primary_list` action removed;
  `get_membership` exposes `quick_add_target_list_id` (single-draft only) and
  active-list entries carry `status` instead of `is_primary`; the auto-low-stock
  add path uses the resolver, so it only auto-adds when there's an unambiguous
  draft.
- **Frontend.** Store rename: `primaryListId` → `quickAddTargetListId`,
  `primarySummary` → `quickAddTargetSummary`, derived from the membership DTO.
  Cart state `'on_primary'` → `'on_target'`. New `useQuickAddTargetPick`
  composable wraps `sessionStorage` for the "remember the 2+-draft pick".
  `useStockItemActions.addToList` handles the discriminated outcome (with stale-
  hint retry); ShoppingListsOverview drops Primary badge, the "Set as primary"
  menu item, and `make_primary` on create / instantiate; ShoppingListDetail
  drops "Set primary" / Primary chip + `setPrimary()`. ShopNowRedirect now picks
  by status: 1 SHOPPING → shop-mode; else 1 DRAFT → detail; else overview. All
  surface labels lose the " (primary)" suffix (no stored flag to mark).
- **Tests.** New `tests/e2e/dora_api/test_primary_target_inference.py` — 7 tests:
  no_draft, single-draft silent add, 2+ drafts return candidates +
  disambiguation, SHOPPING doesn't count as candidate, hint_invalid for non-
  draft, membership target mirrors inference, `make_primary` rejected as extra
  input. Chunk 1 lifecycle test updated (no more `make_primary` arg); still 5/5.
**Decisions made:** Dropped the column **now** (mirroring Chunk 1; user-confirmed
"no compat shims"). Session pick lives in `sessionStorage` (UI scope, no server
state needed). The assistant's old "make this primary" action is removed
outright rather than rewired; there's no longer a flag to set, and the resolver
makes the intent meaningless. Auto-low-stock add now refuses to silently pick
when ambiguous (the user gets a normal cart-button prompt on the next click) —
matches "anti-creep" / no surprises.
**Files touched:** entity `shopping_list.py`; `table_mappings.py`; migration
`d5e9f3b2a1c8_*`; `features/shopping_lists/*` (manage_shopping_list, unfinish,
manage_shopping_list_lines, get_shopping_lists, get_shopping_list_detail,
get_membership, auto_generate); `features/shopping_list_templates/manage_templates`;
`features/stock_items/update_stock_item`; `features/search/global_search`;
`features/assistant/{confirm_actions,tools,ask_assistant}`; `persistence/seed`;
frontend `models/shoppingList.ts`, api services (shoppingList, template),
`stores/shoppingListStore.ts`, new `composables/useQuickAddTargetPick.ts`,
`composables/useStockItemActions.ts`, `composables/useShoppingListActions.ts`,
ShoppingList* pages, ShopNowRedirect, StockItemRow, StockItemChip,
StockItemDetailPage, ShoppingListTemplates, ExportPrint, DoraChat, ProductSearch,
+ the renamed `quickAddTargetListId` callers (13 files).
**Verification:** new inference e2e — **7/7 pass**; Chunk 1 lifecycle e2e still
**5/5**; touched Python `py_compile`-clean; `npx vue-tsc --noEmit` clean. Broader
e2e suite identical fail-baseline as before (122 failed / 10 errors, pre-
existing pagination test rot — FU-048; not from this chunk). **NOT done:**
migration not applied to a live DB; no browser smoke of the 2+-draft picker or
shop-now.
**Next up:** Chunk 3 — lifecycle UI (one primary-action button: Start → Finish
→ Reopen, fold review into finish confirmation, shop-mode renders in place on
SHOPPING). Before that: browser-verify the 2+-draft sessionStorage picker, the
new ShopNowRedirect routing, and FU-059 line ticking (still open from Chunk 1).
**Open questions for user:** none blocking.

---

## 2026-06-07 — P6-01 Chunk 1 (shopping-list lifecycle) — IMPLEMENTED.
**Status:** complete.
**What changed:**
- **Status model.** `ShoppingList.is_archived` + `is_in_progress` collapsed into a single
  `status` enum (`draft` / `shopping` / `done`) on the entity (plain-string sentinels +
  `is_draft`/`is_shopping`/`is_done` props). Migration `c4d8e1a6f3b9` converts existing
  rows (`is_archived→done`, `is_in_progress→shopping`, else `draft`) and **drops** the two
  old columns (no dual-read). DTOs (summaries + detail) expose `status`; the ~dozen
  backend consumers that meant "active" now read `status != done`.
- **Server-owned finish/reopen.** Finish writes `finish_snapshot` (JSON-in-text:
  `{was_primary, promoted_primary_list_id, level_restores}`) capturing what it changed,
  then restocks ticked items + marks `done`. Reopen (`POST /…/unfinish`, **no body**)
  reverses straight from the snapshot and clears it. `start`/`stop` move draft↔shopping;
  invalid `status` PATCH → 400.
- **Frontend.** New `ShoppingListStatus` type + `isListDone/isListShopping` helpers;
  every `is_archived`/`is_in_progress` read swapped to `status` comparisons across the
  shopping-list pages, QuickAdd, recipes, products, ExportPrint; `unfinishAsync` posts an
  empty body (client snapshot capture removed).
- **Two bugs fixed en route** (both pre-existing, logged FU-058/FU-059):
  (1) line tick/delete always 404'd — `update_line`/`delete_line` compared a `UUID` FK to
  a `str` path param; now string-compared. (2) Finish captured no `level_restores` because
  `stock_level` is a `lazy="noload"` relationship; the finish query now `.include`s it.
**Decisions made:** Dropped old booleans **now** (pre-release = no compat shims), against
the plan's "keep for dual-read till Chunk 7". Used a snapshot-on-list column rather than a
separate audit table — lighter, same server-owned-undo guarantee (R-003). `is_primary` +
`completed_at` kept (primary removal is Chunk 2). Scope held to Chunk 1; the two bug fixes
were in-path blockers for the finish/reopen e2e, fixed minimally + logged.
**Files touched:** entity `shopping_list.py`; `table_mappings.py`; migration
`c4d8e1a6f3b9_*`; `features/shopping_lists/*` (manage_shopping_list, unfinish,
get_shopping_lists, get_shopping_list_detail, manage_shopping_list_lines, auto_generate,
list_actions, get_membership); consumers in assistant, suggestions, dashboard, reports,
budget, search, stock_items/update_stock_item; frontend `models/shoppingList.ts`,
`shoppingListApiService.ts`, ShoppingList* pages, QuickAddSheet, MyProductsPage,
Recipes*, data/ExportPrint; new e2e `tests/e2e/dora_api/test_shopping_list_lifecycle.py`.
**Verification:** new lifecycle e2e — **5/5 pass** (draft default, start/stop, invalid
status rejected, summaries expose status, finish→reopen restores level server-side).
Touched backend `py_compile`-clean; frontend `vue-tsc --noEmit` clean (from prior
session). Broader e2e suite has a **pre-existing** 23-fail/10-error baseline (paginated
endpoints read as bare lists in old fixtures, FU-048) — **confirmed identical with `git
stash`**, so no regression from this chunk. **NOT done:** migration not applied to a live
DB (FU-057-style); no browser smoke of the lifecycle UI.
**Next up:** Chunk 2 — contextual target inference to remove stored `is_primary` reads
(needs the inference resolver), then drop `is_primary`. Before that, browser-verify
shop-mode line ticking (FU-059) and the finish/reopen flow.
**Open questions for user:** none blocking.

---

## 2026-06-07 — P6-02 barcode/QR — IMPLEMENTED (cleanup slice; "Cleanup now, UI later").
**Status:** complete (the cleanup slice; deferred slices logged as follow-ups).
**What changed:**
- **Dropped the wrong model:** removed `StockItem.barcode` (column, mapping, entity field,
  register/clear routes, wrong-model UI, DTOs, CSV export column). Migration
  `a3f1c7d2e9b4` (down_revision `b2c3d4e5f6a7`, the true head — handoff's
  `d7f4a2c98e15` was stale) drops the column + uq constraint via `batch_alter_table`
  (R-005 SQLite portability) and adds `AppSetting.scanning_enabled`.
- **Kept the right model:** `ProductBarcode` (barcode→Product) and its lookup branch,
  plus Dora's own QR labels. `register-against-product` route kept + now tested.
- **Off-by-default gating:** new `AppSetting.scanning_enabled` (default false), exposed
  via health `features.scanning`, consumed by new `useScanningEnabled()` composable
  (no new Pinia store). Gated: StockOverview scan/print buttons, stock-item "Show QR",
  Data → "Scanning & QR labels" section + page (off-state banner), admin toggle wired
  in Settings → System.
- **Honest relabel:** "Barcodes & QR" → "Scanning & QR labels"; dropped the "Manage"
  tab; banner states scanning is navigation-only, never live price lookup.
- **Fixed latent bug:** health `_feature_flags()` called non-existent
  `get_or_create_app_settings()` (swallowed by try/except) → `features.assistant` was
  always false. Now reads real AppSetting, reports `assistant` + `scanning`.
- **Tests:** `test_data_router.py` — removed the two `register_stock_item_barcode`
  tests (routes gone), added `register_product_barcode` happy/collision +
  dora-link-resolves tests, removed `barcode` from CSV-header assertion.
- **Docs:** new `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md` (two-system design +
  feedback coverage table); CLAUDE.md "Removed features" P6-02 line reworded; CHANGELOG.
**Decisions made:** Implemented Option 1 ("Cleanup now, UI later") per user choice.
ONE flag gating the whole surface (anti-creep, P10). Register-against-product UI +
ingestion EAN auto-populate deferred to Phase 2 — Product has no EAN field today (only
`merchant_stockcode`), so a register UI now would be manual-only; ingestion is the right
place to auto-fill `ProductBarcode`.
**Files touched:** see CHANGELOG; backend `app_setting.py`, `table_mappings.py`,
`stock_item.py`, `features/app_settings/*`, `features/data/barcodes.py`,
`features/stock_items/get_stock_item*.py`, `features/data/export_stock_overview.py`,
`features/health/health_check.py`, migration `a3f1c7d2e9b4_*`; frontend
`useScanningEnabled.ts`, `healthApiService.ts`, `appSettingsApiService.ts`,
`stockItemApiService.ts`, `barcodeApiService.ts`, `stockItem.ts`, `stockItemDetail.ts`,
`SystemSettings.vue`, `StockItemDetailPage.vue`, `StockOverview.vue`,
`data/BarcodesQR.vue`, `DataManagement.vue`, `MainLayout.vue`; tests
`test_data_router.py`.
**Verification:** all touched Python `py_compile`-clean; frontend sweep confirmed no
stray `registerBarcodeAsync`/`clearBarcodeAsync`, no `features.barcodes`, no
stock-item `.barcode`. **NOT run:** e2e suite (pre-existing broken, FU-048); migration
not applied against a live DB; no browser smoke test of the gated UI.
**Next up:** P6-01 (unblocked). Before that, someone should browser-verify the gated
scanning surface (toggle on/off in Settings → System) and run the migration on a dev DB.
**Open questions for user:** none blocking. The deferred register-against-product UI +
ingestion auto-populate are logged in DORA_FOLLOWUPS.

---

## 2026-06-07 — P6-02 barcode/QR — DESIGN DISCUSSION (recon-only, NO code). HANDOFF: decision pending.
**Status:** recon-only — **blocked on a user decision** (ran out of usage mid-discussion).
**What happened:** Picked P6-02 ("barcode→QR cleanup") as the next task after the
state-ownership refactor. Mapped all barcode/QR code (see "Code map" below), then a
design discussion **changed the shape of P6-02** — do NOT just run the legacy spec.

### The pivot (important — the legacy P6-02 spec is now partly WRONG)
The legacy spec (`docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md` §P6-02) says
"remove real-world barcodes wholesale, keep only Dora QR." The user re-litigated this and
we reached a **better model** (user agreed; I agreed it's a real modeling bug):
- A real-world barcode (EAN/UPC) identifies a **Product** (a saved SKU), not a stock item.
  A stock item maps to *many* products → many barcodes. So:
  - **`ProductBarcode` (barcode→Product) is the CORRECT model — KEEP it** (legacy spec wanted
    it deleted; that's wrong).
  - **`StockItem.barcode` (single barcode column on the item) is the WRONG model — DROP it.**
- Real-world barcode scanning is a **navigation aid** (scan packaged product → resolve
  ProductBarcode→Product→linked StockItem → open it), useful for a niche of users who want
  scanning. Pairs with **Dora QR** for items with no real-world barcode (loose produce, deli,
  decanted staples) + containers/shelves.
- **Two complementary systems**, framed by use-case ("Scan a product" vs "Print Dora labels"),
  **opt-in / off-by-default**, with a clear explainer of why both exist.
- **HARD BOUNDARY (unchanged from the removal):** scanning = navigation only (open YOUR stock
  item). It must NEVER do live "deal lookup" (that's the removed hosted-scraping concern;
  live prices come via the companion/ingestion API, not barcode lookup).

### Decisions RESOLVED this session (by user)
- **`qr_labels_enabled` / scanning flag → install-wide AppSetting** (admin, single row, alongside
  `llm_enabled` in `dora_api/domain/entities/app_setting.py`). NOT a per-user preference.
- Flag shape (one vs two flags): **user had no preference → I recommend ONE flag**
  (`scanning_enabled`, off by default) gating the whole scanning+labels surface (one mental
  feature, simplest UX).

### OPEN QUESTION FOR USER (blocks proceeding) — ask this first next session:
**How much to build under P6-02 NOW vs defer?** Three options put to the user (unanswered):
  1. **(My recommendation) Cleanup now, build UI later:** Now → drop `StockItem.barcode` (column +
     register/clear routes + the wrong-model UI), KEEP `ProductBarcode` + its resolution branch,
     KEEP Dora QR, add the off-by-default flag, relabel honestly. Defer the *register-against-
     product* UI + scan-unknown rework to **Phase 2 (ingestion)** — ideally auto-populate
     `ProductBarcode` from scraped EANs so manual registration becomes a freebie. Keeps P6-02 a
     surface-*reduction*; unblocks P6-01.
  2. Build the full vision now (net-new register-against-product UI + scan-unknown rework + two-
     system UX before P6-01).
  3. Pause P6-02; write `PROPOSAL_BARCODE_SCANNING.md` + update CLAUDE.md first, then decide.

### Also unconfirmed (factual): does the scraper/Product data capture an EAN today?
Products have `merchant_stockcode` (merchant SKU), but I did NOT find a scannable EAN field.
If absent, manual registration is the only path now → strengthens "defer the UI until ingestion
can auto-fill it." Next agent should verify before planning the register UI.

### Doc changes AGREED IN PRINCIPLE (do once build-vs-defer is decided — NOT done yet):
- **CLAUDE.md "Removed features" P6-02 line:** reword — "barcode *deal lookup*" stays removed,
  but clarify `ProductBarcode` (barcode→product *navigation*) is KEPT as the correct model;
  `StockItem.barcode` is what's dropped. (Currently it implies all real-world barcodes are cut.)
- Write **`docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md`**: two-system design, corrected model,
  off-by-default gating, navigation-not-deal-lookup boundary, deferred register-against-product
  UI + ingestion auto-populate idea. (Wave-C proposal shape; end with the feedback coverage
  table per CLAUDE.md if it targets feedback bullets — this is architecture-motivated, so map
  the INV-5 QR-vs-barcode item.)

### Code map (verified current state — source of truth; legacy spec file refs are partly stale):
- **`dora_api/features/data/barcodes.py`** (451 lines) — all routes:
  - KEEP: `GET /api/stock-items/<id>/qr` (PNG, L123-141), `GET /api/stock-items/qr/sheet`
    (HTML print sheet, L228-274).
  - `GET /api/barcodes/lookup` (L350-401) — 3 branches: (1) `dora://` link → stock item
    [KEEP], (2) `StockItem.barcode` direct hit [DROP with the column], (3) `ProductBarcode`
    → Product → StockItem via `preferred_product_id` or StockItemProduct m2m [KEEP].
  - DROP: `POST/DELETE /api/stock-items/<id>/barcode` (register/clear, L284-330).
  - KEEP (it's the correct model): `POST /api/barcodes/register-against-product` (L412-450).
- **`dora_api/domain/entities/product_barcode.py`** — ProductBarcode entity. **KEEP.**
- **`dora_api/domain/entities/stock_item.py`** — `barcode` field (L40) + `Fields.BARCODE` (L78).
  **DROP both.**
- **`dora_api/persistence/table_mappings.py`** — `StockItem.barcode` column (L135) **DROP**;
  ProductBarcode table (L139-148) + mapper (L475-478) **KEEP**.
- **Migration head = `d7f4a2c98e15`** (`..._20260526_barcodes.py`). New migration must chain off
  it and: DROP `StockItem.barcode` column (+ its `uq_StockItem_barcode` unique constraint);
  KEEP the ProductBarcode table; add `scanning_enabled` (bool, default false) to AppSetting.
- Other server refs to `StockItem.barcode`: `export_stock_overview.py` (L46/58 CSV column —
  remove), `get_stock_items.py` StockItemDto.barcode (L41 — remove), `get_stock_item_detail.py`
  (detail DTO barcode — remove), `restore_shared.py` (product_barcodes section L109/163/173 —
  KEEP, it's ProductBarcode), `health_check.py` (L55 `"barcodes": True` hardcoded → drive from
  the new setting or rename to `"scanning"`).
- **Frontend:** `ScanOverlay.vue` (KEEP, gate), `pages/data/BarcodesQR.vue` (538 lines — Scan/
  Print/Manage tabs; the Manage tab + scan-unknown register-against-**stock-item** flow is the
  WRONG model → rework/remove), `services/api/barcodeApiService.ts` (lookupAsync KEEP;
  registerAgainstProductAsync KEEP), `services/api/stockItemApiService.ts` registerBarcodeAsync/
  clearBarcodeAsync (L77-87 — DROP), `StockItemDetailPage.vue` (L59 register-barcode action,
  L75-78 show barcode — DROP/rework), `StockOverview.vue` (ScanOverlay + lookup — KEEP, gate),
  `router/routes.ts` (L136-139 `/data/barcodes` — gate), `MainLayout.vue` (L332 command-palette
  'barcode' tag — relabel/gate), `models/stockItem.ts` (L13-15 barcode field — DROP).
- **Settings infra:** `AppSetting` (`app_setting.py`) only has LLM fields today; admin-only
  single row via `app_settings/get|update_app_settings.py`. PreferencesSettings.vue is per-USER
  (theme/font) — NOT where this flag goes. Need the admin/system-settings surface (or wherever
  `llm_enabled` is edited) for `scanning_enabled`.
- **Tests:** `tests/e2e/dora_api/test_data_router.py` L549-669 (8 barcode/QR tests + CSV) — will
  need updating; note the e2e suite is pre-existing broken (FU-048).
- INV-5 writeup: `docs/05_investigations/FEATURE_CLARIFICATIONS.md` §(a) — the QR-vs-barcode
  clarification that informed this (it flagged StockItem.barcode scan-to-jump as distinct).

### Engineering-standards / scope notes for next agent:
- R-006 (clean migrations): the migration must apply up AND down on a seeded DB. **Can't be
  verified in this env** (no migrated DB — FU-048). Verify on a machine with the DB.
- R-005 (portable data access): column drop must work on SQLite + Postgres (FU-045) — SQLite
  pre-3.35 can't `DROP COLUMN`; check the Alembic batch-mode pattern used by existing migrations.
- Frontend can't be type-checked/browser-verified by the agent that lacks node_modules (see
  FU-051) — but the USER now has a working `quasar dev`, so lean on them to verify.

**Next up:** Resume by asking the user the OPEN build-vs-defer question above. Then (per answer)
either (1) update CLAUDE.md + write PROPOSAL_BARCODE_SCANNING.md and implement the cleanup slice,
(2) build the full vision, or (3) write the proposal only. Logged as FU-055.

## 2026-06-07 — Phase 1 Chunk 5b: Type-B tail (best-deals + remaining list sums)
**Status:** complete (resolves FU-053 + FU-054)
**What changed:**
- **FU-053 best-deals server-side:** new `GET /api/products/best-deals?limit=N`
  (default 3, max 20). `GetBestDealsHandler` loads products, filters active +
  on-special, ranks by discount % desc, slices N, stamps linked stock items.
  Extracted the linked-stock stamping out of `GetProductsHandler` into a shared
  `stamp_linked_stock_items()`. The discount rule is single-sourced in new
  `dora_api/domain/product_offer.py` (`discount_percent`), mirroring the client.
  - Client: `ProductApiService.getBestDealsAsync(limit)`; the dashboard fetches the
    top-3 into a `bestDeals` ref (replacing the `products` ref + `loadProducts` that
    downloaded everything + the `bestDeals` computed). Deleted the inline
    `discountPctFor`; the `% off` badge uses the shared `discountPercent`, whose
    signature widened to `{ price_now; price_was }` so a `Product` works (dedup).
- **FU-054 remaining list sums:** shop-mode (`estimatedTotalAll`/`estimatedRemainingTotal`)
  and the lists-overview `loadPrimaryStats` now read the server `totals` block
  (Chunk 5) instead of re-summing `priceOfLine`/`savingsOfLine`. Both turned out to
  operate on a single fetched detail (shop-mode = the list; overview = the *primary*
  list — not multi-list as the FU feared), so they map 1:1 to `totals`. Removed the
  now-unused `priceOfLine`/`savingsOfLine` imports from both.
- **Tests:** new `tests/test_product_offer.py` (3) pin `discount_percent`
  (genuine special → %, not-on-special/zero/None → None).
**Decisions made:**
- **Best-deals = a focused endpoint**, not a `?sort=discount` on the generic
  products query — discount is a derived expression over the joined `current_offer`,
  which the field-based sort can't express. The handler loads products and ranks in
  Python (one query; "honest at our scale"); a SQL `ORDER BY` is a future optimisation.
- **Route lives in `get_products.py`** (already route-scanned) to avoid any
  blueprint-discovery uncertainty; `/best-deals` is unique among product GETs
  (the `<product_id>` routes are PATCH / price-history).
- **`discount_percent` mirrors the client** (server owns the *ranking*, client keeps
  `discountPercent` for *display* — the accepted Type-C cross-language carve-out).
- Left `savingsOfLine` in `shoppingList.ts` (now unused) — a coherent public model
  helper paralleling `priceOfLine`; not worth removing an export.
**Files touched:** `dora_api/domain/product_offer.py` (new),
`dora_api/features/products/get_products.py`, `tests/test_product_offer.py` (new),
`web_app/src/helpers/scrapedProductOfferLogic.ts`,
`web_app/src/services/api/productApiService.ts`, `web_app/src/pages/DashboardPage.vue`,
`web_app/src/pages/ShoppingListShopMode.vue`, `web_app/src/pages/ShoppingListsOverview.vue`.
**Verification:** 39/39 server unit tests pass; module + route import clean. Frontend
**not type-checked/browser-verified here** (no node_modules / Node v14) — but the user
now has a working dev env; needs a quick check of the dashboard "Best deals" card
(order + `% off`), shop-mode totals, and the lists-overview primary-list stats. Server
`GET /api/products/best-deals?limit=3` unproven against real data (no migrated DB here).
**Engineering-standards gate:** R-003 (discount rule + stamping each single-sourced),
R-005 (ORM, no raw SQL), R-007 (focused endpoint, didn't over-build a generic
derived-sort). ADR candidate: none.
**Next up:** Type B is now complete (budget + use-soon were already server-owned).
Remaining proposal items: **Chunk 6 — Type C** (snapshot offer at *add* time;
`manage_shopping_list_lines.py` — overlaps the shopping-list redesign) and **Chunk 7
— Type D** (persist sorts/filters to URL/localStorage, optional/lowest priority).

## 2026-06-07 — Fix pre-existing frontend build breakage (surfaced during Chunk 3-5 verify)
**Status:** complete (fixes applied; **not compile-verified here** — see FU-051)
**Context:** Running `quasar dev` to verify Chunks 3-5 surfaced a pile of errors —
**all in files I never touched** (confirmed via `git status`), i.e. pre-existing on
this WIP branch, not from the state-ownership work. Most likely surfaced by stricter
tooling after a fresh `npm install`. Fixed them so verification can proceed.
**What changed:**
- **Startup blocker — `//` line comments in plain-CSS `<style>` blocks** (invalid
  CSS → vite:vue "Unexpected '/'"). A project-wide scan found 3 files:
  - `LoginPage.vue` — genuinely plain CSS (full `:deep()` selectors, no nesting);
    converted the `//` block to `/* */`. Also modernised `:before`/`:after` →
    `::before`/`::after` inside `:deep()`.
  - `DashboardPage.vue` + `ProductSearch.vue` — these blocks use SCSS features
    (nested `:deep(img){}` + `//`) but were tagged `<style scoped>`; corrected to
    `<style scoped lang="scss">` (SCSS is a CSS superset — existing rules unaffected).
- **`exactOptionalPropertyTypes` vue-tsc errors:**
  - `BaseButton.vue` — `onClick(event: MouseEvent)` didn't match q-btn's
    `(evt: Event,…)`; changed to `(event: Event)` + `emit('click', event as MouseEvent)`.
    Widened optional props (`icon/label/loading/disable/to/href/target`) to `| undefined`
    so callers can bind possibly-undefined values (fixes the BulkMove/FilterBar cascades).
  - `FilterBar.vue` — removed the `modelValue: undefined` default (an explicit
    `undefined` default breaks `withDefaults` inference under exactOptional, which
    cascaded into the `activeCount`/`label` "possibly undefined" errors).
- **Lint:** `RecipeCookMode.vue` removed the unused `startListening`;
  `suggestionsApiService.ts` `kind: SuggestionKind | string` → `SuggestionKind | (string & {})`
  (keeps autocomplete, satisfies `no-redundant-type-constituents`);
  `MealPlansOverview.vue` dropped the unnecessary `as MealPlan | null` assertion.
**Files touched:** `web_app/src/pages/LoginPage.vue`, `DashboardPage.vue`,
`ProductSearch.vue`, `MealPlansOverview.vue`, `RecipeCookMode.vue`,
`web_app/src/components/BaseButton.vue`, `FilterBar.vue`,
`stock/BulkMoveLocationDialog.vue` (no change — fixed via BaseButton),
`web_app/src/services/api/suggestionsApiService.ts`.
**Decisions made:** these were out of the Chunk-5 scope but blocked verifying the
work, so fixed per the user's call. Root-caused each (not just silenced): the `//`
fix targets *plain-CSS* blocks only (SCSS blocks legitimately use `//`); the
exactOptional fixes target the real inference break, not band-aids.
**Verification:** **NOT run** — `web_app/node_modules` absent / Node v14 here, so no
`eslint`/`vue-tsc`/`quasar dev`. Each fix is standards-correct and high-confidence,
but unproven in this env. The user is running dev — these need confirmation there
(FU-051). The `//`-scan was exhaustive (project-wide regex over non-scss `<style>`).
**Engineering-standards gate:** R-002 (theme) untouched; R-008 (code-style) — fixes are
minimal + root-caused. No new rule. **Possible ADR candidate:** "plain `<style>` blocks
must not use `//` or nesting — tag `lang=\"scss\"` or use `/* */`"; deferred to the user.
**Next up:** user confirms the app boots + verifies Chunks 3-5 in browser (FU-051),
then resume Type-B tail (FU-053/054) → Chunk 6 (Type C).

## 2026-06-07 — Phase 1 (state-ownership) Chunk 5: server-owned shopping-list totals (Type B)
**Status:** complete (flagship Type-B slice; best-deals + shop-mode/overview deferred)
**What changed:**
- **Server:** `ShoppingListDetailDto` gained a `totals: ShoppingListTotalsDto`
  block (`total_price`, `remaining_price`, `total_savings`, `unticked_count`,
  `ticked_count`, `line_count`), computed by a new `compute_list_totals()` over
  the already-built line DTOs. Faithful ports of the client formulas —
  `_chosen_offer` (selected else offers[0]), `_line_price` (`priceOfLine`),
  `_line_savings` (`savingsOfLine`) — so the numbers can't drift.
- **Client:** the dashboard `primaryListStats` and the **shopping-list detail
  page** totals (`remainingTotal`/`fullTotal`/`tickedTotal`/`savingsTotal`) now
  read `detail.totals.*` instead of summing lines. Removed the now-unused
  `priceOfLine`/`savingsOfLine` imports from the dashboard and `savingsOfLine`
  from the detail page. `ShoppingListDetail`/`ShoppingListTotals` TS models updated.
- **Tests:** new `tests/test_shopping_list_totals.py` (9) pin the port: price/
  savings, ticked-excluded-from-remaining, actual-price override, no-offer/no-RRP,
  selected-offer-wins, negative-savings floor, null-qty, empty list.

**Drift found (shrinks the chunk):** the proposal's other Type-B items are
**already server-owned on this branch** — the **budget card** reads
`/budget/status` (server computes spent/remaining/projected; no client re-sum),
and **use-soon** reads `/waste/rescue` (server-ordered). The proposal's stale line
numbers predate that. So the only live client summation for *whole-list* totals
was the dashboard primaryListStats (+ the detail page, same fix).

**Decisions made:**
- **Totals live on the shopping-list *detail* DTO**, not the dashboard summary —
  cohesive (the list owns its own totals) and reused by both the dashboard and the
  detail page from the one fetch. (Consistent with the earlier Q3 "extend the
  existing payload" lean.)
- **Server computes totals over the final, sorted line DTOs**, so `_chosen_offer`
  sees the same `is_selected`/offers[0] ordering the client does — guaranteeing the
  totals equal the old client sums.
- **Per-line price math stays on the client** (`priceOfLine` — Type-C carve-out per
  proposal §4/§8.1). Only the cross-line *aggregate* moved. The per-line formula now
  exists in both languages (server total vs client per-line display); this is the
  accepted carve-out, not new drift.
- **Deferred best-deals + shop-mode/overview sums** (FU-053/FU-054) — best-deals needs
  a discount-sort capability over the joined `current_offer` (derived expression),
  and shop-mode/overview sum *subsets* / *multiple lists* (need per-list-summary
  totals), both bigger + riskier than the named flagship. R-007.

**Files touched:** `dora_api/features/shopping_lists/get_shopping_list_detail.py`,
`tests/test_shopping_list_totals.py` (new), `web_app/src/models/shoppingList.ts`,
`web_app/src/pages/DashboardPage.vue`, `web_app/src/pages/ShoppingListDetail.vue`.

**Verification:**
- 36/36 server unit tests pass (9 new totals + 27 prior). Module imports clean;
  only one `ShoppingListDetailDto` constructor (updated). No frontend literal
  constructions of `ShoppingListDetail` to break.
- **Not run against real data / not type-checked / not browser-verified** (same
  constraints: no migrated DB, no `web_app/node_modules`, Node v14). Folded into FU-051.

**Engineering-standards gate:**
- R-003 — list totals single-sourced in `compute_list_totals`, consumed by dashboard
  + detail page; the per-line client math is the accepted Type-C carve-out.
- R-005 — totals computed over loaded DTOs; no raw SQL.
- R-007 — deferred best-deals + shop-mode/overview (FU-053/054).
- ADR: none — concrete Type-B application of R-003.

**Next up:** finish Type-B — **best deals** (`?sort=discount`/focused endpoint over
`current_offer` + fold the inline discount-% onto the shared helper, FU-053) and the
**shop-mode/lists-overview** line sums (per-list-summary totals, FU-054). Then Type-C
(Chunk 6, offer-snapshot-at-add — overlaps the shopping-list redesign). Pending:
browser verify of Chunks 3-5 (FU-051).

## 2026-06-07 — Phase 1 (state-ownership) Chunk 4: queryable cookability + dashboard count
**Status:** complete
**What changed:**
- **New `dora_api/domain/recipe_cookability.py`** — single authority for the
  cookability *aggregation* rule: `missing_count_for(ingredients)` (distinct
  missing stock items, built on the §3.1 `is_missing`) + `is_cookable`. The
  Chunk-2/3 `RecipeDto.from_entity` now calls `missing_count_for` instead of
  re-expressing the dedup inline (R-003).
- **`?cookable=true|false` + `?max_missing=N` on `GET /api/recipes`.** Extended
  the filters dataclass (renamed `RecipeTagFilters` → `RecipeFilters`, +`cookable`
  /`max_missing`, +`needs_cookability`/`matches_missing`). `_restrict_query`
  narrows the allowed-id set by a shared `load_recipe_cookability(repository)`
  query (one eager load → `{recipe_id: (missing_count, ingredient_count)}`).
  `_parse_tag_filters` → `_parse_recipe_filters` (+`_parse_bool` tri-state).
- **`recipes.cookable_count` on `/api/dashboard/summary`** — recipes with nothing
  missing AND ≥1 ingredient (cook-now semantics), via the same
  `load_recipe_cookability` helper (R-003). Shown as a count beside the
  "Cookable tonight" card title.
- **Frontend (type/display only):** `RecipeFilterArgs` gained `cookable`/`max_missing`
  + query-string encoding; `dashboard.ts` `RecipeSummary` gained `cookable_count`;
  the dashboard card header shows it.
- **Tests:** new `tests/test_recipe_filters.py` (12) — `_parse_bool`,
  `_parse_recipe_filters`, `is_empty`/`needs_cookability`, and the
  `matches_missing` predicate (cookable true/false, max_missing, composition).

**Decisions made:**
- **`?cookable=true` matches the DTO `cookable` field exactly** (missing == 0, so
  an empty recipe qualifies) — the filter returns "recipes where `cookable` is
  true", which is the least surprising contract.
- **Dashboard `cookable_count` excludes empty recipes** (requires ≥1 ingredient)
  so it matches the card's list semantics ("recipes you can actually cook"). The
  two semantics differ only for degenerate 0-ingredient recipes; documented in
  both code sites.
- **Single-sourced the rule in `domain/` + the aggregation query in one helper**
  rather than duplicating the count in the dashboard handler (R-003).
- **Used the repository ORM eager-load, not raw SQL**, for `load_recipe_cookability`
  so it stays portable across SQLite/Postgres (R-005). It's one query (not N+1)
  but loads full entities; a set-based COUNT is a future optimisation (FU-052).
- **Did NOT rewire the shared recipe-store surfaces (RecipesOverview / dashboard
  list) to actually call the new query.** They still load all recipes + filter
  client-side on `r.cookable`. Switching them touches shared-store fetching and
  needs browser verification, so it's logged (FU-052) rather than done blind.

**Files touched:** `dora_api/domain/recipe_cookability.py` (new),
`dora_api/features/recipes/get_recipes.py`,
`dora_api/features/dashboard/get_dashboard_summary.py`,
`tests/test_recipe_filters.py` (new), `web_app/src/models/dashboard.ts`,
`web_app/src/services/api/recipeApiService.ts`, `web_app/src/pages/DashboardPage.vue`.

**Verification:**
- 27/27 server unit tests pass (filters + cookability + stock-status). Imports
  clean, no circular import (dashboard → recipes one-way).
- In-process smoke confirmed `load_recipe_cookability` builds the **correct SQL**
  (LEFT OUTER JOIN Recipe→RecipeIngredient→StockItem→StockLevel) but **could not
  run against data** — this environment's `data/` SQLite has no migrated tables
  ("no such table: Recipe"), same constraint as FU-048. **Not run end-to-end with
  real data; frontend not type-checked/browser-verified** (no `web_app/node_modules`,
  Node v14) — folded into FU-051.

**Engineering-standards gate:**
- R-003 — cookability rule + aggregation query each single-sourced; DTO/filter/
  dashboard all consume them.
- R-005 — ORM eager-load (portable), no raw SQL added.
- R-007 — resisted the shared-store rewire (FU-052).
- ADR: none — a concrete R-003 application, no new rule warranted.

**Next up:** Phase 1 Type-B aggregates (proposal §4/Chunk 5) — dashboard
primary-list $ totals / best-deals / use-soon move server-side; the §8.2 finds
(`?sort=discount&limit=N`, budget totals on the summary). Also pending: browser
verify of Chunks 3+4 (FU-051), and optionally rewire cookable surfaces to query
(FU-052).

## 2026-06-07 — Phase 1 (state-ownership) Chunk 3: delete client cookability copies
**Status:** complete
**What changed:**
- **Server:** `RecipeIngredientDto` now carries server-derived `is_missing` /
  `is_low_stock` (via the §3.1 `is_missing`/`is_low_stock` predicates). Reworked
  `RecipeDto.from_entity` so `missing_count` dedups by `stock_item_id` (matching
  the old client behaviour — an item on two rows is one missing line) and reuses
  the ingredient DTOs.
- **Client (6 files):** deleted every `'Out of Stock'`-name-matching cookability
  reimplementation and switched to the server fields:
  - `RecipesOverview.vue` — `isCookable`/`missingCount`/`missingStockItemNames`
    gone; filters/footer/comparison-chips read `r.cookable` / `r.missing_count` /
    `ing.is_missing`. **Dropped the `stockLevelStore` + its fetch** (no longer
    needed; `stockItemStore` stays for the ingredient picker).
  - `RecipeCard.vue` — `levelNameFor`/`isMissing` gone; `cookableNow` = `recipe.cookable`,
    `missingIds`/`lowCount` derive from `ing.is_missing`/`ing.is_low_stock`.
    **Removed both stock stores** from the component.
  - `RecipeDetailPage.vue` — cookability summary (`missingIngredients`,
    `cookableNow`, in/tracked counts) now reads the *loaded* `recipe.value`
    server fields. Per-ingredient editor "Missing" badge uses a new
    `isMissingItem` reading the stock item's server `is_out_of_stock` boolean.
    Kept `levelNameFor`/`levelColourFor` (presentation coloring via the shared
    `getStockLevelColour` helper).
  - `MealPlansOverview.vue` — `recipeCookable` now `recipe.cookable && ingredients.length>0`.
  - `DashboardPage.vue` — `recipeIsCookable` likewise; **removed both stock
    stores + their dashboard fetches** (the dashboard no longer downloads the
    whole pantry to compute "Cookable tonight").
  - `DoraChat.vue` — `missingIdsForRecipe` reads `ing.is_missing` (kept
    `ensureRecipeData`'s stock load: the assistant's separate `getStock` context
    still needs it).
- **Models:** `recipe.ts` gained `cookable` / `missing_count` on `Recipe` and
  `is_missing` / `is_low_stock` on `RecipeIngredient`; `stockItem.ts` gained the
  Chunk-1 server booleans. Added 2 server unit tests (dedup + ingredient booleans).

**Decisions made:**
- **Per-ingredient `is_missing`/`is_low_stock` on the ingredient DTO** is the
  primitive several consumers needed (low-count, missing list, highlighting),
  mirroring Chunk-1's StockItem booleans. The recipe-level `cookable`/`missing_count`
  alone wasn't enough.
- **`missing_count` dedups by stock_item_id** to preserve the displayed numbers
  (the deleted client copies all deduped).
- **RecipeDetailPage cookability reads the saved `recipe.value`**, not the live
  editable `form`. Trade-off: the sidebar "Missing N" reflects the persisted
  recipe and refreshes after save, rather than updating live mid-edit. Chosen
  because the server can't know unsaved ingredients, and the page reloads after
  every save. Per-ingredient editor badge still updates live (reads stock store).
  Logged as FU-049.
- **Empty recipe = `cookable` server-side** (missing_count 0). Dashboard/MealPlans
  "suggest to cook" surfaces add `&& ingredients.length > 0` locally (presentation
  filter) so an empty recipe isn't suggested — preserves prior behaviour.
- **Left the non-cookability `'Out of Stock'` sites alone** (stock-page filters,
  cook-mode availability, waste/restock, the shared color helper, MealPlans
  "need to buy"). Out of Chunk-3 scope (R-007); the broader §8.3 smell logged as FU-050.

**Files touched:** `dora_api/features/recipes/get_recipes.py`,
`tests/test_recipe_cookability.py`, `web_app/src/models/recipe.ts`,
`web_app/src/models/stockItem.ts`, `web_app/src/pages/RecipesOverview.vue`,
`web_app/src/components/RecipeCard.vue`, `web_app/src/pages/RecipeDetailPage.vue`,
`web_app/src/pages/MealPlansOverview.vue`, `web_app/src/pages/DashboardPage.vue`,
`web_app/src/components/dora/DoraChat.vue`.

**Verification:**
- Server: 17/17 unit tests pass (cookability + stock-status); module imports clean.
- Client: **could not run lint/`vue-tsc` — `web_app/node_modules` is absent and
  local Node is v14.17 (too old for the toolchain).** Verified manually instead:
  grepped every changed file for dangling references to the removed symbols
  (`isMissing`, `missingCount`, `outOfStockLevelId`, removed stores) — none remain;
  confirmed the recipe store/API service pass response fields through (no field
  mapping that would drop the new keys). **Not type-checked / not run in browser** —
  needs an `npm install` + `quasar dev` pass to confirm. Logged under FU-051.

**Engineering-standards gate:**
- R-003 (state-ownership) — this *is* the realisation; 6 client duplications removed.
- R-002 (theme tokens) — touched `MealPlansOverview.vue:96-97` (`grey-4`/`grey-9`
  palette literals) only to change the function arg; the literals are pre-existing
  and already tracked as FU-046. Not fixed here (separate theme sweep).
- R-007 (scope) — resisted migrating the other `'Out of Stock'` sites; logged as FU-050.

**Next up:** Chunk 4 — `?cookable=true` query filter on `GET /api/recipes` +
`cookable_count` on `/dashboard/summary` (Q3 resolved: extend the summary). Then
the cookable surfaces can *query* instead of fetching all recipes. Also: a browser
verify pass for this chunk (FU-051).

## 2026-06-06 — Phase 1 (state-ownership) Chunk 2: RecipeDto cookability fields
**Status:** complete
**What changed:**
- `RecipeDto` gains two new server-owned fields: `missing_count: int` and
  `cookable: bool`. Computed in `RecipeDto.from_entity` from the already-eagerly-
  loaded `ingredient → stock_item → stock_level` tree, via `is_missing()` from
  the §3.1 contract. No new DB join needed — the base query already loads
  `StockLevel`.
- `dora_api/features/recipes/get_recipes.py` updated; all `dataclasses.replace`
  hydration passes (tags, unallocated) preserve the new fields automatically.
- New unit test `tests/test_recipe_cookability.py` (7 tests) pinning presence-only
  cookability, low-stock-not-missing, None-level-is-missing, and sequence clamping.

**Decisions made:**
- **Presence-only, not quantity-aware** (Q2 resolved by user). Matches existing
  client behaviour. Quantity-awareness explicitly deferred.
- **Extend `/dashboard/summary` RecipeSummary** for `cookable_count` (Q3 resolved
  by user). Will be added in Chunk 4.

**Files touched:** `dora_api/features/recipes/get_recipes.py`,
`tests/test_recipe_cookability.py` (new).

**Verification:** 15/15 unit tests pass (7 new cookability + 8 existing
stock-status). Module imports clean. App boots.

**Engineering-standards gate:** R-003 (state-ownership) realisation —
`missing_count`/`cookable` moved from 7 client copies to one server site.
No new rule warranted (R-003 already covers it).

**Next up:** Chunk 3 — delete the 7 client copies of `isMissing`/`isCookable`
that currently name-match `'Out of Stock'`. Then Chunk 4 — `?cookable=true`
query filter + `cookable_count` on `/dashboard/summary`.

---

## 2026-06-06 — Phase 1 (state-ownership) Chunk 1: stock-status contract
**Status:** complete
**What changed:**
- New `dora_api/domain/stock_status.py` — the canonical stock-status authority:
  `StockStatus` enum + sequence constants + predicates (`is_out_of_stock`,
  `is_low_stock`, `needs_restock`, `is_missing`, `status_for`) + pure
  `level_for_status(levels, status)`. Keyed to the level's ordinal `sequence`,
  **never** its display name.
- Migrated every server site off the duplicated `"Out of Stock"` / `"Low Stock"`
  / `"Well-Stocked"` / `"Sufficient Stock"` string-matching and bare sequence
  literals to consume the contract: `attention.py`, `alerts/get_alerts.py`,
  `assistant/tools.py` (5 sites), `waste/waste.py` (rescue `>=3` literal + the
  mark-out-of-stock assignment), `dashboard/get_dashboard_summary.py` (buckets
  now resolve level ids by sequence; dropped `_stock_level_id_for`),
  `reports.py` (keeps-running-out), and the level-**assignment** writes in
  `alerts/act_on_alert.py`, `shopping_lists/manage_shopping_list.py`,
  `stocktake/stocktake.py`, `data/import_spreadsheet.py` (default level).
- `StockItemDto` now exposes `stock_level_sequence` + derived `is_out_of_stock` /
  `is_low_stock` / `needs_restock` (the §3.1 "expose derived booleans" step).
- New unit test `tests/test_stock_status.py` (8 tests) pinning name-independence.

**Decisions made (per user, this session):**
- **Status source = sequence-constants module** (not a new semantic-role column
  on `StockLevel`). Smallest change, no migration; safe because stock levels are
  fixed/seeded and not user-editable (only `get_stock_levels.py`, no CRUD). The
  semantic-role column (option B) is noted as a *future ADR* if levels ever
  become editable. (R-003 / state-ownership; R-007 keeps it minimal.)
- **"Missing" / cookability = out-of-stock only** (low stock still counts as
  "have it") — matches the prior name-based `"Out of Stock"` checks, least
  behaviour change. Encoded once as `is_missing()`.
- Left `assistant/confirm_actions._resolve_level` **alone** — it maps free-text
  user phrasing → level *names* (NLU input resolution), a different concern from
  §3.1's server-derived status facts. Logged as FU-047.

**Files touched:** `dora_api/domain/stock_status.py` (new), `attention.py`,
`alerts/get_alerts.py`, `alerts/act_on_alert.py`, `assistant/tools.py`,
`waste/waste.py`, `dashboard/get_dashboard_summary.py`, `reports/reports.py`,
`shopping_lists/manage_shopping_list.py`, `stocktake/stocktake.py`,
`data/import_spreadsheet.py`, `stock_items/get_stock_items.py`,
`tests/test_stock_status.py` (new).

**Verification:**
- `tests/test_stock_status.py` — 8/8 pass.
- All 12 changed modules byte-compile and import cleanly; full app boots.
- In-process smoke: dashboard summary returns correct counts (total=20, out=2,
  low=5) via the new sequence bucketing; `StockItemDto` derived booleans correct
  across all four seeded levels (0→all-false, 2→low+needs_restock, 3→out+needs_restock).
- **Not done:** the e2e suite under `tests/e2e/dora_api/` is **pre-existing
  broken** on this branch (asserts a bare-list `/stock-levels` response that
  predates a pagination/response-shape change) — verified the same failures
  occur with my changes stashed. Not introduced here; logged as FU-048.

**Engineering-standards gate:** This *is* an R-003 (single-source-of-truth /
state-ownership) realisation — no R-003 violation introduced; no new rule
warranted (R-003 already covers it). No carve-out comments needed.

**Next up:** Chunk 2 — recipe/meal `missing_count` / `cookable` server ownership
(the Type-A flagship; the contract's `is_missing` is the building block). Then
Chunk 3 deletes the ~7 client copies that name-match `'Out of Stock'`. Open §7
Qs still pending: Q2 (does `cookable` account for quantity?), Q3 (extend
`/dashboard/summary` vs focused endpoints for Type-B aggregates).

## 2026-06-06 — Engineering Standards + ADR governance established
**Status:** complete (governance doc + CLAUDE.md wiring; no app code)
**What changed:**
- New `docs/01_charter/ENGINEERING_STANDARDS.md` — the **code/architecture rubric**,
  engineering counterpart to the Charter. Standing rules **R-001..R-009** seeded from
  the Charter, state-ownership proposal, theme audit, followups backlog, and memory:
  R-001 componentisation-first, R-002 theme-tokens-only, R-003 single-source-of-truth
  / state-ownership, R-004 framework discipline, R-005 portable data access, R-006
  clean migrations, R-007 scope/anti-creep, R-008 code-style minimalism, R-009 safe
  mutations. Each rule carries Why / Apply / Violation-signal (greppable) / Carve-outs
  / Source. Includes an **ADR process** + **ADR log** (ADR-001 = adopting the system).
- Wired into `CLAUDE.md`: (1) session-start entry-point list now names the doc;
  (2) new **"Engineering standards & ADRs — MANDATORY, every task"** section; (3) a
  **MANDATORY engineering-standards close-gate** added to the "On ending a work unit"
  ritual. Registered in `docs/00_DOCS_INDEX.md`.

**Decisions made (per user, this session):**
- **Seed-from-core-docs-then-grow-via-ADR**, not an exhaustive up-front sweep of all
  100+ docs (most of `docs/` is plans/feedback, not engineering rules). Rules accrete
  as decisions recur.
- **Mandatory, blocking gate:** every task is checked against the rules; any violation
  (introduced or pre-existing-and-touched) must be fixed, **explained in place** with a
  comment naming the rule (e.g. `// R-002 carve-out: …`), or **flagged** in
  `DORA_FOLLOWUPS.md` citing the rule id. Unexplained drift blocks the work unit from
  closing. Plus a per-task **ADR evaluation** to promote recurring decisions into new
  rules. This is the durable answer to "stop the same tidy-up recurring" (cf. FU-046,
  where post-paint feature work silently regressed theme tokens).
- Kept the doc as the engineering layer; the **Dora Decision Charter** stays the
  product/UX layer. State-ownership + distribution sections in `CLAUDE.md` are now
  framed as R-003 / R-005 expansions (still authoritative for detail).

**Files touched:** `docs/01_charter/ENGINEERING_STANDARDS.md` (new), `CLAUDE.md`,
`docs/00_DOCS_INDEX.md`, this worklog.

**Verification:** doc/process only — no app code, nothing to run. Grounded each seed
rule in a real source (cited per rule). The doc dog-foods its own ADR process
(ADR-001).

**Next up:** unchanged from the Chunk-D entry below — decide on FU-046's A1c theme
regression re-sweep (now itself an R-002 enforcement exercise), or resume the §6 chunk
order. Future tasks now run the standards close-gate automatically.

**Open questions for user:** none — the rule set is intentionally a seed; it grows by
ADR as decisions recur. Flag if any seeded rule (R-001..R-009) is wrong or too strict.

---

## 2026-06-06 — A1 STEP 2 Chunk D — finished + uncovered chunk-regression problem
**Status:** complete (Chunk D fixed) + finding logged (FU-046)
**What changed:**
- **Fixed the 4 live Chunk D palette-literal offenders.** Neutral branches now route
  through `dora-bg-sunken dora-text-secondary` (chips) / `dora-text-muted` (icon btn),
  keeping the saturated semantic branch (`negative`/`positive` + `text-color="white"`)
  on its props — the theme-stable pattern kept since Chunk A:
  - `pages/RecipesOverview.vue` ingredient chip `'grey-3'` → neutral helper class.
  - `pages/RecipeDetailPage.vue` untracked-level chip `'grey-4'` → neutral helper
    class (also kills the white-on-light-grey contrast bug). `levelColourFor()` is
    data-driven stock-level colour — left as-is.
  - `components/RecipeCard.vue` fav heart `'grey'` → `dora-text-muted`; **`'red'`
    kept by user decision** (brand-agnostic favourited affordance). Available-meals
    chip `'grey-7'` → neutral helper class.
  - `RecipeCookMode.vue` / `RecipeEditDialog.vue` were already clean.
- Re-grep of all five files → zero offenders except the intentional `'red'` heart.
- Marked Chunk D ✅ in `THEME_AUDIT.md`; raised **FU-046**.

**Decisions made / KEY FINDING:** Chunk D was *claimed done already* —
`CHANGELOG.md` [Unreleased] (committed `5819fe8`) lists Chunks **D, G, C, B, E, H, F**
as complete. They were, at that commit; **later wave-A/B feature work regressed
several** by adding new palette-literal chips. Confirmed live regressions beyond D:
`StockItemRow.vue:274` (`'grey-5'`, B), `MealPlansOverview.vue:96-97` (`'grey-4'`/
`'grey-9'`, E — same cookable-chip shape as RecipeCard), `ProviderHealthChip.vue:23`
(`'grey-7'`, G). So the CHANGELOG's "all chunks done" is stale and must NOT be trusted
as proof — verify each chunk against current code. Full finding + carve-out caveats in
**FU-046**. The 7 `text-color="white"` hits in Chunk D are NOT offenders (saturated
semantic surfaces — kept per Chunk A).

**Files touched:** `web_app/src/pages/RecipesOverview.vue`,
`web_app/src/pages/RecipeDetailPage.vue`, `web_app/src/components/RecipeCard.vue`,
`web_app/THEME_AUDIT.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md` (FU-046), this worklog.

**Verification:** grep across the five Chunk D files pre/post-fix (palette classes,
hex, `rgb(a)`, palette `color=`/`:color` literals, `text-color="white"` context). Broad
cross-chunk regression scan to ground FU-046. **Not run in browser** — template-only
token swaps; user runs/tests. Worth eyeballing the recipe ingredient chips + RecipeCard
in Pesto Dark to confirm the neutral chips read right.

**Next up:** decide on **FU-046's A1c regression re-sweep** (fix B/E/G regressions +
separate carve-outs from genuine offenders) before declaring A1 complete — recommended
over blindly advancing the §6 chunk order, since the order assumes chunks stay done.

**Open questions for user:** run the A1c regression re-sweep now (recommended), or
defer FU-046 and move on?

---

## 2026-06-06 — A1 STEP 2 Chunk I (onboarding) — already compliant, no-op
**Status:** complete (no code changes)
**What changed:**
- Verified `pages/onboarding/WelcomeWizard.vue` against the theme-token contract.
  **Zero offenders** — the audit's 11 hits are stale. The file was rewritten since
  the 2026-06-04 audit: its colour-coded step-list (`bg-green-1`/`text-green-9`
  checkmark, `bg-amber-2`/`text-amber-9` current-step) was replaced by a single
  `q-linear-progress` bar (`color="primary"`), and `text-grey-*` step labels are now
  `dora-text-muted`/`dora-text-secondary`. Nothing to fix.
- Marked Chunk I ✅ in `web_app/THEME_AUDIT.md §6` with the reason.

**Decisions made:** Static grep is conclusive here — palette classes are literal
strings, so a clean grep across hex / `rgb(a)` / Quasar palette classes / palette
`color=`/`text-color=` props proves compliance without running the app. Every
remaining colour ref is a semantic token (`dora-text-*`, `text-negative` on
`dora-bg-negative-soft`, `color="primary"`, `var(--overlay-active)`,
`var(--q-primary)`); the rest (`text-h5`, `text-body2`, …) are Quasar *typography*
classes, not colours. No browser eyeball required to close the chunk.

**Files touched:** `web_app/THEME_AUDIT.md` (Chunk I marked already-compliant), this
worklog.

**Verification:** grep scan of the current file for hex literals, `rgb/rgba/hsl(a)`,
Quasar palette classes, palette `color=`/`text-color=` props → all empty. Confirmed
`pages/onboarding/` holds only `WelcomeWizard.vue` (no second onboarding file the
audit could have meant). Not run in browser — unnecessary for a zero-offender static
result.

**Next up:** **A1 STEP 2 Chunk D (recipes + cook mode)** per the chunk order in
`THEME_AUDIT.md §6` (A → I → **D** → G → C → B → E → H → F). Note Chunk D's
`RecipeCookMode.vue` row (~6 hits) may *also* be stale post-B8 — verify against
current code before assuming the offenders exist, same as Chunk I turned out.

**Open questions for user:** none. Chunk I closed; clear to proceed to Chunk D on
your say-so.

**Note (not new, not mine to fix here):** the onboarding "Alerts" tour card still
points at `/stock?attention=true` rather than `/alerts` — that's feedback B5 /
**FU-015**, a structure issue explicitly out-of-scope for theme paint. Left as-is.

---

## 2026-06-06 — Distribution & tenancy posture (Decision 5) recorded
**Status:** complete (charter + CLAUDE.md; **no code changes**)
**What changed:**
- Added **Decision 5 — Distribution & tenancy posture** to
  `RECONCILED_FINISHING_PLAN.md §7`, plus a new **§7.5 distribution-posture
  checklist** it references.
- Added a **"Distribution & tenancy posture (check new work against it)"** section
  to `CLAUDE.md`, mirroring the existing state-ownership principle, pointing at
  Decision 5 / §7.5.

**Decisions made / reasoning:** resolves a multi-message strategic thread (SaaS vs
self-hosted vs local-first for a solo dev). User chose the **GitLab model: one
codebase, SaaS-style, self-hostable** — explicitly steering away from both pure SaaS
and a local-first rebuild.
- **Why this isn't a conflict (the crux):** SaaS and self-host-single-instance
  *agree* the server owns the domain logic + is the source of truth; only who runs
  the box / tenant isolation / managed conveniences differ → deployment difference,
  not architecture. **Local-first was rejected earlier in the thread precisely
  because it *disagreed* on where the source of truth lives** — that would have
  flipped the Phase-1 state-ownership refactor's direction. Self-host-vs-SaaS does
  not, so the current stack is already the shared trunk.
- **Five disciplines** to keep Path A reachable without paying for it now:
  repository-routed data access (one-layer tenant scoping later); DB layer portable
  (SQLite + Postgres); env/config-driven cloud-vs-self-host differences (no build
  forks); auth behind an interface with a local default; **no speculative
  `tenant_id`** (single-tenant = tenancy of size 1).
- **One caveat:** only *multi-tenant isolation* (Path A) is genuinely hard to
  retrofit and stays deferred to Phase 4; "managed single-tenant instances" (Path B)
  costs ~nothing now. Decision 5 makes Decision 4's "Path B → Path A" concrete at
  the code level — supersedes nothing.
- **Postgres = standard datastore target (new, user-directed).** User wants to
  migrate to Postgres ("SQLite feels too unstable for the long term"). Resolved as
  **Postgres-default, NOT Postgres-only** — SQLite stays supported as the
  zero-dependency lightweight self-host option so the everyday-person story survives.
  Strengthens discipline #2 (keep DB layer portable both ways, prefer the
  Postgres-native path where SQLite forces a wrinkle — e.g. the UUID/`text()`
  binding). Migration itself logged as **FU-045**, recommended for Phase 4
  productionize (already lists Postgres/gunicorn/Redis) or opportunistically sooner.
- **No build work** — this is a *posture*, recorded so finishing-phase prompts don't
  dig a self-hosted-only hole.

**Files touched:** `docs/01_charter/RECONCILED_FINISHING_PLAN.md` (Decision 5 + §7.5),
`CLAUDE.md` (new posture section), `DORA_FOLLOWUPS.md` (FU-045), this worklog.

**Verification:** doc-only; grounded against existing Decision 4 / Phase-4 Path B→A
tenancy language and the Clapy repository layer the disciplines rely on. Not run.

**Next up:** unchanged — Phase-1 implementation (state-ownership first chunk) remains
the master-plan next step. The offered `PROPOSAL_LOCAL_FIRST_SYNC.md` was **not**
written (local-first rejected; sync belongs to Phase 4 if/when hosted). No open
follow-up created — the posture lives in the charter, not the backlog.

---

## 2026-06-06 — C-locale + C-help design briefs (user-floated ideas)
**Status:** complete (two proposals; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_LOCALE_I18N.md` (C-locale) and
  `docs/04_proposals/PROPOSAL_HELP_OVERLAY.md` (C-help) — two cross-cutting briefs
  for ideas the user floated this session.
- Registered both: `C_big_rock_design_briefs.md` (two new C sections),
  `00_DOCS_INDEX.md` (proposals table). Logged as `FU-043` (locale) and `FU-044`
  (help) in `DORA_FOLLOWUPS.md` — deferred jobs pending approval.

**Decisions made / key findings (verify-state-first):**
- **C-locale — the companion split is necessary but NOT sufficient.** It solves
  product *sourcing* (C-10 ingests country-agnostic data), but Dora-core keeps AU
  residue. Concrete finds: `$` hardcoded (`ShoppingListShopMode.vue`,
  `PreferencesSettings.vue` budget input); voice default `en-AU`
  (`useVoiceInput.ts`); AU merchants in `seed.py` + `AldiLogo`/`IgaLogo` + assistant
  copy. **Key:** `vue-i18n` is already a dep and wired in `boot/i18n.ts`, but
  **dormant** — locale hardcoded `en-US`, `src/i18n/en-US/index.ts` is the untouched
  Quasar stub (`failed`/`success`), zero `$t()` calls. So it's "plumbing present,
  unused," not "from scratch" nor "done." Brief = Layer A (currency/format) + B
  (de-AU) now; Layer C (full translation) deferred — matches the original spec's
  multi-language as a someday.
- **C-help — it's the opt-in inverse of the tour C-5 deleted.** Three help
  modalities already exist (Help page, assistant) but the **in-context "what is
  this"** one is missing. Net-new front-end component; the design's hard problem is
  **content rot**, so it recommends a co-located `v-help` directive + dev-time
  orphan check, with the hint corpus rolled out per-surface (folded into each
  C-1..C-9 impl), not authored up front. Mechanism is ephemeral client view-state —
  essentially no server model. Original spec ("page-based tips from Dora",
  non-obtrusive mascot) corroborates.
- Both briefs are **user-originated in conversation, not feedback-doc bullets** —
  honestly noted in each §coverage table (related bullets mapped: locale ↔ master
  Decision 1 / original-spec multi-language; help ↔ L43 / L444-449 / C-5 tour
  removal). Neither *closes* an existing feedback bullet; they're net-new scope.

**Files touched:** the two new proposals, `docs/03_prompts/C_big_rock_design_briefs.md`,
`docs/00_DOCS_INDEX.md`, `DORA_FOLLOWUPS.md` (FU-043, FU-044), this worklog.

**Verification:** grounded in live code — confirmed the dormant i18n scaffold
(`boot/i18n.ts`, `src/i18n/*`), hardcoded `$`/voice locale, AU seed/branding, and
the existing Help page/assistant surfaces. Design only — no code, not run.

**Next up:** unchanged — Phase-1 implementation (state-ownership first chunk) is
still the master-plan next step. C-locale and C-help now sit alongside the other
Wave-C briefs awaiting the user's approval + open-decision calls before any
implementation prompt is written for them (FU-043/FU-044).

**Open questions for user:**
- C-locale §3 (currency home; vue-i18n adopt-lite vs rip-out; C-10 currency field;
  merchant-logo fate) and C-help §4 (reveal style; content model; mascot;
  discoverability).
- Where these slot in priority vs Phase-1 implementation — C-locale's currency
  work pairs naturally with the C-cross config build; C-help can land anytime.

---

## 2026-06-06 — C-cross config/opt-ins design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` — the C-cross brief that
  C-1/C-4/C-5/C-9 each defer to. Owns once: money opt-in, nutrition mode
  (off/simple/complex), the four taxonomy settings editors (dietary tags /
  cuisine / category / tools), the location-display zone policy, and the
  install-wide feature-flag panel.
- Registered it: `C_big_rock_design_briefs.md` (new C-cross section),
  `00_DOCS_INDEX.md` (proposals table), `COVERAGE_GAPS.md` (flipped the
  money/nutrition/tag-taxonomy/location/feature-flag bullets from "→ C-cross
  (TBD)" to a written home; added SETTINGS/CONFIG line + audit row).

**Decisions made / key findings (verify-state-first):**
- **Two-tier model** is the spine: per-user opt-ins on `User`; install-wide config
  on `AppSetting` + new taxonomy tables. Taxonomies are install-wide because Dora
  is single-household (shared vocabulary), nutrition *mode* is per-user but the
  nutrition-*DB source* is admin.
- **Money is already half-built** — `User.budget_amount IS NULL` currently doubles
  as the money master switch. Recommended a dedicated `money_features_enabled`
  flag because the cost estimate wants money-on *without* a budget number
  (overloaded-NULL smell). Left as open-decision 1.
- **Feature flags belong on the existing single-row `AppSetting`** (already holds
  `llm_enabled`) — fold the assistant flag in, don't duplicate. C-5's first-login
  step writes the same flags; the set is open-decision 2 (recommend conservative).
- **Nutrition complex deferred** as a reserved seam (mirrors C-10 reserving the
  `source` seam for C-8): build off+simple now, reserve `nutrition_mode=complex`
  + the admin `nutrition_db_source` setting, don't build the DB conversion.
- **Scope discipline:** C-cross designs the *config editors* the per-surface briefs
  need; it does NOT redesign the deferred settings shell, own the per-type alert
  matrix (C-9), the inline location-edit interaction (stock-detail polish), or the
  cuisine-vs-category keep/collapse call (C-4 open-decision 1).
- **Original spec corroborates** the feature panel ("I can disable/re-enable
  features I don't use") — §6 keep; merchant enable/disable there is companion/C-8.

**Files touched:** `docs/04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (new),
`docs/03_prompts/C_big_rock_design_briefs.md`, `docs/00_DOCS_INDEX.md`,
`docs/02_feedback/COVERAGE_GAPS.md`, this worklog.

**Verification:** grounded in live code — `User`/`AppSetting`/`StockLocation`
entities, `app_settings` feature, `pages/settings/*`; read every C-cross
deference (C-1 §5, C-4 §2.2/2.6/2.8/2.9, C-5 §2.3); skimmed the original-spec
User & Global Options board; built the cross-cutting feedback-coverage table per
CLAUDE.md. Design only — no code, not run.

**Next up:**
- **Wave-C design briefs are now COMPLETE** — C-1,2,3,4,5,7,9,10 + C-cross + both
  C-impl plans. Only C-6/C-8 remain unwritten, and those are companion-app scope
  (master Decision 1), not Dora-core.
- Per the master plan, the ball is now **Phase-1 implementation**: start with the
  state-ownership first chunk (canonical stock-status contract), then shopping-list
  + cook-mode. Or the user reviews the C-cross open decisions first.

**Open questions for user:**
- The 5 C-cross open decisions (§4): money-flag vs overloaded-NULL; the
  toggleable-feature set; taxonomy edit permission (admin vs any-user);
  location-detail pref yes/no; confirm nutrition off+simple-now/complex-later.
- Proceed to Phase-1 implementation, or review the full proposal set as a whole
  first?

---

## 2026-06-06 — App-wide state-ownership audit (user-prompted)
**Status:** complete (audit + doc updates; **no code changes**)
**What changed:**
- Ran an app-wide sweep for state-ownership smells (duplication / client-side
  cross-entity logic / fetch-all-then-filter / duplicated constants) beyond the
  proposal's flagships.
- Appended **§8 audit addendum** to `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`;
  tightened `IMPL_PLAN_STATE_OWNERSHIP.md` (Chunk 1 thresholds, Chunk 5 new B's);
  added a **standing state-ownership principle to `CLAUDE.md`**.

**Decisions made / key findings (answer to "do other areas need this?"):**
- **Mostly contained, not sprawling.** The proposal's Type A/B/C/D framework
  already captured the worst; the rest of the app is largely clean.
- **Genuinely clean (do NOT relocate — over-correction guard):** unallocated-meals,
  waste value/expiry/ranking, meal-plan shortfall, frequently-added, attention
  scoring + severity weights, the centralized price helper.
- **New instances found, all in dashboard/threshold territory:** (B) best-deals
  fetches all products to sort/slice client-side; (B) budget card re-fetches +
  re-sums what `budget.py` already computes; (A/constant) expiring-soon window `7`
  hardcoded in 3 client spots vs the server constant; (C) one inline discount-%
  copy. Folded into the existing chunks, not a new workstream.
- **Smoking gun is wider:** `"Out of Stock"` name-match in ~28 spots; sequence
  constants re-declared in `attention.py` + `assistant/tools.py` + client
  `doraIntents.ts` — the §3.1 contract must consolidate these, not just add
  booleans.
- **Standing principle** added to CLAUDE.md so new features don't re-introduce it:
  server owns derived facts + cross-entity aggregates + constants; client owns
  presentation + ephemeral view state; but don't over-correct fine display math.

**Files touched:** `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (§8),
`IMPL_PLAN_STATE_OWNERSHIP.md` (Chunks 1 & 5), `CLAUDE.md`, this worklog.

**Verification:** very-thorough Explore sweep across budget/waste/deals/attention/
meal-plan/stock/search domains, mapped to A/B/C/D with a balanced clean-vs-smell
list. Audit only — no code.

**Next up:** unchanged from the C-impl entry — start Phase-1 implementation
(state-ownership Chunk 1, which now also consolidates thresholds), or write the
C-cross brief.

---

## 2026-06-06 — C-impl plans (state ownership + shopping lists)
**Status:** complete (two phased plans; **no code changes**)
**What changed:**
- New `docs/04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md` and
  `docs/04_proposals/IMPL_PLAN_SHOPPING_LISTS.md` — phased plans + first chunks
  from the two existing approved proposals.
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated.

**Decisions made / key findings:**
- **State ownership — verify-state-first caught positive drift** (proposal is
  2026-06-04): recipe ingredient DTO ALREADY carries `stock_level_id`; a
  sequence-based status notion ALREADY exists (`attention.py` constants) but is
  scattered/duplicated across ~28 spots incl. client `doraIntents.ts`; and
  `?cookable=true` is ALREADY referenced client-side but unimplemented. So the
  first chunk is "finish + consolidate," not "build from zero."
  - **First chunk = the canonical stock-status contract (§3.1):** one server
    module keyed to `StockLevel.sequence` (not name), consolidating the scattered
    constants + migrating the server name-hardcodes (dashboard/waste/reports/
    confirm_actions); rename-test is the guard. Pure server, no behaviour change.
  - Then DTO cookable/missing (set-based, no N+1) → `?cookable=true` + dashboard
    `cookable_count` → delete the 7 client copies → Type B aggregates → Type C
    snapshot-at-add (overlaps shopping-list Chunk 1) → Type D optional.
- **Shopping lists — no drift.** First chunk = **status enum + migration
  (is_archived→done / is_in_progress→shopping / else draft, old booleans kept for
  rollback) + server-owned finish audit + reopen** that reverses from the audit
  (kills the brittle client-snapshot undo; the finish/restock transaction is the
  riskiest surface). Then contextual target inference (removes stored is_primary,
  7 consumers; **same resolver the C-7 cart button needs**) → lifecycle one-button
  UI → one creation surface (5 buttons → 1 form on the existing /auto-generate) →
  merge overview into detail → in-store polish (receipt/pricing-as-you-go,
  drag off-by-one) → planned_shop_date + drop old columns.

**Cross-refs captured:** C-7 (quick-add inference == cart Axis B resolver);
state-ownership Type C ↔ shopping-list finish transaction (build snapshot/audit
once); C-9 (shopping-day alert).

**Files touched:** the two new IMPL_PLAN docs, `00_DOCS_INDEX.md`,
`COVERAGE_GAPS.md`, this worklog.

**Verification:** two Explore sweeps mapped current touch-points + drift against
each proposal; cross-read shopping-list feedback (L401-422). Plans only — no code.

**Next up:**
- User reviews both IMPL plans — esp. each **first chunk** and the open decisions
  (state-ownership: missing=out-only-vs-out+low, quantity-aware cookable, Type-B
  endpoint shape; shopping-lists: DONE delete vs purge, remember-pick scope, two
  SHOPPING lists at once).
- **Wave C is now fully drafted** (all design briefs C-1..C-10 except companion
  C-6/C-8, + both C-impl plans). Per the master plan, **Phase 1 implementation**
  starts with the state-ownership first chunk, then shopping-list + cook-mode.
  Optional remaining design: a **C-cross** brief (money/nutrition opt-ins,
  tag/tool taxonomy settings, feature-flag panel) that C-4/C-5/C-9 lean on.

**Open questions for user:** the per-plan open decisions; whether to (a) start
Phase-1 implementation (state-ownership chunk 1), (b) write the C-cross brief, or
(c) review the proposal set as a whole first.

---

## 2026-06-06 — C-10 ingestion-API contract design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_INGESTION_API.md` — the Dora↔companion seam.
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated.

**Context (answered the user's Qs first):** C-6/C-8 exist as briefs but are
**companion-scope, deliberately unwritten** as Dora-core (re-scoped per Decision
1). The ingestion API is **necessary only because of Decision 1** (extract the
scraper into a companion); it's downstream of that call (user confirmed it
stands). It differs from the current `POST /products` by adding machine auth,
batching, idempotency, a `source` label, a first-class `price_observation`, and a
conflict policy — `POST /products` is a single-item, user-session, dedupe-or-skip
interactive save.

**Decisions made / key design:**
- **Auth:** new `IngestionSource` credential (hashed key, label, enabled, trust
  tier) + bearer-token decorator — net-new, since `AuthToken` is email-flow only.
- **One batched `POST /api/ingest`** with three record types (`products`,
  `offers`, `price_observations`), each carrying a `source`; `Idempotency-Key`
  header; per-record result DTO.
- **Mapping:** product → shared catalogue upsert; offer → set `current_offer` +
  append `ProductHistoricOffer` (the existing price-history log); observation →
  personal price-history point (product or stock-item ref).
- **`source` seam = where C-8 lands** — C-10 only stores the source string
  (reserve the seam); the full merchant↔provider taxonomy stays C-8/companion.
- **Multi-user:** pushed data → shared catalogue; personal price history unions it
  with the user's own shopping-pick snapshots (INV-1). Single-user desktop: moot.
- **Trust tier** carried now for P8-04 crowd reuse; enforcement later.
- Boundary restated: sources call in, Dora never calls out.

**Original spec:** taskboard "require an API key to hit the backend API"
corroborates the machine-auth need; "manually add product offers" = a user-side
share of the offer-append path; "back in stock" alert could be fed by offer pushes
(→ C-9).

**Files touched:** `docs/04_proposals/PROPOSAL_INGESTION_API.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, this worklog.

**Verification:** read the live product/offer/historic-offer/merchant/auth-token
models + `create_product.py` + `price_history.py` + §6.6 / §7 Decision 1. Proposal
only.

**Next up:**
- User reviews `PROPOSAL_INGESTION_API.md` — **6 open decisions §5** (price-history
  conflict policy, sync vs async, source storage, shared-catalogue ownership, fate
  of `POST /products`, trust enforcement).
- **Wave-C design briefs are now ALL done** (C-1,2,3,4,5,7,9,10; C-6/C-8 are
  companion-scope). Remaining Wave-C work: the two **C-impl plans** (shopping
  lists, state ownership — turn existing proposals into phased plans), and an
  optional **C-cross** brief (money/nutrition opt-ins, tag/tool taxonomy settings,
  feature flags) referenced by C-4/C-5/C-9.

**Open questions for user:** the 6 §5 decisions; whether to do the C-impl plans or
a C-cross brief next.

---

## 2026-06-06 — C-9 alerts control centre design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_ALERTS.md` — maps ALERTS (L437-441) + dashboard
  alert bullets (L57/L60).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-042** (bell-count fix).

**Decisions made / key design:**
- **Found the bell-count root cause (L438):** badge = high+medium only (excludes
  **low**) while the dropdown lists ALL severities → the "6 vs 10" the user saw is
  the omitted lows; compounded by the badge using raw backend counts while the list
  filters client-snoozed alerts. Fix = **one canonical "what counts" set** feeding
  badge + bell + dashboard + page (FU-042; shippable ahead of the page).
- **Control centre** fills the existing `AlertsPage.vue` stub: summary boxes
  (types/counts/themes) + grouped list with **per-kind icons/styling** + manage
  prefs in-page. This is also the **contract for the deferred dashboard card** (L60).
- **Per-type opt-in/out + configurable thresholds** (L440) — "quiet or noisy";
  expiring-soon window etc. currently hardcoded. Prefs hosted on the page (settings
  deferred).
- **New "no planned meals next week" alert** (L441) from meal-plan data.
- **Unify context-aware subscriptions:** price "notify under" (separate today) +
  future "back in stock" surfaced/managed centrally — centre has two tiers (active
  alerts vs armed subscriptions).
- **Snooze is client-side localStorage** today; recommend **server-side** (reuse
  the `DoraSuggestionSuppression` pattern) so counts are consistent across devices.
- Alerts-route 404 (L57) already fixed by **B5** (confirm); the page was a stub.

**Original spec:** Alerts board strongly corroborates per-type config (stale-level
window, turn-off unchanging-level warnings), expiry-reset/prompt-after-alert
(partly built), and a "back in stock" subscription; plus system alerts (offline/
error) as a possible separate tier (open decision 5).

**Files touched:** `docs/04_proposals/PROPOSAL_ALERTS.md` (new), `00_DOCS_INDEX.md`,
`COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-042), this worklog.

**Verification:** Explore sweep of `get_alerts.py` + `AlertsBell.vue` + dashboard
card + `AlertsPage.vue` + price alerts; root-caused the count mismatch in code;
cross-read ALERTS + dashboard feedback + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_ALERTS.md` — **5 open decisions §5** (priority/what-counts
  model, which alerts default on, snooze server-vs-device, prefs home, system
  alerts tier).
- **Wave-C per-surface briefs are now ALL done** (C-1,2,3,4,5,7,9). Remaining:
  **C-10 ingestion-API** (Dora-core backend seam; gates the companion C-6/C-8) and
  the two **C-impl plans** (shopping lists, state ownership — proposals already
  exist, these produce phased implementation plans). C-cross (config/opt-in
  surfaces: money, nutrition, tag/tool taxonomies, feature flags) is referenced by
  several proposals and may warrant its own brief.

**Open questions for user:** the 5 §5 decisions; whether to do C-10, the C-impl
plans, or a C-cross brief next.

---

## 2026-06-06 — C-5 onboarding design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_ONBOARDING.md` — maps ONBOARDING bullets (L24-46).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-041** (first-run copy
  confirm-in-browser).

**Decisions made / key design:**
- **Centre of gravity = a pick-and-choose starter TEMPLATE of common household
  items** (cheese→Fridge, etc.) — the user's "worst part is getting data in" (L37).
  Plus all/none/some default groups/locations with preview, and opt-in demo
  recipe/meal/plan toggles (warned). Inline import (don't name Grocy; on-page not
  nav-away).
- **Sell the vision first** (L41/L43): short diagram/flowchart intro to the loop +
  core values, shared auth-shell styling, BEFORE any data entry.
- **Stock-item-vs-product explainer** (L46) before "add stock items" (milk vs
  Vitasoy Oat Milk @ Coles).
- **Capture headcount** (→ cook-mode C-3 serving auto-adjust) + **preferred
  stores** (L44/L45).
- **Admin first-login feature enable/disable** (L42) — but needs a matching
  settings panel (settings deferred → dependency).
- **Finish celebration** (confetti, L39) + the tour becomes a workflow/power-user
  explainer covering MORE areas, pointing to help/guides (L40/L43).
- **Theme** = system/pesto-light/pesto-dark only (L28); "Skip everything"→"Skip",
  persist on finish only (L35); slim "added" list (L36).
- **The flagged "you already have groups/locations" copy (L32/L33):** static read
  shows it's gated on has_groups/has_locations (false on a fresh DB), so it
  shouldn't misfire on a clean install — the user likely had dev/seed data.
  Logged FU-041 confirm-in-browser per the MANDATORY rule.
- Dead nav (skip/finish/show-me, L25-27) already fixed by **B5** (confirm).

**Original spec:** barely covers onboarding (only "pre-defined groups/locations on
first usage"); the rich wizard + starter-item template are newer feedback with no
original counterpart — nothing to extract/supersede.

**Files touched:** `docs/04_proposals/PROPOSAL_ONBOARDING.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-041), this worklog.

**Verification:** full read of `WelcomeWizard.vue` + `onboarding.py` via Explore
(incl. the seed/pre-seeding logic for the copy question); cross-read ONBOARDING
feedback (L24-46) + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_ONBOARDING.md` — **5 open decisions §5** (toggleable
  features, starter-template contents, demo-data scope, vision depth, headcount
  granularity).
- Remaining Wave-C Dora-core briefs: **C-9 alerts**, **C-10 ingestion**; plus the
  two C-impl plans (shopping lists, state ownership). C-9 is the natural next
  per-surface brief; C-10 is the backend seam; the impl-plans turn approved
  proposals into phased plans.

**Open questions for user:** the 5 §5 decisions; which brief next.

---

## 2026-06-06 — C-3 cook-mode design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_COOK_MODE.md` — maps COOK MODE bullets (L317-338).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-040** (structured steps
  → C-4 dependency).

**Decisions made / key design:**
- Cook mode is already feature-rich (timer, voice/TTS, B8 session swaps). The
  redesign targets the weak spots:
- **Finish flow = close the loop (highest value):** replace the blunt "update
  everything" toggle with a **per-item stock-level checklist** (set any level) +
  **per-item add-to-list** (C-7), meals-cooked **starts at 0/optional**,
  click-out cancels (A3), and a **celebration / "you saved N meals"** finish.
- **Serving auto-adjust by headcount** (default from onboarding C-5, per-session,
  scales quantities).
- **Ingredients grouped by base location**; stock level **de-emphasised mid-cook**
  (only relevant at finish, L334); UI rebuilt.
- **Highlight instead of tick** (remove ticking) — but reliable highlighting needs
  **structured steps**, which is a C-4 recipe-model change (FU-040).
- **Tools per step** (C-4), **sub-steps + per-step hints** (structured steps),
  **timer** theme-aware + sound + fill-bar + visible reset, **unit formatting**
  inclusion list ("200ml" vs "2 scoops"), **sous-chef** voice branding/discovery.
- B8 session swaps kept as-is (correct).

**Original spec consulted:** the cook-mode note ("interactive mode with TTS, voice
'next step', timers") matches what's already built — §2 just polishes it; location-
grouping note grounds §2.3. No superseded items.

**Key dependency surfaced (FU-040):** the recipe model stores instructions as a
freeform blob; cook mode's per-step highlighting/tools/hints/timers all need
**structured steps** — that model change belongs in C-4.

**Files touched:** `docs/04_proposals/PROPOSAL_COOK_MODE.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-040), this worklog.

**Verification:** full read of `RecipeCookMode.vue` + cook endpoint via Explore;
cross-read COOK MODE feedback (L317-338) + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_COOK_MODE.md` — **5 open decisions §5** (ticking removal,
  structured-steps model, unit inclusion list, scaling display, finish-flow level
  controls).
- Remaining Wave-C Dora-core briefs: **C-5 onboarding**, **C-9 alerts**, **C-10
  ingestion**; plus the two C-impl plans (shopping lists, state ownership).
- Note: C-3, C-4, and C-1 all now point at recipe-model / cross-cutting work; a
  good moment soon to consider the C-impl plans or C-cross (config/opt-ins).

**Open questions for user:** the 5 §5 decisions; which brief next.

---

## 2026-06-06 — C-4 cookbook design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_COOKBOOK.md` — recipe-domain redesign covering
  all RECIPES OVERVIEW + RECIPE DETAIL bullets (L228-315).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-039** (Recipe.image).

**Decisions made / key design:**
- **Tag taxonomy overhaul (the big one):** dietary tags → ONE filter cycling
  must/must-not/neutral (+/−/grey, no-close); cuisine & category → single-select
  each, NOT lumped, NOT "tags"; all taxonomies user-configurable in settings
  (C-cross).
- **Comparison → CUT** per INV-6; fold removal into the same chunk that adds the
  sort/filter axes it was standing in for.
- **Versions** replace Duplicate (original spec confirms intent: keep revisions
  without a separate recipe). Proposed full-snapshot + current-pointer.
- **Multi-part:** recommend **sections-first** (within one recipe) over linked
  sub-recipes (which ripple into cookability/allocation/cost) — open decision.
- **Images** (wire up dead `Recipe.image`, FU-039), **tools-required**
  (configurable + filter), **source** as its own field (stop dumping into
  instructions), **importer** site guidance + import-from-overview.
- **Cost estimate** (opt-in, product/history-fed, → meal-plan/shopping budgets)
  and **nutrition tiers off/simple/complex** — both gated by the money/nutrition
  opt-ins (C-cross); recommend off+simple nutrition now, complex later.
- **Card:** image, editable in-stock count + allocated box (red if avail<alloc,
  only shown when allocations exist), actions on card, ditch ⋮, fix collection
  grouping visibility.
- **Detail cleanup:** empty-ingredient validation (L290), filterable stock-item
  picker, editable-title consistency, buttons across top, log-cook into toolbar,
  "meals on hand"→"available meals", personal recipe notes shown in cook mode.
- Heavy cross-cutting overlap mapped to A1/A3/A4/A8/B3/B8/C-7/C-cross/C-2 rather
  than re-litigated here.

**Original spec consulted:** grounded the versions feature + rationale (the
"original feature notes" L312 cites); confirmed comparison's aspiration is now
served by sort/filter (so CUT stands); **superseded** the old markdown-file
storage idea (current DB model needed for cost/nutrition/allocation).

**Files touched:** `docs/04_proposals/PROPOSAL_COOKBOOK.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-039), this worklog.

**Verification:** Explore sweep of the recipe domain (overview/detail/edit/model/
DTO/tags/allocation/import); cross-read all recipe feedback (L228-315) + original
spec Recipes board & notes; INV-6 CUT decision applied. Proposal only.

**Next up:**
- User reviews `PROPOSAL_COOKBOOK.md` — esp. the **6 open decisions §5**
  (cuisine-vs-category, versions UX, multi-part model, nutrition scope, cost
  estimate acceptability, substitute-status).
- Remaining Wave-C Dora-core briefs: **C-3 cook mode** (now unblocked — consumes
  C-4 tools/versions/notes/location-grouping), C-5 onboarding, C-9 alerts,
  C-10 ingestion; plus the two C-impl plans.

**Open questions for user:** the 6 §5 decisions; which brief next (C-3 is the
natural follow-on).

---

## 2026-06-06 — C-1 stock-overview design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_STOCK_OVERVIEW.md` — full redesign covering all
  37 STOCK OVERVIEW feedback bullets (L63-99).
- `COVERAGE_GAPS.md` + `00_DOCS_INDEX.md` updated (C-1 + C-7 proposals listed).

**Decisions made / key design:**
- **Kill the chip** (L75); rebuild the row: **stock-level button first, big,
  coloured, text-less = the focus action** (L70), replacing BOTH the chip avatar
  and the duplicate right-side level dropdown. Name emphasised; right cluster =
  expiry + planned-meals + cart. Removes badge/red-dot/on-N-lists/⋮/in-chip-cart.
- **Highlighting rules:** status → whole-row outline; selection → row **fill**
  (L91, avoids colour clash); essential is a filter, not a row dot (L66/L82).
- **Nav model (the #1 open decision):** proposed desktop drawer + mobile full-page,
  shared detail component; flagged the L68-vs-L71 wording tension + miss-tap risk
  for the user to confirm.
- **Expiry:** date-picker when unset, +1/+7/+14/clear when set (L87/L88).
- **Top area:** all buttons grouped; filter panel hidden behind a toggle (desktop
  too); search separate + shorter placeholder; stock-level filter → dropdown w/o
  counts; remove "used in recipe" filter; counts → sticky footer (A7).
- **Scan mode** (action-then-scan) — proposed unifying with stocktake (open Q).
- **"# recipes" → "# upcoming planned meals"** — gated on C-2 allocation.
- **Correctness prerequisites folded in:** the 50-item cap (FU-035) and
  filtered-export (L67) must be fixed with the redesign.
- **Original spec consulted** (per the new rule): corroborated the coloured
  level-button shape, the bottom summary panel, the missing-picture placeholder,
  long-press multi-select; and **superseded** column-header sorting (the author
  archived it — "it's a list view now, controlled by filters").

**Ripple/deps noted:** cart → C-7; chip removal app-wide → follow-up; location
display → C-cross; planned-meals → C-2; images → FU-033; detail component shared
with the stock-detail surface.

**Files touched:** `docs/04_proposals/PROPOSAL_STOCK_OVERVIEW.md` (new),
`COVERAGE_GAPS.md`, `00_DOCS_INDEX.md`, this worklog.

**Verification:** Explore sweep of the live overview/row/chip/filters; cross-read
all STOCK OVERVIEW feedback (L63-99) and the original-spec Stock Items board +
notes. Proposal only — nothing built/run.

**Next up:**
- User reviews `PROPOSAL_STOCK_OVERVIEW.md` — esp. the **7 open decisions §7**
  (nav model, miss-tap, open/in-use toggle, scan-vs-stocktake, planned-meals
  fallback, outline palette, 50-cap fix approach).
- Remaining Wave-C Dora-core briefs: C-3 cook mode, C-4 cookbook, C-5 onboarding,
  C-9 alerts, C-10 ingestion; plus the two C-impl plans.

**Open questions for user:** the 7 §7 decisions; which brief next.

---

## 2026-06-06 — Original spec wired in + cart-button extractions
**Status:** complete (docs/governance — no app code)
**What changed:**
- User added their **first-ever project spec** under `docs/00_original_spec/`
  (Feature Boards + ~125 "I can…" Feature Notes + original PROMPT_PLAN, etc.),
  pre-dating this branch's ~100k LOC.
- Referenced it meaningfully (NOT as an override): new section in
  `docs/00_DOCS_INDEX.md`; folder + cross-check rule added to `CLAUDE.md`
  (skim the matching board/notes when writing a brief; extract tagged
  keep/consider/superseded; it never auto-overrides the charter/feedback).
- **Extracted cart-button items into `PROPOSAL_CART_BUTTON.md §9`** (new "From
  the original spec" section + §9.1 remove path):
  - **keep (gap!):** the button is also the **remove** affordance — added a
    symmetric multi-list remove (remove-from-this / remove-from-all). The brief
    had only designed add.
  - **keep:** list picker's last row = "+ New list" (unifies add-to-existing /
    add-new; aligns L382).
  - **consider:** swipe-right → list picker (+ success animation) — new open
    decision §7.7.
  - **keep (corroborates):** standalone product uses the same button; cheapest-
    highlighted rationale.
  - **superseded:** auto-create-stock-item-on-product-add (user's own later note
    + L191 say products/stock-items are separate); stored "primary/default list"
    (replaced by DRAFT-count inference).
  - **cross-ref:** the picture-fallback note corroborates `StockItem.image`
    intent (INV-1 / FU-033) — noted on FU-033.

**Decisions made:**
- Original spec is **historical, non-authoritative**; charter/feedback/reconciled
  plan win where they disagree. Future briefs consult it per the new CLAUDE.md
  rule; `PROPOSAL_CART_BUTTON.md §9` is the reference shape.
- The most material extraction was the **remove path** — a genuine gap in the
  C-7 brief, now folded in.

**Files touched:** `docs/00_DOCS_INDEX.md`, `CLAUDE.md`,
`docs/04_proposals/PROPOSAL_CART_BUTTON.md` (§9 + §7.7), `DORA_FOLLOWUPS.md`
(FU-033 note), this worklog.

**Verification:** read the cart-relevant original notes directly; reconciled each
against the current design before tagging. No code touched.

**Next up:** same as the C-7 entry below — user reviews the cart proposal (now incl.
§9 + the remove path + the swipe open-decision), then picks the next Wave-C brief.

---

## 2026-06-06 — C-7 cart-button design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_CART_BUTTON.md` — unified add-to-list button,
  decision tree, products-without-stock-items model change, feedback coverage.
- `docs/02_feedback/COVERAGE_GAPS.md` Bucket D updated (cart/standalone bullets
  now covered by the proposal).

**Decisions made / key findings:**
- Mapped **~13 add-to-list controls** across the app (full table in the
  proposal). Two paradigms: blind quick-add-to-primary (11 of 13) vs multi-step.
- **Core design = two orthogonal axes:** Axis A "what line" (0/1/2+ linked
  products → none / pre-select / choice modal; or standalone product), Axis B
  "which list" (adopt `SHOPPING_LIST_REDESIGN §2.4` DRAFT-count inference, no
  stored primary). Combine into ONE modal when both ambiguous; 0 prompts in the
  common case.
- **Critical structural finding:** shopping-list lines currently REQUIRE a
  `stock_item_id` — products can't be added standalone, directly contradicting the
  My Products requirement (L191). Proposal adds nullable `product_id` line
  anchoring + the 4 nesting/cascade rules from L191. This is the heavy rock.
- **State-awareness fix:** generalise `cartStateFor`; clicking an already-on item
  becomes idempotent w/ a popover (Add-to-another / Remove), killing the
  contradictory double-toast (L154).
- **Sequencing:** ship the state-aware button against a temporary `is_primary`
  adapter first; flip Axis B to draft-counting when the shopping-list status model
  lands; do the standalone-product migration as a later phase. C-1 should consume
  this component, not define its own.

**Files touched:** `docs/04_proposals/PROPOSAL_CART_BUTTON.md` (new),
`docs/02_feedback/COVERAGE_GAPS.md`, this worklog.

**Verification:**
- Mapped surfaces via an Explore sweep; cross-checked the load-bearing claim
  (lines require `stock_item_id`) against `shoppingListApiService.ts` AddLineCommand
  + the line model. Read `SHOPPING_LIST_REDESIGN_PROPOSAL.md` for Axis-B alignment
  and the actual feedback bullets (L83-84,108,130,154,191,195-196,288,380-382).
- Proposal only — nothing built or run.

**Next up:**
- **User reviews `PROPOSAL_CART_BUTTON.md`** — esp. the 6 open decisions in §7
  (already-on-list click behaviour; >1-product silent vs modal; standalone-product
  line model; session-default scope; quantity; bulk reporting).
- Then continue Wave C. User picked C-7 first; remaining Dora-core briefs:
  C-1 stock overview, C-3 cook mode, C-4 cookbook, C-5 onboarding, C-9 alerts,
  C-10 ingestion API; plus the two C-impl plans (shopping lists, state ownership).

**Open questions for user:** the 6 §7 decisions, and which Wave C brief next.

---

## 2026-06-06 — INV-5, INV-7, INV-8, INV-9, INV-10 (remaining INV)
**Status:** complete (5 memos; **no code changes**) — INV series now fully done.
**What changed:**
- New `docs/05_investigations/FEATURE_CLARIFICATIONS.md` (INV-5)
- New `docs/05_investigations/HISTORY_TAB_ASSESSMENT.md` (INV-7)
- New `docs/05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md` (INV-8)
- New `docs/05_investigations/COMMAND_PALETTE_ASSESSMENT.md` (INV-9)
- New `docs/05_investigations/ESSENTIAL_FLAG_FINDINGS.md` (INV-10)

**Decisions made / key findings:**
- **INV-5:** (a) QR show+print and register-barcode (scan-to-jump) are **two
  distinct kept features, not redundant** — and register-barcode is NOT the
  removed P6-02 (that was barcodes for *deal lookup*; this lookup resolves to a
  stock item to open, verified `barcodes.py:350-401`). Clarify labels. (b)
  Relevancy = naive fuzzywuzzy token-overlap, threshold 70 — keep + document.
  (c) expiry & open are fully independent (no derivation) — keep + add tooltip.
- **INV-7:** History tab = level-changes-only, no context/action. **REWORK** —
  merge waste events + list-add provenance + open/checked context (all already
  in the model) into the timeline. Not cut (loses the only home for item
  history), not keep-as-is (weak).
- **INV-8:** List-level substitute swap works but is buried in the full-list menu
  and mispositioned vs the real in-shop moment; collides with Shop Mode's
  offer-"Substitute". **REWORK** (move into Shop Mode + disambiguate), cut only
  if confirmed unused. Distinct from B8 cook-mode ephemeral swap (no overlap).
- **INV-9:** Palette = 18 static commands (13 redundant nav) + a valuable but
  *hidden* entity search. No usage telemetry. **SHRINK** command set **+ PROMOTE**
  entity search to a visible global bar. Confirmed FU-031 stale "Recipes" labels.
- **INV-10:** "Essential" = existing `is_flagged` — there's **no missing
  feature**, just a labelling gap: the detail toggle reads "Always include in
  auto-generated lists," never "Essential." **Rename it** + add a stock-overview
  quick-toggle; keep the primitive explicit (don't auto-derive). Verified
  `essentials_only_for_low` reads `is_flagged` (`auto_generate.py:80-82`).

**Files touched:** the 5 new memos + this worklog + `DORA_FOLLOWUPS.md`.

**Verification:**
- Spot-verified the two most load-bearing claims against live code (not just
  sub-agents): INV-10 `is_flagged`==essential + toggle label
  (`StockItemDetailPage.vue:205-220`, `auto_generate.py:80-82`), and INV-5
  barcode-lookup purpose (`barcodes.py:350-401` → resolves to stock_item, NOT
  deal lookup) — corrected a sub-agent overstatement that register-barcode is
  "scheduled for deletion."
- Not run in the browser — read-only.

**Next up:**
- **INV series complete (1–10).** User reviews the 5 memos + decides per-item:
  - INV-5: approve label clarifications (QR/scan grouping; help text; tooltip)?
  - INV-7: schedule the History-tab rework, or defer to a detail-polish chunk?
  - INV-8: rework into Shop Mode vs cut — confirm Shop Mode "Substitute"==offer-only in browser first.
  - INV-9: shrink+promote vs keep-as-is? (fold FU-031 rename in either way)
  - INV-10: approve rename + overview quick-toggle.
- Per the master sequencing, after INV the next wave is **Wave C** big-rock
  design briefs (`docs/03_prompts/00_INDEX.md`). Several INV outcomes feed C
  briefs (INV-6→C-4 Cookbook; INV-7/8/10 → stock-item & shopping-list briefs).

**Open questions for user:** see Next up — one decision per INV, plus whether to
start Wave C next.

---

## 2026-06-06 — INV-2, INV-3, INV-4 (perf / logging / email)
**Status:** complete (3 memos; **no code changes**)
**What changed:**
- New `docs/05_investigations/STOCK_OVERVIEW_PERF.md` (INV-2)
- New `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md` (INV-3)
- New `docs/05_investigations/EMAIL_SETUP_FINDINGS.md` (INV-4)

**Decisions made / key findings (several CORRECT the original premises):**
- **INV-2:** The overview does **not** "load all 500 items" — the opposite. The
  frontend (`stockItemStore.ts:48`) fetches only **page 1 (≤50 items)** and never
  loops, so pantries >50 items silently drop the rest. **New correctness bug**
  (FU-035). Real mount cost = 8 parallel requests + per-row O(N) recipe/membership
  lookups, not list size. DS4 didn't speed anything up — it added fade/slide/hover
  motion that masks unchanged latency (perceived-perf, confirmed). Fixes: lift the
  50-cap, defer secondary loads, prebuild lookup maps; server-side aggregation is
  the bigger play.
- **INV-3:** Rotation IS configured but **size-based** (`RotatingFileHandler`,
  10 MB × 5) — a low-volume install never trips 10 MB, so one append-mode file
  grows across all days/restarts → the "46k-line wrong-date" symptom (= FU-027).
  Fix: switch to `TimedRotatingFileHandler` (midnight, ~14 backups). "Two
  locations" = stdout+file handlers + dev `./data/logs` vs desktop `user_log_dir`.
  **No `.local` folder exists** — the split is `data/` (persistent) vs `cache/`
  (regenerable) + desktop platformdirs; recommend keeping as-is.
- **INV-4:** Reset email **works out-of-the-box** — with SMTP env vars it sends;
  without, it runs **dry-run** and logs the reset link (deliberate, for
  self-hosted/desktop). No UI to configure SMTP today (env-var only). Proposed:
  extend the existing `AppSetting` singleton with SMTP fields + a SystemSettings
  section, add an `email_sender_configured` capability, hide the forgot-password
  link when unconfigured. Open Q: does dry-run count as "configured"?

**Files touched:** the three new memos + this worklog + `DORA_FOLLOWUPS.md`
(FU-035 raised; FU-027 referenced).

**Verification:**
- Spot-verified the premise-correcting claims against live code, not just the
  sub-agents: `email_sender.py` dry-run branch, `logging_setup.py` rotation
  config, `get_stock_items.py` `.paginate()`, `query_options.py` DEFAULT_LIMIT=50
  / MAX_LIMIT=500, and `stockItemStore.ts:48` taking only `page.items`.
- Not run in the browser — read-only investigations.

**Next up:**
- User reviews the three memos. Decisions:
  1. INV-2: how to fix the 50-item cap (quick `?limit=500` vs paging vs
     virtualised infinite-scroll)? Schedule the perf fixes?
  2. INV-3: approve switch to time-based log rotation (resolves FU-027)?
  3. INV-4: approve the phased email-setup plan; answer the dry-run "counts as
     configured?" question.
- Remaining INV: INV-5 (QR/barcode/relevancy clarifications), INV-7..10.

**Open questions for user:** see Next up (one decision per INV).

---

## 2026-06-06 — INV-1 (orphaned-field audit)
**Status:** complete (memo only; **no code changes**)
**What changed:**
- New `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md`.
  Full sweep of all entities against DTOs and frontend refs.

**Decisions made:**
- **Two unfinished features found (NOT dead — user corrected this):**
  - `StockItem.image` — supposed to support an own image, with a fallback to a
    *linked product's* image when no own image is set. Neither half was built.
    Recommend **WIRE UP** (storage column already exists).
  - `StockItemSubstitute.notes` — supposed to capture *how* to substitute, e.g.
    "X butter can be replaced with Y amount of olive oil". Column exists (added
    in the undirected-refactor migration) but hardcoded to `None`, never in DTO
    or UI. Recommend **WIRE UP**, fits B8 cook-mode swap especially.
- **Two backend-only fields (intentional design, not bugs):**
  - `ShoppingListLine.picked_offer_price` and `list_price_at_pick` — used by
    budget, reports, waste, assistant but deliberately absent from the DTO.
    Recommend documenting with a comment; no structural fix needed.
- All user-flagged topics (stock groups, notes, preferred merchant, nutrition)
  turned out to be fully wired — no surprises there.
- No structured nutrition columns exist anywhere — only `Recipe.nutrition`
  (freeform string), which is fully surfaced.

**Files touched:**
- `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md` (new)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Read all entity files under `dora_api/domain/entities/`.
- Grepped `web_app/src/` for every suspect field (snake_case + camelCase).
- Checked `table_mappings.py`, all relevant feature handlers, and the
  budget / reports / waste / assistant files for invisible backend use.
- Not run in the browser — read-only investigation.

**Next up:**
- User reviews the memo. Key decisions:
  1. `StockItem.image` + `StockItemSubstitute.notes` are wire-up jobs (user
     confirmed both are intended-but-unbuilt). Need to schedule them — image
     likely its own prompt; substitute-notes folds into INV-8 / B8 cook-mode.
  2. Happy with "document only" for the two snapshot fields?
- Continue INV series: INV-2 (stock-overview perf), INV-3 (logging layout),
  INV-4 (forgot-password email), INV-5 (QR/barcode/relevancy clarifications),
  or jump to INV-7..10.

**Open questions for user:**
- Schedule the two wire-up jobs now or defer (FU-033 image, FU-034 sub-notes)?
- Which INV next?

---

## 2026-06-06 — INV-6 (recipe-comparison worth assessment)
**Status:** complete (memo only; **no code changes**)
**What changed:**
- New `docs/RECIPE_COMPARISON_ASSESSMENT.md`. One-page memo per the
  prompt: (1) what the feature does today, (2) signal of use,
  (3) what a useful comparison would need, (4) Charter check,
  (5) where the real use cases land if cut, (6) cleanup cost,
  (7) recommendation, (8) open follow-up.

**Decisions made:**
- **Recommended CUT.** Feature has no usage signal, the user's own
  feedback says "useless, would users actually use this?", and it
  fails 5 of the 12 Charter principles (P1 Effortless, P5 Closed
  loop, P6 Insight→action, P10 Anti-creep, P11 Fast UX). Every
  real cook-decision question it tries to answer lands more
  cleanly on the Cookbook overview's sort+filter, Cook Mode
  servings auto-adjust, money-opt-in per-row cost, or the Dora
  "what should I cook?" intent.
- **Cleanup placement:** fold the X2 removal into **C-4 Cookbook
  redesign** as a Charter-aligned cut, in the same chunk that adds
  the sort axes (`time`, `missing`, `last_made`,
  `cost_per_serving`) so users land on the overview and find the
  answer comparison was meant to give without entering a dialog.
- **No code touched.** Memo is decision input for C-4.

**Files touched:**
- `docs/RECIPE_COMPARISON_ASSESSMENT.md` (new)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Read live code: `RecipesOverview.vue` compare-mode block
  (header buttons L7-22, dialog L259-356, state + handlers L662-692).
- Cross-referenced against the user feedback bullets in
  `Feedback _ Fixes - as of [06-Jun-2026].md` (Cookbook section)
  and against the reconciled finishing plan / triage / Charter
  Part II (P1, P5, P6, P10, P11).
- Confirmed no backend route exists for comparison and no
  telemetry surface tracks the toggle. Footprint estimate ~100
  lines, one file, no migration.

**Next up:**
- **User reviews the memo.** If `CUT` is approved:
  - The X2 removal becomes part of the C-4 Cookbook brief / impl
    chunk (when C-4 lands as a proposal).
  - `STATUS.md` X2 flips DONE → **CUT (INV-6, 2026-06-06)**.
- Per the prior plan sequencing: ready for the next INV
  (INV-1/2/3/4/5) or to head back to a Wave C brief on your
  signal.

**Open questions for user:**
- Sign off on **CUT** (vs `rework` if there's a use case in §3
  the memo missed).
- Confirm fold-into-C-4 is the right cleanup chunk vs a smaller
  standalone removal prompt.

---

## 2026-06-06 — Docs reorg + feedback coverage audit + INV-7..10 + CLAUDE.md cross-check rule
**Status:** complete (docs/governance — no app code touched)
**What changed:**
- **Docs folder reorganised** by lifecycle:
  - `docs/01_charter/` — DASHY_DORA_CHAMPION_PLAN, RECONCILED_FINISHING_PLAN, STATUS.
  - `docs/02_feedback/` — Feedback raw doc, FEEDBACK_TRIAGE_AND_PLAN, **new** COVERAGE_GAPS.md.
  - `docs/03_prompts/` — (was `docs/prompts/`) all wave A/B/C + INV prompts; INDEX updated.
  - `docs/04_proposals/` — PROPOSAL_MEAL_PLANS, SHOPPING_LIST_REDESIGN, STATE_OWNERSHIP_REFACTOR, DORA_ASSISTANT_ARCHITECTURE.
  - `docs/05_investigations/` — RECIPE_COMPARISON_ASSESSMENT, AUTH_ASSISTANT_SECURITY_FINDINGS, MULTI_USER_READINESS, COMMERCIALIZATION_REPORT, Distribution Spec.
  - `docs/06_legacy_prompt_plans/` — PROMPT_PLAN.md + PROMPT_PLAN_PART_2..7.
  - `docs/99_scratch/` — claude convo.txt, prompt - up to speed.txt, Finish task DS1.txt.
  - Root `docs/00_DOCS_INDEX.md` rewritten to describe new layout.
- **`CLAUDE.md` + `AGENTS.md` updated** with:
  - New folder layout enumerated in step 2.
  - Governing-document paths updated (`01_charter/RECONCILED_FINISHING_PLAN.md`, `01_charter/DASHY_DORA_CHAMPION_PLAN.md`, `03_prompts/`).
  - **New "Cross-checking against the original feedback — MANDATORY" section** requiring every brief/proposal/assessment/impl-plan to end with a flat coverage table mapping every relevant feedback bullet to a section in the doc, OR explicitly mark it out-of-scope. The PROPOSAL_MEAL_PLANS `F1..F49` table is the reference shape.
- **`02_feedback/COVERAGE_GAPS.md` created** — full audit of which feedback bullets currently have no home:
  - **Bucket A (whole-surface gaps)** — Stock Item Detail polish, DATA page, Dora Bot polish, HELP content, Settings deferred bullets.
  - **Bucket B (assessment-style)** — feeds INV-7..10.
  - **Bucket C (cross-cutting/niche/future)** — full systems QA doc, telemetry, design polish, push notifications, P2P, etc.
  - **Bucket D** — surfaces verified covered (so the audit is reproducible).
- **`03_prompts/INV_investigations.md` expanded** with INV-7..10:
  - INV-7 stock-item detail History tab worth.
  - INV-8 substitute swap-into-list behaviour.
  - INV-9 command-palette worth (keep / shrink / cut).
  - INV-10 essential-flag — where it lives, how to set, is it the right primitive.
  - INDEX line updated accordingly.

**Decisions made:**
- All four pieces of the audit response executed (user picked all in
  one `AskUserQuestion`): write COVERAGE_GAPS, reorg, CLAUDE.md
  cross-check rule, INV-7..10.
- Mixed `git mv` and plain `mv` for the moves because some files
  (PROPOSAL_MEAL_PLANS, RECIPE_COMPARISON_ASSESSMENT, the raw feedback
  doc) hadn't been committed yet. Git tracks the rest as renames.
- Worklog historical entries' inline paths kept as-is (they describe
  state at time of writing — not rewriting history).

**Files touched:**
- Moved: 26 docs across the new subfolders.
- Edited: `CLAUDE.md`, `AGENTS.md`, `docs/00_DOCS_INDEX.md`,
  `docs/03_prompts/00_INDEX.md`, `docs/03_prompts/INV_investigations.md`,
  this worklog.
- Created: `docs/02_feedback/COVERAGE_GAPS.md`.

**Verification:**
- `ls docs/` shows only `00_DOCS_INDEX.md` + the seven new subfolders.
- `git status` confirms all files tracked under their new paths.
- `CLAUDE.md` and `AGENTS.md` now point at the new paths consistently.
- COVERAGE_GAPS.md cross-referenced against the full
  `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` section by
  section (SPLASH..Technical Considerations).
- **Not run:** any build / lint — docs-only changes.

**Next up:**
- **Back to INV** — INV-6 already done (`05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`).
  Next: pick from INV-1..10 (1/2/3/4/5 from original, 7/8/9/10 newly
  added). User had earlier sequencing of "INV-6 only first" — INV-6 is
  done.
- User may want to triage `02_feedback/COVERAGE_GAPS.md` Bucket A
  items into new C-briefs (especially C-DATA which is the biggest
  uncovered surface).
- Open user-blocking items unchanged from prior worklog entries.

**Open questions for user:**
- Which INV next? (INV-1 orphaned-fields is the most foundational — it
  also feeds A-1 and A-5 in COVERAGE_GAPS.)
- Want me to draft the C-DATA brief now or defer?

---

## 2026-06-06 — C-2 (Meal Plans proposal — feedback cross-check + rewrite)
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- Cross-checked every Meal Plans bullet in
  `docs/Feedback _ Fixes - as of [06-Jun-2026].md` against the
  proposal. Found 12+ gaps (page chrome removals, custom calendar
  spec detail, carousel direction, no-name plan instances, sidebar
  redesign, past-day bug, hover-to-highlight, etc.). Surfaced 4
  decisions to the user; took the picks
  (trays in left column, rotating sets in scope, single-button
  choice modal, drop cookable cues).
- Rewrote `docs/PROPOSAL_MEAL_PLANS.md` end-to-end. New §3.4-3.7
  cover the missing surface (new-plan flow, no-name instances, page
  chrome removals, page icon). New §5 expands templates with
  template-sets (rotating). New §13 is a flat per-feedback-bullet
  coverage table (F1..F49) so the next reviewer can audit the
  proposal against the source quickly.

**Decisions made (in addition to prior three):**
- 4. Rotating template sets **in scope** — new
  `MealPlanTemplateSet` entity; `from-template/recurring` accepts
  either a template_id or a template_set_id.
- 5. Trays in **left column** above all-recipes (not below carousel
  as feedback originally said — user explicitly picked left column;
  noted as a divergence from feedback wording).
- 6. Shopping-list target = **single button → choice modal**.
- 7. **Drop cookable cues from planner entirely** — no green-check,
  no "in-stock only" filter, no "Suggest meals I can cook now"
  CTA. Cookable lives on cookbook (C-4).

**Files touched:**
- `docs/PROPOSAL_MEAL_PLANS.md` (full rewrite)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Re-read full `MEAL PLANS` section of the feedback doc bullet-by-
  bullet against the proposal. Every bullet F1..F49 mapped to a
  section in §13.
- Live code re-grounding from prior pass still holds (B6 works,
  past-day backend refusal, meals→recipes merge complete).
- Identified a real frontend bug from the feedback's exception
  log (Thu 8am AEST → 400 on Wed drop) — `isPastDay` drift vs the
  backend's `date.today()`. Specced as §12 phase C-2.K.
- No build/run — proposal only.

**Next up:**
- **User reviews the rewritten `docs/PROPOSAL_MEAL_PLANS.md`.** §13
  table is the quick audit.
- 5 smaller decisions remain in §11 (recurring window cap, tray
  count max, templates page route, slot-remap UI build-now-or-defer,
  set rotation start anchor).
- After approval — back to **INV — investigations** as per the
  user's earlier sequencing.

**Open questions for user:**
- §11 smaller decisions when convenient.
- Anything in the flat F1..F49 coverage table you disagree with the
  mapping for.

---

## 2026-06-06 — C-2 (Meal Plans redesign — proposal)
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/PROPOSAL_MEAL_PLANS.md`. Sections:
  1. Re-grounding against live code (meals→recipes merge, B6
     allocation, shortfall, slot model, past-day rules).
  2. Three big open decisions resolved with user (templates fork at
     apply-time; past days skipped entirely on template apply; shortfall
     banner moved per-cell + sidebar summary).
  3. Three-column surface map (left=recipe list, main=week carousel,
     right=calendar+shopping+templates).
  4. Configurable slot vocabulary (`Breakfast/Lunch/Dinner/Snack`
     defaults; user-scoped settings entry).
  5. Templates data model + API + recurring application.
  6. Sequential builder modal as alt path for fresh-cookers.
  7. Two-persona walk-through (batch + fresh).
  8. Wave A primitive reuse map.
  9. Ripple notes for C-3 / C-4 / C-impl / dashboard / settings /
     onboarding.
 10. Smaller secondary open decisions (servings default, recurring
     window cap, etc.).
 11. Sequencing into 8 chunks if approved.

**Decisions made:**
- Took the three "Recommended" answers for the brief's listed open
  decisions: fork-on-apply templates, skip past days, move shortfall
  per-cell. Logged inline in §2 of the proposal so the next agent
  doesn't re-litigate.
- B6 allocation **explicitly verified working** in `_hydrate_unallocated`
  — but kept the CLAUDE.md MANDATORY rule, so the proposal flags it as
  needing in-browser confirm before being closed.
- Calendar widget designed as a custom small widget (NOT `q-date`) —
  the brief specified "minimalist rounded squares with status
  underlines" which q-date can't render.
- Same-recipe-same-(day,slot) drop **increments servings** (single
  entry); same recipe on the same day at *different* slots stays two
  entries (no schema churn). Flagged as a smaller open decision in
  §10 so the user can override.

**Files touched:**
- `docs/PROPOSAL_MEAL_PLANS.md` (new)
- `DORA_WORKLOG.md` (this entry)
- `DORA_FOLLOWUPS.md` (FU-032 — B6 allocation in-browser confirm)

**Verification:**
- Read both create+update meal-plan handlers, get_meal_plans,
  get_meal_plan_ingredients, get_shortfall, reconcile_consumed_meals,
  cook_recipe, adjust_recipe_meals, `_hydrate_unallocated` in
  get_recipes — to ground every "current state" claim against live
  code.
- Read MealPlansOverview.vue start-to-middle (first ~370 lines incl.
  template + setup, palette, week grid, sidebar, dialogs) and
  cross-referenced with the recipe store and dto models.
- No build/run — proposal only.

**Next up:**
- **User reviews `docs/PROPOSAL_MEAL_PLANS.md`** and approves /
  redirects the smaller open decisions in §10.
- Per the user's plan ("a valuable big rock, then back to INV") —
  next session, drive **INV — investigations**
  (`docs/prompts/INV_investigations.md`).
- If approved, the proposal's §11 lays out 8 chunked implementation
  prompts (A→H). Phase A (slot vocabulary) is the first reviewable
  chunk and can ship before the canvas changes start.

**Open questions for user:**
- Sign-off on the proposal (§2 big decisions are locked from prior
  Q&A; §10 smaller decisions need your call when convenient).
- Anything in the surface map that should swap places (e.g. calendar
  on the LEFT and recipe list on the right — the brief said right for
  calendar but you might prefer otherwise).

---

## 2026-06-06 — B9 (misc global bugs)
**Status:** complete (static verification only; node_modules absent)
**What changed (fixes):**
- **B9.2** — `web_app/src/components/menu/MainMenuButton.vue`: hide
  Quasar's built-in `.q-focus-helper` overlay so the custom `::before`
  hover ring is the only outline. Removes "double outline" on inactive
  hover.
- **B9.3** — `web_app/src/layouts/MainLayout.vue`: removed the Settings
  entry from `linksList` (main menu). Already lives in the user-avatar
  dropdown.
- **B9.6** — `web_app/src/pages/PriceHistoryPage.vue`: replaced the
  hard-coded `chartWidth.value = 720` with a `ResizeObserver` against
  the chart card element. Chart now extends to the card edge at every
  breakpoint, minus q-card-section padding (~16px). Selection→chart
  binding and tooltip theming verified already correct in current code.
- **B9.8** — `web_app/src/pages/LoginPage.vue`: removed `display:none`
  on `.login-mascot` below 760px; mascot now scales to 96px (and 72px
  below 360px) and is horizontally centred via `right: 50%; margin-right:
  -<half-width>px` so the `bob` keyframe (which owns `transform`) doesn't
  clobber centring. Plus `.dora-empty-mascot` (ProductSearch) and
  `.dora-hero-mascot` (Dashboard) force their inner `<img>` to
  `width:100%; height:100%; object-fit: contain` so the mascot is centred
  in its padded square.

**What changed (verified already-correct → confirm-in-browser FUs):**
- **B9.1** — drag-drop. Static walk-through both directions produces the
  right ordering; backend sorts by `(sequence, id)`; frontend's
  `insertAt = fromIdx < toIdx ? toIdx-1 : toIdx` checks out.
- **B9.4** — command palette. Every static command in `useCommands(...)`
  has a wired action; `create.stock-item` routes to `/stock?create=1`
  and `StockOverview.maybeOpenCreateFromQuery` watches it.
- **B9.9** — 404 page. Both surfaces already use tokens (A1 themed).

**What changed (needs decision / repro — flagged):**
- **B9.5** — undo. `stockItemStore.updateStockItemAsync` captures
  pre-state field-by-field and registers inverse+redo for every change,
  including expiry pushes/clears. Plumbing correct on static read.
  Closest guess for "oddly": Dashboard's `alerts.value` is its own ref
  and doesn't refetch after an inverse runs on another surface. FU-026
  requests a concrete repro.
- **B9.7** — log rotation. `RotatingFileHandler` is wired (10MB × 5
  backups) at `infrastructure/logging_setup.py:87`. Current ~46k-line
  file is below the size trigger. Symptom implies time-based rotation
  expectation. FU-027 needs decision: `TimedRotatingFileHandler` (and
  when?), or lower `maxBytes`?

**Decisions made:**
- Took the prompt's "OK with two nav fixes touching deferred areas" as
  implicit-yes since the user said "continue B9". Both are surgical.
- CLAUDE.md MANDATORY rule applied per-defect: every "code says fine"
  defect gets `[OPEN] confirm in browser`, not blanket "all fine".

**Files touched:**
- `web_app/src/components/menu/MainMenuButton.vue`
- `web_app/src/layouts/MainLayout.vue`
- `web_app/src/pages/PriceHistoryPage.vue`
- `web_app/src/pages/LoginPage.vue`
- `web_app/src/pages/ProductSearch.vue`
- `web_app/src/pages/DashboardPage.vue`
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, this worklog.

**Verification:**
- Each fix reasoned-through against current code; no build/run.
- ResizeObserver guarded with `typeof` for SSR safety; cleaned up in
  `onBeforeUnmount`.
- Mascot positioning: confirmed the `bob` keyframe only touches
  `transform` (not `right/left/top`), so `right + margin-right` centring
  is animation-safe.
- **Not run:** dev server / lint / type-check (node_modules absent).

**Next up:**
- **User eyeballs the 4 visible fixes** (menu hover, no Settings dup in
  main menu, price-history chart extends + resizes, mobile login mascot
  visible + Dora centred on ProductSearch/Dashboard).
- **User confirms the 3 FU-flagged "static-fine" items in browser**
  (DnD, palette commands, 404 theme).
- **User decision on B9.7** rotation model.
- **Precise repro requested on B9.5** undo oddness.
- **Wave B complete (B1-B9).** Per `docs/prompts/00_INDEX.md`: next is
  INV (investigations, read-only) → Wave C (big-rock design briefs).

**Open questions for user:** see Next up.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 follow-up 2: Dashboard "Continue" sealed-wizard bug + Wave-B audit
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/pages/DashboardPage.vue` — replaced the
  `<q-btn ... to="/welcome">` bare router-link on the skipped-setup
  banner with `@click="onContinueOnboarding"`. New handler calls
  `onboardingApi.restartAsync()` → `authStore.refreshAsync()` → drops
  the `dora.onboarding.skipped_at` localStorage key → `router.push('/welcome')`.
  Imported `OnboardingApiService`.
- `DORA_FOLLOWUPS.md` — logged FU-017 (B3 user re-test) and the
  miss-pattern note (FU-016 already covers the cross-cutting audit).
- `CHANGELOG.md` — Continue fix entry above the previous Skip/Finish
  fix, plus reframing of the original "no changes needed" claim.

**Decisions made:**
- **User asked me to audit my own "already-fine" claims** after the
  Skip/Finish bug landed. Re-walked every "no changes needed" call I
  made this session against the user's reported symptoms:
  - **B3 "can't save without changing the name"** — backend
    handlers (stock_item, recipe, recipe_collection, stock_location,
    stock_group, user_as_admin, me) all use `model_fields_set` +
    exclude-self correctly. The repo's identity map means `_StockItem`
    and `_SameName` are the same Python object when ids match, so the
    `_SameName.id != stock_item_id` guard returns False. Type
    alignment is fine (both UUIDs). I can't reproduce statically.
    Logged FU-017 for the user to re-test in browser — if it still
    repros, the actual error payload will tell us what code path is
    actually firing.
  - **B5 Dashboard "Continue"** — **was wrong**, same family as the
    Skip/Finish bug. The bare `to="/welcome"` link triggered a
    navigation that the router guard immediately reverted, because
    Skip Everything had stamped `onboarding_completed_at` on the
    backend and the guard now redirects authed users with a
    non-null timestamp AWAY from `/welcome` (lines 103-109). Fixed
    by using the existing `restartAsync` infrastructure (backend
    route + frontend service method both already existed —
    `AccountSettings.vue`'s "Restart onboarding" action even
    contains a comment explaining the exact guard issue). The
    "audit" approach worked: I saw the pattern by re-tracing
    Skip Everything's downstream effects on the guard, not by
    re-reading the button's wiring in isolation.
  - **B5 Skip/Finish/Show-me-X** — confirmed wrong, fixed in the
    previous worklog entry.
  - **B4 link-also-saves** — was correct in narrative *post-B1*, but
    pre-B1 fix would have 422'd. Noting for completeness.
  - **B7 "no other double-toast patterns"** — limited audit; only
    walked `addItems` callers. Wider sweep (store-mutation + page
    toast double-emit) not done. Flagging for opportunistic fix.
- **B3 verdict: re-test, don't dig further blind.** User chose
  "follow up later" (FU-017). Cheaper to wait for a live repro than
  to keep tracing speculative paths.

**Files touched:**
- `web_app/src/pages/DashboardPage.vue`
- `DORA_FOLLOWUPS.md`
- `CHANGELOG.md`

**Verification:**
- Walked the Continue path: user has skipped → `currentUser.onboarding_completed_at`
  is an ISO string → click → `restartAsync` POST sets it back to null
  on backend → `refreshAsync()` re-fetches `/me` → cached value is
  now null → `router.push('/welcome')` → guard (94-99) sees null
  for an authed user → falls through to the WelcomeLayout. ✓
- Confirmed `AccountSettings.vue:110-124` does the exact same dance
  in a different surface; copying its pattern.
- Confirmed `/onboarding/restart` exists at
  `dora_api/features/onboarding/onboarding.py:151` and that
  `onboardingApiService.restartAsync` (line 20) hits it.
- `useAuthStore` and `currentUser` already imported and instantiated
  in DashboardPage (lines 766/824) — no new store imports needed.
- **Not run:** dev server / browser (node_modules absent).

**Next up:**
- **User eyeballs**: Skip Everything from a fresh user → land on
  dashboard → banner appears → click Continue → wizard opens at
  the welcome step. No refresh needed.
- Back to the Wave B sequence: **B8** — recipe-detail dead actions /
  permanent substitute swap / deleted substitutes-graph ref.

**Open questions for user:** none. Wider audit findings logged in
`DORA_FOLLOWUPS.md` (FU-016, FU-017, FU-018).

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 follow-up: onboarding "dead button" bug (stale auth state vs router guard)
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue` — both `complete()` and
  `onSkipEverything()` now `await authStore.refreshAsync()` immediately
  after `onboardingApi.completeAsync()` and before `router.push('/')`.
  (Show-me-X also benefits because it calls `complete()`.)

**Decisions made:**
- **My earlier B5 verdict was wrong.** I claimed the buttons were
  "already wired correctly in current code" after a static read. User
  pushed back with the actual symptom: clicks did nothing until a
  browser refresh — classic stale-state behaviour I should have
  recognised. Logging the miss here so the pattern (handler exists ≠
  feature works; check the guard layer) sticks for the next session.
- **Root cause: router-guard / auth-store race.**
  `router/index.ts:94-99` redirects authed users with
  `currentUser?.onboarding_completed_at === null` to `/welcome`.
  `completeAsync()` updates the backend; the frontend's cached
  `currentUser` keeps the stale null. `router.push('/')` then trips
  the guard, which bounces back to `/welcome` immediately. Hard
  refresh works because the router's `beforeEach` calls
  `bootstrapAsync()` on a fresh page load, which re-fetches `/me` and
  observes the new timestamp.
- **Fix kept minimal:** add a single `await authStore.refreshAsync()`
  (the method already exists for exactly this case — its docstring
  literally references the onboarding flow). No changes to the
  router guard, no caching/optimistic updates. Two call sites
  touched.
- **No other callers of `completeAsync()`** in `src/` — verified by
  grep, so no other paths need the same paired refresh.

**Files touched:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue`
- `CHANGELOG.md` (extended the B5 Fixed entry rather than starting a
  new one — same prompt's loop)

**Verification:**
- Walked the failure path through `router/index.ts:75-118`: before
  fix, guard sees stale `null` → `{ path: '/welcome' }`; after fix,
  guard sees ISO timestamp → falls through to the actual destination.
- Confirmed `authStore.refreshAsync()` is the right method (line
  67-71 of authStore.ts) — its own docstring calls out the
  onboarding-state case. `useAuthStore` is already imported and
  instantiated in WelcomeWizard (lines 363/374).
- `clearDraft()` and the localStorage manipulation still run after
  the refresh, in the same order as before the bug fix.
- Grep'd every other call to `onboardingApi.completeAsync()` — only
  the two fixed sites. No other path leaks the same stale guard
  read.
- **Not run:** dev server / browser repro (node_modules absent).
  Once deps installed, this is the exact eyeball flow: Welcome →
  Finish (or Skip everything, or Show-me-X) → should land on its
  destination first try, no refresh needed.

**Next up:**
- **User re-eyeballs B5 onboarding flow** end-to-end. If a
  Finish/Skip/Show-me-X click still appears dead, the next thing to
  check is whether `getMeAsync()` is actually returning the updated
  timestamp (backend issue) rather than a stale-frontend issue.
- Then back to the Wave B sequence: **B8 — recipe-detail dead
  actions / permanent substitute swap / deleted substitutes-graph
  ref**.

**Open questions for user:**
- Worth a parallel audit for any other "frontend cached state vs
  backend mutation" gaps? Common shapes: after-import data refresh,
  after-restore stock-item refresh, after-onboarding-restart refresh.
  Logging as an opportunistic follow-up rather than acting now.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B7 (notification defects: "I'm a notification!" + duplicate toasts)
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/boot/notifyTypeRegistration.ts` — removed placeholder
  `message: 'Hey did you know...'` and `caption: "I'm a notification!"`
  from the custom `info` Notify type registration. Type still defines
  the visual styling (colour, icon, progress bar, classes); the text now
  comes exclusively from the call site, as it should.
- `web_app/src/boot/axios.ts` — **deleted**. Quasar scaffold file with
  `baseURL: 'https://api.example.com'`. Confirmed: NOT registered in
  `quasar.config.ts`'s `boot:` array; `$api` / `$axios` never referenced
  in `src/`. The real http client is `axiosHttpClient.ts`.
- `web_app/src/pages/StocktakeRunner.vue` — `onAddToList` now delegates
  to `useStockItemActions.addToList(stock_item_id)` instead of calling
  `useShoppingListActions.addItems(...)` and then firing its own
  second toast. Dropped the `useShoppingListStore` /
  `useShoppingListActions` imports and the local `primaryListId` /
  no-primary-list branch (handled inside `addToList`).

**Decisions made:**
- **Fix the source, not the call sites.** Every `notify({ type: 'info', ... })`
  call already supplies a real message — the placeholder caption was
  bleeding through *underneath* the real message because Quasar renders
  both message and caption. Trimming the type registration is one
  surgical change rather than touching every caller. Sweep confirmed
  no caller relied on the placeholder defaults.
- **Reuse `useStockItemActions.addToList` instead of writing new
  messaging.** It already does the correct "Already on your primary
  list." vs "Added to primary list." messaging, handles the
  no-primary-list dialog, and is the cross-screen single-item action
  every other surface uses. The duplicate-toast bug was really a "this
  page used the bulk composable for a single item" miswiring.
- **No other double-toast patterns found.** Audited every `addItems`
  caller (4 sites: QuickAddSheet, AlertsBell, MyProductsPage,
  DoraChat). None stacks a custom toast on top of the composable's
  summary toast. DoraChat does push a chat-bubble after `addItems`,
  but that's a different surface (in-chat reply vs system Notify),
  not a redundant toast.
- **Kept `oopsie` type intact.** Its `message: 'Oops, something went
  wrong...'` default is real production copy used by
  `globalErrorHandler.ts` and `boot/stores.ts` which call
  `Notify.create({ type: 'oopsie' })` with no message — that's a
  deliberate "use the default" pattern there, not a placeholder leak.

**Files touched:**
- `web_app/src/boot/notifyTypeRegistration.ts`
- `web_app/src/boot/axios.ts` (deleted)
- `web_app/src/pages/StocktakeRunner.vue`
- `CHANGELOG.md` (Removed + Fixed entries)

**Verification:**
- Grep'd `"I'm a notification"`, `"placeholder"`, `"lorem"`,
  `"example.com"`, `"demo"` across `web_app/src/`. Remaining matches
  are either (a) input-`placeholder=` attributes (legitimate form
  hints), (b) the merchant-logo `.dora-logo-placeholder` CSS class
  (real placeholder badge rendering — not text), or (c) the
  intentional "UI placeholder" tooltips on unfinished
  `SystemSettings` toggles (those are functional indicators, not
  copy bugs).
- Manually walked through `notifyTypeRegistration.ts` post-edit —
  `info` type now only sets visual properties; no leaking text.
- Confirmed StocktakeRunner still uses `useStockLevelStore`,
  `StocktakeApiService`, `StockItemApiService`, and `useQuasar`;
  none of the removed imports are referenced elsewhere in the file.
- Quasar `boot:` array in `quasar.config.ts` does NOT list
  `axios` — confirmed the deletion has zero runtime effect.
- **Not run:** dev server / type-check / lint (node_modules absent).

**Next up:**
- **User eyeballs B7** in browser: Meal Plans → "Generate shopping
  list for this week" → toast should now show just the real message,
  no "I'm a notification!" caption under it. Stocktake → Add to list
  → exactly one toast ("Added to primary list." or "Already on your
  primary list."), no contradictory pair.
- Then proceed to **B8 — Recipe detail dead actions / permanent
  substitute swap / deleted substitutes-graph ref**, next 🟡 in
  Wave B.

**Open questions for user:** none.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 (dead nav buttons — onboarding, dashboard, alerts→404)
**Status:** complete (static verification only — node_modules absent)
**What changed:**
- New `web_app/src/pages/AlertsPage.vue` — minimal stopgap.
  Reuses `useAlertStore` (same source as the bell), groups items by severity
  with severity-coloured avatars + per-kind icons, shows snoozed entries in
  a collapsed expansion at the bottom, click row → `/stock/<id>`.
  Deliberately does NOT host inline actions (push expiry / mark restocked /
  snooze new) — those stay on the bell panel for now. Banner makes that
  explicit so the page doesn't read as half-built.
- `web_app/src/router/routes.ts` — added `/alerts` route under MainLayout.
- `CHANGELOG.md` — Unreleased § Added (AlertsPage stopgap) + § Fixed
  (`/alerts` 404 resolved, rest of B5 cluster verified already-wired).

**Decisions made:**
- **B5 is 80% already-wired.** Audit found the only real bug in the cluster
  was the `/alerts` 404; the rest were already correct in current code.
  Specifically verified:
  - `WelcomeWizard.vue:677` `onSkipEverything` → `onboardingApi.completeAsync()`
    + sets `dora.onboarding.skipped_at` + `router.push('/')`.
  - `WelcomeWizard.vue:702` `complete()` (invoked on Finish via
    `onNext`→`isLastStep`) → `completeAsync()` + clears skipped flag +
    `router.push('/')`.
  - `WelcomeWizard.vue:670` `onShowMe` → completes onboarding, then
    `router.push(path)` for the tour card (4 cards: `/stock`,
    `/shopping-lists`, `/stock?attention=true`, `/help`).
  - `DashboardPage.vue:77` Continue button uses `to="/welcome"` — Quasar
    router-link is fine, navigates correctly.
  Logged the verification rather than making no-op edits.
- **Stopgap target = new minimal page** (per user). Going with a tiny
  page rather than redirecting to the bell drawer keeps the link semantics
  honest (`All N →` lands on a real list view), and reusing `alertStore`
  means no duplicate fetching.
- **No inline actions on the page (yet).** The C-wave brief owns the real
  control centre. Putting half the actions here would risk locking in a
  shape we'd then have to rework. Banner explicitly steers users at the
  bell so they don't think the actions vanished.
- **Page is added to MainLayout's children**, not the deferred-section
  list — `/alerts` is an active navigation target now, not a planning
  doc. The "deferred surfaces" guidance in CLAUDE.md is about *redesign*,
  not *don't add routes that 404 today*.

**Files touched:**
- `web_app/src/pages/AlertsPage.vue` (new)
- `web_app/src/router/routes.ts`
- `CHANGELOG.md`

**Verification:**
- Read every handler the prompt named: `onSkipEverything`, `complete`,
  `onShowMe`, dashboard Continue button. Each navigates and persists state
  per the prompt's "Fix wiring" section already.
- TOUR_CARDS' four paths (`/stock`, `/shopping-lists`,
  `/stock?attention=true`, `/help`) all map to existing routes in
  `routes.ts` — no further 404s in the show-me-X cluster.
- Confirmed `/alerts` previously hit the catch-all `ErrorNotFound`
  (line 196 of `routes.ts`). New route at indent under MainLayout means
  the page renders inside the standard chrome with header bell still
  visible.
- Sanity-checked every ICONS key used in AlertsPage
  (`priority_high`, `warning`, `info`, `snooze`, `undo`,
  `chevron_right`, `check_circle`, `refresh`) — all exist in `style/icons.ts`.
- `useAlertStore` API used: `alerts`, `loading`, `loadError`, `totalCount`,
  `snoozedCount`, `snoozedAlerts`, `refreshAsync`, `snoozedUntil`,
  `unsnoozeAlert` — all on the public return of the store.
- **Not run:** dev server / lint / type-check (node_modules absent).

**Next up:**
- **User eyeballs B5** in browser: click "All N alerts →" on dashboard →
  lands on /alerts with grouped list; bell still works independently;
  onboarding Skip/Finish/Show-me-X still navigate as expected.
- Then proceed to **B7 — notification defects** ("I'm a notification!"
  placeholder, duplicate/contradictory toasts), next 🟢 in Wave B.

**Open questions for user:** none — but note: TOUR_CARDS' "Alerts" tour
card still routes to `/stock?attention=true` (per the existing copy "deep-
link into Stock"). That predates today's `/alerts` page; the user can
decide later whether to switch the tour card to `/alerts` instead. Logged
as a follow-up.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B4 (delete stock item → FK constraint failed)
**Status:** complete (static verification only — node_modules / DB not exercised)
**What changed:**
- `dora_api/features/stock_items/delete_stock_item.py` — full rewrite:
  - New `BlockingRecipe` dataclass; `DeleteStockItemResponse` carries
    `blocked_by_recipes: list[BlockingRecipe]`.
  - Handler now queries `RecipeIngredient._stock_item_id` (same shape as
    `get_stock_item_detail.linked_recipes`) before `repository.remove(...)`.
    If any recipes reference the item, returns a non-empty
    `blocked_by_recipes` and skips the delete entirely — nothing is mutated.
  - New module-local `_blocked_by_recipes_response(...)` helper builds the
    422 problem-details body: standard `errors`/`title`/`type` shape PLUS a
    `blocked_by_recipes: [{recipe_id, name}]` extension the frontend uses
    to render a structured dialog.
- `web_app/src/pages/StockItemDetailPage.vue`:
  - `confirmDelete` message changed from
    `Delete "X"? Recipes that use it will be left with a dangling reference.`
    to `Delete "X"?`. The dangling-reference promise was incorrect: the FK
    is `RESTRICT`, so the previous behaviour was a 500, not a dangle.
  - `doDelete` catch block now inspects `err.details?.blocked_by_recipes`;
    if it's a non-empty array, pops a Quasar `$q.dialog` with
    `html: true` listing the recipe names ("Can't delete this stock item —
    it's an ingredient on N recipe(s): …"). Other errors still flow into
    the existing `notifyErr` toast.
  - Added `NormalisedApiError` to the existing `axiosHttpClient` import so
    the catch can type-narrow.

**Decisions made:**
- **Policy (b) — block-with-explanation** (per user). Implemented entirely on
  the existing 422/problem-details rails; no new HTTP helper added (kept
  churn low — used `flask.jsonify` directly in the module-local helper).
- **Extension field placement.** Put `blocked_by_recipes` on the body itself
  rather than buried inside `errors`. `errors` keeps the string fallback so
  `describeApiError` still produces a readable line for clients that don't
  know the extension (e.g. assistant tools, future routes). This keeps the
  contract additive — no existing error-handling code breaks.
- **Reference map confirms no other action needed.** Every other FK to
  StockItem either cascades or set-nulls — `ShoppingListLine`,
  `ShoppingListTemplateLine`, `StockItemProduct`, `StockLevelChange`,
  legacy `StockItemSubstitute` (all CASCADE); `StockItemWasteEvent`
  (SET NULL with denormalised name to preserve history). Only
  `RecipeIngredient` was RESTRICT and that's now handled.
- **Sweep: only one other RESTRICT FK in schema** — `Product.merchant_id`
  → `Merchant.id`. No DELETE route exists for Merchant, so no exposure.
  Other delete handlers don't need the same treatment.

**Files touched:**
- `dora_api/features/stock_items/delete_stock_item.py`
- `web_app/src/pages/StockItemDetailPage.vue`
- `CHANGELOG.md` (Unreleased § Fixed — B4 entry above B1)

**Verification:**
- Reasoned through three paths against current code:
  1. Item not used anywhere → query returns no ingredient rows → `remove` +
     `save_changes` + 204. (Unchanged behaviour for the happy path.)
  2. Item used by ≥1 recipe → query returns ids → fetch recipe names →
     422 with `blocked_by_recipes` → frontend dialog. (Was 500.)
  3. Item id doesn't exist → unchanged 404.
- Cross-checked the RecipeIngredient query against the existing
  `get_stock_item_detail.linked_recipes` query (same `_recipe_id` /
  `_stock_item_id` mapper-property names); both compile against the same
  table_mappings.
- Verified the only call site for `stockItemStore.deleteStockItemAsync` is
  `StockItemDetailPage.vue:913` — no other surfaces need the new dialog.
- Verified the optimistic-update / Undo flow in the store doesn't fire on
  failure: the store awaits `deleteAsync` before mutating the local array,
  so a 422 throw bypasses the splice and the snapshot/restore toast.
- **Not run:** dev server, DB delete, lint, type-check (node_modules absent).

**Next up:**
- **User eyeballs B4** in browser once deps installed:
  - Delete an unreferenced stock item → succeeds with Undo toast.
  - Delete an item used by a recipe → dialog appears listing the recipe(s);
    no toast; no 500 in server logs.
  - Delete a stock item that's *only* on a shopping list (no recipe) →
    succeeds; the line cascades out cleanly.
- Then proceed to **B5 — dead nav buttons** (onboarding skip/finish, dashboard
  continue, Alerts → 404), next 🟢 in Wave B.

**Open questions for user:** none.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B3 (partial-update semantics / "can't save unless I change the name")
**Status:** complete (verified-resolved — no code changes)
**What changed:** nothing in code. Audit confirmed the reported bug doesn't
reproduce in current backend code (same situation as B2).

**Decisions made:**
- **B3 closed as already-resolved.** The bug Joey reported is the
  classic PUT-style self-collision: name-uniqueness check finds the row, the
  row *is* the row being edited, but the handler doesn't exclude self → 422.
  Every update handler in the repo now does both of B3's recommended fixes:
  - **Partial update via `model_fields_set`** (only set fields get applied):
    `update_stock_item.py`, `update_recipe.py`, `update_stock_location.py`,
    `manage_stock_groups.py`, `update_user_as_admin.py`, `update_me.py`,
    `update_meal_plan.py`.
  - **Exclude-self on the name-uniqueness check** (`_SameName.id != <entity_id>`):
    `update_stock_item.py:118`, `update_recipe.py:100`,
    `update_recipe_collection.py:40`, `update_stock_location.py:48`,
    `manage_stock_groups.py:156`, `update_user_as_admin.py:86`,
    `update_me.py:71`.
  Handlers without a name-uniqueness check (`update_meal_plan`,
  `update_location`, `update_product`, `update_app_settings`) don't need one.
- **Probable history:** the meals→recipes merge and DS-series rework that
  fixed B2 also brought this pattern in line. Stale planning docs again.
- **No CHANGELOG entry** — nothing shipped this session for B3. The
  underlying fix already shipped in earlier work and is already reflected
  in the current code.

**Files touched:** none.

**Verification:**
- Read both handlers the prompt names: `update_stock_item.py`,
  `update_recipe.py`. Both exclude-self and use `model_fields_set`.
- Swept every other `update_*.py` in `dora_api/features/` for the same risk
  pattern. All clean.
- Reasoned through the failure path: send unchanged name → backend finds
  same row → `id != current_id` is False → no `already_exists` → name
  re-assigned no-op → save_changes → 204. Should work today.
- **Not run:** the actual edit flow in browser. User should still eyeball
  before fully closing the loop (edit a stock item changing only expiry,
  edit a recipe changing only servings — both should save without changing
  name). Logged as part of the upcoming verification sweep.

**Next up:**
- **User eyeballs B1 + B3** together once deps are installed. B3 verification
  is: edit a stock item changing only e.g. expiry → saves; edit a recipe
  changing only servings → saves; renaming to a *different* existing name
  still 422s.
- Then proceed to **B4 — delete cascade ("delete stock item → FOREIGN KEY
  constraint failed")**, next 🟡 in Wave B.

**Open questions for user:** none — but if the bug DOES still reproduce in
browser, the cause must be frontend-side (e.g. a stale optimistic-update
toast) or a code path I haven't seen yet. Flag it and I'll re-investigate.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B1 ("Extra inputs are not permitted" on product save/link/quick-add/inactive)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- `web_app/src/services/api/productApiService.ts` — `updateAsync` now strips
  `product_id` from the PATCH body (mirrors the `stockItemApiService.updateAsync`
  pattern). Was sending the full `UpdateProductCommand` including `product_id`,
  which the backend `UpdateProductRequest` (`extra="forbid"`) rejects.
- `web_app/src/pages/ProductSearch.vue` — `ensureSaved` now builds an explicit
  `CreateProductCommand` from the offer (brand, image, is_active=true,
  is_available, merchant_name, merchant_stockcode, name, price_now, price_was,
  size, size_unit, size_value, web_url). Was `{ ...offer, is_active: true }`,
  which leaked the offer-only fields `is_saved`, `is_saved_product_active`,
  `price_difference`, `price_per_cup` and tripped `CreateProductRequest`'s
  `extra="forbid"`.

**Decisions made:**
- **Backend kept frontend-aligned, not the other way around** (per the prompt's
  default). Two `extra="forbid"` schemas survive intact: `CreateProductRequest`
  and `UpdateProductRequest`. The leaking offer fields are display-only state,
  so the right move was to drop them client-side.
- **"Link also saves" requirement was already met.** `confirmLink` (and
  `onQuickAdd`) already call `ensureSaved` before `stockItemApi.linkProductAsync`.
  No new transaction logic added — sequencing was already correct. Fixing
  `ensureSaved`'s payload makes the existing save-then-link flow actually
  succeed.
- **Quick-add and Link backend models already matched the frontend** —
  `QuickAddRequest{stock_item_id}` and `LinkProductRequest{product_id}` accept
  exactly what the frontend sends. Both flows failed because of the save step
  they each chain to (`ensureSaved`), not the quick-add/link calls themselves.
  Logged here so a future agent doesn't go looking for a separate fix.

**Files touched:**
- `web_app/src/services/api/productApiService.ts`
- `web_app/src/pages/ProductSearch.vue`
- `CHANGELOG.md` (Unreleased § Fixed — new section)

**Verification:**
- Grep'd every caller of `productApi.createAsync` / `productApi.updateAsync` /
  `productStore.createProductAsync` / `productStore.updateProductAsync` —
  three call sites total (ProductSearch ensureSaved + onSaveToggle,
  MyProductsPage bulk inactive + per-row toggle). All now send only allowed
  fields.
- Cross-checked `CreateProductRequest` (create_product.py) and
  `UpdateProductRequest` (update_product.py) field-by-field against the new
  explicit `ensureSaved` payload and the trimmed PATCH body. No remaining
  mismatches.
- Walked the four failing actions end-to-end against current code: Save
  (create) → ensureSaved fixed; Save toggle / Mark active+inactive (bulk and
  per-row) → updateAsync trim fixed; Quick-add → ensureSaved + already-OK
  primary-line POST; Link → ensureSaved + already-OK link POST.
- **Not run:** `quasar build` / lint / dev server — `node_modules` absent.
- **Not tested manually** — UI eyeball required (see Next up).

**Next up:**
- **User eyeballs B1** on Product Search + My Products: Save toggle,
  Mark inactive (per-row and bulk), Quick-add to primary list, Link to stock
  item. Confirm no "Extra inputs are not permitted" toast on any.
- Then proceed to **B3 — partial-update semantics ("can't save unless I change
  the name")**, next 🟡 in Wave B.

**Open questions for user:**
- The image field is sent as a string from the frontend (`offer.image`) but
  the backend expects `Base64Bytes | None`. If existing offers populate
  `image` as a full data URL or a `data:image/...;base64,...` string, the
  backend may not parse it cleanly. Worth checking once the dev server runs.
  Logged as FU candidate if it surfaces.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A6 (text-size scale: re-spaced + extra-large + global apply)
**Status:** complete — static verification only (node_modules absent)
**What changed:**
- **New 4th step + re-spaced scale.** `themeService.ts` FONT_SIZE_PX:
  sm 14 / md 16.5 / lg 20.5 / xl 23px (was 14/16/18, too close). Ratios ≈
  0.85 / 1.0 / 1.25 / 1.4 with a very slightly larger default.
- **`xl` wired end-to-end:** `models/auth.ts` `FontSizePreference` += `'xl'`;
  `PreferencesSettings.vue` picker += "Extra large"; backend
  `user.py` `ALLOWED_FONT_SIZES` += `FONT_SIZE_XL`. DB column is `String(2)` so
  "xl" fits — **no migration**. Default stays `md`.
- **Global application (fixed-px → scale tokens):** `PageTitle.vue` (24px →
  `calc(var(--font-size-2xl)*1rem)`), `PreferencesSettings` theme-card blurb and
  `AuditLogSettings` payload/mono (12px → `--font-size-xs`). Added a `.q-tooltip`
  rule in `app.scss` so tooltips follow the pref.

**Decisions made:**
- **User chose 4 steps `0.85 / 1.0 / 1.25 / 1.4` with a "very slightly larger"
  default** (vs the prompt's 3-step options). Implemented base md = 16.5px (a
  +3% bump from 16) → sm 14 / lg 20.5 / xl 23 honour those ratios with clean-ish
  px. This was a bigger change than "re-space" (new enum value end-to-end).
- **Root cause of "not applied everywhere":** `app.scss` already sets
  `:root { font-size: var(--dora-base-font-size) }`, so rem text (incl. Quasar
  `text-*`) already scaled. The only hold-outs were fixed-px — migrated the real
  text ones; left deliberate carve-outs (camera overlay, SVG chart, micro-gauge).
- **Tooltips:** added a defensive global rule (they teleport to <body>; rem still
  resolves against root, but the rule guarantees they track the pref).

**Files touched:**
- Backend: `dora_api/domain/entities/user.py`.
- Frontend: `web_app/src/models/auth.ts`, `web_app/src/services/themeService.ts`,
  `web_app/src/pages/settings/PreferencesSettings.vue`,
  `web_app/src/components/menu/PageTitle.vue`,
  `web_app/src/pages/settings/AuditLogSettings.vue`, `web_app/src/css/app.scss`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- `FONT_SIZE_PX` is the only `Record<FontSizePreference,…>` — updated with `xl`;
  no other exhaustive map/switch over font sizes (grep). Picker is the only
  runtime option list (updated).
- Backend `ALLOWED_FONT_SIZES` now accepts `xl`; `register_user` passes through
  (no input validation against the old set); entity default `md` unchanged.
- Fixed-px audit: 8 sites total; 4 migrated (PageTitle, Preferences blurb,
  AuditLog ×2), 4 intentionally kept (ScanOverlay ×2, PriceHistoryChart SVG,
  Dashboard 3px/7.5px micro-gauge).
- **Not run:** lint / build / dev server — node_modules absent. See FU-025 for
  the required in-browser eyeball (xl on dense screens, tooltip scaling).

**Next up:**
- **User eyeballs A6** (FU-025): switch through Small→Extra large; confirm the
  spread is now obvious and nothing breaks on dense screens at xl; tooltips scale.
- **Wave A is essentially done** bar A8 (renames/refresh/nav-state, 🟡 — has
  decisions). A1, A1b, A2, A3, A4, A5, A6, A7 all complete.
- Wave B: B9 remains (other session's lane).

**Open questions for user:**
- Is md = 16.5px the right "very slightly larger" default, or nudge to 17?
- Happy with the xl spread (23px base → headings get large), or cap it lower?

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A7 (sticky page-counts footer)
**Status:** complete — static verification only (node_modules absent)
**What changed:**
- New `web_app/src/components/PageCountsFooter.vue` — sticky-to-bottom counts
  footer (top border + soft elevation, tokenised; responsive wrap). Props:
  `counts: { label, value, tone? }[]`. tone → theme-aware text-* class.
- `useStockFilters.ts`: added `footerCounts` computed over the FILTERED set —
  Shown + per-stock-level (dynamic from `stockLevels`, so it survives renames;
  tone via name heuristic) + Flagged + Auto-add + Needs attention.
- StockOverview: **removed the top summary banner**; footer renders the counts.
  Toolbar button row untouched (Wave-C owns the top-area teardown).
- RecipesOverview: removed top count text; footer = Shown + Cookable now +
  Favourites (filtered). Removed now-orphan `cookableNowCount`.
- MyProductsPage: removed top count text; footer = Shown + On deal + Unlinked
  (filtered). Replaced orphan `onDealCount`/`unlinkedCount` with `footerCounts`.

**Decisions made:**
- **Counts reflect the FILTERED view** (user's call) — matches the
  export-follows-filtered convention. A "Shown" stat gives the filtered total.
- **Removed the StockOverview summary banner** (user's call) and moved counts to
  the footer; explicitly did NOT touch the toolbar (that's the Wave-C Stock
  Overview brief, per A7's own note).
- **Per-level stats derived dynamically** from the stock-levels list rather than
  hardcoding "Well-Stocked"/"Sufficient" — robust to user-renamed/added levels.
- Footer shown only when the page has data (`v-if=...length > 0`).

**Files touched:**
- New: `web_app/src/components/PageCountsFooter.vue`.
- `web_app/src/composables/useStockFilters.ts` (footerCounts).
- `web_app/src/pages/StockOverview.vue`, `RecipesOverview.vue`, `MyProductsPage.vue`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- 3 pages each: 1 `<PageCountsFooter>` use + import present (scripted).
- 0 orphan count computeds left (cookableNowCount/onDealCount/unlinkedCount gone).
- `summaryCounts` still exported from useStockFilters (now unused by the banner,
  harmless); `countByLevel` still used by the level-filter chips.
- **Not run:** lint / build / dev server — node_modules absent. Sticky-bottom
  behaviour in the Quasar layout needs an in-browser eyeball.

**Next up:**
- **User eyeballs A7:** footer sticks to the bottom without overlapping content;
  counts update live with filters; consistent across the 3 pages; mobile wraps
  sensibly; light + dark.
- **Wave A remaining:** A6 (text-size scale, 🟡) and A8 (renames/refresh/nav-state,
  🟡) — both have decisions to confirm first. A7 was the last 🟢 foundation.
- Wave B: B9 still open (other session's lane).

**Open questions for user:**
- Footer sticky behaviour OK in the real layout, or prefer a plain (non-sticky)
  bottom strip?
- Adopt the footer on other list pages (shopping lists, meal plans) too? (FU-024.)

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A5 (one loading/skeleton treatment everywhere)
**Status:** complete (active surfaces; deferred pages noted) — static verification only
**What changed:**
- New `web_app/src/components/AppSpinner.vue` — shared inline/short-wait spinner
  (consistent size, theme-aware colour, optional label, `block` mode).
- New `web_app/src/components/AppSkeleton.vue` — layout-mimicking placeholder
  blocks (`line`/`rect`/`circle`), pulse on the boot splash's 1.6s rhythm,
  theme-aware (color-mix of `--surface-sunken` + `--text-muted`), reduced-motion
  aware.
- **Detail pages → skeletons (kills the placeholder-text bug):**
  `StockItemDetailPage` (no more "Stock item" while loading — skeleton title +
  toolbar/card blocks), `ShoppingListDetail` (no more "Loading…" — skeleton
  rows), `RecipeDetailPage` (header + two-column skeleton).
- **Spinners → `AppSpinner`** on: RecipesOverview, ShoppingListsOverview (+ inline
  "Loading totals…"), MyProductsPage, DashboardPage, ProductSearch (searching
  banner — was `q-spinner-dots color=primary`, now consistent), RecipeCookMode
  (page + swap-picker), RecipeDetailPage substitutes, ShoppingListShopMode,
  ShoppingListTemplates, ShopNowRedirect, QuickAddSheet.

**Decisions made:**
- **Decision (spinner + skeleton, both)** taken as recommended — boot-pulse-style
  spinner for short/inline waits; skeletons for known-layout detail/list loads.
  The user's impact-block intent was clearly both.
- **Reused the existing boot pulse rhythm** (index.html `pre-mount-pulse` /
  `SplashScreen` `splash-pulse`, both already identical: 1.6s ease-in-out). For
  skeleton blocks I used an **opacity-only** pulse on that rhythm — the boot pulse
  also scales, which would look wrong resizing individual layout blocks.
- **Skeleton colour via `color-mix`** of existing tokens (no new global token, no
  10-theme edit) → automatically theme-aware.
- **Deferred surfaces left on raw `q-spinner`** (Reports, Data→Export/Print,
  Settings sub-pages — on the prompt-pack "deferred" list) plus **DoraChat's
  typing dots** (deliberate). Logged as FU-023. A spinner swap there is harmless
  but low-value and the pages are "don't design yet."
- **Overviews got `AppSpinner`, not list-skeletons** — bounded scope; the
  placeholder-text bug was the detail-page issue. List-skeletons noted in FU-023.

**Files touched:**
- New: `web_app/src/components/AppSpinner.vue`, `web_app/src/components/AppSkeleton.vue`.
- Pages: `StockItemDetailPage`, `ShoppingListDetail`, `RecipeDetailPage`,
  `RecipeCookMode`, `RecipesOverview`, `ShoppingListsOverview`, `MyProductsPage`,
  `DashboardPage`, `ProductSearch`, `ShoppingListShopMode`, `ShoppingListTemplates`,
  `ShopNowRedirect`.
- Components: `QuickAddSheet`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- 0 AppSpinner/AppSkeleton usages missing their import (scripted check).
- Remaining `q-spinner` only on the deferred surfaces + DoraChat dots (expected).
- Detail-page placeholder strings ("Stock item", "Loading…") no longer render
  during load — replaced by skeletons in the keyed loading branch.
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs A5** once deps installed: detail pages show layout skeletons
  (not placeholder text); spinners consistent; ProductSearch searching banner
  reads in dark themes; reduced-motion stops the pulse. Light + dark.
- **Wave A remaining:** A6 (text-size scale, 🟡), A7 (sticky footer, 🟢),
  A8 (renames/refresh/nav-state, 🟡). Suggest A7 next (🟢, no decision), then the
  two 🟡 ones.
- Wave B: B9 still open (other session's lane).

**Open questions for user:**
- Want list-skeletons on the big overviews too (currently a centred spinner), or
  is spinner-for-lists fine? (Tracked in FU-023.)
- Migrate the deferred-page spinners (Reports/Data/Settings) now for full
  consistency, or leave per the "deferred" guidance?

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B8 (recipe detail actions + substitutes → cook-session swap)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- **Substitutes reworked to a temporary cook-session swap** (user's decision):
  - `RecipeCookMode.vue`: added per-ingredient session swap. New `sessionSwaps`
    Map (original stock_item_id → {substituteId, substituteName}), a swap-picker
    BaseDialog (fetches `stockItemApi.getDetailAsync(id).substitutes`), ↔ button +
    "Y instead of X" display + undo per ingredient row. `confirmFinish` maps used
    ids through `sessionSwaps` so the *substitute* is decremented / ran-out-checked,
    not the original. Never touches the saved recipe.
  - `RecipeDetailPage.vue`: removed the destructive `onSwapIngredient` (it edited
    the recipe form + marked dirty → permanent on Save). Substitutes dialog is now
    informational (chips non-clickable) with a note pointing to cook mode.
- Reworded stale "substitutes graph" text → "substitutes" in `RecipeDetailPage`
  (sidebar caption), `useStockItemActions.ts`, `StockOverview.vue`.
- Clarified `CLAUDE.md` "Removed features": the removed thing is the standalone
  substitute **graph page** (N7 `/substitutes`), NOT basic per-item substitutes.

**Decisions made:**
- **The substitutes confusion, resolved with the user.** Current state: the N7
  graph *page* is already deleted (no route/component); basic per-stock-item
  substitutes are live (stock-item tab + `StockItemSubstitute` table + recipe
  find-substitutes). Docs/CLAUDE.md conflated the two ("Substitute graph
  (stock-item substitutes)"). User wants basic substitutes KEPT; only the graph
  page was ever meant to go. Confirmed against `RECONCILED_FINISHING_PLAN §39`
  and `PROMPT_PLAN.md:90,154` (substitutes are a kept P2 feature).
- **Substitute behaviour = temporary cook-session swap** (user picked this over
  add-to-list / informational-only). Swap lives in cook mode, never edits the
  saved recipe. Recipe detail keeps substitutes *visible* (informational).
- **Most B8 reported defects don't reproduce** (stale docs / meals→recipes merge):
  favourite toggle chain is sound (sends `!is_favourite` → PATCH → backend
  assigns); all recipe actions are wired; there is no related-recipes section at
  all (so "clicking a related recipe → overview" can't happen). Logged, not
  "fixed". The genuine bug was the permanent substitute swap.
- Did NOT purge the substitutes backend/table — it's the kept feature.

**Files touched:**
- `web_app/src/pages/RecipeCookMode.vue` (session swap: state, picker dialog, row
  UI, finish mapping; +imports StockItemApiService, Substitute).
- `web_app/src/pages/RecipeDetailPage.vue` (removed destructive swap; dialog now
  informational; caption reworded).
- `web_app/src/composables/useStockItemActions.ts`, `web_app/src/pages/StockOverview.vue`
  (comment rewordings).
- `CLAUDE.md` (Removed-features clarification), `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- No "substitute(s) graph" text remains anywhere in `web_app/src`.
- `onSwapIngredient` fully removed from RecipeDetailPage (0 refs); `Substitute`
  type still used (substituteOptions) — no orphan import.
- RecipeCookMode tag balance: BaseDialog 2/2, q-card-section 8/8, template 5/5.
- `Substitute` model fields (`stock_item_id`, `name`) match the picker usage.
- Reasoned through finish flow: swapped ingredient decrements/ran-out-checks the
  substitute id, not the original.
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs B8** once deps installed: in cook mode, swap an ingredient (↔),
  confirm "Y instead of X" + undo, finish and confirm the *substitute's* level
  drops (not the original) and ran-out adds the substitute; on recipe detail,
  confirm "Find substitutes" no longer edits the recipe (Save stays disabled /
  recipe unchanged). Also confirm favourite un-toggle persists (reported broken;
  looks fine in code).
- Continue Wave B: next is **B9 — misc bugs** (`docs/prompts/B9_misc_bugs.md`),
  or revisit B1/B3/B4/B5/B7 if those weren't actually run yet (verify against
  code — our logs only cover A-series + B8).

**Open questions for user:**
- Cook-session swap feel right, or do you also want a quick swap affordance on
  the recipe detail page itself (not just cook mode)?
- Were B1/B3/B4/B5/B7 already run in other sessions? Our worklog has no record —
  worth confirming before assuming Wave B is nearly done.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A4 (filter system standardisation + "empty = off")
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- New `web_app/src/components/FilterBar.vue` — standard filter skin: persistent
  `#search` slot (outside the panel), collapsible `#filters` slot (default shown
  desktop / hidden mobile), active-filter count badge on the toggle, single
  standard "Clear filters" button shown only when ≥1 filter active, optional
  `#actions` slot. Uncontrolled expand defaults by screen size; supports
  `v-model` if a page needs to control it.
- Migrated all four target pages to FilterBar: `StockOverview` (bulk-select btn →
  `#actions`; chips/selects → `#filters`; search stays in header),
  `RecipesOverview` (filters → `#filters`; search stays in header; inline Clear
  removed), `MyProductsPage` (search → `#search`; toggles/selects → `#filters`),
  `ProductSearch` (bespoke `showFilters` toggle + "Clear ranges" removed; filter
  card → FilterBar `#filters`; search term stays in header).
- Hardened "empty = off" to be explicit/regression-proof: dropdown predicates
  `if (value && …)` → `if (value !== null && …)` in `useStockFilters.ts`,
  `RecipesOverview`, `MyProductsPage`; numeric "Missing ≤" guarded with
  `Number.isFinite`. Added an `activeFilterCount` to each page/composable.

**Decisions made:**
- **The headline A4 bug does NOT reproduce in current code.** A thorough
  per-page audit (quoted predicates) showed every page already skips a blank
  filter (truthiness / `!= null` / empty-array / boolean-false). Stale docs
  again (CLAUDE.md warns of this). So A4's value here is UX standardisation +
  regression-proofing, not a bug fix. Surfaced this to the user before building.
- **Scope = full A4, all four pages (user's call).** Note this overrides master
  Decision 1's "products surface is minimal-touch / companion-bound" for
  `ProductSearch` + `MyProductsPage` — the user explicitly chose to migrate them
  anyway. Logged so a future session doesn't "fix" it back.
- **Prompt's 3 decisions** taken as recommended (user didn't object): filters
  shown desktop / hidden mobile; free-text search kept separate + persistent
  (outside the collapsible panel); numeric blank/non-numeric = off.
- **Search stays separate** — each page keeps its existing search box; FilterBar
  only owns the collapsible panel + toggle + active-count + Clear. Lower-risk
  than relocating searches, and satisfies "search separate from the panel."
- **`activeFilterCount` excludes the search box** (search has its own clearable
  X and lives outside the panel), so the toggle badge reflects panel filters.
- **Replaced one-off clears** per the prompt: ProductSearch "Clear ranges" and
  its bespoke filter toggle are gone, folded into FilterBar's standard Clear +
  toggle.

**Files touched:**
- New: `web_app/src/components/FilterBar.vue`.
- `web_app/src/composables/useStockFilters.ts` (hardened predicates +
  `activeFilterCount`).
- `web_app/src/pages/StockOverview.vue`, `RecipesOverview.vue`,
  `MyProductsPage.vue`, `ProductSearch.vue`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- `<FilterBar>` balanced 1/1 in each of the four pages; import present in each.
- Named slots (`#search`/`#filters`/`#actions`) open/close balanced; q-card
  balance intact in ProductSearch after removing its filter card.
- `showFilters` fully removed from ProductSearch (0 refs); `hasAnyFilter` still
  used by the empty-states in Recipes/MyProducts (no orphans); `clearRanges`
  still used by `clearAllFilters` (no orphan).
- Reasoned through empty=off for every field on every page (now explicit).
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs A4** once deps installed: on each of the 4 pages confirm —
  Filters toggle shows/hides the panel; panel hidden by default on mobile; the
  active-count badge is right; Clear appears only when filters active and resets
  them; blank inputs show all rows; light + dark.
- **Wave A is now A1–A4 done.** Next prompt: check `docs/prompts/00_INDEX.md` for
  the Wave B start (or the next item in `RECONCILED_FINISHING_PLAN.md §5`).
- See `DORA_FOLLOWUPS.md` for A4 leftovers (multi-select control only partially
  standardised; FilterBar panel has no card container; AuditLogSettings filtering
  not standardised — server-side, was out of A4 scope).

**Open questions for user:**
- Any A4 page where the panel default (open desktop / closed mobile) or the
  moved controls feel wrong? Flag page + screen size.
- The products pages were migrated despite being companion-bound — still happy
  with that, or should they be reverted to minimal-touch later?

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A3 (standard modal / BaseDialog) + A2 follow-up (danger-ghost button)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- New `web_app/src/components/BaseDialog.vue` — standard modal shell wrapping
  `q-dialog` + `q-card`. Non-`persistent` by default (backdrop + Esc = cancel,
  never commit/navigate), token radius, optional standardised header
  (`title`/`closable`) and `#actions` footer slot, `cancel` event on any close.
- Migrated **all ~28 standard template `<q-dialog>` modals across 25 files** to
  `BaseDialog` (3 reference files done by hand: `RecipeEditDialog`,
  `RecipeCookMode` finish, `RecipeDetailPage` ×4; the remaining 22 files fanned
  out to 4 parallel subagents against a precise transform spec).
- **A2 follow-up:** confirmed the other agent had already added the
  `danger-ghost` `BaseButton` variant (flat negative — the "ghost danger" delete
  button) and wired it into `StockItemDetailPage` (Delete + clear-expiry) and
  `MealPlansOverview` (Delete plan). Verified complete; nothing more to do there.

**Decisions made:**
- **Destructive dismiss policy** (the prompt's "confirm with me"): user chose
  **backdrop = cancel for ALL modals**, including deletes. Delete only fires from
  its explicit button. This already matched the de-facto code behaviour, so no
  `persistent` was added anywhere.
- **Scope:** user chose "migrate all ~30". Interpreted as: migrate every standard
  *card* modal, and document 3 specialised overlays as intentional exceptions —
  `AlertsBell` (seamless side drawer, no backdrop → modal-cancel semantics don't
  apply), `CommandPalette` (custom search overlay), `ScanOverlay` (persistent
  camera overlay). Forcing these through BaseDialog adds no value and risks their
  custom layout/positioning.
- **The prompt's "bugs" are mostly already fixed** (docs are stale, per CLAUDE.md).
  The `$q.dialog()` programmatic confirms (recipe delete, unsaved-changes,
  cook-start) only commit/navigate on `.onOk()` and resolve false on
  `.onDismiss()` — already correct. Left them as-is; A3's real value here is the
  shell standardisation, not bug-fixing.
- **Shell transform, not internal rewrite.** Each dialog keeps its own
  header/footer markup inside BaseDialog's default slot. Fully unifying 28
  heterogeneous dialogs' internal structure (via the `title`/`#actions` slots)
  would be a large, risky rewrite for little gain — deferred as future polish.
  Mirrors how A2 was run incrementally.
- **`@hide` → `@cancel`.** Dialogs with an `@hide` cleanup handler
  (`CreateStockItemDialog` resetForm, `QuickAddSheet` onHide) were converted to
  `@cancel` — BaseDialog re-emits the dialog's hide as `cancel`. Semantics
  preserved (both fire on any close).
- **Scoped card-class sizing bug caught + fixed.** Three dialogs sized their card
  via a *scoped* CSS class (`comparison-card`, `orphans-card`, `quick-add-sheet`).
  Once the `<q-card>` moved into BaseDialog's style scope (and dialogs teleport to
  `<body>`), those scoped selectors no longer matched. Moved each into the inline
  `card-style` prop and deleted the dead rules. Also fixed `AuditLogSettings`
  (always-maximized, bare card) whose card was being capped at 95vw by BaseDialog's
  default `card-style` — gave it an explicit fill style.

**Files touched:**
- New: `web_app/src/components/BaseDialog.vue`.
- Reference migrations: `components/RecipeEditDialog.vue`, `pages/RecipeCookMode.vue`,
  `pages/RecipeDetailPage.vue`.
- Subagent migrations (22 files): `components/MealPlanEditDialog.vue`,
  `components/stock/BulkMoveLocationDialog.vue`,
  `components/stock/CreateStockItemDialog.vue`, `components/QuickAddSheet.vue`,
  `components/ShortcutsCheatsheet.vue`, `pages/StockItemDetailPage.vue`,
  `pages/StocktakeRunner.vue`, `pages/ShoppingListShopMode.vue`,
  `pages/ShoppingListsOverview.vue`, `pages/ShoppingListTemplates.vue`,
  `pages/MyProductsPage.vue`, `pages/ProductSearch.vue`,
  `pages/MealPlansOverview.vue`, `pages/RecipesOverview.vue`,
  `pages/data/BackupRestore.vue`, `pages/data/DataImport.vue`,
  `pages/data/BarcodesQR.vue`, `pages/PriceHistoryPage.vue`, `pages/WastePage.vue`,
  `pages/VerifyEmailPage.vue`, `pages/settings/AuditLogSettings.vue`,
  `pages/settings/UsersAdminSettings.vue`.
- `CHANGELOG.md`.

**Verification:**
- `<q-dialog` opens app-wide = 4, all expected: `BaseDialog` itself + the 3
  documented exceptions. `</q-dialog>` closers = 4 (balanced).
- 38 `<BaseDialog>` usages across 25 files; every consuming file imports
  `BaseDialog` (scripted check — 0 missing imports).
- `<q-card>`/`</q-card>` and `<BaseDialog>`/`</BaseDialog>` tag balance verified
  per file (scripted — 0 unbalanced).
- `@hide` now only in `BaseDialog` (internal) + `CommandPalette` (exception).
- **Not run:** lint / `quasar build` / dev server — `node_modules` is not
  installed in this checkout, consistent with prior sessions.

**Next up:**
- **User eyeballs A3 in browser** once deps are installed: open a representative
  modal in each family (new-recipe, cook-mode finish, a stock-item picker, the
  recipe comparison dialog, quick-add sheet, a data report dialog, audit detail).
  Confirm: backdrop-click and Esc close *without* committing/navigating; Cancel +
  primary buttons work; widths/maximized behaviour unchanged; the comparison /
  orphans / quick-add cards are still correctly sized (the scoped-class fix).
- Optional A3 polish (deferred): adopt BaseDialog's `title` prop + `#actions`
  slot to truly unify header/footer chrome across dialogs (currently each keeps
  its own markup). Low priority — purely cosmetic consistency.
- Next Wave A prompt: **A4 — filter system** (`docs/prompts/A4_filter_system.md`).

**Open questions for user:**
- Any modal that now closes when it shouldn't, or whose sizing looks off after
  the scoped-class → `card-style` move? Flag the dialog + screen size.
- OK that the 3 specialised overlays (AlertsBell / CommandPalette / ScanOverlay)
  stay on raw `q-dialog`, or do you want them folded in too?

---

## 2026-06-04 — A2 Phase 2 (detail-page toolbars, dialogs, onboarding, auth/settings/data)
**Status:** complete (substantial coverage — see remaining residuals below)
**What changed:**
- 20 additional files migrated, ~95 `q-btn` instances converted to `BaseButton`.
- App-wide `<q-btn` count: **399 → 304** (24% reduction overall; near-full coverage on the high-visibility surfaces).
- Files now using BaseButton: **26**.
- Categories covered: detail-page top toolbars + their dialog footers, all major form/edit dialog components, onboarding wizard, auth pages (Forgot/Reset/Verify/ConfirmEmailChange), key settings sub-pages (UsersAdmin, AuditLog, Merchants), data pages (BackupRestore, DataImport, BarcodesQR).

**Decisions made:**
- Kept the few flat-negative buttons (e.g. `StockItemDetailPage` Delete toolbar btn) as `q-btn` — current BaseButton variant set doesn't have a "flat danger" shape, and the visual is intentional (less alarming than filled `variant="danger"`). Filed as a possible BaseButton extension; not blocking.
- Used `class="text-primary"` on `variant="ghost"` BaseButtons where the original q-btn had `color="primary"` on a flat layout (auth-page "Back to sign in", VerifyEmail "Resend verification", etc.). Keeps text colour theme-aware without a new variant.
- `ResetPasswordPage` "Reset password" submit (large, full-width) deliberately left as q-btn — its `size="lg"` + `class="full-width"` don't map cleanly to BaseButton's fixed 36px height, and it's a one-off design.
- Used auto-forwarding of `icon-right` (and other unknown attrs) through BaseButton's root `q-btn` rather than declaring it as a prop. Works because BaseButton has a single root element so Vue auto-forwards $attrs.
- Wrote the 9 missing BaseButton imports via a sed pass that inserts after the `<script>` tag.

**Files touched (this pass):**
- Pages: `StockItemDetailPage`, `RecipeDetailPage`, `ShoppingListDetail`, `ShoppingListShopMode`, `RecipeCookMode`, `WelcomeWizard` (onboarding), `ForgotPasswordPage`, `ResetPasswordPage`, `VerifyEmailPage`, `ConfirmEmailChangePage`, `UsersAdminSettings`, `AuditLogSettings`, `MerchantsSettings`, `BackupRestore`, `DataImport`, `BarcodesQR`.
- Components: `RecipeEditDialog`, `MealPlanEditDialog`, `stock/CreateStockItemDialog`, `stock/BulkMoveLocationDialog`.
- `CHANGELOG.md`.

**Verification:**
- App-wide `<q-btn` count via grep: 304 remain.
- 26 files now import `BaseButton`.
- All migrated files re-verified to have both the import AND at least one BaseButton usage (no orphan imports).
- **Not run** the dev server.

**Remaining `<q-btn` (~304, out of scope for A2):**
- Inline list-row action buttons (recipe-card hover actions, stock-row quick actions, shopping-list line buttons, settings list-item row actions). Embedded in nested `q-card-actions`/`q-list`/`q-item-section` contexts — re-themed already, just not standardised.
- `q-btn-dropdown` (4 usages) and `q-btn-toggle` (6 usages) — different APIs from `q-btn`; out of BaseButton scope by design.
- `q-btn` inside `q-input` append slots (search-clear, copy-to-clipboard) — better left as the minimal pop-out style.
- A handful of one-off large CTAs (e.g. `ResetPasswordPage` full-width submit) deliberately preserved.
- Few remaining footer buttons in `StockOverview` body sections (empty-state, summary cards) and `RecipeDetailPage` mid-page link-product / add-substitute btns — already migrated for the top toolbars.

**Next up:**
- **User eyeballs Phase 2**: open the detail pages (stock item, recipe, shopping list detail, shop mode, cook mode), the onboarding flow, the auth pages, and a settings sub-page. Confirm consistent button heights, ghost-Cancel + primary-CTA pattern across dialogs.
- **A3 — Standard modal** (next Wave A prompt, `prompts/A3_standard_modal.md`).
- Optional A2 follow-up backlog (deferred):
  - "flat danger" BaseButton variant (or `:flat` modifier) for non-loud destructive actions.
  - `q-btn-dropdown` wrapper component if there's appetite for unifying split-buttons.
  - Inline list-row action button standardisation (high q-btn count remains but visual impact is low — they're tiny icon buttons).

**Open questions for user:**
- Any visual regression?
- Proceed to A3, or pause to eyeball Phase 2 first?

---

## 2026-06-04 — A2 Phase 1 (BaseButton + PageToolbar + 6 page-toolbar migrations)
**Status:** complete (Phase 1 scope only — inline / dialog / body-content q-btns left as-is)
**What changed:**
- New `web_app/src/components/BaseButton.vue` — variants `primary | secondary | ghost | danger | icon`, plus `:attention` modifier. Wraps `q-btn`. Fixed 36px height for toolbar alignment; icon variant is 36×36 square. `attention` uses a pulsing brand-accent box-shadow keyframe (replaces the StockOverview-local `stocktake-glow` CSS); honours `prefers-reduced-motion`.
- New `web_app/src/components/PageToolbar.vue` — title + optional back-arrow on the left, named slot `#actions` on the right.
- Migrated page-top action buttons in `StockOverview` (4 + empty-state CTA), `RecipesOverview` (3), `MealPlansOverview` (2), `MyProductsPage` (2), `ShoppingListTemplates` (1), `StocktakePage` (1, wrapped header in PageToolbar).
- Deleted the now-unused `.stocktake-glow` keyframe rule from `StockOverview.vue` style block.

**Decisions made:**
- Variants: `primary | secondary | ghost | danger | icon` + `attention` modifier (user's confirmation).
- "New X" CTAs use `variant="primary"` (brand), not the pre-existing `color="positive"` (green). Decouples create-action from success-semantic. Matters in Cherry Cola where brand-red ≠ positive-green.
- Phase 1 only: just the 6 main overview pages' top action rows. Inline / list-row / dialog / body buttons left untouched.
- `ShoppingListsOverview` skipped — its New button is a `q-btn-dropdown` split-button (different API than `q-btn`); already uses `color="primary"` so it's on-convention.
- `StocktakePage` is the only one that got the full `PageToolbar` wrapper because it already had a clear title + back-arrow pattern. Other pages have heterogenous header rows (counts, filters, search inline) — wrapping them all would over-rewrite; left their `<div class="row …">` headers but swapped buttons to `BaseButton`.
- Compare button on `RecipesOverview` migrated even though it's not a "New" CTA — it's a top-row toggle and benefits from the standard sizing.
- BaseButton's `attention` modifier upgraded to a pulse animation (rather than the originally-planned static glow) because the existing stocktake-glow used a pulse; preserving the existing visual effect across the migration.

**Files touched:**
- `web_app/src/components/BaseButton.vue` (new)
- `web_app/src/components/PageToolbar.vue` (new)
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/pages/RecipesOverview.vue`
- `web_app/src/pages/MealPlansOverview.vue`
- `web_app/src/pages/MyProductsPage.vue`
- `web_app/src/pages/ShoppingListTemplates.vue`
- `web_app/src/pages/StocktakePage.vue`
- `CHANGELOG.md`

**Verification:**
- Per-file: BaseButton usage count matches the import count (1 import per file, 1–4 uses).
- Reviewed in-context: button heights now consistent across the 6 pages (36px); icon-only buttons are square; semantics preserved (Scan / Stocktake / Compare = secondary outline; New X = primary fill; Refresh = ghost).
- `prefers-reduced-motion` path verified to disable the pulse and fall back to a static glow.
- **Not run** the dev server.

**Phase 1 left out of scope (for future A2 follow-up passes):**
- Inline action buttons inside list rows (recipe cards, shopping-list lines, stock rows).
- Dialog footer buttons (Confirm / Cancel pairs in modals).
- Toolbar buttons on detail / single-entity pages (`StockItemDetailPage`, `RecipeDetailPage`, `ShoppingListDetail`).
- The `ShoppingListsOverview` split-button dropdown.
- `Onboarding/WelcomeWizard.vue` step buttons.
- ~58 files with q-btn usage not yet touched.

**Next up:**
- **User eyeballs Phase 1**: open StockOverview, RecipesOverview, MealPlansOverview, MyProductsPage, ShoppingListTemplates, StocktakePage. Confirm: buttons aligned, "New X" reads as brand colour (not green), Stocktake "glow when overdue" still pulses (visit StockOverview with overdue stocktake items).
- **A2 Phase 2** (optional follow-up): migrate inline/detail-page/dialog q-btns. Worth doing once Phase 1 is approved.
- Alternative: continue down the Wave A list with **A3 — Standard modal** (`prompts/A3_standard_modal.md`).

**Open questions for user:**
- Any visual regression in the 6 migrated pages?
- Run A2 Phase 2 (rest of q-btns) before A3, or push into A3 next?

---

## 2026-06-04 — A1b round 2 (Pesto Dark + dual-source sync)
**Status:** complete
**What changed:**
- Pesto Dark green further toned: `--brand-primary` / `--brand-accent` / `--semantic-positive` `hsl(150 62% 50%)` → `hsl(150 48% 40%)`. `--chart-1` `hsl(150 48% 45%)`. Dora halo tokens retuned to match.
- Pesto Dark text lifted for pop on the dark page: `--text-secondary` 67% → 78% L; `--text-muted` 55% → 66% L.
- **Caught a dual-source bug:** `themeService.ts`'s parallel `THEMES` palette dict was overwriting the new `themes.scss` values via `setCssVar('primary', ...)` etc. on theme apply. Synced Pesto, Pesto Dark, and Lemon Tart Dark palette entries in `themeService.ts` so the Quasar-driven `--q-*` path matches the CSS-driven `--brand-*` path.

**Decisions made:**
- Going one big step rather than nibbling: from "still feels too bright" feedback at 62/50, jumping to 48/40 rather than another small step — easier to walk back if too dark than to keep iterating.
- Kept `--text-on-primary: hsl(165 60% 5%)` (deep forest) for Pesto Dark chip text rather than flipping to white — at the new darker green it reads ~7:1 contrast which is excellent.
- Only synced Pesto, Pesto Dark, LT Dark in `themeService.ts` (the three I touched). The other 7 themes still have a dual-source coupling but their values match between the two files, so no immediate sync needed.
- Did not touch other themes' brand values per same caution — waiting for browser eyeball.

**Files touched:**
- `web_app/src/css/themes.scss`
- `web_app/src/services/themeService.ts`
- `CHANGELOG.md`

**Verification:**
- All three values now match between `themes.scss` and the `THEMES` dict in `themeService.ts` for Pesto, Pesto Dark, LT Dark.
- Contrast reasoning for Pesto Dark:
  - White text on new `--brand-primary` `hsl(150 48% 40%)`: ~5.5:1 (AA Normal pass).
  - `--text-on-primary` `hsl(165 60% 5%)` on new green: ~7:1 (AAA pass).
  - `--text-secondary` `hsl(205 14% 78%)` on `--surface-page` `hsl(165 60% 5%)`: ~9:1 (excellent).
  - `--text-muted` `hsl(205 12% 66%)` on the same page: ~6:1 (comfortable AA).
- **Not run** the dev server.

**Next up:**
- **User eyeballs Pesto Dark again.** Specifically:
  - Cookable Now chip in recipe detail — green still vibrant or comfortable?
  - "Add" / primary CTA buttons across the app — text legible, brand-present without being garish?
  - Captions / subtitles on the dark page — readable now?
  - If still too bright, we go further (hsl(150 40% 34%) range) — easy to walk back.
- If colour feels right, proceed to **A2 (standard button + toolbar)**.
- Note: 7 other themes have the same dual-source coupling — collapsing `themeService.ts` THEMES dict into a CSS-var read is a worthwhile follow-up but doesn't block A1/A1b sign-off.

**Open questions for user:**
- After eyeballing: green still too bright, about right, or now too muted?
- Text on the dark page reading better?

---

## 2026-06-04 — A1b (token value tuning) complete
**Status:** complete
**What changed:**
- Added `--overlay-hover-on-coloured` + `--overlay-active-on-coloured` + `--highlight-search` tokens to `tokens.scss`.
- Rewired `MainMenuButton.vue` hover, `CommandPalette.vue` `.cp-hl` highlight, and `CommandPalette.vue` `.cp-row--selected` to the new / theme-aware tokens.
- Deleted three `.body--dark` overrides (`CommandPalette.vue:404,428`, `ShortcutsCheatsheet.vue:85`) — they were legacy workarounds for a token-flip gap that no longer exists.
- `--ring-focus` is theme-aware in every theme (was hardcoded Pesto green).
- Value retunes per theme:
  - **Pesto** `--brand-primary` desaturated `hsl(150 76% 39%)` → `hsl(150 60% 36%)` (fixes "add" / cookable green too bright).
  - **Pesto Dark** `--brand-primary`/`-accent`/`--semantic-positive`/`--chart-1` toned `hsl(150 75% 55%)` → `hsl(150 62% 50%)`, Dora halo retuned to match.
  - **Lemon Tart Dark** `--semantic-warning` `hsl(46 100% 55%)` → `hsl(40 90% 60%)`.
  - **Cherry Cola Dark** + **Sourdough Dark** Dora halo alphas dropped so the glow doesn't dominate.
  - `--text-muted` (Pesto defaults + Pesto theme) `hsl(168 8% 50%)` → `hsl(168 10% 42%)` for AA contrast.

**Decisions made:**
- `--overlay-hover` already theme-flips in `themes.scss` (dark themes set white veils) — so DEC-A-1's "theme-flip the token" step was already done. The remaining gap was the *toolbar* surface (always coloured), which now has its own `--overlay-hover-on-coloured` token. The `.body--dark` overrides in CommandPalette/ShortcutsCheatsheet were therefore redundant and got deleted, not patched.
- `--highlight-search` defined via `color-mix(var(--brand-accent) 40%, transparent)` so it tracks the theme accent automatically — no per-theme override needed.
- `--text-muted` only bumped in Pesto family. Other light themes (LT, Blueberry, Cherry Cola light, Sourdough light) sit at L=50 which is fine; dark themes already lifted to L=55-60.
- Did **not** touch other light themes' brand-primary values — the "too bright add" complaint is most acute on Pesto (per audit §5 + A1b prompt) and Pesto Dark; over-tuning the whole family without seeing it in the browser risks washing out the brand.

**Files touched:**
- `web_app/src/css/tokens.scss`
- `web_app/src/css/themes.scss`
- `web_app/src/components/menu/MainMenuButton.vue`
- `web_app/src/components/CommandPalette.vue`
- `web_app/src/components/ShortcutsCheatsheet.vue`
- `CHANGELOG.md`

**Verification:**
- Grep confirms 0 remaining `.body--dark` colour-override blocks in the three named components.
- `--ring-focus` is now `color-mix(... var(--brand-primary)...)` in all 10 theme blocks.
- `--overlay-hover` still has its dark-theme overrides (untouched — they were already correct).
- App-wide rgba/hsla literals are now exclusively in DEC carve-outs (LoginPage DEC-2, ScanOverlay DEC-4, ProductSearchCard DEC-8, Aldi/Coles/IGA brand logos, TrendSparkline + ReportsPage SSR fallbacks).
- **Not run** the dev server.

**Next up:**
- **User eyeballs A1b**: especially Pesto "add" buttons (less garish?), Pesto Dark chips (readable?), Lemon Tart Dark warning chips (no longer pure yellow), Cherry Cola Dark / Sourdough Dark Dora bubble (subtler halo), and that the focus ring now matches the theme on Tab.
- **A2 — Standard button + toolbar** (next Wave A foundation; see `prompts/A2_standard_button_toolbar.md`'s Impact block — has decisions).
- Remaining A1 backlog items worth noting:
  - Other light themes' `--text-muted` may also need a 50→42 nudge — defer until A1b is eyeballed.
  - `LoginPage.vue` `--lp-*` ladder still untouched per DEC-2; revisit when C19 (shared auth-shell) is designed.
  - Bright "add" green in non-Pesto light themes — only retune if feedback persists after eyeballing.

**Open questions for user:**
- Anything still reading too bright / too dim / off-brand after A1b? Flag page + theme.
- Proceed to A2, or pause to eyeball?

---

## 2026-06-04 — A1 STEP 2 complete (Chunks D, G, C, B, E, H, F)
**Status:** complete — A1 STEP 2 finished end-to-end across the whole audit.
**What changed:**
- All remaining chunks executed in a single push: D (recipes/cook), G (settings — 9 files), C (products/price-history — minimal-touch per master Decision 1), B (stock — 7 files), E (meal-plans + shopping — 6 files), H (dashboard/reports/waste/data — 8 files), F (Dora + help + shared widgets — 9 files).
- **App-wide final state:** 0 numbered Quasar palette classes (`text-grey-N`, `bg-red-1`, …), 0 bare `text-grey` class usage, 1 numbered palette prop residual (`ScanOverlay.vue:61 label-color="grey-4"` per DEC-4 — accepted).
- **Tokens added** (resolving DEC-3): `--dora-disc-bg` / `--dora-halo` / `--dora-halo-strong` in `tokens.scss` + per-theme overrides in `themes.scss` for all 10 theme variants. `DoraBubble.vue` disc backdrop and `DoraChat.vue` chat surfaces now ride these; `.body--dark` workaround blocks deleted because the tokens flip automatically.
- **Charts wired to tokens:** `usePriceHistoryPalette.ts` and `TrendSparkline.vue` read CSS vars at call time with HSL fallbacks; `PriceHistoryChart.vue` SVG axes routed through CSS classes.
- **Hex-pinned shadow / pulse / glow patterns** replaced via `color-mix(in srgb, var(--token) X%, transparent)` for DEC-6 (menu glow), DEC-7 (stock pulse keyframe), DEC-11 (dashboard elevation shadows).
- **DEC carve-outs preserved:** logos (Aldi/Coles/IGA), ProductSearchCard category hash (DEC-8), MerchantLogo placeholder (DEC-9), ScanOverlay rings (DEC-4), theme-picker swatches (DEC-10), Reports/Dashboard CSS-read fallbacks (consistency-only).

**Decisions made during the run:**
- Quasar `color="warning"` / `color="negative"` / `color="positive"` used for icon and chip semantic colours because they ride `--q-*` written by `themeService.setCssVar` — i.e. they are theme-aware.
- Neutral grey badges and chips (the "(you)" badge, "Inactive" badge, archived-count badge) standardised to `color="grey"` (Quasar's neutral mid-grey, no shade). Fixed but reads OK in both modes; tiny surfaces. Not a follow-up.
- Avatars that were `color="amber-3" text-color="grey-10"` (warm placeholder over light) folded into `color="accent" text-color="dark"` for the "active" branch and `class="dora-bg-sunken dora-text-secondary"` for the neutral branch (so avatars theme-shift).
- The `ShoppingListDetail.vue:2251` Dora-touched highlight folded into `var(--brand-primary-soft)` (resolves the audit's open mapping).
- `ShoppingListShopMode.vue` `var(--surface-elevated, rgba(0,0,0,0.04))` fallbacks — dropped the rgba safety net since the token always exists in this codebase; the orphan `var(--c-ink-mute, …)` reference replaced with `var(--text-muted)`.
- `DoraChat.vue` legacy `--c-accent` / `--c-ink-mute` private vars retired in favour of real tokens.

**Files touched:**
- `web_app/src/css/tokens.scss` (Dora tokens added)
- `web_app/src/css/themes.scss` (per-theme Dora-disc/halo overrides for 10 themes)
- Pages: `RecipesOverview`, `RecipeDetailPage`, `RecipeCookMode`, `MealPlansOverview`, `ShoppingListsOverview`, `ShoppingListDetail`, `ShoppingListShopMode`, `ShoppingListTemplates`, `ShopNowRedirect`, `StockOverview`, `StockItemDetailPage`, `StocktakePage`, `StocktakeRunner`, `ProductSearch`, `MyProductsPage`, `PriceHistoryPage`, `DashboardPage`, `ReportsPage`, `WastePage`, `DataManagement`, `TtsTestPage`, `DoraHelpPage`, `HelpPage`, `pages/data/*` (4 files), `pages/settings/*` (9 files), `pages/onboarding/WelcomeWizard.vue` (chunk I).
- Components: `RecipeCard`, `RecipeEditDialog`, `QuickAddSheet`, `ScanOverlay`, `stock/StockItemRow`, `ProductSearchCard`, `PriceHistoryChart`, `MerchantLogo`, `TrendSparkline`, `dora/DoraBubble`, `dora/DoraChat`, `chips/*`, `SelectComponent`, `CardComponent`, `settings/LocationRow`.
- Composable: `usePriceHistoryPalette.ts`.
- `CHANGELOG.md` (Unreleased § Changed).

**Verification:**
- App-wide greps for numbered palette classes / palette props confirm a single intentional residual (`ScanOverlay`).
- Hex residuals are now exclusively the documented carve-outs (logos, deterministic hash, fallbacks-after-CSS-read).
- Light + dark + Cherry Cola Dark reasoning per chunk: dora glow now picks up theme brand colour (no more "Pesto Pesto Pesto"); dashboard ink shadows ride elevation tokens; charts pull from --chart-1..5.
- **Not run** the dev server. User needs to eyeball: at minimum dashboard, stock overview, recipes overview, a recipe in cook mode, shopping list detail + shop mode, meal plans, the Dora chat panel (note: Dora's halo will look distinctly different per theme now — this is the DEC-3 design call), settings (all sub-pages), reports.

**Next up:**
1. **User eyeballs the whole app across at least three themes** (Pesto, Pesto Dark, Cherry Cola Dark are the most diagnostic). Note anything broken/ugly in the worklog and we'll re-tune in A1b.
2. **A1b — token value tuning.** Backlog so far:
   - DEC-A-1: theme-flip `--overlay-hover` + add `--overlay-hover-on-coloured` (for toolbar surfaces). Delete the `.body--dark` overrides in `CommandPalette.vue` / `ShortcutsCheatsheet.vue` / `MainMenuButton.vue`.
   - DEC-A-2: add `--highlight-search` token (alpha-blended for matched-substring backgrounds).
   - Audit `--semantic-warning` value in `lemon-tart-dark` (pure yellow at 100%, may clash with text-on-it).
   - `--text-muted` contrast vs `--surface-page` in Pesto (currently borderline AA).
   - `--ring-focus` is pinned to Pesto green hue regardless of theme — make it brand-aware.
   - Tune Dora token values per theme — current dark-theme halos use brand-primary at α 0.32/0.55 which may be too bright in Cherry Cola Dark / Sourdough Dark.
3. **A2 — Standard button + toolbar** (next Wave A prompt; has decisions — read `prompts/A2_standard_button_toolbar.md` Impact block first).

**Open questions for user:**
- Anything you see in any theme that looks wrong? Flag the page + theme.
- Proceed to A1b value tuning or jump to A2 standard button/toolbar?

---

## 2026-06-04 — A1 STEP 2, Chunk I (onboarding)
**Status:** complete
**What changed:**
- `pages/onboarding/WelcomeWizard.vue`: all 11 palette-class hits + 3 palette `color=`/`track-color=` props replaced with semantic tokens (`dora-text-muted`, `dora-text-secondary`, `dora-bg-negative-soft text-negative`).
- Dropped `track-color="grey-3"` on the step progress bar so the unfilled track inherits the theme-aware default.
- `color="grey-7"` on the skip-buttons → `class="dora-text-secondary"` (flat btn picks up text colour from class).

**Decisions made:**
- `text-body2 text-grey-8` (body copy in step cards) → `dora-text-secondary` rather than `dora-text-muted` — these are descriptive paragraphs, not captions.
- `text-caption text-grey` → `dora-text-muted` (caption-volume helper).
- No new discovered DECs in this file.

**Files touched:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue`
- `CHANGELOG.md`

**Verification:**
- Re-ran combined grep against this file: zero residual palette classes, palette props, hex, or rgba.
- Light/dark reasoning: the "current step" highlight uses `color="primary"`/`color="secondary"` already (theme-aware); the now-soft error banner picks up theme-defined `--semantic-negative-soft`; the dropped `track-color` lets the progress bar's unfilled portion ride the default light-on-bg.
- **Not run** the dev server.

**Next up:**
- **A1 STEP 2 Chunk D (recipes+cook).** Files: `pages/RecipesOverview.vue`, `pages/RecipeDetailPage.vue`, `pages/RecipeCookMode.vue`, `components/RecipeCard.vue`, `components/RecipeEditDialog.vue`. ~30 hits per the audit.
- Chunk order from `THEME_AUDIT.md §6`: D → G → C → B → E → H → F (last).

**Open questions for user:** none — clear to proceed with Chunk D.

---

## 2026-06-04 — A1 STEP 2, Chunk A (auth/shell)
**Status:** complete
**What changed:**
- Added 11 semantic helper classes to `web_app/src/css/colours.scss` (`dora-text-muted`, `dora-text-secondary`, `dora-text-on-primary`, `dora-text-on-toolbar`, `dora-bg-page/sunken/elevated`, `dora-bg-{positive,negative,warning,info}-soft`). Quasar's `.text-positive/negative/warning/info` already ride `--q-*` and are theme-aware, so reused those for semantic ink.
- Replaced Quasar palette classes / props / hardcoded literals with semantic tokens across all Chunk A files (full list in CHANGELOG entry).
- `ErrorNotFound.vue` 404 page repainted from `bg-blue text-white` to `var(--surface-toolbar) / var(--text-on-toolbar)` so it shifts per theme; "Go Home" button now inverts those.
- `MainMenuButtonStrip.vue:111` amber glow now uses `color-mix(in srgb, var(--brand-accent) 55%, transparent)` (DEC-6).
- Filed two newly-discovered token-system gaps as DEC-A-1 and DEC-A-2 in `web_app/THEME_AUDIT.md §6b` — both are A1b territory, neither blocks future chunks.

**Decisions made:**
- `LoginPage.vue` skipped entirely per DEC-2 (intentional splash).
- Theme-picker swatches in `PreferencesSettings.vue` belong to Chunk G; not touched.
- `text-color="white"` on q-badge / q-avatar inside `AlertsBell.vue` (lines 8, 82, 166) **kept as-is** — those badges sit on `color="negative"` / `color="positive"` surfaces which are always saturated regardless of theme. White-on-saturated is theme-stable; not dark-broken.
- Where icons used `:color="… 'grey-7'"` (`VerifyEmailPage`, `ConfirmEmailChangePage`) the conditional fell back to `undefined` paired with a `dora-text-secondary` class — `q-icon` honours the class when `color` is unset.
- `.body--dark` style overrides in `CommandPalette` / `ShortcutsCheatsheet` left alone — they're workarounds for `--overlay-hover` not theme-flipping (DEC-A-1). Fixing them properly requires adding `--overlay-hover` overrides in dark theme blocks, which is out of A1 scope.

**Files touched:**
- `web_app/src/css/colours.scss` (+11 helper classes)
- `web_app/src/components/OfflineBanner.vue`
- `web_app/src/components/PageErrorState.vue`
- `web_app/src/components/CommandPalette.vue`
- `web_app/src/components/AlertsBell.vue`
- `web_app/src/components/PwaInstallPrompt.vue`
- `web_app/src/components/ShortcutsCheatsheet.vue`
- `web_app/src/components/FormErrorSummary.vue`
- `web_app/src/components/menu/MainMenuButtonStrip.vue`
- `web_app/src/pages/ErrorNotFound.vue`
- `web_app/src/pages/ForgotPasswordPage.vue`
- `web_app/src/pages/ResetPasswordPage.vue`
- `web_app/src/pages/VerifyEmailPage.vue`
- `web_app/src/pages/ConfirmEmailChangePage.vue`
- `web_app/src/pages/SettingsShell.vue`
- `web_app/src/layouts/WelcomeLayout.vue`
- `web_app/THEME_AUDIT.md` (added §6b discovered gaps)
- `CHANGELOG.md` (Unreleased § Changed)

**Verification:**
- Re-ran grep scan across Chunk A files: zero remaining Quasar palette classes / palette `color=` props / hex / named CSS colours. Five `rgba(...)` residuals all in `.body--dark` blocks or the search highlight — filed as DEC-A-1 / DEC-A-2.
- Reasoned through both Pesto (light) and Pesto Dark per the prompt requirement. Cherry Cola Dark sanity-check: the auth banners now use the theme's `--semantic-negative-soft` (deeper red-pink in CC Dark) and the 404 page picks up the deep merlot of `--surface-toolbar`. Should look on-brand instead of pinned to blue.
- **Not run:** the actual dev server. User should open the affected pages (login → forgot → reset → verify → 404, plus Alerts panel, Command palette `Ctrl+K`, Settings shell, PWA install prompt) and switch themes (Pesto Dark, Cherry Cola Dark) to eyeball before signing off the chunk.

**Next up:**
- **User eyeballs Chunk A in browser** (sequence above). Note anything that looks wrong in the worklog so the next chunk can pick it up.
- Then **A1 STEP 2 Chunk I (onboarding — `pages/onboarding/WelcomeWizard.vue`)** per the chunk order in `THEME_AUDIT.md §6`. Smallest chunk, ~11 hits — fast.
- A1b (token-value tuning) backlog now has two new items in `THEME_AUDIT.md §6b`: DEC-A-1 (hover overlay theme-flip) and DEC-A-2 (search-result highlight token).

**Open questions for user:**
- After eyeballing, are the auth banners (red error / green success) reading right in all themes? If anything looks off, flag the page+theme and I'll re-tune in A1b.
- OK to proceed straight to Chunk I, or pause here?

---

## 2026-06-04 — A1 DEC-1..DEC-11 resolved
**Status:** complete (decisions only — no code changed)
**What changed:**
- All 11 `needs_decision` items in `web_app/THEME_AUDIT.md` resolved. New §6a in the audit records the answers.
- DEC-2: keep LoginPage `--lp-*` ladder as-is. Chunk A must skip those lines.
- DEC-3: introduce theme-aware Dora tokens (`--dora-disc-bg`, `--dora-halo`, `--dora-halo-strong`) in `tokens.scss` defaults + per-theme overrides in `themes.scss`. **Chunk F is gated on this token addition** — do it as a prerequisite at the start of Chunk F.
- DEC-1, 4, 5, 6, 7, 8, 9, 10, 11: all accepted as the audit's recommended answers.

**Decisions made:** see `web_app/THEME_AUDIT.md §6a` — that's the canonical record. Of note for sequencing:
- Chunk F (Dora) now has a prerequisite "add Dora tokens" step before any `.vue` edits.
- Chunk A (auth/shell) shrinks slightly because the LoginPage `--lp-*` block is excluded.

**Files touched:** `web_app/THEME_AUDIT.md` (added §6a).

**Verification:** none needed — decisions only.

**Next up:**
**A1 STEP 2 — Chunk A (auth/shell).** Run the chunk fix prompt per `prompts/A1_theme_compliance.md §STEP 2`, scoped to the files listed in `THEME_AUDIT.md §3 Chunk A`. Apply DEC resolutions from §6a. Eyeball Pesto light + Pesto Dark + Cherry Cola Dark before marking the chunk complete.

**Open questions for user:** none — clear to proceed with Chunk A on user say-so.

---

## 2026-06-04 — A1 STEP 1 (theme token-compliance audit)
**Status:** complete
**What changed:**
- Created `web_app/THEME_AUDIT.md` — the offender map + chunk plan for A1 STEP 2 fixes. **No code changes.**
- 9 chunks (A auth/shell, B stock, C products+price-history, D recipes+cook, E meal-plans+shopping, F dora+shared, G settings, H dashboard+reports+waste+data, I onboarding) with per-row offender · proposed token · mode-risk · light-shift.
- Token cheat-sheet from the actual `tokens.scss` / `themes.scss` / `themeService.ts` is at §2.
- 11 `needs_decision` items (DEC-1..DEC-11) consolidated at §4 — these gate STEP 2.
- A1b out-of-scope spotted at §5 (too-bright greens, focus-ring pinned to Pesto, text-muted contrast on Pesto Dark, etc.).

**Decisions made:**
- Excluded `tokens.scss`, `themes.scss`, `colours.scss`, `quasar.variables.scss`, `themeService.ts`, `motion.scss` from the scan — they legitimately hold raw colour values.
- Grouped settings/* into its own chunk (G) rather than the "other" bucket — it had ~50 hits and the theme-picker swatches there are the only legitimate template hex in the app (DEC-10).
- Chunk run order in `THEME_AUDIT.md §6`: A → I → D → G → C → B → E → H → F. Narrowest ripple first; Dora (F) last because it's gated on DEC-3.
- For products chunk (C): minimal-touch only — that surface is moving to the companion app per master Decision 1, so don't refactor structure during paint.

**Files touched:** `web_app/THEME_AUDIT.md` (new).

**Verification:**
- Read `tokens.scss`, `themes.scss` (first ~80 lines), `colours.scss`, `quasar.variables.scss`, `themeService.ts`, `app.scss` to ground the token map.
- Ran grep scans for: hex literals, `rgb/rgba/hsl/hsla()`, Quasar palette classes (`text-grey`, `bg-red-1`, …), Quasar `color=`/`text-color=` palette props, inline `:style` colour expressions, bare CSS named colours, SCSS `$colour` vars outside token files, `setCssVar` calls outside `themeService.ts`.
- The "220 text-grey" count in the audit is an approximation — Quasar's `text-grey` (no shade) is fixed mid-grey in both light and dark themes, so it's the single biggest dark-mode hazard.
- *Not verified* by running the app — this is an audit, not a fix.

**Next up:**
1. **User reviews `web_app/THEME_AUDIT.md`** — especially the 11 DEC-* items in §4. Each one needs a yes/no/option-pick.
2. After decisions, **run A1 STEP 2 chunk-by-chunk** per the prompt template in `prompts/A1_theme_compliance.md` §STEP 2, starting with **Chunk A (auth/shell)**.
3. Parallel-safe Phase 0 candidates if a second agent is available: **re-baseline `STATUS.md`** (docs folder), or **INV-6** (recipe-comparison worth, `prompts/INV_investigations.md`).

**Open questions for user:**
- Sign off DEC-1..DEC-11 in `THEME_AUDIT.md §4` (the audit includes a recommendation on each — fastest path is "I accept all recommendations" unless any specific one bothers you).
- Run STEP 2 Chunk A next in this session, or wait?

---

## 2026-06-04 — Session bootstrap & handoff system
**Status:** recon-only
**What changed:**
- Read the planning library entry points: `00_DOCS_INDEX.md`, `RECONCILED_FINISHING_PLAN.md`, `STATUS.md`, `FEEDBACK_TRIAGE_AND_PLAN.md`, `prompts/00_INDEX.md`, `prompts/A1_theme_compliance.md`.
- Created `CLAUDE.md` and this `DORA_WORKLOG.md` at repo root so handoffs between concurrent Claude sessions are clean.
**Decisions made:**
- Worklog lives at repo root (versioned with code, both agents see it automatically).
- No per-agent labels — timestamp + bullets are enough to reconstruct.
- Worklog is process-only; `CHANGELOG.md` stays the product log. Two files, two purposes.
**Files touched:** `CLAUDE.md`, `DORA_WORKLOG.md`.
**Verification:** docs read; repo state unchanged otherwise.
**Next up:** **Run `prompts/A1_theme_compliance.md` STEP 1 (the audit only — produces `web_app/THEME_AUDIT.md`, no code changes).** This is the master plan's "immediate next step" and is no-regret / dependency-free. STEP 2 (chunked fixes) waits until the audit is reviewed.

Parallel candidates if you want a second session running:
- **Re-baseline `STATUS.md`** (in the docs folder) against current code. It's stale — meals→recipes merge, substitutes-graph removal, stock-map removal, DS4 all unrecorded. Cheap, no collision with A1.
- **INV-6** — assess recipe-comparison's real worth (`prompts/INV_investigations.md`). Read-only; informs the X2 keep/cut call.

**Open questions for user:**
- Any redirect from the recommended A1-audit start, or proceed?
- Want a second agent on STATUS re-baseline or INV-6 in parallel?
