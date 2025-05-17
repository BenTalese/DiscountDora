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
            :size="getIconSize()"
        />
        <div class="dora-mainMenuButton-label">
            {{ label }}
        </div>
    </q-item>
</template>

<script setup lang="ts">
    //#region Imports
    import { useQuasar } from 'quasar';
    import type { MenuButtonProps } from './menuButtonProps';
    const $q = useQuasar();
    //#endregion Imports

    //#region Methods
    function getIconSize() {
        if ($q.screen.width > 1500) return '45px';
        else if ($q.screen.width > 1200) return '35px';
        else return '30px';
    }
    //#endregion Methods

    //#region Props and Events
    defineProps<MenuButtonProps>();
    //#endregion Props and Events
</script>

<style scoped lang="scss">
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
        width: 12%;
        min-height: 60px;

        @media (max-width: 1500px) {
            padding-top: 12px;
            width: 11%;
        }

        @media (max-width: 1200px) {
            padding-top: 15px;
            width: 10%;
        }
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
        text-align: center;

        @media (min-width: 1350px) {
            white-space: nowrap;
        }
    }

    .isHovering .dora-mainMenuButton-label {
        font-size: 1.3rem;
        max-height: 30px;
        opacity: 1;
        transform: translateY(-8px);

        @media (max-width: 1500px) {
            font-size: 1rem;
        }

        @media (max-width: 1200px) {
            font-size: 0.9rem;
        }
    }
</style>
