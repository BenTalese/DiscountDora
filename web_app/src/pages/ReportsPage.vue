<template>
    <!-- FU-609 / R-036 — root on <q-page> for the layout height contract
         (document-scroll page; no :style-fn). -->
    <q-page class="reports-page">
        <header class="reports-header">
            <div class="reports-title-block">
                <h1 class="reports-title">Reports</h1>
                <p class="reports-sub">
                    Estimates pulled from your archived shopping lists, stock
                    history, and tracked store prices.
                </p>
            </div>
            <BaseSegmented
                v-model="range"
                :options="RANGE_OPTIONS"
                rounded
                dense
                color="grey"
                text-color="white"
                toggle-text-color="white"
                @update:model-value="loadAll"
            />
        </header>

        <div class="reports-grid">
            <!-- Stock value over time — money-gated (FU-816). -->
            <article v-if="moneyEnabled" class="report-card report-card-wide">
                <header class="report-card-head">
                    <q-icon :name="ICONS.show_chart" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Stock value over time</h3>
                    <span v-if="stockValue?.estimate_note" class="report-card-note">
                        <q-icon :name="ICONS.info" size="14px" />
                        {{ stockValue.estimate_note }}
                    </span>
                </header>
                <div v-if="loading.stockValue" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('stockValue')"
                    line="I couldn't load your stock value."
                    @retry="loadStockValue"
                />
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

            <!-- Spend by store (donut) — money-gated (FU-816). -->
            <article v-if="moneyEnabled" class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.donut_large" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Spend by store</h3>
                </header>
                <div v-if="loading.storeSpend" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('storeSpend')"
                    line="I couldn't load your spend by store."
                    @retry="loadStoreSpend"
                />
                <div v-else-if="(storeSpend?.rows.length ?? 0) > 0" class="store-row">
                    <v-chart
                        class="report-donut"
                        :option="storeSpendOption"
                        autoresize
                    />
                    <ul class="store-legend">
                        <li v-for="row in storeSpend!.rows" :key="row.store">
                            <span class="store-dot" :style="{ background: storeRowColour(row) }" />
                            <span class="store-name">{{ row.store }}</span>
                            <span class="store-spend">{{ formatMoney(row.spend) }}</span>
                            <span class="store-count">{{ row.list_count }} list{{ row.list_count === 1 ? '' : 's' }}</span>
                        </li>
                    </ul>
                </div>
                <div v-else class="report-empty">
                    No completed shopping lists in this range — finish a list to see
                    your spend break down by store.
                </div>
                <!-- R-041 — the total says what it was built from. Lines with no
                     price at all were dropped in silence, so the card undercounted
                     while the shopping list's own card stated the same gap. -->
                <div
                    v-if="(storeSpend?.unpriced_lines ?? 0) > 0"
                    class="report-card-note report-coverage"
                >
                    {{ storeSpend!.unpriced_lines }} item{{ storeSpend!.unpriced_lines === 1 ? '' : 's' }}
                    had no price recorded, so {{ storeSpend!.unpriced_lines === 1 ? "it isn't" : "they aren't" }} counted here.
                </div>
            </article>

            <!-- Most bought -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.trending_up" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Top 10 most-bought</h3>
                </header>
                <div v-if="loading.mostBought" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('mostBought')"
                    line="I couldn't load what you buy most."
                    @retry="loadMostBought"
                />
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
                    <BaseButton
                        v-if="(keepsOut?.rows.length ?? 0) > 0"
                        variant="ghost"
                        dense
                        size="sm"
                        :icon="ICONS.bookmark"
                        label="Mark all essential"
                        @click="markAllEssential"
                    />
                </header>
                <div v-if="loading.keepsOut" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('keepsOut')"
                    line="I couldn't load your run-outs."
                    @retry="loadKeepsOut"
                />
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

            <!-- Wastage log -->
            <article class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.wasted" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Wastage</h3>
                </header>
                <div v-if="loading.waste" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('waste')"
                    line="I couldn't load your wastage."
                    @retry="loadWaste"
                />
                <template v-else-if="waste">
                    <div class="waste-summary">
                        <span class="waste-total">{{ waste.total_events }}</span>
                        <span class="waste-sub">
                            item{{ waste.total_events === 1 ? '' : 's' }} logged
                            in the last {{ waste.window_days }} day{{ waste.window_days === 1 ? '' : 's' }}
                        </span>
                    </div>
                    <div class="waste-reason-grid">
                        <div
                            v-for="tile in wasteReasonTiles"
                            :key="tile.reason"
                            class="waste-reason-tile"
                            :class="{ 'is-zero': tile.count === 0 }"
                        >
                            <q-icon :name="tile.icon" size="20px" class="waste-reason-icon" />
                            <span class="waste-reason-count">{{ tile.count }}</span>
                            <span class="waste-reason-label">{{ tile.label }}</span>
                        </div>
                    </div>
                    <ul v-if="waste.most_wasted.length > 0" class="report-list">
                        <li
                            v-for="row in waste.most_wasted"
                            :key="row.stock_item_id ?? row.stock_item_name"
                        >
                            <a
                                v-if="row.stock_item_id"
                                class="report-list-name"
                                @click="goToStock(row.stock_item_id!)"
                            >
                                {{ row.stock_item_name }}
                            </a>
                            <span v-else class="report-list-name dora-text-muted">
                                {{ row.stock_item_name }}
                            </span>
                            <span class="report-list-count">×{{ row.event_count }}</span>
                        </li>
                    </ul>
                    <div v-else class="report-empty">
                        Nothing wasted in this range — nicely played.
                    </div>
                </template>
                <div v-else class="report-empty">
                    No wastage data available.
                </div>
            </article>

            <!-- Savings captured — needs money AND products (FU-816): the
                 figure is only ever non-zero if you pick product offers, so on
                 a products-free install this card is a permanent empty state
                 telling you to go and use a feature you opted out of (B9). -->
            <article v-if="productMoneyEnabled" class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.savings" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Savings captured</h3>
                </header>
                <div v-if="loading.savings" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('savings')"
                    line="I couldn't load your savings."
                    @retry="loadSavings"
                />
                <div v-else-if="savings && savings.total_spent > 0" class="savings-body">
                    <div class="savings-number">
                        {{ formatMoney(savings.total_savings) }}
                    </div>
                    <div class="savings-sub">
                        saved vs RRP on {{ formatMoney(savings.total_spent) }} spent
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
                    Finish a shopping list with picked store offers to start
                    tracking savings.
                </div>
            </article>

            <!-- ═══════ P8-09 memory section ══════════════════════════ -->
            <!-- Section divider. Full-width row so the "Memory" band
                 reads as a category header for the three cards below. -->
            <div class="reports-memory-band">
                <q-icon :name="ICONS.history" size="20px" />
                <span>Memory · what you actually did</span>
                <span class="reports-memory-band__hint">
                    Uses your own cook history + finished shopping lists.
                    Nothing invented.
                </span>
            </div>

            <!-- Meals cooked over time -->
            <article class="report-card report-card-wide">
                <header class="report-card-head">
                    <q-icon :name="ICONS.restaurant_menu" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Meals cooked</h3>
                    <span
                        v-if="mealsCooked && mealsCooked.cook_count > 0"
                        class="report-card-note"
                    >
                        {{ mealsCooked.cook_count }} cook{{ mealsCooked.cook_count === 1 ? '' : 's' }}
                        · {{ mealsCooked.meals_total }} meals-worth
                        <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                            <q-tooltip>
                                Total portions you cooked in this range, summed from
                                the "how many meals?" answer at the end of each cook.
                                Different from cook count — one cook can yield
                                several meals.
                            </q-tooltip>
                        </q-icon>
                    </span>
                </header>
                <div v-if="loading.mealsCooked" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('mealsCooked')"
                    line="I couldn't load your cook history."
                    @retry="loadMealsCooked"
                />
                <div
                    v-else-if="(mealsCooked?.cook_count ?? 0) > 0"
                    class="meals-cooked-body"
                >
                    <v-chart
                        v-if="(mealsCooked?.timeline.length ?? 0) > 0"
                        class="report-chart"
                        :option="mealsTimelineOption"
                        autoresize
                    />
                    <ul class="report-list meals-cooked-top">
                        <li
                            v-for="row in mealsCooked!.top_recipes"
                            :key="row.recipe_id ?? row.recipe_name"
                        >
                            <a
                                class="report-list-name"
                                @click="row.recipe_id && goToRecipe(row.recipe_id)"
                            >{{ row.recipe_name }}</a>
                            <span class="report-list-count">
                                ×{{ row.cook_count }} · {{ row.meals_total }} meals
                            </span>
                        </li>
                    </ul>
                </div>
                <div v-else class="report-empty">
                    No cooks logged in this range yet. Finish a recipe in
                    cook mode to start building your memory.
                </div>
            </article>

            <!-- Spend by category — money-gated (FU-816). -->
            <article v-if="moneyEnabled" class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.donut_large" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Spend by category</h3>
                    <span
                        v-if="spendByCategory && spendByCategory.total_spent > 0"
                        class="report-card-note"
                    >
                        {{ formatMoney(spendByCategory.total_spent) }} total
                    </span>
                </header>
                <div v-if="loading.spendByCategory" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('spendByCategory')"
                    line="I couldn't load your spend by category."
                    @retry="loadSpendByCategory"
                />
                <div
                    v-else-if="(spendByCategory?.rows.length ?? 0) > 0"
                    class="store-row"
                >
                    <v-chart
                        class="report-donut"
                        :option="spendByCategoryOption"
                        autoresize
                    />
                    <ul class="store-legend">
                        <li v-for="row in spendByCategory!.rows" :key="row.category">
                            <span class="store-dot" :style="{ background: colourFor(row.category) }" />
                            <span class="store-name">{{ row.category }}</span>
                            <span class="store-spend">{{ formatMoney(row.spent) }}</span>
                            <span class="store-count">{{ row.share_pct }}%</span>
                        </li>
                    </ul>
                </div>
                <div v-else class="report-empty">
                    No spend recorded in this range yet. Finish a shopping
                    list with prices to see where your money's going.
                </div>
            </article>

            <!-- Year-over-year spend — money-gated (FU-816). -->
            <article v-if="moneyEnabled" class="report-card">
                <header class="report-card-head">
                    <q-icon :name="ICONS.compare_arrows" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">
                        Year-over-year
                        <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                            <q-tooltip>
                                This window's total spend compared to the same-length
                                window a year earlier — so a 90-day view compares this
                                90 days to the matching 90 days last year.
                            </q-tooltip>
                        </q-icon>
                    </h3>
                    <span v-if="spendYoY" class="report-card-note">
                        this
                        <template v-if="range === '30d'">30 days</template>
                        <template v-else-if="range === '90d'">90 days</template>
                        <template v-else-if="range === '1y'">year</template>
                        <template v-else-if="range === '2y'">2 years</template>
                        <template v-else-if="range === '5y'">5 years</template>
                        vs. prior
                    </span>
                </header>
                <div v-if="loading.spendYoY" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('spendYoY')"
                    line="I couldn't load the year-over-year comparison."
                    @retry="loadSpendYoY"
                />
                <div v-else-if="range === 'all'" class="report-empty">
                    Pick a bounded range (30d–5y) to compare it against
                    the same-length prior window.
                </div>
                <div
                    v-else-if="spendYoY && (spendYoY.current_total > 0 || spendYoY.previous_total > 0)"
                    class="yoy-body"
                >
                    <div class="yoy-total">
                        <div class="yoy-total__current">
                            {{ formatMoney(spendYoY.current_total) }}
                        </div>
                        <div class="yoy-total__delta">
                            <template v-if="spendYoY.delta_pct === null">
                                (no prior data)
                            </template>
                            <template v-else>
                                <span
                                    :class="spendYoY.delta > 0 ? 'yoy-up' : (spendYoY.delta < 0 ? 'yoy-down' : '')"
                                >
                                    {{ spendYoY.delta_pct > 0 ? '+' : '' }}{{ spendYoY.delta_pct }}%
                                </span>
                                vs. {{ formatMoney(spendYoY.previous_total) }}
                            </template>
                        </div>
                    </div>
                    <ul class="yoy-rows">
                        <li v-for="row in spendYoY.rows.slice(0, 8)" :key="row.category">
                            <span class="yoy-cat">{{ row.category }}</span>
                            <span
                                class="yoy-delta"
                                :class="row.delta > 0 ? 'yoy-up' : (row.delta < 0 ? 'yoy-down' : '')"
                            >
                                <template v-if="row.delta_pct === null">new</template>
                                <template v-else>
                                    {{ row.delta_pct > 0 ? '+' : '' }}{{ row.delta_pct }}%
                                </template>
                            </span>
                            <span class="yoy-amount">
                                {{ formatMoney(row.current) }}
                                <span class="yoy-prev">vs {{ formatMoney(row.previous) }}</span>
                            </span>
                        </li>
                    </ul>
                </div>
                <div v-else class="report-empty">
                    Not enough history yet to compare periods. Finish
                    lists over time and this fills in.
                </div>
            </article>

            <!-- Price trends — needs money AND products (FU-816). -->
            <article v-if="productMoneyEnabled" class="report-card report-card-wide">
                <header class="report-card-head">
                    <q-icon :name="ICONS.query_stats" size="22px" class="report-card-icon" />
                    <h3 class="report-card-title">Price trends</h3>
                </header>
                <div class="price-picker">
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
                        @filter="filterProducts"
                        @update:model-value="onProductSelection"
                    />
                </div>
                <div v-if="loading.priceTrends" class="report-card-loading">
                    <AppSpinner size="32px" />
                </div>
                <CardLoadError
                    v-else-if="slotFailed('priceTrends')"
                    line="I couldn't load these price trends."
                    @retry="loadPriceTrends"
                />
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
    </q-page>
