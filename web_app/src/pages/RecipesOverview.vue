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
        </div>

        <!-- C-4 Chunk 7 — Import-from-URL on the overview's New-Recipe surface. -->
        <BaseDialog v-model="importOpen" card-style="min-width: 460px; max-width: 600px">
            <q-card-section>
                <div class="text-h6">Import from URL</div>
                <div class="text-caption dora-text-muted q-mt-xs">
                    Works on recipe sites that publish
                    <strong>schema.org Recipe JSON-LD</strong> — the format
                    most blogs, BBC Good Food, NYT Cooking, Serious Eats,
                    AllRecipes, and similar publishers use. Other URLs still
                    import: we'll pull the page title and text into
                    Instructions so you can clean it up.
                </div>
            </q-card-section>
            <q-card-section class="q-pt-none">
                <q-input
                    v-model="importUrl"
                    outlined
                    dense
                    label="Recipe URL"
                    placeholder="https://example.com/recipes/lasagne"
                    :error="!!importError"
                    :error-message="importError ?? ''"
                    @keydown.enter.prevent="onConfirmImport"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Import"
                    :loading="importing"
                    :disable="importUrl.trim().length === 0"
                    @click="onConfirmImport"
                />
            </q-card-actions>
        </BaseDialog>

        <!-- ── Filter bar ─ standardised via FilterBar (A4) ───────── -->
        <FilterBar :active-count="activeFilterCount" @clear="clearFilters">
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
            <FilterChip v-model="plannedInOnly" :icon="ICONS.calendar_month" active-color="info">
                Planned
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
                                :recipe="recipe"
                                :highlight-stock-item-ids="usesStockItemIds"
                                @open="onOpenRecipe"
                                @cook="onCookClick"
                                @adjust-meals="onAdjustMeals"
                                @toggle-favourite="onToggleFavourite"
                                @add-missing="onAddMissing"
                                @add-all-to-list="onAddAllToList"
                                @add-to-meal-plan="onAddToMealPlan"
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

    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import PageCountsFooter from 'src/components/PageCountsFooter.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import RecipeEditDialog from 'components/RecipeEditDialog.vue';
    import DietaryTagFilter from 'src/components/recipes/DietaryTagFilter.vue';
    import TriStateFilter from 'src/components/filters/TriStateFilter.vue';
    import type {
        TriStateOption,
        TriStateSort,
    } from 'src/components/filters/triStateFilterTypes';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useNutritionMode } from 'src/composables/useNutritionMode';

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const shoppingListStore = useShoppingListStore();
    const mealPlanStore = useMealPlanStore();
    const recipeVocabStore = useRecipeVocabStore();
    const shoppingListApi = new ShoppingListApiService();
    const recipeApi = new RecipeApiService();
    const { addItems } = useShoppingListActions();

    const { recipes, recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { mealPlans } = storeToRefs(mealPlanStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);
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
                caption: describeApiError(err) || '',
            });
        }
    }

    const loading = ref(false);

    // ── Filter state ────────────────────────────────────────────────
    const searchText = ref('');
    const favouritesOnly = ref(false);
    const cookableNowOnly = ref(false);
    const inStockOnly = ref(false);
    const plannedInOnly = ref(false);
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
    // Set via the "Uses ingredients" picker OR via `?usesStockItem=` query
    // (deep-linked from the stock item detail screen — single id pre-fills
    // a one-element array).
    const usesStockItemIds = ref<string[]>([]);
    // FU-083 — "Doesn't use" pair to "Uses ingredients". Both pick from
    // stock items; combine with AND (must use all of include, must not
    // use any of exclude). Replaces the old free-text "Free from
    // ingredient(s)" path.
    const excludesStockItemIds = ref<string[]>([]);

    type SortKey = 'name' | 'last_made' | 'meal_count' | 'total_time' | 'kcal';
    type SortDir = 'asc' | 'desc';
    // C-4 Chunk 9 — "Kcal" axis added when the nutrition opt-in is on.
    // The sort menu options are computed below; the static list keeps
    // the always-on axes.
    const STATIC_SORT_OPTIONS: { label: string; value: SortKey }[] = [
        { label: 'Name', value: 'name' },
        { label: 'Recently made', value: 'last_made' },
        { label: 'Meals in pool', value: 'meal_count' },
        { label: 'Prep + cook time', value: 'total_time' },
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

    function stockLevelColourFor(name: string | null | undefined): string {
        return name ? getStockLevelColour(name) : 'grey';
    }

    // Recipe ids planned in any meal-plan entry from today onward. FU-083
    // feedback: previous string-compare on `scheduled_for` was meant to
    // work for ISO date strings but yesterday's entries were surviving
    // for some users. This version parses YYYY-MM-DD explicitly and
    // compares against today at local midnight via `Date.getTime()` —
    // robust to a time component on the wire and to time-zone edge
    // cases. The `consumed_at` skip was removed: a *planned* entry
    // remains planned even if the user marked it cooked early.
    // FU-049 still applies — should ideally be server-derived once
    // meal-plan ownership moves; the client compute keeps Chunk 1 self-
    // contained.
    const plannedRecipeIds = computed(() => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayMs = today.getTime();
        const ids = new Set<string>();
        for (const plan of mealPlans.value) {
            for (const entry of plan.entries ?? []) {
                const raw = entry.scheduled_for;
                if (!raw) continue;
                const parsed = new Date(raw);
                if (Number.isNaN(parsed.getTime())) continue;
                // Flask serialises Python `date` as RFC 2822 with a GMT
                // suffix ("Wed, 10 Jun 2026 00:00:00 GMT") — calendar-only
                // semantics, but parsed as UTC midnight. Rebuild a
                // *local*-midnight Date from the UTC calendar parts so
                // the comparison is day-to-day across any timezone
                // (otherwise a UTC midnight that's actually "yesterday
                // local" in a negative-offset zone gets miscategorised).
                const entryLocal = new Date(
                    parsed.getUTCFullYear(),
                    parsed.getUTCMonth(),
                    parsed.getUTCDate(),
                );
                if (entryLocal.getTime() >= todayMs) ids.add(entry.recipe_id);
            }
        }
        return ids;
    });

    // FU-083 — hint computeds removed (the input labels carry the meaning;
    // the hint-under-input text was just inflating the filter row).

    // A7 — sticky footer counts over the FILTERED view.
    const footerCounts = computed(() => [
        { label: 'Shown', value: filteredRecipes.value.length, tone: 'primary' as const },
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
            dotColour: stockLevelColourFor(si.stock_level_name ?? null),
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
            if (plannedInOnly.value && !plannedRecipeIds.value.has(r.recipe_id)) return false;

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
            || plannedInOnly.value
            || (mealCountMin.value !== null && Number.isFinite(mealCountMin.value))
            || (missingMax.value !== null && Number.isFinite(missingMax.value))
            || (kcalMax.value !== null && Number.isFinite(kcalMax.value))
            || collectionFilter.value !== null
            || cuisineFilter.value !== null
            || categoryFilter.value !== null
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
        if (plannedInOnly.value) n++;
        if (mealCountMin.value !== null && Number.isFinite(mealCountMin.value)) n++;
        if (missingMax.value !== null && Number.isFinite(missingMax.value)) n++;
        if (kcalMax.value !== null && Number.isFinite(kcalMax.value)) n++;
        if (collectionFilter.value !== null) n++;
        if (cuisineFilter.value !== null) n++;
        if (categoryFilter.value !== null) n++;
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
            case 'meal_count':
                return asc ? 'Fewest meals first' : 'Most meals first';
            case 'total_time':
                return asc ? 'Fastest first' : 'Slowest first';
            case 'kcal':
                return asc ? 'Lowest kcal first' : 'Highest kcal first';
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
        sortDir.value = next === 'name' ? 'asc' : 'desc';
    });

    // C-4 Chunk 9 — if the user had Kcal as their sort axis and then the
    // nutrition opt-in flips off (admin disable, or user picks Off in
    // Settings), snap back to Name so the picker doesn't show an
    // orphaned value.
    watch(nutritionEnabled, (on) => {
        if (!on && sortBy.value === 'kcal') sortBy.value = 'name';
    });

    function clearFilters() {
        searchText.value = '';
        favouritesOnly.value = false;
        cookableNowOnly.value = false;
        inStockOnly.value = false;
        plannedInOnly.value = false;
        mealCountMin.value = null;
        missingMax.value = null;
        kcalMax.value = null;
        collectionFilter.value = null;
        cuisineFilter.value = null;
        categoryFilter.value = null;
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
    const importOpen = ref(false);
    const importUrl = ref('');
    const importing = ref(false);
    const importError = ref<string | null>(null);

    function onImportClick() {
        importUrl.value = '';
        importError.value = null;
        importOpen.value = true;
    }

    async function onConfirmImport() {
        const url = importUrl.value.trim();
        if (!url) return;
        importError.value = null;
        importing.value = true;
        try {
            const imported = await recipeApi.importFromUrlAsync(url);
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
                nutrition: imported.nutrition,
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
            if (newId) void router.push(`/recipes/${newId}`);
        } catch (err) {
            importError.value = 'Could not import. The URL might not publish structured recipe data.';
            console.warn('Import failed', err);
        } finally {
            importing.value = false;
        }
    }

    function newClientId(): string {
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
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

    // Edit/Duplicate/Delete moved off the card (Chunk 3): the card click opens
    // the detail page, which is the edit + delete surface. Cook is the card's
    // only primary action.
    async function onAdjustMeals(recipeId: string, delta: number) {
        try {
            await recipeStore.adjustMealsAsync(recipeId, delta);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update meals.',
                caption: describeApiError(err) || '',
            });
        }
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
            .filter((s) => s.status !== 'done')
            .map((s) => ({
                label: s.name,
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
            shoppingListStore.quickAddTargetListId ?? activeListOptions.value[0]?.value ?? null;
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
                // Meal plans drive the "planned in" filter (client-side
                // derivation; future Phase-2 work moves this server-side).
                mealPlanStore.getMealPlansAsync(),
                // C-4 Chunk 2 — vocabularies for the cuisine/category/dietary
                // filters (sourced from the editable settings tables).
                recipeVocabStore.getAllAsync(),
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
