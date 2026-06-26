<template>
    <q-btn-toggle
        class="dora-segmented-btn"
        :model-value="modelValue"
        :options="options"
        no-caps
        toggle-color="primary"
        @update:model-value="(v: T) => emit('update:modelValue', v)"
    />
</template>

<script setup lang="ts" generic="T">
    /*
     * Thin wrapper around q-btn-toggle so segmented controls share the
     * app's defaults (no-caps + primary active fill) in one place. Pass
     * dense / flat / unelevated / spread / size etc. through as normal
     * attrs — Vue's default inheritAttrs forwards them onto the root.
     */
    defineProps<{
        modelValue: T;
        options: {
            label?: string;
            icon?: string;
            value: T;
            [k: string]: unknown;
        }[];
    }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: T): void }>();
</script>
