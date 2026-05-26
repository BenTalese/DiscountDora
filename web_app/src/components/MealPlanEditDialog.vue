<template>
    <q-dialog :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" persistent>
        <q-card style="width: 800px; max-width: 95vw">
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
                            :options="['Breakfast', 'Lunch', 'Dinner', 'Snack']"
                        />
                        <q-select
                            class="col-12 col-sm-4"
                            dense
                            outlined
                            label="Meal"
                            v-model="entry.meal_id"
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
                        <q-btn
                            class="col-12 col-sm-1"
                            flat
                            round
                            dense
                            :icon="ICONS.delete"
                            color="negative"
                            @click="removeEntry(idx)"
                        />
                    </div>
                    <q-btn flat :icon="ICONS.add" label="Add entry" @click="addEntry" />

                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" @click="emit('update:modelValue', false)" />
                        <q-btn type="submit" color="primary" label="Save" :loading="saving" />
                    </q-card-actions>
                </q-form>
            </q-card-section>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import type { MealPlan } from 'src/models/meal';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useMealStore } from 'src/stores/mealStore';
    import { computed, reactive, ref, watch } from 'vue';

    const props = defineProps<{ modelValue: boolean; plan: MealPlan | null }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', v: boolean): void;
        (e: 'saved'): void;
    }>();

    const mealStore = useMealStore();
    const { meals } = storeToRefs(mealStore);

    const mealOptions = computed(() =>
        meals.value.map((m) => ({ label: m.name, value: m.meal_id }))
    );

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
                form.entries = props.plan.entries.map((e) => ({
                    meal_id: e.meal_id,
                    scheduled_for: e.scheduled_for,
                    servings: e.servings,
                    slot: e.slot
                }));
            }
        }
    );

    function addEntry() {
        form.entries.push({
            meal_id: '',
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
            const entries = form.entries.filter((e) => !!e.meal_id);
            if (props.plan) {
                await mealStore.updateMealPlanAsync({
                    meal_plan_id: props.plan.meal_plan_id,
                    name: form.name,
                    start_date: form.start_date,
                    entries
                });
            } else {
                await mealStore.createMealPlanAsync({
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
