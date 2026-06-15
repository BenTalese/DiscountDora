import { ICONS } from 'src/style/icons';
// Mirrors AlertDto/AlertsDto from dora_api/features/alerts/get_alerts.py.

export type AlertSeverity = 'high' | 'medium' | 'low';

// C-9.2 — which count bucket an alert falls in: 'actionable' drives the bell
// badge, 'fyi' is shown but never counted into it.
export type AlertTier = 'actionable' | 'fyi';

export type AlertKind =
    | 'expired'
    | 'expiring_soon'
    | 'out_of_stock'
    | 'low_stock'
    | 'stocktake_overdue'
    | 'essential_low';

export type Alert = {
    // Stable scoped key `<scope>:<id>:<kind>` — opaque to the client; posted
    // back to the read/snooze/dismiss endpoints. (Named alert_id for history.)
    alert_id: string;
    kind: AlertKind;
    severity: AlertSeverity;
    stock_item_id: string;
    stock_item_name: string;
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
    }
}

export function colorFor(severity: AlertSeverity): string {
    if (severity === 'high') return 'red-6';
    if (severity === 'medium') return 'orange-7';
    return 'amber-7';
}

// Per-kind accent colour (C-9.3) — a stable visual identity per kind for the
// summary boxes (L224), distinct from the severity-driven row avatar above.
// Quasar palette names, matching colorFor's convention.
export function colorForKind(kind: AlertKind): string {
    switch (kind) {
        case 'expired':
            return 'red-6';
        case 'essential_low':
            return 'deep-orange-6';
        case 'expiring_soon':
            return 'orange-7';
        case 'out_of_stock':
            return 'purple-5';
        case 'low_stock':
            return 'amber-7';
        case 'stocktake_overdue':
            return 'blue-grey-6';
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
    }
}
