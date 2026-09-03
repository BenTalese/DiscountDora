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
    // PROPOSAL_MEAL_PLANS_PART_2 — cook-batch view. `cook_batch_id` groups the
    // linked meals (one cook, several days); the rest are server-derived across
    // the batch. Null/false for a standalone meal.
    cook_batch_id: string | null;
    is_cook_day: boolean;
    cook_batch_total_servings: number | null;
    cook_batch_size: number | null;
    // FU-637 — what one serving of this meal costs, calorie-wise, in the
    // install's current nutrition mode. Server-owned (same figure the cookbook
    // card shows). Null when nutrition is off or the recipe has no figure.
    kcal_per_serving: number | null;
    kcal_is_reliable: boolean;
    /** FU-653 — Dora's belief about this planned meal: `'at_risk'` (an
     *  ingredient she thinks has run out since you planned it) or
     *  `'maybe_cookable'`. Additive only — the week's shortfall and "need to
     *  buy" figures ignore it. Null on cooked entries, and unless the user
     *  opted the meal-planner surface in. */
    inference_hint: 'at_risk' | 'maybe_cookable' | null;
    inference_stock_item_names: string[];
    /** Owner feedback 2026-09-03 — *"if I have 3 meals of fried rice planned
     *  and 2 in the pool, I'd expect the LAST of the 3 to highlight orange.
     *  Currently they all light up."* The per-entry verdict from the server's
     *  pool allocation (soonest-first, and batch-aware: a leftover day is
     *  covered by its own cook). Replaces the client's old "is this entry's
     *  RECIPE in the shortfall set?" test, which lit every entry of a short
     *  recipe. Always false when the household's cook-style is "fresh". */
    needs_cooking: boolean;
};

/** FU-637 — one day's planned calories: "a serving of each meal planned that
 *  day". Not an intake figure — a meal plan schedules pots of food, not plates
 *  for named people. Coverage travels with it: meals whose figure isn't
 *  reliable are left out of the sum and counted in the shortfall. */
export type MealPlanDayNutrition = {
    scheduled_for: string;
    kcal_per_serving: number | null;
    counted_meals: number;
    total_meals: number;
};

export type MealPlan = {
    meal_plan_id: string;
    // instances are nameless (UI shows "Week starting <date>").
    name: string | null;
    start_date: string;
    entries: MealPlanEntry[];
    /** FU-637 — per-day rollup over `entries`, summed server-side. Empty when
     *  nutrition is off. */
    day_nutrition: MealPlanDayNutrition[];
};

export type MealPlanIngredient = {
    stock_item_id: string;
    stock_item_name: string;
    total_quantity: number | null;
    unit: string | null;
    used_in_recipe_ids: string[];
    /** Owner feedback 2026-08-27 — server-owned; true only when *every*
     *  contributing ingredient row across the week was optional. Drives the
     *  shared add-to-list picker's Optional section. */
    is_optional: boolean;
};

/** An ingredient row with no linked stock item, so it can't become a
 *  shopping-list line (FU-505). Reported so the picker can name what it
 *  couldn't take rather than dropping it silently. */
export type UnlinkedIngredient = {
    recipe_name: string;
    ingredient_name: string;
};

/** Envelope returned by both the saved-plan `/ingredients` endpoint and the
 *  builder's `/preview-ingredients`. Was a bare array until 2026-08-27 —
 *  `unlinked` has no per-item home. */
export type MealPlanIngredients = {
    items: MealPlanIngredient[];
    unlinked: UnlinkedIngredient[];
};

export type Shortfall = {
    recipe_id: string;
    recipe_name: string;
    available_meals: number;
    committed_meals: number;
    shortfall: number;
    earliest_needed: string | null;
};

// ── FU-596 — "Build my week" auto-planner ───────────────────────────────
// Mirrors dora_api/features/meal_plans/build_week.py. Selection + slot/day
// placement are server-owned (R-003); the client sends guidance and renders
// / edits / commits the returned proposal.

export type AutoBuildEmphasis = 'use_up_stock' | 'variety' | 'favourites' | 'surprise';

/** Reason chip frozen server-side per proposed meal. */
export type AutoBuildReason =
    | 'uses_expiring'
    | 'cookable_now'
    | 'favourite'
    | 'not_made_recently'
    | 'variety'
    | 'budget_friendly'
    | 'picked';

export type AutoBuildRequest = {
    /** The days the user toggled on (ISO). One meal per day × slot cell, so
     *  the toggles are the meal count — there is no separate knob. */
    days: string[];
    emphasis: AutoBuildEmphasis;
    /** Empty ⇒ every household slot; a subset ⇒ just those. */
    slot_names: string[];
    /** Build one day's line-up and duplicate it to the other selected days. */
    repeat_same_day: boolean;
    budget_cap: boolean;
    /** Servings every proposed meal is created at. The dialog seeds it from
     *  the household headcount (Settings -> Cooking); the review step still
     *  edits each row. */
    default_servings: number;
};

export type ProposedEntry = {
    recipe_id: string;
    recipe_name: string;
    scheduled_for: string;   // ISO date
    slot: string;
    servings: number;
    reason_chip: AutoBuildReason;
    cookable: boolean | null;
    missing_stock_item_names: string[];
    estimated_cost: number | null;
    // PROPOSAL_MEAL_PLANS_PART_2 §9 — grouping token for a proposed cook batch
    // (Batch households). Entries sharing it are one cook; null = standalone.
    cook_key: string | null;
};

/**
 * The server's frozen reason vocabulary (`build_week.py:88-94`, annotated
 * "frozen server-side, R-003"). The rail maps these tokens to copy; it must not
 * invent a token, and a new one must be added on the server first.
 */
export type SuggestionReasonChip =
    | 'uses_expiring'
    | 'cookable_now'
    | 'favourite'
    | 'not_made_recently'
    | 'variety'
    | 'budget_friendly'
    | 'picked';

export type MealPlanSuggestion = {
    recipe_id: string;
    reason_chip: SuggestionReasonChip;
};

export type MealPlanSuggestions = {
    suggestions: MealPlanSuggestion[];
};

export type AutoBuildResponse = {
    entries: ProposedEntry[];
    /** The requested days the server actually built into (past days dropped). */
    days_used: string[];
    slots_used: string[];
    cost_total: number | null;
    budget_amount: number | null;
    projected_over: boolean;
};
