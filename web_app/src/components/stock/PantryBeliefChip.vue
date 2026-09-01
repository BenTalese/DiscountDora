<template>
    <!--
        P8-07 — the Zero-Input Pantry belief hint. ADDITIVE: it sits beside
        the recorded level, never replaces it (the recorded level stays the
        source of truth for shopping + cooking).

        Design (2026-08-12): the hint surfaces ONLY when Dora's inference
        DISAGREES with the recorded level — the one case that's worth a
        glance. Agreement (confident or not) says nothing new, so it stays
        silent; there's no "Dora agrees" state (anti-creep, Charter 10).
        When it does show it's a soft-amber pill "Dora thinks low/out/stocked"
        with a hunch icon; the band, confidence, and plain-English reason live
        in the tooltip (Charter 3/7: honest + explainable).
    -->
    <span v-if="belief && shouldShow" class="belief-hint">
        <q-icon :name="ICONS.dora_voice" size="14px" class="belief-hint__icon" />
        <span class="belief-hint__text">Dora thinks {{ bandWord }}</span>
        <q-tooltip max-width="260px" anchor="top middle" self="bottom middle">
            {{ belief.reason }}
            <br />
            <span class="belief-hint__tip-conf">Confidence: {{ belief.confidence_band }}</span>
            <br />
            <span class="belief-hint__tip-note">Differs from your recorded level — a quick check helps.</span>
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

    // Show only a genuine inference (is_inferred) that DIFFERS from the recorded
    // level. Everything else — agreement, or a belief that merely echoes a
    // freshly-confirmed level — carries no new information, so the row stays
    // uncluttered.
    const shouldShow = computed(
        () => !!props.belief && props.belief.is_inferred && props.belief.differs_from_recorded,
    );

    const BAND_WORD: Record<string, string> = {
        out: 'out',
        low: 'low',
        stocked: 'stocked',
    };
    const bandWord = computed(() =>
        props.belief ? (BAND_WORD[props.belief.believed_band] ?? props.belief.believed_band) : '',
    );
</script>

<style scoped>
    /* A soft-amber pill — the disagreement is the one case worth pulling the
       eye. Text is --text-primary on the soft fill (NOT full-strength warning
       ink — that's the D-002 1.98:1 contrast fail BuyVerdictBadge already
       corrected); the warning tint lives in the fill, border, and (as a
       graphical, non-text indicator) the hunch icon. All colour rides
       semantic tokens (R-002). */
    .belief-hint {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 1px 7px;
        border-radius: 10px;
        font-size: 0.72rem;
        line-height: 1.4;
        background: var(--semantic-warning-soft);
        border: 1px solid var(--semantic-warning);
        color: var(--text-primary);
        white-space: nowrap;
        cursor: default;
        /* DR-8 (#52): beliefs load async, after the row paints. Fade the pill
           in rather than hard-popping it; the row already reserves the line
           height so this doesn't reflow neighbours. --motion-fast collapses to
           ~0 under prefers-reduced-motion (motion.scss), so this self-respects. */
        animation: belief-hint-in var(--motion-fast) var(--motion-ease);
    }
    @keyframes belief-hint-in {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .belief-hint__icon {
        color: var(--semantic-warning);
    }
    .belief-hint__tip-conf {
        opacity: 0.85;
    }
    .belief-hint__tip-note {
        opacity: 0.85;
        font-style: italic;
    }
</style>
