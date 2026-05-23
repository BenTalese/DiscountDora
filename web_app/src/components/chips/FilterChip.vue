<template>
    <q-chip
        clickable
        outline
        :selected="modelValue"
        :color="modelValue ? activeColor : undefined"
        :text-color="modelValue ? 'white' : undefined"
        @click="emit('update:modelValue', !modelValue)"
    >
        <q-icon v-if="icon" :name="icon" size="14px" class="q-mr-xs" />
        <slot />
    </q-chip>
</template>

<script setup lang="ts">
    defineProps<{
        modelValue: boolean;
        icon?: string;
        activeColor?: string;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
    }>();
</script>
