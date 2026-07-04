# PROPOSAL — Stocktake Mode redesign (the walk-the-pantry surface)

- **Status:** 🔵 designed-not-built — **decisions locked** (all open questions
  resolved with the user 2026-07-04). Ready to become an implementation plan.
- **Raised by:** FU-430 (Stocktake redesign brief) + FU-226 (queue-rule
  assessment) — merged. FU-226 owned the *engagement gate* tuning; FU-430 owned
  the broader *review-mode* redesign.
- **Date:** 2026-07-04.
- **Governing docs:** `RECONCILED_FINISHING_PLAN.md` §5 (Phase 1 loop),
  `DASHY_DORA_CHAMPION_PLAN.md` Part II Charter (P1 Effortless, anti-creep
  tiebreak), `ENGINEERING_STANDARDS.md` (R-003 state-ownership, R-005
  distribution posture, R-006 clean migrations).

---

## 1. The problem, framed

Stocktake is Dora's "open the cupboard and eyeball each item" surface. Three
separate questions were historically tangled into one confusing rule set. This
brief keeps them apart, because each has a clean answer on its own:

1. **Who** does Dora nag you about? → the **engagement gate** (§2).
2. **How often** does it nag you about each one? → **cadence** (§4).
3. **What can you do** when it nags you? → the **resolution verbs** (§5).

"Essential" got smeared across all three; it now has exactly one job (§3).

Current code: [`stocktake.py`](../../dora_api/features/stocktake/stocktake.py)
(queue + `/check` + `/bulk-check` + shopping-list `review/complete`),
[`StocktakePage.vue`](../../web_app/src/pages/StocktakePage.vue) (landing) and
[`StocktakeRunner.vue`](../../web_app/src/pages/StocktakeRunner.vue) (focused
one-item-at-a-time flow). Much of the flow already exists — this is
*adjust + extend*, not build-from-scratch.

**Explicitly OUT of scope (cut with the user):** expiry-driven surfacing and a
Waste verb in stocktake. Expiring items are handled by the Stock Overview's
expiring quick-filter + log-waste-there; stocktake stays purely cadence-driven.
This retires the 2026-07-02 FU-226 extension (see §6).

---

## 2. Who gets nagged — one honest question

**The gate asks exactly one thing:** *do you actually keep this item?* Flags
change how an in-play item is *treated*, not *whether it's tracked*.

An item is **in play** (eligible to surface) when **any** is true:

- It's **in stock** right now (`stock_level.sequence < OUT_OF_STOCK_SEQUENCE`), or
- It's been **opened** (`opened_on is not None`), or
- Its level was **adjusted in the last 60 days** (a `StockLevelChange` within the
  window), or
- It was **on a shopping list in the last 60 days** (a `ShoppingListLine` on a
  list whose lifecycle timestamp is within the window; active lists always count).

If none is true, Dora stays silent — the item still exists in stock, it just
doesn't chase you.

### Deliberate changes from the round-18 rule

- **`is_flagged` (Essential) and `auto_add_when_low` REMOVED as gate signals.**
  This fixes "essential + never bought doesn't make sense": a flag never forces
  a not-actually-kept item into the queue. `auto_add_when_low` plays **no role**
  here — it's restock automation, a different switch. Essential becomes a
  cadence modifier only (§3).
- **The two history signals gain a 60-day window** (were unbounded → "on a list
  once 5 months ago, nags forever"). ~2 grocery cycles; ages out abandoned items
  without disturbing normal shop→buy→use rhythms.

### Worked examples

| Item | Round-18 today | Under this brief |
|---|---|---|
| Fresh stub you typed in, never touched | Silent | Silent |
| Essential you flagged but don't stock | **Nags** | **Silent** (flag isn't a gate) |
| Bought once 4 months ago, nothing since | **Nags forever** | **Silent** (60-day window) |
| In stock / opened / recently touched | Nags per cadence | Nags per cadence |

---

## 3. Essential — one job only

> **Essential = "check this one more often, it matters."**

