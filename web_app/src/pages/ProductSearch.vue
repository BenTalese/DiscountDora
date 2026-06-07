<template>
    <div class="product-search q-pa-md">
        <!-- ─── Search bar ─────────────────────────────────────────────── -->
        <div class="row items-center q-gutter-sm q-mb-sm">
            <q-input
                v-model="searchTerm"
                class="col dora-bg-page"
                dense
                outlined
                autofocus
                placeholder="Search products by name"
                :disable="isSearching"
                @keydown.enter="onSearch"
            >
                <template #prepend><q-icon :name="ICONS.search" /></template>
                <template #append>
                    <q-btn v-if="searchTerm" flat dense round :icon="ICONS.close" @click="searchTerm = ''" />
                </template>
            </q-input>

            <q-btn
                v-if="!isSearching"
                color="primary"
                no-caps
                :icon="ICONS.search"
                label="Search"
                :disable="!searchTerm.trim() || enabledMerchantsSelected.length === 0"
                @click="onSearch"
            />
            <q-btn v-else color="negative" no-caps :icon="ICONS.close" label="Cancel" @click="onCancelSearch" />
        </div>

        <!-- ─── Merchant connection status badges ──────────────────────── -->
        <div class="row items-center q-gutter-xs q-mb-md">
            <span class="text-caption dora-text-muted q-mr-xs">Connections:</span>
            <q-chip
                v-for="merchant in merchantStore.merchants"
                :key="merchant.name"
                dense
                :icon="connectionIcon(merchant)"
                :color="connectionColour(merchant)"
                text-color="white"
            >
                {{ merchant.name }}
                <q-tooltip>{{ storeTooltip(merchant) }}</q-tooltip>
            </q-chip>
        </div>

        <!-- ─── Filters ─ standardised via FilterBar (A4) ──────────────── -->
        <FilterBar :active-count="activeFilterCount" @clear="clearAllFilters">
            <template #filters>
                <div class="row items-center q-gutter-sm q-mb-sm">
                    <div class="text-caption dora-text-muted q-mr-sm">Stores</div>
                    <q-chip
                        v-for="merchant in merchantStore.merchants"
                        :key="merchant.name"
                        clickable
                        :selected="isStoreSelected(merchant.name)"
                        :disable="!merchant.is_enabled"
                        :color="storeChipColor(merchant)"
                        :text-color="isStoreSelected(merchant.name) && merchant.is_enabled ? 'white' : undefined"
                        :icon="storeChipIcon(merchant)"
                        @click="toggleStore(merchant)"
                    >
                        {{ merchant.name }}
                        <q-tooltip>{{ storeTooltip(merchant) }}</q-tooltip>
                    </q-chip>
                    <q-btn flat dense size="sm" no-caps label="Toggle all" class="q-ml-sm" @click="toggleAllStores" />
                    <q-space />
                    <q-btn flat dense size="sm" no-caps icon-right="open_in_new" label="Manage merchants" to="/settings/admin/merchants" />
                </div>

                <q-separator class="q-my-sm" />

                <!-- Sort + toggle chips -->
                <div class="row items-center q-gutter-sm q-mb-sm">
                    <q-select
                        v-model="sortModel"
                        :options="OfferSortByOptions"
                        :option-label="(o: IOfferSortByOption) => o.description"
                        dense outlined emit-value map-options
                        style="min-width: 200px"
                        label="Sort by"
                    />
                    <q-chip clickable outline :selected="filters.showOnlyAvailable"
                        :color="filters.showOnlyAvailable ? 'primary' : undefined"
                        :text-color="filters.showOnlyAvailable ? 'white' : undefined"
                        @click="toggleAvailableFilter">In stock only</q-chip>
                    <q-chip clickable outline :selected="filters.showOnlySpecials"
                        :color="filters.showOnlySpecials ? 'amber-7' : undefined"
                        :text-color="filters.showOnlySpecials ? 'white' : undefined"
                        @click="toggleSpecialsFilter">Specials only</q-chip>
                    <q-chip clickable outline :selected="halfPriceOnly"
                        :color="halfPriceOnly ? 'negative' : undefined"
                        :text-color="halfPriceOnly ? 'white' : undefined"
                        @click="halfPriceOnly = !halfPriceOnly">Half price or better</q-chip>
                    <q-space />
                    <div class="row items-center q-gutter-xs">
                        <span class="text-caption dora-text-muted">Per merchant</span>
                        <q-input v-model.number="resultLimit" type="number" dense outlined style="width: 80px" :min="1" :max="50" />
                    </div>
                </div>

                <!-- Range filters -->
                <div class="row items-end q-gutter-md">
                    <div class="column">
                        <span class="text-caption dora-text-muted">Price ($)</span>
                        <div class="row items-center q-gutter-xs">
                            <q-input v-model.number="priceMin" type="number" dense outlined placeholder="min" style="width: 80px" />
                            <span>–</span>
                            <q-input v-model.number="priceMax" type="number" dense outlined placeholder="max" style="width: 80px" />
                        </div>
                    </div>
                    <div class="column">
                        <span class="text-caption dora-text-muted">Unit price (per 100g/ml or ea)</span>
                        <div class="row items-center q-gutter-xs">
                            <q-input v-model.number="unitPriceMax" type="number" step="0.01" dense outlined placeholder="max $" style="width: 110px" />
                        </div>
                    </div>
                    <div class="column">
                        <span class="text-caption dora-text-muted">Size / weight</span>
                        <div class="row items-center q-gutter-xs">
                            <q-input v-model.number="weightMin" type="number" dense outlined placeholder="min" style="width: 80px" />
                            <span>–</span>
                            <q-input v-model.number="weightMax" type="number" dense outlined placeholder="max" style="width: 80px" />
                        </div>
                    </div>
                </div>
            </template>
        </FilterBar>

        <!-- ─── Status banners ─────────────────────────────────────────── -->
        <q-banner v-if="isSearching" class="dora-bg-sunken q-mb-md" dense rounded>
            <template #avatar><AppSpinner size="32px" /></template>
            Searching {{ searchingStoresLabel }}…
            <span class="text-caption dora-text-muted">Live scrapes can take 10–20 seconds.</span>
            <template #action><q-btn flat no-caps label="Cancel" @click="onCancelSearch" /></template>
        </q-banner>

        <q-banner v-if="!isSearching && searchError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            <template #avatar><q-icon :name="ICONS.cloud_off" /></template>
            We couldn't reach one or more merchant scrapers. Check your connection or the merchant API status, then try again.
            <template #action>
                <q-btn flat no-caps label="Retry" @click="onSearch" />
                <q-btn flat no-caps icon-right="open_in_new" label="API status" to="/settings/admin/merchants" />
            </template>
        </q-banner>

        <q-banner v-if="!isSearching && unhealthyEnabledMerchants.length > 0" class="dora-bg-warning-soft text-warning q-mb-md" dense rounded>
            <template #avatar><q-icon :name="ICONS.warning" /></template>
            {{ unhealthyMerchantWarning }}
            <template #action><q-btn flat no-caps icon-right="open_in_new" label="Check providers" to="/settings/admin/merchants" /></template>
        </q-banner>

        <!-- ─── Result grid ────────────────────────────────────────────── -->
        <div v-if="displayedOffers.length > 0" class="dora-card-grid">
            <div v-for="offer in displayedOffers" :key="offerKey(offer)" class="q-pa-sm">
                <ProductSearchCard
                    :offer="offer"
                    :saved="!!offer.is_saved && !!offer.is_saved_product_active"
                    :in-comparison="comparison.includes(offerKey(offer))"
                    :history="historyByKey.get(offerKey(offer)) ?? []"
                    @save="onSaveToggle(offer)"
                    @link="openLinkDialog(offer)"
                    @quick-add="onQuickAdd(offer)"
                    @toggle-compare="toggleCompare(offer)"
                />
            </div>
        </div>

        <!-- ─── Empty states ───────────────────────────────────────────── -->
        <div v-else-if="!isSearching && previousSearchTerm && (productStore.productOffers?.length ?? 0) > 0" class="dora-empty">
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                Nothing matches your current filters.
                <q-btn flat no-caps color="primary" label="Clear filters" @click="clearAllFilters" />
            </div>
        </div>
        <div v-else-if="!isSearching && previousSearchTerm && !productStore.productOffers?.length" class="dora-empty">
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                No products found for <strong>"{{ previousSearchTerm }}"</strong>.
                <div class="text-caption dora-text-muted q-mt-sm">Try spelling it differently, or check the right merchants are enabled.</div>
            </div>
        </div>
        <div v-else-if="!isSearching && !previousSearchTerm" class="dora-empty">
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                Type a product name above and hit <q-icon :name="ICONS.search" /> to search across enabled merchants.
            </div>
        </div>

        <!-- ─── Comparison tray ────────────────────────────────────────── -->
        <q-page-sticky v-if="comparison.length > 0" position="bottom" :offset="[0, 16]">
            <q-card class="bg-primary dora-text-on-primary row items-center q-px-md q-py-sm q-gutter-sm shadow-4">
                <q-icon :name="ICONS.compare_arrows" />
                <span>{{ comparison.length }} selected for comparison</span>
                <q-btn dense no-caps color="white" text-color="primary" label="Compare" :disable="comparison.length < 2" @click="compareOpen = true" />
                <q-btn dense flat no-caps label="Clear" @click="comparison = []" />
            </q-card>
        </q-page-sticky>

        <!-- ─── Comparison dialog ──────────────────────────────────────── -->
        <BaseDialog v-model="compareOpen" card-style="min-width: 320px; max-width: 95vw">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-h6">Compare products</div>
                    <q-space />
                    <q-btn flat dense round :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-card-section>
                    <q-markup-table flat bordered dense>
                        <thead>
                            <tr>
                                <th class="text-left">Attribute</th>
                                <th v-for="o in comparisonOffers" :key="offerKey(o)" class="text-left">{{ o.name }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Merchant</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">{{ o.merchant_name }}</td>
                            </tr>
                            <tr>
                                <td>Price</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">${{ o.price_now.toFixed(2) }}</td>
                            </tr>
                            <tr>
                                <td>% off</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">{{ discountPercent(o) ?? '—' }}{{ discountPercent(o) !== null ? '%' : '' }}</td>
                            </tr>
                            <tr>
                                <td>Unit price</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">{{ unitPriceLabel(o) ?? '—' }}</td>
                            </tr>
                            <tr>
                                <td>Size</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">{{ o.size || '—' }}</td>
                            </tr>
                            <tr>
                                <td>In stock</td>
                                <td v-for="o in comparisonOffers" :key="offerKey(o)">{{ o.is_available ? 'Yes' : 'No' }}</td>
                            </tr>
                        </tbody>
                    </q-markup-table>
                </q-card-section>
        </BaseDialog>

        <!-- ─── Link-to-stock-item dialog ──────────────────────────────── -->
        <BaseDialog v-model="linkOpen" card-style="width: 460px; max-width: 95vw">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-h6">Link to a stock item</div>
                    <q-space />
                    <q-btn flat dense round :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-card-section>
                    <div class="text-caption dora-text-muted q-mb-sm" v-if="linkTargetOffer">
                        {{ linkTargetOffer.name }}
                    </div>
                    <q-select
                        v-model="linkStockItemId"
                        :options="stockItemOptions"
                        emit-value map-options use-input fill-input hide-selected
                        input-debounce="150"
                        outlined dense
                        label="Search your stock items"
                        @filter="filterStockItems"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn color="primary" no-caps label="Link" :loading="linking" :disable="!linkStockItemId" @click="confirmLink" />
                </q-card-actions>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import ProductSearchCard from 'src/components/ProductSearchCard.vue';
    import type { IOfferSortByOption } from 'src/helpers/offerSortByOptions';
    import { OfferSortByOptions } from 'src/helpers/offerSortByOptions';
    import {
        discountPercent,
        findSavedProduct,
        unitPrice,
        unitPriceLabel,
    } from 'src/helpers/scrapedProductOfferLogic';
    import type { Merchant } from 'src/models/merchant';
    import type { Product } from 'src/models/product';
    import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
    import ProductApiService from 'src/services/api/productApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useMerchantStore } from 'src/stores/merchantStore';
    import { useProductStore } from 'src/stores/productStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const merchantStore = useMerchantStore();
    const productStore = useProductStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();

    const { isSearching, searchError } = storeToRefs(productStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const productApi = new ProductApiService();
    const stockItemApi = new StockItemApiService();
    const shoppingListApi = new ShoppingListApiService();

    const filters = productStore.productSearchOfferFilters;

    // ── Search state ─────────────────────────────────────────────────────
    const searchTerm = ref('');
    const previousSearchTerm = ref<string | undefined>();
    const resultLimit = ref(10);

    function offerKey(o: ScrapedProductOffer): string {
        return `${o.merchant_name}-${o.merchant_stockcode}`;
    }
    function savedProductFor(o: ScrapedProductOffer): Product | undefined {
        return findSavedProduct(o, productStore.products as Product[] | undefined);
    }

    const enabledMerchantsSelected = computed(() =>
        filters.stores.filter((s) => merchantStore.merchants.find((m) => m.name === s.name)?.is_enabled),
    );
    const searchingStoresLabel = computed(() => {
        const names = enabledMerchantsSelected.value.map((s) => s.name);
        if (names.length === 0) return 'merchants';
        if (names.length === 1) return names[0]!;
        if (names.length === 2) return `${names[0]} and ${names[1]}`;
        return `${names.length} merchants`;
    });
    const unhealthyEnabledMerchants = computed(() =>
        merchantStore.merchants.filter((m) => m.is_enabled && !merchantStore.isMerchantHealthy(m.name)),
    );
    const unhealthyMerchantWarning = computed(() => {
        const names = unhealthyEnabledMerchants.value.map((m) => m.name);
        if (names.length === 1) return `${names[0]}'s scraper failed its last health check — results may be slow or empty.`;
        return `${names.join(', ')} failed their last health check — results may be slow or empty.`;
    });

    async function onSearch(): Promise<void> {
        if (!searchTerm.value.trim()) return;
        if (enabledMerchantsSelected.value.length === 0) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Select at least one enabled merchant to search.' });
            return;
        }
        await productStore.searchByTermAsync({
            search_term: searchTerm.value,
            result_limit: Math.max(1, Math.min(resultLimit.value || 1, 50)),
            merchants_to_search: enabledMerchantsSelected.value.map((m) => m.name),
        });
        previousSearchTerm.value = searchTerm.value;
    }
    function onCancelSearch(): void {
        productStore.cancelSearch();
        $q.notify({ type: 'info', position: 'bottom-right', message: 'Search cancelled.' });
    }

    // ── Store filters ────────────────────────────────────────────────────
    function isStoreSelected(name: string): boolean {
        return filters.stores.some((s) => s.name === name);
    }
    function toggleStore(merchant: Merchant): void {
        if (!merchant.is_enabled) return;
        const next = isStoreSelected(merchant.name)
            ? filters.stores.filter((s) => s.name !== merchant.name)
            : [...filters.stores, merchant];
        productStore.setProductSearchStoresFilter(next);
    }
    function toggleAllStores(): void {
        const allEnabled = merchantStore.merchants.filter((m) => m.is_enabled);
        const allSelected = allEnabled.every((m) => isStoreSelected(m.name));
        productStore.setProductSearchStoresFilter(allSelected ? [] : allEnabled);
    }
    function storeChipColor(merchant: Merchant): string | undefined {
        if (!merchant.is_enabled) return 'grey-3';
        if (!isStoreSelected(merchant.name)) return undefined;
        return merchantStore.isMerchantHealthy(merchant.name) ? 'primary' : 'amber-7';
    }
    function storeChipIcon(merchant: Merchant): string | undefined {
        if (!merchant.is_enabled) return 'block';
        if (!merchantStore.isMerchantHealthy(merchant.name)) return 'cloud_off';
        return undefined;
    }
    function storeTooltip(merchant: Merchant): string {
        if (!merchant.is_enabled) return `${merchant.name} is disabled. Enable it under Settings → Merchants.`;
        if (!merchantStore.isMerchantHealthy(merchant.name)) return `${merchant.name}'s scraper failed its last health check.`;
        const health = merchantStore.healthForMerchant(merchant.name);
        if (!health) return `${merchant.name} — health unknown.`;
        if (health.skipped) return `${merchant.name} — last health check was skipped.`;
        return `${merchant.name} — last health check passed.`;
    }
    function connectionIcon(merchant: Merchant): string {
        if (!merchant.is_enabled) return 'block';
        return merchantStore.isMerchantHealthy(merchant.name) ? 'check_circle' : 'cloud_off';
    }
    function connectionColour(merchant: Merchant): string {
        if (!merchant.is_enabled) return 'grey-5';
        return merchantStore.isMerchantHealthy(merchant.name) ? 'positive' : 'negative';
    }

    const sortModel = computed<IOfferSortByOption>({
        get: () => filters.sortBy,
        set: (v) => productStore.setProductSearchSortByFilter(v),
    });
    function toggleAvailableFilter(): void {
        productStore.toggleProductSearchFilter('showOnlyAvailable');
    }
    function toggleSpecialsFilter(): void {
        productStore.toggleProductSearchFilter('showOnlySpecials');
    }

    // ── Local range / half-price filters ──────────────────────────────────
    const priceMin = ref<number | null>(null);
    const priceMax = ref<number | null>(null);
    const unitPriceMax = ref<number | null>(null);
    const weightMin = ref<number | null>(null);
    const weightMax = ref<number | null>(null);
    const halfPriceOnly = ref(false);

    function unitPriceValue(o: ScrapedProductOffer): number | null {
        const { price, group } = unitPrice(o);
        if (!isFinite(price)) return null;
        return group === 'count' ? price : price * 100; // per 100g/ml
    }

    const displayedOffers = computed<ScrapedProductOffer[]>(() => {
        const base = productStore.filteredProductOffers ?? [];
        return base.filter((o) => {
            if (priceMin.value != null && o.price_now < priceMin.value) return false;
            if (priceMax.value != null && o.price_now > priceMax.value) return false;
            if (weightMin.value != null && (o.size_value ?? 0) < weightMin.value) return false;
            if (weightMax.value != null && (o.size_value ?? 0) > weightMax.value) return false;
            if (unitPriceMax.value != null) {
                const up = unitPriceValue(o);
                if (up == null || up > unitPriceMax.value) return false;
            }
            if (halfPriceOnly.value && (discountPercent(o) ?? 0) < 50) return false;
            return true;
        });
    });

    function clearRanges(): void {
        priceMin.value = null;
        priceMax.value = null;
        unitPriceMax.value = null;
        weightMin.value = null;
        weightMax.value = null;
        halfPriceOnly.value = false;
    }
    function clearAllFilters(): void {
        if (filters.showOnlyAvailable) toggleAvailableFilter();
        if (filters.showOnlySpecials) toggleSpecialsFilter();
        clearRanges();
    }

    // Active-filter count for the FilterBar badge. Counts the refinement
    // filters that "Clear filters" resets — NOT the merchant/search scope
    // (which has its own "Toggle all"). Mirrors clearAllFilters.
    const activeFilterCount = computed(() => {
        let n = 0;
        if (filters.showOnlyAvailable) n++;
        if (filters.showOnlySpecials) n++;
        if (halfPriceOnly.value) n++;
        if (priceMin.value != null) n++;
        if (priceMax.value != null) n++;
        if (unitPriceMax.value != null) n++;
        if (weightMin.value != null) n++;
        if (weightMax.value != null) n++;
        return n;
    });

    // ── Price-history sparklines (only for saved products) ────────────────
    const historyByKey = ref<Map<string, number[]>>(new Map());
    async function loadHistories(): Promise<void> {
        for (const o of displayedOffers.value) {
            const key = offerKey(o);
            if (historyByKey.value.has(key)) continue;
            const product = savedProductFor(o);
            if (!product) continue;
            try {
                const h = await productApi.getPriceHistoryAsync(product.product_id);
                historyByKey.value.set(key, h.points.map((p) => p.price_now ?? 0).filter((n) => n > 0));
                historyByKey.value = new Map(historyByKey.value);
            } catch {
                // sparkline just stays empty
            }
        }
    }
    watch(displayedOffers, () => void loadHistories());

    // ── Save toggle ───────────────────────────────────────────────────────
    async function ensureSaved(offer: ScrapedProductOffer): Promise<Product | null> {
        const existing = savedProductFor(offer);
        if (existing) return existing;
        await productStore.createProductAsync({
            brand: offer.brand,
            image: offer.image,
            is_active: true,
            is_available: offer.is_available,
            merchant_name: offer.merchant_name,
            merchant_stockcode: offer.merchant_stockcode,
            name: offer.name,
            price_now: offer.price_now,
            price_was: offer.price_was,
            size: offer.size,
            size_unit: offer.size_unit,
            size_value: offer.size_value,
            web_url: offer.web_url,
        });
        productStore.updateProductOffer({
            is_saved: true,
            is_saved_product_active: true,
            merchant_name: offer.merchant_name,
            merchant_stockcode: offer.merchant_stockcode,
        });
        return savedProductFor(offer) ?? null;
    }

    async function onSaveToggle(offer: ScrapedProductOffer): Promise<void> {
        const existing = savedProductFor(offer);
        try {
            if (existing) {
                const nextActive = !offer.is_saved_product_active;
                await productStore.updateProductAsync({ is_active: nextActive, product_id: existing.product_id });
                productStore.updateProductOffer({
                    is_saved_product_active: nextActive,
                    merchant_name: offer.merchant_name,
                    merchant_stockcode: offer.merchant_stockcode,
                });
                $q.notify({ type: 'info', position: 'bottom-right', message: nextActive ? `Re-saved ${offer.name}.` : `Removed ${offer.name} from saved products.` });
            } else {
                await ensureSaved(offer);
                $q.notify({ type: 'positive', position: 'bottom-right', message: `Saved ${offer.name}.` });
            }
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not update the saved product.', caption: describeApiError(err) || '' });
        }
    }

    // ── Quick-add: save + create stock item + link + add to list ──────────
    async function onQuickAdd(offer: ScrapedProductOffer): Promise<void> {
        try {
            const product = await ensureSaved(offer);
            if (!product) throw new Error('Could not save the product.');

            // New tracked items start Out of Stock — you're shopping for them.
            const level =
                stockLevels.value.find((l) => l.name === 'Out of Stock') ?? stockLevels.value[0];
            if (!level) throw new Error('No stock levels configured.');

            const created = await stockItemApi.createAsync({
                name: offer.name,
                stock_level_id: level.stock_level_id,
                stock_location_id: null,
            });
            const stockItemId =
                (created as { stock_item_id?: string }).stock_item_id ?? created.id;
            if (!stockItemId) throw new Error('Stock item id missing from response.');

            await stockItemApi.linkProductAsync(stockItemId, product.product_id);
            const quick = await shoppingListApi.quickAddToPrimaryAsync(stockItemId);
            await Promise.all([stockItemStore.getStockItemsAsync(), shoppingListStore.refreshAsync()]);

            if (quick.result === 'added') {
                $q.notify({ type: 'positive', position: 'bottom-right', message: `Tracking ${offer.name} and added to your list.` });
            } else {
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Tracking ${offer.name}.`,
                    caption: quick.result === 'no_draft'
                        ? 'No draft list — open Shopping lists to add it.'
                        : 'Multiple draft lists — open Shopping lists to pick where.',
                });
            }
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Quick-add failed.', caption: describeApiError(err) || '' });
        }
    }

    // ── Comparison ─────────────────────────────────────────────────────────
    const comparison = ref<string[]>([]);
    const compareOpen = ref(false);
    function toggleCompare(offer: ScrapedProductOffer): void {
        const key = offerKey(offer);
        if (comparison.value.includes(key)) {
            comparison.value = comparison.value.filter((k) => k !== key);
        } else if (comparison.value.length >= 3) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Compare up to 3 at a time.' });
        } else {
            comparison.value = [...comparison.value, key];
        }
    }
    const comparisonOffers = computed(() =>
        comparison.value
            .map((k) => (productStore.productOffers ?? []).find((o) => offerKey(o) === k))
            .filter((o): o is ScrapedProductOffer => !!o),
    );

    // ── Link to stock item ──────────────────────────────────────────────────
    const linkOpen = ref(false);
    const linkTargetOffer = ref<ScrapedProductOffer | null>(null);
    const linkStockItemId = ref<string | null>(null);
    const linking = ref(false);
    const stockItemFilter = ref('');

    const stockItemOptions = computed(() => {
        const q = stockItemFilter.value.trim().toLowerCase();
        return stockItems.value
            .filter((si) => !q || si.name.toLowerCase().includes(q))
            .slice(0, 50)
            .map((si) => ({ label: si.name, value: si.stock_item_id }));
    });
    function filterStockItems(val: string, update: (fn: () => void) => void): void {
        update(() => {
            stockItemFilter.value = val;
        });
    }
    function openLinkDialog(offer: ScrapedProductOffer): void {
        linkTargetOffer.value = offer;
        linkStockItemId.value = null;
        stockItemFilter.value = '';
        linkOpen.value = true;
    }
    async function confirmLink(): Promise<void> {
        if (!linkTargetOffer.value || !linkStockItemId.value) return;
        linking.value = true;
        try {
            const product = await ensureSaved(linkTargetOffer.value);
            if (!product) throw new Error('Could not save the product.');
            await stockItemApi.linkProductAsync(linkStockItemId.value, product.product_id);
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Linked to stock item.' });
            linkOpen.value = false;
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not link.', caption: describeApiError(err) || '' });
        } finally {
            linking.value = false;
        }
    }

    watch(searchError, (err) => {
        if (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Search failed. Check connection and try again.', timeout: 4000 });
        }
    });

    onMounted(async () => {
        await Promise.all([
            merchantStore.getMerchantsAsync(),
            merchantStore.getProviderHealthAsync(),
            productStore.getProductsAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            shoppingListStore.refreshAsync(),
        ]);
    });
</script>

<style scoped lang="scss">
    .product-search {
        max-width: 1400px;
        margin: 0 auto;
    }
    .dora-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    }
    .dora-empty {
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 48px 24px;
        max-width: 720px;
        margin: 0 auto;
    }
    .dora-empty-mascot {
        border-radius: 16px;
        background: var(--surface-elevated);
        padding: 8px;
        flex-shrink: 0;
        // B9.8: q-avatar's default inner-img sizing leaves the mascot
        // pinned to one corner of the padded box (Quasar centers via line
        // height which doesn't fit a square avatar with custom padding).
        // Force the img to fill the padded box and contain so the mascot
        // sits centred regardless of its own aspect ratio.
        :deep(img) {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
    }
    .dora-empty-text {
        font-size: 1.15rem;
        line-height: 1.5;
        color: var(--text-primary);
    }
    @media (max-width: 600px) {
        .dora-empty {
            flex-direction: column;
            text-align: center;
        }
    }
</style>
