<template>
    <div class="q-pa-md">
        <div class="row q-col-gutter-md">
            <!-- ── Left: recipe list ──────────────────────────────────── -->
            <div class="col-12 col-md-3">
                <q-card flat bordered>
                    <q-card-section class="q-pb-xs">
                        <q-input
                            v-model="recipeSearch"
                            dense
                            outlined
                            clearable
                            :debounce="150"
                            placeholder="Search recipes"
                        >
                            <template #prepend><q-icon :name="ICONS.search" /></template>
                        </q-input>
                        <q-banner v-if="focusedTarget" dense class="dora-bg-sunken q-mt-sm rounded-borders">
                            <div class="text-caption">
                                Adding to <strong>{{ focusedTarget.slot }}</strong>,
                                {{ formatDate(focusedTarget.dayIso) }} — pick a recipe.
                            </div>
                            <template #action>
                                <q-btn flat dense no-caps label="Cancel" @click="focusedTarget = null" />
                            </template>
                        </q-banner>
                    </q-card-section>
                    <q-separator />
                    <div class="recipe-list">
                        <q-expansion-item
                            v-for="tray in trays"
                            :key="tray.key"
                            :label="tray.title"
                            :default-opened="tray.defaultOpen"
                            dense
                            header-class="text-weight-medium"
                        >
                            <q-list separator>
                                <q-item
                                    v-for="recipe in tray.recipes"
                                    :key="tray.key + recipe.recipe_id"
                                    class="recipe-row"
                                    :draggable="dragAllowed"
                                    @pointerdown="onRecipePointerDown"
                                    @dragstart="onDragStart(recipe.recipe_id)"
                                    @dragend="draggingRecipeId = null"
                                >
                                    <q-item-section class="cursor-pointer" @click="pickRecipe(recipe.recipe_id)">
                                        <q-item-label lines="2">{{ recipe.name }}</q-item-label>
                                        <q-item-label caption>{{ recipe.unallocated_meals }} free</q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <div class="row items-center no-wrap">
                                            <q-btn
                                                dense round flat size="sm"
                                                :icon="ICONS.remove"
                                                :disable="recipe.available_meals <= 0"
                                                @click="adjustPaletteMeals(recipe.recipe_id, -1)"
                                            >
                                                <q-tooltip>One fewer cooked</q-tooltip>
                                            </q-btn>
                                            <span class="recipe-row__pool">{{ recipe.available_meals }}</span>
                                            <q-btn
                                                dense round flat size="sm"
                                                :icon="ICONS.add"
                                                @click="adjustPaletteMeals(recipe.recipe_id, 1)"
                                            >
                                                <q-tooltip>One more cooked</q-tooltip>
                                            </q-btn>
                                            <q-btn
                                                dense round flat size="sm"
                                                :icon="ICONS.restaurant"
                                                @click="openPaletteLogCook(recipe.recipe_id)"
                                            >
                                                <q-tooltip>Log a cook…</q-tooltip>
                                            </q-btn>
                                        </div>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-expansion-item>
                        <div v-if="recipes.length === 0" class="dora-text-muted text-center q-py-md">
                            No recipes yet — create some in the Cookbook.
                        </div>
                        <div
                            v-else-if="trays.length === 1 && trays[0]?.recipes.length === 0"
                            class="dora-text-muted text-center q-py-md"
                        >
                            No matches.
                        </div>
                    </div>
                </q-card>
            </div>

            <!-- ── Main: vertical week carousel ───────────────────────── -->
            <div class="col-12 col-md-6">
                <div class="row items-center q-mb-xs">
                    <q-btn flat round dense :icon="ICONS.arrow_upward" @click="goPrevWeek">
                        <q-tooltip>Previous week</q-tooltip>
                    </q-btn>
                    <div class="text-subtitle2 q-ml-sm">{{ weekRangeLabel }}</div>
                    <q-space />
                    <q-btn
                        v-if="focusedPlan"
                        flat dense round
                        :icon="ICONS.print"
                        @click="planExport.openPrintView(focusedPlan.meal_plan_id)"
                    >
                        <q-tooltip>Print this week</q-tooltip>
                    </q-btn>
                    <q-btn
                        v-if="focusedPlan"
                        flat dense round
                        :icon="ICONS.delete"
                        @click="confirmClearWeek"
                    >
                        <q-tooltip>Clear this week</q-tooltip>
                    </q-btn>
                </div>

                <transition :name="weekTransition" mode="out-in">
                    <div
                        :key="focusedMonday"
                        @touchstart.passive="onTouchStart"
                        @touchend.passive="onTouchEnd"
                    >
                        <q-card
                            v-for="day in weekDays"
                            :key="day.iso"
                            bordered
                            class="day-card q-mb-sm"
                            :class="{ 'day-card--past': isPastDay(day.iso) }"
                        >
                            <q-card-section class="dora-bg-sunken q-py-xs row items-center">
                                <div class="text-weight-bold">{{ day.label }}</div>
                                <div class="text-caption q-ml-sm dora-text-muted">{{ formatDate(day.iso) }}</div>
                                <q-badge v-if="day.iso === currentDayIso" color="primary" class="q-ml-sm" label="Today" />
                            </q-card-section>
                            <q-card-section class="q-pa-sm column q-gutter-xs">
                                <div
                                    v-for="slot in slotNames"
                                    :key="slot"
                                    class="slot-row"
                                    :class="{
                                        'slot-row--target': isTargeted(day.iso, slot),
                                        'slot-row--clickable': !isPastDay(day.iso),
                                    }"
                                    @click="selectSlot(day.iso, slot)"
                                    @dragover.prevent
                                    @drop.stop="onDropOnSlot(day.iso, slot)"
                                >
                                    <div class="slot-row__label">{{ slot }}</div>
                                    <div class="slot-row__entries">
                                        <MealPlanEntryChip
                                            v-for="entry in slotEntries(day.iso, slot)"
                                            :key="entry.meal_plan_entry_id"
                                            :entry="entry"
                                            :show-slot="false"
                                            :shortfall="isShortfallEntry(entry)"
                                            :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                                            @click.stop
                                            @view="goToRecipe(entry.recipe_id)"
                                            @cook="cookRecipe(entry.recipe_id)"
                                            @remove="removeEntry(entry)"
                                            @adjust="(d: number) => adjustEntryServings(entry, d)"
                                        />
                                        <span
                                            v-if="!slotEntries(day.iso, slot).length && !isPastDay(day.iso)"
                                            class="slot-row__hint"
                                        >
                                            {{ isTargeted(day.iso, slot) ? 'pick a recipe →' : 'tap to add' }}
                                        </span>
                                    </div>
                                </div>

                                <!-- Off-vocabulary historical slots land here (C-2.A). -->
                                <div v-if="otherSlotEntries(day.iso).length" class="slot-row">
                                    <div class="slot-row__label">Other</div>
                                    <div class="slot-row__entries">
                                        <MealPlanEntryChip
                                            v-for="entry in otherSlotEntries(day.iso)"
                                            :key="entry.meal_plan_entry_id"
                                            :entry="entry"
                                            :show-slot="true"
                                            :shortfall="isShortfallEntry(entry)"
                                            :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                                            @click.stop
                                            @view="goToRecipe(entry.recipe_id)"
                                            @cook="cookRecipe(entry.recipe_id)"
                                            @remove="removeEntry(entry)"
                                            @adjust="(d: number) => adjustEntryServings(entry, d)"
                                        />
                                    </div>
                                </div>
                            </q-card-section>
                        </q-card>
                    </div>
                </transition>

                <div class="row items-center justify-center q-mt-xs">
                    <q-btn flat round dense :icon="ICONS.arrow_downward" @click="goNextWeek">
                        <q-tooltip>Next week</q-tooltip>
                    </q-btn>
                </div>
            </div>

            <!-- ── Right: calendar + shopping summary ─────────────────── -->
            <div class="col-12 col-md-3">
                <MealPlanCalendar v-model:focused-monday="focusedMonday" class="q-mb-sm" />

                <q-card flat bordered>
                    <q-card-section class="q-pb-xs">
                        <div class="text-subtitle1">This week's shopping</div>
                        <template v-if="focusedPlan">
                            <div v-if="ingredientsLoading" class="text-caption dora-text-muted">Calculating…</div>
                            <div v-else class="text-h5" :class="needToBuy.length ? 'text-negative' : 'text-positive'">
                                {{ needToBuy.length }}
                            </div>
                            <div class="text-caption dora-text-muted">
                                {{ needToBuy.length ? "item(s) you'll need to buy" : 'fully stocked for this week' }}
                            </div>
                            <div v-if="shortfall.length" class="row items-center q-mt-sm text-warning">
                                <q-icon :name="ICONS.chef_hat" class="q-mr-xs" />
                                <span class="text-subtitle2">{{ cookByLabel }}</span>
                            </div>
                        </template>
                        <div v-else class="text-caption dora-text-muted q-py-sm">
                            No meals planned for this week yet — tap a day's slot, then a recipe.
                        </div>
                    </q-card-section>

                    <q-list v-if="focusedPlan && needToBuy.length" dense separator>
                        <q-item
                            v-for="ing in needToBuy"
                            :key="ing.stock_item_id"
                            @mouseenter="hoverIngredient(ing)"
                            @mouseleave="clearHover"
                        >
                            <q-item-section>
                                <q-item-label>{{ ing.stock_item_name }}</q-item-label>
                                <q-item-label caption>
                                    <span v-if="ing.total_quantity !== null">
                                        needs {{ ing.total_quantity }} {{ ing.unit ?? '' }} ·
                                    </span>
                                    {{ listStatusLabel(ing.stock_item_id) }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <div class="row items-center no-wrap q-gutter-xs">
                                    <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
                                        {{ stockStatusLabel(ing.stock_item_id) }}
                                    </q-chip>
                                    <AddToListButton variant="row" :stock-item-id="ing.stock_item_id" />
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>

                    <q-card-actions v-if="focusedPlan">
                        <q-btn
                            color="primary"
                            no-caps
                            class="full-width"
                            :icon="ICONS.shopping_cart"
                            label="Generate shopping list for this week"
                            :loading="generating"
                            :disable="needToBuy.length === 0"
                            @click="generateListForWeek"
                        />
                    </q-card-actions>
                </q-card>

                <q-expansion-item
                    v-if="focusedPlan && ingredients.length"
                    :icon="ICONS.receipt_long"
                    label="Full ingredient demand"
                    class="q-mt-sm"
                >
                    <q-list dense separator>
                        <q-item v-for="ing in ingredients" :key="ing.stock_item_id">
                            <q-item-section>{{ ing.stock_item_name }}</q-item-section>
                            <q-item-section side>
                                <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
                                    {{ stockStatusLabel(ing.stock_item_id) }}
                                </q-chip>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-expansion-item>
            </div>
        </div>

        <!-- Log cook from a recipe row ─────────────────────────────── -->
        <BaseDialog v-model="paletteLogCookOpen" title="Log a cook" closable card-style="min-width: 320px">
                <q-card-section class="q-pt-none">
                    <q-input
                        v-model.number="paletteLogCookCount"
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
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        color="primary"
                        no-caps
                        label="Log"
                        :loading="paletteLogging"
                        :disable="!(paletteLogCookCount > 0)"
                        @click="confirmPaletteLogCook"
                    />
                </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanCalendar from 'components/MealPlanCalendar.vue';
    import MealPlanEntryChip from 'components/MealPlanEntryChip.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useMealPlanExport } from 'src/composables/useMealPlanExport';
    import { DEFAULT_MEAL_SLOTS } from 'src/helpers/recipeVocabulary';
    import { isoDate as toIso, localTodayIso, mondayOf, shiftDays } from 'src/helpers/weekDates';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import { needsRestockSequence } from 'src/helpers/stockStatus';
    import type { MealPlan, MealPlanEntry, MealPlanIngredient } from 'src/models/mealPlan';
    import type { Recipe } from 'src/models/recipe';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const planExport = useMealPlanExport();
    const mealPlanStore = useMealPlanStore();
    const mealSlotStore = useMealSlotStore();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

    const { mealPlans, shortfall, today } = storeToRefs(mealPlanStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);
    const { recipes } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const ingredients = ref<MealPlanIngredient[]>([]);
    const ingredientsLoading = ref(false);
    const draggingRecipeId = ref<string | null>(null);
    const generating = ref(false);
    const recipeSearch = ref('');

    const currentDayIso = computed(() => today.value ?? localTodayIso());
    function isPastDay(iso: string): boolean {
        return iso < currentDayIso.value;
    }

    // ── Focused week (the carousel's source of truth) ──────────────────────
    const focusedMonday = ref<string>(mondayOf(localTodayIso()));
    const focusedPlan = computed<MealPlan | null>(
        () => mealPlans.value.find((p) => mondayOf(p.start_date) === focusedMonday.value) ?? null,
    );
    const weekDays = computed(() => {
        const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return labels.map((label, i) => ({ label, iso: shiftDays(focusedMonday.value, i) }));
    });
    const weekRangeLabel = computed(
        () => `${formatDate(focusedMonday.value)} – ${formatDate(shiftDays(focusedMonday.value, 6))}`,
    );

    // ── Slots (household vocabulary, C-2.A) ────────────────────────────────
    const slotNames = computed(() =>
        mealSlotNames.value.length ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );
    const slotNameSet = computed(() => new Set(slotNames.value));

    function dayEntries(dayIso: string): MealPlanEntry[] {
        return (focusedPlan.value?.entries ?? []).filter((e) => toIso(e.scheduled_for) === dayIso);
    }
    function slotEntries(dayIso: string, slot: string): MealPlanEntry[] {
        return dayEntries(dayIso).filter((e) => e.slot === slot);
    }
    function otherSlotEntries(dayIso: string): MealPlanEntry[] {
        return dayEntries(dayIso).filter((e) => !slotNameSet.value.has(e.slot));
    }

    const shortfallRecipeIds = computed(() => new Set(shortfall.value.map((s) => s.recipe_id)));
    function isShortfallEntry(entry: MealPlanEntry): boolean {
        return shortfallRecipeIds.value.has(entry.recipe_id);
    }

    // Moved shortfall summary (the page-top banner is gone): one sidebar line,
    // chef-hat not warning-triangle. Deadline = earliest `earliest_needed`.
    const cookByLabel = computed(() => {
        const dates = shortfall.value
            .map((s) => s.earliest_needed)
            .filter((d): d is string => !!d);
        const earliest = dates.length ? dates.reduce((a, b) => (a < b ? a : b)) : null;
        return `${shortfall.value.length} to cook${earliest ? ` by ${formatDate(earliest)}` : ''}`;
    });

    // ── Left-column recipe list ────────────────────────────────────────────
    const filteredRecipes = computed(() => {
        const q = recipeSearch.value?.trim().toLowerCase() ?? '';
        if (!q) return recipes.value;
        return recipes.value.filter((r) => r.name.toLowerCase().includes(q));
    });

    // Left-column trays (C-2.I). While searching, just the results; otherwise
    // the curated trays (server-derived: is_favourite / not_made_recently /
    // plan_count, R-003) above the full list. Curated trays cap at 10 and are
    // hidden when empty.
    type Tray = { key: string; title: string; recipes: Recipe[]; defaultOpen: boolean };
    const TRAY_CAP = 10;
    const trays = computed<Tray[]>(() => {
        if (recipeSearch.value?.trim()) {
            return [{ key: 'results', title: `Results (${filteredRecipes.value.length})`, recipes: filteredRecipes.value, defaultOpen: true }];
        }
        const all = recipes.value;
        const out: Tray[] = [];
        const favs = all.filter((r) => r.is_favourite);
        if (favs.length) out.push({ key: 'fav', title: 'Favourites', recipes: favs, defaultOpen: true });
        const stale = all
            .filter((r) => r.not_made_recently)
            .sort((a, b) => madeMs(a) - madeMs(b)) // never-made + oldest first
            .slice(0, TRAY_CAP);
        if (stale.length) out.push({ key: 'stale', title: "Haven't had in a while", recipes: stale, defaultOpen: false });
        const freq = all
            .filter((r) => r.plan_count > 0)
            .sort((a, b) => b.plan_count - a.plan_count)
            .slice(0, TRAY_CAP);
        if (freq.length) out.push({ key: 'freq', title: 'Frequently planned', recipes: freq, defaultOpen: false });
        out.push({ key: 'all', title: `All recipes (${all.length})`, recipes: all, defaultOpen: true });
        return out;
    });
    function madeMs(r: Recipe): number {
        return r.last_made_on ? new Date(r.last_made_on).getTime() : 0;
    }

    // ── Tap-to-add: focus a slot, then pick a recipe ───────────────────────
    const focusedTarget = ref<{ dayIso: string; slot: string } | null>(null);
    function isTargeted(dayIso: string, slot: string): boolean {
        return focusedTarget.value?.dayIso === dayIso && focusedTarget.value?.slot === slot;
    }
    function selectSlot(dayIso: string, slot: string) {
        if (isPastDay(dayIso)) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Past days are read-only.' });
            return;
        }
        focusedTarget.value = isTargeted(dayIso, slot) ? null : { dayIso, slot };
    }
    async function pickRecipe(recipeId: string) {
        if (!focusedTarget.value) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: "Tap a day's meal slot first, then a recipe.",
            });
            return;
        }
        await addEntry(focusedTarget.value.dayIso, focusedTarget.value.slot, recipeId);
    }

    // ── Drag-to-add (desktop pointer only) ─────────────────────────────────
    const dragAllowed = ref(true);
    function onRecipePointerDown(e: PointerEvent) {
        dragAllowed.value = e.pointerType === 'mouse';
    }
    function onDragStart(recipeId: string) {
        draggingRecipeId.value = recipeId;
    }
    async function onDropOnSlot(dayIso: string, slot: string) {
        const recipeId = draggingRecipeId.value;
        draggingRecipeId.value = null;
        if (!recipeId) return;
        if (isPastDay(dayIso)) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Past days are read-only.' });
            return;
        }
        await addEntry(dayIso, slot, recipeId);
    }

    // ── Entry mutations ────────────────────────────────────────────────────
    function planEntryCommands(plan: MealPlan): MealPlanEntryCommand[] {
        return plan.entries
            .filter((e) => !e.consumed_at)
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
    }

    async function refreshAfterMutation() {
        await Promise.all([
            loadIngredients(),
            mealPlanStore.getShortfallAsync(),
            recipeStore.getRecipesAsync(),
        ]);
    }

    async function persistEntries(planId: string, entries: MealPlanEntryCommand[]) {
        // The planner's edits are explicit, so set the clear flag when an
        // action empties the future-entries list. The backend treats an
        // unflagged [] as a probable bug and refuses.
        await mealPlanStore.updateMealPlanAsync({
            meal_plan_id: planId,
            entries,
            ...(entries.length === 0 ? { confirm_clear_entries: true } : {}),
        });
        await refreshAfterMutation();
    }

    async function addEntry(dayIso: string, slot: string, recipeId: string) {
        if (isPastDay(dayIso)) return;
        // Bridge until C-2.E: the first add to an unplanned week implicitly
        // creates the plan (auto-named) carrying that entry.
        if (!focusedPlan.value) {
            await mealPlanStore.createMealPlanAsync({
                start_date: focusedMonday.value,
                entries: [{ recipe_id: recipeId, scheduled_for: dayIso, servings: 1, slot }],
            });
            await refreshAfterMutation();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
            return;
        }
        const plan = focusedPlan.value;
        const cmds = planEntryCommands(plan);
        const existing = cmds.find(
            (c) => c.recipe_id === recipeId && c.scheduled_for === dayIso && c.slot === slot,
        );
        if (existing) {
            existing.servings += 1; // same recipe + day + slot increments, not duplicates
        } else {
            cmds.push({ recipe_id: recipeId, scheduled_for: dayIso, servings: 1, slot });
        }
        await persistEntries(plan.meal_plan_id, cmds);
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
    }

    async function adjustEntryServings(entry: MealPlanEntry, delta: number) {
        const plan = focusedPlan.value;
        if (!plan) return;
        const next = entry.servings + delta;
        const cmds = plan.entries
            .filter((e) => !e.consumed_at)
            .filter((e) => !(e.meal_plan_entry_id === entry.meal_plan_entry_id && next < 1))
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.meal_plan_entry_id === entry.meal_plan_entry_id ? next : e.servings,
                slot: e.slot,
            }));
        await persistEntries(plan.meal_plan_id, cmds);
    }

    async function removeEntry(entry: MealPlanEntry) {
        const plan = focusedPlan.value;
        if (!plan) return;
        const remaining = plan.entries
            .filter((e) => e.meal_plan_entry_id !== entry.meal_plan_entry_id && !e.consumed_at)
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
        await persistEntries(plan.meal_plan_id, remaining);
    }

    // ── Week navigation (carousel) ─────────────────────────────────────────
    const slideDir = ref<'up' | 'down'>('down');
    const reducedMotion = ref(false);
    const weekTransition = computed(() =>
        reducedMotion.value ? '' : slideDir.value === 'down' ? 'wk-down' : 'wk-up',
    );
    function goPrevWeek() {
        focusedMonday.value = shiftDays(focusedMonday.value, -7);
    }
    function goNextWeek() {
        focusedMonday.value = shiftDays(focusedMonday.value, 7);
    }
    // Any focus change — arrows, ↑/↓ keys, swipe, or a calendar-widget click —
    // sets the slide direction, clears the pending add-target, and tracks the
    // focused week in the URL (F28 refresh-resume).
    watch(focusedMonday, (next, prev) => {
        slideDir.value = next >= prev ? 'down' : 'up';
        focusedTarget.value = null;
        void router.replace({ query: { ...route.query, monday: next } });
    });
    function onKeydown(e: KeyboardEvent) {
        const t = e.target as HTMLElement | null;
        if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
        if (e.key === 'ArrowUp') { e.preventDefault(); goPrevWeek(); }
        else if (e.key === 'ArrowDown') { e.preventDefault(); goNextWeek(); }
    }
    let touchStartY = 0;
    function onTouchStart(e: TouchEvent) { touchStartY = e.changedTouches[0]?.clientY ?? 0; }
    function onTouchEnd(e: TouchEvent) {
        const dy = (e.changedTouches[0]?.clientY ?? 0) - touchStartY;
        if (Math.abs(dy) < 60) return;
        if (dy > 0) goPrevWeek(); else goNextWeek();
    }

    // ── Stock status ───────────────────────────────────────────────────────
    // Resolves by sequence (§3.1 contract) — renaming a level row in the UI
    // doesn't shift which bucket a stock item lands in.
    const stockItemById = computed(() => {
        const map = new Map<string, typeof stockItems.value[number]>();
        stockItems.value.forEach((s) => map.set(s.stock_item_id, s));
        return map;
    });
    function levelSequenceForItem(stockItemId: string): number | null {
        const item = stockItemById.value.get(stockItemId);
        if (!item) return null;
        if (typeof item.stock_level_sequence === 'number') return item.stock_level_sequence;
        return stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)?.sequence ?? null;
    }
    function stockStatusLabel(stockItemId: string): string {
        const item = stockItemById.value.get(stockItemId);
        if (!item) return 'Not tracked';
        return stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)?.name ?? 'Not tracked';
    }
    // F7 — use the app-wide sequence→colour mapping so the sidebar matches
    // every other stock-status surface (R-003: one mapping, not a local palette).
    function stockStatusColour(stockItemId: string): string {
        return colourForSequence(levelSequenceForItem(stockItemId));
    }
    const needToBuy = computed(() =>
        ingredients.value.filter((ing) => {
            const seq = levelSequenceForItem(ing.stock_item_id);
            return seq === null || needsRestockSequence(seq);
        }),
    );

    // ── Shopping-list status (F31) + hover-to-highlight (F30, C-2.H) ───────
    function listStatusLabel(stockItemId: string): string {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === stockItemId);
        if (!entry || entry.unticked_list_ids.length === 0) return 'not on a list';
        const byId = new Map(
            (m?.active_lists ?? []).map((l): [string, string] => [l.shopping_list_id, l.name]),
        );
        return `on ${entry.unticked_list_ids.map((id) => byId.get(id) ?? 'a list').join(', ')}`;
    }

    // Hovering a needed ingredient highlights the day cells whose recipes use
    // it (desktop only — mouse events don't fire on touch).
    const hoveredRecipeIds = ref<Set<string>>(new Set());
    function hoverIngredient(ing: MealPlanIngredient) {
        hoveredRecipeIds.value = new Set(ing.used_in_recipe_ids);
    }
    function clearHover() {
        hoveredRecipeIds.value = new Set();
    }

    // ── Recipe pool quick-actions (± / log cook) ───────────────────────────
    const paletteLogCookOpen = ref(false);
    const paletteLogCookCount = ref<number>(1);
    const paletteLogCookRecipeId = ref<string | null>(null);
    const paletteLogging = ref(false);

    async function adjustPaletteMeals(recipeId: string, delta: number) {
        try {
            await recipeStore.adjustMealsAsync(recipeId, delta);
            await Promise.all([recipeStore.getRecipesAsync(), mealPlanStore.getShortfallAsync()]);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update meals.',
                caption: describeApiError(err) || '',
            });
        }
    }
    function openPaletteLogCook(recipeId: string) {
        paletteLogCookRecipeId.value = recipeId;
        paletteLogCookCount.value = 1;
        paletteLogCookOpen.value = true;
    }
    async function confirmPaletteLogCook() {
        if (!paletteLogCookRecipeId.value) return;
        const n = Math.max(1, Math.floor(paletteLogCookCount.value || 0));
        paletteLogging.value = true;
        try {
            await recipeStore.cookAsync(paletteLogCookRecipeId.value, n);
            await Promise.all([recipeStore.getRecipesAsync(), mealPlanStore.getShortfallAsync()]);
            paletteLogCookOpen.value = false;
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
                caption: describeApiError(err) || '',
            });
        } finally {
            paletteLogging.value = false;
        }
    }

    function goToRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }
    function cookRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}/cook`);
    }

    // ── Generate shopping list (composes the C-7 target picker) ────────────
    async function pickGenerateTarget(): Promise<string | null | undefined> {
        const drafts = (shoppingListStore.membership?.active_lists ?? []).filter(
            (l) => l.status === 'draft',
        );
        if (drafts.length === 0) return null;
        const CREATE_NEW = '__create_new__';
        return await new Promise<string | null | undefined>((resolve) => {
            $q.dialog({
                title: 'Add to which list?',
                message: "Generate the week's shopping into an existing draft, or create a new list.",
                options: {
                    type: 'radio',
                    model: drafts[0]!.shopping_list_id,
                    items: [
                        ...drafts.map((d) => ({ label: d.name, value: d.shopping_list_id })),
                        { label: '+ Create new list', value: CREATE_NEW },
                    ],
                },
                cancel: { noCaps: true },
                ok: { label: 'Generate', noCaps: true, color: 'primary' },
                persistent: false,
            })
                .onOk((val: string) => resolve(val === CREATE_NEW ? null : val))
                .onCancel(() => resolve(undefined))
                .onDismiss(() => {});
        });
    }

    async function generateListForWeek() {
        const plan = focusedPlan.value;
        if (!plan) return;
        const target = await pickGenerateTarget();
        if (target === undefined) return;
        generating.value = true;
        try {
            const startIso = toIso(plan.start_date);
            const result = await shoppingListApi.autoGenerateAsync({
                ...(target ? { merge_into_list_id: target } : { name: `Meals: week of ${formatDate(plan.start_date)}` }),
                sources: { meal_plan_week: startIso },
            });
            await shoppingListStore.refreshAsync();
            if (result.nothing_to_add) {
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message: 'Nothing to add — you have everything for this week already.',
                });
                return;
            }
            const itemWord = result.added_count === 1 ? 'item' : 'items';
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: target
                    ? `Added ${result.added_count} ${itemWord} to your list.`
                    : `Shopping list created with ${result.added_count} ${itemWord}.`,
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not generate the list.',
                caption: describeApiError(err) || '',
            });
        } finally {
            generating.value = false;
        }
    }

    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString();
    }
    async function loadIngredients() {
        const id = focusedPlan.value?.meal_plan_id;
        if (!id) { ingredients.value = []; return; }
        ingredientsLoading.value = true;
        try {
            ingredients.value = await mealPlanStore.getIngredientsForPlanAsync(id);
        } finally {
            ingredientsLoading.value = false;
        }
    }
    function confirmClearWeek() {
        const plan = focusedPlan.value;
        if (!plan) return;
        $q.dialog({
            title: 'Clear this week',
            message: `Remove all meals from the week of ${formatDate(plan.start_date)}?`,
            cancel: true,
        }).onOk(() => void doClearWeek(plan.meal_plan_id));
    }
    async function doClearWeek(planId: string) {
        await mealPlanStore.deleteMealPlanAsync(planId);
        await Promise.all([loadIngredients(), mealPlanStore.getShortfallAsync()]);
    }

    watch(() => focusedPlan.value?.meal_plan_id, loadIngredients);

    onMounted(async () => {
        reducedMotion.value = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
        window.addEventListener('keydown', onKeydown);
        await Promise.all([
            mealPlanStore.getMealPlansAsync(),
            mealPlanStore.getShortfallAsync(),
            mealPlanStore.getTodayAsync(),
            mealSlotStore.getMealSlotsAsync(),
            recipeStore.getRecipesAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            shoppingListStore.refreshAsync(),
        ]);
        // Resume on the URL's week if present (F28), else the household's
        // current week (server tz, C-2.K).
        const urlMonday = typeof route.query.monday === 'string' ? route.query.monday : null;
        focusedMonday.value = mondayOf(urlMonday ?? today.value ?? localTodayIso());
        await loadIngredients();
    });
    onUnmounted(() => window.removeEventListener('keydown', onKeydown));
</script>

<style scoped>
    .recipe-list {
        max-height: 65vh;
        overflow-y: auto;
    }
    .recipe-row {
        cursor: grab;
    }
    .recipe-row__pool {
        min-width: 1.4rem;
        text-align: center;
        font-weight: 600;
    }
    .day-card--past {
        opacity: 0.6;
    }
    .slot-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 4px 6px;
        border-radius: 6px;
        transition: background 0.12s ease, outline 0.12s ease;
    }
    .slot-row--clickable {
        cursor: pointer;
    }
    .slot-row--clickable:hover {
        background: var(--surface-sunken);
    }
    .slot-row--target {
        outline: 2px dashed var(--q-primary);
        outline-offset: -2px;
        background: var(--surface-sunken);
    }
    .slot-row__label {
        flex: 0 0 5.5rem;
        font-size: 0.78rem;
        font-weight: 600;
        padding-top: 4px;
        color: var(--text-secondary);
    }
    .slot-row__entries {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .slot-row__hint {
        font-size: 0.72rem;
        color: var(--text-muted);
        font-style: italic;
    }

    .wk-down-enter-active,
    .wk-down-leave-active,
    .wk-up-enter-active,
    .wk-up-leave-active {
        transition: transform 0.18s ease, opacity 0.18s ease;
    }
    .wk-down-enter-from { transform: translateY(20px); opacity: 0; }
    .wk-down-leave-to { transform: translateY(-20px); opacity: 0; }
    .wk-up-enter-from { transform: translateY(-20px); opacity: 0; }
    .wk-up-leave-to { transform: translateY(20px); opacity: 0; }
</style>
