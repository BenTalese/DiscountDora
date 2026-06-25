export type MealPlanEntry = {
    meal_plan_entry_id: string;
    recipe_id: string;
    recipe_name: string;
    scheduled_for: string;
    servings: number;
    slot: string;
    consumed_at: string | null;
    // IMPL_PLAN_MEAL_PLANS_REBUILD §6.5 / Q6 — display fields for the rich
    // meal card (Direction B). Server-derived so the client doesn't
    // cross-join the recipes store (R-003).
    cook_time_minutes: number | null;
    category_name: string | null;
    cuisine_name: string | null;
    has_image: boolean;
};

export type MealPlan = {
    meal_plan_id: string;
    // C-2.E: instances are nameless (UI shows "Week starting <date>").
    name: string | null;
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
