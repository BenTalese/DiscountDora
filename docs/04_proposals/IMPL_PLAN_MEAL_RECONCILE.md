# IMPL_PLAN — Manual meal-plan reconcile ("stocktake mode for meals")

**Origin.** Executes [PROPOSAL_MEAL_RECONCILE.md](./PROPOSAL_MEAL_RECONCILE.md)
(FU-317). Read that first — this plan is chunk-level *how*, not *what*.

**Status:** 🔵 designed-not-built. Six chunks; every chunk lands independently
green and produces a shippable partial. Chunk 1-4 are backend-only (no
user-visible change); chunk 5 lights up the surface; chunk 6 is the settings
row + copy polish.

**D5 resolved 2026-07-09 (FU-517).** Setting is install-wide
`AppSetting.auto_drain_past_meals`. Chunk 1 unblocked.

**Residuals locked (proposal §11).**
- **D1 — `meal_reconcile_overdue` threshold.** Fires when **≥ 3 unresolved
  entries** stretch back **≥ 4 days**. Matches the "half-week-of-dinners"
  vocabulary that the stocktake bands already use.
- **D2 — `cook_recipe` × auto-drain-off coupling.** Kept **independent**.
  A user pressing "finished cooking" is a positive action that should freely
  bump the pool; reconcile is only for planned-but-unconfirmed entries.
  Anti-creep: no coupling that a user with the default posture would have to
  reason about.
- **D3 — Receipt retention.** Keep **forever**. Row count is ~1 per planned
  meal ever — negligible at any realistic household scale, and a "meals I
  cooked, historical" report is a plausible future ask.
- **D4 — Setting copy.** Use *"Assume I cooked past-day meals"* as the row
  label + *"When on, Dora assumes you ate meals as planned. You can dispute
  anything on the Reconcile past meals page. When off, past meals stay
  pending until you confirm them."* as the explainer. Final phrasing polish
  is fair game during Chunk 6.

---

## Anti-drift required reading (before running this plan)

- [PROPOSAL_MEAL_RECONCILE.md](./PROPOSAL_MEAL_RECONCILE.md) — the whole
  proposal, all sections. **Non-negotiable.**
- [`RECONCILED_FINISHING_PLAN.md`](../01_charter/RECONCILED_FINISHING_PLAN.md)
  §5 Phase 1 (close-the-loop) + §7.5 distribution-posture checklist.
