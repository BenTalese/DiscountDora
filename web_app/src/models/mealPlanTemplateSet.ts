export type MealPlanTemplateSetItem = {
    template_id: string;
    template_name: string;
    position: number;
};

export type MealPlanTemplateSetSummary = {
    meal_plan_template_set_id: string;
    name: string;
    description: string | null;
    item_count: number;
    /** Template names in rotation order. */
    template_names: string[];
    created_at: string;
    updated_at: string;
};

export type MealPlanTemplateSetDetail = {
    meal_plan_template_set_id: string;
    name: string;
    description: string | null;
    created_at: string;
    updated_at: string;
    items: MealPlanTemplateSetItem[];
};
