# PROPOSAL — Manual meal-plan reconcile ("stocktake mode for meals")

- **Status:** 🔵 designed-not-built — decisions **mostly locked from principle**;
  four residual calls flagged in §11 for a short user round before impl-plan.
- **Raised by:** [[FU-317]] (F5/F6 verdict in
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`).
- **Date:** 2026-07-09.
- **Governing docs:** `DASHY_DORA_CHAMPION_PLAN.md` Part II Charter
  (P1 Effortless, **P3 Honest**, anti-creep tiebreak),
  `RECONCILED_FINISHING_PLAN.md` §5 (Phase 1 close-the-loop),
  `ENGINEERING_STANDARDS.md` (R-003 state-ownership, R-005 distribution posture,
  R-006 clean migrations).
- **Cross-refs:** [MAGIC_BEHAVIOUR_AUDIT.md § F5/F6](../05_investigations/MAGIC_BEHAVIOUR_AUDIT.md),
  [reconcile_consumed_meals.py](../../dora_api/features/meal_plans/reconcile_consumed_meals.py),
  [startup.py:150](../../dora_api/startup.py),
  [PROPOSAL_STOCKTAKE_MODE.md](./PROPOSAL_STOCKTAKE_MODE.md) (the shape this
  brief borrows from).

---

## 1. The problem, framed

`reconcile_consumed_meals` is the **heaviest implicit behaviour in the app**
(F5 verdict, MAGIC_BEHAVIOUR_AUDIT): every dashboard / meal-plan / recipe
read silently marks past-day `MealPlanEntry` rows as `consumed_at = now()` and
decrements `Recipe.available_meals` by the entry's `servings`. No receipt.
No undo. No "did you actually cook this?" check.

That's a real problem for two reasons the charter cares about:

1. **P3 Honest.** A user who didn't eat a planned meal still has it drained
   from the pool — the number Dora shows disagrees with what actually
   happened. Silently. Every page load.
2. **P1 Effortless / anti-creep.** The rolling-day model *needs*
   reconciliation to work — without it, the pool never drops and every plan
   ages into a stale "still has meals waiting" claim. So the answer is not
   "delete the sweep", it's **make it honest**: show the receipt, allow the
   correction, and let the user pick the posture that matches how they cook.

Three separate questions were tangled into one implicit sweep. This brief
keeps them apart:

1. **Who** decides an entry was consumed? → the **posture** (§2).
2. **When** does the user confirm/amend? → the **manual reconcile surface**
   (§4-5).
3. **What** happens to existing signals when reconciliation is behind? →
   **interactions** (§6).

---

## 2. The two postures — auto-drain vs manual-confirm

**Install-wide setting** (`AppSetting.auto_drain_past_meals`), default **on**.
One knob, one question: *"Should Dora assume past-day plans were cooked?"*

> **2026-07-09 impl-plan discovery.** FU-317's original wording said
> "per-user setting". A codebase check found `MealPlan` has no `user_id` (or
> `household_id`) FK — meal plans are implicitly household-scoped. A per-user
> reconcile posture over a household-shared plan is incoherent: whichever
> user opens the app first effectively decides for everyone. Install-wide
> matches the data model and the anti-creep tiebreak (one authority per
> household). **Pending user sign-off** — see §11 D5. Impl-plan holds at
> "no Chunk 1 code" until confirmed.

- **On (default) — Auto-drain (today's behaviour + a receipt).** Past-day
  entries stamp `consumed_at = now()` on the daily rollover just like today,
  and `Recipe.available_meals` decrements. **New:** every auto-drained entry
  writes a receipt (§7) the user can walk through the manual reconcile page
  and *dispute per-entry* — flipping `consumed_at` back to `NULL` and
  re-incrementing the pool. **Effortless default** for people who plan
  loosely and don't want daily homework.
- **Off — Manual-confirm.** Past-day entries stay `consumed_at IS NULL`
  indefinitely. `Recipe.available_meals` **does not** decrement until the
  user explicitly walks the reconcile surface and confirms *"yes I cooked
  this"* / *"no I didn't"* per entry. **Honest by construction** for people
  who want the pool count to reflect reality every day.

**They coexist by design — not "mutually exclusive".** Same reconcile page,
same per-entry verbs. The setting only decides the *default* state of a
past-day entry when it first crosses midnight: **already-consumed
(disputable)** vs **unconfirmed (must be confirmed)**. Everything downstream
of that is identical. This resolves FU-317 question 4 by refusing the
false choice.

### Deliberate carve-outs

- **Install-wide, not per-user or per-recipe.** The meal plan is
  household-shared (no `user_id` on `MealPlan`); the posture must be too.
  Per-recipe knobs would be exactly the "invisible switch you forgot you
  set" problem the audit is trying to fix.
- **No third "prompt me each rollover" mode.** That's what the reconcile
  page *is*; making it a third posture would multiply state without adding
  a real behaviour.
- **Existing plans are not migrated.** The setting starts `true` for every
  user; the receipt table (§7) is populated forward-only. Historical past-day
  entries stay in whatever state today's sweep already left them.

---

## 3. The reconcile page — the "stocktake for meals" surface

Modelled on `StocktakeRunner.vue` — one queue, one entry at a time, small
number of verbs. **Route:** `/meal-plans/reconcile`. **Empty state:** a plain
"Nothing to reconcile — you're all caught up" card, not a landing screen.

### 3.1 The queue

An entry is **in the reconcile queue** when:

- `scheduled_for < today_in_household_tz`, **and**
- `consumed_at IS NULL` (auto-drain-off) **OR** it has an *unresolved
  reconcile receipt* (auto-drain-on and the user has not walked past it yet)
  — see §7.

Server-owned queue, cursor-paged so it degrades gracefully on the "haven't
opened Dora for three weeks" case. Chronological, oldest first. **Group
header per day** so the user knows the frame ("Monday · 8 Jul", one screen).

### 3.2 The verbs (per entry)

| Verb | Effect | Notes |
|---|---|---|
| **Cooked (as planned)** | `consumed_at = now()`; pool `-servings` if not already decremented; receipt marked *resolved-confirmed*. | Primary. Big button. |
| **Cooked (different portions)** | Same, but with a numeric step for "I actually made N meals-worth" — the pool math uses the corrected `servings` and stamps a `note` on the receipt. | Handles the batch-cook case (F5 → into the reconcile: L371 batch-vs-fresh). |
| **Didn't cook** | `consumed_at = NULL`; if the pool was already auto-decremented, `+servings` back; receipt marked *resolved-not-cooked*. **The entry stays on the plan as a historical "planned, not cooked"** — no delete. | Preserves the audit trail. |
| **Cooked later than planned** | Same as **Cooked** but writes `cooked_on = <picked date>` on the receipt. Pool math unchanged. | Optional — resolves the "we ate Tuesday's dinner on Thursday" case without inventing a separate meal-plan entry. |
| **Skip for now** | Session-only defer; entry stays in the queue on next visit. | No state change. |

**No "mute" / "push" secondaries.** Unlike stocktake, an unresolved entry
here is an outstanding money+food fact — muting it would hide reality. If
the user genuinely doesn't want to bother, that's what auto-drain-on is for.

### 3.3 Completion screen

Five-counter recap (matched to stocktake's shape): *cooked / with-adjustment
/ not-cooked / later-than-planned / still-open*. **No batch add-to-list**
(that's stocktake's job; reconciling doesn't create shortfall — the plan
already exists).

---

## 4. Surfacing — where the user finds this

The reconcile page is worthless if nothing points at it. Three
low-noise surfaces, in decreasing prominence:

- **Alerts feed (Alerts hub + notification tray):** a new alert kind
  `meal_reconcile_overdue`. Fires when *N* unresolved entries stretch back
  *M* days — see §11 open decision **D1** for the threshold. Follows the
  existing `AlertPreference` shape (per-user enable + severity), integrates
  with the email digest and push channels for free.
- **Dashboard chip** in the *Your Kitchen* zone: a small "Reconcile 4 past
  meals →" chip that renders when the queue is non-empty. Hidden entirely
  when empty (R-029 hide-don't-nag) — a zero-state chip is exactly the
  kind of nag the champion plan rules out. Deep-links to
  `/meal-plans/reconcile`.
- **Meal Plans page**, in the header — an inline breadcrumb-style
  *"3 past-day meals need confirming →"* line above the calendar when the
  queue is non-empty. Same hide-when-empty rule. Purely a nudge; the
  primary entry is the dashboard chip + alert.

**No cookbook / recipe-detail surfacing.** Recipes don't reconcile — plans
do.

---

## 5. From reconciling to the rest of the app

The reconcile page is small; its integrations are the interesting part.

### 5.1 Recipe pool (`Recipe.available_meals`)

Ownership stays server-side (R-003). Every verb in §3.2 routes through the
same handler that today's `cook_recipe.py` uses for `available_meals`
arithmetic, so **there is exactly one place** in the codebase that mutates
that column. The current inline `UPDATE "Recipe" SET available_meals = …`
in [reconcile_consumed_meals.py:56-65](../../dora_api/features/meal_plans/reconcile_consumed_meals.py)
gets folded into that shared helper too — no more two-authorities-for-
pool-count drift.

### 5.2 `ConsumptionEvent` (P8-07 belief system)

`Recipe.cook_recipe` writes a `ConsumptionEvent` per ingredient linked stock
item so the Zero-Input Pantry belief service (§P8-07) can drop `Stocked` →
`Low`. **Auto-drain does not write ConsumptionEvents today** (the sweep
touches only `MealPlanEntry` + `Recipe`), which means the belief service
already treats auto-drained meals as "we don't know if you actually ate
this". That is the right shape and this proposal preserves it:

- **Cooked (as planned)** and **Cooked (different portions)** and **Cooked
  later than planned** verbs *do* fan out to `ConsumptionEvent` writes
  through the shared handler, so the reconcile-page confirmations are
  now the single moment where belief updates for a past meal.
- **Didn't cook** and unresolved entries never produce
  `ConsumptionEvent`s.

Net effect: turning auto-drain **off** actually gives the belief service
better data (every historical consume is user-confirmed); turning it **on**
matches today's fidelity but adds the correction path when the user
disagrees.

### 5.3 Cost roll-ups + spend-by-category

Same pattern as 5.2 — spend attribution should follow *actual* consumption,
not planned. Today the reports layer reads `MealPlanEntry.consumed_at IS NOT
NULL` as its cooked filter, so *nothing changes for auto-drain-on users*
(they still see today's numbers plus a "you can dispute this" affordance).
Auto-drain-off users see a slightly emptier "meals cooked" chart until they
walk the queue — that's the honest state, and the reconcile page is the
one place to change it.

### 5.4 The lazy `before_request` hook (F6)

F6 is a plumbing detail of F5 — the audit already recommended keeping the
sweep, just making its *result* visible. Under this proposal:

- **Auto-drain-on users:** the hook runs unchanged, then also writes an
  *unresolved-auto* receipt row per drained entry (§7). Hot-path cost is
  one extra insert per entry per day — negligible; the sweep already fires
  a `RETURNING` update anyway.
- **Auto-drain-off users:** the hook *does not* mutate `MealPlanEntry`
  or `Recipe`. It becomes an inexpensive no-op read; the reconcile page
  is the mutation surface.

**Deciding at each request** (rather than at midnight, or by cron) keeps the
sweep's existing "user opens the app and their pool is current" ergonomics
without a scheduled-job dependency.

---

## 6. Interactions with existing alerts + suggestions

### 6.1 `no_planned_meals` alert

Currently fires when the *upcoming* days have no plan entries. Unchanged —
this alert is forward-looking, reconcile is backward-looking. They coexist
without special-casing.

### 6.2 `meal_reconcile_overdue` — the new alert

- **Fires** when the reconcile queue has entries older than *M* days
  (§11 D1). Severity `info`, follows `AlertPreference`, off-switch is the
  same per-kind row every other alert uses.
- **Snoozes** dismiss the alert for a fixed window (matches other alert
  kinds), but do *not* mark entries reconciled — the queue truth is untouched.
- **Auto-clears** when the queue empties.
- **Cross-user isolation:** the queue is per household (matches every
  other planned-meal surface), but the alert is per user — different users
  in the same household see it independently.

### 6.3 Assistant / suggestions

One new suggestion kind `reconcile_meals_pending` — analogous to
`stocktake_due` — surfacing when the queue is non-empty and older than a
threshold. Accepting the suggestion navigates to `/meal-plans/reconcile`.
No new mutation path; dedup via `(kind, "queue")`.

### 6.4 Setting-change transitions

- **Switching auto-drain ON → OFF.** Historical past-day entries that were
  already auto-drained by today's sweep stay drained; the receipt table
  (§7) surfaces them as *auto (unresolved)* until the user disputes or
  confirms them. New entries follow the manual-confirm posture.
- **Switching auto-drain OFF → ON.** Any past-day entries that were
  sitting `consumed_at IS NULL` while auto-drain was off are **not
  retroactively drained**. The user opted into the manual posture for those
  entries; forcing them consumed on setting flip would be exactly the
  silent-mutation the whole brief is trying to eliminate. The next daily
  rollover behaves as auto-drain-on going forward.

**Charter check.** Both transitions preserve the "no silent state change"
rule (P3 Honest); neither depends on the user's understanding of the
setting's history (P1 Effortless).

---

## 7. Data model & endpoints

### 7.1 Schema

- **`AppSetting.auto_drain_past_meals: bool`** — new column, non-null,
  default `TRUE`. Migration is additive; the singleton row gets the
  default. No backfill. **Install-wide, not per-user** — see §2 discovery
  note + §11 D5.
- **`MealPlanReconcileReceipt`** — new table.
  - `id: uuid`
  - `meal_plan_entry_id: uuid` (FK, cascade-delete on entry delete)
  - `state: enum` — `unresolved_auto` | `unresolved_manual` |
    `resolved_confirmed` | `resolved_adjusted` | `resolved_not_cooked` |
    `resolved_deferred`
  - `original_servings: int` — the entry's planned servings at receipt
    creation (immutable audit trail)
  - `actual_servings: int nullable` — set on `resolved_adjusted`
  - `cooked_on: date nullable` — set on later-than-planned
  - `resolved_by_user_id: uuid nullable`
  - `resolved_at: datetime nullable`
  - `note: text nullable`
  - `created_at: datetime`
  - Index on `(state, created_at)` for the queue query.

  One receipt per entry per *reconcile event*. Auto-drain writes one at the
  moment of drain; manual-confirm writes one at the moment of user action.
  **Never mutate a resolved receipt** — a change of mind writes a new
  receipt against the same entry with the reverse effect, preserving the
  history (matches the `MealPlanSwapLedger` shape from FU-451).

Alembic revision follows R-006: forward migration only, no data mangling.

### 7.2 Endpoints

- `GET /api/meal-plans/reconcile-queue` — paged, oldest-first, grouped by
  day; includes the receipt's current state so the SPA can render the
  strikethroughs on already-resolved rows if the user scrolls back.
- `POST /api/meal-plans/reconcile/<entry_id>` — body carries the verb + any
  fields (`actual_servings`, `cooked_on`, `note`). Idempotent on the
  verb (a repeat call for the same verb is a no-op; a different verb
  writes a corrective receipt).
- `PATCH /api/auth/me` — extend the existing self-patch endpoint with
  `auto_drain_past_meals`. No new route.

### 7.3 R-005 distribution posture

Every mutation routes through `SqlAlchemyRepository` (no raw text() outside
the receipt-table single-insert path); the setting lives on `AppSetting`
(install-wide, matching the household-shared meal plan); no `tenant_id`
speculative column. Portable to Postgres + SQLite at the DB layer as-is.

---

## 8. Settings block

A new **"Meal reconciliation"** row in **Settings → Admin → System**
(alongside the other install-wide meal-plan controls), **not** Preferences:

- **"Assume past-day meals were cooked"** toggle, default on. Admin-only
  edit — matches every other `AppSetting`-backed knob.
- One-line explainer: *"When on, Dora assumes the household ate meals as
  planned; anyone can dispute an entry on the Reconcile past meals page.
  When off, past meals stay pending until someone confirms them."*
- Link chip → `/meal-plans/reconcile` (visible to every user; the page
  itself is not admin-gated).

---

## 9. Charter check

| Principle | How this satisfies it |
|---|---|
| **P1 Effortless** | Default posture is unchanged from today's UX for people who like it. The reconcile page only exists when there's something to reconcile; the dashboard chip and alert are hide-when-empty. |
| **P3 Honest** | Every past-day state change is either explicitly the user's or lives behind a visible receipt they can walk and reverse. The number Dora shows can always be reconciled back to a user action. |
| **P4 Preservation of trust** | The receipt table is append-only — a corrected decision writes a new receipt, never overwrites the old one. |
| **Anti-creep (tiebreak)** | One setting, one page, one alert, one suggestion. No per-recipe knob, no third posture, no scheduled cron. Nothing bolted on that a user with the default posture ever has to think about. |
| **R-003 state-ownership** | `available_meals` mutation collapses to one server-side helper across `cook_recipe`, the sweep, and the reconcile verbs. |
| **R-005 distribution posture** | Repository-routed, portable SQL, install-wide `AppSetting` (matches shared-plan reality; no `tenant_id` speculative column). Same artefact runs self-hosted + managed + SaaS. |

---

## 10. From the original spec

`docs/00_original_spec/` is historical / non-authoritative (pre-~100k-LOC).
Nothing in the original Feature Boards or "I can …" notes anticipated a
manual-reconcile surface; the original meal-plan design predated the
`available_meals` pool entirely. Nothing worth extracting for this brief.

---

## 11. Open decisions (for the user before impl-plan)

Everything above is decidable from principle. The four items below need a
short round-of-questions before the impl plan is written:

- **D1 — `meal_reconcile_overdue` threshold.** Recommend fires when
  **≥ 3 unresolved entries** stretch back **≥ 4 days** (roughly half a
  week's worth of dinners, matching the stocktake-mode band vocabulary).
  Tune?
- **D2 — Should auto-drain-off gate the pool from being *manually
  incremented* via `cook_recipe`?** i.e. if the user cooks a recipe
  through the cook-mode "finished cooking" surface, do we still bump
  `available_meals + N`, or does that also require reconciling the
  matching planned entry? Recommendation: **keep them independent** —
  `cook_recipe` is a positive action the user just took, it should
  freely increment the pool; reconcile is only for planned-but-unconfirmed
  entries. Alternative: pair them for people who want a strict "pool
  reflects only reconciled cooks" model. Erring toward Effortless.
- **D3 — Retention of resolved receipts.** They're append-only; the table
  grows monotonically. Options: (a) keep forever (transparent, ~1 row per
  planned meal ever); (b) prune resolved receipts older than the audit
  window (`DORA_AUDIT_RETENTION_DAYS`, currently ~365d — but that env var
  was retired by FU-333, so this would need a new `AppSetting` knob).
  Recommendation: **(a) keep forever** until the row count becomes a
  real cost — a "meals I cooked, historical" report is a plausible
  future ask.
- **D4 — Setting name copy.** Toggle labels above are working copy. The
  UX-copy skill can pick a final phrasing during impl-plan.
- **D5 — Setting scope: install-wide vs per-user (discovered 2026-07-09
  during Chunk 1 pre-flight).** FU-317's original body said "per-user".
  `MealPlan` has no `user_id` or `household_id` — it's an implicitly
  household-shared table. Per-user reconcile posture over a household-
  shared plan is incoherent: the sweep runs on the first request per
  request-cycle, so whichever user opens the app first silently decides
  for everyone. **Recommendation: install-wide `AppSetting.auto_drain_past_meals`**
  (this proposal now reflects that). Alternative shapes considered and
  rejected: (a) per-user + first-user-wins (silent), (b) per-user + skip
  if ANY user is off (adds a user-scan on every request; still weird
  when postures diverge). Chunk 1 code is held until this D5 is
  explicitly confirmed.

---

## 12. Feedback coverage table (MANDATORY)

Per CLAUDE.md — every feedback bullet that motivates or is touched by this
brief. Bullets are quoted from `docs/02_feedback/Feedback _ Fixes - as of
[06-Jun-2026].md`; MR-N = bullet order within this surface.

| # | Feedback bullet (paraphrased) | Resolution |
|---|---|---|
| MR-1 | *"Are meals already being allocated to meal plans? … distinguish between 'going to cook' and 'already cooked' so the correct information is given."* (Recipes section, L89) | ✅ Directly addressed. The `consumed_at IS NULL` vs `NOT NULL` split IS the distinction; today the sweep merges them silently. The reconcile receipt makes it visible and correctable. |
| MR-2 | *"How many meals on hand … Is there much value in seeing the number of cooked meals on this page? Is it clutter?"* (Recipes section, L274) | Out of scope — a Recipes-Overview presentation call, not a reconcile-model call. Left for [[FU-432]] follow-on. |
| MR-3 | *"Number in stock which is editable, and the number of allocated meals (which only shows if there is allocations at all) in its own box."* (Recipes section, L275) | Out of scope — same Recipes-Overview presentation call as MR-2. |
| MR-4 | *"Allocation seems to be broken. Allocating a meal does not affect x unallocated of x on hand."* (Meal Plans, L345) | Adjacent, not the same bug. The reconcile page ensures `available_meals` reflects reality; the allocation-visibility fix is a separate presentation surface. Cross-linked as a note; not this brief's job. |
| MR-5 | *"Meal plans should be able to be made recurring … perhaps once a week passes, it locks to read-only entirely?"* (L369) | Partial — this brief makes past-day entries *reconcile-only-writable*, not editable. That's the right shape for "read-only entirely" once every entry is resolved. Full recurring-plan design is separately tracked (Meal Plans redesign). |
| MR-6 | *"How can recurring and editing coexist? Perhaps once an edit is made to a future week it is treated as its own plan …"* (L370) | Out of scope — recurring-plan design lives in [[PROPOSAL_MEAL_PLANS.md]]. Reconcile is orthogonal to recurrence. |
| MR-7 | *"UX works for both groups of people: those who batch cook … and those who cook only fresh … 'how many meals did you save?'"* (L371) | ✅ Addressed via the **Cooked (different portions)** verb (§3.2) — batch cooks can log `actual_servings`, fresh cooks tap the primary verb. |
| MR-8 | *"'start cook mode' should prompt a confirmation if it's not 'ready to cook now'."* (Recipes/Cook Mode, L309) | Out of scope — cook-mode gate, not a reconcile call. Cross-linked. |

`COVERAGE_GAPS.md` has no per-MR rows to flip.

---

## 13. Anti-drift checklist (before running the impl-plan prompt)

Per CLAUDE.md's anti-drift rule for `03_prompts/` — an impl-plan for this
proposal must assemble its required reading from:

- **This proposal** (governing scope).
- **Charter anchors** — Part II Charter (P1, P3, P4, anti-creep);
  `RECONCILED_FINISHING_PLAN.md` §5 Phase 1;
  `ENGINEERING_STANDARDS.md` R-003 / R-005 / R-006 / R-029.
- **Feedback bullets** — L89, L369, L371 (the three "MR" rows this brief
  directly resolves).
- **Cross-cutting audits** — `MAGIC_BEHAVIOUR_AUDIT.md` § F5/F6 (the
  origin); `PROPOSAL_STOCKTAKE_MODE.md` (the shape borrowed).
- **Open follow-ups on adjacent surfaces** — [[FU-432]] Recipes-Overview
  presentation; [[FU-317]] (this) closes on impl-plan sign-off.

Skipping any of the above is how prompts ship in isolation and silently
violate the charter (CLAUDE.md anti-drift rule).
