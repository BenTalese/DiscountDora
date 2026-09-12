import type { MealPlanEntry } from 'src/models/mealPlan';

/**
 * Whether a planned meal should flag its missing ingredients.
 *
 * Owner call 2026-09-12: the card flags the **gap only** — a meal you can cook
 * says nothing at all, because "Dora agrees" is not information (Charter 10),
 * and a second green signal beside the amber "the pool is short one of these"
 * is exactly the *"this one says it's okay but this one says not okay"*
 * confusion the same batch asked us to remove.
 *
 * It is also scoped to the meals the question applies to: *"only relevant for
 * fresh cooks and cooking day meal slots"*. A leftovers day is eaten from a
 * cook that already happened, and in a batch household an unlinked meal comes
 * off the cooked pool — neither is about to send you to the shops. In a
 * **fresh** household there is no pool at all, so every meal is cooked on its
 * day and every one of them can be short.
 *
 * Shared by `MealPlanEntryChip` and `MealPlanRichCard` (R-001) so the desktop
 * chip and the phone card cannot disagree about when a meal looks cookable.
 */
export function showsMissingIngredients(
    entry: MealPlanEntry,
    batchEnabled: boolean,
): boolean {
    if (entry.consumed_at || entry.missing_count <= 0) return false;
    if (!batchEnabled) return true;
    if (entry.cook_fresh) return true;
    return entry.cook_batch_id !== null && entry.is_cook_day;
}
