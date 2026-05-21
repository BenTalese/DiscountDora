<template>
    <div class="product-search q-pa-md">
        <!-- ─── Search bar ─────────────────────────────────────────────── -->
        <div class="row items-center q-gutter-sm q-mb-md">
            <q-input
                v-model="searchTerm"
                class="col bg-white"
                dense
                outlined
                autofocus
                placeholder="Search products by name"
                :disable="isSearching"
                @keydown.enter="onSearch"
            >
                <template #prepend>
                    <q-icon name="search" />
                </template>
                <template #append>
                    <q-btn
                        v-if="searchTerm"
                        flat
                        dense
                        round
                        icon="close"
                        @click="searchTerm = ''"
                    />
                </template>
            </q-input>

            <q-btn
                v-if="!isSearching"
                color="primary"
                no-caps
                icon="search"
                label="Search"
                :disable="!searchTerm.trim() || enabledMerchantsSelected.length === 0"
                @click="onSearch"
            />
            <q-btn
                v-else
                color="negative"
                no-caps
                icon="close"
                label="Cancel"
                @click="onCancelSearch"
            />

            <q-btn
                flat
                round
                dense
                icon="tune"
                :color="showFilters ? 'primary' : undefined"
                @click="showFilters = !showFilters"
            >
                <q-tooltip>Toggle filters</q-tooltip>
            </q-btn>
        </div>

        <!-- ─── Filters row ────────────────────────────────────────────── -->
        <q-card v-if="showFilters" flat bordered class="q-mb-md">
            <q-card-section class="q-py-sm">
                <!-- Stores: chips with health-aware styling -->
                <div class="row items-center q-gutter-sm q-mb-sm">
                    <div class="text-caption text-grey q-mr-sm">Stores</div>
                    <q-chip
                        v-for="merchant in merchantStore.merchants"
                        :key="merchant.name"
                        clickable
                        :selected="isStoreSelected(merchant.name)"
                        :disable="!merchant.is_enabled"
                        :color="storeChipColor(merchant)"
                        :text-color="
                            isStoreSelected(merchant.name) && merchant.is_enabled ? 'white' : undefined
                        "
                        :icon="storeChipIcon(merchant)"
                        @click="toggleStore(merchant)"
                    >
                        {{ merchant.name }}
                        <q-tooltip>{{ storeTooltip(merchant) }}</q-tooltip>
                    </q-chip>

                    <q-btn
                        flat
                        dense
                        size="sm"
                        no-caps
                        label="Toggle all"
                        class="q-ml-sm"
                        @click="toggleAllStores"
                    />
                    <q-space />
                    <q-btn
                        flat
                        dense
                        size="sm"
                        no-caps
                        icon-right="open_in_new"
                        label="Manage merchants"
                        to="/settings/admin/merchants"
                    />
                </div>

                <q-separator class="q-my-sm" />

                <!-- Sort + quick filter chips -->
                <div class="row items-center q-gutter-sm">
                    <q-select
                        v-model="sortModel"
                        :options="OfferSortByOptions"
                        :option-label="(o: IOfferSortByOption) => o.description"
                        dense
                        outlined
                        emit-value
                        map-options
                        style="min-width: 220px"
                        label="Sort by"
                    />

                    <q-chip
                        clickable
                        :selected="productStore.productSearchOfferFilters.showOnlyAvailable"
                        :color="
                            productStore.productSearchOfferFilters.showOnlyAvailable
                                ? 'primary'
                                : undefined
                        "
                        :text-color="
                            productStore.productSearchOfferFilters.showOnlyAvailable
                                ? 'white'
                                : undefined
                        "
                        outline
                        @click="toggleAvailableFilter"
                    >
                        In stock only
                    </q-chip>

                    <q-chip
                        clickable
                        :selected="productStore.productSearchOfferFilters.showOnlySpecials"
                        :color="
                            productStore.productSearchOfferFilters.showOnlySpecials
                                ? 'amber-7'
                                : undefined
                        "
                        :text-color="
                            productStore.productSearchOfferFilters.showOnlySpecials
                                ? 'white'
                                : undefined
                        "
                        outline
                        @click="toggleSpecialsFilter"
                    >
                        Specials only
                    </q-chip>

                    <q-space />

                    <div class="row items-center q-gutter-xs">
                        <span class="text-caption text-grey">Per merchant</span>
                        <q-input
                            v-model.number="resultLimit"
                            type="number"
                            dense
                            outlined
                            style="width: 80px"
                            :min="1"
                            :max="50"
                        />
                    </div>
                </div>
            </q-card-section>
        </q-card>

        <!-- ─── Status banners ─────────────────────────────────────────── -->
        <q-banner
            v-if="isSearching"
            class="bg-grey-2 q-mb-md"
            dense
            rounded
        >
            <template #avatar>
                <q-spinner-dots color="primary" size="32px" />
            </template>
            Searching {{ searchingStoresLabel }}…
            <span class="text-caption text-grey">
                Live scrapes can take 10–20 seconds.
            </span>
            <template #action>
                <q-btn flat no-caps label="Cancel" @click="onCancelSearch" />
            </template>
        </q-banner>

        <q-banner
            v-if="!isSearching && searchError"
            class="bg-red-1 text-red-9 q-mb-md"
            dense
            rounded
        >
            <template #avatar>
                <q-icon name="cloud_off" />
            </template>
            We couldn't reach one or more merchant scrapers. Check your connection
            or the merchant API status, then try again.
            <template #action>
                <q-btn flat no-caps label="Retry" @click="onSearch" />
                <q-btn
                    flat
                    no-caps
                    icon-right="open_in_new"
                    label="API status"
                    to="/settings/admin/merchants"
                />
            </template>
        </q-banner>

        <q-banner
            v-if="!isSearching && unhealthyEnabledMerchants.length > 0"
            class="bg-amber-1 text-amber-10 q-mb-md"
            dense
            rounded
        >
            <template #avatar>
                <q-icon name="warning" />
            </template>
            {{ unhealthyMerchantWarning }}
            <template #action>
                <q-btn
                    flat
                    no-caps
                    icon-right="open_in_new"
                    label="Check providers"
                    to="/settings/admin/merchants"
                />
            </template>
        </q-banner>

        <!-- ─── Result grid ────────────────────────────────────────────── -->
        <div v-if="filteredOffers && filteredOffers.length > 0" class="dora-card-grid">
            <div
                v-for="offer in filteredOffers"
                :key="`${offer.merchant_name}-${offer.merchant_stockcode}`"
                class="q-pa-sm"
            >
                <card-component
                    :icon-class="
                        offer.is_saved && offer.is_saved_product_active ? 'text-red-12' : 'text-grey'
                    "
                    :img="imageService.decodeBase64Image(offer.image)"
                    :img-caption="offer.is_available ? undefined : 'OUT OF STOCK'"
                    @icon-click="onSaveToggle(offer)"
                    icon="favorite"
                >
                    <template #body>
                        <q-card-section class="dora-flex-1 q-py-none">
                            <div class="column full-height no-wrap justify-between">
                                <div class="text-body2 text-weight-regular q-pb-sm">
                                    {{ offer.name }}
                                    <span v-if="offer.size" class="text-grey">· {{ offer.size }}</span>
                                </div>
                                <div>
                                    <div class="items-center no-wrap row text-body2 text-weight-medium">
                                        <template v-if="offer.price_now > 0">
                                            <span>${{ offer.price_now }}</span>
                                            <q-badge
                                                v-if="offer.price_difference > 0"
                                                class="q-mx-sm"
                                                color="yellow-6"
                                                text-color="black"
                                            >
                                                SAVE ${{ offer.price_difference }}
                                            </q-badge>
                                        </template>
                                        <span v-else>Price unavailable</span>
                                    </div>
                                    <div class="dora-height-20 text-caption text-weight-regular">
                                        <span v-if="isOfferOnSpecial(offer)">
                                            <s>${{ offer.price_was }}</s>&nbsp;
                                        </span>
                                        <span>{{ offer.price_per_cup }}</span>
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                    </template>

                    <template #footer>
                        <q-card-actions class="dora-bgc-offWhite" align="right">
                            <q-btn
                                v-if="offer.web_url"
                                flat
                                dense
                                round
                                size="sm"
                                icon="open_in_new"
                                :href="offer.web_url"
                                target="_blank"
                                rel="noopener"
                            >
                                <q-tooltip>Open on {{ offer.merchant_name }}</q-tooltip>
                            </q-btn>
                            <q-space />
                            <MerchantLogo :name="offer.merchant_name" />
                        </q-card-actions>
                    </template>
                </card-component>
            </div>
        </div>

        <!-- ─── Empty states ───────────────────────────────────────────── -->
        <div
            v-else-if="
                !isSearching &&
                previousSearchTerm &&
                productStore.productOffers &&
                productStore.productOffers.length > 0
            "
            class="dora-empty"
        >
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                Nothing matches your current filters.
                <q-btn
                    flat
                    no-caps
                    color="primary"
                    label="Clear filters"
                    @click="clearTransientFilters"
                />
            </div>
        </div>

        <div
            v-else-if="!isSearching && previousSearchTerm && !productStore.productOffers?.length"
            class="dora-empty"
        >
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                No products found for <strong>"{{ previousSearchTerm }}"</strong>.
                <div class="text-caption text-grey q-mt-sm">
                    Try spelling it differently, or check that the right merchants are enabled.
                </div>
            </div>
        </div>

        <div v-else-if="!isSearching && !previousSearchTerm" class="dora-empty">
            <q-avatar size="120px" square class="dora-empty-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div class="dora-empty-text">
                Type a product name above and hit <q-icon name="search" />
                to search across enabled merchants.
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import CardComponent from 'src/components/CardComponent.vue';
    import MerchantLogo from 'src/components/MerchantLogo.vue';
    import type { IOfferSortByOption } from 'src/helpers/offerSortByOptions';
    import { OfferSortByOptions } from 'src/helpers/offerSortByOptions';
    import { isOfferOnSpecial } from 'src/helpers/scrapedProductOfferLogic';
    import type { Merchant } from 'src/models/merchant';
    import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
    import ImageService from 'src/services/files/imageService';
    import { useMerchantStore } from 'src/stores/merchantStore';
    import { useProductStore } from 'src/stores/productStore';
    import { computed, onMounted, ref, watch } from 'vue';

    const $q = useQuasar();
    const merchantStore = useMerchantStore();
    const productStore = useProductStore();

    const { isSearching, searchError } = storeToRefs(productStore);

    const imageService = new ImageService();

    // ── Search state ─────────────────────────────────────────────────────
    const searchTerm = ref('');
    const previousSearchTerm = ref<string | undefined>();
    const resultLimit = ref(10);

    const showFilters = ref(true);

    const enabledMerchantsSelected = computed(() =>
        productStore.productSearchOfferFilters.stores.filter(
            (s) => merchantStore.merchants.find((m) => m.name === s.name)?.is_enabled
        )
    );

    const searchingStoresLabel = computed(() => {
        const names = enabledMerchantsSelected.value.map((s) => s.name);
        if (names.length === 0) return 'merchants';
        if (names.length === 1) return names[0]!;
        if (names.length === 2) return `${names[0]} and ${names[1]}`;
        return `${names.length} merchants`;
    });

    const unhealthyEnabledMerchants = computed(() =>
        merchantStore.merchants.filter(
            (m) => m.is_enabled && !merchantStore.isMerchantHealthy(m.name)
        )
    );

    const unhealthyMerchantWarning = computed(() => {
        const names = unhealthyEnabledMerchants.value.map((m) => m.name);
        if (names.length === 1) {
            return `${names[0]}'s scraper failed its last health check — results from it may be slow or empty.`;
        }
        const list = names.join(', ');
        return `${list} failed their last health check — results from them may be slow or empty.`;
    });

    async function onSearch(): Promise<void> {
        if (!searchTerm.value.trim()) return;
        if (enabledMerchantsSelected.value.length === 0) {
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                message: 'Select at least one enabled merchant to search.'
            });
            return;
        }

        await productStore.searchByTermAsync({
            search_term: searchTerm.value,
            result_limit: Math.max(1, Math.min(resultLimit.value || 1, 50)),
            merchants_to_search: enabledMerchantsSelected.value.map((m) => m.name)
        });
        previousSearchTerm.value = searchTerm.value;
    }

    function onCancelSearch(): void {
        productStore.cancelSearch();
        $q.notify({
            type: 'info',
            position: 'bottom-right',
            message: 'Search cancelled.'
        });
    }

    // ── Filters ──────────────────────────────────────────────────────────
    function isStoreSelected(name: string): boolean {
        return productStore.productSearchOfferFilters.stores.some((s) => s.name === name);
    }

    function toggleStore(merchant: Merchant): void {
        if (!merchant.is_enabled) return;
        const selected = isStoreSelected(merchant.name);
        const next = selected
            ? productStore.productSearchOfferFilters.stores.filter((s) => s.name !== merchant.name)
            : [...productStore.productSearchOfferFilters.stores, merchant];
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
        // Selected + health-aware: amber if the provider is unhealthy.
        return merchantStore.isMerchantHealthy(merchant.name) ? 'primary' : 'amber-7';
    }

    function storeChipIcon(merchant: Merchant): string | undefined {
        if (!merchant.is_enabled) return 'block';
        if (!merchantStore.isMerchantHealthy(merchant.name)) return 'cloud_off';
        return undefined;
    }

    function storeTooltip(merchant: Merchant): string {
        if (!merchant.is_enabled) {
            return `${merchant.name} is disabled. Enable it under Settings → Merchants.`;
        }
        if (!merchantStore.isMerchantHealthy(merchant.name)) {
            return `${merchant.name}'s scraper failed its last health check — results may be slow or empty.`;
        }
        const health = merchantStore.healthForMerchant(merchant.name);
        if (!health) return `${merchant.name} — health unknown.`;
        if (health.skipped) return `${merchant.name} — last health check was skipped.`;
        return `${merchant.name} — last health check passed.`;
    }

    // Sort + quick filters: a writable mirror of the store state.
    const sortModel = computed<IOfferSortByOption>({
        get: () => productStore.productSearchOfferFilters.sortBy,
        set: (v) => productStore.setProductSearchSortByFilter(v)
    });

    function toggleAvailableFilter(): void {
        productStore.toggleProductSearchFilter('showOnlyAvailable');
    }
    function toggleSpecialsFilter(): void {
        productStore.toggleProductSearchFilter('showOnlySpecials');
    }
    function clearTransientFilters(): void {
        if (productStore.productSearchOfferFilters.showOnlyAvailable) toggleAvailableFilter();
        if (productStore.productSearchOfferFilters.showOnlySpecials) toggleSpecialsFilter();
    }

    const filteredOffers = computed(() => productStore.filteredProductOffers);

    // Surface a network failure once via a notify (the banner stays so users
    // can read + retry; the toast just draws attention).
    watch(searchError, (err) => {
        if (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Search failed. Check connection and try again.',
                timeout: 4000
            });
        }
    });

    // ── Save toggle (with toast feedback) ────────────────────────────────
    async function onSaveToggle(offer: ScrapedProductOffer): Promise<void> {
        const { is_saved_product_active, merchant_name, merchant_stockcode } = offer;

        const existing = productStore.products?.find(
            (p) =>
                p.merchant_name === merchant_name &&
                p.merchant_stockcode === merchant_stockcode
        );

        try {
            if (existing) {
                await productStore.updateProductAsync({
                    is_active: !is_saved_product_active,
                    product_id: existing.product_id
                });
                productStore.updateProductOffer({
                    is_saved_product_active: !is_saved_product_active,
                    merchant_name,
                    merchant_stockcode
                });
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message: !is_saved_product_active
                        ? `Re-saved ${offer.name}.`
                        : `Removed ${offer.name} from saved products.`
                });
            } else {
                await productStore.createProductAsync({
                    ...offer,
                    is_active: true
                });
                productStore.updateProductOffer({
                    is_saved: true,
                    is_saved_product_active: true,
                    merchant_name,
                    merchant_stockcode
                });
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Saved ${offer.name}.`
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update the saved product.',
                caption: String(err)
            });
        }
    }

    onMounted(async () => {
        // Health is best-effort: if merchant_api isn't running we still want
        // the page to load with whatever merchant list we managed to fetch.
        await Promise.all([
            merchantStore.getMerchantsAsync(),
            merchantStore.getProviderHealthAsync(),
            productStore.getProductsAsync()
        ]);
    });
</script>

<style scoped>
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
        background: #fef3d8;
        padding: 8px;
        flex-shrink: 0;
    }
    .dora-empty-text {
        font-size: 1.15rem;
        line-height: 1.5;
        color: #2e2820;
    }

    @media (max-width: 600px) {
        .dora-empty {
            flex-direction: column;
            text-align: center;
        }
    }
</style>
