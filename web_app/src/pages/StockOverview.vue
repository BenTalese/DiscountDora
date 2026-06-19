<template>
    <div class="q-pa-md">
        <!-- Header bar — C-1 Chunk 2 / L94: one button group across the
             top in this order: New item · Export · Bulk select · Scan ·
             Stocktake. Search stays separate on the right (L99). -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <BaseButton variant="primary" :icon="ICONS.add" label="New item" @click="onCreateClick" />
            <!-- Feedback 2026-06-18 (round 3): Export now rides BaseButton
                 (secondary) so it sits flush with the other toolbar
                 buttons. The dropdown menu hangs off the BaseButton via
                 q-menu — same UX, consistent chrome. -->
            <BaseButton variant="secondary" :icon="ICONS.more_horiz" label="Export">
                <q-menu auto-close>
                    <q-list dense style="min-width: 200px">
                        <!-- C-1 Chunk 1 / L67 — both exports respect the
                             currently filtered set. `filteredIds` is undefined
                             when no filters are active so the server-side
                             fast-path stays "export everything". -->
                        <q-item clickable @click="overviewExport.downloadCsv(filteredIds)">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.file_download" />
                            </q-item-section>
                            <q-item-section>Export as CSV</q-item-section>
                        </q-item>
                        <q-item clickable @click="overviewExport.openPrintView(filteredIds)">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.print" />
                            </q-item-section>
                            <q-item-section>Print / Save as PDF</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </BaseButton>
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
            <!-- Feedback 2026-06-18: Filter toggle moved into the main
                 toolbar so the FilterBar doesn't get its own row of chrome
                 just for the toggle button. Same v-model + count drives
                 the panel below. -->
            <FilterToggleButton
                v-model="filtersExpanded"
                :active-count="filters.activeFilterCount.value"
                @clear="filters.clearFilters"
            />
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
                :color="showStockImages ? 'primary' : undefined"
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
        <!-- Feedback 2026-06-18: panel-only mode (`:toolbar="false"`); the
             toggle button lives in the page toolbar above. -->
        <FilterBar
            v-model="filtersExpanded"
            :toolbar="false"
            :active-count="filters.activeFilterCount.value"
            @clear="filters.clearFilters"
        >
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
                Essential
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
                use-input
                fill-input
                hide-selected
                input-debounce="200"
                clearable
                label="Any location"
                style="min-width: 180px"
                @filter="filters.filterLocations"
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

        <!-- Bulk action bar ─────────────────────────────────────────────
             Round-16: outer wrapper has `q-py-xs` (4px) — just enough
             buffer for q-slide-transition's height measurement to
             settle smoothly, without creating cavernous empty space
             when the bar is closed. Unlike FilterBar, this wrapper
             has no always-visible content (no toolbar row inside it),
             so q-py-md left ~32px of dead height even when collapsed. -->
        <div class="bulk-bar q-py-xs">
        <q-slide-transition>
            <div v-if="bulkMode" class="dora-subbar">
                <div class="dora-subbar__inner">
                    <div class="row items-center q-gutter-sm">
                    <q-icon :name="ICONS.checklist" />
                    <span class="text-weight-medium">{{ bulkSelection.size }} selected</span>
                    <q-space />
                    <q-btn flat dense no-caps label="Select visible" @click="selectVisible" />
                    <q-btn
                        flat
                        dense
                        no-caps
                        label="Deselect all"
                        :disable="bulkSelection.size === 0"
                        @click="deselectAll"
                    />
                    <q-btn
                        flat
                        dense
                        no-caps
                        :icon="ICONS.add_shopping_cart"
                        label="Add to list…"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkAddToListPrompt"
                    />
                    <q-btn
                        flat
                        dense
                        no-caps
                        :icon="ICONS.remove_shopping_cart"
                        label="Remove from list…"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkRemoveFromListPrompt"
                    />
                    <q-btn
                        flat
                        dense
                        no-caps
                        label="Move location"
                        :disable="bulkSelection.size === 0"
                        @click="openMoveDialog"
                    />
                    <q-btn
                        flat
                        dense
                        no-caps
                        label="Restock"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkRestock"
                    />
                    <q-btn
                        v-if="scanningEnabled"
                        flat
                        dense
                        no-caps
                        icon="qr_code_2"
                        label="Print QRs"
                        :disable="bulkSelection.size === 0"
                        @click="bulkPrintQrs"
                    />
                    </div>
                </div>
            </div>
        </q-slide-transition>
        </div>

        <!-- Splitter: item list on the left, in-page detail peek on the right.
             C-1b.2 (L117, L118): peek opens at 50% (not 58%), and while a peek
             is open the drag-range is clamped to [40%, 65%] so neither pane
             gets squished to an unusable width. When no peek is open we let
             the list go full-width (100%), so the limits are dynamic. -->
        <q-splitter
            v-model="splitPct"
            :limits="splitterLimits"
            :disable="!peekId"
            unit="%"
            separator-class="dora-splitter__separator"
            class="stock-splitter"
            :class="{ 'stock-splitter--peeking': !!peekId }"
        >
            <!-- Feedback 2026-06-18 (round 3): the user picked a clean
                 vertical bar over the gripper dots. The separator now
                 paints a coloured vertical line that brightens to accent
                 on hover; the cursor change + colour cue carry the
                 draggability signal. No #separator template content
                 needed — the bar IS the separator. -->
            <template #before>
                <div class="q-pr-md q-pt-xs">
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
                        @open-detail="peekId = $event"
                    />
                </div>
            </template>
        </q-splitter>

        <PageCountsFooter v-if="stockItems.length > 0" :counts="filters.footerCounts.value" />

        <CreateStockItemDialog v-model="createDialogOpen" />

        <BulkMoveLocationDialog
            v-model="moveDialogOpen"
            :count="bulkSelection.size"
            :location-options="filters.allLocationOptions.value"
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
    import BaseButton from 'src/components/BaseButton.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import FilterToggleButton from 'src/components/FilterToggleButton.vue';
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
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useLocationStore } from 'src/stores/locationStore';
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
    const locationStore = useLocationStore();
    const shoppingListStore = useShoppingListStore();
    const slActions = useShoppingListActions();
    const shoppingListApi = new ShoppingListApiService();
    const recipeStore = useRecipeStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
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
        locationTree: () => locationStore.tree,
        recipes: () => recipes.value,
        stockGroups: () => stockGroups.value,
        membership: () => shoppingListStore.membership as Membership | null,
    });

    // Filter panel expanded state — shared between the toolbar's
    // FilterToggleButton and the FilterBar's collapsible panel.
    const filtersExpanded = ref(false);

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
    // Feedback 2026-06-18: open at 58% (the C-1b.2 50% felt too narrow on
    // the list side). Drag-range clamped to [40, 70] while peeking,
    // [40, 100] when closed (so the list can take the full width).
    const peekId = ref<string | null>(null);
    const splitPct = ref(100);
    const splitterLimits = computed<[number, number]>(() =>
        peekId.value ? [40, 70] : [40, 100],
    );
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
    function deselectAll() {
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

    // ── Bulk add to list ────────────────────────────────────────────────
    // Round-18: always prompt for the target list, then add every
    // selected item to it. The server's addLineAsync already de-dupes
    // ("already on list"); items already on a DIFFERENT list still get
    // added (multi-list membership is fine).
    async function pickActiveListId(title: string, source: 'all' | 'present-only'): Promise<string | null> {
        const m = shoppingListStore.membership;
        const all = (m?.active_lists ?? []).filter((l) => l.status !== 'done');
        let candidates = all;
        if (source === 'present-only') {
            const ids = new Set<string>();
            for (const sid of bulkSelection.value) {
                const entry = m?.items.find((i) => i.stock_item_id === sid);
                entry?.unticked_list_ids.forEach((lid) => ids.add(lid));
            }
            candidates = all.filter((l) => ids.has(l.shopping_list_id));
        }
        if (candidates.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: source === 'present-only'
                    ? 'None of the selected items are on a list.'
                    : 'No active lists. Create one first.',
            });
            return null;
        }
        return await new Promise<string | null>((resolve) => {
            $q.dialog({
                title,
                options: {
                    type: 'radio',
                    model: candidates[0]!.shopping_list_id,
                    items: candidates.map((l) => ({ label: l.name, value: l.shopping_list_id })),
                },
                cancel: true,
                persistent: false,
            })
                .onOk((val: string) => resolve(val))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
    }

    async function bulkAddToListPrompt() {
        if (bulkSelection.value.size === 0) return;
        const listId = await pickActiveListId('Add to which list?', 'all');
        if (!listId) return;
        bulkBusy.value = true;
        try {
            const ids = [...bulkSelection.value];
            await slActions.addItems(listId, ids.map((id) => ({ stock_item_id: id })));
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    async function bulkRemoveFromListPrompt() {
        if (bulkSelection.value.size === 0) return;
        const listId = await pickActiveListId('Remove from which list?', 'present-only');
        if (!listId) return;
        bulkBusy.value = true;
        try {
            const list = await stockOverviewExportRemoveHelper(listId);
            const selected = bulkSelection.value;
            const linesToDelete = list.lines.filter(
                (l) => l.stock_item_id && selected.has(l.stock_item_id),
            );
            for (const line of linesToDelete) {
                await shoppingListApi.deleteLineAsync(listId, line.line_id);
            }
            await shoppingListStore.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Removed ${linesToDelete.length} from "${list.display_name ?? list.name ?? 'list'}".`,
            });
            cancelBulk();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove from list.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // Thin wrapper so the remove handler can fetch the list lines without
    // pulling another API instance into the file scope.
    async function stockOverviewExportRemoveHelper(listId: string) {
        return await shoppingListApi.getDetailAsync(listId);
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
        void router.push('/cookbook');
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
            locationStore.refreshAsync(),
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
    /* Round-15: shared "sub-toolbar" treatment used by the bulk-select
       banner and (via :deep) the FilterBar's filter panel. Soft
       surface-elevated card with a tint border so both areas read as a
       distinct sub-zone of the page.

       Two subtle traps `q-slide-transition` lays:
       1. A real `border` on the transition host renders even at height 0
          (1px top + 1px bottom → 2px sliver). We use `inset box-shadow`
          instead — it paints inside the box without contributing to its
          size and disappears cleanly when the box has 0 height.
       2. Putting `border-radius` on an inner wrapper clips it against
          the host's straight edges during the height animation, so the
          rounded corners pop in only when the transition releases. We
          keep the radius on the OUTER host so the card grows rounded
          from the start.
       Result: smooth open/close, no snap, rounded from frame one. */
    /* Both sub-bars share an identical 3-level structure that we got
       wrong twice; the values below match the FilterBar panel verbatim.
       Outer (.dora-subbar / .filter-bar__panel) — q-slide-transition host,
       carries chrome (background + inset shadow border + border-radius).
       Inner (__inner) — padding box (12px 16px).
       Content row inside the inner — flex layout (q-gutter-sm, etc). */
    .dora-subbar,
    :deep(.filter-bar__panel) {
        background: var(--surface-elevated);
        box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--text-primary) 10%, transparent);
        border-radius: 8px;
    }
    :deep(.filter-bar__panel) { margin-top: 4px; }
    /* Round-16: FilterBar's default q-py-md (16px top + 16px bottom)
       stacked with the bulk wrapper's padding adds up to ~32px of empty
       space between them. Override here so the filter section's own
       outer padding shrinks to 4px (matching bulk-bar's q-py-xs). The
       slide's smoothness comes from the inner buffer, not the magnitude
       of the outer padding — small is enough. */
    :deep(.filter-bar) {
        padding-top: 4px;
        padding-bottom: 4px;
    }
    .dora-subbar__inner,
    :deep(.filter-bar__panel-inner) {
        padding: 12px 16px;
    }
    .stock-splitter {
        min-height: 50vh;
    }
    /* Feedback 2026-06-18 (round 3): the divider is a clean coloured
       vertical bar. When no peek is open it collapses to transparent so
       the full-width list reads cleanly. While peeking the bar paints in
       a muted text-tinted colour and brightens to accent on hover, with
       a wider hit area so it's easy to grab. */
    .stock-splitter :deep(.dora-splitter__separator) {
        background: transparent;
        transition: background-color 0.25s ease;
    }
    .stock-splitter--peeking :deep(.dora-splitter__separator) {
        width: 6px;
        background: color-mix(in srgb, var(--text-primary) 18%, transparent);
    }
    .stock-splitter--peeking :deep(.dora-splitter__separator):hover {
        background: var(--q-accent);
    }
    /* Feedback 2026-06-18 (round 2): drop the panel's max-height +
       internal overflow. The competing scroll hid the embedded header
       (name + delete) once the user scrolled inside the panel. Letting
       the panel grow naturally means the page scroll handles overflow
       and the header stays in the layout. */
    .stock-peek {
        min-height: 0;
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
