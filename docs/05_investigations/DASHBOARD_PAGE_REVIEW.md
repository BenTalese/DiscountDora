# DASHBOARD_PAGE_REVIEW — PO + engineering review of `/` (the dashboard)

**Date:** 2026-09-02 · **Type:** read-only assessment, no code changes.
**Scope:** `web_app/src/pages/DashboardPage.vue` (3126 lines),
`web_app/src/components/dashboard/` (`DashboardCard.vue`, `DoraScoreCard.vue`,
`DraftShopCard.vue`, `ReconcilePastMealsChip.vue`),
`web_app/src/helpers/dashboardMessages.ts`, `web_app/src/models/dashboard.ts`,
`dora_api/features/dashboard/get_dashboard_summary.py`,
`dora_api/features/dashboard/get_dora_score.py`, plus the surfaces it shares data
with (`ReportsPage.vue`, `AboutSettings.vue`, `components/AnimatedNumber.vue`,
`composables/useMoney.ts`).
**Weighting:** ~80% product, ~20% engineering — same brief as the Reports review.
**Method:** static read against `DESIGN_STYLE_GUIDE.md` (A/B/D rules),
`ENGINEERING_STANDARDS.md` (R rules), the feedback bullets at
`Feedback _ Fixes - as of [06-Jun-2026].md:48-61`, and — the thing that makes this
review different from the Reports one — **the page's own governing plan**,
`docs/04_proposals/IMPL_PLAN_DASHBOARD_REBUILD.md`. Nothing was driven live; every
finding is line-cited, and the ones needing a running app are marked and carried
as FUs or DORA_VERIFY items.

**Companion document:** `REPORTS_PAGE_REVIEW.md` (same day). The two surfaces
share five endpoints and one card shell; where a finding is genuinely shared it is
cross-referenced rather than restated, and §3.10 corrects one thing that review
attributed to Reports.

---

## 0 · Verdict in one paragraph

Reports had never been designed. **The dashboard was designed, thoroughly, and the
design is good** — `IMPL_PLAN_DASHBOARD_REBUILD.md` (2026-06-23) diagnosed the old
page in one line (*"the dashboard shows counters, not answers"*), resolved ten
decisions with the owner, shipped seven phases, and closed every row of its own
coverage table. The zones, the server-persisted per-card layout, the two-section
alert card, the fortnight calendar, the Money zone: all of it landed and all of it
works. So this review is not a missing feedback pass. **It is a drift audit**, and
the drift is of one specific kind: **the plan's structural commitments were the
ones that didn't hold.** Its curated default-visible set of 8 cards is now 13 of
17. Its Definition of Done — *"`DashboardPage.vue` is a thin composition over
`components/dashboard/*` widgets (R-001 — the 1964-line monolith is gone)"* — was
closed by extracting the card *shell* only (FU-293), and the page has since grown
to **3126 lines**, 59% larger than the monolith the rebuild set out to dissolve.
Everything added after Phase 7 — `draft_shop`, `dora_score`, `reconcile_pending` —
arrived default-on, inline, and without revisiting the curated set. **The
dashboard is not undesigned; it is un-held.**

**Answering "is the current design best, does it need polish, or is it fine as
is":** the *card-level* design is genuinely good and mostly needs protecting
(§1). The *page-level* composition has three problems that polish cannot fix —
one dataset rendered four times (§3.2), deterministic dead grid regions on every
desktop width (§4.6 — five at ≥1440px, two below it; corrected after measurement),
and a card census nobody is holding to a number (§3.1).
Underneath both sits the largest token-discipline gap in the app: **44 raw
font-sizes, 22 raw radii, 95 raw spatial values, and zero `--font-size-*`,
`--radius-*` or `--space-*` tokens in 3126 lines** (§4.3–4.4). Sequence the
composition work first; the token sweep is the last chunk, not the first (§7).

---

## 1 · What is good — protect these in any rework

The dashboard is the app's most-invested surface and it shows. These are not
faint praise; several are the standard other pages should be held to.

1. **The card layout system is real engineering, and it works.** Four fixed
   zones, per-card show/hide, within-zone reorder by tap *and* drag, drag gated
   off on touch (C13), feature gates that remove a card from the grid *and* the
   menu, and the whole layout persisted server-side on `user.dashboard_layout` so
   it follows the user across devices (`DashboardPage.vue:1473-1653`). Rendering
   order via CSS `order` with full-width zone headers forcing the band breaks
   (`:1568-1586`) is a genuinely clever way to get zones without moving markup.
   **This is the machinery the Reports review recommends Reports adopt** (FU-809).
   Nothing here should be softened.
2. **The gate seam is the app's reference implementation.** `CardDef.gate` +
   `cardAvailable()` (`:1542-1552`) is a three-line abstraction that correctly
   removes money cards on a money-off install and product cards from a
   product-less one, from both the page and the menu. FU-586's fix — re-firing
   just the gated loaders when a flag transitions on (`:2270-2281`) — is the kind
   of cold-load bug that usually ships silently forever.
3. **The loading skeleton is exactly what `B10`/`D-007` ask for**
   (`:198-219`): four real `<DashboardCard>` shells holding `AppSkeleton` lines,
   so the placeholders match the loaded cards *by construction* rather than by a
   developer eyeballing them. The primary-list card's stat-grid skeleton
   (`:399-407`) reserves the exact space its totals will land in. Reports ships
   ten centred spinners; this is the pattern Reports should copy.
4. **The empty-state inversion is the right call, and the copy is Dora's.**
   Actionable cards render a *positive* "all clear" state instead of vanishing
   (`.dora-empty-ok`, `:257-260`, `:521-524`), with a rationale comment
   distinguishing it from R-029 hide-when-off. *"Once you've restocked the same
   things a few times, I'll flag what to keep an eye on."* (`:952-955`) is `B9`
   copy at its best. A calm dashboard reads as reassuring, not broken — which was
   the plan's Phase-1 thesis and it delivered.
5. **`ReconcilePastMealsChip.vue` is the only file in this scope that uses the
   type and radius tokens properly** (`calc(var(--font-size-sm) * 1rem)`,
   `--radius-md`, `--text-muted`). It is the template for the §4.3 sweep. (It
   also has a rendering bug — §4.5.4 — which is not its fault.)
6. **The alert card's two-section design answers feedback D6 precisely**
   (`:262-339`): by-kind summary chips so you see the *shape* of what's wrong
   before the detail, then the three most-urgent rows with inline actions, then
   "See all". Every row is a real `<router-link>` with a precomputed target
   (`:1855-1862`) — not the href-less `<a>` Reports shipped.
7. **`getComputedStyle` for the donut's semantic colours** (`:1697-1702`) is the
   right instinct — read the theme rather than hardcode it. (The implementation
   never re-reads; §3.10.)
8. **Backend honesty in the score.** `_composite_of` excludes dormant components
   rather than zeroing them (`domain/dora_score.py:309-313`), the lagged window
   is skipped entirely when there's no composite to trend
   (`get_dora_score.py:74-76`), and every component ships a human `reason` string.
   The card renders dormant components dimmed with an em-dash rather than hiding
   them, so the reader can see what isn't counted. That is `R-041` coverage done
   right, and it is the only place on the page that does it (§6 finding 9).

---

## 2 · The framing: this page has a plan, and the plan is the yardstick

The Reports review's key move was dating the spec. Here the spec is recent,
detailed, and was followed — so the useful comparison is **plan vs. built**.

| The plan said | What shipped |
|---|---|
| §2.2 — default-on is **only** alerts / use-soon / suggestions / cookable / week-ahead / primary-list / savings / restock (**8 cards**) | **13 default-on** on a money+products install; `use_soon` was later cut, and `draft_shop`, `budget`, `best_deals`, `dora_score`, `reconcile_pending` are all default-on |
| §6 DoD — *"`DashboardPage.vue` is a thin composition over `components/dashboard/*` widgets (R-001 — the 1964-line monolith is gone)"* | **3126 lines**; 13 of 17 cards still inlined; `components/dashboard/` holds the shell + 3 small cards |
| Phase 0 — *"Extraction scaffolding … **the single most important structural move**"* | Deferred out of Phase 0 → Phase 2 → FU-293, which resolved by extracting the shell alone |
| Phase 0 — *"Dashboard dark-mode / token audit (D2) — sweep the ~640 lines of scoped SCSS for any value bypassing tokens"* | The scoped SCSS is now ~970 lines with **zero** `--font-size-*` / `--radius-*` / `--space-*` tokens (§4.3–4.4). The audit's own finding class was never closed |
| Phase 5 — quick actions: *"Add item · Add to list · Log price · (Scan, gated behind `scanning_enabled`)"* | Three built; Scan not built (defensible — scanning is off by default) |
| Charter cross-check — *"Anti-creep — net default-visible card count held roughly flat"* | Cut 4 counters, added 9 cards. The grid is **31% larger than the 13-card "kitchen sink"** the rebuild was called in to fix |

Two things follow, and they set the shape of every recommendation below.

**First: the failures are all failures of *holding*, not of designing.** Nobody
made a bad call. The curated-8 decision had no mechanism — no test, no comment in
`CARD_DEFS`, no line in the plan saying "adding a default-on card reopens §2.2" —
so three later features each added one card, each defensibly, and the set drifted
to 13 without a single decision being wrong. Same for the de-monolith: FU-293 did
real work (the shell *is* extracted and *is* shared), closed itself honestly, and
the DoD it was standing in for quietly stopped being tracked.