- It does **not** put an item in play, and does **not** mean "buy this."
- Its only effect: when an item is already in play, Essential shifts its cadence
  **one band faster** (§4) — Monthly→Fortnightly→Weekly, capped at Weekly.
- Applies whether Auto is on or off.

Essential is the **one deliberate per-item lever** — a single pre-existing toggle
on items that matter, not per-item number-tuning. **There is no per-item
Weekly/Fortnightly/Monthly picker, ever** — nobody hand-tunes 200 items. The
only sources of per-item cadence difference are Essential (a coarse toggle) and
Auto (§4).

---

## 4. How often — cadence as three bands

| Band | Days | For |
|---|---|---|
| **Weekly** | 7 | fast movers / important |
| **Fortnightly** | 14 | the default |
| **Monthly** | 30 | slow, stable stock |

**Two global settings** (§8 — new "Stocktake" settings block):

1. **Default cadence band** — Weekly / Fortnightly / Monthly, **default
   Fortnightly**. Applied uniformly to every item.
2. **Auto-tuning** — a toggle, **ON by default** ("auto = speed").

**When Auto is OFF:** every item uses the global default band. Essential still
shifts its item one band faster. That's the whole rule — dumb and uniform.

**When Auto is ON:** Dora derives each item's band from its movement history —
the trailing **90 days** of `StockLevelChange` rows:

- **avg gap ≤ 10 days** → **Weekly** (fast mover)
- **avg gap 11–24 days** → **Fortnightly**
- **avg gap ≥ 25 days**, or no changes in the window → **Monthly** (stable)
- **hit Low or Out in the last 14 days** → bump **one band faster** (actively
  depleting)
- Essential then bumps **one more band faster** on top.

A brand-new item has no history → it uses the **global default band** until
enough history accrues for Auto to speak.

This is the self-tuning the user asked for: active items climb toward Weekly,
dormant ones relax to Monthly, and if an item goes fully quiet past 60 days it
drops out of the queue entirely (the §2 gate). Two graceful fades — cadence
relaxes first, then the gate removes it.

**When is an item "overdue"?** `days_since_baseline > band_days`, where
**baseline = `last_checked_at`, falling back to `created_at`** when never checked
(see §4.1). Ordering: most-overdue first → oldest baseline → name.

**R-003:** band resolution, overdue maths, and the engagement gate are all
**server-owned derived facts**. The client renders; it never re-derives a band
or a threshold. The queue DTO carries the resolved band + overdue days.

### 4.1 Never-checked items — grace period

Round-18 pinned never-checked items to the top via a `9999` sentinel. **Replace
that with a grace period:** a never-checked item uses `created_at` as its overdue
baseline, so it becomes due exactly **one band after you added it** — the same
rule as everything else. No more "type in a new item → it's instantly top of the
queue." The row can still be *labelled* "never checked" for clarity, but it no
longer jumps the line. **Drop the `9999` sentinel.**

---

## 5. What you can do — the resolution verbs

The runner card shows the item, its current level, and how overdue it is, then:

**Primary row (two big buttons, side by side):**

| Button | Meaning | Effect |
|---|---|---|
| **Still correct** | "I looked — level's right." | `last_checked_at = now`; advance. |
| **Change level** | "I looked — and set it." | Opens the colour level picker; on pick, sets level **and** bumps `last_checked_at`; advance. **The button itself displays the current level's name + colour, with small "(change)" beneath** — so it doubles as the level readout (resolves old SK-8/SK-9). |

**Secondary row (three smaller buttons):**

| Button | Meaning | Effect |
|---|---|---|
| **Skip** | "Later *today* — keep reminding me." | Session-only: drops to the end of this session; **no clock change**; reappears if the queue is reopened. |
| **Push** | "Not now — stop asking for a few days." | Sets `snoozed_until = now + 3 days`; **no `last_checked_at` stamp** (makes no claim the stock is right); advance. |
| **Mute** | "Stop nagging about this item." | **Confirmation dialog first**, then `stocktake_alerts_are_enabled = false`; advance. Reversible from the item's detail page. |

