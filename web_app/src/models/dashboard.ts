export type StockItemSummary = {
    total: number;
    out_of_stock: number;
    low_stock: number;
};

export type ShoppingListSummary = {
    total: number;
    total_items: number;
};

export type ProductSummary = {
    total: number;
};

export type RecipeSummary = {
    total: number;
    favourites: number;
};

export type MealSummary = {
    total_definitions: number;
    total_in_stock: number;
};

export type UpcomingMealPlanEntry = {
    recipe_name: string;
    scheduled_for: string; // ISO date
    slot: string;
    servings: number;
};

export type MealPlanSummary = {
    upcoming_entries: UpcomingMealPlanEntry[];
};

export type DashboardSummary = {
    stock_items: StockItemSummary;
    shopping_lists: ShoppingListSummary;
    products: ProductSummary;
    recipes: RecipeSummary;
    meals: MealSummary;
    meal_plan: MealPlanSummary;
};
