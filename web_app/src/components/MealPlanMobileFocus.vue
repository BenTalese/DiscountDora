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
            <!-- Owner feedback 2026-09-03 — *"mobile view is missing some
                 functionality… no save as template, no browse/apply template,
                 no clear week."* It was: the phone carried two of the desktop
                 toolbar's six week actions as bare icon buttons, and the other
                 four had no entry point at all below 1024px. This is the SAME
                 overflow menu the desktop toolbar carries — same order, same
                 disabled rules — so there is one list of week actions rather
                 than a phone-sized subset of one (R-001 / D-023).

                 Duplicate and print give up their promoted icon buttons to it:
                 two of six promoted for no reason is what made the gap easy to
                 miss in the first place. `planner.printFocusedWeek` still does
                 the work (it opens the print-view route in a new tab, and the
                 browser's "Save as PDF" is the export). -->
            <BaseButton
                variant="icon"
                :icon="ICONS.more_vert"
                class="q-ml-sm"
                aria-label="More week actions"
            >
                <q-menu anchor="bottom right" self="top right">
                    <q-list style="min-width: 220px">
                        <q-item
                            v-close-popup clickable
                            :disable="plannedCount === 0"
                            @click="emit('duplicateWeek')"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.content_copy" />
                            </q-item-section>
                            <q-item-section>Duplicate to next week</q-item-section>
                        </q-item>
                        <q-item
                            v-close-popup clickable
                            :disable="plannedCount === 0"
                            @click="emit('print')"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.print" />
                            </q-item-section>
                            <q-item-section>Print this week</q-item-section>
                        </q-item>

                        <q-separator />

                        <q-item
                            v-close-popup clickable
                            :disable="!canSaveCurrentWeek"
                            @click="emit('saveTemplate')"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.save" />
                            </q-item-section>
                            <q-item-section>Save week as template…</q-item-section>
                        </q-item>
                        <q-item v-close-popup clickable @click="emit('openTemplates')">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.event_repeat" />
                            </q-item-section>
                            <q-item-section>Apply template…</q-item-section>
                        </q-item>

                        <q-separator />

                        <q-item
                            v-close-popup clickable
                            :disable="plannedCount === 0"
                            class="text-negative"
                            @click="emit('clearWeek')"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.delete_outline" color="negative" />
                            </q-item-section>
                            <q-item-section>Clear week</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
                <q-tooltip>More week actions</q-tooltip>
            </BaseButton>
        </div>

        <!-- FU-596 — flagship "Build my week" entry point. Dora's audience is
            mobile, so the auto-planner must be reachable here, not just on the
            desktop toolbar. -->
        <BaseButton
            variant="primary"
            class="full-width q-mt-sm"
            :icon="ICONS.dora_voice"
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
                :aria-label="dayChipLabel(day)"
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
                <!-- Owner feedback 2026-09-01 — "I expect the mobile view day
                     picker to act the same as the full calendar in that it
                     shows the same pip info at the bottom. Currently they feel
                     diverged." They were: this drew ONE dot meaning "something
                     is planned", while the desktop calendar drew a pip per meal
                     coded planned / short / cooked. Same component now, at the
                     small size (`MealPlanDayPips.vue`). D-013 — the pips are
                     not the only signal; the chip's `aria-label` names the
                     day's state in words. -->
                <MealPlanDayPips
                    class="mobile-focus__day-chip-pips"
                    size="sm"
                    v-bind="pipsFor(day.iso)"
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
                :shortfall="entry.needs_cooking"
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

        <!-- The week's consequences — the status strip and "This week's
             shopping" with its per-ingredient breakdown — used to live here as
             a collapsible card whose own header restated what was inside it.
             Owner feedback 2026-09-03, twice over: *"the expandable card in
             mobile view at the bottom is a bit odd. Don't like how it
             duplicates information so much. Just make it a normal card with
             the expanded contents shown"* and *"can't see the ingredient
             breakdown properly on the shopping list"*. Both are answered by
             giving the phone the SAME two components the desktop right rail
             renders, plainly and un-collapsed, rather than a second
             implementation behind a disclosure (R-001). The page owns that —
             it owns the planner's data — so see `MealPlansOverview.vue`'s
             mobile branch. -->

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
    import MealPlanDayPips from 'src/components/MealPlanDayPips.vue';
    import MealPlanRichCard from 'src/components/MealPlanRichCard.vue';
    import { ICONS } from 'src/style/icons';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import type { WeekDay } from 'src/composables/useMealPlanner';
    import { dayPips } from 'src/helpers/mealPlanDayPips';
    import { localTodayIso } from 'src/helpers/weekDates';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        weekDays: WeekDay[];
        slotNames: readonly string[];
        entriesFor: (dayIso: string) => MealPlanEntry[];
        isPastDay: (dayIso: string) => boolean;
        currentDayIso: string;
        weekRangeLabel: string;
        plannedCount: number;
        /** Gates "Save week as template…" on the same fact the desktop
         *  toolbar's copy of that item gates on (R-003 — one predicate, owned
         *  by the page). */
        canSaveCurrentWeek: boolean;
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
        (e: 'goPrevWeek'): void;
        (e: 'goNextWeek'): void;
        (e: 'print'): void;
        (e: 'duplicateWeek'): void;
        (e: 'saveTemplate'): void;
        (e: 'openTemplates'): void;
        (e: 'clearWeek'): void;
        (e: 'openBuilder'): void;
    }>();

    /** Same coding as the desktop month grid, from the same helper: each
     *  entry's own server-owned `consumed_at` + `needs_cooking` (R-003). */
    function pipsFor(dayIso: string) {
        return dayPips(props.entriesFor(dayIso));
    }

    /** The pips' text alternative. A chip reading "M 15" with three coloured
     *  dots says nothing to a screen reader otherwise. */
    function dayChipLabel(day: WeekDay): string {
        const entries = props.entriesFor(day.iso);
        if (!entries.length) return `${day.label} ${dayOfMonth(day.iso)} — no meals planned`;
        const short = entries.filter((e) => !e.consumed_at && e.needs_cooking).length;
        const meals = `${entries.length} meal${entries.length === 1 ? '' : 's'}`;
        return short
            ? `${day.label} ${dayOfMonth(day.iso)} — ${meals}, ${short} short`
            : `${day.label} ${dayOfMonth(day.iso)} — ${meals}`;
    }

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

    // `onListCount` / `weekStatusCaption` / `addToListLabel` lived here to feed
    // the collapsible consequences card. All three went with it on 2026-09-03:
    // the caption existed only to summarise a panel that was open by default,
    // and the other two are `MealPlanWeekStatus`'s and
    // `MealPlanShoppingSummary`'s own business now that the page renders those
    // two directly.

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
    /* On the focused chip the primary fill is the ground, so the status
       colours have to sit on it rather than under it. Only `planned` collides
       (it is the same green family); warning and muted stay legible. */
    .mobile-focus__day-chip--focused :deep(.mp-pips__pip--planned) {
        background: white;
    }
    .mobile-focus__day-chip--focused :deep(.mp-pips__more) {
        color: white;
    }
    .mobile-focus__day-chip-label {
        font-weight: 700;
    }
    .mobile-focus__day-chip-num {
        font-weight: 600;
        font-size: 0.85rem;
    }
    .mobile-focus__day-chip-pips {
        margin-top: 2px;
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
    .slot-sheet {
        width: 100vw;
        max-width: 100vw;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        margin: 0 !important;
    }
</style>
