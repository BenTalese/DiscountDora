import type { MealPlanEntry } from 'src/models/mealPlan';

/**
 * Stable `v-for` keys for a list of planned meals.
 *
 * **Why not `meal_plan_entry_id`.** `PATCH /meal-plans/{id}` replaces the whole
 * forward portion of a plan on every edit — it deletes the future entries and
 * inserts new rows (`update_meal_plan.py`, and the cook-batch rebuild that sits
 * on top of it depends on that shape). So an entry's database id changes every
 * time *anything* in the week is saved, including a change to a different meal
 * on a different day. Keyed on that id, Vue sees a whole new list and remounts
 * every card.
 *
 * That is invisible until something lives *inside* a card across an edit — and
 * one thing does: the entry menu's servings stepper. Owner report 2026-09-05:
 * *"tapping increase or decrease servings on mobile once hides the dropdown for
 * a meal slot. To increase by 3 you have to tap 6 times."* Each tap saved the
 * week, the card remounted, and the `q-menu` inside it went with it.
 *
 * The key is therefore the entry's *content identity* — the three fields that
 * say which meal this is, none of which a servings change touches. A day+slot
 * that genuinely holds the same recipe twice gets an occurrence suffix, so the
 * keys stay unique without pretending the two rows are one.
 *
 * The database id is still the identity for everything else (writes, batch
 * membership, reconcile). This is a rendering concern only.
 */
export type KeyedMealPlanEntry = { key: string; entry: MealPlanEntry };

export function keyedEntries(entries: MealPlanEntry[]): KeyedMealPlanEntry[] {
    const seen = new Map<string, number>();
    return entries.map((entry) => {
        const base = `${String(entry.scheduled_for)}|${entry.slot}|${entry.recipe_id}`;
        const occurrence = seen.get(base) ?? 0;
        seen.set(base, occurrence + 1);
        return { key: occurrence === 0 ? base : `${base}#${occurrence}`, entry };
    });
}
