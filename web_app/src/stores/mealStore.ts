import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Meal, MealPlan, MealPlanIngredient } from 'src/models/meal';
import type { CreateMealCommand, UpdateMealCommand } from 'src/services/api/mealApiService';
import MealApiService from 'src/services/api/mealApiService';
import type {
    CreateMealPlanCommand,
    UpdateMealPlanCommand
} from 'src/services/api/mealPlanApiService';
import MealPlanApiService from 'src/services/api/mealPlanApiService';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const mealApiService = new MealApiService();
const mealPlanApiService = new MealPlanApiService();

export const useMealStore = defineStore('meal', () => {
    const meals: Ref<Meal[]> = ref([]);
    const mealPlans: Ref<MealPlan[]> = ref([]);

    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    const getMealsAsync = () =>
        mealApiService.getAllAsync().then((page) => {
            meals.value = [...page.items].sort((a, b) => collator.compare(a.name, b.name));
        });

    const getMealPlansAsync = () =>
        mealPlanApiService.getAllAsync().then((page) => {
            mealPlans.value = [...page.items].sort((a, b) => a.start_date.localeCompare(b.start_date));
        });

    const createMealAsync = async (command: CreateMealCommand) => {
        const resource = await mealApiService.createAsync(command);
        const entity =
            'meal_id' in resource
                ? (resource as unknown as Meal)
                : await mealApiService.getAsync(resource.id as string);
        meals.value.push(entity);
        meals.value.sort((a, b) => collator.compare(a.name, b.name));
    };

    const updateMealAsync = async (command: UpdateMealCommand) => {
        await mealApiService.updateAsync(command);
        const updated = await mealApiService.getAsync(command.meal_id);
        const idx = meals.value.findIndex((m) => m.meal_id === command.meal_id);
        if (idx >= 0) meals.value[idx] = updated;
    };

    const deleteMealAsync = async (mealId: string) => {
        await mealApiService.deleteAsync(mealId);
        meals.value = meals.value.filter((m) => m.meal_id !== mealId);
    };

    const adjustStockAsync = async (mealId: string, delta: number) => {
        await mealApiService.adjustStockAsync(mealId, delta);
        const updated = await mealApiService.getAsync(mealId);
        const idx = meals.value.findIndex((m) => m.meal_id === mealId);
        if (idx >= 0) meals.value[idx] = updated;
    };

    const createMealPlanAsync = async (command: CreateMealPlanCommand) => {
        await mealPlanApiService.createAsync(command);
        await getMealPlansAsync();
    };

    const updateMealPlanAsync = async (command: UpdateMealPlanCommand) => {
        await mealPlanApiService.updateAsync(command);
        await getMealPlansAsync();
    };

    const deleteMealPlanAsync = async (mealPlanId: string) => {
        await mealPlanApiService.deleteAsync(mealPlanId);
        mealPlans.value = mealPlans.value.filter((p) => p.meal_plan_id !== mealPlanId);
    };

    const getIngredientsForPlanAsync = (mealPlanId: string): Promise<MealPlanIngredient[]> =>
        mealPlanApiService.getIngredientsAsync(mealPlanId);

    return {
        // Plain ref (not readonly): consumers pass meals into display
        // components and helpers typed as mutable Meal[].
        meals,
        mealPlans: readonly(mealPlans),
        getMealsAsync,
        getMealPlansAsync,
        createMealAsync,
        updateMealAsync,
        deleteMealAsync,
        adjustStockAsync,
        createMealPlanAsync,
        updateMealPlanAsync,
        deleteMealPlanAsync,
        getIngredientsForPlanAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMealStore, import.meta.hot));
}
