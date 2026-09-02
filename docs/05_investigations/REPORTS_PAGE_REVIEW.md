# REPORTS_PAGE_REVIEW — PO + engineering review of `/reports`

**Date:** 2026-09-02 · **Type:** read-only assessment, no code changes.
**Scope:** `web_app/src/pages/ReportsPage.vue` (1211 lines),
`web_app/src/services/api/reportsApiService.ts`,
`dora_api/features/reports/reports.py` (1393 lines), plus the surfaces it
duplicates (`DashboardPage.vue`, `components/shoppingList/StoreSpendCard.vue`,
`components/dashboard/DashboardCard.vue`, `style/storeSwatch.ts`).
**Weighting:** ~80% product, ~20% engineering, as briefed.
**Method:** static read against `DESIGN_STYLE_GUIDE.md` (A/B/D rules),
`ENGINEERING_STANDARDS.md` (R rules), and the two sibling surfaces that render
the same data. Nothing was driven live — every finding below is code-evidenced
and line-cited, and the ones that need a running app to confirm are marked and
carried as FUs.

---

## 0 · Verdict in one paragraph

This page has never been designed and has never been reviewed. It is a faithful,
almost line-by-line implementation of the 2025 `N6 — Reports / Analytics page`
prompt in `docs/00_original_spec/PROMPT_PLAN.md:649` — six cards, that exact
order, "donut + legend with $ amounts", "big number + sparkline", and a "Make
essential" bulk button, all specified before the charter, the feedback pass, the
design style guide, the money opt-in, or the dashboard rebuild existed. Five more
widgets were later bolted onto that six-card frame without revisiting it. On the
owner's side, the REPORTS section of
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md:423` contains exactly
one character — `?` — and `COVERAGE_GAPS.md:238` records the surface as "feedback
empty; deferred". **So this document is the missing feedback pass.** The page is
not badly designed; it is undesigned, and it is now the only significant surface
in the app that ignores the money opt-in.

**Answering the brief's "is the current design best, does it need polish, or is
it fine as is":** the card *shell* is fine and should simply be shared rather
than re-declared (§4.2). The *information design inside the cards* is not fine
and polish will not fix it — the page needs a point of view before it needs
tokens (§4.10, §5). The type/spacing/colour work is real but it is the second
job, not the first.

---

## 1 · What is good — protect these in any rework

1. **The empty-state copy.** The best in the app. Specific, actionable, in
   Dora's voice: *"No stock-level history in this range yet. Update an item's
   level or wait — the line builds as you use the app."* / *"Nothing's been added
   to a list while out of stock — nicely played."* Whatever happens to the
   widgets, keep the words.
2. **Backend honesty discipline.** `delta_pct = None` rather than a fake `+100%`
   when the prior window was zero (`reports.py:1346`); lines with no price
   snapshot skipped rather than back-filled with today's price
   (`reports.py:34-39`); `estimate_note` shipped to the client so the caveat is
   renderable. This is rare and correct, and it is the standard the front end
   fails to live up to (§4.7, §6 finding 8).
3. **"You keep running out of these"** is the most genuinely insightful thing on
   the page (see §3.5). It is badly named and badly actioned, but the signal is
   right.
4. **The wastage reason tiles** (`ReportsPage.vue:155-166`) are the best-designed
   component here — a fixed 5-up grid where zero-count tiles still render,
   dimmed, so the shape is stable and "you have not logged any of these" reads as
   intentional rather than as missing data. This is the pattern the rest of the
   page should copy.
5. **YoY ranks by absolute delta magnitude** (`reports.py:1356`), so the biggest
   movers surface regardless of sign. Someone thought about that.
6. **Spend by category (group)** is the one widget that answers a question people
   actually ask out loud.

---

## 2 · The framing: why the page looks like this

Reading `PROMPT_PLAN.md:649` explains almost every oddity, and it matters because
it tells you which problems are drift and which are original sin:

| Today | Origin |
|---|---|
| Hard-coded 2-column grid, single 900px breakpoint | N6: *"responsive grid, 2 cols desktop, 1 col mobile"* — predates the dashboard's `col-12 col-sm-6 col-lg-4` 3-up |
| Card CSS byte-identical to `DashboardCard.vue` | N6: *"match its card style and layout idioms"* — copied before the shell was extracted into a component |
| Donut + legend for spend by store | N6, verbatim |
| Big number + sparkline for savings | N6, verbatim |
| "Mark all essential" bulk button | N6: *"a 'Make essential' bulk action button"* |
| ECharts as a dependency | N6: *"Use Apache ECharts via vue-echarts, OR Chart.js"* |
| Six cards, in that order | N6's list, in that order |

Three things N6 asked for that were **not** built, and are still worth having:

- *"Every chip and number is clickable: deep links to StockItemDetail or to a
  pre-filtered StockOverview."* Only item names link. Every money figure, every
  store row, every YoY row and the whole savings card are dead ends.
- *"Use `<StockItemChip>`."* Plain `<a>` elements were built instead — which is
  also why they are not keyboard-focusable (§4.9).
- Deep links into a *pre-filtered* stock overview. Nothing on the page filters
  anything.

Everything added after N6 — the Memory band, meals cooked, spend by category,
year-over-year, wastage — was appended to the six-card frame rather than
prompting a re-think of it. That is how a page designed for six widgets ended up
with eleven.

---

## 3 · The owner's questions, answered

### 3.1 Does spend-by-store use the same colouring as the shopping list's "where you'll shop"? — No. This is the worst consistency failure on the page.

Three surfaces render "spend by store". All three look different:

| Surface | Rendering | Colour source |
|---|---|---|
| Shopping list (`StoreSpendCard.vue:32-40`) | Proportional CSS bar + chips | `storeColour()` — logo `brand_colour` first, deterministic name hash as fallback |
| Dashboard (`DashboardPage.vue:1016-1028`) | Plain text list, top 3 + total | None |
| Reports (`ReportsPage.vue:64-77`) | ECharts donut + dot legend | Page-local `colourFor()` — name hash into `--chart-1..6` |

So Woolworths is green on your shopping list (its logo colour) and could be
mauve in Reports (hash position in the chart ramp). The header comment of
`style/storeSwatch.ts:1-25` documents this *exact* bug class being fixed — for
`StoreLogo.vue` and the shopping list card. Reports was never migrated.

`colourFor()` (`ReportsPage.vue:612`) should be deleted. `StoreSpendRow` needs
`brand_colour` added server-side (it already carries `store_id`), and the card
should call `storeColour(row.store, row.brand_colour)`.

Note the same function also colours **spend by category** — hashing stock-group
names into the chart ramp. That one is legitimate (a stock group has no brand
colour), so `colourFor` survives as a categorical helper; it just must not be
what colours a *store*.

### 3.2 Should it offer the dashboard's opt-in behaviour? — Yes, and it is the highest-value single change.

The dashboard has: four named zones, per-card show/hide, per-zone reorder,
server-persisted layout on `user.dashboard_layout`, and two feature gates
(`money`, `products`) that remove a card from the page *and* from the Cards menu
(`DashboardPage.vue:1467-1545`). Reports has none of it.

More pointedly: **`ReportsPage.vue` does not import a single feature flag**, and
the nav entry (`MainLayout.vue:278`) is unconditional. With money turned off, a
household still gets spend by store, savings captured, spend by category,
year-over-year, price trends, and two dollar-formatted chart axes. That directly
contradicts the owner's own feedback bullet at
`Feedback _ Fixes - as of [06-Jun-2026].md:254` — *"some people may not want to
know how many dollars they are eating… It should be an option to turn off (all
budget/money related features outside the very basic product search
information)"* — which is the bullet the whole money opt-in / ADR-005 posture was
built from. Every other money surface honours it. Reports does not.

The overlap goes further than "adopt the pattern": `savings`, `spend_trend`,
`pantry_value`, `price_drops` and `restock` are **already dashboard cards backed
by these exact endpoints**. Reports is currently the ungated, unconfigurable,
larger-format twin of the dashboard's Money zone. They should share one card
registry, not maintain two.

### 3.3 Is stock value over time valuable? — No. Cut it from Reports.

The formula (`reports.py:134-151`) is `stock_level.sequence × cheapest
linked-product price as-of the bucket`. `sequence` is a **0–5 ordinal** — an item
at "Plenty" contributes `rank × price` whether that is one jar or twelve. When
there is no linked product it falls back to the item's own price observations;
with neither, the item contributes zero.

So the number is an ordinal multiplied by a dollar figure, which is not a dollar
figure at all — and it systematically undercounts, exactly as observed, because
every unpriced item silently contributes nothing. The `estimate_note` admits this
in 11.5px grey text (which is itself below the type floor, §4.3). A chart whose
caveat is "this is not what it says it is" should not be the first thing on the
page.

**Replace, don't repair.** If you want a pantry-state trend, chart something
actually measured: *count of items at Low/Out over time*, or *essential coverage*
(% of `is_essential` items in stock). Both come from `StockLevelChange`, which is
already loaded for this very handler, both are honest, and both are actionable in
a way a fuzzy dollar total never is. Keep the endpoint for the dashboard's
opt-in `pantry_value` card if you want it to survive at all; drop the card here.

### 3.4 The wastage widget — how big does it grow? Too big. You are right.

`most_wasted` returns up to **25 rows** (`waste.py:52,571`), and `.report-list`
has **no `max-height`** — only `.meals-cooked-top` got one, at 240px
(`ReportsPage.vue:1155-1161`). Twenty-five rows at ~37px each is ~1000px, plus
the summary line and the five reason tiles: a ~1200px card.

In a 2-column grid that card drags its row partner — Savings, which is one big
number — to the same height, producing roughly 900px of dead white space beside
it. That is `D-011` / FU-578 #30's stranded-card pattern in its most extreme
form, and it is the one card that can trigger it dynamically from user data.

Fix: cap the visible list at 5–8 with a "see all" that lands on a filtered waste
view, and give `.report-list` the same `max-height` + scroll the meals list
already has.

### 3.5 What is the point of "You keep running out of these", and of "Mark all essential"?

**The widget is the best signal on the page and the title is failing it.** It
does not mean "everything that goes out of stock lands here". `KeepsRunningOutHandler`
(`reports.py:534-619`) walks every shopping-list line that ever had an
`added_at`, resolves via `StockLevelChange` history what level that item was at
*at the moment it was added*, and counts how often that level was Out of Stock.

The insight is therefore: **"you ran out of this before you got around to
restocking it"** — a planning failure, not a stock state. That is worth surfacing.
The current title describes the symptom; it should say the thing it actually
knows, with one line of explanation beneath it.

Two hard problems:

1. **It silently ignores the range picker.** `getKeepsRunningOutAsync()` takes no
   range and the endpoint has no range param (`reports.py:642`). It counts all
   history, forever, while sitting underneath a control that says "30 days".
   Either wire the range through or lift the card out from under the picker.
2. **"Mark all essential" should go.** It is an unconfirmed bulk mutation across
   ten items (`ReportsPage.vue:887-904`) with no confirm step, no undo, no
   per-row control, and no awareness of current state — it re-sets items that are
   already essential and still toasts "Marked 10 items essential". `B6`/`D-008`
   expect a confirm on a bulk state change of that size. Meanwhile INV-10
   (`ESSENTIAL_FLAG_FINDINGS.md`, recommendation 2) already concluded the right
   home for setting this is the **stock-overview multi-select**, where the
   "Essentials" filter chip already lives so set and filter are co-located.

   Replace it with a per-row toggle that shows current state, or drop the action
   entirely and let each row link to its item.

### 3.6 What is spend by store actually based on?

Completed lists (`status = done`) whose `completed_at >= since` — so yes, the
range picker — then **ticked** lines with a captured price, grouped by store
(`reports.py:365-445`). Two things worth knowing:

- **Price ladder:** `actual_unit_price` (your till-receipt override) falling back
  to `picked_offer_price`. Lines with neither are dropped from the total **with
  no footnote**. The shopping list's own card is scrupulous about this — it
  renders *"12 items unpriced, not counted"* (`StoreSpendCard.vue:251-255`).
  Reports quietly undercounts and says nothing.
- **Store attribution only works through picked products.** The query requires
  `selected_product_id IS NOT NULL` (`reports.py:407`), so the store comes from
  the product's store and nothing else. The shopping list resolves store through
  a five-rung R-003 chokepoint — `purchased → planned → usual → last-purchase →
  offer` (`_line_price.py:88-129`). **Reports uses rung five only.**

  Consequence: a household that tags items *"I buy this at Aldi"* and never
  touches the products feature sees a fully populated store breakdown on its
  receipt and an **empty card** in Reports, from the same finished list. This is
  the highest-value correctness fix on the page after gating.

### 3.7 Savings captured — is it product-feature gated? — No, and the metric itself is weak.

No money gate, no products gate. It needs both: savings is
`list_price_at_pick − picked_offer_price` (`reports.py:774-778`), which only ever
has data if you use product offers. On a products-free install it is a permanent
empty state telling the user to go do the thing they opted out of — which is
`B9`'s explicit "don't offer an action that lands on another data-gated surface"
rule.

The deeper product problem: *"saved vs RRP"* is retailer-marketing framing. It
measures the discount the store advertised, not money you kept. A household that
bought three discounted things it did not need "saved" money by this metric,
which sits badly against the charter's Honesty principle and against Anti-creep.

If it survives, invert it: the **spend** is the headline, savings is the support
line, and the honest comparison is against *your own historical unit price for
that item* rather than the retailer's claimed RRP. That is a claim you can stand
behind, and price-trends already holds the data for it.

> **DECIDED (owner, 2026-09-02): the card survives with the inverted metric, and
> the change is app-wide with a tense split.** Live in-list savings keep the
> vs-shelf-price baseline; this retrospective card moves to the household's own
> historical unit price; both name their baseline in the label. Existing archived
> lists are reseeded rather than backfilled, because the new baseline needs a
> pick-time snapshot column and deriving it later would make past figures move.
> Recorded as **ADR-068 / R-071**; work carried by **FU-831**. Two consequences
> for this page specifically: the **money and products gates this section asks for
> are still needed** (they ride in Chunk 1 / FU-816), and the handler's current
> "no RRP snapshot ⇒ contribute zero savings" fallback stops being acceptable —
> under an own-price baseline an item with no price history has *no* baseline, so
> it becomes an **R-041 coverage** case (report the count it was built from), not
> a silent zero.

### 3.8 What is the point of "Meals cooked"? The widget is fine; the presentation is not selling it.

It is cook-events-per-bucket as a line, plus a top-10 recipe list. Three
failures:

1. **Wrong chart for the data.** `cook_count` per bucket is 0, 1 or 2 for a
   normal household. FU-578 #29 already logged the symptom ("renders as one solid
   filled block"). Worse, it is `smooth: true` with an area fill
   (`ReportsPage.vue:691-699`) — a smoothed curve through integer counts implies
   1.4 cooks happened on Tuesday. Sparse integer counts want **columns or a
   calendar heatmap**, never a smoothed area line.
2. **The headline is the smallest text on the card.** "14 cooks · 31 meals-worth"
   sits in `.report-card-note` at 11.5px (`ReportsPage.vue:241-255`). That is the
   sellable number, rendered below the legibility floor.
3. **It omits the thing it is uniquely able to say: repertoire.** *"You cooked 9
   distinct recipes this month"* / *"31 of your 40 saved recipes have not been
   cooked in a year."* Nothing else in the app can answer that, it is computable
   from the same `CookEvent` rows already loaded, and it drives people back into
   the cookbook. That is what would sell this card.

Proposed headline: **"You cooked 14 times this month — 31 meals, 9 different
recipes. Most-cooked: Beef stew (×5)."**

### 3.9 "Spend by category" should be "Spend by stock group" — agreed, and the backend already agrees.

`SpendByCategoryHandler` groups by `StockItem.stock_group.name`
(`reports.py:1126-1131`); only the UI label says "category". Rename the card.

Note the rename is wider than one string if you want it consistent: the
year-over-year card's rows are also stock groups labelled `category`, through
`SpendByCategoryRow.category` and `SpendYoYCategoryRow.category` and both TS
interfaces. Decide whether the rename stops at the label (cheap, slightly
dishonest) or goes through the DTOs (correct, touches four files). Recommendation:
label now, DTOs when either handler is next opened.

### 3.10 Is price trends broken? — Almost certainly yes, on SQLite, for every range except "All time".

`PriceTrendsHandler` compares `offered_on < since` with no timezone coercion
(`reports.py:709`). `offered_on` is `DateTime(timezone=True)`
(`table_mappings.py:202,211`); **SQLite does not preserve tzinfo**, so it returns
naive, while `since` comes from `datetime.now(timezone.utc)` and is aware.
Comparing them raises `TypeError: can't compare offset-naive and offset-aware
datetimes` — a 500.

Every other handler in the same file guards this. `_price_as_of` calls `_as_utc()`
before the identical comparison (`reports.py:319-320`); there are two separate
in-file comments about SQLite dropping tzinfo (`reports.py:222-226`,
`reports.py:1078-1080`). This one handler was missed.

It is invisible to the test suite because the only price-trends test that seeds
real data passes `range=all` (`tests/e2e/dora_api/test_reports_router.py:156-169`)
— precisely the branch where `since is None` and the comparison never executes.
It would work on Postgres, which makes it a §7.5 distribution-posture break: a
SQLite-only failure in code that is supposed to stay portable both ways.

Two further defects in the same card, independent of that one:

- **The product picker can only ever see 50 products.** It hydrates through
  `productStore.getProductsAsync()` → bare `GET /products` → paginated at
  `DEFAULT_LIMIT = 50` (`query_options.py:22`), then filters client-side
  (`ReportsPage.vue:556-570`). This is FU-668's unpaged-first-page trap verbatim,
  third confirmed instance after stock items (FU-035) and the cookbook. Product
  51 onward is unsearchable and the user gets no indication.
- **`clearable` on a `multiple` q-select emits `null`**, and the very next thing
  `loadPriceTrends` does is read `.length` off it (`ReportsPage.vue:773`).
  Clicking the clear affordance should throw.

### 3.11 Considering all setups

| Setup | What `/reports` shows today |
|---|---|
| **Money off** | The entire page. Spend by store, savings, spend by group, YoY, price trends, two dollar-formatted chart axes. Nothing gated. Contradicts feedback L254. |
| **No products** | Price trends unusable, savings permanently empty, spend-by-store empty (product-only attribution, §3.6), stock value near-zero. Four dead cards. |
| **Non-AUD currency** | Legends and totals correct (`formatMoney`), but two chart y-axes hard-code `formatter: '${value}'` (`ReportsPage.vue:627,730`) — a literal dollar sign past the `useMoney` authority. R-003 / D-006. |
| **Meal planning or cooking unused** | "Meals cooked" is a permanent empty state under a band promising "what you actually did". |
| **Waste logging unused** | A large zero and five dimmed tiles. Correct behaviour, but a whole card saying nothing. |
| **Scanning off / stocktake off** | No effect — correctly. |
| **Fresh install** | Eleven empty states at `min-height: 240px` each: roughly 3000px of nothing. The worst first-run page in the app. |
| **Range = 2y / 5y / all** | Wastage silently clamps to 365 days server-side (`waste.py:520`) — self-labelled, acceptable. Keeps-running-out ignores the range entirely and does not say so. YoY blanks itself with an explanation — good. |

---

## 4 · Design, UI and UX pass

### 4.1 The verdict, split in two

- **The card shell is fine.** It is visually consistent with the dashboard and
  reads cleanly. It should be *shared* rather than re-declared (§4.2), and its
  off-scale values fixed globally, but nothing about it needs redesigning.
- **The information design inside the cards is not fine, and polish will not fix
  it.** Eleven equal-weight boxes in a flat grid, sorted by nothing, with no lede,
  no hierarchy, and no opt-out. The problems in §4.3–4.9 are real and worth
  fixing, but fixing all of them yields a beautifully tokenised page that still
  has no point of view. Sequence accordingly (§7).

### 4.2 The card shell is a copy-paste fork of `DashboardCard.vue`, and it has already drifted

Side-by-side, `ReportsPage.vue`'s `.report-card*` rules and
`components/dashboard/DashboardCard.vue`'s `.dora-card*` rules are byte-identical:

| Property | `DashboardCard.vue` | `ReportsPage.vue` |
|---|---|---|
| `border-radius` | `18px` | `18px` |
| `padding` | `18px 20px 20px` | `18px 20px 20px` |
| head `gap` / `margin-bottom` | `8px` / `14px` | `8px` / `14px` |
| title | `1.05rem` / `600` / `flex: 1` | `1.05rem` / `600` / `flex: 1` |
| icon | `--brand-primary`, `22px` | `--brand-primary`, `22px` |
| background / border / shadow | `--surface-component` / `--border-default` / `--elevation-card` | identical |

The fork has already lost things the shared component gained afterwards: the
hover elevation + lift, the `prefers-reduced-motion` guard on that hover, the
`:deep(.dora-card-action)` styling for header-right content, the
`letter-spacing: 0.005em` on the title, and the router-link variant that makes a
whole card one keyboard-focusable target. It added one thing:
`min-height: 240px`.

This is a textbook R-001 finding with a ready-made fix: delete ~60 lines of CSS
and render `<DashboardCard>`. The `#action` slot already exists for the
range-note and the tooltip icons.

