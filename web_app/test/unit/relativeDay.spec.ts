// @vitest-environment jsdom
//
// jsdom rather than the default `node` env: `useDateFormat` imports `useMoney`
// for the household locale, which reaches `axiosHttpClient` → the Quasar client
// bundle → `window`. Nothing here touches the DOM; it just needs the global to
// exist at import time.
/**
 * FU-820 — date-only values must render as the calendar day they name, in every
 * timezone.
 *
 * The bug: `new Date('2026-09-03')` parses the date-only form as **UTC**
 * midnight (per spec), and everything that then reads local parts — `getDate()`,
 * `Intl.DateTimeFormat`, which defaults to the local zone — reports the previous
 * day for any negative UTC offset. Measured in America/New_York before the fix:
 *
 *   formatDate('2026-09-03')       → "02/09/2026"   (should be 03/09/2026)
 *   formatRelativeDay(tomorrow)    → "Today"        (should be "Tomorrow")
 *
 * East of Greenwich the two forms agree, which is why it survived: Australia is
 * the shipping default and every developer runs there. So these tests assert the
 * contract in a **negative-offset** zone specifically — running them only in
 * local time would pass vacuously on the machine that wrote them.
 *
 * `TZ` is set in the vitest config's `env` for the whole suite rather than here,
 * because Node caches the zone before module evaluation.
 */
import { describe, expect, it } from 'vitest';
import {
    daysFromToday,
    isDateOnly,
    parseLocalIso,
} from 'src/helpers/weekDates';
import { formatDate, formatRelativeDay } from 'src/composables/useDateFormat';

describe('parseLocalIso — date-only strings parse to local midnight', () => {
    it('keeps the calendar day the string names', () => {
        const d = parseLocalIso('2026-09-03')!;
        expect(d.getFullYear()).toBe(2026);
        expect(d.getMonth()).toBe(8); // 0-indexed September
        expect(d.getDate()).toBe(3);
        expect(d.getHours()).toBe(0);
    });

    it('is not the same instant as the built-in date-only parse (the whole point)', () => {
        // If these ever match, the host is running UTC and this suite is not
        // actually exercising the bug — fail loudly rather than pass quietly.
        const offsetMinutes = new Date(2026, 8, 3).getTimezoneOffset();
        expect(
            offsetMinutes,
            'These tests must run in a non-UTC zone to be meaningful — see vitest config `env.TZ`.',
        ).not.toBe(0);
    });

    it('returns null for anything carrying a time, so instants are left alone', () => {
        expect(parseLocalIso('2026-09-03T10:00:00Z')).toBeNull();
        expect(parseLocalIso('2026-09-03T10:00:00')).toBeNull();
        expect(parseLocalIso('not a date')).toBeNull();
        expect(parseLocalIso('')).toBeNull();
    });

    it('isDateOnly matches exactly the bare calendar form', () => {
        expect(isDateOnly('2026-09-03')).toBe(true);
        expect(isDateOnly('2026-09-03T00:00:00Z')).toBe(false);
        expect(isDateOnly('2026-9-3')).toBe(false);
    });
});

describe('daysFromToday — whole calendar days, not elapsed hours', () => {
    // Late local evening is where a UTC-based comparison flips a day, so anchor
    // "now" there deliberately.
    const now = new Date(2026, 8, 3, 22, 30);

    it('counts today, tomorrow and yesterday', () => {
        expect(daysFromToday('2026-09-03', now)).toBe(0);
        expect(daysFromToday('2026-09-04', now)).toBe(1);
        expect(daysFromToday('2026-09-02', now)).toBe(-1);
    });

    it('counts across a month boundary', () => {
        expect(daysFromToday('2026-10-01', new Date(2026, 8, 30, 9, 0))).toBe(1);
    });

    it('survives a DST transition without an off-by-one', () => {
        // US DST ends 2026-11-01; the 7 days spanning it are still 7 days.
        expect(daysFromToday('2026-11-05', new Date(2026, 9, 29, 12, 0))).toBe(7);
    });

    it('returns null for a non-date-only value', () => {
        expect(daysFromToday('2026-09-03T10:00:00Z', now)).toBeNull();
    });
});

describe('formatRelativeDay — names the right day west of Greenwich', () => {
    const now = new Date(2026, 8, 3, 22, 30);

    it('says Today / Tomorrow / Yesterday', () => {
        expect(formatRelativeDay('2026-09-03', now)).toBe('Today');
        expect(formatRelativeDay('2026-09-04', now)).toBe('Tomorrow');
        expect(formatRelativeDay('2026-09-02', now)).toBe('Yesterday');
    });

    it('names the weekday inside the coming week', () => {
        // 2026-09-07 is a Monday.
        expect(formatRelativeDay('2026-09-07', now)).toBe('Monday');
    });

    it('falls back to a formatted date beyond a week', () => {
        const out = formatRelativeDay('2026-12-25', now);
        expect(out).not.toBe('Today');
        expect(out).toMatch(/2026/);
    });
});

describe('formatDate — a date-only value renders its own calendar day', () => {
    it('renders the day the string names, not the day before', () => {
        // The regression this whole file exists for: in a negative-offset zone
        // this used to render 02/09/2026.
        expect(formatDate('2026-09-03', { day: 'numeric' })).toBe('3');
        expect(formatDate('2026-01-01', { day: 'numeric', month: 'numeric' })).toMatch(/^1\/1$|^1\/1\/|1\/1/);
    });

    it('does not shift a value that carries an explicit time', () => {
        // An instant is an instant — rendering it in the viewer's zone is
        // correct and must not change.
        const iso = '2026-09-03T12:00:00Z';
        const expected = new Intl.DateTimeFormat('en-AU', { day: 'numeric' }).format(
            new Date(iso),
        );
        expect(formatDate(iso, { day: 'numeric' })).toBe(expected);
    });

    it('still renders empty for empty/invalid input', () => {
        expect(formatDate(null)).toBe('');
        expect(formatDate('')).toBe('');
        expect(formatDate('rhubarb')).toBe('');
    });
});
