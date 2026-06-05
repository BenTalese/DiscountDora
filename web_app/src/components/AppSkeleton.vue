<template>
    <!--
        A5 — layout-mimicking skeleton placeholder. Compose several to mirror
        a view's real layout while it loads (instead of literal placeholder
        text like "Stock item"). Pulses on the same 1.6s rhythm as the boot
        splash; honours prefers-reduced-motion. Purely presentational, so it
        is hidden from assistive tech.
    -->
    <div
        class="app-skeleton"
        :class="`app-skeleton--${type}`"
        :style="dims"
        aria-hidden="true"
    />
</template>

<script setup lang="ts">
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** line = a row of text; rect = a block; circle = an avatar. */
            type?: 'line' | 'rect' | 'circle';
            width?: string;
            height?: string;
            radius?: string;
        }>(),
        { type: 'line' },
    );

    const dims = computed(() => ({
        width: props.width,
        height: props.height,
        borderRadius: props.radius,
    }));
</script>

<style scoped lang="scss">
    .app-skeleton {
        /* Theme-aware base: a touch of muted ink mixed into the sunken
           surface so it reads as a placeholder in both light and dark. */
        background: color-mix(in srgb, var(--surface-sunken) 86%, var(--text-muted) 14%);
        animation: app-skeleton-pulse 1.6s ease-in-out infinite;
    }
    .app-skeleton--line {
        width: 100%;
        height: 0.9em;
        border-radius: var(--radius-sm, 4px);
    }
    .app-skeleton--rect {
        width: 100%;
        height: 100%;
        border-radius: var(--radius-md, 6px);
    }
    .app-skeleton--circle {
        border-radius: var(--radius-full, 9999px);
    }

    /* Opacity-only pulse — matches the boot splash's 1.6s rhythm without
       scaling individual layout blocks (which would look wrong). */
    @keyframes app-skeleton-pulse {
        0%, 100% { opacity: 0.55; }
        50% { opacity: 1; }
    }
    @media (prefers-reduced-motion: reduce) {
        .app-skeleton {
            animation: none;
            opacity: 0.7;
        }
    }
</style>
