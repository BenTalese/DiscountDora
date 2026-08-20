# Implementation Plan — Stock Signal Consolidation

**Status:** ➗ **code-complete — all six chunks landed**, browser-verify owed on the
whole surface. (1 + 2 on 2026-08-19; Step 0, 3, 4, 5 and 6 on 2026-08-20.) The row
carries the four channels §0.2 asked for; the queue is belief-ranked; the runner is
three phases. Nothing is waiting on an owner answer.

Two decisions were **owner-amended after landing**, both recorded in place: D-14's
glow removal became *glow gated on essentials*, and Chunk 4's merge of the expiry
and open/in-use controls was **reverted** (§0.2 counts them as one channel either
way, so it bought nothing). Per-chunk detail in `DORA_WORKLOG.md` (2026-08-19
"later 7"/"later 8"; 2026-08-20 ×5) and FU-683.

**What's left is verification, not construction** — nothing on this surface has been
seen in a browser (FU-687 removed the dev-verify config), and the checks are queued
in `DORA_VERIFY.md`. Landing Chunk 1 also exposed **FU-684** — the buy verdict had never
actually worked, because an `.include()`d `stock_level` came back unhydrated and
collapsed the need axis to thin-data on every item.
**Raised:** 2026-08-19 (design session, owner-led)
**Surface:** Stock Overview row + stocktake + alerts + buy verdict
**Supersedes nothing.** Sits on top of `IMPL_PLAN_STOCK_OVERVIEW.md` (C-1, shipped),
`PROPOSAL_STOCKTAKE_MODE.md`, `PROPOSAL_ALERTS.md`, `PROPOSAL_BUY_VERDICT_ORACLE.md`.

---

## 0. Why this exists

The owner's framing, verbatim in intent: *"there's quite a bit going on for stock
overview … I can see people getting overwhelmed … stocktake, Dora thinks, expiry,
needs attention, essential, needs check, buy verdict, open/in-use, all competing
for attention."*

The investigation found the problem is **not** feature count. It is three things:

1. **Colour collision.** Amber and red each carry four and three unrelated
   meanings respectively, including semantically inverted ones on the same row.
2. **Duplicated engines.** Three independent implementations of "how often does
   this item move", two independent implementations of "what needs attention".
3. **Derived signals painted next to their own inputs**, so a roll-up competes
   with the atoms it was computed from.

The tell is that `StockRowLegend.vue` is 262 lines documenting twelve visual
states, and `AttentionRulesDialog.vue` exists at all. A decoder ring is a
symptom.

### 0.1 The collision, stated plainly

| Colour | Meaning 1 | Meaning 2 | Meaning 3 | Meaning 4 |
|---|---|---|---|---|
| Amber | Low stock (level square) | Expiring soon / essential-low (row outline) | Dora disagrees (ring on level box) | Wait before buying (ring on cart) |
| Red | Out of stock (level square) | Expired / essential-out (row outline) | **Don't** buy (ring on cart) | — |

Red on the level box means "you urgently need to buy this." Red on the cart
button eight pixels away means "don't buy this." The user cannot build a mental
model, so every glance requires decoding.

### 0.2 Row channels, before and after

**Before (9):** level square · essential stripe · WARN outline · ALERT outline ·
dimmed row · pulsing level box (stocktake) · amber ring on level box (belief) ·
coloured ring on cart (verdict) · expiry text (+ open marker).

**After (4):** level box (hue + dashed-if-uncertain) · row treatment
(outline / normal / dim, one three-band scale) · essential stripe · expiry text
(absorbing the open marker).

---

## 1. Evidence register — every finding, with location

Use this as the audit checklist. Each item is independently verifiable.

### 1.1 Live bugs

| # | Bug | Location | Impact |
|---|---|---|---|
| **B1** | Expiring-soon window hardcoded to `7` client-side, while the server resolves a household-configurable window via `effective_expiring_soon_window` | `web_app/src/composables/useStockFilters.ts:137` | Admin changes the window → alerts move, row outlines and the "Needs attention" count don't |
| **B2** | Per-user `AlertPreference` is honoured server-side but **ignored entirely** by the overview | `useStockFilters.ts:143` (`hasAlert`) vs `dora_api/features/alerts/alert_kinds.py` | User disables `expiring_soon` → bell goes quiet, pantry keeps outlining and counting those rows |
| **B3** | Alerts page deep-links to `/stock?attention=true`, which filters by the **client** rule — a different rule than the count that was tapped | `web_app/src/pages/AlertsPage.vue:331` → `StockOverview.vue:1446` | Tap "N things need attention", land on a list that doesn't contain the same N items |
| **B4** | Non-essential out-of-stock is a MEDIUM **actionable** alert server-side, but the row is **dimmed** ("out of stock, not marked essential") | `get_alerts.py:235` vs `StockRowLegend.vue` | Same item is simultaneously "act on this" and visually de-emphasised |
| **B5** | Buy verdict fires **one HTTP request per rendered row**; the module cache dedupes by id, it does not stop fan-out across distinct items | `StockItemRow.vue:390` calling `useBuyVerdict` | 200-item pantry = 200 requests to render a ring that is suppressed whenever `confidence === 'low'` — the common case |
| **B6** | Same per-line N+1 on the shopping list via `BuyVerdictBadgeInline` | `ShoppingListDetail.vue:631` | Survives B5's fix; becomes the *primary* surface once the row ring is removed |
| **B7** | `buy_verdict_enabled` is a **household** AppSetting despite being a pure per-user display overlay | `app_setting.py:59` vs `user.py:212` (`inferred_pantry_enabled`) | Confirmed by owner as a mistake — one person's UI preference changes everyone's UI |

