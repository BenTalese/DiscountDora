// Mirrors AlertDto/AlertsDto from dora_api/features/alerts/get_alerts.py.

export type AlertSeverity = 'high' | 'medium' | 'low';

export type AlertKind =
    | 'expired'
    | 'expiring_soon'
    | 'out_of_stock'
    | 'low_stock'
    | 'stocktake_overdue'
    | 'essential_low';

export type Alert = {
    alert_id: string;
    kind: AlertKind;
    severity: AlertSeverity;
    stock_item_id: string;
    stock_item_name: string;
    message: string;
    detail: string | null;
    related_date: string | null;
};

export type Alerts = {
    items: Alert[];
    high_count: number;
    medium_count: number;
    low_count: number;
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
            return 'event_busy';
        case 'expiring_soon':
            return 'schedule';
        case 'out_of_stock':
            return 'remove_shopping_cart';
        case 'low_stock':
            return 'trending_down';
        case 'stocktake_overdue':
            return 'fact_check';
        case 'essential_low':
            return 'priority_high';
    }
}

export function colorFor(severity: AlertSeverity): string {
    if (severity === 'high') return 'red-6';
    if (severity === 'medium') return 'orange-7';
    return 'amber-7';
}

// Actions the user can take inline. The set varies by alert kind — e.g.
// "Mark restocked" makes no sense for an expiry alert.
export function actionsFor(kind: AlertKind): { action: AlertAction; label: string; icon: string }[] {
    switch (kind) {
        case 'expired':
        case 'expiring_soon':
            return [
                { action: 'extend_expiry', label: 'Push 7 days', icon: 'event_repeat' },
                { action: 'reset_expiry', label: 'Clear expiry', icon: 'event_busy' },
            ];
        case 'out_of_stock':
        case 'low_stock':
        case 'essential_low':
            return [
                { action: 'mark_restocked', label: 'Mark restocked', icon: 'inventory' },
            ];
        case 'stocktake_overdue':
            return [
                { action: 'acknowledge_stocktake', label: 'Looks fine', icon: 'check' },
            ];
    }
}
