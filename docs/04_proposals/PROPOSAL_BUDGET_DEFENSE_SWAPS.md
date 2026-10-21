# Proposal — Budget-defense swaps + deal-quality signal (FU-451 + FU-450)

> **SCOPE UPDATE (2026-07-09, post-implementation).** The `good_deal` **alert
> type** (§4b, §6c, verifications tied to it in §11, everything downstream in
> chunk 3 of §10) is **CUT**. Proactive "this thing is cheap right now" nudges
> read as the app pushing users to buy from stores — the wrong posture for
> Dora (react to *your* list/pantry/plan, don't advertise). The
> `fake_markdown` detection (§4a) and the pure `DealQuality` compute stay in
> full: they're consumed by Buy Verdict (demote a fake special from buy → wait)
> and by the FU-451 swap ranker (filter fake markdowns), neither of which
> pushes anything at the user. Everything below about the `good_deal` alert
> kind, the `good_deal_alert_threshold` User column, the Preferences →
> Notifications toggle, the AlertsPage mapping, and the `--alert-kind-good-deal`
> token is **superseded** by this note. Related FU-516 (throttle deviation) is
> dropped with the feature.

> **SCOPE UPDATE (2026-07-09, at implementation).** **Product swaps (Pass B)
> are CUT, not deferred.** They structurally depend on a per-stock-item
> "usual/preferred product" (with price) to swap *down from* — the recipe-cost
> estimate already uses the cheapest linked product, so "buy the cheaper brand"
> has no baseline without tracking which brand the household actually buys. That
> per-product upkeep was **deliberately rejected** by the product owner (nobody
> wants that maintenance burden in the app). `PreferredBuy` is free-text only
> (no price), so it can't back it either. FU-451 therefore ships **recipe swaps
> only** (Pass A). Everything below about product-swap candidates, the
> `ProductSwapCandidate` DTO, the product-swap reason chips, and the
> product-swap row in the mockup is **superseded** by this note. FU-450's
> deal-quality signal still ships in full — it stands on its own value (Buy
> Verdict honesty + `good_deal` alerts), independent of the cut product swaps.

Wave-C design brief. Covers the "negotiator" half of P6-09 (over-budget
meal-plan weeks emit ranked recipe/product swap suggestions) plus the two
surviving pieces of P6-03 (`fake_markdown` detection + a `good_deal` alert
type). The 0–100 deal score + percentile UI from P6-03 is **explicitly out
of scope** — P8-05's Buy Verdict card replaced that surface.

Not an implementation plan — a design lock. The chunked impl-plan is a
separate follow-up (see §10 for the rough shape).

---

## 1. The problem

The **budget** half of P2-05 shipped (headroom, projected spend, over-budget
flag, dashboard card, FU-448 trim-to-budget). The **negotiator** half of
P6-09 never did. When a household is projected to blow the week's budget,
Dora currently only offers one lever: **cut items** off the shopping list.
Cutting is destructive; sometimes the better lever is a **swap** — buy the
on-special brand instead of your usual, or plan a cheaper recipe for
Thursday. Cheaper for the same nutritional outcome, no cutting required.

P6-03's original framing was a rich deal-quality UI (0–100 score, history
chart). P8-05 shipped a leaner version of that as the Buy Verdict card. Two
P6-03 pieces never made it through and are still worth building:

- **`fake_markdown` detection** — a merchant's claimed "special" is not a
  special if the "was" price is inflated. The user has seen the real
  everyday price in their own purchase history; a "deal" that isn't cheaper
  than their recent paid price should be flagged, not celebrated.
- **`good_deal` alert type** — a proactive nudge when a product linked to
  a stock item the household actually buys hits a genuinely-good price.
  Complements the reactive "should I buy this now?" answer P8-05 gives.

The negotiator can't rank product swaps honestly without both signals — a
swap ranked by "cheapest current offer" would happily route users into
`fake_markdown` traps. So they ship together.

**Charter fit:** P3 (self-correcting — Dora suggests corrections
proactively), P7 (safe mutations — every swap previews before it commits),
P8 (honest — never celebrate fake markdowns), P12 (Effortless — one tap,
concrete $ savings, no menu diving).

---

## 2. What already exists (skip if you know)

The negotiator sits on top of a lot of shipped infrastructure. This section
is the audit; skip to §3 if you already know it.

