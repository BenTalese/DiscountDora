// FU-378 — action-first Stock Overview scan mode. The user picks an action
// FIRST (open the item, or set it to a stock level), then scans items to
// apply it in a loop. This module holds the *pure* decision logic so the
// branch/message contract is unit-testable without a camera or a store; the
// StockOverview page owns the reactive wiring + the actual mutation.

import type { BarcodeLookupResult } from 'src/services/api/barcodeApiService';
import type { StockLevel } from 'src/models/stockLevel';

/** The action a scan applies. `open` keeps the legacy jump-to-detail
 *  behaviour; `level` sets every scanned item to a chosen stock level
 *  (covers the stocktake "scan-to-check" case — decision §7a #4). */
export type ScanAction =
    | { kind: 'open' }
    | { kind: 'level'; levelId: string; levelName: string };

/** One entry in the Scan button's action menu. */
export interface ScanActionOption {
    action: ScanAction;
    label: string;
    /** Level sequence for the colour dot; undefined for the `open` action. */
    sequence?: number;
}

/** Build the Scan-button action menu: "open details" first, then one
 *  "Set to <name>" per configured stock level (ordered as passed in, i.e.
 *  by sequence). Keyed off the level rows so a renamed seed level shows its
 *  custom name — never a hardcoded "Out of Stock" literal (R-003). */
export function buildScanActionOptions(levels: readonly StockLevel[]): ScanActionOption[] {
    const options: ScanActionOption[] = [
        { action: { kind: 'open' }, label: 'Open stock item' },
    ];
    for (const level of levels) {
        options.push({
            action: { kind: 'level', levelId: level.stock_level_id, levelName: level.name },
            label: `Set to ${level.name}`,
            sequence: level.sequence,
        });
    }
    return options;
}

export interface ScanLevelOutcome {
    /** Stock item to apply the level to, or null when the scan can't act. */
    stockItemId: string | null;
    /** Feedback message for the scan banner. */
    message: string;
    /** Whether the scan resolved to an actionable pantry item. */
    ok: boolean;
}

/** Decide what a level-set scan should do given the barcode lookup result.
 *  Pure: the caller resolves the item name (via `nameFor`) and performs the
 *  mutation. A `product_no_link` / `unknown` result can't be acted on in the
 *  scan loop — we report it and keep scanning rather than derailing into the
 *  add-item flow (that's the `open` action's / FU-373's job). */
export function resolveScanLevelOutcome(
    result: BarcodeLookupResult,
    levelName: string,
    nameFor: (id: string) => string | undefined,
): ScanLevelOutcome {
    if (result.kind === 'stock_item' || result.kind === 'stock_item_via_product') {
        const name = nameFor(result.id) ?? 'Item';
        return { stockItemId: result.id, message: `${name} → ${levelName}`, ok: true };
    }
    if (result.kind === 'product_no_link') {
        return {
            stockItemId: null,
            message: 'Known product, but no pantry item is linked to it yet.',
            ok: false,
        };
    }
    // `unknown` — not in Dora at all.
    return {
        stockItemId: null,
        message: 'Not a recognised item — add it to your pantry first.',
        ok: false,
    };
}
