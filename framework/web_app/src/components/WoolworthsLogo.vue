<template>
    <q-img
        class="w-px-32"
        src="../../src/assets/woolworths-logo.webp"
        :style="`width: ${width}px;`"
    />
</template>

<script setup lang="ts">

    interface WoolworthsLogoProps {

        /**
         * Sets the width of the logo in pixels.
         */
        width?: number | undefined

    }

    withDefaults(defineProps<WoolworthsLogoProps>(), {
        width: 32
    })

</script>
