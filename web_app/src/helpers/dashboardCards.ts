// The dashboard's card registry: which cards exist, what zone each lives in,
// what gates it, and whether it starts visible.
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
// Pure data + types only. No component logic, no reactivity — the page still
// owns visibility state, ordering, persistence and rendering. This is the first
// slice of the R-001 extraction that FU-829 finishes.

import { ICONS } from 'src/style/icons';

export type ZoneId = 'act' | 'today' | 'money' | 'kitchen';

export type CardId =
    | 'attention'
    | 'primary_list'
    // 'act' zone — the "draft this week's shop" card. It's a real, registered,
    // rendered card, but its id was once missing from this union — an R-010
    // closed-set gap that broke `vue-tsc` and hard-failed `quasar build`
    // (FU-550).
    | 'draft_shop'
    | 'suggestions'
    | 'cookable'
    | 'stock_items'
    // FU-818 — "What's coming": the 7-day strip and the 14-day fortnight
    // calendar merged into this one id. The retired `calendar` id is dropped by
    // the page's `parseLayout`, which filters a stored layout to known ids.
    | 'meal_plan'
    // Phase 4 — Money zone widgets backed by the reports API. FU-830 folded the
    // old `budget` id into `savings` and cut `best_deals`; both are gone from
    // this union, so a stored layout naming them is filtered out.
    | 'savings'
    | 'spend_trend'
    | 'pantry_value'
    | 'price_drops'
    // Phase 5 — predictive restock.
    | 'restock'
    // Kitchen-health score (top of the Your-kitchen zone).
    | 'dora_score'
    // FU-317 Chunk 5 — reconcile past meals nudge. Hide-when-empty (R-029): the
    // component renders nothing when the queue is empty.
    | 'reconcile_pending';

export type CardGate = 'money' | 'products';

export type CardDef = {
    id: CardId;
    label: string;
    icon: string;
    zone: ZoneId;
    /** Opt-in-by-default cards (Anti-creep, §2.2) start hidden — e.g. the
     *  secondary Money-zone glance widgets (spend trend, pantry value). */
    defaultHidden?: boolean;
    /** Feature gate: the card is unavailable (hidden from the dashboard AND the
     *  Cards menu) unless its gate is on. `money` → `useMoneyEnabled` (any
     *  dollar surface, ADR-005); `products` → product data-presence (§2.4 —
     *  don't offer product widgets to users with no products). */
    gate?: CardGate;
};

/** Zones group cards into purpose-bands so the eye gets a triage gradient
 *  (Phase 2). They're fixed — a card belongs to one zone; the user reorders
 *  *within* a zone and toggles visibility. Render order = zone order, then the
 *  user's order within each zone. */
export const ZONES: { id: ZoneId; label: string }[] = [
    { id: 'act', label: 'Act now' },
    { id: 'today', label: 'Today' },
    { id: 'money', label: 'Money' },
    { id: 'kitchen', label: 'Your kitchen' },
];

/**
 * The default order within each zone (and the Cards-menu order). A user's saved
 * order overrides it.
 *
 * ⚠️ **The default-visible count is a resolved decision, not a free choice.**
 * §2.2 set it so the dashboard "looks focused out of the box"; the owner amended
 * it on 2026-09-02 to *merges only, no demotions*, which lands it at **11**
 * (10 in practice — `reconcile_pending` is hide-when-empty).
 *
 * So **adding a card without `defaultHidden` reopens that decision.** Either
 * mark the new card `defaultHidden: true`, or get the count re-agreed and update
 * `DEFAULT_VISIBLE_COUNT` deliberately. The spec asserts it, which is the
 * mechanism §2.2 never had.
 */
export const CARD_DEFS: CardDef[] = [
    { id: 'attention', label: 'Needs your attention', icon: ICONS.notifications_active, zone: 'act' },
    // FU-351 — P6-10 one-click "Draft my shop" entry point. Sits in the `act`
    // zone (the home screen *does*) between Attention and Suggestions. Reuses
    // the /auto-generate engine with sensible defaults.
    { id: 'draft_shop', label: 'Draft this week\'s shop', icon: ICONS.playlist_add_check, zone: 'act' },
    { id: 'suggestions', label: 'Dora suggests', icon: ICONS.dora_voice, zone: 'act' },
    { id: 'cookable', label: 'Cookable tonight', icon: ICONS.restaurant_menu, zone: 'today' },
    // FU-818 — absorbed the opt-in `calendar` card. Keeps the `meal_plan` id so
    // a saved layout keeps its slot in the user's order.
    { id: 'meal_plan', label: 'What\'s coming', icon: ICONS.calendar_month, zone: 'today' },
    { id: 'primary_list', label: 'Primary shopping list', icon: ICONS.shopping_cart, zone: 'today' },
    { id: 'restock', label: 'Restock radar', icon: ICONS.replay, zone: 'today' },
    // Money zone. FU-810/830 — one spend-led card: the budget bar when a target
    // exists, kept-vs-RRP as the supporting line. It absorbed the separate
    // `budget` card, which was the other half of the same sentence (budget knew
    // the target; savings recomputed spend from a second endpoint, and the two
    // could show different windows side by side). Money-gated (FU-297) — even
    // the no-target body states dollars.
    { id: 'savings', label: 'Grocery spend', icon: ICONS.savings, zone: 'money', gate: 'money' },
    // Product-data-gated (FU-296) — surfaces only genuine new lows so the claim
    // "price drop" is honest (§2.4). Opt-in like the other secondary money
    // widgets.
    //
    // FU-819 — `best_deals` was CUT. It rendered the identical `.dora-deal-row`
    // anatomy behind the same gate, differing only in ranking (biggest % off RRP
    // vs. a server-verified new low), so a user with both on saw two visually
    // identical lists with no explanation of why there were two. Price drops is
    // the claim Dora can stand behind. `discountPercent` survives as a per-offer
    // display helper — one offer's % off its own ticket is a shelf-price
    // question and stays legitimate (ADR-068).
    { id: 'price_drops', label: 'Price drops', icon: ICONS.trending_down, zone: 'money', gate: 'products', defaultHidden: true },
    { id: 'spend_trend', label: 'Spend by store', icon: ICONS.storefront, zone: 'money', gate: 'money', defaultHidden: true },
    { id: 'pantry_value', label: 'Pantry value', icon: ICONS.inventory, zone: 'money', gate: 'money', defaultHidden: true },
    // Sits above 'Pantry' in the Kitchen zone by default: the composite score is
    // the summary, the pantry donut the detail underneath. `favorite` (♥) reads
    // as "health" and isn't used elsewhere on the dashboard.
    { id: 'dora_score', label: 'Kitchen health', icon: ICONS.favorite, zone: 'kitchen' },
    // FU-317 Chunk 5 — dashboard nudge for the meal-plan reconcile queue. The
    // component renders nothing when the queue is empty (R-029), so no
    // `defaultHidden` — the component itself is the gate.
    { id: 'reconcile_pending', label: 'Reconcile past meals', icon: ICONS.event_note, zone: 'kitchen' },
    { id: 'stock_items', label: 'Pantry', icon: 'inventory_2', zone: 'kitchen' },
];

/**
 * How many cards a fresh install shows with every gate satisfied — the number
 * §2.2 owns. Asserted in the spec so it can only change on purpose.
 *
 * 11 registered-and-visible; **10 in practice**, because `reconcile_pending`
 * additionally hides itself when the queue is empty.
 */
export const DEFAULT_VISIBLE_COUNT = 11;
