<template>
    <q-btn-toggle
        class="dora-segmented-btn"
        :class="{ 'dora-segmented-btn--pill': pill }"
        :rounded="pill"
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
    withDefaults(
        defineProps<{
            modelValue: T;
            options: {
                label?: string;
                icon?: string;
                value: T;
                [k: string]: unknown;
            }[];
            /**
             * Pill shape: the group is a rounded track and the active segment
             * is a rounded fill inside it, instead of the default squared-off
             * block. Opt-in per call site rather than the app-wide default —
             * the owner asked for it on the recipe method's step-style switch
             * (2026-08-31: *"I prefer rounded pill style buttons here. The
             * hard squarish look it currently has is not so nice looking"*),
             * and the eight other segmented controls weren't part of that
             * call. It stays one component so the two shapes can't drift
             * (D-015).
             */
            pill?: boolean;
        }>(),
        { pill: false },
    );
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

    /*
     * Pill variant. `rounded` on QBtnToggle rounds the *group's* outer ends;
     * the segments inside stay square, so the selected one reads as a block
     * clipped by a curve. Rounding each segment to the pill radius makes the
     * active fill a pill sitting in a pill-shaped track, which is the shape
     * the owner asked for.
     *
     * The track needs its own outline for the unselected segments to sit
     * *in* something — without it a pill-shaped fill floats on the page with
     * nothing to be a segment of.
     */
    .dora-segmented-btn--pill {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-pill);
        background: var(--surface-sunken);
        padding: 2px;
    }
    .dora-segmented-btn--pill :deep(.q-btn) {
        border-radius: var(--radius-pill);
    }
    /* Quasar draws the inter-segment divider as a right border on every button
       but the last. Between two pills it reads as a stray tick. */
    .dora-segmented-btn--pill :deep(.q-btn::before),
    .dora-segmented-btn--pill :deep(.q-btn-group > .q-btn:not(:last-child)) {
        border-right: 0;
    }
</style>
