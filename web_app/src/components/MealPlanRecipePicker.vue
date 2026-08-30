<template>
    <q-card flat bordered class="meal-plan-recipe-picker">
        <q-card-section class="q-pb-xs">
            <!-- S3 — targeting. The destination is named at BOTH ends (here and
                 on the slot itself): at 1280px+ the rail and the targeted day
                 are far apart, and naming both ends is the reliable version of
                 drawing a connector between them.
                 `role="status"` makes it a live region, so arming a slot is
                 *announced*, not only drawn — the pulse is visual-only and this
                 is its screen-reader equivalent. -->
            <q-banner
                v-if="focusedTarget"
                dense
                role="status"
                class="picker-target q-mb-sm rounded-borders"
            >
                <div class="text-caption">
                    Adding to <strong>{{ focusedTarget.slot }}</strong>,
                    {{ formatDate(focusedTarget.dayIso) }} — pick a recipe.
                </div>
                <template #action>
                    <BaseButton variant="ghost" dense label="Cancel" @click="emit('cancelTarget')" />
                </template>
            </q-banner>

            <!-- L99 — "keep search filter separate to other filters". The search
                 box sits ABOVE the chips and narrows whatever the active chip
                 produced, rather than being one of them. -->
            <q-input
                ref="searchRef"
                :model-value="recipeSearch"
                dense
                outlined
                clearable
                :debounce="150"
                placeholder="Search recipes"
                @update:model-value="(v) => emit('update:recipeSearch', (v ?? '') as string)"
            >
                <template #prepend><q-icon :name="ICONS.search" /></template>
            </q-input>

            <MealPlanRailFilterChips
                class="q-mt-sm"
                :chips="chips"
                :selected="activeFilter"
                @update:selected="onFilterChange"
            />
        </q-card-section>
        <q-separator />

        <div class="recipe-list">
            <!-- F21 — one flat filtered list, where the trays capped their
                 shortcuts at 10 and hid what didn't fit behind an accordion.
                 Above the threshold this virtualises: the item size and the CSS
                 row height MUST agree exactly or Quasar re-measures mid-scroll
                 (the trap `StockOverview` documents at its own switch). -->
            <q-virtual-scroll
                v-if="visibleRecipes.length > VIRTUAL_SCROLL_THRESHOLD"
                :items="visibleRecipes"
                :virtual-scroll-item-size="VIRTUAL_ROW_HEIGHT_PX"
                separator
            >
                <template #default="{ item }">
                    <div :key="item.recipe_id" class="recipe-list__slot">
                        <q-checkbox
                            v-if="isMultiSelect"
                            :model-value="isSelected(item.recipe_id)"
                            @update:model-value="toggleSelection(item.recipe_id)"
                        />
                        <MealPlanRecipeRow
                            :recipe="item"
                            :mode="rowMode"
                            :target-slot="focusedTarget?.slot"
                            :reason-text="reasonFor(item.recipe_id)"
                            :batch-enabled="batchEnabled && !isMultiSelect"
                            @pick="onRowPick"
                            @pool-adjust="(id, delta) => emit('paletteMealAdjust', id, delta)"
                            @log-cook="openPaletteLogCook"
                        />
                    </div>
                </template>
            </q-virtual-scroll>

            <template v-else>
                <div
                    v-for="recipe in visibleRecipes"
                    :key="recipe.recipe_id"
                    class="recipe-list__slot"
                >
                    <q-checkbox
                        v-if="isMultiSelect"
                        :model-value="isSelected(recipe.recipe_id)"
                        @update:model-value="toggleSelection(recipe.recipe_id)"
                    />
                    <MealPlanRecipeRow
                        :recipe="recipe"
                        :mode="rowMode"
                        :target-slot="focusedTarget?.slot"
                        :reason-text="reasonFor(recipe.recipe_id)"
                        :batch-enabled="batchEnabled && !isMultiSelect"
                        @pick="onRowPick"
                        @pool-adjust="(id, delta) => emit('paletteMealAdjust', id, delta)"
                        @log-cook="openPaletteLogCook"
                    />
                </div>
            </template>

            <div v-if="recipes.length === 0" class="dora-text-muted text-center q-py-md">
                No recipes yet — create some in the Cookbook.
            </div>
            <div
                v-else-if="visibleRecipes.length === 0"
                class="dora-text-muted text-center q-py-md"
            >
                {{ emptyMessage }}
            </div>
        </div>

        <!-- Log cook from a recipe row ─────────────────────────────── -->
        <BaseDialog v-model="logCookOpen" title="Log a cook" closable card-style="min-width: 320px">
            <q-card-section class="q-pt-none">
                <q-input
                    v-model.number="logCookCount"
                    type="number"
                    min="1"
                    max="999"
                    outlined
                    dense
                    autofocus
                    label="Meals cooked"
                    hint="Adds to the recipe's pool."
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Log"
                    :loading="logging"
                    :disable="!(logCookCount > 0)"
                    @click="confirmLogCook"
                />
            </template>
        </BaseDialog>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanRailFilterChips from 'src/components/MealPlanRailFilterChips.vue';
    import MealPlanRecipeRow from 'src/components/MealPlanRecipeRow.vue';
    import { useQuasar } from 'quasar';
    import type { Recipe } from 'src/models/recipe';
    import type { MealPlanSuggestion } from 'src/models/mealPlan';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import {
        buildFilterChips, filterRecipes, type RecipeFilterKey,
    } from 'src/helpers/recipeRailFilters';
    import { suggestionReasonText } from 'src/helpers/mealPlanSuggestionCopy';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { computed, onMounted, ref, watch } from 'vue';

    const { batchEnabled } = useBatchEnabled();

    /** Above this many rows the list virtualises. Matches the threshold
     *  `StockOverview` uses, so the two long lists in the app behave the same. */
    const VIRTUAL_SCROLL_THRESHOLD = 50;
    /** Must equal the rendered row height (`.recipe-list__slot` min-height), or
     *  Quasar re-measures mid-scroll and the list judders. */
    const VIRTUAL_ROW_HEIGHT_PX = 64;

    const props = withDefaults(
        defineProps<{
            recipeSearch: string;
            recipes: Recipe[];
            focusedTarget: { dayIso: string; slot: string } | null;
            formatDate: (iso: string) => string;
            logCook: (recipeId: string, count: number) => Promise<number>;
            /** Server-ranked suggestions for the focused week (§4.4). Empty
             *  until loaded; the "Dora suggests" chip shows the plain list
             *  meanwhile rather than an empty rail. */
            suggestions?: MealPlanSuggestion[] | undefined;
            /** When set to 'multi-select', rows show a checkbox and click
             *  toggles selection (used by the sequential builder, §9-B).
             *  Default 'click-add' is the original behaviour — click a row
             *  to add the recipe to the focused day/slot. */
            selectionMode?: 'click-add' | 'multi-select' | undefined;
            /** Selected recipe ids in 'multi-select' mode. Ignored otherwise. */
            selectedIds?: string[] | undefined;
        }>(),
        { selectionMode: 'click-add', selectedIds: () => [], suggestions: () => [] },
    );

    const emit = defineEmits<{
        (e: 'update:recipeSearch', value: string): void;
        (e: 'update:selectedIds', ids: string[]): void;
        (e: 'cancelTarget'): void;
        (e: 'recipePick', recipeId: string): void;
        (e: 'paletteMealAdjust', recipeId: string, delta: number): void;
        /** Raised when the user selects the "Dora suggests" chip, so the host
         *  can fetch the ranking lazily rather than on every page load. */
        (e: 'suggestionsRequested'): void;
    }>();

    // ── Filter chips ───────────────────────────────────────────────────────
    const activeFilter = ref<RecipeFilterKey>('all');
    const chips = computed(() => buildFilterChips(props.recipes));

    function onFilterChange(key: RecipeFilterKey) {
        activeFilter.value = key;
        if (key === 'suggests') emit('suggestionsRequested');
    }

    const reasonByRecipeId = computed(
        () => new Map(props.suggestions.map((s) => [s.recipe_id, s.reason_chip])),
    );

    /**
     * The rows on screen. Every chip but `suggests` is a predicate over the
     * cookbook; `suggests` instead takes the server's ranked id list and
     * preserves ITS order, because the ranking is the whole value — re-sorting
     * it by name would throw away what was computed.
     */
    const visibleRecipes = computed<Recipe[]>(() => {
        if (activeFilter.value !== 'suggests') {
            return filterRecipes(props.recipes, activeFilter.value, props.recipeSearch);
        }
        if (!props.suggestions.length) {
            return filterRecipes(props.recipes, 'all', props.recipeSearch);
        }
        const byId = new Map(props.recipes.map((r) => [r.recipe_id, r]));
        const query = props.recipeSearch.trim().toLowerCase();
        return props.suggestions
            .map((s) => byId.get(s.recipe_id))
            .filter((r): r is Recipe => !!r)
            .filter((r) => !query || r.name.toLowerCase().includes(query));
    });

    const isSuggesting = computed(
        () => activeFilter.value === 'suggests' && props.suggestions.length > 0,
    );

    const rowMode = computed<'browsing' | 'targeting' | 'suggesting'>(() => {
        if (props.focusedTarget) return 'targeting';
        return isSuggesting.value ? 'suggesting' : 'browsing';
    });

    function reasonFor(recipeId: string): string {
        if (!isSuggesting.value) return '';
        const chip = reasonByRecipeId.value.get(recipeId);
        return chip ? suggestionReasonText(chip) : '';
    }

    const emptyMessage = computed(() => {
        if (props.recipeSearch.trim()) return 'No matches.';
        if (activeFilter.value === 'suggests') return 'Nothing to suggest for this week.';
        return 'Nothing here yet.';
    });

    // ── Selection ──────────────────────────────────────────────────────────
    const isMultiSelect = computed(() => props.selectionMode === 'multi-select');
    function isSelected(recipeId: string): boolean {
        return props.selectedIds.includes(recipeId);
    }
    function toggleSelection(recipeId: string) {
        const next = isSelected(recipeId)
            ? props.selectedIds.filter((id) => id !== recipeId)
            : [...props.selectedIds, recipeId];
        emit('update:selectedIds', next);
    }
    /** In multi-select the whole row is a selection toggle; in click-add it
     *  adds to the armed slot. One row component, two host contracts. */
    function onRowPick(recipeId: string) {
        if (isMultiSelect.value) toggleSelection(recipeId);
        else emit('recipePick', recipeId);
    }

    // ── Focus on arming (§4.6) ─────────────────────────────────────────────
    //
    // "Focus moves into the rail's search on auto-open. Not optional: the pulse
    // is visual-only, and moving focus is its keyboard equivalent."
    //
    // The picker focuses ITSELF rather than exposing a method for the page to
    // call. The page's version didn't work: it set `railOpen` and then reached
    // for the child through a template ref, but the child mounts as a result of
    // that very state change, so the ref was still null when the call was made
    // — and measured in the browser, focus never moved at 300ms OR at 1500ms.
    // Owning it here means `onMounted` runs when this component's own DOM
    // exists, which is exactly the guarantee that was missing.
    //
    // Two entry points, because the rail may be either closed or already open:
    // mounting with a target set (the rail just opened for it), and a target
    // arriving/changing while mounted (you re-armed a different slot).
    const searchRef = ref<{ focus: () => void } | null>(null);

    function focusSearch() {
        searchRef.value?.focus();
    }

    onMounted(() => {
        if (props.focusedTarget) focusSearch();
    });
    watch(() => props.focusedTarget, (target) => {
        if (target) focusSearch();
    });

    const $q = useQuasar();
    const logCookOpen = ref(false);
    const logCookCount = ref<number>(1);
    const logCookRecipeId = ref<string | null>(null);
    const logging = ref(false);

    function openPaletteLogCook(recipeId: string) {
        logCookRecipeId.value = recipeId;
        logCookCount.value = 1;
        logCookOpen.value = true;
    }
    async function confirmLogCook() {
        if (!logCookRecipeId.value) return;
        logging.value = true;
        try {
            const n = await props.logCook(logCookRecipeId.value, logCookCount.value);
            logCookOpen.value = false;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Logged ${n} cooked meal${n === 1 ? '' : 's'}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log cook.',
                caption: toastCaption(err),
            });
        } finally {
            logging.value = false;
        }
    }
