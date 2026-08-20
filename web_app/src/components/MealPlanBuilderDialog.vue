<template>
    <BaseDialog
        :model-value="modelValue"
        title="Build my week"
        closable
        card-style="min-width: 560px; max-width: 95vw"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <q-card-section class="q-pt-none">
            <q-stepper v-model="step" flat animated>
                <!-- ── Step 1 — Guide ─────────────────────────────────────── -->
                <q-step :name="1" title="Guide" :icon="ICONS.auto_awesome" :done="step > 1">
                    <div class="text-caption dora-text-muted q-mb-md">
                        Tell Dora what you're after and she'll build a plan. You can
                        tweak everything before it's saved.
                    </div>

                    <div class="builder-field">
                        <BaseToggleGroup
                            v-model="selectedDays"
                            label="Which days"
                            :options="dayToggleOptions"
                        />
                    </div>

                    <div class="builder-field">
                        <BaseToggleGroup
                            v-model="selectedSlots"
                            label="Which meals"
                            :options="slotToggleOptions"
                        />
                    </div>

                    <div v-if="selectedDays.length > 1" class="builder-field">
                        <q-checkbox
                            v-model="repeatSameDay"
                            dense
                            label="Same meals every day"
                        />
                        <div class="text-caption dora-text-muted q-mt-xs">
                            Builds one day's meals and repeats them across the days you picked.
                        </div>
                    </div>

                    <div class="builder-field">
                        <div class="builder-field__label">Emphasis</div>
                        <BaseSegmented v-model="emphasis" :options="emphasisOptions" dense />
                        <div class="text-caption dora-text-muted q-mt-xs">
                            {{ emphasisHint }}
                        </div>
                    </div>

                    <div v-if="moneyEnabled" class="builder-field">
                        <q-toggle
                            v-model="budgetCap"
                            dense
                            label="Keep the week under budget"
                        />
                    </div>

                    <div class="builder-field__label">{{ plannedCountHint }}</div>
                </q-step>

                <!-- ── Step 2 — Review ────────────────────────────────────── -->
                <q-step :name="2" title="Review" :icon="ICONS.restaurant" :done="step > 2">
                    <div class="row items-center q-mb-sm">
                        <div class="text-subtitle2">
                            {{ proposed.length }} meal{{ proposed.length === 1 ? '' : 's' }}
                        </div>
                        <q-space />
                        <BaseButton
                            variant="ghost" dense
                            :icon="ICONS.refresh"
                            label="Reshuffle"
                            :loading="generatingProposal"
                            @click="generate"
                        />
                    </div>

                    <div v-if="showShortfallHint" class="builder-hint">
                        <q-icon :name="ICONS.info" size="18px" class="builder-hint__icon" />
                        <div>
                            Dora planned {{ lastBuildPlaced }} of the {{ lastBuildRequested }}
                            meals you picked. Each meal uses a different recipe, and there
                            weren’t enough to fill them all — so some days are still empty.
                            Add more recipes, choose fewer days or meals, or tick
                            <strong>Same meals every day</strong> to reuse recipes.
                        </div>
                    </div>

                    <div v-if="proposed.length === 0" class="dora-text-muted text-center q-py-md text-caption">
                        No meals yet — reshuffle, or add your own below.
                    </div>

                    <template v-for="group in groupedByDay" :key="group.iso">
                        <div v-if="group.entries.length" class="builder-day">
                            <div class="builder-day__label">{{ group.label }}</div>
                            <div
                                v-for="entry in group.entries"
                                :key="entry._key"
                                class="builder-row"
                            >
                                <div class="builder-row__main">
                                    <div class="builder-row__name">{{ entry.recipe_name }}</div>
                                    <div class="builder-row__meta">
                                        <span
                                            v-if="cookMarker(entry)"
                                            class="builder-cook"
                                            :class="{ 'builder-cook--leftover': cookMarker(entry) === 'leftover' }"
                                        >
                                            <q-icon :name="ICONS.link" size="12px" />
                                            {{ cookMarker(entry) === 'cook' ? 'Cook once' : 'Leftovers' }}
                                        </span>
                                        <q-chip dense square class="builder-reason">
                                            {{ reasonLabel(entry.reason_chip) }}
                                        </q-chip>
                                        <span
                                            v-if="entry.estimated_cost != null && moneyEnabled"
                                            class="dora-text-muted text-caption"
                                        >
                                            ~{{ money(entry.estimated_cost) }}
                                        </span>
                                        <span
                                            v-else-if="entry.cookable === true"
                                            class="dora-text-muted text-caption"
                                        >
                                            You have everything
                                        </span>
                                    </div>
                                </div>
                                <div class="builder-row__controls">
                                    <q-select
                                        v-if="dayOptions.length > 1"
                                        v-model="entry.scheduled_for"
                                        outlined dense options-dense emit-value map-options
                                        class="builder-day-select"
                                        :options="dayOptions"
                                    >
                                        <q-tooltip>Move to another day</q-tooltip>
                                    </q-select>
                                    <q-select
                                        v-model="entry.slot"
                                        outlined dense options-dense
                                        class="builder-slot-select"
                                        :options="slotNames"
                                    >
                                        <q-tooltip>Which meal slot</q-tooltip>
                                    </q-select>
                                    <div class="builder-servings">
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.remove"
                                            :disable="entry.servings <= 1"
                                            @click="entry.servings = Math.max(1, entry.servings - 1)"
                                        />
                                        <span class="builder-servings__count">{{ entry.servings }}</span>
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.add"
                                            @click="entry.servings = entry.servings + 1"
                                        />
                                        <q-tooltip>Servings</q-tooltip>
                                    </div>
                                    <BaseButton
                                        variant="icon" dense
                                        :icon="ICONS.swap_horiz"
                                        @click="openSwap(entry)"
                                    >
                                        <q-tooltip>Swap for another recipe</q-tooltip>
                                    </BaseButton>
                                    <BaseButton
                                        variant="icon" dense
                                        :icon="ICONS.delete_outline"
                                        @click="removeEntry(entry)"
                                    >
                                        <q-tooltip>Remove</q-tooltip>
                                    </BaseButton>
                                </div>
                            </div>
                        </div>
                    </template>

                    <BaseButton
                        variant="secondary" dense class="q-mt-sm"
                        :icon="ICONS.add"
                        label="Add a meal"
                        @click="openAdd"
                    />

                    <!-- What you'll need (aggregate ingredient demand) -->
                    <q-separator class="q-my-md" />
                    <div class="text-subtitle2">What you'll need</div>
                    <div v-if="previewLoading" class="text-caption dora-text-muted">Calculating…</div>
                    <template v-else>
                        <div class="text-caption dora-text-muted q-mb-xs">
                            {{ needToBuyCount }} to buy ·
                            {{ Math.max(previewIngredients.length - needToBuyCount, 0) }} in stock
                        </div>
                        <q-list dense separator class="builder-list">
                            <q-item v-for="ing in previewIngredients" :key="ing.stock_item_id">
                                <q-item-section>
                                    <q-item-label>{{ ing.stock_item_name }}</q-item-label>
                                    <q-item-label caption v-if="ing.total_quantity !== null">
                                        needs {{ formatQuantity(round(ing.total_quantity), ing.unit) }}
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <q-chip
                                        dense
                                        :color="stockStatusColour(ing.stock_item_id) ?? undefined"
                                        :text-color="stockStatusColour(ing.stock_item_id) ? 'white' : undefined"
                                        :class="{ 'dora-bg-sunken dora-text-secondary': !stockStatusColour(ing.stock_item_id) }"
                                    >
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
                    </template>
                </q-step>

                <!-- ── Step 3 — Done ──────────────────────────────────────── -->
                <q-step :name="3" title="Done" :icon="ICONS.check">
                    <div v-if="!doneState">
                        <div class="text-subtitle2">
                            Ready to save {{ proposed.length }} meal{{ proposed.length === 1 ? '' : 's' }}.
                        </div>
                        <div class="text-caption dora-text-muted q-mt-xs">
                            They'll be added to {{ targetLabel }}.
                            You can generate the shopping list straight after.
                        </div>
                    </div>
                    <div v-else class="column q-gutter-sm items-start">
                        <div class="text-subtitle2">All set — {{ proposed.length }} meal(s) planned.</div>
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
            <!-- Step 1: primary generate, plus a manual "pick myself" escape. -->
            <BaseButton
                v-if="step === 1"
                variant="ghost"
                label="I'll pick myself"
                @click="startManual"
            />
            <BaseButton
                v-if="step === 1"
                :icon="ICONS.auto_awesome"
                label="Build my week"
                :loading="generatingProposal"
                :disable="!canGenerate"
                @click="generate"
            />
            <BaseButton
                v-if="step === 2"
                label="Next"
                :disable="proposed.length === 0"
                @click="step = 3"
            />
            <BaseButton
                v-if="step === 3 && !doneState"
                label="Save plan"
                :loading="building"
                :disable="proposed.length === 0"
                @click="onBuild"
            />
            <BaseButton v-if="doneState" label="Done" v-close-popup />
        </template>
    </BaseDialog>

    <!-- Add / swap recipe picker (click-add) ─────────────────────────────── -->
    <BaseDialog
        v-model="pickerOpen"
        :title="pickerMode === 'swap' ? 'Swap this meal' : 'Add a meal'"
        closable
        card-style="min-width: 460px; max-width: 95vw"
    >
        <q-card-section class="q-pt-none">
            <div class="builder-picker">
                <MealPlanRecipePicker
                    v-model:recipe-search="recipeSearch"
                    :trays="trays"
                    :recipes="recipes"
                    :focused-target="null"
                    :drag-allowed="false"
                    :format-date="formatDate"
                    :log-cook="noopLogCook"
                    @recipe-pick="onPickRecipe"
                />
            </div>
        </q-card-section>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import BaseToggleGroup, { type ToggleOption } from 'src/components/BaseToggleGroup.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import { buildRecipeTrays } from 'src/helpers/recipeTrays';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type {
        AutoBuildEmphasis, AutoBuildReason, MealPlanIngredient, ProposedEntry,
    } from 'src/models/mealPlan';
    import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
    import type { Recipe } from 'src/models/recipe';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import { useQuasar } from 'quasar';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        recipes: Recipe[];
        /** Household meal-slot vocabulary (ordered). */
        slotNames: string[];
        /** Days of the focused week (`{ label, iso }`). */
        weekDays: { label: string; iso: string }[];
        currentDayIso: string;
        isPastDay: (iso: string) => boolean;
        formatDate: (iso: string) => string;
        moneyEnabled: boolean;
        /** Persists the (edited) proposal onto the focused week. */
        buildPlan: (entries: MealPlanEntryCommand[]) => Promise<void>;
        /** Generates the shopping list; scoped to `recipeIds` when given. */
        generateList: (recipeIds?: string[]) => Promise<void>;
        printWeek: () => void;
    }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const api = new MealPlanApiService();
    const $q = useQuasar();
    const { stockStatusLabel, stockStatusColour, needsBuying } = useStockStatus();

    // ── Local editable copy of a proposed entry (adds a stable render key) ──
    type DraftEntry = ProposedEntry & { _key: string };

    const step = ref(1);
    const proposed = ref<DraftEntry[]>([]);
    const generatingProposal = ref(false);
    const building = ref(false);
    const generatingList = ref(false);
    const doneState = ref(false);
    const previewIngredients = ref<MealPlanIngredient[]>([]);
    const previewLoading = ref(false);

    // FU-611 — the ranker only ever picks *distinct* recipes, so a day×slot
    // grid larger than the cookbook fills days in order and then stops, leaving
    // later days silently blank (the review list just omits empty days). Capture
    // what the last build asked for vs. what it could place so the review step
    // can explain the gap. Both 0 for a manual ("I'll pick myself") start.
    const lastBuildRequested = ref(0);
    const lastBuildPlaced = ref(0);
    // Only surface the hint when the *build* genuinely fell short, and keep it up
    // only until the user fills the missing cells by hand — so it never fires
    // just because someone deleted a meal from an otherwise-full plan. Scoped to
    // the non-repeat case (repeat-same-day is the mitigation we point them at).
    const showShortfallHint = computed(() =>
        !repeatSameDay.value
        && lastBuildRequested.value > 0
        && lastBuildPlaced.value < lastBuildRequested.value
        && proposed.value.length < lastBuildRequested.value,
    );

    // ── Guidance inputs ─────────────────────────────────────────────────────
    // Two independent toggle sets — the days to plan and the meal slots to fill
    // — whose cross-product is the plan (one meal per day × slot). There is no
    // separate meal-count control: the toggles *are* the count.
    const selectedDays = ref<string[]>([]);
    const selectedSlots = ref<string[]>([]);
    const repeatSameDay = ref(false);
    const emphasis = ref<AutoBuildEmphasis>('use_up_stock');
    const budgetCap = ref(false);

    const emphasisOptions = [
        { label: 'Use up stock', value: 'use_up_stock' as AutoBuildEmphasis },
        { label: 'Variety', value: 'variety' as AutoBuildEmphasis },
        { label: 'Favourites', value: 'favourites' as AutoBuildEmphasis },
        { label: 'Surprise me', value: 'surprise' as AutoBuildEmphasis },
    ];
    const emphasisHints: Record<AutoBuildEmphasis, string> = {
        use_up_stock: 'Leans on meals you can cook now and stock that’s expiring soon.',
        variety: 'Spreads cuisines and picks things you haven’t had in a while.',
        favourites: 'Favourites and meals you cook often.',
        surprise: 'A mixed bag — mostly things you haven’t had lately.',
    };
    const emphasisHint = computed(() => emphasisHints[emphasis.value]);

    const upcomingDays = computed(() => props.weekDays.filter((d) => !props.isPastDay(d.iso)));
    // All seven weekdays always render in the same positions so the row never
    // reflows mid-week; days already gone are inert with an explaining tooltip.
    const dayToggleOptions = computed<ToggleOption[]>(() =>
        props.weekDays.map((d) => {
            const past = props.isPastDay(d.iso);
            return {
                label: d.label,
                value: d.iso,
                caption: props.formatDate(d.iso),
                ...(past ? { disable: true, tooltip: 'That day has already been and gone.' } : {}),
            };
        }),
    );
    const slotToggleOptions = computed<ToggleOption[]>(
        () => props.slotNames.map((s) => ({ label: s, value: s })),
    );
    // The review step still lets the user move a meal to another day, but only
    // to a day that can actually hold one.
    const dayOptions = computed(() =>
        upcomingDays.value.map((d) => ({ label: `${d.label} — ${props.formatDate(d.iso)}`, value: d.iso })),
    );

    const canGenerate = computed(
        () => selectedDays.value.length > 0 && selectedSlots.value.length > 0,
    );
    // One meal per cell either way — "same meals every day" changes *which*
    // recipes land, not how many.
    const plannedMealCount = computed(
        () => selectedDays.value.length * selectedSlots.value.length,
    );
    const plannedCountHint = computed(() => {
        if (selectedDays.value.length === 0) return 'Pick at least one day.';
        if (selectedSlots.value.length === 0) return 'Pick at least one meal.';
        const n = plannedMealCount.value;
        return `Dora will plan ${n} meal${n === 1 ? '' : 's'}.`;
    });

    // Default the slot selection to breakfast, lunch and dinner — the three
    // main meals most households plan — matched against the configured slot
    // vocabulary (household order preserved). If none of the three are named
    // in this install's slots, fall back to a single dinner-ish slot so the
    // builder always opens with something selected.
    const defaultSlots = computed<string[]>(() => {
        const mains = props.slotNames.filter((s) => /breakfast|lunch|dinner/i.test(s));
        if (mains.length) return mains;
        const dinner = props.slotNames.find((s) => /dinner/i.test(s));
        return dinner ? [dinner] : props.slotNames.slice(-1);
    });

    /** Where the Done step says the meals are landing. */
    const targetLabel = computed(() => {
        const days = [...new Set(proposed.value.map((e) => e.scheduled_for))].sort();
        if (days.length !== 1) return 'the current week';
        const iso = days[0]!;
        const day = props.weekDays.find((d) => d.iso === iso);
        return day ? `${day.label}, ${props.formatDate(iso)}` : props.formatDate(iso);
    });

    // ── Reason chips ────────────────────────────────────────────────────────
    const REASON_LABELS: Record<AutoBuildReason, string> = {
        uses_expiring: 'Uses expiring stock',
        cookable_now: 'You have everything',
        favourite: 'Favourite',
        not_made_recently: 'Haven’t had lately',
        variety: 'Adds variety',
        budget_friendly: 'Budget-friendly',
        picked: 'Added',
    };
    function reasonLabel(r: AutoBuildReason): string {
        return REASON_LABELS[r] ?? 'Added';
    }

    // ── Recipe trays for the add/swap picker ────────────────────────────────
    // R-003: shares the planner rail's builder rather than mirroring it. The
    // two copies had already been edited independently once; the FU-578 #47
    // one-instance-per-recipe dedupe lives in that one module.
    const recipeSearch = ref('');
    const trays = computed(() => buildRecipeTrays(props.recipes, recipeSearch.value));

    // ── Ingredient preview (aggregate demand) ───────────────────────────────
    const needToBuyCount = computed(
        () => previewIngredients.value.filter((i) => needsBuying(i.stock_item_id)).length,
    );
    function round(n: number): number {
        return Math.round(n * 100) / 100;
    }
    function money(n: number): string {
        return `$${n.toFixed(2)}`;
    }
    function noopLogCook(): Promise<number> {
        return Promise.resolve(0);
    }

    async function refreshPreview() {
        if (proposed.value.length === 0) {
            previewIngredients.value = [];
            return;
        }
        previewLoading.value = true;
        try {
            previewIngredients.value = await api.previewIngredientsAsync(
                proposed.value.map((e) => ({ recipe_id: e.recipe_id, servings: e.servings })),
            );
        } finally {
            previewLoading.value = false;
        }
    }
    // Recompute the buy list whenever the reviewed set changes (recipe or
    // servings), but only while the review step is visible.
    watch(
        () => proposed.value.map((e) => `${e.recipe_id}:${e.servings}`).join(','),
        () => { if (step.value === 2) void refreshPreview(); },
    );

    // ── Grouping for the review list ────────────────────────────────────────
    const groupedByDay = computed(() =>
        props.weekDays.map((d) => ({
            iso: d.iso,
            label: `${d.label} · ${props.formatDate(d.iso)}`,
            entries: proposed.value.filter((e) => e.scheduled_for === d.iso),
        })),
    );

    let keySeq = 0;
    function toDraft(e: ProposedEntry): DraftEntry {
        keySeq += 1;
        return { ...e, _key: `d${keySeq}` };
    }

    // ── Generate (server auto-build) ────────────────────────────────────────
    async function generate() {
        if (!canGenerate.value) return;
        generatingProposal.value = true;
        try {
            const res = await api.autoBuildAsync({
                days: [...selectedDays.value],
                emphasis: emphasis.value,
                slot_names: [...selectedSlots.value],
                repeat_same_day: repeatSameDay.value,
                budget_cap: budgetCap.value,
            });
            proposed.value = res.entries.map(toDraft);
            // Cells the toggles asked for vs. what the ranker could place (FU-611).
            lastBuildRequested.value = res.days_used.length * res.slots_used.length;
            lastBuildPlaced.value = res.entries.length;
            step.value = 2;
            await refreshPreview();
        } catch {
            // Stay on the Guide step; the axios layer already normalised the
            // error — surface a friendly toast rather than crashing the dialog.
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't build a plan just now — try again.",
            });
        } finally {
            generatingProposal.value = false;
        }
    }

    function startManual() {
        proposed.value = [];
        previewIngredients.value = [];
        lastBuildRequested.value = 0;
        lastBuildPlaced.value = 0;
        step.value = 2;
    }

    // ── Review-step editing ─────────────────────────────────────────────────
    function removeEntry(entry: DraftEntry) {
        proposed.value = proposed.value.filter((e) => e._key !== entry._key);
    }

    const pickerOpen = ref(false);
    const pickerMode = ref<'add' | 'swap'>('add');
    const swapTargetKey = ref<string | null>(null);

    function openAdd() {
        pickerMode.value = 'add';
        swapTargetKey.value = null;
        recipeSearch.value = '';
        pickerOpen.value = true;
    }
    function openSwap(entry: DraftEntry) {
        pickerMode.value = 'swap';
        swapTargetKey.value = entry._key;
        recipeSearch.value = '';
        pickerOpen.value = true;
    }

    /** Chosen day with the fewest meals so a manual add spreads too. Falls back
     *  to any upcoming day when the user skipped the toggles ("I'll pick
     *  myself" jumps straight to the review step). */
    function leastLoadedDay(): string {
        const days = selectedDays.value.length
            ? selectedDays.value
            : upcomingDays.value.map((d) => d.iso);
        if (!days.length) return props.currentDayIso;
        const load = (iso: string) => proposed.value.filter((e) => e.scheduled_for === iso).length;
        return days.reduce((best, iso) => (load(iso) < load(best) ? iso : best), days[0]!);
    }
    function slotFor(recipe: Recipe): string {
        const pool = selectedSlots.value.length ? selectedSlots.value : props.slotNames;
        if (recipe.time_of_day && pool.includes(recipe.time_of_day)) return recipe.time_of_day;
        return pool[0] ?? 'Dinner';
    }

    function onPickRecipe(recipeId: string) {
        const recipe = props.recipes.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        if (pickerMode.value === 'swap' && swapTargetKey.value) {
            // Swapping a recipe breaks its cook batch's one-recipe rule — unlink it.
            proposed.value = proposed.value.map((e) =>
                e._key === swapTargetKey.value
                    ? { ...e, recipe_id: recipe.recipe_id, recipe_name: recipe.name,
                        reason_chip: 'picked', cookable: recipe.cookable,
                        missing_stock_item_names: [], estimated_cost: null, cook_key: null }
                    : e,
            );
        } else {
            proposed.value = [...proposed.value, toDraft({
                recipe_id: recipe.recipe_id,
                recipe_name: recipe.name,
                scheduled_for: leastLoadedDay(),
                slot: slotFor(recipe),
                servings: 1,
                reason_chip: 'picked',
                cookable: recipe.cookable,
                missing_stock_item_names: [],
                estimated_cost: null,
                cook_key: null,
            })];
        }
        pickerOpen.value = false;
    }

    // PROPOSAL_MEAL_PLANS_PART_2 §9 — a proposed cook batch only survives to the
    // commit if it's still a valid group after any review-step edits: >=2 rows,
    // one recipe, one slot, distinct days. Otherwise the entry commits standalone
    // (the server would reject a malformed group). Also powers the review marker.
    function validCookKey(entry: DraftEntry): string | null {
        if (!entry.cook_key) return null;
        const group = proposed.value.filter((e) => e.cook_key === entry.cook_key);
        if (group.length < 2) return null;
        const recipes = new Set(group.map((e) => e.recipe_id));
        const slots = new Set(group.map((e) => e.slot));
        const days = group.map((e) => e.scheduled_for);
        if (recipes.size > 1 || slots.size > 1 || new Set(days).size !== days.length) return null;
        return entry.cook_key;
    }
    // Cook-day = the earliest day of a (valid) batch; that row shows "Cook", the
    // rest "Leftovers".
    function cookMarker(entry: DraftEntry): 'cook' | 'leftover' | null {
        const key = validCookKey(entry);
        if (!key) return null;
        const days = proposed.value.filter((e) => e.cook_key === key).map((e) => e.scheduled_for);
        return entry.scheduled_for === days.reduce((a, b) => (a < b ? a : b)) ? 'cook' : 'leftover';
    }

    // ── Commit + follow-ups ─────────────────────────────────────────────────
    async function onBuild() {
        building.value = true;
        try {
            await props.buildPlan(proposed.value.map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: e.scheduled_for,
                servings: e.servings,
                slot: e.slot,
                ...(validCookKey(e) ? { cook_key: validCookKey(e) as string } : {}),
            })));
            doneState.value = true;
        } finally {
            building.value = false;
        }
    }

    async function onGenerateList() {
        generatingList.value = true;
        try {
            // A single-day build → scope the list to exactly the meals just
            // planned; a multi-day build wants the whole week's list.
            const singleDay = new Set(proposed.value.map((e) => e.scheduled_for)).size === 1;
            const ids = singleDay
                ? [...new Set(proposed.value.map((e) => e.recipe_id))]
                : undefined;
            await props.generateList(ids);
        } finally {
            generatingList.value = false;
        }
    }

    // ── Reset on (re)open ────────────────────────────────────────────────────
    watch(() => props.modelValue, (open) => {
        if (!open) return;
        step.value = 1;
        proposed.value = [];
        previewIngredients.value = [];
        lastBuildRequested.value = 0;
        lastBuildPlaced.value = 0;
        doneState.value = false;
        recipeSearch.value = '';
        emphasis.value = 'use_up_stock';
        repeatSameDay.value = false;
        budgetCap.value = false;
        // Open on the obvious default: every day still ahead in this week, and
        // the dinner slot. One tap gets you a week; the rest is fine-tuning.
        selectedDays.value = upcomingDays.value.map((d) => d.iso);
        selectedSlots.value = [...defaultSlots.value];
    });
