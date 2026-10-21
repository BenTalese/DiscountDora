// Week/date helpers shared by the meal planner page + its calendar widget
// (R-003: one source for the week-date logic). Every function builds a
// YYYY-MM-DD string from explicit calendar parts and uses UTC math — never
// `toISOString()` on a *local* Date, which is UTC-shifted and drifts a day in
// positive-offset zones near midnight (the C-2.K bug class).

/** Normalise any date/datetime string to a YYYY-MM-DD date string. */
export function isoDate(value: string): string {
    return new Date(value).toISOString().slice(0, 10);
}

/** Today as YYYY-MM-DD from the browser's *local* calendar parts.
 *
 *  R-021 carve-out — display-only, pre-server-response fallback. The
 *  household "today" is owned by the server (`AppSetting.timezone` →
 *  `household_today()` → `mealPlanStore.todayIso`); state and decisions
 *  must use that. This helper exists so the calendar can paint a "today"
 *  cell on the very first frame before the store has hydrated — once the
 *  server response lands, the binding flips and any one-day discrepancy
 *  resolves automatically. Never use this to gate persisted state, build
 *  a server payload, or decide which day a value belongs to. */
export function localTodayIso(): string {
    const d = new Date();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${month}-${day}`;
}

/** A YYYY-MM-DD date string, matched exactly (no time part). */
const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

/** True when `value` is a bare YYYY-MM-DD calendar date with no time part. */
export function isDateOnly(value: string): boolean {
    return DATE_ONLY.test(value);
}

/** Parse a YYYY-MM-DD string into a Date at **local** midnight of that
 *  calendar day.
 *
 *  Use this instead of `new Date(iso)` for every date-only value. Per spec,
 *  `new Date('2026-09-03')` parses the *date-only* form as **UTC** midnight, so
 *  the resulting instant lands on the previous local day for any negative UTC
 *  offset — and anything that then reads local parts (`getDate()`,
 *  `Intl.DateTimeFormat`, which defaults to the local zone) reports the wrong
 *  day. Measured in America/New_York: `new Date('2026-09-03')` renders as
 *  **02/09/2026**.
 *
 *  East of Greenwich the two forms agree, which is why this survived so long —
 *  Australia is the shipping default and every developer runs there.
 *
 *  Returns `null` for anything that isn't a bare YYYY-MM-DD, so callers can
 *  fall through to normal Date parsing for real datetimes (which carry their own
 *  offset and must NOT be shifted). */
export function parseLocalIso(value: string): Date | null {
    if (!DATE_ONLY.test(value)) return null;
    const [y, m, d] = value.split('-').map(Number);
    // The regex above guarantees three numeric parts, so these are defined;
    // `Date`'s constructor accepts them without assertion.
    const parsed = new Date(y!, m! - 1, d);
    return Number.isFinite(parsed.getTime()) ? parsed : null;
}

/** Whole-day delta from *local today* to a YYYY-MM-DD date. 0 = today,
 *  1 = tomorrow, -1 = yesterday. Both sides are normalised to local midnight so
 *  the result is a calendar-day count, not an elapsed-hours division. */
export function daysFromToday(value: string, now: Date = new Date()): number | null {
    const target = parseLocalIso(value);
    if (!target) return null;
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    // Both operands are local midnight, so the difference is a whole number of
    // days except across a DST boundary — round to absorb the ±1h.
    return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

/** Shift a YYYY-MM-DD date by N days (may be negative). */
export function shiftDays(iso: string, days: number): string {
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(Date.UTC(y!, m! - 1, d! + days)).toISOString().slice(0, 10);
}

/** The Monday (ISO week start) of the week containing the given date. */
export function mondayOf(value: string): string {
    const [y, m, d] = isoDate(value).split('-').map(Number);
    const dt = new Date(Date.UTC(y!, m! - 1, d));
    const dow = dt.getUTCDay(); // 0=Sun … 6=Sat
    return shiftDays(dt.toISOString().slice(0, 10), dow === 0 ? -6 : 1 - dow);
}
