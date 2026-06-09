<template>
    <div class="q-pa-md">
        <!-- Header bar — C-1 Chunk 2 / L94: one button group across the
             top in this order: New item · Export · Bulk select · Scan ·
             Stocktake. Search stays separate on the right (L99). -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <BaseButton variant="primary" :icon="ICONS.add" label="New item" @click="onCreateClick" />
            <q-btn-dropdown flat no-caps :icon="ICONS.more_horiz" label="Export">
                <q-list dense style="min-width: 200px">
                    <!-- C-1 Chunk 1 / L67 — both exports respect the
                         currently filtered set. `filteredIds` is undefined
                         when no filters are active so the server-side
                         fast-path stays "export everything". -->
                    <q-item clickable v-close-popup @click="overviewExport.downloadCsv(filteredIds)">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.file_download" />
                        </q-item-section>
                        <q-item-section>Export as CSV</q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup @click="overviewExport.openPrintView(filteredIds)">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.print" />
                        </q-item-section>
                        <q-item-section>Print / Save as PDF</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
            <BaseButton
                v-if="!bulkMode"
                variant="secondary"
                :icon="ICONS.checklist"
                label="Bulk select"
                @click="bulkMode = true"
            />
            <BaseButton
                v-else
                variant="secondary"
                :icon="ICONS.close"
                label="Cancel"
                @click="cancelBulk"
            />
            <BaseButton
                v-if="scanningEnabled"
                variant="secondary"
                :icon="ICONS.qr_code_scanner"
                label="Scan"
                @click="overviewScanOpen = true"
            />
            <BaseButton
                variant="secondary"
                :icon="ICONS.fact_check"
                :label="stocktakeOverdue > 0 ? `Stocktake (${stocktakeOverdue})` : 'Stocktake'"
                :attention="stocktakeOverdue > 0"
                to="/stocktake"
            />
            <q-space />
            <!-- C-1 Chunk 3 / FU-106 — inline image-toggle. Flips the
                 per-user `show_stock_images` flag; the row's image
                 slot collapses out of the layout when off. Sits next
                 to the search input so it's reachable without
                 expanding filters. -->
            <q-btn
                flat
                dense
                round
                :icon="showStockImages ? ICONS.image : ICONS.image_not_supported"
                :aria-label="showStockImages ? 'Hide row images' : 'Show row images'"
                :loading="imageToggleBusy"
                @click="onToggleStockImages"
            >
                <q-tooltip>
                    {{ showStockImages ? 'Hide row images (denser rows)' : 'Show row images' }}
                </q-tooltip>
            </q-btn>
            <q-input
                ref="searchInputRef"
                v-model="filters.searchText.value"
                outlined
                dense
                debounce="150"
                placeholder="Search"
                clearable
                autofocus
                style="min-width: 280px"
            >
                <template #prepend>
                    <q-icon :name="ICONS.search" />
                </template>
            </q-input>
        </div>

        <!-- Summary counts moved to the sticky PageCountsFooter (A7). -->

        <!-- Quick filters ─ standardised via FilterBar (A4) ────────────── -->
        <!-- C-1 Chunk 2 / L94: Bulk-select moved up to the top button
             group; the filter bar no longer hosts page actions. -->
        <FilterBar :active-count="filters.activeFilterCount.value" @clear="filters.clearFilters">
            <template #filters>
            <div class="row q-gutter-sm items-center">
            <!-- C-1 Chunk 2 / L97 — single dropdown defaults to "Any level".
                 Per-level chips with count badges retired; counts live in
                 the sticky footer now (PageCountsFooter). -->
            <q-select
                v-model="filters.levelFilter.value"
                :options="levelFilterOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                dense
                outlined
                clearable
                label="Any level"
                style="min-width: 180px"
            />

            <q-separator vertical class="q-mx-sm" />

            <FilterChip v-model="filters.essentialsOnly.value" :icon="ICONS.flag" active-color="warning">
                Flagged for auto
            </FilterChip>

            <FilterChip v-model="filters.autoAddOnly.value" :icon="ICONS.bolt" active-color="primary">
                Will auto-add on low
            </FilterChip>

            <FilterChip v-model="filters.openOnly.value" :icon="ICONS.lock_open" active-color="secondary">
                Open / in-use
            </FilterChip>

            <FilterChip v-model="filters.hasAlertOnly.value" :icon="ICONS.warning" active-color="negative">
                Needs attention
            </FilterChip>

            <!-- C-1 Chunk 2 / L96 — "Used in a recipe" filter removed
                 (low signal; the recipe pages own that view). -->

            <q-chip
                v-if="filters.cartFilter.value !== 'all'"
                clickable
                color="primary"
                text-color="white"
                removable
                @remove="filters.cartFilter.value = 'all'"
            >
                <q-icon :name="ICONS.shopping_cart" size="14px" class="q-mr-xs" />
                {{ filters.cartFilter.value === 'on_list' ? 'On a list' : 'Not on any list' }}
            </q-chip>

            <q-select
                v-model="filters.locationFilter.value"
                :options="filters.locationOptions.value"
                dense
                outlined
                emit-value
                map-options
                clearable
                label="Any location"
                style="min-width: 180px"
            />

            <q-select
                v-model="filters.groupFilter.value"
                :options="filters.groupOptions.value"
                dense
                outlined
                emit-value
                map-options
                clearable
                label="Any group"
                style="min-width: 180px"
            />

            <q-select
                v-model="filters.sortBy.value"
                :options="STOCK_SORT_OPTIONS"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                outlined
                dense
                label="Sort by"
                style="min-width: 180px"
            />
            </div>
            </template>
        </FilterBar>

        <!-- Bulk action bar ───────────────────────────────────────────── -->
        <q-banner v-if="bulkMode" class="bg-primary dora-text-on-primary q-mb-md" dense rounded>
            <template #avatar>
                <q-icon :name="ICONS.checklist" />
            </template>
            {{ bulkSelection.size }} selected
            <template #action>
                <q-btn flat no-caps label="Select visible" color="white" @click="selectVisible" />
                <!-- C-7 Chunk 1 — unified bulk add: resolves the target
                     once + emits one summary toast (decision 6). -->
                <AddToListButton
                    variant="bulk"
                    class="text-white"
                    :items="[...bulkSelection]"
                    @bulk-done="cancelBulk"
                />
                <q-btn
                    flat
                    no-caps
                    label="Move location"
                    color="white"
                    :disable="bulkSelection.size === 0"
                    @click="openMoveDialog"
                />
                <q-btn
                    flat
                    no-caps
                    label="Mark restocked"
                    color="white"
                    :loading="bulkBusy"
                    :disable="bulkSelection.size === 0"
                    @click="bulkRestock"
                />
                <q-btn
                    flat
                    no-caps
                    label="Set substitute"
                    color="white"
                    :disable="bulkSelection.size === 0"
                    @click="bulkSetSubstitute"
                />
                <q-btn
                    v-if="scanningEnabled"
                    flat
                    no-caps
                    icon="qr_code_2"
                    label="Print QRs"
                    color="white"
                    :disable="bulkSelection.size === 0"
                    @click="bulkPrintQrs"
                />
            </template>
        </q-banner>

        <!-- Splitter: item list on the left, in-page detail peek on the right -->
        <q-splitter
            v-model="splitPct"
            :limits="[40, 100]"
            :disable="!peekId"
            unit="%"
            class="stock-splitter"
        >
            <template #before>
                <div class="q-pr-md">
                    <!-- C-1 Chunk 1 — small lists keep the glide-in
                         ListTransition (DS4 perceived-perf masking, see
                         STOCK_OVERVIEW_PERF.md); large lists swap to
                         q-virtual-scroll so a >50-item pantry actually
                         renders smoothly. Threshold matches the legacy
                         page-1 cap so behaviour stays familiar below it. -->
                    <ListTransition
                        v-if="filters.filteredStockItems.value.length > 0 && filters.filteredStockItems.value.length <= VIRTUAL_SCROLL_THRESHOLD"
                        tag="div"
                        class="q-list q-gutter-y-sm"
                    >
                        <StockItemRow
                            v-for="(item, idx) in filters.filteredStockItems.value"
                            :key="item.stock_item_id"
                            :item="item"
                            :bulk-mode="bulkMode"
                            :selected="bulkSelection.has(item.stock_item_id)"
                            :focused="focusedIndex === idx"
                            :peeking="peekId === item.stock_item_id"
                            @click="onRowClick"
                            @bulk-toggle="toggleBulk"
                            @filter-location="filters.locationFilter.value = $event"
                            @long-press="onRowLongPress"
                        />
                    </ListTransition>
                    <q-virtual-scroll
                        v-else-if="filters.filteredStockItems.value.length > VIRTUAL_SCROLL_THRESHOLD"
                        :items="filters.filteredStockItems.value"
                        :virtual-scroll-item-size="VIRTUAL_SCROLL_ITEM_SIZE"
                        :virtual-scroll-slice-size="30"
                        class="stock-virtual-scroll q-list q-gutter-y-sm"
                        v-slot="{ item, index }"
                    >
                        <StockItemRow
                            :key="item.stock_item_id"
                            :item="item"
                            :bulk-mode="bulkMode"
                            :selected="bulkSelection.has(item.stock_item_id)"
                            :focused="focusedIndex === index"
                            :peeking="peekId === item.stock_item_id"
                            @click="onRowClick"
                            @bulk-toggle="toggleBulk"
                            @filter-location="filters.locationFilter.value = $event"
                            @long-press="onRowLongPress"
                        />
                    </q-virtual-scroll>

                    <!-- Empty state ───────────────────────────────────── -->
                    <q-banner v-else class="dora-bg-sunken q-mt-md" rounded>
                        <template v-if="stockItems.length === 0">
                            <div class="text-subtitle1 q-mb-sm">Your pantry is empty.</div>
                            <div class="text-body2 q-mb-md dora-text-secondary">
                                Start by adding an item, or build your pantry from things you
                                already track elsewhere.
                            </div>
                            <div class="q-gutter-sm">
                                <BaseButton variant="primary" :icon="ICONS.add" label="New item" @click="onCreateClick" />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    :icon="ICONS.menu_book"
                                    label="Create from a recipe's ingredients"
                                    @click="goToRecipes"
                                />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    :icon="ICONS.shopping_cart"
                                    label="Import from a shopping list"
                                    @click="goToLists"
                                />
                            </div>
                        </template>
                        <template v-else>
                            No items match the current filters.
                            <q-btn flat dense no-caps label="Clear" @click="filters.clearFilters" />
                        </template>
                    </q-banner>
                </div>
            </template>

            <template #after>
                <div v-if="peekId" class="stock-peek">
                    <StockItemDetailPage
                        :id-override="peekId"
                        embedded
                        @close="peekId = null"
                    />
                </div>
            </template>
        </q-splitter>

        <PageCountsFooter v-if="stockItems.length > 0" :counts="filters.footerCounts.value" />

        <CreateStockItemDialog v-model="createDialogOpen" />

        <BulkMoveLocationDialog
            v-model="moveDialogOpen"
            :count="bulkSelection.size"
            :location-options="filters.locationOptions.value"
            :busy="bulkBusy"
            @confirm="bulkMove"
        />

        <!-- ── Scan (N5) — jumps to the matching item's detail page ── -->
        <ScanOverlay
            v-model="overviewScanOpen"
            close-on-decode
            @decoded="onOverviewScanDecoded"
        />
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import type { QInput } from 'quasar';
    import { useQuasar } from 'quasar';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import PageCountsFooter from 'src/components/PageCountsFooter.vue';
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import ScanOverlay from 'src/components/ScanOverlay.vue';
    import BulkMoveLocationDialog from 'src/components/stock/BulkMoveLocationDialog.vue';
    import CreateStockItemDialog from 'src/components/stock/CreateStockItemDialog.vue';
    import StockItemRow from 'src/components/stock/StockItemRow.vue';
    import ListTransition from 'src/components/transitions/ListTransition.vue';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useShortcut } from 'src/composables/useShortcut';
    import { useStockFilters, STOCK_SORT_OPTIONS } from 'src/composables/useStockFilters';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import type { Membership } from 'src/models/shoppingList';
    import type { StockGroup } from 'src/models/stockGroup';
    import { useStockOverviewExport } from 'src/composables/useStockOverviewExport';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import StocktakeApiService from 'src/services/api/stocktakeApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import StockItemDetailPage from 'src/pages/StockItemDetailPage.vue';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const { scanningEnabled } = useScanningEnabled();
    const stockGroupApi = new StockGroupApiService();
    const stockItemApi = new StockItemApiService();
    const barcodeApi = new BarcodeApiService();
    const overviewExport = useStockOverviewExport();
    const stocktakeApi = new StocktakeApiService();
    const stocktakeOverdue = ref(0);

    async function loadStocktakeCount() {
        try {
            const result = await stocktakeApi.queueAsync(1);
            stocktakeOverdue.value = result.total;
        } catch {
            stocktakeOverdue.value = 0;
        }
    }

    const router = useRouter();
    const route = useRoute();
    const actions = useStockItemActions();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const shoppingListStore = useShoppingListStore();
    const recipeStore = useRecipeStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);
    const { recipes } = storeToRefs(recipeStore);

    // Stock groups load locally — no store yet, only needed by the filter
    // dropdown on this page.
    const stockGroups = ref<StockGroup[]>([]);

    // C-1 Stock Overview Chunk 1 — virtualisation tuning. Below the
    // threshold we keep the existing ListTransition glide-in so small
    // pantries feel unchanged; above it we hand off to q-virtual-scroll
    // so a 500-item pantry renders smoothly. Item-size is a rough
    // average — Quasar self-corrects after the first measure.
    const VIRTUAL_SCROLL_THRESHOLD = 50;
    const VIRTUAL_SCROLL_ITEM_SIZE = 72;

    // C-1 Chunk 3 / FU-106 — inline image-toggle. Flips the per-user
    // `show_stock_images` flag via the C-cross composable.
    const { showStockImages, setStockImages } = useImagePrefs();
    const imageToggleBusy = ref(false);
    async function onToggleStockImages() {
        imageToggleBusy.value = true;
        try {
            await setStockImages(!showStockImages.value);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save image preference.',
            });
            void err;
        } finally {
            imageToggleBusy.value = false;
        }
    }

    const filters = useStockFilters({
        stockItems: () => stockItems.value,
        stockLevels: () => stockLevels.value,
        stockLocations: () => stockLocations.value,
        recipes: () => recipes.value,
        stockGroups: () => stockGroups.value,
        membership: () => shoppingListStore.membership as Membership | null,
    });

    // C-1 Chunk 2 / L97 — options for the level dropdown. Built off the
    // stockLevelStore so order matches the rest of the app.
    const levelFilterOptions = computed(() =>
        stockLevels.value.map((l) => ({
            value: l.stock_level_id,
            label: l.name,
        })),
    );

    // C-1 Chunk 1 / L67 — id list passed to the export endpoint when ANY
    // filter (text, level, location, …) is active. `undefined` keeps the
    // server-side "export everything" fast-path so unfiltered exports
    // don't push a URL with hundreds of UUIDs.
    const filteredIds = computed<string[] | undefined>(() => {
        const hasFilter =
            (filters.searchText.value ?? '').trim().length > 0
            || filters.activeFilterCount.value > 0;
        if (!hasFilter) return undefined;
        return filters.filteredStockItems.value.map((i) => i.stock_item_id);
    });

    // ── Splitter peek ────────────────────────────────────────────────────
    const peekId = ref<string | null>(null);
    const splitPct = ref(100);
    watch(peekId, (v) => (splitPct.value = v ? 58 : 100));

    // C-1 Chunk 5 / L68 / L71 — two-frame detail nav:
    //   Desktop  → splitter peek (the embedded drawer).
    //   Mobile   → full page navigation (`/stock/<id>`), no drawer.
    // One shared `StockItemDetailPage` powers both (L69). Bulk mode
    // wins over either; long-press enters bulk mode on mobile (see
    // `onRowLongPress` below).
    function onRowClick(stockItemId: string) {
        if (bulkMode.value) {
            toggleBulk(stockItemId);
            return;
        }
        if ($q.screen.lt.md) {
            void router.push(`/stock/${stockItemId}`);
            return;
        }
        peekId.value = peekId.value === stockItemId ? null : stockItemId;
    }

    // L72 — long-press on a stock row (mobile) enters bulk-select with
    // the held item already ticked. v-touch-hold on the row emits this
    // event; no-op on desktop where bulk-mode lives in the top toolbar.
    function onRowLongPress(stockItemId: string) {
        if (!$q.screen.lt.md) return;
        if (!bulkMode.value) bulkMode.value = true;
        if (!bulkSelection.value.has(stockItemId)) toggleBulk(stockItemId);
    }

    // ── Keyboard shortcuts (S5) ──────────────────────────────────────────
    const searchInputRef = ref<QInput | null>(null);
    const focusedIndex = ref(-1);

    function focusSearch() {
        searchInputRef.value?.focus();
    }
    function moveFocus(delta: number) {
        const count = filters.filteredStockItems.value.length;
        if (count === 0) return;
        focusedIndex.value = Math.max(0, Math.min(count - 1, focusedIndex.value + delta));
    }
    function openFocused() {
        const item = filters.filteredStockItems.value[focusedIndex.value];
        if (item) onRowClick(item.stock_item_id);
    }
    function addFocusedOrSelected() {
        if (bulkSelection.value.size > 0) {
            void bulkAddToPrimary();
            return;
        }
        const item = filters.filteredStockItems.value[focusedIndex.value];
        if (item) void actions.addToList(item.stock_item_id);
    }

    useShortcut([
        { keys: 'n', scope: 'Stock overview', description: 'New stock item', handler: onCreateClick },
        { keys: 'f', scope: 'Stock overview', description: 'Focus the filter/search', handler: focusSearch },
        { keys: '/', scope: 'Stock overview', description: 'Focus the filter/search', handler: focusSearch },
        { keys: 'a', scope: 'Stock overview', description: 'Add focused / selected to primary list', handler: addFocusedOrSelected },
        { keys: 'arrowdown', scope: 'Stock overview', description: 'Focus next item', handler: () => moveFocus(1) },
        { keys: 'arrowup', scope: 'Stock overview', description: 'Focus previous item', handler: () => moveFocus(-1) },
        { keys: 'arrowright', scope: 'Stock overview', description: 'Focus next item', handler: () => moveFocus(1) },
        { keys: 'arrowleft', scope: 'Stock overview', description: 'Focus previous item', handler: () => moveFocus(-1) },
        { keys: 'enter', scope: 'Stock overview', description: 'Open the focused item', handler: openFocused },
    ]);

    // ── Bulk select mode ─────────────────────────────────────────────────
    const bulkMode = ref(false);
    const bulkSelection = ref<Set<string>>(new Set());
    const bulkBusy = ref(false);

    function toggleBulk(id: string) {
        if (bulkSelection.value.has(id)) bulkSelection.value.delete(id);
        else bulkSelection.value.add(id);
        bulkSelection.value = new Set(bulkSelection.value);
    }
    function selectVisible() {
        for (const item of filters.filteredStockItems.value) {
            bulkSelection.value.add(item.stock_item_id);
        }
        bulkSelection.value = new Set(bulkSelection.value);
    }
    function cancelBulk() {
        bulkMode.value = false;
        bulkSelection.value = new Set();
    }

    async function bulkAddToPrimary() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) await actions.addToList(id);
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    async function bulkRestock() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) await actions.markRestocked(id);
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    function bulkSetSubstitute() {
        // Substitutes are managed on each item's detail page (StockItemDetail, P2).
        $q.notify({
            type: 'info',
            position: 'bottom-right',
            message: 'Setting substitutes arrives with the item detail revamp.',
        });
    }

    // ── Bulk move location ───────────────────────────────────────────────
    const moveDialogOpen = ref(false);
    function openMoveDialog() {
        moveDialogOpen.value = true;
    }
    async function bulkMove(locationId: string | null) {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) {
                await stockItemApi.moveAsync(id, locationId);
            }
            await stockItemStore.getStockItemsAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Items moved.',
            });
            moveDialogOpen.value = false;
            cancelBulk();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move items.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Navigation ───────────────────────────────────────────────────────
    // C-1 Chunk 3 — `goToList` retired with the "On N lists" chip; the
    // cart button owns the list interaction now.
    function goToRecipes() {
        void router.push('/recipes');
    }
    function goToLists() {
        void router.push('/shopping-lists');
    }

    // ── Create dialog ────────────────────────────────────────────────────
    const createDialogOpen = ref(false);
    function onCreateClick() {
        createDialogOpen.value = true;
    }

    // ── Bulk-print QRs (post-N5 polish) ───────────────────────────────────
    // Fires the same QR-sheet endpoint Data → Barcodes & QR uses, scoped to
    // the current bulk selection so the user can stocktake-print without
    // round-tripping through that page.
    function bulkPrintQrs() {
        if (bulkSelection.value.size === 0) return;
        overviewExport.openQrSheet(Array.from(bulkSelection.value));
    }

    // ── Scan overlay (N5) ────────────────────────────────────────────────
    // Same flow as Data → Barcodes & QR · Scan, but the success path jumps
    // straight to the matched item's detail page rather than opening an
    // inline modal — the user came here looking for a specific item.
    const overviewScanOpen = ref(false);
    async function onOverviewScanDecoded(value: string) {
        try {
            const result = await barcodeApi.lookupAsync(value);
            if (result.kind === 'stock_item') {
                overviewScanOpen.value = false;
                void router.push(`/stock/${result.id}`);
                return;
            }
            if (result.kind === 'product' && result.stock_item_id) {
                overviewScanOpen.value = false;
                void router.push(`/stock/${result.stock_item_id}`);
                return;
            }
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                message:
                    result.kind === 'product'
                        ? 'Product barcode not yet linked to a stock item.'
                        : "Unknown barcode — not linked to a product yet.",
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Lookup failed.',
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    async function loadStockGroups() {
        try {
            stockGroups.value = await stockGroupApi.getAllAsync();
        } catch {
            stockGroups.value = [];
        }
    }

    // Deep-link filter hydration: other screens (e.g. Locations) link here
    // with `?location_id=…&attention=true` to pre-narrow the list. Read those
    // on mount and reactively whenever the query changes (e.g. user uses
    // back/forward).
    function applyQueryFilters() {
        const q = route.query;
        if (typeof q.location_id === 'string' && q.location_id) {
            filters.locationFilter.value = q.location_id;
        }
        if (q.attention === 'true' || q.attention === '1') {
            filters.hasAlertOnly.value = true;
        }
        if (typeof q.level_id === 'string' && q.level_id) {
            filters.levelFilter.value = q.level_id;
        }
    }

    watch(
        () => [route.query.location_id, route.query.attention, route.query.level_id],
        applyQueryFilters,
    );

    // Open the create dialog when ?create=1 lands — works for both initial
    // arrivals (onMounted) and re-navigations from the command palette when
    // the page is already mounted (Vue Router updates query in place without
    // unmounting). The query is replaced away straight after so a refresh
    // doesn't reopen the dialog.
    function maybeOpenCreateFromQuery(): void {
        if (route.query.create === '1') {
            onCreateClick();
            void router.replace({ path: '/stock', query: {} });
        }
    }
    watch(() => route.query.create, () => maybeOpenCreateFromQuery());

    onMounted(async () => {
        await Promise.all([
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            stockLocationStore.getStockLocationsAsync(),
            shoppingListStore.refreshAsync(),
            recipeStore.getRecipesAsync(),
            loadStockGroups(),
            loadStocktakeCount(),
        ]);
        // Apply *after* the supporting data is loaded so the filter chips
        // visibly snap to the linked-from state on the first render.
        applyQueryFilters();
        maybeOpenCreateFromQuery();
    });
</script>

<style scoped>
    .stock-summary-banner {
        padding: 12px 16px;
        background: var(--overlay-hover);
        border-radius: 8px;
    }
    .stock-summary-stat {
        text-align: center;
        min-width: 84px;
    }
    .stock-splitter {
        min-height: 50vh;
    }
    .stock-peek {
        max-height: 80vh;
        overflow-y: auto;
    }
    /* C-1 Chunk 1 — virtualised list needs a sized scroll container.
       The viewport-relative height keeps the footer + top toolbar
       visible while the rows scroll inside the splitter pane. */
    .stock-virtual-scroll {
        max-height: calc(100vh - 320px);
        min-height: 240px;
        overflow-y: auto;
    }
</style>
