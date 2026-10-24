// Finalisation 01-R1 — the label precedence is a contract three surfaces
// share (recipe page, cook-mode guard, add-to-list rows) and it had already
// drifted once: the guard ignored `label`.
import { describe, expect, it } from 'vitest';

import { UNNAMED_INGREDIENT, ingredientDisplayName } from 'src/helpers/recipeIngredientLabel';

describe('ingredientDisplayName', () => {
    it('prefers the recipe\'s own label over the linked item name', () => {
        expect(ingredientDisplayName({ label: 'tasty cheddar', stock_item_name: 'Cheese', raw_text: '200g cheese' }))
            .toBe('tasty cheddar');
    });

    it('falls back to the linked item name, then the raw text', () => {
        expect(ingredientDisplayName({ label: null, stock_item_name: 'Cheese', raw_text: '200g cheese' })).toBe('Cheese');
        expect(ingredientDisplayName({ label: '', stock_item_name: null, raw_text: '200g cheese' })).toBe('200g cheese');
    });

    it('names a row with nothing to show', () => {
        expect(ingredientDisplayName({})).toBe(UNNAMED_INGREDIENT);
        expect(ingredientDisplayName({ label: '', stock_item_name: '', raw_text: '' })).toBe(UNNAMED_INGREDIENT);
    });
});
