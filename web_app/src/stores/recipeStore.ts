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

    // Reactive so consumers can distinguish "still hydrating" from
    // "hydrated and the id genuinely doesn't resolve" (FU-109 deep-link chip).
    const recipesHydrated = ref(false);
    let recipesInflight: Promise<void> | null = null;
    let collectionsHydrated = false;
    let collectionsInflight: Promise<void> | null = null;

    const getRecipesAsync = () =>
        recipeApiService.getAllAsync().then((page) => {
            recipes.value = [...page.items].sort((a, b) => collator.compare(a.name, b.name));
            recipesHydrated.value = true;
        });

    const getRecipeCollectionsAsync = () =>
        recipeCollectionApiService.getAllAsync().then((page) => {
            recipeCollections.value = [...page.items].sort((a, b) => collator.compare(a.name, b.name));
            collectionsHydrated = true;
        });

    /** R-016 — lazy hydration for the recipes list. Call this in `onMounted`
     *  when you need the collection populated but don't care about a forced
     *  refresh. Call `getRecipesAsync` directly for an explicit refetch
     *  (post-mutation, pull-to-refresh). */
    const ensureLoadedAsync = (): Promise<void> => {
        if (recipesHydrated.value) return Promise.resolve();
        recipesInflight ??= getRecipesAsync().finally(() => { recipesInflight = null; });
        return recipesInflight;
    };

    /** R-016 — lazy hydration for the collections list (independent fetch). */
    const ensureCollectionsLoadedAsync = (): Promise<void> => {
        if (collectionsHydrated) return Promise.resolve();
        collectionsInflight ??= getRecipeCollectionsAsync().finally(() => { collectionsInflight = null; });
        return collectionsInflight;
    };

    const createRecipeAsync = async (command: CreateRecipeCommand): Promise<Recipe> => {
        const resource = await recipeApiService.createAsync(command);
        const entity =
            'recipe_id' in resource
                ? (resource as unknown as Recipe)
                : await recipeApiService.getAsync(resource.id as string);
        recipes.value.push(entity);
        recipes.value.sort((a, b) => collator.compare(a.name, b.name));
        // callers (RecipeEditDialog) navigate to the new detail
        // page after create, so we hand back the entity we just resolved.
        return entity;
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

    const cookAsync = async (recipeId: string, mealsCooked: number) => {
        await recipeApiService.cookAsync(recipeId, mealsCooked);
        const updated = await recipeApiService.getAsync(recipeId);
        const idx = recipes.value.findIndex((r) => r.recipe_id === recipeId);
        if (idx >= 0) recipes.value[idx] = updated;
    };

    const adjustMealsAsync = async (recipeId: string, delta: number) => {
        const { available_meals } = await recipeApiService.adjustMealsAsync(recipeId, delta);
        const idx = recipes.value.findIndex((r) => r.recipe_id === recipeId);
        if (idx >= 0) {
            recipes.value[idx] = { ...recipes.value[idx]!, available_meals };
        }
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
        recipesHydrated: readonly(recipesHydrated),
        recipeCollections: readonly(recipeCollections),
        getRecipesAsync,
        getRecipeCollectionsAsync,
        ensureLoadedAsync,
        ensureCollectionsLoadedAsync,
        createRecipeAsync,
        updateRecipeAsync,
        deleteRecipeAsync,
        toggleFavouriteAsync,
        cookAsync,
        adjustMealsAsync,
        createRecipeCollectionAsync,
        updateRecipeCollectionAsync,
        deleteRecipeCollectionAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useRecipeStore, import.meta.hot));
}
