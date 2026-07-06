# Proposal — Budget-Aware Auto-Generated Shopping Lists (P2-05 tail)

**Status:** Draft · **Date:** 2026-07-06
**Scope:** the optimizer half of the champion-plan **P2-05 "Budget-Aware
Auto Lists"** — the piece that was deferred when the user-facing budget
shipped (`FU-448`).
**Anchors read before writing:** `RECONCILED_FINISHING_PLAN.md §5, §7 Decision
7`, `DASHY_DORA_CHAMPION_PLAN.md` Part II charter, `PROPOSAL_BUY_VERDICT_ORACLE.md`
(the shipped P8-05 oracle we lean on), `Feedback _ Fixes - as of [06-Jun-2026].md`
line 254 (budget-features-must-be-optional bullet), `FEEDBACK_TRIAGE_AND_PLAN.md`
row C10.

> **Charter tie-break for every decision below:** Effortless (P1) +
> Anti-creep (P10) + Personal-data-only (P4 / P9). The budget-aware pass
> must reduce "did I overspend?" to one glance + one tap, must not add a
> new page, and must lean on signals Dora already computes for the user.

---

## 1. The problem

Dora already tracks the user's budget (`User.budget_amount` +
`budget_period`) and surfaces spend-vs-budget on the dashboard
([`DashboardPage.vue:380`](../../web_app/src/pages/DashboardPage.vue)),
plus a periodic alert when the period is running hot. But the
auto-generate shopping-list flow
([`auto_generate.py`](../../dora_api/features/shopping_lists/auto_generate.py))
does not consult the budget at all — it collects candidates from six
sources (recipe / meal-plan / flagged / essential / low-stock /
frequently-added), sums, and emits. If the resulting list would blow
the budget for the current period, nothing flags it and the user only
finds out when the receipt-reconcile lands them over their spend line.

The champion plan's P2-05 called for a proper budget-aware pass. The
user-facing budget shipped; the optimizer half never did. This
proposal fills that gap.

---

## 2. What already exists (skip if you know)

- **Budget** — `User.budget_amount` (money) + `budget_period` (weekly /
  fortnightly / monthly). Live in [`budget.py`](../../dora_api/features/budget/budget.py);
  spend-so-far in the current period computed there too.
- **Money opt-in gate (C10)** — the whole family of money surfaces is
  gated on `AppSetting.money_features_enabled` (install-wide). If money
  features are off, none of this proposal renders. That gate is
  authoritative; we do **not** add a second toggle.
- **Auto-generate** — [`AutoGenerateHandler`](../../dora_api/features/shopping_lists/auto_generate.py)
  with the six sources above and a strict provenance priority. Each
  candidate carries `added_via` (the provenance chip) and a target
  quantity. Prices resolve at read-time via the offer-picker in
  [`get_shopping_list_detail.py`](../../dora_api/features/shopping_lists/get_shopping_list_detail.py),
  which is where `_line_price` + `compute_list_totals` live.
- **Buy-verdict oracle (P8-05)** — shipped
  ([`get_buy_verdict.py:372`](../../dora_api/features/stock_items/get_buy_verdict.py:372)).
  Emits `buy` / `wait` / `skip` per stock item using the user's own
  price + cadence + waste + level signals. **Reusable directly** — the
  optimizer does not re-derive a "should I cut this?" score.
- **Money display everywhere** goes through `useMoney` (post-FU-043) so
  the banner + preview inherit currency/locale correctly.

---

## 3. Design decisions (locked with user 2026-07-06)

### 3.1 UX shape — soft warn + one-tap auto-trim (option 1 + 2)

Auto-generate always produces the **full** list — no silent trimming.
If the projected total exceeds the user's period-remaining budget, a
banner appears at the top of the list detail:

> ⚠️ **Projected $147 · budget remaining $92 — trim $55 to fit.**
> [ Show what would be cut ] [ Trim to fit ] [ Dismiss ]

Three affordances, all discoverable, none forced:

- **Show what would be cut** — expands a preview list underneath the
  banner. Each candidate line for cutting shows the reason chip (see
  §5) and the amount saved. Nothing is removed yet.
- **Trim to fit** — one tap: the candidates cut cleanly, dropped lines
  move to a collapsible **"Deferred to fit budget"** section on the same
  list (not deleted — still visible + one-tap re-add).
- **Dismiss** — hides the banner for this list. User is deciding to
  over-spend consciously; that's fine.

The banner **never fires silently**. It never mutates the list. Only
"Trim to fit" mutates it, and the mutation is reversible via the
Deferred section. This matches the user's stated shape ("banner + UI
affordance to take auto-trim suggestion").

### 3.2 Budget window — period remaining

