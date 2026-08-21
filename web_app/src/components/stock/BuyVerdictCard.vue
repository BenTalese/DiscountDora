<template>
    <!-- Feedback 2026-08-16: collapsed by default. The header alone answers
         the question ("Worth buying now") with the one action worth taking;
         the reasons, the wait hint and the data-provenance footer are the
         "why", and only open when asked for.
         Feedback 2026-08-21: this used to be a card-inside-a-card — an
         elevated shell wrapping a tinted header block. It now wears the same
         single-surface shape as `PantryBeliefCard` (the "Dora thinks" card it
         sits under): the verdict tint lives on the card itself, the summary
         line is the disclosure, and the one-tap action is an icon-only button
         sitting to the RIGHT of the caret, exactly where the belief card's
         chevron ends. Two cards, one idiom. -->
    <div v-if="verdict" :class="['dora-buy-verdict-card', `is-${verdict.verdict}`]">
        <div class="dora-buy-verdict-card__header">
            <button
                type="button"
                class="dora-buy-verdict-card__summary"
                :aria-expanded="expanded"
                @click="expanded = !expanded"
            >
                <!-- Always the dollar glyph. A per-verdict icon meant `unsure`
                     drew a question-mark bubble, which read as an info chip
                     rather than as "this card is about money". -->
                <q-icon
                    :name="ICONS.currency_usd"
                    size="18px"
                    class="dora-buy-verdict-card__icon"
                />
                <span class="dora-buy-verdict-card__headline">{{ headline }}</span>
                <q-space />
                <q-icon
                    :name="expanded ? ICONS.collapse : ICONS.expand"
                    size="18px"
                    class="dora-text-muted"
                />
            </button>
            <!-- Icon-only, and outside the disclosure button so a tap on the
                 action can't toggle the card. The name survives as the tooltip
                 + aria-label (D-rule: icon-only controls are still named). -->
            <BaseButton
                v-if="verdict.one_tap_action.kind !== 'none'"
                variant="primary"
                dense
                :icon="actionIcon"
                :aria-label="actionLabel"
                @click="onActionClick"
            >
                <q-tooltip>{{ actionLabel }}</q-tooltip>
            </BaseButton>
        </div>

        <div v-if="expanded" class="dora-buy-verdict-card__body">
        <div class="text-caption dora-text-muted">
            {{ verdict.confidence }} confidence
        </div>

        <!-- time-boxed hint on `wait` verdicts. Server only sends
             this when a confident cycle was detected; the reason string
             is authoritative, the friendly "in ~N days" is a client-side
             formatting nicety. -->
        <div v-if="verdict.wait_hint" class="dora-buy-verdict-card__wait-hint">
            <div class="row items-center q-mb-xs">
                <q-icon
                    :name="ICONS.event_repeat ?? 'mdi-calendar-refresh'"
                    size="18px"
                    class="q-mr-sm"
                />
                <strong>{{ waitHintTargetLabel }}</strong>
            </div>
            <div class="text-caption dora-text-muted" style="margin-left: 26px">
                {{ verdict.wait_hint.reason }}
            </div>
        </div>

        <ul v-if="verdict.reasons.length > 0" class="dora-buy-verdict-card__reasons">
            <li v-for="(reason, i) in verdict.reasons" :key="i">
                <div class="row items-center">
                    <q-icon
                        :name="axisIcon(reason.axis)"
                        size="18px"
                        class="q-mr-sm dora-text-muted"
                    />
                    <strong>{{ reason.label }}</strong>
                </div>
                <div
                    v-if="reason.detail"
                    class="text-caption dora-text-muted"
                    style="margin-left: 26px"
                >
                    {{ reason.detail }}
                </div>
            </li>
        </ul>

        <div class="text-caption dora-text-muted dora-buy-verdict-card__footer">
            Based on
            {{ verdict.data_used.price_samples }} price sample{{
                verdict.data_used.price_samples === 1 ? '' : 's'
            }}
            <!-- Feedback 2026-08-17: the "across N shopping trips" clause is
                 gone. It read as the denominator of the price samples, which it
                 isn't — prices arrive from imports, "your prices" entries and
                 manual edits, none of which are trips — so it implied a
                 relationship between the two numbers that doesn't exist.
                 `purchases_last_12mo` is still on the DTO and still feeds the
                 verdict's own reasoning server-side; it just isn't a footnote
                 the reader can do anything with. -->
            <template v-if="verdict.data_used.waste_events_last_12mo > 0">
                · {{ verdict.data_used.waste_events_last_12mo }} waste event{{
                    verdict.data_used.waste_events_last_12mo === 1 ? '' : 's'
                }}
            </template>
            (last 12 months).
        </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import type { BuyVerdict } from 'src/services/api/buyVerdictApiService';
    import { ICONS } from 'src/style/icons';
    import { computed, ref } from 'vue';

    const props = defineProps<{
        verdict: BuyVerdict | null;
    }>();

    const expanded = ref(false);

    const emit = defineEmits<{
        (e: 'action', kind: BuyVerdict['one_tap_action']['kind']): void;
    }>();

    const actionLabel = computed(() =>
        props.verdict?.one_tap_action.kind === 'add_to_list'
            ? 'Add to list'
            : (props.verdict?.one_tap_action.label ?? ''),
    );

    // The action is icon-only now, so every kind needs a glyph. `add_to_list`
    // keeps the cart the overview row uses, so the same action reads the same
    // in both places.
    const ACTION_ICONS: Record<BuyVerdict['one_tap_action']['kind'], string> = {
        add_to_list: ICONS.add_shopping_cart,
        mark_stocked: ICONS.inventory_2,
        remove_from_list: ICONS.playlist_remove,
        skip: ICONS.close,
        none: ICONS.check,
    };
    const actionIcon = computed(
        () => ACTION_ICONS[props.verdict?.one_tap_action.kind ?? 'none'],
    );

    const headline = computed(() => {
        if (!props.verdict) return '';
        if (props.verdict.verdict === 'buy') return 'Worth buying now';
        if (props.verdict.verdict === 'wait') return 'Might be worth waiting';
        if (props.verdict.verdict === 'skip') return 'Probably skip';
        return 'No strong buy signal';
    });

    // Friendly relative-date headline for the P8-06 wait-hint. The full
    // "why" string from the server sits underneath as the sub-caption.
    const waitHintTargetLabel = computed(() => {
        const hint = props.verdict?.wait_hint;
        if (!hint) return '';
        const target = new Date(`${hint.until}T00:00:00`);
        if (Number.isNaN(target.getTime())) return '';
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const days = Math.round((target.getTime() - today.getTime()) / 86_400_000);
        const dateLabel = formatLocaleDate(target, {
            month: 'short', day: 'numeric',
        });
        if (days <= 0) return `Expect a dip around ${dateLabel}`;
        if (days === 1) return `Expect a dip tomorrow (${dateLabel})`;
        if (days <= 14) return `Expect a dip in ~${days} days (${dateLabel})`;
        return `Expect a dip around ${dateLabel}`;
    });

    function axisIcon(axis: 'price' | 'need' | 'waste'): string {
        if (axis === 'price') return ICONS.price_check ?? 'mdi-cash-check';
        if (axis === 'need') return ICONS.inventory_2 ?? 'mdi-package-variant-closed';
        return ICONS.delete_outline ?? 'mdi-delete-outline';
    }

    function onActionClick(): void {
        if (props.verdict) emit('action', props.verdict.one_tap_action.kind);
    }
