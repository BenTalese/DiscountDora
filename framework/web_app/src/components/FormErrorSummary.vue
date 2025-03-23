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
    defineProps<{
        errorMessage?: string | undefined;
    }>();
</script>
