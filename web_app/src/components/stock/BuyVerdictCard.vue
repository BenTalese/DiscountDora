<template>
    <div v-if="verdict" class="dora-buy-verdict-card">
        <div :class="['dora-buy-verdict-card__header', `is-${verdict.verdict}`]">
            <span :class="['dora-buy-verdict-card__dot', `is-${verdict.verdict}`]" />
            <div class="col">
                <div class="dora-buy-verdict-card__headline">
                    {{ headline }}
                </div>
                <div class="text-caption dora-text-muted">
                    {{ verdict.confidence }} confidence · Personal data only
                </div>
            </div>
            <BaseButton
                v-if="verdict.one_tap_action.kind !== 'none'"
                variant="primary"
                :label="verdict.one_tap_action.label"
                @click="onActionClick"
            />
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
            <template v-if="verdict.data_used.purchases_last_12mo > 0">
                across {{ verdict.data_used.purchases_last_12mo }} shop{{
                    verdict.data_used.purchases_last_12mo === 1 ? '' : 's'
                }}
            </template>
            <template v-if="verdict.data_used.waste_events_last_12mo > 0">
                · {{ verdict.data_used.waste_events_last_12mo }} waste event{{
                    verdict.data_used.waste_events_last_12mo === 1 ? '' : 's'
                }}
            </template>
            (last 12 months).
        </div>
    </div>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import type { BuyVerdict } from 'src/services/api/buyVerdictApiService';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = defineProps<{
        verdict: BuyVerdict | null;
    }>();
    const emit = defineEmits<{
        (e: 'action', kind: BuyVerdict['one_tap_action']['kind']): void;
    }>();

    const headline = computed(() => {
        if (!props.verdict) return '';
        if (props.verdict.verdict === 'buy') return 'Worth buying now';
        if (props.verdict.verdict === 'wait') return 'Might be worth waiting';
        if (props.verdict.verdict === 'skip') return 'Probably skip';
        return 'No strong signal';
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
        const dateLabel = target.toLocaleDateString(undefined, {
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
    .dora-buy-verdict-card {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px;
        background: var(--surface-elevated);
        border: 1px solid var(--surface-sunken);
        border-radius: 8px;
    }
    .dora-buy-verdict-card__header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 6px;
        background: var(--surface-sunken);
    }
    .dora-buy-verdict-card__header.is-buy {
        background: var(--semantic-positive-soft);
    }
    .dora-buy-verdict-card__header.is-wait {
        background: var(--semantic-warning-soft);
    }
    .dora-buy-verdict-card__header.is-skip {
        background: var(--semantic-negative-soft);
    }
    .dora-buy-verdict-card__headline {
        font-weight: 600;
        font-size: 1rem;
    }
    .dora-buy-verdict-card__dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .dora-buy-verdict-card__dot.is-buy    { background: var(--semantic-positive); }
    .dora-buy-verdict-card__dot.is-wait   { background: var(--semantic-warning); }
    .dora-buy-verdict-card__dot.is-skip   { background: var(--semantic-negative); }
    .dora-buy-verdict-card__dot.is-unsure { background: var(--text-muted); }

    /* P8-06 — the wait-hint block sits between header and reasons.
       Warm tint matches the wait-verdict header colour. */
    .dora-buy-verdict-card__wait-hint {
        padding: 10px 12px;
        border-radius: 6px;
        background: var(--semantic-warning-soft);
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
