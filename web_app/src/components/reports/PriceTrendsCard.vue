<template>
    <DashboardCard :icon="ICONS.query_stats" title="Price trends">
        <div class="pt-picker">
            <q-select
                :model-value="selectedProductIds"
                :options="productOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                use-input
                multiple
                use-chips
                :max-values="5"
                outlined
                dense
                clearable
                label="Pick up to 5 products"
                @filter="onFilter"
                @update:model-value="onSelection"
            />
        </div>
        <!-- B10 — a chart-shaped block, not a spinner. The rule is explicit
             that an async surface over 150ms shows a skeleton shaped like its
             content and "never a blank pane"; a centred spinner in a 280px box
             is the blank pane with a moving dot in it. -->
        <AppSkeleton
            v-if="loading"
            type="rect"
            height="280px"
            radius="var(--radius-md)"
        />
        <CardLoadError
            v-else-if="failed"
            line="I couldn't load these price trends."
            @retry="emit('retry')"
        />
        <div v-else-if="hasPoints" ref="chartHostRef" class="pt-chart">
            <PriceHistoryChart
                :series="chartSeries"
                :width="chartWidth"
                :height="280"
                legend
            />
        </div>
        <CardEmpty v-else :icon="ICONS.query_stats">
            Pick a product to chart its unit price over time.
        </CardEmpty>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "Is this worth buying?" — unit price over time, per product.
     *
     * **FU-833 landed here:** this was the app's last ECharts consumer, and the
     * dependency is gone with it. The replacement is `PriceHistoryChart` — the
     * inline-SVG chart the app already owned, which ships in ~8 KB against the
     * 549 KB ECharts was inlining into this route's chunk, and which draws
     * exactly this: a multi-series line with y-ticks, x-labels, a hover
     * crosshair and (new, and the reason the swap was worth doing rather than
     * merely cheap) a legend and a real text alternative. A canvas chart cannot
     * carry one, which is what left §4.9's finding unfixable while it stood.
     *
     * Two behavioural changes worth naming, both accepted: the line is no longer
     * smoothed — a spline through fortnightly price points invents readings
     * between them — and a gap in one product's series is a gap, where
     * `connectNulls` used to bridge it. Both make the chart say less than it
     * did, which is the point.
     */
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import CardEmpty from 'src/components/CardEmpty.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import PriceHistoryChart from 'src/components/PriceHistoryChart.vue';
    import { trendSeriesToChart } from 'src/composables/usePriceChartSeries';
    import type { PriceTrendsResponse } from 'src/services/api/reportsApiService';

    const props = withDefaults(defineProps<{
        priceTrends: PriceTrendsResponse | null;
        productOptions: { label: string; value: string }[];
        selectedProductIds: string[];
        loading?: boolean;
        failed?: boolean;
    }>(), { loading: false, failed: false });

    const emit = defineEmits<{
        (e: 'retry'): void;
        (e: 'select', ids: string[]): void;
        (e: 'filter', input: string, doneFn: (cb: () => void) => void): void;
    }>();

    /** `clearable` on a `multiple` q-select emits **null**, not `[]`. The old
     *  handler read `.length` off it on the very next line, so clicking clear
     *  threw. Normalised once, here, rather than making every reader
     *  null-aware. */
    function onSelection(value: string[] | null) {
        emit('select', value ?? []);
    }
    function onFilter(input: string, doneFn: (cb: () => void) => void) {
        emit('filter', input, doneFn);
    }

    const hasPoints = computed(() =>
        (props.priceTrends?.series ?? []).some((s) => s.points.length > 0),
    );
    const chartSeries = computed(
        () => trendSeriesToChart(props.priceTrends?.series ?? []),
    );

    // The SVG chart is sized in px, not by CSS, so the card measures its own
    // content box and hands the width down — the same pattern `/price-history`
    // and the bottom sheet already use. ECharts' `autoresize` did this
    // internally; losing it is the one thing the swap costs.
    const chartHostRef = ref<HTMLElement | null>(null);
    const chartWidth = ref(640);
    let observer: ResizeObserver | null = null;

    function measure(): void {
        const el = chartHostRef.value;
        if (!el) return;
        const next = Math.max(260, Math.floor(el.clientWidth));
        if (next !== chartWidth.value) chartWidth.value = next;
    }

    function observe(): void {
        const el = chartHostRef.value;
        if (!el || typeof ResizeObserver === 'undefined') return;
        measure();
        if (observer) return;
        observer = new ResizeObserver(() => measure());
        observer.observe(el);
    }

    onMounted(observe);
    // The host only exists once there is something to draw, so re-attach when
    // the card crosses from its empty state into a chart.
    watch(hasPoints, (has) => {
        if (has) requestAnimationFrame(observe);
    });
    onBeforeUnmount(() => {
        observer?.disconnect();
        observer = null;
    });
</script>

<style scoped lang="scss">
    .pt-picker { margin-bottom: var(--space-3); }
    .pt-chart {
        min-height: 220px;
        overflow-x: auto;
    }
</style>
