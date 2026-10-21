import { acceptHMRUpdate, defineStore } from 'pinia';
import type { MealPlanTemplateSetSummary } from 'src/models/mealPlanTemplateSet';
import MealPlanTemplateSetApiService, {
    type CreateMealPlanTemplateSetCommand,
    type UpdateMealPlanTemplateSetCommand,
} from 'src/services/api/mealPlanTemplateSetApiService';
import type { Ref } from 'vue';
import { ref } from 'vue';

const api = new MealPlanTemplateSetApiService();

export const useMealPlanTemplateSetStore = defineStore('mealPlanTemplateSet', () => {
    const sets: Ref<MealPlanTemplateSetSummary[]> = ref([]);

    const getSetsAsync = async () => {
        sets.value = await api.getAllAsync();
    };

    const createAsync = async (command: CreateMealPlanTemplateSetCommand) => {
        await api.createAsync(command);
        await getSetsAsync();
    };

    const updateAsync = async (id: string, command: UpdateMealPlanTemplateSetCommand) => {
        await api.updateAsync(id, command);
        await getSetsAsync();
    };

    const deleteAsync = async (id: string) => {
        await api.deleteAsync(id);
        await getSetsAsync();
    };

    return { sets, getSetsAsync, createAsync, updateAsync, deleteAsync };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMealPlanTemplateSetStore, import.meta.hot));
}
