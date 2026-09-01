import type { MealPlanEntry } from 'src/models/mealPlan';

/**
 * The per-meal status pip shown on a day, in one place.
 *
 * Lived inside `MealPlanCalendar.vue` until 2026-09-01, which is why the mobile
 * day strip drew something else entirely — a single dot meaning "has meals".
 * The two are now one component (`MealPlanDayPips.vue`) over this one function
 * (R-001).
 *
 * R-003 — a pip is coded from the SERVER's shortfall set and the entry's own
 * `consumed_at`. The client never re-judges whether a meal is cookable.
 */
export type DayPip = 'planned' | 'short' | 'consumed';

/** Pips per day before collapsing to "+N". Three reads at a glance; four starts
 *  to look like a progress bar. */
export const MAX_DAY_PIPS = 3;

export function pipForEntry(entry: MealPlanEntry, shortfallRecipeIds: Set<string>): DayPip {
    if (entry.consumed_at) return 'consumed';
    return shortfallRecipeIds.has(entry.recipe_id) ? 'short' : 'planned';
}

/** The capped pip row for one day, plus however many meals didn't fit. */
export function dayPips(
    entries: readonly MealPlanEntry[],
    shortfallRecipeIds: Set<string>,
    max: number = MAX_DAY_PIPS,
): { pips: DayPip[]; overflow: number } {
    return {
        pips: entries.slice(0, max).map((e) => pipForEntry(e, shortfallRecipeIds)),
        overflow: Math.max(0, entries.length - max),
    };
}
