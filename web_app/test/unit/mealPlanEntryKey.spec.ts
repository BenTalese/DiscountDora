import { describe, expect, it } from 'vitest';
import { keyedEntries } from 'src/helpers/mealPlanEntryKey';
import type { MealPlanEntry } from 'src/models/mealPlan';

function entry(over: Partial<MealPlanEntry>): MealPlanEntry {
    return {
        meal_plan_entry_id: 'id-1',
        recipe_id: 'recipe-1',
        recipe_name: 'Ragu',
        scheduled_for: '2026-09-07',
        servings: 2,
        slot: 'Dinner',
        consumed_at: null,
        cook_time_minutes: null,
        category_name: null,
        cuisine_name: null,
        has_image: false,
        cook_batch_id: null,
        is_cook_day: false,
        cook_batch_total_servings: null,
        cook_batch_size: null,
        kcal_per_serving: null,
        kcal_is_reliable: false,
        inference_hint: null,
        inference_stock_item_names: [],
        needs_cooking: false,
        cook_fresh: false,
        estimated_cost: null,
        ...over,
    };
}

describe('keyedEntries', () => {
    it('survives the id churn a save causes', () => {
        // The write path deletes and re-inserts every forward entry, so this is
        // the same meal before and after an edit — with a new database id and
        // one more serving. A key that changed here would remount the card and
        // close the menu the user is tapping in (owner report 2026-09-05).
        const before = keyedEntries([entry({ meal_plan_entry_id: 'old', servings: 2 })]);
        const after = keyedEntries([entry({ meal_plan_entry_id: 'new', servings: 3 })]);

        expect(after[0]!.key).toBe(before[0]!.key);
    });

    it('separates two of the same recipe in one slot', () => {
        const keys = keyedEntries([
            entry({ meal_plan_entry_id: 'a' }),
            entry({ meal_plan_entry_id: 'b' }),
        ]).map((k) => k.key);

        expect(new Set(keys).size).toBe(2);
    });

    it('distinguishes the same recipe across days and slots', () => {
        const keys = keyedEntries([
            entry({}),
            entry({ slot: 'Lunch' }),
            entry({ scheduled_for: '2026-09-08' }),
        ]).map((k) => k.key);

        expect(new Set(keys).size).toBe(3);
    });
});
