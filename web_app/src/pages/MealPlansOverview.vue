<template>
    <div class="q-pa-md">
        <div class="row items-center q-mb-md q-gutter-sm">
            <q-btn color="positive" :icon="ICONS.add" no-caps label="New plan" @click="onCreatePlan" />
            <q-btn
                outline
                color="primary"
                no-caps
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
                        :icon="ICONS.file_download"
                        label="CSV"
                        @click="planExport.downloadCsv(selectedPlan.meal_plan_id)"
                    />
                    <q-btn
                        flat
                        dense
                        no-caps
                        :icon="ICONS.print"
                        label="Print"
                        @click="planExport.openPrintView(selectedPlan.meal_plan_id)"
                    />
                    <q-btn flat dense no-caps :icon="ICONS.delete" color="negative" label="Delete plan" @click="confirmDeletePlan" />
                </div>

                <!-- Draggable meal palette -->
                <q-card flat bordered class="q-pa-sm q-mb-md">
                    <div class="text-caption text-grey q-mb-xs">
                        <q-icon :name="ICONS.drag_indicator" /> Drag a meal onto a day to plan it
                    </div>
                    <div class="row q-gutter-xs">
                        <div
                            v-for="meal in meals"
                            :key="meal.meal_id"
                            draggable="true"
                            @dragstart="onDragStart(meal.meal_id)"
                            @dragend="draggingMealId = null"
                        >
                            <q-chip
                                square
                                class="cursor-grab"
                                :color="mealCookableById(meal.meal_id) ? 'positive' : 'grey-4'"
                                :text-color="mealCookableById(meal.meal_id) ? 'white' : 'grey-9'"
                                :icon="mealCookableById(meal.meal_id) ? 'check_circle' : 'restaurant'"
                            >
                                {{ meal.name }}
                                <q-tooltip>
                                    {{ mealCookableById(meal.meal_id) ? 'Cookable now' : 'Missing ingredients' }}
                                </q-tooltip>
                            </q-chip>
                        </div>
                        <div v-if="meals.length === 0" class="text-caption text-grey q-pa-sm">
                            No meals yet — create some on the Meals page.
                        </div>
                    </div>
                </q-card>

                <!-- 7-day grid -->
                <div class="row q-col-gutter-sm">
                    <div class="col-12 col-sm-6 col-md" v-for="day in weekDays" :key="day.iso">
                        <q-card
                            bordered
                            class="full-height day-cell"
                            :class="{ 'day-cell--drop': draggingMealId }"
                            @dragover.prevent
                            @drop="onDropOnDay(day.iso)"
                        >
                            <q-card-section class="bg-grey-2 q-pa-sm">
                                <div class="text-weight-bold">{{ day.label }}</div>
                                <div class="text-caption">{{ formatDate(day.iso) }}</div>
                            </q-card-section>
                            <q-card-section class="q-pa-sm">
                                <template v-if="entriesByDay.get(day.iso)?.length">
                                    <q-chip
                                        v-for="entry in entriesByDay.get(day.iso)"
                                        :key="entry.meal_plan_entry_id"
                                        square
                                        clickable
                                        class="q-mb-xs full-width entry-chip"
                                        :color="mealCookableById(entry.meal_id) ? 'primary' : 'grey-6'"
                                        text-color="white"
                                    >
                                        <div class="column">
                                            <div class="text-caption text-italic">{{ entry.slot }}</div>
                                            <div>{{ entry.meal_name }} ×{{ entry.servings }}</div>
                                        </div>
                                        <q-menu transition-show="jump-down" transition-hide="jump-up">
                                            <q-list dense style="min-width: 200px">
                                                <q-item-label header>{{ entry.meal_name }}</q-item-label>
                                                <template v-for="r in recipesForMeal(entry.meal_id)" :key="r.recipe_id">
                                                    <q-item clickable v-close-popup @click="goToRecipe(r.recipe_id)">
                                                        <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                                                        <q-item-section>View {{ r.name }}</q-item-section>
                                                    </q-item>
                                                    <q-item clickable v-close-popup @click="cookRecipe(r.recipe_id)">
                                                        <q-item-section avatar><q-icon :name="ICONS.restaurant" /></q-item-section>
                                                        <q-item-section>Cook {{ r.name }}</q-item-section>
                                                    </q-item>
                                                </template>
                                                <q-separator />
                                                <q-item clickable v-close-popup @click="removeEntry(entry)">
                                                    <q-item-section avatar><q-icon :name="ICONS.close" color="negative" /></q-item-section>
                                                    <q-item-section>Remove from plan</q-item-section>
                                                </q-item>
                                            </q-list>
                                        </q-menu>
                                    </q-chip>
                                </template>
                                <div v-else class="text-caption text-grey text-center q-py-sm">
                                    Drop a meal here
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
                        <div v-if="ingredientsLoading" class="text-caption text-grey">Calculating…</div>
                        <div v-else class="text-h5" :class="needToBuy.length ? 'text-negative' : 'text-positive'">
                            {{ needToBuy.length }}
                        </div>
                        <div class="text-caption text-grey">
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
            <q-banner class="bg-grey-2">Create a meal plan to get started.</q-banner>
        </div>

        <!-- Suggest cookable meals ───────────────────────────────────── -->
        <q-dialog v-model="suggestOpen">
            <q-card style="width: 460px; max-width: 95vw">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-h6">Meals you can cook now</div>
                    <q-space />
                    <q-btn flat dense round :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-card-section>
                    <div v-if="cookableMeals.length === 0" class="text-grey">
                        Nothing's fully in stock right now. Restock or pick a meal with fewer
                        missing ingredients.
                    </div>
                    <q-list v-else separator>
                        <q-item v-for="meal in cookableMeals" :key="meal.meal_id">
                            <q-item-section avatar><q-icon :name="ICONS.check_circle" color="positive" /></q-item-section>
                            <q-item-section>{{ meal.name }}</q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs">
                                    <q-btn
                                        v-if="selectedPlan"
                                        flat dense no-caps label="Add to today"
                                        @click="addMealToday(meal.meal_id)"
                                    />
                                    <q-btn
                                        flat dense no-caps color="primary" label="Cook"
                                        :disable="recipesForMeal(meal.meal_id).length === 0"
                                        @click="cookMeal(meal.meal_id)"
                                    />
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>
        </q-dialog>

        <MealPlanEditDialog v-model="editDialogOpen" :plan="editingPlan" @saved="onPlanSaved" />
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import MealPlanEditDialog from 'components/MealPlanEditDialog.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useMealPlanExport } from 'src/composables/useMealPlanExport';
    import type { MealPlan, MealPlanIngredient } from 'src/models/meal';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import { useMealStore } from 'src/stores/mealStore';
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
    const mealStore = useMealStore();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

    const { meals, mealPlans } = storeToRefs(mealStore);
    const { recipes } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const selectedPlanId = ref<string | null>(null);
    const editDialogOpen = ref(false);
    const editingPlan = ref<MealPlan | null>(null);
    const ingredients = ref<MealPlanIngredient[]>([]);
    const ingredientsLoading = ref(false);
    const draggingMealId = ref<string | null>(null);
    const suggestOpen = ref(false);
    const generating = ref(false);

    const planOptions = computed(() =>
        mealPlans.value.map((p) => ({
            label: `${p.name} (${formatDate(p.start_date)})`,
            value: p.meal_plan_id,
        })),
    );
    const selectedPlan = computed<MealPlan | null>(
        () =>
            (mealPlans.value.find((p) => p.meal_plan_id === selectedPlanId.value) ??
                null) as MealPlan | null,
    );

    // Dates from the API arrive RFC-formatted ("Mon, 18 May 2026 …"); normalise
    // everything to a UTC YYYY-MM-DD so grid matching and PATCH payloads agree.
    function toIso(d: string): string {
        return new Date(d).toISOString().slice(0, 10);
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
        const map = new Map<string, MealPlan['entries']>();
        if (!selectedPlan.value) return map;
        for (const entry of selectedPlan.value.entries) {
            const key = toIso(entry.scheduled_for);
            const list = map.get(key) ?? [];
            list.push(entry);
            map.set(key, list);
        }
        return map;
    });

    // ── Stock status ─────────────────────────────────────────────────────
    const stockLevelByItemId = computed(() => {
        const map = new Map<string, string>();
        stockItems.value.forEach((s) => map.set(s.stock_item_id, s.stock_level_id));
        return map;
    });
    function stockLevelName(stockItemId: string): string | null {
        const levelId = stockLevelByItemId.value.get(stockItemId);
        if (!levelId) return null;
        return stockLevels.value.find((l) => l.stock_level_id === levelId)?.name ?? null;
    }
    function stockStatusLabel(stockItemId: string): string {
        return stockLevelName(stockItemId) ?? 'Not tracked';
    }
    function stockStatusColour(stockItemId: string): string {
        const name = stockLevelName(stockItemId);
        if (name === 'Out of Stock') return 'negative';
        if (name === 'Low Stock') return 'warning';
        if (name === 'Sufficient Stock') return 'info';
        if (name === 'Well-Stocked') return 'positive';
        return 'grey';
    }

    // need-to-buy: anything low, out, or not tracked can't reliably cover demand.
    const needToBuy = computed(() =>
        ingredients.value.filter((ing) => {
            const name = stockLevelName(ing.stock_item_id);
            return name === null || name === 'Low Stock' || name === 'Out of Stock';
        }),
    );

    // ── Cookable-now (same definition as P6 / RecipeCard) ─────────────────
    const outOfStockLevelId = computed(
        () => stockLevels.value.find((l) => l.name === 'Out of Stock')?.stock_level_id ?? null,
    );
    function isMissing(stockItemId: string): boolean {
        const item = stockItems.value.find((si) => si.stock_item_id === stockItemId);
        if (!item) return true;
        return item.stock_level_id === outOfStockLevelId.value;
    }
    function recipesForMeal(mealId: string) {
        return meals.value.find((m) => m.meal_id === mealId)?.recipes ?? [];
    }
    function recipeCookable(recipeId: string): boolean {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe) return false;
        return recipe.ingredients.every((ing) => !isMissing(ing.stock_item_id));
    }
    function mealCookableById(mealId: string): boolean {
        const meal = meals.value.find((m) => m.meal_id === mealId);
        if (!meal || meal.recipes.length === 0) return false;
        return meal.recipes.every((r) => recipeCookable(r.recipe_id));
    }
    const cookableMeals = computed(() =>
        meals.value.filter((m) => mealCookableById(m.meal_id)),
    );

    // ── Drag & drop planning ──────────────────────────────────────────────
    function onDragStart(mealId: string) {
        draggingMealId.value = mealId;
    }

    function currentEntryCommands(): MealPlanEntryCommand[] {
        return (selectedPlan.value?.entries ?? []).map((e) => ({
            meal_id: e.meal_id,
            scheduled_for: toIso(e.scheduled_for),
            servings: e.servings,
            slot: e.slot,
        }));
    }

    async function persistEntries(entries: MealPlanEntryCommand[]) {
        if (!selectedPlan.value) return;
        await mealStore.updateMealPlanAsync({ meal_plan_id: selectedPlan.value.meal_plan_id, entries });
        await loadIngredients();
    }

    async function onDropOnDay(dayIso: string) {
        const mealId = draggingMealId.value;
        draggingMealId.value = null;
        if (!mealId || !selectedPlan.value) return;
        await persistEntries([
            ...currentEntryCommands(),
            { meal_id: mealId, scheduled_for: dayIso, servings: 2, slot: 'Dinner' },
        ]);
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
    }

    async function removeEntry(entry: MealPlan['entries'][number]) {
        const remaining = (selectedPlan.value?.entries ?? [])
            .filter((e) => e.meal_plan_entry_id !== entry.meal_plan_entry_id)
            .map((e) => ({
                meal_id: e.meal_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
        await persistEntries(remaining);
    }

    async function addMealToday(mealId: string) {
        suggestOpen.value = false;
        const todayIso = new Date().toISOString().slice(0, 10);
        await persistEntries([
            ...currentEntryCommands(),
            { meal_id: mealId, scheduled_for: todayIso, servings: 2, slot: 'Dinner' },
        ]);
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to today.' });
    }

    // ── Navigation to recipe / cook mode ──────────────────────────────────
    function goToRecipe(recipeId: string) {
        void router.push(`/recipes/${recipeId}`);
    }
    function cookRecipe(recipeId: string) {
        void router.push(`/recipes/${recipeId}/cook`);
    }
    function cookMeal(mealId: string) {
        const first = recipesForMeal(mealId)[0];
        if (first) cookRecipe(first.recipe_id);
    }

    // ── Generate shopping list for the week ───────────────────────────────
    async function generateListForWeek() {
        if (!selectedPlan.value) return;
        generating.value = true;
        try {
            // X5: route through /auto-generate with the week start so the
            // backend pulls the entries, subtracts well-stocked items, and
            // tags every line as added_via=auto_meal_plan.
            const startIso = toIso(selectedPlan.value.start_date);
            const result = await shoppingListApi.autoGenerateAsync({
                name: `Meals: ${selectedPlan.value.name}`,
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
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Shopping list created with ${result.added_count} item${
                    result.added_count === 1 ? '' : 's'
                }.`,
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

    // ── Plan CRUD ─────────────────────────────────────────────────────────
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
            ingredients.value = await mealStore.getIngredientsForPlanAsync(selectedPlanId.value);
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
        await mealStore.getMealPlansAsync();
        await loadIngredients();
    }
    function confirmDeletePlan() {
        if (!selectedPlan.value) return;
        const plan = selectedPlan.value;
        $q.dialog({ title: 'Delete plan', message: `Delete "${plan.name}"?`, cancel: true, persistent: true })
            .onOk(() => void doDeletePlan(plan.meal_plan_id));
    }
    async function doDeletePlan(planId: string) {
        await mealStore.deleteMealPlanAsync(planId);
        selectedPlanId.value = null;
        await loadIngredients();
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
            mealStore.getMealPlansAsync(),
            mealStore.getMealsAsync(),
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
    .entry-chip {
        height: auto;
    }
    .cursor-grab {
        cursor: grab;
    }
</style>
