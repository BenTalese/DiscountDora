# Proposal — Waste Minimisation (C-waste)

**Status:** Decisions resolved 2026-06-24 (co-designed in-session) · **Date:** 2026-06-24 · Changes NO code.
**Source assessment:** an in-session scratch read on 2026-06-24 (deleted 2026-07-04 after FU-426 confirmed every keep-item was absorbed here or explicitly dropped with rationale — this proposal is the authoritative record).
**Headline:** the `/waste` page is dissolved into smaller, lighter surfaces. The data signal (the
`StockItemWasteEvent` stream) is preserved end-to-end so the future Dora Score can still read it;
only the page surface and the heavy capture flow are removed.

> **Charter tie-break:** Anti-creep (P10) + Effortless (P1). Waste is a charter pillar of the
> future Dora Score (`DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447) but is *user-silent* in
> the current feedback round. The decision is to **keep the signal, shed the surface** until
> the Score actually lands — at which point the Score is the real waste UI, not a dedicated
> page. The minimal capture flow that remains is shame-free (no dollar question, no notes,
> no shame copy) by design.

---

## 1. Scope

Six surfaces touched:

1. **`/waste` page** — deleted (route, page, nav entry).
2. **StockOverview** — `Stalest first` sort replaced by `Expires soonest`.
3. **StockItemRow expiry dropdown** — gains `Mark as wasted` (clears expiry + logs the event).
4. **Cookbook (RecipesOverview)** — new filter "Uses expiring ingredients" with a 14-day horizon
   and a `Uses N expiring` badge surfaced *only when the filter is active*.
5. **Dashboard** — `Use soon` card removed; the `Needs your attention` card already covers
   near-expiry items.
6. **Reports** — untouched. No "Waste & money lost" card is added (deliberately —
   see §7).

Backend: `StockItemWasteEvent` is slimmed (no value, no note, no quantity). `waste.py`
endpoints survive in a reduced form for the cookbook filter and the simplified
`waste_insights` Dora tool. The `expiry_rescue` Dora tool is unchanged.

---

## 2. Decisions (all locked in-session 2026-06-24)

| # | Decision |
|---|---|
| D1 | Capture flow keeps a **modal with reason only**. No estimated value, no note, no "mark out of stock" toggle. |
| D2 | Modal body becomes a **tile grid of reason chips** (icon + label) where tapping a tile *is* the submit. No separate "Log" button. Cancel = top-right close-X. |
| D3 | After submit, show a 5-second **Undo toast** (Quasar `$q.notify` with an Undo action that deletes the event). |
| D4 | Reasons retained: Expired, Spoiled, Didn't like, Bought too much, Other. (Vocabulary unchanged from today.) |
| D5 | StockOverview: **axe** `updated_oldest` ("Stalest first") sort; add **`expiry_asc`** ("Expires soonest"). `updated_recent` ("Recently updated") already covers the "what have I been touching" question, so removing the stalest sort loses nothing. |
| D6 | Cookbook filter horizon: **fixed 14 days**, not user-configurable. Recipes ordered by **count of expiring ingredients used (desc)**. Badge `Uses N expiring` shown on cards **only while the filter is active**. |
| D7 | "Mark used" and "Mark frozen" are **not** added as row actions. Used is implicit (stock-level decrement on the row); freezer is a *physical* move, not an app state. |
| D8 | `frequent_waster` suggestion deep-link target: **StockItemDetail** for that item (History tab surfaces waste events already, per C-1b.5 / INV-7). |
| D9 | Dashboard `Use soon` card cut; `Needs your attention` is the single near-expiry surface. |
| D10 | `/waste` route deleted with **no redirect** (pre-release, no compat shims per user's working-style memory). |
| D11 | **No nav slot replacement** — the gap stays empty. |
| D12 | **No Reports waste card.** The cheap "most/recently wasted" view lives only inside the simplified `waste_insights` Dora tool. |
| D13 | `StockItemWasteEvent` schema is **stripped** of `estimated_value`, `note`, and `quantity`. Pre-release migration is a clean `DROP COLUMN` (no idempotent guards per the migrations memory). |
| D14 | Dora Score reassessment (waste is a pillar per DDCP §§444+ but is being de-emphasised as a UI feature) is logged as a **deferred follow-up**, not in scope here. See `DORA_FOLLOWUPS.md` FU-302. |

---

## 3. Current state (verified 2026-06-24)

- **`WastePage.vue`** (525 LOC, 1 component) — three jobs stitched together: 3/7/14/30-day
  rescue list with per-row Used/Freeze/Wasted, a recipe-match panel, a 90-day insights strip
  shown conditionally. The page is the second-thinnest top-nav page and has no test file.
- **Backend** — `dora_api/features/waste/waste.py` (397 LOC) exposes:
  - the rescue feed (used by the page + Dashboard + Dora `expiry_rescue` tool),
  - the recipe-match endpoint (used by the page only),
  - the insights aggregation (used by the page + Dora `waste_insights` tool),
  - the event-logging endpoint (used by the page + StockItemDetail).
- **`StockItemWasteEvent` entity** (`stock_item_waste_event.py`) — carries
  `{stock_item_id, stock_item_name, reason, quantity, estimated_value, note, occurred_at}`,
  FK `SET NULL` on stock-item delete so history survives a purge.
- **Reach into the rest of the app:**
  - Dashboard `Use soon` card (cut here).
  - StockItemDetail History tab merges waste events into the unified lifecycle timeline
    (C-1b.5 / INV-7 — kept).
  - Suggestions `frequent_waster` deep-links here today (re-pointed to StockItemDetail).
  - Dora tools `expiry_rescue` (kept) and `waste_insights` (simplified).
- **StockOverview sort `updated_oldest`** is mis-implemented: labelled "Stalest first" but
  actually sorts by `stock_level_last_updated` (least-recently-touched stock level), which
  has nothing to do with stale food. Bug confirmed at
  [`useStockFilters.ts:241`](../../web_app/src/composables/useStockFilters.ts).

---

## 4. Surface-by-surface design

### 4.1 Delete the page

Files to remove or update:

- `web_app/src/pages/WastePage.vue` — delete.
- `web_app/src/router/routes.ts` (or wherever `/waste` is declared) — remove the route.
- `web_app/src/layouts/MainLayout.vue` (around line 229) — remove the nav entry. The slot
  stays empty (D11).
- `web_app/src/helpers/dashboardMessages.ts:86` — remove the "Use soon card" tip.
- Any deep-links from suggestions or settings copy that hard-code `/waste` — re-point per
  §4.6.

### 4.2 StockOverview — fix the sort that was already trying to do this job

In [`useStockFilters.ts`](../../web_app/src/composables/useStockFilters.ts):

- **Remove** `'updated_oldest'` from the sort union, its option entry ("Stalest first"), and
  its `case` in the sort switch.
- **Add** `'expiry_asc'` ("Expires soonest"):
  - sort by `expiry_date asc nulls last`,
  - secondary by `stock_level_last_updated asc` (so two items with no expiry fall back to
    "least recently touched"),
  - tertiary by `name`.

The existing "Needs attention" filter chip already includes near-expiry items, so users who
want the rescue list have two complementary controls — a sort *and* a filter — without any
new UI.

### 4.3 Mark-as-wasted row action

In [`StockItemRow.vue`](../../web_app/src/components/stock/StockItemRow.vue), the row's
existing expiry-clear dropdown gains a `Mark as wasted` option:

- Side-effect: `DELETE expiry_date` on the item (same as today's "Clear expiry") **AND**
  `POST` a `StockItemWasteEvent` with the chosen reason.
- Triggers the modal described in §5.

This single touchpoint replaces the entire `/waste` capture flow for the common case.

### 4.4 Cookbook filter

In [`RecipesOverview.vue`](../../web_app/src/pages/RecipesOverview.vue):

- New filter row control: a boolean toggle **`Uses expiring ingredients (≤14d)`**.
- Predicate: recipe has ≥1 ingredient that is in stock and either expired or expiring within
  14 days. Re-uses the same expiring-items signal the rescue feed reads (push the predicate
  into the recipe-list endpoint or compute via the existing recipe-match logic in
  `waste.py`).
- **Sort override when active:** recipes ordered by `count(expiring ingredients used) desc`,
  then by the user's current secondary sort (falling back to name).
- **Card badge:** while (and only while) the filter is active, each card shows a small chip
  `Uses N expiring`. When the filter is off, no badge — no noise.

### 4.5 Dashboard

In [`DashboardPage.vue`](../../web_app/src/pages/DashboardPage.vue):

- Remove the `use_soon` card definition (around line 1157), the card markup (around lines
  490+, 498), the `'use_soon'` entry from the card-id union (around line 1108), and any
  related CSS.
- `Needs your attention` (D6) is unchanged — confirm in browser that it already includes
  near-expiry items; if it doesn't today, extend it to (it's the agreed single surface).
  This is the only surface change to that card, if any.

### 4.6 Reports & deep-links

- **Reports** is not touched. No waste card, no entry.
- **`frequent_waster` suggestion** — re-point its `link` target from `/waste` to
  `/stock-items/:id` (StockItemDetail; the History tab already shows the waste events).
- **`expiry_rescue` Dora tool** — keep as-is; backend rescue feed survives.
- **`waste_insights` Dora tool** — simplify to two answer shapes only:
  - "items wasted most often in the last N days" (count by `stock_item_name`),
  - "items most recently wasted" (last K events).

  Reason/value/note breakdowns are dropped from the tool output — they're unavailable
  going forward, and the historical fields are dropped per D13.

---

## 5. The `Mark as wasted` modal

Reframed because dropping three fields leaves the old form-row layout looking empty.

```
┌─────────────────────────────────────┐
│  Cherry tomatoes                  × │   ← item name + close
│  ~250g · Fridge                     │   ← subline (optional, from row data)
├─────────────────────────────────────┤
│  Why did this go to waste?          │
│                                     │
│  ┌──────────────┐ ┌──────────────┐  │
│  │ [clock]      │ │ [bug]        │  │
│  │ Expired      │ │ Spoiled      │  │
│  └──────────────┘ └──────────────┘  │
│  ┌──────────────┐ ┌──────────────┐  │
│  │ [meh]        │ │ [cart]       │  │
│  │ Didn't like  │ │ Bought too   │  │
│  │              │ │ much         │  │
│  └──────────────┘ └──────────────┘  │
│  ┌─────────────────────────────────┐│
│  │ [dots]  Other                   ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

Behaviour:

- **Tile tap = submit.** No separate "Log waste" button.
- Cancel = top-right close-X (provided by `BaseDialog`'s `closable`). Tap outside the modal
  also dismisses.
- Tile target ~64px tall, full-width on mobile (single column there), 2-up on desktop.
  "Other" spans the full width as a quieter row beneath the four primary reasons.
- Icons from `src/style/icons.ts` (`ICONS`) — no emoji literals (per code-style memory).
- Submit posts the event and clears the row's expiry in the same tick (single round-trip
  if the backend exposes a combined endpoint; otherwise two requests, expiry-clear first
  so the row UI updates before the toast fires).
- Toast: `$q.notify({ message: 'Logged as wasted', actions: [{ label: 'Undo', handler: ... }], timeout: 5000 })`. Undo calls a delete-event endpoint (new — see §6).
- **No Dora mascot in the modal.** Charter is anti-shame; a sad/worried face is the wrong
  note. The empathy is in what's *missing* (no dollar field, no "tell us why in detail"
  textarea), not in a face.

