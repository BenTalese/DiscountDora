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
    /** Recipes cookable right now (nothing missing, at least one ingredient).
     *  Server-computed (§3.3) so the card shows the count without the client
     *  fetching + joining every recipe against the whole pantry.
     *  IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — excludes recipes with any
     *  unlinked required ingredient (those are tri-state None, not True).
     *  See ``needs_linking_count`` for that tally. */
    cookable_count: number;
    /** IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — recipes with ≥1 unlinked
     *  required ingredient. The Dashboard "Cookable tonight" card can
     *  render "N cookable · M need linking" when M > 0. Zero until the
     *  paste importer ships (Chunk 5) — no existing recipe has unlinked
     *  ingredients. */
    needs_linking_count: number;
};

export type MealSummary = {
    total_definitions: number;
    total_in_stock: number;
};

export type UpcomingMealPlanEntry = {
    recipe_id: string;
    recipe_name: string;
    scheduled_for: string; // ISO date
    slot: string;
    servings: number;
    /** FU-298 — count of missing ingredients for this entry's recipe, derived
     *  server-side from the shared cookability map. `null` for empty recipes
     *  (no ingredients) OR for tri-state None recipes with unlinked
     *  ingredients (Chunk 4). `0` = ready to cook; > 0 = N missing. Use
     *  ``unlinked_ingredient_count`` to distinguish the two null cases. */
    missing_count: number | null;
    /** IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — number of required
     *  ingredients on this entry's recipe that have no stock_item
     *  link. Non-zero ⇒ badge shows "N need linking" instead of the
     *  ambiguous "No ingredients". */
    unlinked_ingredient_count: number;
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
