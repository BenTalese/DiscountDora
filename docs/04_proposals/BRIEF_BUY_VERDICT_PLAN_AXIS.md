# Design brief — a `plan` axis for the buy-verdict oracle

**Status:** design only, **not approved to build**. Two things gate it, both
in §7.
**Governs:** an addition to [PROPOSAL_BUY_VERDICT_ORACLE.md](PROPOSAL_BUY_VERDICT_ORACLE.md)
(P8-05/06). That proposal stays the master for the oracle's shape; this brief
adds one axis and does not restate the rest.
**Raised:** 2026-08-28, from owner feedback — *"Should buy verdict also be fed
by future planned meals? Or is that a weak metric? E.g. high confidence you
should buy tomato sauce because you planned to make spaghetti Bolognese but
you're out of tomato sauce. Just an idea, might not be good."*

---

## 1. The answer to the question as asked

It is not a weak metric. It is probably the **strongest need evidence the
oracle can hold**, and it is the only one that isn't a guess.

Every existing `need` input is an inference about the past projected forward:
the recorded `StockLevel` is a fact about a moment that has since passed, and
cadence ("bought every ~11 days, last shop 12 days ago") is a statistical
argument. A planned meal is categorically different — it is a **stated
intention about the future**, entered by the user, with a date and a serving
count attached. When the owner's example fires, Dora isn't estimating that you
might want tomato sauce; you have told it you intend to cook Bolognese on
Thursday for four.

So the idea is good. The design risk is not "is the signal weak" — it is
**what the signal does when the plan doesn't happen**, which §5 is about.

## 2. What the oracle can see today

Nothing. `_need_axis` ([get_buy_verdict.py:375](../../dora_api/features/stock_items/get_buy_verdict.py))
reads exactly two things via `_need_band`:

1. the recorded `StockLevel` band, and
2. the Zero-Input `PantryBelief`, which wins when its confidence is above
   `low`.

`MealPlanEntry` is not in `_AxisInputs`, is not in `_gather_inputs`, and no
meal-plan module is imported. The owner's example is invisible to the verdict
today — a household can have Bolognese planned for Thursday, be out of tomato
sauce, and get `unsure / thin_data` on the item.

The data needed already exists and is already aggregated:

| What | Where |
|---|---|
| Planned meals with dates + servings | `MealPlanEntry` (`scheduled_for`, `servings`, `slot`, `consumed_at`) |
| Which stock items a week's meals require, aggregated, with `is_optional` resolved | `features/meal_plans/get_meal_plan_ingredients.py` — `MealPlanIngredientDto` |
| Whether plans actually get cooked | `MealPlanReconcileReceipt` states (`resolved_confirmed` / `resolved_adjusted` / `resolved_not_cooked`), written by `features/meal_plans/reconcile.py` |

That third row is the important one and is discussed in §5. It means the
adherence guard is **buildable from data Dora already writes**, not a new
tracking mechanism.

## 3. Why a fourth axis, not an extension of `need`

The obvious cheap implementation is to let a planned-meal shortfall push
`_need_band` to `out`. It should not be built that way.

**The evidence qualities are different, and the oracle now models that
explicitly.** Since the 2026-08-24 regrade, `strength` ("how much should you
care") and `confidence` ("how good is the evidence") are separate dials,
specifically so that *"very likely worth buying, but I've only seen two
shops"* is sayable. Cadence and a plan sit at opposite ends of that split:

- cadence is **low-confidence, timeless** — a statistical claim with no date on it;
- a plan is **high-confidence, dated** — a commitment that expires on Thursday.

Folding them into one band throws the distinction away in both directions. A
plan would inherit cadence's hedging (`_need_is_soft_inference` would call a
user-entered plan a "soft inference"), and cadence would inherit the plan's
certainty.

**The prose would also collapse.** `_need_axis` returns one `VerdictReasonDto`
per axis, and belief's `reason` already wins the slot when belief drove the
band. A plan-driven need has a completely different sentence to say —
*"Bolognese on Thursday needs 400g"* is not a variant of *"bought every ~11
days"* — and there is only one slot. A fourth axis gets its own.

**Precedent:** this is the same call `inference_overlay.py` made about pantry
belief, and the reasoning in its docstring applies verbatim: it lives beside
the belief engine "rather than inside `recipe_cookability` — putting it there
would invite exactly the merge we're avoiding."

## 4. Proposed shape

### 4.1 The axis

| Axis | Input | Signals |
|---|---|---|
| **Plan** | `MealPlanEntry` rows in the horizon whose recipe requires this stock item, via the `get_meal_plan_ingredients` aggregate | `planned_shortfall` / `planned_covered` / `no_plans` / `thin_data` |

- **`planned_shortfall`** — a planned meal in the horizon needs this item and
  the recorded/believed level won't cover it. The signal that does work.
- **`planned_covered`** — planned meals need it and you have it. Deliberately
  emitted rather than staying silent: it is the honest counter-argument to a
  cadence-driven "you're probably due", and suppressing it would make the axis
  a one-way ratchet toward `buy`.
