<template>
    <div class="q-pa-md">
        <div class="row items-center q-mb-md">
            <div class="text-h5 q-mr-md">Recipes</div>
            <q-btn color="positive" icon="add" label="New Recipe" @click="onCreateClick" />
            <q-space />
            <q-input
                dense
                debounce="200"
                placeholder="Search"
                v-model="searchText"
                clearable
                outlined
            >
                <template #append><q-icon name="search" /></template>
            </q-input>
        </div>

        <div class="row q-mb-md q-gutter-sm items-center">
            <q-toggle v-model="favouritesOnly" label="Favourites only" />
            <q-select
                dense
                outlined
                style="min-width: 200px"
                emit-value
                map-options
                clearable
                v-model="collectionFilter"
                :options="collectionOptions"
                label="Collection"
            />
            <q-select
                dense
                outlined
                style="min-width: 200px"
                emit-value
                map-options
                v-model="stockFilter"
                :options="stockFilterOptions"
                label="Stock"
            />
        </div>

        <div class="row q-col-gutter-md">
            <div
                class="col-12 col-sm-6 col-md-4"
                v-for="recipe in filteredRecipes"
                :key="recipe.recipe_id"
            >
                <q-card
                    :class="{ 'recipe-disabled': hasOutOfStock(recipe) }"
                    bordered
                    class="recipe-card"
                >
                    <q-card-section>
                        <div class="row items-center no-wrap">
                            <div class="text-h6 ellipsis">{{ recipe.name }}</div>
                            <q-space />
                            <q-btn
                                :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                                :color="recipe.is_favourite ? 'red' : 'grey'"
                                flat
                                round
                                dense
                                @click="recipeStore.toggleFavouriteAsync(recipe)"
                            />
                        </div>
                        <div class="text-caption text-grey">
                            <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
                            <span v-if="recipe.cuisine && recipe.category"> · </span>
                            <span v-if="recipe.category">{{ recipe.category }}</span>
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row q-gutter-sm">
                            <q-chip v-if="totalTime(recipe) !== null" dense icon="schedule">
                                {{ totalTime(recipe) }} min
                            </q-chip>
                            <q-chip v-if="recipe.difficulty" dense icon="star_outline">
                                {{ recipe.difficulty }}
                            </q-chip>
                            <q-chip v-if="recipe.servings" dense icon="restaurant">
                                Serves {{ recipe.servings }}
                            </q-chip>
                        </div>
                        <div class="q-mt-sm text-caption">
                            <q-icon name="check_circle" color="positive" />
                            {{ ingredientCount(recipe, 'in') }} in stock,
                            <q-icon name="warning" color="warning" />
                            {{ ingredientCount(recipe, 'low') }} low,
                            <q-icon name="cancel" color="negative" />
                            {{ ingredientCount(recipe, 'out') }} out
                        </div>
                    </q-card-section>

                    <q-card-actions align="right">
                        <q-btn flat label="Cook" color="primary" icon="restaurant_menu" @click="onCookClick(recipe)" />
                        <q-btn flat label="Edit" @click="onEditClick(recipe)" />
                        <q-btn flat label="Mark Made" @click="recipeStore.markMadeAsync(recipe.recipe_id)" />
                        <q-btn flat icon="delete" color="negative" @click="confirmDelete(recipe)" />
                    </q-card-actions>
                </q-card>
            </div>

            <div class="col-12" v-if="filteredRecipes.length === 0">
                <q-banner class="bg-grey-2">No recipes match your filters.</q-banner>
            </div>
        </div>

        <RecipeEditDialog
            v-model="editDialogOpen"
            :recipe="editingRecipe"
            @saved="onSaved"
        />
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { Recipe } from 'src/models/recipe';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import RecipeEditDialog from 'components/RecipeEditDialog.vue';

    const $q = useQuasar();
    const router = useRouter();
    const recipeStore = useRecipeStore();
    // stockItemStore is loaded so the recipe edit dialog has stock items to
    // pick from when creating/editing a recipe.
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();

    const { recipes, recipeCollections } = storeToRefs(recipeStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const searchText = ref('');
    const favouritesOnly = ref(false);
    const collectionFilter = ref<string | null>(null);
    const stockFilter = ref<'all' | 'inStock' | 'hideOutOfStock'>('all');

    const stockFilterOptions = [
        { label: 'All recipes', value: 'all' },
        { label: 'All ingredients in stock', value: 'inStock' },
        { label: 'Hide recipes with out-of-stock items', value: 'hideOutOfStock' }
    ];

    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({ label: c.name, value: c.recipe_collection_id }))
    );

    const outOfStockLevelId = computed(
        () => stockLevels.value.find((l) => l.name === 'Out of Stock')?.stock_level_id ?? null
    );
    const lowStockLevelId = computed(
        () => stockLevels.value.find((l) => l.name === 'Low Stock')?.stock_level_id ?? null
    );

    function ingredientCount(recipe: Recipe, kind: 'in' | 'low' | 'out'): number {
        return recipe.ingredients.filter((i) => {
            if (kind === 'out') return i.stock_level_id === outOfStockLevelId.value;
            if (kind === 'low') return i.stock_level_id === lowStockLevelId.value;
            return (
                i.stock_level_id !== outOfStockLevelId.value &&
                i.stock_level_id !== lowStockLevelId.value
            );
        }).length;
    }

    function hasOutOfStock(recipe: Recipe): boolean {
        return ingredientCount(recipe, 'out') > 0;
    }

    function totalTime(recipe: Recipe): number | null {
        if (recipe.prep_time_minutes === null && recipe.cook_time_minutes === null) return null;
        return (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);
    }

    const filteredRecipes = computed(() =>
        recipes.value.filter((r) => {
            if (favouritesOnly.value && !r.is_favourite) return false;
            if (collectionFilter.value && r.recipe_collection_id !== collectionFilter.value)
                return false;
            if (stockFilter.value === 'hideOutOfStock' && hasOutOfStock(r)) return false;
            if (stockFilter.value === 'inStock' && hasOutOfStock(r)) return false;
            if (stockFilter.value === 'inStock' && ingredientCount(r, 'low') > 0) return false;
            if (searchText.value) {
                const q = searchText.value.toLowerCase();
                if (!r.name.toLowerCase().includes(q)) return false;
            }
            return true;
        })
    );

    const editDialogOpen = ref(false);
    const editingRecipe = ref<Recipe | null>(null);

    function onCreateClick() {
        editingRecipe.value = null;
        editDialogOpen.value = true;
    }

    function onEditClick(recipe: Recipe) {
        editingRecipe.value = recipe;
        editDialogOpen.value = true;
    }

    function onCookClick(recipe: Recipe) {
        void router.push(`/recipes/${recipe.recipe_id}/cook`);
    }

    async function onSaved() {
        editDialogOpen.value = false;
        await recipeStore.getRecipesAsync();
    }

    function confirmDelete(recipe: Recipe) {
        $q.dialog({
            title: 'Delete recipe',
            message: `Delete "${recipe.name}"? This cannot be undone.`,
            cancel: true,
            persistent: true
        }).onOk(async () => {
            await recipeStore.deleteRecipeAsync(recipe.recipe_id);
        });
    }

    onMounted(async () => {
        await Promise.all([
            recipeStore.getRecipesAsync(),
            recipeStore.getRecipeCollectionsAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync()
        ]);
    });
</script>

<style scoped>
    .recipe-card {
        height: 100%;
    }
    .recipe-disabled {
        opacity: 0.55;
    }
</style>
