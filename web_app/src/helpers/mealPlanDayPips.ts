import { mealCardStatus } from 'src/helpers/mealPlanEntryStatus';
import type { MealPlanEntry } from 'src/models/mealPlan';

/**
 * The per-meal status pip shown on a day, in one place.
 *
 * Lived inside `MealPlanCalendar.vue` until 2026-09-01, which is why the mobile
 * day strip drew something else entirely — a single dot meaning "has meals".
 * The two are now one component (`MealPlanDayPips.vue`) over this one function
 * (R-001).
 *
 * R-003 — a pip is coded from the entry's own server-owned facts. Until
 * 2026-09-03 the caller passed in the set of *recipe* ids with a shortfall,
 * which coded every meal of a short recipe as short even when the cooked
 * servings covered the earlier ones; the per-entry allocation now lives on the
 * entry (see `MealPlanEntry`).
 *
 * **Owner 2026-09-12** — *"what does the calendar day pip show now that we've
 * modified the rows with cookability and shortfall?"* It showed only the
 * readiness half (`needs_cooking`), so after the card gained a second axis a
 * day full of meals you had no ingredients for was six green pips. The amber
 * pip is now the card's own trim roll-up: **anything that needs you**, either
 * axis. One rule, two surfaces (`mealPlanEntryStatus`), so the month view and
 * the week cards cannot disagree about which days are fine.
 */
export type DayPip = 'planned' | 'short' | 'consumed';

/** Pips per day. Two rows of three, so a heavily-planned day cannot push the
 *  calendar's square out of shape (owner 2026-09-03: *"keep the day squares
 *  where they are — they shouldn't be pushed around"*). Beyond this the pips
 *  simply stop; there is no "+N" (owner: *"remove the +X text"*, and *"don't
 *  think the +X is needed on mobile either — just show the dots"*). */
export const MAX_DAY_PIPS = 6;

export function pipForEntry(entry: MealPlanEntry, batchEnabled: boolean): DayPip {
    if (entry.consumed_at) return 'consumed';
    const { trim } = mealCardStatus(entry, batchEnabled, entry.needs_cooking);
    return trim === 'alert' ? 'short' : 'planned';
}

/** The capped pip row for one day. */
export function dayPips(
    entries: readonly MealPlanEntry[],
    batchEnabled: boolean,
    max: number = MAX_DAY_PIPS,
): { pips: DayPip[] } {
    return { pips: entries.slice(0, max).map((e) => pipForEntry(e, batchEnabled)) };
}
