<template>
    <!-- FU-609 — root on <q-page> for the layout height contract so the sticky
         PageCountsFooter pins to the viewport bottom even on a short list. No
         :style-fn here: this page document-scrolls (a growing card grid), it is
         NOT a fixed-height app-shell like StockOverview — <q-page>'s default
         min-height is exactly what's wanted. See ENGINEERING_STANDARDS R-036. -->
    <q-page class="q-pa-md">
        <!-- ── Toolbar ─────────────────────────────────────────────
             2026-08-17 feedback: standardised on the Stock Overview
             toolbar (`StockOverview.vue`) so the two list surfaces read
             as one control. Actions left in a fixed order (add · import ·
             photos · view), filter-toggle + search pushed right. On
             phones every action drops its label and rides its icon alone
             (tooltip carries the name), and `__find` wraps to a full-width
             second row so the search box has room — same two-row shape,
             same `compactToolbar` gate. Import was `ghost` (which reads
             white/transparent next to the filled actions); it's a
             secondary now, like Stock's own non-primary buttons. -->
        <div class="row items-center q-gutter-sm recipes-toolbar">
            <!-- Counts live in the sticky PageCountsFooter (A7). -->
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                :label="compactToolbar ? undefined : 'New recipe'"
                aria-label="New recipe"
                @click="onCreateClick"
            >
                <q-tooltip v-if="compactToolbar">New recipe</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="secondary"
                :icon="ICONS.content_paste"
                :label="compactToolbar ? undefined : 'Import'"
                aria-label="Import a recipe"
                @click="onImportClick"
            >
                <q-tooltip v-if="compactToolbar">Import a recipe</q-tooltip>
            </BaseButton>
            <!-- 2026-08-17 feedback: card grid ⇄ one row per recipe (the
                 Stock Overview shape). The icon shows the shape the button
                 switches TO. Remembered per device via localStorage —
                 `useListViewMode`.
                 2026-08-18: this ALSO owns photos now. The toolbar used to
                 carry a separate "Hide photos" toggle beside it, which made
                 four states out of two real ones — "compact with photos" and
                 "cards without" were both just a smaller/emptier version of
                 the other mode. Cards show photos, compact doesn't. The
                 per-user `show_recipe_images` preference still exists and
                 still gates the recipe *detail* page; it moved to
                 Settings → Appearance, so choosing a cookbook layout can't
                 silently change what you see while cooking. -->
            <BaseButton
                variant="secondary"
                :icon="viewMode === 'grid' ? ICONS.view_list : ICONS.view_module"
                :label="compactToolbar ? undefined : (viewMode === 'grid' ? 'Compact' : 'Cards')"
                :aria-label="viewMode === 'grid' ? 'Switch to compact rows, without photos' : 'Switch to cards, with photos'"
                @click="toggleViewMode"
            >
                <!-- The "· remembered next visit" suffix was dropped
                     2026-08-19 (owner): the setting IS remembered, but saying
                     so in a tooltip you read every time is noise. -->
                <q-tooltip>
                    {{ viewMode === 'grid' ? 'Compact rows, no photos' : 'Card grid with photos' }}
                </q-tooltip>
            </BaseButton>

            <q-space class="gt-xs" />
            <div class="row items-center q-gutter-sm no-wrap recipes-toolbar__find">
                <!-- Feedback 2026-06-18: filter toggle in the main toolbar so
                     the FilterBar doesn't carry its own row of chrome. -->
                <FilterToggleButton
                    v-model="filtersExpanded"
                    :active-count="activeFilterCount"
                    :compact="compactToolbar"
                    @clear="clearFilters"
                />
                <q-input
                    v-model="searchText"
                    class="col"
                    dense
                    outlined
                    debounce="200"
                    placeholder="Search"
                    clearable
                >
                    <template #prepend><q-icon :name="ICONS.search" /></template>
                </q-input>
            </div>
        </div>

        <!-- Import-from-URL on the overview's New-Recipe
             surface. FU-102: dialog chrome extracted to a shared component;
             this page wires the imported DTO to `createAsync` + nav.
             IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — the PWA share target
             (manifest.json `share_target.action: /cookbook`) drops
             `?share_text=…&share_url=…` onto this route; on mount we
             read them, auto-open the dialog, and pre-fill the fields
             so the user only has to hit Import. -->
        <RecipeImportDialog
            v-model="importOpen"
            :prefill-content="sharePrefillContent"
            :prefill-source-url="sharePrefillSourceUrl"
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
            <!-- FU-108: filter controls ordered by usage frequency
                 (quick chips → sort → common single-selects →
                 ingredients → numeric bounds → occasional
                 dietary/tools → set-and-forget collection).
                 2026-08-17 feedback: split into the Stock Overview's two
                 rows — toggle chips on top, input filters below — each
                 scrolling sideways on phones rather than wrapping to four
                 or five lines (an open panel was eating the viewport).
                 Same rows, same overflow treatment, same class shape as
                 `stock-quick-filters` / `stock-input-filters`. -->
            <FilterRow>
            <FilterChip v-model="favouritesOnly" :icon="ICONS.favorite" active-color="negative">
                Favourites
            </FilterChip>
            <!-- Icon matches the recipe row's Cook button (`chef_hat`) — the
                 filter and the action it predicts should read as the same
                 thing. The help affordance sits INSIDE the chip rather than
                 floating beside it, so the chip is one target and the row
                 doesn't gain a stray un-aligned glyph. -->
            <FilterChip v-model="cookableNowOnly" :icon="ICONS.chef_hat" active-color="positive">
                Cookable now
                <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                    <q-tooltip>Recipes where every ingredient is currently in stock.</q-tooltip>
                </q-icon>
            </FilterChip>
            <!-- "Meals prepared" (was "Have meals in pool"): portions you've
                 already cooked ahead and can eat now. Only meaningful when the
                 install runs batch cook-style — with `batchEnabled` off there
                 is no cook-ahead surface at all, so the filter is hidden rather
                 than shown always matching nothing (R-029). -->
            <FilterChip
                v-if="batchEnabled"
                v-model="inStockOnly"
                :icon="ICONS.mealsPrepared"
                active-color="primary"
            >
                Meals prepared
            </FilterChip>
            <!-- tri-state: click 1 = Planned only, click 2 = Not
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
            </FilterRow>

            <!-- ── Row 2: input filters ──────────────────────────────── -->
            <FilterRow variant="fields">
            <!-- Order — owner feedback 2026-08-20: "Collection and dietary
                 tags filters should be near the front." They were dead last
                 and second-to-last, behind six facets and four numeric
                 bounds. Now: sort · Collection · Dietary tags (the two he
                 reaches for) · the recipe's own facets · numeric bounds ·
                 Tools (genuinely occasional). The earlier FU-108 ordering was
                 by *guessed* frequency; this is by reported use. -->

            <!-- Axis + direction are one control (SortControl) — the direction
                 toggle rides in the select's append slot rather than sitting
                 beside it as a separately-sized button. -->
            <SortControl
                v-model:sort-by="sortBy"
                v-model:sort-dir="sortDir"
                :options="SORT_OPTIONS"
            />

            <BaseSelect
                emit-value
                map-options
                clearable
                v-model="collectionFilter"
                :options="collectionOptionsWithNone"
                label="Collection"
            >
                <template #prepend><q-icon :name="ICONS.collection" size="18px" /></template>
            </BaseSelect>
            <!-- L237 — one tri-state dietary filter (must-have / must-not /
                 neutral) replacing the old two include/exclude selects.
                 These were `DietaryTagFilter`, a wrapper whose only remaining
                 job was defaulting the label; its own docblock said new uses
                 should consume TriStateFilter directly, so with icons to plumb
                 through as well it was collapsed rather than widened (R-001). -->
            <TriStateFilter
                label="Dietary tags"
                :icon="ICONS.eco"
                :options="dietaryTagOptions"
                v-model:include="dietaryTagsInclude"
                v-model:exclude="dietaryTagsExclude"
            />

            <!-- L235 — cuisine + category are distinct single-select filters,
                 no longer lumped together as one "tags" multi-select.
                 Icons match the matching Settings → Kitchen setup pages
                 (cuisines = globe, categories = shape, meal slots = clock,
                 tools = blender, dietary tags = leaf) so the same concept
                 carries the same glyph wherever it appears. -->
            <BaseSelect
                emit-value
                map-options
                clearable
                v-model="cuisineFilter"
                :options="cuisineOptions"
                label="Cuisine"
            >
                <template #prepend><q-icon :name="ICONS.public" size="18px" /></template>
            </BaseSelect>
            <BaseSelect
                emit-value
                map-options
                clearable
                v-model="categoryFilter"
                :options="categoryOptions"
                label="Category"
            >
                <template #prepend><q-icon :name="ICONS.category" size="18px" /></template>
            </BaseSelect>
            <!-- time-of-day single-select. §1.12: vocabulary sourced from the
                 household MealSlot table (DEFAULT_MEAL_SLOTS is only the
                 pre-first-load fallback).
                 Keeps the clock glyph — it matches Settings → Meal slots. The
                 crossover the owner reported ran the other way: the *duration*
                 chips on the cookbook card/row were also on a clock, and are
                 now on `timer`. Clock = a time of day, timer = a length of
                 time; one glyph each. -->
            <BaseSelect
                emit-value
                map-options
                clearable
                v-model="timeOfDayFilter"
                :options="TIME_OF_DAY_OPTIONS"
                label="Time of day"
            >
                <template #prepend><q-icon :name="ICONS.schedule" size="18px" /></template>
            </BaseSelect>
            <!-- §1.7 — difficulty single-select. Closed vocabulary
                 (Easy / Medium / Hard). The card's difficulty chip was on
                 `star_outline`, which reads as a *rating*; it now shares this
                 speedometer (owner feedback 2026-08-20). -->
            <BaseSelect
                emit-value
                map-options
                clearable
                v-model="difficultyFilter"
                :options="DIFFICULTY_OPTIONS"
                label="Difficulty"
            >
                <template #prepend><q-icon :name="ICONS.difficulty" size="18px" /></template>
            </BaseSelect>
            <!-- Uses / Doesn't use ingredients consolidated
                 into the shared TriStateFilter, with `searchable` for the
                 large stock-item set and a per-row stock-level colour dot.
                 Single button (+/-) replaces the two paired q-selects. -->
            <TriStateFilter
                label="Ingredients"
                :icon="ICONS.ingredients"
                searchable
                search-placeholder="Search ingredients…"
                :options="ingredientFilterOptions"
                :sort-options="ingredientSortOptions"
                default-sort="name"
                v-model:include="usesStockItemIds"
                v-model:exclude="excludesStockItemIds"
            />

            <!-- Numeric bounds. :hint removed; the under-input copy was just
                 padding out the filter row's height and offsetting alignment
                 without adding info. Every bound carries the same icon as its
                 sort axis / the surface it counts, so the row scans as a set
                 rather than a mix of iconned and bare fields. -->
            <!-- "Serves ≥" — owner feedback 2026-08-20 ("missing filter for #
                 of serves"). A lower bound, not a range: the intent is "I'm
                 cooking for five tonight", and a recipe that serves more than
                 that just leaves leftovers. A recipe with no servings recorded
                 fails a set bound — same intent rule as the facets above
                 ("show me things that feed 5", not "…or that might"). -->
            <q-input
                v-model.number="servesMin"
                dense
                outlined
                type="number"
                min="0"
                class="filter-row__wide"
                label="Serves ≥"
                hide-bottom-space
            >
                <template #prepend><q-icon :name="ICONS.people" size="18px" /></template>
            </q-input>
            <q-input
                v-model.number="ingredientsMax"
                dense
                outlined
                type="number"
                min="0"
                class="filter-row__wide"
                label="Ingredient count ≤"
                hide-bottom-space
            >
                <template #prepend><q-icon :name="ICONS.ingredientCount" size="18px" /></template>
            </q-input>
            <!-- kcal upper-bound filter (gated). -->
            <q-input
                v-if="kcalAxisAvailable"
                v-model.number="kcalMax"
                dense
                outlined
                type="number"
                min="0"
                class="filter-row__wide"
                label="Kcal ≤"
                hide-bottom-space
            >
                <template #prepend><q-icon :name="ICONS.local_fire_department" size="18px" /></template>
            </q-input>
            <q-input
                v-if="batchEnabled"
                v-model.number="mealCountMin"
                dense
                outlined
                type="number"
                min="0"
                class="filter-row__wide"
                label="Meals prepared ≥"
                hide-bottom-space
            >
                <template #prepend><q-icon :name="ICONS.mealsPrepared" size="18px" /></template>
            </q-input>

            <!-- L310 — tools inclusion/exclusion filter (same tri-state control). -->
            <TriStateFilter
                label="Tools"
                :icon="ICONS.blender"
                :options="toolFilterOptions"
                v-model:include="toolsInclude"
                v-model:exclude="toolsExclude"
            />
            <!-- Two filters used to live here and no longer do:
                 • "Missing ingredients ≤" — removed 2026-08-20 (owner: "feels
                   a bit useless?"). The zero case IS the "Cookable now" chip,
                   nothing sorted by it, and every card/row already shows what
                   the recipe is short of. Its `missingMax` state went with it.
                 • "Free from ingredient(s)" free-text — its concern is covered
                   by the "Doesn't use" side of the Ingredients picker above;
                   the text-match was a source of false negatives. -->
            </FilterRow>
            </template>
        </FilterBar>
        <!-- disclaimer surfaced when any dietary filter is on.
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
        <!-- Owner feedback 2026-08-20: "filter area needs a little gap between
             itself and page content, just like stock overview has". FilterBar
             only pads itself 4px; on StockOverview the separation comes from
             the bulk-action bar's own `q-py-xs` wrapper sitting between the
             panel and the list. This page has no bulk bar, so the list started
             flush against the filter panel. Own the gap here rather than
             adding bottom margin to FilterBar — that would move every other
             surface that uses it, and StockOverview's spacing is already
             right. -->
        <div class="recipes-content">
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

            <!-- One flat list, in the order the sort axis put them.
                 Recipes used to be boxed into collapsible collection
                 folders; in a large cookbook that buried search results
                 under a folder you had to notice and open, which is the
                 opposite of what a search is for. The collection is now a
                 fact on each card's meta line, and the toolbar's Collection
                 filter is how you narrow to one.
                 Two shapes, one data path: the compact branch is the same
                 recipes, the same handlers and the same derived figures
                 (`useRecipeDisplay`) — only the component differs. -->
            <div v-if="viewMode === 'grid'" class="row q-col-gutter-md">
                <div
                    v-for="recipe in sortedRecipes"
                    :key="recipe.recipe_id"
                    class="col-12 col-sm-6 col-md-4 col-lg-3"
                >
                    <RecipeCard
                        :recipe="recipeWithExpiringCount(recipe)"
                        :show-image="true"
                        :show-expiring-badge="expiringOnly"
                        @open="onOpenRecipe"
                        @cook="onCookClick"
                        @toggle-favourite="onToggleFavourite"
                        @add-missing="onAddMissing"
                        @add-all-to-list="onAddAllToList"
                    />
                </div>
            </div>
            <div v-else>
                <RecipeRow
                    v-for="recipe in sortedRecipes"
                    :key="recipe.recipe_id"
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
        </FadeTransition>
        </div>

        <PageCountsFooter v-if="recipes.length > 0" :counts="footerCounts" />

        <!-- ── Edit dialog ────────────────────────────────────────── -->
        <RecipeEditDialog
            v-model="editDialogOpen"
            :recipe="editingRecipe"
            @created="onRecipeCreated"
            @updated="onRecipeUpdated"
        />

        <!-- Cook-mode guard. Owner feedback 2026-08-19: starting cook mode
             from here skipped the "you're missing ingredients" confirm that
             the recipe page shows. Same component, same predicate — the only
             difference is that nothing here can be dirty, because the cookbook
             doesn't edit recipes. -->
        <CookModeGuardDialog
            v-model="cookGuardOpen"
            :recipe="cookGuardRecipe"
            @start="startCookMode"
        />

        <!-- ── Per-ingredient picker (Chunk B §1.4) ─────────────── -->
        <RecipeIngredientPickerDialog
            ref="pickerRef"
            v-model="pickerOpen"
            :recipe="pickerRecipe"
            :initial-checked-ids="pickerInitialCheckedIds"
            @confirm="onPickerConfirm"
        />

    </q-page>
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
    import RecipeRow from 'src/components/recipes/RecipeRow.vue';
    import RecipeEditDialog from 'components/RecipeEditDialog.vue';
    import RecipeIngredientPickerDialog from 'src/components/recipes/RecipeIngredientPickerDialog.vue';
    import CookModeGuardDialog from 'src/components/recipes/CookModeGuardDialog.vue';
    import FilterRow from 'src/components/filters/FilterRow.vue';
    import TriStateFilter from 'src/components/filters/TriStateFilter.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import SortControl, { type SortAxisFor } from 'src/components/filters/SortControl.vue';
    import type {
        TriStateOption,
        TriStateSort,
    } from 'src/components/filters/triStateFilterTypes';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useFilterPanelExpanded } from 'src/composables/useFilterPanelExpanded';
    import { useListState } from 'src/composables/useListState';
    import { useListViewMode } from 'src/composables/useListViewMode';
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
    import { needsCookGuard } from 'src/helpers/cookModeGuard';
    import {
        DEFAULT_MEAL_SLOTS,
        DIFFICULTY_RANK,
        DIFFICULTY_VALUES,
        type Difficulty,
    } from 'src/helpers/recipeVocabulary';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useNutritionMode } from 'src/composables/useNutritionMode';

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const shoppingListStore = useShoppingListStore();
    // meal-plan store dependency dropped: `is_planned` is
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
    // Phones drop every toolbar label down to its icon — same gate and same
    // reason as Stock Overview (the row was eating a quarter of the screen).
    const compactToolbar = computed(() => $q.screen.lt.sm);
    // Card grid ⇄ compact rows, remembered across visits (localStorage).
    const viewMode = useListViewMode('cookbook-overview');
    function toggleViewMode() {
        viewMode.value = viewMode.value === 'grid' ? 'compact' : 'grid';
    }
    // FU-637 — the kcal axis works in both modes now. Which figure a recipe
    // carries (typed in simple, rolled-up in complex) and whether it's solid
    // enough to judge on are both the server's call — the list DTO ships the
    // answer, so nothing is re-derived here (R-003).
    const { nutritionEnabled: kcalAxisAvailable } = useNutritionMode();
    // Install-wide cook-style. "fresh" installs have no cooked-ahead portions,
    // so every meals-prepared affordance (chip, minimum-count input, sort axis)
    // is hidden rather than left to always match nothing.
    const { batchEnabled } = useBatchEnabled();
    const kcalOf = (recipe: Recipe) => ({
        value: recipe.kcal_per_serving ?? null,
        judgeable: recipe.kcal_is_reliable === true,
    });
    // Two conditional axes, each gated on the feature that gives it meaning:
    // Kcal on the nutrition opt-in, "Meals prepared" on batch cook-style.
    const SORT_OPTIONS = computed<SortAxisFor<SortKey>[]>(() => {
        const options = [...STATIC_SORT_OPTIONS];
        if (batchEnabled.value) {
            options.push({
                label: 'Meals prepared', value: 'meal_count',
                ascLabel: 'Fewest first', descLabel: 'Most first',
            });
        }
        if (kcalAxisAvailable.value) {
            options.push({
                label: 'Kcal', value: 'kcal',
                ascLabel: 'Lowest first', descLabel: 'Highest first', defaultDir: 'asc',
            });
        }
        return options;
    });

    const loading = ref(false);

    // ── Filter state ────────────────────────────────────────────────
    // (the filter panel's expanded state is declared below, once
    // `activeFilterCount` exists — it's what decides whether the panel opens.)
    // A8 §3 nav-state — filters/search/sort survive navigation within the
    // session and reset on full reload. Non-persisted (fetch-in-flight,
    // fetched-data caches) stay as their own refs below.
    const cookbookState = useListState('cookbook-overview', () => ({
        searchText: ref(''),
        favouritesOnly: ref(false),
        cookableNowOnly: ref(false),
        inStockOnly: ref(false),
        // tri-state: 'off' = no constraint; 'include' = only planned
        // recipes (any future un-consumed MealPlanEntry); 'exclude' = only
        // un-planned recipes. Cycles via TriStateFilterChip.
        plannedFilterState: ref<TriState>('off'),
        // C-waste W4 — when on, restricts the list to recipes using ≥1
        // expiring-within-14-days in-stock ingredient AND force-sorts by
        // count desc.
        expiringOnly: ref(false),
        // `null` means "no bound". Cleared inputs land as NaN via
        // v-model.number; predicates guard on Number.isFinite.
        mealCountMin: ref<number | null>(null),
        // "Serves ≥" lower bound (owner feedback 2026-08-20).
        servesMin: ref<number | null>(null),
        // "Kcal ≤" filter (only renders when nutrition opt-in
        // is on). Recipes with no kcal value pass through.
        kcalMax: ref<number | null>(null),
        collectionFilter: ref<string | null>(null),
        // L235 — cuisine + category are distinct single-select id filters.
        cuisineFilter: ref<string | null>(null),
        categoryFilter: ref<string | null>(null),
        // time-of-day single-select. Null = no filter.
        timeOfDayFilter: ref<string | null>(null),
        // §1.7 — difficulty single-select. Null = no filter.
        difficultyFilter: ref<Difficulty | null>(null),
        // "# ingredients ≤" cap.
        ingredientsMax: ref<number | null>(null),
        // Set via the "Uses ingredients" picker OR via `?usesStockItem=` query.
        usesStockItemIds: ref<string[]>([]),
        // "Doesn't use" pair. Combine with AND.
        excludesStockItemIds: ref<string[]>([]),
    }));
    const {
        searchText, favouritesOnly, cookableNowOnly, inStockOnly,
        plannedFilterState, expiringOnly, mealCountMin, servesMin, kcalMax,
        collectionFilter, cuisineFilter, categoryFilter, timeOfDayFilter,
        difficultyFilter, ingredientsMax, usesStockItemIds, excludesStockItemIds,
    } = cookbookState;
    const EXPIRING_FILTER_HORIZON_DAYS = 14;
    /** Per-recipe at-risk facts from the filter fetch: how many ingredients
     *  are at risk, and when the soonest of them goes off. Both are server-
     *  derived; the client only orders and colours by them. */
    type ExpiringFacts = { count: number; soonest: string | null };
    const expiringByRecipeId = ref<Map<string, ExpiringFacts>>(new Map());
    const expiringFetchInFlight = ref(false);

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
    // "Kcal" axis added when the nutrition opt-in is on.
    // The sort menu options are computed below; the static list keeps
    // the always-on axes.
    // time-of-day reads the household meal-slot vocabulary
    // (MealSlot table), falling back to the seed constant only before the
    // store's first load.
    const TIME_OF_DAY_OPTIONS = computed(() =>
        mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );
    // §1.7 — difficulty closed vocabulary; mirrors ALLOWED_DIFFICULTY_VALUES
    // on the server.
    const DIFFICULTY_OPTIONS = [...DIFFICULTY_VALUES];

    // Labels name the axis only — the direction lives on the attached toggle
    // (see SortControl), so no option here says "first" or carries an arrow.
    // Each axis states how its two directions read and which one it snaps to
    // when picked; that used to live in a separate `sortDirTooltip` switch and
    // a separate `watch(sortBy)`, three places to keep in step for one fact.
    const STATIC_SORT_OPTIONS: SortAxisFor<SortKey>[] = [
        {
            label: 'Name', value: 'name',
            ascLabel: 'A → Z', descLabel: 'Z → A', defaultDir: 'asc',
        },
        {
            label: 'Recently made', value: 'last_made',
            ascLabel: 'Oldest first', descLabel: 'Most recent first',
        },
        // Recently added is the fifth IMPL_PLAN_COOKBOOK Chunk 1
        // axis; landed once Recipe.created_at became available on the DTO.
        {
            label: 'Recently added', value: 'created_at',
            ascLabel: 'Oldest first', descLabel: 'Most recent first',
        },
        // "Prep + cook time" described the arithmetic rather than the thing
        // being sorted; owner feedback 2026-08-18.
        {
            label: 'Total time', value: 'total_time',
            ascLabel: 'Fastest first', descLabel: 'Slowest first', defaultDir: 'asc',
        },
        // Fewer ingredients first is the common "make this quick" intent.
        {
            label: 'Ingredient count', value: 'ingredient_count',
            ascLabel: 'Fewest first', descLabel: 'Most first', defaultDir: 'asc',
        },
        // §1.7 — difficulty ordinal (Easy < Medium < Hard; nulls sink).
        {
            label: 'Difficulty', value: 'difficulty',
            ascLabel: 'Easiest first', descLabel: 'Hardest first', defaultDir: 'asc',
        },
    ];
    const cookbookSortState = useListState('cookbook-overview:sort', () => ({
        sortBy: ref<SortKey>('name'),
        // explicit asc/desc toggle. Default per axis: name = asc,
        // everything else = desc.
        sortDir: ref<SortDir>('asc'),
    }));
    const { sortBy, sortDir } = cookbookSortState;

    // Cookbook filter + sort state is persisted, so an install that *had* batch
    // cook-style on can come back with a meals-prepared sort or filter still
    // stored after an admin switches to "fresh". Left alone that shows an empty
    // Sort-by select and an active-but-invisible filter silently hiding recipes,
    // so neutralise the state rather than only hiding the controls. Immediate:
    // `batchEnabled` resolves from /api/health after mount, so a stale stored
    // value would otherwise survive until the flag next changed.
    watch(batchEnabled, (enabled) => {
        if (enabled) return;
        if (sortBy.value === 'meal_count') sortBy.value = 'name';
        inStockOnly.value = false;
        mealCountMin.value = null;
    }, { immediate: true });

    // Dietary + tools filter state — tri-state include/exclude id arrays
    // (combine with AND). Persisted with the rest of the cookbook filters.
    const cookbookTriStates = useListState('cookbook-overview:tri', () => ({
        dietaryTagsInclude: ref<string[]>([]),
        dietaryTagsExclude: ref<string[]>([]),
        toolsInclude: ref<string[]>([]),
        toolsExclude: ref<string[]>([]),
    }));
    const {
        dietaryTagsInclude, dietaryTagsExclude, toolsInclude, toolsExclude,
    } = cookbookTriStates;
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


    // `is_planned` is now server-owned (RecipeDto field,
    // derived from MealPlanEntry rows in the same query that fills
    // `committed_meals`). The client predicate reads it directly; the
    // old client-side walk of `mealPlanStore.mealPlans[].entries[]`
    // with timezone-juggling on `scheduled_for` is retired.

    // hint computeds removed (the input labels carry the meaning;
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
    // used by the shared TriStateFilter (the +/-
    // partner replaces the old two paired q-selects). The component
    // owns the search input AND the sort selector (name / stock level)
    // — we hand it the full options list with a `dotColour` per row
    // and embed the stock-level sequence in `meta` so the level-sort
    // compare can read it without re-querying the store.
    const ingredientFilterOptions = computed<TriStateOption[]>(() =>
        stockItems.value.map((si) => ({
            value: si.stock_item_id,
            label: si.name,
            // sequence-keyed (R-003). `si.stock_level_sequence`
            // is null on untracked items → null dotColour, which the
            // TriStateFilter renders as a muted dot.
            dotColour: colourForSequence(si.stock_level_sequence ?? null),
            meta: { levelSequence: si.stock_level_sequence ?? null },
        })),
    );

    // Sort axes for the ingredient filter. Name is the default
    // (alphabetical is more browsable than level when scanning); "Stock
    // level" is the secondary axis.
    //
    // Level sort runs **stocked first** (owner feedback 2026-08-20: "doesn't
    // let you change sort direction — if we aren't doing that then level sort
    // should be stocked first, not out of stock first"). A direction toggle
    // was the other option and was rejected: this is a picker inside a
    // dropdown inside a filter panel, and a third control in there costs more
    // than the one direction it would add. Stocked-first is also the right
    // single direction — the dominant use of "Uses ingredients" is picking
    // something you actually have. Ascending sequence = in-stock first per
    // `stock_status.py`; untracked items (null sequence) sink to the bottom
    // rather than riding at the top, which is what a -1 sentinel would do
    // under ascending order.
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
                const UNTRACKED = Number.MAX_SAFE_INTEGER;
                const aSeq = (a.meta?.levelSequence as number | null | undefined) ?? UNTRACKED;
                const bSeq = (b.meta?.levelSequence as number | null | undefined) ?? UNTRACKED;
                if (aSeq === bSeq) return a.label.localeCompare(b.label);
                return aSeq - bSeq;
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
            // tri-state: include keeps only planned; exclude keeps
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
                && expiringByRecipeId.value.size > 0
                && !expiringByRecipeId.value.has(r.recipe_id)
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
            // "Serves ≥" lower bound. A recipe with no servings recorded
            // fails a set bound rather than passing through — the user asked
            // for something that feeds N, and "unknown" isn't an answer.
            if (
                servesMin.value !== null
                && Number.isFinite(servesMin.value)
                && (r.servings ?? 0) < servesMin.value
            ) {
                return false;
            }
            // "Kcal ≤" filter. Recipes we can't put a trustworthy number on
            // pass through rather than being hidden — that covers both an
            // unannotated recipe and a complex-mode rollup too thin to judge
            // (excluding a recipe on a 1-of-8 estimate would mislead exactly
            // the person filtering by calories).
            if (
                kcalAxisAvailable.value
                && kcalMax.value !== null
                && Number.isFinite(kcalMax.value)
            ) {
                const { value, judgeable } = kcalOf(r);
                if (judgeable && value !== null && value > kcalMax.value) return false;
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
            // time-of-day single-select. Null = no filter; a
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
            // "# ingredients ≤" cap. Blank/NaN reverts to no
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
                if (!r.ingredients.some((i) => i.stock_item_id !== null && wanted.has(i.stock_item_id))) return false;
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
            // "Doesn't use" stock-item picker (the +/- partner to
            // "Uses ingredients"). Recipe is excluded if any picked id is in
            // its ingredient set. Replaces the old free-text path.
            if (excludesStockItemIds.value.length > 0) {
                const ingIds = new Set(r.ingredients.map((i) => i.stock_item_id));
                if (excludesStockItemIds.value.some((id) => ingIds.has(id))) return false;
            }
            return true;
        }),
    );

    // explicit asc/desc direction. Null sentinels (last_made,
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
            const facts = expiringByRecipeId.value;
            return arr.sort((a, b) => {
                const af = facts.get(a.recipe_id);
                const bf = facts.get(b.recipe_id);
                // URGENCY first (owner feedback 2026-08-18): the soonest
                // expiry wins, so 2 ingredients going off today outrank 4
                // going off next week — the filter exists to save the food
                // that's closest to being binned, not the biggest pile.
                // ISO dates compare correctly as strings; a recipe with no
                // date sinks below every recipe that has one.
                const ad = af?.soonest ?? null;
                const bd = bf?.soonest ?? null;
                if (ad !== bd) {
                    if (ad === null) return 1;
                    if (bd === null) return -1;
                    return ad.localeCompare(bd);
                }
                // Same urgency → the bigger rescue first.
                const ac = af?.count ?? 0;
                const bc = bf?.count ?? 0;
                if (ac !== bc) return bc - ac;
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
                    // never null on rows from the API (DTO field
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
                    // Thin estimates sort last alongside "no figure at all" —
                    // ranking on one would put a half-known recipe above a
                    // fully-known one on nothing but missing data.
                    const ak = kcalOf(a);
                    const bk = kcalOf(b);
                    const av = ak.judgeable ? ak.value : null;
                    const bv = bk.judgeable ? bk.value : null;
                    if (av === null && bv === null) return a.name.localeCompare(b.name);
                    if (av === null) return 1;
                    if (bv === null) return -1;
                    if (av === bv) return a.name.localeCompare(b.name);
                    return (av - bv) * dirSign;
                }
                case 'ingredient_count': {
                    // neither side is null (ingredients[] is
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

    // NOTE: the collection-bucketing + collapsed-folder state that used to
    // live here is gone. Recipes render as one flat sorted list; the
    // collection travels on each card's meta line (`useRecipeDisplay`) and
    // the Collection dropdown below is how you narrow to one.

    const hasAnyFilter = computed(
        () =>
            searchText.value !== ''
            || favouritesOnly.value
            || cookableNowOnly.value
            || inStockOnly.value
            || plannedFilterState.value !== 'off'
            || expiringOnly.value
            || (mealCountMin.value !== null && Number.isFinite(mealCountMin.value))
            || (servesMin.value !== null && Number.isFinite(servesMin.value))
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
        if (servesMin.value !== null && Number.isFinite(servesMin.value)) n++;
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

    // 2026-08-20 owner call — the panel opens iff something is filtered, and
    // that state is not remembered across visits. Adopted here from Stock
    // overview, which is where the owner met the behaviour and preferred it.
    // Declared here rather than up with the rest of the filter state because
    // it reads `activeFilterCount`, which is defined just above.
    const filtersExpanded = useFilterPanelExpanded(
        'cookbook-overview',
        () => activeFilterCount.value > 0,
    );

    // if the user had Kcal as their sort axis and then the
    // nutrition mode leaves simple (off, or complex where the figure is
    // derived per-recipe instead), snap back to Name so the picker doesn't
    // show an orphaned value.
    watch(kcalAxisAvailable, (on) => {
        if (!on && sortBy.value === 'kcal') sortBy.value = 'name';
    });

    // C-waste W4 — merge the server-fetched expiring count back onto
    // recipes from the store before passing them to the card. The
    // store's copies don't carry the count (the default fetch doesn't
    // ask for it); the filter-on fetch does. Identity-stable in the
    // off case so Vue's reactivity skips unnecessary card re-renders.
    function recipeWithExpiringCount(recipe: Recipe): Recipe {
        if (!expiringOnly.value) return recipe;
        const facts = expiringByRecipeId.value.get(recipe.recipe_id);
        const count = facts?.count ?? 0;
        const soonest = facts?.soonest ?? null;
        if (
            count === (recipe.expiring_ingredient_count ?? 0)
            && soonest === (recipe.expiring_soonest_date ?? null)
        ) return recipe;
        return {
            ...recipe,
            expiring_ingredient_count: count,
            expiring_soonest_date: soonest,
        };
    }

    // Fetch the expiring set whenever the filter is flipped on; clear
    // it when flipped off so a stale map doesn't leak into a future
    // session. R-003 — the predicate (which items expire within N days,
    // which recipes use them) lives entirely on the server.
    watch(expiringOnly, async (on) => {
        if (!on) {
            expiringByRecipeId.value = new Map();
            return;
        }
        expiringFetchInFlight.value = true;
        try {
            const items = await recipeApi.getAllPagesAsync({
                expiring_within_days: EXPIRING_FILTER_HORIZON_DAYS,
            });
            const next = new Map<string, ExpiringFacts>();
            for (const r of items) {
                next.set(r.recipe_id, {
                    count: r.expiring_ingredient_count ?? 0,
                    soonest: r.expiring_soonest_date ?? null,
                });
            }
            expiringByRecipeId.value = next;
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
        servesMin.value = null;
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

    // overview-side URL importer. Mirrors the detail-page
    // flow (which overwrites the current recipe); here we *create* a new
    // recipe from the import preview and route into its detail page so the
    // user can finish the cleanup.
    //
    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 4/5 — every ingredient rides
    // through create now: matched ones as linked (stock_item_id set),
    // unmatched ones as unlinked (raw_text set, stock_item_id null).
    // The Chunk-6 bulk-linker page is where the user resolves the
    // unlinked ones at their leisure. Toast surfaces the count so the
    // user knows.
    const importOpen = ref(false);
    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — PWA share-target landing.
    // The manifest points `share_target.action: /cookbook` and maps
    // the OS share sheet's title/text/url into ?share_title / ?share_text
    // / ?share_url. On mount we lift them into the dialog's prefill
    // props and pop it. Cleared after read so a refresh doesn't
    // re-open the dialog forever.
    const sharePrefillContent = ref('');
    const sharePrefillSourceUrl = ref('');

    function onImportClick() {
        sharePrefillContent.value = '';
        sharePrefillSourceUrl.value = '';
        importOpen.value = true;
    }

    async function onRecipeImported(imported: ImportedRecipe) {
        try {
            const unmatchedCount = imported.ingredients.filter(
                (i) => !i.stock_item_id,
            ).length;

            // Map every ingredient through — Chunk 4 made both branches
            // legal at the create endpoint. Client_ids are fresh for
            // structured-step linkage.
            const ingredientPayload = imported.ingredients.map((i) => ({
                stock_item_id: i.stock_item_id,
                raw_text: i.raw_text ?? null,
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
                const matchedCount = imported.ingredients.length - unmatchedCount;
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    timeout: 5000,
                    message: `Imported "${imported.name}".`,
                    caption: unmatchedCount === 0
                        ? `${matchedCount} ingredient${matchedCount === 1 ? '' : 's'} matched.`
                        : `${matchedCount} matched · ${unmatchedCount} unlinked — link them later from the recipe.`,
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

    // Cook-mode entry, guarded the same way `RecipeDetailPage` guards it —
    // the shared predicate lives in `helpers/cookModeGuard` so the two
    // surfaces can't answer "should we ask first?" differently (R-003).
    // `dirty` is never passed: the cookbook has no editable form.
    const cookGuardOpen = ref(false);
    const cookGuardRecipe = ref<Recipe | null>(null);

    function onCookClick(recipeId: string) {
        const r = recipes.value.find((x) => x.recipe_id === recipeId) ?? null;
        if (needsCookGuard(r)) {
            cookGuardRecipe.value = r;
            cookGuardOpen.value = true;
            return;
        }
        startCookMode(recipeId);
    }

    /** Navigate in. Called directly on a clean entry, or by the guard's
     *  "Start anyway", which has no recipe id of its own to hand back. */
    function startCookMode(recipeId?: string) {
        const id = recipeId ?? cookGuardRecipe.value?.recipe_id;
        if (!id) return;
        cookGuardOpen.value = false;
        void router.push(`/cookbook/${id}/cook`);
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

    // the modal is a stub-creator. On create,
    // close and navigate straight to the detail page so the user can
    // flesh the recipe out (ingredients, steps, image, times, tags)
    // without hunting the list. On update (rename/reclassify from
    // the overview), just refresh the grid.
    async function onRecipeCreated(recipeId: string) {
        editDialogOpen.value = false;
        await router.push(`/cookbook/${recipeId}`);
    }

    async function onRecipeUpdated() {
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
                recipeStore.ensureLoadedAsync(),
                recipeStore.ensureCollectionsLoadedAsync(),
                stockItemStore.ensureLoadedAsync(),
                shoppingListStore.ensureLoadedAsync(),
                // `is_planned` is now server-derived (RecipeDto
                // field), so this page no longer needs to fetch meal plans
                // for the "Planned" filter. The store hydration is left to
                // other surfaces that genuinely need it.
                // vocabularies for the cuisine/category/dietary
                // filters (sourced from the editable settings tables).
                recipeVocabStore.ensureLoadedAsync(),
                // household meal-slot vocabulary for the time-of-day filter.
                mealSlotStore.ensureLoadedAsync(),
                // Disclaimer text for the dietary filter. Errors non-fatal.
                recipeApi.getTagCatalogueAsync()
                    .then((c) => { tagCatalogue.value = c; })
                    .catch(() => { tagCatalogue.value = null; }),
            ]);
        } finally {
            loading.value = false;
        }
        applyQuery();
        // IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — PWA share target landed
        // us here with the OS-share payload in the query string. Lift
        // the text / URL into the dialog's prefill, pop it, and strip
        // the params so a subsequent refresh doesn't re-open.
        const shareText = (route.query.share_text ?? '').toString();
        const shareTitle = (route.query.share_title ?? '').toString();
        const shareUrl = (route.query.share_url ?? '').toString();
        if (shareText || shareUrl) {
            sharePrefillContent.value = shareText || shareTitle;
            sharePrefillSourceUrl.value = shareUrl;
            importOpen.value = true;
            const cleaned = { ...route.query };
            delete cleaned.share_text;
            delete cleaned.share_title;
            delete cleaned.share_url;
            void router.replace({ path: route.path, query: cleaned });
        }
    });
</script>

<style scoped>
    .full-height {
        height: 100%;
    }
    /* ── Toolbar (2026-08-17 feedback) ────────────────────────────────
       Lifted wholesale from `StockOverview.vue` so both list surfaces
       behave identically: desktop = one row (actions left, filter-toggle
       + search right); phones = icon-only actions with `__find` wrapping
       to a full-width second line. `flex-basis: 100%` forces that wrap;
       `q-space.gt-xs` is hidden there so nothing pushes against it. */
    .recipes-toolbar {
        margin-bottom: var(--space-4);
    }
    .recipes-toolbar__find {
        flex: 1 1 auto;
        min-width: 280px;
    }
    @media (max-width: 599px) {
        .recipes-toolbar__find {
            flex-basis: 100%;
            min-width: 0;
        }
    }

    /* Separation between the filter panel and the list — see the
       template note above the wrapper. Matches the gap StockOverview gets
       incidentally from its bulk-bar wrapper. */
    .recipes-content {
        margin-top: var(--space-3);
    }

    /* The filter rows' scroll behaviour and control scale moved to
       `components/filters/FilterRow.vue` (2026-08-19). Both this page and
       StockOverview had grown a copy of the same ~40 lines, which is how they
       drifted to different control heights; the tri-state dropdown overrides
       that used to live here are gone entirely now that TriStateFilter renders
       a real field (see `BaseFilterField`). Only per-control track opt-outs
       remain, and those are `filter-row__wide` / `filter-row__auto` classes
       applied at the call site. */
</style>
