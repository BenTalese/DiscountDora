// The dashboard's card registry: which cards exist, what gates each one, and
// whether it starts visible.
//
// Extracted from `DashboardPage.vue` (FU-830) for one concrete reason: the
// default-visible count is a *resolved decision* and it needs a mechanism that
// holds it. `IMPL_PLAN_DASHBOARD_REBUILD.md` §2.2 fixed that count with the
// owner in June 2026; by September it had drifted from 8 to 13 of 17, because
// three later features each shipped without `defaultHidden` and nothing —
// no test, no comment, no trigger to reopen §2.2 — noticed. That is the finding
// of `DASHBOARD_PAGE_REVIEW.md` §3.1, and a registry buried in a 3200-line SFC
// cannot be asserted against. Now it can (`test/unit/dashboardCards.spec.ts`).
//
// ## Zones were removed (owner, 2026-09-04)
//
// Cards used to be grouped into four fixed purpose-bands (`act` / `today` /
// `money` / `kitchen`) with reorder allowed only *within* a band. The same
// feedback batch that cut six cards killed the grouping: *"with how many widgets
// we're axing, I don't think we need the groupings. Allow the user to reorder
// the cards however they want."* Ten cards do not need a triage gradient — the
// gradient was carrying six that no longer exist. So the order is now one flat
// list the user owns end to end, and the grid parity maths runs once over the
// whole list rather than per band.
//
// Pure data + types only. No component logic, no reactivity — the page still
// owns visibility state, ordering, persistence and rendering.

import { ICONS } from 'src/style/icons';

export type CardId =
    // The next meals worth cooking. Renamed from `cookable` in the 09-04 batch:
    // the id said "cookable tonight" and the card has rendered "Next to cook"
    // since FU-298, and it now switches selection strategy on the household's
    // cook style, which "cookable" actively misdescribes.
    | 'next_to_cook'
    // One of the two cards that replaced `attention` + `suggestions` (owner,
    // 09-04). It answers a cross-entity question the alerts bell and the chat
    // can't: "what's about to go off that I could cook now". Its sibling
    // `before_you_shop` was cut on 09-08 — see the deletion note below.
    | 'use_it_up'
    | 'stock_items'
    // FU-818 — "What's coming": the 7-day strip and the 14-day fortnight
    // calendar merged into this one id. The retired `calendar` id is dropped by
    // the page's `parseLayout`, which filters a stored layout to known ids.
    | 'meal_plan'
    // Phase 4 — Money zone widgets backed by the reports API. FU-830 folded the
    // old `budget` id into `savings` and cut `best_deals`; the 09-04 batch cut
    // `spend_trend` and `pantry_value` (see the deletion note below).
    //
    // `my_budget` since 09-08, because the card is now only that: the owner cut
    // its kept-vs-RRP half and its swaps line and retitled it "My budget", and
    // an id saying `savings` on a card that states no savings is exactly the
    // drift this file exists to stop. `savings` is retired like any other id —
    // `parseLayout` drops it — the same trade `cookable` → `next_to_cook` made
    // in the 09-04 batch.
    //
    // **`my_budget`, not `budget`**, and that is not a stylistic choice:
    // `budget` is *already* a retired id (FU-830 folded a separate "Grocery
    // budget" card into `savings`), so it is sitting in stored layouts today.
    // Reusing it would hand this card some users' old hidden flag — the exact
    // resurrection `dashboardCards.spec.ts`'s retired-id list exists to catch,
    // and it caught this.
    | 'my_budget'
    | 'price_drops'
    // Phase 5 — predictive restock.
    | 'restock'
    // Kitchen-health score.
    | 'dora_score';

// ── Cards deleted in the 2026-09-04 owner batch ──────────────────────────
//
// Recorded here rather than silently dropped, because R-057 treats a replaced
// surface's contracts as an inventory to check, not a casualty list. A stored
// layout naming any of these is filtered out by the page's `parseLayout`.
//
//   `attention`          Needs your attention   — same content as the alerts
//                        bell, one nav row above it.
//   `suggestions`        Dora suggests          — same content as the Dora chat,
//                        which is on the same screen.
//                        Both replaced by `use_it_up` + `before_you_shop`.
//   `draft_shop`         Draft this week's shop — a single button whose whole
//                        job the shopping-list page does better, with the user
//                        able to see what the list is being built from.
//   `spend_trend`        Spend by store         — a report, and Reports has it.
//                        The dashboard and the reports page shouldn't overlap.
//   `pantry_value`       Pantry value           — the same judgement the reports
//                        review already reached about stock valuation.
//
// ── Cards deleted in the 2026-09-08 owner batch ──────────────────────────
//
//   `before_you_shop`    Before you shop        — *"There's a lot of crossover
//                        between before you shop and restock radar. I'm
//                        inclined to axe before you shop and chuck 'planned' as
//                        a chip on the rows for restock radar."* Done exactly
//                        that: `restock` rows carry `is_planned` now, and
//                        `/dashboard/before-you-shop` is deleted with its only
//                        consumer. The one thing this loses is the "already on
//                        a list" filter — logged as FU-897, not dropped
//                        silently.
//   `shopping_lists`     Shopping lists         — *"Shopping lists widget is
//                        useless, axe it."* `/dashboard/lists` went with it; the
//                        nav's own Shopping lists entry is the way there, which
//                        is the same reasoning that cut the header links off
//                        every remaining card in this batch.
//
//   `reconcile_pending`  Reconcile past meals   — a bare button card. Meal
//                        reconciliation is now the `plan_adherence` component
//                        of Kitchen health, and *that* row is the link to go and
//                        do it: a metric that explains why you'd bother, instead
//                        of a nag that doesn't.