</script>

<style scoped>
    /* The card fills whatever height its host gives it and hands the scroll to
       the recipe list, so the search box, the chips and the "adding to…" target
       banner stay pinned while the recipes move under them.
       Before Unit 1 this was `max-height: 65vh` — a viewport formula that knew
       nothing about the page chrome above it. Inside the planner's fixed-height
       shell the pane is already correctly sized, so measuring the viewport a
       second time would reintroduce exactly the overhang R-036 forbids. The
       three other hosts (mobile picker sheet, builder dialog) size this card
       themselves too. */
    .meal-plan-recipe-picker {
        display: flex;
        flex-direction: column;
        min-height: 0;
    }
    .recipe-list {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        padding: var(--space-2);
        /* Reserve the gutter so row width doesn't jump as searching crosses the
           list from non-scrolling to scrolling. */
        scrollbar-gutter: stable;
    }
    /* Wraps each row so multi-select can put a checkbox beside it without the
       row component knowing anything about selection. The min-height must match
       `VIRTUAL_ROW_HEIGHT_PX`. */
    .recipe-list__slot {
        display: flex;
        align-items: center;
        gap: var(--space-1);
        min-height: 64px;
    }
    .recipe-list__slot > :last-child {
        flex: 1 1 auto;
        min-width: 0;
    }

    /* S3 — the target banner is a FILLED accent surface, not a sunken one. It
       was `dora-bg-sunken`, which reads as an inert panel; this is the durable
       signal that the rail is armed, and it has to survive `prefers-reduced-
       motion` flattening every animation to 0.01ms (§4.7). */
    .picker-target {
        background: color-mix(in srgb, var(--brand-primary) 14%, var(--surface-component));
        border-left: 3px solid var(--brand-primary);
    }
</style>
