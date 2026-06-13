// Cookbook card revision (§1.7 + §1.12) — closed-set vocabularies for
// `Recipe.difficulty` and `Recipe.time_of_day`. Mirrors the server
// constants in `dora_api/domain/entities/recipe.py`
// (`ALLOWED_DIFFICULTY_VALUES`, `DEFAULT_MEAL_SLOTS`).
//
// §1.12 caveat: `DEFAULT_MEAL_SLOTS` will become the *seeded default* of
// a user-configurable meal-slot list when `PROPOSAL_MEAL_PLANS.md §4`
// lands. Until then, this constant is the single source of truth for
// both the cookbook surfaces and the (future) planner.

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
