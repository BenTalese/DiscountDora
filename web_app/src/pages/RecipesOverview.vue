<template>
    <div class="q-pa-md">
        <!-- ── Header ─────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md">
            <div class="text-caption dora-text-muted">
                {{ filteredRecipes.length }} of {{ recipes.length }} shown
                · {{ cookableNowCount }} cookable now
            </div>
            <q-space />
            <BaseButton
                :variant="compareMode ? 'primary' : 'secondary'"
                :label="compareMode ? `Comparing (${selectedIds.size}/3)` : 'Compare'"
                :icon="ICONS.compare"
                class="q-mr-sm"
                @click="toggleCompareMode"
            />
            <BaseButton
                v-if="compareMode"
                variant="primary"
                label="Show comparison"
                :icon="ICONS.open_in_new"
                class="q-mr-sm"
                :disable="selectedIds.size < 2"
                @click="showComparison = true"
            />
            <q-input
                dense
                debounce="200"
                placeholder="Search"
                v-model="searchText"
                clearable
                outlined
                class="q-mr-sm"
            >
                <template #append><q-icon :name="ICONS.search" /></template>
            </q-input>
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                label="New recipe"
                @click="onCreateClick"
            />
        </div>

        <!-- ── Filter bar ─ standardised via FilterBar (A4) ───────── -->
        <FilterBar :active-count="activeFilterCount" @clear="clearFilters">
            <template #filters>
            <div class="row q-gutter-sm items-center">
            <q-toggle v-model="favouritesOnly" label="Favourites only" dense />
            <q-toggle v-model="cookableNowOnly" label="Cookable now" dense />
            <q-input
                v-model.number="missingMax"
                dense
                outlined
                type="number"
                min="0"
                style="max-width: 130px"
                label="Missing ≤"
                :hint="missingMax !== null ? `Hide if missing > ${missingMax}` : ''"
            />
            <q-select
                dense
                outlined
                style="min-width: 200px"
                emit-value
                map-options
                clearable
                v-model="collectionFilter"
                :options="collectionOptionsWithNone"
                label="Collection"
            />
            <q-select
                dense
                outlined
                style="min-width: 200px"
                multiple
                use-chips
                emit-value
                map-options
                v-model="tagFilter"
                :options="tagOptions"
                label="Tags (cuisine / category)"
            />
            <q-select
                dense
                outlined
                use-input
                input-debounce="150"
                style="min-width: 220px"
                emit-value
                map-options
                clearable
                v-model="usesStockItemId"
                :options="stockItemSearchOptions"
                @filter="onStockItemFilter"
                label="Uses stock item"
            />
            <!-- P2-08 — dietary tag filters. The "must have", "must not
                 have", and "free from ingredient" axes combine with AND,
                 mirroring how the backend reads the query string. -->
            <q-select
                dense
                outlined
                style="min-width: 220px"
                multiple
                use-chips
                emit-value
                map-options
                v-model="dietaryTagsInclude"
                :options="dietaryTagOptionsForInclude"
                label="Must have these tags"
            />
            <q-select
                dense
                outlined
                style="min-width: 220px"
                multiple
                use-chips
                emit-value
                map-options
                v-model="dietaryTagsExclude"
                :options="dietaryTagOptionsForExclude"
                label="Must NOT have these tags"
            />
            <q-select
                dense
                outlined
                use-input
                multiple
                use-chips
                new-value-mode="add-unique"
                hide-dropdown-icon
                style="min-width: 220px"
                v-model="ingredientExclude"
                :options="[]"
                label="Free from ingredient(s)"
                hint="Type and press Enter"
            />
            </div>
            </template>
        </FilterBar>
        <!-- P2-08 — disclaimer surfaced when any dietary filter is on.
             Pulled from the backend so the wording stays consistent
             between the SPA and Dora. -->
        <div
            v-if="(dietaryTagsInclude.length > 0 || dietaryTagsExclude.length > 0 || ingredientExclude.length > 0) && tagCatalogue?.disclaimer"
            class="text-caption dora-text-muted q-mb-md"
        >
            <q-icon name="info" size="14px" class="q-mr-xs" />
            {{ tagCatalogue.disclaimer }}
        </div>

        <!-- ── Grid grouped by collection ─────────────────────────── -->
        <FadeTransition mode="out-in">
        <div v-if="loading && recipes.length === 0" key="rec-loading" class="text-center q-py-xl">
            <q-spinner color="primary" size="48px" />
        </div>
        <div v-else key="rec-content">
            <div
                v-if="filteredRecipes.length === 0"
                class="text-center dora-text-muted q-py-xl"
            >
                <q-icon :name="ICONS.menu_book" size="60px" class="q-mb-sm" />
                <div>No recipes match the current filters.</div>
                <q-btn
                    v-if="hasAnyFilter"
                    flat
                    no-caps
                    color="primary"
                    label="Clear filters"
                    class="q-mt-sm"
                    @click="clearFilters"
                />
            </div>

            <div
                v-for="group in groups"
                :key="group.key"
                class="q-mb-lg"
            >
                <div class="row items-center q-mb-sm">
                    <q-icon :name="ICONS.folder" size="18px" class="q-mr-xs" />
                    <div class="text-subtitle1">{{ group.label }}</div>
                    <q-chip dense outline size="sm" class="q-ml-sm">
                        {{ group.recipes.length }}
                    </q-chip>
                </div>
                <div class="row q-col-gutter-md">
                    <div
                        v-for="recipe in group.recipes"
                        :key="recipe.recipe_id"
                        class="col-12 col-sm-6 col-md-4 col-lg-3"
                    >
                        <RecipeCard
                            :recipe="recipe"
                            :selectable="compareMode"
                            :selected="selectedIds.has(recipe.recipe_id)"
                            :highlight-stock-item-id="usesStockItemId ?? ''"
                            @open="onOpenRecipe"
                            @cook="onCookClick"
                            @edit="onEditClick"
                            @duplicate="onDuplicate"
                            @delete="confirmDelete"
                            @toggle-favourite="onToggleFavourite"
                            @toggle-select="onToggleSelect"
                            @add-missing="onAddMissing"
                            @add-all-to-list="onAddAllToList"
                            @add-to-meal-plan="onAddToMealPlan"
                        />
                    </div>
                </div>
            </div>
        </div>
        </FadeTransition>

        <!-- ── Edit dialog ────────────────────────────────────────── -->
        <RecipeEditDialog
            v-model="editDialogOpen"
            :recipe="editingRecipe"
            @saved="onSaved"
        />

        <!-- ── Add-missing-to-list dialog ─────────────────────────── -->
        <BaseDialog v-model="addMissingOpen" card-style="min-width: 380px; max-width: 480px">
                <q-card-section>
                    <div class="text-h6">Add to a shopping list</div>
                    <div class="text-caption dora-text-muted">
                        {{ addMissingPayload?.stockItemIds.length ?? 0 }}
                        item{{
                            (addMissingPayload?.stockItemIds.length ?? 0) === 1 ? '' : 's'
                        }} from
                        "{{ addMissingPayload?.recipeName }}"
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-select
                        v-model="addMissingTargetListId"
                        :options="activeListOptions"
                        emit-value
                        map-options
                        outlined
                        dense
                        label="Add to"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        unelevated
                        color="primary"
                        no-caps
                        label="Add"
                        :loading="addingMissing"
                        :disable="!addMissingTargetListId"
                        @click="confirmAddMissing"
                    />
                </q-card-actions>
        </BaseDialog>

        <!-- ── Comparison dialog ──────────────────────────────────── -->
        <BaseDialog
            v-model="showComparison"
            :maximized="$q.screen.lt.md"
            card-style="width: 95vw; max-width: 1200px; height: 90vh"
            card-class="column"
        >
                <q-card-section class="row items-center q-pb-sm">
                    <div class="text-h6">
                        Comparing {{ selectedRecipes.length }} recipe{{
                            selectedRecipes.length === 1 ? '' : 's'
                        }}
                    </div>
                    <q-space />
                    <q-btn flat round dense :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-separator />
                <q-card-section class="col scroll">
                    <div class="row q-col-gutter-md">
                        <div
                            v-for="recipe in selectedRecipes"
                            :key="recipe.recipe_id"
                            class="col-12 col-md-6 col-lg-4"
                        >
                            <q-card flat bordered class="full-height">
                                <q-card-section>
                                    <div class="text-subtitle1">{{ recipe.name }}</div>
                                    <div class="text-caption dora-text-muted">
                                        <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
                                        <span v-if="recipe.cuisine && recipe.category"> · </span>
                                        <span v-if="recipe.category">{{ recipe.category }}</span>
                                    </div>
                                </q-card-section>
                                <q-separator />
                                <q-list dense>
                                    <q-item>
                                        <q-item-section>Prep + cook</q-item-section>
                                        <q-item-section side>
                                            {{ totalTime(recipe) ?? '—' }}
                                            <span v-if="totalTime(recipe) !== null"> min</span>
                                        </q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>Servings</q-item-section>
                                        <q-item-section side>
                                            {{ recipe.servings ?? '—' }}
                                        </q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>Difficulty</q-item-section>
                                        <q-item-section side>
                                            {{ recipe.difficulty ?? '—' }}
                                        </q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>Ingredients</q-item-section>
                                        <q-item-section side>
                                            {{ recipe.ingredients.length }}
                                        </q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>Missing right now</q-item-section>
                                        <q-item-section side>
                                            {{ missingCount(recipe) }}
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                                <q-separator />
                                <q-card-section>
                                    <div class="text-caption dora-text-muted q-mb-xs">
                                        Ingredients
                                    </div>
                                    <q-chip
                                        v-for="ing in recipe.ingredients"
                                        :key="ing.recipe_ingredient_id"
                                        dense
                                        :color="
                                            missingStockItemNames(recipe).has(ing.stock_item_name)
                                                ? 'negative'
                                                : 'grey-3'
                                        "
                                        :text-color="
                                            missingStockItemNames(recipe).has(ing.stock_item_name)
                                                ? 'white'
                                                : undefined
                                        "
                                    >
                                        {{ ing.stock_item_name }}
                                        <span v-if="ing.quantity">
                                            &nbsp;{{ ing.quantity }}{{ ing.unit ?? '' }}
                                        </span>
                                    </q-chip>
                                </q-card-section>
                            </q-card>
                        </div>
                    </div>
                </q-card-section>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import RecipeEditDialog from 'components/RecipeEditDialog.vue';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();
    const recipeApi = new RecipeApiService();
    const { addItems } = useShoppingListActions();

    const { recipes, recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const loading = ref(false);

    // ── Filter state ────────────────────────────────────────────────
    const searchText = ref('');
    const favouritesOnly = ref(false);
    const cookableNowOnly = ref(false);
    // `null` means "no upper bound" — the input clears to null on backspace.
    const missingMax = ref<number | null>(null);
    const collectionFilter = ref<string | null>(null);
    const tagFilter = ref<string[]>([]);
    // Set via the "Uses stock item" picker OR via `?usesStockItem=` query
    // (deep-linked from the stock item detail screen).
    const usesStockItemId = ref<string | null>(null);

    // P2-08 — dietary filter state. All three combine with AND; the
    // include set is "must have all of these" and the exclude set is
    // "must have none of these". `ingredientExclude` is free-text (so
    // the user can type "egg yolks" or "shellfish"), matched as a
    // case-insensitive substring against the recipe's ingredient
    // stock-item names server-side.
    const dietaryTagsInclude = ref<string[]>([]);
    const dietaryTagsExclude = ref<string[]>([]);
    const ingredientExclude = ref<string[]>([]);
    const tagCatalogue = ref<RecipeTagCatalogue | null>(null);

    // Group tag options by their `category` so the dropdown reads as
    // small clustered sections instead of one long alphabetical list.
    const dietaryTagOptionsForInclude = computed(() =>
        (tagCatalogue.value?.tags ?? []).map((t) => ({
            label: `${t.category}: ${t.label}`,
            value: t.value,
        })),
    );
    const dietaryTagOptionsForExclude = computed(() => dietaryTagOptionsForInclude.value);

    // ── Cookable / missing helpers ──────────────────────────────────
    // Same definition as RecipeCard: missing = not tracked OR out of stock.
    // Duplicated here (rather than imported from the component) so filter
    // logic doesn't depend on a component being mounted.
    const outOfStockLevelId = computed(
        () => stockLevels.value.find((l) => l.name === 'Out of Stock')?.stock_level_id ?? null,
    );

    function isMissing(stockItemId: string): boolean {
        if (!stockItemId) return true;
        const item = stockItems.value.find((si) => si.stock_item_id === stockItemId);
        if (!item) return true;
        return item.stock_level_id === outOfStockLevelId.value;
    }

    function missingCount(recipe: Recipe): number {
        const seen = new Set<string>();
        let count = 0;
        for (const ing of recipe.ingredients) {
            if (!ing.stock_item_id || seen.has(ing.stock_item_id)) continue;
            seen.add(ing.stock_item_id);
            if (isMissing(ing.stock_item_id)) count++;
        }
        return count;
    }

    function isCookable(recipe: Recipe): boolean {
        return missingCount(recipe) === 0;
    }

    function totalTime(recipe: Recipe): number | null {
        if (recipe.prep_time_minutes === null && recipe.cook_time_minutes === null) {
            return null;
        }
        return (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);
    }

    function missingStockItemNames(recipe: Recipe): Set<string> {
        return new Set(
            recipe.ingredients
                .filter((i) => isMissing(i.stock_item_id))
                .map((i) => i.stock_item_name),
        );
    }

    const cookableNowCount = computed(() => recipes.value.filter(isCookable).length);

    // ── Tag (cuisine + category) options ────────────────────────────
    // Recipes don't have a dedicated `tags` field — we synthesise tags
    // from the cuisine and category columns since they fill the same
    // role for filtering.
    const tagOptions = computed(() => {
        const set = new Set<string>();
        for (const r of recipes.value) {
            if (r.cuisine) set.add(r.cuisine);
            if (r.category) set.add(r.category);
        }
        return [...set].sort().map((t) => ({ label: t, value: t }));
    });

    const collectionOptionsWithNone = computed(() => [
        ...recipeCollections.value.map((c) => ({
            label: c.name,
            value: c.recipe_collection_id,
        })),
        { label: '(Uncategorised)', value: '__none__' },
    ]);

    // ── Stock item picker ───────────────────────────────────────────
    const stockItemFilterText = ref('');
    const stockItemSearchOptions = computed(() => {
        const q = stockItemFilterText.value.toLowerCase();
        return stockItems.value
            .filter((si) => !q || si.name.toLowerCase().includes(q))
            .slice(0, 30)
            .map((si) => ({ label: si.name, value: si.stock_item_id }));
    });
    function onStockItemFilter(value: string, update: (cb: () => void) => void) {
        update(() => {
            stockItemFilterText.value = value;
        });
    }

    // ── Filtering + grouping ────────────────────────────────────────
    const filteredRecipes = computed(() =>
        recipes.value.filter((r) => {
            if (favouritesOnly.value && !r.is_favourite) return false;
            // A4: explicit "empty = off" — null collection skips the predicate.
            // ('__none__' is a real value meaning "uncategorised", so keep it.)
            if (collectionFilter.value !== null) {
                if (
                    collectionFilter.value === '__none__'
                        ? r.recipe_collection_id !== null
                        : r.recipe_collection_id !== collectionFilter.value
                ) {
                    return false;
                }
            }
            if (cookableNowOnly.value && !isCookable(r)) return false;
            // A4: blank or non-numeric "Missing ≤" = off (Number.isFinite guards NaN).
            if (
                missingMax.value !== null
                && Number.isFinite(missingMax.value)
                && missingCount(r) > missingMax.value
            ) {
                return false;
            }
            if (tagFilter.value.length > 0) {
                const recipeTags = [r.cuisine, r.category].filter(
                    (t): t is string => Boolean(t),
                );
                if (!tagFilter.value.some((t) => recipeTags.includes(t))) return false;
            }
            if (usesStockItemId.value !== null) {
                if (!r.ingredients.some((i) => i.stock_item_id === usesStockItemId.value))
                    return false;
            }
            if (searchText.value) {
                const q = searchText.value.toLowerCase();
                if (!r.name.toLowerCase().includes(q)) return false;
            }
            // P2-08 — dietary tag filters. `tags` is a recipe-level
            // array; we filter client-side because all recipes are
            // already loaded into the store. The server endpoint
            // honours the same axes for the Dora tool path.
            if (dietaryTagsInclude.value.length > 0) {
                const has = new Set(r.tags ?? []);
                if (!dietaryTagsInclude.value.every((t) => has.has(t))) return false;
            }
            if (dietaryTagsExclude.value.length > 0) {
                const has = new Set(r.tags ?? []);
                if (dietaryTagsExclude.value.some((t) => has.has(t))) return false;
            }
            if (ingredientExclude.value.length > 0) {
                const terms = ingredientExclude.value
                    .map((t) => t.trim().toLowerCase())
                    .filter(Boolean);
                if (terms.length > 0) {
                    const hit = r.ingredients.some((ing) => {
                        const name = (ing.stock_item_name ?? '').toLowerCase();
                        return terms.some((term) => name.includes(term));
                    });
                    if (hit) return false;
                }
            }
            return true;
        }),
    );

    type Group = { key: string; label: string; recipes: Recipe[] };
    const groups = computed<Group[]>(() => {
        const buckets = new Map<string, Group>();
        for (const r of filteredRecipes.value) {
            const collection = recipeCollections.value.find(
                (c) => c.recipe_collection_id === r.recipe_collection_id,
            );
            const key = collection?.recipe_collection_id ?? '__none__';
            const label = collection?.name ?? 'Uncategorised';
            if (!buckets.has(key)) buckets.set(key, { key, label, recipes: [] });
            buckets.get(key)!.recipes.push(r);
        }
        return [...buckets.values()].sort((a, b) => {
            // Push "Uncategorised" to the bottom; otherwise alphabetical.
            if (a.key === '__none__') return 1;
            if (b.key === '__none__') return -1;
            return a.label.localeCompare(b.label);
        });
    });

    const hasAnyFilter = computed(
        () =>
            searchText.value !== ''
            || favouritesOnly.value
            || cookableNowOnly.value
            || missingMax.value !== null
            || collectionFilter.value !== null
            || tagFilter.value.length > 0
            || usesStockItemId.value !== null
            || dietaryTagsInclude.value.length > 0
            || dietaryTagsExclude.value.length > 0
            || ingredientExclude.value.length > 0,
    );

    // Active-filter count for the FilterBar badge (excludes the search box,
    // which lives separately in the header and has its own clear affordance).
    const activeFilterCount = computed(() => {
        let n = 0;
        if (favouritesOnly.value) n++;
        if (cookableNowOnly.value) n++;
        if (missingMax.value !== null && Number.isFinite(missingMax.value)) n++;
        if (collectionFilter.value !== null) n++;
        if (tagFilter.value.length > 0) n++;
        if (usesStockItemId.value !== null) n++;
        if (dietaryTagsInclude.value.length > 0) n++;
        if (dietaryTagsExclude.value.length > 0) n++;
        if (ingredientExclude.value.length > 0) n++;
        return n;
    });

    function clearFilters() {
        searchText.value = '';
        favouritesOnly.value = false;
        cookableNowOnly.value = false;
        missingMax.value = null;
        collectionFilter.value = null;
        tagFilter.value = [];
        usesStockItemId.value = null;
        dietaryTagsInclude.value = [];
        dietaryTagsExclude.value = [];
        ingredientExclude.value = [];
    }

    // ── Comparison mode ─────────────────────────────────────────────
    // Spec caps at 3 picks so the side-by-side view stays readable on
    // narrow screens. Picking a 4th replaces the oldest selection.
    const compareMode = ref(false);
    const selectedIds = ref<Set<string>>(new Set());
    const showComparison = ref(false);
    const MAX_COMPARE = 3;

    function toggleCompareMode() {
        compareMode.value = !compareMode.value;
        if (!compareMode.value) selectedIds.value = new Set();
    }

    function onToggleSelect(recipeId: string) {
        const next = new Set(selectedIds.value);
        if (next.has(recipeId)) {
            next.delete(recipeId);
        } else {
            if (next.size >= MAX_COMPARE) {
                // Drop the oldest selection. Sets preserve insertion order
                // so the first iteration is the earliest pick.
                const oldest = next.values().next().value;
                if (oldest) next.delete(oldest);
            }
            next.add(recipeId);
        }
        selectedIds.value = next;
    }

    const selectedRecipes = computed(() =>
        [...selectedIds.value]
            .map((id) => recipes.value.find((r) => r.recipe_id === id))
            .filter((r): r is Recipe => Boolean(r)),
    );

    // ── Recipe actions ──────────────────────────────────────────────
    const editDialogOpen = ref(false);
    const editingRecipe = ref<Recipe | null>(null);

    function onCreateClick() {
        editingRecipe.value = null;
        editDialogOpen.value = true;
    }

    function onEditClick(recipeId: string) {
        // Edit now lives on the dedicated detail/edit page (P7) — the
        // dialog stays for the "New recipe" creation flow only.
        void router.push(`/recipes/${recipeId}`);
    }

    function onOpenRecipe(recipeId: string) {
        void router.push(`/recipes/${recipeId}`);
    }

    function onCookClick(recipeId: string) {
        void router.push(`/recipes/${recipeId}/cook`);
    }

    function onToggleFavourite(recipeId: string) {
        const r = recipes.value.find((x) => x.recipe_id === recipeId);
        if (r) void recipeStore.toggleFavouriteAsync(r);
    }

    async function onDuplicate(recipeId: string) {
        const original = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!original) return;
        try {
            await recipeApi.createAsync({
                name: `${original.name} (copy)`,
                category: original.category,
                cook_time_minutes: original.cook_time_minutes,
                cuisine: original.cuisine,
                difficulty: original.difficulty,
                instructions: original.instructions,
                nutrition: original.nutrition,
                prep_time_minutes: original.prep_time_minutes,
                recipe_collection_id: original.recipe_collection_id,
                servings: original.servings,
                time_of_day: original.time_of_day,
                ingredients: original.ingredients.map((i) => ({
                    stock_item_id: i.stock_item_id,
                    quantity: i.quantity,
                    unit: i.unit,
                    notes: i.notes,
                })),
            });
            await recipeStore.getRecipesAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Duplicated "${original.name}".`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not duplicate.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function confirmDelete(recipeId: string) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        $q.dialog({
            title: 'Delete recipe',
            message: `Delete "${recipe.name}"? This cannot be undone.`,
            cancel: true,
        }).onOk(() => {
            void recipeStore.deleteRecipeAsync(recipeId);
        });
    }

    // ── Add to shopping list ────────────────────────────────────────
    const addMissingOpen = ref(false);
    const addMissingPayload = ref<{
        recipeName: string;
        stockItemIds: string[];
        // X5 — when set, the confirm path routes through /auto-generate
        // with sources.recipes=[id] so the line lands with
        // added_via=auto_recipe and the recipe name as the chip detail.
        recipeId?: string;
    } | null>(null);
    const addMissingTargetListId = ref<string | null>(null);
    const addingMissing = ref(false);

    const activeListOptions = computed(() =>
        shoppingListStore.summaries
            .filter((s) => !s.is_archived)
            .map((s) => ({
                label: s.name + (s.is_primary ? ' (primary)' : ''),
                value: s.shopping_list_id,
            })),
    );

    function openAddDialog(recipeName: string, ids: string[], recipeId?: string) {
        if (ids.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `Nothing to add for "${recipeName}".`,
            });
            return;
        }
        addMissingPayload.value = {
            recipeName,
            stockItemIds: ids,
            ...(recipeId !== undefined ? { recipeId } : {}),
        };
        addMissingTargetListId.value =
            shoppingListStore.primaryListId ?? activeListOptions.value[0]?.value ?? null;
        if (!addMissingTargetListId.value) {
            $q.dialog({
                title: 'No active shopping list',
                message: 'Create one first to add ingredients to it.',
                ok: { label: 'Open lists', noCaps: true, color: 'primary' },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists'); });
            return;
        }
        addMissingOpen.value = true;
    }

    function onAddMissing(recipeId: string, stockItemIds: string[]) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        openAddDialog(recipe?.name ?? 'recipe', stockItemIds, recipeId);
    }

    function onAddAllToList(recipeId: string) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        const ids = [
            ...new Set(
                recipe.ingredients
                    .map((i) => i.stock_item_id)
                    .filter((id): id is string => Boolean(id)),
            ),
        ];
        openAddDialog(recipe.name, ids);
    }

    async function confirmAddMissing() {
        if (!addMissingPayload.value || !addMissingTargetListId.value) return;
        addingMissing.value = true;
        try {
            const payload = addMissingPayload.value;
            // X5: when we know the recipe, delegate to /auto-generate so the
            // lines land with added_via=auto_recipe + the recipe name as the
            // chip detail. The endpoint also re-checks "well-stocked" itself
            // so the subset matches the server's view of stock.
            if (payload.recipeId) {
                const result = await shoppingListApi.autoGenerateAsync({
                    merge_into_list_id: addMissingTargetListId.value,
                    sources: { recipes: [payload.recipeId] },
                });
                if (result.nothing_to_add) {
                    $q.notify({
                        type: 'info',
                        position: 'bottom-right',
                        message: `Nothing missing for "${payload.recipeName}".`,
                    });
                } else {
                    $q.notify({
                        type: 'positive',
                        position: 'bottom-right',
                        message: `Added ${result.added_count} item${
                            result.added_count === 1 ? '' : 's'
                        } from "${payload.recipeName}".`,
                    });
                }
                await shoppingListStore.refreshAsync();
            } else {
                await addItems(
                    addMissingTargetListId.value,
                    payload.stockItemIds.map((id) => ({
                        stock_item_id: id,
                    })),
                );
            }
            addMissingOpen.value = false;
            addMissingPayload.value = null;
        } finally {
            addingMissing.value = false;
        }
    }

    // ── Add to meal plan ────────────────────────────────────────────
    // Meal plans schedule *meals*, not recipes directly — so without a
    // wrapping meal, we can only point the user at the meal-plans page.
    // We pass the recipe id along so a future enhancement on that page
    // can offer "schedule a meal that uses this recipe" inline.
    function onAddToMealPlan(recipeId: string) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        $q.dialog({
            title: 'Add to a meal plan',
            message:
                `Meal plans schedule meals (which group recipes). To plan ` +
                `"${recipe?.name ?? 'this recipe'}", open Meal Plans, pick a ` +
                `plan, and add a meal that includes this recipe.`,
            ok: { label: 'Open meal plans', color: 'primary', noCaps: true },
            cancel: { noCaps: true },
        }).onOk(() => {
            void router.push({ path: '/meal-plans', query: { recipe_id: recipeId } });
        });
    }

    async function onSaved() {
        editDialogOpen.value = false;
        await recipeStore.getRecipesAsync();
    }

    // ── Query-param deep links ──────────────────────────────────────
    // The stock item detail screen links here with `?usesStockItem=…` to
    // ask "which recipes use this item?". Hydrate that filter on mount
    // and reactively if the query changes.
    function applyQuery() {
        const id = route.query.usesStockItem;
        if (typeof id === 'string' && id) {
            usesStockItemId.value = id;
        }
        // Dashboard's "Cookable tonight → See more" link sets ?cookable=true.
        if (route.query.cookable === 'true' || route.query.cookable === '1') {
            cookableNowOnly.value = true;
        }
    }
    watch(
        () => [route.query.usesStockItem, route.query.cookable],
        applyQuery,
    );

    onMounted(async () => {
        loading.value = true;
        try {
            await Promise.all([
                recipeStore.getRecipesAsync(),
                recipeStore.getRecipeCollectionsAsync(),
                stockItemStore.getStockItemsAsync(),
                stockLevelStore.getStockLevelsAsync(),
                shoppingListStore.refreshAsync(),
                // P2-08 — load the curated dietary-tag catalogue. Cached
                // for the session; errors are non-fatal (the tag pickers
                // simply render empty).
                recipeApi.getTagCatalogueAsync()
                    .then((c) => { tagCatalogue.value = c; })
                    .catch(() => { tagCatalogue.value = null; }),
            ]);
        } finally {
            loading.value = false;
        }
        applyQuery();
    });
</script>

<style scoped>
    .full-height {
        height: 100%;
    }
</style>
