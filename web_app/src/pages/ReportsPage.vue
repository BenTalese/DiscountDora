<template>
    <div class="reports-page">
        <header class="reports-header">
            <div class="reports-title-block">
                <h1 class="reports-title">Reports</h1>
                <p class="reports-sub">
                    Estimates pulled from your archived shopping lists, stock
                    history, and tracked merchant prices.
                </p>
            </div>
            <q-btn-toggle
                v-model="range"
                :options="RANGE_OPTIONS"
                no-caps
                rounded
                dense
                color="grey-3"
                text-color="grey-9"
                toggle-color="primary"
                toggle-text-color="white"
                @update:model-value="loadAll"
            />
        </header>

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div class="reports-grid">
            <!-- Stock value over time -->
            <article class="report-card report-card-wide">
                <header class="report-card-head">
                    <q-icon :name="ICONS.show_chart" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Stock value over time</h3>
                    <span v-if="stockValue?.estimate_note" class="report-card-note">
                        <q-icon :name="ICONS.info" size="14px" />
                        {{ stockValue.estimate_note }}
                    </span>
                </header>
                <div v-if="loading.stockValue" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <v-chart
                    v-else-if="(stockValue?.points.length ?? 0) > 0"
                    class="report-chart"
                    :option="stockValueOption"
                    autoresize
                />
                <div v-else class="report-empty">
                    No stock-level history in this range yet. Update an item's level
                    or wait — the line builds as you use the app.
                </div>
            </article>

            <!-- Spend by merchant (donut) -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.donut_large" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Spend by merchant</h3>
                </header>
                <div v-if="loading.merchantSpend" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <div v-else-if="(merchantSpend?.rows.length ?? 0) > 0" class="merchant-row">
                    <v-chart
                        class="report-donut"
                        :option="merchantSpendOption"
                        autoresize
                    />
                    <ul class="merchant-legend">
                        <li v-for="row in merchantSpend!.rows" :key="row.merchant">
                            <span class="merchant-dot" :style="{ background: colourFor(row.merchant) }" />
                            <span class="merchant-name">{{ row.merchant }}</span>
                            <span class="merchant-spend">${{ row.spend.toFixed(2) }}</span>
                            <span class="merchant-count">{{ row.list_count }} list{{ row.list_count === 1 ? '' : 's' }}</span>
                        </li>
                    </ul>
                </div>
                <div v-else class="report-empty">
                    No completed shopping lists in this range — finish a list to see
                    your spend break down by merchant.
                </div>
            </article>

            <!-- Most bought -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.trending_up" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Top 10 most-bought</h3>
                </header>
                <div v-if="loading.mostBought" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <ul v-else-if="(mostBought?.rows.length ?? 0) > 0" class="report-list">
                    <li v-for="row in mostBought!.rows" :key="row.stock_item_id">
                        <a class="report-list-name" @click="goToStock(row.stock_item_id)">
                            {{ row.name }}
                        </a>
                        <span class="report-list-count">×{{ row.appearances }}</span>
                    </li>
                </ul>
                <div v-else class="report-empty">
                    No archived lists in this range yet.
                </div>
            </article>

            <!-- Keeps running out -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.warning_amber" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">You keep running out of these</h3>
                    <q-btn
                        v-if="(keepsOut?.rows.length ?? 0) > 0"
                        flat
                        dense
                        no-caps
                        size="sm"
                        :icon="ICONS.bookmark"
                        label="Mark all essential"
                        @click="markAllEssential"
                    />
                </header>
                <div v-if="loading.keepsOut" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <ul v-else-if="(keepsOut?.rows.length ?? 0) > 0" class="report-list">
                    <li v-for="row in keepsOut!.rows" :key="row.stock_item_id">
                        <a class="report-list-name" @click="goToStock(row.stock_item_id)">
                            {{ row.name }}
                        </a>
                        <span class="report-list-count">{{ row.times_out_when_added }}× out when added</span>
                    </li>
                </ul>
                <div v-else class="report-empty">
                    Nothing's been added to a list while out of stock — nicely played.
                </div>
            </article>

            <!-- Savings captured -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.savings" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Savings captured</h3>
                </header>
                <div v-if="loading.savings" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <div v-else-if="savings && savings.total_spent > 0" class="savings-body">
                    <div class="savings-number">
                        ${{ savings.total_savings.toFixed(2) }}
                    </div>
                    <div class="savings-sub">
                        saved vs RRP on ${{ savings.total_spent.toFixed(2) }} spent
                        ({{ savings.lists.length }} list{{ savings.lists.length === 1 ? '' : 's' }})
                    </div>
                    <v-chart
                        v-if="savings.lists.length > 1"
                        class="report-sparkline"
                        :option="savingsSparkOption"
                        autoresize
                    />
                </div>
                <div v-else class="report-empty">
                    Finish a shopping list with picked merchant offers to start
                    tracking savings.
                </div>
            </article>

            <!-- Price trends -->
            <article class="report-card report-card-wide">
                <header class="report-card-head">
                    <q-icon :name="ICONS.query_stats" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Price trends</h3>
                </header>
                <div class="price-picker">
                    <q-select
                        v-model="selectedProductIds"
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
                        @filter="filterProducts"
                        @update:model-value="loadPriceTrends"
                    />
                </div>
                <div v-if="loading.priceTrends" class="report-card-loading">
                    <q-spinner size="32px" color="primary" />
                </div>
                <v-chart
                    v-else-if="(priceTrends?.series.length ?? 0) > 0 && priceTrendsHasPoints"
                    class="report-chart"
                    :option="priceTrendsOption"
                    autoresize
                />
                <div v-else class="report-empty">
                    Pick a product to chart its unit price over time.
                </div>
            </article>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { LineChart, PieChart } from 'echarts/charts';
    import {
        GridComponent,
        LegendComponent,
        TitleComponent,
        TooltipComponent,
    } from 'echarts/components';
    import { use } from 'echarts/core';
    import { CanvasRenderer } from 'echarts/renderers';
    import { Notify } from 'quasar';
    import type { Product } from 'src/models/product';
    import ProductApiService from 'src/services/api/productApiService';
    import ReportsApiService, {
        type KeepsRunningOutResponse,
        type MerchantSpendResponse,
        type MostBoughtResponse,
        type PriceTrendsResponse,
        type ReportRange,
        type SavingsCapturedResponse,
        type StockValueResponse,
    } from 'src/services/api/reportsApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { computed, onMounted, ref } from 'vue';
    import VChart from 'vue-echarts';
    import { useRouter } from 'vue-router';

    use([
        CanvasRenderer,
        LineChart,
        PieChart,
        GridComponent,
        TitleComponent,
        TooltipComponent,
        LegendComponent,
    ]);

    const router = useRouter();
    const reportsApi = new ReportsApiService();
    const productApi = new ProductApiService();
    const stockApi = new StockItemApiService();

    const RANGE_OPTIONS: { label: string; value: ReportRange }[] = [
        { label: '30 days', value: '30d' },
        { label: '90 days', value: '90d' },
        { label: '1 year', value: '1y' },
        { label: 'All time', value: 'all' },
    ];

    const range = ref<ReportRange>('30d');
    const loadError = ref<string | null>(null);

    const loading = ref({
        stockValue: false,
        merchantSpend: false,
        mostBought: false,
        keepsOut: false,
        savings: false,
        priceTrends: false,
    });

    const stockValue = ref<StockValueResponse | null>(null);
    const merchantSpend = ref<MerchantSpendResponse | null>(null);
    const mostBought = ref<MostBoughtResponse | null>(null);
    const keepsOut = ref<KeepsRunningOutResponse | null>(null);
    const savings = ref<SavingsCapturedResponse | null>(null);
    const priceTrends = ref<PriceTrendsResponse | null>(null);

    const allProducts = ref<Product[]>([]);
    const selectedProductIds = ref<string[]>([]);
    const productOptions = ref<{ label: string; value: string }[]>([]);

    function filterProducts(input: string, doneFn: (cb: () => void) => void) {
        const needle = input.trim().toLowerCase();
        doneFn(() => {
            const matches = needle.length === 0
                ? allProducts.value
                : allProducts.value.filter((p) =>
                    p.name.toLowerCase().includes(needle)
                    || (p.merchant_name ?? '').toLowerCase().includes(needle),
                );
            productOptions.value = matches.slice(0, 50).map((p) => ({
                label: `${p.name} · ${p.merchant_name}`,
                value: p.product_id,
            }));
        });
    }

    // ── Chart options ────────────────────────────────────────────────────
    // Pull the active theme's chart palette + brand colours from the
    // document so charts re-paint when the user switches theme. Recomputes
    // on `themeTick` bumps (triggered by the route nav + manual reload).
    //
    // CSS custom properties return their literal stored value — modern
    // `hsl(h s% l%)` syntax for our tokens. Normalise through a canvas
    // so chart libraries always see a canonical hex/rgba string.
    const themeTick = ref(0);
    const colourCanvas = typeof document === 'undefined'
        ? null : document.createElement('canvas').getContext('2d');
    function normaliseColour(raw: string): string {
        if (!colourCanvas) return raw;
        try {
            colourCanvas.fillStyle = '#000';
            colourCanvas.fillStyle = raw;
            return colourCanvas.fillStyle;
        } catch {
            return raw;
        }
    }
    const chartPalette = computed(() => {
        void themeTick.value;
        const cs = typeof document === 'undefined' ? null : getComputedStyle(document.documentElement);
        const read = (name: string, fallback: string) =>
            normaliseColour(cs?.getPropertyValue(name).trim() || fallback);
        return {
            primary: read('--brand-primary', '#17b073'),
            positive: read('--semantic-positive', '#6ba368'),
            series: [
                read('--chart-1', '#17b073'),
                read('--chart-2', '#006a80'),
                read('--chart-3', '#fed224'),
                read('--chart-4', '#e89a45'),
                read('--chart-5', '#5b8db8'),
                read('--chart-6', '#a07cc8'),
            ],
        };
    });

    function colourFor(key: string): string {
        let hash = 0;
        for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) | 0;
        const series = chartPalette.value.series;
        return series[Math.abs(hash) % series.length]!;
    }

    const stockValueOption = computed(() => ({
        tooltip: { trigger: 'axis', valueFormatter: (v: number) => `$${v.toFixed(2)}` },
        grid: { left: 50, right: 16, top: 24, bottom: 32 },
        xAxis: {
            type: 'category',
            data: stockValue.value?.points.map((p) => p.date) ?? [],
            axisLabel: { fontSize: 10 },
        },
        yAxis: { type: 'value', axisLabel: { formatter: '${value}' } },
        series: [{
            type: 'line',
            smooth: true,
            symbol: 'none',
            areaStyle: { opacity: 0.15 },
            lineStyle: { width: 2 },
            data: stockValue.value?.points.map((p) => p.value) ?? [],
            color: chartPalette.value.primary,
        }],
    }));

    const merchantSpendOption = computed(() => ({
        tooltip: { trigger: 'item', valueFormatter: (v: number) => `$${v.toFixed(2)}` },
        series: [{
            type: 'pie',
            radius: ['55%', '80%'],
            avoidLabelOverlap: true,
            label: { show: false },
            data: (merchantSpend.value?.rows ?? []).map((row) => ({
                name: row.merchant,
                value: row.spend,
                itemStyle: { color: colourFor(row.merchant) },
            })),
        }],
    }));

    const savingsSparkOption = computed(() => ({
        grid: { left: 0, right: 0, top: 4, bottom: 4 },
        xAxis: { type: 'category', show: false, data: savings.value?.lists.map((l) => l.name) ?? [] },
        yAxis: { type: 'value', show: false },
        tooltip: { trigger: 'axis', valueFormatter: (v: number) => `$${v.toFixed(2)} saved` },
        series: [{
            type: 'line',
            smooth: true,
            symbol: 'none',
            areaStyle: { opacity: 0.2 },
            lineStyle: { width: 2 },
            color: chartPalette.value.positive,
            data: savings.value?.lists.map((l) => l.savings) ?? [],
        }],
    }));

    const priceTrendsHasPoints = computed(() =>
        (priceTrends.value?.series ?? []).some((s) => s.points.length > 0),
    );

    const priceTrendsOption = computed(() => {
        const series = priceTrends.value?.series ?? [];
        const allDates = new Set<string>();
        for (const s of series) for (const p of s.points) allDates.add(p.date);
        const dates = [...allDates].sort();
        return {
            tooltip: { trigger: 'axis', valueFormatter: (v: number) => v == null ? '—' : `$${v.toFixed(2)}` },
            legend: { bottom: 0, type: 'scroll' },
            grid: { left: 50, right: 16, top: 24, bottom: 40 },
            xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10 } },
            yAxis: { type: 'value', axisLabel: { formatter: '${value}' } },
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

    // ── Loaders ──────────────────────────────────────────────────────────
    async function loadStockValue() {
        loading.value.stockValue = true;
        try { stockValue.value = await reportsApi.getStockValueAsync(range.value); }
        finally { loading.value.stockValue = false; }
    }
    async function loadMerchantSpend() {
        loading.value.merchantSpend = true;
        try { merchantSpend.value = await reportsApi.getSpendByMerchantAsync(range.value); }
        finally { loading.value.merchantSpend = false; }
    }
    async function loadMostBought() {
        loading.value.mostBought = true;
        try { mostBought.value = await reportsApi.getMostBoughtAsync(range.value); }
        finally { loading.value.mostBought = false; }
    }
    async function loadKeepsOut() {
        loading.value.keepsOut = true;
        try { keepsOut.value = await reportsApi.getKeepsRunningOutAsync(); }
        finally { loading.value.keepsOut = false; }
    }
    async function loadSavings() {
        loading.value.savings = true;
        try { savings.value = await reportsApi.getSavingsCapturedAsync(range.value); }
        finally { loading.value.savings = false; }
    }
    async function loadPriceTrends() {
        if (selectedProductIds.value.length === 0) {
            priceTrends.value = null;
            return;
        }
        loading.value.priceTrends = true;
        try {
            priceTrends.value = await reportsApi.getPriceTrendsAsync(
                selectedProductIds.value, range.value,
            );
        }
        finally { loading.value.priceTrends = false; }
    }
    async function loadProductsCatalogue() {
        try {
            const page = await productApi.getAllAsync();
            allProducts.value = page.items;
            productOptions.value = page.items.slice(0, 50).map((p) => ({
                label: `${p.name} · ${p.merchant_name}`,
                value: p.product_id,
            }));
        } catch {
            allProducts.value = [];
        }
    }

    async function loadAll() {
        loadError.value = null;
        try {
            await Promise.all([
                loadStockValue(),
                loadMerchantSpend(),
                loadMostBought(),
                loadKeepsOut(),
                loadSavings(),
                loadPriceTrends(),
            ]);
        } catch {
            loadError.value = 'Could not load reports. Try refreshing.';
        }
    }

    function goToStock(id: string) {
        void router.push(`/stock/${id}`);
    }

    async function markAllEssential() {
        const ids = (keepsOut.value?.rows ?? []).map((r) => r.stock_item_id);
        if (ids.length === 0) return;
        try {
            await Promise.all(ids.map((id) => stockApi.updateAsync({ stock_item_id: id, is_flagged: true })));
            Notify.create({
                type: 'positive',
                position: 'bottom-right',
                message: `Marked ${ids.length} item${ids.length === 1 ? '' : 's'} essential.`,
            });
        } catch {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not mark all essential — try the items individually.',
            });
        }
    }

    onMounted(() => {
        void loadProductsCatalogue();
        void loadAll();
    });
