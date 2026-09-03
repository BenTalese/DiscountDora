<template>
    <!-- One pip per meal, capped. B2 / D-013: a coloured pip is never the only
         signal — every host pairs this with a tooltip or an `aria-label` that
         names the meals.

         R-001 — this exists because the month calendar and the mobile day strip
         had diverged into two different answers to the same question. The
         calendar drew per-meal pips coded planned / short / cooked; the phone's
         day chip drew ONE undifferentiated dot meaning "something is planned"
         (owner 2026-09-01: "I expect the mobile view day picker to act the same
         as the full calendar in that it shows the same pip info at the bottom.
         Currently they feel diverged"). Two call sites, one component.

         Owner feedback 2026-09-03 — the "+N" overflow label is gone from both
         hosts ("remove the +X text"; "don't think the +X is needed on mobile
         calendar — just show the dots"). The pips WRAP into rows of three
         inside a fixed-size cell instead, and stop when the cell is full: the
         old single row plus a text label grew the calendar's day square, which
         is what pushed the grid askew on a busy week. -->
    <span class="mp-pips" :class="`mp-pips--${size}`">
        <span
            v-for="(pip, i) in pips"
            :key="i"
            class="mp-pips__pip"
            :class="`mp-pips__pip--${pip}`"
        />
    </span>
</template>

<script setup lang="ts">
    import type { DayPip } from 'src/helpers/mealPlanDayPips';

    withDefaults(
        defineProps<{
            pips: DayPip[];
            /** `sm` is the phone's day chip, where the pip row shares a ~40px
             *  cell with a letter and a date. */
            size?: 'sm' | 'md';
        }>(),
        { size: 'md' },
    );
</script>

<style scoped>
    /* A fixed three-column grid rather than a flex row: the pips wrap to a
       second row on a busy day without the cell ever getting wider, which is
       the whole point (a day square that grows moves its neighbours). */
    .mp-pips {
        display: grid;
        grid-template-columns: repeat(3, auto);
        justify-content: center;
        gap: 2px;
    }
    .mp-pips--md { min-height: 5px; }
    .mp-pips--sm { min-height: 4px; }

    .mp-pips__pip {
        border-radius: 50%;
    }
    .mp-pips--md .mp-pips__pip { width: 5px; height: 5px; }
    .mp-pips--sm .mp-pips__pip { width: 4px; height: 4px; }

    .mp-pips__pip--planned { background: var(--semantic-positive); }
    .mp-pips__pip--short { background: var(--semantic-warning); }
    .mp-pips__pip--consumed { background: var(--text-muted); }
</style>
