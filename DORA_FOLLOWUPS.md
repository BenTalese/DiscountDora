# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

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


## [OPEN] FU-328 — Four pre-existing pytest failures (data_router / household_tz / product / recipe_is_planned)
- **Raised:** 2026-06-29 (FU-288 resolution — full-suite run uncovered a
  *different* set of failures than FU-288 originally named).
- **Type:** finding (pre-existing drift; confirmed on a clean stash).
- **What:** `./.venv/bin/pytest tests/` shows **4 failures, all pre-existing**,
  unrelated to the three profile-picture tests FU-288 named (those all pass
  now). Confirmed via `git stash` — they fail on clean HEAD too:
  - `tests/e2e/dora_api/test_data_router.py::test__chunked_upload__chunk_offset_mismatch__is_400`
  - `tests/e2e/dora_api/test_household_tz_boundaries.py::test__dashboard__upcoming_window_anchored_on_household_today`
  - `tests/e2e/dora_api/test_product_router.py::test__update_product__PriceNowAtZeroBoundary__IsBadRequest`
  - `tests/e2e/dora_api/test_recipe_is_planned.py::test__recipes__is_planned_true_when_future_unconsumed_entry_exists`
  Suite totals: 4 failed, 536 passed.
- **Why deferred:** out of scope of the FU-288 / FU-285 / FU-289 work unit
  (R-007); each failure belongs to its own feature area (data import,
  household-tz boundaries, product validation, planner-derived `is_planned`).
- **Recommended resolution:** opportunistic per area — when next touching
  data-import / dashboard upcoming-window / product validation / `is_planned`
  derivation, run that test first, see what it expects, and either fix the
  code or update the assertion. Don't bundle as one "fix the 4" job — each
  failure is its own story.

## [OPEN] FU-320 — Document every auto-behaviour in the in-app help and point at the setting that controls it
- **Raised:** 2026-06-28 (FU-092 magic-behaviour audit close-out).
- **Type:** documentation / discoverability.
- **What:** For every auto-behaviour catalogued in
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`, write a plain-
  English entry in the relevant in-app help section (Settings help,
  feature-specific help cards, onboarding tooltips — whichever
  surface owns the feature). Each entry:
  1. Names the behaviour ("When you mark an item Low, Dora may add
     it to your shopping list automatically").
  2. States the trigger and what changes ("…when you turn on
     *Auto-add when low* on the item, and you have exactly one
     draft list").
  3. **Links to the setting / toggle that controls it** so the user
     can turn it off, switch it, or read more — never just "the app
     does this" with no escape hatch.
  All 18 findings get coverage (including the (a)-keep-silent ones —
  the doc is the receipt that proves they're not hidden, even if no
  per-event surface fires). Audit table → help-section map should be
  spelled out in this FU's eventual implementation chunk.
- **Gate (HARD):** **do NOT start until all related FUs are
  resolved.** The related set is:
  - [[FU-315]] auto-add toast/chip verify
  - [[FU-316]] remembered-list toast + "always ask" setting
  - [[FU-317]] manual meal-plan reconcile proposal **and** its
    implementation chunks (the F5 area is the one where the help
    copy would change most after the new feature lands)
  - [[FU-318]] cheapest-pick chip
  - [[FU-319]] inline-create pantry toast
  Starting this work earlier than that means the help copy goes
  stale the moment one of those follow-ups lands (new toast wording,
  new setting toggle, new manual-reconcile surface to point at).
- **Why deferred:** documentation that describes a moving target is
  worse than no documentation. Wait for the surface decisions to
  settle.
- **Recommended resolution:** focused doc-writing pass once the gate
  clears — own its own prompt under `docs/03_prompts/`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` (the
  source-of-truth catalogue this FU documents into help).

## [OPEN] FU-319 — Toast "Added <name> to your pantry" on inline-create from the recipe ingredient picker (F9)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F9 — (b)).
- **Type:** UX / cleanup.
- **What:** The recipe ingredient `q-select` exposes a "Create '<typed>'"
  no-option entry that fires a POST to create a brand-new `StockItem`
  inline. The new item survives even if the user cancels the recipe save
  (verified during the audit). Add a small positive toast "Added <name>
  to your pantry" when that inline-create path fires so the user isn't
  surprised by a new tracked item on the next StockOverview visit.
- **Where:** `web_app/src/pages/RecipeDetailPage.vue:395` (the picker)
  and the create-stock-item handler the inline-create eventually calls.
- **Recommended resolution:** opportunistic — fold into the next cookbook /
  recipe-editor touch. 1–2 lines.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F9.

## [OPEN] FU-318 — "Cheapest" chip on shopping-list lines using the auto-picked offer (F7)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F7 — (b)).
- **Type:** UX / cleanup.
- **What:** When a line has no `selected_product_id`, the displayed
  price / store comes from `chosenOfferFor(line)` falling back to
  `offers[0]` (server pre-sorted cheapest-first). Render a small
  `cheapest` chip on those lines so the user can see *why* the price is
  what it is — removes the only "did I really pick that store?" surprise
  on the list. Don't render the chip when `selected_product_id` is set
  (user picked) or when the user has typed an `actual_unit_price`
  override (the price-source label takes precedence).
- **Where:** `web_app/src/pages/ShoppingListDetail.vue` line render +
  `web_app/src/models/shoppingList.ts:172` (`chosenOfferFor`); confirm
  the same fallback shape at
  `dora_api/features/shopping_lists/get_shopping_list_detail.py:108-110`.
- **Recommended resolution:** opportunistic — fold into the next
  shopping-list-detail polish pass. ~10 LOC.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F7.

## [OPEN] FU-317 — Proposal: manual meal-plan reconcile feature ("stocktake-mode for meals") + opt-in for auto-drain (F5)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F5 — plan-first).
- **Type:** proposal / design (no code yet).
- **What:** `reconcile_consumed_meals` is currently the heaviest implicit
  behaviour in the app — every dashboard / meal-plan / recipe read
  silently marks past-day plan entries as consumed and decrements the
  `Recipe.available_meals` pool. No receipt, no undo, no "did you
  actually cook this?" check.
  User wants this thought through before any code touches the
  reconcile path. The desired shape:
  1. **Per-user setting**, default **on**, for "auto-drain past-day
     plans". When off, past-day entries stay unconsumed until the user
     explicitly confirms them.
  2. **A new manual-reconcile feature** modelled on stocktake mode —
     its own page, its own surfacing (alert / dashboard chip), and a
     UX that **shows the user what *should* have been consumed** since
     they last reconciled, so they can confirm / amend per-entry
     before the pool decrements.
  3. Decide what happens to existing alerts (`no_planned_meals`, etc.)
     when manual-reconcile is overdue — does an "unreconciled meals"
     alert fire? At what severity?
  4. Decide whether auto-drain and manual-reconcile coexist (auto-drain
     decrements; manual-reconcile lets the user dispute / amend after
     the fact) or are mutually exclusive (off-by-default users never
     auto-drain; on-by-default users never reconcile).
- **Where to write:** new `docs/04_proposals/PROPOSAL_MEAL_RECONCILE.md`.
  Cross-cut feedback table at the end per the CLAUDE.md mandate.
- **Why deferred:** Charter-level UX call; needs a designed surface
  (page + alert + dashboard chip) before the implementation chunks make
  sense. The audit itself is FU-092's scope; the *feature* is not.
- **Recommended resolution:** focused design session — own its own
  prompt under `docs/03_prompts/`. Before any code touches
  `reconcile_consumed_meals.py` or the `before_request` hook in
  `startup.py:150`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F5 (+
  F6, which rides this decision).

## [OPEN] FU-316 — Quick-add "remembered list": per-add toast names the destination + "always ask" setting (F3)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F3 — combo (b)+(c)).
- **Type:** UX / cleanup + settings.
- **What:**
  1. Verify that the per-add toast names the destination list
     (e.g. "Added to *Sunday shop*", not just "Added") for the
     `useQuickAddTargetPick`-powered remembered-list path. If not,
     update the wording in `useShoppingListActions` (or wherever the
     toast fires).
  2. Add a per-user setting **"Always ask which list when I have
     more than one draft"**, default **off** (current behaviour
     preserved). When on, `useQuickAddTargetPick` either skips the
     `save()` step entirely or `clear()`s after every add so the
     picker fires every time.
- **Where:** `web_app/src/composables/useQuickAddTargetPick.ts` +
  `useShoppingListActions` (toast wording); per-user setting lives in
  Settings → Account.
- **Recommended resolution:** opportunistic — folds into a shopping-list
  polish pass.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F3.

## [OPEN] FU-315 — Verify auto-add-when-low toast + line indicator (F1)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F1 — (b) + line
  indicator).
- **Type:** verification / cleanup.
- **What:** When a stocktake update transitions a stock item to Low/Out
  and `auto_add_when_low` is on, the API returns `auto_added_line_id` +
  `auto_added_to_list_id` (see
  `update_stock_item.py:217-241`). Verify:
  1. The SPA reads those fields off the PATCH response and fires a
     positive toast naming the list ("Added <item> to *Sunday shop*").
     If the toast doesn't fire or doesn't name the list, fix it.
  2. The line's existing `added_via` chip on `ShoppingListDetail.vue`
     renders as **"auto: low stock"** for the auto_low_stock case
     (already wired in `addedViaLabel` at L2206-2222 of
     `ShoppingListDetail.vue`); confirm it's visible at normal density
     and doesn't get crowded out by other line chrome.
- **Where:** `dora_api/features/stock_items/update_stock_item.py` (server
  side already in place); SPA toast wiring on whatever surface PATCHes
  stock-item updates (`StockItemDetailPage.vue`, quick stocktake flows).
- **Recommended resolution:** browser-verify pass — pair with the next
  stock-item / shopping-list smoke.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F1.

## [OPEN] FU-314 — Retire grandfathered `lazy="selectin"` overrides on `Recipe.cuisine` / `.category`
- **Raised:** 2026-06-28 (R-019 / ADR-014 adoption — "no magic" rule).
- **Type:** finding / engineering-standards cleanup.
- **What:** R-019 (the new "no magic" rule) calls out per-entity
  SQLAlchemy `lazy="..."` overrides as a flavour of magic — the read
  site no longer reflects what it loads. Two such overrides exist:
  `Recipe.cuisine` and `Recipe.category` were set to `lazy="selectin"`
  during C-4 Chunk 2 so the ~10 read sites didn't each need an
  `.include()`. ADR-014 grandfathers these (R-007 scope discipline)
  but flags them as a follow-up.
- **What to do:** flip both relationships back to the codebase default
  (`noload`); walk every read site that currently relies on the
  implicit load and add an explicit `.include(...)` / `selectinload(...)`
  at the query. Greppable starting points:
  `get_recipes.py`, `import_recipe_from_url.py`,
  `update_recipe.py`, `create_recipe.py`,
  `new_recipe_version.py`, plus anything else hitting
  `recipe.cuisine` / `recipe.category` after a `repository.get(Recipe)`
  call. Add a query-count test (FU-138 pattern) before & after to
  confirm we didn't trade one selectin for ten lazy-loads.
- **Why deferred:** out of scope for the rule-adoption session;
  R-007 — flag, don't drift.
- **Recommended resolution:** opportunistic — pair with the next
  cookbook / recipe-query touch, or do as a focused cleanup chunk.

## [OPEN] FU-313 — Designed token ladder for graded severity / heatmap palettes
- **Raised:** 2026-06-26 (FU-046 A1 theme-token regression sweep).
- **Type:** deferred job.
- **What:** four surfaces still ride Quasar's numbered palette because they
  encode a *graded* severity / heatmap, not a binary semantic — a single
  `negative` / `warning` doesn't carry the ordinal signal. Sites:
  - `web_app/src/models/alert.ts:144-169` — alert-severity gradient
    (red → orange → amber → deep-orange → purple → teal → indigo).
  - `web_app/src/models/location.ts:41-45` — location-heatmap palette
    (green → teal → amber → orange → red).
  - `web_app/src/pages/AlertsPage.vue:422-423` — `historyChipColor`
    state ladder: `'orange-7'` (snoozed), `'blue-grey-5'` (read).
  - `web_app/src/components/AddToListButton.vue:247` and
    `web_app/src/pages/StockItemDetailPage.vue:1635` — `'amber-9'`
    "needs attention" tones (inspect; likely the same shape).
- **Why deferred:** swapping these to a single semantic loses ordinal info, and
  picking N specific palette stops is a design decision, not a sweep. They need
  a designed token ladder — e.g. `--severity-1`..`--severity-5` (and a
  `--heatmap-1..N`) — defined in `web_app/src/style/tokens.scss` +
  `themes.scss` so each step is theme-aware in both light and dark, and a tiny
  `severityClass(level)` helper to map an ordinal to the right token-bound
  class.
- **Recommended resolution:** opportunistic — bundle with the next visual
  pass on alerts/heatmaps, or when an A-wave design brief touches severity UI.
- **State note:** (filled in when resolved)

## [OPEN] FU-304 — Meal planner rebuild: build both layouts (A + B) behind a toggle
- **Raised:** 2026-06-25 (`/design-critique` on the meal planner →
  `docs/04_proposals/IMPL_PLAN_MEAL_PLANS_REBUILD.md`).
- **Type:** deferred job.
- **What:** the brief diagnoses the planner's emergent sprawl (all-slots ×
  all-days + vertical carousel + non-sticky columns + centre-weighted grid).
  **Q1 RESOLVED (2026-06-25):** build **both** directions and keep them live
  behind a **temp desktop toggle** — upgrade the existing page to **Direction A**
  (de-sprawled carousel) and add a **separate page** for **Direction B** (desktop
  week grid). Shared state/logic; pick a winner later, then delete the loser +
  toggle. Canonical phasing is **§12** of the brief.
- **Progress (2026-06-25 PM):**
  - **R-Phase 0 closed** — Q2 (used-slots default), Q3 (gate behind batch
    posture), Q4 (bottom-sheet picker), Q5 (slot-as-tag, B page only),
    Q6 (server-enrich `MealPlanEntryDto`) all locked with the recommended
    option. Brief §11 updated to reflect resolutions. FU-179 still left to
    user (browser-verify).
  - **R-Phase 1 landed** — extracted `useMealPlanner()` composable +
    `MealPlanRecipePicker.vue` + `MealPlanWeekDayCard.vue` +
    `MealPlanShoppingSummary.vue`. `MealPlansOverview.vue` shrinks
    1,222 → 304 lines, behaviour-preserving. vue-tsc + eslint clean on the
    five changed files.
  - **R-Phase 2 landed (2026-06-25 PM, same session)** — Direction A
    upgrade: de-sprawled per-day slots (Q2) with calm "+ add a meal" +
    show-all toggle, sticky context columns, new
    `MealPlanWeekStatus.vue` strip, `MealPlanFirstRun.vue` hero,
    empty-week "Plan this week" banner, U7 destructive-button fix. Seven
    files changed/added; vue-tsc + eslint clean. Browser walk folded into
    FU-305.
  - **R-Phase 3 landed (2026-06-25 PM, same session)** — Direction B
    page + A/B toggle. Q6 server-enriched `MealPlanEntryDto` (4 new
    display fields + bulk-hydrated `has_image`).
    `MealPlanRichCard.vue` (slot-as-tag per Q5), `MealPlanWeekBoard.vue`
    (7-day grid with day-major default + group-by-slot alt view),
    `MealPlansBoardPage.vue` (top strip + sticky consequences bar +
    pinnable picker drawer + calendar-as-popover), and the
    `useMealPlannerView` persistence helper. New route
    `/meal-plans/board`. List/Grid toggle on both pages (desktop-only).
    13 files touched; vue-tsc + eslint + AST-parse clean. Browser walk
    folded into FU-305.
  - **R-Phase 4 landed (2026-06-25 PM, same session)** — shared mobile
    single-day focus. `MealPlanMobileFocus.vue` (day-strip + focused-day
    cards + collapsible week status) and `MealPlanPickerSheet.vue`
    (bottom-sheet picker). Both pages render the same focus at `lt.md`;
    A/B toggle gated to desktop only. Slot-as-tag rich card reused on
    mobile. Drag is force-disabled at the picker level on mobile (H7).
    vue-tsc + eslint clean.
  - **R-Phase 5 landed (2026-06-25 PM, same session)** — three cleanups:
    (a) Q3 batch posture gate end-to-end (User column + migration +
    `useBatchEnabled` + Settings → Preferences toggle + 5 component
    gates); (b) sequential builder rebuilt onto the shared picker
    (multi-select mode) + dead Email button hidden + build decoupled
    from generate-list; (c) `MealPlanTemplatesDrawer.vue` apply/manage
    drawer wired into both pages. 14 files touched + new Alembic
    migration `e4c7a2f9b5d3`. vue-tsc + eslint + AST-parse clean.
    The migration needs to run on the user's DB before the next
    backend boot.
  - **R-Phase 6 landed (2026-06-26)** — hierarchy + a11y + skeletons.
    Calmer status accents on entry chip + rich card (border + icon +
    aria-label, not saturated fill). Slot rows / day columns / week
    rows / calendar weeks promoted to real `<button>` with combined
    accessible labels. Global ArrowUp/Down nav scoped via
    `closest('button,a,select,…')` so it doesn't steal focus keys.
    New `MealPlanSkeleton.vue` (list / grid / mobile variants) +
    `useMealPlanner.isInitialLoading` ref render layout-shaped
    placeholders during the ~10 parallel mount loads. Calendar status
    text alternatives via `title` + aria-label close 1.4.1.
    9 files touched; vue-tsc + eslint clean.
