<template>
    <!-- DR-15 / D-010: a filter chip is one of the four high-frequency
         gestures. `dora-press` answers the touch itself; the bump fires when
         the chip's *state* flips, which is the bit that matters on a filter bar
         where several chips look similar and only the tone tells them apart.
         Both ride motion.scss tokens, so reduced-motion flattens them. -->
    <q-chip
        clickable
        outline
        :class="['dora-press', toggleFeedback]"
        :selected="modelValue"
        :style="modelValue ? { color: activeToneColour } : undefined"
        @click="emit('update:modelValue', !modelValue)"
    >
        <q-icon v-if="icon" :name="icon" size="14px" class="q-mr-xs" />
        <slot />
    </q-chip>
</template>

<script setup lang="ts">
    import { useMicroFeedback } from 'src/composables/useMicroFeedback';
    import { computed } from 'vue';

    type ActiveTone =
        | 'primary'
        | 'secondary'
        | 'positive'
        | 'negative'
        | 'warning';

    const props = defineProps<{
        modelValue: boolean;
        icon?: string;
        activeColor?: ActiveTone;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
    }>();

    /* The active tone resolves to a theme token here rather than riding
       Quasar's `color` prop. An outline chip paints its text AND its
       border in `currentColor` (`.q-chip--outline { border: 1px solid
       currentColor }`), and Quasar's `text-<colour>` class maps straight
       to `--q-<colour>` — which for `secondary` is the *surface-grade*
       brand secondary. In the dark themes that colour IS the toolbar
       background, so the Essential / Open chips read as near-invisible
       when active (2026-08-16 feedback). Indicator-grade secondary lives
       in its own token; the rest map to the semantics unchanged. */
    const TONE_COLOURS: Record<ActiveTone, string> = {
        primary: 'var(--q-primary)',
        secondary: 'var(--brand-secondary-strong)',
        positive: 'var(--q-positive)',
        negative: 'var(--q-negative)',
        warning: 'var(--q-warning)',
    };

    const activeToneColour = computed(
        () => TONE_COLOURS[props.activeColor ?? 'primary'],
    );

    const toggleFeedback = useMicroFeedback(() => props.modelValue, 'bump');
</script>
