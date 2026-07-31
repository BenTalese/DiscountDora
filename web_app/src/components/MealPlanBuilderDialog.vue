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
                        <div class="builder-field__label">Plan for</div>
                        <BaseSegmented v-model="scope" :options="scopeOptions" dense />
                    </div>

                    <div v-if="scope === 'day'" class="builder-field">
                        <div class="builder-field__label">Which day</div>
                        <q-select
                            v-model="dayIso"
                            outlined dense emit-value map-options
                            :options="dayOptions"
                        />
                    </div>

                    <div class="builder-field">
                        <div class="builder-field__label">
                            How many meals ({{ mealCount }})
                        </div>
                        <q-slider
                            v-model="mealCount"
                            :min="1" :max="maxMeals" :step="1"
                            label snap markers
                        />
                    </div>

                    <div class="builder-field">
                        <div class="builder-field__label">Emphasis</div>
                        <BaseSegmented v-model="emphasis" :options="emphasisOptions" dense />
                        <div class="text-caption dora-text-muted q-mt-xs">
                            {{ emphasisHint }}
                        </div>
                    </div>

                    <div class="builder-field">
                        <div class="builder-field__label">Slots</div>
                        <BaseSegmented v-model="slotMode" :options="slotModeOptions" dense />
                        <q-select
                            v-if="slotMode === 'single'"
                            v-model="singleSlot"
                            outlined dense class="q-mt-xs"
                            :options="slotNames"
                        />
                        <q-select
                            v-if="slotMode === 'pick'"
                            v-model="pickedSlots"
                            outlined dense multiple use-chips class="q-mt-xs"
                            :options="slotNames"
                        />
                    </div>

                    <div v-if="moneyEnabled" class="builder-field">
                        <q-toggle
                            v-model="budgetCap"
                            dense
                            label="Keep the week under budget"
                        />
                    </div>
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
                            They'll be added to
                            {{ scope === 'day' ? focusedDayLabel : 'the current week' }}.
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
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import type { RecipeTray } from 'src/composables/useMealPlanner';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type {
        AutoBuildEmphasis, AutoBuildReason, AutoBuildScope, MealPlanIngredient,
        ProposedEntry,
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
        /** Household `meals_per_week` — the week-scope default meal count. */
        targetCount: number;
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

    // ── Guidance inputs ─────────────────────────────────────────────────────
    const scope = ref<AutoBuildScope>('week');
    const dayIso = ref<string>('');
    const mealCount = ref<number>(props.targetCount);
    const emphasis = ref<AutoBuildEmphasis>('use_up_stock');
    const slotMode = ref<'spread' | 'single' | 'pick'>('spread');
    const singleSlot = ref<string>('');
    const pickedSlots = ref<string[]>([]);
    const budgetCap = ref(false);

    const scopeOptions = [
        { label: 'This week', value: 'week' as AutoBuildScope },
        { label: 'A day', value: 'day' as AutoBuildScope },
    ];
    const emphasisOptions = [
        { label: 'Use up stock', value: 'use_up_stock' as AutoBuildEmphasis },
        { label: 'Variety', value: 'variety' as AutoBuildEmphasis },
        { label: 'Favourites', value: 'favourites' as AutoBuildEmphasis },
        { label: 'Surprise me', value: 'surprise' as AutoBuildEmphasis },
    ];
    const slotModeOptions = [
        { label: 'Spread', value: 'spread' as const },
        { label: 'One slot', value: 'single' as const },
        { label: 'Pick slots', value: 'pick' as const },
    ];
    const emphasisHints: Record<AutoBuildEmphasis, string> = {
        use_up_stock: 'Leans on meals you can cook now and stock that’s expiring soon.',
        variety: 'Spreads cuisines and picks things you haven’t had in a while.',
        favourites: 'Favourites and meals you cook often.',
        surprise: 'A mixed bag — mostly things you haven’t had lately.',
    };
    const emphasisHint = computed(() => emphasisHints[emphasis.value]);

    const upcomingDays = computed(() => props.weekDays.filter((d) => !props.isPastDay(d.iso)));
    const dayOptions = computed(() =>
        upcomingDays.value.map((d) => ({ label: `${d.label} — ${props.formatDate(d.iso)}`, value: d.iso })),
    );
    const weekStartIso = computed(() => props.weekDays[0]?.iso ?? props.currentDayIso);
    const focusedDayLabel = computed(() => {
        const d = props.weekDays.find((x) => x.iso === dayIso.value);
        return d ? `${d.label}, ${props.formatDate(d.iso)}` : 'that day';
    });

    // Grid ceiling so the count slider can't ask for more than the days×slots.
    const activeSlotCount = computed(() => {
        if (slotMode.value === 'single') return 1;
        if (slotMode.value === 'pick') return Math.max(pickedSlots.value.length, 1);
        return Math.max(props.slotNames.length, 1);
    });
    const maxMeals = computed(() => {
        const days = scope.value === 'day' ? 1 : Math.max(upcomingDays.value.length, 1);
        return Math.max(1, Math.min(21, days * activeSlotCount.value));
    });

    const defaultSingleSlot = computed(
        () => props.slotNames.find((s) => /dinner/i.test(s))
            ?? props.slotNames[props.slotNames.length - 1]
            ?? 'Dinner',
    );
    const resolvedSlotNames = computed<string[]>(() => {
        if (slotMode.value === 'single') return [singleSlot.value || defaultSingleSlot.value];
        if (slotMode.value === 'pick') return [...pickedSlots.value];
        return []; // spread ⇒ all household slots (server default)
    });

    // Keep the count sensible as scope / slots change. A single day defaults to
    // one meal (the "plan this Wednesday" case); the week uses the household
    // meals-per-week preference. Either way the slider caps at the grid size.
    watch(scope, (s) => {
        mealCount.value = s === 'day' ? 1 : props.targetCount;
        if (mealCount.value > maxMeals.value) mealCount.value = maxMeals.value;
        if (mealCount.value < 1) mealCount.value = 1;
        // Ensure the day picker holds a valid upcoming day the moment day-scope
        // is chosen (don't rely solely on the on-open reset).
        if (s === 'day' && !upcomingDays.value.some((d) => d.iso === dayIso.value)) {
            dayIso.value = upcomingDays.value[0]?.iso ?? props.currentDayIso;
        }
    });
    watch(maxMeals, (m) => {
        if (mealCount.value > m) mealCount.value = m;
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

    // ── Recipe trays for the add/swap picker (mirrors the planner rail) ─────
    const recipeSearch = ref('');
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
    function effectiveDayIso(): string {
        // Guard against an empty picker (e.g. the default day fell in the past):
        // fall back to the first upcoming day, then today.
        if (dayIso.value) return dayIso.value;
        return upcomingDays.value[0]?.iso ?? props.currentDayIso;
    }
    async function generate() {
        generatingProposal.value = true;
        try {
            const res = await api.autoBuildAsync({
                scope: scope.value,
                start_date: scope.value === 'week' ? weekStartIso.value : effectiveDayIso(),
                meal_count: mealCount.value,
                emphasis: emphasis.value,
                slot_names: resolvedSlotNames.value,
                budget_cap: budgetCap.value,
            });
            proposed.value = res.entries.map(toDraft);
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

    /** First upcoming day with the fewest meals so a manual add spreads too. */
    function leastLoadedDay(): string {
        const days = scope.value === 'day' && dayIso.value ? [dayIso.value] : upcomingDays.value.map((d) => d.iso);
        if (!days.length) return props.currentDayIso;
        const load = (iso: string) => proposed.value.filter((e) => e.scheduled_for === iso).length;
        return days.reduce((best, iso) => (load(iso) < load(best) ? iso : best), days[0]!);
    }
    function slotFor(recipe: Recipe): string {
        const pool = resolvedSlotNames.value.length ? resolvedSlotNames.value : props.slotNames;
        if (recipe.time_of_day && pool.includes(recipe.time_of_day)) return recipe.time_of_day;
        return pool[0] ?? 'Dinner';
    }

    function onPickRecipe(recipeId: string) {
        const recipe = props.recipes.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        if (pickerMode.value === 'swap' && swapTargetKey.value) {
            proposed.value = proposed.value.map((e) =>
                e._key === swapTargetKey.value
                    ? { ...e, recipe_id: recipe.recipe_id, recipe_name: recipe.name,
                        reason_chip: 'picked', cookable: recipe.cookable,
                        missing_stock_item_names: [], estimated_cost: null }
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
            })];
        }
        pickerOpen.value = false;
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
            })));
            doneState.value = true;
        } finally {
            building.value = false;
        }
    }

    async function onGenerateList() {
        generatingList.value = true;
        try {
            // Day scope → scope the list to exactly the meals just planned.
            const ids = scope.value === 'day'
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
        doneState.value = false;
        recipeSearch.value = '';
        scope.value = 'week';
        emphasis.value = 'use_up_stock';
        slotMode.value = 'spread';
        singleSlot.value = defaultSingleSlot.value;
        pickedSlots.value = [];
        budgetCap.value = false;
        mealCount.value = Math.min(props.targetCount, maxMeals.value);
        // Default the day picker to today-in-week, else the first upcoming day.
        const today = props.currentDayIso;
        dayIso.value = upcomingDays.value.some((d) => d.iso === today)
            ? today
            : upcomingDays.value[0]?.iso ?? today;
    });
</script>

<style scoped>
    .builder-field {
        margin-bottom: 1rem;
    }
    .builder-field__label {
        font-size: var(--font-size-sm);
        font-weight: 500;
        margin-bottom: 0.35rem;
    }
    .builder-day {
        margin-top: 0.75rem;
    }
    .builder-day__label {
        font-size: var(--font-size-sm);
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }
    .builder-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0;
        border-bottom: 1px solid var(--separator);
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
        border: 1px solid var(--separator);
        border-radius: 6px;
    }
    .builder-list {
        max-height: 40vh;
        overflow-y: auto;
    }
</style>