### Budget compute (shipped, FU-448)

- [`dora_api/features/budget/budget.py`](../../dora_api/features/budget/budget.py)
  — `period_bounds(today, period)`, `period_spent(user, start, end, repo)`,
  `period_headroom(user, on_date, repo)`. Weekly = Mon-Sun; monthly =
  calendar. Over-budget = `period_headroom < 0` OR `spent > amount`.
- Dashboard P2-05 card at
  [`DashboardPage.vue`](../../web_app/src/pages/DashboardPage.vue) reads
  `budget_status` and shows spent / projected / remaining / over-budget flag.

### Trim-to-budget (shipped, FU-448)

- [`dora_api/features/shopping_lists/trim_to_budget.py`](../../dora_api/features/shopping_lists/trim_to_budget.py)
  — preview/apply endpoint, five-tier classifier, closed-set reason chips,
  never-cut rules, `deferred_by_budget` column on the line, banner on
  `ShoppingListDetail.vue`. This brief **mirrors its API shape** — the swap
  endpoint reuses the request/response pattern.

### Recipe cost (shipped, Cookbook Chunk 9 / FU-116)

- [`dora_api/features/recipes/get_recipes.py::_compute_estimated_cost`](../../dora_api/features/recipes/get_recipes.py)
  — per-recipe cost derived from linked-product current offer → stock-item
  price observation (FU-216 `paid_price` ladder) → skip. Returns:
  `estimated_cost`, `estimated_cost_priced_count`, `estimated_cost_total_count`.
  Only on detail endpoint; gated on money-features opt-in. This is the
  substrate for `cost_per_week`.

### Compare prices (shipped)

- `compare_prices(stock_item_id)` in
  [`features/assistant/tools.py`](../../dora_api/features/assistant/tools.py)
  — returns current offers across linked products for a single stock item,
  ranked by price. Reused by the swap ranker.

### Buy Verdict (shipped, P8-05)

- [`dora_api/features/stock_items/get_buy_verdict.py`](../../dora_api/features/stock_items/get_buy_verdict.py)
  — buy/wait/skip badge on stock-item rows and shopping-list lines. **Missing:**
  the `fake_markdown` flag (FU-450 back-ports it) and the `good_deal` alert
  type (FU-450 adds it to `get_alerts.py`).

### Meal plan (shipped)

- [`domain/entities/meal_plan.py`](../../dora_api/domain/entities/meal_plan.py)
  — `MealPlan.start_date` + list of `MealPlanEntry(recipe_id, scheduled_for,
  servings, slot, consumed_at)`. A **week** = `[start_date, +7d)`. No
  `cost_per_week` column exists yet — this brief adds a computed field on
  the DTO, not a stored column.

### Removed and STAYING removed (charter guardrail — verbatim)

> **Substitute graph** — the standalone visual graph *page* (the old N7
> `/substitutes` route / `SubstitutesGraph.vue`). That page is deleted;
> don't rebuild it. **NOT removed:** the basic per-stock-item substitutes
> — the substitutes list on a stock item's detail page, surfaced in
> recipes and as a *temporary, cook-session-only* swap in cook mode (B8).
> Keep those.

Swaps here are **cheaper-product-for-same-stock-item** (reuses
`compare_prices`) or **alternative-recipe-for-same-slot**. Never
graph-based substitution. Never stock-item-→-other-stock-item swaps that
change what the household is eating. See §8 for the full non-goals list.

---

## 3. Design decisions (locked with user 2026-07-07)

Every one of these was an open call before the session. Locked below so
implementation doesn't drift.

