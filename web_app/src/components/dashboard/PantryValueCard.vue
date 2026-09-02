<template>
    <DashboardCard :icon="ICONS.inventory" title="Pantry value">
        <CardLoadError
            v-if="failed"
            line="I couldn't value your pantry just now."
            @retry="emit('retry')"
        />
        <div v-else-if="latest !== null">
            <div class="dora-stat-num">{{ formatMoney(latest) }}</div>
            <div v-if="delta !== null && delta !== 0" class="dora-pantry-delta">
                {{ delta > 0 ? '▲' : '▼' }}
                {{ formatMoney(Math.abs(delta)) }} over {{ windowDays }} days
            </div>
            <!-- R-041 — the caveat renders WHENEVER the number does, not only
                 when the server bothers to send one. This figure is an estimate
                 that silently undercounts: unpriced items contribute zero. -->
            <div class="text-caption dora-text-muted q-mt-xs">
                {{ estimateNote || FALLBACK_NOTE }}
            </div>
        </div>
        <div v-else class="dora-empty">
            Add prices to your stock items to see what your pantry's worth.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * An opt-in glance at the pantry's estimated worth.
     *
     * ⚠️ **The underlying metric is on notice.** `REPORTS_PAGE_REVIEW.md` §3.3
     * found that the server computes it as `stock_level.sequence × price` — a
     * 0–5 *ordinal* multiplied by a dollar figure, so an item at "Plenty"
     * contributes `rank × price` whether that is one jar or twelve — and that it
     * systematically undercounts, because items with no price contribute nothing.
     * The review recommends **replacing** the metric (count of items at Low/Out
     * over time, or essential coverage — both honestly measured) rather than
     * repairing it. Until that lands, the number must never render bare, which
     * is why the caveat below is unconditional rather than `v-if`'d on the
     * server sending one (R-041).
     *
     * Extracted from `DashboardPage.vue` (FU-829).
     */
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';

    withDefaults(
        defineProps<{
            /** Latest point in the series, or null when nothing is priced. */
            latest: number | null;
            /** Change across the window, or null when there aren't two points. */
            delta: number | null;
            /** The window the delta spans, so the copy can't drift from the fetch. */
            windowDays?: number;
            /** The server's own caveat, when it sends one. */
            estimateNote?: string | undefined;
            failed?: boolean;
        }>(),
        { windowDays: 90, estimateNote: undefined, failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();

    const FALLBACK_NOTE =
        "Estimated from the prices you've recorded — items with no price aren't counted.";
</script>

<style scoped lang="scss">
    /* The `.is-up` / `.is-down` semantic colouring is deliberately absent
       (§6 finding 20). A rising pantry value was painted **green** while Reports
       paints rising *spend* **red** — the same underlying fact ("more dollars in
       the household's food system") coloured opposite ways on two screens. A1
       also reserves negative for out-of-stock / destructive / errors, and a
       pantry getting cheaper is none of those. The ▲/▼ carries the direction;
       semantic colour is kept for **budget**, which has a real threshold. */
    .dora-pantry-delta {
        margin-top: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
    }
</style>
