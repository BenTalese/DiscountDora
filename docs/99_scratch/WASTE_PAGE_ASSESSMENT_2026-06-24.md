# Thoughts on the Waste page

*Scratch assessment — 2026-06-24. Source of POV: a planning session, not a delivery prompt. Triage as keep / convert-to-prompt / discard.*

## Context

You asked for an honest, broad assessment of `/waste` — including whether it
should be removed. I read the page, its backend, every doc that mentions
waste, and the peer pages it sits beside in nav. This is my POV, not a
delivery plan. If you like a direction, the next session can convert it into a
prompt.

---

## What the page actually does today

[`WastePage.vue`](../../web_app/src/pages/WastePage.vue) (525 LOC) does **three
jobs stitched into one screen**:

1. **Forward-looking rescue** — "Use soon" panel with a 3/7/14/30-day
   horizon, three one-tap actions per item (Used / Freeze / Wasted), and
   pre-filled value from the most recent shopping-list line.
2. **Recipe match** — right-hand panel ranking favourited recipes by overlap
   with at-risk items (uses the cookbook ranking, optional ingredients
   ignored per §1.9).
3. **Backward-looking insights** — bottom strip showing 90-day waste totals
   and top-wasted items with reason breakdown, conditional on data
   existing.

Backend is [`waste.py`](../../dora_api/features/waste/waste.py) (397 LOC) +
[`StockItemWasteEvent`](../../dora_api/domain/entities/stock_item_waste_event.py)
with `SET NULL` on stock-item delete (so waste history survives an item
purge — a nice piece of intent).

Reach into the rest of the app is real, not cosmetic:
- Dashboard's "Use soon" card peeks at the same rescue feed.
- [`StockItemDetailPage.vue`](../../web_app/src/pages/StockItemDetailPage.vue)
  History tab merges waste events into the unified lifecycle timeline
  (C-1b.5 / INV-7).
- Suggestions has a `frequent_waster` kind that deep-links here.
- Dora tools `expiry_rescue` and `waste_insights` read this data.

---

## Charter and feedback standing — the awkward gap

This is where the page gets interesting, because **the two sources of truth
disagree on whether it deserves to exist**:

**The charter says yes.** `DASHY_DORA_CHAMPION_PLAN.md` makes waste one of
four Dora Score pillars ("low waste, on-budget, fresh, few run-outs", §444),
calls out waste as a required assistant input signal (§334), and uses
"waste warning ('you waste this ~60% of the time — still stocked')" as an
example of charter-aligned verdict UX (§346). The closed-loop reasoning
(P5 / P6 in INV-7) hinges on purchase→use→**waste**→restock being visible.
You can't deliver the Dora Score without a waste signal.

**The user has never asked for it.** The current
`Feedback _ Fixes - as of [06-Jun-2026].md` has zero mentions of waste.
`FEEDBACK_TRIAGE_AND_PLAN.md` line 19 explicitly listed waste in *"areas
you're deferring (do not design, but track ripple into them)"*. The active
[`docs/03_prompts/00_INDEX.md`](../03_prompts/00_INDEX.md) still keeps
waste in the deferred queue. It was built anyway because P2-06 in the
legacy plan was ready to go.

So: charter pillar + user-silent + built ahead of schedule. That's the
shape of every "feature you might want to question."

---

## How it sits next to its peers

| Page | LOC | Components | Last touched | In nav | Vibe |
|------|-----|-----------|--------------|--------|------|
| Dashboard | 2935 | 5 | today (9 commits / 24h) | ✅ Home | Actively loved |
| ShoppingListDetail | 2572 | 8 | 2026-06-22 | ✅ | Actively loved |
| RecipeDetail | 2117 | 10 | 2026-06-16 | (sub) | Mature, polished |
| StockOverview | 1020 | 11 | 2026-06-19 | ✅ | Mature, stable |
| Reports | 693 | 0 (inline ECharts) | 2026-06-18 | ✅ | Polished |
| **Waste** | **525** | **1 (BaseDialog)** | **2026-06-18** | **✅** | **Lean / minimal** |
| Alerts | 434 | 4 | 2026-06-15 | ✅ | "B5 stopgap" |

Waste is the **second-thinnest top-nav page**, just above the explicitly-
labelled-stopgap Alerts page. Architecturally it's nearly inline (one
imported component), no feature gate, no recent commits, no test file. It
isn't broken — it's just not loved the way Dashboard or Shopping is.

---

## The honest tension

The page is doing real work, but the **boundaries between Waste, Alerts,
Reports, and Dashboard are smearing**:

- **Forward-looking rescue** lives on the Dashboard ("Use soon" card),
  the Waste page (the same list, fuller), and the Alerts page (expiry IS
  an alert). Three surfaces, one job.
- **Backward-looking insights** are conspicuously **absent from Reports**
  ([`ReportsPage.vue`](../../web_app/src/pages/ReportsPage.vue) has no waste
  card today) and only appear at the bottom of the Waste page when data
  exists. Reports has six cards (stock value, spend by store, top items,
  run-outs, savings, price trends); a "Waste & money lost" card would
  fit naturally and is arguably the real `COVERAGE_GAPS` here.
