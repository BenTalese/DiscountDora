<template>
    <!--
        Recipe cost breakdown, as a modal.

        Owner feedback 2026-08-24: the breakdown was an expansion row on the
        page ("weird as a section") holding a bare two-column table. Cost is a
        question you ask, get an answer to, and close — a modal, not a
        permanent fixture of the page. And the answer is not a list of
        numbers: it's *what dominates the bill* and *how much of the recipe we
        could actually price*. So the priced ingredients are ranked, each with
        a share bar, and the unpriced ones are grouped by why we couldn't
        price them rather than repeating "—" down a column.
    -->
    <BaseDialog
        v-model="open"
        title="Cost breakdown"
        closable
        card-style="min-width: 0; width: min(560px, 94vw)"
    >
        <q-card-section class="rcost__summary">
            <div class="rcost__totals">
                <div class="rcost__total">
                    <span class="rcost__k">Estimated total</span>
                    <span class="rcost__v">{{ total !== null ? formatMoney(total) : '—' }}</span>
                </div>
                <div v-if="perServing !== null" class="rcost__total">
                    <span class="rcost__k">Per serving</span>
                    <span class="rcost__v">{{ formatMoney(perServing) }}</span>
                </div>
            </div>

            <!-- How much of the recipe the estimate actually covers. A
                 confidence statement, not decoration: an estimate built from
                 3 of 11 ingredients is a different number to one built from
                 11 of 11, and the old table made the reader count rows. -->
            <div class="rcost__coverage">
                <div class="rcost__bar" role="img" :aria-label="coverageLabel">
                    <div class="rcost__barfill" :style="{ width: coveragePct + '%' }"></div>
                </div>
                <span class="rcost__cov">{{ coverageLabel }}</span>
            </div>
        </q-card-section>

        <q-separator />

        <q-card-section class="rcost__body">
            <template v-if="priced.length > 0">
                <ul class="rcost__list">
                    <li v-for="line in priced" :key="line.key">
                        <div class="rcost__row">
                            <span class="rcost__name">{{ line.name }}</span>
                            <span class="rcost__amount">{{ formatMoney(line.line_cost!) }}</span>
                        </div>
                        <div class="rcost__share">
                            <div class="rcost__sharefill" :style="{ width: sharePct(line) + '%' }"></div>
                        </div>
                        <div class="rcost__meta">
                            <span v-if="formatQuantity(line.quantity, line.unit)">
                                {{ formatQuantity(line.quantity, line.unit) }}
                            </span>
                            <span v-if="unitPriceLabel(line)">{{ unitPriceLabel(line) }}</span>
                        </div>
                    </li>
                </ul>
            </template>
            <p v-else class="rcost__empty">
                Nothing here could be priced yet.
            </p>

            <template v-for="group in unpricedGroups" :key="group.reason">
                <div class="rcost__grouphead">{{ group.title }}</div>
                <p class="rcost__groupnames">{{ group.names.join(' · ') }}</p>
            </template>
        </q-card-section>

        <template #actions>
            <BaseButton variant="ghost" label="Close" @click="open = false" />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';

    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import type { RecipeCostLine, RecipeCostUnpricedReason } from 'src/models/recipe';

    const props = defineProps<{
        modelValue: boolean;
        lines: RecipeCostLine[];
        /** Server-derived estimate. Null when nothing could be priced. */
        total: number | null;
        pricedCount: number;
        totalCount: number;
        servings: number | null;
    }>();

    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v),
    });

    /** Display math only — the estimate itself is server-owned (R-003). */
    const perServing = computed(() => {
        if (props.total === null || !props.servings || props.servings <= 0) return null;
        return props.total / props.servings;
    });

    type PricedLine = RecipeCostLine & { key: string };

    /** Dearest first: the actionable read of a bill is what dominates it. */
    const priced = computed<PricedLine[]>(() =>
        props.lines
            .filter((l) => l.line_cost !== null)
            .map((l, i) => ({ ...l, key: `${l.name}-${i}` }))
            .sort((a, b) => (b.line_cost ?? 0) - (a.line_cost ?? 0)));

    const dearest = computed(() => priced.value[0]?.line_cost ?? 0);
    function sharePct(line: PricedLine): number {
        if (dearest.value <= 0) return 0;
        return Math.max(2, Math.round(((line.line_cost ?? 0) / dearest.value) * 100));
    }

    /** "$0.00 / g" is what a per-gram price rounds to in cents, and it reads
     *  as free. Prices that fine are quoted per kilo or per litre in every
     *  shop, so that's how they're shown here; anything coarser is left
     *  alone. */
    function unitPriceLabel(line: RecipeCostLine): string | null {
        if (line.unit_price === null || !line.priced_unit) return null;
        const scaleTo: Record<string, string> = { g: 'kg', ml: 'L' };
        const bigger = scaleTo[line.priced_unit];
        if (bigger && line.unit_price < 0.05) {
            return `${formatMoney(line.unit_price * 1000)} / ${bigger}`;
        }
        return `${formatMoney(line.unit_price)} / ${line.priced_unit}`;
    }

    const coveragePct = computed(() => {
        if (props.totalCount <= 0) return 0;
        return Math.round((props.pricedCount / props.totalCount) * 100);
    });
    const coverageLabel = computed(
        () => `Priced ${props.pricedCount} of ${props.totalCount} ingredients`);

    /** The phrasing lives on the client (the server ships reasons, not copy) —
     *  same split as the page's `costLineReason`, grouped so a recipe with
     *  eight unlinked rows reads as one sentence rather than eight. */
    const REASON_TITLES: Record<RecipeCostUnpricedReason, string> = {
        no_link: 'Not linked to a pantry item',
        no_price: 'No price recorded yet',
        unit_mismatch: "Units don't match the price",
    };

    const unpricedGroups = computed(() => {
        const buckets = new Map<RecipeCostUnpricedReason, string[]>();
        for (const line of props.lines) {
            if (line.line_cost !== null || !line.reason) continue;
            const names = buckets.get(line.reason) ?? [];
            names.push(line.name);
            buckets.set(line.reason, names);
        }
        return [...buckets.entries()].map(([reason, names]) => ({
            reason,
            title: REASON_TITLES[reason],
            names,
        }));
    });
