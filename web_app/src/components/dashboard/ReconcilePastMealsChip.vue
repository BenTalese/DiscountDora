<template>
    <!-- FU-317 Chunk 5 — dashboard nudge for the meal-plan reconcile
         queue. Hide-when-empty (R-029): the card doesn't render at all
         when there's nothing to reconcile. The number is the server's
         exact count (via `useReconcileQueue().total`); no client-side
         derivation. -->
    <router-link
        v-if="total > 0"
        to="/meal-plans/reconcile"
        class="reconcile-chip"
        :aria-label="`Reconcile ${total} past meals`"
    >
        <q-icon :name="ICONS.event_note" size="24px" class="reconcile-chip__icon" />
        <div class="reconcile-chip__body">
            <div class="reconcile-chip__title">
                Reconcile {{ total }} past meal{{ total === 1 ? '' : 's' }}
            </div>
            <div class="reconcile-chip__caption">
                A quick pass keeps your pool honest.
            </div>
        </div>
        <q-icon :name="ICONS.chevron_right" size="20px" class="reconcile-chip__arrow" />
    </router-link>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useReconcileQueue } from 'src/composables/useReconcileQueue';

    const { total } = useReconcileQueue();
</script>

<style scoped lang="scss">
    .reconcile-chip {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        background: var(--surface-component);
        /* R-060: was `--border-subtle`, a token that has never been declared —
           so the whole declaration was invalid and this chip rendered with no
           border at all, alone in a grid of bordered cards. A6: a card/panel
           outline is `--border-default`. */
        border: 1px solid var(--border-default);
        /* It sits in the card grid and reads as one of the cards, so it takes
           the card radius, not the control radius (D-017). */
        border-radius: var(--radius-lg);
        color: var(--text-primary);
        text-decoration: none;
        transition: background 120ms ease, border-color 120ms ease;

        &:hover,
        &:focus-visible {
            background: color-mix(in srgb, var(--brand-primary) 6%, var(--surface-component));
            border-color: var(--accent-ink);
        }
    }

    .reconcile-chip__icon {
        /* Decorative leading icon — muted, same call as the card head icons:
           A1 keeps the brand accent for the view's one primary CTA. */
        color: var(--text-secondary);
        flex: 0 0 auto;
    }

    .reconcile-chip__body {
        flex: 1 1 auto;
        min-width: 0;
    }

    .reconcile-chip__title {
        font-weight: 600;
    }

    .reconcile-chip__caption {
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-muted);
    }

    .reconcile-chip__arrow {
        color: var(--text-muted);
        flex: 0 0 auto;
    }
</style>