</template>

<script lang="ts" setup>
    import AppSpinner from 'src/components/AppSpinner.vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import { formatMoney } from 'src/composables/useMoney';
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
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import ProductApiService from 'src/services/api/productApiService';
    import { storeColour } from 'src/style/storeSwatch';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import ReportsApiService, {
        type KeepsRunningOutResponse,
        type StoreSpendResponse,
        type MostBoughtResponse,
        type PriceTrendsResponse,
        type ReportRange,
        type SavingsCapturedResponse,
        type StockValueResponse,
        type MealsCookedResponse,
        type SpendByCategoryResponse,
        type SpendYoYResponse,
        type YoYReportRange,
    } from 'src/services/api/reportsApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import WasteApiService, { type WasteInsights } from 'src/services/api/wasteApiService';
    import { computed, onMounted, ref, watch } from 'vue';
    // FU-824 — reactive theme-token reads; replaces the dead `themeTick` ref.
    import { paletteToken } from 'src/composables/useThemePalette';
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
    const stockApi = new StockItemApiService();
    const wasteApi = new WasteApiService();
    // The picker searches the catalogue server-side rather than filtering a
    // hydrated page in the browser, so it talks to the API service directly —
    // there is no shared client-side product collection left to keep in sync.
    const productApi = new ProductApiService();

    const RANGE_OPTIONS: { label: string; value: ReportRange }[] = [
        { label: '30 days', value: '30d' },
        { label: '90 days', value: '90d' },
        { label: '1 year', value: '1y' },
        // multi-year windows unlock the culinary-memory section
        // ("what did we cook in the last two years", "how has dairy
        // trended over 5 years").
        { label: '2 years', value: '2y' },
        { label: '5 years', value: '5y' },
        { label: 'All time', value: 'all' },
    ];

    const range = ref<ReportRange>('30d');

    // ── Feature gates (FU-816) ───────────────────────────────────────────
    // This page imported no feature flag at all, so an install that had turned
    // money off still got spend by store, savings, spend by category,
    // year-over-year, price trends and two dollar-formatted chart axes — the
    // one significant surface in the app still contradicting the owner's own
    // "money must be switchable off" feedback. The endpoints refuse with 403
    // now too (R-058); these gates stop us asking.
    //
    // The nav entry stays unconditional on purpose: most-bought,
    // keeps-running-out, wastage and meals-cooked are all count-based and
    // survive a money-off install, so hiding the page would cost four working
    // reports to gate six.
    const { moneyEnabled } = useMoneyEnabled();
    const { products: productsEnabled } = useFeatureFlags();
    // Savings and price trends need both: savings is only ever non-zero if you
    // pick product offers, and price trends charts products by definition. B9
    // — don't render a card whose empty state tells the user to go and use a
    // feature they opted out of.
    const productMoneyEnabled = computed(
        () => moneyEnabled.value && productsEnabled.value,
    );

    const loading = ref({
        stockValue: false,
        storeSpend: false,
        mostBought: false,
        keepsOut: false,
        savings: false,
        priceTrends: false,
        mealsCooked: false,
        spendByCategory: false,
        spendYoY: false,
        waste: false,
    });

    const stockValue = ref<StockValueResponse | null>(null);
    const storeSpend = ref<StoreSpendResponse | null>(null);
    const mostBought = ref<MostBoughtResponse | null>(null);
    const keepsOut = ref<KeepsRunningOutResponse | null>(null);
    const savings = ref<SavingsCapturedResponse | null>(null);
    const priceTrends = ref<PriceTrendsResponse | null>(null);
    // read from the range picker like every other card.
    const mealsCooked = ref<MealsCookedResponse | null>(null);
    const spendByCategory = ref<SpendByCategoryResponse | null>(null);
    // YoY only accepts bounded windows; if the user picks "All time",
    // we skip the YoY fetch and the card renders its own explanation.
    const spendYoY = ref<SpendYoYResponse | null>(null);
    // Waste log — always reported over a day-count window; the API caps at
    // 365, so a "2y"/"5y"/"all" pick from the shared range picker still
    // shows the last year of wastage. The card subtitle uses the effective
    // window returned by the server so what you see matches what's real.
    const waste = ref<WasteInsights | null>(null);

    // ── Per-card failure (REPORTS_PAGE_REVIEW.md finding 8) ──────────────
    // Every loader used to let a failed fetch fall through to the card's EMPTY
    // state, so a 500 on the waste endpoint rendered "Nothing wasted in this
    // range — nicely played" and a failed spend fetch rendered "no completed
    // shopping lists". The page congratulated you on data it could not load.
    // Same fix, same component and same reasoning as the dashboard's Chunk 4:
    // failure is visible, per-card, and retryable where it happened.
    type SlotId = keyof typeof loading.value;
    const slotErrors = ref<Set<SlotId>>(new Set());
    function slotFailed(id: SlotId): boolean {
        return slotErrors.value.has(id);
    }
    /** Run one card's fetch, recording success or failure against its id.
     *  Never throws — one bad card must not take the page down, which is what
     *  the old blanket catch was protecting; the difference is that the failure
     *  is no longer laundered into an empty state. */
    async function loadSlot(id: SlotId, run: () => Promise<void>): Promise<void> {
        loading.value[id] = true;
        try {
            await run();
            if (slotErrors.value.has(id)) {
                const next = new Set(slotErrors.value);
                next.delete(id);
                slotErrors.value = next;
            }
        } catch (err) {
            // Logged, not swallowed: the console is how a self-hosting owner
            // finds out which endpoint is unhappy.
            console.warn(`reports card "${id}" failed to load`, err);
            const next = new Set(slotErrors.value);
            next.add(id);
            slotErrors.value = next;
        } finally {
            loading.value[id] = false;
        }
    }

    const selectedProductIds = ref<string[]>([]);
    const productOptions = ref<{ label: string; value: string }[]>([]);

    // FU-668, third instance. This used to filter `allProducts` — the store's
    // hydrated first page — in the browser, and `GET /products` is paginated at
    // 50, so product 51 onward was unsearchable with nothing on screen saying
    // so. The needle now goes to the server. Store name is no longer part of
    // the match (it lives on the Store row, not the Product), which is the one
    // capability traded for seeing the whole catalogue.
    async function filterProducts(input: string, doneFn: (cb: () => void) => void) {
        let matches: { label: string; value: string }[] = [];
        try {
            const page = await productApi.searchAsync(input, 20);
            matches = page.items.map((p) => ({
                label: `${p.name} · ${p.store_name}`,
                value: p.product_id,
            }));
        } catch (err) {
            console.warn('product search failed', err);
        }
        doneFn(() => { productOptions.value = matches; });
    }

    // ── Chart options ────────────────────────────────────────────────────
    // Pull the active theme's chart palette + brand colours from the document
    // so charts re-paint when the user switches theme.
    //
    // FU-824: this used to claim it recomputed "on `themeTick` bumps (triggered
    // by the route nav + manual reload)". `themeTick` was declared, read here,
    // and **never incremented anywhere in the repo** — so the palette was
    // sampled once and frozen, and switching theme on this page left every
    // chart on the old theme's colours. The ref is gone; `paletteToken` now
    // carries a real dependency on the theme version, bumped by
    // `themeService.applyThemeKey`.
    //
    // CSS custom properties return their literal stored value — modern
    // `hsl(h s% l%)` syntax for our tokens. Normalise through a canvas
    // so chart libraries always see a canonical hex/rgba string.
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
        const read = (name: string, fallback: string) =>
            normaliseColour(paletteToken(name, fallback));
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

    /** Categorical colour for a bucket that has no colour of its own — a stock
     *  group, in practice. Deterministic so a group keeps its hue between
     *  renders.
     *
     *  FU-814 item 2: this used to colour **stores** as well, hashing the store
     *  name into the chart ramp, so Woolworths was its logo green on the
     *  shopping list and whatever the hash landed on here. Stores now go
     *  through `storeColour`, whose own header comment documents this exact bug
     *  being fixed for the other two consumers. Do not put a store back in
     *  here. */
    function colourFor(key: string): string {
        let hash = 0;
        for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) | 0;
        const series = chartPalette.value.series;
        return series[Math.abs(hash) % series.length]!;
    }

    /** The one store-colour authority, shared with `StoreLogo` and the shopping
     *  list's spend card: the logo's brand colour first, a deterministic name
     *  hash only as a fallback.
     *
     *  The **no-store bucket is not a store** and must not be handed a store
     *  identity colour — driving this live, the "No store set" row drew the
     *  same slate as the farmers market directly above it, because the hash
     *  palette is a sealed six and two names can land on one entry. The
     *  shopping list solves the same problem with a hatched grey (D-001: never
     *  distinguish by hue alone); here it takes the muted text token, which is
     *  visibly not one of the identity hues. Full parity with the hatch comes
     *  when the donut is replaced by that card's bar (§4.6, chunk 3). */
    function storeRowColour(
        row: { store_id: string | null; store: string; brand_colour: string | null },
    ): string {
        // Resolved, not a `var()` string: the same function feeds the donut,
        // and a canvas fill cannot resolve a custom property.
        if (row.store_id === null) {
            return normaliseColour(paletteToken('--text-muted', '#6b7280'));
        }
        return storeColour(row.store, row.brand_colour);
    }

    const stockValueOption = computed(() => ({
        tooltip: { trigger: 'axis', valueFormatter: (v: number) => formatMoney(v) },
        grid: { left: 50, right: 16, top: 24, bottom: 32 },
        xAxis: {
            type: 'category',
            data: stockValue.value?.points.map((p) => p.date) ?? [],
            axisLabel: { fontSize: 10 },
        },
        // R-003 / D-006 — one money-formatting authority. A hard-coded `$`
        // prefix here gave a non-AUD install correct legends and lying axes.
        yAxis: {
            type: 'value',
            axisLabel: { formatter: (value: number) => formatMoney(value) },
        },
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

    const storeSpendOption = computed(() => ({
        tooltip: { trigger: 'item', valueFormatter: (v: number) => formatMoney(v) },
        series: [{
            type: 'pie',
            radius: ['55%', '80%'],
            avoidLabelOverlap: true,
            label: { show: false },
            data: (storeSpend.value?.rows ?? []).map((row) => ({
                name: row.store,
                value: row.spend,
                itemStyle: { color: storeRowColour(row) },
            })),
        }],
    }));

    const savingsSparkOption = computed(() => ({
        grid: { left: 0, right: 0, top: 4, bottom: 4 },
        xAxis: { type: 'category', show: false, data: savings.value?.lists.map((l) => l.name) ?? [] },
        yAxis: { type: 'value', show: false },
        tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${formatMoney(v)} saved` },
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

    // ── P8-09 memory chart options ──────────────────────────────────
    const mealsTimelineOption = computed(() => ({
        tooltip: {
            trigger: 'axis',
            formatter: (rows: Array<{ data: number; axisValueLabel?: string }>) => {
                if (!rows.length) return '';
                const row = rows[0]!;
                return `${row.axisValueLabel ?? ''}<br/>${row.data} cook${row.data === 1 ? '' : 's'}`;
            },
        },
        grid: { left: 40, right: 16, top: 24, bottom: 32 },
        xAxis: {
            type: 'category',
            data: mealsCooked.value?.timeline.map((p) => p.date) ?? [],
            axisLabel: { fontSize: 10 },
        },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            type: 'line',
            smooth: true,
            symbol: 'none',
            areaStyle: { opacity: 0.15 },
            lineStyle: { width: 2 },
            data: mealsCooked.value?.timeline.map((p) => p.cook_count) ?? [],
            color: chartPalette.value.primary,
        }],
    }));

    const spendByCategoryOption = computed(() => ({
        tooltip: {
            trigger: 'item',
            valueFormatter: (v: number) => formatMoney(v),
        },
        series: [{
            type: 'pie',
            radius: ['55%', '80%'],
            avoidLabelOverlap: true,
            label: { show: false },
            data: (spendByCategory.value?.rows ?? []).map((row) => ({
                name: row.category,
                value: row.spent,
                itemStyle: { color: colourFor(row.category) },
            })),
        }],
    }));

    const priceTrendsOption = computed(() => {
        const series = priceTrends.value?.series ?? [];
        const allDates = new Set<string>();
        for (const s of series) for (const p of s.points) allDates.add(p.date);
        const dates = [...allDates].sort();
        return {
            tooltip: { trigger: 'axis', valueFormatter: (v: number) => v == null ? '—' : formatMoney(v) },
            legend: { bottom: 0, type: 'scroll' },
            grid: { left: 50, right: 16, top: 24, bottom: 40 },
            xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10 } },
            // R-003 / D-006 — one money-formatting authority. A hard-coded `$`
        // prefix here gave a non-AUD install correct legends and lying axes.
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

    // ── Loaders ──────────────────────────────────────────────────────────
    // A gated-off card must not fetch: the endpoint would 403 (R-058) and the
    // card would render a load failure for a report the install deliberately
    // does not have.
    async function loadStockValue() {
        if (!moneyEnabled.value) { stockValue.value = null; return; }
        await loadSlot('stockValue', async () => {
            stockValue.value = await reportsApi.getStockValueAsync(range.value);
        });
    }
    async function loadStoreSpend() {
        if (!moneyEnabled.value) { storeSpend.value = null; return; }
        await loadSlot('storeSpend', async () => {
            storeSpend.value = await reportsApi.getSpendByStoreAsync(range.value);
        });
    }
    async function loadMostBought() {
        await loadSlot('mostBought', async () => {
            mostBought.value = await reportsApi.getMostBoughtAsync(range.value);
        });
    }
    async function loadKeepsOut() {
        // Passes the page's range now (§3.5 / D7) — the card sat under a
        // control saying "30 days" while counting all history, forever.
        await loadSlot('keepsOut', async () => {
            keepsOut.value = await reportsApi.getKeepsRunningOutAsync(10, range.value);
        });
    }
    async function loadSavings() {
        if (!productMoneyEnabled.value) { savings.value = null; return; }
        await loadSlot('savings', async () => {
            savings.value = await reportsApi.getSavingsCapturedAsync(range.value);
        });
    }
    async function loadPriceTrends() {
        if (!productMoneyEnabled.value) { priceTrends.value = null; return; }
        if (selectedProductIds.value.length === 0) {
            priceTrends.value = null;
            return;
        }
        await loadSlot('priceTrends', async () => {
            priceTrends.value = await reportsApi.getPriceTrendsAsync(
                selectedProductIds.value, range.value,
            );
        });
    }
    /** `clearable` on a `multiple` q-select emits `null`, not `[]`, and the old
     *  handler read `.length` off it on the next line — clicking the clear
     *  affordance threw. Normalise at the boundary rather than making every
     *  reader null-aware. */
    function onProductSelection(value: string[] | null) {
        selectedProductIds.value = value ?? [];
        void loadPriceTrends();
    }
    async function loadProductsCatalogue() {
        // Seeds the picker before the user types. Empty needle ⇒ the server's
        // first page, same as any other search.
        await filterProducts('', (assign) => assign());
    }

    // ── P8-09 memory loaders ────────────────────────────────────────
    async function loadMealsCooked() {
        await loadSlot('mealsCooked', async () => {
            mealsCooked.value = await reportsApi.getMealsCookedAsync(range.value, 10);
        });
    }
    async function loadSpendByCategory() {
        if (!moneyEnabled.value) { spendByCategory.value = null; return; }
        await loadSlot('spendByCategory', async () => {
            spendByCategory.value = await reportsApi.getSpendByCategoryAsync(range.value);
        });
    }
    // Reason tiles for the Wastage card — one per canonical waste reason.
    // Zero-count tiles still render (dimmed) so the grid stays a stable
    // shape and "you haven't logged any of these" reads as intentional.
    const WASTE_REASON_TILES: {
        reason: 'expired' | 'spoiled' | 'did_not_like' | 'overbought' | 'other';
        label: string;
        icon: string;
    }[] = [
        { reason: 'expired', label: 'Expired', icon: ICONS.wasteExpired },
        { reason: 'spoiled', label: 'Spoiled', icon: ICONS.wasteSpoiled },
        { reason: 'did_not_like', label: "Didn't like", icon: ICONS.wasteDidNotLike },
        { reason: 'overbought', label: 'Overbought', icon: ICONS.wasteOverbought },
        { reason: 'other', label: 'Other', icon: ICONS.wasteOther },
    ];
    const wasteReasonTiles = computed(() =>
        WASTE_REASON_TILES.map((t) => ({
            ...t,
            count: waste.value?.by_reason[t.reason] ?? 0,
        })),
    );

    const RANGE_TO_DAYS: Record<ReportRange, number> = {
        '30d': 30, '90d': 90, '1y': 365, '2y': 730, '5y': 1825, 'all': 3650,
    };
    async function loadWaste() {
        await loadSlot('waste', async () => {
            waste.value = await wasteApi.getInsightsAsync(RANGE_TO_DAYS[range.value]);
        });
    }
    async function loadSpendYoY() {
        if (!moneyEnabled.value) { spendYoY.value = null; return; }
        // YoY skips the "all" range — it needs a bounded window to
        // compare against the same-length prior window. Blank the card
        // when the user's chosen "all" so it can render an explanation.
        if (range.value === 'all') {
            spendYoY.value = null;
            return;
        }
        await loadSlot('spendYoY', async () => {
            spendYoY.value = await reportsApi.getSpendYearOverYearAsync(
                range.value as YoYReportRange,
            );
        });
    }

    // No page-level error banner: each loader records its own failure, so the
    // reader can see exactly which parts of the page to trust. A banner over
    // ten cards said "something here is wrong" without saying what, while the
    // failed card underneath still read as empty.
    async function loadAll() {
        await Promise.all([
            loadStockValue(),
            loadStoreSpend(),
            loadMostBought(),
            loadKeepsOut(),
            loadSavings(),
            loadPriceTrends(),
            loadMealsCooked(),
            loadSpendByCategory(),
            loadSpendYoY(),
            loadWaste(),
        ]);
    }

    function goToStock(id: string) {
        void router.push(`/stock/${id}`);
    }

    function goToRecipe(id: string) {
        // Cookbook detail; the top-recipes list from meals-cooked links
        // straight into it so "what did I cook a lot?" → "open it".
        void router.push(`/cookbook/${id}`);
    }

    async function markAllEssential() {
        const ids = (keepsOut.value?.rows ?? []).map((r) => r.stock_item_id);
        if (ids.length === 0) return;
        try {
            await Promise.all(ids.map((id) => stockApi.updateAsync({ stock_item_id: id, is_essential: true })));
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

    // FU-586's failure mode, found in the browser on this page's first live
    // run: the gates read the once-per-document `/api/health` probe, which had
    // NOT resolved when the page mounted — so every gated loader early-returned
    // and only the three count-based reports fetched, while the money cards
    // rendered their *empty* state as if the household had never shopped.
    // Nothing re-ran them when the flags landed. The dashboard hit this exactly
    // once before and fixed it the same way; re-fire only the gated loaders on
    // a gate turning on. On a warm navigation the gate is already true at
    // mount, `loadAll` fetches normally, and these never fire.
    watch(moneyEnabled, (on) => {
        if (!on) return;
        void loadStockValue();
        void loadStoreSpend();
        void loadSpendByCategory();
        void loadSpendYoY();
    });
    watch(productMoneyEnabled, (on) => {
        if (!on) return;
        void loadSavings();
        void loadPriceTrends();
    });

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
    .store-row {
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
    }
    .store-legend {
        list-style: none;
        margin: 0;
        padding: 0;
        flex: 1;
        min-width: 200px;
    }
    .store-legend li {
        display: grid;
        grid-template-columns: 12px minmax(0, 1fr) auto auto;
        gap: 8px;
        align-items: center;
        padding: 4px 0;
        font-size: 0.88rem;
    }
    .store-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
    }
    .store-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .store-spend { font-weight: 600; }
    .store-count { color: var(--text-secondary); font-size: 0.78rem; }
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
    .waste-summary {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin: 4px 0 12px;
    }
    .waste-total {
        font-size: 1.8rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        color: var(--text-primary);
    }
    .waste-sub { color: var(--text-secondary); font-size: 0.85rem; }
    .waste-reason-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
        margin-bottom: 12px;
    }
    @media (max-width: 640px) {
        .waste-reason-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    .waste-reason-tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 10px 6px;
        background: var(--surface-elevated);
        border-radius: 10px;
        aspect-ratio: 1;
        text-align: center;
    }
    .waste-reason-tile.is-zero { opacity: 0.45; }
    .waste-reason-icon { color: var(--brand-primary); }
    .waste-reason-tile.is-zero .waste-reason-icon { color: var(--text-secondary); }
    .waste-reason-count {
        font-size: 1.2rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        color: var(--text-primary);
    }
    .waste-reason-label {
        font-size: 0.72rem;
        color: var(--text-secondary);
        line-height: 1.15;
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
    /* R-041 coverage note — sits under the card body, not inside it. */
    .report-coverage { margin-top: 12px; }

    /* P8-09 memory section ─────────────────────────────────────── */
    .reports-memory-band {
        grid-column: 1 / -1;
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-top: 12px;
        padding: 8px 12px;
        /* R-060: `--border-subtle` is undeclared, so this always fired its
           hard-coded fallback — a black wash that reads wrong in a dark theme
           (R-002). A6: an in-card separator is `--divider`. */
        border-top: 1px solid var(--divider);
        color: var(--text-primary);
        font-weight: 600;
        font-size: 0.95rem;
    }
    .reports-memory-band__hint {
        color: var(--text-secondary);
        font-weight: 400;
        font-size: 0.85rem;
    }
    .meals-cooked-body {
        display: grid;
        grid-template-columns: minmax(0, 2fr) minmax(200px, 1fr);
        gap: 16px;
        align-items: start;
    }
    @media (max-width: 900px) {
        .meals-cooked-body { grid-template-columns: 1fr; }
    }
    .meals-cooked-top {
        margin: 0;
        padding: 0;
        list-style: none;
        max-height: 240px;
        overflow-y: auto;
    }
    .yoy-body {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .yoy-total {
        display: flex;
        align-items: baseline;
        gap: 12px;
    }
    .yoy-total__current {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .yoy-total__delta {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    .yoy-rows {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .yoy-rows li {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        gap: 12px;
        align-items: baseline;
        font-size: 0.9rem;
    }
    .yoy-cat { color: var(--text-primary); }
    .yoy-delta {
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }
    .yoy-up { color: var(--semantic-negative, #b43c3c); }
    .yoy-down { color: var(--semantic-positive, #228b22); }
    .yoy-amount {
        color: var(--text-secondary);
        font-variant-numeric: tabular-nums;
    }
    .yoy-prev {
        opacity: 0.65;
        margin-left: 4px;
    }
</style>
