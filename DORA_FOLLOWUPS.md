# Dora Follow-ups Ledger

Stateful backlog of **follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other two logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session,
  each with a tracked state so every session knows what's still pending.

## How to use this file

- **On session start:** scan for `[OPEN]` items. Surface the ones whose
  *recommended resolution point* is "now" or matches the work about to start, and
  **ask the user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. Mark items you actually resolved as `[RESOLVED]` (don't delete them —
  the trail matters), with a one-line note on how.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not proof
  a user-reported bug is fixed. Track each reported item individually; never bury
  several as one "all fine" note. (See CLAUDE.md → "On ending a work unit".)
- Keep the newest items near the top of the Open section.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open

## [OPEN] FU-042 — Alerts bell count ≠ list count (badge excludes low + ignores snooze)
- **Raised:** 2026-06-06 (C-9 brief; feedback L438)
- **Type:** finding (reported bug — root cause found statically)
- **What:** The bell badge shows fewer than the dropdown lists ("I see 6, the bell
  shows 10"). Two causes: (1) badge = `high_count + medium_count` (`alertStore:99`)
  — it **excludes low-severity**, but the list shows all severities; (2) the badge
  uses raw backend counts while the list filters **client-snoozed** alerts
  (`alertStore:81`), so snoozing shrinks the list but not the badge.
- **Why open:** real reported bug; fixable independently of the full C-9 page.
- **Recommended resolution:** define ONE "what counts" set (C-9 §2.3) and derive
  the badge, bell list, dashboard card, and page from it — badge number must equal
  the count of items in its tier, and snooze must apply everywhere. Confirm in
  browser after. Can ship ahead of the control-centre page.

## [OPEN] FU-041 — Onboarding "you already have groups/locations" copy on first-run
- **Raised:** 2026-06-06 (C-5 brief; feedback L32/L33)
- **Type:** finding (reported defect — didn't reproduce statically)
- **What:** User reported the seed step says "You already have some groups set
  up…" / "You already have locations…" during *first-time* setup. Static read
  shows that copy is gated on `has_groups`/`has_locations` (`onboarding.py:94-117`,
  `WelcomeWizard.vue:161-172,195-205`), which are false on a truly-empty DB — so it
  shouldn't render on a clean install. The user likely had dev/seed data or a prior
  seed run. No migration pre-creates *user* groups/locations (confirmed).
- **Why open:** the report came from real usage; a static read isn't proof.
- **Recommended resolution:** **confirm in browser** on a genuinely fresh DB
  (register first user → onboarding) that the "already have" copy does NOT appear
  and the seed checkboxes are enabled. If it DOES appear, find what's seeding user
  groups/locations and fix. Folded into the C-5 §2.6 design either way.

## [OPEN] FU-040 — C-4 should model structured recipe steps (C-3 depends on it)
- **Raised:** 2026-06-06 (C-3 brief)
- **Type:** follow-up (design dependency)
- **What:** Recipe instructions are a freeform text blob (`recipe.py` instructions;
  cook mode splits on newlines, `RecipeCookMode.vue:356-363`). Cook mode's richer
  per-step features — reliable ingredient highlighting (instead of fragile
  text-match), per-step tools, per-step hints, per-step timers — all need
  **structured steps** (step = text + optional sub-steps + hint + the
  ingredients/tools it uses). This is a recipe-model change that belongs in **C-4**
  (adjacent to its multi-part "sections"), not cook mode.
- **Why deferred:** C-3 is a proposal; the model change is C-4's to own. Flagged so
  C-4 picks it up if/when revisited.
- **Recommended resolution:** fold a structured-steps model into the C-4 design
  (it's listed as C-3 open decision 2 and cross-ref'd in `PROPOSAL_COOK_MODE.md
  §2.6`). Cook mode degrades gracefully to freeform if a recipe has no structure.

## [OPEN] FU-039 — Wire up `Recipe.image` (parallels StockItem.image)
- **Raised:** 2026-06-06 (C-4 brief)
- **Type:** deferred job
- **What:** `Recipe.image` (bytes) exists on the entity but is never displayed,
  edited, or uploaded — a dead field, same pattern as `StockItem.image` (FU-033).
  C-4 (L249 "recipes should have an image") wires it up: upload + display on card
  and detail + missing-image placeholder.
- **Why deferred:** part of the C-4 Cookbook redesign; needs the image-handling
  decisions (size limits, formats) resolved with the StockItem.image work for
  consistency.
- **Recommended resolution:** during C-4 implementation; share the image
  upload/storage approach with FU-033 (StockItem.image) so there's one mechanism.
  See [[stockitem-image-substitute-notes-intent]].

## [OPEN] FU-038 — Cart button fires contradictory double-toast on already-on-list
- **Raised:** 2026-06-06 (C-7 brief; feedback L154)
- **Type:** finding (reported bug)
- **What:** Adding an already-listed item shows two toasts at once — "0 added, 1
  already on list" AND "<item> added to your primary list" (feedback L154). The
  `addToList` path (`useStockItemActions.ts:38-64`) and a caller both notify. The
  C-7 proposal makes the button idempotent/state-aware, but this double-toast can
  be fixed independently and sooner.
- **Why deferred:** C-7 is a proposal (no code). The full state-aware button is a
  bigger build; the toast dedupe is a small standalone fix.
- **Recommended resolution:** opportunistic / quick win — dedupe to one toast in
  `addToList`; confirm in browser. Or fold into C-7 implementation phase 1.

## [OPEN] FU-037 — `.secret_key` hardcoded to `./data/`, ignores DORA_DATA_DIR
- **Raised:** 2026-06-06 (INV-3 re-verification)
- **Type:** finding (latent bug)
- **What:** `dora_api/app.py:23` resolves the session-secret file as
  `Path('data') / '.secret_key'` — a literal CWD-relative path, NOT
  `DORA_CONFIG.get_data_dir()`. Everything else (DB, config, uploads, logs)
  honours `DORA_DATA_DIR`. So on the desktop app (data dir =
  `%LOCALAPPDATA%\BenTalese\Dora`) the secret key instead writes to `./data/`
  relative to the launch CWD.
- **Why it matters:** the secret escapes the configured/backed-up data dir; it's
  CWD-dependent, so launching from a different folder regenerates it and silently
  invalidates all existing session cookies (everyone logged out). Found via
  static read; not yet observed at runtime.
- **Recommended resolution:** now/soon — change to resolve via
  `DORA_CONFIG.get_data_dir() / '.secret_key'`. Low-risk one-liner. Confirm in
  browser/desktop that sessions persist across a restart from a different CWD.

## [OPEN] FU-036 — Confirm Shop Mode "Substitute" swaps offer-only (gates INV-8)
- **Raised:** 2026-06-06 (INV-8)
- **Type:** finding
- **What:** Static read says Shop Mode's "Substitute" button
  (`ShoppingListShopMode.vue:176-182`) swaps the **merchant offer**, while the
  permanent stock-item substitute swap lives in the full-list per-line menu
  (`ShoppingListDetail.vue:756-763`). INV-8's "rework into Shop Mode" recommendation
  depends on this being true.
- **Why deferred:** INV is investigation-only; needs runtime confirmation.
- **Recommended resolution:** confirm in browser — in Shop Mode, tap "Substitute"
  on a line and verify it changes the offer/merchant (not the stock item). If it
  actually swaps the item, INV-8's recommendation changes.

## [OPEN] FU-035 — Stock overview silently shows only the first 50 items
- **Raised:** 2026-06-06 (INV-2)
- **Type:** finding (likely real bug)
- **What:** `stockItemStore.getStockItemsAsync` (`stockItemStore.ts:48`) calls
  `getAllAsync()` → `GET /stock-items` with no query string. Backend defaults to
  page 1, `DEFAULT_LIMIT = 50` (`query_options.py:24`; `MAX_LIMIT = 500`). The
  store takes `page.items` and never reads `page.total` or loops further pages —
  so a pantry with >50 items shows only the first 50 (alphabetically). Filters
  and counts operate on the truncated set. Found via static read.
- **Why deferred:** INV-2 is investigation-only; this is a code fix.
- **Recommended resolution:** confirm in browser (create >50 stock items, check
  the overview shows them all), then fix — cheapest is requesting `?limit=500`;
  better long-term is paging or virtualised infinite-scroll. See
  `STOCK_OVERVIEW_PERF.md`.

## [OPEN] FU-034 — Wire up `StockItemSubstitute.notes` (substitution notes)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItemSubstitute.notes` column exists (added in the
  `c8a1d3b6e9f4` undirected-refactor migration) but was never wired up.
  `add_substitute.py:66` hardcodes `notes=None`; absent from `SubstituteDto`;
  zero frontend references. **Intended feature** (user confirmed): notes should
  capture *how* to substitute, e.g. "X butter → Y amount of olive oil".
- **Why deferred:** wire-up work, not no-regret; best done with the substitute
  surface so the note shows where it's useful (incl. B8 cook-mode swap).
- **Recommended resolution:** later — fold into **INV-8** (substitute
  swap-into-list assessment) or **B8** cook-mode temporary-swap work.

## [OPEN] FU-033 — Wire up `StockItem.image` (own image + product fallback)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItem.image` (LargeBinary) exists but is always set to `None`
  (`create_stock_item.py:84`), never returned in any DTO, no frontend.
  **Intended feature** (user confirmed): a stock item should carry its own
  image, and when it has none but a *linked product* has an image, fall back to
  the product's image. Neither half is built.
- **Why deferred:** it's a feature (upload + fallback + display), not a clean-up.
  Needs design Qs resolved first (precedence, size limits, list-view display).
- **Recommended resolution:** later — its own prompt, or a stock-item-detail
  polish chunk.
- **State note:** 2026-06-06 — corroborated by the original spec note
  *"When I link a product to a stock item, if the stock item has no picture it
  takes the product's picture automatically… otherwise a 'no pic' fallback"*
  (`docs/00_original_spec/Feature Notes/`). Confirms own-image + product-image
  fallback is a designed feature, not dead code. Still `[OPEN]`.

## [OPEN] FU-032 — C-2: confirm B6 allocation works end-to-end in browser
- **Raised:** 2026-06-06 (C-2 recon)
- **Type:** finding
- **What:** Backend `_hydrate_unallocated` (in `get_recipes.py`) computes
  `unallocated_meals = max(available_meals - sum(future un-consumed
  servings), 0)` via a single GROUP BY. The recipe palette renders the
  result directly. On static read, B6 (allocation reduces "X unallocated
  of Y on hand") works correctly. Original B6 report was from real usage,
  so per the CLAUDE.md MANDATORY rule it stays `[OPEN] confirm in
  browser` until eyeballed.
- **Recommended resolution:** confirm in browser — cook 4 meals of a
  recipe, drop it on two future days (2 servings each), verify palette
  shows "(0/4)". If it doesn't, capture the response from
  `GET /recipes?...&include=unallocated` and re-open as a real bug.

## [OPEN] FU-031 — B9.3: stale "Recipes" labels after A8 cookbook rename
- **Raised:** 2026-06-06 (B9.3 sweep)
- **Type:** leftover
- **What:** A8 renamed Recipes → Cookbook (`/cookbook`; `/recipes` redirects).
  The command palette still says "Go to Recipes" → `/recipes`. Functional via
  the redirect, but the label is now stale. Same likely in other static lists
  (tour cards, help text). Worth a one-shot rename sweep.
- **Recommended resolution:** opportunistic — fold into the A8 wrap-up or
  next polish pass.

## [OPEN] FU-030 — B9.9: confirm 404 page already-themed (no code change)
- **Raised:** 2026-06-06 (B9.9; CLAUDE.md confirm-in-browser rule)
- **Type:** finding
- **What:** Both 404 surfaces already use tokens — `ErrorNotFound.vue`
  uses `--surface-toolbar`/`--text-on-toolbar`; `errors/ErrorPageNotFound.vue`
  delegates to `PageErrorState`. A1 themed them. Reported defect didn't
  reproduce statically.
- **Recommended resolution:** confirm in browser — hit a 404 URL (e.g.
  `/this-route-does-not-exist`) and verify both fullscreen and in-layout
  variants look themed (not default Quasar).

## [OPEN] FU-029 — B9.4: confirm command-palette commands all trigger
- **Raised:** 2026-06-06 (B9.4; CLAUDE.md confirm-in-browser rule)
- **Type:** finding
- **What:** Ctrl+K palette: every static command has a wired action.
  `create.stock-item` navigates to `/stock?create=1` and the page already
  watches `route.query.create`. Reported defect "doesn't trigger some
  actions" did not reproduce in static code.
- **Recommended resolution:** confirm in browser — open palette, run each
  Create / Navigate / Shopping-lists / View / Help command, verify each
  produces the intended outcome. If any really is broken, re-open as a
  real bug with the command id.

## [OPEN] FU-028 — B9.1: confirm shopping-list drag-drop ordering
- **Raised:** 2026-06-06 (B9.1; CLAUDE.md confirm-in-browser rule)
- **Type:** finding
- **What:** Static walk-through (both drag-up and drag-down examples) ends
  with the dragged item correctly placed BEFORE the target index. Backend
  `bulk_operations.reorder_lines` sorts by `(sequence, id)`. Frontend
  `ShoppingListDetail.onLineDrop` insertAt math
  (`fromIdx < toIdx ? toIdx - 1 : toIdx`) is correct.
- **Recommended resolution:** confirm in browser — reorder a few times,
  drag both directions, drop on a row and check the dragged item lands
  exactly where the dashed outline showed. If wrong, capture the exact
  before/after order and we'll re-investigate.

## [OPEN] FU-027 — B9.7: log-rotation model decision (timed vs size)
- **Raised:** 2026-06-06 (B9.7)
- **Type:** open decision
- **What:** `dora_api/infrastructure/logging_setup.py:87` wires
  `RotatingFileHandler` size-based at 10MB × 5 backups. The current
  ~46k-line file is well below the 10MB trigger, so it has simply not
  rotated yet. The user's reported symptom — "logs span the wrong date
  range" — implies an expectation of *time-based* rotation (e.g. one
  file per day).
- **Decision needed:** keep size-based (and just trust the threshold), or
  switch to `TimedRotatingFileHandler` (and pick `when` — typically
  'midnight' for daily). Could also go hybrid (whichever fires first)
  but Python's stdlib doesn't ship that out of the box.
- **Recommended resolution:** decide before any other log-related work
  (INV touches `.local` folder layout — natural pair).
- **State note:** 2026-06-06 (INV-3) — root cause confirmed and a concrete
  recommendation written in `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md`
  (switch to `TimedRotatingFileHandler`, midnight, ~14 backups; keep `data/` +
  `cache/` split; no `.local` folder exists). Still `[OPEN]` pending the
  user's go-ahead to implement.
- **State note:** 2026-06-06 (post re-verification) — user asked whether the
  folder layout was actually verified; it was NOT originally (code-resolved paths
  described as if observed). Re-read the resolver directly: layout is less clean
  than first stated — `.secret_key` hardcoded escape (FU-037) + dev-vs-desktop
  log-nesting difference. On-disk confirmation still pending (app never run on
  this checkout); checklist added to the memo.

## [OPEN] FU-026 — B9.5: precise repro for "undo behaves oddly across surfaces"
- **Raised:** 2026-06-06 (B9.5)
- **Type:** finding / open verification
- **What:** `useUndo` registry is sound (per-entry inverse closures, redo
  stack cleared on new register, pending optimistic states). The
  surface-level mutations (`updateStockItemAsync`) capture pre-state
  field-by-field and register an inverse and redo closure for every
  changed field — including expiry pushes and clears. Static read shows
  the example flow (push expiry on dashboard → clear on detail page →
  Ctrl-Z twice) yields the correct end states.
  - Closest plausible "oddly" without a repro: the *originating surface*
    (Dashboard alerts) caches its own `alerts.value` and does NOT
    refetch after an inverse runs on another surface. So Ctrl-Z mutates
    the store correctly, but the Dashboard renders stale state until
    the user navigates / refreshes.
- **Recommended resolution:** capture an exact reproduction (which
  action on which surface in which order, what was expected, what
  actually happened, ideally a screen recording). Then either fix the
  staleness vector with a surface-level refetch on the affected store
  or pick a different design.

## [OPEN] FU-025 — Eyeball A6 text scale (xl + slightly-larger default) on dense screens
- **Raised:** 2026-06-05 (A6)
- **Type:** finding
- **What:** A6 widened the steps to 14 / 16.5 / 20.5 / 23px (added Extra-large) and
  bumped the default a touch (16 → 16.5px), so EVERY md user sees slightly bigger
  text now. Needs a real-browser check: at **Extra large**, spot-check dense
  screens (Stock Overview, Recipe detail, Meal plans) for layout breakage; confirm
  tooltips now scale (new `.q-tooltip` rule); confirm the small step's ~9–12px
  captions are still readable. Light + dark.
- **Why deferred:** can't run the app (node_modules absent).
- **Recommended resolution:** now-ish — when the app is next run. Deliberately-fixed
  px left in place (ScanOverlay camera UI, PriceHistoryChart SVG labels, Dashboard
  3px/7.5px micro-gauge) are intentional carve-outs, not bugs.

## [OPEN] FU-024 — A7 leftovers: dead banner CSS + wider footer adoption
- **Raised:** 2026-06-05 (A7)
- **Type:** leftover
- **What:** (a) Removing StockOverview's summary banner left its scoped
  `.stock-summary-banner` / `.stock-summary-stat` CSS unused (harmless dead
  rules). (b) `PageCountsFooter` is only wired on the 3 prompt pages
  (StockOverview, RecipesOverview, MyProductsPage); other list pages
  (ShoppingLists, MealPlans, etc.) could adopt it for consistency.
- **Why deferred:** dead CSS is harmless; broader adoption was out of A7's
  defined scope (3 pages).
- **Recommended resolution:** opportunistic — delete the dead CSS next time
  StockOverview is touched (or during the Wave-C Stock Overview top-area
  teardown); adopt the footer on other list pages if/when they get polish.

## [OPEN] FU-023 — A5 leftover: spinners not yet migrated on deferred surfaces
- **Raised:** 2026-06-05 (A5)
- **Type:** leftover
- **What:** A5 unified loading on the active app pages, but left raw `q-spinner`
  on the **deferred surfaces** (Reports, Data→Export/Print, Settings sub-pages —
  per the prompt-pack "deferred" list) and on **DoraChat's typing dots** (a
  deliberate `q-spinner-dots` indicator). Also: overview pages got `AppSpinner`
  rather than list-skeletons — fine, but list-skeletons would be a nicer touch.