**Why Push ≠ Still correct:** "Still correct" asserts you verified it and resets
the full cadence clock. Push is the honest defer — it doesn't lie by stamping a
verification that never happened. **Why Skip ≠ Push:** Skip is session-only ("get
to it this afternoon"); Push persists for 3 days across sessions.

**Dropped:** the standalone **Out of stock** button (Out is just a level in the
Change-level picker) and the **per-item "Add to list"** button (moves to the
completion screen — §5.2). **No keyboard shortcuts** in the runner (buttons only;
resolves SK-4/SK-10). The level picker dialog renders **level colours** like the
Stock Overview (SK-8).

### 5.1 No landing page

Tapping **Stocktake** drops the user **straight into the runner** on the first
item — no intermediate landing (the old `StocktakePage.vue` is retired). The
count is always visible in the runner's progress strip, so a pre-count screen
adds nothing. A **`(?)` help affordance** in the runner explains "how stocktake
works" (this is where the old explainer text + any shortcut/behaviour notes live
— resolves SK-1 "no Refresh button" and SK-2 "top-of-queue text feels obvious",
both by removing the screen that hosted them).

### 5.2 Completion screen

At the end of the session, the summary card shows counts —
**Checked / Changed / Skipped / Pushed / Muted** — and hosts the batch
**add-to-list** step (SK-7): *"You marked these Out/Low — add them to your
shopping list?"* with an add-all action. One decision for the whole walk; the
per-item add button is gone. (This also sidesteps the old SK-11 double-toast,
since the single-item `addToList` path is no longer invoked mid-runner.)

---

## 6. Expiry & Waste — considered and CUT

The 2026-07-02 FU-226 extension proposed folding expiry-surfacing and a Waste
verb into stocktake ("two halves of one walk"). **Cut, per the user:**

- **Expiry stays out of the queue.** Stocktake is purely cadence-driven. Expiring
  items are found via the **Stock Overview's expiring quick-filter**, and waste
  is logged **there**. No dual-mode queue, no `?mode=expiring`, no
  `entry_reason`-for-expiry, no synthetic-overdue pinning.
- **No Waste verb in stocktake.** One surface for waste (Overview + item detail),
  not two.

Rationale: anti-creep. The expiry/waste flow already exists and works; a second
surface duplicates it. This keeps stocktake calm and single-purpose.

---

## 7. Data-model & API impact (for the implementer)

**New global settings** (install-scoped, config/DB-driven — R-005):
- `stocktake_default_cadence_band` — enum {weekly, fortnightly, monthly},
  default **fortnightly**.
- `stocktake_auto_tuning_enabled` — bool, default **true**.

**StockItem:**
- Add `snoozed_until` (nullable timestamp). Queue excludes `snoozed_until > now`.
- `days_until_stocktake_alert` (per-item int) is **superseded** by the band
  system — no longer user-settable (no per-item picker). Clean migration
  (R-006): stop surfacing/writing it; the resolved cadence is computed
  server-side from band + Essential + Auto. Decide keep-as-dead-column vs drop in
  the impl plan.
- `stocktake_alerts_are_enabled` (existing) — now toggled by **Mute** in the
  runner + reversible on item detail.
- `is_flagged` (existing Essential) — drives the §3 one-band-faster shift.

**Queue logic (`stocktake.py`):**
- Engagement gate: remove `is_flagged`/`auto_add_when_low` from `_is_engaged`;
  add **60-day windows** to the two history signals (join list lifecycle
  timestamp / change `created_at`).
- `_compute_overdue`: **drop the `9999` sentinel**; baseline = `last_checked_at
  or created_at`.
- Band resolution: new server-side helper (global default + Auto-from-history +
  Essential bump), reflected in the DTO.
- **Change-level should also bump `last_checked_at`** — today `onPickLevel`
  only sets the level; verifying-and-correcting is still a check.

