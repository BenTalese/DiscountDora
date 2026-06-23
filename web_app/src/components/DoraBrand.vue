<template>
    <span class="dora-brand" :class="{ 'dora-brand--inline': inline }">
        Dashy Dora
    </span>
</template>

<script setup lang="ts">
    // IMPL_PLAN_SETTINGS_REBUILD §2.5 step 5 — shared "Dashy Dora" mark.
    // Centralises the Cute Dino font so every surface reusing the brand
    // string stays consistent.
    defineProps<{ inline?: boolean }>();
</script>

<style scoped lang="scss">
    .dora-brand {
        font-family: 'Cute Dino', 'Nunito Variable', 'Nunito', sans-serif;
        letter-spacing: 0.005em;
    }
    .dora-brand--inline {
        display: inline;
    }
</style>