**One caveat that makes this less trivial than it looks:** `18px` radius and
`18px 20px 20px` padding are **off the token scale in both files** (`--radius-lg`
is 10px, `--radius-xl` 16px, `--radius-2xl` 22px; `--space-4` is 16px, `--space-5`
20px). Consolidating onto the shared component is safe; *also* correcting it onto
the scale changes the dashboard's appearance. Those are two separate decisions —
see D3 in §8.

> **DECIDED (owner, 2026-09-02): both, and in one pass — correct to `--radius-lg`
> (10px) + `--space-4` (16px).** The "two separate decisions" framing above was
> right, but it implied the correction was a close call; a survey of every
> `border-radius` in `web_app/src` settled it. **10px appears at 41 sites**
> (`--radius-lg` ×22 + raw `10px` ×19); **18px at 3** — `DashboardCard`, this
> page's fork, and the dashboard hero. The guide matches the app; these are the
> outliers. `--radius-xl` (16px) was rejected as the gentler landing because it
> would leave two card radii in the app (D-017). Folded into **FU-814** so
> `DashboardCard` is touched once, not twice.

### 4.3 Typography: 17 raw font-size literals, zero tokens, two below the hard floor

`A2` requires the `--font-size-*` unitless ratios applied as
`calc(var(--font-size-x) * 1rem)`, and states the floor plainly: *"Hard floor:
`--font-size-xs` (12px). Nothing smaller, ever (D-003)… any value the user acts
on (price, count, badge label) is `--font-size-sm` (14) or larger."*