</script>

<style scoped>
    .builder-field {
        margin-bottom: 1rem;
    }
    .builder-field__label {
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 500;
        margin-bottom: 0.35rem;
    }
    .builder-hint {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        margin: 0.25rem 0 0.5rem;
        padding: 0.5rem 0.65rem;
        background: var(--surface-sunken);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
        line-height: 1.35;
    }
    .builder-hint__icon {
        flex: 0 0 auto;
        margin-top: 1px;
        color: var(--text-secondary);
    }
    .builder-day {
        margin-top: 0.75rem;
    }
    .builder-day__label {
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }
    .builder-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0;
        border-bottom: 1px solid var(--divider);
    }
    .builder-row__main {
        flex: 1 1 auto;
        min-width: 0;
    }
    .builder-row__name {
        font-weight: 500;
    }
    .builder-row__meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.1rem;
    }
    .builder-reason {
        background: var(--surface-sunken);
        color: var(--text-secondary);
    }
    /* PROPOSAL_MEAL_PLANS_PART_2 §9 — proposed cook-batch marker (icon + text). */
    .builder-cook {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--brand-primary);
    }
    .builder-cook--leftover {
        color: var(--text-secondary);
        font-weight: 500;
    }
    .builder-row__controls {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex: 0 0 auto;
    }
    .builder-slot-select {
        min-width: 120px;
    }
    .builder-day-select {
        min-width: 130px;
    }
    .builder-servings {
        display: flex;
        align-items: center;
        gap: 0.15rem;
    }
    .builder-servings__count {
        min-width: 1.2rem;
        text-align: center;
        font-variant-numeric: tabular-nums;
    }
    .builder-picker {
        max-height: 55vh;
        overflow-y: auto;
        border: 1px solid var(--border-default);
        border-radius: 6px;
    }
    .builder-list {
        max-height: 40vh;
        overflow-y: auto;
    }
</style>
