export type MealPlanEntry = {
    meal_plan_entry_id: string;
    recipe_id: string;
    recipe_name: string;
    scheduled_for: string;
    servings: number;
    slot: string;
    consumed_at: string | null;
};

export type MealPlan = {
    meal_plan_id: string;
    name: string;
    start_date: string;
    entries: MealPlanEntry[];
};

export type MealPlanIngredient = {
    stock_item_id: string;
    stock_item_name: string;
    total_quantity: number | null;
    unit: string | null;
    used_in_recipe_ids: string[];
};

export type Shortfall = {
    recipe_id: string;
    recipe_name: string;
    available_meals: number;
    committed_meals: number;
    shortfall: number;
    earliest_needed: string | null;
};
