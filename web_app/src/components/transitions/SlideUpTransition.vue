<template>
    <transition name="dora-slide-up" :appear="!!appear">
        <slot />
    </transition>
</template>

<script lang="ts" setup>
    // Fade + small upward settle. For elements that arrive from below the
    // fold: bottom sheets, toasts, inline panels, dialog content.
    withDefaults(defineProps<{ appear?: boolean }>(), { appear: false });
</script>

<style scoped>
    .dora-slide-up-enter-active {
        transition: opacity var(--motion-normal) var(--motion-ease-out),
            transform var(--motion-normal) var(--motion-ease-out);
    }
    .dora-slide-up-leave-active {
        transition: opacity var(--motion-fast) var(--motion-ease-in),
            transform var(--motion-fast) var(--motion-ease-in);
    }
    .dora-slide-up-enter-from,
    .dora-slide-up-leave-to {
        opacity: 0;
        transform: translateY(var(--motion-slide-distance));
    }
</style>
