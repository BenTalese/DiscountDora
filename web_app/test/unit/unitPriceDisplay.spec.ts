import { describe, expect, it } from 'vitest';

import {
    displayDenominatorFor,
    quoteUnitPrice,
    requoteUnitPrice,
    toCanonicalPriceUnit,
} from 'src/helpers/unitPriceDisplay';

// The convention is generated from `dora_api/domain/units.py`; these pin the
// client's *reading* of it — that a price entered in grams comes back quoted
// per 100g rather than per gram, which is the whole point of the helper.

describe('toCanonicalPriceUnit', () => {
    it('rebases onto the dimension canonical price unit, not the base unit', () => {
        expect(toCanonicalPriceUnit(500, 'g')).toEqual({ amount: 0.5, dimension: 'mass' });
        expect(toCanonicalPriceUnit(750, 'ml')).toEqual({ amount: 0.75, dimension: 'volume' });
        expect(toCanonicalPriceUnit(2, 'kg')).toEqual({ amount: 2, dimension: 'mass' });
        expect(toCanonicalPriceUnit(6, 'ea')).toEqual({ amount: 6, dimension: 'count' });
    });

    it('returns null for a unit the table does not know', () => {
        expect(toCanonicalPriceUnit(1, 'furlong')).toBeNull();
    });
});

describe('displayDenominatorFor', () => {
    it('quotes metric per 100g / 100ml whatever the pack size', () => {
        expect(displayDenominatorFor('mass', 0.5, 'metric').label).toBe('100g');
        expect(displayDenominatorFor('mass', 2, 'metric').label).toBe('100g');
        expect(displayDenominatorFor('volume', 0.5, 'metric').label).toBe('100ml');
        expect(displayDenominatorFor('volume', 2, 'metric').label).toBe('100ml');
    });

    it('follows the install measurement system', () => {
        expect(displayDenominatorFor('mass', 1, 'us').label).toBe('lb');
        expect(displayDenominatorFor('mass', 0.1, 'us').label).toBe('oz');
        // The UK prices metric on the shelf even though it cooks in ounces.
        expect(displayDenominatorFor('mass', 0.5, 'imperial').label).toBe('100g');
    });

    it('leaves count alone', () => {
        expect(displayDenominatorFor('count', 6, 'metric')).toEqual({ label: 'ea', factor: 1 });
    });
});

describe('quoteUnitPrice', () => {
    it('quotes a sub-kilo pack per 100g rather than per gram', () => {
        // The owner's case: $3.50 for 500 g read "$0.01 per g".
        expect(quoteUnitPrice(3.5, 500, 'g', 'metric')).toEqual({ amount: 0.7, unit: '100g' });
    });

    it('quotes a full-kilo pack per 100g', () => {
        expect(quoteUnitPrice(6.9, 1, 'kg', 'metric')).toEqual({ amount: expect.closeTo(0.69, 10), unit: '100g' });
    });

    it('quotes a bottle and a big one both per 100ml', () => {
        expect(quoteUnitPrice(8.75, 500, 'ml', 'metric')).toEqual({ amount: 1.75, unit: '100ml' });
        expect(quoteUnitPrice(4, 2, 'L', 'metric')).toEqual({ amount: 0.2, unit: '100ml' });
    });

    it('leaves count prices as a plain each', () => {
        expect(quoteUnitPrice(6, 12, 'ea', 'metric')).toEqual({ amount: 0.5, unit: 'ea' });
    });

    it('returns null rather than a price per something it cannot name', () => {
        expect(quoteUnitPrice(3.5, 500, 'furlong', 'metric')).toBeNull();
        expect(quoteUnitPrice(3.5, 0, 'g', 'metric')).toBeNull();
    });
});

describe('requoteUnitPrice', () => {
    it('scales a per-gram price up to the shelf denominator', () => {
        const quoted = requoteUnitPrice(0.004, 'g', 'metric');
        expect(quoted?.unit).toBe('100g');
        expect(quoted?.amount).toBeCloseTo(0.4, 10);
    });

    it('requotes a per-kg price per 100g and leaves each alone', () => {
        expect(requoteUnitPrice(6.9, 'kg', 'metric')).toEqual({ amount: expect.closeTo(0.69, 10), unit: '100g' });
        expect(requoteUnitPrice(2.5, 'ea', 'metric')).toEqual({ amount: 2.5, unit: 'ea' });
    });
});