"Budget" for the optimizer = `budget_amount − spend_in_current_period`,
using the same period-clock as the dashboard card. Rationale:

- Ties to the surface the user already reads. A shop mid-month has less
  headroom than a shop on day 1 of the period, and the banner reflects
  that automatically.
- No new setting or per-shop cap. The user's mental model is the
  budget line they already have.
- Single-shop caps (party shop, gift shop) are out of scope for v1.
  Log as a follow-up if it comes up.

If `budget_amount` is unset or 0, the banner never fires — no budget,
no constraint. Self-gating; no flag.

### 3.3 What "period remaining" means when the list will be shopped later

The list is built now; the shop happens whenever. We compute headroom
against the period **the list is expected to be shopped in**. Default:
today's period. When `shopping_list.expected_shop_at` is set to a date
that falls in a later period, we compute against **that** period's
full budget (no spend deducted, since the period hasn't started). This
edge case is rare but the logic is one branch and worth getting right
so a "next month's shop" doesn't trigger a false alarm against this
month's remaining.

### 3.4 Explainability is per-line, not per-run

Every candidate cut carries a **one-phrase reason chip**. No modal, no
tooltip essay. The full vocabulary is fixed (§5) so the chips render
in a stable width and read consistently.

---

## 4. The trim rule stack

Cuts happen in **tiers**. The optimizer walks tiers from safest-to-cut
(Tier 1) down, and inside a tier walks from **highest-price line first**
(biggest bang per cut) until projected total ≤ budget. It never cuts
across a tier when a later tier still has room — it exhausts a tier,
then descends.

### Tier 1 — Habit items with no immediate demand *(cut first)*

`provenance = auto_frequently_added` **AND** no meal-plan / recipe row
requires this item in the next 7 days **AND** stock level is not `out`.

Rationale: these are pantry-refill habits, not needs. If money is
tight, they can wait a week.

Chip: **"Habit — can wait"**

### Tier 2 — Low-stock items with cover

`provenance ∈ {auto_low_stock}` **AND** cadence estimates ≥ 5 days of
cover remaining **AND** no meal-plan / recipe row requires the item in
the next 7 days.

Chip: **"5 days' cover left"** (days from cadence; falls back to
**"Not urgent"** when cadence has no signal)

### Tier 3 — Buy-verdict "wait" lines

Any line whose `get_buy_verdict` verdict is `wait` **AND** not required
by a meal-plan / recipe row in the next 3 days **AND** stock level is
not `out`.

Rationale: the oracle has already decided the price is high right now.
The optimizer just borrows that call.

Chip: **"Above your usual price"**

### Tier 4 — Out-of-stock, no scheduled meal

`stock level = out` **AND** no meal-plan / recipe row requires the item
in the next 7 days.

Rationale: out-of-stock without a booked meal is annoying but survivable.

Chip: **"Out, but no meal booked"**

### Tier 5 — Recipe / meal-plan items scheduled ≥ 5 days out

`provenance ∈ {auto_recipe, auto_meal_plan}` **AND** the earliest
scheduled_for referencing this item is ≥ 5 days from today.

Rationale: last resort. The far end of the plan can shift; the near
end can't. Within this tier, prefer cutting items only referenced by
one entry (single point of failure vs. multi-meal staples).

Chip: **"For [Recipe] on [DayName]"**

### Never cut

- `is_flagged` essentials.
- Any item required by a meal-plan / recipe row in the next **2 days**.
- Items with buy-verdict `buy` (the oracle is actively saying "grab
  it") **and** stock level `low` or `out`.
- Items whose current line total is < $2. Not worth the cognitive load
  of a chip.

### Stopping condition

Walk tiers until `projected_total ≤ budget_headroom` **or** we run out
of cuttable lines. If we run out and still overshoot, the banner
updates to:

> **Trimmed everything safe. Still $X over — this shop needs a hand
> from you.** [ Show what's left ]

No further magic. The user drops something themselves.

---

## 5. Explainability chip vocabulary (fixed set)

The deferred section renders one chip per line; the vocabulary is
closed so we don't drift into essay copy.

| Chip                        | Fires when                                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| Habit — can wait            | Tier 1                                                                     |
| N days' cover left          | Tier 2 (cadence-signal present)                                            |
| Not urgent                  | Tier 2 (cadence-signal missing)                                            |
| Above your usual price      | Tier 3 (buy-verdict = wait)                                                |
| Out, but no meal booked     | Tier 4                                                                     |
| For [Recipe] on [DayName]   | Tier 5 (single-meal reference)                                             |
| Needed for [N] meals later  | Tier 5 (multi-meal reference; last-resort)                                 |

Chips render with the existing `q-chip` component; short label, muted
tint on the deferred section, primary tint on the "Show what would be
cut" preview.

---

## 6. UI surface

### 6.1 Where the banner lives

**ShoppingListDetail page**, above the line list. Not the
auto-generate modal — the modal is a "pick sources" step, and the
banner needs the final line prices, which resolve after generation. It
appears on **every** load of a list where:

- The list has `auto_generated_at` set (i.e. it came from
  auto-generate — the banner is not for manual lists),
- **AND** projected remaining total (unticked lines) > budget headroom.

If the user ticks lines while shopping and the projected total drops
back under, the banner disappears. Sticky in one direction only.

### 6.2 Banner states

- **Over budget, no trim done yet:** the three-CTA banner in §3.1.
- **Trim previewed but not applied:** banner keeps the "Trim to fit"
  button + a per-line preview underneath; each preview line has an
  inline "Keep" button to exclude it from the trim.
- **Trim applied:** banner is replaced by a compact confirmation strip
  — **"Trimmed $55 to fit. See deferred (3) →"**. Tapping the link
  scrolls to the collapsible Deferred section.
- **Under budget:** banner not shown.

### 6.3 Deferred section

A `q-expansion-item` at the bottom of the list, labelled **"Deferred
to fit budget (3)"** with the count. Each entry: line name, reason
chip, saved amount, and a **"Add back"** button that moves the entry
back into the active list (idempotent).

---

## 7. Backend shape

### 7.1 One endpoint, preview + apply modes

`POST /api/shopping-lists/<list_id>/trim-to-budget`

**Request body:**
```json
{
  "mode": "preview" | "apply",
  "budget_target_cents": 9200,        // optional; defaults to period-remaining
  "exclude_line_ids": ["uuid", ...]   // lines the user chose to keep (per §6.2)
}
```

**Response:**
```json
{
  "projected_total_cents": 14700,
  "budget_target_cents": 9200,
  "overshoot_cents": 5500,
  "trimmed": [
    { "line_id": "uuid", "reason_chip": "Habit — can wait", "saved_cents": 890 },
    ...
  ],
  "still_over_cents": 0,               // >0 if we ran out of cuttable lines
  "applied": false                     // true iff mode=apply
}
```

Preview does not mutate. Apply moves each `trimmed[]` line to a
`deferred_by_budget = True` state on `ShoppingListLine` (see §7.2).

### 7.2 Two columns on `ShoppingListLine`

`deferred_by_budget: bool` (default False) + `deferred_reason: str | None`
(the frozen chip vocab from §5). When `deferred_by_budget = True`, the
line does **not** contribute to the projected total or ticked/unticked
counts; it renders under the "Deferred" section carrying `deferred_reason`
as the chip label. One-tap "Add back" flips the flag off and clears the
reason in lock-step.

**Deviation from the original v1 sketch (which said "no reason column,
re-derive on read"):** at build time we found re-derivation would (a) re-run
the full trim classifier on every list-detail read for lists with deferred
lines — meal-plan + verdict + cadence queries per line, which get_shopping_list_detail
otherwise avoids — and (b) let the chip drift if verdict / cadence / meal-plan state
changed between the trim tap and the read (so the reason the user *saw* when they
hit "Trim to fit" could silently become a different chip a day later). Freezing the
chip at trim time removes both risks and keeps the read path free of the optimiser's
dependencies. The brief itself flagged this as the fallback ("If we later want to
freeze the reason at trim time, add a `deferred_reason: str | None` then") — we're
doing it now.

### 7.3 Budget headroom is a shared helper

Extract the "budget for a given date" computation from
[`budget.py`](../../dora_api/features/budget/budget.py) into a
reusable helper `period_headroom_cents(user, on_date)` and call it
from both the dashboard card and the new endpoint. State-ownership
R-003: server owns the budget arithmetic; the SPA never re-derives.

### 7.4 The auto_generate handler stays untouched

Auto-generate keeps its current shape. It emits the full list. The
budget-aware pass is a **second, separate call** — either fired
automatically on list-detail load (banner check) or triggered by the
"Trim to fit" button. Keeping the two paths separate makes the
optimizer opt-in per list (via the banner) and keeps auto-generate
easy to reason about.

---

## 8. Explicit non-goals (Charter Anti-creep)

Dropped from the original P2-05 spec, not to be reintroduced:

- **Multi-store strategies** (`fewest_stores`, `preferred_store`) and
  `preferred_merchants` — coupled to hosted multi-store scraping
  which `RECONCILED_FINISHING_PLAN.md` Decision 7 retired. If they
  ever come back, they belong on the C-10 ingested-products surface,
  not here.
- **Per-line suggested substitutions** (buy the cheaper store-brand,
  swap 500g pack for 1kg). Different problem shape (substitute graph);
  worth its own brief later.
- **Auto-apply on generate.** The user explicitly wanted the trim to
  be a discoverable button, not a silent step of generation.
- **A separate "budget planner" page.** Anti-creep. Everything happens
  on the list detail surface the user already reads.
- **Per-shop caps** ("keep this shop under $X"). Deferred; log as a
  follow-up if a real user request appears.
- **Retroactive re-trim** when the user manually adds a line after the
  trim. The banner will re-appear on next load if the addition pushes
  us back over budget; that's the loop.

---

## 9. From the original spec

`docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_2.md:400` (P2-05
"Budget-Aware Auto Lists") originally called for:

- **keep** — soft-warn banner (matches §3.1), per-line reasons
  (matches §5), preview-before-apply (matches §6.2).
- **keep, reshaped** — the "period-remaining vs single-shop cap"
  question the spec left open. We resolved it to period-remaining in
  §3.2; single-shop cap deferred (§8).
- **superseded** — the original priority stack the spec sketched
  (essential > planned > frequent) is subsumed and refined by our
  five-tier stack in §4, which additionally leans on the shipped
  buy-verdict oracle.
- **cut** — `preferred_merchants` + `fewest_stores` / `preferred_store`
  strategies (§8, per Decision 7).

Source is ~14 months old, pre-charter, and pre-buy-verdict. Nothing
else from the spec is worth extracting.

---

## 10. Sequencing (rough — full impl-plan is separate)

1. `period_headroom_cents(user, on_date)` helper + tests
   (state-ownership refactor, no user-visible change).
2. `deferred_by_budget` column on `ShoppingListLine` + migration +
   read-path filtering. Ships as always-False; no UI yet.
3. `POST /shopping-lists/<id>/trim-to-budget` preview mode. Tests
   cover each tier's chip vocabulary, the stopping condition, and
   the "still over" fallback.
4. Apply mode + the auto-derived reason chip on read.
5. SPA banner + preview + apply + Deferred section on ShoppingListDetail.
6. Assistant intent: **"Trim this list to my budget"** → hits the
   endpoint in apply mode; the reply summarises what got cut. Small
   surface, high leverage, matches the C10 "money features opt-in"
   posture (only fires when money features are on).

Each step is independently shippable; step 5 is the only user-facing
turn-on.

---

## 11. Verify (browser)

Added to `DORA_VERIFY.md → Shopping lists` when this ships:

- With `money_features_enabled = false`, the banner never renders on
  any auto-generated list, regardless of price.
- With money features on and no `budget_amount` set, banner never
  renders (self-gating).
- With money features on, `budget_amount = $100/week`, and
  `spend_so_far = $60` in the current period: an auto-generated list
  projecting $80 shows the banner ($40 headroom, $40 over).
- Tapping **Trim to fit** removes the highest-priced Tier-1 line
  first; if that isn't enough, descends tiers as §4 specifies.
- Trimmed lines appear in the collapsible Deferred section with the
  correct chip; "Add back" restores them and re-triggers the banner
  if now over budget.
- Manually ticking active lines while shopping shrinks the projected
  remaining; banner disappears when remaining ≤ headroom.
- When cadence has no signal for a Tier-2 candidate, the chip reads
  "Not urgent" (not "N days' cover left").
- Meal-plan-scheduled item within 2 days is **never** cut, even if
  every other cut is exhausted and we're still over budget.
- The "Trimmed everything safe. Still $X over" fallback fires when
  the remaining active list is all essentials + within-2-days meals.

---

## 12. Coverage table

FU-448 called out six shape questions (a–f); C10 in feedback-triage
constrains the whole family behind an opt-in gate; one raw feedback
bullet motivates the linkage between recipe cost → meal plan →
shopping-list budget.

| Question / Anchor                                      | Addressed in       |
|--------------------------------------------------------|--------------------|
| (a) UX shape — warn / trim / swap                      | §3.1               |
| (b) Priority stack under budget constraint             | §4                 |
| (c) Budget window — period vs single-shop              | §3.2               |
| (d) Explainability — per-line reasons                  | §5                 |
| (e) Interaction with P8-05 buy-verdict                 | §4 Tier 3          |
| (f) Which original-P2-05 pieces get dropped            | §8, §9             |
| C10 — money features opt-in & hideable                 | §2 (uses existing gate); banner/endpoint self-gate |
| Feedback L254 — recipe cost → meal plan → list budget  | Out of scope here — this brief handles the *list-side budget cap*; the recipe-cost + meal-plan-cost flow is its own downstream feature (log if not already followed up) |
| Decision 7 — hosted scraping retired                   | §8 (drops multi-store strategies) |
