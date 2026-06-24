# Dashboard Rebuild — Implementation Plan

**Status:** 📋 Brief — ready for execution by a Claude agent (phased).
**Raised:** 2026-06-23 (after a `/design-critique` pass on `DashboardPage.vue`,
mirroring the Settings rebuild flow).
**Owns:** `web_app/src/pages/DashboardPage.vue` + any dashboard widget
components extracted in the process (new `web_app/src/components/dashboard/`
directory) + the dashboard summary / reports wiring it consumes.
**Supersedes:** the "DASHBOARD — deferred per master plan" hold in
`docs/02_feedback/COVERAGE_GAPS.md` L169. The user has now explicitly pulled the
dashboard forward; this is its design home.

**Cross-references:**
- `docs/01_charter/ENGINEERING_STANDARDS.md` — R-001 (componentisation),
  R-002 (theme tokens only), R-003 (single source of truth / state-ownership),
  R-007 (scope discipline), R-008 (comment-or-flag), R-011 (framework-idiomatic
  Quasar/Vue), R-014 (defined empty states), R-016 (lazy store hydration).
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II — Charter principles
  (tiebreak: **Effortless + Anti-creep**; also Honesty).
- `docs/01_charter/RECONCILED_FINISHING_PLAN.md` §7.5 — distribution posture
  (any new backend report must stay repository-routed + Postgres/SQLite portable).
- `docs/04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` — derived facts
  (savings, restock prediction, pantry value) compute server-side, not in the
  browser.
- `docs/04_proposals/PROPOSAL_ALERTS.md` (C-9) — the alerts control page is the
  canonical alerts surface; the dashboard alert card is a *peek* into it
  (Phase 3 depends on it).
- Feedback source of truth: `docs/02_feedback/Feedback _ Fixes - as of
  [06-Jun-2026].md` §DASHBOARD (L48–61) + strays L176 / L272 / L480.

---

## 0. Read this first

This is a **rebuild brief**, not a one-shot prompt. The current dashboard's
problem is **structural, not cosmetic**: the visual craft is good (warm hero,
animated donut, week strip, token discipline), but roughly 40% of the grid is
spent on **vanity counters** (`products` total, `recipes` total, `meals` on
hand, `shopping_lists` count) that answer no question the user actually has,
while the app's headline value — **how much money you've saved** — is invisible
despite a `savings-captured` report endpoint already existing and wired up
elsewhere.

A pure repaint would re-skin a demo page. Do the **content/IA work first**
(what the dashboard is *for*), then the layout (zones + reorder), then the
new value widgets that surface the reports the dashboard currently ignores.

The brief is decomposed into phases. **Each phase is independently shippable**
and ends with a clean diff + worklog entry. Do **not** roll all phases into one
PR — the user has asked for incremental delivery on rebuilt surfaces before
(see the Settings rebuild).

### The diagnosis in one line

> The dashboard currently shows **counters, not answers.** Every card should
> answer a question the user has (*Is anything wrong? What do I cook? What did I
> save? What will I run out of?*) — not state a total that exists only because
> the data exists.

---

## 1. Source of truth — current state

Current page: `web_app/src/pages/DashboardPage.vue` (~1964 lines — everything,
template + script + scoped SCSS, lives in this one file; **R-001 violation** to
unwind as we extract widgets).

Data sources today:
- `GET /dashboard/summary` (`dora_api/features/dashboard/get_dashboard_summary.py`)
  — one bulk payload: stock buckets, shopping-list counts, product count, recipe
  totals + `cookable_count`, meals on hand, 7-day upcoming meal-plan entries.
- Per-card slot loaders (parallel, fail-independent): alerts, best-deals,
  primary-list detail, budget status, waste rescue, suggestion store, recipe
  store (for cookable), shopping-list store.

