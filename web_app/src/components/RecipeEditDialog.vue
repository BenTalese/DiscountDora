<template>
    <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent>
        <q-card style="width: 800px; max-width: 95vw">
            <q-card-section>
                <div class="text-h5">{{ recipe ? 'Edit Recipe' : 'New Recipe' }}</div>
            </q-card-section>

            <q-card-section>
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <q-input
                        outlined
                        label="Name *"
                        v-model="form.name"
                        :rules="[(v: string) => !!v || 'Name is required']"
                        autofocus
                    />

                    <div class="row q-col-gutter-md">
                        <q-input class="col-12 col-sm-6" outlined label="Cuisine" v-model="form.cuisine" />
                        <q-input class="col-12 col-sm-6" outlined label="Category" v-model="form.category" />
                    </div>

                    <div class="row q-col-gutter-md">
                        <q-select
                            class="col-12 col-sm-4"
                            outlined
                            label="Time of Day"
                            v-model="form.time_of_day"
                            :options="['Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Snack', 'Any']"
                            clearable
                        />
                        <q-select
                            class="col-12 col-sm-4"
                            outlined
                            label="Difficulty"
                            v-model="form.difficulty"
                            :options="['Easy', 'Medium', 'Hard']"
                            clearable
                        />
                        <q-input
                            class="col-12 col-sm-4"
                            outlined
                            label="Servings"
                            type="number"
                            v-model.number="form.servings"
                        />
                    </div>

                    <div class="row q-col-gutter-md">
                        <q-input
                            class="col-12 col-sm-6"
                            outlined
                            label="Prep time (minutes)"
                            type="number"
                            v-model.number="form.prep_time_minutes"
                        />
                        <q-input
                            class="col-12 col-sm-6"
                            outlined
                            label="Cook time (minutes)"
                            type="number"
                            v-model.number="form.cook_time_minutes"
                        />
                    </div>

                    <q-select
                        outlined
                        label="Collection"
                        v-model="form.recipe_collection_id"
                        :options="collectionOptions"
                        emit-value
                        map-options
                        clearable
                    />

                    <q-input
                        outlined
                        type="textarea"
                        label="Instructions"
                        autogrow
                        v-model="form.instructions"
                    />

                    <q-input
                        outlined
                        type="textarea"
                        label="Nutrition (optional, freeform)"
                        autogrow
                        v-model="form.nutrition"
                    />

                    <q-separator />

                    <div class="text-subtitle1">Ingredients</div>
                    <div
                        class="row items-center q-col-gutter-sm q-mb-sm"
                        v-for="(ingredient, idx) in form.ingredients"
                        :key="idx"
                    >
                        <q-select
                            class="col-12 col-sm-4"
                            dense
                            outlined
                            label="Stock item"
                            v-model="ingredient.stock_item_id"
                            :options="stockItemOptions"
                            emit-value
                            map-options
                            :rules="[(v: string) => !!v || 'Required']"
                        />
                        <q-input
                            class="col-6 col-sm-2"
                            dense
                            outlined
                            label="Qty"
                            type="number"
                            v-model.number="ingredient.quantity"
                        />
                        <q-input
                            class="col-6 col-sm-2"
                            dense
                            outlined
                            label="Unit"
                            v-model="ingredient.unit"
                        />
                        <q-input
                            class="col-10 col-sm-3"
                            dense
                            outlined
                            label="Notes"
                            v-model="ingredient.notes"
                        />
                        <q-btn
                            class="col-2 col-sm-1"
                            flat
                            round
                            dense
                            icon="delete"
                            color="negative"
                            @click="removeIngredient(idx)"
                        />
                    </div>
                    <q-btn flat icon="add" label="Add ingredient" @click="addIngredient" />

                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" @click="$emit('update:modelValue', false)" />
                        <q-btn type="submit" color="primary" label="Save" :loading="saving" />
                    </q-card-actions>
                </q-form>
            </q-card-section>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import type { Recipe } from 'src/models/recipe';
    import type { CreateRecipeIngredientCommand } from 'src/services/api/recipeApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, reactive, ref, watch } from 'vue';

    const props = defineProps<{ modelValue: boolean; recipe: Recipe | null }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'saved'): void;
    }>();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const { recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);

    type IngredientForm = CreateRecipeIngredientCommand;

    type RecipeForm = {
        name: string;
        category: string | null;
        cook_time_minutes: number | null;
        cuisine: string | null;
        difficulty: string | null;
        instructions: string | null;
        nutrition: string | null;
        prep_time_minutes: number | null;
        recipe_collection_id: string | null;
        servings: number | null;
        time_of_day: string | null;
        ingredients: IngredientForm[];
    };

    const emptyForm = (): RecipeForm => ({
        name: '',
        category: null,
        cook_time_minutes: null,
        cuisine: null,
        difficulty: null,
        instructions: null,
        nutrition: null,
        prep_time_minutes: null,
        recipe_collection_id: null,
        servings: null,
        time_of_day: null,
        ingredients: []
    });

    const form = reactive<RecipeForm>(emptyForm());
    const saving = ref(false);

    const stockItemOptions = computed(() =>
        stockItems.value.map((s) => ({ label: s.name, value: s.stock_item_id }))
    );
    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({ label: c.name, value: c.recipe_collection_id }))
    );

    watch(
        () => props.modelValue,
        (open) => {
            if (!open) return;
            Object.assign(form, emptyForm());
            if (props.recipe) {
                form.name = props.recipe.name;
                form.category = props.recipe.category;
                form.cook_time_minutes = props.recipe.cook_time_minutes;
                form.cuisine = props.recipe.cuisine;
                form.difficulty = props.recipe.difficulty;
                form.instructions = props.recipe.instructions;
                form.nutrition = props.recipe.nutrition;
                form.prep_time_minutes = props.recipe.prep_time_minutes;
                form.recipe_collection_id = props.recipe.recipe_collection_id;
                form.servings = props.recipe.servings;
                form.time_of_day = props.recipe.time_of_day;
                form.ingredients = props.recipe.ingredients.map((i) => ({
                    stock_item_id: i.stock_item_id,
                    quantity: i.quantity,
                    unit: i.unit,
                    notes: i.notes
                }));
            }
        }
    );

    function addIngredient() {
        form.ingredients.push({ stock_item_id: '', quantity: null, unit: null, notes: null });
    }

    function removeIngredient(idx: number) {
        form.ingredients.splice(idx, 1);
    }

    async function onSubmit() {
        saving.value = true;
        try {
            const ingredients = form.ingredients.filter((i) => !!i.stock_item_id);
            if (props.recipe) {
                await recipeStore.updateRecipeAsync({
                    recipe_id: props.recipe.recipe_id,
                    name: form.name,
                    category: form.category,
                    cook_time_minutes: form.cook_time_minutes,
                    cuisine: form.cuisine,
                    difficulty: form.difficulty,
                    instructions: form.instructions,
                    nutrition: form.nutrition,
                    prep_time_minutes: form.prep_time_minutes,
                    recipe_collection_id: form.recipe_collection_id,
                    servings: form.servings,
                    time_of_day: form.time_of_day,
                    ingredients
                });
            } else {
                await recipeStore.createRecipeAsync({
                    name: form.name,
                    category: form.category,
                    cook_time_minutes: form.cook_time_minutes,
                    cuisine: form.cuisine,
                    difficulty: form.difficulty,
                    instructions: form.instructions,
                    nutrition: form.nutrition,
                    prep_time_minutes: form.prep_time_minutes,
                    recipe_collection_id: form.recipe_collection_id,
                    servings: form.servings,
                    time_of_day: form.time_of_day,
                    ingredients
                });
            }
            emit('saved');
        } finally {
            saving.value = false;
        }
    }
</script>
