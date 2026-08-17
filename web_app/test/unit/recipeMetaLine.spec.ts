// @vitest-environment jsdom
/**
 * `useRecipeDisplay().metaLine` — the caption under a recipe's name, shared
 * by RecipeCard and RecipeRow (R-003: one composable, two layouts).
 *
 * The collection leads the line. It used to be the cookbook's grouping
 * *layout* — collapsible folders — which buried search results under a folder
 * you had to notice and open; the folders went and the collection became a
 * fact about the recipe like cuisine or category. Pinned here because the
 * order is a deliberate call and the dedupe (DR-4 / FU-578 #14) is easy to
 * regress when a part is added.
 */
import { describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useRecipeDisplay } from 'src/composables/useRecipeDisplay';
import type { Recipe } from 'src/models/recipe';

function recipeWith(parts: Partial<Recipe>): Recipe {
    return {
        recipe_collection_name: null,
        cuisine_name: null,
        category_name: null,
        time_of_day: null,
        ingredients: [],
        ...parts,
    } as unknown as Recipe;
}

function metaLineFor(parts: Partial<Recipe>): string {
    setActivePinia(createPinia());
    return useRecipeDisplay(() => recipeWith(parts)).metaLine.value;
}

describe('recipe meta line', () => {
    it('leads with the collection, then cuisine, category, time of day', () => {
        expect(metaLineFor({
            recipe_collection_name: 'Weeknight Dinners',
            cuisine_name: 'Italian',
            category_name: 'Main',
            time_of_day: 'Evening',
        })).toBe('Weeknight Dinners · Italian · Main · Evening');
    });

    it('omits the collection for an uncollected recipe', () => {
        expect(metaLineFor({
            cuisine_name: 'Italian',
            time_of_day: 'Evening',
        })).toBe('Italian · Evening');
    });

    it('renders a collection-only recipe', () => {
        expect(metaLineFor({ recipe_collection_name: 'To Try' })).toBe('To Try');
    });

    it('dedupes case-insensitively across every part (DR-4)', () => {
        expect(metaLineFor({
            recipe_collection_name: 'Desserts',
            cuisine_name: 'desserts',
            category_name: 'Dessert',
        })).toBe('Desserts · Dessert');
    });
});
