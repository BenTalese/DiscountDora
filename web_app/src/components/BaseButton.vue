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
        | 'filled-icon'
        | 'positive'
        /* Small secondary actions that sit inside a control group rather than
         * at the bottom of a form: "Select all" / "Select missing" in the
         * ingredient picker, the little helper actions in Settings. Owner
         * feedback 2026-08-19: "select all / select missing buttons don't have
         * the appearance of buttons. I've seen a few of these smaller UI
         * elements pop up (e.g. in settings). Might be good to componentise to
         * get a consistent look." They were `ghost` + `dense` + `size="sm"`,
         * i.e. bare tinted text — nothing said "target". `subtle` keeps them
         * visually quieter than `secondary` while still being an obviously
         * pressable, bordered, filled block. */
        | 'subtle';

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
            // Optional Quasar palette override. When set, replaces the variant's
            // default color — lets callers do dynamic coloring on icon variants
            // (e.g. RecipeCard chef-hat toggling primary/warning) without
            // reaching for raw q-btn.
            color?: string | undefined;
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
        const base = (() => {
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
                case 'filled-icon':
                    return { unelevated: true, round: true, dense: true, color: 'primary' };
                case 'positive':
                    return { unelevated: true, color: 'positive' };
                // No Quasar `color`: the fill and ink are painted from theme
                // tokens below, because there is no palette entry for
                // "sunken surface" (R-002 — tokens, not hardcoded colours).
                case 'subtle':
                    return { unelevated: true };
                default:
                    return { unelevated: true, color: 'primary' };
            }
        })();
        return props.color !== undefined ? { ...base, color: props.color } : base;
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
    .dora-btn--danger-icon,
    .dora-btn--filled-icon {
        min-height: 36px;
        min-width: 36px;
        border-radius: var(--radius-full);
    }
    .dora-btn--ghost {
        color: var(--text-primary);
    }
    /* Reads as a button at a glance — a fill, a border and a radius — without
       competing with the dialog's real primary action. */
    .dora-btn--subtle {
        background: var(--surface-sunken);
        border: 1px solid var(--border-default);
        color: var(--text-primary);
        font-size: 0.8125rem;
        padding: 0 var(--space-3);
        /* Deliberately shorter than the 44px B1/D-004 floor: it matches the
           36px every other `.dora-btn` runs at, and pinning one variant taller
           than its siblings would look like a mistake. The app-wide 44px-on-
           touch gap is logged as its own follow-up rather than fixed by
           inventing an exception here. */
        min-height: 36px;
    }
    .dora-btn--subtle:hover {
        background: color-mix(in srgb, var(--brand-primary) 10%, var(--surface-sunken));
        border-color: var(--border-strong);
    }
    /* DR-3 / FU-578 #53 — flat/outline variants hard-set their text to a
       full-strength colour, so Quasar's opacity-only disabled dim left
       them reading near-white on the bulk-bar (indistinguishable from
       enabled). Pin a muted colour on the disabled state so the "not
       available yet" affordance is unmistakable. Filled variants
       (primary/danger/positive) keep white-on-fill + the opacity dim —
       greying their label would fight the fill — so they're excluded. */
    .dora-btn--ghost.disabled,
    .dora-btn--subtle.disabled,
    .dora-btn--secondary.disabled,
    .dora-btn--icon.disabled,
    .dora-btn--danger-ghost.disabled,
    .dora-btn--danger-icon.disabled {
        color: var(--text-muted);
    }
    /* Attention modifier — pulsing accent glow around the button to draw
       the eye. Used for one-off CTAs (stocktake glow, etc.). The button
       fill tint pulses in sync with the surrounding glow so the whole
       control breathes, not just the ring. The animation pauses for users
       with reduced-motion enabled.

       The fill is animated on the ::before layer, NOT the button element:
       Quasar forces `.q-btn--outline { background: transparent !important }`,
       and `!important` is *ignored inside @keyframes*, so a fill on the
       element can never paint on an outline button (the Stocktake button is
       `secondary` = outline). Quasar's `.q-btn:before` is an inset,
       radius-inheriting layer that paints behind the label and carries no
       `!important` background, so the tint shows there for every variant. */
    .dora-btn--attention {
        animation: dora-btn-attention-glow 2s ease-in-out infinite;
    }
    .dora-btn--attention::before {
        animation: dora-btn-attention-fill 2s ease-in-out infinite;
    }
    @keyframes dora-btn-attention-glow {
        0%, 100% {
            box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand-accent) 55%, transparent);
        }
        50% {
            box-shadow: 0 0 0 8px color-mix(in srgb, var(--brand-accent) 0%, transparent);
        }
    }
    @keyframes dora-btn-attention-fill {
        0%, 100% {
            background-color: color-mix(in srgb, var(--brand-accent) 32%, transparent);
        }
        50% {
            background-color: color-mix(in srgb, var(--brand-accent) 0%, transparent);
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .dora-btn--attention {
            animation: none;
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-accent) 35%, transparent);
        }
        .dora-btn--attention::before {
            animation: none;
            background-color: color-mix(in srgb, var(--brand-accent) 22%, transparent);
        }
    }
</style>
