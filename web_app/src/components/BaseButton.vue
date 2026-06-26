<template>
    <q-btn
        v-bind="qBtnAttrs"
        :class="['dora-btn', `dora-btn--${variant}`, { 'dora-btn--attention': attention }]"
        :icon="icon"
        :label="label"
        :loading="loading"
        :disable="disable"
        :type="type"
        :to="to"
        :href="href"
        :target="target"
        no-caps
        @click="onClick"
    >
        <slot />
    </q-btn>
</template>

<script setup lang="ts">
    import { computed } from 'vue';

    type Variant =
        | 'primary'
        | 'secondary'
        | 'ghost'
        | 'danger'
        | 'danger-ghost'
        | 'icon'
        | 'danger-icon'
        | 'positive';

    const props = withDefaults(
        defineProps<{
            variant?: Variant;
            attention?: boolean;
            // Optionals that callers commonly bind to a possibly-undefined value
            // are typed `| undefined` so `exactOptionalPropertyTypes` permits it.
            icon?: string | undefined;
            label?: string | undefined;
            loading?: boolean | undefined;
            disable?: boolean | undefined;
            type?: 'button' | 'submit' | 'reset';
            to?: string | object | undefined;
            href?: string | undefined;
            target?: string | undefined;
        }>(),
        {
            variant: 'primary',
            attention: false,
            type: 'button',
        },
    );

    const emit = defineEmits<{
        (e: 'click', event: MouseEvent): void;
    }>();

    // q-btn types its @click as `(evt: Event, go?) => void`; accept `Event` here
    // and narrow to MouseEvent for our typed emit (click events are MouseEvents).
    function onClick(event: Event) {
        emit('click', event as MouseEvent);
    }

    const qBtnAttrs = computed(() => {
        switch (props.variant) {
            case 'primary':
                return { unelevated: true, color: 'primary' };
            case 'secondary':
                return { outline: true, color: 'primary' };
            case 'ghost':
                return { flat: true };
            case 'danger':
                return { unelevated: true, color: 'negative' };
            case 'danger-ghost':
                return { flat: true, color: 'negative' };
            case 'icon':
                return { flat: true, round: true, dense: true };
            case 'danger-icon':
                return { flat: true, round: true, dense: true, color: 'negative' };
            case 'positive':
                return { unelevated: true, color: 'positive' };
            default:
                return { unelevated: true, color: 'primary' };
        }
    });
</script>

<style scoped lang="scss">
    .dora-btn {
        /* Fixed height for toolbar alignment. Icon variant is square. */
        min-height: 36px;
        border-radius: var(--radius-md);
        font-weight: 500;
        letter-spacing: 0.01em;
        transition:
            box-shadow var(--motion-normal, 200ms) ease,
            background-color var(--motion-normal, 200ms) ease;
    }
    .dora-btn--icon,
    .dora-btn--danger-icon {
        min-height: 36px;
        min-width: 36px;
        border-radius: var(--radius-full);
    }
    .dora-btn--ghost {
        color: var(--text-primary);
    }
    /* Attention modifier — pulsing accent glow around the button to draw
       the eye. Used for one-off CTAs (stocktake glow, etc.). The
       animation pauses for users with reduced-motion enabled. */
    .dora-btn--attention {
        animation: dora-btn-attention-pulse 2s ease-in-out infinite;
        border-color: var(--brand-primary) !important;
    }
    @keyframes dora-btn-attention-pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand-accent) 55%, transparent);
        }
        50% {
            box-shadow: 0 0 0 8px color-mix(in srgb, var(--brand-accent) 0%, transparent);
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .dora-btn--attention {
            animation: none;
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-accent) 35%, transparent);
        }
    }
</style>