</script>

<style scoped>
    .reports-page {
        padding: 24px 24px 96px;
        background: var(--surface-page);
        color: var(--text-primary);
        min-height: 100%;
    }
    .reports-header {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 24px;
    }
    .reports-title-block { flex: 1; min-width: 280px; }
    .reports-title { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .reports-sub {
        margin: 4px 0 0;
        color: var(--text-secondary);
        font-size: 0.92rem;
        max-width: 60ch;
    }
    .reports-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
    }
    @media (max-width: 900px) {
        .reports-grid { grid-template-columns: 1fr; }
    }
    .report-card {
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 18px;
        padding: 18px 20px 20px;
        box-shadow: var(--elevation-card);
        min-height: 240px;
        display: flex;
        flex-direction: column;
    }
    .report-card-wide { grid-column: 1 / -1; }
    .report-card-head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
    }
    .report-card-icon { color: var(--brand-primary); }
    .report-card-title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        flex: 1;
    }
    .report-card-note {
        font-size: 0.72rem;
        color: var(--text-secondary);
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .report-card-loading,
    .report-empty {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
        font-size: 0.9rem;
        text-align: center;
        padding: 24px;
    }
    .report-chart {
        flex: 1;
        height: 280px;
        min-height: 220px;
    }
    .report-donut {
        width: 180px;
        height: 180px;
        flex-shrink: 0;
    }
    .merchant-row {
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
    }
    .merchant-legend {
        list-style: none;
        margin: 0;
        padding: 0;
        flex: 1;
        min-width: 200px;
    }
    .merchant-legend li {
        display: grid;
        grid-template-columns: 12px minmax(0, 1fr) auto auto;
        gap: 8px;
        align-items: center;
        padding: 4px 0;
        font-size: 0.88rem;
    }
    .merchant-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
    }
    .merchant-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .merchant-spend { font-weight: 600; }
    .merchant-count { color: var(--text-secondary); font-size: 0.78rem; }
    .report-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .report-list li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        padding: 8px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .report-list-name {
        color: var(--text-primary);
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .report-list-name:hover { text-decoration: underline; color: var(--brand-primary); }
    .report-list-count {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-variant-numeric: tabular-nums;
    }
    .savings-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
    .savings-number {
        font-size: 2.4rem;
        font-weight: 700;
        color: var(--semantic-positive);
        letter-spacing: -0.02em;
    }
    .savings-sub { color: var(--text-secondary); font-size: 0.88rem; }
    .report-sparkline {
        width: 100%;
        height: 60px;
        margin-top: 12px;
    }
    .price-picker { margin-bottom: 12px; }
</style>
