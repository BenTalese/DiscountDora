// FU-378 — the action-first Stock Overview scan mode. These cover the pure
// decision logic: building the Scan-button action menu from the live level
// rows, and mapping a barcode lookup result + chosen level into the per-item
// scan feedback. No Vue, no camera, no store — so it lives in the unit corpus
// alongside supportChannel / doraIntents.
import { describe, expect, it } from 'vitest';

import {
    buildScanActionOptions,
    resolveScanLevelOutcome,
} from 'src/helpers/scanActions';
import type { StockLevel } from 'src/models/stockLevel';
import type { BarcodeLookupResult } from 'src/services/api/barcodeApiService';

const LEVELS: StockLevel[] = [
    { stock_level_id: 'l0', name: 'Well stocked', sequence: 0 },
    { stock_level_id: 'l1', name: 'Running low', sequence: 1 },
    { stock_level_id: 'l2', name: 'Out', sequence: 2 },
];

describe('buildScanActionOptions', () => {
    it('leads with "Open stock item", then one entry per level in order', () => {
        const options = buildScanActionOptions(LEVELS);
        expect(options).toHaveLength(4);

        expect(options[0]!.action).toEqual({ kind: 'open' });
        expect(options[0]!.label).toBe('Open stock item');
        expect(options[0]!.sequence).toBeUndefined();

        expect(options[1]!.label).toBe('Set to Well stocked');
        expect(options[1]!.sequence).toBe(0);
        expect(options[1]!.action).toEqual({
            kind: 'level',
            levelId: 'l0',
            levelName: 'Well stocked',
        });

        expect(options[3]!.action).toEqual({
            kind: 'level',
            levelId: 'l2',
            levelName: 'Out',
        });
    });

    it('uses the level rows\' custom names (no hardcoded literals)', () => {
        const renamed: StockLevel[] = [
            { stock_level_id: 'x', name: 'Heaps left', sequence: 0 },
        ];
        const options = buildScanActionOptions(renamed);
        expect(options[1]!.label).toBe('Set to Heaps left');
    });

    it('with no levels configured, still offers "Open stock item"', () => {
        const options = buildScanActionOptions([]);
        expect(options).toHaveLength(1);
        expect(options[0]!.action).toEqual({ kind: 'open' });
        expect(options[0]!.label).toBe('Open stock item');
    });
});

describe('resolveScanLevelOutcome', () => {
    const nameFor = (id: string) => (id === 'si-1' ? 'Milk' : undefined);

    it('resolves a directly-registered stock item and builds the "<name> → <level>" message', () => {
        const result: BarcodeLookupResult = { kind: 'stock_item', id: 'si-1' };
        const outcome = resolveScanLevelOutcome(result, 'Well stocked', nameFor);
        expect(outcome).toEqual({
            stockItemId: 'si-1',
            message: 'Milk → Well stocked',
            ok: true,
        });
    });

    it('resolves a stock item reached via a product', () => {
        const result: BarcodeLookupResult = {
            kind: 'stock_item_via_product',
            id: 'si-1',
            product_id: 'p1',
            barcode_id: 'b1',
        };
        const outcome = resolveScanLevelOutcome(result, 'Out', nameFor);
        expect(outcome.ok).toBe(true);
        expect(outcome.stockItemId).toBe('si-1');
        expect(outcome.message).toBe('Milk → Out');
    });

    it('falls back to "Item" when the name is not in the local cache', () => {
        const result: BarcodeLookupResult = { kind: 'stock_item', id: 'si-unknown' };
        const outcome = resolveScanLevelOutcome(result, 'Running low', nameFor);
        expect(outcome.ok).toBe(true);
        expect(outcome.message).toBe('Item → Running low');
    });

    it('cannot act on a product with no linked stock item', () => {
        const result: BarcodeLookupResult = {
            kind: 'product_no_link',
            product_id: 'p1',
            barcode_id: 'b1',
        };
        const outcome = resolveScanLevelOutcome(result, 'Out', nameFor);
        expect(outcome.ok).toBe(false);
        expect(outcome.stockItemId).toBeNull();
        expect(outcome.message).toMatch(/no pantry item/i);
    });

    it('cannot act on a genuinely unknown barcode', () => {
        const result: BarcodeLookupResult = { kind: 'unknown', value: '9999' };
        const outcome = resolveScanLevelOutcome(result, 'Out', nameFor);
        expect(outcome.ok).toBe(false);
        expect(outcome.stockItemId).toBeNull();
        expect(outcome.message).toMatch(/add it/i);
    });
});
