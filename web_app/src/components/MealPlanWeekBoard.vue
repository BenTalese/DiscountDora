<template>
    <div class="week-board" :class="{ 'week-board--by-slot': groupBySlot }">
        <!-- Day-major view (default §6.4): a column per day, cards stacked. -->
        <template v-if="!groupBySlot">
            <div
                v-for="day in weekDays"
                :key="day.iso"
                class="week-board__col"
                :class="{
                    'week-board__col--past': isPastDay(day.iso),
                    'week-board__col--today': day.iso === currentDayIso,
                    'week-board__col--drop-target': dragOverDayIso === day.iso,
                }"
                role="group"
                :aria-label="`${day.label} ${formatDayDate(day.iso)}, ${entriesFor(day.iso).length} meal${entriesFor(day.iso).length === 1 ? '' : 's'} planned`"
                @dragover.prevent="onDragOver(day.iso)"
                @dragleave="onDragLeave(day.iso)"
                @drop.stop.prevent="onDrop(day.iso)"
            >
                <div class="week-board__header">
                    <div class="week-board__day-label">{{ day.label }}</div>
                    <div class="week-board__day-date">{{ formatDayDate(day.iso) }}</div>
                </div>
                <div class="week-board__entries">
                    <MealPlanRichCard
                        v-for="entry in entriesFor(day.iso)"
                        :key="entry.meal_plan_entry_id"
                        :entry="entry"
                        :shortfall="shortfallRecipeIds.has(entry.recipe_id)"
                        :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                        @view="emit('entryView', entry.recipe_id)"
                        @cook="emit('entryCook', entry.recipe_id)"
                        @remove="emit('entryRemove', entry)"
                        @adjust="(d: number) => emit('entryAdjust', entry, d)"
                    />
                    <button
                        v-if="!isPastDay(day.iso)"
                        type="button"
                        class="week-board__add"
                        :class="{ 'week-board__add--empty': !entriesFor(day.iso).length }"
                        :aria-label="`Add a meal to ${day.label} ${formatDayDate(day.iso)}`"
                        @click="emit('addToDay', day.iso)"
                    >
                        <q-icon :name="ICONS.add" size="14px" class="q-mr-xs" />
                        <span>{{ entriesFor(day.iso).length ? 'Add' : 'Add a meal' }}</span>
                    </button>
                </div>
            </div>
        </template>

        <!-- "Group by slot" alternate view — slot-major, day-minor. Honours
            the F46 intent ("time of day as rows") without forcing it as the
            scaffold. -->
        <template v-else>
            <div
                v-for="slot in slotNames"
                :key="slot"
                class="week-board__slot-row"
            >
                <div class="week-board__slot-label">{{ slot }}</div>
                <div class="week-board__slot-cells">
                    <div
                        v-for="day in weekDays"
                        :key="day.iso + slot"
                        class="week-board__slot-cell"
                        :class="{
                            'week-board__col--past': isPastDay(day.iso),
                            'week-board__col--today': day.iso === currentDayIso,
                            'week-board__col--drop-target': dragOverDayIso === day.iso,
                        }"
                        @dragover.prevent="onDragOver(day.iso)"
                        @dragleave="onDragLeave(day.iso)"
                        @drop.stop.prevent="onDropOnSlot(day.iso, slot)"
                    >
                        <MealPlanRichCard
                            v-for="entry in entriesForSlot(day.iso, slot)"
                            :key="entry.meal_plan_entry_id"
                            :entry="entry"
                            :shortfall="shortfallRecipeIds.has(entry.recipe_id)"
                            :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                            @view="emit('entryView', entry.recipe_id)"
                            @cook="emit('entryCook', entry.recipe_id)"
                            @remove="emit('entryRemove', entry)"
                            @adjust="(d: number) => emit('entryAdjust', entry, d)"
                        />
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import MealPlanRichCard from 'src/components/MealPlanRichCard.vue';
    import { ICONS } from 'src/style/icons';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import type { WeekDay } from 'src/composables/useMealPlanner';
    import { ref } from 'vue';

    const props = defineProps<{
        weekDays: WeekDay[];
        slotNames: readonly string[];
        entriesFor: (dayIso: string) => MealPlanEntry[];
        entriesForSlot: (dayIso: string, slot: string) => MealPlanEntry[];
        isPastDay: (dayIso: string) => boolean;
        currentDayIso: string;
        shortfallRecipeIds: Set<string>;
        hoveredRecipeIds: Set<string>;
        formatDayDate: (iso: string) => string;
        groupBySlot: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'entryView', recipeId: string): void;
        (e: 'entryCook', recipeId: string): void;
        (e: 'entryRemove', entry: MealPlanEntry): void;
        (e: 'entryAdjust', entry: MealPlanEntry, delta: number): void;
        (e: 'addToDay', dayIso: string): void;
        (e: 'dropOnDay', dayIso: string): void;
        (e: 'dropOnDaySlot', dayIso: string, slot: string): void;
    }>();

    // Drop-target highlight follows the dragged recipe — visual confirmation
    // that the column is the target before release (Fitts-friendly).
    const dragOverDayIso = ref<string | null>(null);
    function onDragOver(dayIso: string) {
        if (props.isPastDay(dayIso)) return;
        dragOverDayIso.value = dayIso;
    }
    function onDragLeave(dayIso: string) {
        if (dragOverDayIso.value === dayIso) dragOverDayIso.value = null;
    }
    function onDrop(dayIso: string) {
        dragOverDayIso.value = null;
        if (props.isPastDay(dayIso)) return;
        emit('dropOnDay', dayIso);
    }
    function onDropOnSlot(dayIso: string, slot: string) {
        dragOverDayIso.value = null;
        if (props.isPastDay(dayIso)) return;
        emit('dropOnDaySlot', dayIso, slot);
    }
