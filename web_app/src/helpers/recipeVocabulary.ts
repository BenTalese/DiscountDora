// Cookbook card revision (§1.7 + §1.12) — closed-set vocabularies for
// `Recipe.difficulty` and `Recipe.time_of_day`. Mirrors the server
// constants in `dora_api/domain/entities/recipe.py`
// (`ALLOWED_DIFFICULTY_VALUES`, `DEFAULT_MEAL_SLOTS`).
//
// the meal-slot vocabulary is now the household-wide `MealSlot`
// table (mealSlotStore / `/api/meal-slots`). `DEFAULT_MEAL_SLOTS` here is
// kept only as the seeded default + a pre-first-load fallback for the slot
// dropdowns — the store is the live source of truth once loaded.

export const DIFFICULTY_VALUES = ['Easy', 'Medium', 'Hard'] as const;
export type Difficulty = (typeof DIFFICULTY_VALUES)[number];

export const DIFFICULTY_RANK: Record<Difficulty, number> = {
    Easy: 0,
    Medium: 1,
    Hard: 2,
};

export const DEFAULT_MEAL_SLOTS = [
    'Breakfast',
    'Lunch',
    'Dinner',
    'Snack',
    'Dessert',
] as const;
export type MealSlot = (typeof DEFAULT_MEAL_SLOTS)[number];