| Class | Literal | px@16 | Role | Should be | Verdict |
|---|---|---|---|---|---|
| `.reports-title` | `1.6rem`/700 | 25.6 | Page title (h1) | `--font-size-2xl` (24) bold | off-scale |
| `.reports-sub` | `0.92rem` | 14.7 | Secondary body | `--font-size-sm` (14) | off-scale |
| `.report-card-title` | `1.05rem`/600 | 16.8 | Card title (h3) | `--font-size-xl` (20) **bold** | off-scale **and undersized** |
| `.report-card-note` | `0.72rem` | 11.5 | Carries values | `--font-size-sm` (14) | **below floor, D-003** |
| `.waste-reason-label` | `0.72rem` | 11.5 | Tile label | `--font-size-xs` (12) | **below floor, D-003** |
| `.store-count` | `0.78rem` | 12.5 | "3 lists" / share % | `--font-size-sm` | value under 14 |
| `.report-list-count` | `0.85rem` | 13.6 | "×7", counts | `--font-size-sm` | value under 14 |
| `.savings-number` | `2.4rem` | 38.4 | Hero number | `--font-size-3xl` (30) | off-scale by 8px |
| `.waste-total`, `.yoy-total__current` | `1.8rem` | 28.8 | Hero number | `--font-size-3xl` (30) | off-scale |
| `.waste-reason-count` | `1.2rem` | 19.2 | Tile value | `--font-size-lg` (18) | off-scale |
| `.store-legend li` | `0.88rem` | 14.1 | Row text | `--font-size-sm` | off-scale |
| `.report-empty` | `0.9rem` | 14.4 | Empty copy | `--font-size-sm` | off-scale |
| `.reports-memory-band` / `__hint` | `0.95rem` / `0.85rem` | 15.2 / 13.6 | Band label | `--font-size-md` / `-sm` | off-scale |
| `.yoy-rows li` | `0.9rem` | 14.4 | Row text | `--font-size-sm` | off-scale |

