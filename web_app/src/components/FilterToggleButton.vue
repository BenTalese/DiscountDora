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
    -->
    <div class="row items-center q-gutter-sm no-wrap">
        <BaseButton
            v-if="(activeCount ?? 0) > 0"
            variant="ghost"
            :icon="ICONS.filter_alt_off"
            label="Clear"
            @click="$emit('clear')"
        />

        <BaseButton
            :variant="expanded ? 'secondary' : 'ghost'"
            :icon="ICONS.tune"
            :label="toggleLabel"
            @click="expanded = !expanded"
        >
            <q-badge v-if="(activeCount ?? 0) > 0" color="primary" floating>
                {{ activeCount }}
            </q-badge>
        </BaseButton>
    </div>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    withDefaults(
        defineProps<{
            activeCount?: number;
            toggleLabel?: string;
        }>(),
        { activeCount: 0, toggleLabel: 'Filters' },
    );

    defineEmits<{ (e: 'clear'): void }>();

    const expanded = defineModel<boolean>({ default: false });
</script>
