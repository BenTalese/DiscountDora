<template>
    <q-page padding>
        <!-- ── Header ─────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md">
            <!-- Counts moved to the sticky PageCountsFooter (A7). -->
            <q-space />
            <BaseButton
                variant="secondary"
                :icon="ICONS.link_off"
                :label="`Stock items without products (${stockItemsMissingProducts.length})`"
                class="q-mr-sm"
                :disable="stockItemsMissingProducts.length === 0"
                @click="orphansOpen = true"
            />
            <BaseButton
                variant="secondary"
                :icon="ICONS.refresh"
                label="Refresh"
                :loading="loading"
                @click="loadAll"
            />
        </div>

        <!-- ── Bulk-select banner ─────────────────────────────────── -->
        <q-banner
            v-if="filteredProducts.length > 0"
            class="q-mb-sm bulk-bar"
            :class="{ 'bulk-bar-active': bulkMode }"
            dense
            rounded
        >
            <template #avatar>
                <q-icon :name="bulkMode ? 'checklist' : 'list_alt'" />
            </template>
            <span v-if="!bulkMode">
                Select products to add them to a list, unlink, or mark inactive.
            </span>
            <span v-else>
                {{ selectedIds.size }} selected
            </span>
            <template #action>
                <template v-if="!bulkMode">
                    <q-btn
                        flat
                        no-caps
                        :icon="ICONS.checklist"
                        label="Select"
                        @click="enterBulkMode"
                    />
                </template>
                <template v-else>
                    <q-btn
                        flat
                        no-caps
                        label="Select all visible"
                        @click="selectAllVisible"
                    />
                    <q-btn
                        flat
                        no-caps
                        label="Select on-deal"
                        @click="selectOnDealVisible"
                    />
                    <q-btn
                        flat
                        no-caps
                        :icon="ICONS.add_shopping_cart"
                        :label="`Add ${onDealSelectedCount} on-deal to list`"
                        color="primary"
                        :disable="onDealSelectedCount === 0"
                        :loading="bulkBusy"
                        @click="onBulkAddOnDeal"
                    />
                    <q-btn
                        flat
                        no-caps
                        :icon="ICONS.link_off"
                        label="Unlink"
                        :disable="selectedIds.size === 0"
                        :loading="bulkBusy"
                        @click="onBulkUnlink"
                    />
                    <q-btn
                        flat
                        no-caps
                        :icon="ICONS.visibility_off"
                        label="Mark inactive"
                        :disable="selectedIds.size === 0"
                        :loading="bulkBusy"
                        @click="onBulkInactive"
                    />
                    <q-btn flat no-caps label="Done" @click="exitBulkMode" />
                </template>
            </template>
        </q-banner>

        <!-- ── Filters ─ standardised via FilterBar (A4) ──────────── -->
        <FilterBar :active-count="activeFilterCount" @clear="clearFilters">
            <template #search>
                <q-input
                    v-model="searchText"
                    dense
                    outlined
                    clearable
                    debounce="200"
                    placeholder="Search products"
                >
                    <template #append><q-icon :name="ICONS.search" /></template>
                </q-input>
            </template>
            <template #filters>
            <div class="row q-gutter-sm items-center">
            <q-toggle v-model="onDealOnly" label="On deal now" dense />
            <q-toggle v-model="includeInactive" label="Show inactive" dense />
            <q-select
                v-model="merchantFilter"
                outlined
                dense
                emit-value
                map-options
                clearable
                :options="merchantOptions"
                label="Merchant"
                style="min-width: 180px"
            />
            <q-select
                v-model="linkedStockItemFilter"
                outlined
                dense
                emit-value
                map-options
                clearable
                use-input
                input-debounce="150"
                :options="linkedStockItemOptions"
                @filter="onLinkedFilter"
                label="Linked stock item"
                style="min-width: 240px"
            />
            </div>
            </template>
        </FilterBar>

        <!-- ── Grid ───────────────────────────────────────────────── -->
        <FadeTransition mode="out-in">
        <div
            v-if="loading && products.length === 0"
            key="prod-loading"
            class="text-center q-py-xl"
        >
            <AppSpinner size="48px" />
        </div>

        <q-banner v-else-if="loadError" key="prod-error" class="dora-bg-negative-soft text-negative" dense rounded>
            {{ loadError }}
        </q-banner>

        <div
            v-else-if="filteredProducts.length === 0"
            key="prod-empty"
            class="text-center dora-text-muted q-py-xl"
        >
            <q-icon :name="ICONS.shopping_bag" size="60px" class="q-mb-sm" />
            <div v-if="products.length === 0">
                You haven't saved any products yet. Use Product Search to find and
                save deals.
            </div>
            <div v-else>No products match the current filters.</div>
            <q-btn
                v-if="products.length === 0"
                color="primary"
                no-caps
                :icon="ICONS.search"
                label="Open Product Search"
                class="q-mt-md"
                to="/product-search"
            />
            <q-btn
                v-else-if="hasAnyFilter"
                flat
                no-caps
                color="primary"
                label="Clear filters"
                class="q-mt-md"
                @click="clearFilters"
            />
        </div>

        <div v-else key="prod-content" class="row q-col-gutter-md">
            <div
                v-for="product in filteredProducts"
                :key="product.product_id"
                class="col-12 col-sm-6 col-md-4 col-lg-3"
            >
                <q-card
                    flat
                    bordered
                    class="my-product-card"
                    :class="{
                        'my-product-card--selected': selectedIds.has(product.product_id),
                        'my-product-card--inactive': !product.is_active,
                    }"
                    @click="onCardClick(product.product_id)"
                >
                    <q-card-section class="row items-start q-pb-sm q-gutter-xs">
                        <q-checkbox
                            v-if="bulkMode"
                            :model-value="selectedIds.has(product.product_id)"
                            dense
                            @click.stop
                            @update:model-value="toggleSelect(product.product_id)"
                        />
                        <q-avatar v-else rounded size="40px" class="dora-bg-sunken">
                            <img v-if="product.image" :src="product.image" :alt="product.name" />
                            <q-icon v-else :name="ICONS.shopping_bag" size="20px" />
                        </q-avatar>
                        <div class="col">
                            <div class="text-subtitle2 ellipsis-2-lines">
                                {{ product.name }}
                            </div>
                            <div class="text-caption dora-text-muted">
                                <span v-if="product.brand">{{ product.brand }}</span>
                                <span v-if="product.brand && product.size"> · </span>
                                <span v-if="product.size">{{ product.size }}</span>
                            </div>
                        </div>
                        <q-badge
                            v-if="discountPct(product) !== null"
                            color="negative"
                            text-color="white"
                        >
                            {{ discountPct(product) }}% off
                        </q-badge>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row items-baseline q-gutter-xs">
                            <span class="text-h6">
                                ${{ (product.price_now ?? 0).toFixed(2) }}
                            </span>
                            <span
                                v-if="onSpecial(product)"
                                class="text-caption dora-text-muted strike"
                            >
                                ${{ (product.price_was ?? 0).toFixed(2) }}
                            </span>
                        </div>
                        <div class="text-caption dora-text-muted">
                            <MerchantLogo
                                v-if="product.merchant_name"
                                :name="product.merchant_name"
                                :height="14"
                                :width="24"
                                class="q-mr-xs"
                            />
                            {{ product.merchant_name || '—' }}
                        </div>
                    </q-card-section>

                    <q-separator />
                    <q-card-section class="q-py-sm">
                        <div v-if="product.linked_stock_item_id" class="row items-center q-gutter-xs">
                            <q-chip
                                dense
                                clickable
                                color="primary"
                                text-color="white"
                                :icon="ICONS.link"
                                @click.stop="goToStockItem(product.linked_stock_item_id!)"
                            >
                                {{ product.linked_stock_item_name ?? 'Stock item' }}
                                <q-tooltip>Open stock item</q-tooltip>
                            </q-chip>
                        </div>
                        <div v-else class="text-caption dora-text-muted">
                            <q-icon :name="ICONS.link_off" size="14px" />
                            Not linked to any stock item.
                            <a
                                href="#"
                                class="text-primary"
                                @click.stop.prevent="openLinkDialog(product)"
                            >
                                Link…
                            </a>
                        </div>
                        <q-badge
                            v-if="!product.is_active"
                            color="grey"
                            text-color="white"
                            class="q-mt-xs"
                        >
                            Inactive
                        </q-badge>
                        <q-badge
                            v-if="!product.is_available"
                            color="warning"
                            text-color="white"
                            class="q-mt-xs q-ml-xs"
                        >
                            Out of stock
                        </q-badge>
                    </q-card-section>

                    <q-separator />
                    <q-card-actions align="right" class="q-py-sm">
                        <q-btn
                            v-if="product.web_url"
                            flat
                            dense
                            no-caps
                            :icon="ICONS.open_in_new"
                            :href="product.web_url"
                            target="_blank"
                            rel="noopener"
                            @click.stop
                        >
                            <q-tooltip>Open at merchant</q-tooltip>
                        </q-btn>
                        <q-btn
                            flat
                            dense
                            no-caps
                            :icon="ICONS.add_shopping_cart"
                            color="primary"
                            :disable="!product.linked_stock_item_id"
                            @click.stop="onAddSingle(product)"
                        >
                            <q-tooltip>
                                {{ product.linked_stock_item_id
                                    ? 'Add the linked stock item to your primary list'
                                    : 'Link to a stock item first.'
                                }}
                            </q-tooltip>
                        </q-btn>
                        <q-btn flat round dense :icon="ICONS.more_vert" @click.stop>
                            <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                                <q-list dense style="min-width: 200px">
                                    <q-item
                                        v-if="product.linked_stock_item_id"
                                        clickable
                                        @click="goToStockItem(product.linked_stock_item_id!)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon name="inventory_2" />
                                        </q-item-section>
                                        <q-item-section>Open stock item</q-item-section>
                                    </q-item>
                                    <q-item
                                        v-if="product.linked_stock_item_id"
                                        clickable
                                        @click="onUnlinkSingle(product)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.link_off" />
                                        </q-item-section>
                                        <q-item-section>Unlink</q-item-section>
                                    </q-item>
                                    <q-item
                                        v-else
                                        clickable
                                        @click="openLinkDialog(product)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.link" />
                                        </q-item-section>
                                        <q-item-section>Link to stock item…</q-item-section>
                                    </q-item>
                                    <q-separator />
                                    <q-item clickable @click="onToggleActive(product)">
                                        <q-item-section avatar>
                                            <q-icon
                                                :name="product.is_active ? 'visibility_off' : 'visibility'"
                                            />
                                        </q-item-section>
                                        <q-item-section>
                                            {{ product.is_active ? 'Mark inactive' : 'Mark active' }}
                                        </q-item-section>
                                    </q-item>
                                    <q-separator />
                                    <q-item
                                        clickable
                                        @click="onViewPriceHistory(product.product_id)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.show_chart" />
                                        </q-item-section>
                                        <q-item-section>View price history</q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-card-actions>
                </q-card>
            </div>
        </div>
        </FadeTransition>

        <PageCountsFooter v-if="products.length > 0" :counts="footerCounts" />

        <!-- ── Bulk-add target-list picker ────────────────────────── -->
        <BaseDialog v-model="bulkAddOpen" card-style="min-width: 380px">
                <q-card-section>
                    <div class="text-h6">Add to which list?</div>
                    <div class="text-caption dora-text-muted">
                        {{ bulkAddCandidates.length }} stock item{{
                            bulkAddCandidates.length === 1 ? '' : 's'
                        }} from on-deal products in your selection.
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-select
                        v-model="bulkAddTargetListId"
                        outlined
                        dense
                        emit-value
                        map-options
                        :options="activeListOptions"
                        label="Active list"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        unelevated
                        color="primary"
                        no-caps
                        label="Add"
                        :loading="bulkBusy"
                        :disable="!bulkAddTargetListId"
                        @click="confirmBulkAdd"
                    />
                </q-card-actions>
        </BaseDialog>

        <!-- ── Stock items without products dialog ────────────────── -->
        <BaseDialog
            v-model="orphansOpen"
            :maximized="$q.screen.lt.sm"
            card-style="width: 560px; max-width: 100vw; height: 90vh"
            card-class="column"
        >
                <q-card-section class="row items-center q-pb-sm">
                    <div>
                        <div class="text-h6">Stock items without products</div>
                        <div class="text-caption dora-text-muted">
                            {{ stockItemsMissingProducts.length }} item{{
                                stockItemsMissingProducts.length === 1 ? '' : 's'
                            }} that no product in My Products is linked to.
                            Hop into Product Search to find one.
                        </div>
                    </div>
                    <q-space />
                    <q-btn flat round dense :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-separator />
                <q-card-section class="col scroll">
                    <q-list separator>
                        <q-item
                            v-for="item in stockItemsMissingProducts"
                            :key="item.stock_item_id"
                        >
                            <q-item-section avatar>
                                <q-avatar :color="levelColourFor(item)" text-color="white" size="32px">
                                    <q-icon name="inventory_2" size="16px" />
                                </q-avatar>
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ item.name }}</q-item-label>
                                <q-item-label caption>
                                    {{ levelNameFor(item) ?? 'No level' }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs">
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        :icon="ICONS.search"
                                        color="primary"
                                        @click="searchForOrphan(item)"
                                    >
                                        <q-tooltip>Find a product</q-tooltip>
                                    </q-btn>
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        :icon="ICONS.open_in_new"
                                        @click="goToStockItem(item.stock_item_id)"
                                    >
                                        <q-tooltip>Open stock item</q-tooltip>
                                    </q-btn>
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>

        <!-- ── Link-to-stock-item dialog ──────────────────────────── -->
        <BaseDialog v-model="linkOpen" card-style="min-width: 420px">
                <q-card-section>
                    <div class="text-h6">Link to a stock item</div>
                    <div class="text-caption dora-text-muted">
                        {{ linkTarget?.name }}
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-select
                        v-model="linkChoiceStockItemId"
                        outlined
                        dense
                        use-input
                        input-debounce="150"
                        :options="linkStockItemOptions"
                        emit-value
                        map-options
                        clearable
                        @filter="onLinkPickerFilter"
                        label="Stock item"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        unelevated
                        color="primary"
                        no-caps
                        label="Link"
                        :loading="linkBusy"
                        :disable="!linkChoiceStockItemId"
                        @click="confirmLink"
                    />
                </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import PageCountsFooter from 'src/components/PageCountsFooter.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import MerchantLogo from 'src/components/MerchantLogo.vue';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { Product } from 'src/models/product';
    import type { StockItem } from 'src/models/stockItem';
    import type { StockLevelName } from 'src/models/stockLevel';
    import ProductApiService from 'src/services/api/productApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const productApi = new ProductApiService();
    const stockItemApi = new StockItemApiService();
    const shoppingListStore = useShoppingListStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { addItems } = useShoppingListActions();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const products = ref<Product[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    async function loadAll() {
        loading.value = true;
        loadError.value = null;
        try {
            const [page] = await Promise.all([
                productApi.getAllAsync(),
                stockItems.value.length === 0
                    ? stockItemStore.getStockItemsAsync()
                    : Promise.resolve(),
                stockLevels.value.length === 0
                    ? stockLevelStore.getStockLevelsAsync()
                    : Promise.resolve(),
                shoppingListStore.refreshAsync(),
            ]);
            products.value = page.items;
        } catch (err) {
            loadError.value = `Could not load: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    // ── Filters ─────────────────────────────────────────────────────
    const searchText = ref('');
    const onDealOnly = ref(false);
    const includeInactive = ref(false);
    const merchantFilter = ref<string | null>(null);
    const linkedStockItemFilter = ref<string | null>(null);
    const linkedStockItemPickerText = ref('');

    function onLinkedFilter(value: string, update: (cb: () => void) => void) {
        update(() => {
            linkedStockItemPickerText.value = value;
        });
    }

    function discountPct(product: Product): number | null {
        if (!product.price_was || !product.price_now) return null;
        if (product.price_was <= product.price_now) return null;
        return Math.round(((product.price_was - product.price_now) / product.price_was) * 100);
    }
    function onSpecial(product: Product): boolean {
        return discountPct(product) !== null;
    }

    const merchantOptions = computed(() => {
        const names = [...new Set(products.value.map((p) => p.merchant_name).filter(Boolean))];
        return names.sort().map((n) => ({ label: n, value: n }));
    });

    const linkedStockItemOptions = computed(() => {
        // List of stock items that are linked to *some* product in this set
        // — so users can filter the grid down to one specific item.
        const linkedIds = new Set(
            products.value
                .map((p) => p.linked_stock_item_id)
                .filter((id): id is string => Boolean(id)),
        );
        const q = linkedStockItemPickerText.value.trim().toLowerCase();
        return stockItems.value
            .filter((s) => linkedIds.has(s.stock_item_id))
            .filter((s) => !q || s.name.toLowerCase().includes(q))
            .map((s) => ({ label: s.name, value: s.stock_item_id }));
    });

    const filteredProducts = computed(() =>
        products.value.filter((p) => {
            if (!includeInactive.value && !p.is_active) return false;
            if (onDealOnly.value && !onSpecial(p)) return false;
            // A4: explicit "empty = off" — a null selection skips the predicate.
            if (merchantFilter.value !== null && p.merchant_name !== merchantFilter.value)
                return false;
            if (
                linkedStockItemFilter.value !== null
                && p.linked_stock_item_id !== linkedStockItemFilter.value
            )
                return false;
            if (searchText.value) {
                const q = searchText.value.toLowerCase();
                const haystack = [
                    p.name,
                    p.brand,
                    p.merchant_name,
                    p.linked_stock_item_name ?? '',
                    p.size,
                ]
                    .filter(Boolean)
                    .join(' ')
                    .toLowerCase();
                if (!haystack.includes(q)) return false;
            }
            return true;
        }),
    );

    // A7 — sticky footer counts over the FILTERED view.
    const footerCounts = computed(() => [
        { label: 'Shown', value: filteredProducts.value.length, tone: 'primary' as const },
        {
            label: 'On deal',
            value: filteredProducts.value.filter(onSpecial).length,
            tone: 'positive' as const,
        },
        {
            label: 'Unlinked',
            value: filteredProducts.value.filter((p) => !p.linked_stock_item_id).length,
            tone: 'warning' as const,
        },
    ]);

    const hasAnyFilter = computed(
        () =>
            searchText.value !== ''
            || onDealOnly.value
            || includeInactive.value
            || merchantFilter.value !== null
            || linkedStockItemFilter.value !== null,
    );
    // Active-filter count for the FilterBar badge (excludes the search box).
    const activeFilterCount = computed(() => {
        let n = 0;
        if (onDealOnly.value) n++;
        if (includeInactive.value) n++;
        if (merchantFilter.value !== null) n++;
        if (linkedStockItemFilter.value !== null) n++;
        return n;
    });
    function clearFilters() {
        searchText.value = '';
        onDealOnly.value = false;
        includeInactive.value = false;
        merchantFilter.value = null;
        linkedStockItemFilter.value = null;
    }

    // ── Bulk-select ─────────────────────────────────────────────────
    const bulkMode = ref(false);
    const selectedIds = ref<Set<string>>(new Set());
    const bulkBusy = ref(false);

    function enterBulkMode() {
        bulkMode.value = true;
        selectedIds.value = new Set();
    }
    function exitBulkMode() {
        bulkMode.value = false;
        selectedIds.value = new Set();
    }
    function toggleSelect(productId: string) {
        const next = new Set(selectedIds.value);
        if (next.has(productId)) next.delete(productId);
        else next.add(productId);
        selectedIds.value = next;
    }
    function onCardClick(productId: string) {
        if (bulkMode.value) toggleSelect(productId);
    }
    function selectAllVisible() {
        selectedIds.value = new Set(filteredProducts.value.map((p) => p.product_id));
    }
    function selectOnDealVisible() {
        selectedIds.value = new Set(
            filteredProducts.value.filter(onSpecial).map((p) => p.product_id),
        );
    }

    const onDealSelectedCount = computed(
        () =>
            products.value.filter(
                (p) => selectedIds.value.has(p.product_id) && onSpecial(p),
            ).length,
    );

    // ── Bulk add on-deal to a list ──────────────────────────────────
    const bulkAddOpen = ref(false);
    const bulkAddTargetListId = ref<string | null>(null);

    const activeListOptions = computed(() =>
        shoppingListStore.summaries
            .filter((s) => s.status !== 'done')
            .map((s) => ({
                label: s.name + (s.is_primary ? ' (primary)' : ''),
                value: s.shopping_list_id,
            })),
    );

    const bulkAddCandidates = computed(() =>
        products.value.filter(
            (p) =>
                selectedIds.value.has(p.product_id)
                && onSpecial(p)
                && Boolean(p.linked_stock_item_id),
        ),
    );

    function onBulkAddOnDeal() {
        if (bulkAddCandidates.value.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message:
                    'Nothing to add — selected on-deal products need a linked stock item.',
            });
            return;
        }
        bulkAddTargetListId.value =
            shoppingListStore.primaryListId ?? activeListOptions.value[0]?.value ?? null;
        if (!bulkAddTargetListId.value) {
            $q.dialog({
                title: 'No active shopping list',
                message: 'Create or unarchive one first.',
                ok: { label: 'Open lists', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists'); });
            return;
        }
        bulkAddOpen.value = true;
    }

    async function confirmBulkAdd() {
        if (!bulkAddTargetListId.value) return;
        bulkBusy.value = true;
        try {
            // Each candidate carries the merchant-product to pre-select so
            // the line opens with the deal already picked, not "cheapest".
            await addItems(
                bulkAddTargetListId.value,
                bulkAddCandidates.value.map((p) => ({
                    stock_item_id: p.linked_stock_item_id!,
                    selected_product_id: p.product_id,
                })),
            );
            bulkAddOpen.value = false;
            exitBulkMode();
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Bulk unlink ─────────────────────────────────────────────────
    async function onBulkUnlink() {
        const targets = products.value.filter(
            (p) => selectedIds.value.has(p.product_id) && p.linked_stock_item_id,
        );
        if (targets.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'None of the selected products are linked.',
            });
            return;
        }
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Unlink ${targets.length} product${targets.length === 1 ? '' : 's'}?`,
                message:
                    'They stay in My Products, but stop showing on the stock items they were linked to.',
                ok: { label: 'Unlink', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        bulkBusy.value = true;
        try {
            for (const product of targets) {
                if (!product.linked_stock_item_id) continue;
                await stockItemApi.unlinkProductAsync(
                    product.linked_stock_item_id,
                    product.product_id,
                );
            }
            await loadAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Unlinked ${targets.length} product${targets.length === 1 ? '' : 's'}.`,
            });
            exitBulkMode();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not unlink everything.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Bulk mark inactive ──────────────────────────────────────────
    async function onBulkInactive() {
        const targets = products.value.filter(
            (p) => selectedIds.value.has(p.product_id) && p.is_active,
        );
        if (targets.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'Nothing to mark inactive — all selected are already inactive.',
            });
            return;
        }
        bulkBusy.value = true;
        try {
            for (const product of targets) {
                await productApi.updateAsync({
                    product_id: product.product_id,
                    is_active: false,
                });
            }
            await loadAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Marked ${targets.length} inactive.`,
            });
            exitBulkMode();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Per-product actions ─────────────────────────────────────────
    async function onAddSingle(product: Product) {
        if (!product.linked_stock_item_id) return;
        const primary = shoppingListStore.primaryListId;
        if (!primary) {
            $q.dialog({
                title: 'No primary list',
                message: 'Set a primary shopping list to use the cart shortcut.',
                ok: { label: 'Open lists', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists'); });
            return;
        }
        await addItems(primary, [
            {
                stock_item_id: product.linked_stock_item_id,
                selected_product_id: product.product_id,
            },
        ]);
    }

    async function onUnlinkSingle(product: Product) {
        if (!product.linked_stock_item_id) return;
        try {
            await stockItemApi.unlinkProductAsync(
                product.linked_stock_item_id,
                product.product_id,
            );
            await loadAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Unlinked.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not unlink.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onToggleActive(product: Product) {
        try {
            await productApi.updateAsync({
                product_id: product.product_id,
                is_active: !product.is_active,
            });
            await loadAll();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function goToStockItem(stockItemId: string) {
        void router.push(`/stock/${stockItemId}`);
    }

    function onViewPriceHistory(productId: string) {
        void router.push({ path: '/price-history', query: { product_id: productId } });
    }

    // ── Link-to-stock-item dialog ───────────────────────────────────
    // We don't have a "link" endpoint exposed yet, so this is wired up to
    // delegate to the stock item page where linking happens today. Future
    // backend work can let this dialog do the link inline.
    const linkOpen = ref(false);
    const linkTarget = ref<Product | null>(null);
    const linkChoiceStockItemId = ref<string | null>(null);
    const linkPickerText = ref('');
    const linkBusy = ref(false);

    function onLinkPickerFilter(value: string, update: (cb: () => void) => void) {
        update(() => {
            linkPickerText.value = value;
        });
    }

    const linkStockItemOptions = computed(() => {
        const q = linkPickerText.value.trim().toLowerCase();
        return stockItems.value
            .filter((s) => !q || s.name.toLowerCase().includes(q))
            .slice(0, 50)
            .map((s) => ({ label: s.name, value: s.stock_item_id }));
    });

    function openLinkDialog(product: Product) {
        linkTarget.value = product;
        linkChoiceStockItemId.value = null;
        linkPickerText.value = '';
        linkOpen.value = true;
    }

    function confirmLink() {
        if (!linkTarget.value || !linkChoiceStockItemId.value) return;
        linkBusy.value = true;
        try {
            // Linking happens on the stock-item side (it owns the m2m
            // collection). We bounce the user there with a query hint;
            // the stock item detail page already has the product picker.
            const stockItemId = linkChoiceStockItemId.value;
            const productId = linkTarget.value.product_id;
            linkOpen.value = false;
            void router.push({
                path: `/stock/${stockItemId}`,
                query: { link_product_id: productId, section: 'products' },
            });
        } finally {
            linkBusy.value = false;
        }
    }

    // ── Stock items without products ────────────────────────────────
    const orphansOpen = ref(false);

    const stockItemsMissingProducts = computed<StockItem[]>(() => {
        const linkedIds = new Set(
            products.value
                .filter((p) => p.is_active && p.linked_stock_item_id)
                .map((p) => p.linked_stock_item_id as string),
        );
        return stockItems.value.filter((s) => !linkedIds.has(s.stock_item_id));
    });

    function levelNameFor(item: StockItem): StockLevelName | null {
        return (
            (stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)
                ?.name) ?? null
        );
    }
    function levelColourFor(item: StockItem): string {
        const name = levelNameFor(item);
        return name ? getStockLevelColour(name) : 'grey';
    }

    function searchForOrphan(item: StockItem) {
        orphansOpen.value = false;
        void router.push({
            path: '/product-search',
            query: { stock_item_id: item.stock_item_id, q: item.name },
        });
    }

    onMounted(loadAll);
</script>

<style scoped>
    .my-product-card {
        height: 100%;
        transition: outline-color 120ms ease, box-shadow 120ms ease;
        outline: 2px solid transparent;
        outline-offset: -2px;
    }
    .my-product-card:hover {
        box-shadow: 0 4px 14px var(--overlay-active);
    }
    .my-product-card--selected {
        outline-color: var(--q-primary);
    }
    .my-product-card--inactive {
        opacity: 0.6;
    }
    .strike {
        text-decoration: line-through;
    }
    .bulk-bar {
        background: var(--overlay-hover);
    }
    .bulk-bar-active {
        background: var(--brand-primary-soft);
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
