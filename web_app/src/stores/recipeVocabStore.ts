import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Category, Cuisine, DietaryTag, Tool } from 'src/models/recipeVocab';
import CategoryApiService from 'src/services/api/categoryApiService';
import CuisineApiService from 'src/services/api/cuisineApiService';
import DietaryTagApiService from 'src/services/api/dietaryTagApiService';
import ToolApiService from 'src/services/api/toolApiService';
import type { Ref } from 'vue';
import { ref } from 'vue';

// C-4 Chunk 2 — shared cache of the three recipe vocabularies, consumed by
// the cookbook overview filters and the recipe edit surfaces. The settings
// pages talk to the api services directly (CRUD); this store is read-mostly.

const cuisineApi = new CuisineApiService();
const categoryApi = new CategoryApiService();
const dietaryTagApi = new DietaryTagApiService();
const toolApi = new ToolApiService();

export const useRecipeVocabStore = defineStore('recipeVocab', () => {
    const cuisines: Ref<Cuisine[]> = ref([]);
    const categories: Ref<Category[]> = ref([]);
    const dietaryTags: Ref<DietaryTag[]> = ref([]);
    const tools: Ref<Tool[]> = ref([]);

    const getCuisinesAsync = async () => {
        cuisines.value = await cuisineApi.getAllAsync();
    };
    const getCategoriesAsync = async () => {
        categories.value = await categoryApi.getAllAsync();
    };
    const getDietaryTagsAsync = async () => {
        dietaryTags.value = await dietaryTagApi.getAllAsync();
    };
    const getToolsAsync = async () => {
        tools.value = await toolApi.getAllAsync();
    };

    const getAllAsync = async () => {
        await Promise.all([
            getCuisinesAsync(),
            getCategoriesAsync(),
            getDietaryTagsAsync(),
            getToolsAsync(),
        ]);
    };

    return {
        cuisines,
        categories,
        dietaryTags,
        tools,
        getCuisinesAsync,
        getCategoriesAsync,
        getDietaryTagsAsync,
        getToolsAsync,
        getAllAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useRecipeVocabStore, import.meta.hot));
}
