// C-2.A — household-wide meal-slot vocabulary. Same {id, name, sequence}
// lookup shape as the recipe vocabularies, edited in Recipe Vocab settings.
// `usage_count` is rolled up by the list endpoint (matching the stored slot
// label on meal-plan entries + recipe `time_of_day`) for the delete warning.
// Unlike the recipe vocabs, slots are NOT an FK: deleting one leaves existing
// labels intact (they become off-vocab).

export type MealSlot = {
    meal_slot_id: string;
    name: string;
    sequence: number;
    usage_count: number;
};
