<template>
    <div class="q-pa-md board-page">
        <!-- R-Phase 6 §9-I skeleton during initial mount loads. -->
        <MealPlanSkeleton
            v-if="planner.isInitialLoading.value"
            :variant="$q.screen.lt.md ? 'mobile' : 'grid'"
        />

        <!-- First-run guard (mirror of the A page §6.7) -->
        <MealPlanFirstRun v-else-if="!planner.recipes.value.length" />

        <template v-else>
            <!-- R-Phase 4 — shared mobile single-day focus (§8.2). On B the
                desktop top strip / consequences bar / week board are all
                replaced by the same focus component the A page uses. -->
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
                    @go-prev-week="planner.goPrevWeek"
                    @go-next-week="planner.goNextWeek"
                    @print="planner.printFocusedWeek"
                />
            </template>

            <template v-else>
            <!-- ── Top strip (§6.4) ─────────────────────────────────────── -->
            <div class="board-top-strip">
                <BaseButton variant="icon" :icon="ICONS.arrow_back" @click="planner.goPrevWeek">
                    <q-tooltip>Previous week</q-tooltip>
                </BaseButton>
                <div class="board-top-strip__range">{{ planner.weekRangeLabel.value }}</div>
                <BaseButton variant="icon" :icon="ICONS.arrow_forward" @click="planner.goNextWeek">
                    <q-tooltip>Next week</q-tooltip>
                </BaseButton>
                <BaseButton variant="ghost" dense :label="todayLabel" class="q-ml-sm" @click="goToToday">
                    <q-tooltip>Jump to this week</q-tooltip>
                </BaseButton>
                <!-- Calendar widget — now a month-jump popover (§8.1). -->
                <BaseButton variant="icon" :icon="ICONS.calendar_month" class="q-ml-sm">
                    <q-tooltip>Pick a week</q-tooltip>
                    <q-menu fit anchor="bottom right" self="top right">
                        <div style="min-width: 260px; padding: 8px">
                            <MealPlanCalendar v-model:focused-monday="planner.focusedMonday.value" />
                        </div>
                    </q-menu>
                </BaseButton>

                <q-space />

                <!-- FU-338 — Print action lives in-context (matches the
                     print affordance on MealPlansOverview and every other
                     printable surface). Uses the same `useMealPlanExport`
                     path via `planner.printFocusedWeek`. Hidden when no
                     plan is focused (nothing to print). -->
                <BaseButton
                    v-if="planner.focusedPlan.value"
                    variant="icon"
                    :icon="ICONS.print"
                    class="q-mr-sm"
                    @click="planner.printFocusedWeek"
                >
                    <q-tooltip>Print this week</q-tooltip>
                </BaseButton>

                <BaseButton
                    variant="ghost"
                    :icon="ICONS.event_repeat" label="Templates"
                    @click="templatesDrawerOpen = true"
                />

                <BaseButton
                    variant="secondary" class="q-ml-sm"
                    :icon="ICONS.lightbulb" label="Plan step-by-step"
                    @click="builderOpen = true"
                />
                <BaseButton
                    variant="secondary" class="q-ml-sm"
                    :icon="ICONS.search" label="Recipes"
                    @click="pickerOpen = true"
                />

                <!-- Group-by-slot toggle (Q5 alt view) -->
                <q-toggle
                    v-model="groupBySlot"
                    dense size="sm" class="q-ml-md dora-text-muted"
                    label="Group by slot"
                />

                <!-- A/B toggle (desktop, temp; §8.2) -->
                <BaseSegmented
                    :model-value="'grid'"
                    @update:model-value="onViewToggle"
                    class="q-ml-md board-view-toggle"
                    dense unelevated
                    :options="[
                        { label: 'List', value: 'list' },
                        { label: 'Grid', value: 'grid' },
                    ]"
                />
            </div>

            <!-- ── Consequences bar (sticky, §6.4) ──────────────────────── -->
            <div class="board-consequences">
                <MealPlanWeekStatus
                    :planned-count="plannedCount"
                    :shortfall-count="planner.shortfall.value.length"
                    :need-to-buy-count="planner.needToBuy.value.length"
                    :cook-by-label="planner.cookByLabel.value"
                />
                <BaseButton
                    v-if="planner.focusedPlan.value && planner.needToBuy.value.length"
                    variant="primary" :icon="ICONS.shopping_cart"
                    label="Generate shopping list"
                    :loading="planner.generating.value"
                    @click="planner.generateListForWeek"
                />
            </div>

            <!-- ── Empty-week banner (R-014, mirrors A) ─────────────────── -->
            <q-card
                v-if="plannedCount === 0"
                flat bordered
                class="board-empty-week q-mb-sm"
            >
                <q-card-section class="row items-center">
                    <div>
                        <div class="text-subtitle2">Plan this week</div>
                        <div class="text-caption dora-text-muted">
                            Use the step-by-step builder, or tap any day below to add a meal.
                        </div>
                    </div>
                    <q-space />
                    <BaseButton
                        variant="primary" :icon="ICONS.lightbulb"
                        label="Plan step-by-step"
                        @click="builderOpen = true"
                    />
                </q-card-section>
            </q-card>

            <!-- ── The week board ───────────────────────────────────────── -->
            <MealPlanWeekBoard
                :week-days="planner.weekDays.value"
                :slot-names="planner.slotNames.value"
                :entries-for="(iso: string) => planner.dayEntries(iso)"
                :entries-for-slot="(iso: string, slot: string) => planner.slotEntries(iso, slot)"
                :is-past-day="planner.isPastDay"
                :current-day-iso="planner.currentDayIso.value"
                :shortfall-recipe-ids="planner.shortfallRecipeIds.value"
                :hovered-recipe-ids="planner.hoveredRecipeIds.value"
                :format-day-date="planner.formatDate"
                :group-by-slot="groupBySlot"
                @entry-view="planner.goToRecipe"
                @entry-cook="planner.cookRecipe"
                @entry-remove="planner.removeEntry"
                @entry-adjust="planner.adjustEntryServings"
                @add-to-day="onAddToDay"
                @drop-on-day="onDropOnDay"
                @drop-on-day-slot="planner.onDropOnSlot"
            />
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

        <!-- Templates drawer (R-Phase 5 / §9-E). -->
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

        <!-- ── Recipe picker drawer (right-side, pinnable) ───────────────── -->
        <q-dialog
            v-model="pickerOpen"
            position="right"
            :seamless="pickerPinned"
            :persistent="pickerPinned"
            :no-backdrop-dismiss="pickerPinned"
            transition-show="slide-left"
            transition-hide="slide-right"
        >
            <q-card class="picker-drawer column">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-subtitle1">Recipes</div>
                    <q-space />
                    <BaseButton
                        variant="icon"
                        :icon="pickerPinned ? ICONS.lock : ICONS.lock_open"
                        @click="pickerPinned = !pickerPinned"
                    >
                        <q-tooltip>{{ pickerPinned ? 'Unpin' : 'Pin open' }}</q-tooltip>
                    </BaseButton>
                    <BaseButton variant="icon" :icon="ICONS.close" @click="pickerOpen = false">
                        <q-tooltip>Close</q-tooltip>
                    </BaseButton>
                </q-card-section>
                <q-card-section class="col q-pa-sm">
                    <MealPlanRecipePicker
                        v-model:recipe-search="planner.recipeSearch.value"
                        :trays="planner.trays.value"
                        :recipes="planner.recipes.value"
                        :focused-target="planner.focusedTarget.value"
                        :drag-allowed="planner.dragAllowed.value"
                        :format-date="planner.formatDate"
                        :log-cook="planner.logPaletteCook"
                        @cancel-target="planner.clearFocusedTarget"
                        @recipe-pick="onRecipePicked"
                        @recipe-pointer-down="planner.onRecipePointerDown"
                        @recipe-drag-start="planner.onDragStart"
                        @recipe-drag-end="planner.onDragEnd"
                        @palette-meal-adjust="planner.adjustPaletteMeals"
                    />
                </q-card-section>
            </q-card>
        </q-dialog>

        <!-- ── Add-to-day slot picker menu (anchored mid-screen) ─────────── -->
        <BaseDialog v-model="addSlotPickerOpen" :title="addSlotPickerTitle" closable card-style="min-width: 260px">
            <q-list separator>
                <q-item
                    v-for="slot in planner.slotNames.value"
                    :key="slot"
                    clickable v-close-popup
                    @click="onSlotChosen(slot)"
                >
                    <q-item-section>{{ slot }}</q-item-section>
                </q-item>
            </q-list>
        </BaseDialog>

        <!-- ── Shared dialogs (save template / recurring / builder) ─────── -->
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

        <SequentialBuilderDialog
            v-model="builderOpen"
            :recipes="planner.recipes.value"
            :target-count="mealsPerWeek"
            :build-plan="planner.builderBuildPlan"
            :generate-list="planner.generateListForWeek"
            :print-week="planner.printFocusedWeek"
        />

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
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import MealPlanCalendar from 'components/MealPlanCalendar.vue';
    import MealPlanFirstRun from 'src/components/MealPlanFirstRun.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import MealPlanWeekBoard from 'src/components/MealPlanWeekBoard.vue';
    import MealPlanWeekStatus from 'src/components/MealPlanWeekStatus.vue';
    import SequentialBuilderDialog from 'components/SequentialBuilderDialog.vue';
    import MealPlanMobileFocus from 'src/components/MealPlanMobileFocus.vue';
    import MealPlanPickerSheet from 'src/components/MealPlanPickerSheet.vue';
    import MealPlanSkeleton from 'src/components/MealPlanSkeleton.vue';
    import MealPlanTemplatesDrawer from 'src/components/MealPlanTemplatesDrawer.vue';
    import { useMealPlanner } from 'src/composables/useMealPlanner';
    // FU-181 — target-count is the user's `meals_per_week` pref (falls
    // back to 7 when unset). Reactive so a Preferences change lights up
    // the builder without a reload.
    import { useMealsPerWeek } from 'src/composables/useMealsPerWeek';
    import { resolvePlannerView, setPlannerView } from 'src/composables/useMealPlannerView';
    import { localTodayIso, mondayOf, shiftDays } from 'src/helpers/weekDates';
    import { useQuasar } from 'quasar';
    import { useRoute, useRouter } from 'vue-router';
    import { computed, onMounted, ref, watch } from 'vue';

    const planner = useMealPlanner();
    const { mealsPerWeek } = useMealsPerWeek();
    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    // ── A/B view persistence (§8.2) ────────────────────────────────────────
    onMounted(() => {
        const desired = resolvePlannerView(route.query as Record<string, unknown>, 'grid');
        if (desired === 'list') {
            void router.replace({
                path: '/meal-plans',
                query: { ...route.query, view: 'list' },
            });
        } else {
            // Landing here implicitly means grid — record the preference so
            // the next visit lands on the same page without the bounce.
            setPlannerView('grid');
        }
    });

    const groupBySlot = ref(false);

    const plannedCount = computed(
        () => (planner.focusedPlan.value?.entries ?? []).filter((e) => !e.consumed_at).length,
    );

    const todayLabel = computed(() => {
        const todayMonday = mondayOf(planner.today.value ?? localTodayIso());
        return planner.focusedMonday.value === todayMonday ? 'This week' : 'Today';
    });
    function goToToday() {
        planner.focusedMonday.value = mondayOf(planner.today.value ?? localTodayIso());
    }

    // ── A/B toggle wiring ──────────────────────────────────────────────────
    function onViewToggle(value: string | number | null) {
        if (value === 'list') {
            setPlannerView('list');
            void router.replace({
                path: '/meal-plans',
                query: { ...router.currentRoute.value.query, view: 'list' },
            });
        }
    }

    // ── Drop / add wiring (board uses day-level drop; slot picker for tap-add) ──
    const addSlotPickerOpen = ref(false);
    const addSlotPickerDay = ref<string | null>(null);
    const addSlotPickerTitle = computed(() => {
        if (!addSlotPickerDay.value) return 'Pick a slot';
        return `Add to ${planner.formatDate(addSlotPickerDay.value)}`;
    });
    function onAddToDay(dayIso: string) {
        addSlotPickerDay.value = dayIso;
        addSlotPickerOpen.value = true;
    }
    function onSlotChosen(slot: string) {
        if (!addSlotPickerDay.value) return;
        planner.selectSlot(addSlotPickerDay.value, slot);
        addSlotPickerOpen.value = false;
        pickerOpen.value = true; // Open the picker so the user can choose a recipe.
    }
    async function onDropOnDay(dayIso: string) {
        // Default the dropped recipe into the household's first slot (or the
        // most recently used). Per Q5 the slot is shown as a tag on the card,
        // so the user can re-tag without leaving the board if they meant a
        // different slot.
        const defaultSlot = planner.slotNames.value[0] ?? 'Dinner';
        await planner.onDropOnSlot(dayIso, defaultSlot);
    }

    function onRecipePicked(recipeId: string) {
        void planner.pickRecipe(recipeId);
        // Auto-close the picker after an add when it's not pinned (Tesler).
        if (!pickerPinned.value) pickerOpen.value = false;
    }

    // Auto-open the picker once a focused-target is set from elsewhere, so the
    // user doesn't have to hunt for the picker after tapping a day. Desktop
    // only — the mobile flow uses the bottom-sheet picker below.
    watch(
        () => planner.focusedTarget.value,
        (target) => {
            if ($q.screen.lt.md) return;
            if (target) pickerOpen.value = true;
        },
    );

    // ── Picker drawer ──────────────────────────────────────────────────────
    const pickerOpen = ref(false);
    const pickerPinned = ref(false);

    // ── Save-template dialog ───────────────────────────────────────────────
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

    // ── Recurring-apply dialog ─────────────────────────────────────────────
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
        recurringEnd.value = shiftDays(planner.focusedMonday.value, 28);
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

    // ── Sequential builder ─────────────────────────────────────────────────
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
    .board-page {
        min-height: 100%;
    }
    .board-top-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
    }
    .board-top-strip__range {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .board-consequences {
        position: sticky;
        top: 0;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 8px;
        margin-bottom: 8px;
        background: var(--surface-elevated);
        border: 1px solid var(--separator);
        border-radius: 8px;
        backdrop-filter: blur(6px);
    }
    .board-consequences :deep(.week-status) {
        flex: 1 1 auto;
        margin-bottom: 0;
        background: transparent;
        padding: 0;
    }
    .board-empty-week {
        background: var(--surface-sunken);
    }
    .picker-drawer {
        width: min(420px, 100vw);
        height: 100vh;
    }
</style>
