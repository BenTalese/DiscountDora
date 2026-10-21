import { acceptHMRUpdate, defineStore } from 'pinia';
import type {
    MealPlan, MealPlanIngredients, MealPlanSuggestion, Shortfall,
} from 'src/models/mealPlan';
import MealPlanApiService, {
    type CreateMealPlanCommand,
    type UpdateMealPlanCommand,
} from 'src/services/api/mealPlanApiService';
import type { Ref } from 'vue';
import { ref } from 'vue';

const api = new MealPlanApiService();

export const useMealPlanStore = defineStore('mealPlan', () => {
    const mealPlans: Ref<MealPlan[]> = ref([]);
    const shortfall: Ref<Shortfall[]> = ref([]);
    // Household "today" (ISO) in the install's timezone — server-owned (C-2.K).
    const today: Ref<string | null> = ref(null);

    const getMealPlansAsync = async () => {
        const page = await api.getAllAsync();
        mealPlans.value = page.items;
    };

    const createMealPlanAsync = async (command: CreateMealPlanCommand) => {
        await api.createAsync(command);
        await getMealPlansAsync();
    };

    const updateMealPlanAsync = async (command: UpdateMealPlanCommand) => {
        await api.updateAsync(command);
        await getMealPlansAsync();
    };

    const deleteMealPlanAsync = async (id: string) => {
        await api.deleteAsync(id);
        mealPlans.value = mealPlans.value.filter((p) => p.meal_plan_id !== id);
    };

    const getIngredientsForPlanAsync = async (id: string): Promise<MealPlanIngredients> =>
        await api.getIngredientsAsync(id);

    /** BRIEF_MEAL_PLANNER_RAIL_AND_SHELL §4.4 — the rail's ranked suggestions
     *  for one week. Deliberately NOT cached in the store: the ranking is only
     *  valid for the week it was asked about (it excludes what's already
     *  planned there), so the caller owns the week-scoped cache and the store
     *  stays a pass-through. */
    const getWeekSuggestionsAsync = async (
        weekStart: string,
    ): Promise<MealPlanSuggestion[]> =>
        (await api.getWeekSuggestionsAsync(weekStart)).suggestions;

    /**
     * `GET /meal-plans/shortfall` — the recipe-level report: how many *servings*
     * short of its plan each recipe is.
     *
     * **No client consumer since 2026-09-03.** The meal planner was the only
     * one, and it used these rows to decide which meal chips to mark as needing
     * a cook — a recipe-level answer to a per-entry question, which is why three
     * planned fried rices all lit up when the pool covered two. That verdict now
     * rides on the plan entries themselves (`MealPlanEntry.needs_cooking`), so
     * the planner stopped fetching this; keeping the second fetch would have
     * left two answers to one question in the client (R-003).
     *
     * Kept rather than deleted because the *endpoint* is live and answers a
     * different question (servings short, not meals to cook) — the assistant's
     * `meals_shortfall` tool reads it server-side. If nothing on the client
     * claims it, this and `MealPlanApiService.getShortfallAsync` should go; see
     * DORA_FOLLOWUPS FU-862.
     */
    const getShortfallAsync = async () => {
        shortfall.value = await api.getShortfallAsync();
    };

    const getTodayAsync = async () => {
        today.value = await api.getTodayAsync();
    };

    return {
        mealPlans,
        shortfall,
        today,
        getMealPlansAsync,
        createMealPlanAsync,
        updateMealPlanAsync,
        deleteMealPlanAsync,
        getIngredientsForPlanAsync,
        getWeekSuggestionsAsync,
        getShortfallAsync,
        getTodayAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMealPlanStore, import.meta.hot));
}
