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
    | 'shopping_day';

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

// Icon per kind so the panel rows render consistently.
export function iconFor(kind: AlertKind): string {
    switch (kind) {
        case 'expired':
            return ICONS.event_busy;
        case 'expiring_soon':
            return ICONS.schedule;
        case 'out_of_stock':
            return ICONS.remove_shopping_cart;
        case 'low_stock':
            return ICONS.trending_down;
        case 'stocktake_overdue':
            return ICONS.fact_check;
        case 'essential_low':
            return ICONS.priority_high;
        case 'no_planned_meals':
            return ICONS.restaurant;
        case 'shopping_day':
            return ICONS.shopping_cart;
    }
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
// Some kinds intentionally reuse severity-ladder tokens where the semantic
// overlaps (expired ⇒ critical, expiring_soon ⇒ medium, low_stock ⇒ low,
// essential_low ⇒ high); the rest have their own categorical accents.
export function colorForKind(kind: AlertKind): string {
    switch (kind) {
        case 'expired':
            return 'severity-critical';
        case 'essential_low':
            return 'severity-high';
        case 'expiring_soon':
            return 'severity-medium';
        case 'out_of_stock':
            return 'alert-kind-out-of-stock';
        case 'low_stock':
            return 'severity-low';
        case 'stocktake_overdue':
            return 'alert-kind-stocktake-overdue';
        case 'no_planned_meals':
            return 'alert-kind-no-planned-meals';
        case 'shopping_day':
            return 'alert-kind-shopping-day';
    }
}

// Plain-language theme for the summary boxes, e.g. "5 expiring soon".
export function kindTheme(kind: AlertKind): string {
    switch (kind) {
        case 'expired':
            return 'expired';
        case 'expiring_soon':
            return 'expiring soon';
        case 'out_of_stock':
            return 'out of stock';
        case 'low_stock':
            return 'low stock';
        case 'essential_low':
            return 'essential low';
        case 'stocktake_overdue':
            return 'stocktake due';
        case 'no_planned_meals':
            return 'meals to plan';
        case 'shopping_day':
            return 'shopping day';
    }
}

// The two count tiers (C-9.2). Actionable drives the badge; FYI is shown but
// uncounted. Used for the hub's tier group headers + the manage panel.
export function tierLabel(tier: AlertTier): string {
    return tier === 'actionable' ? 'Needs action' : 'FYI';
}

// Actions the user can take inline. The set varies by alert kind — e.g.
// "Mark restocked" makes no sense for an expiry alert.
export function actionsFor(kind: AlertKind): { action: AlertAction; label: string; icon: string }[] {
    switch (kind) {
        case 'expired':
        case 'expiring_soon':
            return [
                { action: 'extend_expiry', label: 'Push 7 days', icon: ICONS.event_repeat },
                { action: 'reset_expiry', label: 'Clear expiry', icon: ICONS.event_busy },
            ];
        case 'out_of_stock':
        case 'low_stock':
        case 'essential_low':
            return [
                { action: 'mark_restocked', label: 'Mark restocked', icon: ICONS.inventory },
            ];
        case 'stocktake_overdue':
            return [
                { action: 'acknowledge_stocktake', label: 'Looks fine', icon: ICONS.check },
            ];
        case 'no_planned_meals':
        case 'shopping_day':
            // Navigation-only nudges — acting on them means opening the linked
            // surface (linkFor), not a server-side state change.
            return [];
    }
}

// Where opening an alert (row click / "View in context") navigates. Stock kinds
// go to the item; the C-9.4 nudges deep-link to their surface — shopping_day to
// the list (target_id), no_planned_meals to the planner. Routing lives client-
// side (presentation); the server only supplies the ids.
export function linkFor(alert: Alert): string | null {
    switch (alert.kind) {
        case 'no_planned_meals':
            return '/meal-plans';
        case 'shopping_day':
            return alert.target_id ? `/shopping-lists/${alert.target_id}` : '/shopping-lists';
        default:
            return alert.stock_item_id ? `/stock/${alert.stock_item_id}` : null;
    }
}
