import { ICONS } from 'src/style/icons';
// Mirrors AlertDto/AlertsDto from dora_api/features/alerts/get_alerts.py.

export type AlertSeverity = 'high' | 'medium' | 'low';

// which count bucket an alert falls in: 'actionable' drives the bell
// badge, 'fyi' is shown but never counted into it.
export type AlertTier = 'actionable' | 'fyi';

export type AlertKind =
    | 'expired'
    | 'expiring_soon'
    | 'out_of_stock'
    | 'low_stock'
    | 'stocktake_overdue'
    | 'essential_low'
    // forward-looking nudges (no stock item).
    | 'no_planned_meals'
    | 'shopping_day'
    | 'meal_reconcile_overdue';

export type Alert = {
    // Stable scoped key `<scope>:<id>:<kind>` — opaque to the client; posted
    // back to the read/snooze/dismiss endpoints. (Named alert_id for history.)
    alert_id: string;
    kind: AlertKind;
    severity: AlertSeverity;
    // Stock-scoped alerts carry the owning item; C-9.4 non-stock kinds null these.
    stock_item_id: string | null;
    stock_item_name: string | null;
    // Deep-link target id for non-stock kinds (e.g. the shopping list uuid).
    target_id: string | null;
    message: string;
    detail: string | null;
    related_date: string | null;
    // Per-user interaction overlay (C-9.1, server-derived).
    read: boolean;
    snoozed_until: string | null;
    // Effective tier for this user (C-9.2): 'actionable' (badge) or 'fyi'.
    // Per-kind default, overridable via alert prefs — server-derived.
    tier: AlertTier;
};

export type Alerts = {
    items: Alert[];          // active (not snoozed, not dismissed)
    snoozed: Alert[];        // snoozed by this user
    high_count: number;      // active severity counts (caption)
    medium_count: number;
    low_count: number;
    actionable_count: number; // active high+medium — the bell badge
    fyi_count: number;        // active low
    snoozed_count: number;
};

// Per-user, per-kind preference (C-9.2). Mirrors AlertPrefDto from
// dora_api/features/alerts/manage_alert_prefs.py.
export type AlertPref = {
    kind: AlertKind;
    enabled: boolean;
    tier_override: AlertTier | null;
    default_tier: AlertTier;
    effective_tier: AlertTier;
};

export type AlertPrefs = {
    prefs: AlertPref[];
};

export type UpdateAlertPrefCommand = {
    kind: AlertKind;
    enabled?: boolean;
    tier_override?: AlertTier | null;
};

// Alert history (C-9.3) — the audit trail of the user's decisions, mirrors
// AlertHistoryEntryDto from dora_api/features/alerts/get_alert_history.py.
export type AlertHistoryState = 'dismissed' | 'snoozed' | 'read';

export type AlertHistoryEntry = {
    alert_key: string;
    kind: string;
    label: string;
    state: AlertHistoryState;
    at: string;
    stock_item_id: string | null;
    snoozed_until: string | null;
};

export type AlertHistory = {
    entries: AlertHistoryEntry[];
};

// Upcoming "this fortnight" timeline (C-9.6) — mirrors UpcomingDto from
// dora_api/features/alerts/get_upcoming.py. A server-owned aggregation (R-003);
// the client only renders the grid + per-category dots.
export type UpcomingCategory = 'expiry' | 'shopping' | 'meal';

export type UpcomingExpiry = { stock_item_id: string; name: string };
export type UpcomingShopping = { list_id: string; name: string };
export type UpcomingMeal = { recipe_id: string; recipe_name: string; slot: string };

export type UpcomingDay = {
    date: string;                 // ISO date
    expiries: UpcomingExpiry[];
    shopping: UpcomingShopping[];
    meals: UpcomingMeal[];
};

export type Upcoming = {
    start: string;                // household-today (first grid cell)
    end: string;                  // last day (inclusive)
    days: number;                 // window length
    dates: UpcomingDay[];         // non-empty days only
};

export type AlertAction =
    | 'reset_expiry'
    | 'extend_expiry'
    | 'mark_restocked'
    | 'acknowledge_stocktake';

export type AlertActionOption = { action: AlertAction; label: string; icon: string };

// The per-kind presentation contract. Every AlertKind has exactly one row —
// `Record<AlertKind, …>` makes TS reject a new kind that forgets one (FU-521:
// this is what was missing when `meal_reconcile_overdue` was added on the
// backend and five separate switch sites silently fell through). Add a kind =
// extend the union + add one row here; the accessors below need no edit.
export type AlertKindMeta = {
    icon: string;      // panel row / avatar icon
    color: string;     // categorical accent for summary boxes (class-suffix)
    theme: string;     // plain-language label, e.g. "expiring soon"
    actions: AlertActionOption[];  // inline actions this kind offers (empty = nav-only nudge)
    // Deep-link for the non-stock nudge kinds. Stock kinds omit it and fall back
    // to the item route in `linkFor`. A function because `shopping_day` needs the id.
    link?: (alert: Alert) => string;
};

