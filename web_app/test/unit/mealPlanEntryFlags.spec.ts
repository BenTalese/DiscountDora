// Owner 2026-09-12 — when a planned meal flags its missing ingredients.
//
// Worth pinning under the lean verification stance: it is a pure predicate with
// no pinia and no network, it is shared by the desktop chip and the phone card
// (so a drift between them would be invisible until someone opened both), and
// walking every combination by hand means seeding a batch household, a fresh
// household, a linked cook and a leftovers day every single time.
import { describe, expect, it } from 'vitest';

import { showsMissingIngredients } from 'src/helpers/mealPlanEntryFlags';
import type { MealPlanEntry } from 'src/models/mealPlan';

function entry(over: Partial<MealPlanEntry>): MealPlanEntry {
    return {
        meal_plan_entry_id: 'id-1',
        recipe_id: 'recipe-1',
        recipe_name: 'Ragu',
        scheduled_for: '2026-09-14',
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
        missing_count: 2,
        ...over,
    };
}

describe('showsMissingIngredients', () => {
    it('says nothing when you have everything', () => {
        expect(showsMissingIngredients(entry({ missing_count: 0 }), false)).toBe(false);
    });

    it('says nothing about a meal already cooked', () => {
        expect(showsMissingIngredients(entry({ consumed_at: '2026-09-13' }), false)).toBe(false);
    });

    it('flags every short meal in a fresh household — each is cooked on its day', () => {
        expect(showsMissingIngredients(entry({}), false)).toBe(true);
    });

    describe('in a batch household', () => {
        it('flags the cook day of a batch', () => {
            const e = entry({ cook_batch_id: 'batch-1', is_cook_day: true });
            expect(showsMissingIngredients(e, true)).toBe(true);
        });

        it('stays quiet on a leftovers day — that food is already cooked', () => {
            const e = entry({ cook_batch_id: 'batch-1', is_cook_day: false });
            expect(showsMissingIngredients(e, true)).toBe(false);
        });

        it('flags a meal marked cook-fresh, which stands outside the pool', () => {
            expect(showsMissingIngredients(entry({ cook_fresh: true }), true)).toBe(true);
        });

        it('stays quiet on an unlinked meal, which is served from the pool', () => {
            expect(showsMissingIngredients(entry({}), true)).toBe(false);
        });
    });
});
