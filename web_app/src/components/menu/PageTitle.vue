<template>
    <q-toolbar-title shrink class="dora-pageTitle text-accent">
        {{ label }}
    </q-toolbar-title>
</template>

<script setup lang="ts">
    defineProps<{
        label: string;
    }>();
</script>

<style scoped>
    .dora-pageTitle {
        font-family: 'Cute Dino', sans-serif;
        /* A6 — scale token (was fixed 24px) so it follows the text-size pref. */
        font-size: calc(var(--font-size-2xl) * 1rem);
        margin-top: 4px;
        opacity: 0.9;
    }
</style>
