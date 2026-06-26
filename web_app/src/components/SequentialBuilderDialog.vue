<template>
    <BaseDialog
        :model-value="modelValue"
        title="Plan step-by-step"
        closable
        card-style="min-width: 560px; max-width: 95vw"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <q-card-section class="q-pt-none">
            <q-stepper v-model="step" flat animated>
                <q-step :name="1" title="Pick meals" :icon="ICONS.restaurant" :done="step > 1">
                    <div class="text-caption dora-text-muted q-mb-sm">
                        Choose the meals you want to cook this week
                        ({{ selectedIds.length }} / {{ targetCount }}).
                    </div>
                    <!-- §9-B — same picker the planner uses (search + trays).
                        Multi-select mode keeps a checkbox per row. -->
                    <div class="builder-picker">
                        <MealPlanRecipePicker
                            v-model:recipe-search="recipeSearch"
                            v-model:selected-ids="selectedIds"
                            selection-mode="multi-select"
                            :trays="trays"
                            :recipes="recipes"
                            :focused-target="null"
                            :drag-allowed="false"
                            :format-date="formatDate"
                            :log-cook="noopLogCook"
                        />
                    </div>
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
                            They'll be added across the upcoming days of the week you're viewing.
                            You can generate the shopping list straight after.
                        </div>
                    </div>
                    <div v-else class="column q-gutter-sm items-start">
                        <div class="text-subtitle2">All set — {{ selectedIds.length }} meal(s) planned.</div>
                        <div class="row q-gutter-sm">
                            <BaseButton
                                :icon="ICONS.shopping_cart"
                                label="Generate shopping list"
                                :loading="generatingList"
                                @click="onGenerateList"
                            />
                            <BaseButton variant="secondary" :icon="ICONS.print" label="Print this week" @click="printWeek" />
                        </div>
                    </div>
                </q-step>
            </q-stepper>
        </q-card-section>

        <template #actions>
            <BaseButton v-if="!doneState" variant="ghost" label="Cancel" v-close-popup />
            <q-space />
            <BaseButton v-if="step > 1 && !doneState" variant="ghost" label="Back" @click="step = step - 1" />
            <BaseButton v-if="step === 1" label="Next" :disable="selectedIds.length === 0" @click="goToPreview" />
            <BaseButton v-if="step === 2" label="Next" @click="step = 3" />
            <BaseButton
                v-if="step === 3 && !doneState"
                label="Build plan"
                :loading="building"
                @click="onBuild"
            />
            <BaseButton v-if="doneState" label="Done" v-close-popup />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import type { RecipeTray } from 'src/composables/useMealPlanner';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type { MealPlanIngredient } from 'src/models/mealPlan';
    import type { Recipe } from 'src/models/recipe';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        recipes: Recipe[];
        targetCount: number;
        /** Writes the picked meals onto the focused week. */
        buildPlan: (recipeIds: string[]) => Promise<void>;
        /** Opens the C-7 target picker and generates the list for the focused week. */
        generateList: () => Promise<void>;
        /** Opens the print view for the focused week. */
        printWeek: () => void;
    }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const api = new MealPlanApiService();
    const { stockStatusLabel, stockStatusColour, needsBuying } = useStockStatus();

    const step = ref(1);
    const selectedIds = ref<string[]>([]);
    const recipeSearch = ref('');
    const previewIngredients = ref<MealPlanIngredient[]>([]);
    const previewLoading = ref(false);
    const building = ref(false);
    const generatingList = ref(false);
    const doneState = ref(false);

    // §9-B — local tray computation. Reuses the same favourites / haven't-had /
    // frequently-planned / all-recipes structure the planner picker shows, so
    // browsing recipes here feels identical to the rail. (Server-derived
    // signals: is_favourite, not_made_recently, plan_count — R-003.)
    const TRAY_CAP = 10;
    const filteredRecipes = computed(() => {
        const q = recipeSearch.value?.trim().toLowerCase() ?? '';
        if (!q) return props.recipes;
        return props.recipes.filter((r) => r.name.toLowerCase().includes(q));
    });
    const trays = computed<RecipeTray[]>(() => {
        if (recipeSearch.value?.trim()) {
            return [{
                key: 'results',
                title: `Results (${filteredRecipes.value.length})`,
                recipes: filteredRecipes.value,
                defaultOpen: true,
            }];
        }
        const all = props.recipes;
        const out: RecipeTray[] = [];
        const favs = all.filter((r) => r.is_favourite);
        if (favs.length) out.push({ key: 'fav', title: 'Favourites', recipes: favs, defaultOpen: true });
        const stale = all
            .filter((r) => r.not_made_recently)
            .sort((a, b) => madeMs(a) - madeMs(b))
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

    const needToBuyCount = computed(
        () => previewIngredients.value.filter((i) => needsBuying(i.stock_item_id)).length,
    );

    function round(n: number): number {
        return Math.round(n * 100) / 100;
    }
    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString();
    }
    function noopLogCook(): Promise<number> {
        // The picker's log-cook control is hidden in multi-select mode, so this
        // never fires — but the prop is required by the picker contract.
        return Promise.resolve(0);
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
            // §9-B — build is now decoupled from generate-list. Generating the
            // list is an explicit, optional follow-up on the done step.
            await props.buildPlan(selectedIds.value);
            doneState.value = true;
        } finally {
            building.value = false;
        }
    }

    async function onGenerateList() {
        generatingList.value = true;
        try {
            await props.generateList();
        } finally {
            generatingList.value = false;
        }
    }

    // Reset whenever the dialog (re)opens.
    watch(() => props.modelValue, (open) => {
        if (open) {
            step.value = 1;
            selectedIds.value = [];
            recipeSearch.value = '';
            previewIngredients.value = [];
            doneState.value = false;
        }
    });
</script>

<style scoped>
    .builder-picker {
        max-height: 50vh;
        overflow-y: auto;
        border: 1px solid var(--separator);
        border-radius: 6px;
    }
    .builder-list {
        max-height: 45vh;
        overflow-y: auto;
    }
</style>