**Second: this is the fifth sighting of a pattern already queued for promotion.**
The 2026-09-01 close-gate flagged "componentisation-not-finished" for an ADR; the
Reports review found a fourth instance the same week. **This is the strongest
instance yet, because here the componentisation goal was written into a
Definition of Done and closed by a partial.** That is no longer a code smell — it
is a process gap with a name, and §8 D6 / FU-829 says so.

---

## 3 · The questions this page raises, answered

No owner questions were supplied for this surface, so these are the twelve the
page raises on a close read, in rough value order.

### 3.1 Is 17 cards too many? — The number is not the problem. Nobody owning the number is the problem.

The census, from `CARD_DEFS` (`:1289-1330`):

| Zone | Cards | Default-on | Opt-in | Gated |
|---|---|---|---|---|
| Act now | attention, draft_shop, suggestions | 3 | — | — |
| Today | cookable, meal_plan, primary_list, restock, calendar | 4 | calendar | — |
| Money | savings, budget, best_deals, price_drops, spend_trend, pantry_value | 3 | price_drops, spend_trend, pantry_value | all 6 |
| Your kitchen | dora_score, reconcile_pending, stock_items | 3 | — | — |
| | **17** | **13** | **4** | **6** |

Seventeen registered cards behind a working opt-out system is *fine* — that is
what the opt-in machinery is for, and it is Anti-creep's escape hatch. **Thirteen
default-on is not fine**, because the plan resolved that number to 8 with the
owner and the drift happened without anyone reopening the decision. The three
cards that pushed it over are all recent and all shipped `defaultHidden`-less:
`draft_shop` (FU-351), `dora_score` (P8-08), `reconcile_pending` (FU-317). Each is
a good card. Together they are 60% of an unplanned expansion.

**Recommendation:** re-derive the default set once, deliberately, then *encode* it
— a one-line comment in `CARD_DEFS` naming §2.2 as the authority, so the next
card added has to argue with something. My read of the curated set, updated for
what's since shipped: **attention · draft_shop · cookable · meal_plan ·
primary_list · savings · stock_items · reconcile_pending** (8), with `budget`
folded into `savings` (§3.5), `suggestions`, `restock`, `best_deals` and
`dora_score` demoted to opt-in. → **FU-817** (owner call — this is a product
judgement about what a new user should see, not a cleanup).

### 3.2 What is the single biggest waste of dashboard area? — The meal plan, rendered four times.

`summary.meal_plan.upcoming_entries` — one array from one endpoint — feeds four
separate renderings:

| Surface | What it renders | Source |
|---|---|---|
| Hero line (`:1752-1769`) | "Tomorrow: Chicken curry for 4." | `nextEntry` = `upcoming_entries[0]` |
| **Next to cook** (`:566-621`) | Top 3 upcoming, deduped by recipe, ready/missing badge | `nextToCook` over `upcoming_entries` |
| **The week ahead** (`:784-830`) | "Next up" callout (**the same entry as the hero line**) + a 7-day pip strip | `nextEntry` + `weekStrip` over `upcoming_entries` |
| **This fortnight** (`:833-914`) | 14-day dot grid + per-day detail | `/alerts/upcoming` — **a different endpoint** |

On a default desktop install with one meal planned for tomorrow, that meal appears
**four times above the fold**: in the hero sentence, as a Next-to-cook row, as the
week-ahead "Next up" callout, and as a pip in the week-ahead strip. Enable the
fortnight calendar and it is five.

Worse, the fourth surface uses a **different query**. `weekStrip` builds days 0–6
from `/dashboard/summary`'s 7-day window; `calendarCells` builds days 0–13 from
`/alerts/upcoming`. The two windows overlap by seven days, and nothing guarantees
they agree — different handlers, different date boundaries (the summary uses
`household_today()`, `R-021`-correct; the calendar trusts `u.start` from the other
endpoint). If they ever diverge, the same week renders two ways on one screen with
no way for the user to tell which is right. `R-003`.