- **Sequencing (resolved):** extraction-first — **R-Phase 1** pulls a
  `useMealPlanner()` composable + leaf components out of the current page
  (behaviour-preserving R-001) **before** the B page is created, to avoid a
  1,222-line duplicate that double-maintains mutation logic. **Done.**
- **Recommended resolution:** next session — **"pick a winner" cleanup**
  (live with both layouts; once A or B wins, delete the loser page +
  `useMealPlannerView` + the A/B toggle + any leaf components unused by
  the survivor). After that FU-304 itself closes.

## [OPEN] FU-308 — Fold the /meal-plans/templates manager into the drawer (or retire it)
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** follow-up.
- **What:** R-Phase 5's templates drawer covers the daily Apply / Rename /
  Delete / Save flow. The dedicated `/meal-plans/templates` page still
  exists and is reachable via direct URL — it shipped before the drawer
  and overlaps with the drawer for the basic CRUD. Once browser-verified,
  either (a) fold any unique-to-page features (e.g. bulk reorder, full
  description editing) into the drawer and retire the route, or (b) keep
  the page as the "heavy management" screen and add a clearer entry
  point on the planner pages (right now neither the A page templates
  card nor the B page Templates button links to it).
- **Why deferred:** R-Phase 5 explicitly scoped to the drawer (§9-E);
  reworking the dedicated page is its own assessment.
- **Recommended resolution:** opportunistic — at the "pick a winner"
  cleanup, decide if the manager page survives.

## [OPEN] FU-309 — Run the batch-posture migration before next backend boot
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** finding (operational debt — built static; no Python
  interpreter on this host).
- **What:** R-Phase 5 adds `User.batch_features_enabled` as a non-null
  column (migration `e4c7a2f9b5d3_20260625_user_batch_optin.py`). The
  GET `/api/users/me` handler reads it through `from_entity`, so a
  backend boot against an unmigrated DB will 500 on every
  authenticated call. Run `flask db upgrade` (or your equivalent) on
  local DBs before restarting the API. Existing users default to
  False ("fresh"), matching the Charter P10 Anti-creep choice.
- **Why deferred:** no Python interpreter on the session host;
  migration is static.
- **Recommended resolution:** **now**, before the next backend boot
  on any environment.

