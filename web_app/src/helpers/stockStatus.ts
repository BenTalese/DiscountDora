// Client-side mirror of the canonical stock-status contract owned by
// `dora_api/domain/stock_status.py`. Status is keyed to a stock level's
// ordinal `sequence`, never its display name — renaming a level in the UI
// must not change behaviour anywhere. The constants here are the same
// sequence values the server seeds (and the `StockStatus` IntEnum maps to).
//
// Prefer reading derived booleans (`is_out_of_stock`, `is_low_stock`,
// `needs_restock`) straight off a stock-item or ingredient DTO; reach for
// the helpers below only when you have a bare sequence number or a
// StockLevel row.

export const STOCKED_SEQUENCE = 0;
export const LOW_STOCK_SEQUENCE = 1;
export const OUT_OF_STOCK_SEQUENCE = 2;

type WithSequence = { sequence: number };

function sequenceOf(level: WithSequence | number | null | undefined): number | null {
    if (level === null || level === undefined) return null;
    return typeof level === 'number' ? level : level.sequence;
}

export function isOutOfStockSequence(level: WithSequence | number | null | undefined): boolean {
    const seq = sequenceOf(level);
    return seq !== null && seq >= OUT_OF_STOCK_SEQUENCE;
}

export function isLowStockSequence(level: WithSequence | number | null | undefined): boolean {
    return sequenceOf(level) === LOW_STOCK_SEQUENCE;
}

export function needsRestockSequence(level: WithSequence | number | null | undefined): boolean {
    const seq = sequenceOf(level);
    return seq !== null && seq >= LOW_STOCK_SEQUENCE;
}

/** Find the level row whose sequence matches the canonical status —
 *  use this whenever the client must *assign* a level (e.g. "mark used" →
 *  out-of-stock), so a custom-renamed seed row still resolves correctly. */
export function findLevelBySequence<T extends WithSequence>(
    levels: readonly T[],
    sequence: number,
): T | undefined {
    return levels.find((l) => l.sequence === sequence);
}
