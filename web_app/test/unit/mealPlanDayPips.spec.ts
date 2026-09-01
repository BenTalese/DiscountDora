/**
 * The per-meal day pip. Extracted out of `MealPlanCalendar.vue` on 2026-09-01
 * because the phone's day strip was drawing something else entirely (one dot
 * meaning "has meals"), which is exactly the drift a shared pure function plus
 * a test stops recurring.
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
        ...over,
    } as unknown as MealPlanEntry;
}

const SHORT = new Set(['r-short']);

describe('pipForEntry', () => {
    it('codes a cooked meal as consumed even when its recipe is short', () => {
        // `consumed_at` wins: the meal happened, so a cook shortfall against
        // that recipe is no longer this day's problem.
        expect(pipForEntry(entry({ recipe_id: 'r-short', consumed_at: '2026-09-01T18:00:00Z' }), SHORT))
            .toBe('consumed');
    });

    it('codes an uncooked meal from the server shortfall set', () => {
        expect(pipForEntry(entry({ recipe_id: 'r-short' }), SHORT)).toBe('short');
        expect(pipForEntry(entry({ recipe_id: 'r-1' }), SHORT)).toBe('planned');
    });
});

describe('dayPips', () => {
    it('is empty with no overflow for a day with nothing planned', () => {
        expect(dayPips([], SHORT)).toEqual({ pips: [], overflow: 0 });
    });

    it('caps the row and reports the remainder', () => {
        const entries = Array.from({ length: MAX_DAY_PIPS + 2 }, () => entry());
        const { pips, overflow } = dayPips(entries, SHORT);
        expect(pips).toHaveLength(MAX_DAY_PIPS);
        expect(overflow).toBe(2);
    });

    it('preserves entry order in the pips it keeps', () => {
        const { pips } = dayPips(
            [entry({ recipe_id: 'r-short' }), entry(), entry({ consumed_at: 'x' })],
            SHORT,
        );
        expect(pips).toEqual(['short', 'planned', 'consumed']);
    });
});
