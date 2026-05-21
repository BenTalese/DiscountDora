<template>
    <div class="q-pa-md">
        <div class="row items-center q-mb-md">
            <div class="text-h5 q-mr-md">Meal Plans</div>
            <q-btn color="positive" icon="add" label="New Plan" @click="onCreatePlan" />
            <q-space />
            <q-select
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

        <div v-if="selectedPlan">
            <div class="row items-center q-mb-md">
                <div class="text-subtitle1">
                    Week of {{ formatDate(selectedPlan.start_date) }}
                </div>
                <q-space />
                <q-btn flat icon="edit" label="Edit entries" @click="onEditEntries" />
                <q-btn flat icon="delete" color="negative" label="Delete plan" @click="confirmDeletePlan" />
            </div>

            <div class="row q-col-gutter-sm">
                <div
                    class="col-12 col-sm-6 col-md"
                    v-for="day in weekDays"
                    :key="day.iso"
                >
                    <q-card bordered class="full-height">
                        <q-card-section class="bg-grey-2 q-pa-sm">
                            <div class="text-weight-bold">{{ day.label }}</div>
                            <div class="text-caption">{{ formatDate(day.iso) }}</div>
                        </q-card-section>
                        <q-card-section class="q-pa-sm">
                            <div v-if="entriesByDay.get(day.iso)?.length">
                                <q-chip
                                    v-for="entry in entriesByDay.get(day.iso)"
                                    :key="entry.meal_plan_entry_id"
                                    dense
                                    square
                                    class="q-mb-xs"
                                    :color="mealStockColour(entry.meal_id)"
                                    text-color="white"
                                >
                                    <div>
                                        <div class="text-caption text-italic">{{ entry.slot }}</div>
                                        <div>{{ entry.meal_name }} ×{{ entry.servings }}</div>
                                    </div>
                                </q-chip>
                            </div>
                            <div v-else class="text-caption text-grey">No meals planned</div>
                        </q-card-section>
                    </q-card>
                </div>
            </div>

            <q-separator class="q-my-md" />

            <div class="text-subtitle1 q-mb-sm">Ingredients required</div>
            <q-banner v-if="ingredientsLoading" class="bg-grey-2">Loading ingredients...</q-banner>
            <q-banner v-else-if="ingredients.length === 0" class="bg-grey-2">
                No ingredients aggregated from this plan's meals.
            </q-banner>
            <q-table
                v-else
                flat
                bordered
                dense
                :rows="ingredients"
                :columns="ingredientColumns"
                row-key="stock_item_id"
                :pagination="{ rowsPerPage: 0 }"
                hide-pagination
            >
                <template #body-cell-status="cellProps">
                    <q-td :props="cellProps">
                        <q-chip dense :color="stockStatusColour(cellProps.row.stock_item_id)" text-color="white">
                            {{ stockStatusLabel(cellProps.row.stock_item_id) }}
                        </q-chip>
                    </q-td>
                </template>
                <template #body-cell-quantity="cellProps">
                    <q-td :props="cellProps">
                        <span v-if="cellProps.row.total_quantity !== null">
                            {{ cellProps.row.total_quantity }} {{ cellProps.row.unit ?? '' }}
                        </span>
                        <span v-else>—</span>
                    </q-td>
                </template>
            </q-table>
        </div>

        <div v-else>
            <q-banner class="bg-grey-2">Create a meal plan to get started.</q-banner>
        </div>

        <MealPlanEditDialog
            v-model="editDialogOpen"
            :plan="editingPlan"
            @saved="onPlanSaved"
        />
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { MealPlan, MealPlanIngredient } from 'src/models/meal';
    import { useMealStore } from 'src/stores/mealStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import MealPlanEditDialog from 'components/MealPlanEditDialog.vue';

    const $q = useQuasar();
    const mealStore = useMealStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();

    const { meals, mealPlans } = storeToRefs(mealStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const selectedPlanId = ref<string | null>(null);
    const editDialogOpen = ref(false);
    const editingPlan = ref<MealPlan | null>(null);
    const ingredients = ref<MealPlanIngredient[]>([]);
    const ingredientsLoading = ref(false);

    const planOptions = computed(() =>
        mealPlans.value.map((p) => ({
            label: `${p.name} (${formatDate(p.start_date)})`,
            value: p.meal_plan_id
        }))
    );

    const selectedPlan = computed<MealPlan | null>(
        () => mealPlans.value.find((p) => p.meal_plan_id === selectedPlanId.value) ?? null
    );

    const weekDays = computed(() => {
        if (!selectedPlan.value) return [];
        const start = new Date(selectedPlan.value.start_date);
        const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return labels.map((label, i) => {
            const d = new Date(start);
            d.setDate(d.getDate() + i);
            const iso = d.toISOString().slice(0, 10);
            return { label, iso };
        });
    });

    const entriesByDay = computed(() => {
        const map = new Map<string, MealPlan['entries']>();
        if (!selectedPlan.value) return map;
        for (const entry of selectedPlan.value.entries) {
            const list = map.get(entry.scheduled_for) ?? [];
            list.push(entry);
            map.set(entry.scheduled_for, list);
        }
        return map;
    });

    const ingredientColumns = [
        { name: 'name', label: 'Ingredient', field: 'stock_item_name', align: 'left' as const, sortable: true },
        { name: 'quantity', label: 'Quantity', field: 'total_quantity', align: 'left' as const },
        { name: 'status', label: 'Stock', field: 'stock_item_id', align: 'left' as const }
    ];

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
        return stockLevelName(stockItemId) ?? 'Unknown';
    }

    function stockStatusColour(stockItemId: string): string {
        const name = stockLevelName(stockItemId);
        if (name === 'Out of Stock') return 'negative';
        if (name === 'Low Stock') return 'warning';
        if (name === 'Sufficient Stock') return 'info';
        if (name === 'Well-Stocked') return 'positive';
        return 'grey';
    }

    function mealStockColour(mealId: string): string {
        const meal = meals.value.find((m) => m.meal_id === mealId);
        if (!meal) return 'grey';
        return meal.quantity_in_stock > 0 ? 'primary' : 'grey-7';
    }

    function formatDate(iso: string): string {
        const d = new Date(iso);
        return d.toLocaleDateString();
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

    watch(selectedPlanId, loadIngredients);
    watch(mealPlans, (plans) => {
        if (!selectedPlanId.value && plans.length > 0) {
            selectedPlanId.value = plans[plans.length - 1]!.meal_plan_id;
        }
    }, { immediate: true });

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
        $q.dialog({
            title: 'Delete plan',
            message: `Delete "${plan.name}"?`,
            cancel: true,
            persistent: true
        }).onOk(async () => {
            await mealStore.deleteMealPlanAsync(plan.meal_plan_id);
            selectedPlanId.value = null;
            await loadIngredients();
        });
    }

    onMounted(async () => {
        await Promise.all([
            mealStore.getMealPlansAsync(),
            mealStore.getMealsAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync()
        ]);
    });
</script>