- **Why deferred:** those pages are flagged "do not design yet"; a spinner swap
  is harmless but low-value there, and DoraChat's dots are an intentional style.
- **Recommended resolution:** opportunistic — migrate the deferred-page spinners
  to `AppSpinner` whenever those pages are next worked on. Decide DoraChat dots
  separately (keep as a typing indicator, or switch to AppSpinner). Consider
  list-skeletons for the big overviews during the FU-010 holistic look pass.

## [OPEN] FU-022 — Confirm A4 reported filter bug did NOT reproduce
- **Raised:** 2026-06-05 (A4; back-filled per the non-issue rule)
- **Type:** finding
- **What:** A4 was built around a reported bug — "clearing a filter input filters
  *everything* out instead of behaving as filter off (empty MUST = off)." Static
  read across StockOverview / RecipesOverview / MyProductsPage / ProductSearch
  found it did **not** reproduce — every page already skipped blank predicates
  (truthiness / `!= null` / empty-array / boolean-false). A4 hardened them to be
  explicit anyway, but the original symptom was never observed.
- **Why deferred:** can't run the app (node_modules absent); the report came from
  real usage, so a static read isn't proof.
- **Recommended resolution:** confirm in browser — on each of the four pages,
  clear each filter and verify all rows return (no wipe-out). If a wipe still
  happens somewhere, re-open as a real bug.

