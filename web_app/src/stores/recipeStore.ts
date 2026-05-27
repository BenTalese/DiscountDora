import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Recipe, RecipeCollection } from 'src/models/recipe';
import type { CreateRecipeCommand, UpdateRecipeCommand } from 'src/services/api/recipeApiService';
import RecipeApiService from 'src/services/api/recipeApiService';
import type {
    CreateRecipeCollectionCommand,
    UpdateRecipeCollectionCommand
} from 'src/services/api/recipeCollectionApiService';
import RecipeCollectionApiService from 'src/services/api/recipeCollectionApiService';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const recipeApiService = new RecipeApiService();
const recipeCollectionApiService = new RecipeCollectionApiService();

export const useRecipeStore = defineStore('recipe', () => {
    const recipes: Ref<Recipe[]> = ref([]);
    const recipeCollections: Ref<RecipeCollection[]> = ref([]);

    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    const getRecipesAsync = () =>
        recipeApiService.getAllAsync().then((page) => {
            recipes.value = [...page.items].sort((a, b) => collator.compare(a.name, b.name));
        });

    const getRecipeCollectionsAsync = () =>
        recipeCollectionApiService.getAllAsync().then((page) => {
            recipeCollections.value = [...page.items].sort((a, b) => collator.compare(a.name, b.name));
        });

    const createRecipeAsync = async (command: CreateRecipeCommand) => {
        const resource = await recipeApiService.createAsync(command);
        const entity =
            'recipe_id' in resource
                ? (resource as unknown as Recipe)
                : await recipeApiService.getAsync(resource.id as string);
        recipes.value.push(entity);
        recipes.value.sort((a, b) => collator.compare(a.name, b.name));
    };

    const updateRecipeAsync = async (command: UpdateRecipeCommand) => {
        await recipeApiService.updateAsync(command);
        const updated = await recipeApiService.getAsync(command.recipe_id);
        const idx = recipes.value.findIndex((r) => r.recipe_id === command.recipe_id);
        if (idx >= 0) {
            recipes.value[idx] = updated;
        } else {
            recipes.value.push(updated);
        }
    };

    const deleteRecipeAsync = async (recipeId: string) => {
        await recipeApiService.deleteAsync(recipeId);
        recipes.value = recipes.value.filter((r) => r.recipe_id !== recipeId);
    };

    const toggleFavouriteAsync = async (recipe: Recipe) =>
        updateRecipeAsync({ recipe_id: recipe.recipe_id, is_favourite: !recipe.is_favourite });

    const markMadeAsync = async (recipeId: string) => {
        await recipeApiService.markMadeAsync(recipeId);
        const updated = await recipeApiService.getAsync(recipeId);
        const idx = recipes.value.findIndex((r) => r.recipe_id === recipeId);
        if (idx >= 0) recipes.value[idx] = updated;
    };

    const createRecipeCollectionAsync = async (command: CreateRecipeCollectionCommand) => {
        await recipeCollectionApiService.createAsync(command);
        await getRecipeCollectionsAsync();
    };

    const updateRecipeCollectionAsync = async (command: UpdateRecipeCollectionCommand) => {
        await recipeCollectionApiService.updateAsync(command);
        await getRecipeCollectionsAsync();
    };

    const deleteRecipeCollectionAsync = async (recipeCollectionId: string) => {
        await recipeCollectionApiService.deleteAsync(recipeCollectionId);
        recipeCollections.value = recipeCollections.value.filter(
            (c) => c.recipe_collection_id !== recipeCollectionId
        );
    };

    return {
        // Exposed as a plain ref (not readonly): consumers pass recipes into
        // display components and filter helpers typed as mutable Recipe[].
        recipes,
        recipeCollections: readonly(recipeCollections),
        getRecipesAsync,
        getRecipeCollectionsAsync,
        createRecipeAsync,
        updateRecipeAsync,
        deleteRecipeAsync,
        toggleFavouriteAsync,
        markMadeAsync,
        createRecipeCollectionAsync,
        updateRecipeCollectionAsync,
        deleteRecipeCollectionAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useRecipeStore, import.meta.hot));
}
