<template>
    <div class="q-pa-md">
        <div class="row items-center q-mb-md">
            <q-btn color="positive" :icon="ICONS.add" label="New Meal" @click="onCreate" />
            <q-space />
            <div class="text-subtitle1">
                Total meals in stock: <strong>{{ totalInStock }}</strong>
            </div>
        </div>

        <div class="row q-col-gutter-md">
            <div
                class="col-12 col-sm-6 col-md-4"
                v-for="meal in meals"
                :key="meal.meal_id"
            >
                <q-card bordered class="full-height">
                    <q-card-section>
                        <div class="row items-center no-wrap">
                            <div class="text-h6 ellipsis">{{ meal.name }}</div>
                            <q-space />
                            <q-badge :color="meal.quantity_in_stock > 0 ? 'positive' : 'grey'">
                                {{ meal.quantity_in_stock }} in stock
                            </q-badge>
                        </div>
                        <div class="text-caption text-grey q-mt-xs">
                            <span v-if="meal.recipes.length === 0">No recipes</span>
                            <span v-else>{{ meal.recipes.map((r) => r.name).join(', ') }}</span>
                        </div>
                    </q-card-section>

                    <q-card-actions align="right">
                        <q-btn
                            flat
                            round
                            dense
                            :icon="ICONS.remove"
                            :disable="meal.quantity_in_stock <= 0"
                            @click="mealStore.adjustStockAsync(meal.meal_id, -1)"
                        />
                        <q-btn
                            flat
                            round
                            dense
                            :icon="ICONS.add"
                            @click="mealStore.adjustStockAsync(meal.meal_id, 1)"
                        />
                        <q-space />
                        <q-btn flat label="Edit" color="primary" @click="onEdit(meal)" />
                        <q-btn flat :icon="ICONS.delete" color="negative" @click="confirmDelete(meal)" />
                    </q-card-actions>
                </q-card>
            </div>
            <div class="col-12" v-if="meals.length === 0">
                <q-banner class="bg-grey-2">No meals yet — create your first one.</q-banner>
            </div>
        </div>

        <q-dialog v-model="dialogOpen" persistent>
            <q-card style="width: 600px; max-width: 90vw">
                <q-card-section>
                    <div class="text-h6">{{ editing ? 'Edit Meal' : 'New Meal' }}</div>
                </q-card-section>
                <q-card-section>
                    <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                        <q-input
                            outlined
                            label="Name *"
                            v-model="form.name"
                            :rules="[(v: string) => !!v || 'Name required']"
                            autofocus
                        />
                        <q-input
                            outlined
                            label="Quantity in stock"
                            type="number"
                            v-model.number="form.quantity_in_stock"
                            min="0"
                        />
                        <q-select
                            outlined
                            multiple
                            use-chips
                            label="Recipes"
                            v-model="form.recipe_ids"
                            :options="recipeOptions"
                            emit-value
                            map-options
                        />
                        <q-card-actions align="right">
                            <q-btn flat label="Cancel" @click="dialogOpen = false" />
                            <q-btn type="submit" color="primary" label="Save" :loading="saving" />
                        </q-card-actions>
                    </q-form>
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { Meal } from 'src/models/meal';
    import { useMealStore } from 'src/stores/mealStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { computed, onMounted, reactive, ref } from 'vue';

    const $q = useQuasar();
    const mealStore = useMealStore();
    const recipeStore = useRecipeStore();
    const { meals } = storeToRefs(mealStore);
    const { recipes } = storeToRefs(recipeStore);

    const totalInStock = computed(() => meals.value.reduce((sum, m) => sum + m.quantity_in_stock, 0));
    const recipeOptions = computed(() =>
        recipes.value.map((r) => ({ label: r.name, value: r.recipe_id }))
    );

    const dialogOpen = ref(false);
    const editing = ref<Meal | null>(null);
    const saving = ref(false);

    type Form = { name: string; quantity_in_stock: number; recipe_ids: string[] };
    const emptyForm = (): Form => ({ name: '', quantity_in_stock: 0, recipe_ids: [] });
    const form = reactive<Form>(emptyForm());

    function onCreate() {
        editing.value = null;
        Object.assign(form, emptyForm());
        dialogOpen.value = true;
    }

    function onEdit(meal: Meal) {
        editing.value = meal;
        form.name = meal.name;
        form.quantity_in_stock = meal.quantity_in_stock;
        form.recipe_ids = meal.recipes.map((r) => r.recipe_id);
        dialogOpen.value = true;
    }

    async function onSubmit() {
        saving.value = true;
        try {
            if (editing.value) {
                await mealStore.updateMealAsync({
                    meal_id: editing.value.meal_id,
                    name: form.name,
                    quantity_in_stock: form.quantity_in_stock,
                    recipe_ids: form.recipe_ids
                });
            } else {
                await mealStore.createMealAsync({
                    name: form.name,
                    quantity_in_stock: form.quantity_in_stock,
                    recipe_ids: form.recipe_ids
                });
            }
            dialogOpen.value = false;
        } finally {
            saving.value = false;
        }
    }

    function confirmDelete(meal: Meal) {
        $q.dialog({
            title: 'Delete meal',
            message: `Delete "${meal.name}"?`,
            cancel: true,
            persistent: true
        }).onOk(async () => {
            await mealStore.deleteMealAsync(meal.meal_id);
        });
    }

    onMounted(async () => {
        await Promise.all([mealStore.getMealsAsync(), recipeStore.getRecipesAsync()]);
    });
</script>