| Decision | Locked to | Rejected alternative(s) |
|---|---|---|
| **Scope shape** | Wave-C brief first, chunked impl-plan follows. | Skinny MVP; full build in one session (too many design calls); CUT. |
| **FU-450 vs FU-451 order** | Both in this brief; both ship together. | FU-450 first (adds a chunk of upstream); price-only ranker for FU-451 (would ship `fake_markdown` traps). |
| **UI surfaces** | Meal-plan week (contextual, where recipe swaps make sense) + Dashboard budget card summary bullet (deep-linked). | Meal-plan week only (invisible from the dashboard); Dashboard only (recipe swaps are meaningless without week context). |
| **Apply flow** | Preview card → Confirm CTA. Matches trim-to-budget + PutAwayDialog patterns. | Optimistic apply + Undo toast (risky for cascading effects on shopping list); Multi-select + Apply-all (adds surface, no clear win). |
| **`cost_per_week` compute** | Server-side, on-the-fly, no new column. Reuses `_compute_estimated_cost` per recipe, sums across the week's uncooked entries. | New column on `MealPlan` (introduces a stale-cache class of bug for a purely-derived value). |
| **"Over budget" trigger** | `projected_over` — `period_spent + cost_per_week > budget_amount`. Fires **before** the week actually blows the budget. | `over_budget` only (fires after the damage is done, too late to swap). |
| **Recipe-swap candidate space** | Cookable-with-current-stock first, then tag-similar (same cuisine or same meal-type). Household-affinity (cooked before) as tie-breaker. | Full cookbook cross-product (too many candidates, most irrelevant). |
| **Product-swap candidate space** | For each ingredient in each week-recipe, if a linked non-preferred product's current price < preferred product's, propose. Reuses `compare_prices` per stock item. | Cross-item substitutes (banned by charter — no substitute graph). |
| **Deal-quality integration** | Swaps to products flagged `fake_markdown=true` are **filtered out** of the candidate set, not just down-ranked. Fake savings aren't real savings. | Down-rank only (still shows dishonest suggestions). |
| **Money-features gate** | Whole surface gated on the same opt-in that gates recipe cost + budget card. When money features are off, nothing here renders — no bullet on the dashboard, no button on the meal-plan week. | Show a disabled hint (R-029 hide-don't-nag). |
| **Undo** | A fresh reverse-apply POST (not a soft-delete state). Matches P7. | Toast-driven undo with a time window. |

---

## 4. The two-part algorithm stack

### 4a. FU-450 — deal-quality signal (upstream)

Pure function over a product's offer history. Runs on any surface that
already has a `Product`: the Buy Verdict card, the swap ranker, and the
new `good_deal` alert.

**Inputs:**
- `product_id`
- `window_days` (default `90`, admin-configurable)
- Access to `ProductOffer` current + historic rows for that product
- Access to the household's `StockItemPriceObservation` rows (FU-216) for
  the same product's linked stock item

**Computes (a `DealQuality` dataclass):**
- `lowest_price`, `highest_price`, `median_price`, `current_price` — over
  the window from historic + current offers combined.
- `is_lowest_in_window: bool` — `current <= lowest_seen_in_window`.
- `percentile: float` — 0..1, current vs the window's price distribution.
- `fake_markdown: bool` — `offer_claims_saving AND
  current_price >= median(household_paid_prices)`. Uses the household's
  real paid prices (FU-216) as ground truth for "what this thing actually
  costs" — not the merchant's claimed "was" price.
- `band: Literal["poor", "fair", "good", "great"]` — derived from
  `percentile` (< 0.5 → poor, < 0.7 → fair, < 0.9 → good, else great) and
  clamped to `"poor"` if `fake_markdown` is true.

**Explicitly NOT computed:** the 0–100 numeric score, the percentile UI
surface, the price-history chart. P8-05's Buy Verdict card is the
canonical "should I buy" surface — this signal feeds it, doesn't compete.

**Where the signal surfaces:**
- Fed into Buy Verdict's existing "wait / buy" logic — `fake_markdown=true`
  demotes any `buy` to `wait`, and the reason chip changes to *"Markdown
  looks inflated — you've paid less recently"*.
- The `good_deal` alert (see 4b).
- The swap ranker (see 4c).

### 4b. `good_deal` alert type (new alert kind, in `get_alerts.py`)

Fires when a product **linked to a stock item the household tracks** hits
band `good` or `great` (per user threshold). Payload shape mirrors existing
alerts:
- `alert_kind = "good_deal"`
- `severity = "medium"` for `good`, `"high"` for `great`
- `stock_item_id`, `stock_item_name`, `product_id`, `product_name`, `current_price`
- `message`: *"Peanut butter — Coles brand is at its lowest in 90 days"*
- `detail`: *"$3.20 · you usually pay $4.50"*
- `primary_action`: one-tap **add to shopping list** (reuses FU-437 add-to-list intent)

**Throttling:**
- Same `(product_id, band)` combination cannot fire more than once every
  14 days. Prevents a product that spends weeks bouncing at the top of the
  window from re-alerting every day.
- Snooze + dismiss inherit the shared alert-interaction plumbing (FU-099
  scope key + AlertInteraction row).

**Per-user threshold** (new column on `User`, defaults to `"good"`):
`good_deal_alert_threshold ∈ {"great", "good"}`. `"great"` = only the top
band. `"good"` = both bands. **No "fair" / "poor" option** — the whole
point is proactive nudges for real deals, not noise.

### 4c. FU-451 — the swap ranker (downstream of 4a + 4b)

Runs per-week. Ranks candidates by projected $ saving, subject to filters.

**Trigger.** Called for a `MealPlan` when
`period_spent + cost_per_week > budget_amount`. The trigger is derived
server-side; the client just calls the endpoint and gets zero rows back
if the week isn't over budget.

**Candidate generation — two passes:**

**Pass A: Recipe swaps.** For each `MealPlanEntry` in the week where
`consumed_at is None`:
1. Take the entry's recipe's `estimated_cost`.
2. Find candidate replacements from the household's cookbook where
   `estimated_cost < entry.recipe.estimated_cost`, filtered by:
   - Cookable-with-current-stock preferred (highest tier).
   - Tag-similar fallback (same cuisine tag OR same meal-slot tag).
   - Never-cooked-by-this-household filtered out unless nothing else
     matches (household affinity — don't push a stranger recipe as the
     "cheaper" answer).
3. For each candidate, compute `saved = entry.recipe.estimated_cost -
   candidate.estimated_cost` (per-serving, then multiplied by
   `entry.servings`).
4. Yield a `RecipeSwapCandidate` row per (entry, candidate).

**Pass B: Product swaps.** For each `MealPlanEntry.recipe.ingredients`
where `ingredient.stock_item_id is not None`:
1. Call `compare_prices(stock_item_id)` to get all linked products'
   current offers.
2. For each non-preferred product where `current_price <
   preferred_product.current_price`:
   - **Filter out** if that product's `DealQuality.fake_markdown is True`.
   - Compute `saved = (preferred_price - candidate_price) *
     ingredient.quantity_needed`.
   - Yield a `ProductSwapCandidate` row.

**Ranking** (both passes, combined pool):
1. Primary: `saved` descending.
2. Secondary: `deal_quality.band` ("great" > "good" > "fair" > "poor").
3. Tertiary: household affinity for recipe swaps (cooked before), or
   preferred-product-status for product swaps.
4. Tie-breaker: most recent activity on the stock item.

**Response cap:** top 5 across both types combined. More than 5 is
overwhelm, not choice. Users can call the endpoint again after applying
one — the new week cost triggers a fresh ranking.

**Constraints (never violate):**
- No swap for a `consumed_at IS NOT NULL` entry.
- No product swap that would require re-linking > 1 product per apply
  (keeps the preview honest — one line, one $ delta).
- No swap into a product flagged `fake_markdown=true`.
- No recipe swap into a recipe the user already has planned that same
  week (avoids "you should cook this on Thursday AND Tuesday").

---

## 5. Explainability chip vocabulary (fixed set)

Every candidate carries **exactly one** reason chip from this closed list.
Same design as FU-448's chips — bounded vocab so the UI never has to
render arbitrary strings.

**Product-swap chips:**
- `on_special` — "On special — save $X"
- `cheaper_everyday` — "Cheaper unit price"
- `real_deal` — "Genuinely good price (checked history)"
- `youve_paid_less_before` — "You've paid $Y here before"

**Recipe-swap chips:**
- `cheaper_recipe_cookable` — "Cheaper — uses stock you have"
- `cheaper_recipe_similar` — "Cheaper — same style meal"
- `cheaper_recipe_household_fav` — "Cheaper — you've cooked it before"

**Never-emitted chips (filtered candidates):**
- Anything for a `fake_markdown=true` product.
- Anything for a `consumed_at IS NOT NULL` entry.

The chip is frozen at ranker time on the swap DTO — the SPA doesn't
re-derive it. Matches the FU-448 pattern (`deferred_reason` column, frozen
on trim).

---

## 6. UI surface

Two entry points, one flow.

### 6a. Dashboard budget card (summary + deep-link)

Card is at [`DashboardPage.vue:390-446`](../../web_app/src/pages/DashboardPage.vue).
When the household is `projected_over` for the current week:

- Add a bullet under the existing spent/remaining lines:
  > **Save $12.40 this week** — 3 swaps ready · **See suggestions →**
- Clicking the CTA deep-links to the meal-plan week view with the
  Suggestions panel expanded.
- If the current week isn't `projected_over`, the bullet isn't rendered.
- If money features are off, the whole card is gated already — no change.

The card **does not** render the swap list itself. It's a signpost, not
the surface. Reason: the dashboard is a status snapshot; swap ranking has
per-day context (which recipe, which day, which product) that needs
proper surface real estate.

### 6b. Meal-plan week — Suggestions panel (the real surface)

Meal-plan week view (per grounding — `MealPlansOverview.vue` +
`MealPlanWeekView.vue` or similar). Adds a new section below the week's
meals when `projected_over`:

```
┌─────────────────────────────────────────────────────────┐
│ ⚠  Over budget by $8.20 this week                      │
│                                                         │
│  Est. week cost   $102.20                              │
│  Budget           $ 94.00                              │
│                                                         │
│  ● 4 swaps could bring it back to $89.60               │
├─────────────────────────────────────────────────────────┤
│  🍳 Recipe swap · Thursday dinner            $-4.10    │
│  Beef stroganoff → Chicken tray-bake                   │
│  Cheaper — same style meal                             │
│  [ Preview ]                                            │
├─────────────────────────────────────────────────────────┤
│  🏷 Product swap · Peanut butter             $-1.20    │
│  Woolworths Own → Coles brand                          │
│  On special — save $1.20                               │
│  [ Preview ]                                            │
└─────────────────────────────────────────────────────────┘
```

**Preview modal** (Charter P7 — every mutation is a preview → confirm):

```
Preview: Swap Thursday's Beef stroganoff → Chicken tray-bake

  Estimated week cost after this swap
  $ 98.10  (was $102.20, saved $4.10)

  Missing ingredients you'd need to buy
  Chicken thighs · Sweet potato · Rosemary

  [ Cancel ]                      [ Apply swap → ]
```

**Undo affordance:** after apply, a persistent "Just applied — Undo"
banner shows for the rest of the session. Undo is a fresh reverse POST,
not a soft state.

**Zero-state:** if the week is `projected_over` but no candidates rank
above zero-saving (rare, but possible when every alternative is also
expensive), the panel reads:
> **Over budget** — no swap saves you money this week. Cutting from your
> shopping list may be the only lever. **Open shopping list →**

### 6c. Alerts — `good_deal` type

Renders in the existing `AlertsPage.vue` alert list. Uses the shared
alert-item template — no bespoke card. One-tap **Add to shopping list**
action wired to the existing add-to-list intent (FU-437).

Filter/sort semantics inherit from other alert kinds. Threshold setting
lives at `Preferences → Notifications` alongside the other alert-type
toggles.

---

## 7. Backend shape

### 7a. New endpoints

| Method | Path | Purpose | Idempotent? |
|---|---|---|---|
| `GET` | `/api/meal-plans/<meal_plan_id>/swap-suggestions` | Ranked list + preview data. Returns empty when not `projected_over` or money-features off. | Yes |
| `POST` | `/api/meal-plans/<meal_plan_id>/apply-swap` | Applies one swap. Returns the updated week + a `swap_ledger_id` for undo. | No |
| `POST` | `/api/meal-plans/<meal_plan_id>/undo-swap` | Reverses a previously-applied swap by ledger id. | No |

### 7b. DTOs

```python
@dataclass(frozen=True)
class DealQuality:
    lowest_price: float
    highest_price: float
    median_price: float
    current_price: float
    is_lowest_in_window: bool
    percentile: float
    fake_markdown: bool
    band: Literal["poor", "fair", "good", "great"]

@dataclass(frozen=True)
class RecipeSwapCandidate:
    kind: Literal["recipe"] = "recipe"
    entry_id: UUID                     # MealPlanEntry to replace
    entry_scheduled_for: date
    entry_slot: str
    from_recipe_id: UUID
    from_recipe_name: str
    to_recipe_id: UUID
    to_recipe_name: str
    saved: float
    reason_chip: str
    missing_ingredient_names: List[str]

@dataclass(frozen=True)
class ProductSwapCandidate:
    kind: Literal["product"] = "product"
    entry_id: UUID                     # week context — which meal this affects
    ingredient_id: UUID
    stock_item_id: UUID
    stock_item_name: str
    from_product_id: UUID
    from_product_name: str
    to_product_id: UUID
    to_product_name: str
    saved: float
    reason_chip: str
    deal_quality_band: str             # From DealQuality.band

@dataclass(frozen=True)
class SwapSuggestionsResponse:
    projected_over: bool
    cost_per_week: float
    cost_per_week_priced_ratio: dict   # {"priced": N, "total": M, "unpriced_recipe_ids": [...]}
    budget_amount: float | None
    overshoot: float                   # Amount over budget
    projected_after_applying_all: float  # If every candidate applied
    candidates: List[Union[RecipeSwapCandidate, ProductSwapCandidate]]  # Max 5

@dataclass(frozen=True)
class ApplySwapRequest:
    kind: Literal["recipe", "product"]
    # Recipe apply:
    entry_id: UUID | None = None
    to_recipe_id: UUID | None = None
    # Product apply:
    stock_item_id: UUID | None = None
    to_product_id: UUID | None = None

@dataclass(frozen=True)
class ApplySwapResponse:
    swap_ledger_id: UUID               # For undo
    new_cost_per_week: float
    new_projected_over: bool
```

### 7c. New table: `MealPlanSwapLedger`

Small append-only table so undo is deterministic and audit-visible.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `meal_plan_id` | UUID FK | |
| `applied_by_user_id` | UUID FK | Actor |
| `applied_at` | datetime | |
| `kind` | str(16) | `"recipe"` or `"product"` |
| `undone` | bool | Defaults false; flips true when reversed |
| `undone_at` | datetime? | |
| `payload_json` | text | Frozen snapshot of the pre-apply state — enough to rebuild the row that changed. Recipe swap: `{entry_id, from_recipe_id, from_servings}`. Product swap: `{stock_item_id, from_product_id, previous_preferred: bool}`. |

Undo reads `payload_json` and reverses. No cascade to the shopping list —
that's a separate action the user can take next if desired.

### 7d. Interaction with existing surfaces

- **Trim-to-budget (FU-448)** — swaps happen **first** (reduce projected
  cost), trim happens **second** (cut what's still over). Two levers, user
  chooses order. No new coupling; the dashboard budget card shows both
  affordances when applicable.
- **Buy Verdict (P8-05)** — `DealQuality` becomes an input to
  `get_buy_verdict`; the verdict card gains a reason line
  *"Markdown looks inflated"* when `fake_markdown=true` is the reason
  behind a `wait` verdict. No API shape change on the verdict itself.
- **Auto-add-when-low (FU-448 lineage)** — `good_deal` alerts do NOT
  auto-add. They surface for user tap. Auto-add continues to be governed
  only by the low-stock signal, not by deal quality (avoids "your list
  keeps swelling every time a special hits").
- **Compare-prices assistant tool** — unchanged. Ranker calls it
  internally; no shape change to the tool response.

---

## 8. Explicit non-goals (Charter anti-creep)

These were considered and rejected. Documented so a future session doesn't
quietly reintroduce them.

- **No 0–100 deal score UI.** P8-05 Buy Verdict is the "should I buy"
  surface. The band (`poor/fair/good/great`) is an internal enum, not
  rendered as a numeric score anywhere in the SPA.
- **No price-history chart page.** Legacy P6-03 wanted an extended
  PriceHistoryPage plotting offer history with low/median markers. Cut —
  the household paid-price history is already visible on the stock-item
  detail; adding a second chart is duplicated surface.
- **No substitute graph reintroduction.** Charter Removed-features list is
  binding. Swaps here are cheaper-product-same-stock-item OR
  cheaper-recipe-same-slot. Never "this stock item can be replaced with
  that stock item".
- **No stock-map / spatial layout.** Location is still a simple tree; the
  swap surface doesn't touch location.
- **No cross-week swaps.** Ranker only considers the currently-selected
  week. "Move Thursday's steak to next Wednesday to smooth the budget" is
  a plausible future feature but adds a week-scoped scheduler dimension
  that isn't worth the complexity now.
- **No auto-apply.** Every mutation goes through preview → confirm.
  Optimistic apply with undo-toast was rejected — swap mutations cascade
  to the shopping list and can affect what the household eats; that's not
  the class of decision to make behind the user's back.
- **No "buy the cheaper brand across every ingredient at once" bulk apply.**
  Users can chain single applies; a bulk-apply hides too much decision
  behind one tap. Multi-select was also rejected in §3.
- **No swap for a `consumed_at IS NOT NULL` entry.** Ate it, can't swap
  it. Ranker filters these out.
- **No swaps for out-of-stock ingredients.** If a proposed swap would
  require buying something the household doesn't have and doesn't want to
  buy, the missing-ingredients preview surfaces the cost of the swap
  honestly. It's the user's call.
- **No new "Deals" tab.** `good_deal` alerts live in the existing
  AlertsPage; no separate discoverability surface.

---

## 9. From the original spec

The `docs/00_original_spec/` sweep surfaced no explicit budget-defense-swap
feature note. The original spec's meal-plan surface (Feature Notes) reads
as "sequential meal-plan builder" and template rotation — not budget
negotiation. The substitute graph existed but was later removed; this
brief inherits its scope-guardrail (never reintroduce a stock-item
substitute graph), not its shape.

**Nothing to extract.** The authoritative spec here is P6-09 / P6-03 in
`06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md`, quoted in the
grounding research (agent report 2026-07-07). No dropped intent worth
reviving.

---

## 10. Sequencing (rough — chunked impl-plan is separate)

The impl-plan will slice this into ~6 shippable chunks. Rough shape:

**Chunk 1 — `DealQuality` compute (FU-450 core).** Pure function +
`get_deal_quality(product_id, repo, window_days)`. Unit tests for the
percentile / fake-markdown branches. No new endpoint yet — surface via a
data-tool `assistant/tools.py` shape so it's testable in isolation.

**Chunk 2 — Wire `DealQuality` into Buy Verdict.** Update
`get_buy_verdict` to consult the new function; `fake_markdown=true`
demotes a `buy` to `wait` and injects the reason chip. Migration-free,
purely additive on the verdict endpoint.

**Chunk 3 — `good_deal` alert type (FU-450 alert).** Add to
`get_alerts.py`, hook throttle (14 days per product+band). New
per-user threshold column `good_deal_alert_threshold`. Wire the
Preferences → Notifications toggle. Add to `AlertList.vue` template
mappings.

**Chunk 4 — `cost_per_week` + `projected_over` (FU-451 substrate).**
Extend the meal-plan detail DTO with `cost_per_week`, `priced_ratio`,
`projected_over` computed server-side. Show the number on the meal-plan
week UI (read-only). Gate on money-features opt-in.

**Chunk 5 — Swap ranker + endpoints (FU-451 core).** Implement the
two-pass candidate generator + ranker. Add
`GET /meal-plans/<id>/swap-suggestions`, `POST .../apply-swap`, `POST
.../undo-swap`. Create the `MealPlanSwapLedger` table (single migration).
Reason-chip vocab frozen in code. Full unit-test coverage for the ranker
(same shape as trim-to-budget's 17 classifier tests).

**Chunk 6 — SPA surface (FU-451 UI).** Suggestions panel on the meal-plan
week + summary bullet on the Dashboard budget card. Preview modal + Undo
banner. Zero-state and money-features-off paths.

Each chunk lands with tests, R-008-clean comments, a `DORA_VERIFY.md`
entry, and a CHANGELOG line.

**Total scope:** ~1200-1500 LOC across backend + frontend, one migration
(`MealPlanSwapLedger` table), one User column (`good_deal_alert_threshold`).
No entity-shape changes, no breaking API changes.

---

## 11. Verify (browser + operator)

Written for `DORA_VERIFY.md` — the QA pile. Grouped by chunk so
partial-ship states remain walkable.

### FU-450 verifications

- [ ] With a Product that has ≥ 90 days of offer history, at least one
  `<= median` current price → Buy Verdict on that item flips to `wait` with
  reason *"Markdown looks inflated — you've paid less recently"*.
- [ ] Same product, current price *below* the household's median paid
  price → Buy Verdict shows real-deal reason chip, not the fake-markdown
  one.
- [ ] `good_deal` alert fires for a product hitting `great` band, does
  NOT re-fire within 14 days.
- [ ] Threshold set to `"great"` in Preferences → no alerts for `good`
  band products.
- [ ] `good_deal` alert's one-tap **Add to list** works, respects the
  primary-list picker (FU-316).

### FU-451 verifications

- [ ] Meal-plan week that's projected over budget → Suggestions panel
  renders under the meal grid; **Save $X · N swaps ready** header.
- [ ] Dashboard budget card shows the summary bullet with the same $ total;
  clicking the CTA deep-links to the correct week with the panel expanded.
- [ ] Preview modal shows the correct `saved` amount and the correct
  `new_cost_per_week`; missing ingredients are listed if a recipe swap
  requires them.
- [ ] Confirm on the preview modal → meal-plan week reflects the swap
  immediately; "Undo" banner appears; clicking Undo restores the previous
  state.
- [ ] Swap into a `fake_markdown=true` product does NOT appear in the
  candidate list (ranker filter).
- [ ] A meal with `consumed_at IS NOT NULL` does not appear in the
  candidate list.
- [ ] Money features off (Preferences) → no Suggestions panel, no summary
  bullet, no `cost_per_week` number.
- [ ] Zero-state: force a week where no candidate has positive saving
  (contrived seed) → panel shows the "no swap saves money" copy with the
  shopping-list link.
- [ ] Rate limit: apply-swap called with a stale candidate (server rejects
  because the projected state has drifted) → 409 with an "out of date"
  message; suggestions refresh on retry.

---

## 12. Coverage table

Wave-C cross-cutting mode — map the feedback bullets that motivated this
work, not every bullet in the app.

| Bullet | Source | Covered by section |
|---|---|---|
| **L254** — "Recipe estimated cost... fed from recipes into meal planning, then meal plans into shopping list budgets... all features can connect together nicely... option to turn off for the not-budget-conscious." | `Feedback _ Fixes - as of [06-Jun-2026].md` L254 | §4c (ranker consumes recipe cost), §6b (meal-plan week surfaces `cost_per_week`), §7d (interaction with shopping-list trim), §3 (money-features gate — the whole surface hides when off). |
| **L341** — Sequential meal-plan builder feeding shopping-list flow, week-scoped. | Feedback L341 | §6b — swap surface sits directly inside the meal-plan week context L341 asks Dora to be a "useful tool" around. |
| **L342** — Meal-plan templates + auto-add signal. | Feedback L342 | Out of direct scope. Template reuse is a separate feature; this brief respects it by making swap-apply idempotent per `MealPlanEntry` — a template applied to a week can still be swap-negotiated afterwards without contaminating the template itself. |
| **P6-09 legacy spec** (§594) | `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md` | §4c (ranker), §7 (endpoints), §6 (UI). Every element of the legacy spec traces to a section here except the substitute-graph-shape (explicitly rejected — §8). |
| **P6-03 legacy spec** (§233) | `PROMPT_PLAN_PART_6_POLISH.md:233` | §4a (`DealQuality` compute), §4b (`good_deal` alert). 0–100 score UI + price-history chart page explicitly cut in §8. |
| **FU-448 pattern reuse** | Prior brief | §5 (chip vocab pattern), §7a (endpoint shape), §7c (ledger table pattern). |
| **FU-450 items (`fake_markdown`, `good_deal` alert)** | `DORA_FOLLOWUPS.md` FU-450 | §4a, §4b, §11 verifications. |

**No `docs/02_feedback/COVERAGE_GAPS.md` gap flips** — the feedback
bullets above were already tracked. This brief plants a solution for
L254; L341 gets a partial answer (the week-view surface is where swaps
live); L342 stays open (template rotation is separate work).

---

## Cross-refs

- **Blocks nothing** — chunks 1-6 can land in order without gating other work.
- **Blocked by nothing** — every dependency (recipe cost, buy verdict, budget compute, compare prices, meal-plan week, alerts framework) is already shipped.
- **Cross-refs:**
  [[FU-450]] (this brief resolves the surviving pieces),
  [[FU-451]] (this brief resolves in full),
  [[FU-448]] (prior brief; the trim-to-budget lever that this brief complements),
  [[FU-352]] (Dora Score over-budget bullet — could deep-link to the swap surface as a future refinement),
  P8-05 (Buy Verdict — consumes `DealQuality` per §4a),
  P8-07 (Zero-Input Pantry — informs cookable-with-current-stock filter in §4c),
  P8-08 (Dora Score — orthogonal surface).