// Inline actions, shared by the kinds that offer the same set.
const EXPIRY_ACTIONS: AlertActionOption[] = [
    { action: 'extend_expiry', label: 'Push 7 days', icon: ICONS.event_repeat },
    { action: 'reset_expiry', label: 'Clear expiry', icon: ICONS.event_busy },
];
const RESTOCK_ACTIONS: AlertActionOption[] = [
    { action: 'mark_restocked', label: 'Mark restocked', icon: ICONS.inventory },
];
const STOCKTAKE_ACTIONS: AlertActionOption[] = [
    { action: 'acknowledge_stocktake', label: 'Looks fine', icon: ICONS.check },
];

// Colours: some kinds intentionally reuse severity-ladder tokens where the
// semantic overlaps (expired ⇒ critical, expiring_soon ⇒ medium, low_stock ⇒
// low, essential_low ⇒ high); the rest have their own categorical accents.
// `meal_reconcile_overdue` reuses the FYI-tier low accent (a dedicated token
// could be added if its visual identity needs one).
export const ALERT_KIND_META: Record<AlertKind, AlertKindMeta> = {
    expired:                { icon: ICONS.event_busy,           color: 'severity-critical',            theme: 'expired',            actions: EXPIRY_ACTIONS },
    expiring_soon:          { icon: ICONS.schedule,             color: 'severity-medium',              theme: 'expiring soon',      actions: EXPIRY_ACTIONS },
    out_of_stock:           { icon: ICONS.remove_shopping_cart, color: 'alert-kind-out-of-stock',      theme: 'out of stock',       actions: RESTOCK_ACTIONS },
    low_stock:              { icon: ICONS.trending_down,        color: 'severity-low',                 theme: 'low stock',          actions: RESTOCK_ACTIONS },
    stocktake_overdue:      { icon: ICONS.fact_check,           color: 'alert-kind-stocktake-overdue', theme: 'stocktake due',      actions: STOCKTAKE_ACTIONS },
    essential_low:          { icon: ICONS.priority_high,        color: 'severity-high',                theme: 'essential low',      actions: RESTOCK_ACTIONS },
    no_planned_meals:       { icon: ICONS.restaurant,           color: 'alert-kind-no-planned-meals',  theme: 'meals to plan',      actions: [], link: () => '/meal-plans' },
    shopping_day:           { icon: ICONS.shopping_cart,        color: 'alert-kind-shopping-day',      theme: 'shopping day',       actions: [], link: (a) => (a.target_id ? `/shopping-lists/${a.target_id}` : '/shopping-lists') },
    meal_reconcile_overdue: { icon: ICONS.playlist_add_check,   color: 'severity-low',                 theme: 'meals to reconcile', actions: [], link: () => '/meal-plans/reconcile' },
};

// Icon per kind so the panel rows render consistently. The `?.` fallbacks in
// these accessors are load-bearing: the backend can ship a new AlertKind before
// the frontend knows it (that's the 2026-07-09 crash), so an unmapped kind must
// degrade to a blank/nav-only row, never throw (regression-pinned in
// test/unit/alertRow.spec.ts "unknown alert kind degrades safely").
export function iconFor(kind: AlertKind): string {
    // FU-531: an unmapped kind (backend shipped ahead of the client) falls back
    // to a generic bell rather than an empty circle — "degraded but safe" should
    // still look intentional.
    return ALERT_KIND_META[kind]?.icon ?? ICONS.notifications;
}

// Severity ladder — returned string is the class-suffix Quasar's `color` prop
// consumes (`bg-<name>` / `text-<name>`). Matching utility classes live in
// `web_app/src/css/colours.scss` and read from the tokens in tokens.scss.
// was Quasar numbered palette (red-6/orange-7/amber-7);
// now theme-aware via `light-dark()` tokens.
export function colorFor(severity: AlertSeverity): string {
    if (severity === 'high') return 'severity-critical';
    if (severity === 'medium') return 'severity-medium';
    return 'severity-low';
}

// Per-kind accent colour (C-9.3) — a stable visual identity per kind for the
// summary boxes (L224), distinct from the severity-driven row avatar above.
export function colorForKind(kind: AlertKind): string {
    return ALERT_KIND_META[kind]?.color ?? '';
}

// Plain-language theme for the summary boxes, e.g. "5 expiring soon".
export function kindTheme(kind: AlertKind): string {
    return ALERT_KIND_META[kind]?.theme ?? '';
}

// The two count tiers (C-9.2). Actionable drives the badge; FYI is shown but
// uncounted. Used for the hub's tier group headers + the manage panel.
export function tierLabel(tier: AlertTier): string {
    return tier === 'actionable' ? 'Needs action' : 'FYI';
}

// Actions the user can take inline. The set varies by alert kind — e.g.
// "Mark restocked" makes no sense for an expiry alert. Nav-only nudges return [].
export function actionsFor(kind: AlertKind): AlertActionOption[] {
    return ALERT_KIND_META[kind]?.actions ?? [];
}

// Where opening an alert (row click / "View in context") navigates. The C-9.4
// nudges deep-link to their surface via the META `link`; stock kinds fall back
// to the item. Routing lives client-side (presentation); the server only
// supplies the ids.
export function linkFor(alert: Alert): string | null {
    const meta = ALERT_KIND_META[alert.kind];
    if (meta?.link) return meta.link(alert);
    return alert.stock_item_id ? `/stock/${alert.stock_item_id}` : null;
}
