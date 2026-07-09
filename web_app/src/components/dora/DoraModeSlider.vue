<template>
    <div
        class="dora-mode-slider"
        :class="{
            'dora-mode-slider--ai': modelValue,
            'dora-mode-slider--basic': !modelValue,
            'dora-mode-slider--disabled': disabled,
        }"
        role="switch"
        :aria-checked="modelValue"
        :aria-disabled="disabled"
        :tabindex="disabled ? -1 : 0"
        @click="onToggle"
        @keydown.space.prevent="onToggle"
        @keydown.enter.prevent="onToggle"
    >
        <span class="dora-mode-slider__label dora-mode-slider__label--basic">
            <q-icon :name="ICONS.chat_bubble_outline" size="12px" />
            Basic
        </span>
        <span class="dora-mode-slider__label dora-mode-slider__label--ai">
            <q-icon :name="ICONS.auto_awesome" size="12px" />
            AI
        </span>
        <span class="dora-mode-slider__knob" aria-hidden="true"></span>
        <q-tooltip v-if="tooltip" :delay="300">{{ tooltip }}</q-tooltip>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        disabled?: boolean;
        disabledReason?: string;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
    }>();

    const tooltip = computed(() => {
        if (props.disabled) return props.disabledReason ?? '';
        return props.modelValue
            ? 'AI mode on — tap to switch to Basic.'
            : 'Basic mode on — tap to switch to AI.';
    });

    function onToggle() {
        if (props.disabled) return;
        emit('update:modelValue', !props.modelValue);
    }
</script>

<style lang="scss" scoped>
    // Two-position pill. The knob is a skewed thick block that slides
    // between the Basic and AI halves; the active side glows.
    .dora-mode-slider {
        position: relative;
        display: inline-flex;
        align-items: stretch;
        height: 24px;
        min-width: 96px;
        border-radius: 999px;
        background: var(--surface-sunken, rgba(0, 0, 0, 0.06));
        border: 1px solid color-mix(in srgb, var(--brand-primary) 20%, transparent);
        cursor: pointer;
        user-select: none;
        overflow: hidden;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: border-color 200ms ease, box-shadow 200ms ease;
    }
    .dora-mode-slider:focus-visible {
        outline: 2px solid var(--brand-accent);
        outline-offset: 2px;
    }
    .dora-mode-slider--disabled {
        cursor: not-allowed;
        opacity: 0.55;
    }

    .dora-mode-slider__label {
        position: relative;
        z-index: 2;
        flex: 1 1 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        padding: 0 10px;
        color: var(--text-secondary);
        transition: color 220ms ease;
    }
    .dora-mode-slider--basic .dora-mode-slider__label--basic,
    .dora-mode-slider--ai .dora-mode-slider__label--ai {
        color: var(--text-on-primary, #fff);
    }

    // Sliding knob. Skewed for the "slanted thick" feel, glow on the
    // active side. Sits behind the labels via z-index.
    .dora-mode-slider__knob {
        position: absolute;
        top: 2px;
        bottom: 2px;
        left: 2px;
        width: calc(50% - 2px);
        border-radius: 999px;
        background: linear-gradient(
            120deg,
            var(--brand-primary),
            color-mix(in srgb, var(--brand-primary) 70%, var(--brand-accent))
        );
        transform: skewX(-12deg);
        box-shadow:
            0 0 12px color-mix(in srgb, var(--brand-primary) 55%, transparent),
            0 1px 2px rgba(0, 0, 0, 0.15);
        transition:
            transform 260ms cubic-bezier(0.4, 0.1, 0.2, 1.2),
            box-shadow 260ms ease,
            background 260ms ease;
        z-index: 1;
    }
    // Basic side: knob sits on the left (skew keeps -12deg baseline).
    .dora-mode-slider--basic .dora-mode-slider__knob {
        transform: translateX(0) skewX(-12deg);
        background: linear-gradient(
            120deg,
            color-mix(in srgb, var(--text-secondary) 45%, var(--surface-component)),
            color-mix(in srgb, var(--text-secondary) 30%, var(--surface-component))
        );
        box-shadow:
            0 0 8px color-mix(in srgb, var(--text-secondary) 25%, transparent),
            0 1px 2px rgba(0, 0, 0, 0.12);
    }
    // AI side: knob slides to the right, brand-primary glow returns.
    .dora-mode-slider--ai .dora-mode-slider__knob {
        transform: translateX(100%) skewX(-12deg);
    }
</style>
