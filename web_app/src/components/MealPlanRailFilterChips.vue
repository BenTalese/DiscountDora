<template>
    <!-- BRIEF_MEAL_PLANNER_RAIL_AND_SHELL §4.3 — the rail's filter row, which
         replaced four collapsible accordions (F21: "it should be filterable and
         vertical because it's a list, and it can hold hundreds of recipes").

         Composed from the shared `FilterChip` rather than a third chip
         implementation (R-001). The brief proposed building a new chip because
         neither `BaseSegmented` (capped at 2-4 options by B2a; this is five) nor
         `BaseToggleGroup` (for *independent* choices; these are mutually
         exclusive) fits the ROW — but the individual chip already existed, with
         the D-020 indicator-token handling and the DR-15 press/bump feedback
         already solved on it. So the row is new and the chip is not; `FilterChip`
         gained only a `disabled` prop, which B2a wanted anyway.

         Mutual exclusion is expressed by binding each chip's `modelValue` to
         `key === selected`, and by ignoring a click that would turn the active
         chip off — there is always exactly one active filter, so a chip is a
         radio wearing a chip's clothes. `aria-pressed` per chip comes from
         `FilterChip`.

         D-011 — this wraps to two lines at the rail's narrow width. It must
         never scroll horizontally. -->
    <div class="rail-chips" role="group" aria-label="Filter recipes">
        <FilterChip
            v-for="chip in chips"
            :key="chip.key"
            :model-value="chip.key === selected"
            :disabled="chip.disabled"
            :icon="chip.key === 'suggests' ? ICONS.auto_awesome : undefined"
            :active-color="chip.key === 'suggests' ? 'primary' : 'secondary'"
            :class="{ 'rail-chips__suggests': chip.key === 'suggests' }"
            @update:model-value="onChipClick(chip)"
        >
            {{ chip.label }}
            <!-- The count is the chip's own scale, so it reads as part of the
                 label rather than a separate badge competing with it. `all`
                 carries no count: it's the whole list, and "All (47)" beside
                 "Favourites (3)" invites reading 47 as a subset. `suggests`
                 carries none either — it ranks rather than narrows, so a count
                 would claim it filters. -->
            <span
                v-if="chip.key !== 'all' && chip.key !== 'suggests'"
                class="rail-chips__count"
            >{{ chip.count }}</span>
            <q-tooltip v-if="chip.disabled && chip.disabledReason">
                {{ chip.disabledReason }}
            </q-tooltip>
        </FilterChip>
    </div>
</template>

<script setup lang="ts">
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import type { RecipeFilterChip, RecipeFilterKey } from 'src/helpers/recipeRailFilters';
    import { ICONS } from 'src/style/icons';

    defineProps<{
        chips: RecipeFilterChip[];
        selected: RecipeFilterKey;
    }>();

    const emit = defineEmits<{
        (e: 'update:selected', key: RecipeFilterKey): void;
    }>();

    /**
     * Selecting is one-way: clicking the active chip does nothing rather than
     * clearing to an empty filter state. "No filter" is what `All` means, and
     * it is already a chip — a second way to reach the same state, reachable
     * only by clicking the thing that is already on, would just look broken.
     */
    function onChipClick(chip: RecipeFilterChip) {
        if (chip.disabled) return;
        emit('update:selected', chip.key);
    }
</script>

<style scoped>
    .rail-chips {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-1);
    }

    /* §4.4 — "Dora suggests" is NOT a filter: it re-ranks and adds a reason
       line rather than narrowing a set. Putting it in a filter row is a real
       semantic mismatch, accepted because this is where the user looks — but
       the brief requires it be *marked*: first position, leading sparkle, and
       an accent outline even when inactive. */
    .rail-chips__suggests {
        border-color: var(--brand-primary);
        font-weight: 500;
    }

    .rail-chips__count {
        margin-left: var(--space-1);
        opacity: 0.7;
        font-variant-numeric: tabular-nums;
    }
</style>