Two things stand out beyond the token drift. **Card titles at 16.8px/600 do not
read as titles** — they are the same visual weight as body text, so the page has
no scanning rhythm; `A2` puts a card title at 20px bold. And **`.report-card-note`
carries real values at 11.5px** — the meals-cooked headline, the spend-by-group
total, the YoY window label. The most sellable numbers on the page are rendered
below the legibility floor.

Because the base is user-scalable, these literals also mean the page does not
scale with a user's font-size preference the way tokenised surfaces do.

### 4.4 Spacing and radius: three radii, none of them consistently on-scale

Off-scale values in the page's ~300 lines of scoped CSS: page padding
`24px 24px 96px` (96 is not on the scale), grid `gap: 18px` (should be
`--space-4` 16 or `--space-6` 24), card padding `18px 20px 20px`, card radius
`18px`, head `margin-bottom: 14px`, list-row padding `8px 10px`, row/tile radius
`10px`, dot radius `999px` (should be `--radius-pill`).

`B4` also specifies `--space-6` (24px) between sibling cards; the grid uses 18px.

The page therefore carries **three different corner radii** (18px cards, 10px
rows and tiles, 999px dots) where the app's ladder is 10 / 16 / 22 / pill. It
reads fine because 18 sits between 16 and 22, but nothing else in the app is
18px except the forked `DashboardCard`.

### 4.5 Colour: three role misuses, one of them a genuine product judgement

1. **Nested rows use `--surface-elevated`.** `.report-list li` and
   `.waste-reason-tile` (`ReportsPage.vue:1041,1088`) sit *inside* a
   `--surface-component` card. `A1`'s surface ladder reserves `--surface-elevated`
   for *"menus, popovers, a card that floats above other cards"*, and puts wells
   and inset regions on `--surface-sunken`. The ladder is inverted: rows nested
   inside a card are rendered as if floating above it. The shopping list gets this
   right (`--surface-sunken` for the picked drawer and the neutral chips), and
   `B11` specifies sunken for zebra. Should be `--surface-sunken`.
2. **`--brand-primary` on eleven decorative card icons.** `A1` reserves brand
   primary for *"the single primary CTA per view, active-nav indicator, brand
   marks"*. Eleven green icons dilute it to wallpaper, and then there is no green
   left to mean "this is the action" — which is part of why nothing on the page
   reads as actionable. Icons should be `--text-secondary`; keep brand primary for
   whatever single action each card eventually gets. (Note this is inherited from
   `DashboardCard`, so it is a shared decision.)
3. **Red/green for spend direction, and it is the wrong call.**
   `.yoy-up { --semantic-negative }` / `.yoy-down { --semantic-positive }`
   (`ReportsPage.vue:1201-1202`). `A1` defines negative as *"Out-of-stock level,
   destructive actions, errors"*. Spending $31 more on dairy is not an error —
   you may have hosted more dinners, or fed a teenager. The app should not
   moralise about a household's grocery spend when it has no budget target to
   measure against. Use `--text-primary` with a directional arrow and let the
   number speak; reserve semantic colour for the **budget** card, which has an
   actual threshold to breach. (Colour-blind safety happens to be covered here
   because the `+`/`-` sign travels with it, so this is a semantics objection, not
   a `D-001` violation.)

   Also in that rule: `var(--semantic-negative, #b43c3c)` and
   `var(--semantic-positive, #228b22)` carry hard-coded hex fallbacks for tokens
   that certainly exist — R-002, and in a dark theme the fallback would be wrong
   if it ever fired.

### 4.6 Six chart languages for four kinds of question