## [OPEN] FU-021 — Confirm A3 reported modal bug did NOT reproduce
- **Raised:** 2026-06-05 (A3; back-filled per the non-issue rule)
- **Type:** finding
- **What:** A3 was built around reported bugs — modals that "navigate/commit away
  on click-outside" (esp. the unsaved-changes modal navigating instead of
  staying) and modals with "no Cancel." Static read found these did **not**
  reproduce in current code: the `$q.dialog` confirms (recipe delete,
  unsaved-changes, cook-start) only commit/navigate on explicit `.onOk()` and
  resolve false on dismiss; template dialogs don't commit on `@hide`; all had a
  Cancel/Close. A3 standardised them via `BaseDialog` anyway.
- **Why deferred:** can't run the app (node_modules absent); reported from real
  usage, so a static read isn't proof.
- **Recommended resolution:** confirm in browser — backdrop-click / Esc on the
  key modals (new-recipe, recipe delete, cook-finish, and especially the
  unsaved-changes dialog) must cancel WITHOUT navigating or committing. Re-open
  any that still misbehave.

## [OPEN] FU-020 — Recipe-detail substitute swap affordance (cook-mode-only for now?)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding / open question
- **What:** B8 made substitute swapping a temporary **cook-session** action (in
  cook mode only). The recipe-detail "Find substitutes" dialog is now purely
  informational. Open question for the user: do you also want a quick swap
  affordance on the recipe detail page itself, or is cook-mode-only the intended
  model?