- **`no_plans`** — nothing planned needs it. Contributes no reason and, per
  §4.3, does **not** drop confidence. Distinct from `thin_data`.
- **`thin_data`** — meal planning is unused on this install, or the recipe's
  ingredients aren't linked to stock items so the question can't be answered.
  This is the `no_plans` / `don't know` distinction the waste axis already
  draws between `no_waste_history` and `thin_data`; getting it wrong makes an
  install that never opens Meal Plans permanently one confidence step worse
  off.

### 4.2 Horizon

Cap at the **planning horizon the user actually maintains** — the end of the
furthest meal plan that has entries, and never more than 14 days. Two reasons:
a plan three weeks out is aspiration rather than intention, and an uncapped
horizon means one ambitious month of planning permanently biases every verdict
toward `buy`.

Meals already reconciled (`consumed_at` set, or a `resolved_*` receipt) are
excluded — they are history, and history is the other axes' job.

### 4.3 Composition

The plan axis is **strength-affecting and direction-affecting, but only ever
one way**:

1. `planned_shortfall` on a **required** ingredient → contributes to `buy` and
   raises `strength`, because a dated commitment outranks an undated guess.
   Where cadence would say `unsure`, a shortfall says `buy`.
2. `planned_shortfall` on an **optional** ingredient → a reason, no strength
   change. `MealPlanIngredientDto.is_optional` is already resolved correctly
   across the week ("optional only when *every* contributing row was"), so
   this comes free.
3. `planned_covered` → never raises strength, and blocks a `wait` from being
   upgraded to `skip`. You are about to cook with it; telling someone to skip
   an item their Thursday dinner needs is the failure mode that would make the
   whole axis untrustworthy.
4. **The plan axis never produces `wait`.** `wait` is a claim about price
   movement, and a plan says nothing about price. It also must not override a
   `skip` that came from `wastes_often` — see §5.
5. `no_plans` contributes nothing and **does not** drop confidence, unlike
   `thin_data`. Most installs will sit here most of the time.

### 4.4 Prose

The reason string names the meal and the day, because that is the entire value
of the axis over cadence — it is checkable. *"Bolognese on Thursday needs
tomato sauce"*, not *"a planned meal needs this"*. Where several meals in the
horizon need the item, name the soonest and count the rest: *"Bolognese
Thursday + 2 more meals this week"*.

