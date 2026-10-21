<template>
    <transition name="dora-scale" :appear="!!appear">
        <slot />
    </transition>
</template>

<script lang="ts" setup>
    // Fade + subtle scale-up. The shared modal/popup open animation — the
    // vuejs.org modal example pattern. Spring easing gives a small settle.
    withDefaults(defineProps<{ appear?: boolean }>(), { appear: false });
</script>

<style scoped>
    .dora-scale-enter-active {
        transition: opacity var(--motion-normal) var(--motion-ease-out),
            transform var(--motion-normal) var(--motion-ease-spring);
    }
    .dora-scale-leave-active {
        transition: opacity var(--motion-fast) var(--motion-ease-in),
            transform var(--motion-fast) var(--motion-ease-in);
    }
    .dora-scale-enter-from,
    .dora-scale-leave-to {
        opacity: 0;
        transform: scale(var(--motion-scale-from));
    }
</style>
