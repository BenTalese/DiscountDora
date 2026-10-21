<template>
    <button type="button" class="location-add-chip" @click="$emit('click')">
        <q-icon :name="ICONS.add" size="14px" />
        <span>{{ label }}</span>
    </button>
</template>

<script lang="ts" setup>
    // R-001 — the dashed "add a child here" affordance, once. It was written
    // inline on the area row ("+ Section") while the zone card used a
    // BaseButton ghost ("+ Area"), so the two levels of the same tree offered
    // the same action in two different visual languages (owner 2026-09-03).
    import { ICONS } from 'src/style/icons';

    defineProps<{ label: string }>();
    defineEmits<{ (e: 'click'): void }>();
</script>

<style scoped lang="scss">
    .location-add-chip {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: var(--space-1) var(--space-3);
        border: 1px dashed var(--border-default);
        border-radius: var(--radius-sm);
        background: none;
        font: inherit;
        font-size: 0.8125rem;
        line-height: 1.4;
        color: var(--text-muted);
        cursor: pointer;
        transition: color var(--motion-fast, 120ms) ease,
            border-color var(--motion-fast, 120ms) ease;
    }
    .location-add-chip:hover {
        color: var(--text-secondary);
        border-color: var(--border-strong);
    }
    .location-add-chip:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }
    /* D-004 — real control, so a touch target on coarse pointers. */
    @media (pointer: coarse) {
        .location-add-chip {
            min-height: 44px;
            padding-inline: var(--space-4);
        }
    }
</style>
