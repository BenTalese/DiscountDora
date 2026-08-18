<template>
    <q-page class="q-pa-md stock-overview" :style-fn="pageStyleFn">
        <!-- Header bar — FU-121: New item · Scan · Stocktake · Bulk select
             · Log price · Export.
             2026-08-15 feedback: on phones this row was eating a quarter of
             the screen, so every action drops its label there and rides its
             icon alone (`:label="compactToolbar ? undefined : '…'"`, tooltip
             carries the name). The filter toggle + search then move to their
             own second row where the search can actually fill the width,
             instead of being crushed onto the end of the action row. -->
        <div class="row items-center q-gutter-sm stock-toolbar">
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                :label="compactToolbar ? undefined : 'New item'"
                aria-label="New item"
                @click="onCreateClick"
            >
                <q-tooltip v-if="compactToolbar">New item</q-tooltip>
            </BaseButton>
            <!-- FU-378 — action-first scan. Opens the camera in the default
                 "open item" action; the current action is shown and switched
                 from inside the overlay (see the #controls slot below), so
                 the user can keep scanning and always see what each scan
                 does. Gated on scanningEnabled. -->
            <BaseButton
                v-if="scanningEnabled"
                variant="secondary"
                :icon="ICONS.qr_code_scanner"
                :label="compactToolbar ? undefined : 'Scan'"
                aria-label="Scan"
                @click="openScan"
            >
                <q-tooltip v-if="compactToolbar">Scan</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="secondary"
                :icon="ICONS.fact_check"
                :label="stocktakeLabel"
                :aria-label="stocktakeAriaLabel"
                :attention="stocktakeOverdue > 0"
                to="/stocktake"
            >
                <!-- Compact mode drops the label but NOT the overdue count —
                     that number is the whole reason the button glows. -->
                <q-badge v-if="compactToolbar && stocktakeOverdue > 0" color="primary" floating>
                    {{ stocktakeOverdue }}
                </q-badge>
                <q-tooltip v-if="compactToolbar">{{ stocktakeAriaLabel }}</q-tooltip>
            </BaseButton>
            <BaseButton
                v-if="!bulkMode"
                variant="secondary"
                :icon="ICONS.checklist"
                :label="compactToolbar ? undefined : 'Bulk select'"
                aria-label="Bulk select"
                @click="bulkMode = true"
            >
                <q-tooltip v-if="compactToolbar">Bulk select</q-tooltip>
            </BaseButton>
            <BaseButton
                v-else
                variant="secondary"
                :icon="ICONS.close"
                :label="compactToolbar ? undefined : 'Cancel'"
                aria-label="Cancel bulk select"
                @click="cancelBulk"
            >
                <q-tooltip v-if="compactToolbar">Cancel bulk select</q-tooltip>
            </BaseButton>
            <!-- 2026-08-15 feedback: "Log a price" moves off the dashboard
                 and onto the surface where the user is actually looking at
                 the item they want to price. Same `useLogPrice()` sheet the
                 dashboard opened, so there's one flow, not two (R-003) —
                 it just picks the stock item first. Money-gated to match the
                 row-level button. On phones this toolbar entry is the ONLY
                 way in: the per-row price buttons hide there to give the row
                 its horizontal space back. -->
            <BaseButton
                v-if="moneyEnabled"
                variant="secondary"
                :icon="ICONS.cash_plus"
                :label="compactToolbar ? undefined : 'Log price'"
                aria-label="Log a price"
                @click="openLogPrice()"
            >
                <q-tooltip v-if="compactToolbar">Log a price</q-tooltip>
            </BaseButton>
            <!-- Feedback 2026-06-18 (round 3): Export rides BaseButton
                 (secondary) so it sits flush with the other toolbar
                 buttons. The dropdown menu hangs off the BaseButton via
                 q-menu — same UX, consistent chrome. -->
            <BaseButton
                variant="secondary"
                :icon="ICONS.export_data"
                :label="compactToolbar ? undefined : 'Export'"
                aria-label="Export"
            >
                <q-menu auto-close>
                    <q-list dense style="min-width: 200px">
                        <!-- both exports respect the
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

            <!-- Desktop keeps the filter toggle + search on this same row,
                 pushed right. On phones `stock-toolbar__find` wraps to its
                 own line (see the scoped media query) so the search input
                 gets the full width instead of a 280px sliver. -->
            <q-space class="gt-xs" />
            <div class="row items-center q-gutter-sm no-wrap stock-toolbar__find">
                <!-- Feedback 2026-06-18: Filter toggle moved into the main
                     toolbar so the FilterBar doesn't get its own row of chrome
                     just for the toggle button. Same v-model + count drives
                     the panel below. -->
                <FilterToggleButton
                    v-model="filtersExpanded"
                    :active-count="filters.activeFilterCount.value"
                    :compact="compactToolbar"
                    @clear="clearAllFilters"
                />
                <q-input
                    ref="searchInputRef"
                    v-model="filters.searchText.value"
                    class="col"
                    outlined
                    dense
                    debounce="150"
                    placeholder="Search"
                    clearable
                    :autofocus="!compactToolbar"
                >
                    <template #prepend>
                        <q-icon :name="ICONS.search" />
                    </template>
                </q-input>
            </div>
        </div>

        <!-- Summary counts moved to the sticky PageCountsFooter (A7). -->

        <!-- Quick filters ─ standardised via FilterBar (A4) ────────────── -->
        <!-- Feedback 2026-06-18: panel-only mode (`:toolbar="false"`); the
             toggle button lives in the page toolbar above. -->
        <FilterBar
            v-model="filtersExpanded"
            :toolbar="false"
            :active-count="filters.activeFilterCount.value"
            @clear="clearAllFilters"
        >
            <template #filters>
            <!-- ── Row 1: quick filters ────────────────────────────────────
                 2026-08-15 feedback: the toggle chips and the deep-link
                 chips now live on their own row ABOVE the input filters
                 rather than interleaved with the dropdowns. On phones the
                 row scrolls horizontally (`stock-quick-filters`) instead of
                 wrapping to four lines — an open filter panel used to eat
                 half the screen.
                 The (?) info icons that trailed Expiring soon / Essential /
                 Open / Needs check are gone: each chip says what it does,
                 and the tooltips were repeating the label back at the user.
                 The one genuinely non-obvious rule — what the row colours
                 mean — moved to Help → Guides ("What the colours and
                 outlines mean"), which is where a reference belongs. -->
            <div class="row items-center no-wrap stock-quick-filters">
                <!-- FU-108: chip cluster ordered by usage frequency —
                     highest-signal alert chip leads. -->
                <FilterChip v-model="filters.hasAlertOnly.value" :icon="ICONS.warning" active-color="negative">
                    Needs attention
                </FilterChip>

                <FilterChip v-model="filters.expiringSoonOnly.value" :icon="ICONS.expiry" active-color="warning">
                    Expiring soon
                </FilterChip>

                <FilterChip v-model="filters.essentialsOnly.value" :icon="ICONS.flag" active-color="secondary">
                    Essential
                </FilterChip>

                <FilterChip v-model="filters.openOnly.value" :icon="ICONS.lock_open" active-color="secondary">
                    Open / in-use
                </FilterChip>

                <FilterChip v-model="filters.needsCheckOnly.value" :icon="ICONS.fact_check" active-color="warning">
                    Needs check
                </FilterChip>

                <!-- "Used in a recipe" filter removed
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

                <!-- Recipe-ingredients filter — set via deep-link from a
                     recipe card on the stock-item detail page. The chip is
                     the only UI surface for the filter (no dropdown);
                     removing it clears the deep-link state. -->
                <q-chip
                    v-if="filters.recipeFilter.value !== null
                        && (filters.recipeFilterContext.value !== null || !recipesHydrated)"
                    clickable
                    color="primary"
                    text-color="white"
                    removable
                    @remove="clearRecipeFilter"
                >
                    <q-icon :name="ICONS.menu_book" size="14px" class="q-mr-xs" />
                    {{ recipeFilterChipLabel }}
                </q-chip>
            </div>

            <!-- ── Row 2: input filters (level / sort / location / group) ── -->
            <!-- 2026-08-16 feedback: same sideways-scroll treatment as the
                 quick-filter row above. Four 180px dropdowns wrapped to
                 two or three lines on a phone, which is the same "open
                 filter panel eats the viewport" problem the chip row was
                 fixed for — the two rows now behave identically. -->
            <div class="row items-center no-wrap stock-input-filters">
            <!-- single dropdown defaults to "Any level".
                 Per-level chips with count badges retired; counts live in
                 the sticky footer now (PageCountsFooter).
                 Feedback (2026-06-30): the option list and trigger both
                 render the level colour-dot, matching the detail-page
                 picker so the three surfaces look identical. -->
            <q-select
                v-model="filters.levelFilter.value"
                :options="stockLevels"
                :option-label="(o: StockLevel) => o.name"
                :option-value="(o: StockLevel) => o.stock_level_id"
                emit-value
                map-options
                dense
                outlined
                clearable
                label="Any level"
                style="min-width: 180px"
            >
                <template #selected-item="scope">
                    <span class="row items-center no-wrap">
                        <StockLevelDot
                            :sequence="filterLevelSequence"
                            dot-class="q-mr-sm"
                        />
                        {{ scope.opt.name }}
                    </span>
                </template>
                <template #option="scope">
                    <q-item v-bind="scope.itemProps">
                        <q-item-section avatar>
                            <StockLevelDot :sequence="scope.opt.sequence" />
                        </q-item-section>
                        <q-item-section>{{ scope.opt.name }}</q-item-section>
                    </q-item>
                </template>
            </q-select>

            <!-- FU-108: sort ahead of location/group refinements —
                 users pick a sort axis far more often than they narrow
                 by location or group. -->
            <SortControl
                v-model:sort-by="filters.sortBy.value"
                v-model:sort-dir="filters.sortDir.value"
                :options="STOCK_SORT_OPTIONS"
                style="min-width: 180px"
            />

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
                    <BaseButton variant="ghost" dense label="Select visible" @click="selectVisible" />
                    <BaseButton
                        variant="ghost"
                        dense
                        label="Deselect all"
                        :disable="bulkSelection.size === 0"
                        @click="deselectAll"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        :icon="ICONS.add_shopping_cart"
                        label="Add to list…"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkAddToListPrompt"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        :icon="ICONS.remove_shopping_cart"
                        label="Remove from list…"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkRemoveFromListPrompt"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        label="Move location"
                        :disable="bulkSelection.size === 0"
                        @click="openMoveDialog"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        label="Restock"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="bulkRestock"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        :icon="ICONS.wasted"
                        label="Log waste…"
                        :loading="bulkBusy"
                        :disable="bulkSelection.size === 0"
                        @click="openBulkWasteDialog"
                    />
                    <BaseButton
                        v-if="scanningEnabled"
                        variant="ghost"
                        dense
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
                <div class="q-pt-xs stock-list-pane">
                    <!-- small lists keep the glide-in
                         ListTransition (DS4 perceived-perf masking, see
                         STOCK_OVERVIEW_PERF.md); large lists swap to
                         q-virtual-scroll so a >50-item pantry actually
                         renders smoothly. Threshold matches the legacy
                         page-1 cap so behaviour stays familiar below it. -->
                    <ListTransition
                        v-if="filters.filteredStockItems.value.length > 0 && filters.filteredStockItems.value.length <= VIRTUAL_SCROLL_THRESHOLD"
                        tag="div"
                        class="q-list stock-list"
                        :style="listStyle"
                    >
                        <StockItemRow
                            v-for="(item, idx) in filters.filteredStockItems.value"
                            :key="item.stock_item_id"
                            :item="item"
                            :bulk-mode="bulkMode"
                            :selected="bulkSelection.has(item.stock_item_id)"
                            :focused="focusedIndex === idx"
                            :peeking="peekId === item.stock_item_id"
                            :needs-check="needsCheckIds.has(item.stock_item_id)"
                            @click="onRowClick"
                            @bulk-toggle="toggleBulk"
                            @filter-location="filters.locationFilter.value = $event"
                            @long-press="onRowLongPress"
                        />
                    </ListTransition>
                    <q-virtual-scroll
                        v-else-if="filters.filteredStockItems.value.length > VIRTUAL_SCROLL_THRESHOLD"
                        :items="filters.filteredStockItems.value"
                        :virtual-scroll-item-size="rowHeight"
                        :virtual-scroll-slice-size="30"
                        class="q-list stock-list"
                        :style="listStyle"
                        v-slot="{ item, index }"
                    >
                        <StockItemRow
                            :key="item.stock_item_id"
                            :item="item"
                            :bulk-mode="bulkMode"
                            :selected="bulkSelection.has(item.stock_item_id)"
                            :focused="focusedIndex === index"
                            :peeking="peekId === item.stock_item_id"
                            :needs-check="needsCheckIds.has(item.stock_item_id)"
                            @click="onRowClick"
                            @bulk-toggle="toggleBulk"
                            @filter-location="filters.locationFilter.value = $event"
                            @long-press="onRowLongPress"
                        />
                    </q-virtual-scroll>

                    <!-- Empty state ───────────────────────────────────── -->
                    <!-- Carries its own right margin: the pane's padding moved
                         onto the scrolling list, and this branch isn't it. -->
                    <q-banner v-else class="dora-bg-sunken q-mt-md q-mr-md" rounded>
                        <template v-if="stockItems.length === 0">
                            <div class="text-subtitle1 q-mb-sm">Your pantry is empty.</div>
                            <div class="text-body2 q-mb-md dora-text-secondary">
                                Start by adding an item, or build your pantry from things you
                                already track elsewhere.
                            </div>
                            <div class="q-gutter-sm">
                                <BaseButton variant="primary" :icon="ICONS.add" label="New item" @click="onCreateClick" />
                                <BaseButton
                                    variant="secondary"
                                    :icon="ICONS.menu_book"
                                    label="Create from a recipe's ingredients"
                                    @click="goToRecipes"
                                />
                                <BaseButton
                                    variant="secondary"
                                    :icon="ICONS.shopping_cart"
                                    label="Import from a shopping list"
                                    @click="goToLists"
                                />
                            </div>
                        </template>
                        <template v-else>
                            No items match the current filters.
                            <BaseButton variant="ghost" dense label="Clear" @click="clearAllFilters" />
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

        <CreateStockItemDialog
            v-model="createDialogOpen"
            :prefill="createDialogPrefill"
            @created="createDialogPrefill = null"
        />

        <BulkMoveLocationDialog
            v-model="moveDialogOpen"
            :count="bulkSelection.size"
            :location-options="filters.allLocationOptions.value"
            :busy="bulkBusy"
            @confirm="bulkMove"
        />

        <!-- Bulk "Log waste" — reuses the single-item reason picker
             (R-001). One reason applies to every selected item; each
             item gets its own StockItemWasteEvent (reason-only per
             PROPOSAL_WASTE_MINIMISATION §5). -->
        <MarkAsWastedDialog
            v-model="bulkWasteOpen"
            :item-name="bulkWasteItemName"
            :subline="bulkWasteSubline"
            @submit="onBulkMarkAsWasted"
        />

        <!-- ── Scan (N5 + FU-378 action-first mode) ──────────────────
             `open` action → jump to the matched item's detail page (legacy
             N5 behaviour, closes on first decode). A `level` action stays
             open, applying the chosen level to each scanned item and
             reporting the per-item outcome via the overlay's result banner.
             The current action is shown + switched in the #controls slot, so
             the user always sees what a scan does and can change it without
             leaving the camera. -->
        <ScanOverlay
            ref="scanOverlayRef"
            v-model="overviewScanOpen"
            :close-on-decode="scanAction.kind === 'open'"
            :defer-feedback="scanAction.kind === 'level'"
            @decoded="onOverviewScanDecoded"
        >
            <template #controls>
                <BaseButton variant="primary" :icon="currentScanActionIcon">
                    <StockLevelDot
                        v-if="currentScanActionSequence !== null"
                        :sequence="currentScanActionSequence"
                        dot-class="q-mr-sm"
                    />
                    <span>Action: {{ currentScanActionLabel }}</span>
                    <q-icon :name="ICONS.expand_more" size="20px" class="q-ml-xs" />
                    <q-menu auto-close anchor="top middle" self="bottom middle">
                        <q-list dense style="min-width: 240px">
                            <q-item-label header>Scan does…</q-item-label>
                            <q-item
                                v-for="opt in scanActionOptions"
                                :key="opt.label"
                                v-close-popup
                                clickable
                                :active="isCurrentScanAction(opt.action)"
                                active-class="text-primary"
                                @click="selectScanAction(opt.action)"
                            >
                                <q-item-section avatar>
                                    <StockLevelDot
                                        v-if="opt.sequence !== undefined"
                                        :sequence="opt.sequence"
                                    />
                                    <q-icon v-else :name="ICONS.open_in_new" />
                                </q-item-section>
                                <q-item-section>{{ opt.label }}</q-item-section>
                                <q-item-section v-if="isCurrentScanAction(opt.action)" side>
                                    <q-icon :name="ICONS.check" color="primary" />
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </BaseButton>
                <div class="scan-action-caption">{{ scanActionCaption }}</div>
            </template>
        </ScanOverlay>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import type { QInput } from 'quasar';
    import { useQuasar } from 'quasar';
    import SortControl from 'src/components/filters/SortControl.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import FilterBar from 'src/components/FilterBar.vue';
    import FilterToggleButton from 'src/components/FilterToggleButton.vue';
    import PageCountsFooter from 'src/components/PageCountsFooter.vue';
    import FilterChip from 'src/components/chips/FilterChip.vue';
    import ScanOverlay from 'src/components/ScanOverlay.vue';
    import {
        buildScanActionOptions,
        resolveScanLevelOutcome,
        type ScanAction,
    } from 'src/helpers/scanActions';
    import BulkMoveLocationDialog from 'src/components/stock/BulkMoveLocationDialog.vue';
    import CreateStockItemDialog from 'src/components/stock/CreateStockItemDialog.vue';
    import MarkAsWastedDialog from 'src/components/stock/MarkAsWastedDialog.vue';
    import type { CreateStockItemPrefill } from 'src/components/stock/createStockItemPrefill';
    import StockItemRow from 'src/components/stock/StockItemRow.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import ListTransition from 'src/components/transitions/ListTransition.vue';
    import { useFilterPanelExpanded } from 'src/composables/useFilterPanelExpanded';
    import { useLogPrice } from 'src/composables/useLogPrice';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useShortcut } from 'src/composables/useShortcut';
    import { useStockFilters, STOCK_SORT_OPTIONS } from 'src/composables/useStockFilters';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import type { Membership } from 'src/models/shoppingList';
    import type { StockGroup } from 'src/models/stockGroup';
    import type { StockLevel } from 'src/models/stockLevel';
    import { useStockOverviewExport } from 'src/composables/useStockOverviewExport';
    import {
        STOCK_ROW_HEIGHT_DESKTOP,
        STOCK_ROW_HEIGHT_MOBILE,
    } from 'src/helpers/stockRowMetrics';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import StocktakeApiService from 'src/services/api/stocktakeApiService';
    import WasteApiService, { type WasteReason } from 'src/services/api/wasteApiService';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { usePantryBeliefs } from 'src/composables/usePantryBeliefs';
    import { useLocationStore } from 'src/stores/locationStore';
    import StockItemDetailPage from 'src/pages/StockItemDetailPage.vue';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const { scanningEnabled } = useScanningEnabled();
    const { moneyEnabled } = useMoneyEnabled();
    // FU-300's sheet, reused verbatim — the dashboard's "Log a price"
    // quick-action moved here (2026-08-15 feedback) rather than being
    // rebuilt, so both entry points remain one flow.
    const { openLogPrice } = useLogPrice();
    // Phones drop every toolbar label down to its icon; the row was taking
    // a quarter of the screen. Also gates the search autofocus — landing on
    // this page with the keyboard already up is right on desktop and
    // actively annoying on a phone.
    const compactToolbar = computed(() => $q.screen.lt.sm);
    const stockGroupApi = new StockGroupApiService();
    const stockItemApi = new StockItemApiService();
    const barcodeApi = new BarcodeApiService();
    const overviewExport = useStockOverviewExport();
    const stocktakeApi = new StocktakeApiService();
    const stocktakeOverdue = ref(0);
    // PROPOSAL_STOCKTAKE_MODE §7 — the server-owned set of "needs check"
    // ids. Drives the row pulse outline + the "Needs check" filter chip
    // (R-003 — SPA never re-derives). Kept as a Set so hasId lookups
    // are O(1) inside the filter predicate and the row renderer.
    const needsCheckIds = ref<Set<string>>(new Set());

    async function loadStocktakeCount() {
        try {
            // Bumped from limit=1 → 500 so we get the ids alongside the
            // count. 500 is the server's cap; a household with more
            // than that overdue is a pathological state.
            const result = await stocktakeApi.queueAsync(500);
            stocktakeOverdue.value = result.total;
            needsCheckIds.value = new Set(
                result.items.map((i) => i.stock_item_id),
            );
        } catch {
            stocktakeOverdue.value = 0;
            needsCheckIds.value = new Set();
        }
    }

    // Compact mode shows the count as a floating badge instead, so the
    // label goes bare and the full sentence lives on the tooltip/aria.
    const stocktakeAriaLabel = computed(() =>
        stocktakeOverdue.value > 0
            ? `Stocktake (${stocktakeOverdue.value} due)`
            : 'Stocktake',
    );
    const stocktakeLabel = computed(() =>
        compactToolbar.value ? undefined : stocktakeAriaLabel.value,
    );

    const router = useRouter();
    const route = useRoute();
    const actions = useStockItemActions();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    // inferred-pantry beliefs, loaded once on mount; StockItemRow
    // reads from the shared cache.
    const pantryBeliefs = usePantryBeliefs();
    const locationStore = useLocationStore();
    const shoppingListStore = useShoppingListStore();
    const slActions = useShoppingListActions();
    const shoppingListApi = new ShoppingListApiService();
    const recipeStore = useRecipeStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { recipes, recipesHydrated } = storeToRefs(recipeStore);

    // Stock groups load locally — no store yet, only needed by the filter
    // dropdown on this page.
    const stockGroups = ref<StockGroup[]>([]);

    // virtualisation tuning. Below the
    // threshold we keep the existing ListTransition glide-in so small
    // pantries feel unchanged; above it we hand off to q-virtual-scroll
    // so a 500-item pantry renders smoothly. Item-size is a rough
    // average — Quasar self-corrects after the first measure.
    const VIRTUAL_SCROLL_THRESHOLD = 50;
    // Row geometry comes from one place (`stockRowMetrics`) and is used
    // twice from here: as `virtual-scroll-item-size`, and as the
    // `--stock-row-height` custom property the row's CSS sizes itself from.
    // They must agree exactly or Quasar re-measures mid-scroll and the list
    // visibly snaps — the 2026-08-15 "jumpy scrolling" report.
    const rowHeight = computed(() =>
        $q.screen.lt.sm ? STOCK_ROW_HEIGHT_MOBILE : STOCK_ROW_HEIGHT_DESKTOP,
    );
    const listStyle = computed(() => ({
        '--stock-row-height': `${rowHeight.value}px`,
    }));

    // App-shell height (2026-08-04). QPage hands us the layout's real
    // chrome `offset` (header, plus a QFooter if the layout ever grows
    // one) and the viewport `height`, both from live layout state — so the
    // page fills the viewport exactly without a hardcoded pixel guess.
    // `height` is 0 only before Quasar's first screen measure; fall back to
    // calc() so the shell is still correct on that first paint.
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }

    const filters = useStockFilters({
        stockItems: () => stockItems.value,
        stockLevels: () => stockLevels.value,
        locationTree: () => locationStore.tree,
        recipes: () => recipes.value,
        stockGroups: () => stockGroups.value,
        membership: () => shoppingListStore.membership as Membership | null,
        needsCheckIds: () => needsCheckIds.value,
    }, { persistScope: 'stock-overview' });

    // Filter panel expanded state — shared between the toolbar's
    // FilterToggleButton and the FilterBar's collapsible panel.
    // persisted per-page across reloads (mobile always starts
    // hidden regardless of saved state).
    const filtersExpanded = useFilterPanelExpanded('stock-overview');

    // ── Recipe-ingredients deep-link filter ─────────────────────────────
    // Triggered by the "filter to this recipe's ingredients" action on
    // RecipeCard (currently surfaced on StockItemDetailPage). The query
    // param is the only entry point; the chip is the only on-page UI.
    // The label falls back to "this recipe" while the recipe list is
    // still hydrating so the chip never reads "Ingredients of: " bare.
    const recipeFilterChipLabel = computed(() => {
        const ctx = filters.recipeFilterContext.value;
        const name = ctx?.name ?? 'this recipe';
        return `Ingredients of: ${name}`;
    });
    // Wrap useStockFilters' clearFilters so the recipe deep-link param is
    // stripped from the URL alongside the in-memory state. Without this
    // wrap, "Clear filters" would zero the chip but leave ?recipe= on the
    // URL — a refresh/back would silently reinstate the filter.
    function clearAllFilters() {
        filters.clearFilters();
        if (route.query.recipe) {
            const next = { ...route.query };
            delete next.recipe;
            void router.replace({ path: route.path, query: next });
        }
    }
    function clearRecipeFilter() {
        filters.recipeFilter.value = null;
        // Strip the param so a refresh/back-nav doesn't restore the
        // filter the user just dismissed.
        if (route.query.recipe) {
            const next = { ...route.query };
            delete next.recipe;
            void router.replace({ path: route.path, query: next });
        }
    }
    function applyRecipeQuery(value: unknown) {
        const id = typeof value === 'string' && value.length > 0 ? value : null;
        if (filters.recipeFilter.value !== id) filters.recipeFilter.value = id;
        // Open the filter panel so the chip is visible on landing.
        if (id) filtersExpanded.value = true;
    }
    watch(() => route.query.recipe, applyRecipeQuery, { immediate: true });

    // Sequence of the currently-selected level filter — drives the
    // colour-dot rendered inside the q-select trigger. `null` when "Any
    // level" is active (StockLevelDot falls back to the sunken bg).
    const filterLevelSequence = computed<number | null>(() => {
        const id = filters.levelFilter.value;
        if (!id) return null;
        const seq = stockLevels.value.find((l) => l.stock_level_id === id)?.sequence;
        return typeof seq === 'number' ? seq : null;
    });

    // id list passed to the export endpoint when ANY
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

    // two-frame detail nav:
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

    // ── Buy-verdict actions ─────────────────────────────────────────────
    // Retired 2026-08-15 with the row's standalone verdict chip. The verdict
    // is now a ring + tooltip on the cart button, and that button's own click
    // already performs the add/remove the chip's one-tap action offered — so
    // there is nothing left for the page to broker. The richer surfaces
    // (stock-item detail, shopping list) still use `useBuyVerdictActions`.

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
        const wasSelected = bulkSelection.value.has(id);
        if (wasSelected) bulkSelection.value.delete(id);
        else bulkSelection.value.add(id);
        bulkSelection.value = new Set(bulkSelection.value);
        // 2026-08-15 feedback: unticking the last item leaves bulk mode
        // running with an empty selection and every action disabled —
        // a dead-end bar the user then has to dismiss by hand. Treat
        // "deselected the last one" as backing out of the mode. Only the
        // untick path does this: `deselectAll` is an explicit "clear but
        // stay in bulk mode" action and keeps its own behaviour.
        if (wasSelected && bulkSelection.value.size === 0) bulkMode.value = false;
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
            // pass silent so per-item toasts don't storm; one summary at the end.
            const ids = [...bulkSelection.value];
            for (const id of ids) await actions.addToList(id, null, { silent: true });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Added ${ids.length} item${ids.length === 1 ? '' : 's'} to your list.`,
            });
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    async function bulkRestock() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            // silent per-item, one summary toast.
            const ids = [...bulkSelection.value];
            for (const id of ids) await actions.markRestocked(id, { silent: true });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Marked ${ids.length} item${ids.length === 1 ? '' : 's'} restocked.`,
            });
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Bulk log waste ──────────────────────────────────────────────────
    // Reuses the single-item MarkAsWastedDialog (R-001). One reason
    // applies to the whole selection ("these all went off"). Each
    // selected item gets its own StockItemWasteEvent + its expiry
    // cleared (same shape as the single-item flow in StockItemRow).
    const wasteApi = new WasteApiService();
    const bulkWasteOpen = ref(false);
    const bulkWasteItemName = computed(() => {
        const n = bulkSelection.value.size;
        return `${n} item${n === 1 ? '' : 's'}`;
    });
    const bulkWasteSubline = computed(() =>
        'One reason applies to every selected item.',
    );
    function openBulkWasteDialog() {
        if (bulkSelection.value.size === 0) return;
        bulkWasteOpen.value = true;
    }
    async function onBulkMarkAsWasted(reason: WasteReason) {
        if (bulkSelection.value.size === 0) return;
        // Snapshot ids + their expiry state BEFORE any await — the
        // store may re-fetch and mutate rows mid-flight (matches the
        // per-row pattern in StockItemRow.onMarkAsWasted).
        const targets = [...bulkSelection.value].map((id) => {
            const row = stockItems.value.find(
                (i) => i.stock_item_id === id,
            );
            return {
                stock_item_id: id,
                original_expiry: row?.expiry_date ?? null,
            };
        });
        bulkBusy.value = true;
        const succeeded: Array<{
            event_id: string;
            stock_item_id: string;
            original_expiry: string | null;
        }> = [];
        try {
            for (const t of targets) {
                try {
                    const { event_id } = await wasteApi.logEventAsync({
                        stock_item_id: t.stock_item_id,
                        reason,
                    });
                    if (t.original_expiry) {
                        await stockItemStore.updateStockItemAsync({
                            stock_item_id: t.stock_item_id,
                            expiry_date: null,
                        });
                    }
                    succeeded.push({
                        event_id,
                        stock_item_id: t.stock_item_id,
                        original_expiry: t.original_expiry,
                    });
                } catch {
                    // Swallow per-item failure — the summary toast reports
                    // the discrepancy so a network blip on one item doesn't
                    // abandon the rest of the batch.
                }
            }
        } finally {
            bulkBusy.value = false;
        }
        const okCount = succeeded.length;
        const failCount = targets.length - okCount;
        if (okCount === 0) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log any as wasted.',
            });
            return;
        }
        const failSuffix = failCount > 0
            ? ` (${failCount} could not be logged)`
            : '';
        $q.notify({
            type: 'info',
            position: 'bottom-right',
            message: `Logged ${okCount} item${okCount === 1 ? '' : 's'} as wasted${failSuffix}.`,
            timeout: 6000,
            actions: [{
                label: 'Undo',
                color: 'white',
                handler: () => {
                    void (async () => {
                        try {
                            for (const s of succeeded) {
                                await wasteApi.deleteEventAsync(s.event_id);
                                if (s.original_expiry) {
                                    await stockItemStore.updateStockItemAsync({
                                        stock_item_id: s.stock_item_id,
                                        expiry_date: s.original_expiry,
                                    });
                                }
                            }
                            $q.notify({
                                type: 'positive',
                                position: 'bottom-right',
                                message: 'Undone.',
                            });
                        } catch (err) {
                            $q.notify({
                                type: 'negative',
                                position: 'bottom-right',
                                message: 'Could not undo.',
                                caption: toastCaption(err),
                            });
                        }
                    })();
                },
            }],
        });
        cancelBulk();
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
                cancel: { noCaps: true },
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
                caption: toastCaption(err),
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
                caption: toastCaption(err),
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Navigation ───────────────────────────────────────────────────────
    // `goToList` retired with the "On N lists" chip; the
    // cart button owns the list interaction now.
    function goToRecipes() {
        void router.push('/cookbook');
    }
    function goToLists() {
        void router.push('/shopping-lists');
    }

    // ── Create dialog ────────────────────────────────────────────────────
    const createDialogOpen = ref(false);
    // carries a scan-driven prefill (Open Food Facts hit, EAN-only
    // fallback, or product_no_link) so the dialog can seed the name/image/
    // barcode and auto-register the EAN on submit. Cleared on close so the
    // next non-scan "New item" click starts blank.
    const createDialogPrefill = ref<CreateStockItemPrefill | null>(null);
    function onCreateClick() {
        createDialogPrefill.value = null;
        createDialogOpen.value = true;
    }
    watch(createDialogOpen, (open) => {
        if (!open) createDialogPrefill.value = null;
    });

    // ── Bulk-print QRs (post-N5 polish) ───────────────────────────────────
    // Fires the same QR-sheet endpoint Data → Barcodes & QR uses, scoped to
    // the current bulk selection so the user can stocktake-print without
    // round-tripping through that page.
    function bulkPrintQrs() {
        if (bulkSelection.value.size === 0) return;
        overviewExport.openQrSheet(Array.from(bulkSelection.value));
    }

    // ── Scan overlay (N5 + FU-378 action-first mode) ─────────────────────
    // `scanAction` is a *persistent* selection shown + switched inside the
    // overlay: the user always sees what a scan does and can change it
    // without leaving the camera. `open` is the legacy N5 jump-to-detail
    // flow (closes on decode); a `level` action stays open and sets that
    // level on every scanned item (covers the stocktake scan-to-check case
    // — decision §7a #4). Opening the Scan button resets to the `open`
    // default (navigate-on-scan unless you pick an action).
    const overviewScanOpen = ref(false);
    const scanOverlayRef = ref<InstanceType<typeof ScanOverlay> | null>(null);
    const scanAction = ref<ScanAction>({ kind: 'open' });

    // The full action menu, rebuilt from the live level rows so a renamed
    // seed level shows its custom name (R-003 — no hardcoded level literals).
    const scanActionOptions = computed(() => buildScanActionOptions(stockLevels.value));

    // Current-action display: label, the optional level colour-dot sequence,
    // the leading icon, and a one-line caption of what each scan will do.
    const currentScanActionLabel = computed(() =>
        scanAction.value.kind === 'open'
            ? 'Open stock item'
            : `Set to ${scanAction.value.levelName}`,
    );
    const currentScanActionSequence = computed<number | null>(() => {
        if (scanAction.value.kind !== 'level') return null;
        const id = scanAction.value.levelId;
        return stockLevels.value.find((l) => l.stock_level_id === id)?.sequence ?? null;
    });
    const currentScanActionIcon = computed(() =>
        scanAction.value.kind === 'open' ? ICONS.open_in_new : undefined,
    );
    const scanActionCaption = computed(() =>
        scanAction.value.kind === 'open'
            ? 'Each scan opens that item — the scanner then closes.'
            : 'Keep scanning — each item is set to this level.',
    );

    function isCurrentScanAction(action: ScanAction): boolean {
        const cur = scanAction.value;
        if (action.kind === 'open') return cur.kind === 'open';
        return cur.kind === 'level' && cur.levelId === action.levelId;
    }

    function selectScanAction(action: ScanAction) {
        scanAction.value = action;
    }

    function openScan() {
        // Reset to the navigate-on-scan default each time the button is
        // pressed; switching to a level action happens inside the overlay.
        scanAction.value = { kind: 'open' };
        overviewScanOpen.value = true;
    }

    // Look up a stock item's display name for the scan result banner.
    function stockItemName(id: string): string | undefined {
        return stockItems.value.find((si) => si.stock_item_id === id)?.name;
    }

    // Apply the chosen level to a scanned item. Reuses the shared
    // updateStockLevelAsync mutation (R-003) so it behaves exactly like the
    // in-row level swap (optimistic + offline-queue + auto-add hook). Any
    // result other than a resolvable stock item is reported and skipped —
    // we don't derail the scan loop into the add-item flow.
    async function onScanLevelDecoded(value: string, action: Extract<ScanAction, { kind: 'level' }>) {
        const overlay = scanOverlayRef.value;
        try {
            const result = await barcodeApi.lookupAsync(value);
            const outcome = resolveScanLevelOutcome(result, action.levelName, stockItemName);
            if (!outcome.ok || !outcome.stockItemId) {
                overlay?.pushResult(outcome.message, 'bad');
                return;
            }
            await stockItemStore.updateStockLevelAsync({
                stock_item_id: outcome.stockItemId,
                stock_level_id: action.levelId,
            });
            overlay?.pushResult(outcome.message, 'good');
        } catch {
            overlay?.pushResult('Lookup failed — try again.', 'bad');
        }
    }

    async function onOverviewScanDecoded(value: string) {
        // Route level actions to the loop-apply handler; everything else is
        // the legacy open/navigate flow below.
        if (scanAction.value.kind === 'level') {
            await onScanLevelDecoded(value, scanAction.value);
            return;
        }
        try {
            const result = await barcodeApi.lookupAsync(value);
            // both stock-item kinds route directly. `UNIQUE` on
            // StockItemProduct.product_id guarantees there's no multi-link
            // ambiguity to handle. **P8-02 invariant: already-mapped EANs
            // never trigger the OFF lookup or the add flow** — they jump
            // straight to the existing item so no duplicate is created.
            if (result.kind === 'stock_item' || result.kind === 'stock_item_via_product') {
                overviewScanOpen.value = false;
                void router.push(`/stock/${result.id}`);
                return;
            }
            // `product_no_link` — the Product exists (probably from ingestion)
            // but no stock item is linked. Skip OFF (the user's own Product
            // data wins over an open-data suggestion) and open the add-item
            // dialog with a barcode-only prefill; the dialog registers the
            // EAN against the new stock item on save. Deeper "link into an
            // existing item" flow is deferred (see FU-056 Phase-2 Products
            // UI).
            if (result.kind === 'product_no_link') {
                overviewScanOpen.value = false;
                createDialogPrefill.value = {
                    barcode: value,
                    source: 'product_no_link',
                };
                createDialogOpen.value = true;
                return;
            }
            // `unknown` — the EAN is genuinely not in Dora. Ask Open Food
            // Facts. On a hit, seed the dialog with the OFF suggestion; on
            // a miss (or network failure — OFF returns `found: false` for
            // both), open the dialog with only the barcode so the user can
            // still one-tap add + register the EAN. The barcode registers
            // against the new stock item on submit either way.
            overviewScanOpen.value = false;
            let prefill: CreateStockItemPrefill = { barcode: value, source: 'unknown' };
            try {
                const off = await barcodeApi.offLookupAsync(value);
                if (off.found) {
                    prefill = {
                        barcode: value,
                        source: 'off',
                        name: off.name ?? undefined,
                        brand: off.brand ?? undefined,
                        imageUrl: off.image_url ?? undefined,
                        categories: off.categories ?? undefined,
                        quantity: off.quantity ?? undefined,
                    };
                }
            } catch {
                // OFF endpoint itself failed (server-side, distinct from a
                // "found: false" miss). Fall through to the barcode-only
                // prefill so the user isn't blocked — the add still works,
                // and the EAN still gets registered on submit.
            }
            createDialogPrefill.value = prefill;
            createDialogOpen.value = true;
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
        // FU-583 — the Dora Score freshness/stocktake actions deep-link here.
        // `expiring=1` narrows to expiring-soon / expired; `stocktake=1` opens
        // the existing "Needs check" (stocktake-queue) filter.
        if (q.expiring === 'true' || q.expiring === '1') {
            filters.expiringSoonOnly.value = true;
        }
        if (q.stocktake === 'true' || q.stocktake === '1') {
            filters.needsCheckOnly.value = true;
        }
    }

    watch(
        () => [
            route.query.location_id,
            route.query.attention,
            route.query.level_id,
            route.query.expiring,
            route.query.stocktake,
        ],
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
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            locationStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
            recipeStore.ensureLoadedAsync(),
            loadStockGroups(),
            loadStocktakeCount(),
            // load the inferred-pantry beliefs once; rows read them
            // from the shared cache. Non-blocking-safe (fails soft).
            pantryBeliefs.loadAsync(),
        ]);
        // Apply *after* the supporting data is loaded so the filter chips
        // visibly snap to the linked-from state on the first render.
        applyQueryFilters();
        maybeOpenCreateFromQuery();
    });
