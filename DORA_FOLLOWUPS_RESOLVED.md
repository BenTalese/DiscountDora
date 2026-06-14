# Dora Follow-ups Ledger — Resolved

Archive of `[RESOLVED]` items moved out of `DORA_FOLLOWUPS.md`. Kept for the
audit trail — never delete entries here.

When you resolve an open item, move its block from `DORA_FOLLOWUPS.md` to this
file, flip the heading from `[OPEN]` to `[RESOLVED]`, and append a one-line
state note describing how it was resolved (date + brief mechanism). New
resolutions go at the **top**.

---

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
