<template>
    <q-btn
        v-if="isVisible"
        flat
        dense
        round
        icon="menu"
        aria-label="Open navigation menu"
        @click="onClick"
    />
</template>

<script setup lang="ts">
    defineProps<{
        onClick: () => void;
        isVisible: boolean;
    }>();
</script>
