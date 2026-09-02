<template>
    <!-- FU-609 / R-036 — root on <q-page> for the layout height contract
         (document-scroll page; no :style-fn). -->
    <q-page class="reports-page">
        <header class="reports-header">
            <div class="reports-title-block">
                <h1 class="reports-title">Reports</h1>
                <!-- §4.10.1 — the page opens with the answer, not the caveat.
                     The "estimates pulled from…" disclaimer that used to sit
                     here is now an info icon beside the range control. -->
                <ReportsLede
                    v-if="moneyEnabled"
                    :range="range"
                    :store-spend="storeSpend"
                    :spendYoY="spendYoY"
                />
            </div>
            <div class="reports-range">
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
                <q-icon :name="ICONS.info" size="18px" class="reports-caveat">
                    <q-tooltip>
                        Built from your archived shopping lists, stock history and
                        tracked store prices. Estimates, not accounting.
                    </q-tooltip>
                </q-icon>
            </div>
        </header>

        <div class="reports-grid">
            <!-- Money-gated (FU-816). Merges what were three cards — spend by
                 store, spend by category and year-over-year — into one question
                 with an axis control (§5). -->
            <div v-if="moneyEnabled" class="reports-grid__wide">
                <SpendCard
                    :range="range"
                    :store-spend="storeSpend"
                    :spend-by-category="spendByCategory"
                    :spendYoY="spendYoY"
                    :savings="savings"
                    :colour-for="colourFor"
                    :failed="spendFailed"
                    @retry="loadSpend"
                />
            </div>

            <WasteAndRunOutsCard
                :waste="waste"
                :keeps-out="keepsOut"
                :waste-failed="slotFailed('waste')"
                :run-outs-failed="slotFailed('keepsOut')"
                @retry-waste="loadWaste"
                @retry-run-outs="loadKeepsOut"
            />

            <KitchenMemoryCard
                :range="range"
                :meals-cooked="mealsCooked"
                :most-bought="mostBought"
                :cooks-failed="slotFailed('mealsCooked')"
                :bought-failed="slotFailed('mostBought')"
                @retry-cooks="loadMealsCooked"
                @retry-bought="loadMostBought"
            />

            <!-- Chunk 4 / FU-703 D3 — the everyday-user price report, built
                 from your own logged prices. Money-gated but NOT products-gated:
                 it is the price trend an install with an empty catalogue can
                 still have, which is the whole reason it exists. -->
            <!-- Full width, and D-011 is why: it holds two lists side by side
                 *and* opens a chart under them, so at half width it stranded an
                 empty column beside itself — the same dead-air rule the
                 dashboard's own grid was fixed for (FU-631 #3). Measured in the
                 browser, not reasoned about. -->
            <div v-if="moneyEnabled" class="reports-grid__wide">
                <ItemPriceMoversCard
                    :range="range"
                    :movers="itemMovers"
                    :failed="slotFailed('itemMovers')"
                    @retry="loadItemMovers"
                />
            </div>

            <!-- Needs money AND products: the chart is products by definition,
                 and it answers in dollars. -->
            <div v-if="productMoneyEnabled" class="reports-grid__wide">
                <PriceTrendsCard
                    :price-trends="priceTrends"
                    :product-options="productOptions"
                    :selected-product-ids="selectedProductIds"
                    :loading="loading.priceTrends"
                    :failed="slotFailed('priceTrends')"
                    @retry="loadPriceTrends"
                    @select="onProductSelection"
                    @filter="filterProducts"
                />
            </div>
        </div>
    </q-page>
</template>

