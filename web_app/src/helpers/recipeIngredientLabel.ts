/**
 * What to call a recipe ingredient row on screen — one precedence, shared by
 * the recipe page, the cook-mode guard dialog and the add-to-list rows.
 *
 * `label` is the "which one" name the recipe shows for a linked item ("tasty
 * cheddar" for the pantry's Cheese, shipped 2026-10-21) and wins; then the
 * linked item's name; then the pasted/typed text. The guard and add-to-list
 * helpers used to skip `label`, so the same missing row was named differently
 * on the recipe page and in the dialog (finalisation 01-R1).
 */
export type IngredientNameSource = {
    label?: string | null | undefined;
    stock_item_name?: string | null | undefined;
    raw_text?: string | null | undefined;
};

export const UNNAMED_INGREDIENT = 'Unnamed ingredient';

export function ingredientDisplayName(ing: IngredientNameSource): string {
    return ing.label || ing.stock_item_name || ing.raw_text || UNNAMED_INGREDIENT;
}