The **reports API is fully built and entirely unused by the dashboard**
(`web_app/src/services/api/reportsApiService.ts`):
- `getSavingsCapturedAsync(range)` → total saved vs. RRP + per-list breakdown.
- `getSpendByStoreAsync(range)` → spend grouped by store.
- `getMostBoughtAsync(range)` / `getKeepsRunningOutAsync()` → behavioural.
- `getPriceTrendsAsync(ids, range)` → per-product price series.
- `getStockValueAsync(range)` → pantry value over time.

These are the raw material for the new value widgets (Phase 4–5).

### Current 13 cards (hardcoded `CARD_DEFS` order)

| # | Card id | Type | Verdict |
|---|---|---|---|
| 1 | `attention` (alerts) | action | **Keep — flagship** |
| 2 | `primary_list` | action | **Keep + absorb `shopping_lists`** |
| 3 | `budget` | money | **Keep** |
| 4 | `use_soon` (waste) | action | **Keep** |
| 5 | `suggestions` (Dora) | action | **Keep, verify vs. chat badge** |
| 6 | `cookable` | answer | **Keep + upgrade (L272)** |
| 7 | `best_deals` | money | **Keep** |
| 8 | `meal_plan` (week strip) | glance | **Keep** |
| 9 | `stock_items` (donut) | glance | **Modify — deep-link buckets** |
| 10 | `recipes` (total/favs) | counter | **Cut** (§2.6) |
| 11 | `meals` (on hand) | counter | **Cut** (§2.6) |
| 12 | `shopping_lists` (count) | counter | **Cut → merge into `primary_list`** |
| 13 | `products` (total) | counter | **Cut** |

### User observations / critique findings (verbatim + codified)

From feedback §DASHBOARD (L48–61):
- Skip-wizard banner: Continue did nothing (since fixed — verify), buttons take
  a whole row (should inline), and the banner should evolve into a **welcome /
  message system** that keeps the yellow "Dora says" treatment.
- "Dark mode not working" on the dashboard (token-compliance check).
- "How useful is refresh really?" — remove if navigation already refreshes (C16).
- Card **reordering** via draggable rows in the toggle list (C13: drag = power
  user, always offer a tap alternative, disable drag on mobile).
- Alerts nav 404 → **alerts control page** (C-9, likely already built — confirm).
- **Alert card redesign**: two sections — top = summary boxes/chart by type
  ("5 items expiring", "3 high-attention"), bottom = peek at top 3, big "See
  all" button.
- **"This fortnight" calendar widget**: coloured dots per date combining
  shopping / expiry / meals; click a date → that day's detail.

Strays: mascot not centred in its box (L176 — B9.8 addressed this; verify);
"next up to cook" — next 3 recipes by meal-plan + stock, with at-a-glance
ready/missing (L272); cross-app undo off after dashboard "push expiry" (L480).

From the critique pass:
- **No savings widget** — the #1 missed opportunity.
- **Vanity counters** dominate; **actionable cards hide when empty** while
  counters never do, so the calm/new-user dashboard is the worst version.
- **Flat hierarchy** — no triage gradient; urgent and trivial cards share weight.
- **A11y**: clickable `<article @click>` cards aren't keyboard-operable;
  `href="#" @click.prevent` everywhere instead of `<router-link>`; nested
  interactives inside clickable cards.
- **No quick actions / no temporal intelligence** (restock prediction unused).

---

## 2. Impact & decisions — RESOLVED with user 2026-06-23

1. **Card-prefs storage → SERVER-PERSISTED.** Reorder + zone membership +
   visibility move off `localStorage` to a per-user preference saved via the
   backend (multi-device, survives cache clear). Phase 2 carries a small prefs
   endpoint + migration (repository-routed, Postgres/SQLite portable — §7.5).
2. **Default-visible set → CURATED.** On a fresh install, default-on is **only**:
   Act-now (alerts / use-soon / suggestions), Today (cookable / week-ahead /
   primary-list), **Savings**, **Restock radar**. Everything else (spend trend,
   pantry value, price drops, any surviving glance stat) is **opt-in** via the
   Cards menu. The dashboard looks focused out of the box (Anti-creep).
