/**
 * The cook-mode entry guard.
 *
 * Owner-reported defect 2026-08-19: starting cook mode from the cookbook
 * skipped the "you're missing ingredients" confirm that the recipe page shows.
 * The cause was that only `RecipeDetailPage` knew the rule, so the fix moved it
 * into `helpers/cookModeGuard` and pointed both surfaces at it.
 *
 * That makes this predicate exactly the kind of thing worth an automated test
 * (per DORA_VERIFY_TRIAGE's stance): a stable, pure domain contract, and the
 * one place a regression would silently re-open the reported bug — a second
 * surface drifting is invisible until someone walks both by hand.
 */
import { describe, expect, it } from 'vitest';

import {
    cookGuardReasons,
    missingIngredientNames,
    missingStockItemIds,
    needsCookGuard,
    unlinkedIngredientNames,
} from 'src/helpers/cookModeGuard';
import type { Recipe } from 'src/models/recipe';

type IngredientPart = {
    stock_item_id: string | null;
    is_missing: boolean;
    stock_item_name?: string | null;
    raw_text?: string | null;
};

function recipeWith(
    cookable: boolean | null,
    ingredients: IngredientPart[] = [],
    unlinked = 0,
): Recipe {
    return {
        recipe_id: 'r1',
        name: 'Lasagne',
        cookable,
        unlinked_ingredient_count: unlinked,
        ingredients,
    } as unknown as Recipe;
}

describe('cookGuardReasons', () => {
    it('is empty for a cookable, clean recipe — that entry goes straight in', () => {
        expect(cookGuardReasons(recipeWith(true), false)).toEqual([]);
        expect(needsCookGuard(recipeWith(true), false)).toBe(false);
    });

    it('flags missing ingredients when cookable is false', () => {
        const recipe = recipeWith(false, [
            { stock_item_id: 's1', is_missing: true },
        ]);
        expect(cookGuardReasons(recipe)).toEqual(['missing-ingredients']);
        expect(needsCookGuard(recipe)).toBe(true);
    });

    it('distinguishes unknown cookability from known-short', () => {
        // `null` means something isn't linked to stock, so cookability can't be
        // computed — a different message from "you are short two things".
        expect(cookGuardReasons(recipeWith(null, [], 2)))
            .toEqual(['unknown-cookability']);
        // …and the two are mutually exclusive, never both.
        expect(cookGuardReasons(recipeWith(false)))
            .toEqual(['missing-ingredients']);
    });

    it('adds the unsaved-changes reason on top, only when dirty', () => {
        const recipe = recipeWith(false, [{ stock_item_id: 's1', is_missing: true }]);
        expect(cookGuardReasons(recipe, true))
            .toEqual(['unsaved', 'missing-ingredients']);
        // The cookbook never passes `dirty`, so a cookable recipe there is a
        // clean entry — this is the half that made the two surfaces disagree.
        expect(cookGuardReasons(recipeWith(true), true)).toEqual(['unsaved']);
    });

    it('treats a null recipe as nothing to guard', () => {
        expect(cookGuardReasons(null, true)).toEqual([]);
        expect(needsCookGuard(null)).toBe(false);
    });
});

describe('missingStockItemIds', () => {
    it('dedupes — one ingredient on two rows is still one thing to buy', () => {
        const recipe = recipeWith(false, [
            { stock_item_id: 's1', is_missing: true },
            { stock_item_id: 's1', is_missing: true },
            { stock_item_id: 's2', is_missing: true },
        ]);
        expect(missingStockItemIds(recipe)).toEqual(['s1', 's2']);
    });

    it('excludes unlinked rows — they are the unknown case, not the short one', () => {
        const recipe = recipeWith(null, [
            { stock_item_id: null, is_missing: true },
            { stock_item_id: 's1', is_missing: true },
        ], 1);
        expect(missingStockItemIds(recipe)).toEqual(['s1']);
    });

    it('excludes in-stock rows', () => {
        const recipe = recipeWith(true, [
            { stock_item_id: 's1', is_missing: false },
        ]);
        expect(missingStockItemIds(recipe)).toEqual([]);
    });
});

/**
 * Owner feedback 2026-09-01: the guard dialog said "2 ingredients missing" and
 * left you to work out which two. The dialog now lists names, so the naming
 * belongs to the same helper the predicate does — otherwise the count and the
 * list can disagree, which is exactly the drift this file exists to stop.
 */
describe('missingIngredientNames', () => {
    it('names the missing linked ingredients, deduped on the stock item', () => {
        const recipe = recipeWith(false, [
            { stock_item_id: 's1', is_missing: true, stock_item_name: 'Pecorino' },
            { stock_item_id: 's1', is_missing: true, stock_item_name: 'Pecorino' },
            { stock_item_id: 's2', is_missing: true, stock_item_name: 'Guanciale' },
        ]);
        expect(missingIngredientNames(recipe)).toEqual(['Pecorino', 'Guanciale']);
    });

    it('agrees with the count the ids give — one list, one number', () => {
        const recipe = recipeWith(false, [
            { stock_item_id: 's1', is_missing: true, stock_item_name: 'Pecorino' },
            { stock_item_id: 's2', is_missing: false, stock_item_name: 'Eggs' },
            { stock_item_id: null, is_missing: true, raw_text: 'a pinch of luck' },
        ], 1);
        expect(missingIngredientNames(recipe))
            .toHaveLength(missingStockItemIds(recipe).length);
    });

    it('falls back to the raw text when the link has no name', () => {
        const recipe = recipeWith(false, [
            { stock_item_id: 's1', is_missing: true, stock_item_name: null, raw_text: '200g spaghetti' },
        ]);
        expect(missingIngredientNames(recipe)).toEqual(['200g spaghetti']);
    });

    it('treats a null recipe as nothing to name', () => {
        expect(missingIngredientNames(null)).toEqual([]);
    });
});

describe('unlinkedIngredientNames', () => {
    it('names only the unlinked rows — the unknown-cookability case', () => {
        const recipe = recipeWith(null, [
            { stock_item_id: null, is_missing: false, raw_text: '1 tsp sea salt' },
            { stock_item_id: 's1', is_missing: true, stock_item_name: 'Pecorino' },
        ], 1);
        expect(unlinkedIngredientNames(recipe)).toEqual(['1 tsp sea salt']);
    });

    it('dedupes by label — unlinked rows have no id to dedupe on', () => {
        const recipe = recipeWith(null, [
            { stock_item_id: null, is_missing: false, raw_text: 'olive oil' },
            { stock_item_id: null, is_missing: false, raw_text: 'olive oil' },
        ], 2);
        expect(unlinkedIngredientNames(recipe)).toEqual(['olive oil']);
    });

    it('treats a null recipe as nothing to name', () => {
        expect(unlinkedIngredientNames(null)).toEqual([]);
    });
});
