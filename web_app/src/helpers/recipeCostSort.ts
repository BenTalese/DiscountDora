import type { Recipe } from 'src/models/recipe';

/**
 * Cheapest-first ordering by **cost per serving**, shared by the cookbook's
 * sort axis and the meal planner's rail (R-001 — it was the cookbook's alone
 * until the owner asked for the same ranking in the planner on 2026-09-05, and
 * two copies of a tie-break rule is how two lists come to disagree).
 *
 * Per serving, not per recipe: a $18 tray bake that feeds eight is cheaper than
 * a $9 dish for two, and ranking on the total puts them the wrong way round.
 * The figure is server-owned (`estimated_cost_per_serving`), which is also why
 * a recipe with no servings recorded arrives as null rather than being treated
 * as serves-one by whoever divided.
 *
 * Nulls sink, and only nulls. A recipe priced from two of its six ingredients
 * has a real number attached, looks cheap, and *is shown as* cheap — sinking it
 * here while the row displays a figure is the contradiction the owner hit on
 * the kcal filter. Ties, and rows with no figure at all, fall back to name.
 */
export function compareByCostPerServing(a: Recipe, b: Recipe, dirSign = 1): number {
    const av = a.estimated_cost_per_serving ?? null;
    const bv = b.estimated_cost_per_serving ?? null;
    if (av === null && bv === null) return a.name.localeCompare(b.name);
    if (av === null) return 1;
    if (bv === null) return -1;
    if (av === bv) return a.name.localeCompare(b.name);
    return (av - bv) * dirSign;
}
