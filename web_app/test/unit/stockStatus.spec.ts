// FU-520 workstream 1 — unit coverage for the canonical stock-status contract.
//
// `stockStatus.ts` mirrors `dora_api/domain/stock_status.py`: status is keyed
// to a level's ordinal `sequence`, never its display name — renaming a level
// must not change behaviour. `stockLevelLogic.ts` layers the sequence-keyed
// colour rule on top. Both are pinned here because every stock surface
// (overview, detail, pickers, shopping-list rows) branches on them.
//
// Pure functions only — no Vue, no network (see vitest.config.ts).
import { describe, expect, it } from 'vitest';

import { colourForSequence } from 'src/helpers/stockLevelLogic';
import {
    findLevelBySequence,
    isLowStockSequence,
    isOutOfStockSequence,
    LOW_STOCK_SEQUENCE,
    needsRestockSequence,
    OUT_OF_STOCK_SEQUENCE,
    STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';

describe('stock-status sequence helpers', () => {
    it('pins the canonical seeded sequence values', () => {
        // These mirror what the server seeds — a change here is a breaking
        // contract change, not a refactor.
        expect(STOCKED_SEQUENCE).toBe(0);
        expect(LOW_STOCK_SEQUENCE).toBe(1);
        expect(OUT_OF_STOCK_SEQUENCE).toBe(2);
    });

    it('classifies stocked / low / out from a bare sequence number', () => {
        expect(isOutOfStockSequence(STOCKED_SEQUENCE)).toBe(false);
        expect(isOutOfStockSequence(LOW_STOCK_SEQUENCE)).toBe(false);
        expect(isOutOfStockSequence(OUT_OF_STOCK_SEQUENCE)).toBe(true);

        expect(isLowStockSequence(STOCKED_SEQUENCE)).toBe(false);
        expect(isLowStockSequence(LOW_STOCK_SEQUENCE)).toBe(true);
        expect(isLowStockSequence(OUT_OF_STOCK_SEQUENCE)).toBe(false);
    });

    it('treats sequences beyond "out" (custom levels) as still out-of-stock', () => {
        expect(isOutOfStockSequence(3)).toBe(true);
        expect(isOutOfStockSequence(99)).toBe(true);
    });

    it('needs-restock is low OR out (and anything beyond)', () => {
        expect(needsRestockSequence(STOCKED_SEQUENCE)).toBe(false);
        expect(needsRestockSequence(LOW_STOCK_SEQUENCE)).toBe(true);
        expect(needsRestockSequence(OUT_OF_STOCK_SEQUENCE)).toBe(true);
        expect(needsRestockSequence(5)).toBe(true);
    });

    it('accepts a StockLevel-shaped row as well as a bare number', () => {
        expect(isLowStockSequence({ sequence: LOW_STOCK_SEQUENCE })).toBe(true);
        expect(isOutOfStockSequence({ sequence: OUT_OF_STOCK_SEQUENCE })).toBe(true);
        expect(needsRestockSequence({ sequence: STOCKED_SEQUENCE })).toBe(false);
    });

    it('is safely false for null / undefined (unknown level)', () => {
        expect(isOutOfStockSequence(null)).toBe(false);
        expect(isOutOfStockSequence(undefined)).toBe(false);
        expect(isLowStockSequence(null)).toBe(false);
        expect(needsRestockSequence(undefined)).toBe(false);
    });
});

describe('findLevelBySequence — resolving a level row by canonical status', () => {
    const LEVELS = [
        { stock_level_id: 'lv-stocked', name: 'Plenty', sequence: 0 },
        { stock_level_id: 'lv-low', name: 'Running low', sequence: 1 },
        { stock_level_id: 'lv-out', name: 'None left', sequence: 2 },
    ];

    it('finds a renamed seed row by sequence, ignoring the display name', () => {
        expect(findLevelBySequence(LEVELS, OUT_OF_STOCK_SEQUENCE)?.stock_level_id).toBe('lv-out');
        expect(findLevelBySequence(LEVELS, STOCKED_SEQUENCE)?.name).toBe('Plenty');
    });

    it('returns undefined when no row carries the sequence', () => {
        expect(findLevelBySequence(LEVELS, 7)).toBeUndefined();
        expect(findLevelBySequence([], STOCKED_SEQUENCE)).toBeUndefined();
    });
});

describe('colourForSequence — sequence-keyed level palette', () => {
    it('maps stocked → positive and low → negative', () => {
        expect(colourForSequence(STOCKED_SEQUENCE)).toBe('positive');
        expect(colourForSequence(LOW_STOCK_SEQUENCE)).toBe('negative');
    });

    it('returns null for out-of-stock so callers route the neutral theme token (R-002)', () => {
        expect(colourForSequence(OUT_OF_STOCK_SEQUENCE)).toBeNull();
    });

    it('returns null for unknown / custom / missing sequences', () => {
        expect(colourForSequence(42)).toBeNull();
        expect(colourForSequence(null)).toBeNull();
        expect(colourForSequence(undefined)).toBeNull();
    });
});