- [`ENGINEERING_STANDARDS.md`](../01_charter/ENGINEERING_STANDARDS.md) —
  R-003 (state-ownership), R-005 (distribution posture), R-006 (clean
  migrations), R-029 (hide-don't-nag), R-031 (constructor DI via Protocols).
- [`DASHY_DORA_CHAMPION_PLAN.md`](../01_charter/DASHY_DORA_CHAMPION_PLAN.md)
  Part II Charter — P1 Effortless, P3 Honest, P4 Preservation of trust,
  anti-creep tiebreak.
- The **reference implementations** — mirror their shape verbatim:
  - [PROPOSAL_STOCKTAKE_MODE.md](./PROPOSAL_STOCKTAKE_MODE.md) +
    [StocktakeRunner.vue](../../web_app/src/pages/StocktakeRunner.vue)
    for the runner UX.
  - `MealPlanSwapLedger` (introduced by FU-451) for the append-only
    receipt shape.
- [MAGIC_BEHAVIOUR_AUDIT.md § F5/F6](../05_investigations/MAGIC_BEHAVIOUR_AUDIT.md)
  — the origin, and the description of the current sweep that this plan
  replaces.

---

## The six chunks

### Chunk 1 — Schema + append-only receipt writer (backend, no UX)

**Ships:** the data model + a working receipt writer plumbed into the
existing `before_request` sweep. **No user-visible change** — after this
chunk, the app still behaves like today for every user; the receipt table
is being populated in the background and the setting exists but nothing
reads it yet.

- **Migration** (alembic, forward-only, additive):
  - Add `AppSetting.auto_drain_past_meals BOOLEAN NOT NULL DEFAULT TRUE`
    (D5 install-wide — FU-517 resolved).
  - Create `MealPlanReconcileReceipt` table with the columns listed in
    proposal §7.1: `id` (uuid PK), `meal_plan_entry_id` (uuid FK →
    `MealPlanEntry.id`, `ON DELETE CASCADE`), `state` (enum text —
    six values from §7.1), `original_servings` (int),
    `actual_servings` (int nullable), `cooked_on` (date nullable),
    `resolved_by_user_id` (uuid FK → `User.id`, nullable, `ON DELETE
    SET NULL`), `resolved_at` (datetime nullable, tz-aware),
    `note` (text nullable), `created_at` (datetime NOT NULL, tz-aware).
  - Composite index `(state, created_at)` for the queue query.
- **ORM classic-mapper table** — matches the existing meal-plan pattern.
  Do NOT use declarative here (repo convention is classic mapper for new
  domain tables).
- **Model + repository** — `MealPlanReconcileReceipt` model class;
  repository stays `SqlAlchemyRepository` (no new repo — this is a
  domain child of `MealPlanEntry`, added-through-the-existing-seam).
- **Wire the sweep to write receipts.** In
  [reconcile_consumed_meals.py](../../dora_api/features/meal_plans/reconcile_consumed_meals.py):
  - For every entry the `RETURNING` clause reports, `INSERT` one
    receipt row with `state='unresolved_auto'`, `original_servings =
    entry.servings`, `created_at = _Now`. Same connection-level
    transaction as the existing sweep.
  - `available_meals` decrement stays — this chunk does not yet touch
    `cook_recipe`'s arithmetic; the two authorities still exist and
    Chunk 2 collapses them.
  - Gate the sweep's mutation on the install-wide setting: read
    `AppSetting.auto_drain_past_meals` on the same connection (the
    row is already loaded elsewhere in the sweep for `timezone`, so
    fold it into the same `SELECT` — one round-trip). If FALSE, the
    sweep still runs its `SELECT` over past-day entries but writes
    receipts with `state='unresolved_manual'` and **does not** update
    `MealPlanEntry.consumed_at` and **does not** decrement the pool.
    Same table, same code path — the setting only decides the initial
    receipt state.
- **Tests** — `tests/e2e/dora_api/test_reconcile_receipts.py`:
  1. `AppSetting.auto_drain_past_meals=TRUE`, past-day plan present →
     sweep writes one `unresolved_auto` receipt + decrements pool
     (existing behaviour + the new row).
  2. `AppSetting.auto_drain_past_meals=FALSE`, past-day plan present →
     sweep writes one `unresolved_manual` receipt + **does NOT**
     decrement pool.
  3. Idempotence — re-running the sweep produces no additional
     receipts for entries that already have one (the
     `WHERE consumed_at IS NULL` guard still holds for auto-drain-on;
     for auto-drain-off we need a `NOT EXISTS` sub-select against the
     receipt table).
  4. Cascade delete — deleting a `MealPlanEntry` removes its receipts.

**Close-gate.** Full pytest green; new tests pass; `pip-audit` clean;
`vue-tsc` N/A. No CHANGELOG entry (nothing user-visible).

### Chunk 2 — Shared `Recipe.available_meals` mutation helper (R-003 collapse)

**Ships:** a single server-side helper that owns every mutation of
`Recipe.available_meals`. Removes the two-authorities-for-pool-count drift
between the raw `UPDATE "Recipe" SET available_meals = …` in the sweep and
`cook_recipe.py`'s `+= meals_cooked` arithmetic.

- **New helper** — `dora_api/features/recipes/pool.py`:
  - `def bump_pool(recipe_id: UUID, delta: int, conn=None) -> int:`
    — atomic `UPDATE ... RETURNING available_meals`, floors at 0
    on decrement, returns the new value. Accepts an optional
    connection for the sweep's connection-level transaction (per
    proposal §5.1's note that ownership is server-side + one place).
- **Rewrite call-sites.** The two current mutators — the raw SQL in
  `reconcile_consumed_meals.py:56-65` and `cook_recipe.py`'s inline
  handler math — both route through `bump_pool`. `ConsumptionEvent`
  writes stay where they are (they're a separate concern —
  P8-07 belief service, per proposal §5.2).
- **Rollback contract** — the helper never itself starts a
  transaction; callers own the transaction boundary. This preserves
  the sweep's "own connection, decoupled from per-request session"
  invariant.
- **Tests** — extend the existing `test_cook_recipe.py` +
  `test_reconcile_receipts.py` to exercise the helper's contract
  (delta > 0, delta < 0, delta that would take the pool below 0
  → clamps to 0).

**Close-gate.** Full pytest green. `grep -r "available_meals" dora_api/`
should show exactly one write-site (the helper); every other reference
is a read. Log any straggler as an FU rather than fixing silently.
No CHANGELOG entry.

### Chunk 3 — Reconcile queue + per-entry endpoints

**Ships:** the REST surface the SPA needs. **Still no user-visible change**
— the SPA doesn't call these yet.

- `GET /api/meal-plans/reconcile-queue?cursor=<opaque>&limit=<int>` —
  cursor-paged (default 30), oldest-first, grouped by `scheduled_for`
  (grouping done client-side; the response is a flat cursor page).
  DTO shape:
  ```json
  {
    "entries": [
      { "entry_id": "...", "scheduled_for": "2026-07-05",
        "recipe": { "id": "...", "name": "Beef stroganoff" },
        "planned_servings": 2, "slot": "Dinner",
        "receipt": { "state": "unresolved_auto", ... } }
    ],
    "next_cursor": "..." | null
  }
  ```
  Only entries whose *latest* receipt has state `unresolved_*` are
  included. Resolved-state entries can be surfaced by a separate
  `?include_resolved=true` param (for "let me see what I already
  confirmed" — same page, past section) but that's out-of-scope for
  MVP; add the param but return empty until Chunk 5 wires it.
- `POST /api/meal-plans/reconcile/<entry_id>` — body:
  ```json
  { "verb": "cooked" | "cooked_adjusted" | "not_cooked" |
           "cooked_later" | "skip",
    "actual_servings": 3,               // required for cooked_adjusted
    "cooked_on": "2026-07-08",          // required for cooked_later
    "note": "kids' portions" }          // optional
  ```
  Effects per proposal §3.2. Every verb (except `skip`) writes a **new**
  receipt row (never mutates the existing one — matches
  `MealPlanSwapLedger`). Idempotence: repeat call with same verb → 200,
  no additional row. Different verb → new corrective receipt.
- `PATCH /admin/settings` — extend the existing admin-only settings
  endpoint with `auto_drain_past_meals` in its input model + DTO. No
  new route. (`PATCH /auth/me` is *not* touched — the setting is
  install-wide, not per-user, per D5.)
- **Handlers** use constructor injection against `Repository` Protocol
  per R-031 / ADR-027 (no `get_container()`).
- **Rate-limit** — `POST /reconcile/<id>` uses the same per-user
  `subject` bucket introduced by FU-458: 60/min (matches
  `/assistant/act`; batch reconciles are plausible).
- **Tests** — `test_reconcile_queue.py` + `test_reconcile_verb.py`.
  Every verb, idempotence, cross-user isolation (household A's queue
  never surfaces on household B), cursor pagination, invalid-verb
  → 400, missing-required-field → 400.

**Close-gate.** Full pytest green. Postman/curl smoke: queue → verb →
queue-refreshed round-trip. No CHANGELOG entry (still backend-only).

### Chunk 4 — Alert + suggestion

**Ships:** the two surfacing signals — the alert kind + the suggestion
kind. Still no page for the user to walk, but the badges start pointing
somewhere real.

- **New alert kind `meal_reconcile_overdue`.** Following the
  [`PROPOSAL_ALERTS.md`](./PROPOSAL_ALERTS.md) + `ALERT_ROUTER` pattern
  used by every existing kind:
  - Enum member in `dora_api/features/alerts/kinds.py` (or wherever
    the current enum lives).
  - Resolver function that queries the reconcile queue and returns
    `overdue=True` when D1 fires (≥ 3 unresolved entries stretching
    ≥ 4 days back — read those from
    `dora_api/features/meal_plans/reconcile.py` constants; do NOT
    inline the numbers at the alert site).
  - `AlertPreference` gets the new kind added to its default map
    (default `severity='info'`, `enabled=true`).
  - Auto-clears when the queue empties (same shape every other alert
    uses).
  - Cross-user isolation: alert per user, queue per household. A user
    who disables the alert doesn't see the badge; another user in
    the same household still does.
- **New suggestion kind `reconcile_meals_pending`.** Dedup key
  `(kind, "queue")`. Accepting navigates to `/meal-plans/reconcile`
  (no mutation via the suggestion — proposal §6.3).
- **Tests** — extend `test_alerts.py` + `test_suggestions.py` for both
  new kinds. Threshold-crossing (2 entries at ≥ 4 days → silent;
  3 entries at ≥ 4 days → fires; 3 entries at 3 days → silent).

**Close-gate.** Full pytest green. Alerts panel + assistant surface both
render the new kind end-to-end when the server-side threshold trips.
Still no reconcile page — the deep-link goes 404. That's fine; Chunk 5
lights it up.

### Chunk 5 — Reconcile page + surfacing chips

**Ships:** the user-visible half. After this chunk the FU-317 feature is
functionally complete for the user.

- **New route** `/meal-plans/reconcile` → new
  `web_app/src/pages/MealReconcilePage.vue`. Structure mirrors
  `StocktakeRunner.vue` byte-for-byte (single-entry runner, empty
  state is a state of the runner not a landing page).
- **New components:**
  - `MealReconcileEntry.vue` — the per-entry card. Big primary
    **Cooked** button; secondary **Cooked (different portions)**
    opens an inline `q-input` for `actual_servings`; secondary
    **Cooked later** opens a `q-date` for `cooked_on`; tertiary
    **Didn't cook**; small **Skip for now**. Level-picker-style
    colour affordances not needed here (reconcile has no colour axis).
  - `MealReconcileCompletionScreen.vue` — five-counter recap
    (cooked / adjusted / not-cooked / cooked-later / still-open).
    "Done" button routes to `/dashboard`.
- **Dashboard chip** — new `ReconcilePastMealsChip.vue` mounted in
  the *Your Kitchen* zone next to the existing "Kitchen health" card.
  Hide-when-empty (R-029). One-line copy: *"Reconcile N past meals →"*
  with the meal-count derived from the queue-length endpoint (add a
  `HEAD /reconcile-queue` or a cheap `GET /reconcile-queue?limit=0`
  → response includes a `total` count; pick whichever costs less
  to compute in the existing handler).
- **Meal Plans header nudge** — a plain inline row above the
  calendar (`MealPlansOverview.vue`): *"N past-day meals need
  confirming →"*. Same hide-when-empty rule; same queue-length source.
- **Composable** — `web_app/src/composables/useReconcileQueue.ts`
  wraps the fetch + verb-submit + count-refresh. Every surface
  (page, chip, header nudge) reads through it so a verb submitted
  on the page invalidates the chip's count in the same tick.
- **Wire the pool refresh** — after any non-`skip` verb, invalidate
  the recipe-pool cache (`recipeStore.invalidate(recipe_id)`) so
  the pool count updates on adjacent surfaces without a page reload.
- **Tests:**
  - `tests/vitest` — happy path per verb, idempotence, empty state.
  - Manual browser walk added to `DORA_VERIFY.md` under a new
    **Meal Plans → Reconcile past meals** section.

**Close-gate.** `vue-tsc --noEmit` clean; vitest green; full pytest
green. CHANGELOG entry — `Added: Manual meal-plan reconcile page
(FU-317)`. `DORA_VERIFY.md` block added.

### Chunk 6 — Settings row + final copy polish

**Ships:** the last visible piece — the setting toggle — and a UX-copy
sweep across the whole feature.

- **Settings → Admin → System** gains a *"Meal reconciliation"* section
  (near the other install-wide meal-plan / stocktake blocks). Admin-only
  edit (`AppSetting`-backed). Add:
  - Toggle *"Assume past-day meals were cooked"* — writes
    `AppSetting.auto_drain_past_meals` via the existing admin
    `PATCH /admin/settings` endpoint (add the field to its input
    model + DTO; no new route).
  - Explainer copy (D4 above, updated wording — household voice, not
    per-user voice).
  - Link chip → `/meal-plans/reconcile` (visible to every user; the
    reconcile page itself is not admin-gated).
- **Copy sweep** through:
  - Reconcile page verbs (final labels + one-line helper text under
    each — pass to the UX-copy skill).
  - Alert copy (`meal_reconcile_overdue`).
  - Suggestion copy (`reconcile_meals_pending`).
  - Dashboard chip + meal-plans header nudge.
- **Feedback coverage** — after Chunk 6 lands, flip the three
  MR-anchored feedback bullets (MR-1 / MR-5 / MR-7) in
  [COVERAGE_GAPS.md](../02_feedback/COVERAGE_GAPS.md) from gap →
  covered.

**Close-gate.** `vue-tsc --noEmit` clean; vitest green; full pytest
green. CHANGELOG entry updated (`Added` block gains the setting row).
`DORA_VERIFY.md` block extended with the setting toggle. `[[FU-320]]`
gate item updated: the impl half of FU-317 is now done (already
struck-through by the proposal close-gate — extend the note to
"proposal + impl done, F5 help copy safe to write").

---

## Cross-cutting rules for every chunk

- **R-003.** No client-side derivation of pool counts, queue membership,
  or overdue-ness. Every derived fact ships from the server DTO.
- **R-005.** No raw SQL outside the shared repository seam. Portable to
  Postgres + SQLite as-is. New `AppSetting` rows: **none** (this feature
  is install-wide, `AppSetting` column only — D5 recommendation).
- **R-006.** Forward-only alembic migration; no schema mangling of
  existing tables; no backfill. The `MealPlanReconcileReceipt` table
  is populated forward-only from Chunk 1's deploy moment onwards.
  Historical past-day entries stay in whatever state today's sweep
  already left them (proposal §2).
- **R-029.** Every surfacing surface (dashboard chip, meal-plans header
  nudge, alert badge) hides when the queue is empty. Never a zero-state
  chip.
- **R-031.** Every new handler receives its `Repository` via ctor
  injection typed against the `Repository` Protocol.
- **No feature flag.** The install-wide default (`auto_drain_past_meals`
  = TRUE at Chunk 1's migration) *is* the kill-switch — an admin who
  wants to disable the whole feature flips the setting off, receipts
  keep flowing as `unresolved_manual`, and the reconcile page + alert
  remain functional. No separate feature flag needed.

---

## What's out of scope for this impl plan

- **Recurring plans + "past week goes read-only"** (feedback L369/L370).
  Adjacent — this plan makes past-day entries *reconcile-only-writable*,
  which is a partial step, but the full recurring-plan design lives in
  [PROPOSAL_MEAL_PLANS.md](./PROPOSAL_MEAL_PLANS.md).
- **Recipes-Overview presentation** of allocated vs on-hand
  (feedback L274/L275, MR-2/MR-3). Tracked under [[FU-432]] follow-on.
- **Cook-mode "not ready to cook" confirmation** (feedback L309). Cook
  mode gate, not reconcile. Not in this plan.
- **Historical "meals I cooked, ever" report.** D3 keeps receipts
  forever precisely so this can be built later; it's not in scope now.
- **F5's suggestion in the audit** — a "cookbook recent-cooked list"
  planning chip on the dashboard. Deferred; the reconcile page + chip
  is a strictly better version of the same surface for the same audit
  finding.

---

## Prompt entry point

Run this plan from a session that starts by:

1. Reading [PROJECT_STATE.md](../../PROJECT_STATE.md) (the front door).
2. Reading the top entry of [DORA_WORKLOG.md](../../DORA_WORKLOG.md).
3. Reading this file top-to-bottom.
4. Confirming the anti-drift required-reading list above is satisfied.
5. Picking the next unshipped chunk (start with Chunk 1 unless the
   worklog says otherwise).

**Do NOT** start with Chunk 5 or 6 — the backend chunks must land first
so the surface has something real to reflect. Chunks 1-4 can be
squeezed into a single session if it's a long one; Chunk 5 alone is a
half-day of SPA work; Chunk 6 is a quick tidy-and-copy pass.
