// DR-15 / FU-578 #47 — the recipe-picker tray contract.
//
// Worth an automated test under the lean verification stance (DORA_VERIFY
// banner): the "one selectable instance per recipe" rule is a stable
// invariant, it's shared by two pickers (planner rail + step-by-step wizard),
// and re-checking it by hand means building a cookbook with the right mix of
// favourites/history every time. Pure function, no pinia, no network.
import { describe, expect, it } from 'vitest';

import { buildRecipeTrays, RECIPE_TRAY_CAP } from 'src/helpers/recipeTrays';
import type { Recipe } from 'src/models/recipe';

function recipe(over: Partial<Recipe> & { recipe_id: string; name: string }): Recipe {
    return {
        is_favourite: false,
        not_made_recently: false,
        plan_count: 0,
        last_made_on: null,
        ...over,
    } as Recipe;
}

/** Every recipe id across every tray, duplicates included. */
function allIds(trays: ReturnType<typeof buildRecipeTrays>): string[] {
    return trays.flatMap((t) => t.recipes.map((r) => r.recipe_id));
}

describe('buildRecipeTrays', () => {
    it('shows each recipe exactly once across all trays (FU-578 #47)', () => {
        const recipes = [
            recipe({ recipe_id: 'a', name: 'Fav + stale', is_favourite: true, not_made_recently: true }),
            recipe({ recipe_id: 'b', name: 'Fav + planned', is_favourite: true, plan_count: 9 }),
            recipe({ recipe_id: 'c', name: 'Stale', not_made_recently: true }),
            recipe({ recipe_id: 'd', name: 'Planned', plan_count: 4 }),
            recipe({ recipe_id: 'e', name: 'Plain' }),
        ];
        const ids = allIds(buildRecipeTrays(recipes));

        expect(ids).toHaveLength(recipes.length);
        expect(new Set(ids).size).toBe(recipes.length);
    });

    it('claims by priority: favourites beat the behavioural shortcut trays', () => {
        const trays = buildRecipeTrays([
            recipe({ recipe_id: 'a', name: 'Fav + stale + planned', is_favourite: true, not_made_recently: true, plan_count: 7 }),
            recipe({ recipe_id: 'c', name: 'Stale only', not_made_recently: true }),
        ]);
        const byKey = Object.fromEntries(trays.map((t) => [t.key, t.recipes.map((r) => r.recipe_id)]));

        expect(byKey.fav).toEqual(['a']);
        expect(byKey.stale).toEqual(['c']);
        expect(byKey.freq).toBeUndefined(); // 'a' was already claimed above
    });

    it('lets a recipe squeezed out by a tray cap fall through, never vanish', () => {
        // One more stale recipe than the cap allows. The overflow must land in
        // the final tray rather than being claimed and then not shown.
        const recipes = Array.from({ length: RECIPE_TRAY_CAP + 1 }, (_, i) =>
            recipe({
                recipe_id: `s${i}`,
                name: `Stale ${i}`,
                not_made_recently: true,
                // Oldest first, so the *newest* is the one over the cap.
                last_made_on: `2026-01-${String(i + 1).padStart(2, '0')}`,
            }),
        );
        const trays = buildRecipeTrays(recipes);
        const stale = trays.find((t) => t.key === 'stale');
        const rest = trays.find((t) => t.key === 'all');

        expect(stale?.recipes).toHaveLength(RECIPE_TRAY_CAP);
        expect(rest?.recipes.map((r) => r.recipe_id)).toEqual([`s${RECIPE_TRAY_CAP}`]);
        expect(allIds(trays)).toHaveLength(recipes.length);
    });

    it('titles the final tray for what it actually holds', () => {
        const plainOnly = buildRecipeTrays([recipe({ recipe_id: 'e', name: 'Plain' })]);
        expect(plainOnly).toHaveLength(1);
        expect(plainOnly[0]!.title).toBe('All recipes (1)');

        const mixed = buildRecipeTrays([
            recipe({ recipe_id: 'a', name: 'Fav', is_favourite: true }),
            recipe({ recipe_id: 'e', name: 'Plain' }),
        ]);
        expect(mixed.at(-1)!.title).toBe('Everything else (1)');
    });

    it('collapses to one flat Results tray while searching', () => {
        const trays = buildRecipeTrays(
            [
                recipe({ recipe_id: 'a', name: 'Chicken pie', is_favourite: true }),
                recipe({ recipe_id: 'b', name: 'Beef pie' }),
                recipe({ recipe_id: 'c', name: 'Salad' }),
            ],
            '  PIE ',
        );

        expect(trays).toHaveLength(1);
        expect(trays[0]!.key).toBe('results');
        expect(trays[0]!.title).toBe('Results (2)');
        expect(trays[0]!.defaultOpen).toBe(true);
        expect(allIds(trays)).toEqual(['a', 'b']);
    });

    it('returns a single empty tray for an empty cookbook', () => {
        const trays = buildRecipeTrays([]);
        expect(trays).toHaveLength(1);
        expect(trays[0]!.title).toBe('All recipes (0)');
    });
});
