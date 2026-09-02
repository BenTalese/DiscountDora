<template>
    <DashboardCard :icon="ICONS.storefront" title="Spend by store">
        <template #action>
            <span class="dora-card-action">last 30 days</span>
        </template>
        <CardLoadError
            v-if="failed"
            line="I couldn't load your spend by store."
            @retry="emit('retry')"
        />
        <template v-else-if="top.length > 0">
            <ul class="dora-spend-list">
                <li
                    v-for="row in top"
                    :key="row.store_id ?? row.store"
                    class="dora-spend-row"
                >
                    <span class="dora-spend-store">{{ row.store }}</span>
                    <span class="dora-spend-amt">{{ formatMoney(row.spend) }}</span>
                </li>
            </ul>
            <!-- R-041 — the total says what it covers. It used to read a bare
                 "$412 total" under three store rows, which reads as the sum of
                 those three; it is in fact the sum of *all* of them, and it was
                 being computed in the browser. Both fixed: the server ships
                 `total_spend` + `store_count`, and the line names its coverage
                 whenever the number renders. -->
            <div class="dora-spend-total">
                {{ formatMoney(total) }} across
                {{ storeCount }} store{{ storeCount === 1 ? '' : 's' }}
                <span v-if="storeCount > top.length">
                    · top {{ top.length }} shown
                </span>
            </div>
        </template>
        <div v-else class="dora-empty">
            Your spend by store shows up once you complete a shop.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * An opt-in glance at where the money went over the last 30 days.
     *
     * Known inconsistency, recorded rather than fixed here: this renders stores
     * as a plain text list with **no colour**, while the shopping list draws the
     * same data as a proportional bar with brand-coloured segments and Reports
     * draws it as a donut with hash-assigned chart hues — three renderings of one
     * dataset, three colour systems (`REPORTS_PAGE_REVIEW.md` §3.1, FU-814/815).
     * The convergence belongs to that FU, not to an extraction.
     *
     * Extracted from `DashboardPage.vue` (FU-829).
     */
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { StoreSpendRow } from 'src/services/api/reportsApiService';

    withDefaults(
        defineProps<{
            /** The rows actually shown — the page slices to the top few. */
            top: StoreSpendRow[];
            /** Server-computed total across EVERY row (R-041). */
            total: number;
            /** How many stores that total was built from (R-041 coverage). */
            storeCount: number;
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();
</script>

<style scoped lang="scss">
    /* Moved with the card (R-027); off the page-local `--c-*` aliases, which
       don't resolve from a component (R-060). */
    .dora-spend-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .dora-spend-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-spend-store {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 600;
    }
    .dora-spend-amt {
        font-weight: 700;
        white-space: nowrap;
    }
    .dora-spend-total {
        margin-top: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-align: right;
    }
</style>
