// Shape of GET /dashboard/summary — the single aggregated payload the
// dashboard renders from (AboutSettings' "at a glance" block also reads it).
//
// FU-826 trimmed seven fields that nothing in the app rendered: `products`
// and `meals` as whole sub-objects, `shopping_lists.total_items`, and
// `recipes.{favourites, cookable_count, needs_linking_count}`. They were
// shipped for the counter cards IMPL_PLAN_DASHBOARD_REBUILD Phase 1 deleted —
// the cards went, the payload behind them didn't. Two of them
// (`meals.*`) were dedicated aggregate queries running on every dashboard
// load. `shopping_lists.total_items` was additionally the subject of FU-767,
// a bug report about it over-counting; the honest fix for a field no surface
// renders is deletion, which retires that FU too.

export type StockItemSummary = {
    total: number;
    out_of_stock: number;
    low_stock: number;
};

export type ShoppingListSummary = {
    /** Active (non-done) lists. Drives the primary-list card's
     *  "+N other active lists" footer link. */
    total: number;
};

export type RecipeSummary = {
    /** Read by AboutSettings' at-a-glance block and the dashboard hero's
     *  "your recipe book's empty" nudge. */
    total: number;
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
    recipes: RecipeSummary;
    meal_plan: MealPlanSummary;
};
