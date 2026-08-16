<template>
    <div class="mobile-focus">
        <!-- Week nav -->
        <div class="mobile-focus__weeknav">
            <BaseButton variant="icon" :icon="ICONS.arrow_back" @click="goPrevWeek">
                <q-tooltip>Previous week</q-tooltip>
            </BaseButton>
            <div class="mobile-focus__weeknav-label">{{ weekRangeLabel }}</div>
            <BaseButton variant="icon" :icon="ICONS.arrow_forward" @click="goNextWeek">
                <q-tooltip>Next week</q-tooltip>
            </BaseButton>
            <!-- in-context print. Parent wires this to
                 `planner.printFocusedWeek` (opens the print-view route in a
                 new tab, then the browser's "Save as PDF" is the export). -->
            <BaseButton
                v-if="plannedCount > 0"
                variant="icon"
                :icon="ICONS.content_copy"
                class="q-ml-sm"
                aria-label="Duplicate to next week"
                @click="emit('duplicateWeek')"
            >
                <q-tooltip>Duplicate to next week</q-tooltip>
            </BaseButton>
            <BaseButton
                v-if="plannedCount > 0"
                variant="icon"
                :icon="ICONS.print"
                @click="emit('print')"
            >
                <q-tooltip>Print this week</q-tooltip>
            </BaseButton>
        </div>

        <!-- FU-596 — flagship "Build my week" entry point. Dora's audience is
            mobile, so the auto-planner must be reachable here, not just on the
            desktop toolbar. -->
        <BaseButton
            variant="primary"
            class="full-width q-mt-sm"
            :icon="ICONS.auto_awesome"
            label="Build my week"
            @click="emit('openBuilder')"
        />

        <!-- Day strip — 7 day buttons across the top. Today is highlighted;
            the focused day carries the primary accent. -->
        <div class="mobile-focus__day-strip" role="tablist">
            <button
                v-for="day in weekDays"
                :key="day.iso"
                type="button"
                role="tab"
                :aria-selected="day.iso === focusedDayIso"
                class="mobile-focus__day-chip"
                :class="{
                    'mobile-focus__day-chip--today': day.iso === currentDayIso,
                    'mobile-focus__day-chip--focused': day.iso === focusedDayIso,
                    'mobile-focus__day-chip--past': isPastDay(day.iso),
                    'mobile-focus__day-chip--has-meals': entriesFor(day.iso).length > 0,
                }"
                @click="focusedDayIso = day.iso"
            >
                <span class="mobile-focus__day-chip-label">{{ day.label.charAt(0) }}</span>
                <span class="mobile-focus__day-chip-num">{{ dayOfMonth(day.iso) }}</span>
                <span
                    v-if="entriesFor(day.iso).length > 0"
                    class="mobile-focus__day-chip-dot"
                />
            </button>
        </div>

        <!-- Focused-day header -->
        <div class="mobile-focus__day-header">
            <div>
                <div class="text-h6 q-mb-none">{{ focusedDayLongLabel }}</div>
                <div class="text-caption dora-text-muted">{{ focusedDayHumanCount }}</div>
            </div>
            <q-badge
                v-if="focusedDayIso === currentDayIso"
                color="primary"
                class="q-ml-sm"
                label="Today"
            />
        </div>

        <!-- Focused-day entries (rich cards, slot-as-tag — same content
            model as Direction B). -->
        <div class="mobile-focus__entries">
            <MealPlanRichCard
                v-for="entry in entriesFor(focusedDayIso)"
                :key="entry.meal_plan_entry_id"
                :entry="entry"
                :shortfall="shortfallRecipeIds.has(entry.recipe_id)"
                :highlight="false"
                @view="emit('entryView', entry.recipe_id)"
                @cook="emit('entryCook', entry.recipe_id)"
                @remove="emit('entryRemove', entry)"
                @adjust="(d: number) => emit('entryAdjust', entry, d)"
                @link="emit('entryLink', entry)"
                @unlink="emit('entryUnlink', entry)"
                @lighter="emit('entryLighter', entry)"
            />
            <button
                v-if="!isPastDay(focusedDayIso)"
                type="button"
                class="mobile-focus__add"
                :class="{ 'mobile-focus__add--empty': !entriesFor(focusedDayIso).length }"
                @click="onAddTapped"
            >
                <q-icon :name="ICONS.add" size="16px" class="q-mr-xs" />
                <span>{{ entriesFor(focusedDayIso).length ? 'Add a meal' : `Plan ${focusedDayShortLabel}` }}</span>
            </button>
            <div
                v-else-if="!entriesFor(focusedDayIso).length"
                class="dora-text-muted text-center q-py-md text-caption"
            >
                Past day — read-only.
            </div>
        </div>

        <!-- Week-wide consequences (collapsible). Stays on the page so the
            mobile flow can act on shopping/cook signals without rotating
            back to a desktop. -->
        <q-expansion-item
            v-if="plannedCount > 0"
            class="mobile-focus__consequences q-mt-md"
            :icon="ICONS.shopping_cart"
            :label="`This week: ${plannedCount} planned`"
            :caption="weekStatusCaption"
            default-opened
        >
            <q-card flat>
                <q-card-section class="q-pt-none">
                    <MealPlanWeekStatus
                        :planned-count="plannedCount"
                        :shortfall-count="shortfallCount"
                        :need-to-buy-count="needToBuyCount"
                        :cook-by-label="cookByLabel"
                    />
                    <BaseButton
                        v-if="needToBuyCount > 0"
                        variant="primary"
                        class="full-width q-mt-sm"
                        :icon="ICONS.shopping_cart"
                        label="Generate shopping list"
                        :loading="generating"
                        @click="emit('generateList')"
                    />
                </q-card-section>
            </q-card>
        </q-expansion-item>

        <!-- Slot picker bottom-sheet — opened from the "Add a meal" tap.
            Picking a slot focuses that day+slot then opens the recipe sheet. -->
        <q-dialog
            v-model="slotSheetOpen"
            position="bottom"
            transition-show="slide-up"
            transition-hide="slide-down"
        >
            <q-card class="slot-sheet">
                <q-card-section class="row items-center q-py-sm">
                    <div class="text-subtitle1">Which slot?</div>
                    <q-space />
                    <BaseButton variant="icon" :icon="ICONS.close" @click="slotSheetOpen = false" />
                </q-card-section>
                <q-separator />
                <q-list separator>
                    <q-item
                        v-for="slot in slotNames"
                        :key="slot"
                        clickable v-close-popup
                        @click="onSlotChosen(slot)"
                    >
                        <q-item-section>{{ slot }}</q-item-section>
                    </q-item>
                </q-list>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import MealPlanRichCard from 'src/components/MealPlanRichCard.vue';
    import MealPlanWeekStatus from 'src/components/MealPlanWeekStatus.vue';
    import { ICONS } from 'src/style/icons';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import type { WeekDay } from 'src/composables/useMealPlanner';
    import { localTodayIso } from 'src/helpers/weekDates';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        weekDays: WeekDay[];
        slotNames: readonly string[];
        entriesFor: (dayIso: string) => MealPlanEntry[];
        isPastDay: (dayIso: string) => boolean;
        currentDayIso: string;
        shortfallRecipeIds: Set<string>;
        weekRangeLabel: string;
        plannedCount: number;
        shortfallCount: number;
        needToBuyCount: number;
        cookByLabel: string;
        generating: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'entryView', recipeId: string): void;
        (e: 'entryCook', recipeId: string): void;
        (e: 'entryRemove', entry: MealPlanEntry): void;
        (e: 'entryAdjust', entry: MealPlanEntry, delta: number): void;
        (e: 'entryLink', entry: MealPlanEntry): void;
        (e: 'entryUnlink', entry: MealPlanEntry): void;
        (e: 'entryLighter', entry: MealPlanEntry): void;
        (e: 'addToSlot', dayIso: string, slot: string): void;
        (e: 'generateList'): void;
        (e: 'goPrevWeek'): void;
        (e: 'goNextWeek'): void;
        (e: 'print'): void;
        (e: 'duplicateWeek'): void;
        (e: 'openBuilder'): void;
    }>();

    // Focused day — defaults to today when today is inside the focused week,
    // else the first day of the week.
    const focusedDayIso = ref<string>(initialFocusedDay());
    function initialFocusedDay(): string {
        const today = props.currentDayIso ?? localTodayIso();
        const inWeek = props.weekDays.some((d) => d.iso === today);
        return inWeek ? today : props.weekDays[0]?.iso ?? today;
    }

    // When the week changes, reset to today-in-week (or the first day) so the
    // user lands on a sensible default rather than the same weekday they were
    // on previously.
    watch(
        () => props.weekDays.map((d) => d.iso).join(','),
        () => {
            focusedDayIso.value = initialFocusedDay();
        },
    );

    const focusedDayLongLabel = computed(() => {
        const day = props.weekDays.find((d) => d.iso === focusedDayIso.value);
        if (!day) return '';
        return formatLocaleDate(day.iso, {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
        });
    });
    const focusedDayShortLabel = computed(
        () => props.weekDays.find((d) => d.iso === focusedDayIso.value)?.label ?? '',
    );
    const focusedDayHumanCount = computed(() => {
        const n = props.entriesFor(focusedDayIso.value).length;
        if (n === 0) return 'No meals planned';
        return `${n} meal${n === 1 ? '' : 's'} planned`;
    });

    function dayOfMonth(iso: string): number {
        return new Date(iso).getDate();
    }

    const weekStatusCaption = computed(() => {
        const parts: string[] = [];
        if (props.shortfallCount) parts.push(`${props.shortfallCount} to cook`);
        if (props.needToBuyCount) parts.push(`${props.needToBuyCount} to buy`);
        return parts.join(' · ');
    });

    // ── Add-flow: slot picker → emit('addToSlot') (parent opens the recipe sheet) ──
    const slotSheetOpen = ref(false);
    function onAddTapped() {
        slotSheetOpen.value = true;
    }
    function onSlotChosen(slot: string) {
        emit('addToSlot', focusedDayIso.value, slot);
        slotSheetOpen.value = false;
    }

    function goPrevWeek() {
        emit('goPrevWeek');
    }
    function goNextWeek() {
        emit('goNextWeek');
    }