Copy is checked against D-014 (Dora's voice) and must not imply Dora will act
on it — the axis explains a verdict, it does not add anything to a list.

## 5. The failure mode this must be designed against

**A plan you never cook.** If Dora pushes tomato sauce to `buy` for a
Bolognese that gets skipped three weeks running, the axis is not merely
useless — it is actively worse than silence, because it spends the user's
money and its own credibility at the same time. An oracle that is wrong
*confidently* is the one users stop reading.

This is not hypothetical. Meal plans are aspirational for most households;
that is why `reconcile_consumed_meals` and the whole reconcile queue exist at
all.

**The guard: adherence gates the strength boost, not the reason.**

`MealPlanReconcileReceipt` already records, per past entry, whether it was
`resolved_confirmed` / `resolved_adjusted` (cooked) or `resolved_not_cooked`.
That is an adherence rate, computable over a trailing window, from data
already written.

- Adherence **high** → the axis works as described in §4.3.
- Adherence **low** → the axis still emits its reason (the plan is a true fact
  about the user's stated intention, and hiding it would be dishonest under
  P3), but it **does not raise strength** and cannot flip `unsure` to `buy`.
- Adherence **unknown** (too few resolved entries to have a denominator) →
  treat as thin, exactly as `_waste_axis` treats `purchases_12mo <
  _MIN_PURCHASES_FOR_WASTE_RATE`. Do not assume good adherence from silence.

The specific thresholds and window are deferred to implementation, alongside
the existing thin-data thresholds in the composer (proposal §2.3) — they
belong in one place with the others, not invented here.

**Second failure mode: double-counting.** If the user has already put the
Bolognese ingredients on a shopping list (which the meal planner's one-shot
add makes easy), the item is handled and a `buy` is noise. Whether the axis
should read shopping-list membership is an open question — §7, decision 3.

## 6. What blocks it — the standing directive

`inference_overlay.py:23` records an explicit owner directive from
**2026-08-17**:

> the cookbook is never filtered on a belief, shopping lines are never
> auto-added from one, and **a planned meal's shortfall is unchanged**.
> Everything here is additive commentary the user can switch off.

The proposed axis **changes an answer** — that is its entire point. §4.3
item 1 moves a verdict from `unsure` to `buy` on the strength of a planned
meal. That is squarely inside what the directive forbids.

Two things are worth separating before the owner rules on it:

- The directive was made about the **inference overlay**, whose remarks come
  from a *belief* — an inference Dora generated. A planned meal is not an
  inference; it is user-entered data. The directive's stated rationale
  ("honesty gates … a low-confidence guess contradicting a recorded fact is
  noise") does not obviously reach it.
- But the buy verdict is exactly the kind of surface the directive was
  protecting, and the overlay's own `SURFACE_MEAL_PLAN` flag exists because
  annotating meal plans was considered intrusive enough to need an opt-in.

**This brief does not assume the reversal.** It is decision 1 in §7.

## 7. Open decisions

1. **Reverse the 2026-08-17 "a planned meal's shortfall is unchanged"
   directive for the buy-verdict surface?** — **owner call, blocks the whole
   axis.** If no, this brief is closed as *considered and declined* and the
   most that can ship is a non-strength-affecting reason line (§4.3 with item
   1 removed), which is worth much less. → spawned as **FU-774**.
2. **Opt-in flag, and which one?** The overlay's per-surface flags live on
   `User` (`inference_meal_plan_enabled` et al.), but the buy verdict is
   gated install-wide by `AppSetting.buy_verdict_enabled` plus the money
   prerequisite (R-058). A per-user flag on an install-wide surface is a
   mismatch. Recommendation: a new install-wide
   `AppSetting.buy_verdict_plan_axis_enabled`, defaulting **off**, matching
   how the overlay's three newer surface flags default. → spawned as
   **FU-775**.
3. **Should the axis discount items already on an open shopping list?**
   (§5, double-counting.) This is a real cross-entity read, and doing it in
   the client would violate the state-ownership principle outright, so if it
   happens it happens server-side in `_gather_inputs`. → spawned as
   **FU-776**.

*Open decisions — all three spawned as FUs; none left undecided in this doc.*

## 8. Standards check

- **R-003 / state-ownership** — the axis is a cross-entity aggregate (meal
  plans × recipes × stock levels) and therefore server-owned by definition.
  No client may compute it. It reuses `get_meal_plan_ingredients`'s existing
  aggregation rather than introducing a second way to answer "what do this
  week's meals need"; a second copy of the `is_optional` rule in particular
  would be a straight R-003 violation.
- **R-058 / money prerequisite** — the plan axis is not price-driven, but it
  lives inside a surface that returns 403 with money off. It does not change
  that; it must not become an argument for a money-free "half verdict", which
  the 2026-08-27 audit explicitly closed off.
- **Charter P3 (Honest) / P12 (No-invent)** — the `no_plans` vs `thin_data`
  split (§4.1) and the adherence-unknown branch (§5) are both direct
  applications. The axis must never assert a plan-driven need it cannot name a
  meal and a date for.
- **R-005 / distribution posture** — pure-personal, DB-only, no external call,
  no config. Works identically self-hosted and managed. One portable migration
  if decision 2 lands.
- **ADR evaluation** — nothing here is a recurring decision yet. If a *second*
  consumer of plan-derived need appears (the shopping-list verdict endpoint is
  the obvious candidate), the "plans are dated intentions, not inferences"
  distinction is worth promoting to a rule at that point, not now.

## 9. Cross-check against the original feedback

Per CLAUDE.md, per-surface work maps the feedback bullets for its surface.
This brief targets the buy-verdict oracle, which — as
`PROPOSAL_BUY_VERDICT_ORACLE.md §7` already records — **has no bullets in
`Feedback _ Fixes - as of [06-Jun-2026].md`**: it is a champion feature that
postdates the feedback pass. The Charter mapping stands in as the coverage
table, and this brief's motivating input is the owner's 2026-08-28 message
quoted at the top rather than a numbered bullet.

Adjacent bullets this touches, mapped for honesty:

| Bullet | Where handled |
|---|---|
| `§SHOPPING LIST DETAILS VIEW` — the general *"why is this on my list?"* thread | §4.4 — a plan-driven reason names the meal and the day, which is the most direct answer to that question the oracle can give |
| `§MEAL PLANS` — planning is only useful if it changes what you buy | §4.3 — this is the first place a plan affects a purchase decision at all |

Out of scope, with reason:

- **Auto-adding plan shortfalls to a list.** Forbidden by the same 2026-08-17
  directive (§6) and, separately, by the oracle's own rule that it emits
  intent and never grows a new mutation seam (proposal §2.4).
- **Nutrition as an axis.** Unchanged from proposal §7 — conflates "should I
  buy this?" with "is this good for me?".
- **`wait_until` interaction (P8-06/FU-438).** A plan gives a *deadline*
  ("needed by Thursday"), which is genuinely interesting against a price-cycle
  prediction ("your usual low lands next fortnight") — the two together could
  say "buy now, the low won't arrive in time". Deliberately out of scope:
  FU-438 isn't built, and designing against it would be speculative.

## 10. From the original spec

`docs/00_original_spec/` predates the champion plan, and per proposal §8 has
no precursor to the buy oracle. Checked the Meal Plans board for a dropped
"plan drives the shop" intent: the original framing was a one-shot *"generate
a shopping list from the week"*, which is a **bulk-add** feature and shipped
in the 08-27 meal-plans batch. It is a different mechanism from a per-item
verdict signal — **superseded**, nothing to extract.
