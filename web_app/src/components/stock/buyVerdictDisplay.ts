// Display helpers shared by `BuyVerdictCard` and `BuyVerdictBadge`.
//
// Both surfaces render the same `reasons` array — the card expanded, the badge
// inside its popover — so the per-reason icon and detail line have to agree.
// `axisIcon` was already copy-pasted into both (R-003 drift); rather than add
// `reasonDetail` as a second copy, both now live here.

import { formatMoney } from 'src/composables/useMoney';
import type { BuyVerdictReason } from 'src/services/api/buyVerdictApiService';
import { ICONS } from 'src/style/icons';

export function axisIcon(axis: BuyVerdictReason['axis']): string {
    if (axis === 'price') return ICONS.price_check ?? 'mdi-cash-check';
    if (axis === 'need') return ICONS.inventory_2 ?? 'mdi-package-variant-closed';
    return ICONS.delete_outline ?? 'mdi-delete-outline';
}

/** The reason's sub-line, or '' when it has none.
 *
 *  Price-axis reasons arrive as two raw numbers rather than a prose `detail`,
 *  because the server does not format currency (D-006) — it used to emit a
 *  hardcoded `$12.34`, which showed a dollar sign to a household on EUR.
 *  Composing the line here runs both amounts through the install's
 *  currency + locale formatter. Every other axis just carries `detail`. */
export function reasonDetail(reason: BuyVerdictReason): string {
    const last = reason.amount_last;
    if (last !== null && last !== undefined) {
        return `${formatMoney(last)} last shop · usually ${formatMoney(reason.amount_usual)}`;
    }
    return reason.detail ?? '';
}