</script>

<style scoped>
    /* FU-012: bulk-select banner pairs with the FilterBar panel — both
       use the sunken-well treatment now. FilterBar owns its own styling
       (in the component); this matches it so the two sub-bars still
       read as siblings. `q-slide-transition` quirks: keep chrome on the
       outer host (radius from frame one) and avoid a real border (would
       render a 2px sliver at height 0) — neither matters with the new
       borderless sunken treatment, but the pattern is worth remembering. */
    .dora-subbar {
        background: var(--surface-sunken);
        border-radius: 6px;
    }

    /* ── Toolbar (2026-08-15 feedback) ────────────────────────────────
       Desktop: one row, actions left, filter-toggle + search right.
       Phones: the action buttons go icon-only (handled in the template)
       and `__find` wraps to a full-width second line so the search box
       actually has room. `flex-basis: 100%` is what forces the wrap;
       `q-space.gt-xs` is hidden there so nothing pushes against it. */
    .stock-toolbar {
        margin-bottom: var(--space-4);
    }
    .stock-toolbar__find {
        flex: 1 1 auto;
        min-width: 280px;
    }
    @media (max-width: 599px) {
        .stock-toolbar__find {
            flex-basis: 100%;
            min-width: 0;
        }
    }

    /* ── Quick-filter row ─────────────────────────────────────────────
       Toggle chips sit on their own row above the input filters. On
       phones they scroll sideways rather than wrapping onto four lines
       — an open filter panel was taking half the viewport. The
       scrollbar is hidden because the chips overflowing IS the
       affordance; a 2px bar under them just adds noise. */
    .stock-quick-filters,
    .stock-input-filters {
        gap: var(--space-2);
        overflow-x: auto;
        overflow-y: hidden;
        padding-bottom: 2px;
        scrollbar-width: none;
    }
    .stock-quick-filters::-webkit-scrollbar,
    .stock-input-filters::-webkit-scrollbar {
        display: none;
    }
    .stock-input-filters {
        margin-top: var(--space-3);
    }
    /* Sized rather than content-sized. Two reasons: a flex item shrinks
       past its own `min-width` once the row scrolls, and the Location
       picker (a `use-input` QSelect) is capped at `width: 100%` globally,
       which in a scrolling row resolves to the whole visible strip — it
       came out 311px next to its 180px siblings. Pinning the track width
       here makes all four read as one row of equal controls. */
    .stock-input-filters > * {
        flex: 0 0 180px;
    }
    .dora-subbar__inner {
        padding: 12px 16px;
    }
    /* ── App-shell layout (2026-08-04) ────────────────────────────────
       The page is a fixed-height flex column: chrome (toolbar, filters,
       bulk bar) and the counts footer keep their natural height, the
       splitter takes whatever is left, and all scrolling happens INSIDE
       the splitter panes. The document itself never scrolls.

       Why this replaced the previous CSS: the page was running two
       incompatible scroll models at once. The virtual list capped itself
       at `calc(100vh - 320px)` (an app-shell move, which stopped the
       document from overflowing), while PageCountsFooter used
       `position: sticky; bottom: 0` (a document-scroll move, which only
       works when the document DOES overflow). Net effect: the footer
       only pinned while the peek pane was open — the unbounded detail
       page was the sole thing making the document overflow — and
       QSplitter's flex row stretched the short left pane to match the
       tall right one, leaving a dead gap above the footer. Bounding the
       shell here removes both symptoms by construction rather than by
       counter-patching each one. */
    .stock-overview {
        display: flex;
        flex-direction: column;
        min-height: 0;
    }
    /* Only the splitter flexes; every other direct child (toolbar,
       FilterBar, bulk bar, counts footer) keeps its natural height.
       `min-height: 0` is required — a flex child refuses to shrink below
       its content height without it, which would push the footer back
       off-screen. */
    .stock-overview > .stock-splitter {
        flex: 1 1 auto;
        min-height: 0;
    }
    /* Quasar sets `overflow: auto` on BOTH splitter panels by default
       (quasar.css — `.q-splitter__before, .q-splitter__after`). The left
       panel's list child owns its scroll (see `.stock-list`), so the
       panel must not scroll too, or the same column ends up with two
       nested scrollbars. The right panel keeps the default and is the
       peek's single scroller. */
    .stock-splitter :deep(.q-splitter__before) {
        overflow: hidden;
    }
    .stock-splitter :deep(.q-splitter__after) {
        overflow: auto;
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
    /* Peek pane. Its panel owns the scroll now, so pin the embedded
       detail header. Losing that header on scroll was the 2026-06-18
       (round 2) complaint, and the workaround then was to drop the
       panel's internal overflow entirely — which is what let the peek
       grow unbounded and stretch the left pane. Sticky keeps both: an
       internally-scrolling panel AND a header that stays put. */
    .stock-peek {
        min-height: 0;
    }
    .stock-peek :deep(.stock-detail__header) {
        position: sticky;
        top: 0;
        z-index: 3;
        background: var(--surface-page);
    }
    /* Left pane. Fills the splitter panel and hands the scroll to whichever
       list branch is mounted. */
    .stock-list-pane {
        height: 100%;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    /* C-1 Chunk 1 — the virtualised list needs a sized scroll container.
       It now inherits that size from the shell instead of guessing at the
       chrome height with a viewport formula. The two list branches
       (ListTransition below VIRTUAL_SCROLL_THRESHOLD, QVirtualScroll
       above it) are mutually exclusive, so exactly one scroller exists at
       a time and the pane can't nest two. */
    .stock-list {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        /* The pane's right padding lives HERE, on the scroller, not on the
           pane. A scrollbar is painted at the scroller's outer edge, so
           holding the padding here puts the bar hard against the pane edge
           with the gap between it and the rows. With the padding on the
           pane instead, the scroller stopped 16px short and the bar read as
           floating inside the rows with dead space beyond it. */
        padding-right: var(--space-4);
        /* Reserve the gutter so the row width doesn't jump when the list
           crosses from non-scrolling to scrolling (filtering, deleting). */
        scrollbar-gutter: stable;
    }
    /* Phones paint an overlay scrollbar that takes no layout width, so
       reserving a stable gutter AND a 16px pad just stole ~28px from every
       row for a bar that isn't there (2026-08-15 feedback). Drop both to a
       hairline; the desktop rules above are untouched. */
    @media (max-width: 599px) {
        .stock-list {
            padding-right: var(--space-1);
            scrollbar-gutter: auto;
        }
    }
    /* FU-378 — caption under the in-overlay current-action switcher. Light
       text on the dark camera surface. */
    .scan-action-caption {
        color: rgba(255, 255, 255, 0.82);
        font-size: 13px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
    }
</style>
