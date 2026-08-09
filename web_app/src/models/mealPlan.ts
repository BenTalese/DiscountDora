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
    // instances are nameless (UI shows "Week starting <date>").
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
