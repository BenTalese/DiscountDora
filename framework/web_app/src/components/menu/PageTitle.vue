<template>
    <q-toolbar-title
        :shrink="shouldShrink"
        class="dora-toolbarTitle text-accent"
    >
        {{ label }}
    </q-toolbar-title>
</template>

<script setup lang="ts">
    //#region Props and Events
    defineProps<{
        label: string,
        shouldShrink: boolean
    }>();
    //#endregion Props and Events
</script>

<style scoped>
    .dora-toolbarTitle {
        font-family: 'Cute Dino';
        font-size: 30px;
        margin-top: 5px;
    }
</style>
