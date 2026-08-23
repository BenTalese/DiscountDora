<template>
    <div class="sl-receipt">
        <!-- Amend is a mode, and a mode you are in must say so. The banner also
             carries the one consequence a user cannot see: correcting a price
             here does NOT re-run the restock. -->
        <q-banner
            v-if="amending"
            class="q-mb-md dora-bg-warning-soft"
            rounded
            dense
        >
            <template #avatar>
                <q-icon :name="ICONS.edit" color="warning" />
            </template>
            <div class="text-body2">
                <strong>Amending this receipt.</strong>
                Price, store and quantity only — your pantry was already
                restocked when you finished, and correcting the record here
                doesn't restock anything again.
            </div>
            <template #action>
                <BaseButton variant="ghost" label="Done" @click="emit('stop-amend')" />
            </template>
        </q-banner>

        <q-card flat bordered class="sl-receipt-card">
            <q-card-section class="row items-center no-wrap q-gutter-x-sm q-pb-sm">
                <q-icon :name="ICONS.receipt_long" size="20px" class="dora-text-secondary" />
                <div class="column" style="min-width: 0">
                    <div class="text-subtitle1 text-weight-medium">
                        {{ boughtLines.length }} item{{ boughtLines.length === 1 ? '' : 's' }} bought
                    </div>
                    <div v-if="completedLabel" class="text-caption dora-text-muted">
                        {{ completedLabel }}
                    </div>
                </div>
                <q-space />
                <div v-if="moneyEnabled" class="column items-end">
                    <div class="text-h5 sl-receipt-total">{{ formatMoney(detail.totals.total_price) }}</div>
                    <div v-if="unpricedCount > 0" class="text-caption dora-text-muted">
                        {{ unpricedCount }} not priced
                    </div>
                </div>
            </q-card-section>

            <q-separator />

            <q-list separator>
                <q-item
                    v-for="line in boughtLines"
                    :key="line.line_id"
                    class="sl-receipt-row"
                >
                    <q-item-section>
                        <q-item-label class="ellipsis">
                            <span v-if="(line.quantity ?? 0) > 1" class="sl-receipt-qty">
                                {{ line.quantity }}×
                            </span>
                            {{ line.stock_item_name }}
                        </q-item-label>
                        <q-item-label caption>
                            <span v-if="line.purchased_store_name">{{ line.purchased_store_name }}</span>
                            <span v-else-if="line.resolved_store_name" class="dora-text-muted">
                                {{ line.resolved_store_name }}
                            </span>
                            <span
                                v-if="line.estimate_source !== 'actual' && line.estimated_unit_price != null"
                                class="dora-text-muted"
                            >
                                <template v-if="line.purchased_store_name || line.resolved_store_name"> · </template>
                                estimated, no price entered
                            </span>
                        </q-item-label>
                    </q-item-section>

                    <q-item-section v-if="amending" side>
                        <!-- Only the three fields the agreed design unlocks.
                             Adding, removing and re-ordering lines stay closed:
                             a receipt is a record of what happened, and the
                             restock it drove has already been applied. -->
                        <div class="row items-center q-gutter-xs no-wrap">
                            <BaseButton
                                variant="icon"
                                size="sm"
                                :icon="ICONS.remove"
                                :disable="(line.quantity ?? 0) <= 0"
                                aria-label="One fewer"
                                @click="emit('adjust-quantity', line, -1)"
                            />
                            <span class="sl-receipt-qty-value">{{ line.quantity ?? '—' }}</span>
                            <BaseButton
                                variant="icon"
                                size="sm"
                                :icon="ICONS.add"
                                aria-label="One more"
                                @click="emit('adjust-quantity', line, 1)"
                            />
                            <BaseButton
                                variant="ghost"
                                dense
                                :icon="ICONS.edit"
                                :label="unitLabel(line)"
                                class="sl-receipt-amount"
                                @click="emit('edit-price', line)"
                            >
                                <q-tooltip>Correct the price and store for this line</q-tooltip>
                            </BaseButton>
                        </div>
                    </q-item-section>
                    <q-item-section v-else-if="moneyEnabled" side class="sl-receipt-money">
                        <div class="sl-receipt-amount">{{ lineAmount(line) }}</div>
                        <div
                            v-if="(line.quantity ?? 1) > 1 && line.estimated_unit_price != null"
                            class="text-caption dora-text-muted"
                        >
                            {{ formatMoney(line.estimated_unit_price) }} each
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>

            <template v-if="skippedLines.length > 0">
                <q-separator />
                <q-card-section class="q-py-sm">
                    <div class="text-caption dora-text-muted q-mb-xs">
                        Didn't buy ({{ skippedLines.length }})
                    </div>
                    <div class="row q-gutter-xs">
                        <q-chip
                            v-for="line in skippedLines"
                            :key="line.line_id"
                            dense
                            square
                            class="dora-bg-sunken"
                        >
                            {{ line.stock_item_name }}
                        </q-chip>
                    </div>
                </q-card-section>
            </template>
        </q-card>

        <!-- Where the money went. Same card as the plan face, past tense —
             the numbers are the same aggregate, only the trip has happened. -->
        <StoreSpendCard
            class="q-mt-sm"
            title="Where you spent it"
            :buckets="detail.totals.by_store"
            :collapsible="$q.screen.lt.md"
        />
    </div>
