// Week/date helpers shared by the meal planner page + its calendar widget
// (R-003: one source for the week-date logic). Every function builds a
// YYYY-MM-DD string from explicit calendar parts and uses UTC math — never
// `toISOString()` on a *local* Date, which is UTC-shifted and drifts a day in
// positive-offset zones near midnight (the C-2.K bug class).

/** Normalise any date/datetime string to a YYYY-MM-DD date string. */
export function isoDate(value: string): string {
    return new Date(value).toISOString().slice(0, 10);
}

/** Today as YYYY-MM-DD from the browser's *local* calendar parts. A pre-load
 *  fallback only — the household "today" from the server (C-2.K) is preferred. */
export function localTodayIso(): string {
    const d = new Date();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${month}-${day}`;
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
