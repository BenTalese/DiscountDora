<template>
    <q-btn
        v-if="isVisible"
        flat
        dense
        round
        :icon="ICONS.menu"
        aria-label="Open navigation menu"
        @click="onClick"
    />
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    defineProps<{
        onClick: () => void;
        isVisible: boolean;
    }>();
</script>
