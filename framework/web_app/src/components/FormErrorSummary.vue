<template>
    <p
        v-if="errorMessage"
        class="text-negative q-pa-sm bg-red-1 rounded-borders shadow-2"
    >
        <q-icon
            name="error"
            class="q-mr-sm"
        />
        {{ errorMessage }}
    </p>
</template>

<script setup lang="ts">
    //#region Props and Events
    defineProps<{
        errorMessage?: string | undefined;
    }>();
    //#endregion Props and Events
</script>
