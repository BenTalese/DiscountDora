<template>
    <BaseDialog
        :model-value="modelValue"
        title="Plan step-by-step"
        closable
        card-style="min-width: 480px; max-width: 95vw"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <q-card-section class="q-pt-none">
            <q-stepper v-model="step" flat animated>
                <q-step :name="1" title="Pick meals" :icon="ICONS.restaurant" :done="step > 1">
                    <div class="text-caption dora-text-muted q-mb-sm">
                        Choose the meals you want to cook this week
                        ({{ selectedIds.length }} / {{ targetCount }}).
                    </div>
                    <q-list bordered separator class="builder-list rounded-borders">
                        <q-item v-for="r in recipes" :key="r.recipe_id" tag="label">
                            <q-item-section side>
                                <q-checkbox
                                    :model-value="selectedIds.includes(r.recipe_id)"
                                    @update:model-value="toggle(r.recipe_id)"
                                />
                            </q-item-section>
                            <q-item-section>{{ r.name }}</q-item-section>
                        </q-item>
                        <q-item v-if="recipes.length === 0">
                            <q-item-section class="dora-text-muted text-center">No recipes yet.</q-item-section>
                        </q-item>
                    </q-list>
                </q-step>

                <q-step :name="2" title="What you'll need" :icon="ICONS.shopping_cart" :done="step > 2">
                    <div v-if="previewLoading" class="text-caption dora-text-muted">Calculating…</div>
                    <template v-else>
                        <div class="text-subtitle2">
                            {{ needToBuyCount }} to buy · {{ previewIngredients.length - needToBuyCount }} in stock
                        </div>
                        <q-list dense separator class="q-mt-xs builder-list">
                            <q-item v-for="ing in previewIngredients" :key="ing.stock_item_id">
                                <q-item-section>
                                    <q-item-label>{{ ing.stock_item_name }}</q-item-label>
                                    <q-item-label caption v-if="ing.total_quantity !== null">
                                        needs {{ round(ing.total_quantity) }} {{ ing.unit ?? '' }}
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
                                        {{ stockStatusLabel(ing.stock_item_id) }}
                                    </q-chip>
                                </q-item-section>
                            </q-item>
                            <q-item v-if="previewIngredients.length === 0">
                                <q-item-section class="dora-text-muted text-center">
                                    These meals don't list any ingredients.
                                </q-item-section>
                            </q-item>
                        </q-list>
                        <div class="text-caption dora-text-muted q-mt-sm">
                            Tip: go Back to untick a meal and drop its ingredients.
                        </div>
                    </template>
                </q-step>

                <q-step :name="3" title="Build" :icon="ICONS.check">
                    <div v-if="!doneState">
                        <div class="text-subtitle2">
                            Ready to plan {{ selectedIds.length }} meal{{ selectedIds.length === 1 ? '' : 's' }}.
                        </div>
                        <div class="text-caption dora-text-muted q-mt-xs">
                            They'll be added across the upcoming days of the week you're viewing; then
                            you can generate the shopping list.
                        </div>
                    </div>
                    <div v-else class="column q-gutter-sm items-start">
                        <div class="text-subtitle2">All set — {{ selectedIds.length }} meal(s) planned.</div>
                        <div class="row q-gutter-sm">
                            <q-btn no-caps outline color="primary" :icon="ICONS.print" label="Print this week" @click="printWeek" />
                            <q-btn no-caps outline disable label="Email">
                                <q-tooltip>Emailing your plan isn't set up yet.</q-tooltip>
                            </q-btn>
                        </div>
                    </div>
                </q-step>
            </q-stepper>
        </q-card-section>

        <template #actions>
            <q-btn v-if="!doneState" flat no-caps label="Cancel" v-close-popup />
            <q-space />
            <q-btn v-if="step > 1 && !doneState" flat no-caps label="Back" @click="step = step - 1" />
            <q-btn v-if="step === 1" color="primary" no-caps label="Next" :disable="selectedIds.length === 0" @click="goToPreview" />
            <q-btn v-if="step === 2" color="primary" no-caps label="Next" @click="step = 3" />
            <q-btn
                v-if="step === 3 && !doneState"
                color="primary" no-caps label="Build & generate list"
                :loading="building"
                @click="onBuild"
            />
            <q-btn v-if="doneState" color="primary" no-caps label="Done" v-close-popup />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type { MealPlanIngredient } from 'src/models/mealPlan';
    import type { Recipe } from 'src/models/recipe';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        recipes: Recipe[];
        targetCount: number;
        /** Writes the picked meals onto the focused week + generates the list. */
        buildPlan: (recipeIds: string[]) => Promise<void>;
        /** Opens the print view for the focused week. */
        printWeek: () => void;
    }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const api = new MealPlanApiService();
    const { stockStatusLabel, stockStatusColour, needsBuying } = useStockStatus();

    const step = ref(1);
    const selectedIds = ref<string[]>([]);
    const previewIngredients = ref<MealPlanIngredient[]>([]);
    const previewLoading = ref(false);
    const building = ref(false);
    const doneState = ref(false);

    const needToBuyCount = computed(
        () => previewIngredients.value.filter((i) => needsBuying(i.stock_item_id)).length,
    );

    function toggle(id: string) {
        selectedIds.value = selectedIds.value.includes(id)
            ? selectedIds.value.filter((x) => x !== id)
            : [...selectedIds.value, id];
    }
    function round(n: number): number {
        return Math.round(n * 100) / 100;
    }

    async function goToPreview() {
        step.value = 2;
        previewLoading.value = true;
        try {
            previewIngredients.value = await api.previewIngredientsAsync(
                selectedIds.value.map((id) => ({ recipe_id: id, servings: 1 })),
            );
        } finally {
            previewLoading.value = false;
        }
    }

    async function onBuild() {
        building.value = true;
        try {
            await props.buildPlan(selectedIds.value);
            doneState.value = true;
        } finally {
            building.value = false;
        }
    }

    // Reset whenever the dialog (re)opens.
    watch(() => props.modelValue, (open) => {
        if (open) {
            step.value = 1;
            selectedIds.value = [];
            previewIngredients.value = [];
            doneState.value = false;
        }
    });
</script>

<style scoped>
    .builder-list {
        max-height: 45vh;
        overflow-y: auto;
    }
</style>