The composable's own comment at `useBuyVerdict.ts` claims the cache stops "a page
rendering 100 rows [firing] 100 requests". That is only true on remount. Correct
the comment when fixing B5.

### 1.2 Duplication / R-003 register

| # | Duplication | Locations |
|---|---|---|
| **D1** | `14`-day Low/Out bump window declared twice | `stocktake.py` `_LOW_OUT_BUMP_WINDOW_DAYS` · `cadence.py` `_LOW_OUT_BUMP_DAYS` |
| **D2** | `90`-day auto-history window declared twice, **with a comment admitting the mirror** (`# mirrors cadence.py's _AUTO_HISTORY_WINDOW_DAYS`) | `stocktake.py` · `cadence.py` |
| **D3** | **Three** implementations of "mean gap between movements" | `pantry_belief._mean_gap_days` (unique purchase dates) · `get_buy_verdict._cadence_detail` (**identical inputs, identical math**) · `cadence.auto_band_from_history` (StockLevelChange timestamps) |
| **D4** | Cross-entity domain rule (essential × level × expiry window) computed in TypeScript — state-ownership violation | `useStockFilters.ts:143` |
| **D5** | Three gradation scales for one idea | `severity` (high/medium/low) · `tier` (actionable/FYI) · client `WARN`/`ALERT` |

D3 is the load-bearing one. Belief and the buy verdict produce the same fact in
different prose from the same inputs:

- Belief: *"~Low — bought 12 days ago, you usually finish in about 14 days."*
- Verdict: *"Running low · Bought every ~14 days · ~2 days to run-out."*

They can already contradict each other today, because belief factors in cook
events and the verdict does not.

### 1.3 Belief confidence model — safety envelope

Worked from `compute_belief` (`_CONF_HIGH = 0.66`,
`data_factor = clamp((n-1)/3, 0.25, 1.0)`,
`recency_factor = clamp(1.1 - 0.5·progress, 0.2, 1.0)`):

| Band | High-confidence reachable? | Requires |
|---|---|---|
| Out | **No** — ceiling is 0.525 | structurally impossible |
| Low | Yes | ≥4 unique purchase dates, near the band edge |
| Stocked | Yes | ≥3 unique purchase dates, recent buy (progress ≲0.2) |

Thin-data path caps at 0.4; no-data path at 0.1. Both below the gate.

Two properties that matter downstream:

- The Out ceiling is protective — Dora can never confidently assert "you're out."
- **The model has no quantity awareness.** `purchase_dates` is a set of *dates*;
  buying 1 tin and buying 12 tins are identical signals. Tolerable for a display
  chip, not for anything that writes.

---

## 2. Decisions

Each decision below was made with the owner in session on 2026-08-19. Rejected
options are recorded with their reasoning so this doesn't get relitigated.

### D-1. Belief becomes the stocktake queue's ranking input; cadence becomes the floor

Belief and cadence are **not** the same feature — stocktake is an *activity*
(a work session that produces fresh `last_checked_at` data), belief is an
*annotation*. They overlap on exactly one thing: **which items are most worth
checking.** Cadence answers with a calendar; belief answers with evidence.

