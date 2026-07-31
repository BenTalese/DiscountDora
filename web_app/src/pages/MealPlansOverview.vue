<template>
    <div class="q-pa-md">
        <!-- R-Phase 6 §9-I — skeleton during the initial parallel mount load
            so the planner shape arrives instantly instead of popcorning in. -->
        <MealPlanSkeleton
            v-if="planner.isInitialLoading.value"
            :variant="$q.screen.lt.md ? 'mobile' : 'list'"
        />

        <!-- R-Phase 2 first-run path (§6.7). When the user has no recipes, the
            planner can't do its job — replace the empty 3-column layout with
            a single hero that points to the Cookbook. -->
        <MealPlanFirstRun v-else-if="!planner.recipes.value.length" />

        <template v-else>
            <!-- FU-317 Chunk 5 — reconcile nudge line above the planner
                 when past-day meals need confirming. Hide-when-empty
                 (R-029); the server owns the count via `useReconcileQueue`. -->
            <router-link
                v-if="reconcileTotal > 0"
                to="/meal-plans/reconcile"
                class="meal-plans-reconcile-nudge q-mb-sm"
            >
                {{ reconcileTotal }} past-day meal{{ reconcileTotal === 1 ? '' : 's' }} need{{ reconcileTotal === 1 ? 's' : '' }} confirming →
            </router-link>

            <!-- R-Phase 4 — shared mobile single-day focus (§8.2). Both A
                and B render the same mobile view; the A/B toggle is desktop-
                only because the carousel-vs-grid experiment doesn't apply
                below md. -->
            <template v-if="$q.screen.lt.md">
                <MealPlanMobileFocus
                    :week-days="planner.weekDays.value"
                    :slot-names="planner.slotNames.value"
                    :entries-for="planner.dayEntries"
                    :is-past-day="planner.isPastDay"
                    :current-day-iso="planner.currentDayIso.value"
                    :shortfall-recipe-ids="planner.shortfallRecipeIds.value"
                    :week-range-label="planner.weekRangeLabel.value"
                    :planned-count="plannedCount"
                    :shortfall-count="planner.shortfall.value.length"
                    :need-to-buy-count="planner.needToBuy.value.length"
                    :cook-by-label="planner.cookByLabel.value"
                    :generating="planner.generating.value"
                    @entry-view="planner.goToRecipe"
                    @entry-cook="planner.cookRecipe"
                    @entry-remove="planner.removeEntry"
                    @entry-adjust="planner.adjustEntryServings"
                    @add-to-slot="onMobileAddToSlot"
                    @generate-list="planner.generateListForWeek"
                    @open-builder="builderOpen = true"
                    @go-prev-week="planner.goPrevWeek"
                    @go-next-week="planner.goNextWeek"
                />
            </template>
            <template v-else>
            <div class="row items-center q-mb-sm">
                <q-space />
                <!-- FU-304 closed 2026-07-07 — Direction A won; the A/B
                     `BaseSegmented` toggle and the sibling `/meal-plans/board`
                     page were retired. -->
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.auto_awesome"
                    label="Build my week"
                    @click="builderOpen = true"
                />
            </div>

            <div class="row q-col-gutter-md">
                <!-- ── Left: recipe list ──────────────────────────────────── -->
                <div class="col-12 col-md-3 planner-side">
                    <div class="planner-sticky">
                        <MealPlanRecipePicker
                            v-model:recipe-search="planner.recipeSearch.value"
                            :trays="planner.trays.value"
                            :recipes="planner.recipes.value"
                            :focused-target="planner.focusedTarget.value"
                            :drag-allowed="planner.dragAllowed.value"
                            :format-date="planner.formatDate"
                            :log-cook="planner.logPaletteCook"
                            @cancel-target="planner.clearFocusedTarget"
                            @recipe-pick="planner.pickRecipe"
                            @recipe-pointer-down="planner.onRecipePointerDown"
                            @recipe-drag-start="planner.onDragStart"
                            @recipe-drag-end="planner.onDragEnd"
                            @palette-meal-adjust="planner.adjustPaletteMeals"
                        />
                    </div>
                </div>

                <!-- ── Main: vertical week carousel ───────────────────────── -->
                <div class="col-12 col-md-6">
                    <div class="row items-center q-mb-xs">
                        <BaseButton variant="icon" :icon="ICONS.arrow_upward" @click="planner.goPrevWeek">
                            <q-tooltip>Previous week</q-tooltip>
                        </BaseButton>
                        <div class="text-subtitle2 q-ml-sm">{{ planner.weekRangeLabel.value }}</div>
                        <q-space />
                        <BaseButton
                            v-if="planner.focusedPlan.value"
                            variant="icon"
                            :icon="ICONS.print"
                            @click="planner.printFocusedWeek"
                        >
                            <q-tooltip>Print this week</q-tooltip>
                        </BaseButton>
                        <!-- U7 — destructive action is labelled, not an icon-only
                            sibling of "print". Confirm dialog is unchanged. -->
                        <BaseButton
                            v-if="planner.focusedPlan.value"
                            variant="danger-ghost"
                            dense
                            :icon="ICONS.delete_outline"
                            label="Clear week"
                            class="q-ml-sm"
                            @click="planner.confirmClearWeek"
                        />
                    </div>

                    <!-- Secondary row: show-all toggle (Q2) -->
                    <div class="row items-center justify-end q-mb-sm">
                        <q-toggle
                            v-model="showAllSlots"
                            dense
                            size="sm"
                            label="Show all slots"
                            class="dora-text-muted"
                            :title="showAllSlots
                                ? 'Showing every household meal slot per day'
                                : 'Showing only slots with planned meals'"
                        />
                    </div>

                    <!-- R-Phase 2 — promoted week status (U2 + H1). Stays at the
                        top of the working column so the answer-bearing summary
                        is always glanceable as the carousel scrolls. -->
                    <MealPlanWeekStatus
                        :planned-count="plannedCount"
                        :shortfall-count="planner.shortfall.value.length"
                        :need-to-buy-count="planner.needToBuy.value.length"
                        :cook-by-label="planner.cookByLabel.value"
                    />

                    <!-- Empty-week banner (recipes exist, this week is
                        empty). Replaces 7 days of "tap to add" sprawl with
                        one designed CTA. Calm empty state, distinct from
                        R-029 hide-when-off. -->
                    <q-card
                        v-if="plannedCount === 0"
                        flat bordered
                        class="empty-week-banner q-mb-sm"
                    >
                        <q-card-section class="row items-center">
                            <div>
                                <div class="text-subtitle2">Plan this week</div>
                                <div class="text-caption dora-text-muted">
                                    Let Dora build it for you, or tap any day below to add a meal.
                                </div>
                            </div>
                            <q-space />
                            <BaseButton
                                variant="primary"
                                :icon="ICONS.auto_awesome"
                                label="Build my week"
                                @click="builderOpen = true"
                            />
                        </q-card-section>
                    </q-card>

                    <transition :name="planner.weekTransition.value" mode="out-in">
                        <div
                            :key="planner.focusedMonday.value"
                            @touchstart.passive="planner.onTouchStart"
                            @touchend.passive="planner.onTouchEnd"
                        >
                            <MealPlanWeekDayCard
                                v-for="day in planner.weekDays.value"
                                :key="day.iso"
                                :day="day"
                                :is-past="planner.isPastDay(day.iso)"
                                :is-today="day.iso === planner.currentDayIso.value"
                                :slot-names="planner.slotNames.value"
                                :slot-entries="(slot: string) => planner.slotEntries(day.iso, slot)"
                                :other-entries="planner.otherSlotEntries(day.iso)"
                                :is-targeted-slot="(slot: string) => planner.isTargeted(day.iso, slot)"
                                :shortfall-recipe-ids="planner.shortfallRecipeIds.value"
                                :hovered-recipe-ids="planner.hoveredRecipeIds.value"
                                :format-date="planner.formatDate"
                                :show-all-slots="showAllSlots"
                                @select-slot="(slot: string) => planner.selectSlot(day.iso, slot)"
                                @drop-on-slot="(slot: string) => planner.onDropOnSlot(day.iso, slot)"
                                @entry-view="planner.goToRecipe"
                                @entry-cook="planner.cookRecipe"
                                @entry-remove="planner.removeEntry"
                                @entry-adjust="planner.adjustEntryServings"
                            />
                        </div>
                    </transition>

                    <div class="row items-center justify-center q-mt-xs">
                        <BaseButton variant="icon" :icon="ICONS.arrow_downward" @click="planner.goNextWeek">
                            <q-tooltip>Next week</q-tooltip>
                        </BaseButton>
                    </div>

                    <!-- FU-451 — budget-defense swaps (renders itself only when
                         money features are on AND the week is over budget). -->
                    <SwapSuggestionsPanel
                        :meal-plan-id="planner.focusedPlan.value?.meal_plan_id ?? null"
                        @changed="onSwapApplied"
                    />
                </div>

                <!-- ── Right: calendar + shopping summary ─────────────────── -->
                <div class="col-12 col-md-3 planner-side">
                    <div class="planner-sticky">
                        <MealPlanCalendar v-model:focused-monday="planner.focusedMonday.value" class="q-mb-sm" />

                        <MealPlanShoppingSummary
                            :focused-plan="planner.focusedPlan.value"
                            :ingredients-loading="planner.ingredientsLoading.value"
                            :ingredients="planner.ingredients.value"
                            :need-to-buy="planner.needToBuy.value"
                            :shortfall-count="planner.shortfall.value.length"
                            :cook-by-label="planner.cookByLabel.value"
                            :generating="planner.generating.value"
                            :list-status-label="planner.listStatusLabel"
                            :stock-status-label="planner.stockStatusLabel"
                            :stock-status-colour="planner.stockStatusColour"
                            @generate-list="planner.generateListForWeek"
                            @hover-ingredient="planner.hoverIngredient"
                            @clear-hover="planner.clearHover"
                        />

                        <!-- Templates (C-2.F / §9-E unified drawer) ─────── -->
                        <q-card flat bordered class="q-mt-sm">
                            <q-card-section class="q-pb-none">
                                <div class="text-subtitle1">Templates</div>
                                <div class="text-caption dora-text-muted">
                                    Save a week's meals and re-use them on any other week.
                                </div>
                            </q-card-section>
                            <q-card-actions class="column items-stretch q-gutter-xs">
                                <BaseButton
                                    variant="secondary"
                                    :icon="ICONS.event_repeat"
                                    label="Browse + apply templates…"
                                    @click="templatesDrawerOpen = true"
                                />
                            </q-card-actions>
                        </q-card>
                    </div>
                </div>
            </div>
            </template>
        </template>

        <!-- Mobile-only bottom-sheet picker (R-Phase 4 / Q4). -->
        <MealPlanPickerSheet
            v-if="$q.screen.lt.md"
            v-model="pickerSheetOpen"
            v-model:recipe-search="planner.recipeSearch.value"
            :trays="planner.trays.value"
            :recipes="planner.recipes.value"
            :focused-target="planner.focusedTarget.value"
            :format-date="planner.formatDate"
            :log-cook="planner.logPaletteCook"
            @cancel-target="planner.clearFocusedTarget"
            @recipe-pick="planner.pickRecipe"
            @palette-meal-adjust="planner.adjustPaletteMeals"
        />

        <!-- Templates drawer (R-Phase 5 / §9-E). Apply + manage in-place;
            no page hop. Shared by both A and B pages. -->
        <MealPlanTemplatesDrawer
            v-model="templatesDrawerOpen"
            :templates="planner.templates.value"
            :can-save-current-week="
                !!planner.focusedPlan.value
                    && planner.focusedPlan.value.entries.length > 0
            "
            @save-current-week="openSaveTemplate"
            @apply-recurring="openRecurring"
            @apply-template="onTemplateApply"
        />

        <!-- Save the focused week as a template ─────────────────────── -->
        <BaseDialog v-model="saveTemplateOpen" title="Save as a template" closable card-style="min-width: 340px">
            <q-card-section class="q-pt-none q-gutter-sm">
                <q-input v-model="templateName" outlined dense autofocus label="Template name" :disable="savingTemplate" />
                <q-input
                    v-model="templateDescription"
                    outlined dense type="textarea" autogrow
                    label="Description (optional)"
                    :disable="savingTemplate"
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary" label="Save template"
                    :loading="savingTemplate"
                    :disable="!templateName.trim()"
                    @click="confirmSaveTemplate"
                />
            </template>
        </BaseDialog>

        <!-- "Build my week" auto-planner (FU-596) ──────────────────── -->
        <MealPlanBuilderDialog
            v-model="builderOpen"
            :recipes="planner.recipes.value"
            :target-count="mealsPerWeek"
            :slot-names="planner.slotNames.value"
            :week-days="planner.weekDays.value"
            :current-day-iso="planner.currentDayIso.value"
            :is-past-day="planner.isPastDay"
            :format-date="planner.formatDate"
            :money-enabled="moneyEnabled"
            :build-plan="planner.builderBuildPlan"
            :generate-list="planner.generateListForWeek"
            :print-week="planner.printFocusedWeek"
        />

        <!-- Apply a template recurringly over a week range ─────────── -->
        <BaseDialog v-model="recurringOpen" title="Apply recurring" closable card-style="min-width: 360px; max-width: 95vw">
            <q-card-section class="q-pt-none q-gutter-sm">
                <q-select
                    v-model="recurringSource"
                    outlined dense
                    :options="planner.recurringSourceOptions.value"
                    emit-value map-options
                    label="Template or rotating set"
                    :disable="recurringApplying"
                />
                <div class="row q-col-gutter-sm">
                    <q-input class="col" v-model="recurringStart" outlined dense type="date" label="From (week of)" :disable="recurringApplying" />
                    <q-input class="col" v-model="recurringEnd" outlined dense type="date" label="To (week of)" :disable="recurringApplying" />
                </div>
                <div class="text-caption dora-text-muted">
                    Each week is forked from the template (a set rotates through its templates).
                    Past days are skipped; up to 26 weeks.
                </div>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary" label="Apply"
                    :loading="recurringApplying"
                    :disable="!recurringSource || !recurringStart || !recurringEnd"
                    @click="confirmRecurring"
                />
            </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanCalendar from 'components/MealPlanCalendar.vue';
    import MealPlanFirstRun from 'src/components/MealPlanFirstRun.vue';
    import MealPlanMobileFocus from 'src/components/MealPlanMobileFocus.vue';
    import MealPlanPickerSheet from 'src/components/MealPlanPickerSheet.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import MealPlanShoppingSummary from 'src/components/MealPlanShoppingSummary.vue';
    import MealPlanSkeleton from 'src/components/MealPlanSkeleton.vue';
    import MealPlanTemplatesDrawer from 'src/components/MealPlanTemplatesDrawer.vue';
    import MealPlanWeekDayCard from 'src/components/MealPlanWeekDayCard.vue';
    import MealPlanWeekStatus from 'src/components/MealPlanWeekStatus.vue';
    import MealPlanBuilderDialog from 'components/MealPlanBuilderDialog.vue';
    import SwapSuggestionsPanel from 'src/components/SwapSuggestionsPanel.vue';
    import { useMealPlanner } from 'src/composables/useMealPlanner';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    // FU-317 Chunk 5 — reconcile nudge line count.
    import { useReconcileQueue } from 'src/composables/useReconcileQueue';
    // target-count sourced from the user's `meals_per_week` pref
    // via this composable (fallback 7 when unset).
    import { useMealsPerWeek } from 'src/composables/useMealsPerWeek';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { shiftDays } from 'src/helpers/weekDates';
    import { useQuasar } from 'quasar';
    import { computed, ref, watch } from 'vue';

    const planner = useMealPlanner();
    const { mealsPerWeek } = useMealsPerWeek();
    const { moneyEnabled } = useMoneyEnabled();
    const { total: reconcileTotal } = useReconcileQueue();
    const mealPlanStore = useMealPlanStore();
    const $q = useQuasar();

    // FU-451 — a budget-defense swap mutates a meal-plan entry's recipe via a
    // dedicated endpoint, so reload the plans (week grid) + ingredient demand
    // to reflect it.
    async function onSwapApplied() {
        await mealPlanStore.getMealPlansAsync();
        await planner.loadIngredients();
    }

    // FU-304 closed 2026-07-07 — Direction A wins. The A/B view helper
    // (`useMealPlannerView`), the desktop `BaseSegmented` toggle, and the
    // `onMounted` "restore Grid view" redirect were all retired with the
    // Direction B page. `MealPlansOverview` is now the only planner surface.

    // ── Q2 — slot visibility default ───────────────────────────────────────
    // Default off: only used slots render per day (collapses the empty-cell
    // sprawl, U1). Toggle reveals every household slot if the user prefers
    // the legacy view.
    //
    // FU-306 — the toggle is a per-device view preference (not a household
    // pref), so it rides `localStorage` rather than a User/Preference column.
    // Multi-slot households that flip it "on" now keep it on across reloads;
    // a genuine per-household setting can graduate to `Preference` later if
    // the same user wants it synced across their devices.
    const SHOW_ALL_SLOTS_KEY = 'mealPlanShowAllSlots';
    const showAllSlots = ref(readShowAllSlots());
    watch(showAllSlots, (value) => {
        try {
            localStorage.setItem(SHOW_ALL_SLOTS_KEY, value ? '1' : '0');
        } catch {
            // localStorage can be unavailable (private-mode Safari, disk
            // quota exceeded) — fail silent; the session-local ref still
            // works, we just lose cross-reload persistence.
        }
    });
    function readShowAllSlots(): boolean {
        try {
            return localStorage.getItem(SHOW_ALL_SLOTS_KEY) === '1';
        } catch {
            return false;
        }
    }

    const plannedCount = computed(
        () => (planner.focusedPlan.value?.entries ?? []).filter((e) => !e.consumed_at).length,
    );

    // ── Save-template dialog (page-local UI state) ─────────────────────────
    const saveTemplateOpen = ref(false);
    const templateName = ref('');
    const templateDescription = ref('');
    const savingTemplate = ref(false);

    function openSaveTemplate() {
        templateName.value = `Week of ${planner.formatDate(planner.focusedMonday.value)}`;
        templateDescription.value = '';
        saveTemplateOpen.value = true;
    }
    async function confirmSaveTemplate() {
        savingTemplate.value = true;
        try {
            const ok = await planner.saveFocusedWeekAsTemplate(templateName.value, templateDescription.value);
            if (ok) saveTemplateOpen.value = false;
        } finally {
            savingTemplate.value = false;
        }
    }

    // ── Recurring-apply dialog (page-local UI state) ───────────────────────
    const recurringOpen = ref(false);
    const recurringSource = ref<string | null>(null);
    const recurringStart = ref('');
    const recurringEnd = ref('');
    const recurringApplying = ref(false);

    async function openRecurring() {
        const ready = await planner.loadRecurringSources();
        if (!ready) return;
        recurringSource.value = planner.recurringSourceOptions.value[0]?.value ?? null;
        recurringStart.value = planner.focusedMonday.value;
        recurringEnd.value = shiftDays(planner.focusedMonday.value, 28); // default 4 weeks
        recurringOpen.value = true;
    }
    async function confirmRecurring() {
        if (!recurringSource.value || !recurringStart.value || !recurringEnd.value) return;
        recurringApplying.value = true;
        try {
            const ok = await planner.applyRecurring({
                source: recurringSource.value,
                startMonday: recurringStart.value,
                endMonday: recurringEnd.value,
            });
            if (ok) recurringOpen.value = false;
        } finally {
            recurringApplying.value = false;
        }
    }

    // ── Sequential builder (page-local open state) ─────────────────────────
    const builderOpen = ref(false);

    // ── Mobile add-flow (R-Phase 4) ────────────────────────────────────────
    const pickerSheetOpen = ref(false);
    function onMobileAddToSlot(dayIso: string, slot: string) {
        planner.selectSlot(dayIso, slot);
        if (planner.focusedTarget.value) pickerSheetOpen.value = true;
    }

    // ── Templates drawer (R-Phase 5 / §9-E) ────────────────────────────────
    const templatesDrawerOpen = ref(false);
    async function onTemplateApply(templateId: string) {
        const ok = await planner.warnBeforeReplaceWeek();
        if (!ok) return;
        await planner.applyTemplate(templateId);
        templatesDrawerOpen.value = false;
    }