</script>

<style scoped lang="scss">
    .rcost__summary {
        display: flex;
        flex-direction: column;
        gap: var(--space-3, 12px);
    }
    .rcost__totals {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-6, 24px);
    }
    .rcost__total { display: flex; flex-direction: column; gap: 2px; }
    .rcost__k {
        font-size: var(--font-size-xs, 0.6875rem);
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .rcost__v {
        font-size: 1.5rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }

    .rcost__coverage { display: flex; align-items: center; gap: var(--space-3, 12px); }
    .rcost__bar {
        flex: 1;
        height: 6px;
        border-radius: var(--radius-pill, 999px);
        background: var(--surface-sunken);
        overflow: hidden;
    }
    .rcost__barfill { height: 100%; background: var(--brand-primary); }
    .rcost__cov {
        font-size: 0.8125rem;
        color: var(--text-muted);
        white-space: nowrap;
    }

    .rcost__body { max-height: 52vh; overflow-y: auto; }
    .rcost__list { list-style: none; margin: 0; padding: 0; }
    .rcost__list > li { padding: var(--space-2, 8px) 0; }
    .rcost__row {
        display: flex;
        align-items: baseline;
        gap: var(--space-3, 12px);
    }
    .rcost__name { flex: 1; min-width: 0; }
    .rcost__amount { font-weight: 700; font-variant-numeric: tabular-nums; }
    .rcost__share {
        height: 4px;
        border-radius: var(--radius-pill, 999px);
        background: var(--surface-sunken);
        overflow: hidden;
        margin-top: var(--space-1, 4px);
    }
    .rcost__sharefill { height: 100%; background: var(--brand-primary-soft); }
    .rcost__meta {
        display: flex;
        gap: var(--space-3, 12px);
        margin-top: 2px;
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .rcost__grouphead {
        margin-top: var(--space-4, 16px);
        font-size: var(--font-size-xs, 0.6875rem);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .rcost__groupnames {
        margin: var(--space-1, 4px) 0 0;
        font-size: 0.8125rem;
        color: var(--text-secondary);
    }
    .rcost__empty { color: var(--text-muted); font-size: 0.875rem; margin: 0; }
</style>
