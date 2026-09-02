import {
    currentLocale,
    ensureLocalePolicy,
} from 'src/composables/useMoney';
import { daysFromToday, parseLocalIso } from 'src/helpers/weekDates';

// DR-14 / D-006 — the single date/time formatting authority. Every
// user-facing date goes through here so the whole app renders in the
// household's locale (e.g. 'en-AU' → "17/07/2026", not the browser's US
// "7/17/2026" — FU-578 #9). It reuses the ONE locale source already owned by
// `useMoney` (the install's `locale_policy.locale`), so money and dates can
// never drift apart (R-003). Templates never call `.toLocaleDateString()` /
// `.toLocaleString()` directly.
//
// Timezone: `locale_policy` carries locale only. Date-only values (the vast
// majority of Dora's renders — expiry, planned-for, effective dates) are
// tz-independent *as data*, but they must be PARSED as local midnight to render
// as the calendar day they name — see `toDate` below, and R-021's client-side
// counterpart. Datetime renders use the browser tz, which matches "when this
// happened on my clock". If a household tz is later added to the policy, it is
// wired in one place here.

type DateInput = string | number | Date | null | undefined;

function toDate(value: DateInput): Date | null {
    if (value === null || value === undefined || value === '') return null;
    if (value instanceof Date) {
        return Number.isFinite(value.getTime()) ? value : null;
    }
    if (typeof value === 'string') {
        // A bare YYYY-MM-DD names a calendar day, not an instant. `new Date()`
        // parses that form as **UTC** midnight per spec, and Intl then formats
        // in the *local* zone — so west of Greenwich every date-only value
        // rendered one day early. Measured in America/New_York before this fix:
        // `formatDate('2026-09-03')` → "02/09/2026".
        //
        // Parse it as local midnight instead, so the rendered day is the day the
        // string names in every timezone. Strings that carry a time (or an
        // explicit offset) fall through untouched — those ARE instants and must
        // not be shifted.
        const localDay = parseLocalIso(value);
        if (localDay) return localDay;
    }
    const d = new Date(value);
    return Number.isFinite(d.getTime()) ? d : null;
}

// Cache one Intl.DateTimeFormat per (locale | options) — construction isn't
// free and date-heavy pages (history, alerts, reports) hit it a lot. Rebuilt
// implicitly when the locale changes because the key includes it.
const formatterCache = new Map<string, Intl.DateTimeFormat>();

function getFormatter(opts: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
    const locale = currentLocale();
    const key = `${locale}|${JSON.stringify(opts)}`;
    let fmt = formatterCache.get(key);
    if (!fmt) {
        fmt = new Intl.DateTimeFormat(locale, opts);
        formatterCache.set(key, fmt);
    }
    return fmt;
}

/** Format a date value in the household locale. Pass Intl options exactly as
 *  you would to `toLocaleDateString` (the second arg) — the only difference is
 *  the locale is the install's, not the browser's. Invalid/empty input renders
 *  as an empty string, so guard with `formatDate(x) || fallback` where a raw
 *  echo is wanted. Default (no opts) is the locale's short numeric date. */
export function formatDate(value: DateInput, opts: Intl.DateTimeFormatOptions = {}): string {
    // Fire-and-forget so any call site that imports `formatDate` directly
    // (without the composable) still triggers the one-per-session locale
    // probe. Idempotent; until it resolves we render the AU default, which is
    // already correct for the shipping market — never the browser's US format.
    void ensureLocalePolicy();
    const d = toDate(value);
    if (!d) return '';
    return getFormatter(opts).format(d);
}

/** Date + time, in the household locale (replaces bare `.toLocaleString()`).
 *  Medium date + short time reads cleanly and consistently ("17 Jul 2026,
 *  12:15 pm") — no seconds, no US-vs-ISO mixing (FU-578 #32). */
export function formatDateTime(value: DateInput): string {
    return formatDate(value, { dateStyle: 'medium', timeStyle: 'short' });
}

/** Name a calendar day the way a person would: "Today", "Tomorrow", the weekday
 *  if it's inside the coming week, otherwise the locale's short date.
 *
 *  Takes a YYYY-MM-DD string (the shape every `scheduled_for` / expiry / planned
 *  date has). Lifted out of `DashboardPage.vue`, where it was doing
 *  `new Date(iso)` and therefore naming the **wrong day** for every user west of
 *  Greenwich — tomorrow's dinner read "Today". It now runs on
 *  `daysFromToday`, which compares local midnights.
 *
 *  `now` is injectable for tests only. */
export function formatRelativeDay(value: string, now: Date = new Date()): string {
    const diff = daysFromToday(value, now);
    // Not a bare calendar date — fall back to the plain formatter rather than
    // guessing at a relative label for an instant.
    if (diff === null) return formatDate(value);
    if (diff === 0) return 'Today';
    if (diff === 1) return 'Tomorrow';
    if (diff === -1) return 'Yesterday';
    // Inside the coming week, the weekday alone is the most readable form
    // ("Thursday"); beyond that it stops being unambiguous.
    if (diff > 1 && diff < 7) return formatDate(value, { weekday: 'long' });
    return formatDate(value);
}

export function useDateFormat() {
    void ensureLocalePolicy();
    return {
        formatDate,
        formatDateTime,
        formatRelativeDay,
    };
}
