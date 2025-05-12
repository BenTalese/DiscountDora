<template>
    <q-item
        :to="link"
        active-class="dora-sideMenuButton-active"
        clickable
        exact
        tag="a"
    >
        <q-item-section avatar>
            <q-icon :name="icon" />
        </q-item-section>

        <q-item-section>
            <q-item-label>{{ label }}</q-item-label>
            <q-item-label caption>{{ caption }}</q-item-label>
        </q-item-section>
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
    .dora-sideMenuButton-active {
        color: rgb(133, 27, 27);
        background: #f2c037;
    }
</style>