- **Logging** lives in two places (the page dialog and the stock-item
  detail timeline). That's fine.

The single line that crystallises it for me: the page is **named for the
problem, not for the user job**. The first heading on the screen is "Use
soon," but the nav label and tab title say "Waste." A user opens the page
to *avoid* waste, not to dwell on it; the framing accidentally violates
the no-shame UX rule the original P2-06 spec called out.

---

## Should it be removed?

Honest answer: **no, but reshape it.** Three reasons removal is the wrong
call:

1. **The Dora Score depends on it.** Killing the surface means deleting
   the only place users currently log discards, which decays the signal
   the score is supposed to read.
2. **The integrations are load-bearing.** Suggestions (`frequent_waster`),
   Dora tools (`waste_insights`), and the History tab all read the
   `StockItemWasteEvent` stream. The page is what feeds them.
3. **Pre-release latitude.** You *can* break things pre-release — but
   that's permission to clean up, not a reason to demolish a working
   surface that the charter calls a pillar.

What I'd actually do, in priority order:

**1. Rename the surface (cheap, high signal).**
Call it "Use soon" or "Rescue" in nav + tab title. Keep the route as
`/waste` if it's easier, or alias it. This is a 10-minute change that
aligns the label with both the user job and the charter's anti-shame
language. The word "waste" stays on the *log dialog* and the insights
strip, where it's the accurate term.

**2. Push the insights strip into Reports as its own card.**
The "What you've been wasting" panel is doing reporting work — it's a
90-day aggregation by item, by reason, with dollars. That's a Reports
card, not a sub-section of an action page. Adding it closes a real gap
(the `ORPHANED_FIELDS_AUDIT.md` already notes `waste.py` consumes
`picked_offer_price` alongside `budget.py` and `reports.py` — they're
peers). After the move, the Waste/Rescue page can drop the conditional
strip and become a focused single-job page.

**3. Decide explicitly whether Dashboard "Use soon" and the full page
are layered or duplicated.**
If they're layered (Dashboard = top 4 peek, page = full list +
recipes), that's fine — say so in the dashboard rebuild doc. If
they're duplicated, fold the Dashboard card into a deep-link teaser
and let the page own the list. Right now both render the same items
with the same actions; users won't know which to trust.

**4. Don't invest further until the Dora Score lands.**
The page is a charter pillar but a P3-era charter pillar (champion
phase). Until the Score is being built, more polish on the standalone
page is premature — the *real* Waste surface will be the Score
breakdown card with "waste down $4 this month" microcopy (charter
§447). Hold the line at "lean + accurate" for now.

What I would **not** do: add bulk logging, photo capture, freezer-zone
modelling, or shame-coded UI. Each of those was in the original P2-06
spec and each is exactly the kind of accretion `R-007` (scope
discipline) is meant to prevent.

---

## Critical files (read these before deciding)

- [`web_app/src/pages/WastePage.vue`](../../web_app/src/pages/WastePage.vue)
  — the surface in question
- [`web_app/src/pages/ReportsPage.vue`](../../web_app/src/pages/ReportsPage.vue)
  — where the insights strip would migrate to
- [`web_app/src/pages/DashboardPage.vue`](../../web_app/src/pages/DashboardPage.vue)
  lines 1080–1090, 1786–1790 — the "Use soon" card that overlaps
- [`web_app/src/layouts/MainLayout.vue`](../../web_app/src/layouts/MainLayout.vue)
  line 229 — the nav label to rename
- [`dora_api/features/waste/waste.py`](../../dora_api/features/waste/waste.py)
  — backend; **unchanged** by any of the above moves (no migration
  needed)
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447
- `docs/05_investigations/HISTORY_TAB_ASSESSMENT.md` (INV-7) lines 55–68
  — the closed-loop reasoning that keeps waste as a model concept

---

## Feedback coverage (per CLAUDE.md)

The current feedback round has **no waste bullets**. Recording this
explicitly so a future reader doesn't assume the table is missing:

| Feedback bullet | Section | Notes |
|-----------------|---------|-------|
| *(none)* | — | Waste is user-silent in `Feedback _ Fixes - as of [06-Jun-2026].md`; the page exists because of the charter, not the user. If this assessment ever becomes a prompt, the coverage check should be against the charter (DDCP §§334, 346, 444–447) and `COVERAGE_GAPS.md` line 55, not feedback. |

---

## Verification (if you act on this)

This is an *assessment*, not a code change. Nothing to test until a
follow-up prompt acts on one of the options. If/when one is picked:

- Rename: visual check on nav + tab title in browser (desktop +
  mobile), confirm router still resolves `/waste`, confirm Dora tool
  responses still reference the page by its new label.
- Reports migration: load Reports with and without waste data, confirm
  empty state + populated state both render; confirm the Waste page no
  longer shows the bottom strip; confirm `frequent_waster` suggestion
  still deep-links to a sensible target.
- Dashboard vs page reconciliation: load Dashboard + Waste page with
  identical at-risk data, confirm no item count drift and consistent
  action behaviour.
