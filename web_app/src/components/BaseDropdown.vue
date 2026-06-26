<template>
    <q-btn-dropdown class="dora-dropdown-btn" no-caps>
        <template v-if="$slots.label" #label>
            <slot name="label" />
        </template>
        <slot />
    </q-btn-dropdown>
</template>

<script setup lang="ts">
    /*
     * Thin wrapper around q-btn-dropdown so menu-style triggers share
     * the app's no-caps default and present a single place to evolve the
     * dropdown chrome. All other attrs (flat/outline/dense/disable/icon
     * /label/class) and slots pass through as normal.
     */
</script>
