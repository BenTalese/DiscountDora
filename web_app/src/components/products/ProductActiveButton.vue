<template>
    <BaseButton
        variant="icon"
        :icon="ICONS.search"
        :color="active ? 'primary' : undefined"
        :class="{ 'product-active-btn--off': !active }"
        :aria-label="label"
        @click.stop="emit('toggle')"
    >
        <BaseTooltip>{{ label }}</BaseTooltip>
    </BaseButton>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    /** Whether this product is still being tracked (feedback MP-8).
     *
     *  The owner's own suggestion: *"Not sure what styling shows products are
     *  inactive. Maybe a button with a search icon, grey if inactive, blue if
     *  active?"* The search icon turned out to be literally right — since
     *  batch D, `is_active` decides whether the scheduled sync re-scrapes the
     *  product at all (PF-8). So this control isn't cosmetic: it's the user's
     *  lever on what gets looked up, and grey genuinely means "we stopped
     *  checking this one".
     *
     *  That's also why the state lives on a control rather than only in a
     *  badge — a flag that changes background behaviour needs to be
     *  switchable where it's visible.
     */
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = defineProps<{ active: boolean }>();

    const emit = defineEmits<{ (e: 'toggle'): void }>();

    // Says what the click does *and* implies the current state, so a screen
    // reader gets both from one string (D-005).
    const label = computed(() =>
        props.active
            ? 'Tracking prices — click to stop checking this product'
            : 'Not tracking prices — click to start checking again',
    );
</script>

<style scoped>
    .product-active-btn--off {
        color: var(--text-muted);
    }
</style>
