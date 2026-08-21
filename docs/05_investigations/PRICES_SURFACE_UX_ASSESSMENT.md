# PRICES_SURFACE_UX_ASSESSMENT — "Your prices" + price history

**Date:** 2026-08-21 · **Type:** Read-only investigation, no code changes.
**Owner FU:** FU-703 (structural decision) · defect FUs: FU-704 … FU-708.

**Question the owner asked:** *"What do you think of the UX of the 'my prices'
and price-history areas? Open question — deep analysis."*

**Owner's framing (2026-08-21), captured because it is the root cause:**

> Products started as a first-class entity in the system, but then I pulled that
> all out into a niche area (only if you push data yourself into Dora will it
> appear at all) and upgraded the stock-item entity to house more everyday-user
> functionality such as your own prices. In doing that, it has kind of butchered
> things, tearing in the other direction when it was half built already. For most
> users there is no product-offer data, and so I don't want the UI to be
> confusing to them, but I also want to maximise the functionality and usefulness
> to them.

That framing is the correct diagnosis, and it is visible in the code. This memo
records the evidence, the decisions taken in that session, and what was left open.

---

## 1. Scope read

| File | Role |
|---|---|
| `components/dora/YourPricesWidget.vue` | stock-item baseline + 2 actions |
| `components/dora/PriceEntry.vue` | the one shared entry form (4 call sites) |
| `components/dora/PriceHistoryBottomSheet.vue` | per-stock-item union chart |
| `components/LogPriceSheet.vue` | dashboard quick-action, picker + form |
| `components/stock/StockItemRowPriceButton.vue` | row-level entry |
| `pages/PriceHistoryPage.vue` | product-keyed compare + alerts |
| `components/PriceHistoryChart.vue` | shared SVG chart |
| `pages/StockItemDetailPage.vue` | widget + raw observation list + History tab |
| `features/stock_items/your_prices.py` | baseline math (median / 1.15× / min 3 / 12mo) |
| `domain/entities/price_alert.py` | alert entity |

## 2. The structural finding — two axes that never meet

Your own data is keyed to **stock items** (`StockItemPriceObservation` → median
baseline). Offer data is keyed to **products**. The UI never reconciles them:

| Surface | Keyed to | Compare across items? | Range control? | Front door |
|---|---|---|---|---|
| "Your prices" widget | stock item | no | no | bottom of Overview tab |
| "Full history" sheet | stock item (obs ∪ offers) | no — one item | no | inside the widget |
| `/price-history` page | **product** | yes, up to 5 | yes (30d/90d/1y/all) | **none — orphan route** |
| "History" tab | stock item lifecycle | no | no | tab on the same page |

**The capability sits on the wrong axis.** Comparison, ranging and alerting exist
only for the data the everyday user does not have. Their own data gets a
single-item modal with no range control. The question the product exists to
answer — *"which of my items got more expensive?"* — has no surface at all.
Everything is per-item interrogation; nothing aggregates.

### 2.1 `/price-history` is an orphan route

`MainLayout.vue` never pushes a nav entry for it. Reachable from exactly three
places: a My Products card's overflow menu (`MyProductsPage.vue:1049`), a link in
`SubscriptionsPanel.vue:12`, and the onboarding wizard tour
(`WelcomeWizard.vue:714`, which advertises it as **"Prices"** on installs where it
may be permanently empty). It is also implicitly products-gated — it picks
products only — so on a products-empty install it is a dead page that onboarding
still tours.

### 2.2 The alert feature is structurally impossible for the majority

`PriceAlert` is **product-keyed** and fired by the scrape pipeline. Creation
exists only on the orphan route. So for a no-products install, "notify me when
it's cheap" is not merely undiscoverable — there is no inbound price feed to fire
it. Copy elsewhere still implies the feature exists.

### 2.3 Three things called "history", two sharing an icon

On the stock-item detail page, simultaneously:

