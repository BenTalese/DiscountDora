export type MealPlanTemplateSummary = {
    meal_plan_template_id: string;
    name: string;
    description: string | null;
    entry_count: number;
    created_at: string;
    updated_at: string;
};

export type MealPlanTemplateEntry = {
    recipe_id: string;
    recipe_name: string;
    offset_from_monday: number;
    slot: string;
    servings: number;
};

export type MealPlanTemplateDetail = {
    meal_plan_template_id: string;
    name: string;
    description: string | null;
    created_at: string;
    updated_at: string;
    entries: MealPlanTemplateEntry[];
};

/** Result of forking a week from a template (POST /meal-plans/from-template). */
export type ApplyTemplateResult = {
    meal_plan_id: string | null;
    added_count: number;
    skipped_past_count: number;
    replaced_count: number;
};

/** Result of a recurring apply (POST /meal-plans/from-template/recurring). */
export type RecurringApplyResult = {
    weeks_applied: number;
    total_added: number;
    total_skipped_past: number;
    first_meal_plan_id: string | null;
};
