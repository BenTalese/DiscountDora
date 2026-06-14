<template>
    <BaseDialog
        :model-value="modelValue"
        card-style="width: 800px; max-width: 95vw"
        @update:model-value="emit('update:modelValue', $event)"
    >
            <q-card-section>
                <div class="text-h6">{{ plan ? 'Edit Meal Plan' : 'New Meal Plan' }}</div>
            </q-card-section>
            <q-card-section>
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <FormErrorSummary :message="generalError" />

                    <div class="row q-col-gutter-md">
                        <q-input
                            class="col-12 col-sm-6"
                            outlined
                            label="Name *"
                            v-model="form.name"
                            :error="!!fieldErrors.name"
                            :error-message="fieldErrors.name"
                            @update:model-value="clearField('name')"
                            :rules="[(v: string) => !!v || 'Required']"
                        />
                        <q-input
                            class="col-12 col-sm-6"
                            outlined
                            label="Start date (Monday) *"
                            type="date"
                            v-model="form.start_date"
                            :error="!!fieldErrors.start_date"
                            :error-message="fieldErrors.start_date"
                            @update:model-value="clearField('start_date')"
                        />
                    </div>

                    <q-separator />

                    <div class="text-subtitle2">Entries</div>
                    <div
                        v-for="(entry, idx) in form.entries"
                        :key="idx"
                        class="row q-col-gutter-sm items-center"
                    >
                        <q-input
                            class="col-12 col-sm-3"
                            dense
                            outlined
                            label="Date"
                            type="date"
                            v-model="entry.scheduled_for"
                        />
                        <q-select
                            class="col-6 col-sm-2"
                            dense
                            outlined
                            label="Slot"
                            v-model="entry.slot"
                            :options="slotOptions"
                        />
                        <q-select
                            class="col-12 col-sm-4"
                            dense
                            outlined
                            label="Meal"
                            v-model="entry.recipe_id"
                            :options="mealOptions"
                            emit-value
                            map-options
                        />
                        <q-input
                            class="col-6 col-sm-2"
                            dense
                            outlined
                            label="Servings"
                            type="number"
                            v-model.number="entry.servings"
                            min="1"
                        />
                        <BaseButton
                            class="col-12 col-sm-1 text-negative"
                            variant="icon"
                            :icon="ICONS.delete"
                            @click="removeEntry(idx)"
                        />
                    </div>
                    <BaseButton variant="ghost" :icon="ICONS.add" label="Add entry" @click="addEntry" />

                    <q-card-actions align="right">
                        <BaseButton variant="ghost" label="Cancel" @click="emit('update:modelValue', false)" />
                        <BaseButton type="submit" variant="primary" label="Save" :loading="saving" />
                    </q-card-actions>
                </q-form>
            </q-card-section>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import type { MealPlan } from 'src/models/mealPlan';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { DEFAULT_MEAL_SLOTS } from 'src/helpers/recipeVocabulary';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';

    const props = defineProps<{ modelValue: boolean; plan: MealPlan | null }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', v: boolean): void;
        (e: 'saved'): void;
    }>();

    const mealPlanStore = useMealPlanStore();
    const mealSlotStore = useMealSlotStore();
    const recipeStore = useRecipeStore();
    const { recipes } = storeToRefs(recipeStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);

    const mealOptions = computed(() =>
        recipes.value.map((r) => ({ label: r.name, value: r.recipe_id }))
    );

    // C-2.A — household meal-slot vocabulary (restores "Dessert"). Falls back
    // to the seed constant only until the store's first load lands.
    const slotOptions = computed(() =>
        mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );

    onMounted(() => {
        void mealSlotStore.getMealSlotsAsync().catch(() => undefined);
    });

    type Form = { name: string; start_date: string; entries: MealPlanEntryCommand[] };

    function todayIso(): string {
        const d = new Date();
        const monday = new Date(d);
        monday.setDate(d.getDate() - d.getDay() + (d.getDay() === 0 ? -6 : 1));
        return monday.toISOString().slice(0, 10);
    }

    const emptyForm = (): Form => ({ name: '', start_date: todayIso(), entries: [] });
    const form = reactive<Form>(emptyForm());
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

    watch(
        () => props.modelValue,
        (open) => {
            if (!open) return;
            Object.assign(form, emptyForm());
            generalError.value = null;
            fieldErrors.value = {};
            if (props.plan) {
                form.name = props.plan.name;
                form.start_date = props.plan.start_date;
                form.entries = props.plan.entries
                    .filter((e) => !e.consumed_at)
                    .map((e) => ({
                        recipe_id: e.recipe_id,
                        scheduled_for: e.scheduled_for,
                        servings: e.servings,
                        slot: e.slot
                    }));
            }
        }
    );

    function addEntry() {
        form.entries.push({
            recipe_id: '',
            scheduled_for: form.start_date,
            servings: 1,
            slot: 'Dinner'
        });
    }

    function removeEntry(idx: number) {
        form.entries.splice(idx, 1);
    }

    async function onSubmit() {
        saving.value = true;
        generalError.value = null;
        fieldErrors.value = {};
        try {
            const entries = form.entries.filter((e) => !!e.recipe_id);
            if (props.plan) {
                // Backend refuses entries=[] without an explicit
                // confirm_clear_entries flag so a UI bug can't silently
                // wipe a plan. The dialog is the explicit path, so set
                // the flag when the user has emptied the list.
                await mealPlanStore.updateMealPlanAsync({
                    meal_plan_id: props.plan.meal_plan_id,
                    name: form.name,
                    start_date: form.start_date,
                    entries,
                    ...(entries.length === 0 ? { confirm_clear_entries: true } : {}),
                });
            } else {
                await mealPlanStore.createMealPlanAsync({
                    name: form.name,
                    start_date: form.start_date,
                    entries
                });
            }
            emit('saved');
        } catch (err) {
            const extracted = extractFieldErrors(err);
            fieldErrors.value = extracted.fieldErrors;
            generalError.value =
                extracted.generalError ?? 'Could not save the meal plan. Please review the form.';
        } finally {
            saving.value = false;
        }
    }
</script>
