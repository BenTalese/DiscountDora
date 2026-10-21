<template>
    <BaseButton
        v-if="isVisible"
        variant="icon"
        :icon="ICONS.menu"
        aria-label="Open navigation menu"
        @click="onClick"
    />
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    defineProps<{
        onClick: () => void;
        isVisible: boolean;
    }>();
</script>
