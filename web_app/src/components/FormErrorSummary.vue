<template>
    <q-banner
        v-if="message"
        class="bg-red-1 text-red-9 q-mb-md"
        dense
        rounded
        role="alert"
    >
        <template v-slot:avatar>
            <q-icon name="error" color="negative" />
        </template>
        {{ message }}
    </q-banner>
</template>

<script setup lang="ts">
    defineProps<{
        message?: string | null;
    }>();
</script>