</script>

<style scoped>
    /* Day-major: 7 equal columns on desktop; collapses to a vertical stack
        below 1024px (the A page already serves narrow viewports well, and
        the dedicated mobile pattern lands in R-Phase 4). */
    .week-board {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 8px;
        align-items: stretch;
    }
    .week-board--by-slot {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    @media (max-width: 1023px) {
        .week-board:not(.week-board--by-slot) {
            grid-template-columns: 1fr;
        }
    }
    .week-board__col {
        display: flex;
        flex-direction: column;
        background: var(--surface-elevated);
        border: 1px solid var(--separator);
        border-radius: 8px;
        min-height: 180px;
        transition: border-color 0.12s ease, background 0.12s ease;
    }
    .week-board__col--past {
        opacity: 0.55;
    }
    .week-board__col--today {
        border-color: var(--q-primary);
        box-shadow: 0 0 0 1px var(--q-primary) inset;
    }
    .week-board__col--drop-target {
        border-color: var(--q-primary);
        background: var(--surface-sunken);
    }
    .week-board__header {
        padding: 6px 8px;
        border-bottom: 1px solid var(--separator);
        background: var(--surface-sunken);
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    .week-board__day-label {
        font-weight: 700;
        font-size: 0.85rem;
    }
    .week-board__day-date {
        font-size: 0.7rem;
        color: var(--text-muted);
    }
    .week-board__entries {
        flex: 1 1 auto;
        padding: 6px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .week-board__add {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-top: auto;
        padding: 6px 10px;
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: transparent;
        border: 1px dashed var(--separator);
        border-radius: 999px;
        cursor: pointer;
        transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease;
        min-height: 28px;
    }
    .week-board__add:hover,
    .week-board__add:focus-visible {
        color: var(--q-primary);
        border-color: var(--q-primary);
        background: var(--surface-sunken);
        outline: none;
    }
    .week-board__add--empty {
        margin-top: 0;
        padding: 12px;
        font-size: 0.82rem;
    }

    /* Group-by-slot view — slot label on the left, 7 cells across. */
    .week-board__slot-row {
        display: grid;
        grid-template-columns: 6rem 1fr;
        gap: 8px;
        align-items: stretch;
    }
    .week-board__slot-label {
        font-weight: 600;
        font-size: 0.78rem;
        color: var(--text-secondary);
        padding-top: 8px;
    }
    .week-board__slot-cells {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 6px;
    }
    .week-board__slot-cell {
        min-height: 60px;
        padding: 4px;
        background: var(--surface-elevated);
        border: 1px solid var(--separator);
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
</style>
