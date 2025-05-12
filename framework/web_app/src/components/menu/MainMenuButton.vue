<template>
    <q-item
        :class="{ isHovering }"
        :to="link"
        active-class="dora-mainMenuButton-active"
        class="dora-mainMenuButton-container q-mx-xs"
        flat
        no-caps
        stack
    >
        <q-icon
            :name="icon"
            class="dora-mainMenuButton-icon"
            size="45px"
        />
        <div class="dora-mainMenuButton-label">
            {{ label }}
        </div>
    </q-item>
</template>

<script setup lang="ts">
    //#region Imports
    import type { MenuButtonProps } from './menuButtonProps';
    //#endregion Imports

    //#region Props and Events
    defineProps<MenuButtonProps>();
    //#endregion Props and Events
</script>

<style scoped>
    /* TODO: Colour this properly */
    .dora-mainMenuButton-active {
        background-color: #f2c037;
        color: rgb(133, 27, 27);
    }

    .dora-mainMenuButton-container {
        align-items: center;
        display: flex;
        flex-direction: column;
        transition:
            background-color 0.5s ease,
            color 0.5s ease;
        width: 130px;
    }

    .dora-mainMenuButton-icon {
        transition:
            transform 0.5s ease,
            margin 0.5s ease;
    }

    .isHovering .dora-mainMenuButton-icon {
        margin-bottom: 4px;
        transform: scale(0.7);
    }

    .dora-mainMenuButton-label {
        font-size: 0.65rem;
        font-weight: bold;
        line-height: 1;
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: translateY(10px);
        transition:
            opacity 0.5s ease,
            max-height 0.5s ease,
            font-size 0.5s ease,
            transform 0.5s ease;
        white-space: nowrap;
    }

    .isHovering .dora-mainMenuButton-label {
        font-size: 0.9rem;
        max-height: 30px;
        opacity: 1;
        transform: translateY(-8px);
    }
</style>