</script>

<style scoped>
    /* Deliberately the same geometry + token set as `PantryBeliefCard`:
       one surface, 8px radius, 10px/12px padding, tint in the fill and the
       border only (never in the text ink — full-strength semantic ink on a
       soft fill is the D-002 contrast fail). */
    .dora-buy-verdict-card {
        border-radius: 8px;
        padding: 10px 12px;
        background: var(--surface-sunken);
        border: 1px solid var(--border-strong);
        color: var(--text-primary);
    }
    .dora-buy-verdict-card.is-buy {
        background: var(--semantic-positive-soft);
        border-color: var(--semantic-positive);
    }
    .dora-buy-verdict-card.is-wait {
        background: var(--semantic-warning-soft);
        border-color: var(--semantic-warning);
    }
    .dora-buy-verdict-card.is-skip {
        background: var(--semantic-negative-soft);
        border-color: var(--semantic-negative);
    }
    .dora-buy-verdict-card__header {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .dora-buy-verdict-card__body {
        margin-top: 6px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        font-size: 0.8125rem;
        line-height: 1.45;
    }
    .dora-buy-verdict-card__headline {
        font-weight: 600;
        font-size: 1rem;
    }
    /* The whole summary line is the disclosure control, so it has to be a
       real button: keyboard-reachable, and wide enough that a thumb lands on
       it (D-004). Chrome is stripped back to the surrounding card. */
    .dora-buy-verdict-card__summary {
        display: flex;
        align-items: center;
        gap: 6px;
        /* Takes the row; the action button keeps its intrinsic width. */
        flex: 1 1 auto;
        min-width: 0;
        min-height: 44px;
        padding: 0;
        border: none;
        background: none;
        font: inherit;
        color: inherit;
        text-align: left;
        cursor: pointer;
    }
    .dora-buy-verdict-card__summary:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
        border-radius: 4px;
    }
    .dora-buy-verdict-card__icon {
        flex-shrink: 0;
        color: var(--text-secondary);
    }
    /* Graphical (non-text) glyph, so the semantic hue is legible here in the
       same way the belief card tints its own icon. */
    .dora-buy-verdict-card.is-buy  .dora-buy-verdict-card__icon { color: var(--semantic-positive); }
    .dora-buy-verdict-card.is-wait .dora-buy-verdict-card__icon { color: var(--semantic-warning); }
    .dora-buy-verdict-card.is-skip .dora-buy-verdict-card__icon { color: var(--semantic-negative); }

    /* P8-06 — the wait-hint block sits between header and reasons. It used
       to carry its own warm fill, which on a now-already-warm `wait` card was
       both invisible and one more nested box — the exact "card inside a card"
       the 2026-08-21 feedback called out. A rule down the left edge marks it
       out instead. */
    .dora-buy-verdict-card__wait-hint {
        padding-left: 8px;
        border-left: 3px solid var(--semantic-warning);
    }

    .dora-buy-verdict-card__reasons {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-buy-verdict-card__footer {
        border-top: 1px solid var(--surface-sunken);
        padding-top: 8px;
    }
</style>