- a **"History"** tab (`ICONS.history`) — lifecycle timeline, which itself
  contains `Bought · $X` price events;
- a **"Full history"** button (`ICONS.history`) — the price chart sheet;
- an untitled **raw observation list** below the widget — the same prices again.

Three price trails on one page. The raw list has no heading; it falls out of the
bottom of the widget as an unbordered continuation.

## 3. Archaeology — the original spec confirms the diagnosis

`docs/00_original_spec/Feature Boards/Products.md` carries **every** price Feature
Note (`I can see the price history of a product by merchant`, per-unit price,
%-off, half-price filters, sort by unit price). `Feature Boards/Stock Items.md`
contains **zero** price intent — `grep -i "price\|cost"` returns nothing.

*(Historical, non-authoritative — tagged **superseded** as a decision, but
**keep** as evidence.)* Prices were designed product-first from day one. "Your
prices" on stock items is entirely post-charter. Nothing in the original frame
anticipated the everyday user owning price data, which is exactly why the
reading-side capability (compare, range, alert) all landed on the product axis
and never grew a stock-item twin.

## 4. Everyday-user experience (products off) — what actually remains

- Log a price from 4 entry points (good — one shared `PriceEntry`, R-001 clean).
- See "Usually $X" + "paying more than usual" on one item at a time.
- See a single-item chart with no range control.
- An untitled raw list of their own observations, delete-only.
- No compare. No aggregate. No alerts. No trend.

So capture is strong and **reading is close to absent** — the inverse of what a
dataset-building product wants.

## 5. Interaction / UI defects found

Grouped; each is either folded into FU-703's design work or spun out as its own FU.

### 5.1 Mobile (highest impact — this form is used standing in an aisle)

- `PriceEntry` puts **Price / Size / Unit three-across** in a bare
  `row q-gutter-sm` with no `col-12 col-sm-*` breakpoints (`PriceEntry.vue:36`).
  ~105px per field at 375px.
- `type="number"` with no `inputmode="decimal"` → wrong keypad + spinner arrows
  eating width.
- **Every explanation is a `q-tooltip`** → hover-only, invisible on touch. That
  includes the pack-count help (the most confusing field) and both
  `help_outline` tooltips that *define* "usually" / "above usual". The
  trust-critical copy is desktop-only.
- `PriceHistoryChart` is **`@mousemove` only** (`PriceHistoryChart.vue:2`). On a
  phone it is a decorative picture — no way to read a value off it.
- `/price-history`'s picker rail is `col-12 col-md-3`, so mobile stacks a 360px
  scrolling product list *above* the chart on every visit. The chart's empty
  state reads *"Pick one or more products on the left."*

### 5.2 Signal semantics and tone

`your_prices.py` is clean and correctly server-owned (R-003). Its presentation is
not:

- **Only bad news gets a chip.** Above-usual → warning chip + `mdi-trending-up`.
  Below-usual → a muted `· about average` text fragment. A money-saving app that
  nags on overpay and stays silent on a win has its polarity backwards.
- Warning **colour** on "paying more than usual" reads as *you did something
  wrong*. It is shelf inflation, not user error.
- **Confidence is invisible.** 3 samples and 40 samples render identically;
  `Based on N prices` is a caption under a full-strength conclusion.
- **Four phrasings of one number:** `Usually $X` (widget) · `Your usual: $X`
  (compare card) · `Usually $X/L` (sheet legend) · `above usual` vs
  `paying more than usual`.
- **Silent dimension flip.** Baselines are per-dimension and "the most recent
  dimension wins for the headline". One count-based log (`1 ea`) can move a
  mass-based item's headline baseline with **zero** UI signal — the user's
  "usual" changes for no visible reason.

### 5.3 Data-integrity / trust

- **Delete has no confirm, no undo, and there is no edit path at all**
  (`StockItemDetailPage.vue:1829`). A fat-fingered `1250` for `12.50` poisons the
  median it feeds and can only be fixed by delete + retype.
