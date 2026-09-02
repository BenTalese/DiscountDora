<template>
    <p v-if="sentence" class="reports-lede">{{ sentence }}</p>
</template>

<script lang="ts" setup>
    /**
     * The page's opening line — the answer, not the caveat.
     *
     * `REPORTS_PAGE_REVIEW.md` §4.10.1: the page used to open with a title, a
     * disclaimer ("estimates pulled from…") and a control. Three things, none of
     * which is a finding. One sentence of real numbers is what turns a dashboard
     * of instruments into a report; the caveat moved to an info icon beside the
     * range picker, where it belongs.
     *
     * **Everything here is already server-computed** — no cross-entity
     * arithmetic in the browser (R-003). `current_total`, `delta_pct` and the
     * per-group movers come from the year-over-year handler, which despite its
     * name compares any window against the same-length window before it, and the
     * shop count comes from spend-by-store's own `store_count` (R-041).
     *
     * Renders nothing when there is no spend to describe: a lede that says "you
     * spent $0.00 across 0 shops" is worse than a page that gets on with it.
     */
    import { computed } from 'vue';
    import { formatMoney } from 'src/composables/useMoney';
    import type {
        ReportRange,
        SpendYoYResponse,
        StoreSpendResponse,
    } from 'src/services/api/reportsApiService';

    const props = defineProps<{
        range: ReportRange;
        storeSpend: StoreSpendResponse | null;
        spendYoY: SpendYoYResponse | null;
    }>();

    const WINDOW_WORDS: Record<ReportRange, string> = {
        '30d': 'in the last 30 days',
        '90d': 'in the last 90 days',
        '1y': 'in the last year',
        '2y': 'in the last 2 years',
        '5y': 'in the last 5 years',
        'all': 'all time',
    };
    // The comparison window is the same length as the current one, immediately
    // before it — so the sentence must not say "than last month" on a 90-day view.
    const PRIOR_WORDS: Record<ReportRange, string> = {
        '30d': 'the 30 days before',
        '90d': 'the 90 days before',
        '1y': 'the year before',
        '2y': 'the 2 years before',
        '5y': 'the 5 years before',
        'all': '',
    };

    const sentence = computed<string | null>(() => {
        const total = props.storeSpend?.total_spend ?? 0;
        if (total <= 0) return null;

        const shops = props.storeSpend?.store_count ?? 0;
        const parts = [
            `You spent ${formatMoney(total)} across `
            + `${shops} shop${shops === 1 ? '' : 's'} ${WINDOW_WORDS[props.range]}`,
        ];

        // `delta_pct` is null when the prior window had no spend — a new
        // household, not a 100% rise (the handler is careful about this and so
        // is the sentence).
        const yoy = props.spendYoY;
        if (yoy && yoy.delta_pct !== null && PRIOR_WORDS[props.range]) {
            const direction = yoy.delta_pct >= 0 ? 'more' : 'less';
            parts.push(
                ` — ${Math.abs(yoy.delta_pct)}% ${direction} than ${PRIOR_WORDS[props.range]}`,
            );
        }
        parts.push('.');

        // Biggest mover. The handler already ranks rows by absolute delta, so
        // the first row IS the mover — no re-sorting a fetched collection here.
        const mover = yoy?.rows?.[0];
        if (mover && mover.delta !== 0) {
            const word = mover.delta > 0 ? 'up' : 'down';
            parts.push(
                ` Biggest mover: ${mover.category}, ${word} `
                + `${formatMoney(Math.abs(mover.delta))}.`,
            );
        }
        return parts.join('');
    });
</script>

<style scoped lang="scss">
    .reports-lede {
        margin: var(--space-2) 0 0;
        max-width: 70ch;
        font-size: calc(var(--font-size-lg) * 1rem);
        line-height: 1.45;
        color: var(--text-primary);
    }
</style>
