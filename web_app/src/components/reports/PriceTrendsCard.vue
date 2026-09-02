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
        <div v-if="loading" class="pt-loading">
            <AppSpinner size="32px" />
        </div>
        <CardLoadError
            v-else-if="failed"
            line="I couldn't load these price trends."
            @retry="emit('retry')"
        />
        <v-chart
            v-else-if="hasPoints"
            class="pt-chart"
            :option="option"
            autoresize
        />
        <div v-else class="dora-empty">
            Pick a product to chart its unit price over time.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "Is this worth buying?" — unit price over time, per product.
     *
     * The one genuinely chart-shaped widget on the page, and the only surviving
     * ECharts consumer after chunk 3 (composition became CSS bars, counts became
     * CSS columns, the savings sparkline became a sentence, stock-value-over-time
     * was cut). That makes **FU-833** a one-widget job now: move this onto
     * `PriceHistoryChart.vue` — 462 lines of inline SVG the app already ships in
     * 8 KB, which draws exactly this chart — and the dependency goes with it.
     * Left in place here deliberately: swapping the renderer is a behavioural
     * change to the one thing on this page that has to keep working, and it
     * carries its own a11y investment (the SVG component has no legend, no
     * x-ticks and no `aria`).
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import VChart from 'vue-echarts';
    import { LineChart } from 'echarts/charts';
    import {
        GridComponent,
        LegendComponent,
        TitleComponent,
        TooltipComponent,
    } from 'echarts/components';
    import { use } from 'echarts/core';
    import { CanvasRenderer } from 'echarts/renderers';
    import { formatMoney } from 'src/composables/useMoney';
    import type { PriceTrendsResponse } from 'src/services/api/reportsApiService';

    // Registration lives with the one component that draws a chart, so the page
    // itself no longer imports ECharts at all. `PieChart` is gone with the
    // donuts — the tree-shaken set is now a line chart and nothing else.
    use([
        CanvasRenderer,
        LineChart,
        GridComponent,
        TitleComponent,
        TooltipComponent,
        LegendComponent,
    ]);

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

    const option = computed(() => {
        const series = props.priceTrends?.series ?? [];
        const allDates = new Set<string>();
        for (const s of series) for (const p of s.points) allDates.add(p.date);
        const dates = [...allDates].sort();
        return {
            tooltip: {
                trigger: 'axis',
                valueFormatter: (v: number) => (v == null ? '—' : formatMoney(v)),
            },
            legend: { bottom: 0, type: 'scroll' },
            grid: { left: 50, right: 16, top: 24, bottom: 40 },
            xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10 } },
            // R-003 / D-006 — one money-formatting authority. A hardcoded `$`
            // gave a non-AUD install correct legends and a lying axis.
            yAxis: {
                type: 'value',
                axisLabel: { formatter: (value: number) => formatMoney(value) },
            },
            series: series.map((s) => {
                const byDate = new Map(s.points.map((p) => [p.date, p.unit_price]));
                return {
                    name: s.name,
                    type: 'line',
                    smooth: true,
                    connectNulls: true,
                    symbol: 'circle',
                    symbolSize: 4,
                    data: dates.map((d) => byDate.get(d) ?? null),
                };
            }),
        };
    });
</script>

<style scoped lang="scss">
    .pt-picker { margin-bottom: var(--space-3); }
    .pt-chart {
        height: 280px;
        min-height: 220px;
    }
    .pt-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--space-6);
    }
</style>
