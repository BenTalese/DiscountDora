<template>
    <div
        class="dora-mode-slider"
        :class="{
            'dora-mode-slider--ai': modelValue,
            'dora-mode-slider--basic': !modelValue,
            'dora-mode-slider--disabled': disabled,
            'dora-mode-slider--actionable': disabled && disabledIsActionable,
        }"
        role="switch"
        :aria-checked="modelValue"
        :aria-disabled="disabled"
        :tabindex="0"
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
    // D-016 carve-out: the rule says a disabled control is "not focusable +
    // visibly inert". This one carries `aria-disabled` rather than native
    // disabled semantics precisely so it stays focusable and keeps a handler —
    // the ARIA-sanctioned shape for a control that can't do its own job but
    // can take you to where you fix that. It stays visibly dimmed either way.
    // `disabledIsActionable` gates the behaviour; without it the control is
    // inert as before.
    //
    // D-019 note: `togglingMode` (a transient flag) also feeds `disabled` from
    // the caller, but the rule's focus-loss harm can't bite here — tabindex is
    // unconditionally 0, so an in-flight PATCH never blurs the control the
    // user is standing on.
    //
    // NB: this comment lives here rather than above the template's root
    // element on purpose — a leading template comment makes the SFC
    // multi-root, which breaks `wrapper.classes()` / `.trigger()` in the spec.
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        disabled?: boolean;
        disabledReason?: string;
        // When true, activating the slider while `disabled` emits
        // `disabled-activate` instead of doing nothing — the caller routes
        // the user somewhere they can fix the reason it's disabled.
        disabledIsActionable?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'disabled-activate'): void;
    }>();

    const tooltip = computed(() => {
        if (props.disabled) {
            const reason = props.disabledReason ?? '';
            // A hover-only explanation is invisible on touch, so when the
            // disabled state is actionable the control itself is the
            // affordance and the tooltip is just extra detail for pointers.
            if (props.disabledIsActionable) {
                return reason ? `${reason} Tap to open Settings.` : 'Tap to set AI mode up in Settings.';
            }
            return reason;
        }
        return props.modelValue
            ? 'AI mode on — tap to switch to Basic.'
            : 'Basic mode on — tap to switch to AI.';
    });

    function onToggle() {
        if (props.disabled) {
            if (props.disabledIsActionable) emit('disabled-activate');
            return;
        }
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
    // Actionable-disabled: still dimmed (AI isn't on) but it *does* something
    // when tapped, so it must not advertise itself as inert.
    .dora-mode-slider--disabled.dora-mode-slider--actionable {
        cursor: pointer;
        opacity: 0.7;
        border-style: dashed;
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
