import type { WasteReason } from 'src/services/api/wasteApiService';
import { ICONS } from 'src/style/icons';

/**
 * C-waste — single source of truth for the waste-reason vocabulary
 * shared across the Mark-as-wasted modal (tile labels) and the
 * StockItemDetail history timeline (lowercase humaniser).
 *
 * The reason list mirrors `WASTE_REASON_*` on the backend
 * (`stock_item_waste_event.py`); add new reasons there first.
 */

export type WasteReasonTile = {
    reason: WasteReason;
    label: string;
    icon: string;
};

// Order matters: this is the tile-grid order in the modal. The first
// four reasons sit in a 2-col grid; "Other" gets a full-width row
// below them (see MarkAsWastedDialog.vue).
export const WASTE_REASON_TILES: readonly WasteReasonTile[] = [
    { reason: 'expired', label: 'Expired', icon: ICONS.wasteExpired },
    { reason: 'spoiled', label: 'Spoiled', icon: ICONS.wasteSpoiled },
    { reason: 'did_not_like', label: "Didn't like", icon: ICONS.wasteDidNotLike },
    { reason: 'overbought', label: 'Bought too much', icon: ICONS.wasteOverbought },
    { reason: 'other', label: 'Other', icon: ICONS.wasteOther },
];

// Lowercase for inline use in the StockItemDetail timeline ("Wasted: expired").
const TIMELINE_LABELS: Record<WasteReason, string> = {
    expired: 'expired',
    spoiled: 'spoiled',
    did_not_like: "didn't like",
    overbought: 'overbought',
    other: 'other reason',
};

export function humaniseWasteReason(reason: string): string {
    return TIMELINE_LABELS[reason as WasteReason] ?? reason;
}