---

## 6. Backend changes

### 6.1 Entity slim-down (D13)

`dora_api/domain/entities/stock_item_waste_event.py` — drop three fields:

| Field | Fate |
|---|---|
| `stock_item_id` | keep (nullable FK, SET NULL on delete) |
| `stock_item_name` | keep (denormalised survival) |
| `reason` | keep |
| `occurred_at` | keep |
| ~~`quantity`~~ | drop |
| ~~`estimated_value`~~ | drop |
| ~~`note`~~ | drop |

Migration: a single Alembic revision that drops the three columns. No data preservation (the
fields were optional and we're pre-release). The constants and `WASTE_REASON_VALUES` set are
unchanged.

### 6.2 Endpoints

In `dora_api/features/waste/waste.py`:

| Endpoint | Change |
|---|---|
| Rescue feed (`GET expiring items`) | Keep — consumed by `expiry_rescue` Dora tool. |
| Insights aggregation | Simplify the response to `{most_wasted: [...], most_recent: [...]}`. Drop reason breakdowns and value sums (they're unavailable post-D13). |
| Event logging (`POST`) | Drop `quantity` / `estimated_value` / `note` from the request schema (Pydantic `extra=forbid`, per R-rule). Keep `reason` + `stock_item_id`. |
| Recipe-match | Either delete and fold the predicate into the cookbook recipe-list endpoint, **or** keep and have the cookbook filter call it. Recommendation: fold it into the recipe-list endpoint as a query parameter (`expiring_within_days=14`) so the cookbook stays in one round-trip. |
| **New:** event delete (`DELETE` by id) | Add — backs the Undo toast. Idempotent; returns 204 even if the event is already gone. |

### 6.3 Suggestion link

`features/suggestions/suggestions.py` — change the `frequent_waster` suggestion's `link`
template from `/waste` to `/stock-items/<stock_item_id>`. The stock-item id is already in
scope when this suggestion is generated.

---

## 7. What we are deliberately NOT doing

Captured so future readers don't re-litigate:

- **No money/value capture** on wasted items. The dollar signal stops here.
- **No "Mark frozen" / freezer-zone modelling.** Freezer is physical, not an app state.
- **No note field** on waste events.
- **No "Also mark as Out of Stock" toggle** — the row's stock-level control already covers it.
- **No bulk waste logging.**
- **No photo capture, no shame UI, no streaks/gamification.**
- **No Reports "Waste & money lost" card.** The 90-day-totals strip from the old page does
  not survive in any surface; the simplified `waste_insights` tool is sufficient.
- **No dashboard replacement card** for `Use soon`.
- **No `/waste` redirect.** Pre-release; bookmarks break.

Each of these was either in the old P2-06 spec or floated in the 2026-06-24 assessment; each
is scope discipline (R-007).

---

## 8. Engineering-standards check

| Rule | Touchpoint |
|---|---|
| R-002 (token-only colours) | Modal styling reuses `BaseDialog` + token classes; tile chips use `--c-surface-2` / `--c-line` etc. |
| R-003 (state ownership) | The expiring-soon signal stays server-derived (rescue feed). Cookbook filter pushes its predicate to the server — no client-side cross-entity computation. |
| R-007 (scope discipline) | §7 is this rule applied directly. |
| R-018 (no compat shims pre-release) | D10 (no `/waste` redirect), D13 (clean column drop). |

No new ADR-worthy decision emerges from this work; it's an application of existing rules.

---

## 9. Feedback coverage

Per CLAUDE.md, every targeted proposal carries a coverage table. This one is charter-driven,
not feedback-driven:

| Bullet | Section | Notes |
|---|---|---|
| *(none)* | — | The current feedback round (`Feedback _ Fixes - as of [06-Jun-2026].md`) contains zero waste bullets. This proposal is charter-/scope-discipline driven: `DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447 (waste as a Dora Score pillar) + `COVERAGE_GAPS.md` line 205 ("Reports / Waste — feedback empty; deferred") — the latter flips to resolved-by-this-proposal. |

---

## 10. Cross-cutting follow-up — Dora Score reassessment

The charter calls waste a pillar of the Dora Score:
- DDCP §444 — "low waste, on-budget, fresh, few run-outs"
- DDCP §334 — waste as a required assistant input signal
- DDCP §346 — "waste warning ('you waste this ~60% of the time — still stocked')"

This proposal preserves the *signal* (events still logged, stored, queryable) so the Score
can read it later. But the de-emphasis of waste as a UI feature is a quiet vote that the
Score model itself may want re-weighting — perhaps waste shrinks to a smaller pillar, or
combines with another (e.g. "fresh + low-waste" as one freshness pillar).

This is a **charter-level decision**, not a UI cleanup, and is explicitly out of scope here.
Logged as `DORA_FOLLOWUPS.md` **FU-302**, recommended-resolution = before Phase 3 (the
champion phase, where the Score is actually designed).

---

## 11. Critical files

Read before implementing:

- [`web_app/src/pages/WastePage.vue`](../../web_app/src/pages/WastePage.vue) — the surface being deleted
- [`web_app/src/composables/useStockFilters.ts`](../../web_app/src/composables/useStockFilters.ts) — sort change
- [`web_app/src/components/stock/StockItemRow.vue`](../../web_app/src/components/stock/StockItemRow.vue) — new "Mark as wasted" entry under the expiry dropdown
- [`web_app/src/pages/RecipesOverview.vue`](../../web_app/src/pages/RecipesOverview.vue) — new filter + conditional badge
- [`web_app/src/pages/DashboardPage.vue`](../../web_app/src/pages/DashboardPage.vue) — remove Use-soon card (lines 490+, 1108, 1157)
- [`web_app/src/helpers/dashboardMessages.ts`](../../web_app/src/helpers/dashboardMessages.ts) line 86 — drop the tip
- [`web_app/src/layouts/MainLayout.vue`](../../web_app/src/layouts/MainLayout.vue) line ~229 — remove nav entry
- [`dora_api/features/waste/waste.py`](../../dora_api/features/waste/waste.py) — endpoints
- [`dora_api/domain/entities/stock_item_waste_event.py`](../../dora_api/domain/entities/stock_item_waste_event.py) — schema slim
- [`dora_api/features/suggestions/suggestions.py`](../../dora_api/features/suggestions/suggestions.py) — `frequent_waster` link
- `dora_api/features/dora_assistant/tools/` — `expiry_rescue` (keep) and `waste_insights` (simplify)
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447 — for the FU-302 framing
- `docs/02_feedback/COVERAGE_GAPS.md` line 205 — flip on close

---

## 12. Verification (when the impl plan runs)

- StockOverview: `Expires soonest` is the new default-discoverable sort; `Stalest first` is
  gone; sorting an inventory of mixed-expiry items places nearest-expiry first, items without
  expiry last, no client console errors. Verify in browser desktop + mobile.
- StockItemRow: opening the expiry dropdown shows `Mark as wasted`; tapping it opens the
  tile-grid modal; tapping a tile clears the expiry on the row, posts an event, fires the
  Undo toast; Undo deletes the event and (decision: does Undo also restore the expiry? See
  open §13.A).
- Cookbook: enabling the filter narrows the list to recipes using ≥1 expiring-within-14-days
  ingredient; cards show the `Uses N expiring` badge while the filter is on; disabling the
  filter removes the badge and restores the user's sort.
- Dashboard: `Use soon` card is gone (incl. from the Cards menu); `Needs your attention`
  still surfaces near-expiry items.
- Reports: visually unchanged.
- `/waste`: navigating to it 404s (or the SPA's not-found page); no nav entry; no settings or
  suggestion link still points here.
- Dora tools: `expiry_rescue` returns expiring items; `waste_insights` returns the simplified
  `{most_wasted, most_recent}` shape.
- Backend: migration up/down clean on SQLite + Postgres; `tests/e2e/dora_api/test_waste*.py`
  updated to the new schema.

---

## 13. Open items not yet decided

Small UX questions left for the impl run (don't block this proposal):

- **A. Undo restores expiry?** When the user hits Undo on the wasted-toast, do we also
  restore the original expiry date that was cleared? Logically yes — Undo should fully revert
  the side-effect. Default to **yes** unless the impl reveals friction.
- **B. Cookbook filter naming.** "Uses expiring ingredients" vs "Cook expiring first" vs
  "Use what's expiring". I'd go with "Uses expiring ingredients" — most literal, fits the
  existing filter-row vocabulary. Pick at impl-time.
- **C. Expires-soonest sort default.** Should it become the *default* sort when "Needs
  attention" filter is on? Tempting but adds magic; default to **no** — user's last sort
  choice persists.

These are notes, not blockers.