**Recommendation:** the week strip and the fortnight calendar are one card
(`D-012` — a 14-day dot grid and a 7-day pip strip are the same widget at two
zoom levels; the plan itself noted *"possible future consolidation with the
week-strip"* at Phase 6). Keep **Next to cook** — it is the only one of the four
that answers a question (*what do I cook, and can I?*) rather than restating the
calendar. Drop the week-ahead "Next up" callout, which is the hero line in a box.
→ **FU-818** (owner call — it deletes a card the owner asked for at L61).

### 3.3 Does the hero earn its height? — Not on a default install. It is four stacked bands before the first card.

Top-to-bottom on a normal desktop load: hero card (72px mascot + greeting +
one-line summary + Cards button, ~120px) → quick-action row (~48px) → the "Dora
says" welcome band (mascot + message + hint, ~80px) → then the first zone header,
then cards. Roughly **280px of chrome before any data**, of which the greeting
("Good afternoon, Ben") and the hint-of-the-day are decoration.

The individual pieces are good — the welcome-message system is exactly what
feedback D1c/d/e asked for, the pools are well-written, and the "Dora says" yellow
treatment was explicitly requested (L55). The problem is that **three of the four
bands are the same register**: a friendly greeting, then a friendly one-liner,
then a friendly message plus a friendly hint. Nothing in the stack is the answer
to a question.

And `heroLine` (`:1752`) is the one band that *does* carry signal — "3 items are
out of stock" — which the Needs-your-attention card and the Pantry donut both
also say, on the same screen, from the same numbers.

**Recommendation:** merge the greeting and the welcome band into one row (the
mascot appears twice today, at 72px and 40px, ~200px apart). Give `heroLine` the
Reports-review treatment (§4.10.1 there): make it the page's lede and let it be
the *only* place the out-of-stock count is prose. Keep the hint pool — it is the
app's best discoverability surface — but move it below the fold or into the
Cards menu, where the person who wants to learn the app already is.

### 3.4 On a money-off install, is the dashboard clean? — Almost. Two leaks, one of them arithmetic.

Credit first: this is the surface that *does* gate money properly, and it is the
model FU-816 wants Reports to copy. All six Money-zone cards carry `gate: 'money'`
or `'products'`, gated cards vanish from the grid and the menu, the "Log price"
quick action is `v-if="moneyEnabled"` (`:116`), and every money loader
early-returns rather than fetching (`:2068-2106`). With money off the whole Money
zone header collapses (`zoneHasVisibleCards`). That is three seams, correctly.

Two things still get through:

1. **Kitchen health weights its composite with money data the household opted
   out of.** `get_dora_score.py:115` calls `GetBudgetStatusHandler` unconditionally;
   that handler does **not** check the money flag (`budget.py:215-225` computes
   period boundaries *"even when the feature is off"* by design, for the passive
   spend figure). So on an install with money off but a budget amount still on
   `AppSetting`, `has_budget=True`, `budget_over_pct` is computed, and the Budget
   component contributes a fifth of the composite. The card then renders a
   **"Budget — No budget set — this component is skipped"** row with a **"Set a
   budget →"** link to `/settings/money`. This is `R-058`, textbook, with the
   precedent one directory away: `get_buy_verdict.py:840` refuses outright via
   `money_features_enabled(repo)` for exactly this reason (ADR-055). The endpoint
   has no gate at all. → **FU-823**.
2. **The hint pool advertises money and product features regardless of the
   flags.** `dashboardMessages.ts:87-89` ships *"Linking a product to a stock item
   lets me track its price over time"*, *"Your saved products power the 'Best
   deals' card"*, and *"Set a grocery budget and I'll quietly track spend against
   it for you"* into a rotation shown to every install. A money-off household gets
   told, one day in fifteen, to set a budget it has switched off. Fix is small —
   tag hints with an optional gate and filter the pool.

Note also that the client's `useMoneyEnabled` layers *install* + *per-user*
opt-in, while the server's `money_features_enabled` is install-wide only. So a
user who personally opted out on a money-enabled install still has their Kitchen
health composite weighted by budget. Same fix.

### 3.5 Budget and Savings are two halves of one sentence, in two cards.

`savings` (`:960-1004`) renders "You've saved **$128** vs RRP, last 30 days · on
$1,004.37 spent across 6 shops", with a Month/Year/All toggle. `budget`
(`:434-502`) renders "**$412** of $500 · $88 left" with a progress bar, plus the
budget-defense swap bullet. Both are `gate: 'money'`, both default-on, both
`col-lg-6`, and they sit adjacent in the Money zone by default.

They are the same story — *what did this cost, and how am I doing* — split so that
neither is complete. Savings has a period toggle; Budget has a fixed period from
settings, so the two can be showing different windows side by side. Budget knows
the spend figure; Savings recomputes spend from a different endpoint
(`savings.total_spent`). On a household with no budget set, the Budget card
degrades to *"$412 spent so far. Set a target in Settings…"* — which is a spend
figure, i.e. the thing Savings is already reporting.

**Recommendation:** one **Money** card — spend as the headline (with the budget
bar when a target exists), saved-vs-RRP as the supporting line, one period
control. That is the Reports review's §4.10.3 recommendation ("delta is the hero;
level is the support") applied here, and it takes the Money zone's default-on
count from 3 to 2. The vs-RRP baseline question is already open as **FU-810** —
this consolidation is downstream of it, so do them together.

### 3.6 Best deals and Price drops are one card wearing two hats.

Both are `gate: 'products'`. Both render the identical `.dora-deal-row` anatomy —
36px product image, name, store, now/was prices, a red `% off` badge (`:638-679`
and `:1081-1122`, ~40 lines of near-duplicate template). The difference is the
question: Best deals = *biggest % off RRP right now*; Price drops = *at a
server-verified new low*. Price drops is the honest one (that was the point of
FU-296 — *"only claim 'new low' when true"*). Best deals is the vs-RRP metric the
Reports review argued rewards buying things you don't need.

A user with products enabled and both cards on sees two visually identical lists
of discounted products, differing only in ranking, with no explanation of why
there are two.

**Recommendation:** one **Deals** card with the new-low rows first and a
`% off` row beneath, or — cleaner — keep Price drops and cut Best deals, since
the new-low signal is the one Dora can stand behind. → **FU-819** (owner call;
Best deals is an original-spec P12 card, see §9).

### 3.7 Is Kitchen health honest and useful? — Honest, yes. Useful, mostly. Its rendering is broken in every theme.

The score is the best-engineered widget in this scope (§1.8): five components,
dormant signals excluded rather than zeroed, per-component reason strings, a
remediating action link per component, a 7-day trend arrow. It also *avoids* the
trap the composite invites — it never shames, and `actionLinkFor` deliberately
returns `null` for waste rather than linking a page that no longer exists
(`DoraScoreCard.vue:151-160`, with the reasoning written down).

Two real problems:

1. **The card renders entirely on design tokens that do not exist.**
   `--dora-text`, `--dora-positive`, `--dora-negative`, `--dora-primary`,
   `--dora-muted-bg`, `--dora-positive-bg`, `--dora-negative-bg` are referenced
   throughout its `<style>` block and **declared nowhere in `web_app/src/css/`**
   (only `--dora-disc-bg` and `--dora-halo*` exist). So every colour on the card
   is its hard-coded hex fallback: `#228b22` green, `#b43c3c` red, `#f5c462`
   yellow, `#666` grey, `rgba(0,0,0,0.06)` bar track. In all ten themes,
   light and dark. The "fair" bar and the component action links render **yellow**
   where the app's action colour is green; the bar track is a black wash that
   disappears on a dark surface. And `.dora-score-hero__number` is
   `color: var(--dora-text)` with **no fallback**, so that declaration is invalid
   at computed-value time and the score's headline number silently inherits
   whatever the card gives it. This is `R-060` — the rule written for exactly this
   failure mode, established 2026-08-28 — and `R-002`. → **FU-822**.
2. **"Stocktake" is scored as a *rate*, which punishes a well-run pantry.** The
   component is *% of stock items whose `last_checked_at` falls in the last 30
   days* (`get_dora_score.py:186-191`). A household that did a full stocktake 40
   days ago and has changed nothing since scores 0 on that component and drags the
   composite down by a fifth — for having a stable, accurate pantry. The reason
   string even says it out loud: *"Nothing has been checked in the last 30 days."*
   Compare the other four components, which all measure *events that went wrong*.
   This one measures *an activity not performed*. It is the one component that
   isn't a health signal; it's a nag. Worth an owner look, not an FU — the fix is
   a threshold judgement (score against the install's configured stocktake
   cadence rather than a hard 30 days) and it belongs to whoever owns the score.

### 3.8 What does a fresh install see? — The best answer of any page in the app.

Genuinely: this is where the plan's Phase-1 thesis pays off. A brand-new install
gets the hero, three quick actions, the skip-wizard banner (for 24h), and then
cards that say *"All clear — nothing needs your attention right now"*, *"Nothing
to suggest right now — you're on top of things"*, *"Nothing planned for the next
week. Plan a meal →"*, *"Once you've restocked the same things a few times, I'll
flag what to keep an eye on."* Compare Reports' fresh install: eleven 240px empty
boxes, ~3000px of nothing. The contrast is the whole argument for `R-014`.

Two nits. `B9`'s anatomy is *"feature icon (32–48px, muted) · one-line
what-goes-here · optional one primary action"* — the "all clear" states have an
18px check icon, the rest have no icon at all, and only two carry an action. And
`B9`'s second clause — *"don't offer an action that lands on another
empty/data-gated surface on a fresh account"* — is breached by Best deals' *"Hunt
for deals →"*, which on a product-less install opens a product search with nothing
in it. Small, and this card is `gate: 'products'` so it's a narrow window.

### 3.9 Does the Cards menu get found? — Almost certainly not, and it is the page's best feature.

Per-card show/hide, per-zone reorder, drag on desktop, tap everywhere,
server-persisted across devices — behind a **dense ghost button labelled "Cards"**
in the hero's top-right (`:24`). `variant="ghost" dense` is the app's tertiary
treatment; it reads as chrome. There is no first-run pointer at it, no empty-state
mention, and the only discoverability is one entry in a 15-item hint rotation
that surfaces roughly once a fortnight: *"Reorder dashboard cards from the Cards
menu — **drag** the ones you check most to the top."* — advice that is wrong on
mobile, where `cardDragEnabled` is false by design (`:1621`).

`R-012` (working features stay visible). The fix is cheap: make it a `secondary`
button with the "Customise" label, and fix the hint to name the tap controls.
Folded into §4.9's moves rather than its own FU.

### 3.10 Does the stock donut recolour on a theme switch? — No, and the comment claiming it does is the one Reports copied.

`stockSegments` (`:1678-1710`) reads the semantic tokens off
`document.documentElement` inside a `computed`, with the comment *"Read the
semantic-* tokens off the document so the donut recolours when the user switches
theme without a full reload."* The computed's reactive dependencies are
`summary`, `stockInStockCount`, `stockLowLink` and `stockOutLink` — **none of
which a theme switch touches.** `getComputedStyle` is not reactive. So the palette
is sampled once and frozen: switch light→dark while sitting on the dashboard and
the donut keeps its old-theme greens and reds until the summary refetches.

**Correction to the Reports review:** its finding 11 treated Reports'
`themeTick` — declared, read, never incremented — as a Reports defect. It is the
same defect, and this is where it came from. Reports' author saw the dashboard's
frozen-palette read, recognised it needed invalidating, added a `themeTick` ref to
do it, and never wired the increment. The dashboard never had the ref. **One fix
serves both surfaces**: a shared `useThemePalette()` that exposes a reactive
version counter bumped by whatever already applies the theme class. → **FU-824**,
which supersedes the Reports-side half of FU-814's scope for this item.

### 3.11 Are the dashboard's money figures right? — Three of them are rounded to the nearest dollar.

`AnimatedNumber` formats as `prefix + n.toFixed(decimals) + suffix` with
**`decimals` defaulting to 0** (`AnimatedNumber.vue:24,41-43`). The dashboard
passes `:prefix="dashCurrencySymbol"` and **no `decimals`** at three money sites:

| Site | Value | Renders | Should render |
|---|---|---|---|
| `:385` | `primaryListStats.remaining` | `$47` | `$47.30` |
| `:394` | `primaryListStats.savings` | `$4` | `$3.80` |
| `:992` | `savings.total_savings` | `$128` | `$128.45` |

So the app's flagship money claim — **"You've saved $128"** — is rounded, and sits
directly above `.dora-savings-spent`, which *does* go through `formatMoney` and
renders *"on $1,004.37 spent across 6 shops"*. **Two number formats, one card, one
currency.** No thousands separator either: a $1,234.56 saving renders `$1235`.

And `currencySymbol()` is being used outside its contract. Its own docstring says
*"Used by `q-input` `prefix=` — Quasar's input takes a plain string, not a
formatted value"* (`useMoney.ts:94-98`). It returns only the symbol; `formatMoney`
owns *placement*. On a `fr-FR` install `formatMoney(12.34)` gives `12,34 €` while
the dashboard renders `€12`. `D-006` (one formatting authority), `R-003`, and a
Charter-Honesty problem on the number the whole Money zone exists to show.
→ **FU-821**. The fix is either `:decimals="2"` plus a formatted-string prop, or
better: give `AnimatedNumber` a `format` function prop and hand it `formatMoney`.

### 3.12 Do the relative dates say the right day? — Not west of Greenwich.

`formatRelativeDay` (`:1804-1816`) does `new Date(iso)` on a `YYYY-MM-DD` string.
Per spec that parses as **UTC midnight**; `setHours(0,0,0,0)` then normalises to
local midnight *of whatever local date that instant fell on*. East of Greenwich
(Australia, the shipping default) UTC midnight is the same local date and it
works. West of Greenwich it is the **previous** local date, so every relative day
is off by one: tomorrow's dinner reads **"Today"**, today's reads "Yesterday"
(falling through to a formatted date since `diff` is negative).

Four call sites, all user-facing: the hero line (`:1759`), Next to cook's
"Tomorrow lunch" (`:1910`), The week ahead's "Next up" meta (`:797`), and the
fortnight calendar's day header (`:870`).

The same file already contains the correct parser — `parseLocalIso` (`:2154-2157`)
splits the string and constructs a local date — used only by the calendar grid. So
the page holds both the right implementation and the wrong one, and the wrong one
has four times the reach. `weekStrip` is unaffected (it compares ISO strings, the
correct approach). → **FU-820**. The fix belongs in `useDateFormat` /
`helpers/weekDates.ts` next to `localTodayIso`, not inline again.

### 3.13 Considering all setups

| Setup | What the dashboard does |
|---|---|
| **Money on, products on** (dev default) | All 17 available, 13 default-on. Dead grid regions at every desktop width — 5 at ≥1440px, 2 at 1024–1439 (§4.6). |
| **Money off** | Money zone collapses entirely — correct. Two leaks: Kitchen health's budget row + weighted composite (§3.4.1), money hints in the rotation (§3.4.2). |
| **Products off / no products** | `best_deals` + `price_drops` vanish from grid and menu — correct, and the reference implementation for §2.4. |
| **Per-user money opt-out, install money on** | Cards gate correctly (client layers both). The **dora-score endpoint does not** — composite still weighted by budget (§3.4). |
| **Fresh install** | The app's best first-run page (§3.8). |
| **All cards hidden** | Honest banner pointing back at the Cards menu (`:1137-1141`). Good. |
| **`/dashboard/summary` fails** | Red banner, and then **nothing** — `v-if="loading && !summary"` is false, `v-else-if="summary"` is false, so the grid renders empty. Copy says *"Try refreshing"*, and the refresh button was deliberately removed by D3. Honest but a dead end; the banner should carry a retry that calls `loadAll`. |
| **Any other loader fails** | Silent. All eleven slot loaders swallow to `null`/`[]` and render the card's *empty* state, so a failed fetch reads as "nothing here yet" — the same honesty failure as Reports finding 8, eleven times over (§4.7). |
| **Mobile (360px)** | Cards stack (`col-12` below `sm`); quick actions span the row; drag off, tap reorder on. Phase 7 did its job. The 44px tap floor is not met by the `size="sm"` row buttons or the 11.5px range chips (§4.8). |
| **Tablet (768px)** | `attention` is `col-12 col-lg-6` — no `col-sm-6` — so it is full-width on tablet while its zone-mates are half. Every other card has the `sm` step. Looks like an oversight. |

---

## 4 · Design, UI and UX pass

### 4.1 The verdict, split in three

- **The card *interiors* are good.** Real hierarchy, real actions, real empty
  states, good copy. Where Reports needed a point of view, these cards have one.
  Protect them.
- **The page *composition* is not good, and it is arithmetic, not taste.**
  Deterministic dead regions on every desktop width — five at ≥1440px, two below
  (§4.6, corrected after measurement) — one dataset rendered four times (§3.2),
  280px of chrome before the first card (§3.3).
- **The *token discipline* is the app's worst, and it is invisible from the
  rendered page.** Zero scale tokens in 3126 lines, two undeclared token families
  producing real rendering bugs (§4.5.4, §3.7.1). This is the cheapest work here
  in judgement and the largest in line count — which is exactly why it goes last
  (§7), after the card set stops moving.

### 4.2 The de-monolith that stopped, and what it costs now

`components/dashboard/` holds four files: the shell, and three of seventeen cards
(`DoraScoreCard`, `DraftShopCard`, `ReconcilePastMealsChip`). The other **fourteen
card bodies live inline** in `DashboardPage.vue`, along with their ~970 lines of
scoped SCSS. The plan's DoD called for the opposite.

The concrete costs, all visible in this review:

- **You cannot review a card.** Every finding above required reading a 3126-line
  file to isolate one card's ~40 lines of template, its computed properties ~600
  lines below, its loader ~400 below that, and its CSS ~700 below that. Four
  regions of one file per card.
- **Duplication survives because it isn't adjacent.** `.dora-deal-row` is rendered
  by two cards 400 lines apart with near-identical markup (§3.6). `.dora-cook-row`
  is shared by Next-to-cook and Restock radar via a modifier class — good — but
  only because they happened to be built together.
- **The three extracted cards drifted immediately.** `DoraScoreCard` invented a
  whole token family (§3.7.1); `ReconcilePastMealsChip` uses the *correct* tokens
  and is therefore the only visually different thing in the grid (§4.5.4);
  `DraftShopCard` is clean. Three files, three different token conventions —
  because there was no fourth to establish a norm.
- **The page grew 59% during a project whose stated purpose was to shrink it.**
  1964 → 3126 lines.

**The shell itself is good** and should not be touched: `DashboardCard.vue`
renders a real `<router-link>` when `to` is set so the whole card is one
keyboard-focusable target, handles the `#action` slot's scope correctly with
`:deep()`, and carries its own `prefers-reduced-motion` guard. Note for the
Reports side: this is the component Reports forked byte-identically (FU-814), and
its `18px` radius / `18px 20px 20px` padding are off-scale in *both* files —
FU-811 owns that decision.

→ **FU-829**: finish the extraction *and* write the ADR the pattern has now earned
five sightings of.

### 4.3 Typography: 44 raw font-sizes, zero tokens, eight below the hard floor

`A2` requires the `--font-size-*` unitless ratios as
`calc(var(--font-size-x) * 1rem)`. The page uses **44 raw literals and zero
tokens**. (Reports: 17 and zero. This is the bigger offender, and the one Reports
was told to match.)

The eight below the 12px floor — `D-003`, *"Nothing smaller, ever"*:

| Class | Literal | px@16 | Role | Verdict |
|---|---|---|---|---|
| `.dora-strip-more` (`:2882`) | `0.65rem` | **10.4** | "+2" — a **count the user reads** | below floor, and it carries a value |
| `.dora-cards-menu-zone` (`:2390`) | `0.7rem` | **11.2** | Zone header in the Cards menu | below floor |
| `.dora-strip-dow` (`:2857`) | `0.7rem` | **11.2** | "MON" in the week strip | below floor |
| `.dora-range-chip` (`:2615`) | `0.72rem` | **11.5** | **Interactive control label** (Month/Year/All) | below floor; `B2` says never under 14 on a control |
| `.dora-zone-label` (`:2378`) | `0.72rem` | **11.5** | Zone band header — a page landmark | below floor |
| `.dora-next-up-label` (`:2538`) | `0.72rem` | **11.5** | "NEXT UP" eyebrow | below floor |
| `.dora-cal-legend` (`:2697`) | `0.72rem` | **11.5** | The calendar's **legend** (`D-013`) | below floor; the decoder ring is the least legible text on the card |
| `.dora-cal-group-label` (`:2779`) | `0.72rem` | **11.5** | "MEALS" / "EXPIRING" | below floor |

Plus the donut's SVG text: `font-size: 7.5px` and `3px` in a 36-unit viewBox
rendered at 132px, so ~27.5px and **~11px** effective — the "items" label under
the count is also under the floor. (Stated properly because "3px text" would be
wrong; the viewBox scales it.)

And the off-scale-but-legal remainder, which is most of the rest: `1.5rem` (24.0 —
should be `--font-size-2xl`, coincidentally exact), `1.9rem`/`2.2rem` (30.4/35.2 —
hero numbers, `--font-size-3xl` is 30), `1.6rem`, `1.3rem`, `1.25rem`, `1.05rem`,
`0.95rem` ×5, `0.9rem` ×3, `0.85rem` ×9, `0.82rem` ×5, `0.8rem` ×3, `0.78rem` ×3.
Nine declarations at `0.85rem` (13.6px) where `--font-size-sm` is 14 — that single
value accounts for a fifth of the file's type and is 0.4px off the token.

**Zone band headers at 11.5px are the finding worth acting on beyond the sweep.**
The zone system is the page's information architecture; its labels are rendered
smaller than any other text on the screen. `A2` puts a section header at 20px
bold. They are currently 11.5px/700 uppercase at `opacity: 0.8` on
`--text-secondary` — which is also a `D-002` contrast question worth measuring,
since 0.8 opacity on an already-muted token is exactly the compounding the DR-1
retune was about.

### 4.4 Spacing and radius: 95 spatial literals, 22 radii, six distinct corner values

**Zero `--space-*` tokens. Zero `--radius-*` tokens.** In 3126 lines.

Radius (`A4`'s ladder is 4 / 6 / 10 / 16 / 22 / pill; `D-017`: *"One element type =
one radius and one padding value app-wide"*):

| Value | Count | Used for | On scale? |
|---|---|---|---|
| `999px` | 6 | dots, pills, range toggle | yes — but should be `--radius-pill` |
| `10px` | 7 | list rows, tiles, calendar cells, welcome mascot | yes (`--radius-lg`) — though `--radius-lg` is the *card* radius, and these are rows inside cards |
| `12px` | 4 | stat tiles, next-up block, empty states, cal detail | **no** |
| `14px` | 2 | hero mascot, welcome band | **no** |
| `18px` | 1 | the hero card | **no** (and shared with `DashboardCard` — FU-811) |
| `3px` | 1 | the attention severity bar | **no** |

Spacing: 95 declarations across 15 distinct px values. On-scale: 4, 8, 12, 16, 24.
Off-scale: **3, 5, 6, 9, 10, 14, 18, 96** — roughly 57 of the 95 declarations.
`A3` names two of these explicitly: *"No off-scale margins/paddings (no 5px, 13px,
**18px**)"*. The page has both a `5px` and an `18px`.

Also: the card grid is `q-col-gutter-md` (16px) where `B4` specifies `--space-6`
(24px) between sibling cards, and the page padding is `24px 24px 96px` — 96 is not
on the scale (it is 4×24, so `--space-12` ×2 or a named safe-area value would do).

None of this is visible as *ugly*. It is visible as **"assembled from snippets"**,
which is `D-017`'s stated rationale, and it is why the page cannot inherit a
future scale change.

### 4.5 Colour: one inverted ladder, one contradiction, one undeclared family

1. **The surface ladder is inverted, in 12 places, and this is where Reports
   copied it from.** `--surface-elevated` is used as the background for
   `.dora-stat`, `.dora-empty`, `.dora-range-toggle`, `.dora-spend-row`,
   `.dora-cal-cell`, `.dora-cal-detail`, `.dora-suggest-row`, `.dora-strip-day`,
   `.dora-alert-chip`, `.dora-attn-row`, `.dora-cook-row`, `.dora-deal-row` — all
   of which sit **inside** a `--surface-component` card. `A1` reserves
   `--surface-elevated` for *"menus, popovers, a card that floats above other
   cards"* and puts wells and inset regions on `--surface-sunken`; `B11` specifies
   sunken for zebra. Every nested row on the dashboard is painted as if floating
   above the card containing it. The shopping list gets this right. Twelve
   selectors, one find-and-replace, and it is the single change that would most
   improve the page's sense of depth.
2. **Pantry value up is green; spend up is red — and they are the same fact.**
   `.dora-pantry-delta.is-up { color: --c-ok }` / `.is-down { color: --c-bad }`
   (`:2686-2691`): a rising pantry value renders **positive green**. Meanwhile
   Reports' `.yoy-up` renders rising spend as **negative red**. Both numbers mean
   "more dollars in the household's food system", and the app colours them
   opposite ways on two screens. Beyond the internal contradiction, `A1` defines
   negative as *"Out-of-stock level, destructive actions, errors"* — a pantry
   getting cheaper is not an error, and a pantry getting more valuable may just be
   hoarding. The Reports review's recommendation applies verbatim: use
   `--text-primary` with a directional arrow, and reserve semantic colour for
   **budget**, which has an actual threshold to breach. (Budget does this
   correctly today — `text-negative` only when `over_budget`.)
3. **`--brand-primary` on ~15 decorative card icons.** Inherited from
   `DashboardCard.vue:73-75`, so it is a shared decision with Reports (same
   finding, same fix, one place). `A1` reserves brand primary for *"the single
   primary CTA per view"*. On this page there is a genuine cost: the quick-action
   bar's three `variant="secondary"` buttons and `DraftShopCard`'s primary "Draft
   my shop" button are competing for attention with fifteen green icons that mean
   nothing.
4. **`--border-subtle` is not a token, and the reconcile chip therefore has no
   border.** `ReconcilePastMealsChip.vue:40` sets
   `border: 1px solid var(--border-subtle)`. That custom property is referenced in
   five files (`MealReconcileLog.vue:286`, `ReportsPage.vue:1136` — which at least
   passes a fallback — `BaseSelect.vue:303`, `TriStateFilter.vue:275`, and this
   one) and **declared in none**. Per `R-060`'s stated mechanism, an undefined
   custom property with no fallback makes the whole declaration invalid at
   computed-value time, so `border` falls back to its initial value:
   `border-style: none`. **The chip renders borderless and shadowless in a grid of
   bordered, elevated cards** — which is exactly the "looks off and nobody can say
   why" symptom `R-060` was written for after the cook-mode header. → **FU-822**,
   with the other four call sites.
5. **The page-local `--c-*` alias layer is defensible but has one stale
   comment.** `.dora-dash` declares 14 aliases (`:2292-2312`) mapping global
   tokens to page-local names. It is called out in FU-747 as R-002 drift. The
   aliases do all resolve to real tokens, so nothing breaks; the cost is that a
   reader must hold a second vocabulary, and that scoped child components cannot
   see them — which the code already knows (`:2386-2388` explains that the Cards
   menu teleports out of `.dora-dash` and must use the global token). That comment
   is the argument against the alias layer, written in the file that has it.

### 4.6 Layout: deterministic dead regions on every desktop width (5 at ≥1440px, 2 below — corrected)

> **⚠️ CORRECTED 2026-09-02 (chunk 2, measured in a browser).** The count below
> is right at **≥1440px** and **wrong below it**. The table assumes `col-lg-*`
> engages at the app's own ≥1024 "desktop" breakpoint (A8); **Quasar's `lg` is
> ≥1440**, so below that only the `col-sm-*` step applied. Measured with the old
> classes re-applied in a real browser:
>
> | Width | Dead regions |
> |---|---|
> | 1920px | **5** |
> | 1440px | **5** |
> | 1280px | **2** |
> | 1024px | **2** |
> | 768px | **2** |
>
> So the defect was real at every width, but "five on a default desktop"
> overstates it for the 1024–1439 range that most laptops sit in — there it was
> two (Next-to-cook and Best-deals, the odd-numbered tails). The zone table below
> describes the ≥1440 case; read it as such.
>
> **The mistake is worth more than the correction.** Chasing it turned up that
> the dashboard was **the only surface in the app reaching for `col-lg-*`** to
> mean "desktop" (2 usages against 14 for `col-md-*`), so its intended desktop
> layout never engaged on an ordinary 1280px laptop: "Needs your attention" and
> "The week ahead" carried no `col-sm-*` step and therefore rendered
> **full-width** there, which is certainly not what their author intended. Logged
> as **FU-836**. Fixed set: **0 dead regions at 375 / 768 / 1024 / 1280 / 1440 /
> 1920**, measured.

This is the strongest design finding in the review because it is arithmetic, not
opinion. The grid is a flex row with per-card `order`; each card's width comes
from its Quasar column classes. Walking the **default** visible set at ≥1440px
(see the correction above), zone by zone, in `order` sequence:

| Zone | Cards in order (lg width) | Rows as they pack | Dead area |
|---|---|---|---|
| **Act now** | attention (6), draft_shop (6), suggestions (6) | `6+6` · `6+▨` | **one half-width gap** |
| **Today** | cookable (6), meal_plan (**8**), primary_list (6), restock (6) | `6+▨` (8 won't fit beside 6) · `8+▨` · `6+6` | **a half gap and a third gap** |
| **Money** | savings (6), budget (6), best_deals (6) | `6+6` · `6+▨` | **one half-width gap** |
| **Your kitchen** | dora_score (**4**), stock_items (**4**) | `4+4+▨` | **one third-width gap** |

That is **five dead regions at ≥1440px** (two at 1024–1439 — see the correction
at the top of this section) — not an edge
case, not an odd-count coincidence, but the deterministic consequence of the
default card order and the width classes. `D-011`: *"a lone card goes full-width
(or the grid packs); no card beside dead air."* `B4`: *"No lone half-width card
beside dead air."*

The Today zone is the worst: `meal_plan` at `col-lg-8` cannot share a row with
anything else in a zone of `col-lg-6`s, so it strands a card above it *and* a
third beside it. And Your kitchen strands a third-width by default because
`reconcile_pending` — the card that would complete the 4+4+4 row — is
hide-when-empty and therefore usually absent.

**FU-631 #3 already owns this**, describing it as *"a lone `col-lg-6` card at the
end of a zone"*. That understates it by four regions; I have amended that FU with
the arithmetic rather than opening a duplicate. Its analysis of the fix stands:
because widths are static classes and order is dynamic, "make a lone last-in-zone
card full-width" needs per-zone odd-count logic, not a CSS rule. The cheaper
option worth weighing first: **give every card the same width class** and let the
grid pack — the only cards that genuinely want more room are `meal_plan` and
`calendar`, and `calendar` is already `col-12`.

Other layout notes: `attention` is missing its `col-sm-6` step (§3.13);
`.dora-attn-name` has `max-width: 220px` with `text-overflow: ellipsis`, so long
item names truncate at a fixed pixel width regardless of available space; and the
week strip and calendar grid are both `repeat(7, minmax(0,1fr))` with `gap: 6px`,
which at 360px gives ~44px cells — right at the `D-004` floor for the calendar's
tappable cells, and the strip's `+2` label inside them is 10.4px (§4.3).

### 4.7 Loading, empty and error states

- **Loading is right** (§1.3) — this is the app's reference skeleton.
- **Empty is right** (§3.8) — modulo `B9`'s missing icons.
- **Error is the gap, eleven times.** Every slot loader catches and assigns
  `null`/`[]` with a comment explaining the card will show its empty state:
  `loadAlerts` (`:1868-1871`), `loadBestDeals`, `loadPrimaryListDetail`,
  `loadBudget`, `loadSwapSummary`, `loadSavings`, `loadSpendByStore`,
  `loadPantryValue`, `loadPriceDrops`, `loadKeepsRunningOut`, `loadUpcoming`. So a
  500 on the savings endpoint renders *"Finish a shop and I'll tally what you
  saved vs RRP"* — telling a user who has shopped for months that they haven't
  shopped. Same class as Reports finding 8, and here it is deliberate and
  documented, which makes it a design decision to revisit rather than an
  oversight. The honest shape is a third state per card: loading / empty / **"couldn't
  load this one"** with a retry.
- **The summary failure path renders nothing but a banner** (§3.13), and its copy
  names an affordance D3 removed. Add a Retry to the banner calling `loadAll`.

### 4.8 Accessibility

Better than Reports, and still short of `A6`. Counted across the page: **6
`aria-*` attributes, 7 `role=` attributes, 0 `:focus-visible` rules, 1
`outline: none`.**

- **Zero focus-visible styling in 3126 lines**, and the one `:focus` rule that
  exists actively removes the indicator: `.dora-donut-seg--link:hover,
  .dora-donut-seg--link:focus { opacity: 0.8; outline: none; }` (`:2466-2470`).
  `A6` is explicit — *"Never `outline: none` without a replacement. This is not
  optional"* — and an opacity change identical to the hover state is not a focus
  indicator. `D-016` also requires hover and focus be *distinguishable*; here they
  are byte-identical.
- **`role="grid"` with no rows or gridcells.** `.dora-cal-grid` (`:847`) declares
  `role="grid"` over 14 `<button>` children. An ARIA grid requires `role="row"`
  wrappers and `role="gridcell"` children; without them the role is invalid and a
  screen reader is told there is a grid it cannot navigate. Either build the full
  row/cell structure with arrow-key handling, or drop the role and let the buttons
  be buttons (they already work).
- **The calendar's selected and today states are colour-only.** `is-selected` is a
  background tint, `is-today` a border colour and bold weight; neither sets
  `aria-pressed` or `aria-current`. `D-013` requires the coding be decodable — the
  legend covers the three dot colours but not "today" or "selected".
- **One href-less `<a role="button">`**: Best deals' *"Hunt for deals →"*
  (`:682`) has `tabindex="0"` and `@keydown.enter` but no `keydown.space`, which a
  `role="button"` must handle, and no focus styling. One instance (Reports had
  four).
- **The donut's `aria-label` is excellent** (`:729`) — it states the full
  breakdown in words, which is precisely the text alternative Reports' five
  canvas charts lack. And the low/out segments are `role="link"` + `tabindex="0"`
  with Enter *and* Space handlers. Someone did this properly; the missing piece is
  only the focus ring they then removed.
- **Tap targets.** The `size="sm"` inline action buttons (Cook, Add, alert
  actions) and the 11.5px range chips are below the `D-004` 44px floor; the mobile
  block adds `padding: 6px 12px` to the chips (`:3250-3252`), reaching roughly
  30px. FU-631 #2 owns the app-wide version of this.

### 4.9 What it should look like — the design ideas

Nine moves, roughly in value order. Note how few are "polish" — the card
interiors are already good, so most of the value is in composition.

1. **Make the grid pack.** One width class for every card except `meal_plan` and
   `calendar`; kill the dead regions (§4.6). This is the highest-value change
   on the page and it is mostly deletion of column classes.
2. **One calendar, one lede, one shopping-list entry point.** Merge the week strip
   into the fortnight card (§3.2); make `heroLine` the page's single prose
   statement and drop the week-ahead "Next up" duplicate; and consider whether
   `draft_shop`, `primary_list` and the "Add to list" quick action need to be
   three separate affordances in one screen.
3. **One Money card** (§3.5) — spend as headline, budget bar when a target
   exists, saved-vs-RRP as support, one period control. Takes the Money zone from
   three default cards to two and makes each one complete.
4. **Zone labels at section-header weight** (§4.3). The page's information
   architecture is currently its least legible text.
5. **Fix the surface ladder** — twelve `--surface-elevated` → `--surface-sunken`
   (§4.5.1). One replace, and the page gains real depth.
6. **Retire semantic colour for value direction** (§4.5.2); keep it for budget,
   which has a threshold.
7. **A third card state: "couldn't load this one"** with a retry (§4.7), plus a
   Retry on the summary banner.
8. **Promote the Cards menu** (§3.9) — `secondary` variant, "Customise" label,
   and fix the hint that tells mobile users to drag.
9. **Icons to `--text-secondary`, focus rings everywhere, values never under
   14px** (§4.3, §4.5.3, §4.8) — the sweep that makes the whole thing read as
   deliberate. Last, deliberately (§7).

---

## 5 · Information architecture: 17 widgets, six questions

The plan's DoD names the six questions the dashboard should answer above the fold:
*wrong? cook? saved? budget? deals? restock?* Against the current default set:

| Question | Answered by | Verdict |
|---|---|---|
| Is anything wrong? | attention (+ hero line, + donut) | **Answered three times.** Consolidate the prose into the hero. |
| What do I cook? | cookable, meal_plan, calendar (+ hero line) | **Answered four times** from two different endpoints (§3.2). |
| What did I save? | savings | Answered — with a rounded number (§3.11) and an open baseline question (FU-810). |
| How's the budget? | budget | Answered, but as half of a sentence (§3.5). |
| Any deals? | best_deals, price_drops | **Answered twice, identically** (§3.6). |
| What will I run out of? | restock, attention | Answered — restock is the predictive one and it is genuinely good. |
| *(not in the DoD)* How's the kitchen doing? | dora_score | Added later; a real seventh question, worth keeping (§3.7). |
| *(not in the DoD)* What needs reconciling? | reconcile_pending | Added later; hide-when-empty, so it costs nothing when idle. |
| *(not in the DoD)* Start this week's shop | draft_shop | Added later; the most Effortless thing on the page. |

So the six questions are all answered, three of them multiple times, and three
good new questions were added. **The dashboard's problem is not coverage — it is
that nothing was removed when things were added.** A four-card default per zone
answering nine questions once each would be a better page than a thirteen-card
default answering six questions nineteen times.

**What is missing entirely:**

- **A way back to Reports.** Five Money-zone cards are the small-format twins of
  Reports cards backed by the same endpoints (FU-809 asks whether they should
  share a registry). Not one of them links to `/reports`. The dashboard is where a
  user would go looking for "show me more of this", and it is a dead end in that
  direction.
- **Anything about waste.** The `use_soon` card was cut (PROPOSAL_WASTE_MINIMISATION
  W5), correctly folded into the attention card's expiry alerts. But Kitchen
  health scores waste as one of five components, and there is no waste surface on
  the dashboard for its (deliberately absent) action link to point at. That is a
  known gap in the waste proposal, noted here because the score card is where it
  shows.
- **A "what changed since I last looked" signal.** Every card renders current
  state. The one delta on the page is Kitchen health's 7-day trend arrow, and it
  is the most interesting number on the screen. Worth generalising, not building
  eleven of.

---

## 6 · Engineering findings, ranked

| # | Finding | Location | Rule |
|---|---|---|---|
| 1 | `formatRelativeDay` parses `YYYY-MM-DD` as UTC then normalises to local — every relative day off by one west of Greenwich. 4 user-facing call sites. The correct parser (`parseLocalIso`) is 350 lines below in the same file. | `:1804-1816` vs `:2154-2157` | R-003, D-006 |
| 2 | Three money figures render via `AnimatedNumber`'s `toFixed(0)` + bare currency symbol — rounded to whole dollars, no separators, wrong symbol placement in suffix locales. One card shows both formats. | `:385,394,992`; `AnimatedNumber.vue:41-43` | D-006, R-003, Honesty |
| 3 | `--border-subtle` is referenced in 5 components and declared nowhere → invalid declaration → the reconcile chip renders with **no border**. | `ReconcilePastMealsChip.vue:40` + 4 others | **R-060** |
| 4 | `DoraScoreCard` styles reference 7 undeclared `--dora-*` properties; all colour comes from hard-coded hex fallbacks in all 10 themes, and `--dora-text` has no fallback at all. | `DoraScoreCard.vue:196-286` | **R-060**, R-002 |
| 5 | Kitchen health calls `GetBudgetStatusHandler` unconditionally; that handler doesn't check the money flag, so a money-off install's composite is weighted by budget data and the card renders a "Set a budget →" link. Endpoint has no gate. Precedent: `get_buy_verdict.py:840`. | `get_dora_score.py:112-119` | **R-058**, ADR-005 |
| 6 | The stock donut samples theme colours once inside a `computed` with no reactive dependency on the theme — never repaints on a theme switch, and the comment claims it does. Origin of Reports' `themeTick`. | `:1697-1710` | — |
| 7 | "Hide for today" (tooltip, `:192`) sets a plain ref recreated on every mount — the welcome band returns on the next navigation to the dashboard. | `:1372,190` | D-014 (copy claims a behaviour) |
| 8 | `/dashboard/summary` computes and ships **7 fields nothing renders**: `products.total`, `recipes.favourites`, `recipes.cookable_count`, `recipes.needs_linking_count`, `meals.total_definitions`, `meals.total_in_stock`, `shopping_lists.total_items`. Two are dedicated aggregate queries run on every dashboard load. FU-767 is a bug report about one of them. | `get_dashboard_summary.py:159,163,174,182,190,194,154` | R-007, dead code |
| 9 | Deterministic dead grid regions at every desktop width — 5 at ≥1440px, 2 at 1024–1439 (count corrected by measurement; §4.6). **Fixed in chunk 2**: 0 at 375/768/1024/1280/1440/1920. | §4.6 | **D-011**, B4 |
| 10 | Eleven slot loaders swallow errors into the card's *empty* state — a failed fetch reads as "nothing here yet". | `:1868` + 10 repeats | Honesty, D-007 |
| 11 | `totalSpend` sums all rows client-side while the list shows only the top 3, and renders the total bare with no "+N more" and no coverage. `StoreSpendResponse` ships no total. | `:2197-2200` | **R-041**, state-ownership |
| 12 | Pantry value renders a bare dollar figure whose `estimate_note` caveat is a caption, over a formula the Reports review found dimensionally meaningless (`level_ordinal × price`, unpriced items contribute 0). | `:1042-1057` | **R-041** |
| 13 | Savings renders a bare total with its coverage (*"only lines where a real deal price was captured"*) behind a tooltip — R-041's named violation signal. | `:968-998` | **R-041** |
| 14 | Product images loaded via `<img :src="/api/products/${id}/image">` at 2 sites here (3 app-wide) — unauthenticated by construction, and a relative `/api/` path can't resolve at all in the Capacitor shell. | `:647,1090`; `MyProductsPage.vue:223` | **R-045** |
| 15 | 44 raw font-sizes / 22 raw radii (6 distinct) / 95 raw spatial values; **zero** `--font-size-*`, `--radius-*` or `--space-*` tokens in 3126 lines. 8 declarations below the 12px floor, one carrying a count. | §4.3–4.4 | R-002, **D-003**, D-017, A2/A3/A4 |
| 16 | R-001: 14 of 17 card bodies still inline; page grew 1964 → **3126** lines against a DoD that said the monolith would be gone. FU-293 closed the shell only. | §4.2 | **R-001** |
| 17 | Zero `:focus-visible` rules; the one `:focus` rule sets `outline: none` with an opacity change identical to hover. | `:2466-2470` | **A6**, D-016 |
| 18 | `role="grid"` over 14 buttons with no rows/gridcells — invalid ARIA. | `:847` | A6 |
| 19 | Twelve nested rows on `--surface-elevated` inside `--surface-component` cards — the ladder inverted. Reports copied this. | §4.5.1 | A1, B11 |
| 20 | Pantry-value delta colours rising value green while Reports colours rising spend red — the app contradicts itself on the same fact. | `:2686-2691` | A1 |
| 21 | `parseLayout` appends unseen cards to the **end** of the order while its comment says *"at its `CARD_DEFS` position"* — so `dora_score`, whose CardDef says it *"sits above 'Pantry'"*, sorts below Pantry for every user with a saved layout. | `:1499-1501` vs `:1320-1324` | R-019 (comment ≠ code) |
| 22 | `ZONE_BASE` invariant comment says *"the ≤9 card indices"*; there are 17. Still safe (17 < 100), but the guard is implicit and the comment is stale. | `:1568-1572` | R-019 |
| 23 | The hint pool advertises budget and product features to installs that have them switched off. | `dashboardMessages.ts:87-89` | ADR-005, feedback L254 |
| 24 | Hand-rolled `<button class="dora-range-chip">` segmented control where `BaseSegmented` exists; no `aria-pressed`, no focus state, 11.5px label. | `:977-988` | **R-048**, B2a |
| 25 | `get_dora_score._gather_inputs` loads **every** `StockItem` into memory, and is called twice per request (current + lagged window). Also constructs a second `SqlAlchemyRepository` mid-handler instead of using `self.repository`. | `get_dora_score.py:115,126` | R-031, perf |
| 26 | `loadSwapSummary` fetches today + **all** meal plans, then a third call for swap suggestions, on every dashboard load — to render one optional bullet on the budget card. | `:2019-2045` | R-016 |
| 27 | `pantryValueDelta`'s window is hardcoded as the string "over 90 days" in the template while the fetch passes `'90d'` — one constant, two places. | `:1050,2091` | R-003 |
| 28 | The summary-failure banner tells the user to "try refreshing" and offers no retry; the refresh button was deliberately removed by D3. | `:1999` | D-014 |

Findings 1–8 are functional defects. 9–14 are honesty/architecture. 15–28 are
consistency and design-rule debt.

---

## 7 · Recommended sequencing

Deliberately the mirror of the Reports sequencing, for the same reason: don't
tokenise cards that are about to be merged or deleted.

**Chunk 1 — the functional defects.** Findings 1–8. All small, all testable, no
design decisions in any of them. Findings 3 and 4 are one R-060 sweep; 1 and 2 are
one "dates and money go through the shared formatter" pass; 5 is a three-line
gate with a precedent to copy; 8 is deletion (and it closes FU-767 by making the
field it's about disappear). This chunk needs no owner input and should go first.

**Chunk 2 — make the grid pack.** Finding 9 / §4.9.1. Independent of every card
decision below, because it is about width classes rather than which cards exist.
Highest visible improvement per line changed on the whole page.

**Chunk 3 — the card census.** **Unblocked 2026-09-02** — FU-817/818/819 and
FU-810 are all answered (§8), so this is now a defined build, carried by
**FU-830**: merge the week strip into the fortnight card (7-day default,
expandable to 14, one endpoint); fold Budget into the retrospective Money card
with spend as the headline; cut Best deals; drop the week-ahead "Next up"
callout; encode the default count in `CARD_DEFS`. Net: **17 registered → 14,
13 default-on → 11** (10 effective). This is where the IA duplication in §5 gets
paid off. **One dependency to sequence around:** the Money card's *metric* changes
under FU-831 (ADR-068), which is backend work with a migration and a reseed — do
the card merge here against the existing figure and let FU-831 swap the number
underneath, rather than blocking the whole census on a schema change.

**Chunk 3b — the savings baseline (FU-831).** Independent of the dashboard and
larger than it: a pick-time `usual_price_at_pick` snapshot + write path, the
retrospective handler moved onto it, R-041 coverage for items with no price
history, the tense-split labelling across Reports / dashboard / shopping list, and
a reseed. Runs in parallel with Chunks 2–3; nothing on the dashboard blocks on it
except the Money card's final copy.

**Chunk 4 — honesty and error states.** Findings 10–13: a third "couldn't load"
card state, R-041 coverage on the three bare aggregates, a Retry on the summary
banner. Deliberately after Chunk 3 so the coverage work lands only on surviving
cards.

**Chunk 5 — finish the extraction.** Finding 16. One card per component, into
`components/dashboard/`, taking its body SCSS with it — which is what makes Chunk
6 tractable, because a 40-line component's tokens can be swept and reviewed in
one sitting where a 970-line stylesheet cannot. Write the ADR here (FU-829).

**Chunk 6 — the design-rule sweep.** Findings 15, 17–20, 24: tokens, focus rings,
the surface ladder, semantic colour, `BaseSegmented`, the `B9` empty-state icons.
Last, and much cheaper after Chunk 5.

---

## 8 · Open decisions

Every item carries a recommendation; the four that were genuinely the owner's call
were logged as FUs and **have since been answered**.

> **Owner answered D1–D4 on 2026-09-02**, the same day as the review. Decisions
> are recorded inline below. FU-817/818/819 and the Reports review's FU-810 are
> **resolved**; the decided work is carried by **FU-830** (dashboard restructure)
> and **FU-831** (savings baseline, cross-surface). The metric half produced
> **ADR-068 / R-071**. The two remaining Reports calls, FU-811 and FU-812, are
> still open.

- **D1 — Does the default-visible card set get re-derived and encoded?**
  *Recommendation was: yes, to 8.* **DECIDED: merges only, no demotions, then
  encode the number.** The three merges (D2, D3, D4) take default-on from 13 to
  **11** — 10 in practice, since `reconcile_pending` is hide-when-empty — without
  any feature losing its front-page slot: `suggestions`, `restock`, `dora_score`
  and `stock_items` all stay default-on. A comment in `CARD_DEFS` names
  `IMPL_PLAN_DASHBOARD_REBUILD` §2.2, as amended by this decision, as the
  authority, so the next card added has to argue with something.
  *(Correction to this review as first written: §3.1 and the option put to the
  owner both said the merges reach 10. They reach **11** — the calendar merge
  removes a **registered** card that was already `defaultHidden`, so it does not
  move the default count. The decision is unaffected; the target is one card
  looser than quoted.)* → **FU-817 resolved**; work in FU-830.
- **D2 — Which of the four meal-plan surfaces survive?** **DECIDED: keep Next to
  cook; merge the week strip into the fortnight card; drop the week-ahead "Next
  up" callout.** The merged card is one registered card showing **7 days by
  default, expandable to 14**, from a single endpoint — which also closes the
  two-query disagreement §3.2 found. Registered −1; default-on unchanged.
  → **FU-818 resolved**; work in FU-830.
- **D3 — Best deals or Price drops?** **DECIDED: keep Price drops, cut Best
  deals.** The server-verified new low is the claim Dora can stand behind, and
  cutting Best deals removes the last *card* resting on the vs-RRP baseline D4
  reopens. `discountPercent` survives as a per-offer display helper — one offer's
  % off the ticket is a shelf-price question and stays legitimate (ADR-068).
  → **FU-819 resolved**; work in FU-830.
- **D4 — Do Budget and Savings become one Money card?** **DECIDED, and the answer
  came with a metric change that outgrew this page.** FU-810 was answered *"keep
  the card, change the baseline"*; two follow-on calls then settled what that
  means app-wide. **"Saved" splits by tense** — live in-list savings stay vs shelf
  price (the honest question in the aisle, and the only baseline available for an
  item with no price history), the retrospective card moves to the household's own
  historical unit price, and **both are labelled**, in the DTO field name as well
  as the copy. **Existing archived lists are reseeded, not backfilled** (the
  own-price baseline needs its own pick-time snapshot column; deriving it
  retroactively would make past shops' savings move every time a price is logged).
  Budget folds into the retrospective card with **spend as the headline** and
  savings as support. Now **ADR-068 / R-071**. The metric work spans Reports, the
  dashboard and the shopping list → **FU-831**; the card merge itself rides in
  FU-830.
- **D5 — Is Kitchen health's "Stocktake" component a health signal or a nag?**
  *Answered inline (§3.7.2): score it against the install's configured stocktake
  cadence rather than a hard 30 days, so a stable pantry isn't penalised.* A
  threshold change inside the score's own domain module; folded into Chunk 1's
  R-058 work since both touch that handler. No separate FU.
- **D6 — Does the componentisation-not-finished pattern become a rule now?**
  *Answered inline: yes.* This is its fifth sighting, and the first where the goal
  was written into a Definition of Done and closed by a partial (§2). The rule
  worth writing is narrower and more useful than "componentise first" (which
  R-001 already says): **a Definition of Done item that is deferred to a
  follow-up is not satisfied by that follow-up's partial resolution — the DoD
  outlives the FU, and closing the FU has to say which DoD rows are still open.**
  → **FU-829** carries both the remaining extraction and the ADR.
- **D7 — Does the page-local `--c-*` alias layer stay?** *Recommendation: retire
  it during Chunk 5.* The aliases all resolve, so nothing is broken; but they cost
  a second vocabulary and stop working the moment a card becomes a component —
  which Chunk 5 does to fourteen of them. FU-747 already tracks it; no new FU.
- **D8 — Does the dashboard link to Reports?** *Recommendation: yes, one link
  from the Money zone header.* Contingent on FU-809 (shared card registry), which
  would make it structural rather than decorative. Deferred to that decision.

**Open decisions — closed:** all eight resolved above. **D1–D4 were answered by
the owner on 2026-09-02** (same day as the review) — their FUs (817/818/819, plus
the Reports review's 810) are resolved and the decided work is carried by FU-830
and FU-831; D4's metric half is now ADR-068 / R-071. D5–D8 were answered inline:
D5 folds into Chunk 1, D6 into FU-829, D7 into FU-747, D8 into FU-809. No
undecided fork remains in this document.

---

## 9 · From the original spec

Skimmed `docs/00_original_spec/Feature Boards/Dashboard.md` and `PROMPT_PLAN.md`
P12 (`:202-211`). Historical and non-authoritative; the charter, the feedback and
the rebuild plan override. Three items worth extracting:

- **P12's *"Every chip and number is a deep link into the relevant screen"* —
  keep, and note the dashboard nearly got there.** This is the same instruction
  N6 gave Reports and Reports ignored entirely. The dashboard honoured most of
  it: alert rows, donut segments, legend rows, recipe names, deal rows, calendar
  items and stock items are all real `<router-link>`s. The remaining dead ends are
  the money figures — savings, spend rows, pantry value, budget — which is the
  same category Reports missed. Worth finishing while the Money zone is being
  consolidated in Chunk 3.
- **P12's *"morning glance"* framing — keep, and use it as the test.** It is a
  better yardstick than the DoD's six questions, because a glance has a size. If
  the page does not fit on one screen it is not a glance, and thirteen cards do
  not. Adopted as the argument in §3.1.
- **The Feature Board's *"I can see a card for stock items / shopping lists / my
  products / my recipes"* — superseded, deliberately, and the rebuild was right.**
  All four are exactly the vanity counters `IMPL_PLAN_DASHBOARD_REBUILD` §2.6 cut,
  and the two that survived did so by becoming answers (the donut deep-links its
  buckets; the shopping-list counter became "+N other active lists" on the primary
  card). Do not rebuild them. Noted because the board still lists them as
  Backlog, and a future reader mining it for dropped intent would find four items
  that were dropped on purpose.

The board's *"I can enable and disable the visibility of cards on the
dashboard"* is the one item that shipped essentially as written — and it shipped
better than specified (zones, ordering, server persistence, feature gates).

---

## 10 · Feedback coverage

Mandated by `CLAUDE.md`. Unlike Reports, this surface has a real feedback set —
`Feedback _ Fixes - as of [06-Jun-2026].md:48-61` plus the three strays that
`COVERAGE_GAPS.md:177-181` maps here — and it was already mapped to phases by
`IMPL_PLAN_DASHBOARD_REBUILD.md` §5. The table below re-verifies each bullet
against the code *as it stands now*, which is the value this document adds over
that one.

| Bullet | Source | Shipped? | Where covered here |
|---|---|---|---|
| D1a — Skip-wizard "Continue" does nothing | L51 | ✅ `onContinueOnboarding` restarts + refreshes auth + routes (`:1405-1421`) | — |
| D1b — Skip banner buttons take their own row | L52 | ✅ inline (`:149-165`) | — |
| D1c — Welcome message when onboarding complete | L53 | ✅ (`:170-195`) | §3.3 (it is one band too many, not wrong) |
| D1d — Cycled, day-of-week, 5/day, pool 35-40 + hints pool | L54 | ✅ 35 welcomes ×7 days + 15 hints, deterministic per day (`dashboardMessages.ts`) | §3.4.2 — the hints need gating |
| D1e — Replace "Dora says" bubble, keep the yellow | L55 | ✅ (`.dora-welcome`, `:3119-3133`) | — |
| **D2 — Dark mode not working** | L56 | ⚠️ **partially** — the page's own tokens are theme-aware, but `DoraScoreCard` renders hard-coded light-theme hex in every theme, and the donut freezes its palette on switch | **§3.7.1 (FU-822), §3.10 (FU-824)** — this bullet is not fully closed |
| D3 — Remove the refresh button | L57 | ✅ removed, `loadAll` kept (`:20-23`) | §4.7 — the error copy still names it |
| D4 — Reorder cards via draggable rows | L58 | ✅ drag + tap + mobile-off (`:1613-1641`) | §3.9 — built well, undiscoverable |
| D5 — Alerts nav 404 → alerts control page | L59 | ✅ `/alerts` exists, verified FU-295 | — |
| D6 — Alert card redesign: summary + peek + See all | L60 | ✅ exactly as specified (`:262-339`) | §1.6 — protect this |
| D7 — "This fortnight" calendar, coloured dots, click a date | L61 | ✅ opt-in card on `/alerts/upcoming` (`:833-914`) | §3.2 — it duplicates the week strip from a different endpoint |
| L176 — Mascot not centred in the greeting card | stray | ❓ unverifiable statically — `q-avatar square` + 2px padding + 14px radius (`:7-9`, `:2332-2337`) | → DORA_VERIFY |
| L272 — "Next up to cook": next 3 by meal-plan + stock, ready/missing | stray | ✅ (`:566-621`, FU-298) | §3.2 — keep this one of the four |
| L480 — Cross-app undo after push-expiry | stray | ✅ resolved separately (FU-357) | out of scope, as the plan said |
| L254 — Money features must be switchable off, app-wide | cross-cutting | ⚠️ **cards yes, score and hints no** | **§3.4 (FU-823)** |
| L471 — Font size/type usage is bad for headings | cross-cutting | ❌ | **§4.3** — 44 literals, zone labels at 11.5px |
| Critique — no savings widget | plan §1 | ✅ | §3.5, §3.11 |
| Critique — vanity counters dominate | plan §1 | ✅ cut from the page… | **§6 finding 8 — but they are still computed and shipped by the API** |
| Critique — actionable cards hide when empty | plan §1 | ✅ inverted (R-014) | §1.4, §3.8 — the app's best example |
| Critique — flat hierarchy / no triage gradient | plan §1 | ✅ zones | §4.3 — the labels are illegible |
| Critique — a11y: clickable articles, `href="#"`, nested interactives | plan §1 | ⚠️ **mostly** — real router-links now, but zero focus rings and one `outline:none` | **§4.8** |
| Critique — no quick actions / no temporal intelligence | plan §1 | ✅ quick-action bar + restock radar | §5 — three shopping entry points now |
| Critique — donut buckets not actionable | plan §1 | ✅ deep-linked (FU-299) | §1.7 |
| Plan §2.2 — curated default-visible set (8 cards) | plan decision | ❌ **13 default-on** | **§3.1 (FU-817), §2** |
| Plan §6 DoD — thin composition over `components/dashboard/*` | plan DoD | ❌ **3126 lines, 14 cards inline** | **§4.2 (FU-829), §2** |
| Plan Charter — Anti-creep: default count held roughly flat | plan §4 | ❌ 13 cards vs the 13-card "kitchen sink" it replaced, +4 opt-in | **§3.1, §5** |

**Out of scope, deliberately:** the alerts engine itself (only its dashboard
read-surface is covered); the Dora Score's scoring *thresholds* beyond §3.7.2's
one observation (they belong to the score's own domain module); the reports
endpoints' internals (covered by `REPORTS_PAGE_REVIEW.md`); the waste-surface gap
(PROPOSAL_WASTE_MINIMISATION's, noted in §5 only because the score card is where
it shows); FU-631's mobile tap-target and toolbar items.

**`COVERAGE_GAPS.md` update:** the DASHBOARD entry (`:177-181`) points at
`IMPL_PLAN_DASHBOARD_REBUILD.md` and reads as closed. It has been amended to
point here as well, noting that D2 (dark mode) and L254 (money opt-in) are
**re-opened** by this review's findings, and that the plan's §2.2 and §6 DoD rows
are unmet.
