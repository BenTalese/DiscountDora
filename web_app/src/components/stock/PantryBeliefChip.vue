<template>
    <!--
        P8-07 — the Zero-Input Pantry belief chip. ADDITIVE: it sits beside
        the recorded level, never replaces it (the recorded level stays the
        source of truth for shopping + cooking). Shows what Dora infers, its
        confidence, and — via the tooltip — the plain-English reason
        (Charter 3/7: honest + explainable). Hidden unless the belief is a
        genuine inference worth surfacing.
    -->
    <span
        v-if="belief && belief.is_inferred"
        class="belief-chip"
        :class="[`belief-chip--${belief.believed_band}`, { 'belief-chip--differs': belief.differs_from_recorded }]"
    >
        <q-icon :name="ICONS.auto_awesome" size="13px" class="belief-chip__icon" />
        <span class="belief-chip__dot" :class="`belief-chip__dot--${belief.believed_band}`" />
        <span class="belief-chip__text">Dora: {{ bandLabel }}</span>
        <span class="belief-chip__conf">· {{ belief.confidence_band }}</span>
        <q-tooltip max-width="260px" anchor="top middle" self="bottom middle">
            {{ belief.reason }}
            <template v-if="belief.differs_from_recorded">
                <br />
                <span class="belief-chip__tip-note">Differs from your recorded level — a quick check helps.</span>
            </template>
        </q-tooltip>
    </span>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import type { PantryBelief } from 'src/models/pantryBelief';

    const props = defineProps<{
        belief: PantryBelief | null;
    }>();

    // The chip only surfaces genuine inferences (is_inferred) — a belief that
    // merely echoes a freshly-confirmed level carries no new information, so
    // the row stays uncluttered (Charter 10). That gate lives in the template
    // `v-if` so vue-tsc narrows `belief` to non-null for the bindings.

    const BAND_LABEL: Record<string, string> = {
        out: '~Out',
        low: '~Low',
        stocked: 'Stocked',
    };
    const bandLabel = computed(() =>
        props.belief ? (BAND_LABEL[props.belief.believed_band] ?? props.belief.believed_band) : '',
    );
</script>

<style scoped>
    /* Compact, muted by default — an ambient hint, not a loud badge. All
       colour rides semantic tokens (R-002). */
    .belief-chip {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 1px 7px 1px 5px;
        border-radius: 10px;
        font-size: 0.72rem;
        line-height: 1.4;
        color: var(--text-secondary);
        background: var(--surface-sunken);
        border: 1px solid transparent;
        white-space: nowrap;
        cursor: default;
    }
    .belief-chip__icon {
        color: var(--brand-primary);
        opacity: 0.85;
    }
    .belief-chip__dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .belief-chip__dot--stocked { background: var(--semantic-positive); }
    .belief-chip__dot--low { background: var(--semantic-warning); }
    .belief-chip__dot--out { background: var(--semantic-negative); }
    .belief-chip__conf {
        color: var(--text-muted, var(--text-secondary));
        opacity: 0.8;
    }
    /* When Dora's inference disagrees with the recorded level, outline the
       chip in a warning tint so it reads as "worth a look". */
    .belief-chip--differs {
        border-color: var(--semantic-warning);
        background: var(--semantic-warning-soft);
    }
    .belief-chip__tip-note {
        opacity: 0.85;
        font-style: italic;
    }
</style>
