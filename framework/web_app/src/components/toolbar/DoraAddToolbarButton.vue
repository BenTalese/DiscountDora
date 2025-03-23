<template>
    <DoraToobarButton
        back-colour="positive"
        icon="add"
        icon-colour="blue-grey-10"
        @click="handleClick"
    />

    <!-- TODO: Below is alternate styling idea -->
    <!-- <DoraToobarButton
        back-colour="secondary"
        icon="add"
        icon-colour="green"
        @click="handleClick"
    /> -->
</template>

<script lang="ts" setup>
    //#region Imports
    import DoraToobarButton from './DoraToolbarButton.vue';
    //#endregion Imports

    //#region Props and Events
    const props = defineProps({
        onClick: { type: Function, required: true }
    });
    //#endregion Props and Events

    //#region Methods
    const handleClick = () => props.onClick();
    //#endregion Methods
</script>
