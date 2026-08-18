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

<style scoped lang="scss">
    /*
     * Active-segment ink (D-002). `toggle-color="primary"` makes Quasar emit
     * its `.text-primary` utility on the selected button — and that utility
     * carries `!important`, so it beat every attempt to set readable ink from
     * a call site. In `flat` mode, where the caller paints its own brand-
     * primary fill, the result was primary-on-primary: measured at
     * rgb(53,151,102) text on rgb(53,151,102) background in pesto-dark — a
     * 1:1 ratio, i.e. an invisible label (reported 2026-08-18 on the cookbook
     * Ingredients filter's sort toggle).
     *
     * `--text-on-primary` is the token that exists for exactly this job, and
     * every theme defines it against its own brand-primary. Matching Quasar's
     * `!important` is the only thing that beats `!important` — specificity
     * alone can't — hence the flag here rather than a deeper selector.
     */
    .dora-segmented-btn :deep(.q-btn[aria-pressed='true']) {
        color: var(--text-on-primary) !important;
    }
</style>
