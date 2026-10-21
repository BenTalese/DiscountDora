<template>
    <q-tooltip :delay="delay" :hide-delay="hideDelay">
        <slot />
    </q-tooltip>
</template>

<script setup lang="ts">
    // R-001 — the single tooltip in the app. Every `<q-tooltip>` call site was
    // swept onto this so the show-delay is set in one place rather than 300-odd.
    //
    // Owner feedback 2026-09-09: *"I don't like how everywhere through the app
    // you immediately see the tooltip on mobile for all UI elements when
    // interacting with them. There should be a delay. Otherwise you see
    // tooltips flashing as you use the app."*
    //
    // Quasar defaults `delay` to 0 and, on mobile, binds show to `touchstart`
    // and hide to `touchend`/`click` — so a plain tap flashed the tooltip up and
    // straight back down on every button in the app. A non-zero delay means the
    // show timer is cleared by `touchend` before it ever fires on a normal tap,
    // while a deliberate long-press still surfaces the label. The same value
    // doubles as the standard hover dwell on desktop, so one number covers both
    // pointers and there is no `pointer: coarse` split to keep in sync.
    withDefaults(
        defineProps<{
            delay?: number;
            hideDelay?: number;
        }>(),
        {
            delay: 500,
            hideDelay: 0,
        },
    );
</script>
