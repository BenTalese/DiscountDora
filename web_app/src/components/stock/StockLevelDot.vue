<template>
    <!-- Slot exists so a caller can drop a `q-tooltip` in: a bare coloured dot
         is not a decodable state signal on its own (D-013). -->
    <q-avatar
        :color="colour ?? undefined"
        :class="[{ 'dora-bg-neutral': !colour }, dotClass]"
        :size="size"
    >
        <slot />
    </q-avatar>
</template>

<script setup lang="ts">
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import { computed } from 'vue';

    /**
     * R-001: the level-dot avatar used across the stock-level picker
     * surfaces — Stock Item detail header, Stock Overview filter, and
     * the create-stock-item dialog. Centralising it here means a future
     * palette tweak lands in one place and the three pickers stay
     * visually identical by construction.
     */
    const props = withDefaults(defineProps<{
        sequence: number | null | undefined;
        size?: string;
        /** Extra classes for layout (e.g. `q-mr-sm` on the picker
         *  trigger). Kept as a free-text string so callers don't need
         *  to know about the sunken fallback. */
        dotClass?: string;
    }>(), {
        size: '16px',
        dotClass: '',
    });

    const colour = computed(() => colourForSequence(props.sequence));
</script>
