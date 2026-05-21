export type RecipeIngredient = {
    recipe_ingredient_id: string;
    stock_item_id: string;
    stock_item_name: string;
    stock_level_id: string | null;
    stock_location_id: string | null;
    stock_location_name: string | null;
    quantity: number | null;
    unit: string | null;
    notes: string | null;
};

export type Recipe = {
    recipe_id: string;
    name: string;
    category: string | null;
    cook_time_minutes: number | null;
    cuisine: string | null;
    difficulty: string | null;
    instructions: string | null;
    is_favourite: boolean;
    last_made_on: string | null;
    nutrition: string | null;
    prep_time_minutes: number | null;
    recipe_collection_id: string | null;
    servings: number | null;
    time_of_day: string | null;
    ingredients: RecipeIngredient[];
};

export type RecipeCollection = {
    recipe_collection_id: string;
    name: string;
};