</script>

<style scoped>
    .wk-down-enter-active,
    .wk-down-leave-active,
    .wk-up-enter-active,
    .wk-up-leave-active {
        transition: transform 0.18s ease, opacity 0.18s ease;
    }
    .wk-down-enter-from { transform: translateY(20px); opacity: 0; }
    .wk-down-leave-to { transform: translateY(-20px); opacity: 0; }
    .wk-up-enter-from { transform: translateY(-20px); opacity: 0; }
    .wk-up-leave-to { transform: translateY(20px); opacity: 0; }

    /* U2 — sticky context columns (desktop). The carousel column is the only
        one that scrolls; the palette and shopping rail stay visible. */
    @media (min-width: 1024px) {
        .planner-side {
            align-self: flex-start;
        }
        .planner-sticky {
            position: sticky;
            top: 16px;
            max-height: calc(100vh - 32px);
            overflow-y: auto;
        }
    }

    .empty-week-banner {
        background: var(--surface-sunken);
    }

    /* FU-317 Chunk 5 — reconcile nudge above the planner. Text-link
       shape, no card chrome; hover tints via color-mix (matches the
       dashboard chip). */
    .meal-plans-reconcile-nudge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        color: var(--brand-primary);
        text-decoration: none;
        font-size: var(--font-size-sm);
        font-weight: 500;
        border-radius: var(--radius-sm);
        transition: background 120ms ease;
    }
    .meal-plans-reconcile-nudge:hover,
    .meal-plans-reconcile-nudge:focus-visible {
        background: color-mix(in srgb, var(--brand-primary) 8%, transparent);
    }
</style>
