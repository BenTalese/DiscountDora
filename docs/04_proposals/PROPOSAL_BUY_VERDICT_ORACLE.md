# Proposal — "Should I Buy This?" Buy-verdict Oracle (P8-05)

**Status:** Draft → Implementing · **Date:** 2026-07-02
**Scope:** the champion-plan P8-05 in-aisle decision engine.

> **Charter tie-break for every decision below:** Effortless (P1) +
> Anti-creep (P10). The oracle must reduce a shopping-mode decision to
> one glance + one tap; it must not become a fifth dashboard.

---

## 1. The problem

The user is standing in an aisle (or drafting a list at home) with an
item in hand. Every competing app tells them **which store has the
deal**. Dora's differentiator is telling them whether **they, personally,
should buy it right now** — using only their own data (Charter P4,
P9): what they've paid, how fast they run out, and how often they end up
throwing it away.

The champion plan says P8-05 depends on personal price intelligence
(P6-03), cadence (P6-04), waste signal (P6-06), and the stock-level
band (P6-04 output). All four are present in Dora today.

## 2. The corrected model

**Wrong shape** (looked reasonable at first): a global assistant tool
that answers "Should I buy X?" as a chat response. That collapses under
Charter P6 (one-action) — the user has to type / ask, then click a
follow-up. Slow, indirect, hidden.

**Right shape:** a verdict is a *property of a stock item* right now.
Compute it server-side (R-003), surface it wherever the user is making
a buying decision — Stock Overview (list-building) and Shopping List
(in-shop). Same endpoint, two consumers.

### 2.1 Verdict shape

```
GET /api/stock-items/<id>/buy-verdict
→ {
    "verdict":   "buy" | "wait" | "skip" | "unsure",
    "confidence": "high" | "medium" | "low",
    "reasons": [
      { "axis": "price" | "need" | "waste",
        "signal": "cheapest_3mo" | "usual_price" | "above_usual" |
                  "out_of_stock" | "low_stock" | "well_stocked" |
                  "wastes_often" | "wastes_sometimes" | "no_waste_history" |
                  "thin_data",
        "label":  "Cheapest you've paid in 3 months",
        "detail": "$3.20 last shop · usually $3.80" }
    ],
    "one_tap_action": {
      "kind":  "add_to_list" | "skip" | "mark_stocked" | "remove_from_list",
      "label": "Add to primary list"
    },
    "data_used": {
      "price_samples": 7,
      "days_since_last_purchase": 6,
      "average_days_between_purchase": 14,
      "waste_events_last_12mo": 2,
      "stock_level_band": "out" | "low" | "stocked"
    }
  }
```

The response is small (~1 KB) and the SPA caches it per stock item until
a mutation invalidates it. `data_used` is what powers the "why?"
tooltip — Charter P7 (preview + explain) requires the user can always
see the basis.

### 2.2 The three axes

| Axis | Input | Signals |
|---|---|---|
| **Price** | archived-list line prices via `line_paid_unit_price` ladder | `cheapest_3mo` / `usual_price` / `above_usual` / `thin_data` |
| **Need**  | current `StockLevel.sequence` + cadence (avg-days-between-purchases − days-since-last) | `out_of_stock` / `low_stock` / `well_stocked` (+ optional "runs out in ~N days") |
| **Waste** | `StockItemWasteEvent` occurrences in the last 12 months over purchase count | `wastes_often` (≥40%) / `wastes_sometimes` (10–39%) / `no_waste_history` |

### 2.3 Composition rules

The overall verdict trumps by *need*, then reads *price*, then *warns
on waste*:

1. **Need = out_of_stock** → `buy`. Price and waste become secondary
   reasons; the shelf is empty and you cook from it, so the decision
   is settled. Confidence: `high` if we know your cadence, else
   `medium`.
2. **Need = low_stock**:
   - If price is `cheapest_3mo` → `buy` (high confidence — cheap +
     needed).
   - If price is `above_usual` → `wait` (medium — price will likely
     come back).
   - Else → `buy` (medium — you need it, price is fine).
