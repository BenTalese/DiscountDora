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
    missingStockItemIds,
    needsCookGuard,
} from 'src/helpers/cookModeGuard';
import type { Recipe } from 'src/models/recipe';

type IngredientPart = {
    stock_item_id: string | null;
    is_missing: boolean;
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
