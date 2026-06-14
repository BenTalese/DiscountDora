import { acceptHMRUpdate, defineStore } from 'pinia';
import type { MealSlot } from 'src/models/mealSlot';
import MealSlotApiService from 'src/services/api/mealSlotApiService';
import type { Ref } from 'vue';
import { computed, ref } from 'vue';

// C-2.A — shared cache of the household-wide meal-slot vocabulary, consumed
// by the planner edit dialog and the recipe `time_of_day` pickers. The
// settings page talks to the api service directly (CRUD); this store is
// read-mostly, mirroring recipeVocabStore.

const mealSlotApi = new MealSlotApiService();

export const useMealSlotStore = defineStore('mealSlot', () => {
    const mealSlots: Ref<MealSlot[]> = ref([]);

    // Ordered slot names — the shape every read-site dropdown wants.
    const mealSlotNames = computed(() =>
        [...mealSlots.value]
            .sort((a, b) => a.sequence - b.sequence || a.name.localeCompare(b.name))
            .map((s) => s.name),
    );

    const getMealSlotsAsync = async () => {
        mealSlots.value = await mealSlotApi.getAllAsync();
    };

    return {
        mealSlots,
        mealSlotNames,
        getMealSlotsAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMealSlotStore, import.meta.hot));
}
