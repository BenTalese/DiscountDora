<template>
    <div class="q-pa-md">
        <div class="row items-center q-mb-md q-gutter-sm">
            <BaseButton variant="primary" :icon="ICONS.add" label="New plan" @click="onCreatePlan" />
            <BaseButton
                variant="secondary"
                :icon="ICONS.lightbulb"
                label="Suggest meals I can cook now"
                @click="suggestOpen = true"
            />
            <q-space />
            <q-select
                v-if="planOptions.length > 0"
                dense
                outlined
                style="min-width: 250px"
                emit-value
                map-options
                v-model="selectedPlanId"
                :options="planOptions"
                label="Active plan"
            />
        </div>

        <!-- Shortfall rollup — visible whenever any recipe is over-committed. -->
        <q-banner
            v-if="shortfall.length"
            class="dora-bg-warning-soft text-warning q-mb-md"
            rounded
        >
            <template v-slot:avatar>
                <q-icon :name="ICONS.warning" color="warning" />
            </template>
            <div class="text-subtitle2">You need to cook:</div>
            <div class="row q-gutter-xs q-mt-xs">
                <q-chip
                    v-for="item in shortfall"
                    :key="item.recipe_id"
                    square
                    color="warning"
                    text-color="white"
                    clickable
                    @click="cookRecipe(item.recipe_id)"
                >
                    {{ item.shortfall }}× {{ item.recipe_name }}
                    <span v-if="item.earliest_needed" class="q-ml-xs text-caption">
                        by {{ formatDate(item.earliest_needed) }}
                    </span>
                </q-chip>
            </div>
        </q-banner>

        <div v-if="selectedPlan" class="row q-col-gutter-md">
            <!-- ── Main: palette + week grid ──────────────────────────── -->
            <div class="col-12 col-md-9">
                <div class="row items-center q-mb-sm">
                    <div class="text-subtitle1">Week of {{ formatDate(selectedPlan.start_date) }}</div>
                    <q-space />
                    <q-btn flat dense no-caps :icon="ICONS.edit" label="Edit entries" @click="onEditEntries" />
                    <q-btn
                        flat
                        dense
                        no-caps
                        :icon="ICONS.print"
                        label="Print"
                        @click="planExport.openPrintView(selectedPlan.meal_plan_id)"
                    />
                    <BaseButton variant="danger-ghost" :icon="ICONS.delete" label="Delete plan" @click="confirmDeletePlan" />
                </div>

                <!-- Draggable recipe palette -->
                <q-card flat bordered class="q-pa-sm q-mb-md">
                    <div class="text-caption dora-text-muted q-mb-xs">
                        <q-icon :name="ICONS.drag_indicator" /> Drag a recipe onto a day to plan it
                    </div>
                    <div class="row q-gutter-xs">
                        <div
                            v-for="recipe in recipes"
                            :key="recipe.recipe_id"
                            draggable="true"
                            @dragstart="onDragStart(recipe.recipe_id)"
                            @dragend="draggingRecipeId = null"
                        >
                            <q-chip
                                square
                                clickable
                                class="cursor-grab"
                                :color="recipeCookable(recipe) ? 'positive' : 'grey-4'"
                                :text-color="recipeCookable(recipe) ? 'white' : 'grey-9'"
                                :icon="recipeCookable(recipe) ? 'check_circle' : 'restaurant'"
                            >
                                {{ recipe.name }}
                                <span class="q-ml-xs text-caption">({{ recipe.unallocated_meals }})</span>
                                <q-tooltip>
                                    {{ recipe.unallocated_meals }} unallocated of {{ recipe.available_meals }} on hand · click for actions
                                </q-tooltip>
                                <!-- Click (not drag) opens this menu; the chip stays draggable. -->
                                <q-menu transition-show="jump-down" transition-hide="jump-up">
                                    <q-card style="min-width: 240px">
                                        <q-card-section class="q-pb-xs">
                                            <div class="text-subtitle2">{{ recipe.name }}</div>
                                            <div class="text-caption dora-text-muted">
                                                {{ recipe.unallocated_meals }} free of
                                                {{ recipe.available_meals }} cooked
                                            </div>
                                        </q-card-section>
                                        <q-card-actions class="q-px-md q-pb-sm">
                                            <q-btn
                                                dense
                                                round
                                                outline
                                                :icon="ICONS.remove"
                                                :disable="recipe.available_meals <= 0"
                                                @click="adjustPaletteMeals(recipe.recipe_id, -1)"
                                            />
                                            <div
                                                class="text-h6 q-px-sm"
                                                style="min-width: 2.5rem; text-align: center;"
                                            >
                                                {{ recipe.available_meals }}
                                            </div>
                                            <q-btn
                                                dense
                                                round
                                                outline
                                                :icon="ICONS.add"
                                                @click="adjustPaletteMeals(recipe.recipe_id, 1)"
                                            />
                                            <q-space />
                                            <q-btn
                                                no-caps
                                                flat
                                                color="primary"
                                                :icon="ICONS.restaurant"
                                                label="Log cook…"
                                                v-close-popup
                                                @click="openPaletteLogCook(recipe.recipe_id)"
                                            />
                                        </q-card-actions>
                                    </q-card>
                                </q-menu>
                            </q-chip>
                        </div>
                        <div v-if="recipes.length === 0" class="text-caption dora-text-muted q-pa-sm">
                            No recipes yet — create some on the Recipes page.
                        </div>
                    </div>
                </q-card>

                <!-- 7-day grid -->
                <div class="row q-col-gutter-sm">
                    <div class="col-12 col-sm-6 col-md" v-for="day in weekDays" :key="day.iso">
                        <q-card
                            bordered
                            class="full-height day-cell"
                            :class="{
                                'day-cell--drop': draggingRecipeId && !isPastDay(day.iso),
                                'day-cell--past': isPastDay(day.iso),
                            }"
                            @dragover.prevent
                            @drop="onDropOnDay(day.iso)"
                        >
                            <q-card-section class="dora-bg-sunken q-pa-sm">
                                <div class="text-weight-bold">{{ day.label }}</div>
                                <div class="text-caption">{{ formatDate(day.iso) }}</div>
                            </q-card-section>
                            <q-card-section class="q-pa-sm">
                                <template v-if="entriesByDay.get(day.iso)?.length">
                                    <q-chip
                                        v-for="entry in entriesByDay.get(day.iso)"
                                        :key="entry.meal_plan_entry_id"
                                        square
                                        :clickable="!entry.consumed_at"
                                        class="q-mb-xs full-width entry-chip"
                                        :color="entry.consumed_at
                                            ? 'grey-5'
                                            : isShortfallEntry(entry)
                                                ? 'warning'
                                                : 'primary'"
                                        text-color="white"
                                    >
                                        <div class="column">
                                            <div class="text-caption text-italic">{{ entry.slot }}</div>
                                            <div>
                                                {{ entry.recipe_name }} ×{{ entry.servings }}
                                                <q-icon v-if="entry.consumed_at" :name="ICONS.check" class="q-ml-xs" />
                                                <q-icon v-else-if="isShortfallEntry(entry)" :name="ICONS.warning" class="q-ml-xs">
                                                    <q-tooltip>Needs cooking — pool is short</q-tooltip>
                                                </q-icon>
                                            </div>
                                        </div>
                                        <q-menu
                                            v-if="!entry.consumed_at"
                                            transition-show="jump-down"
                                            transition-hide="jump-up"
                                        >
                                            <q-list dense style="min-width: 200px">
                                                <q-item-label header>{{ entry.recipe_name }}</q-item-label>
                                                <q-item clickable v-close-popup @click="goToRecipe(entry.recipe_id)">
                                                    <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                                                    <q-item-section>View recipe</q-item-section>
                                                </q-item>
                                                <q-item clickable v-close-popup @click="cookRecipe(entry.recipe_id)">
                                                    <q-item-section avatar><q-icon :name="ICONS.restaurant" /></q-item-section>
                                                    <q-item-section>Cook now</q-item-section>
                                                </q-item>
                                                <q-separator />
                                                <q-item clickable v-close-popup @click="removeEntry(entry)">
                                                    <q-item-section avatar><q-icon :name="ICONS.close" color="negative" /></q-item-section>
                                                    <q-item-section>Remove from plan</q-item-section>
                                                </q-item>
                                            </q-list>
                                        </q-menu>
                                    </q-chip>
                                </template>
                                <div v-else-if="isPastDay(day.iso)" class="text-caption dora-text-muted text-center q-py-sm">
                                    —
                                </div>
                                <div v-else class="text-caption dora-text-muted text-center q-py-sm">
                                    Drop a recipe here
                                </div>
                            </q-card-section>
                        </q-card>
                    </div>
                </div>
            </div>

            <!-- ── Sidebar: demand rollup ─────────────────────────────── -->
            <div class="col-12 col-md-3">
                <q-card flat bordered>
                    <q-card-section class="q-pb-xs">
                        <div class="text-subtitle1">This week's shopping</div>
                        <div v-if="ingredientsLoading" class="text-caption dora-text-muted">Calculating…</div>
                        <div v-else class="text-h5" :class="needToBuy.length ? 'text-negative' : 'text-positive'">
                            {{ needToBuy.length }}
                        </div>
                        <div class="text-caption dora-text-muted">
                            {{ needToBuy.length ? "item(s) you'll need to buy" : 'fully stocked for this plan' }}
                        </div>
                    </q-card-section>

                    <q-list v-if="needToBuy.length" dense separator>
                        <q-item v-for="ing in needToBuy" :key="ing.stock_item_id">
                            <q-item-section>
                                <q-item-label>{{ ing.stock_item_name }}</q-item-label>
                                <q-item-label caption v-if="ing.total_quantity !== null">
                                    needs {{ ing.total_quantity }} {{ ing.unit ?? '' }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
                                    {{ stockStatusLabel(ing.stock_item_id) }}
                                </q-chip>
                            </q-item-section>
                        </q-item>
                    </q-list>

                    <q-card-actions>
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
                    v-if="ingredients.length"
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

        <div v-else>
            <q-banner class="dora-bg-sunken">Create a meal plan to get started.</q-banner>
        </div>

        <!-- Suggest cookable recipes ───────────────────────────────── -->
        <BaseDialog v-model="suggestOpen" title="Recipes you can cook now" closable card-style="width: 460px; max-width: 95vw">
                <q-card-section>
                    <div v-if="cookableRecipes.length === 0" class="dora-text-muted">
                        Nothing's fully in stock right now. Restock or pick a recipe with fewer
                        missing ingredients.
                    </div>
                    <q-list v-else separator>
                        <q-item v-for="recipe in cookableRecipes" :key="recipe.recipe_id">
                            <q-item-section avatar><q-icon :name="ICONS.check_circle" color="positive" /></q-item-section>
                            <q-item-section>{{ recipe.name }}</q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs">
                                    <q-btn
                                        v-if="selectedPlan"
                                        flat dense no-caps label="Add to today"
                                        @click="addRecipeToday(recipe.recipe_id)"
                                    />
                                    <q-btn
                                        flat dense no-caps color="primary" label="Cook"
                                        @click="cookRecipe(recipe.recipe_id)"
                                    />
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>

        <MealPlanEditDialog v-model="editDialogOpen" :plan="editingPlan" @saved="onPlanSaved" />

        <!-- Log cook from the planner palette ─────────────────────── -->
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
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanEditDialog from 'components/MealPlanEditDialog.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useMealPlanExport } from 'src/composables/useMealPlanExport';
    import {
        LOW_STOCK_SEQUENCE,
        needsRestockSequence,
        OUT_OF_STOCK_SEQUENCE,
        SUFFICIENT_STOCK_SEQUENCE,
        WELL_STOCKED_SEQUENCE,
    } from 'src/helpers/stockStatus';
    import type { MealPlan, MealPlanEntry, MealPlanIngredient } from 'src/models/mealPlan';
    import type { Recipe } from 'src/models/recipe';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const planExport = useMealPlanExport();
    const mealPlanStore = useMealPlanStore();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

    const { mealPlans, shortfall } = storeToRefs(mealPlanStore);
    const { recipes } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const selectedPlanId = ref<string | null>(null);
    const editDialogOpen = ref(false);
    const editingPlan = ref<MealPlan | null>(null);
    const ingredients = ref<MealPlanIngredient[]>([]);
    const ingredientsLoading = ref(false);
    const draggingRecipeId = ref<string | null>(null);
    const suggestOpen = ref(false);
    const generating = ref(false);

    const planOptions = computed(() =>
        mealPlans.value.map((p) => ({
            label: `${p.name} (${formatDate(p.start_date)})`,
            value: p.meal_plan_id,
        })),
    );
    const selectedPlan = computed<MealPlan | null>(
        () => mealPlans.value.find((p) => p.meal_plan_id === selectedPlanId.value) ?? null,
    );

    function toIso(d: string): string {
        return new Date(d).toISOString().slice(0, 10);
    }

    function todayIsoLocal(): string {
        const d = new Date();
        return new Date(d.getFullYear(), d.getMonth(), d.getDate()).toISOString().slice(0, 10);
    }

    function isPastDay(iso: string): boolean {
        return iso < todayIsoLocal();
    }

    const weekDays = computed(() => {
        if (!selectedPlan.value) return [];
        const [y, m, d] = toIso(selectedPlan.value.start_date).split('-').map(Number);
        const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return labels.map((label, i) => {
            const dt = new Date(Date.UTC(y!, m! - 1, d! + i));
            return { label, iso: dt.toISOString().slice(0, 10) };
        });
    });

    const entriesByDay = computed(() => {
        const map = new Map<string, MealPlanEntry[]>();
        if (!selectedPlan.value) return map;
        for (const entry of selectedPlan.value.entries) {
            const key = toIso(entry.scheduled_for);
            const list = map.get(key) ?? [];
            list.push(entry);
            map.set(key, list);
        }
        return map;
    });

    const shortfallRecipeIds = computed(() => new Set(shortfall.value.map((s) => s.recipe_id)));
    function isShortfallEntry(entry: MealPlanEntry): boolean {
        return shortfallRecipeIds.value.has(entry.recipe_id);
    }

    // ── Stock status ─────────────────────────────────────────────────────
    // Resolves by sequence (§3.1 contract) — renaming a level row in the
    // UI doesn't shift which bucket a stock item lands in.
    const stockItemById = computed(() => {
        const map = new Map<string, typeof stockItems.value[number]>();
        stockItems.value.forEach((s) => map.set(s.stock_item_id, s));
        return map;
    });
    function levelSequenceForItem(stockItemId: string): number | null {
        const item = stockItemById.value.get(stockItemId);
        if (!item) return null;
        if (typeof item.stock_level_sequence === 'number') return item.stock_level_sequence;
        return stockLevels.value.find(
            (l) => l.stock_level_id === item.stock_level_id,
        )?.sequence ?? null;
    }
    function stockStatusLabel(stockItemId: string): string {
        const item = stockItemById.value.get(stockItemId);
        if (!item) return 'Not tracked';
        return (
            stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)?.name
            ?? 'Not tracked'
        );
    }
    function stockStatusColour(stockItemId: string): string {
        const seq = levelSequenceForItem(stockItemId);
        switch (seq) {
            case OUT_OF_STOCK_SEQUENCE: return 'negative';
            case LOW_STOCK_SEQUENCE: return 'warning';
            case SUFFICIENT_STOCK_SEQUENCE: return 'info';
            case WELL_STOCKED_SEQUENCE: return 'positive';
            default: return 'grey';
        }
    }

    const needToBuy = computed(() =>
        ingredients.value.filter((ing) => {
            const seq = levelSequenceForItem(ing.stock_item_id);
            // Untracked (no seq) OR low/out → still needs buying.
            return seq === null || needsRestockSequence(seq);
        }),
    );

    // ── Cookable-now ─────────────────────────────────────────────────────
    // Cookability is server-owned (§3.2): recipes carry `cookable`. A recipe
    // with no ingredients is `cookable` server-side, but we don't surface an
    // empty recipe as "cook now", so require at least one ingredient here.
    function recipeCookable(recipe: Recipe): boolean {
        return recipe.cookable && recipe.ingredients.length > 0;
    }
    const cookableRecipes = computed(() => recipes.value.filter(recipeCookable));

    // ── Drag & drop planning ──────────────────────────────────────────────
    function onDragStart(recipeId: string) {
        draggingRecipeId.value = recipeId;
    }

    function currentEntryCommands(): MealPlanEntryCommand[] {
        return (selectedPlan.value?.entries ?? [])
            .filter((e) => !e.consumed_at)
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
    }

    async function persistEntries(entries: MealPlanEntryCommand[]) {
        if (!selectedPlan.value) return;
        // The planner's own drag/drop and chip-menu removals are
        // explicit edits, so set the clear flag when an action would
        // leave the future-entries list empty. Backend treats unflagged
        // [] as a probable bug and refuses.
        await mealPlanStore.updateMealPlanAsync({
            meal_plan_id: selectedPlan.value.meal_plan_id,
            entries,
            ...(entries.length === 0 ? { confirm_clear_entries: true } : {}),
        });
        await Promise.all([loadIngredients(), mealPlanStore.getShortfallAsync(), recipeStore.getRecipesAsync()]);
    }

    async function onDropOnDay(dayIso: string) {
        const recipeId = draggingRecipeId.value;
        draggingRecipeId.value = null;
        if (!recipeId || !selectedPlan.value) return;
        if (isPastDay(dayIso)) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Past days are read-only.' });
            return;
        }
        await persistEntries([
            ...currentEntryCommands(),
            { recipe_id: recipeId, scheduled_for: dayIso, servings: 1, slot: 'Dinner' },
        ]);
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
    }

    async function removeEntry(entry: MealPlanEntry) {
        const remaining = (selectedPlan.value?.entries ?? [])
            .filter((e) => e.meal_plan_entry_id !== entry.meal_plan_entry_id && !e.consumed_at)
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
        await persistEntries(remaining);
    }

    async function addRecipeToday(recipeId: string) {
        suggestOpen.value = false;
        const todayIso = todayIsoLocal();
        await persistEntries([
            ...currentEntryCommands(),
            { recipe_id: recipeId, scheduled_for: todayIso, servings: 1, slot: 'Dinner' },
        ]);
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to today.' });
    }

    // ── Palette quick-actions (± / log cook) ──────────────────────────
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

    // Cart-button Chunk 4 / L382: route the generate target through Axis B —
    // when any draft list already exists, offer "add to existing / new"
    // instead of always creating a fresh one. Returns the chosen list id, or
    // null to mean "create new", or undefined if the user cancelled.
    async function pickGenerateTarget(): Promise<string | null | undefined> {
        const drafts = (shoppingListStore.membership?.active_lists ?? []).filter(
            (l) => l.status === 'draft',
        );
        if (drafts.length === 0) return null;
        const CREATE_NEW = '__create_new__';
        return await new Promise<string | null | undefined>((resolve) => {
            $q.dialog({
                title: 'Add to which list?',
                message: 'Generate the week\'s shopping into an existing draft, or create a new list.',
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
        if (!selectedPlan.value) return;
        const target = await pickGenerateTarget();
        if (target === undefined) return;
        generating.value = true;
        try {
            const startIso = toIso(selectedPlan.value.start_date);
            const result = await shoppingListApi.autoGenerateAsync({
                ...(target ? { merge_into_list_id: target } : { name: `Meals: ${selectedPlan.value.name}` }),
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
        if (!selectedPlanId.value) {
            ingredients.value = [];
            return;
        }
        ingredientsLoading.value = true;
        try {
            ingredients.value = await mealPlanStore.getIngredientsForPlanAsync(selectedPlanId.value);
        } finally {
            ingredientsLoading.value = false;
        }
    }
    function onCreatePlan() {
        editingPlan.value = null;
        editDialogOpen.value = true;
    }
    function onEditEntries() {
        editingPlan.value = selectedPlan.value;
        editDialogOpen.value = true;
    }
    async function onPlanSaved() {
        editDialogOpen.value = false;
        await Promise.all([
            mealPlanStore.getMealPlansAsync(),
            mealPlanStore.getShortfallAsync(),
            recipeStore.getRecipesAsync(),
        ]);
        await loadIngredients();
    }
    function confirmDeletePlan() {
        if (!selectedPlan.value) return;
        const plan = selectedPlan.value;
        $q.dialog({ title: 'Delete plan', message: `Delete "${plan.name}"?`, cancel: true })
            .onOk(() => void doDeletePlan(plan.meal_plan_id));
    }
    async function doDeletePlan(planId: string) {
        await mealPlanStore.deleteMealPlanAsync(planId);
        selectedPlanId.value = null;
        await loadIngredients();
        await mealPlanStore.getShortfallAsync();
    }

    watch(selectedPlanId, loadIngredients);
    watch(
        mealPlans,
        (plans) => {
            if (!selectedPlanId.value && plans.length > 0) {
                selectedPlanId.value = plans[plans.length - 1]!.meal_plan_id;
            }
        },
        { immediate: true },
    );

    onMounted(async () => {
        await Promise.all([
            mealPlanStore.getMealPlansAsync(),
            mealPlanStore.getShortfallAsync(),
            recipeStore.getRecipesAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
        ]);
    });
</script>

<style scoped>
    .day-cell {
        min-height: 120px;
        transition: outline 0.12s ease;
    }
    .day-cell--drop {
        outline: 2px dashed var(--q-primary);
        outline-offset: -2px;
    }
    .day-cell--past {
        opacity: 0.6;
    }
    .entry-chip {
        height: auto !important;
        white-space: normal;
    }
</style>
