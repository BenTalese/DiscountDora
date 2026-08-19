/**
 * When entering cook mode needs a confirm first, and what to say.
 *
 * Owner feedback 2026-08-19: "start cook mode confirmation when missing
 * ingredients doesn't pop up from [the cookbook], but it does from the recipe
 * detail view. Inconsistent."
 *
 * It was inconsistent because the rule only existed inside
 * `RecipeDetailPage` — `RecipesOverview.onCookClick` pushed straight to the
 * cook route. Rather than copy the condition into the second page (and let a
 * third surface drift again), the decision lives here and the dialog that
 * renders it lives in `components/recipes/CookModeGuardDialog.vue`. One rule,
 * one wording, every entry point (R-003).
 *
 * The unsaved-changes half only applies where a recipe can be edited in place,
 * so callers pass `dirty` and the cookbook simply never sets it.
 */
import type { Recipe } from 'src/models/recipe';

/** Distinct reasons to stop and ask. A recipe can trip more than one. */
export type CookGuardReason =
    | 'unsaved'
    /** `cookable === null` — at least one ingredient isn't linked to stock, so
     *  cookability genuinely isn't known (not "known to be false"). */
    | 'unknown-cookability'
    /** `cookable === false` — linked ingredients are out of stock. */
    | 'missing-ingredients';

/** Distinct stock items the recipe needs and doesn't have.
 *
 *  Deduped because one ingredient appearing on two rows is still one thing to
 *  buy, and unlinked rows are excluded — a row with no `stock_item_id` can't be
 *  "missing" in the stock sense, it's the `unknown-cookability` case instead. */
export function missingStockItemIds(recipe: Recipe): string[] {
    const ids = recipe.ingredients
        .filter((i) => i.is_missing && i.stock_item_id !== null)
        .map((i) => i.stock_item_id as string);
    return [...new Set(ids)];
}

/**
 * Every reason this recipe should prompt before cook mode starts. Empty array
 * = clean entry, go straight in.
 */
export function cookGuardReasons(
    recipe: Recipe | null,
    dirty = false,
): CookGuardReason[] {
    if (!recipe) return [];
    const reasons: CookGuardReason[] = [];
    if (dirty) reasons.push('unsaved');
    // Tri-state: `null` (unknown, because something is unlinked) and `false`
    // (known short) are different messages, so they're different reasons.
    if (recipe.cookable === null) reasons.push('unknown-cookability');
    else if (recipe.cookable === false) reasons.push('missing-ingredients');
    return reasons;
}

/** Convenience predicate for the click handlers. */
export function needsCookGuard(recipe: Recipe | null, dirty = false): boolean {
    return cookGuardReasons(recipe, dirty).length > 0;
}