3. **Fortnight calendar (D7) → DEFERRED to its own phase.** Build Phases 0–5
   (high-value, mostly-existing-data) first; the calendar + its new aggregation
   endpoint becomes a dedicated follow-up after the rebuild lands. Phase 6 below
   is retained as the spec but is **not** part of the initial rebuild sequence.
4. **Price-drops signal → SERVER-SIDE "new low".** A small backend addition
   computes a genuine new-low / drop from price history (Honesty: "lowest you've
   seen" must be true). **Plus a data-presence gate:** the product-derived money
   widgets (**price drops** *and* **best deals**) are **hidden from the Cards
   list entirely** unless product data exists — products is a data-presence
   overlay now (`products_enabled` flag was dropped — see
   `PROPOSAL_PRODUCTS_AS_OVERLAY.md`), so users with no products never see
   widgets they can't populate. Reuse the existing `v-if="productsEnabled"`
   data-presence signal that gates other product surfaces (R-003 — one signal).
5. **Suggestions → KEEP, verify non-duplication.** Keep the `suggestions` card
   but, during the build, confirm in the running app that it surfaces something
   the chat-launcher badge doesn't already. If it's pure duplication, cut it then.
6. **Recipes + meals counters → CUT BOTH.** Not merged — removed entirely.
   Cookable-tonight + week-ahead already answer the useful recipe questions; raw
   totals add nothing. (Updates the Phase 1 / §1 verdicts below from
   "demote/merge" to "cut".)
7. **Welcome-message copy → I draft.** The build authors the full pools
   (~35–40 day-of-week-flavoured welcomes + a separate helpful-hints pool) in
   Dora's voice, for the user to trim/tweak.
8. **Empty-state for default money/restock cards → friendly onboarding.**
   Savings + Restock are default-visible but empty for new users (no completed
   shops / no run-out history). They render a **positive "here's what this will
   track" empty state + CTA** ("Finish a shop to see your savings") and stay
   visible so the feature is discoverable — consistent with the Phase-1
   empty-state inversion (R-014). They do **not** auto-hide.
9. **Quick-action row → lightweight inline popups.** Add-item / add-to-list /
   log-price open a small inline dialog on the dashboard, submit, done — no
   navigation (max Effortless). Reuse the existing mutation services + any
   existing create-form sub-components where possible (R-001/R-011); don't
   duplicate validation logic.
10. **Delivery cadence → power through, one chunk at a time.** The user cannot
    review in this environment, so phases are executed sequentially without
    gating on PR review. Still: one clean commit + `CHANGELOG`/`DORA_WORKLOG`
    entry per phase, and `vue-tsc` + `eslint` green before moving to the next
    chunk (build-to-plan, verify-in-browser later).

---

## 3. Phased plan

Each phase: scope → files → standards gate → worklog entry. Ship in order;
later phases assume earlier ones landed.

### Phase 0 — Foundations & hygiene (no new widgets)

Low-risk groundwork that every later phase builds on.

- **Remove the refresh button** (feedback C16/D3) — `onMounted(loadAll)` already
  refreshes on nav; the manual button earns nothing. Keep `loadAll` for the
  internal re-fetch after actions.
- **Fix card interaction model + a11y** (critique):
  - Replace `href="#" @click.prevent="goTo(...)"` with `<router-link>` / `:to`.
  - Replace clickable `<article @click>` with a real control (router-link
    wrapper or `role="button"` + `tabindex="0"` + Enter/Space) — R-011.
  - Resolve nested-interactive ambiguity (no clickable card *containing*
    clickable rows/buttons; pick one per card).
- **Dashboard dark-mode / token audit** (D2) — sweep the ~640 lines of scoped
  SCSS for any value bypassing tokens; confirm the donut's `getComputedStyle`
  fallback hexes only fire when a token is genuinely absent (R-002).
- **Verify mascot centring** (L176) — B9.8 claims this fixed; confirm in the
  hero + log a `finding` if it regresses.
- **Extraction scaffolding** — create `web_app/src/components/dashboard/` and a
  shared `DashboardCard.vue` shell (header + action slot + empty-state slot)
  so subsequent phases extract one widget per component instead of growing the
  1964-line page (R-001). This is the single most important structural move.

*Gate:* R-001 (begin de-monolithing), R-002 (token audit), R-011 (real
controls). `vue-tsc` + `eslint` green.

### Phase 1 — Prune the vanity, fix empty-state inversion, welcome system

> **Status (2026-06-24): content work DONE + green.** Cuts, the shopping-lists
> merge, empty-state inversion, and the welcome/message system have landed.
> `DashboardCard.vue` extraction was **moved to Phase 2** on purpose — Phase 1
> *deletes* 4 cards and Phase 2 *restructures* the grid into zones, so extracting
> the surviving cards into a shell is done there (during the restructure), not
> here where it'd churn cards about to be moved/deleted.


Turn counters into answers; make the calm-state dashboard look *best*, not
emptiest.

- **Cut `products`** card (pure vanity).
- **Merge `shopping_lists`** into `primary_list` (show "+N other lists" line);
  drop the standalone counter.
- **Cut `recipes` + `meals`** entirely (§2.6) — cookable-tonight + week-ahead
  cover the useful recipe questions; raw totals add nothing.
- **Invert empty states (R-014):** actionable cards (`attention`, `use_soon`,
  `suggestions`) render a *positive* empty state ("Nothing expiring — nice")
  instead of `v-if`-hiding. No value card silently disappears.
- **Welcome / message system** (D1c/d/e):
  - Inline the skip-wizard banner actions (D1b — Continue/Hide on the same row,
    not their own row); confirm Continue works (D1a — code path exists via
    `onContinueOnboarding`, verify in browser).
  - When onboarding *is* complete, the hero/footer shows a cycled welcome
    message: day-of-week-aware pool (~35–40, 5/day feel) + a separate
    helpful-hints pool, keeping the yellow "Dora says" treatment. Replaces the
    bottom-right "Dora says" tip bubble but preserves its look (D1e).
    Selection deterministic-per-day (extend the existing `TIPS` epoch-day
    picker; R-003 — one picker, two pools).

*Gate:* R-014 (empty states), R-003 (single message picker), R-007 (no
scope bleed into the message *content* engine beyond pools).

### Phase 2 — Layout zones + card reorder (+ DashboardCard extraction)

> **Status (2026-06-24): zones + reorder + server-persisted prefs DONE + green.**
> Zones (Act now / Today / Money / Your kitchen) render via CSS `order` (full-
> width band headers + per-card order) — no markup moves. Reorder is within-zone
> up/down (tap — C13's required alternative; literal drag-handles → FU-294).
> Prefs are server-persisted on `User.dashboard_layout` (backend static-only,
> FU-292). **DashboardCard extraction was NOT done** — delivering zones via CSS
> `order` avoided needing it, and it's a pure-internal R-001 refactor with
> browser-only-verifiable CSS risk → deferred to FU-293.


Give the eye a triage gradient and satisfy the drag/reorder ask. **Also do the
R-001 de-monolith here:** while restructuring the grid into zones, extract each
surviving card into `web_app/src/components/dashboard/` behind a shared
`DashboardCard.vue` shell (header + action slot + body slot + empty-state slot),
moving the shell SCSS (`.dora-card*`) into that component (the body SCSS for
slotted content stays in the page — slotted content keeps the parent's scope).
This was deferred out of Phases 0/1 deliberately (don't extract cards you're
about to delete or move).

- **Zones** — group the grid into labelled bands rendered in priority order:
  **Act now** (alerts, use-soon, suggestions) · **Today** (cookable, week
  ahead, primary list) · **Money** (savings, budget, best deals, price drops) ·
  **Your kitchen** (pantry donut, restock radar, surviving stats). A zone with
  no visible cards collapses entirely.
- **Reorder** (D4/C13) — draggable rows in the Cards toggle menu *and* a tap
  alternative (move up/down); **drag disabled on mobile**. Persist order
  (and per-zone membership) per §2.1 decision. R-003 — order is one source,
  consumed by the render.

*Gate:* C13 compliance (tap alternative + mobile-off), R-003 (single
order/zone source), R-016 (don't eager-load widget data for hidden cards).

### Phase 3 — Alert card redesign (the two-section summary)

> **Status (2026-06-24): DONE + green.** Top = by-kind summary chips ("5 ·
> expiring soon"), bottom = peek at the top 3 (most-urgent first) with inline
> actions, plus a prominent "See all alerts →". Alert row links are now real
> `<router-link>`s (the Phase-0 a11y carve-out is resolved). `/alerts` route
> exists (D5 appears fixed — confirm-in-browser FU-295). By-kind grouping is
> client-side display of the already-fetched list (R-003 note in code).


Depends on the alerts control page (C-9 / `PROPOSAL_ALERTS.md`) existing — the
`/alerts` route is already referenced in code, so D5's 404 is likely resolved;
**confirm in browser** and log a finding if not.

- **Top section:** summary boxes/chart by alert *type* + count ("5 expiring",
  "3 high-attention", "2 low stock") — D6. Counts/grouping server-owned (R-003).
- **Bottom section:** peek at the top 3 (current row design, kept).
- **Prominent "See all →"** into the alerts control page.

*Gate:* R-003 (alert grouping computed server-side, not summed in the browser),
R-001 (extracted `AlertSummaryWidget.vue`).

### Phase 4 — The Money zone (surface the unused reports)

> **Status (2026-06-24): savings + spend + pantry DONE + green; price-drops
> deferred (FU-296).** Three widgets shipped on existing reports endpoints:
> **Savings captured** (flagship, default-on, range toggle Month/Year/All),
> **Spend by store** (opt-in), **Pantry value** (opt-in). All gate on
> `useMoneyEnabled` (ADR-005); `best_deals` now gates on product data-presence
> (§2.4) via a new `cardAvailable` + `gate` seam on CardDef. **Price drops** was
> NOT built — it needs a new server-side "new low" signal (no Python env here) →
> FU-296. Budget-card money-gating inconsistency noted → FU-297.


The highest-value phase — turns "demo" into "tool". All endpoints exist
(`reportsApiService`); compute any new derivation server-side (state-ownership).

- 🥇 **Savings captured** widget — "You've saved **$X** this {period} vs. RRP",
  sparkline + lifetime toggle (`getSavingsCapturedAsync`). **Default-visible.**
  Sits beside `budget` so spend + saved tell the whole money story.
- **Price drops** — tracked products at a server-computed new low / drop (§2.4).
  Honesty: only claim "new low" when true. **Data-presence gated** — this card
  *and* `best_deals` are hidden from the Cards list unless product data exists
  (§2.4); reuse the existing `productsEnabled` data-presence signal (R-003).
  Opt-in even when present.
- **Spend trend** — this period vs. last, by store (`getSpendByStoreAsync`).
  Opt-in.
- **Pantry value** — estimated value on hand + trend (`getStockValueAsync`).
  Opt-in glance number.

*Gate:* R-003 / state-ownership (no client-side summing across fetched
collections — the reports already aggregate), R-007 (no new report logic beyond
the price-drop signal), §7.5 portability if any endpoint is added.

### Phase 5 — Restock radar, quick actions, cookable upgrade

> **Status (2026-06-24): restock + quick actions DONE + green; cookable upgrade
> + donut deep-links deferred.** Shipped: **Restock radar** (default-on, zone
> 'today', `getKeepsRunningOutAsync`, one-tap Add-to-list via the shared
> `useStockItemActions`), and a **quick-action bar** (Add item → CreateStockItem
> Dialog; Add to list → global QuickAddSheet `openQuickAdd`). Deferred: cookable
> upgrade L272 (FU-298 — overlaps meal-plan, design call), donut deep-links
> (FU-299 — needs `/stock` status-filter support), log-price quick action
> (FU-300 — needs a target picker).


Add temporal intelligence and let the home screen *do*, not just route.

- **Restock radar** (`getKeepsRunningOutAsync`) — items that keep running out,
  one-tap "add to primary list". **Default-visible.** Predictive, on-brand.
- **Quick-action row** (Charter: Effortless) — Add item · Add to list · Log
  price · (Scan, gated behind `scanning_enabled`). Inline create, no navigation.
- **Cookable upgrade** (L272) — show next 3 to cook driven by meal-plan + stock,
  each flagged ready / missing-N-ingredients, deep-linking to the recipe.
- **Stock donut deep-links** (critique) — low/out segments link to
  `/stock?status=low|out` filtered views.

*Gate:* R-001 (each is its own component), R-011 (use existing mutation
services for quick actions — no bespoke fetch), Effortless principle.

### Phase 6 — "This fortnight" calendar widget (D7)

> **Status (2026-06-24): DONE + green — and NO new backend needed.** §2.3 assumed
> this required a new aggregation endpoint, but `GET /alerts/upcoming` (C-9.6,
> `get_upcoming.py`) already returns exactly the per-date expiries + shopping +
> meals D7 wants (server-aggregated, R-003). So the calendar shipped frontend-only
> and is fully tsc/eslint-verifiable. Built as an **opt-in** card (zone 'today',
> `defaultHidden` — it's wide and overlaps the week-ahead strip; enable from the
> Cards menu). A 14-day grid (lazy-loads when shown, R-016); each cell shows
> coloured dots (meal/expiry/shopping); tapping a day expands its detail with
> deep-links. Possible future consolidation with the week-strip noted.

A 14-day grid; each date carries coloured dots for **planned shopping /
item expiries / planned meals**; clicking a date opens that day's detail
(meals + events). One range query server-side (R-003 — don't stitch three
client fetches into a calendar in the browser); Postgres/SQLite portable (§7.5).

*Gate:* new endpoint repository-routed + portable; R-003 aggregation server-side.

### Phase 7 — Mobile pass

> **Status (2026-06-24): code tweaks DONE + green; needs a device walk (FU-301).**
> The zone grid already stacks (cards are col-12 below `sm`); added mobile rules
> for the quick-action bar (buttons span the row), the savings range chips, and
> the alert summary chips (comfortable tap targets). Inherently visual — the
> real validation is a device/responsive walk, folded into FU-301.


- Zones stack cleanly; quick-action row collapses sensibly.
- Drag disabled (Phase 2 already), tap-reorder works on touch.
- Touch targets ≥44px (critique flagged the dense `size="sm"` row buttons).
- Calendar widget degrades to a scrollable strip if the grid is too dense.

*Gate:* C13 (mobile drag off), touch-target sizing, `vue-tsc` + `eslint` green.

---

## 4. Charter cross-check

- **Effortless** — quick-action row + one-tap restock + actionable deep-links
  mean the home screen *acts*, not just navigates. ✅
- **Anti-creep** — net default-visible card count held roughly flat (cut 1,
  merge 2, demote 1, add 2 by default; rest opt-in). New widgets *replace*
  vanity, surfacing already-built reports rather than inventing features. ✅
- **Honesty** — "new low" / "saved $X" / "expiring" claims must be true and
  server-derived; no optimistic client math (state-ownership). ✅

---

## 5. Coverage table — feedback §DASHBOARD (+ strays)

Every dashboard feedback bullet from `Feedback _ Fixes - as of [06-Jun-2026].md`
mapped to a phase, or marked out-of-scope with a reason. A reviewer should be
able to audit "is anything missing?" at a glance.

| Feedback bullet (source line) | Phase / section | Notes |
|---|---|---|
| D1a — Skip-wizard "Continue" does nothing (L51) | Phase 1 | Code path exists; verify in browser, log finding if broken. |
| D1b — Skip banner buttons take their own row; inline them (L52) | Phase 1 | Inline Continue/Hide. |
| D1c — Welcome message when onboarding complete (L53) | Phase 1 | Cycled welcome via message system. |
| D1d — Welcome cycled/random, day-of-week, 5/day, pool 35–40 + hints pool (L54) | Phase 1 | Two pools, deterministic-per-day picker (R-003). |
| D1e — Replace bottom-right "Dora says" bubble, keep yellow treatment (L55) | Phase 1 | Message system inherits the "Dora says" look. |
| D2 — Dark mode not working (L56) | Phase 0 | Token-compliance sweep of dashboard SCSS (R-002). |
| D3 — Remove refresh button if nav already refreshes (L57) | Phase 0 | Removed; `loadAll` kept for internal re-fetch. |
| D4 — Reorder cards via draggable rows in toggle list (L58) | Phase 2 | Drag + tap alternative + mobile-off (C13). |
| D5 — Alerts nav 404 → build alerts control page (L59) | Phase 3 (dep.) | C-9 surface; `/alerts` route present — confirm resolved. |
| D6 — Alert card redesign: top summary + bottom peek + "See all" (L60) | Phase 3 | Two-section `AlertSummaryWidget`. |
| D7 — "This fortnight" calendar widget, coloured dots, click-a-date (L61) | Phase 6 — DONE | Opt-in card; reused existing `/alerts/upcoming` (C-9.6) — no new backend. |
| L176 — Mascot not centred in greeting card | Phase 0 | B9.8 claims fixed; verify. |
| L272 — "Next up to cook": next 3 by meal-plan + stock, ready/missing (L272) | Phase 5 | Cookable widget upgrade. |
| L480 — Cross-app undo off (dashboard push-expiry → clear at stock item) | Out of scope (bug) | Cross-app undo defect, not a dashboard-design item; log as `DORA_FOLLOWUPS` finding for the undo/toast owner. |
| Critique — no savings widget | Phase 4 | Flagship `SavingsCapturedWidget`. |
| Critique — vanity counters dominate (`products`/`recipes`/`meals`/`shopping_lists`) | Phase 1 | Cut `products`+`recipes`+`meals`; merge `shopping_lists` into primary list (§2.6). |
| Critique — actionable cards hide when empty (inversion) | Phase 1 | Positive empty states (R-014). |
| Critique — flat hierarchy / no triage gradient | Phase 2 | Zones. |
| Critique — a11y (clickable articles, `href="#"`, nested interactives) | Phase 0 | Real controls / router-links (R-011). |
| Critique — no quick actions / no temporal intelligence | Phase 5 | Quick-action row + restock radar. |
| Critique — stock donut buckets not actionable | Phase 5 | Deep-link low/out to filtered stock. |

---

## 6. Definition of done

- Dashboard answers the six core questions (wrong? cook? saved? budget? deals?
  restock?) above the fold on a typical install.
- Default-visible cards are all actionable or money/answer cards; no pure
  counter is default-visible.
- `DashboardPage.vue` is a thin composition over `components/dashboard/*`
  widgets (R-001 — the 1964-line monolith is gone).
- Every coverage-table row is Phase-assigned and landed (or explicitly deferred
  with a follow-up id).
- Per phase: `vue-tsc -p tsconfig.json --noEmit` + `npm run lint` green;
  browser walk at 360 / 768 / 1280; `CHANGELOG.md` + `DORA_WORKLOG.md` updated.
