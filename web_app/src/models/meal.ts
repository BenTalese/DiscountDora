export type MealRecipe = {
    recipe_id: string;
    name: string;
};

export type Meal = {
    meal_id: string;
    name: string;
    quantity_in_stock: number;
    recipes: MealRecipe[];
};

export type MealPlanEntry = {
    meal_plan_entry_id: string;
    meal_id: string;
    meal_name: string;
    scheduled_for: string; // ISO date
    servings: number;
    slot: string;
};

export type MealPlan = {
    meal_plan_id: string;
    name: string;
    start_date: string; // ISO date
    entries: MealPlanEntry[];
};

export type MealPlanIngredient = {
    stock_item_id: string;
    stock_item_name: string;
    total_quantity: number | null;
    unit: string | null;
    used_in_meal_ids: string[];
};
