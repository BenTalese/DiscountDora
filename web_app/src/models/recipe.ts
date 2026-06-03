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
    /** Total meals of this recipe currently in the pool (cooked-ahead
     *  portions). User-managed via Cook mode and the ± controls; also
     *  auto-decrements when a meal-plan entry's day passes. */
    available_meals: number;
    /** `available_meals` minus the sum of un-consumed future meal-plan
     *  servings for this recipe. Floored at 0. Derived server-side. */
    unallocated_meals: number;
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
    /** P2-08 — canonical dietary / allergen-free / nutritional tags
     *  the recipe has been tagged with. Empty array when untagged. */
    tags: string[];
};

export type RecipeTagDefinition = {
    value: string;
    label: string;
    category: string;
};

export type RecipeTagCatalogue = {
    tags: RecipeTagDefinition[];
    /** Plain-English disclaimer to surface alongside any tag-based UI. */
    disclaimer: string;
};

export type RecipeCollection = {
    recipe_collection_id: string;
    name: string;
};
