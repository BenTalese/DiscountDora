<template>
    <BaseDialog
        :model-value="modelValue"
        :title="recipe ? 'Edit Recipe' : 'New Recipe'"
        closable
        card-style="width: 800px; max-width: 95vw"
        @update:model-value="$emit('update:modelValue', $event)"
    >
            <q-card-section>
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <FormErrorSummary :message="generalError" />

                    <q-input
                        outlined
                        label="Name *"
                        v-model="form.name"
                        :error="!!fieldErrors.name"
                        :error-message="fieldErrors.name"
                        @update:model-value="clearField('name')"
                        :rules="[(v: string) => !!v || 'Name is required']"
                        autofocus
                    />

                    <!-- L255/L260 — cuisine + category are distinct
                         single-selects sourced from the editable vocab
                         tables (no longer free-text). -->
                    <div class="row q-col-gutter-md">
                        <q-select
                            class="col-12 col-sm-6"
                            outlined
                            label="Cuisine"
                            v-model="form.cuisine_id"
                            :options="cuisineOptions"
                            emit-value
                            map-options
                            clearable
                        />
                        <q-select
                            class="col-12 col-sm-6"
                            outlined
                            label="Category"
                            v-model="form.category_id"
                            :options="categoryOptions"
                            emit-value
                            map-options
                            clearable
                        />
                    </div>

                    <div class="row q-col-gutter-md">
                        <q-select
                            class="col-12 col-sm-4"
                            outlined
                            label="Time of Day"
                            v-model="form.time_of_day"
                            :options="timeOfDayOptions"
                            clearable
                        />
                        <q-select
                            class="col-12 col-sm-4"
                            outlined
                            label="Difficulty"
                            v-model="form.difficulty"
                            :options="difficultyOptions"
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

                    <!-- C-4 Chunk 2 — dietary tag editor. Multi-select chips
                         drawn from the editable DietaryTag vocabulary
                         (option value = tag id). Disclaimer keeps the framing
                         honest: tags are a planning aid, not a safety claim. -->
                    <div>
                        <q-select
                            outlined
                            multiple
                            use-chips
                            emit-value
                            map-options
                            v-model="form.dietary_tag_ids"
                            :options="tagOptionsByCategory"
                            label="Dietary tags (optional)"
                        />
                        <div
                            v-if="tagCatalogue?.disclaimer"
                            class="text-caption dora-text-muted q-mt-xs"
                        >
                            <q-icon name="info" size="14px" class="q-mr-xs" />
                            {{ tagCatalogue.disclaimer }}
                        </div>
                    </div>

                    <!-- C-4 Chunk 5 — tools (multi-select) + image. -->
                    <q-select
                        outlined
                        multiple
                        use-chips
                        emit-value
                        map-options
                        v-model="form.tool_ids"
                        :options="toolOptions"
                        label="Tools (optional)"
                    />

                    <ImageUploadField
                        :preview-url="form.image"
                        :name="form.name"
                        alt="Recipe image"
                        @pick="(url) => { form.image = url; }"
                        @clear="() => { form.image = null; }"
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
                            class="col-10 col-sm-2"
                            dense
                            outlined
                            label="Notes"
                            v-model="ingredient.notes"
                        />
                        <q-checkbox
                            class="col-auto col-sm-1"
                            v-model="ingredient.is_optional"
                            label="Optional"
                            dense
                        >
                            <q-tooltip>
                                Optional ingredients don't affect whether the recipe is cookable.
                            </q-tooltip>
                        </q-checkbox>
                        <BaseButton
                            class="col-2 col-sm-1 text-negative"
                            variant="icon"
                            :icon="ICONS.delete"
                            @click="removeIngredient(idx)"
                        />
                    </div>
                    <BaseButton variant="ghost" :icon="ICONS.add" label="Add ingredient" @click="addIngredient" />

                </q-form>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" @click="$emit('update:modelValue', false)" />
                <BaseButton variant="primary" label="Save" :loading="saving" @click="onSubmit" />
            </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
    import RecipeApiService, {
        type CreateRecipeIngredientCommand,
    } from 'src/services/api/recipeApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import {
        DEFAULT_MEAL_SLOTS,
        DIFFICULTY_VALUES,
    } from 'src/helpers/recipeVocabulary';
    import { computed, onMounted, reactive, ref, watch } from 'vue';

    const difficultyOptions = [...DIFFICULTY_VALUES];

    const props = defineProps<{ modelValue: boolean; recipe: Recipe | null }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'saved'): void;
    }>();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const recipeVocabStore = useRecipeVocabStore();
    const mealSlotStore = useMealSlotStore();
    const { recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { cuisines, categories, tools } = storeToRefs(recipeVocabStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);

    // C-2.A — `time_of_day` reads the household meal-slot vocabulary; falls
    // back to the seed constant only before the store's first load.
    const timeOfDayOptions = computed(() =>
        mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );

    type IngredientForm = CreateRecipeIngredientCommand;

    type RecipeForm = {
        name: string;
        category_id: string | null;
        cook_time_minutes: number | null;
        cuisine_id: string | null;
        difficulty: string | null;
        instructions: string | null;
        nutrition: string | null;
        prep_time_minutes: number | null;
        recipe_collection_id: string | null;
        servings: number | null;
        time_of_day: string | null;
        ingredients: IngredientForm[];
        dietary_tag_ids: string[];
        tool_ids: string[];
        image: string | null;
    };

    const emptyForm = (): RecipeForm => ({
        name: '',
        category_id: null,
        cook_time_minutes: null,
        cuisine_id: null,
        difficulty: null,
        instructions: null,
        nutrition: null,
        prep_time_minutes: null,
        recipe_collection_id: null,
        servings: null,
        time_of_day: null,
        ingredients: [],
        dietary_tag_ids: [],
        tool_ids: [],
        image: null,
    });

    const form = reactive<RecipeForm>(emptyForm());
    const saving = ref(false);
    const generalError = ref<string | null>(null);
    const fieldErrors = ref<Record<string, string>>({});

    function clearField(field: string) {
        if (fieldErrors.value[field]) {
            const next = { ...fieldErrors.value };
            delete next[field];
            fieldErrors.value = next;
        }
    }

    const stockItemOptions = computed(() =>
        stockItems.value.map((s) => ({ label: s.name, value: s.stock_item_id }))
    );
    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({ label: c.name, value: c.recipe_collection_id }))
    );
    // C-4 Chunk 2 — cuisine/category single-selects sourced from the vocab store.
    const cuisineOptions = computed(() =>
        cuisines.value.map((c) => ({ label: c.name, value: c.cuisine_id })),
    );
    const categoryOptions = computed(() =>
        categories.value.map((c) => ({ label: c.name, value: c.category_id })),
    );
    const toolOptions = computed(() =>
        tools.value.map((t) => ({ label: t.name, value: t.tool_id })),
    );

    // Dietary tag catalogue (value = tag id). Labels are prefixed with the
    // grouping category so a flat single-list q-select still reads as grouped
    // ("Dietary pattern: Vegan", "Allergen-free: Gluten-free", …).
    const recipeApi = new RecipeApiService();
    const tagCatalogue = ref<RecipeTagCatalogue | null>(null);
    const tagOptionsByCategory = computed(() =>
        (tagCatalogue.value?.tags ?? []).map((t) => ({
            label: `${t.category}: ${t.label}`,
            value: t.value,
        })),
    );

    onMounted(async () => {
        // Vocab lists for the cuisine/category selects (load if not already cached).
        recipeVocabStore.getAllAsync().catch(() => undefined);
        mealSlotStore.getMealSlotsAsync().catch(() => undefined);
        try {
            tagCatalogue.value = await recipeApi.getTagCatalogueAsync();
        } catch {
            // Non-fatal — the picker just renders empty if the
            // catalogue endpoint isn't available.
            tagCatalogue.value = null;
        }
    });

    watch(
        () => props.modelValue,
        (open) => {
            if (!open) return;
            Object.assign(form, emptyForm());
            generalError.value = null;
            fieldErrors.value = {};
            if (props.recipe) {
                form.name = props.recipe.name;
                form.category_id = props.recipe.category_id;
                form.cook_time_minutes = props.recipe.cook_time_minutes;
                form.cuisine_id = props.recipe.cuisine_id;
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
                    notes: i.notes,
                    is_optional: i.is_optional ?? false,
                }));
                form.dietary_tag_ids = [...(props.recipe.dietary_tag_ids ?? [])];
                form.tool_ids = [...(props.recipe.tool_ids ?? [])];
                // Image isn't loaded into the create/edit dialog (it lives on
                // the detail page); leave form.image null so an edit here never
                // clobbers an existing image.
            }
        }
    );

    function addIngredient() {
        form.ingredients.push({
            stock_item_id: '',
            quantity: null,
            unit: null,
            notes: null,
            is_optional: false,
        });
    }

    function removeIngredient(idx: number) {
        form.ingredients.splice(idx, 1);
    }

    async function onSubmit() {
        saving.value = true;
        generalError.value = null;
        fieldErrors.value = {};
        try {
            const ingredients = form.ingredients.filter((i) => !!i.stock_item_id);
            if (props.recipe) {
                await recipeStore.updateRecipeAsync({
                    recipe_id: props.recipe.recipe_id,
                    name: form.name,
                    category_id: form.category_id,
                    cook_time_minutes: form.cook_time_minutes,
                    cuisine_id: form.cuisine_id,
                    difficulty: form.difficulty,
                    instructions: form.instructions,
                    nutrition: form.nutrition,
                    prep_time_minutes: form.prep_time_minutes,
                    recipe_collection_id: form.recipe_collection_id,
                    servings: form.servings,
                    time_of_day: form.time_of_day,
                    ingredients,
                    dietary_tag_ids: form.dietary_tag_ids,
                    tool_ids: form.tool_ids,
                    // image deliberately omitted on edit (managed on detail page).
                });
            } else {
                await recipeStore.createRecipeAsync({
                    name: form.name,
                    category_id: form.category_id,
                    cook_time_minutes: form.cook_time_minutes,
                    cuisine_id: form.cuisine_id,
                    difficulty: form.difficulty,
                    instructions: form.instructions,
                    nutrition: form.nutrition,
                    prep_time_minutes: form.prep_time_minutes,
                    recipe_collection_id: form.recipe_collection_id,
                    servings: form.servings,
                    time_of_day: form.time_of_day,
                    ingredients,
                    dietary_tag_ids: form.dietary_tag_ids,
                    tool_ids: form.tool_ids,
                    image: form.image,
                });
            }
            emit('saved');
        } catch (err) {
            const extracted = extractFieldErrors(err);
            fieldErrors.value = extracted.fieldErrors;
            generalError.value =
                extracted.generalError ?? 'Could not save the recipe. Please review the form.';
        } finally {
            saving.value = false;
        }
    }
</script>