**Endpoints:**
- `POST /stock-items/<id>/snooze` (Push; body `{days: 3}` or fixed).
- Mute via existing PATCH of `stocktake_alerts_are_enabled` (no new endpoint
  needed).
- Queue DTO gains resolved band (for display); `overdue_days` kept.

**Stock Overview (`R-003` display):**
- Overdue in-play rows get a **pulsing outline around the stock-level button**,
  matching the stocktake attention glow.
- A **"Needs check" quick-filter** chip. Both read the server's overdue flag —
  no client-side re-derivation of "overdue".

**R-005:** all repository-routed, Postgres+SQLite portable; new settings are
config-driven, not hardcoded.

---

## 8. Settings

A new **"Stocktake" block** in the Settings page (near Stock / Alerts):
- **Default check cadence** selector — Weekly / Fortnightly / Monthly (default
  Fortnightly).
- **Auto-tuning** toggle (on by default) + a one-line explainer of what it does
  ("Dora checks fast-moving items more often and stable ones less").

---

## 9. From the original spec

`00_original_spec/Taskboard Notes/Need some way to check on stock levels…`
(pre-~100k-LOC, **historical / non-authoritative**) seeded this feature:
last-checked distinct from last-updated; a stock-alerts badge; "this stock item
is okay" to acknowledge; and **highlight overdue rows on the Stock Overview**.

- **keep / now building** — the *overdue-row highlight on the Stock Overview*,
  realised as the §7 pulsing outline around the stock-level button. Matches the
  original intent and the user's explicit direction.
- **superseded** — the raw incrementing badge count is subsumed by the richer
  queue + attention-glow already shipped.

---

## 10. Feedback coverage table (MANDATORY)

Every Stocktake Mode bullet from `Feedback _ Fixes - as of [06-Jun-2026].md`
(§ STOCKTAKE MODE). SK-N = document order.

| # | Feedback bullet | Resolution |
|---|---|---|
| SK-1 | Doesn't need a refresh button | ✅ §5.1 — landing removed; Refresh gone. |
| SK-2 | Top-of-queue info text feels obvious | ✅ §5.1 — landing removed; explainer → `(?)` help. |
| SK-3 | Text feels small all over | Out of scope — app-wide type-scale, not Stocktake-specific. |
| SK-4 | Keyboard shortcuts on buttons look tacky | ✅ §5 — shortcuts dropped entirely; labels cleaned. |
| SK-5 | Skip button should be as big as others | ✅ §5 — **reframed**: Skip is a meta-action → intentionally one of the *smaller* secondary buttons. |
| SK-6 | What are the rules for the list? Let's review | ✅ §2 (gate) + §4 (cadence) — the whole who/how-often redesign. The anchor. |
| SK-7 | Buttons never prompt add-to-shopping-list | ✅ §5.2 — completion-screen batch add. |
| SK-8 | Stock-level change doesn't show colours | ✅ §5 — Change-level button + picker render level colours. |
| SK-9 | Colour differ between "still correct" and "change level"? | ✅ §5 — Still-correct = positive; Change-level takes the current level's colour. |
| SK-10 | Skip shortcut should be `4` | ✅ §5 — moot; all shortcuts dropped. |
| SK-11 | Shopping-list button unaware of list state; double toast | ✅ Already fixed (single-item `addToList` path) + §5.2 removes the mid-runner button entirely. |

`COVERAGE_GAPS.md` has no per-SK rows to flip.

---

## 11. Open decisions

**All resolved 2026-07-04.** For the record:
- Push window → **fixed 3 days** (no picker).
- Expiring-queue shape → **cut** (expiry out of stocktake).
- Add-to-list → **completion-screen batch**.
- Never-checked → **grace period** (`created_at` baseline, drop `9999`).
- Bulk mode → **runner-only** (no list/bulk mode).
- Essential → **cadence-only, one band faster; the sole per-item lever**.
- Auto → **full two-way mapping, ON by default; Fortnightly default band**.

The only implementation-level call left for the impl plan: whether to **drop or
dead-column** `days_until_stocktake_alert` (§7).
