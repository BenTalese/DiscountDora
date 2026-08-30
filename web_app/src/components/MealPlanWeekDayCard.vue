<template>
    <q-card
        bordered
        class="day-card q-mb-sm"
        :class="{ 'day-card--past': isPast, 'day-card--has-target': hasTargetedSlot }"
    >
        <q-card-section class="dora-bg-sunken q-py-xs row items-center">
            <div class="text-weight-bold">{{ day.label }}</div>
            <div class="text-caption q-ml-sm dora-text-muted">{{ formatDate(day.iso) }}</div>
            <q-badge v-if="isToday" color="primary" class="q-ml-sm" label="Today" />
            <q-space />
            <!-- FU-637 — a serving of each meal planned for this day. Not an
                 intake figure: the plan schedules food, not plates for named
                 people. Shows the shortfall when some meals couldn't be
                 counted, so a light-looking day can't be a half-counted one. -->
            <div v-if="nutrition && nutrition.kcal_per_serving !== null" class="text-caption dora-text-muted">
                {{ Math.round(nutrition.kcal_per_serving) }} kcal
                <span v-if="nutrition.counted_meals < nutrition.total_meals">
                    ({{ nutrition.counted_meals }}/{{ nutrition.total_meals }})
                </span>
                <q-tooltip>
                    One serving of each meal planned for {{ day.label }}<template
                        v-if="nutrition.counted_meals < nutrition.total_meals"
                    >, counting {{ nutrition.counted_meals }} of
                    {{ nutrition.total_meals }} meals — the rest don't have a
                    calorie figure yet</template>.
                </q-tooltip>
            </div>
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
                        @lighter="emit('entryLighter', entry)"
                        @link="emit('entryLink', entry)"
                        @unlink="emit('entryUnlink', entry)"
                    />
                    <span
                        v-if="!slotEntries(slot).length && !isPast"
                        class="slot-row__hint"
                    >
                        {{ isTargetedSlot(slot) ? '← pick a recipe' : 'tap to add' }}
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
                        @lighter="emit('entryLighter', entry)"
                        @link="emit('entryLink', entry)"
                        @unlink="emit('entryUnlink', entry)"
                    />
                </div>
            </div>

            <!-- Calm per-day add affordance — replaces the 5× italic
                "tap to add" sprawl when showAllSlots is false. Empty-state
                pattern, distinct from R-029. -->
            <button
                v-if="!isPast && unusedSlots.length"
                type="button"
                class="add-meal-button"
                :class="{ 'add-meal-button--empty': !visibleSlots.length && !otherEntries.length }"
            >
                <q-icon :name="ICONS.add" size="14px" class="q-mr-xs" />
                <span>{{ addButtonLabel }}</span>
                <!-- Arming a slot from this menu is a focus HAND-OFF, not a
                     round trip: §4.6 requires focus to land in the rail's
                     search so the armed slot can be answered from the keyboard.
                     QMenu fights that twice on close, and both were measured in
                     the browser:
                       1. it returns focus to whatever opened it — hence
                          `no-refocus`; without it focus snapped back to this
                          button and stayed there 1500ms after arming;
                       2. its teardown blurs the active element, so emitting on
                          click focused the rail and then lost it to BODY a beat
                          later.
                     So the selection is emitted on `@hide`, once the menu is
                     fully gone and nothing further will touch focus. -->
                <q-menu
                    anchor="top right"
                    self="bottom right"
                    auto-close
                    no-refocus
                    @hide="flushPendingSlot"
                >
                    <q-list dense style="min-width: 140px">
                        <q-item
                            v-for="slot in unusedSlots"
                            :key="slot"
                            clickable
                            @click="pendingSlot = slot"
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
    import type { MealPlanDayNutrition, MealPlanEntry } from 'src/models/mealPlan';
    import type { WeekDay } from 'src/composables/useMealPlanner';
    import { computed, ref } from 'vue';

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
        /** FU-637 — this day's server-summed calories. Null when nutrition is
         *  off or nothing on the day could be counted. */
        nutrition?: MealPlanDayNutrition | null;
    }>();

    /* The slot picked from the add-meal menu, held until the menu has finished
       hiding. See the `@hide` comment in the template: emitting on click races
       QMenu's own focus teardown, which would undo the rail's focus hand-off. */
    const pendingSlot = ref<string | null>(null);
    function flushPendingSlot() {
        const slot = pendingSlot.value;
        pendingSlot.value = null;
        if (slot) emit('selectSlot', slot);
    }

    /* §4.6 — when one of this day's slots is armed, the whole card takes an
       accent border. Without it the only marker is a single slot row inside one
       of seven stacked cards, so finding your own target means scanning slot by
       slot. */
    const hasTargetedSlot = computed(
        () => props.slotNames.some((slot) => props.isTargetedSlot(slot)),
    );

    const emit = defineEmits<{
        (e: 'selectSlot', slot: string): void;
        (e: 'entryView', recipeId: string): void;
        (e: 'entryCook', recipeId: string): void;
        (e: 'entryRemove', entry: MealPlanEntry): void;
        (e: 'entryAdjust', entry: MealPlanEntry, delta: number): void;
        (e: 'entryLink', entry: MealPlanEntry): void;
        (e: 'entryUnlink', entry: MealPlanEntry): void;
        (e: 'entryLighter', entry: MealPlanEntry): void;
    }>();

    // Q2 — used slots default. When showAllSlots is on, every household slot
    // renders (legacy behaviour, "tap to add" hint per slot). When off, only
    // slots with entries render; an explicit "+ add a meal" button opens a
    // slot-picker menu for the unused ones.
    /* An armed slot is ALWAYS visible, even when empty and even with
       "show all slots" off. §4.6 requires the destination to be named at both
       ends — the rail banner and the slot itself — because at 1280px+ they are
       far apart and naming both is the reliable version of drawing a connector.
       Without this the week's only marker was the card's accent border, so
       arming "Breakfast" from the add-meal menu highlighted the day but never
       said which slot; the target row simply didn't exist to be highlighted
       (measured in the browser — the `← pick a recipe` hint rendered nowhere). */
    const visibleSlots = computed(() => {
        if (props.showAllSlots) return props.slotNames;
        return props.slotNames.filter(
            (s) => props.slotEntries(s).length > 0 || props.isTargetedSlot(s),
        );
    });
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
    /* §4.6 — the armed slot is a FILLED accent surface with an inset accent
       bar. It used to be `outline: 2px dashed` over a sunken fill, which reads
       as an empty DROP ZONE — and with drag-and-drop retired (D1) a drop-zone
       idiom is not merely dated, it is actively misleading: there is nothing to
       drop any more. This says "this is the destination", not "drop here". */
    .slot-row--target {
        background: color-mix(in srgb, var(--q-primary) 14%, var(--surface-component));
        box-shadow: inset 2px 0 0 0 var(--q-primary);
    }
    .day-card--has-target {
        border-color: var(--q-primary);
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
        border: 1px dashed var(--border-default);
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