</script>

<style scoped>
    .mobile-focus {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .mobile-focus__weeknav {
        display: flex;
        align-items: center;
        gap: 6px;
        justify-content: center;
    }
    .mobile-focus__weeknav-label {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .mobile-focus__day-strip {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 4px;
    }
    .mobile-focus__day-chip {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1px;
        padding: 6px 4px;
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        color: var(--text-secondary);
        font-size: 0.7rem;
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease;
        min-height: 44px;
    }
    .mobile-focus__day-chip:hover,
    .mobile-focus__day-chip:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .mobile-focus__day-chip--past {
        opacity: 0.55;
    }
    .mobile-focus__day-chip--today {
        border-color: var(--q-primary);
    }
    .mobile-focus__day-chip--focused {
        background: var(--q-primary);
        color: white;
        border-color: var(--q-primary);
    }
    .mobile-focus__day-chip--focused .mobile-focus__day-chip-dot {
        background: white;
    }
    .mobile-focus__day-chip-label {
        font-weight: 700;
    }
    .mobile-focus__day-chip-num {
        font-weight: 600;
        font-size: 0.85rem;
    }
    .mobile-focus__day-chip-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--q-primary);
        margin-top: 2px;
    }
    .mobile-focus__day-chip--has-meals:not(.mobile-focus__day-chip--focused) .mobile-focus__day-chip-dot {
        background: var(--q-primary);
    }
    .mobile-focus__day-header {
        display: flex;
        align-items: center;
        padding: 4px 0;
    }
    .mobile-focus__entries {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .mobile-focus__add {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 10px 12px;
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: transparent;
        border: 1px dashed var(--border-default);
        border-radius: 999px;
        cursor: pointer;
        transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease;
        min-height: 44px;
    }
    .mobile-focus__add:hover,
    .mobile-focus__add:focus-visible {
        color: var(--q-primary);
        border-color: var(--q-primary);
        background: var(--surface-sunken);
        outline: none;
    }
    .mobile-focus__add--empty {
        padding: 14px 16px;
        font-size: 0.9rem;
    }
    .mobile-focus__consequences {
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        border-radius: 8px;
    }
    .slot-sheet {
        width: 100vw;
        max-width: 100vw;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        margin: 0 !important;
    }
</style>