- **No date field** — you can only ever log "now"; `observed_at` is server-set. A
  receipt from yesterday cannot be entered.
- **Store select vanishes** when no stores exist
  (`v-if="storeOptions.length > 0"`) with no "add a store" affordance. Store is
  the dimension that makes "where is this cheapest" answerable; the capability
  disappears silently.
- The raw observation list is **uncapped and ungrouped** — no store/dimension
  grouping, no "show more". Contrast the History tab, which does honest
  truncation.

### 5.4 Copy / affordance bugs on `/price-history`

- **Mis-parented tooltip.** `All-time low: $X · currently N% above`
  (`PriceHistoryPage.vue:147`) carries a tooltip saying *"You're paying more than
  your own usual price… Not a comparison to the all-time-low"* — it contradicts
  the label it is attached to. That copy belongs on the "Your usual" line below,
  which already has its own tooltip.
- **"Manage alerts" cannot create an alert** — the modal only lists and deletes.
  Creation is the per-card input. Two affordances, one job, and the prominent one
  is the incomplete one.

### 5.5 Consistency

- **Three chrome shapes for one task**: row button → centred `BaseDialog`;
  dashboard → bottom sheet with picker; widget → centred dialog. The component
  reuse is right; the container is not unified.
- **Row-button spinner sits behind its own dialog** — `busy` renders on the row
  button *after* the dialog opens, so prefill arrival is signalled only by the
  "Prefilled …" caption popping in and reflowing the form.
- **Chart, multi-series**: 5 products → 5 dashed baselines in the same faint style
  with 5 labels stacked in the same right gutter; no y-axis unit label; nothing
  prevents plotting $/L against $/kg on one axis.
  `preserveAspectRatio="none"` will distort if the SVG is ever CSS-scaled.
- **"Your prices" is below the fold** at the bottom of the Overview tab (under
  name/level/notes/preferred-buys) while `BuyVerdictCard` — which is *about*
  price — sits at the top. Price is split across both ends of one tab.

## 6. Decisions taken in this session (owner, 2026-08-21)

| # | Question | Decision |
|---|---|---|
| D1 | Fate of the product-keyed surfaces (`/price-history`, My Products nav) | **Deferred — needs owner thought.** Leaning "keep both, fix nav + naming" (the minimal-structural option) over absorb-and-retire, but not committed. Tracked as **FU-703**. |
| D2 | The everyday user's core job on a prices surface | **All four are in scope** — triage (what's costing me more), lookup (what do I usually pay), capture (near-zero-friction logging), trend (basket drift). Not narrowed; design must serve all four, sequenced. |
| D3 | Where the everyday-user surface lives | **Two candidates to pursue:** (a) a **price lens on Stock overview** — no new nav slot, reuses the existing filter/row machinery; (c) a **section inside Reports** for the trend job. A dedicated top-level "Prices" nav entry was **not** chosen. |
| D4 | Alerting for the no-products user | **Advanced-only, hide cleanly.** Alerts stay product-keyed and require an inbound feed; they hide entirely when products are off, and the copy stops implying they exist. No stock-item watchlist, no nightly baseline check. |

**Note on D2 + D3 together:** picking all four jobs while rejecting a dedicated
nav entry means the jobs get *distributed* — triage + lookup onto the Stock
overview lens, capture into `PriceEntry` + the existing entry points, trend into
Reports. That split is deliberate and is the main thing FU-703's design work has
to make coherent rather than scattered.

## 7. Open decisions — closed / spawned as FUs

- **D1 (product-axis fate)** → **FU-703**. This is the one real fork left; every
  other item below is a defect with an obvious fix.
- Defects → **FU-704** (mobile `PriceEntry` + touch-invisible help),
  **FU-705** (chart has no touch interaction), **FU-706** (observation
  edit/confirm/date/cap), **FU-707** (signal tone, confidence, copy unification,
  silent dimension flip), **FU-708** (`/price-history` copy + affordance bugs).