- **Why deferred:** cook-mode-only was the chosen scope for B8; adding a second
  swap entry point is a UX decision, not a bug.
- **Recommended resolution:** now-ish — quick user call. If "yes", design where it
  applies (a swap that's still non-destructive to the saved recipe — likely a
  "pre-stage this swap for the next cook" rather than editing the recipe).

## [OPEN] FU-019 — Confirm B8 reported defects that did NOT reproduce (per-defect)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding
- **What:** Three user-reported B8 defects could not be reproduced in a *static*
  read of current code (post meals→recipes merge). Each was REPORTED from real
  usage, so each needs an in-browser confirm before it can be called resolved —
  tracked individually below, not dismissed as a blanket "all fine":
  - **(a) "Remove-from-favourites does nothing."** Static read: chain looks sound
    (`toggleFavouriteAsync` sends `!is_favourite` → PATCH → backend assigns →
    refetch). Confirm un-favourite persists in the running app. If it fails,
    likely PATCH-semantics (cf. B3) — re-open as a real bug.
  - **(b) "Clicking a related recipe dumps you on the Cookbook overview."** Static
    read: there is **no related-recipes section anywhere** in the current UI.
    Confirm whether the user expects one (i.e. is the real ask "add related
    recipes"?) or whether this is genuinely gone.
  - **(c) "All recipe actions inert except Cook."** Static read: every action
    (favourite, save, log-cook, adjust-meals, import, add-to-list, delete,
    export) is wired to a working handler. Confirm each actually fires in-app.
- **Why deferred:** can't run the app (node_modules absent); needs eyeballing.
- **Recommended resolution:** now-ish — confirm each of (a)/(b)/(c) when the app
  is next run. Flip to `[RESOLVED]` only once verified; re-open any that still
  break as real bugs.

## [OPEN] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Why deferred:** out of B7's original scope; opportunistic cleanup.
- **Recommended resolution:** opportunistic — fold into the next polish
  pass.

## [OPEN] FU-017 — B3: user re-test "can't save unless I change the name"
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** open verification
- **What:** Static read says every update handler already does the right
  thing (`model_fields_set` + exclude-self on the name-uniqueness check).
  No code changed this session for B3. But the user originally reported
  the symptom in browser testing, and the Wave-B self-audit found two
  other "looked fine on paper, broken in browser" cases — so this might
  also reproduce despite the static evidence.
  - To re-test: edit a stock item, change only e.g. `expiry_date`, save.
    Then edit a recipe, change only `servings`, save. Both should
    succeed without a "name already exists" 422.
  - If it reproduces, capture the request payload + response body and
    share — that will tell us whether (a) wrong endpoint is being hit
    (e.g. the create-new path), (b) the frontend is sending a
    different `name` value than displayed, or (c) something else.
- **Why deferred:** can't reproduce statically; cheaper to wait for a
  live error than keep tracing speculative paths.
- **Recommended resolution:** when the user gets a browser session up
  next — try the test above; report back.

## [OPEN] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up)
- **Type:** finding
- **What:** The onboarding "dead button" bug was a stale `authStore.currentUser`
  read by the router guard after `onboardingApi.completeAsync()` updated the
  backend. The same shape could exist for any flow where the backend mutates
  user-scoped state that a guard or computed reads from a frontend cache —
  candidates worth scanning: account changes (email/role/admin flag), data
  import/restore, restart-onboarding, and stock-item Undo restore. Look for
  `currentUser?.*` reads in router and layout guards, and pair each with the
  store mutation that should refresh them.
- **Why deferred:** out of B5's bug-fix scope; cross-cutting audit.
- **Recommended resolution:** opportunistic — fold into a Wave-A or polish
  pass once one obvious symptom shows up; not worth a dedicated session.

## [OPEN] FU-015 — B5: Onboarding tour "Alerts" card points at stock, not /alerts
- **Raised:** 2026-06-05 (B5)
- **Type:** finding
- **What:** `WelcomeWizard.vue` `TOUR_CARDS` "Alerts — Dora pings you" still
  routes to `/stock?attention=true` (its description even says "deep-link
  into Stock"). Now that `/alerts` exists as a real page, the tour card
  could go there instead — or keep both as different teaching moments
  (Stock + filter vs the dedicated list).
- **Why deferred:** out of B5's bug-fix scope; user-style decision.
- **Recommended resolution:** opportunistic, or fold into the C-wave
  alerts control centre brief.

## [OPEN] FU-014 — B1: confirm `image` field round-trips for product create
- **Raised:** 2026-06-05 (B1)
- **Type:** finding
- **What:** `CreateProductRequest.image` is typed `Base64Bytes | None` but the
  frontend ships `offer.image` as a string (likely a raw URL or a `data:` URL).
  B1 didn't change this — pre-existing — but the offer-spread fix in
  `ensureSaved` now sends `image` explicitly, so it'll exercise the parse path
  every save. If creates 422 on `image`, switch the request model to
  `str | None` (a URL, not bytes) or make the frontend omit the field.
- **Why deferred:** out of B1's scope (B1 was field-list mismatches, not type
  mismatches); no node_modules so couldn't test live.
- **Recommended resolution:** opportunistic — first time the user actually
  saves a scraped product in browser, watch for a 422 on `image`.

## [OPEN] FU-013 — A4 leftover: "consistent multi-select control" only partial
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

## [OPEN] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel is a plain div. `ProductSearch`
  previously wrapped its filters in a bordered `q-card`; that border is now gone
  (so all four pages match the borderless inline style the others always used).
- **Why deferred:** consistency was the goal; the other 3 pages never had a card.
  Whether the panel wants subtle containment (border/elevation) is a design call.
- **Recommended resolution:** fold into the FU-010 holistic look review, or a
  quick tweak to `FilterBar.vue` if the panel reads as too bare in the browser.

## [OPEN] FU-011 — AuditLogSettings filtering not standardised
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

## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** other light themes' `--text-muted` contrast nudge ([[FU-003]]),
  and the structural dual-source collapse ([[FU-004]]) so the review isn't fighting
  a moving target.
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

## [OPEN] FU-009 — Decide fate of the 3 specialised overlays vs BaseDialog
- **Raised:** 2026-06-05 (A3)
- **Type:** finding
- **What:** `AlertsBell` (seamless drawer), `CommandPalette` (search overlay), and
  `ScanOverlay` (persistent camera) were intentionally left on raw `q-dialog` —
  they aren't standard card modals.
- **Why deferred:** folding them into BaseDialog adds no value and risks their
  custom layout/positioning.
- **Recommended resolution:** now (quick yes/no from user) — otherwise leave as the
  documented permanent exception.

## [OPEN] FU-008 — Unify dialog chrome via BaseDialog `title`/`#actions` slots
- **Raised:** 2026-06-05 (A3)
- **Type:** deferred job
- **What:** A3 migrated dialogs as a shell transform; each still carries its own
  header/footer markup. BaseDialog already exposes `title`/`closable`/`#actions`
  to standardise chrome.
- **Why deferred:** rewriting ~28 heterogeneous dialogs' internals is large and
  risky for a cosmetic-consistency gain.
- **Recommended resolution:** opportunistic — convert a dialog's chrome whenever
  it's being touched for another reason; no dedicated pass needed.

## [OPEN] FU-007 — Eyeball A3 modals in a real browser
- **Raised:** 2026-06-05 (A3)
- **Type:** leftover
- **What:** A3 was verified statically only — `node_modules` isn't installed in
  this checkout, so no lint / `quasar build` / dev-server run happened. Need to
  confirm backdrop+Esc dismiss without committing, and that the comparison /
  orphans / quick-add cards (scoped-class → `card-style` fix) still size right.
- **Why deferred:** can't run the app without installing deps.
- **Recommended resolution:** now-ish — once deps are installed / before signing
  off Wave A.

## [OPEN] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`; it currently sits at **~289
  plain `q-btn`** (+ 4 `q-btn-dropdown`, 6 `q-btn-toggle`) across ~40 files. This
  is **NOT part of the standard plan** — A2's prompt was scoped to *toolbar*
  buttons + "New X" placement only, and no other prompt covers the rest. So the
  remainder is a genuine unplanned leftover, captured here on purpose.
- **Breakdown / nuance (don't treat as one uniform job):**
  - **Inline list-row action buttons** — the bulk (recipe cards, stock rows,
    shopping-list lines, settings rows). Low visual impact, the main target.
  - **Products surface** (`MyProductsPage` ~20, `ProductSearch` ~18) — **skip
    these**: that surface is moving to the companion app (master Decision 1), so
    it's intentionally minimal-touch. Migrating them is likely wasted effort.
  - **`q-btn` in `q-input` append slots** (search-clear, copy-to-clipboard) —
    intentionally the minimal pop-out style; leave as-is.
  - **`q-btn-dropdown` / `q-btn-toggle`** — different APIs, out of BaseButton
    scope by design (see FU-005).
  - **`DoraChat` (~14)** — its own component; migrate only if DoraChat is being
    reworked anyway.
- **Why deferred:** out of A2's defined scope; high count, mostly low-impact, and
  a chunk of it (products) shouldn't be migrated at all.
- **Recommended resolution:** later — a dedicated low-priority pass *after* Wave A,
  explicitly excluding the products surface, q-input append buttons, and the
  dropdown/toggle variants. Or purely opportunistic (migrate a page's inline
  buttons whenever that page is open for other work). Not no-regret; not urgent.

## [OPEN] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages are out of BaseButton's
  scope (different APIs). A wrapper would unify split-buttons if there's appetite.
- **Why deferred:** different component API; not needed for A2.
- **Recommended resolution:** later — only if a design need arises; not no-regret.

## [OPEN] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Recommended resolution:** later — a clean-up before commercialise (Phase 4),
  or when a theme bug points back to the dual source.

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

## [OPEN] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Recommended resolution:** later during **C19** (shared auth-shell) — revisit
  the whole auth surface together.

---

# Resolved

## [RESOLVED] FU-001 — "Flat danger" BaseButton variant for low-emphasis deletes
- **Raised:** 2026-06-04 (A2 Phase 2)
- **Type:** follow-up
- **What:** A2 left flat-negative delete buttons as raw `q-btn` because BaseButton
  had no flat-danger shape.
- **Why deferred:** needed a new BaseButton variant.
- **State note:** RESOLVED 2026-06-05 — `danger-ghost` variant added
  (`{ flat: true, color: 'negative' }`) and wired into `StockItemDetailPage`
  (Delete + clear-expiry) and `MealPlansOverview` (Delete plan).
