<template>
    <!--
        Shared search / filter text box (R-001). Every "type to narrow a list"
        input in the app is this control: dense + outlined + clearable, with a
        leading search icon.

        It exists for one load-bearing reason beyond the duplication: Quasar's
        `clearable` X emits **null**, not an empty string. Four call sites held
        a `ref('')`, fed it to `clearable`, and then called `.trim()` on the
        result — so pressing X threw inside a computed and took the page down
        (reported 2026-08-18 on the cookbook's Ingredients filter). `clear-value`
        pins the cleared value to `''` so the model never leaves string-land,
        and the typed emit below means a caller *can't* reintroduce the null.
        Fixing it here rather than with a `?? ''` at each read means the next
        search box added to the app gets the fix for free.
    -->
    <q-input
        :model-value="modelValue"
        dense
        outlined
        clearable
        clear-value=""
        :label="label"
        :placeholder="placeholder"
        :debounce="debounce"
        :autofocus="autofocus"
        @update:model-value="onUpdate"
    >
        <template #prepend>
            <q-icon :name="ICONS.search" :size="iconSize" />
        </template>
    </q-input>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';

    withDefaults(
        defineProps<{
            modelValue: string;
            label?: string;
            placeholder?: string;
            /** ms; matches the call site's list-filtering cost. */
            debounce?: number | string;
            autofocus?: boolean;
            iconSize?: string;
        }>(),
        { debounce: 100, autofocus: false, iconSize: '18px' },
    );

    const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>();

    // Belt and braces on top of `clear-value`: Quasar types the payload as
    // `string | number | null`, so normalise before it reaches the caller's
    // `string` model rather than trusting the prop alone.
    function onUpdate(value: string | number | null) {
        emit('update:modelValue', value === null ? '' : String(value));
    }
</script>
