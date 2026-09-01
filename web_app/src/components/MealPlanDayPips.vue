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
         Currently they feel diverged"). Two call sites, one component. -->
    <span class="mp-pips" :class="`mp-pips--${size}`">
        <span
            v-for="(pip, i) in pips"
            :key="i"
            class="mp-pips__pip"
            :class="`mp-pips__pip--${pip}`"
        />
        <span v-if="overflow > 0" class="mp-pips__more">+{{ overflow }}</span>
    </span>
</template>

<script setup lang="ts">
    import type { DayPip } from 'src/helpers/mealPlanDayPips';

    withDefaults(
        defineProps<{
            pips: DayPip[];
            overflow: number;
            /** `sm` is the phone's day chip, where the pip row shares a ~40px
             *  cell with a letter and a date. */
            size?: 'sm' | 'md';
        }>(),
        { size: 'md' },
    );
</script>

<style scoped>
    .mp-pips {
        display: flex;
        align-items: center;
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

    .mp-pips__more {
        font-size: calc(var(--font-size-xs) * 1rem);
        line-height: 1;
        color: var(--text-secondary);
    }
</style>
