import { acceptHMRUpdate, defineStore } from 'pinia';
import type { MealPlan, MealPlanIngredient, Shortfall } from 'src/models/mealPlan';
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

    const getIngredientsForPlanAsync = async (id: string): Promise<MealPlanIngredient[]> =>
        await api.getIngredientsAsync(id);

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
        getShortfallAsync,
        getTodayAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMealPlanStore, import.meta.hot));
}
