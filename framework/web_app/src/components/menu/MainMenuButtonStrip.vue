<template>
    <div
        @mouseenter="isHovering = true"
        @mouseleave="isHovering = false"
        class="row justify-evenly no-wrap scroll-x dora-mainMenuButtonStrip"
        v-if="isVisible"
    >
        <MainMenuButton
            :isHovering="isHovering"
            :key="link.label"
            v-bind="link"
            v-for="link in menuLinks"
        />
    </div>
</template>

<script setup lang="ts">
    //#region Imports
    import { ref } from 'vue';
    import MainMenuButton from './MainMenuButton.vue';
    import type { MenuButtonProps } from './menuButtonProps';
    //#endregion Imports

    //#region Props and Events
    defineProps<{
        isVisible: boolean;
        menuLinks: MenuButtonProps[];
    }>();
    //#endregion Props and Events

    //#region State
    const isHovering = ref(false);
    //#endregion State
</script>

<style scoped>
    .dora-mainMenuButtonStrip {
        flex: 1;
        scrollbar-width: none; /* Hide scrollbar on Firefox */
        -ms-overflow-style: none; /* Hide scrollbar on IE/Edge */
    }

    .dora-mainMenuButtonStrip::-webkit-scrollbar {
        display: none; /* Hide scrollbar on Chrome, Safari, Opera */
    }
</style>