<script lang="ts" setup>
    /**
     * `/reports` — four questions, one card each.
     *
     * ## What this page is now
     *
     * `REPORTS_PAGE_REVIEW.md` §5: eleven widgets answered four questions, and
     * three of them were the same query sliced three ways. The card set is now
     * question-led — where did my money go (Spend), what am I mismanaging (Waste
     * & run-outs), what do we actually eat (Kitchen memory), what am I paying
     * more for (Price changes), is this worth buying (Price trends) — plus a
     * lede sentence that gives the answer before the instruments do.
     *
     * **Added in chunk 4:** Price changes, the report §5 called the largest
     * missing widget on the page — the everyday user's own
     * `StockItemPriceObservation` history had no trend surface anywhere in the
     * app, while Price trends charted a product catalogue most installs never
     * populate (FU-703 D3).
     *
     * **Cut in chunk 3:** stock value over time. Its formula was a 0–5 level
     * *ordinal* multiplied by a price, which is not a dollar figure at all, and
     * it systematically undercounted because every unpriced item contributed
     * zero (§3.3). The endpoint survives for the dashboard's opt-in
     * `pantry_value` card; only the card here is gone.
     *
     * ## What this file owns
     *
     * Data and gates, not presentation. Every card body lives in
     * `components/reports/` (R-001) and the shell is the shared `DashboardCard`,
     * so the ~60-line byte-identical fork of it that used to live here — and had
     * already drifted, losing the hover, the reduced-motion guard and the
     * router-link variant — is gone (FU-814 item 1).
     */
    import { computed, onMounted, ref, watch } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import ItemPriceMoversCard from 'src/components/reports/ItemPriceMoversCard.vue';
    import KitchenMemoryCard from 'src/components/reports/KitchenMemoryCard.vue';
    import PriceTrendsCard from 'src/components/reports/PriceTrendsCard.vue';
    import ReportsLede from 'src/components/reports/ReportsLede.vue';
    import SpendCard from 'src/components/reports/SpendCard.vue';
    import WasteAndRunOutsCard from 'src/components/reports/WasteAndRunOutsCard.vue';
    import ProductApiService from 'src/services/api/productApiService';
    import { paletteToken } from 'src/composables/useThemePalette';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import ReportsApiService, {
        type KeepsRunningOutResponse,
        type StoreSpendResponse,
        type MostBoughtResponse,
        type PriceTrendsResponse,
        type ItemPriceMoversResponse,
        type ReportRange,
        type SavingsCapturedResponse,
        type MealsCookedResponse,
        type SpendByCategoryResponse,
        type SpendYoYResponse,
        type YoYReportRange,
    } from 'src/services/api/reportsApiService';
    import WasteApiService, { type WasteInsights } from 'src/services/api/wasteApiService';

    const reportsApi = new ReportsApiService();
    const wasteApi = new WasteApiService();
    // The picker searches the catalogue server-side rather than filtering a
    // hydrated page in the browser, so there is no shared client-side product
    // collection left to keep in sync.
    const productApi = new ProductApiService();

    const RANGE_OPTIONS: { label: string; value: ReportRange }[] = [
        { label: '30 days', value: '30d' },
        { label: '90 days', value: '90d' },
        { label: '1 year', value: '1y' },
        // multi-year windows unlock the culinary-memory questions ("what did we
        // cook in the last two years", "how has dairy trended over 5 years").
        { label: '2 years', value: '2y' },
        { label: '5 years', value: '5y' },
        { label: 'All time', value: 'all' },
    ];

    const range = ref<ReportRange>('30d');

    // ── Feature gates (FU-816) ───────────────────────────────────────────
    // This page imported no feature flag at all, so an install that had turned
    // money off still got spend by store, savings, spend by category,
    // year-over-year, price trends and two dollar-formatted chart axes. The
    // endpoints refuse with 403 now too (R-058); these gates stop us asking.
    //
    // The nav entry stays unconditional on purpose: Waste & run-outs and Kitchen
    // memory are both count-based and survive a money-off install, so hiding the
    // page would cost two working reports to gate two.
    const { moneyEnabled } = useMoneyEnabled();
    const { products: productsEnabled } = useFeatureFlags();
    const productMoneyEnabled = computed(
        () => moneyEnabled.value && productsEnabled.value,
    );

    const loading = ref({
        storeSpend: false,
        mostBought: false,
        keepsOut: false,
        savings: false,
        priceTrends: false,
        mealsCooked: false,
        spendByCategory: false,
        spendYoY: false,
        waste: false,
        itemMovers: false,
    });

    const storeSpend = ref<StoreSpendResponse | null>(null);
    const mostBought = ref<MostBoughtResponse | null>(null);
    const keepsOut = ref<KeepsRunningOutResponse | null>(null);
    const savings = ref<SavingsCapturedResponse | null>(null);
    const priceTrends = ref<PriceTrendsResponse | null>(null);
    const mealsCooked = ref<MealsCookedResponse | null>(null);
    const spendByCategory = ref<SpendByCategoryResponse | null>(null);
    // YoY only accepts bounded windows; on "All time" we skip the fetch and the
    // card's compare axis renders its own explanation.
    const spendYoY = ref<SpendYoYResponse | null>(null);
    // Waste is always reported over a day-count window; the API caps at 365, so
    // a 2y/5y/all pick still shows the last year. The card's caption uses the
    // effective window the server returned, so what you read is what's real.
    const waste = ref<WasteInsights | null>(null);
    // Chunk 4 — movement in the prices you logged yourself, per canonical unit.
    const itemMovers = ref<ItemPriceMoversResponse | null>(null);

    // ── Per-card failure (REPORTS_PAGE_REVIEW.md finding 8) ──────────────
    // Every loader used to let a failed fetch fall through to the card's EMPTY
    // state, so a 500 on the waste endpoint rendered "Nothing wasted in this
    // range — nicely played". Same fix, same component and same reasoning as the
    // dashboard's Chunk 4: failure is visible, per-card, and retryable where it
    // happened.
    type SlotId = keyof typeof loading.value;
    const slotErrors = ref<Set<SlotId>>(new Set());
    function slotFailed(id: SlotId): boolean {
        return slotErrors.value.has(id);
    }
    /** Run one card's fetch, recording success or failure against its id. Never
     *  throws — one bad card must not take the page down, which is what the old
     *  blanket catch was protecting; the difference is that the failure is no
     *  longer laundered into an empty state. */
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

    /** The Spend card draws three endpoints, so it fails as one thing: a card
     *  that renders an axis toggle can't tell the reader "two thirds of me are
     *  trustworthy". Any of the three failing puts the whole card in the error
     *  state, and Try again re-fetches all three. */
    const spendFailed = computed(
        () => slotFailed('storeSpend')
            || slotFailed('spendByCategory')
            || slotFailed('spendYoY'),
    );

    const selectedProductIds = ref<string[]>([]);
    const productOptions = ref<{ label: string; value: string }[]>([]);

    // FU-668, third instance. This used to filter the product store's hydrated
    // first page in the browser, and `GET /products` is paginated at 50, so
    // product 51 onward was unsearchable with nothing on screen saying so. The
    // needle goes to the server now. Store name is no longer part of the match
    // (it lives on the Store row, not the Product) — the one capability traded
    // for seeing the whole catalogue.
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

    /** Categorical colour for a bucket with no colour of its own — a stock
     *  group, in practice. Deterministic so a group keeps its hue between
     *  renders.
     *
     *  This used to colour **stores** as well, hashing the store name into the
     *  chart ramp, so one store was its logo green on the shopping list and
     *  whatever the hash landed on here (FU-814). Stores go through
     *  `storeColour` in the card. Do not put a store back in here. */
    function colourFor(key: string): string {
        const series = [
            paletteToken('--chart-1', '#17b073'),
            paletteToken('--chart-2', '#006a80'),
            paletteToken('--chart-3', '#fed224'),
            paletteToken('--chart-4', '#e89a45'),
            paletteToken('--chart-5', '#5b8db8'),
            paletteToken('--chart-6', '#a07cc8'),
        ];
        let hash = 0;
        for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) | 0;
        return series[Math.abs(hash) % series.length]!;
    }

    // ── Loaders ──────────────────────────────────────────────────────────
    // A gated-off card must not fetch: the endpoint would 403 (R-058) and the
    // card would render a load failure for a report the install deliberately
    // does not have.
    async function loadStoreSpend() {
        if (!moneyEnabled.value) { storeSpend.value = null; return; }
        await loadSlot('storeSpend', async () => {
            storeSpend.value = await reportsApi.getSpendByStoreAsync(range.value);
        });
    }
    async function loadSpendByCategory() {
        if (!moneyEnabled.value) { spendByCategory.value = null; return; }
        await loadSlot('spendByCategory', async () => {
            spendByCategory.value = await reportsApi.getSpendByCategoryAsync(range.value);
        });
    }
    async function loadSpendYoY() {
        if (!moneyEnabled.value) { spendYoY.value = null; return; }
        // YoY needs a bounded window to compare against the same-length prior
        // window. Blank it on "All time" so the card can explain itself.
        if (range.value === 'all') { spendYoY.value = null; return; }
        await loadSlot('spendYoY', async () => {
            spendYoY.value = await reportsApi.getSpendYearOverYearAsync(
                range.value as YoYReportRange,
            );
        });
    }
    async function loadSavings() {
        if (!productMoneyEnabled.value) { savings.value = null; return; }
        await loadSlot('savings', async () => {
            savings.value = await reportsApi.getSavingsCapturedAsync(range.value);
        });
    }
    /** The Spend card's retry — all three axes plus its savings support line. */
    async function loadSpend() {
        await Promise.all([
            loadStoreSpend(), loadSpendByCategory(), loadSpendYoY(), loadSavings(),
        ]);
    }

    async function loadMostBought() {
        await loadSlot('mostBought', async () => {
            mostBought.value = await reportsApi.getMostBoughtAsync(range.value);
        });
    }
    async function loadKeepsOut() {
        // Passes the page's range now (§3.5 / D7) — the card sat under a control
        // saying "30 days" while counting all history, forever.
        await loadSlot('keepsOut', async () => {
            keepsOut.value = await reportsApi.getKeepsRunningOutAsync(10, range.value);
        });
    }
    async function loadMealsCooked() {
        await loadSlot('mealsCooked', async () => {
            mealsCooked.value = await reportsApi.getMealsCookedAsync(range.value, 10);
        });
    }

    const RANGE_TO_DAYS: Record<ReportRange, number> = {
        '30d': 30, '90d': 90, '1y': 365, '2y': 730, '5y': 1825, 'all': 3650,
    };
    async function loadWaste() {
        await loadSlot('waste', async () => {
            waste.value = await wasteApi.getInsightsAsync(RANGE_TO_DAYS[range.value]);
        });
    }

    async function loadItemMovers() {
        if (!moneyEnabled.value) { itemMovers.value = null; return; }
        await loadSlot('itemMovers', async () => {
            itemMovers.value = await reportsApi.getItemPriceMoversAsync(range.value, 8);
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
    function onProductSelection(ids: string[]) {
        selectedProductIds.value = ids;
        void loadPriceTrends();
    }
    async function loadProductsCatalogue() {
        if (!productMoneyEnabled.value) return;
        // Seeds the picker before the user types. Empty needle ⇒ the server's
        // first page, same as any other search.
        await filterProducts('', (assign) => assign());
    }

    // No page-level error banner: each card records its own failure, so the
    // reader can see exactly which parts of the page to trust. A banner over the
    // whole grid said "something here is wrong" without saying what, while the
    // failed card underneath still read as empty.
    async function loadAll() {
        await Promise.all([
            loadStoreSpend(),
            loadSpendByCategory(),
            loadSpendYoY(),
            loadSavings(),
            loadMostBought(),
            loadKeepsOut(),
            loadMealsCooked(),
            loadWaste(),
            loadItemMovers(),
            loadPriceTrends(),
        ]);
    }

    // FU-586's failure mode, found in the browser on this page's first live run:
    // the gates read the once-per-document `/api/health` probe, which had NOT
    // resolved when the page mounted — so every gated loader early-returned and
    // only the ungated reports fetched, while the money cards rendered their
    // *empty* state as if the household had never shopped. Nothing re-ran them
    // when the flags landed. The dashboard hit this exactly once before and fixed
    // it the same way; re-fire only the gated loaders on a gate turning on. On a
    // warm navigation the gate is already true at mount, `loadAll` fetches
    // normally, and these never fire. (The duplication is FU-844.)
    watch(moneyEnabled, (on) => {
        if (!on) return;
        void loadStoreSpend();
        void loadSpendByCategory();
        void loadSpendYoY();
        void loadItemMovers();
    });
    watch(productMoneyEnabled, (on) => {
        if (!on) return;
        void loadSavings();
        void loadPriceTrends();
        void loadProductsCatalogue();
    });

    onMounted(() => {
        void loadProductsCatalogue();
        void loadAll();
    });
</script>

<style scoped lang="scss">
    .reports-page {
        padding: var(--space-6) var(--space-6) var(--space-12);
        background: var(--surface-page);
        color: var(--text-primary);
        min-height: 100%;
    }
    .reports-header {
        display: flex;
        align-items: flex-start;
        gap: var(--space-4);
        flex-wrap: wrap;
        margin-bottom: var(--space-6);
    }
    .reports-title-block { flex: 1; min-width: 280px; }
    .reports-title {
        margin: 0;
        font-size: calc(var(--font-size-2xl) * 1rem);
        font-weight: 700;
    }
    .reports-range {
        display: flex;
        align-items: center;
        gap: var(--space-2);
    }
    .reports-caveat { color: var(--text-secondary); }
    .reports-grid {
        display: grid;
        /* A8's vocabulary — phone <600, tablet 600–1023, desktop ≥1024. The old
           single 900px breakpoint was N6's "2 cols desktop, 1 col mobile" and
           isn't a width this app knows about, so a 1000px tablet got two 470px
           columns holding 280px charts (§4.8). */
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: var(--space-6);
    }
    @media (max-width: 1023px) {
        .reports-grid { grid-template-columns: 1fr; }
    }
    .reports-grid__wide { grid-column: 1 / -1; }
</style>