3. **Need = well_stocked**:
   - If waste is `wastes_often` → `skip` (high — you've historically
     thrown this away; adding more is wasteful).
   - If price is `cheapest_3mo` → `buy` (medium — bargain, worth
     stocking).
   - If price is `above_usual` → `wait` (medium).
   - Else → `unsure` (low — no strong signal in any direction; the
     user's call).
4. **Any axis is `thin_data`** — that axis contributes no reason and
   drops overall confidence one step. If **all three** axes are thin →
   `unsure` + `low`, with a single reason "Not enough history yet".
   Never make up a verdict.

Thin-data thresholds (tune in one place — the composer):

- **Price:** < 3 price samples in the last 12 months.
- **Need cadence:** < 2 unique purchase dates *or* one purchase.
- **Waste rate:** requires ≥ 3 purchases to have a denominator; a
  never-purchased-never-wasted item is `no_waste_history`, not
  `wastes_often` at 0/0.

### 2.4 One-tap action

Server picks the sensible next move based on the verdict + current
context:

- `buy` → `add_to_list` (the primary list, or the currently-open one).
- `skip` on a Stock Overview item that's currently on a list → the
  action returns `remove_from_list` instead.
- `mark_stocked` when verdict is `skip` because *well-stocked +
  wasteful* — nudge the user to close the loop on inventory rather
  than shop.
- `unsure` → no action, banner reads "No strong signal" and the
  regular controls stay accessible.

The mutation itself uses the *existing* endpoints (cart button →
shopping-list POST). The oracle emits the intent; it doesn't grow a
new mutation seam.

## 3. Charter alignment

- **P1 Effortless** — glance-and-tap on the surfaces where the
  decision is being made.
- **P3 Honest** — thin data collapses to `unsure`, not to a made-up
  answer. Confidence label is part of the payload.
- **P4 Personal** — the oracle uses *only* the user's own data. No
  external calls; no crowd baselines (see §5).
- **P6 One-action** — the verdict comes with the mutation button
  already wired.
- **P7 Preview / explain** — the tooltip surfaces `data_used`
  verbatim so the user sees exactly what Dora reasoned from.
- **P9 No-scrape** — nothing leaves the install.
- **P10 Anti-creep** — one endpoint, one composer, one badge
  component, two consumers (Overview + Shopping List). No new
  dashboard, no new page.
- **P12 No-invent** — thin data ⇒ `unsure`; never fabricate a price
  band from one sample.

## 4. Surfaces

### 4.1 Stock Overview row (list-building context)

An inline `BuyVerdictBadge` renders on each row when the verdict
confidence is `high` or `medium` (silent on `low` to avoid dashboarding
every row). Colour tokens map to `--positive` / `--warning` /
`--negative` / `--info`. Popover on tap/hover surfaces the reasons +
the one-tap action.

### 4.2 Shopping List Detail line (in-shop context)

Same badge on each shopping-list line. In shop mode the badge is even
more valuable — "wait, actually don't buy this" is the killer feature.
Popover action is context-aware: `remove_from_list` on lines already
present, `mark_stocked` when the pantry says the item is well-stocked
(user is second-guessing what they already have).

### 4.3 Item detail page — later

The full `BuyVerdictCard` (three-axis breakdown) lands on the stock-
item detail page in a later slice, once the badge + endpoint are
proven in production. Not scoped in this proposal.

## 5. What this slice does NOT do

- **Crowd-price baselines (P8-04).** User's own feasibility concern is
  legitimate — pooling anonymised prices across households has real
  privacy, incentive, and freshness problems that Dora is not built to
  own. Flagged as a governance question (FU-436 below); the oracle is
  designed to work without it, and can trivially blend a crowd baseline
  in later if the decision goes the other way.
- **Loyalty / email price ingestion (P8-03).** Not shipped either;
  price data comes only from completed shopping lists (P6-01 →
  archived lines). Enough to run the oracle; deeper price coverage
  would just narrow the `thin_data` window.
- **Wait-or-Buy oracle (P8-06).** The `wait` verdict here is coarse
  ("price is above usual — try later"). P8-06 will produce a
  time-boxed answer ("your usual low lands ~end of fortnight"). Same
  endpoint gets a `wait_until` field in a future slice.
- **In-place price entry.** Users still record prices via
  shop-mode / finish-list. The oracle reads; it doesn't ingest.

## 6. Feature flag & rollout

Add `AppSetting.buy_verdict_enabled` (default **true** — pure-personal,
no external surface to gate). Surfaced via `/health` as
`features.buy_verdict`; the SPA uses `useBuyVerdictEnabled()` to gate
the two consumers. Admin toggle lands in Settings → System.

Distribution-posture check (§7.5): pure-personal, DB-only, no config
required, works identically self-hosted / managed / SaaS. Portable
migration (R-005).

## 7. Cross-check (Charter + feedback)

P8-05 has no per-surface feedback bullets — it's a champion feature
predating the feedback pass. The Charter mapping in §3 stands in as the
coverage table.

Adjacent feedback that this touches (mapped for honesty):
- `§STOCK OVERVIEW` "cart-icon discussion" — the badge's one-tap
  action reuses the existing cart button; no new mutation UI.
- `§SHOPPING LIST DETAILS VIEW` (general "why is this on my list?" thread) — a skip verdict with a reason string is the answer.

Out of scope (with reason):
- Global "best deals" board — that's P8-06 / P8-07 territory and
  would need crowd data or scraped feeds Dora doesn't consume.
- Nutrition verdict axis — nutrition is a separate opt-in surface
  (C-cross); folding it into a buy verdict conflates two questions
  ("is this cheap?" vs "is this healthy?").

## 8. From the original spec

`docs/00_original_spec/` predates the champion-plan Part 8 by design;
it has no direct precursor to the buy oracle. The closest hint is the
old "smart shopping" language on the Shopping Lists board, which
described a manual sort by store — nothing worth extracting here.

## 9. Open follow-ups

- **FU-436** — governance decision on P8-04 crowd prices (KEEP /
  SHRINK / CUT), triggered by the user's feasibility concern raised
  during P8-05 kickoff. Track like INV-9 (palette): produce a short
  assessment, land the call in the reconciled plan.
- **FU-437** — extend the oracle to the item-detail page with the
  full `BuyVerdictCard` after the badge lands.
- **FU-438** — P8-06 Wait-or-Buy — populate the `wait_until` field
  on the same endpoint once cadence-based price cycle detection
  exists.
