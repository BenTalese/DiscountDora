/**
 * The per-meal day pip. Extracted out of `MealPlanCalendar.vue` on 2026-09-01
 * because the phone's day strip was drawing something else entirely (one dot
 * meaning "has meals"), which is exactly the drift a shared pure function plus
 * a test stops recurring.
 *
 * Rewritten 2026-09-03: a pip's "short" state now reads the entry's own
 * server-owned `needs_cooking` verdict rather than a set of short RECIPE ids
 * handed in by the caller. The old signature could only say "this recipe is
 * short somewhere", so three planned fried rices against a pool of two all
 * coded short; the pool allocation is per entry (and per cook batch) and lives
 * on the server. The `overflow` half of the return went at the same time — the
 * "+N" label is gone from both hosts.
 */
import { describe, expect, it } from 'vitest';

import { MAX_DAY_PIPS, dayPips, pipForEntry } from 'src/helpers/mealPlanDayPips';
import type { MealPlanEntry } from 'src/models/mealPlan';

function entry(over: Partial<MealPlanEntry> = {}): MealPlanEntry {
    return {
        meal_plan_entry_id: `e-${Math.random()}`,
        recipe_id: 'r-1',
        recipe_name: 'Lasagne',
        scheduled_for: '2026-09-01',
        servings: 1,
        slot: 'Dinner',
        consumed_at: null,
        needs_cooking: false,
        ...over,
    } as unknown as MealPlanEntry;
}

describe('pipForEntry', () => {
    it('codes a cooked meal as consumed even when it was flagged as needing a cook', () => {
        // `consumed_at` wins: the meal happened, so a cook shortfall against
        // that recipe is no longer this day's problem.
        expect(pipForEntry(entry({ needs_cooking: true, consumed_at: '2026-09-01T18:00:00Z' })))
            .toBe('consumed');
    });

    it("codes an uncooked meal from the entry's own verdict", () => {
        expect(pipForEntry(entry({ needs_cooking: true }))).toBe('short');
        expect(pipForEntry(entry({ needs_cooking: false }))).toBe('planned');
    });

    it('codes two meals of the SAME recipe differently when only one is short', () => {
        // The regression this signature exists to prevent (owner, 2026-09-03):
        // with a pool covering the first of two fried rices, exactly one pip
        // is amber.
        const covered = entry({ recipe_id: 'r-rice', needs_cooking: false });
        const short = entry({ recipe_id: 'r-rice', needs_cooking: true });
        expect(dayPips([covered, short]).pips).toEqual(['planned', 'short']);
    });
});

describe('dayPips', () => {
    it('is empty for a day with nothing planned', () => {
        expect(dayPips([])).toEqual({ pips: [] });
    });

    it('caps the row at the maximum and reports no remainder', () => {
        const entries = Array.from({ length: MAX_DAY_PIPS + 2 }, () => entry());
        expect(dayPips(entries).pips).toHaveLength(MAX_DAY_PIPS);
    });

    it('preserves entry order in the pips it keeps', () => {
        const { pips } = dayPips([
            entry({ needs_cooking: true }),
            entry(),
            entry({ consumed_at: 'x' }),
        ]);
        expect(pips).toEqual(['short', 'planned', 'consumed']);
    });
});