| Widget | Current treatment | Question it answers | Right treatment |
|---|---|---|---|
| Stock value | Smoothed area line | Trend | (cut — §3.3) |
| Spend by store | Donut + dot legend | Composition | **Horizontal bar** |
| Spend by category | Donut + dot legend | Composition | **Horizontal bar** |
| Savings | Sparkline (no axes) | Trend | Sparkline, fine |
| Meals cooked | Smoothed area line | Sparse counts | **Columns** or calendar heatmap |
| Price trends | Multi-series line | Continuous series | Line, correct |

Three arguments for killing the donuts specifically:

- **They do not scale.** A donut is readable at three slices. Spend by stock
  group routinely has eight or more, at which point the ring is decorative and
  all the information lives in the legend beside it — which is a bar chart with
  extra steps.
- **A 180px fixed donut plus a `min-width: 200px` legend in a flex-wrap row
  (`ReportsPage.vue:989-1006`) is fragile at half-width on a tablet**, wrapping
  the legend below the ring and leaving the ring stranded.
- **It costs the page its consistency.** The shopping list already renders this
  exact dataset as a proportional horizontal bar with brand-coloured segments and
  a hatched "no store" catch-all — a component that is thoughtfully built, already
  solves the zero-value-bucket and the unassigned-bucket problems
  (`StoreSpendCard.vue:154-197,284-308`), and is the thing the user has already
  learned to read.

**Reuse `.sl-store-bar` here.** It deletes the donut, deletes the legend, deletes
`colourFor` for stores, and makes "where you shopped" look the same in all three
places. It is the single highest-leverage design change on the page, and it is
mostly deletion.

Consequence worth flagging: `ReportsPage.vue` is the **only** `v-chart` consumer
in the app, and its built chunk is **562KB** — the second-largest asset in the
bundle after the icon font, ahead of the entire main CSS file. If the redesign
lands on one line chart and one sparkline, ECharts is no longer worth its weight;
if it keeps five charts, it is. Worth deciding deliberately rather than by
inertia.

> **DECIDED (owner, 2026-09-02): ECharts goes.** Two corrections to the paragraph
> above, both from measuring rather than reasoning. (1) The chunk is **549 KB**
> measured (`ReportsPage-L-6CPwJ3.js`) and ECharts is **inlined into the route
> chunk**, not a shared vendor bundle — so the cost is paid only by visitors to
> `/reports`, never at app boot, which is a weaker argument for removal than
> "second-largest asset" implied. (2) The far stronger argument, which this review
> missed: **the app already owns a hand-rolled replacement that ships in 8 KB.**
> `components/PriceHistoryChart.vue` is 462 lines of inline SVG doing multi-series
> polylines, y-ticks and a hover tooltip — the exact chart price-trends needs.
> Combined with this section's own recommendation (donuts → CSS proportional bars,
> counts → columns), **no surviving chart needs a library**. ECharts is already
> tree-shaken to `LineChart` + `PieChart` (`:457-465`), so removal is the only
> remaining lever. Work in **FU-833**; it includes giving `PriceHistoryChart` the
> legend, x-ticks and `aria`/text-alternative it currently lacks — which is also
> how §4.9's "five canvas charts with no accessible alternative" finding finally
> gets fixable, since SVG can carry what canvas cannot.

### 4.7 Loading and empty states

- **`B10` is unambiguous:** *"Any async surface >150ms shows a skeleton shaped
  like its content… never the literal string 'Loading…', never a blank pane."*
  All ten cards render a centred `AppSpinner` in a 240px box
  (`ReportsPage.vue:40-42` and nine repeats). Ten spinners firing at once on
  page load is also visually noisy in a way one skeleton grid would not be. Each
  card should get a skeleton matching its shape — a title bar plus a chart block,
  or five row bars.
- **`B9` anatomy is** *"feature icon (32–48px, muted) · one-line what-goes-here ·
  optional one primary action"*. The empty states here are text-only in a
  centred grey box — no icon, no action. The **copy is excellent** (§1.1) and
  should survive untouched; it just needs the icon and the shape around it.
- **Empty and error are indistinguishable**, which is the honesty failure (§6
  finding 8): a card whose fetch 500'd renders *"Nothing wasted in this range —
  nicely played"*. The page congratulates you on data it failed to load.
- **`min-height: 240px` on every card** means the empty-state cost is paid in
  full: eleven empty cards is ~3000px of scrolling on a fresh install.
  Hide-when-empty (R-029) is the pattern the dashboard uses for
  `reconcile_pending`; combined with opt-in cards it would make a new install
  land on a short, honest page instead of a long, apologetic one.

### 4.8 Layout and breakpoints

- **One breakpoint, at 900px** (`ReportsPage.vue:939`), which is not in the app's
  vocabulary. `A8` defines phone <600 / tablet 600–1023 / desktop ≥1024, and the
  dashboard uses `col-12 col-sm-6 col-lg-4`. So a 1000px tablet gets two 470px
  columns holding 280px charts, and an 899px window gets one ~850px column
  holding a 280px chart. Neither is a considered layout; both are artefacts of
  N6's "2 cols desktop, 1 col mobile".
- **A wide desktop gets 2 columns where the dashboard gets 3.**
- **The stranded half-card is structural, not incidental.** The first block is
  wide + 5 half-cards, so one always sits alone beside dead air — `D-011`,
  `B4`'s *"no lone half-width card beside dead air"*, and FU-578 #30. Opt-in
  cards make this worse, not better, unless the grid uses a masonry/auto-flow or
  the card set is curated to an even count per band.
- **Phone:** a 240px minimum card plus a 280px chart, eleven times, is a very
  long scroll for a surface nobody reaches on a phone with a specific question.
  Charts should shorten below 600px.
- **The Memory band is a half-implemented zone system.** It is one divider,
  drawn mid-page, that separates spend-by-store (above) from spend-by-group and
  YoY (below) — despite those being the same data from the same query shape.
  Either commit to zones properly, sharing the dashboard's vocabulary, or drop
  the single band.

### 4.9 Accessibility

- **Zero `aria-*`, zero `role=`, zero `:focus-visible`** in 1211 lines. `A6`:
  *"Focus is always visible… This is not optional."*
- **`.report-list-name` is an `<a>` with `@click` and no `href`**
  (`ReportsPage.vue:96,127,172,275`) — not keyboard focusable, not a link, not
  middle-clickable, invisible to a screen reader's link list. Four widgets
  affected. N6 asked for `<StockItemChip>`; this is what got built instead.
- **`@click="row.recipe_id && goToRecipe(row.recipe_id)"`** (`ReportsPage.vue:277`)
  renders `cursor: pointer` and hover underline for a deleted recipe, then does
  nothing when clicked.