No live undecided item remains in this memo — D2/D3/D4 are answered above, D1 is
FU-703.

## 8. Feedback coverage — `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`

The **PRODUCT HISTORY** section (file lines 215–226) is the feedback block this
memo targets. Every bullet mapped:

| # | Feedback bullet (abbrev.) | Where addressed |
|---|---|---|
| PH1 | "Feels like a major feature, hidden away a bit." | §2.1 — confirmed: orphan route, no nav entry. Root cause is §2 (capability on the wrong axis), not just placement. → FU-703 |
| PH2 | "Can select products but no change occurs on the page." | **Already fixed** — FU-605 (shallow-ref watch reassignment; see the `toggleSelect` comment in `PriceHistoryPage.vue`). Noted, not re-raised. |
| PH3 | "Product card feels squished, can't see full placeholder for notify-under. Verify." | §5.4 / §5.1 — card is `col-12 col-sm-6 col-md-4` with an inline label + button; still cramped. → FU-708 |
| PH4 | "Number input for notify-under should format to a decimal, price-input standard." | §5.4 → FU-708 (`step="0.01"` is set but there is no decimal formatting / blur normalisation). |
| PH5 | "The %off and other text is so tiny." | §5.4 → FU-708 (chip is `size="sm"` on a card with spare width). |
| PH6 | "%off chip colouring feels different to elsewhere — componentise and standardise." | §5.4 → FU-708 (raw `q-chip color="positive"` here vs the deal chips elsewhere; R-001 + D-rule colour semantics). |
| PH7 | "Hover bubble not theme-aware — white on white in dark mode." | Not reproduced in this static read (the `.chart-tooltip` styles were not opened). **Logged as a finding, confirm in browser** → FU-708, per the mandatory reported-defect rule. |
| PH8 | "Manage-alerts button is context-aware here — good, but also want a central alert-control area with per-type styling/icons." | Partially shipped as `SubscriptionsPanel`. §5.4 records that the local "Manage alerts" **cannot create** an alert, which is the inverse defect → FU-708. Central granular control stays out of scope of this memo. |
| PH9 | "Graph does not extend all the way to the edge of the box — bug? hidden info?" | §5.5 — measured width is `clientWidth - 32` with `preserveAspectRatio="none"` and a fixed right padding reserved for baseline labels; the gap is real and intentional-by-accident. → FU-708 |
| PH10 | "If kept as own page… drawer/bottom-sheet from My Products instead; use My Products as the selector." | **Superseded in part** — the bottom-sheet shape the owner described was built, but scoped to *stock items* (`PriceHistoryBottomSheet`), not products. The page-vs-sheet question for the product axis is exactly D1 → **FU-703**. |

Out of scope for this memo (tracked elsewhere): the PRODUCT SEARCH and MY
PRODUCTS feedback blocks, except where a bullet lands on a price surface.

`docs/02_feedback/COVERAGE_GAPS.md` — no flips needed; these bullets were already
attributed to the product-history surface.

## 9. Engineering-standards check (close-gate)

Read-only memo; no code changed, so no rule was introduced or touched. Rules the
findings above cite, for whoever picks up FU-703 onward:

- **R-001** (componentisation) — `PriceEntry` reuse is exemplary; the %-off chip
  on `/price-history` is a raw `q-chip` that should be the shared deal chip.
- **R-003** (single source of truth / state ownership) — `your_prices.py` is
  clean; the client renders and never re-derives. No violation found.
- **R-035 / `DESIGN_STYLE_GUIDE`** — colour semantics (warning on "paying more
  than usual"), hover-only help on touch, and the four competing phrasings of
  "usually" are D-rule issues, recorded in §5.2.

**ADR evaluation:** one candidate, deliberately *not* promoted yet because it
depends on D1 — *"a domain signal must not be presented as a warning when the
user did not cause it"* (tone / colour semantics for market-driven facts). If
FU-707 lands as described, promote it then.
