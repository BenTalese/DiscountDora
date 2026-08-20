// FU-034 substitute ratio caption, in one place.
//
// Three surfaces render a substitute's ratio: the stock-item detail page's
// substitute list, cook mode's swap picker, and the recipe page's per-row
// substitute popover. Two of them carried byte-identical private copies of
// this function, each with a comment saying it "mirrors" the other — which is
// what an R-003 violation looks like just before it becomes three copies.
//
// The API always returns the ratio oriented "this item → substitute", so the
// direction never has to be reasoned about here.

import { formatQuantity } from 'src/helpers/formatQuantity';
import type { Substitute } from 'src/models/stockItemDetail';

/** Compact `1 tsp → 1 tbsp` caption. Null when no ratio is recorded — all
 *  four ratio fields are set together or not at all. */
export function formatSubstituteRatio(sub: Substitute): string | null {
    if (sub.ratio_quantity_in == null || sub.ratio_unit_in == null
        || sub.ratio_quantity_out == null || sub.ratio_unit_out == null) {
        return null;
    }
    const from = formatQuantity(sub.ratio_quantity_in, sub.ratio_unit_in);
    const to = formatQuantity(sub.ratio_quantity_out, sub.ratio_unit_out);
    return `${from} → ${to}`;
}
