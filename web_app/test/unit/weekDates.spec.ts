// FU-520 workstream 1 — unit coverage for the meal-planner week/date helpers.
//
// `weekDates.ts` exists to kill the C-2.K bug class: local-Date →
// `toISOString()` drifts a day in positive-offset timezones near midnight.
// The helpers therefore do pure UTC math on YYYY-MM-DD strings — which makes
// them fully deterministic and testable without touching the machine's zone.
// `localTodayIso()` is the one deliberately-local escape hatch (R-021
// carve-out, display-only) — we only pin its *shape*, since its value depends
// on the machine timezone by design.
import { describe, expect, it } from 'vitest';

import { isoDate, localTodayIso, mondayOf, shiftDays } from 'src/helpers/weekDates';

describe('isoDate — normalising to YYYY-MM-DD', () => {
    it('passes a bare date string through unchanged', () => {
        expect(isoDate('2026-07-10')).toBe('2026-07-10');
    });

    it('strips the time from a UTC datetime string', () => {
        expect(isoDate('2026-07-10T09:30:00.000Z')).toBe('2026-07-10');
        expect(isoDate('2026-07-10T23:59:59Z')).toBe('2026-07-10');
    });

    it('resolves an offset datetime to its UTC calendar date', () => {
        // 01:00 +10 is 15:00 UTC the previous day.
        expect(isoDate('2026-07-10T01:00:00+10:00')).toBe('2026-07-09');
    });
});

describe('shiftDays — day arithmetic on date strings', () => {
    it('shifts forward within a month', () => {
        expect(shiftDays('2026-07-10', 3)).toBe('2026-07-13');
    });

    it('shifts backward with a negative count', () => {
        expect(shiftDays('2026-07-10', -10)).toBe('2026-06-30');
    });

    it('rolls over month boundaries', () => {
        expect(shiftDays('2026-07-31', 1)).toBe('2026-08-01');
        expect(shiftDays('2026-03-01', -1)).toBe('2026-02-28');
    });

    it('rolls over year boundaries', () => {
        expect(shiftDays('2026-12-31', 1)).toBe('2027-01-01');
        expect(shiftDays('2026-01-01', -1)).toBe('2025-12-31');
    });

    it('handles leap-year February', () => {
        expect(shiftDays('2028-02-28', 1)).toBe('2028-02-29');
        expect(shiftDays('2028-03-01', -1)).toBe('2028-02-29');
    });

    it('is a no-op at zero days', () => {
        expect(shiftDays('2026-07-10', 0)).toBe('2026-07-10');
    });
});

describe('mondayOf — ISO week start', () => {
    // 2026-07-06 is a Monday.
    const MONDAY = '2026-07-06';

    it('returns the same day for a Monday', () => {
        expect(mondayOf(MONDAY)).toBe(MONDAY);
    });

    it('snaps every mid-week day back to that Monday', () => {
        expect(mondayOf('2026-07-07')).toBe(MONDAY); // Tue
        expect(mondayOf('2026-07-08')).toBe(MONDAY); // Wed
        expect(mondayOf('2026-07-09')).toBe(MONDAY); // Thu
        expect(mondayOf('2026-07-10')).toBe(MONDAY); // Fri
        expect(mondayOf('2026-07-11')).toBe(MONDAY); // Sat
    });

    it('treats Sunday as the END of the week (ISO), not the start', () => {
        expect(mondayOf('2026-07-12')).toBe(MONDAY); // Sun → previous Monday
    });

    it('crosses a month boundary when the Monday is in the previous month', () => {
        // 2026-08-01 is a Saturday; its ISO week starts Monday 2026-07-27.
        expect(mondayOf('2026-08-01')).toBe('2026-07-27');
    });

    it('accepts a datetime string and normalises it first', () => {
        expect(mondayOf('2026-07-09T10:00:00Z')).toBe(MONDAY);
    });
});

describe('localTodayIso — display-only local today (R-021 carve-out)', () => {
    it('emits a YYYY-MM-DD string', () => {
        // The exact value is machine-timezone-dependent BY DESIGN (it paints
        // the first-frame "today" cell before the server hydrates), so we pin
        // only the shape here — never the value.
        expect(localTodayIso()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
});
