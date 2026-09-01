<template>
    <!--
        P8-07 — Dora's inferred pantry belief, as a card.

        `PantryBeliefChip` is the *row* form of this and stays deliberately
        silent when Dora agrees with the recorded level: on a list of 200
        items, "Dora agrees" 200 times is noise.

        The stock-item detail page is the opposite case. The owner asked
        (2026-08-16) to "always show Dora's opinion so we can see the
        reasoning for agreeing with the level" — you came to this page for
        one item, and on one item the agreement *and* its reasoning are the
        point. So this card always renders when a belief exists, collapsed to
        the same pill the row shows, and opens to the full reasoning.
    -->
    <!-- Feedback 2026-08-24: this card's chevron didn't line up in a column
         with the buy-verdict card's directly below it. Both were centred in
         their own row; the difference was structural — this one was an 18px
         glyph flush to the card's padding, that one is centred inside a 44px
         tap target. `CollapsibleCard` now owns that shape for every disclosure
         in the app, so the two chevrons share an x by construction rather than
         by two components happening to agree. -->
    <CollapsibleCard
        v-if="belief"
        :class="['belief-card', `is-${tone}`]"
        header-toggles
        reveals="details"
    >
        <template #header>
            <div class="belief-card__summary">
                <q-icon :name="ICONS.dora_voice" size="18px" class="belief-card__icon" />
                <span class="belief-card__headline">{{ headline }}</span>
            </div>
        </template>

        <div class="belief-card__body">
            <div>{{ belief.reason }}</div>
            <div class="belief-card__meta dora-text-muted">
                Confidence: {{ belief.confidence_band }}
            </div>
            <div class="belief-card__meta dora-text-muted">
                <template v-if="belief.differs_from_recorded">
                    This differs from your recorded level — a quick check helps.
                </template>
                <template v-else>
                    This agrees with your recorded level.
                </template>
            </div>
        </div>
    </CollapsibleCard>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import CollapsibleCard from 'src/components/CollapsibleCard.vue';
    import type { PantryBelief } from 'src/models/pantryBelief';

    const props = defineProps<{
        belief: PantryBelief | null;
    }>();

    // Amber only when Dora disagrees — that's the case worth pulling the eye.
    // Agreement is information, not an alert, so it sits on a neutral surface.
    const tone = computed(() =>
        props.belief?.differs_from_recorded ? 'differs' : 'agrees',
    );

    const BAND_WORD: Record<string, string> = {
        out: 'out',
        low: 'low',
        stocked: 'stocked',
    };
    const headline = computed(() => {
        if (!props.belief) return '';
        const band = BAND_WORD[props.belief.believed_band] ?? props.belief.believed_band;
        return `Dora thinks ${band}`;
    });
</script>

<style scoped>
    /* Same colour reasoning as PantryBeliefChip: the warning tint lives in
       the fill/border and the (graphical, non-text) icon, never in the text
       ink — full-strength warning ink is the D-002 1.98:1 contrast fail. */
    .belief-card {
        border-radius: 8px;
        padding: 10px 12px;
        background: var(--surface-sunken);
        border: 1px solid var(--border-strong);
        color: var(--text-primary);
    }
    .belief-card.is-differs {
        background: var(--semantic-warning-soft);
        border-color: var(--semantic-warning);
    }
    /* The header row, the 44px caret and the focus ring all come from
       `CollapsibleCard` now. What's left here is this card's own content. */
    .belief-card__summary {
        display: flex;
        align-items: center;
        gap: 6px;
        min-width: 0;
        min-height: 44px;
    }
    .belief-card__headline {
        font-weight: 600;
        font-size: 0.875rem;
    }
    .belief-card.is-differs .belief-card__icon {
        color: var(--semantic-warning);
    }
    .belief-card.is-agrees .belief-card__icon {
        color: var(--text-secondary);
    }
    .belief-card__body {
        margin-top: 6px;
        font-size: 0.8125rem;
        line-height: 1.45;
    }
    .belief-card__meta {
        font-size: 0.75rem;
        margin-top: 2px;
    }
</style>
