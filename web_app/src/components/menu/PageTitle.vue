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
        font-size: 24px;
        margin-top: 4px;
        opacity: 0.9;
    }
</style>