## [OPEN] FU-307 — Per-entry cookability on the Direction-B meal card
- **Raised:** 2026-06-25 (R-Phase 3 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the rich meal card on Direction B currently colours the left
  accent amber when the **recipe is in the cook-shortfall set** (the same
  signal the existing chip uses). It does **not** yet show "missing 3
  ingredients" / "ready to cook now" per entry. To do that the meal-plan
  query would need to include `MealPlanEntry.recipe.ingredients`
  (selectin-loaded), and the entry DTO would fold `missing_count_for(...)`
  + `cookable` through. The query expansion is modest but not free.
- **Why deferred:** §6.5 calls for status accent + tag, which the existing
  shortfall signal already drives; per-entry "what's missing" is the next
  precision step rather than a critical part of the card.
- **Recommended resolution:** opportunistic — when Direction B is named the
  winner and the cookability detail is wanted on the card. The same enrichment
  can flow into the A-page chip too (`MealPlanEntryChip.vue`).

## [OPEN] FU-306 — Persist "Show all slots" toggle across reload
- **Raised:** 2026-06-25 (R-Phase 2 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the new "Show all slots" toggle above the meal-plan carousel is
  currently a session-local `ref` — refreshing the page reverts to the
  used-slots default. For a household that *does* plan all five slots a day,
  re-flicking the toggle every visit is friction.
- **Why deferred:** the default (used-slots) covers the dominant case
  cleanly. A genuine multi-slot household will tell us; pre-emptively
  wiring a household preference is small but not free (settings UI + a new
  pref column).
- **Recommended resolution:** opportunistic — when adding the next batch of
  household preferences, lift `showAllSlots` into the household
  `Preference` table (or a small local-storage cache if the call is "this
  is purely a per-device view choice").

## [OPEN] FU-302 — Dora Score reassessment: waste-as-pillar weight
- **Raised:** 2026-06-24 (C-waste design — `PROPOSAL_WASTE_MINIMISATION.md`).
- **Type:** finding
- **What:** `DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447 treat waste as one of four Dora Score pillars ("low waste, on-budget, fresh, few run-outs"). The C-waste design deliberately de-emphasises waste as a UI feature — the `/waste` page is deleted, the capture flow shrinks to a single row dropdown action with no money/note capture, no Reports card. The *signal* is preserved (events still logged + queryable) so the Score can read it. But the de-emphasis is a quiet vote that the Score model itself may want re-weighting — perhaps waste shrinks to a smaller pillar, or merges with another (e.g. "fresh + low-waste" → one freshness pillar). This is a **charter-level** decision, not a UI cleanup, and was explicitly out of scope for C-waste.
- **Why deferred:** the Score isn't designed yet (Phase 3 / champion phase); doing the weighting now would be speculative. Better to revisit when the Score model is being built and the full pillar picture is on the table.
- **Recommended resolution:** later during pre-Phase 3 (when the Dora Score model is actually being designed; the reassessment is an input to that design, not its own deliverable).

## [OPEN] FU-300 — Dashboard quick actions: add "Log price" (needs a product target)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up.
- **What:** the Phase-5 quick-action bar ships **Add item** (CreateStockItemDialog)
  and **Add to list** (QuickAddSheet). Decision §9 also listed **Log price**, but a
  standalone log-price action has no obvious target (price is logged against a
  specific product/stock item) — it needs an item/product picker first.
- **Why deferred:** unclear UX without a target picker; the other two quick actions
  delivered the "home screen does, not just routes" value.
- **Recommended resolution:** opportunistic — add a Log-price quick action that
  first picks a stock item (reuse the QuickAddSheet search) then opens the existing
  `PriceEntry` flow.

## [OPEN] FU-299 — Dashboard stock donut: deep-link buckets to filtered /stock
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up (enhancement) — was slated as a Phase-5 item.
- **What:** the critique wanted the Pantry donut's low/out segments to deep-link to
  a filtered stock view (`/stock?status=low|out`). The donut card is currently a
  whole-card link to `/stock`. `StockOverviewPage` has **no status query-param
  filter**, so the deep-link target doesn't exist yet.
- **Why deferred:** adding query-driven filtering to the stock overview is out of
  the dashboard's scope (R-007).
- **Recommended resolution:** when touching the stock overview — add `?status=`
  query support there, then de-clickable the donut card and link each legend
  row/segment to the matching filtered view.

## [OPEN] FU-296 — Dashboard "price drops" widget (needs server "new low" signal)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 4).
- **Type:** deferred job.
- **What:** the Money-zone **price-drops** widget (§2.4) — tracked products at a
  genuine new low / recent drop — was **not built**. Savings / spend / pantry
  value shipped (existing reports endpoints), but price-drops needs a new
  server-side "new low since last seen" signal (Honesty: the claim must be true)
  that doesn't exist yet, plus the product-data-presence gate (the `gate:
  'products'` seam + `cardAvailable` are already in place for it).
- **Why deferred:** requires a new backend endpoint (price-history analysis) that
  can't be built+verified without a Python env here; the other three Money
  widgets delivered the phase's value on existing endpoints.
- **Recommended resolution:** when on a Python-capable machine — add a
  `/reports/price-drops` (or extend price-trends) endpoint returning products at
  a new low, then add the `price_drops` card (zone 'money', `gate: 'products'`,
  `defaultHidden: true`) consuming it.

## [OPEN] FU-295 — Confirm the Alerts page (D5) no longer 404s
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 3).
- **Type:** finding (reported defect, static-only verification).
- **What:** feedback D5 reported "Alerts navigation is broken (goes to 404)". A
  static read shows the `/alerts` route IS registered (`routes.ts` →
  `pages/AlertsPage.vue`, the C-9 control surface), so it appears fixed — but a
  static read is not proof.
- **Recommended resolution:** the verify itself is tracked in `DORA_VERIFY.md`
  under "Dashboard rebuild" (it's the same click that exercises the Phase-3
  alert card → `/alerts` link). Close this FU once that pass is green.

## [OPEN] FU-327 — Windows + macOS desktop build scripts for the Piper bundle
- **Raised:** 2026-06-24 (Piper platform audit). Renumbered from FU-288
  on 2026-06-29 to resolve a ledger numbering collision (two open items
  shared FU-288 — this build-script one and a separate profile-picture
  test-fix item; the latter took FU-288 and was resolved that day).
- **Type:** deferred job.
- **What:** `packaging/build-linux.sh` is the only platform build script. The
  spec (`dora.spec`) is platform-agnostic, but the Piper binary fetch
  (`packaging/fetch_piper.py`) only runs when invoked explicitly, and the
  default-voice fetch (`packaging/fetch_default_voice.py`) ditto. A Windows
  desktop bundle needs `build-windows.bat` (or PowerShell) that runs the same
  three steps in order — `fetch_piper.py --platform windows_amd64`,
  `fetch_default_voice.py`, then `pyinstaller dora.spec`. macOS needs
  `build-macos.sh` for both arm64 and x86_64 (separate runs).
- **Why deferred:** the dev machine for this session is Linux; can't smoke
  Windows / macOS builds without runners. The fetch script already has
  `_ASSETS` entries for all three platforms — only the orchestration is
  missing.
- **Recommended resolution:** opportunistic — first time a Windows or macOS
  release is needed. Until then the Linux + Docker artifacts are the shipped
  paths and they're complete.

## [OPEN] FU-287 — iOS / WKWebView autoplay across an `await` for Piper synth
- **Raised:** 2026-06-24 (Piper platform audit).
- **Type:** finding (real cross-platform constraint, not a regression).
- **What:** iOS Safari (and the macOS WKWebView the desktop bundle uses on
  Mac) enforce a strict user-gesture rule for `HTMLAudioElement.play()`. The
  gesture-permission "credit" is consumed the first time `play()` is called
  after a user interaction — and crucially, it can be **revoked** by an
  intervening `await` that spans more than a few hundred ms. Two flows
  affected:
  - `DoraChat.vue:1061` — user sends → LLM round-trip (`await`) → reply →
    `speechOut.speak(reply.text)` → `await ttsApi.synthesizeAsync()` → new
    `<audio>` → `await audio.play()`. On iOS, after the LLM round-trip + the
    synth fetch the gesture token is often gone. Browser-voice fallback
    (`SpeechSynthesis`) is subject to the same rule but is more forgiving —
    not a guaranteed fix.
  - `RecipeCookMode.vue:923, 1222-1228` — timer-fired narration. No gesture
    at all; the timer callback is not a user activation.
  This is not a regression — the cook-mode timer narration already had the
  same problem on the pre-Piper SpeechSynthesis path. Piper just adds one
  more `await` (the synth fetch) before `audio.play()`, making the gate
  fractionally easier to hit on chat replies.
- **Why deferred:** needs iOS device testing + a small refactor to add a
  silent-audio unlock primer. The current code is correct on every other
  platform.
- **Recommended resolution:** when the user reports voice failing on iPhone,
  OR opportunistic with the FU-283 browser walk. Fix shape:
  - Add a one-time `unlockAudio()` to `useSpeechOutput`: on the first user
    interaction (router init or a global `pointerdown` listener), play a
    silent / muted audio buffer to claim the gesture credit. Subsequent
    network-trip `audio.play()` calls then inherit it.
  - Alternative: keep a single long-lived `<audio>` element rather than
    creating one per utterance; iOS treats reused elements more leniently.
  - Document the timer-narration limitation in `RecipeCookMode.vue` (it
    already half-acknowledges it at line 944).

## [OPEN] FU-287 — Cross-app undo off after dashboard "push expiry"
- **Raised:** 2026-06-23 (Dashboard `/design-critique` pass).
- **Type:** finding.
- **What:** feedback L480 — "Undo cross-app seems off, e.g. dashboard push
  expiry, then go to stock item and clear its expiry." An undo/toast initiated
  on the dashboard alert action doesn't behave correctly once you navigate to
  the stock item and mutate the same field. Marked **out-of-scope** in
  `IMPL_PLAN_DASHBOARD_REBUILD.md` §5 — it's an undo/toast-ownership defect, not
  a dashboard-design item.
- **Why deferred:** belongs to whoever owns the cross-app undo/toast mechanism,
  not the dashboard rebuild scope (R-007).
- **Recommended resolution:** confirm in browser, then route to the undo/toast
  owner (likely the global notify/undo layer).

## [OPEN] FU-284 — settings mobile nav still horizontal-scroll fallback (Phase 5 owes top tab strip)
- **Raised:** 2026-06-23 (Settings rebuild Phase 3).
- **Type:** deferred job.
- **What:** §6.3 was resolved as **top tab strip** but Phase 3 only ships the
  desktop shell + a `flex-direction: row; overflow-x: auto` fallback on
  `<1024px`. The real implementation (three top tabs → chip strip with the
  selected group's sub-items) is owned by Phase 5.
- **Why deferred:** Phase 3 owns desktop visuals only; mobile is a dedicated
  phase that also revisits SettingsSection row collapse + theme grid + the
  DoraSegmented overflow shape.
- **Recommended resolution:** later during Phase 5 (mobile pass).

## [OPEN] FU-229 — reports.py spend-by-store ignores `actual_unit_price` (ladder divergence)
- **Raised:** 2026-06-22 (FU-227 chunk 5 — K2 ladder extract).
- **Type:** finding (behaviour inconsistency).
- **What:** the K2 extract collapsed the **actual→picked** ladder
  (`line_paid_unit_price`) across `budget.py`, `waste.py`, `assistant/tools.py`
  and `suggestions/generators.py`. `reports.py` was on the plan's K2 list but
  does **not** apply that ladder: its spend-by-store (`reports.py:~354`) and
  savings (`SavingsCapturedHandler` ~746) handlers use SQL column projection of
  `picked_offer_price` only and never reference `actual_unit_price`.
  - Savings (`list_price_at_pick − picked_offer_price`) is **correctly**
    snapshot-based — it measures RRP-vs-committed-offer, not what you paid. No
    change wanted there.
  - **Spend-by-store**, though, is "what did I spend" and arguably should prefer
    `actual_unit_price` when set, to match budget/waste/assistant. Today a
    user's till-receipt override is invisible to spend-by-store.
- **Why deferred:** folding `actual_unit_price` into the SQL projection changes
  report numbers — a behaviour change beyond chunk-5 scope (R-007), and not
  ratified by the user. The ladder helper operates on entity objects, not the
  column-projected rows these queries return, so it's not a drop-in.
- **Recommended resolution:** opportunistic — next reports pass or the Postgres
  migration (FU-045) when these queries get revisited. Decide explicitly whether
  spend-by-store should prefer actual paid; if yes, project `actual_unit_price`
  alongside and COALESCE in SQL (or load entities and reuse `line_paid_unit_price`).

## [OPEN] FU-228 — Phase E rename test rot: ~53 tests still use `merchant` / `purchased_merchant_id`
- **Raised:** 2026-06-22 (FU-227 chunk 1 — surfaced when running full pytest).
- **Type:** finding.
- **What:** the Phase E `merchant → store` rename missed several test files. Failing tests
  consistently fail with `unexpected keyword argument 'purchased_merchant_id'` /
  `'merchant' Extra inputs are not permitted` (Pydantic `extra="forbid"` on the renamed
  models). Affected (non-exhaustive):
  - `tests/test_shopping_list_totals.py` (~8 tests; the `_line()` helper builds
    `ShoppingListLineDto(... purchased_merchant_id=...)`)
  - `tests/e2e/dora_api/test_product_router.py` (~6 tests for `update_product` /
    extra-attrs / price-now-without-price-was — all using the old `merchant` shape)
  - `tests/e2e/dora_api/test_ingest_batch.py::test__ingest__unknown_store_quarantines`
    (uses `merchant: 'MysteryStore'` in the ingest payload — renamed to `store`)
  - plus other product-router cases (53 total failures observed; not all itemised).
- **Why deferred:** R-007 scope discipline. Chunk 1 of FU-227 is a unit-conversion
  refactor; sweeping a rename across all test files belongs in a dedicated tidy-up unit.
- **Confirmed pre-existing** by `git stash`-then-run — baseline = 54 failed; mine = 53
  failed (one deselected). My changes introduced **zero** new failures.
- **Recommended resolution:** opportunistic during the next backend pytest pass on a
  Python-equipped env. The fix is mechanical (s/`purchased_merchant_id`/`purchased_store_id`/g,
  s/`merchant=`/`store=`/g, s/`'merchant': /'store': /g) — but should be verified test-by-test
  in case any case depends on the surrounding context. A single PR titled "Phase E rename:
  finish the test-suite update" would be clean.
- **2026-06-22 (chunk 6) update — full pytest now runs (real Python 3.11.9 on this box).**
  Confirmed baseline 55 failed / 7 errors at pristine HEAD; current 54 failed / 0 errors.
  The 54 remaining are all this rename rot, in: `test_merchant_router` (16),
  `test_product_router` (18), `test_shopping_list_totals` (8), `test_ingest_batch` (6),
  `test_ingestion_store_mappings` (4), `test_preferred_buys` (2). **Separately**, the
  7 errors + 1 failure at baseline were *chunk-5* fallout (NOT rename rot): the
  `PATCH status=done` removal broke `test_finish_harvest::test__patch_status_done`
  (asserted 400, handler returns 422) and `test_primary_target_inference`'s `fresh_state`
  fixture + hint-invalid test (archived lists via `status=done`). Those are **fixed** in
  chunk 6 (test-only). So this FU-228 backlog is now purely the rename rot above.


## [OPEN] FU-226 — Assess the new stocktake-queue rules (history vs. current vs. desired)
- **Raised:** 2026-06-19 (Stock Overview bulk + stocktake feedback round)
- **Type:** finding (UX policy — needs user judgement)
- **What:** Round-18 swapped the stocktake queue's filter from "anything overdue
  surfaces" to a stricter engagement-based rule. The user wants this written down
  so they can sit with it and decide whether it's right, looser, or stricter
  before any more code lands.

### What it WAS (pre-round-18)

  In `dora_api/features/stocktake/stocktake.py::get_stocktake_queue`:

  An item entered the queue when **both** were true:
  1. `stocktake_alerts_are_enabled == True` (per-item manual opt-out).
  2. `_compute_overdue(item) > 0`, where overdue is:
     - **`9999`** if `last_checked_at is None` (never-checked sentinel — items
       always surfaced as "maximally overdue").
     - Otherwise: `max(0, days_since_last_check − days_until_stocktake_alert)`.
       The per-item cadence is `days_until_stocktake_alert` (default 14, set on
       create).

  Ordering: most-overdue first → oldest `last_checked_at` → name.

  Pain point the user reported: a freshly-created stub item ("nachos I don't
  really keep in stock") immediately landed at the top of the queue because
  it'd never been checked → 9999 overdue. Dora pestered the user about every
  item they'd ever typed into the system, including items they'd long ago
  decided not to manage.

### What it IS NOW (round-18, 2026-06-19)

  Same two existing gates (per-item opt-out + `overdue > 0`), PLUS a new
  **engagement gate** that runs before either. An item must show ≥1 sign the
  user actually manages it:

  1. `is_flagged` (Essential) **or** `auto_add_when_low` — explicit "this
     matters" flags.
  2. Currently in stock — `stock_level.sequence < OUT_OF_STOCK_SEQUENCE`.
  3. Ever opened — `opened_on is not None`.
  4. Level was changed at least once — any `StockLevelChange` row exists for
     this stock_item_id. (The history table only grows when a level actually
     moves, so this distinguishes "never touched" from "touched once and back
     to default".)
  5. On any shopping list, ever — any `ShoppingListLine` row references this
     stock_item_id, regardless of list status (active or done).

  Signals 4 + 5 are bulk-fetched in one DISTINCT query each, so the queue
  endpoint stays cheap on big pantries.

  The `9999` never-checked sentinel is **kept**. The intent: engaged-but-
  never-checked items (essential / on a list / in-stock / etc.) still surface
  first; the engagement gate just stops the queue from drowning in unengaged
  stubs.

### Things to weigh when assessing

  - **False negatives** — items the user DOES care about but that fail every
    engagement signal. Likeliest case: an item that's normally well-stocked
    but is genuinely depleted right now, and the user never opened it (not a
    sealed product they "open"), never flagged it essential, never put it on
    a list, never moved the level. Possibly: a recurring seasonal item the
    user wants to be reminded to restock but hasn't engaged with recently.
  - **False positives** — items that pass engagement but shouldn't really
    nag. Likeliest case: items that were on ONE shopping list once five
    months ago and have been ignored since. Signal 5 ("ever on a list") is
    intentionally permissive — should it be "on a recent list" instead?
    (e.g. last 60 days.) Trade-off: DB needs a join on list lifecycle
    timestamps; not free.
  - **Tuning knobs to consider**:
    - Time-bound the "on a list" signal (last N days).
    - Time-bound "level was changed" similarly (only count level changes in
      the last N days as engagement).
    - Add a "snooze for N days" affordance on the queue row so the user can
      mute individual items without flipping the binary `stocktake_alerts_
      are_enabled` flag.
    - Replace the global cadence with a smarter default (e.g. shorter for
      essentials, longer for "in-stock but lots of headroom" items).
    - Promote `stocktake_alerts_are_enabled` from "manual opt-out only" to
      "auto-set false when engagement decays past N days" so the data
      self-cleans.
  - **No-change cost**: if the round-18 rule turns out to be roughly right,
    the only required follow-on is the browser-verify pass (FU-222 covers
    the SPA side; this rule lives in the backend and wants its own dataset
    walk-through).

- **Why deferred:** the user explicitly wants to sit with this and decide
  later. No code change pending here yet — this entry is the substrate for
  that decision.
- **Recommended resolution:** opportunistic — re-open when the user has
  walked their pantry through the new queue and decided whether the
  engagement rule is too tight, too loose, or right.

## [OPEN] FU-224 — App-wide colour-usage assessment (primary vs secondary vs accent)
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** deferred job
- **What:** During the feedback pass the user noted that the open / in-use button on the
  Stock Overview row was using `secondary` and was hard to see in Pesto dark — that fix
  landed by promoting to `primary`, but the user flagged that the broader pattern
  ("majority primary usage; not sure where secondary actually pulls weight") may need a
  separate audit. Walk the app, list every place `color="secondary"` (and other lower-used
  semantics like `info`, `accent`) appears, decide which deserve to stay vs. which should
  consolidate to `primary` or theme tokens for visual hierarchy reasons. Likely outputs:
  a short proposal under `docs/04_proposals/` + targeted fixes.
- **Why deferred:** intentionally out of scope for the feedback pass (R-007). The user
  explicitly called it out as a separate task to think about.
- **Recommended resolution:** opportunistic — fold in next time a theming/styling pass
  comes around, or after FU-046 (theme-token compliance) gets another round.

## [OPEN] FU-189a — `create_product` still auto-creates a Store when the name is unknown
- **Raised:** 2026-06-18 (Phase E rename)
- **Type:** finding — known carve-out
- **What:** `dora_api/features/products/create_product.py` retains the
  legacy auto-create-when-missing behaviour for `Store` (the manual product-add
  path's existing posture). The runbook's strict "no auto-create" rule was
  tagged for FU-190 (the ingestion path enforces it; ingestion correctly
  quarantines unknown store names). For consistency the manual path should
  eventually require an existing `Store` too.
- **Recommended resolution:** later — pair with FU-190 (ingestion store-mapping)
  so the whole "stores are user-curated, never auto-created" rule lands in one
  pass and the SPA's product-create UI gets a store picker at the same time.

## [OPEN] FU-220 — Repurpose `OnboardingLoop` in Help + consider menu re-ordering
- **Raised:** 2026-06-17 (FU-210 revisit — user direction)
- **Type:** follow-up (UX + IA)
- **What:** With the cinematic Story still alive (FU-210 revisit kept the hero loop there) and
  the Finish-step recap dropped, the loop is "a nice reminder of how to use the app." Find a
  durable home for it in **Help** so first-run users can revisit it after onboarding without
  rerunning the wizard. Two open IA questions to chew on at the same time:
  (a) **Help section order.** Should the Help sections be ordered in the loop's flow
      (Stock → Plan → List → Shop → Restock → Cook), so newcomers can read the help in the same
      order they'll actually use the app?
  (b) **Main menu order.** Same question for the left-nav: do the buttons map cleanly to the
      loop today? If not, is reordering worth doing — or is the loop's order aspirational
      and the menu's pragmatic (cookbook + recipes are nouns, not steps)?
- **Why deferred:** out of scope for the FU-210 revisit; needs a small Help-IA design pass
  (touches `HelpPage.vue` / `helpSections.ts` / nav). Not blocking.
- **Recommended resolution:** opportunistic / before commercialise (Phase 4). Keep the loop
  component (`OnboardingLoop.vue`) usable in non-onboarding contexts when you tackle this —
  it currently lives under `components/onboarding/`; consider promoting it to a more general
  location if Help also uses it (e.g. `components/dora/AppLoopDiagram.vue`).

## [OPEN] FU-213 — Price substrate: `StockItemPriceObservation` + server cost helper + consumers
- **Raised:** 2026-06-17 (products-as-overlay pivot — carried from the now-resolved FU-182)
- **Type:** deferred job (build)
- **What:** Land `StockItemPriceObservation(stock_item_id, price, qty, unit, observed_at, source)`
  (per-unit derived server-side — the user enters total + qty) + the server-owned
  `get_stock_item_unit_cost_at(stock_item, when)` helper (R-003), and rebase the two most-affected
  consumers (stock-value report fallback, recipe cost estimate) onto it. Gated by the **Money**
  opt-in (not products). No merchant attribution in the everyday layer. This is
  PROPOSAL_SIMPLE_MODE §2.1's substrate, carried forward intact.
- **Why deferred:** doc pass first; depends on the Money opt-in surface.
- **Recommended resolution:** Phase 1 loop / Phase 3 polish. Design:
  `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.2 (+ surviving PROPOSAL_SIMPLE_MODE §2.1).
- **Update 2026-06-17 — CORE code-complete (static-only).** Built the substrate end-to-end:
  `StockItemPriceObservation` entity + table + map + migration `b3d5f7a9c2e4`; the server-owned
  `get_stock_item_unit_cost_at` helper (`domain/stock_status.py`, R-003); CRUD
  (`/stock-items/{id}/price-observations`); `price_observations` + `unit_cost` on the detail DTO; a
  **money-gated "Prices" section** on the detail Overview (`useMoneyEnabled()`). **Deferred → FU-216:**
  rebasing the stock-value report + recipe cost estimate onto the helper (+ the product-derived cost
  branch). **Verify:** pytest (CRUD + unit-cost) + migration up/down + `vue-tsc`/eslint + browser
  (log/remove a price; section hidden when money off).
- **Update 2026-06-17 — backend GREEN.** Phase A env-verify:
  `tests/e2e/dora_api/test_price_observations.py` 4/4 (add → derived unit_cost=3 on 6/2, latest-wins,
  delete clears, non-positive rejected). Migration `b3d5f7a9c2e4` applies clean. `vue-tsc` + `eslint`
  clean. **Browser pass still pending** (log/remove + money-gate visibility).

## [OPEN] FU-211 — `PreferredBuy` — everyday free-text "what I buy" on the stock item
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** deferred job (build — new feature)
- **What:** New `PreferredBuy(id, stock_item_id FK cascade, label free-text, position, created_at)`
  table + migration. **Always-available** everyday construct (NOT gated by products or money) — a
  short list of free-text labels per stock item (e.g. "Vitasoy Oat Milky 1L") as a memory aid +
  shopping hint. Surface: a "Preferred buys" section on Stock Item Detail (add/edit/delete/reorder).
  Shopping-list hint: `ShoppingListLine.preferred_buy_id` (nullable FK, SET NULL), shown as
  selectable hint text on the line, **no pricing/product semantics**. Strictly separate from
  `Product` (no upgrade/demote bridge — the "two separate systems" principle).
- **Why deferred:** doc pass first.
- **Recommended resolution:** **Phase 0/1** — independent of the gate work; can land alongside
  FU-209/210. Design: `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.1.
- **Update 2026-06-17 — CORE code-complete (static-only).** Built the stock-item surface end-to-end:
  `PreferredBuy` entity + table + map + migration `a2c4e6f8b1d3`; CRUD at
  `/stock-items/{id}/preferred-buys` (add/rename/delete/reorder); `preferred_buys` on the detail DTO;
  model + API service methods; the "Preferred buys" editor on the detail Overview (add / inline
  rename / up-down reorder / remove via `withBusyReload`). Not executed (no env). The **shopping-line
  hint** (`ShoppingListLine.preferred_buy_id`) is split to **FU-215**. **Verify:** pytest + migration
  up/down + `vue-tsc`/eslint + browser (add/rename/reorder/remove; CASCADE on item delete).
- **Update 2026-06-17 — backend GREEN.** Phase A env-verify:
  `tests/e2e/dora_api/test_preferred_buys.py` 5/5 (add→detail, rename, delete, reorder, blank
  rejected, cross-item scope). Migration `a2c4e6f8b1d3` applies clean. `vue-tsc` + `eslint` clean.
  **Browser pass still pending.**

## [OPEN] FU-210 — Onboarding de-persona: remove persona fork + all product framing
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** deferred job (build — a *removal*)
- **What:** Remove the C-5.3 **persona fork** (Cooking/Spend/Everything) and the `products_enabled`
  dimension it set; remove **all product framing** + the **stock-vs-product explainer** from
  onboarding (the everyday user never meets products). **Keep** the structural C-5 chunks (cinematic
  intro, hero loop, starter packs, household headcount, finish celebration) but **un-personalized** —
  drop the C-5.2 persona preview + C-5.6 persona-relevant tailoring; show the full loop + full card
  set. **Money/budgeting becomes a Settings toggle only** (decided with the user) — onboarding shows
  the feature exists, no fork/forced choice. NB: the persona fork + flag have **already shipped**, so
  this is a removal, not just a plan edit.
- **Why deferred:** doc pass first; sizeable frontend change.
- **Recommended resolution:** **with/after FU-209** (the flag drop). Design:
  `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §5; supersedes parts of `PROPOSAL_ONBOARDING.md`
  / `IMPL_PLAN_ONBOARDING.md`. Re-validate onboarding sell-copy (FU-184) after.
- **Update 2026-06-17 — persona FORK removed, code-complete (static-only); illustrative PREVIEW
  deferred.** Removed from `WelcomeWizard.vue` + `onboardingContent.ts`: the persona step,
  `personaChoice`/`customFlags`/`effectiveInstallFlags`, `selectPersona`/`applyPersona` (no more
  install-flag / per-user-pref writes at onboarding), the `AppSettingsApiService` use, and
  `PERSONA_PRESETS`/`INSTALL_FLAG_META`/`InstallFlags`/etc. Flow-cards no longer gate on persona
  flags. Repo grep confirms **zero dangling refs**. Fresh installs now use `AppSetting` defaults +
  enable features in Settings (money is its own Settings toggle). **Still OPEN for:** (a) remove the
  **illustrative hero-loop persona preview** (`OnboardingLoop.vue` + `OnboardingStory.vue` +
  `personaPreview` + `PERSONA_PREVIEWS`) — do it with a running app so the loop renders well without
  persona shaping; (b) **browser-verify** (no persona/Customise/products step; defaults applied;
  spend via Settings; draft resume) + `vue-tsc`/eslint.
- **Update 2026-06-17 — TAIL DONE (static).** Removed the cinematic Story/Loop intro and the Finish
  step's loop recap. Deleted `OnboardingLoop.vue`, `OnboardingStory.vue`, `OnboardingScene.vue`, and
  `onboardingContent.ts` (`PERSONA_PREVIEWS`, `PersonaPreview`, `DEFAULT_PERSONA_PREVIEW`,
  `PersonaPreviewKey`, `NARRATIVE_SCENES`, `LOOP_STAGES`, `LOOP_CENTRE`, `LOOP_INSIGHT` — all
  unreferenced after the removal). `WelcomeWizard.vue` stripped: `view`/`storySceneIndex`/
  `personaPreview` refs gone, draft persistence simplified, rail collapses to the single Setup
  section. `vue-tsc` + `eslint` clean; full backend pytest **401/401** still green. **Still OPEN
  for browser-verify only** — the wizard's behaviour change is FE-only and needs a running app to
  confirm the flow reads sensibly + draft resume works.
- **Update 2026-06-17 — TAIL was MIS-INTERPRETED. Partially reverted via direction from the user.**
  The above "TAIL DONE" pass deleted too much. Restored from `git checkout 941d478^ --`:
  `OnboardingLoop.vue`, `OnboardingStory.vue`, `OnboardingScene.vue`, `onboardingContent.ts`,
  and the pre-removal shape of `WelcomeWizard.vue` (Story stage + Setup view + persona-preview
  state + draft persistence). Then made the **actually-intended** edits:
  - `onboardingContent.ts` — stripped `LOOP_INSIGHT` (dimmed "Spend smarter / coming soon"
    satellite, P3-Honest violation since it advertised an unbuilt feature); re-framed
    `PERSONA_PREVIEWS` labels from persona identities ("Cooking" / "Spend" / "Everything") to
    outcome chips ("Mostly cooking" / "Watching spend" / "All of it"). Keys unchanged so any
    draft state survives. Dropped the now-unused `insight: boolean` field on `PersonaPreview`.
  - `OnboardingLoop.vue` — removed the LOOP_INSIGHT satellite button + its `focusedKey === 'insight'`
    branches + the `lightbulb` mood swap + the dead `.loop-insight*` CSS. Re-worded the persona
    preview's aria-label + chip header from "Preview for / persona" to "What you're here for".
  - `WelcomeWizard.vue` Finish step — removed the OnboardingLoop recap ("Here's the loop you just
    set up — tap any stage…"); the cinematic Story still plays the hero loop earlier so the recap
    was repetitive. Confetti + flow-cards kept.
  - The cinematic Story stage stays **as-is** (un-persona scene visuals were already the case —
    `NARRATIVE_SCENES` doesn't fork by persona).
  - The persona FORK in setup (removed in the earlier pass) **stays removed** per user direction.
  - Loop-in-Help + main-menu/help-section reordering → **FU-220**.
  - **Verified:** `vue-tsc --noEmit` clean; `npm run lint` clean; full pytest **401/401** green.
  - **Still OPEN for browser-verify** — confirm Story plays without LOOP_INSIGHT, the renamed
    chips read sensibly, Finish step is clean, draft resume still works.

## [OPEN] FU-208 — My Products → stock-item "Link…" flow is a silent dead-end
- **Raised:** 2026-06-17 (products-as-overlay pivot — code investigation)
- **Type:** finding (bug)
- **What:** `web_app/src/pages/MyProductsPage.vue` routes its "Link…" action to
  `/stock/{id}?link_product_id=<pid>&section=products`, but **nothing consumes `link_product_id`** —
  C-1b.3 removed the saved-products picker dialog from `StockItemDetailPage.vue` (and its
  `onLink`/`openProductPicker` handlers) per R-008, leaving the My-Products entry point routing to a
  handler that no longer exists. Result: pick a stock item → Link → land on the Products tab → the
  product is **not linked**, no error. Static read confirms zero consumers of `link_product_id`. Per
  CLAUDE.md, logged even though static-confirmed — verify in browser.
- **Why deferred:** belongs with the products-as-overlay build, not the doc pass.
- **Recommended resolution:** **with FU-209** — rebuild a working link path (consume
  `link_product_id` on detail, or link in place via `POST /api/stock-items/{id}/products`). Link
  pre-existing (ingested) products only — do NOT rebuild manual product creation. Design:
  `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.2. **Confirm in browser.**
- **Update 2026-06-17 — code-complete (static-only).** `MyProductsPage.vue` `confirmLink()` now
  links in place via `stockItemApi.linkProductAsync` (`POST /stock-items/{id}/products`) + `loadAll()`
  + a toast, instead of the dead `link_product_id` navigation. **Keep OPEN until browser-verified:**
  from My Products, "Link…" → pick stock item → the product links and shows as linked (no bounce),
  error toast on failure.
- **Update 2026-06-29 — static re-verified.** Confirmed
  `MyProductsPage.vue:1013` `confirmLink()` posts to
  `/stock-items/{id}/products` via `linkProductAsync`, reloads, and toasts.
  Repo-wide grep for `link_product_id` returns only the doc comment at
  `MyProductsPage.vue:984` (no other consumer; no dead nav remains). The
  endpoint exists at `link_product_to_stock_item.py:104`. **Still OPEN —
  CLAUDE.md mandate: only flip to RESOLVED once the click-through has been
  exercised in a running browser.** Folds into the next stock / products
  smoke session.

## [OPEN] FU-200 — Admin bootstrap is a fiction: first registrant becomes self-verified admin
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (security, HIGH)
- **What:** `register_user.py:159` `is_first_user = repo.get(User).count() == 0` → `:166-167`
  `is_admin=is_first_user, email_verified=is_first_user`. On a fresh public deploy whoever hits
  `/register` first becomes a self-verified admin. Masked by a false assurance: `profile.py:72` lists
  `ADMIN_BOOTSTRAP_EMAIL` as production-required, but it is **never read** anywhere else in the code.
- **Why deferred:** read-only review; new finding (not in the prior security investigation).
- **Recommended resolution:** **now / before any internet-facing deploy** — honor
  `ADMIN_BOOTSTRAP_EMAIL` (only that email becomes admin) or gate first-user via a one-time setup token;
  remove the dead var from the required set if not honored. **Confirm in a running app.**

## [OPEN] FU-199 — SSRF in recipe import-from-URL
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (security, HIGH)
- **What:** `POST /api/recipes/import-from-url` fetches an arbitrary user URL with no scheme/host
  validation and `allow_redirects=True` (`import_recipe_from_url.py:66` accepts a bare string; `:310-314`
  `requests.get(...)`). Any authed user can reach cloud metadata (169.254.169.254), localhost services
  (the Ollama LLM), or intranet hosts. Byte cap + timeout exist; destination filtering does not.
- **Why deferred:** read-only review; new finding.
- **Recommended resolution:** **before managed/SaaS (Path A/B) deploy** — validate scheme; resolve
  hostname and reject RFC-1918/loopback/link-local before connecting; re-validate each redirect hop.
  **Confirm in a running app.**

## [OPEN] FU-198 — DB restore + chunked uploads not admin-gated; no shared @require_admin
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (security, HIGH)
- **What:** `data/restore_backup.py:358-363` and the `uploads.py` chunk chain require only a logged-in
  session — restore inserts arbitrary rows across every table. Root cause: no shared admin gate; three
  ad-hoc copies (`users/update_user_as_admin.py:43`, `audit/get_audit_events.py:59`, reused by
  `update_app_settings.py:15`). Ad-hoc gating is how restore shipped ungated.
- **Why deferred:** read-only review; new finding.
- **Recommended resolution:** **now** — introduce one shared admin dependency, audit every mutating
  route for it, gate restore + uploads. **Confirm in a running app.**

## [OPEN] FU-197 — CSRF absent + email-change needs no password proof (confirms prior art)
- **Raised:** 2026-06-16 (senior/tech-lead review; confirms prior-art A.1/A.2 in
  `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md`)
- **Type:** finding (security, HIGH — combine into account-takeover chain)
- **What:** No CSRF token / Origin check on any mutation (`app.py:60-64` `SameSite=Lax`;
  `middleware.py:115-125` checks only session presence). And `email_flows.py:260-304`
  (`request_email_change`) requires no `current_password`, unlike `change_password.py:41,60`. CSRF +
  email-change-without-proof = full account takeover.
- **Why deferred:** prior-art items confirmed still-open against current code; read-only review.
- **Recommended resolution:** **before internet-facing deploy** — double-submit CSRF token enforced in
  middleware (or SameSite=Strict + Origin allow-list); require `current_password` re-proof on email
  change + notify old address. **Confirm in a running app.**

## [OPEN] FU-196 — Postgres target unreachable in running app; review's lower-severity hardening batch
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (architecture + hardening)
- **What:** Umbrella for the review's MEDIUM/LOW items. (a) Postgres is the R-005 standard target but
  `configuration_manager.py:145` hardcodes `sqlite:///`, no PG branch/driver — **overlaps FU-045**, add
  a Postgres CI lane. (b) In-request multi-commit, no unit-of-work, global handler doesn't roll back
  (`create_recipe.py:258/302/317/347`, `startup.py:140-150`). (c) Reflection-based wiring has no
  boot-time resolved-route assertion (`startup.py:135`, `service_wiring.py:17`, `decorators.py:13`).
  (d) `requests==2.31.0` CVE-2024-35195 → bump ≥2.32.4; `fuzzywuzzy` unmaintained. (e) assistant
  endpoints unthrottled (`ask_assistant.py:331,367`); `SESSION_COOKIE_SECURE` off by default
  (`app.py:64`); no app-wide security headers; no account-deletion endpoint (GDPR). (f) orphaned base
  components `CardComponent.vue`/`SelectComponent.vue`; ~237 prompt-ID comments to sweep pre-release;
  `.npmrc` pnpm-only keys warn on every npm command. Full detail in the review doc.
- **Why deferred:** read-only review; these are Tier-2/Tier-3 polish, not ship-blockers.
- **Recommended resolution:** Tier-2 (a–e) before "professional"; Tier-3 (f) pre public release.
  Postgres CI lane folds into FU-045.

## [OPEN] FU-194 — Onboarding demo data (L38) — deferred from C-5.5
- **Raised:** 2026-06-16 (Onboarding C-5.5)
- **Type:** deferred job
- **What:** C-5.5 left out the optional **demo recipe (+ meal / meal-plan)** toggle (proposal §3.5,
  feedback L38). It was the highest-risk piece to build blind: a Recipe needs a RecipeCollection +
  **non-nullable** RecipeIngredient → StockItem FKs + a MealPlan/Entry, and this machine has **no
  Python** to test the seed — a bug would 500 on Finish. Everything else in C-5.5 shipped.
- **Why deferred:** explicitly optional in the proposal; far safer to build where the backend can be
  run + tested so the FK graph is verified.
- **Recommended resolution:** on a provisioned machine (alongside FU-193), or a small dedicated chunk:
  add `POST /api/onboarding/seed-demo` (+ a warned toggle in the starter-data step) creating plain,
  user-deletable rows (**no `is_demo` marking**), mirroring `seed.py`'s `make_recipe`/`make_item`/
  `plan_entry`. Then flip L38 in COVERAGE_GAPS.

## [OPEN] FU-195 — Onboarding starter-data: in-page import + groups/locations "some" (trims from C-5.5)
- **Raised:** 2026-06-16 (Onboarding C-5.5)
- **Type:** leftover
- **What:** Two C-5.5 sub-asks were scoped down: (1) **inline import** (L30) — the starter-data step
  still **links** to `/data/import` rather than embedding the importer on the page (embedding the
  full importer was disproportionate for this build); (2) **groups/locations "some"** (L34) — the
  step offers all/none per catalogue **+ a static preview** (captions list the default names), and
  the **packs** give item-level ticking, but there's no individual tick-list for the default
  groups/locations themselves.
- **Why deferred:** size of the combined C-5.5 + C-5.6 build; both are enhancements, not
  acceptance-blockers (the acceptance centres on packs + the added-list, which shipped).
- **Recommended resolution:** opportunistic — (1) embed a slim importer (or a "paste rows"
  affordance) when the importer is next touched; (2) add a per-name checklist for default
  groups/locations (needs `/seed` to accept name lists, or a `seed-items`-style call for them).

## [OPEN] FU-188 — Back-in-stock subscriptions tier (deferred from Alerts C-9.5)
- **Raised:** 2026-06-15 (Alerts C-9.5 — subscriptions tier)
- **Type:** deferred job
- **What:** The proposal/impl plan for the subscriptions tier mentioned a **back-in-stock**
  subscription shape ("notify me when a merchant's product comes back in stock") alongside the
  price-watch (`PriceAlert`) tier that C-9.5 shipped. C-9.5 built **only** the price-watch
  surface (`SubscriptionsPanel.vue`, money-gated, reusing `/price-history/alerts`). Back-in-stock
  was **not** built: there is no data source / entity for it yet — it's companion/ingestion-scope
  (the producer would push availability), and the in-app side would just surface/manage rows like
  price watches do.
- **Why deferred:** anti-creep — no back-in-stock data exists to surface, so a placeholder UI/shape
  now would be speculative (charter: don't pre-build). User confirmed skipping it for C-9.5.
- **Recommended resolution:** **when** the companion/ingestion path (C-10) defines a back-in-stock
  signal — then add a second tier to `SubscriptionsPanel.vue` (same list/manage shape) reading it.

## [OPEN] FU-187 — Assistant ignores the configurable expiring-soon window (uses the constant default)
- **Raised:** 2026-06-15 (Alerts C-9.2 — threshold threading)
- **Type:** finding / consistency gap
- **What:** C-9.2 moved the expiring-soon window onto `AppSetting.expiring_soon_window_days`
  and threaded it through the alerts evaluator (`get_alerts.py`) and the location heatmap
  (`attention.py`, via `get_location_tree` + `get_stock_item_detail`) using one resolver,
  `stock_status.effective_expiring_soon_window`. The **assistant** (`features/assistant/
  tools.py`, ~4 sites near lines 903/1480/1570/2025) still reads the bare
  `EXPIRING_SOON_WINDOW_DAYS` *default* constant, so if an admin changes the household window
  the assistant's "expiring soon" answers won't match the alerts list / heatmap. This is the
  constant-as-default carve-out the impl plan explicitly allowed for C-9.2; flagged inline at
  the `tools.py` import. It's the one default (R-003 — not a second literal), just not
  honouring the override.
- **Why deferred:** threading the `AppSetting` fetch through the 4 assistant tool sites was
  out of C-9.2's tested scope (acceptance named only bell/page/heatmap); low impact (assistant
  expiry answers only drift if an admin retunes the window).
- **Recommended resolution:** opportunistic — when the assistant's expiry tools are next
  touched, or fold into the FU-174 app-wide date/threshold sweep. Pass the resolved window
  (same `effective_expiring_soon_window`) into the 4 sites.

## [RESOLVED?] FU-186 — Decommission in-app live product search / `merchant_api` + standalone `emailer/` (scraping-divorce ripple)
> **Update 2026-06-17 — Phase D landed.** `merchant_api/` + `emailer/` directories deleted from this
> repo (they live in `../dora-companion`). Backend wiring stripped (audit `SOURCE_MAPI` + `SOURCE_EMAILER`
> retained read-only as `*_LEGACY` for historical rows; nothing in `dora_api` writes those values
> any more). FE wiring stripped: `merchantApiService` / `merchantManagementApiService` /
> `MerchantsSettings.vue` / `ProductSearch.vue` / `ProductSearchCard.vue` / `ProviderHealthChip.vue` /
> `merchantStore` / `scrapedProductOffer*` / `offerSortByOptions` all gone; `axiosHttpClient` no
> longer carries the `'merchant'` `ApiBackend` arm. `useProductSearchUrl()` composable added;
> `useFeatureFlags().products` + the new `AppSetting.product_search_url` drive a re-pointed
> **Product Search** nav entry that opens the admin-configured URL in a new tab (data-gated;
> R-014 disabled-with-hint when URL unset). Infra cleaned: `desktop_app.py` only spawns dora_api,
> `compose.yml` drops the 5172 port + emailer block, `Dockerfile` + `startup.sh` no longer spawn
> the companion processes, `nginx.conf` drops the 5172 proxy comment, `dora.spec` drops the
> merchant_api submodules + emailer templates, `.env` / `.env.example` drop `MAPI_*` + the
> `DORA_EMAIL_ENABLED` deals-emailer block (the `DORA_SMTP_*` vars stay for the transactional
> sender), CI drops the `compileall` smoke job. Migration `f8b2d4a6c1e3` adds
> `AppSetting.product_search_url`. **Verified:** pytest **405/405** (+4 new), `vue-tsc` clean,
> `npm run lint` clean, fresh-SQLite `flask db upgrade` clean. **Move to RESOLVED once the
> browser-pass on the re-pointed nav + the System Settings input is confirmed** (FU-186-verify).


> **Re-sequenced 2026-06-17 — now the ACTIVE track, ahead of FU-189.** The Merchant→Store rename
> (FU-189) is blocked on this because "merchant" = entity AND `merchant_api` companion (a blind
> rename corrupts the companion wiring). Build order: scaffold companion → ingestion API → companion
> standalone+wired → **this decommission** → FU-189 rename. **Companion scaffolded 2026-06-17** as a
> sibling repo at `../dora-companion` (copied `merchant_api/` + `emailer/`; nothing removed from Dora
> yet — the delete + de-wire happens here, after the ingestion API + a functional companion).
- **Raised:** 2026-06-15 (C-10 ingestion API design); **emailer scope added 2026-06-16**
- **Type:** deferred job / decommission
- **What:** With scraping divorced and `/api/ingest` (C-10) as the **only** inbound product path,
  Dora-core must **not scrape live**. The current in-app **product search calls the sibling
  `merchant_api` (port 5172) to live-scrape** — that has to go. Options: (a) repoint in-app
  product search at the **already-ingested local catalogue** (search what your source pushed), or
  (b) move product search entirely to the companion. This **reshapes C-1b's "find & link a
  product"** (it can no longer live-search) and the "Find deals" / best-deals surfaces; `merchant_api`'s
  live-scrape role moves to the private external producer. Folds in **FU-053** (best-deals card
  fetches all products client-side).
  - **Surgical removal — `emailer/` (the standalone weekly-deals email service):** the half-finished
    `emailer/` package (`generate.py` / `delivery.py` / `startup.py` / `product_model.py` /
    `user_model.py` / `templates/` / `food_emojis.txt`) is the **old "Weekly Price Report" deals
    email** — it's coupled to the scraper (its commented-out core fetches `/api/webScraper/offers`;
    `product_model.py` mirrors the merchant-offer shape) and isn't wired into the running app (only
    shares `logging_setup`). Per the user (2026-06-16) it is **part of this same surgical-removal
    sweep**: (1) **move it into the private companion app and finish it off properly there** —
    that's where deals + mailing belong (the companion gathers offers and mails the user; invisible
    to Dora per the hard rule); (2) **then delete `emailer/` from this repo.** Also clean the
    now-dead refs left behind: `SOURCE_EMAILER` (`audit_event.py:12`) + the `emailer` arm in
    `get_audit_events.py` / `logging_setup.py` docs once nothing emits them.
  - **Not in scope / keep:** `dora_api/infrastructure/email_sender.py` is the **transactional**
    sender (password-reset etc., works OOTB per INV-4) — **stays**. The legitimate in-app
    "email me stuff" need is the **Alerts C-9.7 email digest** (per-user opt-in, hangs off the
    alerts evaluator, reuses `email_sender.py`) — so removing `emailer/` leaves **no in-app gap**.
- **Why deferred:** a cross-cutting decommission sweep, distinct from building the ingestion seam;
  needs `/ingest` landed first so the catalogue is populated to search against. The `emailer/` move
  needs the companion repo to land it in.
- **Recommended resolution:** after **C-10.2** (the ingest path exists); pair with **FU-182**
  (Products-off) since both reshape the product surfaces, and re-confirm C-1b §2.4's "find & link"
  against it. Keep the **invisibility rule** — no scraper references in whatever replaces search,
  and none of the companion's existence (incl. the emailer it now hosts) surfaces in the app.
- **Update 2026-06-17 (products-as-overlay pivot — resolution settled):** the search question is
  now decided (`docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.1): **only the Product Search
  page moves** to the companion, which becomes a *complete app* (`merchant_api` + the moved search
  page + its own settings page) in its **own repo**. Dora keeps the **Product Search nav entry** →
  an install-configured URL (data-gated; companion never named — a bounded carve-out to the
  invisibility rule). My Products / Price History / the stock-item Products tab **stay in Dora**.
  The old "pair with FU-182" now reads "pair with **FU-209** (gate reframe) + the new proposal".
  The `emailer/` move/delete is unchanged.

## [OPEN] FU-184 — Reconcile onboarding sell-copy + loop stages against actual app behaviour
- **Raised:** 2026-06-15 (Onboarding C-5 v3 design)
- **Type:** finding / deferred verification (P3 Honest gate)
- **What:** The C-5 onboarding redesign sells "the loop" cinematically (Stock → Plan → List →
  Shop → Restock → Cook, Dora at centre) with one-line claims per stage. These claims + the loop
  stages are **PROVISIONAL** (PROPOSAL_ONBOARDING §6). Before any onboarding copy ships, **walk
  the running app** and confirm each claim is literally true (does finishing a shop really
  auto-restock? does cook mode decrement stock? does price memory + an "inflated price" signal
  actually exist?). Cut/soften anything the app doesn't back.
- **The emerging "Insight / Spend-smarter" stage** (user links products to stock items → Dora
  flags prices that are higher than usual, from their own receipts) is the honest replacement
  for the divorced deal-scraping — but it **isn't a finished feature**. Do NOT promise it in
  onboarding copy until it's real; it's a design placeholder until then. Decide whether to build
  it (it's the spine of the **Spend-tracking** persona).
- **2026-06-16 (C-5.1 closed without tripping this gate):** C-5.1's copy edits are **labels +
  import wording only** (Skip; "spreadsheet or another app"), not aspirational feature claims, so
  the sell-copy honesty gate didn't apply to it. **Still open:** the welcome-card blurb mentions
  *"deals"* (flagged above) and the loop/Insight sell-copy land in **C-5.2/C-5.6** — those are the
  chunks this gate really bites on.
- **2026-06-16 (C-5.2 shipped the copy — gate now LIVE):** the cinematic intro + hero loop are built
  with the **provisional** sell-lines, centralised in **one file**:
  `web_app/src/pages/onboarding/onboardingContent.ts` (`LOOP_STAGES`, `LOOP_CENTRE`, `LOOP_INSIGHT`,
  `NARRATIVE_SCENES`, `PERSONA_PREVIEWS`). The user explicitly chose to **build-to-plan now and
  revisit with the assistant later** to confirm each claim against the finished app. The Insight beat
  is rendered as a dimmed, "soon"-tagged candidate (not a promise), and Shop's old "log what you paid"
  price claim was moved off Shop onto that provisional node. **Revisit = walk the running app, then
  edit that one content file** (cut/soften per claim); no component changes needed for copy-only fixes.
- **2026-06-16 (also spotted, C-5.3):** the onboarding **admin step** still says *"Pick which
  merchants to **scrape**"* (`WelcomeWizard.vue` admin card) — stale post scraping-divorce. Out of
  C-5.1/2/3 scope; reword in the loop/Insight copy pass (or the P8 rename), not piecemeal.
- **Why deferred:** needs the running app to verify; can't be cleared by a static read (env
  unprovisioned this session, same blocker as FU-183).
- **Recommended resolution:** **close-gate on the onboarding-copy chunks (C-5.1/C-5.2/C-5.6)** —
  validate when building them on a provisioned app. Not optional polish.

## [OPEN] FU-218 — Browser-verify the new admin "API access" page (C-10 / Phase B)
- **Raised:** 2026-06-17 (Phase B build)
- **Type:** verification
- **What:** New Settings page lives at `/settings/admin/api-access`. Confirm in the browser:
  (a) sidebar entry appears under Admin · global (admin only); (b) `New key` opens dialog → reveals
  raw key once → copy works → list shows the new row with `Never used` + `Accepted 0 / Skipped 0
  / Failed 0`; (c) expanding the row shows "Store mappings" panel; (d) push a record from any
  bearer client against an unknown store → reload → the source row shows a pending badge + the
  mapping appears in the panel marked "pending"; (e) merchant picker assigns it → the badge
  clears; (f) disable / enable / rename / revoke all round-trip; (g) revoked key is rejected by
  `/api/ingest` immediately.
- **Recommended resolution:** opportunistic — bundle with the other Phase 0 browser passes.

## [RESOLVED?] FU-190 — Ingestion API must honour "no auto-create stores"  *(move to RESOLVED on confirm)*
- **Update 2026-06-17 (Phase B build):** implemented as **(b) quarantine queue** end-to-end (the
  proposal's chosen safety net; the "(c) setup mapping step" is naturally produced by the same
  surface — admins map *before* pushing if they want, but unknown names on first sight quarantine
  instead of being rejected, which is friendlier). On every ingest record the producer's
  `merchant` string is resolved via `IngestionStoreMapping`: known → use the linked Merchant;
  unknown → create a quarantined mapping (`merchant_id IS NULL`), skip the record with reason
  `store_not_mapped`, surface as **pending** on the API access page. Stores themselves are
  **never** created by the endpoint. Admin assigns or clears the merchant via
  `PUT /api/ingestion-sources/<id>/store-mappings`. Covered by `test_ingest_batch.py` (quarantine
  + post-mapping roundtrip) + `test_ingestion_store_mappings.py` (CRUD + invalid merchant rejected).
  **Move to RESOLVED once the FU-218 browser pass confirms the pending → assign flow in the UI.**

## [OPEN] FU-189 — Rename Merchants → Stores, add management page + user-uploaded logos
> **Resequenced to LAST 2026-06-17 — blocked on FU-186.** A blind Merchant→Store rename is ~550 refs
> AND entangled: "merchant" = the `Merchant` entity AND the `merchant_api` companion (`ApiBackend
> 'merchant'`, MerchantApiService/Management, MerchantsSettings, `VITE_MERCHANT_API_*`). Renaming
> blind corrupts the companion wiring + splits the FE/BE contract → won't boot. **Do this only after
> FU-186 removes `merchant_api` from the Dora repo** — then "merchant" = entity only and the rename
> is mechanical. (Companion scaffolded 2026-06-17 at `../dora-companion`; ingestion API is the next
> in-repo step.) `usual_store_id` + the user-curated Stores management page land with this.
- **Raised:** 2026-06-15 (simple-mode brainstorm round 2)
- **Type:** refactor + small feature
- **What:** Three coupled changes:
  1. **Entity + UI rename `Merchant` → `Store`** app-wide. Plain-language
     ("Coles is a store, not a merchant"). Pre-release → no compat shims,
     one migration, one mechanical pass. Sanity-check first that no
     existing `Store` symbol in the codebase already means something else
     (Pinia store, etc.); locations is adjacent but unambiguous.
  2. **Single management page in settings.** User-curated list. **No
     prefilled stores** (sidesteps locale-coupling + the legal-logos
     issue). **No auto-create** from any other code path — notably the
     ingestion API must respect this (see FU-190). Edit / disable /
     delete with referential safety against existing offers + shopping
     lines.
  3. **Per-store image upload.** Reuse the existing image-upload infra
     (recipes/stock items already use it from C-cross §2.8). **Dora
     ships zero logos** — legal safety. Fallback when no image: the
     existing hash-swatch + initial pattern from `ProductSearchCard`
     (referenced in ENGINEERING_STANDARDS.md).
  Full rationale in `docs/99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md`
  §4. Note: a `StockItem.usual_merchant_id` (rename → `usual_store_id`)
  nullable field also lands here — see FU-182's brainstorm scratch §3 for
  the shopping-list grouping use case.
- **Why deferred:** Cross-cutting refactor + new image-upload consumer +
  ingestion implication. Needs scheduling alongside the simple-mode sweep
  (FU-182) since they share data-model territory.
- **Recommended resolution:** schedule as a dedicated work unit before
  FU-182's per-surface sweep, since simple mode's shopping-list grouping
  depends on `usual_store_id` existing. Earlier still if the C-cross §2.6
  feature-flag panel work picks up first.
- **Update 2026-06-17:** confirmed by the products-as-overlay pivot — `usual_store_id` is part of
  the everyday stock-item model (`docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.3),
  always-available (no products/money gating). The stale "before FU-182's sweep" now reads "before
  the FU-209/210/211 build chunks." Still a prerequisite; stays open.

## [OPEN] FU-181 — Wire actual plan-emailing + a `meals_per_week` preference
- **Raised:** 2026-06-14 (C-2.J sequential builder)
- **Type:** follow-up (deferred sub-feature)
- **What:** Two small loose ends from the sequential builder (C-2.J):
  1. **Plan email** — the builder's done-step **Email button is shown disabled**
     ("isn't set up yet", per R-014). Actual emailing of a plan / its shopping
     list isn't built (`useMealPlanExport` only does print). Wire it to the
     existing email infra (INV-4 / `emailer`), SMTP-gated: enable the button
     only when email is configured for the install, otherwise keep it
     disabled-with-a-hint (R-014). The proposal §6 also lists email on the
     recurring/template flows — same backing.
  2. **`meals_per_week` pref** — the builder's target count is hardcoded to 7
     (proposal §6 wanted "user's `meals_per_week` if set, else 7"). No such
     user/household field exists yet. Add it (household-wide, like the slot
     vocab) + have the builder read it. Minor; the 7 default works fine
     meanwhile.
- **Recommended resolution:** opportunistic — pair the email work with the
  broader email/INV-4 effort; the `meals_per_week` pref with the next
  settings/onboarding touch (C-5 seeds it).

## [OPEN] FU-177 — Pre-existing ESLint errors block `npm run build`
- **Raised:** 2026-06-14 (surfaced by C-2.A adversarial review)
- **Type:** finding (pre-existing debt)
- **What:** 5 ESLint errors exist on the current tree, **unrelated to C-2.A**
  (verified identical on a stashed clean tree): `useFeatureFlags.ts:31`,
  `useStockFilters.ts:75` + `:92`, `RecipeDetailPage.vue` (~`:1117`),
  `AboutSettings.vue:82`. `npm run build` runs ESLint first and **aborts on
  these before reaching `vue-tsc`**, so a production `quasar build` currently
  fails. `vue-tsc --noEmit` itself is clean.
- **Why deferred:** out of C-2.A scope (R-007); they live in unrelated files.
- **Recommended resolution:** **soon** — a focused cleanup before the
  end-of-build browser-verification pass (a broken `build` blocks shipping the
  polished page). Investigate each (likely `no-unused-vars` /
  `no-explicit-any`-class); fix or justify per the lint config.

## [OPEN] FU-176 — Apply R-014 (reveal-and-disable) app-wide
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; new rule R-014 / ADR-009)
- **Type:** follow-up
- **What:** New engineering rule **R-014** says adoptable features that aren't
  yet configured/enabled should be **shown disabled with a "not set up" hint**,
  not hidden — so users discover they exist. The meal-plan builder's Email
  button adopts this in C-2.J. The rest of the app needs a sweep: most notably
  the **scanning button**, which today is *hidden* when `scanning_enabled` is
  off (ADR-002) and per the user should now render **disabled-with-a-hint**
  instead. Audit other gated/`v-if`-hidden adoptable surfaces (LLM/assistant
  affordances, any integration entry points) and convert the *presentation* of
  the off state from hidden → visible-disabled where it makes sense (R-014
  carve-outs: genuinely inapplicable or security-sensitive surfaces stay hidden).
- **Why deferred:** out of the meal-plans scope (R-007); it's a cross-cutting
  presentation change touching the scanning gate + others.
- **Recommended resolution:** opportunistic / a focused small sweep — pair with
  the next touch of each gated surface, and update ADR-002's note to point at
  R-014 for the presentation of the off state.

## [OPEN] FU-175 — Assess a purpose-built "bulk edit the week" meal-plan action
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; C-2.E retires MealPlanEditDialog)
- **Type:** follow-up
- **What:** C-2.E deletes `MealPlanEditDialog` — inline servings/slot edit on
  the carousel + implicit create-on-tap cover its jobs. The user wants a
  *purpose-built* bulk-week action assessed separately (it "may not even need a
  modal"): e.g. select multiple entries on the canvas and bump servings /
  reslot / remove in one go, or a compact week-table editor. Assess the real
  need (does inline editing already make this unnecessary?) before building.
- **Why deferred:** the canvas inline-edit (C-2.C) may already satisfy the need;
  building a bulk surface now would be speculative (Anti-creep).
- **Recommended resolution:** after C-2.C/E land and the inline-edit UX has
  been used — assess whether a bulk action earns its place; design a brief if so.

## [OPEN] FU-173 — Slot-vocabulary "remap legacy entries" UI — deferred
- **Raised:** 2026-06-14 (authoring IMPL_PLAN_MEAL_PLANS — C-2.A scope call)
- **Type:** deferred job
- **What:** `PROPOSAL_MEAL_PLANS.md §4 / §11.4` describes a one-shot
  "remap legacy/off-vocabulary `MealPlanEntry.slot` strings to the user's
  current slot list" action in settings. C-2.A deliberately ships the
  per-user vocabulary **without** it (off-vocab strings are preserved verbatim
  and rendered in an "Other" row, C-2.C) — Anti-creep: the cleanup earns its
  place only if real off-vocab data accumulates.
- **Why deferred:** no off-vocab data exists yet (slot is currently picked from
  a fixed 5-value constant); building the remap tool now is speculative.
- **Recommended resolution:** opportunistic — build only if users accumulate
  off-vocabulary slot strings after C-2.A ships the editable list.

## [OPEN] FU-171 — Recipe image hide/show toggle reported broken — no static repro
- **Raised:** 2026-06-13 (FU-088 → Cookbook card revision Chunk A §1.1)
- **Type:** finding (reported defect; didn't reproduce in code)
- **What:** User reported the "Hide/show recipe photos" toggle on the
  Cookbook overview doesn't work (FU-088 bullet 1). Static trace through
  the full chain looked correct end-to-end:
  - `RecipesOverview.vue:21-33` — `BaseButton` with reactive `:icon` and
    `@click="onToggleRecipeImages"`.
  - `onToggleRecipeImages` → `setRecipeImages` → `authStore.updateMeAsync`
    reassigns `currentUser.value` from the PATCH response (`authStore.ts:81-83`).
  - `useImagePrefs.ts:23-25` — `showRecipeImages` computed reads
    `currentUser.value?.show_recipe_images`.
  - `RecipeCard.vue:15` — `v-if="showRecipeImages && recipe.has_image && !imgFailed"`.
  - Backend `update_me.py:162-163` writes the field;
    `register_user.py:112` (DTO) always emits it.
- **Recommended resolution:** **confirm in browser** after Chunk A ships.
  If still broken, capture: (a) does the icon flip on click? (b) does the
  PATCH succeed (network tab)? (c) does the response body include
  `show_recipe_images`? (d) does any card re-render? — that will pinpoint
  which link in the chain breaks at runtime.
- **State note:** open — no code change in Chunk A (no repro to fix). The
  Chunk A card rewrite preserves the same `v-if` gate.

## [OPEN] FU-170 — App-wide button display preference (icon-only / icon+text / mixed)
- **Raised:** 2026-06-13 (FU-088 cookbook card revision — Cook button went icon-only `mdi-chef-hat` per user choice; want this controllable user-wide)
- **Type:** new feature
- **What:** A single user preference (Settings → Appearance, alongside the existing image-display opt-in) controlling how primary action buttons render across the app:
  - **Icon only** — every action button is `flat`/`round` (or `unelevated` for primary) with no label; the verb lives in the tooltip.
  - **Icon + text** — every action button shows both icon and label.
  - **Mixed** (default, recommended) — a curated per-button policy: high-frequency / unambiguous actions (Cook, favourite, add-to-list on the recipe card, ± steppers) go icon-only; less-frequent / verbier actions (Save, Cancel, Create recipe, Delete, Mark cooked, Confirm) keep their labels. The policy is defined once in code, per button, not at the call site.
- **Why:** the cookbook revision (Chunks A–C) introduces the first deliberately icon-only primary button (Cook = chef hat). Without a system-level preference, users who prefer verbose UIs lose the verb entirely, and ad-hoc "should this have a label?" calls drift across the app over time.
- **Shape (sketch — to be designed in a brief):**
  - User-prefs field `button_display: 'icon_only' | 'icon_text' | 'mixed'`, default `'mixed'`.
  - A thin `<AppActionBtn>` wrapper (or a `useButtonDisplay()` composable) that reads the pref + the button's per-instance policy hint (`prefer="icon-only" | "icon-text" | "auto"`) and decides whether to render the label. Existing `q-btn` call sites migrate gradually.
  - Tooltips become mandatory on any button whose policy allows icon-only rendering (accessibility — screen readers still get the verb).
  - Per-button policy lives in a small registry/enum so policy changes are one-line edits, not codebase-wide grep-and-replace.
- **Scope notes:**
  - Footer/toolbar buttons (sticky footer A7, modal action rows A3) are in-scope.
  - Menu items (`q-item`) are out of scope — they need labels for legibility.
  - Settings page itself is out of scope — it uses long-form forms, not action buttons.
- **Recommended resolution:** after the cookbook card revision (Chunks A–C) lands and we have lived with at least one icon-only primary button for a few days. Write a short brief first (charter cross-check: Effortless + Anti-creep — this is a knob, justify it doesn't feel like one), then implement as a small standalone chunk.
- **State note:** open — no brief yet, no code.

## [OPEN] FU-169 — Implement the test-suite improvements proposal
- **Raised:** 2026-06-13 (post-FU-166 proposal)
- **Type:** deferred job
- **What:** `docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` — phased
  plan to make the suite a trustworthy net: **Phase 1 (P0)** CI runs all tests
  (not just `tests/e2e/dora_api`) + pytest config (`xfail_strict`,
  `filterwarnings`, markers) + `pytest-cov` + shared `assert_problem`/
  `assert_envelope` matchers + one naming convention; **Phase 2** per-test DB
  rollback (isolation → kills order coupling, enables `xdist`) + data
  factories + parametrize; **Phase 3** close the 24 untested API surfaces +
  domain/repository/contract tests; **Phase 4** frontend Vitest +
  `merchant_api`/`emailer` fixture tests + Hypothesis + Postgres CI.
- **Why deferred:** sizeable; needs user prioritisation. Each phase ships
  independently green.
- **Recommended resolution:** start **Phase 1** opportunistically (half-day,
  no-regret); sequence the rest per the proposal. Relates to FU-045 (Postgres
  CI, Phase 4) and FU-161 (Aldi scraper — Phase 4 gives it a net).

## [OPEN] FU-161 — Shopping list drag-and-drop "index off" (feedback L414) — confirm in browser
- **Raised:** 2026-06-12 (shopping-list UX design session; original report L414, 06-Jun feedback)
- **Type:** finding (reported defect, not reproduced in static read)
- **What:** "Drag and drop is an index off somehow (wrong items being swapped)."
  *2026-06-12 update:* a deeper read found the fix **already shipped in P6-01
  Chunk 6** — `onLineDrop` carries a comment explicitly correcting the
  "subtract 1 when dragging down" off-by-one, and UX v2 preserved that logic
  verbatim. Per the reported-defect rule it stays open until verified in the
  running app (now part of the FU-165 checklist).
- **Recommended resolution:** confirm in browser (FU-165).

## [OPEN] FU-161 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-154 — Page-local product/stock collections bypass their stores (R-003 smell, likely widespread)
- **Raised:** 2026-06-12 (during FU-014 image-bug investigation)
- **Type:** finding
- **What:** `MyProductsPage.vue` keeps its own local `products = ref<Product[]>([])`
  populated by a direct `productApi.getAllAsync()` in `onMounted` (line 583/1070),
  bypassing `productStore.products` entirely — even though `ProductSearch.vue`'s
  save goes through `productStore.createProductAsync()` which keeps the store
  fresh. Result: a product saved on the search page doesn't appear on My Products
  until the user hard-refreshes the page (confirmed by user, 2026-06-12). This is
  a textbook R-003 (state-ownership / single source of truth) violation — two
  sources of truth for the same domain collection.
- **Why it's likely widespread:** the same pattern (page-local `ref<T[]>` +
  direct API call in `onMounted` for a collection that has a Pinia store) almost
  certainly exists on other pages. Quick suspects to audit:
  - `DashboardPage.vue` (modified in current branch)
  - `StockOverview.vue`, `StockItemDetailPage.vue`
  - `RecipesOverview.vue`, `RecipeDetailPage.vue`
  - `MealPlansOverview.vue`, `WastePage.vue`
  Audit method: grep for `= ref<.*\[\]>\(\[\]\)` + `\.getAllAsync\(\)`
  / `\.get.*Async\(\)` inside `pages/` and cross-reference what Pinia store
  already owns that collection.
- **Confirmed problem area:** `web_app/src/pages/MyProductsPage.vue` (lines
  583, 587–607, 1070). Saved product invisible until refresh.
- **Recommended resolution:** scoped Wave-A-ish prompt — (1) audit all `pages/`
  for the pattern, (2) for each hit, replace the local ref + onMounted-fetch with
  `storeToRefs(theStore)` + `theStore.refresh()`-equivalent, (3) make sure the
  store's create/update/delete methods refresh state so reactivity is automatic.
  Don't relocate fine client-only computeds (per R-003 addendum). Treat
  `MyProductsPage` as the canonical fix to copy.
- **Cross-ref:** ENGINEERING_STANDARDS R-003 (state ownership).

## [OPEN] FU-153 — Assistant LLM config: per-user, reachability probe, multi-provider
- **Raised:** 2026-06-12 (user feedback during FU-085 verify)
- **Type:** design / proposal addition (no code yet)
- **What:** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md §7` (new
  section, this session) captures four interlocking changes to
  the LLM client + config side, distinct from the §1–6 routing
  refactor:
  1. **§7.1 Per-user LLM config** — drop the singleton
     `AppSetting.llm_*` and move it to `User.llm_*` (+ a
     `master_llm_enabled` install-wide kill switch on
     AppSetting). Households with two desktops each running
     their own LLM stop sharing one URL.
  2. **§7.2 Reachability probe** — new `GET
     /api/assistant/ping` hit **once per chat open** (not per
     message, not on a poll). Visible "AI mode unavailable —
     using basic mode" banner + Retry when the user's
     `llm_enabled` is true but their LLM doesn't answer.
  3. **§7.3 Network-topology constraint** — document that the
     backend (not the device) reaches the LLM URL. Operator
     concern for household / remote-LLM setups; pure
     documentation, no code.
  4. **§7.4 Multi-provider** — abstract `LlmClient` with
     `OllamaClient` (existing, moved) + `OpenAiClient` +
     `AnthropicClient` + `GeminiClient`. Per-user
     `llm_provider` enum + encrypted-at-rest API key column.
     Different tool-call schemas adapt to a shared shape
     before reaching `tools.py`.
- **Sequencing (§7.5):** one migration ships §7.1 + §7.4
  schema columns; provider implementations follow per-PR;
  §7.2 probe lands last (cheap once per-user config is
  available); §7.3 is docs only.
- **Existing DORA-BOT feedback cross-ref (§7.6):** the
  per-user mode toggle / "turn the bot off completely" /
  "disabled if unavailable" items in `Feedback _ Fixes - as
  of [06-Jun-2026].md` lines 452-460 pair directly with §7.1
  + §7.2 — the toggle UI visibly reflects the probe result.
- **Recommended resolution:** treat as the next chunked
  IMPL plan after the FU-152 routing redesign (or before;
  they're orthogonal but the per-user config is a
  pre-requisite for the rules-router-per-user too). Pair
  with the AI-mode design pass.
- **State note 2026-06-12:** **user signed off** on §7.1–§7.4
  as written, with one refinement folded into §7.1: the
  per-user Assistant config lives in
  `PreferencesSettings.vue` next to the existing C-cross
  per-user toggles (`money_features_enabled`, etc.) — not a
  net-new settings page. §7.3 (network-topology docs) was
  explicitly accepted as "same connectivity story as the rest
  of the app, nothing special". Next step: draft an IMPL plan
  from §7 when this work is sequenced.

---

## [RESOLVED-MINIMAL] FU-150 — Assistant chat-mode doesn't recognise dietary/cuisine queries
- **Raised:** 2026-06-12
- **Resolved (step 1, this session):** rule-based first-match-wins
  matcher kept, but the `find_recipe` intent's trigger list now
  catches the bare-noun cases ("i need a recipe", "any breakfast
  ideas", "show me a vegetarian recipe", etc.) — and the handler
  was rewritten to **stop yanking "the bit after a preposition"**
  and instead tokenise the whole message (minus stopwords) and
  substring-match each token against name + cuisine + category +
  timeOfDay + dietaryTagNames. Vocab arrives via the extended
  `RecipeSnapshot` (`dietaryTagNames`, `timeOfDay`) hydrated in
  `DoraChat.vue` from the existing Pinia stores; vocab preload
  was added to `ensureRecipeData()`. Net effect: "i need a
  vegetarian recipe" → routes to find_recipe, filters by the
  'vegetarian' dietary tag, lists the top matches. "Asian
  breakfast recipe" → both 'asian' + 'breakfast' must hit
  (cuisine + timeOfDay). Reply echoes the tokens it filtered on
  so the user sees what was matched.
  **Limitations of step 1 (kept as the structural follow-up FU-152):**
  the matcher is still keyword-list + token-substring, with no
  proper slot extraction or query parser. Stopword list is
  hand-coded; synonyms ("veggie" → "vegetarian") aren't resolved;
  composite phrases ("gluten free" survives because the tag name
  matches, but two-word tags + free-text terms in the same
  message can produce surprising AND-filters). The redesign in
  FU-152 spec's the real fix; this RESOLVED-MINIMAL fixes the
  user-visible "vegetarian"/"asian" failure mode now.

## [OPEN] FU-152 — Chat-mode design: tokenise → slot-extract → filter (structural)
- **Raised:** 2026-06-12 (offshoot of FU-150's minimal fix)
- **Type:** design / structural improvement
- **What:** The current chat is a "first-match-wins keyword
  matcher" with hand-curated `matches[]` per intent + a handler
  that pulls "the noun after a preposition" and substring-searches
  recipe fields. FU-150 step 1 broadened the trigger list +
  switched the handler to whole-message tokenisation, which is
  enough for the dietary/cuisine cases but still scales linearly
  in keyword count and produces brittle behaviour for compound
  queries.
- **Proposed redesign (two axes):**
  1. **Vocab-derived triggers.** Load Cuisine + DietaryTag +
     Tool catalogues at chat init. Each catalogue contributes
     its names to a "term → intent" prior so the matcher knows
     "vegetarian"/"asian"/"slow cooker" all route to
     `find_recipe`. Auto-updates when the user adds new vocab.
  2. **Slot extraction**, separate from intent detection. After
     the intent fires, walk the message once and capture
     `slots: {cuisines[], dietaryTags[], timeOfDay?,
     stockItems[], freeText}`. Handlers consume slots
     declaratively — `filterRecipes({ dietary: ['vegetarian'],
     cuisine: 'asian' })` — instead of doing ad-hoc substring
     searches.
  3. **Intent scoring (optional)**: replace first-match-wins
     with a scoring pass per intent (each contributes keyword
     hits + vocab hits + structural cues). Highest-score intent
     wins, tie → fallback. Catches "i'm hungry, what veggie
     thing can I make?" routing to `whats_for_dinner` with a
     dietary slot, rather than tripping `find_recipe` because
     "recipe"-ish keyword fired first.
  4. **Reply transparency**: show the slots the handler
     applied ("Filtering by: vegetarian + asian"). Already
     present in FU-150 step 1 via `queryDisplay`.
- **Why deferred:** step 1 covers the immediate UX failure; the
  full slot-extraction redesign is a separate, focused work
  unit. Pair with the AI-mode sweep — the slot extractor is the
  same shape of work whether the route resolves into the
  rule-engine handler or the LLM handler.
- **Recommended resolution:** later — pair with AI-mode design.

## [OPEN] FU-146 — Sweep external GitHub-issues references — DONE
- **Raised:** 2026-06-12 (user browser verify of FU-085: "should
  remove any mention of github issues as the repo is now private")
- **Type:** finding / hygiene
- **What:** Dora-bot fallback bank, `report_issue` intent + its
  `externalLink`, the `whats_new` "See latest release on GitHub"
  link, `HelpPage` "Report a bug" header button + Help-tab repo
  list + issues list, `AboutSettings` repo + bug-report items,
  and `PageErrorState`'s pre-filled GitHub-issues URL all linked
  to `github.com/BenTalese/DiscountDora` — a now-private repo.
- **Resolved:** 2026-06-12 — replaced the FALLBACK_REPLIES bank +
  `report_issue` intros to drop the GitHub framing; retired the
  externalLink on `fallback` + `report_issue` (Help-nav stays);
  retired the `whats_new` release URL; pulled the four GitHub
  buttons/items from `HelpPage` + `AboutSettings`; retired
  `PageErrorState`'s `reportUrl` + the "Report this" button (the
  `showReport` prop stays so a self-host operator can restore a
  similar surface pointing at their own report sink).
  **Note:** the `report_issue` intent itself stays — it's a
  useful "I found a bug" affordance — but it now navigates to
  Help instead of pointing at an external tracker.

## [OPEN] FU-143 — Backfill `picked_offer_price` for legacy lines
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl)
- **Type:** deferred job (optional)
- **What:** Chunk 6 moved the offer-price snapshot from
  *tick* to *add* / *select*. Rows created before this change
  with a non-NULL `selected_product_id` but NULL
  `picked_offer_price` (never ticked) won't have a snapshot
  until the user later ticks them (the belt-and-braces hook
  at `manage_shopping_list_lines.py` UpdateLineHandler tick
  path + the finish-list fallback at `manage_shopping_list.
  py:212-215`). A one-off script could snapshot-fill every
  legacy row with `selected_product_id IS NOT NULL AND
  picked_offer_price IS NULL`, picking the current offer for
  the chosen product.
- **Why deferred:** Optional. The belt-and-braces paths drain
  legacy rows organically; nothing breaks if a never-ticked
  legacy row stays unsnapshotted (it just doesn't appear in
  budget / waste aggregates until ticked). At pre-release
  scale this is fine to skip.
- **Recommended resolution:** opportunistic — only worth
  doing if a user later complains "budget number doesn't
  match what's in my old draft lists". Then a small Alembic
  data migration or one-shot script clears the deficit in a
  single pass.

## [OPEN] FU-134 — Audit other `autoGenerate` call sites for Axis-B routing
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up
- **What:** The meal-plan "Generate shopping list for this week" button
  now offers add-to-existing vs. create-new via Axis B. Three other
  `shoppingListApi.autoGenerateAsync` call sites were left alone:
  - `web_app/src/components/dialogs/NewListDialog.vue:416` — already
    explicitly picks/creates a target list before generating; no change
    needed (already Axis-B-aware by construction).
  - `web_app/src/pages/RecipesOverview.vue:1153` — recipe "add all
    missing to a new list" path. Acceptance candidate for the same
    treatment (the proposal puts recipe bulk-add under variant="bulk"
    via the `AddToListButton`, which is the longer-term home).
  - `web_app/src/layouts/MainLayout.vue:291` — global/keyboard
    shortcut entry. Check whether this should also offer Axis B or
    is intentionally always-new.
- **Why deferred:** out of Chunk 4's documented scope (`PROPOSAL_CART_
  BUTTON.md §5` surface 10 is meal-plan generate only). Scope discipline
  (R-007) — flag, don't drift.
- **Recommended resolution:** opportunistic — re-evaluate when the
  `AddToListButton variant="bulk"` work lands for recipes (FU-131
  vicinity) and again when the global shortcut surface gets touched.

## [OPEN] FU-133 — Promote generate-target picker into a shared `TargetListPicker`
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up (R-001 carve-out)
- **What:** `pickGenerateTarget` in
  `web_app/src/pages/MealPlansOverview.vue` is a one-shot `$q.dialog`
  radio picker (drafts + "+ Create new"). If a second surface needs
  the same shape (likely candidates: FU-134 audit, future bulk
  add-all-missing flows), extract it as
  `components/dialogs/TargetListPickerDialog.vue` with props
  `{ drafts, allowCreateNew, title?, message? }` and one resolved
  payload type `{ kind: 'existing', id } | { kind: 'new' } | null`.
- **Why deferred:** single consumer today — promoting now would be
  speculative abstraction (R-001 judgement carve-out).
- **Recommended resolution:** when FU-134's audit lands a second
  consumer.

## [OPEN] FU-144 — Cart-state awareness for product-anchored adds
- **Raised:** 2026-06-12 (FU-131 impl)
- **Type:** follow-up
- **What:** `AddToListButton variant="inline-product"`
  doesn't show "on a list" state today — `cartStateFor` keys
  on `stock_item_id` and a product-anchored button has none.
  Result: a user can re-click "Add as product" on the same
  product and get a second product-only line (the backend's
  dedupe catches it and the toast reads "Already on your
  list", so it's safe — just not as informative as the
  stock-item variant). A parallel membership index keyed on
  `product_id` would let the button render the same
  on-list / on-multiple states the stock-item variant does.
- **Why deferred:** out of FU-131's documented scope (the
  three named pieces shipped); product-anchored membership
  is a server-side extension that touches the
  `Membership` DTO + how its `items` array is keyed.
- **Recommended resolution:** when a third product-anchored
  consumer of `AddToListButton` shows up, or when a user
  reports the double-add UX as a problem.

## [OPEN] FU-108 — Reorder Cookbook overview filters by usefulness
- **Raised:** 2026-06-10 (FU-083 follow-up; user, after the bug pass)
- **Type:** finding / UX polish
- **What:** The filter bar in `RecipesOverview.vue` lays controls out
  in the order they were added, not in the order users reach for
  them. The chip cluster (Favourites / Cookable now / Have meals in
  pool / Planned), the numeric inputs, the single-select dropdowns
  (Collection / Cuisine / Category), and the multi-select pickers
  (Uses ingredients / Doesn't use / Dietary / Tools) should be
  ordered by how often users actually flip them — most-used first,
  long-tail later. Pure template reorder, no logic changes.
- **What "useful" means here (open):** the user reads this. A
  reasonable starting cut: **(1) Favourites, Cookable now,
  Planned, Have meals in pool** (the quick-pick chips stay first
  because they're zero-effort); **(2) Cuisine, Category** (single-
  select, common during "what should I cook tonight?"); **(3) Uses
  ingredients / Doesn't use** (when fridge-clearing); **(4) Dietary
  + Tools** (occasional); **(5) Meals ≥ / Missing ingredients ≤**
  (numeric refinement); **(6) Collection** (visual grouping, almost
  set-and-forget). Confirm before moving — the actual answer is the
  user's, not the data's.
- **Recommended resolution:** opportunistic — fold into the next
  pass that touches this template. 10-minute job.

## [OPEN] FU-104 — Move the URL recipe importer into the private companion app (legal posture)
- **Raised:** 2026-06-10 (user, during Cookbook Chunk 7 review)
- **Type:** policy / distribution-posture decision (cross-cutting)
- **What:** The URL importer (`features/recipes/import_recipe_from_url.py`
  + the SPA dialogs added in Cookbook Chunk 7) **fetches third-party
  pages and extracts content** — schema.org JSON-LD for the happy path,
  raw `<title>` + body text in the degraded path. That's
  user-initiated, single-page, and modest-scale, but it's still:
  - **automated retrieval of copyrighted content** (recipe text /
    instructions are often editorial copyright, even if individual
    ingredient lists aren't);
  - **likely against most recipe-site ToS** (which boilerplate-ban
    scraping / automated access);
  - **fetched from our server's IP** in the current shape, not the
    user's browser — so the *operator* of a hosted Dora instance is
    the one making the request, not the user. That's the part most
    likely to attract a takedown letter / IP block / CFAA-style
    claim if it ever runs at scale on a public managed instance.
  - **CDN-fingerprintable** at scale via the `_FETCH_HEADERS`
    user-agent.
  The IMPL_PLAN_COOKBOOK shape lets it live anywhere; the master
  `RECONCILED_FINISHING_PLAN.md` Decision 1 already moved the
  **retailer scraper** out of the core app for the same reason (the
  precedent is established).
- **What this FU is asking us to decide:**
  - **Move the importer into the private companion app** (the same
    self-hosted / "personal-use, off-by-default, runs on the user's
    machine, hits sites from the user's own IP" surface that owns the
    retailer scraper). Core Dora keeps the schema (Recipe.source,
    structured steps, the create endpoint that accepts the parsed
    DTO) — the *fetcher* is what relocates.
  - **Or:** keep it in core but switch the architecture so the
    *browser* fetches the URL (CORS-permitting only — recipe sites
    rarely allow CORS, so practical coverage drops to maybe 10%) and
    posts the HTML up to the parser. Lower legal exposure but a much
    worse import experience.
  - **Or:** keep as-is, scope it as a personal-instance feature
    documented as "use only on URLs you have permission to scrape"
    + drop the named-site list in the dialog copy so we're not seen
    as encouraging it.
- **Why discuss now (not later):** the importer just got a more
  visible surface (overview button) in Chunk 7 + a graceful-degrade
  path that *succeeds* even on no-JSON-LD pages, which broadens the
  set of URLs it'll get pointed at. Better to settle the posture
  before users get used to the current shape and the named-site copy.
- **Constraints to honour in the decision:**
  - **Distribution posture (R-005):** core stays SaaS-style /
    self-hostable from one codebase. Moving the importer to the
    companion app means defining a clean "companion sends parsed
    DTO to core" boundary (companion is its own deployable; core
    treats it as an authenticated source of preview DTOs).
  - **Charter principle P10 Anti-creep:** don't bake "scrape any
    URL" into core if the legal answer is uncertain.
  - **Charter principle P1 Effortless:** users still expect the
    feature to work — the answer can't be "we removed it"; it can be
    "you run a companion locally and it stays effortless from your
    perspective".
- **Recommended resolution:** **discuss + design with user before
  next prompt that touches the importer.** Surface to a proposal
  doc (`docs/04_proposals/IMPORTER_DISTRIBUTION_POSTURE.md` or
  similar) once a direction is picked. Likely outcome: move the
  *fetcher* to the companion app (precedent: retailer scraper),
  keep the *parser* + Recipe.source schema in core. Until then, no
  new public-facing surface should advertise the importer (so:
  Chunk 7's overview button + named-site copy is fine for the
  self-hosted single-user case but should be flagged on any
  managed-instance / multi-user deployment as the next prompt
  here.) — see also `RECONCILED_FINISHING_PLAN.md §7.5` for the
  distribution-posture checklist this needs to pass.

## [OPEN] FU-095 — RecipeEditDialog (quick-create) has no structured-steps surface
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The quick "New recipe" dialog (`RecipeEditDialog.vue`) only
  collects the basics — name, ingredients, cuisine/category, tags, tools,
  image. Structured steps were intentionally **not** added to keep the dialog
  lean for the common "create a stub then edit it" workflow. Users add
  structure via the detail page's Structured/Freeform toggle. If a future
  prompt makes the dialog the primary create path (or users complain about
  switching to detail), wire the `RecipeStepsEditor` into the dialog with
  the same `steps_mode` toggle.
- **Recommended resolution:** opportunistic / when next touching the dialog.

## [OPEN] FU-085 — Run + verify Cookbook Chunk 2 (tag taxonomy overhaul) in a real env
- **Raised:** 2026-06-09 (Chunk 2 implementation; nothing was run — no Python venv / node_modules on the Windows dev box)
- **Type:** finding / verification (blocks trusting Chunk 2)
- **What:** Chunk 2 is a large, unrun backend+frontend change (FK-ify cuisine/category, DietaryTag table, 3 CRUD endpoints + settings, tri-state filter). Verify, in order:
  1. `alembic upgrade head` applies cleanly on **SQLite and Postgres** (migration `a7d2f4c9e1b8`: batch-mode Recipe alter dropping cuisine/category strings + adding cuisine_id/category_id FKs, RecipeTag rebuild to dietary_tag_id, vocab seed). Also test `downgrade`.
  2. App boots — `verify_mappings()` passes for Cuisine/Category/DietaryTag + the reshaped Recipe (risk: the `_cuisine_id`/`_category_id` hidden-FK mapping + the selectin relationships).
  3. `repository.get(Recipe).all()` actually selectin-loads `recipe.cuisine`/`.category` (assistant + global_search depend on it; if not, they'll show null cuisine/category).
  4. Recipe create/update/list round-trips `cuisine_id`/`category_id`/`dietary_tag_ids`; `GET /recipes/tags` returns DB-backed tags (value = id) + disclaimer.
  5. Overview: cuisine/category single-selects filter; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows cuisine/category names + tag chips.
  6. Edit dialog + detail page: cuisine/category selects + dietary multiselect populate from existing recipe + save correctly; URL importer pre-fills matched cuisine/category.
  7. Settings → "Recipe tags & categories": create/rename/delete for all three vocabularies; usage counts + delete warnings; deleting a cuisine/category nulls recipes (SET NULL), deleting a dietary tag removes the links (CASCADE).
  8. Backup → restore round-trips Cuisine/Category/DietaryTag/RecipeTag in FK-correct order.
  9. Dora assistant: search_recipes/suggest_recipes still filter by cuisine + dietary tags (now Python-side / name-resolved).
- **Recommended resolution:** now / first thing once a working env is available — before building Chunk 3+ on top.
- **State note:** 2026-06-09 — first user browser pass: migration applied + app boots + settings CRUD + add-modal dietary tags all **confirmed working** (items 1,2,4,7 effectively ✅). Two gaps found: (a) overview filters unusable → split out as **FU-087**; (b) no dietary-tag editor on the detail page (only the add modal) → **fixed** (added a multiselect to `RecipeDetailPage.vue`, L264). Still to verify: items 3 (selectin), 5 (filters), 6 (detail-page tags), 8 (backup), 9 (assistant).
- **State note:** 2026-06-12 — second user browser pass surfaced
  five concrete findings split out as their own FUs (so FU-085
  doesn't become an umbrella for everything cookbook-shaped):
  - **FU-146** (RESOLVED this session) — GitHub-issues mentions
    swept out (repo private).
  - **FU-147** — detail-page dietary-tag picker doesn't
    pre-populate + chips clear after save (item 6 partial fail).
  - **FU-148** — Cookbook overview missing "time of day" filter.
  - **FU-149** — Cookbook overview missing "# ingredients"
    filter + sort axis.
  - **FU-150** — assistant chat-mode doesn't recognise dietary
    or cuisine queries (item 9 partial fail).
  FU-085 itself stays OPEN until items 3 (selectin), 5 (filters
  end-to-end), 6 (FU-147 fix verified), 8 (backup), 9 (FU-150
  fix verified) are all green.

## [OPEN] FU-312 — Pre-existing eslint error in `StockItemRow.vue` waste-undo handler
- **Raised:** 2026-06-26 (surfaced during FU-209 verification)
- **Type:** finding (pre-existing lint regression)
- **What:** `web_app/src/components/stock/StockItemRow.vue:635` — the Undo
  action handler on the wasted-item toast is an `async () => { ... }`,
  passed where Quasar's notify action expects a `void`-returning handler.
  eslint flags: `@typescript-eslint/no-misused-promises — Promise-
  returning function provided to property where a void return was
  expected`. Confirmed pre-existing (stash-test against `ecd24e5` reproduces
  it without any of today's changes); the regression came in with the waste
  feature back in commit `318e98f`.
- **Why deferred:** out of scope for FU-209; the waste surface isn't being
  touched in this session.
- **Recommended resolution:** wrap the awaited block in a synchronous
  fire-and-forget (`void (async () => { ... })()`) or drop the `async`
  and use `.then()/.catch()` so the handler returns `void`. ~5 line fix.

## [OPEN] FU-065 — Ticked-summary string duplicated across both finish dialogs
- **Raised:** 2026-06-08 (Chunk 3 impl)
- **Type:** finding (R-003 lite — same display string built in two places)
- **What:** `ShoppingListDetail.vue` and `ShoppingListShopMode.vue` each build the "N items will be bumped to Well-Stocked: a, b, c, and N more." string for their respective Finish-and-restock dialog. Identical algorithm, two copies. If the wording or cap-count changes, both need editing.
- **Why deferred:** extracting a single helper is one line of value today; both copies are 4-line, Type-C display logic, and the two dialogs *do* differ (Detail has the copy-unticked-to-new-list radio, ShopMode appends a one-line note). Worth a helper only if a third caller appears, or if the wording becomes prose worth localising.
- **Recommended resolution:** opportunistic — when C-locale (FU-043) lands, fold both summaries through one localised builder. Otherwise leave alone.

## [OPEN] FU-056 (partial) — Phase 2 ingestion EAN auto-populate
- **Raised:** 2026-06-07 (P6-02); slice 1 closed 2026-06-28 (hybrid model)
- **Type:** deferred job (Phase-2 scoped)
- **What's left after the 2026-06-28 hybrid landing:**
  - **Ingestion auto-populate** — when the ingestion API imports a
    retailer catalogue, it should populate `Barcode` from the feed's
    EAN/UPC field automatically so most barcodes resolve without manual
    registration. Just calls `POST /api/data/barcodes` with
    `product_id` set; logic + endpoint already in place. Blocked on the
    ingestion API itself.
  - **Product detail EAN field** — when the Products UI gets touched,
    add a single-EAN row (gated on `features.products`). Uses the same
    endpoint. Per-Product UNIQUE constraint already enforced
    server-side ("one Product = one EAN").
- **Recommended resolution:** Phase 2 ingestion + the Products UI work,
  whichever lands first.

## [OPEN] FU-052 — Switch cookable surfaces to the server query + optimise the helper
- **Raised:** 2026-06-07 (Phase 1 Chunk 4 — queryable cookability)
- **Type:** follow-up
- **What:** Chunk 4 added the `?cookable` / `?max_missing` API + `cookable_count`,
  but the **shared-store surfaces still fetch all recipes and filter client-side**
  on `r.cookable` (RecipesOverview's cookable toggle / missing-max; the dashboard
  "Cookable tonight" list). Proposal step 4 ("switch the cookable surfaces to
  query") isn't finished. Two parts: (a) make those surfaces *query* the server
  (tricky — the recipes Pinia store is shared and does multi-facet client filtering,
  and the dashboard top-3 needs server-side sort+limit, currently client-sorted by
  favourite/last-made); (b) `load_recipe_cookability` loads **all recipes + full
  ingredient trees** on every dashboard summary and every cookable-filtered query —
  one query (not N+1) and fine at personal scale, but a set-based `COUNT(...) GROUP
  BY recipe` would scale better (watch SQLite/Postgres portability — avoid engine-
  specific `FILTER`).
- **Why deferred:** the store rewire is a real refactor needing browser verification
  (FU-051), and the perf optimisation is premature at current scale (R-007).
- **Recommended resolution:** **later — fold into the Type-B aggregates pass / when
  recipe counts grow.** Backend capability already exists; this is the client
  adoption + optimisation tail.

## [OPEN] FU-044 — C-help opt-in help-overlay brief written; awaiting approval + per-surface hint rollout
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_HELP_OVERLAY.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** A persistent "?" toggle overlaying dismissible per-element "what does
  this do" hints — the opt-in inverse of the forced tour C-5 removed. Net-new
  cross-cutting front-end component (no existing tour/coachmark system). The
  expensive part is **content** (a hint per control, kept from rotting), so the
  brief defers the hint corpus to a per-surface rollout folded into each C-1..C-9
  implementation prompt.
- **Why deferred:** brief-only per the Wave-C ritual; no code until the user
  approves and resolves §4 open decisions (reveal style, content model, mascot,
  discoverability).
- **Recommended resolution:** **when the user approves the brief** — build the
  mechanism + `v-help` directive first (§8.1), then seed hints on the highest-
  confusion surfaces, then roll out per-surface as each C-brief implements. Pair
  the C-5 finish-card mention (§4-4) with C-5 implementation.

## [OPEN] FU-043 — C-locale international-readiness brief written; awaiting approval
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_LOCALE_I18N.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** Make Dora usable outside Australia. Companion split solves product
  sourcing; Dora-core still has AU residue — hardcoded `$` currency, `en-AU` voice
  default (`useVoiceInput.ts`), AU merchant branding/copy/seed in core, and a
  **dormant vue-i18n scaffold** (installed in `boot/i18n.ts`, locale hardcoded
  `en-US`, stub messages, zero `$t()`). Brief recommends Layer A (currency/format
  neutrality) + Layer B (de-AU core) now; Layer C (full UI translation) deferred.
- **Why deferred:** brief-only; no code until approval + §3 open decisions
  (currency home, vue-i18n adopt-vs-rip, C-10 currency field, merchant-logo fate).
- **Recommended resolution:** **when the user approves** — fold the currency
  setting + shared money formatter into the C-cross config work (they share the
  config layer); coordinate the C-10 currency field with the ingestion impl;
  de-AU (voice/branding/seed) is independent and low-risk. Layer C stays parked.

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
- **2026-06-16 (C-5.1) re-confirm:** re-read the initial migration
  (`6e127e3cfa54`) — it only `bulk_insert`s **stock levels** and `create_table`s
  StockGroup/StockLocation (schema, no rows). The 8d3f/e9c2 migrations are
  schema-only. So **no migration inserts group/location rows**; the "already
  have" copy can only fire against `seed_dev_data()` output (dev dataset). Still
  needs a live clean-DB confirmation per the reported-defect rule.
- **Recommended resolution:** **confirm in browser** on a genuinely fresh DB
  (register first user → onboarding) that the "already have" copy does NOT appear
  and the seed checkboxes are enabled. If it DOES appear, find what's seeding user
  groups/locations and fix. **Folded into FU-192** (C-5.1 browser smoke).

## [OPEN] FU-032 — C-2: allocation count doesn't decrement after planner drop (live repro, root cause TBD)
- **Raised:** 2026-06-06 (C-2 recon); user repro confirmed 2026-06-12
- **Type:** finding (real bug, not yet root-caused)
- **What:** User dragged recipes from the palette onto future days; the
  chip's count next to the recipe name didn't change. Static read of
  the data path looks correct end-to-end:
  - Frontend `MealPlansOverview.onDropOnDay` → `persistEntries` →
    `mealPlanStore.updateMealPlanAsync` awaits the PATCH **and** the
    follow-up `getMealPlansAsync`, then in parallel
    `recipeStore.getRecipesAsync()` runs.
  - Backend `UpdateMealPlanHandler.handle` calls `save_changes()`
    before returning (commit guaranteed).
  - Backend `_hydrate_unallocated` (`get_recipes.py:591`) issues one
    GROUP BY against `MealPlanEntry` filtering
    `consumed_at IS NULL AND scheduled_for >= today AND recipe_id IN :ids`
    and subtracts from `available_meals`.
  - Frontend chip ([MealPlansOverview.vue:101](web_app/src/pages/MealPlansOverview.vue#L101))
    is `(N) = recipe.unallocated_meals` bound through
    `storeToRefs(recipeStore).recipes` — reassigning `recipes.value` in
    `getRecipesAsync` should trigger re-render.
- **Possible runtime causes (none verifiable without devtools):**
  1. **User is reading `available_meals` not `unallocated_meals`.** The
     chip shows `(unallocated_meals)` next to the recipe name; the
     click-menu shows `available_meals` as the big number. Drops only
     decrement `unallocated_meals` (cooked pool unchanged — that only
     moves on Cook / ± adjust). Worth confirming which number the user
     is tracking.
  2. **Reactivity edge case** with `storeToRefs` + sorted array
     reassignment. Unlikely but only visible at runtime.
  3. **`scheduled_for` date comparison** — backend filters
     `scheduled_for >= :today` using `date.today()` (server local).
     Drops on "today" land on the boundary; future drops shouldn't be
     affected. Cross-timezone client/server could in theory miss a
     same-day entry — unlikely with future drops.
- **C-2 redesign cross-ref:** `PROPOSAL_MEAL_PLANS.md §3.1` re-renders
  the same numbers (`(unallocated / pool)` chip — emphasised on the
  recipe row) and `§3.2` reworks the entry chip shape. The C-2 work is
  **design only — no impl plan yet**, so the chip surface in production
  isn't going to change soon. Don't defer the bug fix to "when C-2
  lands."
- **Recommended resolution:** when the user is next at a browser:
  1. Confirm whether the unchanging number is the `(N)` next to the
     recipe name (real bug) or the bigger `{{ available_meals }}` in
     the click-menu card (expected behaviour, not a bug).
  2. If the `(N)` is genuinely stuck, capture the network response from
     `GET /api/recipes` immediately after the drop — does the JSON
     show the new `unallocated_meals`? If yes, it's a frontend
     reactivity bug; if no, it's the backend's SUM not seeing the new
     row (transaction visibility / date filter).
  3. With that one bit of evidence the root cause collapses to either
     a Vue reactivity patch or a backend date / commit-visibility fix.

## [OPEN] FU-025 — A6 text scale: many surfaces still don't respond (likely needs its own sweep)
- **Raised:** 2026-06-05 (A6); user-verified gap 2026-06-12
- **Type:** finding (real, app-wide)
- **What:** Initial A6 in-browser check (2026-06-12) confirmed the scale
  steps themselves are working at the page level, BUT user observed that
  **a lot of secondary text still doesn't change size** when the scale is
  changed — e.g. **button labels, input text, toggle labels**, and likely
  other component-internal text. These almost certainly use Quasar's
  component CSS (`font-size` declared inside `.q-btn__content`,
  `.q-field__native`, `.q-toggle__label`, etc.) which doesn't inherit from
  the page-level rem-scaling tokens A6 set up. Fixing this is broader than
  any single page — likely a Wave-A-style "global pass" prompt that
  overrides the component-internal font-sizes to track the text-scale
  variable (or replaces hard-coded px with the same `rem`/var the body
  text already uses).
- **Why deferred:** out of FU-025's verify scope; needs its own sweep.
- **Recommended resolution:** now-ish — promote into a small Wave-A-shaped
  prompt ("A6b: text-scale follow-through into component-internal text").
  Audit method: grep `font-size` in `web_app/src/css/quasar.variables.scss`
  / overrides, plus a runtime walk through Stock Overview + a form-heavy
  page (Recipe edit, Stock-item detail) at Small vs Extra-large; list each
  surface that doesn't visibly change and convert its `px` to the same
  text-scale var. Deliberately-fixed-px carve-outs (ScanOverlay camera UI,
  PriceHistoryChart SVG labels, Dashboard 3px/7.5px micro-gauge) stay.


## [OPEN] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up)
- **Type:** finding
- **What:** The onboarding "dead button" bug was a stale `authStore.currentUser`
  read by the router guard after `onboardingApi.completeAsync()` updated the
  backend. The same shape could exist for any flow where the backend mutates
  user-scoped state that a guard or computed reads from a frontend cache —
  candidates worth scanning: account changes (email/role/admin flag), data
  import/restore, restart-onboarding. (Stock-item Undo restore was a candidate
  here too; removed with the app-wide undo posture per FU-163.) Look for
  `currentUser?.*` reads in router and layout guards, and pair each with the
  store mutation that should refresh them.
- **Why deferred:** out of B5's bug-fix scope; cross-cutting audit.
- **Recommended resolution:** opportunistic — fold into a Wave-A or polish
  pass once one obvious symptom shows up; not worth a dedicated session.

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

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

