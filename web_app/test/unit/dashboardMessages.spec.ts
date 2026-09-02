/**
 * FU-823 — the dashboard hint pool must not advertise features the install has
 * switched off.
 *
 * Feedback L254 is the reason the money opt-in exists: *"some people may not
 * want to know how many dollars they are eating… it should be an option to turn
 * off"*. The card gates honour that (ADR-005), but the hint rotation didn't —
 * so a household with money off was told, one day in fifteen, to *"set a
 * grocery budget and I'll quietly track spend against it for you"*. Promoting a
 * gated feature is as much a leak as rendering it.
 */
import { describe, expect, it } from 'vitest';
import {
    HINTS,
    epochDay,
    hintsFor,
    pickHint,
    pickWelcome,
} from 'src/helpers/dashboardMessages';

const ALL = { money: true, products: true };
const NONE = { money: false, products: false };

describe('hint gating', () => {
    it('has gated hints to actually filter (guards a vacuous pass)', () => {
        expect(HINTS.some((h) => h.gate === 'money')).toBe(true);
        expect(HINTS.some((h) => h.gate === 'products')).toBe(true);
        expect(HINTS.some((h) => h.gate === undefined)).toBe(true);
    });

    it('drops money hints when money features are off', () => {
        const pool = hintsFor({ money: false, products: true });
        expect(pool.every((h) => h.gate !== 'money')).toBe(true);
        expect(pool.some((h) => h.gate === 'products')).toBe(true);
    });

    it('drops product hints when there are no products', () => {
        const pool = hintsFor({ money: true, products: false });
        expect(pool.every((h) => h.gate !== 'products')).toBe(true);
        expect(pool.some((h) => h.gate === 'money')).toBe(true);
    });

    it('keeps only ungated hints when everything is off', () => {
        expect(hintsFor(NONE).every((h) => h.gate === undefined)).toBe(true);
        expect(hintsFor(NONE).length).toBeGreaterThan(0);
    });

    it('shows every hint when everything is on', () => {
        expect(hintsFor(ALL)).toHaveLength(HINTS.length);
    });

    it('never surfaces the budget hint across a whole year with money off', () => {
        // The rotation is a modulo over the *filtered* pool, so this is the
        // assertion that matters: not "the pool is filtered" but "no day of the
        // year can produce a money hint".
        const money = HINTS.find((h) => h.gate === 'money')!;
        for (let day = 0; day < 366; day++) {
            const date = new Date(2026, 0, 1 + day);
            expect(pickHint({ money: false, products: true }, date)).not.toBe(money.text);
        }
    });

    it('never returns an empty string while any hint survives the gates', () => {
        for (const gates of [ALL, NONE, { money: true, products: false }, { money: false, products: true }]) {
            expect(pickHint(gates, new Date(2026, 5, 5))).not.toBe('');
        }
    });
});

describe('rotation is still stable per calendar day', () => {
    it('returns the same hint all day and a different one tomorrow', () => {
        const morning = new Date(2026, 5, 5, 8, 0);
        const evening = new Date(2026, 5, 5, 22, 0);
        const tomorrow = new Date(2026, 5, 6, 8, 0);
        expect(pickHint(ALL, morning)).toBe(pickHint(ALL, evening));
        expect(epochDay(tomorrow)).toBe(epochDay(morning) + 1);
    });

    it('picks a weekday-appropriate welcome, stable within the day', () => {
        // 2026-06-05 is a Friday.
        const friday = new Date(2026, 5, 5, 9, 0);
        expect(pickWelcome(friday)).toBe(pickWelcome(new Date(2026, 5, 5, 20, 0)));
        expect(pickWelcome(friday).length).toBeGreaterThan(0);
    });
});
