<template>
    <!--
        Filter toggle for the page toolbar. Pairs with `FilterBar` via a
        shared `expanded` v-model — drop this button in the page's main
        toolbar row, drop `<FilterBar v-model="expanded" :active-count>`
        below it; together they're one logical control.

        Feedback 2026-06-18: previously the toggle lived INSIDE FilterBar,
        on its own line. Pages with their own toolbar row got two rows of
        chrome instead of one. Splitting the toggle out lets it sit flush
        with the rest of the page's toolbar buttons.

        FU-121: Clear sits to the LEFT of Filters so the Filters button
        doesn't shift sideways when the Clear button appears/disappears.

        R-027 (2026-07-02): both buttons render as top-level siblings of
        the parent's toolbar row — no wrapper `<div>`. A wrapper carrying
        `q-gutter-*` clashes with the outer toolbar's own `q-gutter-*`
        (Quasar's negative-margin trick applies at both scopes and knocks
        the wrapper 8px above the sibling BaseButtons). Multi-root Vue 3
        template + parent-owned spacing is the encapsulation-clean fix.
    -->
    <BaseButton
        v-if="(activeCount ?? 0) > 0"
        variant="ghost"
        :icon="ICONS.filter_alt_off"
        :label="compact ? undefined : 'Clear'"
        aria-label="Clear filters"
        @click="$emit('clear')"
    >
        <BaseTooltip v-if="compact">Clear filters</BaseTooltip>
    </BaseButton>

    <BaseButton
        :variant="expanded ? 'secondary' : 'ghost'"
        :icon="ICONS.tune"
        :label="compact ? undefined : toggleLabel"
        :aria-label="toggleLabel"
        @click="expanded = !expanded"
    >
        <BaseTooltip v-if="compact">{{ toggleLabel }}</BaseTooltip>
        <q-badge v-if="(activeCount ?? 0) > 0" color="primary" floating>
            {{ activeCount }}
        </q-badge>
    </BaseButton>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    withDefaults(
        defineProps<{
            activeCount?: number;
            toggleLabel?: string;
            /** Drop both labels and ride the icons alone, with the name in a
             *  tooltip. Matches how the host toolbar's own actions collapse
             *  on phones (2026-08-16 feedback: these two were the only
             *  buttons on the Stock Overview toolbar still carrying text
             *  there). The page owns the breakpoint, not this component —
             *  it's the page that knows how crowded its toolbar is. */
            compact?: boolean;
        }>(),
        { activeCount: 0, toggleLabel: 'Filters', compact: false },
    );

    defineEmits<{ (e: 'clear'): void }>();

    const expanded = defineModel<boolean>({ default: false });
</script>
