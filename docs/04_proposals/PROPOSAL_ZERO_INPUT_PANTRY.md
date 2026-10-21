# P8-07 — The Zero-Input Pantry (inferred inventory) · FLAGSHIP

**Status:** Built 2026-07-03 (server + SPA). Python-env verify pending
(migrations + pytest + endpoint smoke). Browser-verify checklist in
`DORA_VERIFY.md` under Stock.
**Governing doc:** `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` — Part I §6
(the flagship) + the P8-07 prompt (Part IV) + the Charter (Part II).
**Depends on:** P6-01 intake ✅ · P6-04 cadence ✅ · P6-07 cook→consume
(built this unit as FU-449) · P6-13 stocktake ✅.

> **The one line.** Dora holds a confidence-weighted *belief* about what's in
> your kitchen — inferred from the closed loop, not from you maintaining a
> list — and asks a single targeted question only when a real decision hinges
> on something it's unsure about. *"The pantry app you never have to update."*

---

## 1. What shipped

**The belief.** For every stock item the server computes a coarse band
(Out / Low / Stocked) + a confidence (0–1, banded high/medium/low) + a
plain-English reason, from four signals:

| Signal | Source | Effect on the belief |
|---|---|---|
| Intake | last purchase (completed lists, P6-01) | anchors to Stocked; starts a fresh depletion clock |
| Cadence | mean gap between purchases (P6-04) | estimates how long a fresh buy lasts |
| Cooking | consumption events (P6-07 / FU-449) | draws the belief down faster than the calendar alone |
| Time decay | days since the last hard signal | lowers confidence + drifts Stocked → Low → Out |

**Manual override wins.** A recent `last_checked_at` (or a just-now level
change) pins the belief to the recorded level at high confidence — inference
never argues with a fresh human check, and a check resets the clock.

**Additive display (not a takeover).** The user's *recorded* level stays the
source of truth for shopping + cooking. The inferred belief renders as a
small "Dora: ~Low · medium" chip **beside** it (stock overview rows + item
detail), tooltip = the reason. When inference disagrees with the recorded
level the chip takes a warning outline. Off by a per-user Preferences toggle
(default on).

**Ask only when it matters.** No bulk stocktake prompts. A new suggestion
generator (`pantry_check`) fires a *single* targeted quick-check only when a
decision hinges on an uncertain item — it's on a shopping list you're
building (buy decision) or in a meal planned this week (cook decision) — and
the belief confidence is low. Capped at 3; reuses the P6-13 `/check` confirm.

## 2. Architecture

- **Belief core** — `dora_api/features/stock_items/pantry_belief.py`.
  `compute_belief(BeliefInputs) -> PantryBelief` is a **pure function**
  (unit-tested, no DB); `gather_beliefs_for_items` does the batched repo walk
  (no N+1). Server-owned (R-003) — the client only renders.
- **Consumption events** — `ConsumptionEvent` entity + table (FU-449).
  Written on a cook-driven level *drop* via the existing
  `PATCH /stock-items/<id>` path (new `consumption_source` / `_recipe_id`
  fields), so the level-change logic stays in one place (R-001/R-003). The
  cook-mode finish dialog tags its per-item drops `source='cook'`.
- **Endpoint** — `GET /api/stock-items/beliefs` → `{enabled, beliefs}`,
  gated on the per-user `inferred_pantry_enabled` pref.
- **SPA** — `usePantryBeliefs` (shared module cache, one fetch for the whole
  overview) + `PantryBeliefChip.vue` (additive) + the Preferences toggle.

## 3. Charter compliance (flagship — every principle called out)

1. **Effortless** ✅ — the headline win: the belief *replaces* manual level
   upkeep. Nothing new to log; cooking already updates the loop.
2. **Coarse-by-design** ✅ — a BAND (Out/Low/Stocked), never a fake count.
   Output is always one of three bands.
3. **Self-correcting & honest** ✅ — every belief carries a confidence + a
   reason; thin data → low confidence + "not sure", never a confident wrong
   answer; a check corrects + resets it.
4. **Personal beats generic** ✅ — inference is built entirely from *your*
   purchases + *your* cooking; no generic/scraped assumptions.
5. **Leverage the closed loop** ✅ — reads intake + cooking + cadence
   together; FU-449 closes the previously-missing depletion leg.
6. **Every insight → one action** ✅ — the quick-check has a single primary
   action (confirm the level); the chip's tooltip explains, then stops.
7. **Preview → approve → commit; explainable** ✅ — inference never silently
   writes a level. It only *displays* a belief; the user's confirm is the
   write. The reason IS the explanation.
8. **Ownership & privacy** ✅ — all data is the user's own loop history; no
   external calls.
9. **No legal-risk sourcing** ✅ — no external data at all.
10. **Anti-creep** ✅ — additive chip (no new page), off switch, quick-checks
    capped + decision-gated so it never nags. The middle "Sufficient" band was
    already axed to keep the model three-band.
11. **Fast & frictionless** ✅ — one batched belief fetch for the overview;
    belief is a cheap projection.
12. **Don't invent facts** ✅ — the belief is arithmetic over real events; the
    reason quotes the actual counts/dates.

**Trade-off surfaced:** Charter 2 (coarse) vs. a user's desire for precision.
Resolved per the tie-breaker (Effortless + Anti-creep): bands only, never a
count. Charter 10 (some want manual control) honoured via the default-on
opt-out.

## 4. Deliberately out of scope (logged, not silently dropped)

- Enriching the **buy-verdict** cadence detail with consumption (it stays
  purchase-cadence for its "should I buy" purpose) — the belief service is
  the canonical run-out inference that blends cooking. Opportunistic later.
- Recording consumption on **manual** level drops (only cook-sourced drops
  record today; the `source='manual'` marker exists for a future caller).

## 5. Feedback coverage

P8-07 is a champion-plan **invention**, not a feedback item, so this maps
only the bullets it touches (per the cross-cut coverage rule).

| Feedback bullet (06-Jun-2026) | Where addressed |
|---|---|
| L89 — "combine planned-meals with stock level to decide shopping; alert 'Milk is low and on 5 planned meals'" | Partially — the `pantry_check` quick-check fires when a **planned meal** needs an item whose level is uncertain (the cook-decision path). The full "low + on N meals" alert remains its own item. |
| STOCKTAKE MODE §150 — "marking down should prompt to add to list" | Complementary — inference reduces how often a manual stocktake is needed at all; the existing auto-add-when-low hook still covers the add-to-list nudge. |
| Everything else on the Stock / Stocktake surfaces | Out of scope — UI-level items unrelated to inference. |
