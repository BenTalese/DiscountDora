<template>
    <!--
        A5 — the one inline/short-wait spinner. Wraps q-spinner with a
        consistent default size + theme-aware colour, optional label, and a
        `block` mode that centres it in a padded column for page-level waits.
        Use a Skeleton (AppSkeleton) instead for list/detail loads where the
        layout is known.
    -->
    <div class="app-spinner" :class="{ 'app-spinner--block': block }" role="status">
        <q-spinner :size="size" :thickness="thickness" :color="color" />
        <div v-if="label" class="app-spinner__label dora-text-muted text-caption">
            {{ label }}
        </div>
    </div>
</template>

<script setup lang="ts">
    withDefaults(
        defineProps<{
            size?: string;
            thickness?: number;
            /** Quasar colour name; rides `--q-*` so it's theme-aware. */
            color?: string;
            label?: string;
            /** Centre in a padded full-width column (page-level short wait). */
            block?: boolean;
        }>(),
        {
            size: '32px',
            thickness: 5,
            color: 'primary',
        },
    );
</script>

<style scoped>
    .app-spinner {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2, 8px);
    }
    .app-spinner--block {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: var(--space-3, 12px);
        width: 100%;
        padding: var(--space-12, 48px) 0;
    }
</style>
