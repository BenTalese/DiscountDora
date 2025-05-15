<template>
    <q-img
        class="dora-woolworthsLogo"
        src="../../src/assets/woolworths-logo.webp"
        :style="`width: ${width}px;`"
    />
</template>

<script lang="ts" setup>
    interface IWoolworthsLogoProps {
        /**
         * Sets the width of the logo in pixels.
         */
        width?: number | undefined;
    }

    withDefaults(defineProps<IWoolworthsLogoProps>(), {
        width: 32
    });
</script>

<style scoped>
    .dora-woolworthsLogo {
        width: 32px;
    }
</style>