- Belief has signal → queue orders **least-certain first**.
- No belief signal → falls back to **most-overdue first** (today's behaviour).

Cadence survives as the honest answer to "what do we do with no evidence", which
is what it always should have been. This is the graceful-degradation posture the
distribution charter already requires elsewhere.

**No toggle, no sort selector.** Owner directive: *"less stuff to configure is
better."* The fallback is automatic and invisible.

### D-2. Auto-check ("Dora does stocktake for you") — REJECTED

Considered and dropped. Recorded here because it is an obvious idea that will
come back.

**Why it fails, primarily:** it is a *write* solution to a *sort* problem.
Reordering already delivers the felt outcome ("Dora handled the boring ones") by
sinking high-confidence items to the bottom — with no schema change, no scope
conflict, and nothing to lie about.

**Why it is actively dangerous, secondarily:**

1. **It feeds itself.** If auto-check writes `last_checked_at`, path 1 of
   `compute_belief` fires on any hard signal within `_HARD_SIGNAL_FRESH_DAYS = 3`
   and returns `confidence=0.95, is_inferred=False,
   reason="You confirmed this today."` An inference gets laundered into a hard
   signal, and the UI tells the user they confirmed something they never looked
   at. Charter P3 (Honest) broken outright.
2. **`last_checked_at` is already overloaded** — `update_stock_item.py` bumps it
   on any level change, so it means "user *touched* this", not "user *confirmed*
   this". Auto-writes would make it three things.
3. **The reachable failure is the harmful one.** High-confidence *Stocked* is the
   easiest state to reach and its failure mode is unlogged consumption — you
   cooked without cook mode, Dora auto-confirms "stocked", you discover it's
   empty mid-recipe. Cost of a wrong Low is "you buy a spare."
4. **Traceability compounds the cost.** `StockLevelChange` has **no actor/source
   field**, and a *confirming* check produces **no row at all** (no transition,
   no log). Making auto-check traceable — the owner's explicit requirement —
   needs both a source column and a widened event model that records
   confirmations, not just changes. That is the larger half of the work.
5. **One wrong auto-confirm discredits the whole belief overlay**, including the
   parts that work.

**If it is ever revived**, these are non-negotiable: separate field
(`last_auto_verified_at`, never `last_checked_at`); path 1 accepts human signals
only; never auto-check an Essential; require a real loop event (purchase or cook)
inside the window rather than pure calendar extrapolation; never auto-check when
`differs_from_recorded`; cap consecutive auto-verifications before forcing a
human check.

### D-3. Bulk confirm — accepted, as a scan-and-exception screen

The value auto-check was reaching for, captured legitimately. `POST
/api/stocktake/bulk-check` already exists, so this is a UI affordance over an
existing endpoint plus a confidence-sorted selection.

**Critical design constraint:** it must **not** be a "Confirm all (12)" button.
Users tap that reflexively by session three, at which point it *is* auto-check
with a human-shaped fig leaf and every rejected risk returns.

Instead:

- Show the **actual items** — name, believed level, one-line reason. Not a count.
- Everything **pre-ticked**; agreeing stays one tap.
- **Unticking is cheap**, and an unticked item **flows into the walk phase**.

The value is not "confirm in bulk", it is "**disagreeing is cheap**". The screen
only works if it is laid out to be read.

### D-4. Stocktake runner becomes three phases

| Phase | Name | Posture | Content |
|---|---|---|---|
| 1 | **Review** | desk | Dora's confident set (D-3). Skipped silently when empty. |
| 2 | **Walk** | pantry | Uncertain items, least-certain first. Existing runner. |
| 3 | **Sweep** | housekeeping | Items newly dropped out of rotation. |

Shrink → work → tidy.

**Why Review comes first:** the confident items are derived from *logged
evidence* (purchases, cooks) — you don't need to be standing in the pantry to
agree with them. The uncertain ones need eyes on a shelf. Clean split of
cognitive modes, and you enter the pantry with a short list.

**Phase 3 shows only what *changed*** — items that crossed out of rotation since
the last session, not the full excluded set. The engagement gate correctly
excludes plenty of boring things (the tin you stopped buying two years ago is
*supposed* to be invisible); surfacing all of them every session is the nagging
this whole plan removes. Newly-excluded is an *event*, is a handful per session,
and decays to zero for a stable pantry.

Copy: avoid "dead items" — it judges something the user may still care about.
Prefer *"Dora's stopped tracking these — 3 items haven't moved in 60 days."*

Affordances: **mute** · **delete** · *"I still keep this"*.

> ⚠️ **Wiring detail to verify at implementation.** The engagement gate keys off
> in-stock / ever-opened / **level adjusted** in 60d / on a list in 60d. A plain
> check bumps `last_checked_at`, which may **not** be one of those signals — so
> "I still keep this" might not actually re-enter the item into rotation. If
> confirmed, the honest affordance is *set its level* (which both re-enters it
> and is the truthful action) rather than adding a force-include field that
> would just be mute's inverse.

**Edge cases (owner deferred to recommendation):**

- **Empty Review is the normal case early on.** High confidence needs ≥3 logged
  purchases, so a fresh install has zero confident items for months. Skip the
  phase silently. Don't over-invest in its polish for v1.
- **Belief display off → no Review phase.** That user opted out of Dora's
  guesses; opening their stocktake with a screen of Dora's reasoning contradicts
  the toggle. They go straight to the Walk, ordered by overdue.
- **Phase 3 needs a "last session" timestamp** to compute "newly excluded". Small
  new state that doesn't exist yet.

### D-5. One uncertainty marker on the level box — dashed, not hollow

Today the level box carries **two** decorations meaning the same thing to a user
(*this number might be wrong*): the stocktake pulse and the belief ring. Same
widget, two vocabularies, one meaning — the tightest duplication on the surface.

Collapse to **one dashed treatment**. Fires from belief when belief has signal,
from cadence when it doesn't. The user learns one thing. Reasoning lives in the
picker popover, where belief reasoning already lives.

**Dashed, not hollow** (owner agreed): hollow spends the level box's own colour
channel to express metadata *about* that colour, and it makes the least urgent
signal on the row the loudest. Dashed keeps the fill readable and stays quiet.

**Motion is removed entirely.** Animation is the loudest channel in a UI and it
was being spent on "go count something sometime this fortnight". Check the
`prefers-reduced-motion` posture in `DESIGN_STYLE_GUIDE.md` when removing.

### D-6. Attention: one server-owned rule — but assess *what it says* first

Two decisions that were initially conflated and must stay separate:

- **Where the rule lives** — one engine, server-side. Not arguable; the current
  split causes B1–B4.
- **What the rule says** — which conditions count, what tier each sits in, how
  many kinds exist. **This gets assessed with the owner first** (Step 0).

Consolidating does **not** mean adopting `alert_kinds.py` as written. Owner
context: the alerts system was largely AI-built from loose ideas and has never
been vetted — nine kinds, two tiers, per-user `AlertPreference`, an alerts page,
a bell, `act_on_alert`, and a digest email. Building on an unvetted foundation
makes it harder to change later, not easier.

### D-7. The attention outline stays — at one tier, not two

Initially proposed for removal (attention is a roll-up of atoms already on the
row). **Owner overruled, correctly:** the outline is *meant* to be eye-catching;
removing it deletes the signal and keeps the clutter. Position-based signalling
also evaporates the moment you scroll or sort by name.

But the noise is that there are **two** outlines. WARN-amber and ALERT-red mean
"sort of needs attention" and "really needs attention", and a hedged alarm gets
ignored. It is also the worst colour collision: an essential-low item gets an
amber outline wrapped around an amber level square, two different ambers
touching.

**One outline, one token, actionable-tier only.** Severity still drives *sort
order within* the outlined set — a gradient where it pays off, without spending a
colour.

This also fixes volume: an outline firing on 5% of rows works; one firing on 40%
is wallpaper.

### D-8. Non-essential out-of-stock → FYI; dim and outline become one scale

Owner call, resolving B4: *"non essential out items shouldn't be cared about,
they should be dim and at the bottom."* Demote server-side rather than making the
pantry noisier.

The three row treatments then form a single ramp that **matches the sort order
exactly**:

| Treatment | Meaning | Sort position |
|---|---|---|
| Outlined | actionable — needs you | top |
| Normal | fine | middle |
| Dimmed | FYI — out, but you didn't flag it | bottom |

Position and treatment agree instead of arguing.

### D-9. New default sort

```ts
{ value: 'attention', label: 'Needs attention (default)' }
```

First in `STOCK_SORT_OPTIONS` (`useStockFilters.ts:26`) and the new default.
Three-band primary sort per D-8, severity within the top band, **name as the
stable tiebreak** so the list doesn't shuffle unpredictably.

### D-10. Buy verdict comes off the row entirely

Owner call. The verdict was already at both decision points — `AddToListButton`
(the cart button) and `ShoppingListDetail` — so this is not a relocation, it is a
removal of ambient decoration.

An earlier proposal to show it in the cart button's popover on interaction was
**rejected by the owner**: the list picker deliberately doesn't always appear, so
there is no reliable moment to hang it on.

Verdict survives on the **item detail page** (`BuyVerdictCard` — a deliberate
"tell me about this item" surface) and the **shopping list**
(`BuyVerdictBadgeInline` — you're in buying mode). Both are places the user went
looking for it.

Consequences: the overview stops fetching verdicts entirely (B5 → zero requests,
not fewer); `AddToListButton`'s `verdict` prop likely becomes dead — **check for
other callers, then delete the prop and its branch** rather than leaving
unreachable scaffolding.

### D-11. `_need_axis` consumes `compute_belief`

Verdict becomes `belief (need) + price + waste`. One cadence engine, and the two
surfaces can no longer contradict each other. Resolves D3.

Note the pattern across all three crossovers: **belief keeps turning out to be
the domain model other features are independently approximating.** Stocktake
approximated it with a calendar; the verdict approximated it with a second copy
of its own math. That is the argument for belief as shared infrastructure rather
than an optional overlay.

### D-12. Settings scoping rule

`buy_verdict_enabled`: AppSetting → User, beside `inferred_pantry_enabled`.
Settings UI moves `AdminSystemFeaturesSettings.vue` → `AssistantSettings.vue`.
Pre-release, so a **clean migration** — drop the column, add the new one, no
backfill shim (per standing migrations policy).

The resulting line:

| Scope | Contains | Why |
|---|---|---|
| **Per-user** | `inferred_pantry_enabled`, `buy_verdict_enabled` | Dora's opinions; display-only; no shared writes |
| **Household** | `expiring_soon_window_days`, stocktake cadence band + auto-tuning, `scanning_enabled` | real behaviour; shared state |

**Candidate rule (ADR):** *settings that mutate shared state are
household-scoped; settings that only change what you see are per-user.* This is
the state-ownership principle applied to configuration. It caught a genuine
misplacement (B7) on first application, which is the evidence for promoting it.

### D-13. Per-item stocktake mute stays

Mute is a **preference**, not an inference — *"never ask me about the emergency
tin"* is not derivable from confidence at any quality. Different axis entirely.
It pairs correctly with snooze (never-ask vs ask-in-3-days).

**Health signal:** after this work, mute should stop being load-bearing. Today
it's the pressure valve for a queue that nags too much. If people still mute
heavily afterwards, the ranking is still wrong.

**A "muted items" filter was considered and dropped** (owner reversed): the
Phase-3 sweep surfaces the same concern at the right moment, and a filter that
would hardly ever be used is exactly the overview chrome this plan removes.

### D-14. Stocktake toolbar button loses its glow — **AMENDED 2026-08-20: the glow stays, gated on essentials**

> **Owner amendment, superseding the removal below.** *"I want the stocktake
> button glow — don't remove that, but maybe only make it glow if there's
> essential items needing stocktake?"*
>
> This is a better answer than either the old behaviour or D-14's removal, and
> it reframes the diagnosis: **the problem was never the glow, it was the
> condition.** "Something is due a count" is true in any real pantry at any
> time, so a glow on it is permanent, and a permanent glow is wallpaper — which
> is exactly what feedback **L103** ("the glow is not obvious enough, I almost
> didn't see it") feels like from the inside. Making it louder, as the
> 2026-08-15 change tried, can't fix a signal that never turns off. Gating it on
> `is_essential` does: it now fires on a handful of items, rarely, which is the
> only condition under which an interruption keeps working.
>
> **This also resolves the L103 contradiction** that D-14 had to record as
> deliberate — L103 is now *answered* rather than overridden.
>
> Implemented 2026-08-20: `essential_total` on `GET /api/stocktake/queue`
> (counted over the whole overdue set, not the returned page — a household past
> the 500 cap must not stop glowing exactly when it matters most) plus
> `is_essential` per queue item; `:attention="stocktakeEssentialOverdue > 0"`.
> The count still rides the label whether or not it glows, and the aria label
> names the essential count so the glow's *reason* is available non-visually.
>
> **The row-level pulse stays deleted** (D-5). That one can't be gated the same
> way — it fires on every overdue row simultaneously, so it has no rare state.
> One quiet marker per row, one loud signal at the top.

The original reasoning, kept for the record:

`StockOverview.vue:41` sets `:attention="stocktakeOverdue > 0"`, triggering
`dora-btn--attention` — a 2-second infinite pulsing glow. Same argument as D-5.
Give it the count, not the animation.

> ⚠️ **This contradicts feedback L103** (*"The glow of the stocktake button is
> not obvious enough. I almost didn't see it."*). Newer decision wins, but the
> contradiction is deliberate and recorded so it doesn't read as an oversight:
> the 2026-08-19 direction is that stocktake gets **one entry point with a
> count**, and the whole surface moves away from motion as a signal. If the count
> proves too quiet in use, the fix is prominence (size/placement//weight), not
> re-adding an infinite animation.

---

## 3. Chunked plan

Each chunk is one reviewable PR. **Step 0 gates Chunk 3.**

### Step 0 — Alerts assessment (owner-in-the-loop) ★ GATES CHUNK 3 — **DONE 2026-08-20**

No code. Produces the rule content that Chunk 3 implements.

**Answers, as given.** Governing principle the owner stated: *"these are all fluff
— we want people to actually pay attention when there's a notification."* Every
answer below follows from it.

| # | Question | Answer |
|---|---|---|
| 1 | Which of the nine kinds are wanted? | **Cut three** — `out_of_stock`, `low_stock`, `stocktake_overdue`. Six survive. |
| 2 | Does per-user `AlertPreference` earn its complexity? | **Keep per-kind on/off** (that's the L441 ask), **drop `tier_override`**. |
| 3 | Is actionable/FYI right, given `severity`? | **Severity only.** Tier becomes a derived read, not a stored, overridable field. |
| 4 | Does the digest email survive? | **No.** Cut `send_alerts_digest.py` and its whole lane. |
| 5 | Confirm D-8 (non-essential out → FYI)? | **Superseded by Q1** — see below. |

**Q1 supersedes D-8's server half.** D-8 proposed demoting non-essential
out-of-stock from actionable to FYI. Q1 cut the kind outright, so there is no
alert to demote — the condition simply stops being an alert. **D-8's row half is
untouched and still governs Chunk 4**: non-essential + out is still *dimmed and
sorted to the bottom*, because that treatment reads off the item's stock level,
not off an alert. The ramp in D-8 stands exactly as written; only its middle
column's provenance changes.

#### The canonical attention rule (the Chunk 3 target)

An item **needs attention** when, for the requesting user, any enabled kind fires:

| Condition | Kind | Severity |
|---|---|---|
| `expiry_date` < today | `expired` | high |
| 0 ≤ days to expiry ≤ the configurable window | `expiring_soon` | medium |
| `is_essential` **and** (low **or** out) | `essential_low` | high |

Nothing else. Non-essential low, non-essential out and stocktake-overdue are **not
attention** — they are visible on the row (level band) or in the runner (queue),
which is where they belong.

Three forward-looking nudges survive unchanged and are **not** per-item, so they
never touch a stock row: `no_planned_meals`, `shopping_day`,
`meal_reconcile_overdue`. Severity `low`.

**Tier is derived, not stored:** `actionable ⇔ severity ∈ {high, medium}`. With the
cut set that lands cleanly — the three stock kinds are all actionable, the three
nudges all FYI — so the bell badge counts exactly the per-item attention set plus
nothing. `AlertPreference.tier_override` is deleted; `enabled` stays.

**The rule is evaluated per requesting user** (a disabled kind stops firing for
that user everywhere), which is what closes B2: the row outline, the
"Needs attention" chip + footer count, and the AlertsPage deep-link all consume
this one server answer instead of three client re-derivations.

**Open decision from §5 also closed:** "is pantry-wide verdict browsing a real
browse mode?" — **no**. The verdict is off the row (D-10) and the attention rule
above deliberately excludes buying signals; the shopping-list flow covers it.
FU-649 can close with that answer.

### Chunk 1 — Constant + cadence consolidation (backend only, no UI)

- Collapse D1/D2 duplicated constants to one home.
- `_need_axis` / `_cadence_detail` consume `compute_belief` (D-11, resolves D3).
- Add a bulk buy-verdict endpoint for a list's lines (B6), shaped on
  `gather_beliefs_for_items`.
- Correct the misleading cache comment in `useBuyVerdict.ts`.

Independently valuable, no design dependency, unblocks nothing else. Safe first.

### Chunk 2 — Verdict off the row + settings scope

- Remove the verdict ring from `StockItemRow` (D-10); stop fetching per row (B5).
- Verify + delete `AddToListButton`'s now-dead `verdict` prop and branch.
- `buy_verdict_enabled` AppSetting → User; move the settings UI (D-12, B7).
- Wire the shopping list to the Chunk-1 bulk endpoint.

### Chunk 3 — One attention rule (Step 0 answered 2026-08-20)

Split in two on size — 3a is the alerts surface, 3b is the stock surface that
consumes it.

**3a — the Step-0 cuts (server + alerts page)**
- Delete kinds `out_of_stock`, `low_stock`, `stocktake_overdue` (closes B4 — the
  condition that was actionable-and-dimmed no longer exists).
- Tier derived from severity; delete `AlertPreference.tier_override` and the tier
  segmented control on `AlertsPage`. `enabled` stays.
- Delete the digest email lane: `send_alerts_digest.py`, its template, its
  scheduler tick, `User.alerts_email_cadence` and the settings row.

**3b — attention on the stock DTO**
- Implement the canonical rule server-side, per requesting user; expose per-item
  attention on the stock-item DTO.
- Delete client `hasAlert` (D4) — closes B1, B2, B3 at once.
- Collapse WARN/ALERT to one outline token (D-7).
- Delete `AttentionRulesDialog.vue`, or collapse it into whatever documents the
  bell.

### Chunk 4 — Sort + row treatments — **DONE 2026-08-20**

- ✅ New default sort (D-9). `attention` is first in `STOCK_SORT_OPTIONS` and the
  default axis; `migrateStockSort` falls back to it instead of Name (a stored
  `name` is still honoured — that was a choice someone made).
- ✅ Three-band treatment scale (D-8), as one exported `attentionBand()` the
  comparator and the row both read. **This found a live bug:** the bands weren't
  exclusive — an expired, out-of-stock, non-essential row got the attention
  outline *and* the dim, i.e. "act on this" and "ignore this" on one row, the
  same contradiction B4 named one layer down. `stock-row--dim` now requires
  `!needsAttention`.
- ✅ One dashed uncertainty marker (D-5). The stocktake pulse and the belief ring
  are both deleted — keyframes, reduced-motion block and all — replaced by
  `--uncertain` (2px dashed, no motion). Belief wins the *wording* when both
  fire; the picker popover is the only place that says which reason it was, and
  it gained a stocktake header for the cadence case.
- ➗ Stocktake button glow — removed, then **restored gated on essentials** on
  owner challenge the same day. See the D-14 amendment above; the gate *is* the
  design, and it answers L103 rather than overriding it.
- ❌ **Open/in-use folded into the expiry control — built, then REVERTED on owner
  challenge** (*"do you mean expiry and open buttons were merged? that feels like
  the wrong move somehow"*). He was right, and this plan's own numbers say so:
  **§0.2 counts "expiry text (+ open marker)" as ONE channel in both the
  before (9) and the after (4) list** — so merging the two *controls* reduced the
  channel count by **zero**. The costs were real: a one-tap toggle became a
  two-tap menu trip, and one glyph was made to carry two unrelated meanings in
  two encodings (shape = open, colour = expiry), which is the exact overloading
  this plan exists to remove. The bullet meant *don't state "open" twice on the
  row*, not *delete the button* — and the row already satisfied it. Both controls
  are back as they were, with the reasoning recorded in the template so nobody
  re-does the merge from reading the bullet literally.
- ✅ `StockRowLegend.vue` rewritten and it did shrink: **9 documented channels →
  4**. Gone entirely (not reworded): the amber warn tier, three cart-verdict
  rings, the belief ring, the pulse.
- ➕ Not in the chunk list, found while doing it: `AttentionRulesDialog.vue` was
  still documenting the two-tier outline, the cart verdict rings (removed by
  D-10 in **Chunk 2**) and an essential stripe in the wrong colour and width. Its
  cheat sheet also had separate Outline and Dimmed columns, which let it describe
  band combinations the row cannot render. Rewritten to the one three-band
  column + where each band sorts.

### Chunk 5 — Queue ranking — **DONE 2026-08-20**

- ✅ Belief ranks the queue; cadence is the floor and the fallback (D-1). The rule
  lives in its own pure module, `features/stocktake/queue_ranking.py`, the way Chunk
  3's attention rule does — membership stays entirely `resolve_overdue_map`'s job, so
  nothing about *who* is due changed.
- ✅ No toggle, no selector. Which meant the order had to explain itself instead:
  see the two copy changes below.
- **Three ranks, not two.** D-1 names the two ends (least-certain first, most-overdue
  as fallback); implementing it needed a decision about where "no evidence" sits
  relative to "Dora is confident", and the answer is **in between**:
  `uncertain` → `overdue` → `confident`. Not knowing whether we know is a better
  reason to walk than knowing. Recorded because it's a real choice D-1 didn't make.
- **`confident` sinks, it does not leave the queue.** Tempting and wrong: belief has
  no quantity awareness (§1.3) and reaches "high" off ~3 logged purchases, so it's a
  good ranking signal and a bad authority. Cadence still says these are due.
  Conveniently, that rank *is* Chunk 6's Review set (D-3/D-4) — which is why the rank
  is a named, exposed field rather than an anonymous sort key.
- **`medium` confidence counts as uncertain**, even though `inference_overlay` will
  happily remark on a medium belief. Remarking is cheap and reversible; ranking an
  item *down* the walk on a medium hunch risks never reaching it. Bias toward walking.
- **A non-inferred belief is not signal.** `is_inferred == False` means the belief is
  echoing a level the user confirmed recently — that says the *record* is fresh, not
  that the shelf was counted, so those rank `overdue` and sort by the calendar.
- **Gated on the user's stock-inference opt-in** (`inference_overlay.SURFACE_STOCK`,
  reusing `current_user` + `surface_enabled` rather than adding an 18th copy of the
  session→user dance — FU-654 tracks that sweep). Inference off ⇒ pure cadence order,
  pinned by a test as byte-for-byte the old ordering. Ranking a list by an inference
  the user opted out of, on a screen that then can't explain itself, is worse than not
  ranking it.
- ✅ Queue DTO gained `check_rank` + `belief_band` / `belief_confidence` /
  `belief_reason`, and the response gained **`ranked_by`** (`belief` | `cadence`).
  `ranked_by` exists because "every row is `overdue`" is ambiguous — it means both
  "inference is off" and "inference is on but nothing has evidence yet", and those
  deserve different explanations.
- ✅ Runner copy: the item card now carries *"Dora's not sure about this one — …"* in
  belief's own words when belief is why that row came up, and the help dialog explains
  least-certain-first instead of claiming most-overdue-first. Beliefs are gathered for
  the **overdue set only** — the overview polls this endpoint on every load.
- 12 new unit tests on the rule; queue shape assertions updated.

### Chunk 6 — Runner three-phase rebuild — **DONE 2026-08-20**

- ✅ **Review → Walk → Sweep**, one read (`GET /api/stocktake/session`) and a
  phase machine in `StocktakeRunner.vue`. Each phase is **skipped silently** when
  empty, per D-4's edge cases: an empty Review is the normal case for months on a
  young install, and announcing "0 items to review" is a screen whose only content
  is its own absence. Review and Sweep are their own components
  (`components/stocktake/`), leaving the page as the phase machine plus the walk.
- ✅ **`User.stocktake_last_session_at`** (migration `f2a6d4b8c917`), the watermark
  the Sweep needs. **Per-user, not household** — a stocktake is a shared activity
  but "what changed since *I* last looked" is personal, and household scoping
  would have two people blanking each other's Sweep. **NULL ⇒ empty Sweep**, so
  the phase's debut can't dump every long-dead item into it.
- ✅ **The Sweep dates departures rather than storing them.** Both of the
  engagement gate's time-windowed signals expire on a schedule, so
  `dropped_out_at = last_activity + ENGAGEMENT_WINDOW`, and "newly" is that
  instant falling after the watermark. No history table, no nightly job, and it
  can't drift from the gate because it reads the same two events. Items with *no*
  activity at all are excluded — never tracked, rather than newly untracked.
  Muted items are excluded too: mute already said "don't nag me about this", so
  reporting it back is telling the user something they said first.
- ✅ **Review is a scan-and-exception screen, not "Confirm all (12)"** (D-3's
  critical constraint). Real names, believed level, and Dora's one-line reason per
  row; everything pre-ticked; the button counts what it will write. Unticked rows
  are **prepended** to the walk, not appended — the user just said "I want to look
  at this myself", and making them walk the whole queue first would punish exactly
  the disagreement the screen exists to make cheap.
- ✅ **`POST /api/stocktake/session/complete`** stamps the watermark, called once
  when the run reaches its summary — never per phase, never on abandon. Once the
  watermark passes a departure that item is indistinguishable from the long-dead
  ones, so a run backed out of must not swallow a Sweep list nobody saw. A failed
  stamp is deliberately silent (cost: seeing the same tidy-up list next time).

#### The D-4 wiring risk — **CONFIRMED, and the plan's fallback was right**
> *"A plain check bumps `last_checked_at`, which may **not** be one of those
> signals — so 'I still keep this' might not actually re-enter the item."*

Verified in code: `_is_engaged` keys off in-stock / `opened_on` / a
`StockLevelChange` in 60d / a shopping-list appearance in 60d, and
`POST /stock-items/<id>/check` writes `last_checked_at` and `snoozed_until` only.
So wiring that button to a check **would have looked like it worked and changed
nothing** — the item would have reappeared in the next Sweep. Taking the plan's
recommended fallback: **"I still keep this" opens the level picker**, and setting
a level writes a `StockLevelChange` (and for anything in stock satisfies the gate
outright). No force-include column was added; as the plan predicted, it would
have been mute's inverse. It's also the truthful action — the reason Dora lost
track is that nobody has said what's on the shelf.

- 8 new unit tests on the Sweep rule (including both boundary cases: a departure
  exactly *at* the watermark counts as already-seen, and a not-yet-elapsed window
  is never announced early), 4 new e2e on the session endpoints.

**Suggested order:** 1 → 2 → (Step 0) → 3 → 4 → 5 → 6. Chunks 1 and 2 can land
while Step 0 is still being decided.

---

## 4. Standards & charter alignment

**R-003 / state-ownership** — this plan is mostly *paying down* R-003 debt: D1,
D2, D3, D4 are all existing violations. The new server-owned attention field
moves a cross-entity rule off the client, which is the principle's core case.

**Design guide (R-035 / D-rules)** — colour semantics are the substance of D-5,
D-7, D-8. Motion removal (D-5, D-14) must be checked against the guide's
`prefers-reduced-motion` posture. The three-band treatment ramp needs its tokens
confirmed against the Part A role table.

**Charter** — P1 Effortless (a surface needing a 262-line legend isn't), P3
Honest (D-2's rejection is squarely this), P12 No-invent (D-2 again),
Anti-creep tiebreak (D-2, D-13's dropped filter).

**Distribution posture** — no data-access, auth, config, or deployment changes
beyond D-12's column move. Graceful degradation is explicitly designed in (D-1).

**ADR candidate** — the D-12 scoping rule. Recommend promoting to `R-0NN` if it
survives one more application.

---

## 5. Open decisions — closed

Every fork raised in the session is resolved above. For the record:

| Question | Resolution |
|---|---|
| Auto-check: ship it? | **No** — D-2, with revival conditions recorded |
| Ordering: toggle, selector, or automatic? | **Automatic**, no config — D-1 |
| Hollow or dashed uncertainty marker? | **Dashed** — D-5 |
| Keep the attention outline? | **Yes, one tier** — D-7 |
| Adopt `alert_kinds.py` as the consolidation target? | **Not as-written** — Step 0 first — D-6 |
| Muted-items filter? | **Dropped** — D-13 |
| Verdict in the cart popover? | **No** — picker is deliberately conditional — D-10 |
| `buy_verdict_enabled` scope? | **Per-user** — D-12 |
| Per-item mute survives? | **Yes** — D-13 |
| Runner edge cases (empty Review / belief-off / last-session state) | Owner deferred to recommendation — D-4 |
| Which alert kinds survive? | **Six** — `out_of_stock` / `low_stock` / `stocktake_overdue` cut — Step 0 Q1 |
| Per-user alert prefs? | **On/off yes, tier override no** — Step 0 Q2 |
| `severity` vs `tier`? | **Severity only, tier derived** — Step 0 Q3 |
| Digest email? | **Cut** — Step 0 Q4 |
| Is pantry-wide verdict browsing a real browse mode? | **No** — Step 0; closes FU-649 |

**Open decisions — closed.** Nothing in this plan is now waiting on an answer.

---

## 6. Feedback coverage — STOCK OVERVIEW (L63–L108) + ALERTS (L436–L442)

Per the mandatory cross-check rule. Bullets this work *targets*; everything else
on the surface is owned by `IMPL_PLAN_STOCK_OVERVIEW.md` (shipped).

| Line | Summary | Where |
|---|---|---|
| L66 | "Highlighting rules feel weird … essential highlights and puts a red dot" | D-7, D-8 — one outline tier, dim/normal/outline ramp |
| L77 | "Highlight should move to the whole row item outline" | D-7 — outline retained, tier collapsed |
| **L80** | **"What are the current highlighting/outline colour rules? Should be hashed out and refined"** | **§0.1, D-5, D-7, D-8 — the core bullet this plan answers** |
| L82 | "Red status indicator is visual noise … no information not already visible" | §0.2 + D-7 — the same argument, applied to derived signals generally |
| L91 | Selection colour interfering with status colour | Partially — the reduced palette gives selection room; full fix stays with C-1 Chunk 3 |
| L93 | Counts in sticky footer incl. "needs attention" | Count now derives from the server rule (Chunk 3); footer layout unchanged |
| L103 | "Glow of the stocktake button is not obvious enough" | **D-14 — deliberately contradicted.** Rationale recorded there |
| L438 | "An alert control screen feels like it's missing" | Step 0 Q2 — informs whether the prefs surface survives |
| L439 | "Number of alerts doesn't add up to the number bubble" | B3 — same class of defect (two rules, one label); Chunk 3 |
| **L440** | **"Alerts could be smarter with priority and what's actually an alert"** | **Step 0 Q1/Q3 — the assessment this bullet asks for** |
| L441 | "Users should opt in/out of alert types — as quiet or noisy as they want" | Step 0 Q2; B2 is the live bug blocking this working today |
| L442 | "no planned meals for next week" alert type | Out of scope — already shipped as `no_planned_meals` |

**Out of scope, named:** L65 (nav lag), L67–L79, L81, L83–L90, L92, L94–L102,
L104–L108 — owned by `IMPL_PLAN_STOCK_OVERVIEW.md`. L73 (scan mode "possibly
incorporate into stocktake?") is adjacent to D-4's runner rebuild but stays
deferred with the `scanning_enabled` work.

Run `COVERAGE_GAPS.md` after Step 0 to flip L80 / L440 gap → covered.