export type CardGate = 'money' | 'products';

export type CardDef = {
    id: CardId;
    label: string;
    icon: string;
    /** Opt-in-by-default cards (Anti-creep, §2.2) start hidden. */
    defaultHidden?: boolean;
    /** Feature gate: the card is unavailable (hidden from the dashboard AND the
     *  Cards menu) unless its gate is on. `money` → `useMoneyEnabled` (any
     *  dollar surface, ADR-005); `products` → the products feature flag (§2.4 —
     *  don't offer product widgets to an install that has products off). */
    gate?: CardGate;
};

/**
 * The default order (and the Cards-menu order). A user's saved order overrides
 * it, and — since zones went — that saved order spans the whole list.
 *
 * ⚠️ **The default-visible count is a resolved decision, not a free choice.**
 * §2.2 set it so the dashboard "looks focused out of the box"; adding a card
 * without `defaultHidden` reopens that decision. Either mark the new card
 * `defaultHidden: true`, or get the count re-agreed and update
 * `DEFAULT_VISIBLE_COUNT` deliberately. The spec asserts it.
 *
 * Ordering intent: **kitchen health first** (owner, 2026-09-08 — *"feels like
 * its default ordering should be first"*). It is the one card that answers "how
 * are we doing?" rather than "what's next?", and every other card is a way of
 * acting on one of its five signals. Then the things to *do today* (cook, use
 * up), then the week, then restock, then the standing stock view, then money.
 * No band labels — the order itself is the gradient now.
 */
export const CARD_DEFS: CardDef[] = [
    { id: 'dora_score', label: 'Kitchen health', icon: ICONS.favorite },
    { id: 'next_to_cook', label: 'Next to cook', icon: ICONS.restaurant_menu },
    { id: 'use_it_up', label: 'Use it up', icon: ICONS.expiry },
    { id: 'meal_plan', label: 'What\'s coming', icon: ICONS.calendar_month },
    { id: 'restock', label: 'Restock radar', icon: ICONS.replay },
    // `ICONS.inventory_2`, not the bare string 'inventory_2'. The app's icon set
    // is MDI; a raw Material Icons ligature name doesn't resolve and Quasar
    // renders it as literal text — "inventory_2 My stock" was showing on the
    // card header and in the Cards menu. Caught in the 2026-09-04 browser walk;
    // it predates this batch (the card was "Pantry" then).
    { id: 'stock_items', label: 'My stock', icon: ICONS.inventory_2 },
    // FU-810/830 made this one spend-led card with kept-vs-RRP as its
    // supporting line. The 09-08 batch cut that line — *"remove the bottom part
    // 'kept vs RRP', product data is a niche area of the app"* — and the swaps
    // bullet with it, so what remains is the budget and nothing else. Hence
    // both the title and the id. Money-gated (FU-297): every figure is dollars.
    { id: 'my_budget', label: 'My budget', icon: ICONS.savings, gate: 'money' },
    // Products-gated (owner 09-04: *"ensure it's gated behind products feature
    // enabled"*). Surfaces only genuine new lows so the claim "price drop" is
    // honest (§2.4). Opt-in like the other secondary money widgets.
    { id: 'price_drops', label: 'Price drops', icon: ICONS.trending_down, gate: 'products', defaultHidden: true },
];

/**
 * How many cards a fresh install shows with every gate satisfied — the number
 * §2.2 owns. Asserted in the spec so it can only change on purpose.
 *
 * Seven: the eight registered cards less `price_drops`, which is opt-in. It was
 * nine until the 09-08 batch cut `before_you_shop` and `shopping_lists`. Every
 * one of the seven renders unconditionally — the 09-04 batch removed the last
 * hide-when-empty card (`reconcile_pending`), so "registered and visible" and
 * "actually on screen" are the same number.
 */
export const DEFAULT_VISIBLE_COUNT = 7;
