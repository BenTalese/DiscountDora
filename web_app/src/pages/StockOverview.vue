<template>
    <div class="q-pa-md">
        <!-- Header bar ───────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <q-btn color="positive" icon="add" label="New item" no-caps @click="onCreateClick" />
            <q-btn
                outline
                icon="qr_code_scanner"
                label="Scan"
                no-caps
                @click="overviewScanOpen = true"
            />
            <q-btn-dropdown flat no-caps icon="more_horiz" label="Export">
                <q-list dense style="min-width: 200px">
                    <q-item clickable v-close-popup @click="overviewExport.downloadCsv()">
                        <q-item-section avatar>
                            <q-icon name="file_download" />
                        </q-item-section>
                        <q-item-section>Export as CSV</q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup @click="overviewExport.openPrintView()">
                        <q-item-section avatar>
                            <q-icon name="print" />
                        </q-item-section>
                        <q-item-section>Print / Save as PDF</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
            <q-space />
            <q-input
                ref="searchInputRef"
                v-model="filters.searchText.value"
                outlined
                dense
                debounce="150"
                placeholder='Search ("tomato pasta" matches either)'
                clearable
                autofocus
                style="min-width: 280px"
            >
                <template #prepend>
                    <q-icon name="search" />
                </template>
            </q-input>
        </div>

        <!-- Quick-info summary banner — at-a-glance pantry health. -->
        <div
            v-if="stockItems.length > 0"
            class="row q-gutter-md items-center q-mb-md stock-summary-banner"
        >
            <div class="stock-summary-stat">
                <div class="text-h6">{{ stockItems.length }}</div>
                <div class="text-caption text-grey">total items</div>
            </div>
            <q-separator vertical />
            <div class="stock-summary-stat">
                <div class="text-h6 text-orange-9">{{ filters.summaryCounts.value.low }}</div>
                <div class="text-caption text-grey">low stock</div>
            </div>
            <div class="stock-summary-stat">
                <div class="text-h6 text-red-7">{{ filters.summaryCounts.value.out }}</div>
                <div class="text-caption text-grey">out of stock</div>
            </div>
            <q-separator vertical />
            <div class="stock-summary-stat">
                <div class="text-h6 text-amber-9">{{ filters.summaryCounts.value.essentials }}</div>
                <div class="text-caption text-grey">essentials</div>
            </div>
            <div class="stock-summary-stat">
                <div class="text-h6 text-secondary">{{ filters.summaryCounts.value.open }}</div>
                <div class="text-caption text-grey">open / in-use</div>
            </div>
            <q-space />
            <div class="text-caption text-grey">
                {{ filters.filteredStockItems.value.length }} of {{ stockItems.length }} shown
            </div>
        </div>

        <!-- Quick filters ──────────────────────────────────────────────── -->
        <div class="row q-gutter-sm q-mb-md items-center">
            <q-chip
                v-for="level in stockLevels"
                :key="level.stock_level_id"
                clickable
                :selected="filters.levelFilter.value === level.stock_level_id"
                :color="
                    filters.levelFilter.value === level.stock_level_id
                        ? getStockLevelColour(level.name)
                        : undefined
                "
                :text-color="filters.levelFilter.value === level.stock_level_id ? 'white' : undefined"
                outline
                @click="filters.toggleLevelFilter(level.stock_level_id)"
            >
                <q-icon
                    v-if="filters.levelFilter.value === level.stock_level_id"
                    name="check"
                    class="q-mr-xs"
                />
                {{ level.name }}
                <q-badge floating color="grey-3" text-color="grey-9">
                    {{ filters.countByLevel.value.get(level.stock_level_id) ?? 0 }}
                </q-badge>
            </q-chip>

            <q-separator vertical class="q-mx-sm" />

            <FilterChip v-model="filters.essentialsOnly.value" icon="flag" active-color="amber-9">
                Essentials only
            </FilterChip>

            <FilterChip v-model="filters.openOnly.value" icon="lock_open" active-color="secondary">
                Open / in-use
            </FilterChip>

            <FilterChip v-model="filters.hasAlertOnly.value" icon="warning" active-color="negative">
                Needs attention
            </FilterChip>

            <FilterChip v-model="filters.usedInRecipeOnly.value" icon="menu_book" active-color="primary">
                Used in a recipe
            </FilterChip>

            <q-chip
                v-if="filters.cartFilter.value !== 'all'"
                clickable
                color="primary"
                text-color="white"
                removable
                @remove="filters.cartFilter.value = 'all'"
            >
                <q-icon name="shopping_cart" size="14px" class="q-mr-xs" />
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

            <q-space />

            <q-btn
                v-if="bulkMode"
                flat
                no-caps
                icon="close"
                label="Cancel"
                @click="cancelBulk"
            />
            <q-btn
                v-else
                flat
                no-caps
                icon="checklist"
                label="Bulk select"
                @click="bulkMode = true"
            />
        </div>

        <!-- Bulk action bar ───────────────────────────────────────────── -->
        <q-banner v-if="bulkMode" class="bg-primary text-white q-mb-md" dense rounded>
            <template #avatar>
                <q-icon name="checklist" />
            </template>
            {{ bulkSelection.size }} selected
            <template #action>
                <q-btn flat no-caps label="Select visible" color="white" @click="selectVisible" />
                <q-btn
                    flat
                    no-caps
                    label="Add to list"
                    color="white"
                    :loading="bulkBusy"
                    :disable="bulkSelection.size === 0"
                    @click="bulkAddToPrimary"
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
                    <q-list
                        v-if="filters.filteredStockItems.value.length > 0"
                        class="q-gutter-y-sm"
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
                            @go-to-list="goToList"
                        />
                    </q-list>

                    <!-- Empty state ───────────────────────────────────── -->
                    <q-banner v-else class="bg-grey-2 q-mt-md" rounded>
                        <template v-if="stockItems.length === 0">
                            <div class="text-subtitle1 q-mb-sm">Your pantry is empty.</div>
                            <div class="text-body2 q-mb-md text-grey-8">
                                Start by adding an item, or build your pantry from things you
                                already track elsewhere.
                            </div>
                            <div class="q-gutter-sm">
                                <q-btn color="positive" icon="add" no-caps label="New item" @click="onCreateClick" />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    icon="menu_book"
                                    label="Create from a recipe's ingredients"
                                    @click="goToRecipes"
                                />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    icon="shopping_cart"
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
    import { storeToRefs } from 'pinia';
    import type { QInput } from 'quasar';
    import { useQuasar } from 'quasar';
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import ScanOverlay from 'src/components/ScanOverlay.vue';
    import BulkMoveLocationDialog from 'src/components/stock/BulkMoveLocationDialog.vue';
    import CreateStockItemDialog from 'src/components/stock/CreateStockItemDialog.vue';
    import StockItemRow from 'src/components/stock/StockItemRow.vue';
    import { useShortcut } from 'src/composables/useShortcut';
    import { useStockFilters, STOCK_SORT_OPTIONS } from 'src/composables/useStockFilters';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { Membership } from 'src/models/shoppingList';
    import type { StockGroup } from 'src/models/stockGroup';
    import { useStockOverviewExport } from 'src/composables/useStockOverviewExport';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import StockItemDetailPage from 'src/pages/StockItemDetailPage.vue';
    import { onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const stockGroupApi = new StockGroupApiService();
    const stockItemApi = new StockItemApiService();
    const barcodeApi = new BarcodeApiService();
    const overviewExport = useStockOverviewExport();

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

    const filters = useStockFilters({
        stockItems: () => stockItems.value,
        stockLevels: () => stockLevels.value,
        stockLocations: () => stockLocations.value,
        recipes: () => recipes.value,
        stockGroups: () => stockGroups.value,
        membership: () => shoppingListStore.membership as Membership | null,
    });

    // ── Splitter peek ────────────────────────────────────────────────────
    const peekId = ref<string | null>(null);
    const splitPct = ref(100);
    watch(peekId, (v) => (splitPct.value = v ? 58 : 100));

    function onRowClick(stockItemId: string) {
        if (bulkMode.value) {
            toggleBulk(stockItemId);
            return;
        }
        peekId.value = peekId.value === stockItemId ? null : stockItemId;
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
        // The substitutes graph arrives with the StockItemDetail revamp (P2).
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
    function goToList(listId: string) {
        void router.push(`/shopping-lists/${listId}`);
    }
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
                        : 'Unknown barcode — register it from Data → Barcodes & QR.',
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
        background: rgba(0, 0, 0, 0.02);
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
</style>
