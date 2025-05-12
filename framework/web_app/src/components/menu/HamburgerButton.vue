<template>
    <q-btn
        @click="onClick"
        aria-label="Menu"
        dense
        flat
        icon="menu"
        round
        v-if="isVisible"
    />
</template>

<script setup lang="ts">
    //#region Props and Events
    defineProps<{
        onClick: () => void;
        isVisible: boolean;
    }>();
    //#endregion Props and Events
</script>