- **Five canvas-rendered charts with no text alternative.** ECharts on
  `CanvasRenderer` is completely opaque to assistive tech. Each needs at minimum
  an `aria-label` summarising the series ("Spend by store: Coles $210,
  Woolworths $140, Aldi $62"), or a visually-hidden data table.
- **Charts never repaint on theme switch.** `themeTick` (`ReportsPage.vue:580`)
  is declared, read inside `chartPalette` (`:594`), and **never incremented
  anywhere in the file** — the comment at `:575` claiming it is *"triggered by
  the route nav + manual reload"* is not true of any code in the repo. So the
  palette is read from the DOM once and frozen: switch from a light to a dark
  theme while on this page and every chart keeps its old-theme colours until a
  full reload. Dead state that advertises a behaviour it does not have.
- **`.waste-reason-tile` has `aspect-ratio: 1`** and at 360px in a 3-up grid
  comes out ~95px square, holding an 11.5px two-word label ("Didn't like") — it
  will wrap awkwardly. Tap-target size is fine (`D-004`); legibility is not.

### 4.10 What it should look like — the design ideas

Ten concrete moves, roughly in order of value:

1. **Open with the answer, not the caveat.** The page currently opens with a
   title, a disclaimer, and a toggle. Replace the subtitle with a live lede:
   *"You spent $412 across 4 shops in the last 30 days — 8% less than the month
   before. Biggest mover: Dairy, up $31."* The "estimates pulled from…" caveat
   becomes an info icon next to the range control. This one change converts the
   page from a dashboard of instruments into a report.
2. **Make the range control honest about its window.** Show the resolved dates
   beside it ("2 Aug – 2 Sep") so "30 days" is concrete, and make cards that do
   not honour it either honour it or stop sitting under it (§3.5).
3. **Delta is the hero; level is the support.** Every money card's headline
   should be the *change*, not the amount: "$412 · down 8% on last month". The
   YoY handler already proves the query shape for any window, so this is
   generalisable rather than a special case for one card.
4. **One composition language, borrowed from the shopping list.** Horizontal
   proportional bars with `storeColour` for stores and the chart ramp for groups.
   Donuts out. (§4.6)
5. **One counting language.** Columns for cook counts, never smoothed lines
   through integers.
6. **Cards earn their place; the user decides.** Adopt the dashboard's
   zone + show/hide + reorder + gate machinery, and share its card registry. This
   is simultaneously the fix for "too much", for the money gate, and for the
   "is stock value worth keeping" question — make it opt-in and find out.
7. **Skeletons, `B9` empty states, and hide-when-empty** so a fresh install lands
   on something short and true rather than eleven apologies.
8. **Every number is a door.** N6 asked for this and it was never built: the
   store row filters shopping-list history to that store, the group row opens
   stock filtered to that group, the savings figure opens the list breakdown, the
   wastage count opens the waste log. A report you cannot walk into is a poster.
9. **Retire semantic red/green for spend direction** (§4.5.3); keep it for
   budget, which has a real threshold.
10. **Card titles at 20px bold, values never under 14px, brand green spent on
    actions rather than on eleven decorative icons.** The type/colour work from
    §4.3–4.5, which is what makes the whole thing feel deliberate rather than
    assembled.

---

## 5 · Information architecture: eleven widgets, four questions

Eleven cards, four of them money, three of which are the same query sliced three
ways. **Spend by store, spend by group, and year-over-year are one widget with an
axis toggle** — same source, same range, same query shape; the user question is
"where did my money go?" and store / group / vs-last-period is a control, not
three cards.

Proposed card set, question-led:

| Question | Card | Built from |
|---|---|---|
| Where did my money go? | **Spend** — bar, axis toggle: store / group / vs last period | merges spend-by-store + spend-by-category + YoY |
| What am I mismanaging? | **Waste & run-outs** — reason tiles + top offenders + "ran out before restocking" | merges wastage + keeps-running-out; they are the same story |
| What do we actually eat? | **Kitchen memory** — cooks, meals, distinct recipes, top recipes, untouched recipes | meals-cooked + a repertoire count |
| Is this worth buying? | **Price trends** — advanced, opt-in, products-gated | price-trends, plus the missing own-item trend below |

Plus the lede strip (§4.10.1). That is four cards and a sentence, against eleven
cards and a disclaimer.

**What is missing entirely:**

- **A price trend over your own data.** Price trends charts *products* — a
  power-user feature most installs never populate. The everyday user's own
  `StockItemPriceObservation` history (the very substrate the stock-value
  estimate falls back to) has **no trend surface anywhere in the app**. FU-703
  already records the owner's decision D3 that the everyday price job belongs as
  *"a price lens on Stock overview + a trend section in Reports"*. This page is
  where *"which of my items got more expensive?"* is supposed to live, and it is
  the largest missing widget.
- **Export.** Reports is the one page where "give me the CSV" is a reasonable
  ask; `useStockOverviewExport` / `useMealPlanExport` are the precedent, and the
  DATA feedback section already asks for export in multiple formats.
- **Period comparison as a global affordance**, not one card's speciality.

---

## 6 · Engineering findings, ranked

| # | Finding | Location | Rule |
|---|---|---|---|
| 1 | Price trends 500s on SQLite for any bounded range — naive/aware datetime comparison, missing `_as_utc()`. Untested because the only seeded test uses `range=all`. | `reports.py:709` | §7.5 portability |
| 2 | No feature gating on the page or its nav entry — money and products surfaces render regardless. | `ReportsPage.vue` (no import), `MainLayout.vue:278` | ADR-005, feedback L254 |
| 3 | Two store-attribution rules for one dataset: Reports uses offer-store only; the shopping list uses the five-rung ladder. Same list, different breakdown. | `reports.py:407` vs `_line_price.py:88` | R-003 |
| 4 | Two store-colour rules: local hash-into-chart-ramp vs brand-first `storeColour`. | `ReportsPage.vue:612` vs `storeSwatch.ts:84` | R-002, D-001 |
| 5 | `clearable` + `multiple` q-select emits `null`; `.length` read off it immediately. | `ReportsPage.vue:773` | — |
| 6 | Product picker capped at 50 — unpaged-first-page trap, third instance. | `ReportsPage.vue:556`, `productStore.ts:22` | FU-668 |
| 7 | Unbounded `.report-list` in the wastage card (25 rows, no max-height) drags its grid partner. | `ReportsPage.vue:1027`, `waste.py:571` | D-011 |
| 8 | A failed fetch shows a red banner **and** leaves the failed card rendering its "nothing here yet" empty state — failure reads as absence of data. Each loader needs its own catch and an error state. | `ReportsPage.vue:857-875` | Charter Honesty, D-007 |
| 9 | Bulk mutation of 10 items with no confirm, no undo, no state awareness; toast overstates what changed. | `ReportsPage.vue:887-904` | D-008, INV-10 |
| 10 | Hard-coded `'${value}'` in two chart y-axes, past the `formatMoney` authority. | `ReportsPage.vue:627,730` | R-003, D-006 |
| 11 | `themeTick` is dead state — declared, read, never incremented; charts never repaint on theme switch, and the comment claims otherwise. | `ReportsPage.vue:575-594` | — |
| 12 | 17 raw font-size literals, two below the 12px floor and carrying values. | §4.3 table | R-002, D-003, A2 |
| 13 | `.report-card*` is a byte-identical fork of `DashboardCard.vue` that has drifted (lost hover, reduced-motion, action styling, link variant). | §4.2 table | R-001 |
| 14 | Clickable `<a>` with no `href` in four widgets; dead pointer for deleted recipes; no focus styling anywhere. | `ReportsPage.vue:96,127,172,275` | A6, R-011 |
| 15 | Five canvas charts with no accessible alternative. | `ReportsPage.vue` (all `v-chart`) | A6 |
| 16 | Nested rows use `--surface-elevated` where the ladder calls for `--surface-sunken`. | `ReportsPage.vue:1041,1088` | A1 |
| 17 | Keeps-running-out silently ignores the range picker it sits under. | `reports.py:642`, `ReportsPage.vue:762` | — |
| 18 | Structural stranded half-card (1 wide + 5 halves in the first band). | `ReportsPage.vue:29-192` | D-011, B4 |
| 19 | Raw `q-select` bypassing `BaseSelect` — already logged. | `ReportsPage.vue:415` | FU-795 (open) |
| 20 | Page-local breakpoint at 900px, outside the app's 600/1024 vocabulary. | `ReportsPage.vue:939` | A8 |

Findings 1, 5, 6, 8 and 11 are functional defects. The rest are consistency,
design-rule or architecture debt.

---

## 7 · Recommended sequencing

> **Build status (2026-09-02): Chunks 1 and 2 are done, green and driven live.**
> FU-816, FU-815 and FU-813 are resolved; FU-814 items 2/3 closed (item 4 landed
> with dashboard chunk 6; item 1 waits for chunk 3, below). Findings 1, 2, 3, 4,
> 5, 6, 8, 10, 17 are fixed; finding 11 (`themeTick`) was already fixed by
> FU-824 before this build started. **Two things the static review could not
> have found, both caught by driving it:** the gates were a *race* against the
> `/api/health` probe, so on a cold load every money card rendered its **empty**
> state (FU-586 on a second page → **FU-844**); and the store legend drew "No
> store set" in the *same* colour as a real store, because the hash palette is a
> sealed six (→ **FU-843**, with the categorical ramp's own collision). Chunk 3
> is next and is unaffected by both.

**Chunk 1 — gate it.** Money and products gates on the cards and the nav entry,
matching the dashboard's `cardAvailable`. Small, non-negotiable, and it closes an
outstanding contradiction with the owner's own feedback.

**Chunk 2 — fix the functional defects.** Findings 1, 5, 6, 8, 11, plus the
store-attribution ladder (3) and the store colours (4). Add a `range` param to
keeps-running-out (17). Backend-heavy, testable, no design decisions in it.

**Chunk 3 — restructure.** Adopt the dashboard's card registry, zones, opt-in and
`DashboardCard` shell. Collapse the three spend widgets into one with an axis
toggle. Add the lede. Cut stock-value-over-time. Cap the wastage list. This is
where the design work in §4.10 lands, because the surviving card set determines
how much of it is needed.

**Chunk 4 — the missing widget.** Own-item price trends per FU-703's decision D3.

**Chunk 5 — design-rule sweep.** Tokens, skeletons, `B9` empty states,
accessibility, breakpoints. Last deliberately: doing it before Chunk 3 means
tokenising cards that are about to be deleted.

---

## 8 · Open decisions

Every item below carries a recommendation so none is left dangling; the four that
are genuinely the owner's call were logged as FUs and **all four have since been
answered**.

> **Owner answered D1–D4 on 2026-09-02**, the same day as the review (D2 first,
> then D1/D3/D4 in a second pass). FU-809, FU-810, FU-811 and FU-812 are all
> **resolved**; the decided work is carried by **FU-831** (savings baseline),
> **FU-832** (shared catalogue + layout machinery), **FU-833** (drop ECharts) and
> an amended **FU-814** (un-fork *and* correct the card radius). No owner call
> remains open on either page review.

- **D1 — Do Reports and the dashboard's Money zone share one card registry?**
  *Recommendation was: yes.* **DECIDED (owner, 2026-09-02): share a flat catalogue
  plus the machinery — but not the card bodies.** The scope was narrowed once the
  overlap was measured properly: after the dashboard's own restructure (FU-830) the
  two surfaces share **five endpoints** (`savings-captured`, `spend-by-store`,
  `stock-value`, `price-drops`, `keeps-running-out`) but **no presentation** — the
  dashboard's are glance-sized, Reports' are full-size with range controls. So what
  gets shared is:
  1. a **flat data table** keyed by card id declaring gate / label / icon /
     endpoint — explicitly a table, **not** a plugin architecture or an abstraction
     layer (the constraint the owner attached, and the right one for a
     single-maintainer codebase);
  2. an extracted **`useCardLayout()`** composable carrying visibility, order and
     the server-persisted layout, which Reports currently has none of;
  3. the **`DashboardCard` shell** (already FU-814's job).
  Card *bodies* stay separate by design. The R-003 win is concrete: the money and
  products **gate facts stop being declared twice** — today they are declared once
  on the dashboard and zero times on Reports, which is exactly why FU-816 exists.
  → **FU-809 resolved**; the work is **FU-832**. Note FU-816 (add the gates) still
  ships standalone in Chunk 1 — do not wait for the catalogue to fix a live
  contradiction with feedback L254.
- **D2 — Does "Savings captured" survive?** *Recommendation was: keep the card,
  change the metric.* **DECIDED (owner, 2026-09-02): exactly that, and two
  follow-on calls settled the scope the recommendation left open.** **"Saved"
  splits by tense** — live in-list savings stay vs shelf price (RRP), because in
  the aisle "what this offer is under the ticket" is the honest question and it is
  the only baseline available for an item with no price history; the retrospective
  card moves to the household's **own historical unit price**; and **both are
  labelled**, in the DTO field name as well as the copy. **Spend becomes the
  headline** with savings as support. **Existing archived lists are reseeded, not
  backfilled** — the own-price baseline needs its own pick-time snapshot column
  (`usual_price_at_pick` beside `list_price_at_pick`), and deriving it
  retroactively would make every past shop's savings move each time a price is
  logged, which is what the existing snapshot design exists to prevent. Now
  **ADR-068 / R-071** (*a comparative figure carries its baseline in its label,
  and one word never spans two baselines*). → **FU-810 resolved**; the work is
  **FU-831**, which spans this page, the dashboard's Money card and the shopping
  list's live figure. Note the knock-on: the handler's current
  RRP-snapshot-missing fallback silently contributes zero savings, which under the
  new baseline becomes an R-041 coverage obligation rather than a fallback.
- **D3 — Do the off-scale `18px` radius / `18px 20px 20px` padding get corrected
  onto the token scale?** *Recommendation was: consolidate now, defer the
  correction — it's a visual-taste call.* **DECIDED (owner, 2026-09-02): correct
  them, to `--radius-lg` (10px) and `--space-4` (16px).**
  **The recommendation was based on a wrong assumption and a survey overturned
  it.** I framed this as guide-vs-reality, implying the 18px might be the app's de
  facto card radius with the guide lagging. Counting every `border-radius` in
  `web_app/src`: **10px appears at 41 sites** (`--radius-lg` ×22 plus a raw `10px`
  ×19), 12px at 14, `--radius-xl` (16px) at 2, and **18px at exactly 3** —
  `DashboardCard`, `ReportsPage`'s fork of it, and the dashboard hero. So A4 is
  not aspirational: 10px *is* the app's card radius, and these are a three-site
  outlier. That makes it a straightforward correction rather than a taste
  judgement. `--radius-xl` (16px) was rejected as the softer landing precisely
  because it would leave the app with **two** card radii, which is what D-017
  exists to prevent. → **FU-811 resolved**; the correction is folded into
  **FU-814** (amended), since shipping it separately means touching
  `DashboardCard` twice.
- **D4 — Does ECharts stay?** *Recommendation was: defer until the card set
  settles.* **DECIDED (owner, 2026-09-02): drop it — extend
  `PriceHistoryChart.vue` instead.** Two measurements made this answerable now
  rather than later:
  - **ECharts is already as small as it gets, and it is route-scoped.** It is
    inlined into the `ReportsPage` route chunk (measured **549 KB** built,
    `ReportsPage-L-6CPwJ3.js`), not a shared vendor chunk — so only visitors to
    `/reports` pay it, never app boot. And it is *already* tree-shaken to
    `LineChart` + `PieChart` + `CanvasRenderer` (`ReportsPage.vue:457-465`), so
    there is no fat left to trim; the only lever is removal.
  - **The replacement already exists and already ships.**
    `web_app/src/components/PriceHistoryChart.vue` is **462 lines of hand-rolled
    inline SVG** — multi-series polylines, y-ticks, hover tooltip, point circles,
    a shared palette composable — and it builds to **8 KB**
    (`PriceHistoryChart-nDFcRMh6.js`). It already draws precisely the chart
    Reports' price-trends needs, on the same kind of data.
  After the restructure every surviving chart is a CSS proportional bar (§4.6),
  a sparkline polyline, columns, or a multi-series line — **nothing left needs
  ECharts**. Honest cost, stated so it isn't a surprise: that component has **no
  legend, no x-ticks and no `aria`/`role`**, so adopting it as the app's chart
  means investing in it. That investment is worth having anyway — being SVG it
  *can* be made accessible, which §4.9's canvas-charts finding says ECharts never
  can. → **FU-812 resolved**; the work is **FU-833**.
- **D5 — Does "category" → "stock group" go through the DTOs or stop at the
  label?** *Answered inline (§3.9): label now, DTOs when either handler is next
  opened.* No FU needed.
- **D6 — Replacement for stock-value-over-time.** *Answered inline (§3.3):
  Low/Out count over time, or essential coverage. Both from `StockLevelChange`,
  already loaded by that handler.* Folded into Chunk 3, no separate FU.
- **D7 — Keeps-running-out: wire the range, or lift it out from under the
  picker?** *Answered inline (§3.5): wire the range — the card is more useful
  bounded ("you ran out three times **this month**") than as an all-time tally.*
  Folded into Chunk 2.

**Open decisions — closed:** all seven resolved above; D1–D4 additionally spawned
as FU-809 through FU-812.

**Owner status: all four answered 2026-09-02** (same day as the review) — D2 in a
first pass, D1/D3/D4 in a second. FU-809/810/811/812 are resolved; the decided work
is **FU-831** (savings baseline), **FU-832** (flat catalogue + `useCardLayout()`),
**FU-833** (drop ECharts, promote `PriceHistoryChart`) and an amended **FU-814**
(un-fork + correct the radius to `--radius-lg`). **No owner call remains open on
either page review.** Two of the four answers went against this document's
recommendation, both because a measurement overturned the premise — see D3 (the
radius survey) and D4 (the chunk and the 8 KB alternative).

---

## 9 · From the original spec

Skimmed `docs/00_original_spec/PROMPT_PLAN.md` (N6) and
`Unprocessed Ideas (from Google Docs).md`. Historical and non-authoritative; the
charter, feedback and D-rules override. Three items worth extracting:

- **N6's "every chip and number is clickable" — keep.** Specified in 2025, never
  built, and it is still the right instinct: it is the difference between a
  report and a poster. Adopted as §4.10.8.
- **Idea #47, "Add a report generator" — consider, partially.** Custom date
  ranges (built), include/exclude groups (not built), save a report to the
  Reports page (not built), export/download as PDF (not built). The *scan-data*
  framing is **superseded** — scraping moved to the standalone companion. The
  *export* half survives as a live gap (§5), and it is corroborated by the DATA
  feedback section's ask for multiple export formats. The "saved custom reports"
  half is a genuine Anti-creep risk and should stay parked.
- **Idea #34, "See total savings from price deal report" — superseded, and
  deliberately.** "How much would I save if I bought every deal" is a metric that
  rewards buying things you do not need, which is the opposite of what Dora is
  for. `price-drops` plus `savings-captured` cover the honest part of the intent.
  Do not rebuild it.

Nothing else in the original spec's Reports material is worth pulling forward.

---

## 10 · Feedback coverage

Mandated by `CLAUDE.md`. The unusual thing about this surface is that **the
feedback is empty by design of circumstance**: the REPORTS heading in
`Feedback _ Fixes - as of [06-Jun-2026].md:423` contains a single `?`, and
`FEEDBACK_TRIAGE_AND_PLAN.md:19,166,204` records Reports as explicitly deferred
and never reviewed. There is therefore no `F`-bullet set to map. The table below
maps the one Reports bullet, the cross-cutting bullets that land on this page,
and the session's own verbally-supplied feedback, which is the real source here.

| Bullet | Source | Where covered |
|---|---|---|
| REPORTS — `?` (never reviewed) | Feedback L423-425 | **This document is the review.** §1–§6 |
| Money features must be switchable off, app-wide | Feedback L254 | §3.2, §3.7, §3.11, finding 2, Chunk 1 |
| Dashboard: card reordering / toggle list | Feedback L57 (DASHBOARD) | §3.2, §4.10.6 — the machinery Reports should adopt |
| Data export in multiple formats | Feedback L467 (DATA) | §5 "what is missing", §9 (idea #47) |
| Font size/type usage is bad for headings | Feedback L471 (DATA, same class of defect) | §4.3 — card titles at 16.8px |
| Spend-by-store colouring vs shopping list | Owner, this session | §3.1, finding 4 |
| Dashboard-style opt-in behaviour | Owner, this session | §3.2, §4.10.6, D1 |
| Is stock value over time valuable? | Owner, this session | §3.3, D6 |
| How big does the wastage widget grow? | Owner, this session | §3.4, finding 7 |
| Point of "mark all essential" / the whole widget | Owner, this session | §3.5, finding 9 |
| What is spend by store based on? | Owner, this session | §3.6, finding 3 |
| Savings captured — product gated? | Owner, this session | §3.7, finding 2, D2 |
| What is the point of meals cooked? | Owner, this session | §3.8 |
| "Spend by category" should be "stock group" | Owner, this session | §3.9, D5 |
| Is price trends broken? | Owner, this session | §3.10, finding 1 → FU-813 (confirm in browser) |
| Consider all setups (money toggle etc.) | Owner, this session | §3.11 |
| Design / UI / UX pass | Owner, this session | §4 in full |

**Out of scope, deliberately:** the `/price-history` keep-or-cut fork (FU-703 —
it gates §5's missing widget but is an owner decision already in flight); the
waste capture flow itself (only its Reports read-surface is covered); the
dashboard's own card set beyond what Reports would inherit.

No `COVERAGE_GAPS.md` bullets flip from gap → covered as a result of this
document, because Reports had no bullets to begin with. The line at
`COVERAGE_GAPS.md:238` — *"REPORTS — feedback empty; deferred"* — should be
updated to point here.
