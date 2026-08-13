import {
    currentLocale,
    ensureLocalePolicy,
} from 'src/composables/useMoney';

// DR-14 / D-006 — the single date/time formatting authority. Every
// user-facing date goes through here so the whole app renders in the
// household's locale (e.g. 'en-AU' → "17/07/2026", not the browser's US
// "7/17/2026" — FU-578 #9). It reuses the ONE locale source already owned by
// `useMoney` (the install's `locale_policy.locale`), so money and dates can
// never drift apart (R-003). Templates never call `.toLocaleDateString()` /
// `.toLocaleString()` directly.
//
// Timezone: `locale_policy` carries locale only; date-only values (the vast
// majority of Dora's renders — expiry, planned-for, effective dates) are
// tz-independent. Datetime renders use the browser tz, which matches "when
// this happened on my clock". If a household tz is later added to the policy,
// it is wired in one place here.

type DateInput = string | number | Date | null | undefined;

function toDate(value: DateInput): Date | null {
    if (value === null || value === undefined || value === '') return null;
    const d = value instanceof Date ? value : new Date(value);
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

export function useDateFormat() {
    void ensureLocalePolicy();
    return {
        formatDate,
        formatDateTime,
    };
}