</template>

<script lang="ts" setup>
    /**
     * The receipt face — a finished list as a record of what happened.
     *
     * It replaces the old "DONE is DRAFT with everything disabled" rendering,
     * which showed a full editing surface greyed out: every stepper, drag
     * handle and delete button still on screen, all of them inert. That taught
     * the user nothing about the trip and made the page look broken.
     *
     * The data for a real receipt was already there and unused: what was
     * bought, what it cost, where from, and what got skipped. This shows that,
     * read-only, and puts the corrections behind an explicit **Amend** mode so
     * the default state of a historical record is "you cannot fat-finger it".
     */
    import { computed } from 'vue';
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import StoreSpendCard from 'src/components/shoppingList/StoreSpendCard.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { priceOfLine, type ShoppingListDetail, type ShoppingListLine } from 'src/models/shoppingList';

    const props = defineProps<{
        detail: ShoppingListDetail;
        amending: boolean;
        /** Rendered under the heading — the page owns date formatting. */
        completedLabel: string | null;
    }>();

    const emit = defineEmits<{
        'stop-amend': [];
        'edit-price': [line: ShoppingListLine];
        'adjust-quantity': [line: ShoppingListLine, delta: number];
    }>();

    const $q = useQuasar();
    const { moneyEnabled } = useMoneyEnabled();

    // Deferred-by-budget lines are not part of the active list and the server's
    // totals skip them, so the receipt must too — otherwise a line could appear
    // in the itemisation with no money behind it in the header.
    const activeLines = computed(() =>
        props.detail.lines.filter((l) => !l.deferred_by_budget)
    );
    const boughtLines = computed(() => activeLines.value.filter((l) => l.is_ticked));
    const skippedLines = computed(() => activeLines.value.filter((l) => !l.is_ticked));

    const unpricedCount = computed(() =>
        boughtLines.value.filter((l) => l.estimated_unit_price == null).length
    );

    /** A "~" whenever the number is an estimate rather than one the user
     *  typed — on a receipt, the difference between "what it cost" and "what
     *  we think it cost" is the whole point of the document. */
    function lineAmount(line: ShoppingListLine): string {
        if (line.estimated_unit_price == null) return '—';
        const prefix = line.estimate_source === 'actual' ? '' : '~';
        return `${prefix}${formatMoney(priceOfLine(line))}`;
    }

    function unitLabel(line: ShoppingListLine): string {
        return line.estimated_unit_price == null
            ? 'Set price'
            : formatMoney(line.estimated_unit_price);
    }
</script>

<style scoped>
    .sl-receipt-card {
        background: var(--surface-elevated);
    }
    .sl-receipt-total,
    .sl-receipt-amount,
    .sl-receipt-qty,
    .sl-receipt-qty-value {
        font-variant-numeric: tabular-nums;
    }
    .sl-receipt-qty {
        color: var(--text-secondary);
        margin-right: 2px;
    }
    .sl-receipt-qty-value {
        min-width: 20px;
        text-align: center;
    }
    .sl-receipt-money {
        align-items: flex-end;
    }
</style>
