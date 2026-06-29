<template>
    <div class="q-pa-md">
        <!-- ── Header ─────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md">
            <!-- Counts moved to the sticky PageCountsFooter (A7). -->
            <q-space />
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
            <!-- C-cross Chunk 5 — inline image-display toggle. Persists
                 across sessions via /api/users/me; reused on cook mode /
                 detail surfaces as a read-only gate. -->
            <BaseButton
                variant="ghost"
                :icon="showRecipeImages ? ICONS.image : ICONS.image_not_supported"
                :aria-label="showRecipeImages ? 'Hide recipe photos' : 'Show recipe photos'"
                :class="['q-mr-sm', { 'recipes-overview__images-off': !showRecipeImages }]"
                @click="onToggleRecipeImages"
            >
                <q-tooltip>
                    {{ showRecipeImages
                        ? 'Hide recipe photos · saved across sessions'
                        : 'Show recipe photos · saved across sessions' }}
                </q-tooltip>
            </BaseButton>
            <BaseButton
                variant="ghost"
                :icon="ICONS.link"
                label="Import from URL"
                class="q-mr-sm"
                @click="onImportClick"
            />
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                label="New recipe"
                @click="onCreateClick"
            />
            <!-- Feedback 2026-06-18: filter toggle in the main toolbar so
                 the FilterBar doesn't carry its own row of chrome. -->
            <FilterToggleButton
                v-model="filtersExpanded"
                :active-count="activeFilterCount"
                @clear="clearFilters"
            />
        </div>

        <!-- C-4 Chunk 7 — Import-from-URL on the overview's New-Recipe
             surface. FU-102: dialog chrome extracted to a shared component;
             this page wires the imported DTO to `createAsync` + nav. -->
        <RecipeImportDialog
            v-model="importOpen"
            @imported="onRecipeImported"
        />

        <!-- ── Filter bar ─ standardised via FilterBar (A4) ───────── -->
        <FilterBar
            v-model="filtersExpanded"
            :toolbar="false"
            :active-count="activeFilterCount"
            @clear="clearFilters"
        >
            <template #filters>
            <div class="row q-gutter-sm items-center">
            <FilterChip v-model="favouritesOnly" :icon="ICONS.favorite" active-color="negative">
                Favourites
            </FilterChip>
            <FilterChip v-model="cookableNowOnly" :icon="ICONS.check_circle" active-color="positive">
                Cookable now
            </FilterChip>
            <FilterChip v-model="inStockOnly" :icon="ICONS.inventory_2" active-color="primary">
                Have meals in pool
            </FilterChip>
            <!-- FU-081 — tri-state: click 1 = Planned only, click 2 = Not
                 planned only, click 3 = off. Single chip cycles through; the
                 active filter count + Clear filters cover both modes. -->
            <TriStateFilterChip
                v-model="plannedFilterState"
                include-label="Planned"
                exclude-label="Not planned"
                :include-icon="ICONS.calendar_month"
                :exclude-icon="ICONS.calendar_month"
                include-color="info"
                exclude-color="warning"
            />
            <!-- C-waste W4 — surfaces recipes that use at least one
                 in-stock ingredient expiring within 14 days. While on,
                 the list is force-sorted by count desc and each card
                 shows a "Uses N expiring" badge. -->
            <FilterChip v-model="expiringOnly" :icon="ICONS.wasteExpired" active-color="warning">
                Uses expiring ingredients
            </FilterChip>

            <q-separator vertical class="q-mx-sm" />

            <!-- FU-083 — :hint removed; the under-input copy was just
                 padding out the filter row's height and offsetting
                 alignment without adding info. -->
            <q-input
                v-model.number="mealCountMin"
                dense
                outlined
                type="number"
                min="0"
                style="max-width: 140px"
                label="Meals ≥"
                hide-bottom-space
            />
            <q-input
                v-model.number="missingMax"
                dense
                outlined
                type="number"
                min="0"
                style="max-width: 130px"
                label="Missing ingredients ≤"
                hide-bottom-space
            />
            <!-- C-4 Chunk 9 — kcal upper-bound filter (gated). -->
            <q-input
                v-if="nutritionEnabled"
                v-model.number="kcalMax"
                dense
                outlined
                type="number"
                min="0"
                style="max-width: 130px"
                label="Kcal ≤"
                hide-bottom-space
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
            <!-- L235 — cuisine + category are distinct single-select filters,
                 no longer lumped together as one "tags" multi-select. -->
            <q-select
                dense
                outlined
                style="min-width: 170px"
                emit-value
                map-options
                clearable
                v-model="cuisineFilter"
                :options="cuisineOptions"
                label="Cuisine"
            />
            <q-select
                dense
                outlined
                style="min-width: 170px"
                emit-value
                map-options
                clearable
                v-model="categoryFilter"
                :options="categoryOptions"
                label="Category"
            />
            <!-- FU-148 — time-of-day single-select. §1.12: vocabulary
                 sourced from DEFAULT_MEAL_SLOTS (shared with meal-plans
                 PROPOSAL_MEAL_PLANS.md §4). -->
            <q-select
                dense
                outlined
                style="min-width: 170px"
                emit-value
                map-options
                clearable
                v-model="timeOfDayFilter"
                :options="TIME_OF_DAY_OPTIONS"
                label="Time of day"
            />
            <!-- §1.7 — difficulty single-select. Closed vocabulary
                 (Easy / Medium / Hard). -->
            <q-select
                dense
                outlined
                style="min-width: 160px"
                emit-value
                map-options
                clearable
                v-model="difficultyFilter"
                :options="DIFFICULTY_OPTIONS"
                label="Difficulty"
            />
            <!-- FU-149 — "# ingredients ≤" numeric cap. Pairs with the
                 new sort axis below. -->
            <q-input
                v-model.number="ingredientsMax"
                dense
                outlined
                type="number"
                min="0"
                style="max-width: 140px"
                label="# ingredients ≤"
                hide-bottom-space
            />
            <!-- FU-083 follow-up — Uses / Doesn't use ingredients consolidated
                 into the shared TriStateFilter, with `searchable` for the
                 large stock-item set and a per-row stock-level colour dot.
                 Single button (+/-) replaces the two paired q-selects. -->
            <TriStateFilter
                label="Ingredients"
                searchable
                search-placeholder="Search ingredients…"
                :options="ingredientFilterOptions"
                :sort-options="ingredientSortOptions"
                default-sort="name"
                v-model:include="usesStockItemIds"
                v-model:exclude="excludesStockItemIds"
            />
            <!-- L237 — one tri-state dietary filter (must-have / must-not /
                 neutral) replacing the old two include/exclude selects. -->
            <DietaryTagFilter
                :options="dietaryTagOptions"
                v-model:include="dietaryTagsInclude"
                v-model:exclude="dietaryTagsExclude"
            />
            <!-- L310 — tools inclusion/exclusion filter (same tri-state control). -->
            <DietaryTagFilter
                label="Tools"
                :options="toolFilterOptions"
                v-model:include="toolsInclude"
                v-model:exclude="toolsExclude"
            />
            <!-- FU-083 — old "Free from ingredient(s)" free-text input
                 removed; its concern is now covered by the "Doesn't use"
                 stock-item picker above (paired with "Uses ingredients" as a
                 +/- filter on the same option source). Untracked-name
                 exclusion can be added back behind a more discoverable
                 control if real usage demands it; the text-match was a
                 source of false negatives. -->


            <q-separator vertical class="q-mx-sm" />

            <q-select
                v-model="sortBy"
                :options="SORT_OPTIONS"
                emit-value
                map-options
                outlined
                dense
                label="Sort by"
                style="min-width: 180px"
            />
            <!-- FU-083 — direction toggle. Icon flips between
                 arrow-up (asc) and arrow-down (desc). Tooltip explains
                 the current axis's meaning in the chosen direction. -->
            <BaseButton
                variant="ghost"
                :icon="sortDir === 'asc' ? ICONS.arrow_upward : ICONS.arrow_downward"
                :aria-label="`Sort ${sortDir === 'asc' ? 'ascending' : 'descending'}`"
                @click="toggleSortDir"
            >
                <q-tooltip>{{ sortDirTooltip }}</q-tooltip>
            </BaseButton>
            </div>
            </template>
        </FilterBar>
        <!-- P2-08 — disclaimer surfaced when any dietary filter is on.
             Pulled from the backend so the wording stays consistent
             between the SPA and Dora. -->
        <div
            v-if="(dietaryTagsInclude.length > 0 || dietaryTagsExclude.length > 0) && tagCatalogue?.disclaimer"
            class="text-caption dora-text-muted q-mb-md"
        >
            <q-icon name="info" size="14px" class="q-mr-xs" />
            {{ tagCatalogue.disclaimer }}
        </div>

        <!-- ── Grid grouped by collection ─────────────────────────── -->
        <FadeTransition mode="out-in">
        <div v-if="loading && recipes.length === 0" key="rec-loading" class="text-center q-py-xl">
            <AppSpinner size="48px" />
        </div>
        <div v-else key="rec-content">
            <div
                v-if="filteredRecipes.length === 0"
                class="text-center dora-text-muted q-py-xl"
            >
                <q-icon :name="ICONS.menu_book" size="60px" class="q-mb-sm" />
                <div>No recipes match the current filters.</div>
                <BaseButton
                    v-if="hasAnyFilter"
                    variant="ghost"
                    label="Clear filters"
                    class="q-mt-sm"
                    @click="clearFilters"
                />
            </div>

            <!-- Collection groups as rounded, collapsible surface boxes. -->
            <div
                v-for="group in groups"
                :key="group.key"
                class="recipe-group dora-bg-sunken q-mb-lg"
            >
                <div
                    class="recipe-group__header row items-center cursor-pointer"
                    @click="toggleGroup(group.key)"
                >
                    <q-icon
                        :name="isCollapsed(group.key) ? ICONS.chevron_right : ICONS.expand_more"
                        size="22px"
                        class="q-mr-xs"
                    />
                    <q-icon :name="ICONS.folder" size="18px" class="q-mr-xs" />
                    <div class="text-subtitle1 text-weight-medium">{{ group.label }}</div>
                    <q-chip dense outline size="sm" class="q-ml-sm">
                        {{ group.recipes.length }}
                    </q-chip>
                </div>
                <q-slide-transition>
                    <div v-show="!isCollapsed(group.key)" class="row q-col-gutter-md q-pa-md q-pt-none">
                        <div
                            v-for="recipe in group.recipes"
                            :key="recipe.recipe_id"
                            class="col-12 col-sm-6 col-md-4 col-lg-3"
                        >
                            <RecipeCard
                                :recipe="recipeWithExpiringCount(recipe)"
                                :show-expiring-badge="expiringOnly"
                                @open="onOpenRecipe"
                                @cook="onCookClick"
                                @toggle-favourite="onToggleFavourite"
                                @add-missing="onAddMissing"
                                @add-all-to-list="onAddAllToList"
                            />
                        </div>
                    </div>
                </q-slide-transition>
            </div>
        </div>
        </FadeTransition>

        <PageCountsFooter v-if="recipes.length > 0" :counts="footerCounts" />

        <!-- ── Edit dialog ────────────────────────────────────────── -->
        <RecipeEditDialog
            v-model="editDialogOpen"
            :recipe="editingRecipe"
            @saved="onSaved"
        />

        <!-- ── Per-ingredient picker (Chunk B §1.4) ─────────────── -->
        <RecipeIngredientPickerDialog
            ref="pickerRef"
            v-model="pickerOpen"
            :recipe="pickerRecipe"
            :initial-checked-ids="pickerInitialCheckedIds"
            @confirm="onPickerConfirm"
        />

    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import FilterToggleButton from 'src/components/FilterToggleButton.vue';
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import TriStateFilterChip, { type TriState } from 'src/components/chips/TriStateFilterChip.vue';
    import PageCountsFooter from 'src/components/PageCountsFooter.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import RecipeEditDialog from 'components/RecipeEditDialog.vue';
    import RecipeIngredientPickerDialog from 'src/components/recipes/RecipeIngredientPickerDialog.vue';
    import DietaryTagFilter from 'src/components/recipes/DietaryTagFilter.vue';
    import TriStateFilter from 'src/components/filters/TriStateFilter.vue';
    import type {
        TriStateOption,
        TriStateSort,
    } from 'src/components/filters/triStateFilterTypes';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
    import RecipeApiService, { type ImportedRecipe } from 'src/services/api/recipeApiService';
    import RecipeImportDialog from 'src/components/recipes/RecipeImportDialog.vue';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import {
        DEFAULT_MEAL_SLOTS,
        DIFFICULTY_RANK,
        DIFFICULTY_VALUES,
        type Difficulty,
    } from 'src/helpers/recipeVocabulary';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useNutritionMode } from 'src/composables/useNutritionMode';

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const shoppingListStore = useShoppingListStore();
    // FU-081 — meal-plan store dependency dropped: `is_planned` is
    // server-derived now, and the page never read the cache otherwise.
    // Saves one round-trip on cookbook overview load.
    const recipeVocabStore = useRecipeVocabStore();
    const mealSlotStore = useMealSlotStore();
    const recipeApi = new RecipeApiService();
    const { addItems } = useShoppingListActions();

    const { recipes, recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);
    // C-cross Chunk 5 — image-display opt-in for recipe surfaces.
    const { showRecipeImages, setRecipeImages } = useImagePrefs();
    // C-4 Chunk 9 — nutrition flag gates the kcal axis + filter.
    const { nutritionEnabled } = useNutritionMode();
    const SORT_OPTIONS = computed<{ label: string; value: SortKey }[]>(() =>
        nutritionEnabled.value
            ? [...STATIC_SORT_OPTIONS, { label: 'Kcal', value: 'kcal' as SortKey }]
            : STATIC_SORT_OPTIONS,
    );

    async function onToggleRecipeImages() {
        const previous = showRecipeImages.value;
        try {
            await setRecipeImages(!previous);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                timeout: 2000,
                message: previous ? 'Recipe photos hidden.' : 'Recipe photos shown.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save preference.',
                caption: toastCaption(err),
            });
        }
    }

    const loading = ref(false);

    // ── Filter state ────────────────────────────────────────────────
    const filtersExpanded = ref(false);
    const searchText = ref('');
    const favouritesOnly = ref(false);
    const cookableNowOnly = ref(false);
    const inStockOnly = ref(false);
    // FU-081 — tri-state: 'off' = no constraint; 'include' = only planned
    // recipes (any future un-consumed MealPlanEntry); 'exclude' = only
    // un-planned recipes. Cycles via TriStateFilterChip.
    const plannedFilterState = ref<TriState>('off');
    // C-waste W4 — when on, restricts the list to recipes using ≥1
    // expiring-within-14-days in-stock ingredient AND force-sorts by
    // count desc. The id→count map below is populated by a separate
    // server fetch keyed off this ref's true edge.
    const expiringOnly = ref(false);
    const EXPIRING_FILTER_HORIZON_DAYS = 14;
    const expiringCountByRecipeId = ref<Map<string, number>>(new Map());
    const expiringFetchInFlight = ref(false);
    // `null` means "no upper bound" — the input clears to null on backspace.
    // Cleared inputs land as NaN via v-model.number; predicates and the
    // hint string both guard on Number.isFinite so "blank == no filter".
    const missingMax = ref<number | null>(null);
    const mealCountMin = ref<number | null>(null);
    // C-4 Chunk 9 — "Kcal ≤" filter (only renders when the nutrition
    // opt-in is on). Recipes with no kcal value pass through; we don't
    // hide them as "unknown" because that punishes recipes the user
    // hasn't annotated yet.
    const kcalMax = ref<number | null>(null);
    const collectionFilter = ref<string | null>(null);
    // L235 — cuisine + category are distinct single-select id filters.
    const cuisineFilter = ref<string | null>(null);
    const categoryFilter = ref<string | null>(null);
    // FU-148 — time-of-day single-select. §1.12: vocabulary is the
    // server's DEFAULT_MEAL_SLOTS. Null = no filter.
    const timeOfDayFilter = ref<string | null>(null);
    // §1.7 — difficulty single-select. Null = no filter.
    const difficultyFilter = ref<Difficulty | null>(null);
    // FU-149 — "# ingredients ≤" cap. Same blank-input / NaN guard as
    // the other numeric inputs.
    const ingredientsMax = ref<number | null>(null);
    // Set via the "Uses ingredients" picker OR via `?usesStockItem=` query
    // (deep-linked from the stock item detail screen — single id pre-fills
    // a one-element array).
    const usesStockItemIds = ref<string[]>([]);
    // FU-083 — "Doesn't use" pair to "Uses ingredients". Both pick from
    // stock items; combine with AND (must use all of include, must not
    // use any of exclude). Replaces the old free-text "Free from
    // ingredient(s)" path.
    const excludesStockItemIds = ref<string[]>([]);

    type SortKey =
        | 'name'
        | 'last_made'
        | 'created_at'
        | 'meal_count'
        | 'total_time'
        | 'kcal'
        | 'ingredient_count'
        | 'difficulty';
    type SortDir = 'asc' | 'desc';
    // C-4 Chunk 9 — "Kcal" axis added when the nutrition opt-in is on.
    // The sort menu options are computed below; the static list keeps
    // the always-on axes.
    // C-2.A — time-of-day reads the household meal-slot vocabulary
    // (MealSlot table), falling back to the seed constant only before the
    // store's first load.
    const TIME_OF_DAY_OPTIONS = computed(() =>
        mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );
    // §1.7 — difficulty closed vocabulary; mirrors ALLOWED_DIFFICULTY_VALUES
    // on the server.
    const DIFFICULTY_OPTIONS = [...DIFFICULTY_VALUES];

    const STATIC_SORT_OPTIONS: { label: string; value: SortKey }[] = [
        { label: 'Name', value: 'name' },
        { label: 'Recently made', value: 'last_made' },
        // FU-082 — Recently added is the fifth IMPL_PLAN_COOKBOOK Chunk 1
        // axis; landed once Recipe.created_at became available on the DTO.
        { label: 'Recently added', value: 'created_at' },
        { label: 'Meals in pool', value: 'meal_count' },
        { label: 'Prep + cook time', value: 'total_time' },
        // FU-149 — sort by ingredient count (fewer ingredients first
        // is the common "make this quick" intent; the asc/desc toggle
        // covers the other direction).
        { label: '# ingredients', value: 'ingredient_count' },
        // §1.7 — difficulty ordinal (Easy < Medium < Hard; nulls sink).
        { label: 'Difficulty', value: 'difficulty' },
    ];
    const sortBy = ref<SortKey>('name');
    // FU-083 — explicit asc/desc toggle. Default per axis: name = asc,
    // everything else = desc (the most-recent / largest / fastest hits
    // first feel right for those).
    const sortDir = ref<SortDir>('asc');

    // Dietary filter state — the tri-state control owns include/exclude id
    // arrays. They combine with AND (must have all of include, none of
    // exclude).
    const dietaryTagsInclude = ref<string[]>([]);
    const dietaryTagsExclude = ref<string[]>([]);
    const toolsInclude = ref<string[]>([]);
    const toolsExclude = ref<string[]>([]);
    // Disclaimer text still comes from the recipe tag catalogue endpoint.
    const tagCatalogue = ref<RecipeTagCatalogue | null>(null);

    // ── Vocabulary options (cuisine / category / dietary) ───────────────
    const cuisineOptions = computed(() =>
        cuisines.value.map((c) => ({ label: c.name, value: c.cuisine_id })),
    );
    const categoryOptions = computed(() =>
        categories.value.map((c) => ({ label: c.name, value: c.category_id })),
    );
    const dietaryTagOptions = computed(() =>
        dietaryTags.value.map((t) => ({
            label: t.name,
            value: t.dietary_tag_id,
            category: t.category,
        })),
    );
    const toolFilterOptions = computed(() =>
        tools.value.map((t) => ({ label: t.name, value: t.tool_id, category: 'Tools' })),
    );

    // Cookability is server-owned (§3.2): recipes carry `cookable` /
    // `missing_count` and each ingredient carries `is_missing`. The client
    // reads those fields rather than re-deriving from stock data.

    function totalTime(recipe: Recipe): number | null {
        if (recipe.prep_time_minutes === null && recipe.cook_time_minutes === null) {
            return null;
        }
        return (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);
    }


    // FU-081 — `is_planned` is now server-owned (RecipeDto field,
    // derived from MealPlanEntry rows in the same query that fills
    // `committed_meals`). The client predicate reads it directly; the
    // old client-side walk of `mealPlanStore.mealPlans[].entries[]`
    // with timezone-juggling on `scheduled_for` is retired.

    // FU-083 — hint computeds removed (the input labels carry the meaning;
    // the hint-under-input text was just inflating the filter row).

    // A7 — sticky footer counts over the FILTERED view.
    const footerCounts = computed(() => [
        { label: 'Shown', value: filteredRecipes.value.length },
        {
            label: 'Cookable now',
            value: filteredRecipes.value.filter((r) => r.cookable).length,
            tone: 'positive' as const,
        },
        {
            label: 'Favourites',
            value: filteredRecipes.value.filter((r) => r.is_favourite).length,
            tone: 'info' as const,
        },
    ]);

    // ── Tag (cuisine + category) options ────────────────────────────
    // Recipes don't have a dedicated `tags` field — we synthesise tags
    // from the cuisine and category columns since they fill the same
    // role for filtering.
    const collectionOptionsWithNone = computed(() => [
        ...recipeCollections.value.map((c) => ({
            label: c.name,
            value: c.recipe_collection_id,
        })),
        { label: '(Uncategorised)', value: '__none__' },
    ]);

    // ── Ingredient (stock-item) filter options ──────────────────────
    // FU-083 follow-up — used by the shared TriStateFilter (the +/-
    // partner replaces the old two paired q-selects). The component
    // owns the search input AND the sort selector (name / stock level)
    // — we hand it the full options list with a `dotColour` per row
    // and embed the stock-level sequence in `meta` so the level-sort
    // compare can read it without re-querying the store.
    const ingredientFilterOptions = computed<TriStateOption[]>(() =>
        stockItems.value.map((si) => ({
            value: si.stock_item_id,
            label: si.name,
            // FU-050 — sequence-keyed (R-003). `si.stock_level_sequence`
            // is null on untracked items → null dotColour, which the
            // TriStateFilter renders as a muted dot.
            dotColour: colourForSequence(si.stock_level_sequence ?? null),
            meta: { levelSequence: si.stock_level_sequence ?? null },
        })),
    );

    // Sort axes for the ingredient filter. Name is the default
    // (alphabetical is more browsable than level when scanning); the
    // user can flip to "Stock level" to surface low/out items first
    // when planning around what needs using up. Level sort: low/out
    // (higher sequence number per `stock_status.py`) first.
    const ingredientSortOptions: TriStateSort[] = [
        {
            value: 'name',
            label: 'Name',
            compare: (a, b) => a.label.localeCompare(b.label),
        },
        {
            value: 'level',
            label: 'Stock level',
            compare: (a, b) => {
                const aSeq = (a.meta?.levelSequence as number | null | undefined) ?? -1;
                const bSeq = (b.meta?.levelSequence as number | null | undefined) ?? -1;
                if (aSeq === bSeq) return a.label.localeCompare(b.label);
                return bSeq - aSeq;
            },
        },
    ];

    // ── Filtering + sorting + grouping ──────────────────────────────
    // Blank inputs collapse to `null`/NaN; every numeric predicate guards
    // on Number.isFinite so a half-typed/just-cleared field reverts to
    // "no filter" rather than wiping the list (L234).
    const filteredRecipes = computed(() =>
        recipes.value.filter((r) => {
            if (favouritesOnly.value && !r.is_favourite) return false;
            if (cookableNowOnly.value && !r.cookable) return false;
            if (inStockOnly.value && r.available_meals <= 0) return false;
            // FU-081 — tri-state: include keeps only planned; exclude keeps
            // only un-planned; off is no constraint.
            if (plannedFilterState.value === 'include' && !r.is_planned) return false;
            if (plannedFilterState.value === 'exclude' && r.is_planned) return false;

            // C-waste W4 — narrow to recipes the server flagged as
            // using ≥1 expiring-within-horizon ingredient. The map is
            // populated by a separate API call on the filter's true
            // edge; while it's loading we don't narrow (the user sees
            // the unrestricted list rather than an empty flash).
            if (
                expiringOnly.value
                && expiringCountByRecipeId.value.size > 0
                && !expiringCountByRecipeId.value.has(r.recipe_id)
            ) {
                return false;
            }

            if (
                mealCountMin.value !== null
                && Number.isFinite(mealCountMin.value)
                && r.available_meals < mealCountMin.value
            ) {
                return false;
            }
            if (
                missingMax.value !== null
                && Number.isFinite(missingMax.value)
                && r.missing_count > missingMax.value
            ) {
                return false;
            }
            // C-4 Chunk 9 — "Kcal ≤" filter. Only active when nutrition
            // is enabled. Recipes without a kcal value pass through (we
            // don't penalise unannotated recipes).
            if (
                nutritionEnabled.value
                && kcalMax.value !== null
                && Number.isFinite(kcalMax.value)
                && r.kcal !== null
                && r.kcal > kcalMax.value
            ) {
                return false;
            }

            // '__none__' is a real value meaning "uncategorised".
            if (collectionFilter.value !== null) {
                if (
                    collectionFilter.value === '__none__'
                        ? r.recipe_collection_id !== null
                        : r.recipe_collection_id !== collectionFilter.value
                ) {
                    return false;
                }
            }
            // L235 — cuisine + category are independent single-select id filters.
            if (cuisineFilter.value !== null && r.cuisine_id !== cuisineFilter.value) {
                return false;
            }
            if (categoryFilter.value !== null && r.category_id !== categoryFilter.value) {
                return false;
            }
            // FU-148 — time-of-day single-select. Null = no filter; a
            // recipe with null time_of_day fails any non-null filter
            // (matches the user intent of "show me breakfast recipes",
            // not "show me everything tagged breakfast OR unset").
            if (timeOfDayFilter.value !== null && r.time_of_day !== timeOfDayFilter.value) {
                return false;
            }
            // §1.7 — difficulty single-select. Null = no filter; a recipe
            // with null difficulty fails any non-null filter (same
            // intent rule as time_of_day above).
            if (difficultyFilter.value !== null && r.difficulty !== difficultyFilter.value) {
                return false;
            }
            // FU-149 — "# ingredients ≤" cap. Blank/NaN reverts to no
            // filter (matches L234 blank-input rule).
            if (
                ingredientsMax.value !== null
                && Number.isFinite(ingredientsMax.value)
                && r.ingredients.length > ingredientsMax.value
            ) {
                return false;
            }
            if (usesStockItemIds.value.length > 0) {
                const wanted = new Set(usesStockItemIds.value);
                if (!r.ingredients.some((i) => wanted.has(i.stock_item_id))) return false;
            }
            if (searchText.value) {
                const q = searchText.value.toLowerCase();
                if (!r.name.toLowerCase().includes(q)) return false;
            }
            // Tri-state dietary filter — must have all of include, none of exclude.
            if (dietaryTagsInclude.value.length > 0) {
                const has = new Set(r.dietary_tag_ids ?? []);
                if (!dietaryTagsInclude.value.every((t) => has.has(t))) return false;
            }
            if (dietaryTagsExclude.value.length > 0) {
                const has = new Set(r.dietary_tag_ids ?? []);
                if (dietaryTagsExclude.value.some((t) => has.has(t))) return false;
            }
            if (toolsInclude.value.length > 0) {
                const has = new Set(r.tool_ids ?? []);
                if (!toolsInclude.value.every((t) => has.has(t))) return false;
            }
            if (toolsExclude.value.length > 0) {
                const has = new Set(r.tool_ids ?? []);
                if (toolsExclude.value.some((t) => has.has(t))) return false;
            }
            // FU-083 — "Doesn't use" stock-item picker (the +/- partner to
            // "Uses ingredients"). Recipe is excluded if any picked id is in
            // its ingredient set. Replaces the old free-text path.
            if (excludesStockItemIds.value.length > 0) {
                const ingIds = new Set(r.ingredients.map((i) => i.stock_item_id));
                if (excludesStockItemIds.value.some((id) => ingIds.has(id))) return false;
            }
            return true;
        }),
    );

    // FU-083 — explicit asc/desc direction. Null sentinels (last_made,
    // total_time) always sink to the bottom regardless of direction —
    // the user doesn't want a wall of "—" at the top when toggling to
    // newest-first. Name is the universal tiebreaker.
    const sortedRecipes = computed<Recipe[]>(() => {
        const arr = [...filteredRecipes.value];
        // C-waste W4 — while the expiring filter is on, override the
        // user's sort with "most-expiring-ingredients first" so the
        // top of the list is the highest-impact rescue. The user's
        // sort axis + direction are preserved in state for when they
        // toggle the filter off.
        if (expiringOnly.value) {
            const counts = expiringCountByRecipeId.value;
            return arr.sort((a, b) => {
                const av = counts.get(a.recipe_id) ?? 0;
                const bv = counts.get(b.recipe_id) ?? 0;
                if (av !== bv) return bv - av;
                return a.name.localeCompare(b.name);
            });
        }
        const dirSign = sortDir.value === 'desc' ? -1 : 1;
        const cmp = (a: Recipe, b: Recipe): number => {
            switch (sortBy.value) {
                case 'last_made': {
                    const av = a.last_made_on;
                    const bv = b.last_made_on;
                    if (av === null && bv === null) return a.name.localeCompare(b.name);
                    if (av === null) return 1;
                    if (bv === null) return -1;
                    return av.localeCompare(bv) * dirSign;
                }
                case 'created_at': {
                    // FU-082 — never null on rows from the API (DTO field
                    // is always populated post-backfill); ISO-8601 strings
                    // sort lexicographically. Tie-break alphabetical.
                    const c = a.created_at.localeCompare(b.created_at);
                    return c !== 0 ? c * dirSign : a.name.localeCompare(b.name);
                }
                case 'meal_count': {
                    const d = (a.available_meals - b.available_meals) * dirSign;
                    return d !== 0 ? d : a.name.localeCompare(b.name);
                }
                case 'total_time': {
                    const av = totalTime(a);
                    const bv = totalTime(b);
                    if (av === null && bv === null) return a.name.localeCompare(b.name);
                    if (av === null) return 1;
                    if (bv === null) return -1;
                    if (av === bv) return a.name.localeCompare(b.name);
                    return (av - bv) * dirSign;
                }
                case 'kcal': {
                    const av = a.kcal;
                    const bv = b.kcal;
                    if (av === null && bv === null) return a.name.localeCompare(b.name);
                    if (av === null) return 1;
                    if (bv === null) return -1;
                    if (av === bv) return a.name.localeCompare(b.name);
                    return (av - bv) * dirSign;
                }
                case 'ingredient_count': {
                    // FU-149 — neither side is null (ingredients[] is
                    // always at least []), so no sentinel-sink handling.
                    const av = a.ingredients.length;
                    const bv = b.ingredients.length;
                    if (av === bv) return a.name.localeCompare(b.name);
                    return (av - bv) * dirSign;
                }
                case 'difficulty': {
                    // §1.7 — ordinal rank (Easy < Medium < Hard); recipes
                    // with no value sink regardless of direction.
                    const av = a.difficulty as Difficulty | null;
                    const bv = b.difficulty as Difficulty | null;
                    const ar = av && av in DIFFICULTY_RANK ? DIFFICULTY_RANK[av] : null;
                    const br = bv && bv in DIFFICULTY_RANK ? DIFFICULTY_RANK[bv] : null;
                    if (ar === null && br === null) return a.name.localeCompare(b.name);
                    if (ar === null) return 1;
                    if (br === null) return -1;
                    if (ar === br) return a.name.localeCompare(b.name);
                    return (ar - br) * dirSign;
                }
                case 'name':
                default:
                    return a.name.localeCompare(b.name) * dirSign;
            }
        };
        return arr.sort(cmp);
    });

    type Group = { key: string; label: string; recipes: Recipe[] };
    const groups = computed<Group[]>(() => {
        const buckets = new Map<string, Group>();
        for (const r of sortedRecipes.value) {
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

    // Collapsible collection groups — track the collapsed set (default all
    // expanded). Keyed by collection id / '__none__'.
    const collapsedGroups = ref<Set<string>>(new Set());
    const isCollapsed = (key: string) => collapsedGroups.value.has(key);
    function toggleGroup(key: string) {
        const next = new Set(collapsedGroups.value);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        collapsedGroups.value = next;
    }

    const hasAnyFilter = computed(
        () =>
            searchText.value !== ''
            || favouritesOnly.value
            || cookableNowOnly.value
            || inStockOnly.value
            || plannedFilterState.value !== 'off'
            || expiringOnly.value
            || (mealCountMin.value !== null && Number.isFinite(mealCountMin.value))
            || (missingMax.value !== null && Number.isFinite(missingMax.value))
            || (kcalMax.value !== null && Number.isFinite(kcalMax.value))
            || collectionFilter.value !== null
            || cuisineFilter.value !== null
            || categoryFilter.value !== null
            || timeOfDayFilter.value !== null
            || difficultyFilter.value !== null
            || (ingredientsMax.value !== null && Number.isFinite(ingredientsMax.value))
            || usesStockItemIds.value.length > 0
            || excludesStockItemIds.value.length > 0
            || dietaryTagsInclude.value.length > 0
            || dietaryTagsExclude.value.length > 0
            || toolsInclude.value.length > 0
            || toolsExclude.value.length > 0,
    );

    // Active-filter count for the FilterBar badge (excludes the search box,
    // which lives separately in the header and has its own clear affordance,
    // and excludes the sort axis, which is a presentation choice).
    const activeFilterCount = computed(() => {
        let n = 0;
        if (favouritesOnly.value) n++;
        if (cookableNowOnly.value) n++;
        if (inStockOnly.value) n++;
        if (plannedFilterState.value !== 'off') n++;
        if (expiringOnly.value) n++;
        if (mealCountMin.value !== null && Number.isFinite(mealCountMin.value)) n++;
        if (missingMax.value !== null && Number.isFinite(missingMax.value)) n++;
        if (kcalMax.value !== null && Number.isFinite(kcalMax.value)) n++;
        if (collectionFilter.value !== null) n++;
        if (cuisineFilter.value !== null) n++;
        if (categoryFilter.value !== null) n++;
        if (timeOfDayFilter.value !== null) n++;
        if (difficultyFilter.value !== null) n++;
        if (ingredientsMax.value !== null && Number.isFinite(ingredientsMax.value)) n++;
        if (usesStockItemIds.value.length > 0) n++;
        if (excludesStockItemIds.value.length > 0) n++;
        if (dietaryTagsInclude.value.length > 0) n++;
        if (dietaryTagsExclude.value.length > 0) n++;
        if (toolsInclude.value.length > 0) n++;
        if (toolsExclude.value.length > 0) n++;
        return n;
    });

    function toggleSortDir() {
        sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
    }

    // Phrasing per axis so the tooltip explains the *meaning* of the
    // current direction, not just "ascending" vs "descending".
    const sortDirTooltip = computed(() => {
        const asc = sortDir.value === 'asc';
        switch (sortBy.value) {
            case 'last_made':
                return asc ? 'Oldest first' : 'Most recent first';
            case 'created_at':
                return asc ? 'Oldest first' : 'Most recent first';
            case 'meal_count':
                return asc ? 'Fewest meals first' : 'Most meals first';
            case 'total_time':
                return asc ? 'Fastest first' : 'Slowest first';
            case 'kcal':
                return asc ? 'Lowest kcal first' : 'Highest kcal first';
            case 'ingredient_count':
                return asc ? 'Fewest ingredients first' : 'Most ingredients first';
            case 'difficulty':
                return asc ? 'Easiest first' : 'Hardest first';
            case 'name':
            default:
                return asc ? 'A → Z' : 'Z → A';
        }
    });

    // FU-083 — when the user picks a new sort axis, snap to its
    // conventional direction so the first thing they see makes sense
    // (recently-made → newest first; name → A→Z; etc). They can still
    // flip with the direction button.
    watch(sortBy, (next) => {
        // Name + ingredient_count default to ascending — "A→Z" / "fewest
        // first" are the natural reads. Everything else (recently made,
        // most meals, fastest, lowest kcal) defaults to descending.
        sortDir.value =
            next === 'name'
            || next === 'ingredient_count'
            || next === 'difficulty'
                ? 'asc'
                : 'desc';
    });

    // C-4 Chunk 9 — if the user had Kcal as their sort axis and then the
    // nutrition opt-in flips off (admin disable, or user picks Off in
    // Settings), snap back to Name so the picker doesn't show an
    // orphaned value.
    watch(nutritionEnabled, (on) => {
        if (!on && sortBy.value === 'kcal') sortBy.value = 'name';
    });

    // C-waste W4 — merge the server-fetched expiring count back onto
    // recipes from the store before passing them to the card. The
    // store's copies don't carry the count (the default fetch doesn't
    // ask for it); the filter-on fetch does. Identity-stable in the
    // off case so Vue's reactivity skips unnecessary card re-renders.
    function recipeWithExpiringCount(recipe: Recipe): Recipe {
        if (!expiringOnly.value) return recipe;
        const count = expiringCountByRecipeId.value.get(recipe.recipe_id) ?? 0;
        if (count === (recipe.expiring_ingredient_count ?? 0)) return recipe;
        return { ...recipe, expiring_ingredient_count: count };
    }

    // Fetch the expiring set whenever the filter is flipped on; clear
    // it when flipped off so a stale map doesn't leak into a future
    // session. R-003 — the predicate (which items expire within N days,
    // which recipes use them) lives entirely on the server.
    watch(expiringOnly, async (on) => {
        if (!on) {
            expiringCountByRecipeId.value = new Map();
            return;
        }
        expiringFetchInFlight.value = true;
        try {
            const page = await recipeApi.getAllAsync({
                expiring_within_days: EXPIRING_FILTER_HORIZON_DAYS,
            });
            const next = new Map<string, number>();
            for (const r of page.items) {
                next.set(r.recipe_id, r.expiring_ingredient_count ?? 0);
            }
            expiringCountByRecipeId.value = next;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load expiring-ingredient recipes.',
                caption: toastCaption(err),
            });
            expiringOnly.value = false;
        } finally {
            expiringFetchInFlight.value = false;
        }
    });

    function clearFilters() {
        searchText.value = '';
        favouritesOnly.value = false;
        cookableNowOnly.value = false;
        inStockOnly.value = false;
        plannedFilterState.value = 'off';
        expiringOnly.value = false;
        mealCountMin.value = null;
        missingMax.value = null;
        kcalMax.value = null;
        collectionFilter.value = null;
        cuisineFilter.value = null;
        categoryFilter.value = null;
        timeOfDayFilter.value = null;
        difficultyFilter.value = null;
        ingredientsMax.value = null;
        usesStockItemIds.value = [];
        excludesStockItemIds.value = [];
        dietaryTagsInclude.value = [];
        dietaryTagsExclude.value = [];
        toolsInclude.value = [];
        toolsExclude.value = [];
    }

    // ── Recipe actions ──────────────────────────────────────────────
    const editDialogOpen = ref(false);
    const editingRecipe = ref<Recipe | null>(null);

    function onCreateClick() {
        editingRecipe.value = null;
        editDialogOpen.value = true;
    }

    // C-4 Chunk 7 — overview-side URL importer. Mirrors the detail-page
    // flow (which overwrites the current recipe); here we *create* a new
    // recipe from the import preview and route into its detail page so the
    // user can finish the cleanup. Ingredients whose names couldn't be
    // fuzzy-matched to a stock item are skipped server-side (the create
    // endpoint requires a stock_item_id per ingredient); we surface the
    // count in the success toast so the user knows to add them manually.
    // FU-102 — the dialog (RecipeImportDialog) owns url/error/loading
    // state and the `importFromUrlAsync` call. This page only opens it
    // and handles what to do with the result: build a create payload,
    // POST it, navigate to the new recipe, and toast.
    const importOpen = ref(false);

    function onImportClick() {
        importOpen.value = true;
    }

    async function onRecipeImported(imported: ImportedRecipe) {
        try {
            // Only ingredients with a fuzzy-matched stock_item_id can ship
            // through create (FK constraint). The rest stay as a counter in
            // the toast.
            const matchedIngredients = imported.ingredients.filter(
                (i): i is typeof i & { stock_item_id: string } => Boolean(i.stock_item_id),
            );
            const unmatchedCount = imported.ingredients.length - matchedIngredients.length;

            // Map each ingredient + step to a client_id so the create's
            // nested steps can reference them.
            const ingredientPayload = matchedIngredients.map((i) => ({
                stock_item_id: i.stock_item_id,
                quantity: i.quantity,
                unit: i.unit,
                notes: i.notes,
                client_id: newClientId(),
            }));
            const stepsPayload = imported.steps.map((s) => ({
                client_id: s.client_id,
                parent_client_id: s.parent_client_id,
                sequence: s.sequence,
                text: s.text,
                hint: s.hint,
                ingredient_client_ids: [],
                tool_ids: [],
            }));

            const created = await recipeApi.createAsync({
                name: imported.name,
                category_id: imported.category_id,
                cook_time_minutes: imported.cook_time_minutes,
                cuisine_id: imported.cuisine_id,
                difficulty: imported.difficulty,
                instructions: imported.instructions,
                prep_time_minutes: imported.prep_time_minutes,
                recipe_collection_id: null,
                servings: imported.servings,
                time_of_day: null,
                source: imported.source_url,
                ingredients: ingredientPayload,
                steps: stepsPayload,
            });
            // CreatedResponse shape: either `recipe_id` on the body or
            // `id` from the `created()` helper. Cover both.
            const newId =
                (created as Record<string, unknown>).recipe_id as string | undefined
                ?? created.id;
            // Refresh the overview's cache so the new recipe shows up.
            await recipeStore.getRecipesAsync();

            importOpen.value = false;
            if (imported.is_degraded) {
                $q.notify({
                    type: 'warning',
                    position: 'bottom-right',
                    timeout: 6000,
                    message: 'Couldn’t auto-structure that page',
                    caption:
                        'Created a new recipe with the page text in Instructions. ' +
                        'Review and clean it up.',
                });
            } else {
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    timeout: 5000,
                    message: `Imported "${imported.name}".`,
                    caption: unmatchedCount === 0
                        ? `${matchedIngredients.length} ingredient${matchedIngredients.length === 1 ? '' : 's'} matched.`
                        : `${unmatchedCount} ingredient${unmatchedCount === 1 ? '' : 's'} couldn’t be matched — add them manually.`,
                });
            }
            if (newId) void router.push(`/cookbook/${newId}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create the imported recipe.',
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    function newClientId(): string {
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
    }

    function onOpenRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }

    function onCookClick(recipeId: string) {
        void router.push(`/cookbook/${recipeId}/cook`);
    }

    function onToggleFavourite(recipeId: string) {
        const r = recipes.value.find((x) => x.recipe_id === recipeId);
        if (r) void recipeStore.toggleFavouriteAsync(r);
    }

    // ── Per-ingredient picker (Chunk B §1.4) ─────────────────────────
    // Cookbook card emits `add-missing` (not cookable) or `add-all-to-list`
    // (cookable). Both open the same picker; the only difference is the
    // initial check state (default = missing/low checked, sufficient/well
    // unchecked; `add-missing` passes the explicit subset as initial-checked
    // so the user lands on exactly what they need to buy).
    const pickerRef = ref<{ setBusy: (v: boolean) => void } | null>(null);
    const pickerOpen = ref(false);
    const pickerRecipe = ref<Recipe | null>(null);
    const pickerInitialCheckedIds = ref<string[] | undefined>(undefined);

    function requireActiveList(): boolean {
        const hasOne = shoppingListStore.summaries.some((s) => s.status !== 'done');
        if (hasOne) return true;
        $q.dialog({
            title: 'No active shopping list',
            message: 'Create one first to add ingredients to it.',
            ok: { label: 'Open lists', noCaps: true, color: 'primary' },
            cancel: { noCaps: true },
        }).onOk(() => { void router.push('/shopping-lists'); });
        return false;
    }

    function onAddMissing(recipeId: string, stockItemIds: string[]) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        if (recipe.ingredients.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `Nothing to add for "${recipe.name}".`,
            });
            return;
        }
        if (!requireActiveList()) return;
        pickerRecipe.value = recipe;
        pickerInitialCheckedIds.value = stockItemIds;
        pickerOpen.value = true;
    }

    function onAddAllToList(recipeId: string) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        if (recipe.ingredients.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `Nothing to add for "${recipe.name}".`,
            });
            return;
        }
        if (!requireActiveList()) return;
        pickerRecipe.value = recipe;
        pickerInitialCheckedIds.value = undefined;
        pickerOpen.value = true;
    }

    async function onPickerConfirm(payload: { stockItemIds: string[]; targetListId: string }) {
        pickerRef.value?.setBusy(true);
        try {
            await addItems(
                payload.targetListId,
                payload.stockItemIds.map((id) => ({ stock_item_id: id })),
            );
            pickerOpen.value = false;
            pickerRecipe.value = null;
            pickerInitialCheckedIds.value = undefined;
        } finally {
            pickerRef.value?.setBusy(false);
        }
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
        if (typeof id === 'string' && id && !usesStockItemIds.value.includes(id)) {
            usesStockItemIds.value = [id];
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
                shoppingListStore.refreshAsync(),
                // FU-081 — `is_planned` is now server-derived (RecipeDto
                // field), so this page no longer needs to fetch meal plans
                // for the "Planned" filter. The store hydration is left to
                // other surfaces that genuinely need it.
                // C-4 Chunk 2 — vocabularies for the cuisine/category/dietary
                // filters (sourced from the editable settings tables).
                recipeVocabStore.getAllAsync(),
                // C-2.A — household meal-slot vocabulary for the time-of-day filter.
                mealSlotStore.getMealSlotsAsync(),
                // Disclaimer text for the dietary filter. Errors non-fatal.
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
    .recipe-group {
        border-radius: 12px;
    }
    .recipe-group__header {
        padding: 12px 16px;
    }
</style>
