<template>
    <q-card bordered class="day-card q-mb-sm" :class="{ 'day-card--past': isPast }">
        <q-card-section class="dora-bg-sunken q-py-xs row items-center">
            <div class="text-weight-bold">{{ day.label }}</div>
            <div class="text-caption q-ml-sm dora-text-muted">{{ formatDate(day.iso) }}</div>
            <q-badge v-if="isToday" color="primary" class="q-ml-sm" label="Today" />
        </q-card-section>
        <q-card-section class="q-pa-sm column q-gutter-xs">
            <!-- R-Phase 6 §4.6 — slot row is a real <button> so it's
                focusable, announced, and Enter/Space-activated. Past days
                render a plain region (no action). -->
            <component
                :is="isPast ? 'div' : 'button'"
                v-for="slot in visibleSlots"
                :key="slot"
                :type="isPast ? undefined : 'button'"
                :aria-label="isPast ? undefined : `Add a meal to ${day.label} ${formatDate(day.iso)} ${slot}`"
                class="slot-row"
                :class="{
                    'slot-row--target': isTargetedSlot(slot),
                    'slot-row--clickable': !isPast,
                }"
                @click="!isPast && emit('selectSlot', slot)"
                @dragover.prevent
                @drop.stop="emit('dropOnSlot', slot)"
            >
                <div class="slot-row__label">{{ slot }}</div>
                <div class="slot-row__entries">
                    <MealPlanEntryChip
                        v-for="entry in slotEntries(slot)"
                        :key="entry.meal_plan_entry_id"
                        :entry="entry"
                        :show-slot="false"
                        :shortfall="shortfallRecipeIds.has(entry.recipe_id)"
                        :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                        @click.stop
                        @view="emit('entryView', entry.recipe_id)"
                        @cook="emit('entryCook', entry.recipe_id)"
                        @remove="emit('entryRemove', entry)"
                        @adjust="(d: number) => emit('entryAdjust', entry, d)"
                    />
                    <span
                        v-if="!slotEntries(slot).length && !isPast"
                        class="slot-row__hint"
                    >
                        {{ isTargetedSlot(slot) ? 'pick a recipe →' : 'tap to add' }}
                    </span>
                </div>
            </component>

            <!-- Off-vocabulary historical slots land here (C-2.A). -->
            <div v-if="otherEntries.length" class="slot-row">
                <div class="slot-row__label">Other</div>
                <div class="slot-row__entries">
                    <MealPlanEntryChip
                        v-for="entry in otherEntries"
                        :key="entry.meal_plan_entry_id"
                        :entry="entry"
                        :show-slot="true"
                        :shortfall="shortfallRecipeIds.has(entry.recipe_id)"
                        :highlight="hoveredRecipeIds.has(entry.recipe_id)"
                        @click.stop
                        @view="emit('entryView', entry.recipe_id)"
                        @cook="emit('entryCook', entry.recipe_id)"
                        @remove="emit('entryRemove', entry)"
                        @adjust="(d: number) => emit('entryAdjust', entry, d)"
                    />
                </div>
            </div>

            <!-- Calm per-day add affordance (R-014). Replaces the 5× italic
                "tap to add" sprawl when showAllSlots is false. -->
            <button
                v-if="!isPast && unusedSlots.length"
                type="button"
                class="add-meal-button"
                :class="{ 'add-meal-button--empty': !visibleSlots.length && !otherEntries.length }"
            >
                <q-icon :name="ICONS.add" size="14px" class="q-mr-xs" />
                <span>{{ addButtonLabel }}</span>
                <q-menu anchor="top right" self="bottom right" auto-close>
                    <q-list dense style="min-width: 140px">
                        <q-item
                            v-for="slot in unusedSlots"
                            :key="slot"
                            clickable
                            @click="emit('selectSlot', slot)"
                        >
                            <q-item-section>{{ slot }}</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </button>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import MealPlanEntryChip from 'components/MealPlanEntryChip.vue';
    import { ICONS } from 'src/style/icons';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import type { WeekDay } from 'src/composables/useMealPlanner';
    import { computed } from 'vue';

    const props = defineProps<{
        day: WeekDay;
        isPast: boolean;
        isToday: boolean;
        slotNames: readonly string[];
        slotEntries: (slot: string) => MealPlanEntry[];
        otherEntries: MealPlanEntry[];
        isTargetedSlot: (slot: string) => boolean;
        shortfallRecipeIds: Set<string>;
        hoveredRecipeIds: Set<string>;
        formatDate: (iso: string) => string;
        showAllSlots: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'selectSlot', slot: string): void;
        (e: 'dropOnSlot', slot: string): void;
        (e: 'entryView', recipeId: string): void;
        (e: 'entryCook', recipeId: string): void;
        (e: 'entryRemove', entry: MealPlanEntry): void;
        (e: 'entryAdjust', entry: MealPlanEntry, delta: number): void;
    }>();

    // Q2 — used slots default. When showAllSlots is on, every household slot
    // renders (legacy behaviour, "tap to add" hint per slot). When off, only
    // slots with entries render; an explicit "+ add a meal" button opens a
    // slot-picker menu for the unused ones.
    const visibleSlots = computed(() =>
        props.showAllSlots ? props.slotNames : props.slotNames.filter((s) => props.slotEntries(s).length > 0),
    );
    const unusedSlots = computed(() => props.slotNames.filter((s) => !props.slotEntries(s).length));

    const addButtonLabel = computed(() => {
        if (!visibleSlots.value.length && !props.otherEntries.length) return `Plan ${props.day.label}`;
        return 'Add a meal';
    });
</script>

<style scoped>
    .day-card--past {
        opacity: 0.6;
    }
    /* Reset native button affordances — slot rows are buttons for
        accessibility (R-Phase 6 §4.6) but render as plain rows. */
    .slot-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 4px 6px;
        border-radius: 6px;
        transition: background 0.12s ease, outline 0.12s ease;
        background: transparent;
        border: 0;
        text-align: left;
        font: inherit;
        color: inherit;
        width: 100%;
        min-height: 28px;
    }
    .slot-row--clickable {
        cursor: pointer;
    }
    .slot-row--clickable:hover,
    .slot-row--clickable:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .slot-row--clickable:focus-visible {
        outline: 2px solid var(--q-primary);
        outline-offset: 2px;
    }
    .slot-row--target {
        outline: 2px dashed var(--q-primary);
        outline-offset: -2px;
        background: var(--surface-sunken);
    }
    .slot-row__label {
        flex: 0 0 5.5rem;
        font-size: 0.78rem;
        font-weight: 600;
        padding-top: 4px;
        color: var(--text-secondary);
    }
    .slot-row__entries {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .slot-row__hint {
        font-size: 0.72rem;
        color: var(--text-muted);
        font-style: italic;
    }
    .add-meal-button {
        display: inline-flex;
        align-items: center;
        align-self: flex-start;
        margin-top: 4px;
        padding: 4px 10px;
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
    .add-meal-button:hover,
    .add-meal-button:focus-visible {
        color: var(--q-primary);
        border-color: var(--q-primary);
        background: var(--surface-sunken);
        outline: none;
    }
    /* Empty-day variant — a calm full-width affordance, not a tiny chip. */
    .add-meal-button--empty {
        align-self: stretch;
        justify-content: center;
        padding: 10px 12px;
        font-size: 0.82rem;
        min-height: 36px;
    }
</style>
