<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <!-- P6-01 Chunk 5 — list selector. The detail page is the
                 canonical shopping-list surface; switching between lists
                 happens here, not via a separate overview. Includes active
                 and archived (separator), and a "+ New list" entry. -->
            <q-btn-dropdown
                :icon="ICONS.list_alt"
                aria-label="Switch list"
                flat
                no-caps
                dense
                class="q-mr-sm"
            >
                <q-list dense style="min-width: 260px">
                    <q-item clickable v-close-popup @click="newListOpen = true">
                        <q-item-section avatar><q-icon :name="ICONS.add" color="primary" /></q-item-section>
                        <q-item-section class="text-primary text-weight-medium">
                            New list
                        </q-item-section>
                    </q-item>
                    <q-separator />
                    <template v-if="activeSummaries.length > 0">
                        <q-item-label header class="q-pb-none">Active</q-item-label>
                        <q-item
                            v-for="s in activeSummaries"
                            :key="s.shopping_list_id"
                            clickable
                            v-close-popup
                            :active="s.shopping_list_id === listId"
                            active-class="dora-bg-info-soft"
                            @click="switchToList(s.shopping_list_id)"
                        >
                            <q-item-section avatar>
                                <q-icon
                                    :name="s.status === 'shopping' ? ICONS.shopping_cart_checkout : ICONS.list"
                                    :color="s.status === 'shopping' ? 'positive' : 'primary'"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ s.name }}</q-item-label>
                                <q-item-label caption>
                                    {{ s.line_count }} item{{ s.line_count === 1 ? '' : 's' }} ·
                                    {{ s.ticked_count }} ticked
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side @click.stop>
                                <q-btn flat round dense size="sm" :icon="ICONS.more_vert">
                                    <q-menu auto-close anchor="bottom right" self="top right">
                                        <q-list dense style="min-width: 200px">
                                            <q-item
                                                clickable
                                                :disable="s.line_count - s.ticked_count === 0"
                                                @click.stop="copyListUnticked(s)"
                                            >
                                                <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                                                <q-item-section>Copy unticked → new</q-item-section>
                                            </q-item>
                                            <q-item clickable @click.stop="archiveSummary(s)">
                                                <q-item-section avatar><q-icon :name="ICONS.archive" /></q-item-section>
                                                <q-item-section>Archive list</q-item-section>
                                            </q-item>
                                            <q-item clickable @click.stop="deleteSummary(s)">
                                                <q-item-section avatar><q-icon :name="ICONS.delete" color="negative" /></q-item-section>
                                                <q-item-section class="text-negative">Delete list</q-item-section>
                                            </q-item>
                                        </q-list>
                                    </q-menu>
                                </q-btn>
                            </q-item-section>
                        </q-item>
                    </template>
                    <template v-if="archivedSummaries.length > 0">
                        <q-separator />
                        <q-item-label header class="q-pb-none">Archived</q-item-label>
                        <q-item
                            v-for="s in archivedSummaries"
                            :key="s.shopping_list_id"
                            clickable
                            v-close-popup
                            :active="s.shopping_list_id === listId"
                            active-class="dora-bg-info-soft"
                            @click="switchToList(s.shopping_list_id)"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.archive" /></q-item-section>
                            <q-item-section>
                                <q-item-label>{{ s.name }}</q-item-label>
                                <q-item-label caption>
                                    Finished {{ s.completed_at ? formatDate(s.completed_at) : '' }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side @click.stop>
                                <q-btn flat round dense size="sm" :icon="ICONS.more_vert">
                                    <q-menu auto-close anchor="bottom right" self="top right">
                                        <q-list dense style="min-width: 200px">
                                            <q-item clickable @click.stop="copyListAll(s)">
                                                <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                                                <q-item-section>Copy archived → new</q-item-section>
                                            </q-item>
                                            <q-item clickable @click.stop="deleteSummary(s)">
                                                <q-item-section avatar><q-icon :name="ICONS.delete" color="negative" /></q-item-section>
                                                <q-item-section class="text-negative">Delete list</q-item-section>
                                            </q-item>
                                        </q-list>
                                    </q-menu>
                                </q-btn>
                            </q-item-section>
                        </q-item>
                    </template>
                    <q-separator v-if="activeSummaries.length > 0 || archivedSummaries.length > 0" />
                    <q-item clickable v-close-popup to="/shopping-lists/templates">
                        <q-item-section avatar><q-icon :name="ICONS.bookmarks" /></q-item-section>
                        <q-item-section>Manage templates…</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
            <div class="q-ml-sm col">
                <div class="text-h5">
                    <AppSkeleton
                        v-if="loading && !detail"
                        type="line"
                        width="200px"
                        height="1.6rem"
                    />
                    <span v-else-if="!editingName">{{ detail?.name ?? '' }}</span>
                    <q-input
                        v-else
                        v-model="nameDraft"
                        autofocus
                        dense
                        outlined
                        @blur="saveName"
                        @keydown.enter.prevent="saveName"
                        @keydown.esc.prevent="cancelName"
                    />
                    <BaseButton
                        v-if="detail && !editingName"
                        variant="icon"
                        :icon="ICONS.edit"
                        @click="startNameEdit"
                    >
                        <q-tooltip>Rename</q-tooltip>
                    </BaseButton>
                </div>
                <div v-if="detail" class="text-caption dora-text-muted">
                    {{ detail.lines.length }} item{{ detail.lines.length === 1 ? '' : 's' }} ·
                    {{ tickedCount }} ticked ·
                    Created {{ formatDate(detail.created_at) }}
                    <span v-if="detail.status === 'done'"> · Archived</span>
                    <!-- P6-01 Chunk 7 — inline planned-shop-date chip. Click
                         to set / change / clear the planned day. The banner
                         below also surfaces when it's today/tomorrow. -->
                    ·
                    <a
                        href="#"
                        class="dora-link"
                        @click.prevent="openPlannedDateEditor"
                    >
                        {{ plannedShopLabel }}
                    </a>
                </div>
            </div>

            <div v-if="detail" class="row q-gutter-sm items-center">
                <BaseButton
                    variant="icon"
                    :icon="ICONS.more_vert"
                >
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
                        <q-list dense style="min-width: 220px">
                            <q-item-label header class="q-pb-none">Group by</q-item-label>
                            <q-item
                                v-for="opt in groupByOptions"
                                :key="opt.value"
                                clickable
                                v-close-popup
                                @click="groupBy = opt.value"
                            >
                                <q-item-section avatar>
                                    <q-icon
                                        :name="groupBy === opt.value
                                            ? 'radio_button_checked'
                                            : 'radio_button_unchecked'"
                                    />
                                </q-item-section>
                                <q-item-section>{{ opt.label }}</q-item-section>
                            </q-item>
                            <q-separator />
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onRefreshDeals"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.refresh" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Refresh deals</q-item-label>
                                    <q-item-label caption>
                                        Re-check linked product offers
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                v-close-popup
                                :disable="
                                    untickedCount === 0 || otherActiveLists.length === 0
                                "
                                @click="onMoveUnticked"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.drive_file_move" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>
                                        Move unticked to another list
                                    </q-item-label>
                                    <q-item-label caption>
                                        {{
                                            otherActiveLists.length === 0
                                                ? 'No other active lists'
                                                : `${untickedCount} unticked item${
                                                      untickedCount === 1 ? '' : 's'
                                                  } can be moved`
                                        }}
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onSaveAsTemplate"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.bookmark_add" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Save as template</q-item-label>
                                    <q-item-label caption>
                                        Snapshot the current items into a reusable template
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-separator />
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onExportCsv"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.file_download" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Export as CSV</q-item-label>
                                    <q-item-label caption>
                                        Download as a spreadsheet
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onPrint"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.print" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Print / Save as PDF</q-item-label>
                                    <q-item-label caption>
                                        Opens a printable view in a new tab
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-separator />
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onClearAll"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.playlist_remove" color="negative" />
                                </q-item-section>
                                <q-item-section class="text-negative">
                                    Clear all items
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </BaseButton>
                <!-- One primary-action button per lifecycle phase:
                     DRAFT → Start shopping → SHOPPING → Finish & restock → DONE → Reopen.
                     SHOPPING is the shop-mode surface, reached via auto-redirect,
                     so the SHOPPING-phase button doesn't render here. -->
                <BaseButton
                    v-if="detail.status === 'draft'"
                    variant="primary"
                    :icon="ICONS.shopping_cart"
                    label="Start shopping"
                    :disable="detail.lines.length === 0"
                    :loading="togglingProgress"
                    @click="onStartShopping"
                >
                    <q-tooltip>Switch to shop mode and tick items off as you grab them</q-tooltip>
                </BaseButton>
                <BaseButton
                    v-else-if="detail.status === 'done'"
                    variant="primary"
                    :icon="ICONS.undo"
                    label="Reopen"
                    :loading="reopening"
                    @click="onReopen"
                >
                    <q-tooltip>Reopen this list to keep editing it; restock changes are reversed</q-tooltip>
                </BaseButton>
                <!-- Copy-to-new is also reachable from the list selector
                     on archived rows (Chunk 5), but keep an inline
                     affordance when the user is already on the done
                     list — saves a trip through the selector. -->
                <BaseButton
                    v-if="detail.status === 'done'"
                    variant="ghost"
                    :icon="ICONS.content_copy"
                    label="Copy to new list"
                    @click="copyAll"
                />
            </div>
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            <strong>Couldn't load this list.</strong>
            {{ loadError }}
            <template #action>
                <q-btn flat no-caps label="Retry" @click="load" />
            </template>
        </q-banner>

        <FadeTransition mode="out-in">
        <div v-if="loading && !detail" key="sld-loading">
            <!-- Skeleton mirrors a few list rows while the list loads. -->
            <div v-for="n in 5" :key="n" class="row items-center q-gutter-sm q-py-sm">
                <AppSkeleton type="circle" width="24px" height="24px" />
                <AppSkeleton type="line" width="40%" height="1rem" />
                <q-space />
                <AppSkeleton type="line" width="64px" height="1rem" />
            </div>
        </div>

        <div v-else-if="detail" key="sld-content">
            <!-- P6-01 Chunk 7 — shopping-day banner. Surfaces when the
                 planned date is today (or has passed without finishing).
                 Full alert-type wiring (push, suggestion feed) is C-9. -->
            <q-banner
                v-if="shoppingDayBanner"
                dense
                rounded
                :class="shoppingDayBanner.tone === 'today' ? 'dora-bg-info-soft text-primary' : 'dora-bg-warning-soft'"
                class="q-mb-md"
            >
                <template #avatar>
                    <q-icon :name="ICONS.event_note" />
                </template>
                {{ shoppingDayBanner.text }}
                <template #action>
                    <q-btn flat no-caps label="Edit" @click="openPlannedDateEditor" />
                </template>
            </q-banner>

            <!-- Add-item bar (hidden mid-shop). The actual picker lives in
                 <QuickAddSheet> so search, frequently-added suggestions and
                 offer selection behave identically wherever it's triggered. -->
            <q-card
                v-if="detail.status !== 'shopping'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section class="row items-center q-gutter-sm">
                    <q-btn
                        color="primary"
                        no-caps
                        :icon="ICONS.add"
                        label="Quick add an item"
                        :disable="detail.status === 'done'"
                        @click="onOpenQuickAdd"
                    />
                    <span class="text-caption dora-text-muted">
                        Search across every stock item, pick the offer, and
                        drop it onto this list.
                    </span>
                </q-card-section>
            </q-card>

            <!-- Bulk-select toolbar — only when there are lines and not
                 archived. Tick-mode lets you select multiple lines and
                 act on them in one click. Hidden during a live shop to
                 keep the in-progress UX uncluttered. -->
            <q-banner
                v-if="
                    detail.lines.length > 0
                        && detail.status !== 'done'
                        && detail.status !== 'shopping'
                "
                class="q-mb-sm bulk-bar"
                :class="{ 'bulk-bar-active': bulkMode }"
                dense
                rounded
            >
                <template #avatar>
                    <q-icon :name="bulkMode ? 'checklist' : 'list_alt'" />
                </template>
                <span v-if="!bulkMode">
                    Want to tick or untick a bunch at once?
                </span>
                <span v-else>
                    {{ bulkSelection.size }} selected
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
                            label="Select all"
                            @click="selectAllLines"
                        />
                        <q-btn
                            flat
                            no-caps
                            :icon="ICONS.check_box"
                            label="Tick selected"
                            :disable="bulkSelection.size === 0"
                            :loading="bulkBusy"
                            @click="onBulkTick(true)"
                        />
                        <q-btn
                            flat
                            no-caps
                            :icon="ICONS.check_box_outline_blank"
                            label="Untick"
                            :disable="bulkSelection.size === 0"
                            :loading="bulkBusy"
                            @click="onBulkTick(false)"
                        />
                        <q-btn flat no-caps label="Done" @click="exitBulkMode" />
                    </template>
                </template>
            </q-banner>

            <!-- Lines -->
            <q-card v-if="detail.lines.length === 0" flat bordered>
                <q-card-section class="text-center dora-text-muted">
                    No items yet. Use <strong>Quick add</strong> above, or
                    <router-link to="/stock" class="text-primary">
                        cart-add from your stock list
                    </router-link>.
                </q-card-section>
            </q-card>

            <template v-else>
                <div
                    v-for="group in lineGroups"
                    :key="group.key"
                    class="q-mb-md"
                >
                    <div
                        v-if="groupBy !== 'none' && group.label"
                        class="text-subtitle2 dora-text-muted q-mb-xs row items-center q-gutter-xs"
                    >
                        <q-icon
                            :name="groupBy === 'location' ? 'place' : 'storefront'"
                            size="16px"
                        />
                        {{ group.label }}
                        <span class="text-caption">
                            ({{ group.lines.length }} item{{ group.lines.length === 1 ? '' : 's' }})
                        </span>
                    </div>
                    <q-list bordered separator>
                        <q-item
                            v-for="line in group.lines"
                            :key="line.line_id"
                            :class="{
                                'shopping-line-ticked': line.is_ticked,
                                'shopping-line-dragging': dragLineId === line.line_id,
                                'shopping-line-drop-over': dragOverLineId === line.line_id,
                                'shopping-line-focused': focusedLineId === line.line_id,
                            }"
                            :draggable="canReorder"
                            @dragstart="onLineDragStart($event, line.line_id)"
                            @dragend="onLineDragEnd"
                            @dragover.prevent="onLineDragOver($event, line.line_id)"
                            @dragleave="onLineDragLeave($event, line.line_id)"
                            @drop="onLineDrop($event, line.line_id)"
                        >
                            <q-item-section
                                v-if="canReorder"
                                side
                                top
                                class="shopping-line-drag-handle"
                            >
                                <q-icon :name="ICONS.drag_indicator" class="dora-text-muted" />
                                <q-tooltip>Drag to reorder</q-tooltip>
                            </q-item-section>
                            <q-item-section v-if="bulkMode" side top>
                                <q-checkbox
                                    :model-value="bulkSelection.has(line.line_id)"
                                    @update:model-value="toggleBulkLine(line.line_id)"
                                />
                            </q-item-section>
                            <q-item-section side top>
                                <q-checkbox
                                    :model-value="line.is_ticked"
                                    :disable="detail.status === 'done'"
                                    @update:model-value="onToggleTicked(line.line_id, $event)"
                                />
                            </q-item-section>

                            <q-item-section>
                                <!-- The chip carries level, alert dot,
                                     on-list indicator and the cross-feature
                                     menu (find substitutes, see recipes etc.)
                                     consistently with every other screen. -->
                                <div
                                    class="row items-center q-gutter-xs"
                                    :class="{
                                        'shopping-line-ticked-content': line.is_ticked,
                                    }"
                                >
                                    <StockItemChip
                                        v-if="stockItemFor(line.stock_item_id)"
                                        :stock-item="stockItemFor(line.stock_item_id)!"
                                    />
                                    <q-chip
                                        v-else
                                        dense
                                        class="dora-text-muted"
                                    >
                                        {{ line.stock_item_name }}
                                    </q-chip>
                                </div>
                                <q-item-label caption class="q-mt-xs">
                                    <q-chip
                                        v-if="line.added_via && line.added_via !== 'manual'"
                                        dense
                                        size="sm"
                                        class="dora-bg-elevated q-mr-sm"
                                        text-color="grey"
                                        :icon="ICONS.auto_awesome"
                                    >
                                        {{ addedViaLabel(line.added_via) }}
                                    </q-chip>
                                    <span
                                        v-if="line.stock_location_breadcrumb.length > 0"
                                        class="q-mr-sm"
                                    >
                                        <q-icon :name="ICONS.place" size="14px" />
                                        {{ line.stock_location_breadcrumb.join(' › ') }}
                                    </span>
                                    <span v-if="line.offers.length > 0">
                                        {{ line.offers.length }} merchant offer{{
                                            line.offers.length === 1 ? '' : 's'
                                        }}
                                    </span>
                                    <span v-else class="dora-text-muted">
                                        No linked products
                                    </span>
                                </q-item-label>
                                <div
                                    v-if="line.offers.length > 0"
                                    class="row q-gutter-xs q-mt-xs"
                                >
                                    <q-chip
                                        v-for="offer in line.offers"
                                        :key="offer.product_id"
                                        dense
                                        :outline="!isChosen(line, offer.product_id)"
                                        :color="
                                            isChosen(line, offer.product_id)
                                                ? 'primary'
                                                : undefined
                                        "
                                        :text-color="
                                            isChosen(line, offer.product_id)
                                                ? 'white'
                                                : undefined
                                        "
                                        clickable
                                        :disable="detail.status === 'done'"
                                        @click="onPickOffer(line.line_id, offer.product_id)"
                                    >
                                        <q-icon
                                            v-if="offer.is_preferred"
                                            name="star"
                                            size="14px"
                                            color="warning"
                                            class="q-mr-xs"
                                        >
                                            <q-tooltip>Preferred merchant for this item</q-tooltip>
                                        </q-icon>
                                        <q-icon
                                            v-else
                                            name="storefront"
                                            size="14px"
                                            class="q-mr-xs"
                                        />
                                        {{ offer.merchant_name }} ·
                                        {{ offer.price_now != null ? `$${offer.price_now.toFixed(2)}` : '—' }}
                                        <span
                                            v-if="offerSavings(offer) > 0"
                                            class="q-ml-xs offer-savings"
                                            :class="
                                                isChosen(line, offer.product_id)
                                                    ? 'text-amber-2'
                                                    : 'text-positive'
                                            "
                                        >
                                            save ${{ offerSavings(offer).toFixed(2) }}
                                        </span>
                                        <q-tooltip>
                                            {{ offer.brand ? `${offer.brand} — ` : '' }}{{ offer.name }}
                                            <span v-if="offer.size"> ({{ offer.size }})</span>
                                            <span v-if="offer.price_was != null && offer.price_now != null">
                                                · RRP ${{ offer.price_was.toFixed(2) }}
                                            </span>
                                        </q-tooltip>
                                    </q-chip>
                                </div>
                            </q-item-section>

                            <q-item-section side style="min-width: 140px">
                                <div class="row items-center q-gutter-xs no-wrap">
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        size="sm"
                                        :icon="ICONS.remove"
                                        :disable="detail.status === 'done' || (line.quantity ?? 0) <= 0"
                                        @click="onAdjustQuantity(line, -1)"
                                    />
                                    <q-input
                                        :model-value="line.quantity ?? ''"
                                        dense
                                        borderless
                                        type="number"
                                        :min="0"
                                        input-class="text-center shopping-line-qty-input"
                                        style="width: 48px"
                                        :disable="detail.status === 'done'"
                                        placeholder="—"
                                        @blur="onQuantityBlur(line, $event)"
                                        @keydown.enter.prevent="
                                            ($event.target as HTMLInputElement).blur()
                                        "
                                    />
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        size="sm"
                                        :icon="ICONS.add"
                                        :disable="detail.status === 'done'"
                                        @click="onAdjustQuantity(line, 1)"
                                    />
                                </div>
                                <div class="row items-center justify-end no-wrap q-gutter-xs">
                                    <q-icon
                                        v-if="line.actual_unit_price != null"
                                        :name="ICONS.edit"
                                        size="12px"
                                        color="primary"
                                    >
                                        <q-tooltip>
                                            You entered ${{ line.actual_unit_price.toFixed(2) }} per unit
                                            <span v-if="line.purchased_merchant_name">
                                                at {{ line.purchased_merchant_name }}
                                            </span>
                                        </q-tooltip>
                                    </q-icon>
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        size="sm"
                                        :disable="detail.status === 'done'"
                                        class="line-price-btn"
                                        :class="{
                                            'text-primary text-weight-medium':
                                                line.actual_unit_price != null,
                                            'text-grey': line.actual_unit_price == null,
                                        }"
                                        :label="
                                            priceForLine(line) > 0
                                                ? `$${priceForLine(line).toFixed(2)}`
                                                : 'Set price'
                                        "
                                    >
                                        <q-tooltip v-if="detail.status !== 'done'">
                                            Enter the price you actually paid
                                        </q-tooltip>
                                        <q-popup-proxy
                                            v-if="detail.status !== 'done'"
                                            @before-show="onOpenPriceEditor(line)"
                                            cover
                                            transition-show="scale"
                                            transition-hide="scale"
                                        >
                                            <q-card style="min-width: 260px">
                                                <q-card-section class="q-pb-none">
                                                    <div class="text-subtitle2">
                                                        Actual price paid
                                                    </div>
                                                    <div class="text-caption dora-text-muted">
                                                        Overrides the offer price for totals
                                                        and feeds Dora's purchase history.
                                                    </div>
                                                </q-card-section>
                                                <q-card-section class="q-gutter-sm">
                                                    <q-input
                                                        v-model.number="priceEditorDraft.price"
                                                        autofocus
                                                        dense
                                                        outlined
                                                        type="number"
                                                        step="0.01"
                                                        min="0"
                                                        label="Unit price"
                                                        prefix="$"
                                                        @keydown.enter.prevent="savePriceEditor(line)"
                                                    />
                                                    <q-select
                                                        v-if="merchantOptionsFor(line).length > 0"
                                                        v-model="priceEditorDraft.merchant_id"
                                                        :options="merchantOptionsFor(line)"
                                                        dense
                                                        outlined
                                                        emit-value
                                                        map-options
                                                        clearable
                                                        label="Bought from (optional)"
                                                    />
                                                </q-card-section>
                                                <q-card-actions align="right">
                                                    <q-btn
                                                        v-if="line.actual_unit_price != null"
                                                        flat
                                                        no-caps
                                                        color="negative"
                                                        label="Clear"
                                                        v-close-popup
                                                        @click="clearPriceOverride(line)"
                                                    />
                                                    <q-btn
                                                        flat
                                                        no-caps
                                                        label="Cancel"
                                                        v-close-popup
                                                    />
                                                    <q-btn
                                                        unelevated
                                                        no-caps
                                                        color="primary"
                                                        label="Save"
                                                        v-close-popup
                                                        @click="savePriceEditor(line)"
                                                    />
                                                </q-card-actions>
                                            </q-card>
                                        </q-popup-proxy>
                                    </q-btn>
                                </div>
                                <div
                                    v-if="line.purchased_merchant_name"
                                    class="text-caption dora-text-muted text-right"
                                >
                                    {{ line.purchased_merchant_name }}
                                </div>
                            </q-item-section>

                            <q-item-section side>
                                <q-btn
                                    flat
                                    round
                                    dense
                                    :icon="ICONS.more_vert"
                                    :disable="detail.status === 'done'"
                                >
                                    <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                                        <q-list dense style="min-width: 220px">
                                            <q-item
                                                clickable
                                                @click="onSwapSubstitute(line)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon :name="ICONS.swap_horiz" />
                                                </q-item-section>
                                                <q-item-section>
                                                    Swap with substitute…
                                                </q-item-section>
                                            </q-item>
                                            <q-item
                                                clickable
                                                :disable="otherActiveLists.length === 0"
                                                @click="onMoveLine(line)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon :name="ICONS.drive_file_move" />
                                                </q-item-section>
                                                <q-item-section>
                                                    <q-item-label>Move to another list…</q-item-label>
                                                    <q-item-label
                                                        v-if="otherActiveLists.length === 0"
                                                        caption
                                                    >
                                                        No other active lists
                                                    </q-item-label>
                                                </q-item-section>
                                            </q-item>
                                            <q-separator />
                                            <q-item
                                                clickable
                                                @click="onRemoveLine(line.line_id)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon :name="ICONS.delete_outline" color="negative" />
                                                </q-item-section>
                                                <q-item-section class="text-negative">
                                                    Remove from list
                                                </q-item-section>
                                            </q-item>
                                        </q-list>
                                    </q-menu>
                                </q-btn>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </div>
            </template>

            <!-- Totals -->
            <q-card v-if="detail.lines.length > 0" flat bordered class="q-mt-md">
                <q-card-section class="row items-center q-gutter-md">
                    <div class="col">
                        <div class="text-caption dora-text-muted">Remaining (unticked)</div>
                        <div class="text-h6">${{ remainingTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator vertical />
                    <div class="col">
                        <div class="text-caption dora-text-muted">Picked up so far</div>
                        <div class="text-h6">${{ tickedTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator vertical />
                    <div class="col">
                        <div class="text-caption dora-text-muted">Full list total</div>
                        <div class="text-h6">${{ fullTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator v-if="savingsTotal > 0" vertical />
                    <div v-if="savingsTotal > 0" class="col">
                        <div class="text-caption dora-text-muted">Savings vs RRP</div>
                        <div class="text-h6 text-positive">
                            ${{ savingsTotal.toFixed(2) }}
                        </div>
                    </div>
                </q-card-section>
            </q-card>
        </div>

        <!-- Fallback so the content area is never blank — e.g. when
             load() fails (loadError banner above carries the message)
             or the listId in the URL doesn't resolve. Pre-Chunk-7 this
             template had no fallback branch and silently rendered
             nothing when both `loading=false` and `detail=null` were
             true. -->
        <div v-else key="sld-empty" class="text-center dora-text-muted q-py-xl">
            <q-icon :name="ICONS.shopping_cart" size="60px" class="q-mb-sm" />
            <div v-if="loadError" class="text-h6">Couldn't open this list.</div>
            <div v-else class="text-h6">This list isn't available.</div>
            <div class="q-mt-md">
                Pick another list from the selector at the top, or create
                a new one.
            </div>
            <div class="q-mt-md">
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.add"
                    label="New list"
                    @click="newListOpen = true"
                />
            </div>
        </div>
        </FadeTransition>

        <!-- P6-01 Chunk 5 — the New-list dialog lives on the detail page now
             that Detail is the canonical surface. The router landing page
             also mounts this dialog for the no-lists empty state. -->
        <NewListDialog
            v-model="newListOpen"
            @created="onListCreated"
        />

        <!-- P6-01 Chunk 7 — planned-shop-date editor. Sets/changes/clears
             the planned day for this list. Sort + banner + landing pick
             all read from it. -->
        <BaseDialog v-model="plannedDateOpen" card-style="min-width: 280px">
            <q-card-section>
                <div class="text-h6">Plan this shop for</div>
                <div class="text-caption dora-text-muted">
                    Sets which list opens first on shopping day, and
                    surfaces a banner when the day arrives.
                </div>
            </q-card-section>
            <q-card-section>
                <q-input
                    v-model="plannedDateDraft"
                    type="date"
                    outlined
                    dense
                    autofocus
                    label="Shop day"
                    clearable
                    @keydown.enter.prevent="savePlannedDate"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    v-if="detail?.planned_shop_date"
                    variant="ghost"
                    label="Clear"
                    class="text-negative"
                    @click="clearPlannedDate"
                />
                <BaseButton
                    variant="primary"
                    label="Save"
                    :disable="!plannedDateDraft"
                    @click="savePlannedDate"
                />
            </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import NewListDialog from 'src/components/dialogs/NewListDialog.vue';
    import { useQuasar } from 'quasar';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import { notifyUndoable } from 'src/composables/useNotifyUndoable';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { useShoppingListExport } from 'src/composables/useShoppingListExport';
    import { useShortcut } from 'src/composables/useShortcut';
    import { tryWithQueue } from 'src/composables/useOfflineQueue';
    import { register as registerUndo } from 'src/composables/useUndo';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import {
        chosenOfferFor,
        priceOfLine,
        type LineProductOffer,
        type ShoppingListDetail,
        type ShoppingListLine,
        type ShoppingListSummary
    } from 'src/models/shoppingList';
    import type { StockItem } from 'src/models/stockItem';
    import type { Substitute } from 'src/models/stockItemDetail';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const api = new ShoppingListApiService();
    const templateApi = new ShoppingListTemplateApiService();
    const stockItemApi = new StockItemApiService();
    const store = useShoppingListStore();
    const stockItemStore = useStockItemStore();
    const { openQuickAdd, isOpen: quickAddOpen } = useQuickAdd();

    const listId = computed(() => String(route.params.id ?? ''));
    const detail = ref<ShoppingListDetail | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const editingName = ref(false);
    const nameDraft = ref('');

    // Group lines by nothing, by stock location (matches the shopper's
    // route through the store) or by chosen merchant. Location is the
    // P5 default because most shopping happens at one merchant but across
    // many storage spots.
    type GroupByMode = 'none' | 'location' | 'merchant';
    const groupBy = ref<GroupByMode>('none');
    const groupByOptions: { value: GroupByMode; label: string }[] = [
        { value: 'none', label: 'Nothing (just sequence)' },
        { value: 'location', label: 'Stock location' },
        { value: 'merchant', label: 'Merchant' },
    ];

    // ── Start/stop shopping ───────────────────────────────────────────
    const togglingProgress = ref(false);
    const reopening = ref(false);

    async function onStartShopping() {
        togglingProgress.value = true;
        try {
            await api.startShoppingAsync(listId.value);
            // SHOPPING is the shop-mode surface — route there directly so
            // the user lands in the in-store view without an intermediate
            // page flash here. The status watcher below also covers the
            // case where the status flips elsewhere (assistant action, etc).
            void router.replace(`/shopping-lists/${listId.value}/shop`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not start shopping.',
                caption: describeApiError(err) || '',
            });
        } finally {
            togglingProgress.value = false;
        }
    }

    async function onReopen() {
        if (!detail.value) return;
        reopening.value = true;
        try {
            await api.unfinishAsync(listId.value);
            await Promise.all([
                refreshAll(),
                stockItemStore.getStockItemsAsync(),
            ]);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Reopened. Restock changes reversed.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not reopen.',
                caption: describeApiError(err) || '',
            });
        } finally {
            reopening.value = false;
        }
    }

    // ── Bulk-select ───────────────────────────────────────────────────
    const bulkMode = ref(false);
    const bulkSelection = ref<Set<string>>(new Set());
    const bulkBusy = ref(false);

    function enterBulkMode() {
        bulkMode.value = true;
        bulkSelection.value = new Set();
    }
    function exitBulkMode() {
        bulkMode.value = false;
        bulkSelection.value = new Set();
    }
    function toggleBulkLine(lineId: string) {
        if (bulkSelection.value.has(lineId)) {
            bulkSelection.value.delete(lineId);
        } else {
            bulkSelection.value.add(lineId);
        }
        // Force reactivity — Set mutation isn't shallow-tracked.
        bulkSelection.value = new Set(bulkSelection.value);
    }
    function selectAllLines() {
        const ids = (detail.value?.lines ?? []).map((l) => l.line_id);
        bulkSelection.value = new Set(ids);
    }
    async function onBulkTick(isTicked: boolean) {
        if (bulkSelection.value.size === 0) return;
        const ids = [...bulkSelection.value];
        bulkBusy.value = true;
        try {
            await api.bulkTickAsync(listId.value, ids, isTicked);
            await load();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `${ids.length} item${ids.length === 1 ? '' : 's'} ${
                    isTicked ? 'ticked' : 'unticked'
                }.`,
            });
            exitBulkMode();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Bulk update failed.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Drag-to-reorder ───────────────────────────────────────────────
    // Reorder is only available when the list isn't archived AND isn't
    // mid-shop AND there's no group-by-merchant filter active (reordering
    // *within* a merchant group would be confusing — disable the affordance
    // rather than try to be smart).
    const canReorder = computed(() =>
        !!detail.value
            && detail.value.status !== 'done'
            && detail.value.status !== 'shopping'
            && groupBy.value === 'none'
            && !bulkMode.value
    );

    const dragLineId = ref<string | null>(null);
    const dragOverLineId = ref<string | null>(null);
    const DRAG_MIME = 'application/x-dora-shopping-line';

    function onLineDragStart(event: DragEvent, lineId: string) {
        if (!event.dataTransfer) return;
        event.dataTransfer.setData(DRAG_MIME, lineId);
        event.dataTransfer.effectAllowed = 'move';
        dragLineId.value = lineId;
    }
    function onLineDragEnd() {
        dragLineId.value = null;
        dragOverLineId.value = null;
    }
    function onLineDragOver(event: DragEvent, lineId: string) {
        if (!event.dataTransfer?.types.includes(DRAG_MIME)) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        dragOverLineId.value = lineId;
    }
    function onLineDragLeave(_event: DragEvent, lineId: string) {
        if (dragOverLineId.value === lineId) dragOverLineId.value = null;
    }
    async function onLineDrop(event: DragEvent, targetLineId: string) {
        dragOverLineId.value = null;
        const draggedId = event.dataTransfer?.getData(DRAG_MIME);
        if (!draggedId || draggedId === targetLineId || !detail.value) return;
        event.preventDefault();

        // Build the new ordering. P6-01 Chunk 6 / feedback L414 — the old
        // logic subtracted 1 when dragging down, which left the dropped
        // line one row *before* the drag-over target (the "off-by-one"
        // bug). The user's mental model is: the dropped line lands at the
        // visual slot of the row they dragged over. Achieve that by
        // inserting at `toIdx` (the target's original DOM index) in every
        // case — for downward drags the target shifts up to make room,
        // for upward drags the target shifts down.
        const lines = detail.value.lines;
        const ids = lines.map((l) => l.line_id);
        const fromIdx = ids.indexOf(draggedId);
        const toIdx = ids.indexOf(targetLineId);
        if (fromIdx < 0 || toIdx < 0) return;
        ids.splice(fromIdx, 1);
        ids.splice(toIdx, 0, draggedId);

        // Optimistic local update so the UI reflects the move immediately.
        const lookup = new Map(lines.map((l) => [l.line_id, l]));
        const reordered = ids
            .map((id, idx) => {
                const line = lookup.get(id);
                if (!line) return null;
                line.sequence = idx;
                return line;
            })
            .filter((l): l is NonNullable<typeof l> => l !== null);
        detail.value.lines = reordered;

        try {
            await api.reorderLinesAsync(listId.value, ids);
        } catch (err) {
            await load();
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not reorder.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── Line grouping ────────────────────────────────────────────────
    // One flat list, or one bucket per stock location (in shopper-route
    // order — alphabetical for now since we don't have a route weight),
    // or one bucket per chosen merchant. "No location" / "No merchant"
    // lines drop into a labelled bucket at the end so they don't vanish.
    type LineGroup = { key: string; label: string | null; lines: ShoppingListLine[] };

    function locationKeyFor(line: ShoppingListLine): string {
        if (line.stock_location_breadcrumb.length === 0) return '__no_location__';
        return line.stock_location_breadcrumb.join(' › ');
    }

    const baseLines = computed(() => detail.value?.lines ?? []);

    const lineGroups = computed<LineGroup[]>(() => {
        const lines = baseLines.value;
        if (groupBy.value === 'none') {
            return [{ key: 'all', label: null, lines }];
        }
        const buckets = new Map<string, LineGroup>();
        for (const line of lines) {
            let key: string;
            let label: string;
            if (groupBy.value === 'merchant') {
                const chosen = chosenOfferFor(line);
                key = chosen?.merchant_name ?? '__no_merchant__';
                label = chosen?.merchant_name ?? 'No merchant linked';
            } else {
                key = locationKeyFor(line);
                label = key === '__no_location__' ? 'No location set' : key;
            }
            if (!buckets.has(key)) buckets.set(key, { key, label, lines: [] });
            buckets.get(key)!.lines.push(line);
        }
        // Sort lines inside each bucket alphabetically — within a bucket,
        // sequence is irrelevant because grouping has already broken the
        // shopper's manual ordering. Items with no chosen offer / no
        // location sink to the bottom of their group.
        for (const bucket of buckets.values()) {
            bucket.lines.sort((a, b) =>
                a.stock_item_name.localeCompare(b.stock_item_name)
            );
        }
        return [...buckets.values()].sort((a, b) => {
            const aMissing = a.key.startsWith('__');
            const bMissing = b.key.startsWith('__');
            if (aMissing && !bMissing) return 1;
            if (!aMissing && bMissing) return -1;
            return (a.label ?? '').localeCompare(b.label ?? '');
        });
    });

    // Stock items keyed by id, looked up from the store, so we can hand
    // the right StockItem to <StockItemChip> per line.
    function stockItemFor(stockItemId: string): StockItem | undefined {
        return stockItemStore.stockItems.find(
            (si) => si.stock_item_id === stockItemId
        );
    }

    const tickedCount = computed(() =>
        (detail.value?.lines ?? []).filter((l) => l.is_ticked).length
    );
    const untickedCount = computed(() =>
        (detail.value?.lines ?? []).filter((l) => !l.is_ticked).length
    );
    // List-level totals are server-owned (state-ownership Type B) — read them
    // off `detail.totals` rather than re-summing the lines here. Per-line price
    // display still uses `priceOfLine` (the accepted Type-C client helper).
    const remainingTotal = computed(() => detail.value?.totals?.remaining_price ?? 0);
    const fullTotal = computed(() => detail.value?.totals?.total_price ?? 0);
    const tickedTotal = computed(() => fullTotal.value - remainingTotal.value);
    // Savings vs RRP across the whole shop (ticked + unticked).
    const savingsTotal = computed(() => detail.value?.totals?.total_savings ?? 0);

    function isChosen(line: ShoppingListLine, productId: string): boolean {
        const chosen = chosenOfferFor(line);
        return chosen?.product_id === productId;
    }

    function priceForLine(line: ShoppingListLine): number {
        return priceOfLine(line);
    }

    function offerSavings(offer: LineProductOffer): number {
        if (offer.price_now == null || offer.price_was == null) return 0;
        const diff = offer.price_was - offer.price_now;
        return diff > 0 ? diff : 0;
    }

    function formatDate(iso: string): string {
        try {
            return new Date(iso).toLocaleDateString();
        } catch {
            return iso;
        }
    }

    // ── Planned shop date (Chunk 7) ──────────────────────────────────
    // Display label + banner + edit dialog. Banner only fires on lists
    // that aren't archived — a done list's planned date is historical.
    const plannedDateOpen = ref(false);
    const plannedDateDraft = ref<string | null>(null);

    function todayIso(): string {
        return new Date().toISOString().slice(0, 10);
    }
    function tomorrowIso(): string {
        const t = new Date();
        t.setDate(t.getDate() + 1);
        return t.toISOString().slice(0, 10);
    }
    function daysFromToday(iso: string): number {
        const a = new Date(`${todayIso()}T00:00:00`);
        const b = new Date(`${iso}T00:00:00`);
        return Math.round((b.getTime() - a.getTime()) / 86_400_000);
    }

    const plannedShopLabel = computed(() => {
        const d = detail.value?.planned_shop_date ?? null;
        if (!d) return 'No shop day';
        if (d === todayIso()) return 'Shop day: today';
        if (d === tomorrowIso()) return 'Shop day: tomorrow';
        const days = daysFromToday(d);
        if (days < 0) return `Shop day: ${formatDate(d)} (overdue)`;
        return `Shop day: ${formatDate(d)}`;
    });

    const shoppingDayBanner = computed<{ text: string; tone: 'today' | 'overdue' } | null>(() => {
        const d = detail.value?.planned_shop_date ?? null;
        if (!d || detail.value?.status === 'done') return null;
        if (d === todayIso()) {
            return { text: 'Shopping day is today.', tone: 'today' };
        }
        if (daysFromToday(d) < 0) {
            return { text: `Planned shop day was ${formatDate(d)} — still unfinished.`, tone: 'overdue' };
        }
        return null;
    });

    function openPlannedDateEditor() {
        plannedDateDraft.value = detail.value?.planned_shop_date ?? null;
        plannedDateOpen.value = true;
    }

    async function savePlannedDate() {
        if (!detail.value || !plannedDateDraft.value) return;
        const next = plannedDateDraft.value;
        try {
            await api.updateAsync(listId.value, { planned_shop_date: next });
            await Promise.all([load(), store.refreshAsync()]);
            plannedDateOpen.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save shop day.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function clearPlannedDate() {
        if (!detail.value) return;
        try {
            await api.updateAsync(listId.value, { planned_shop_date: null });
            await Promise.all([load(), store.refreshAsync()]);
            plannedDateOpen.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear shop day.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── List selector (Chunk 5) ──────────────────────────────────────
    // Detail is now the canonical surface — the dropdown next to the title
    // is the user's "go look at a different list" affordance, with per-list
    // archive/delete/copy actions inline (the old overview's kebab moved
    // here). The proposal eventually wants this as a desktop right-panel
    // and mobile dropdown; for Chunk 5 a single dropdown carries both.
    const newListOpen = ref(false);

    const activeSummaries = computed(() =>
        store.summaries
            .filter((s) => s.status !== 'done')
            // SHOPPING first, then by planned_shop_date (asc, scheduled
            // lists ahead of unscheduled — Chunk 7), then by created_at
            // desc as a final tiebreak.
            .slice()
            .sort((a, b) => {
                if (a.status !== b.status) {
                    if (a.status === 'shopping') return -1;
                    if (b.status === 'shopping') return 1;
                }
                const aDate = a.planned_shop_date;
                const bDate = b.planned_shop_date;
                if (aDate && bDate && aDate !== bDate) return aDate.localeCompare(bDate);
                if (aDate && !bDate) return -1;
                if (!aDate && bDate) return 1;
                return (b.created_at ?? '').localeCompare(a.created_at ?? '');
            }),
    );
    const archivedSummaries = computed(() =>
        store.summaries
            .filter((s) => s.status === 'done')
            .slice()
            .sort((a, b) => (b.completed_at ?? '').localeCompare(a.completed_at ?? '')),
    );

    function switchToList(id: string) {
        if (id === listId.value) return;
        void router.push(`/shopping-lists/${id}`);
    }

    function onListCreated({ listId: newId }: { listId: string }) {
        void store.refreshAsync();
        switchToList(newId);
    }

    // Per-list actions, moved from the old Overview kebab.
    async function archiveSummary(s: ShoppingListSummary) {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Archive "${s.name}"?`,
                message:
                    'Archived lists are read-only and move to the Archived section. '
                    + 'No stock levels are bumped — use Finish & restock for that.',
                ok: { label: 'Archive', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await api.updateAsync(s.shopping_list_id, { status: 'done' });
            await store.refreshAsync();
            if (s.shopping_list_id === listId.value) await load();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List archived.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not archive.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function deleteSummary(s: ShoppingListSummary) {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${s.name}"?`,
                message: 'This permanently removes the list and all its items.',
                ok: { label: 'Delete', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await api.deleteAsync(s.shopping_list_id);
            await store.refreshAsync();
            // If we deleted the list we're currently viewing, bounce to the
            // landing — it'll pick the next sensible target.
            if (s.shopping_list_id === listId.value) {
                void router.replace('/shopping-lists');
                return;
            }
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List deleted.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function copyListUnticked(s: ShoppingListSummary) {
        await copySummary(s, 'unticked');
    }
    async function copyListAll(s: ShoppingListSummary) {
        await copySummary(s, 'all');
    }
    async function copySummary(s: ShoppingListSummary, include: 'all' | 'unticked') {
        try {
            const { shopping_list_id } = await api.copyAsync(s.shopping_list_id, { include });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List copied.',
            });
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not copy.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function load() {
        loading.value = true;
        loadError.value = null;
        try {
            detail.value = await api.getDetailAsync(listId.value);
        } catch (err) {
            loadError.value = `Could not load list: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    async function refreshAll() {
        // Refresh detail + the store-level summaries/membership in
        // parallel so the cart-button state elsewhere stays accurate.
        await Promise.all([load(), store.refreshAsync()]);
    }

    function startNameEdit() {
        nameDraft.value = detail.value?.name ?? '';
        editingName.value = true;
    }

    function cancelName() {
        editingName.value = false;
    }

    async function saveName() {
        if (!detail.value) return;
        const next = nameDraft.value.trim();
        if (!next || next === detail.value.name) {
            editingName.value = false;
            return;
        }
        try {
            await api.updateAsync(listId.value, { name: next });
            await refreshAll();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not rename.',
                caption: describeApiError(err) || '',
            });
        } finally {
            editingName.value = false;
        }
    }

    function onOpenQuickAdd() {
        // Pre-target this list so the sheet skips its list picker default.
        openQuickAdd({ listId: listId.value });
    }

    // Status watcher: SHOPPING phase IS the shop-mode surface — when a list
    // becomes SHOPPING, route to it. Covers status flips from any path
    // (assistant action, another tab, the start-shopping button, etc.).
    watch(
        () => detail.value?.status,
        (status) => {
            if (status === 'shopping') {
                void router.replace(`/shopping-lists/${listId.value}/shop`);
            }
        },
    );

    // ── Keyboard shortcuts (S5) ──────────────────────────────────────────
    const orderedLines = computed(() => lineGroups.value.flatMap((g) => g.lines));
    const focusedLineId = ref<string | null>(null);

    function moveLineFocus(delta: number) {
        const lines = orderedLines.value;
        if (lines.length === 0) return;
        const current = lines.findIndex((l) => l.line_id === focusedLineId.value);
        const next = current < 0 ? 0 : Math.max(0, Math.min(lines.length - 1, current + delta));
        focusedLineId.value = lines[next]?.line_id ?? null;
    }
    function tickFocusedLine() {
        if (detail.value?.status === 'done') return;
        const line = orderedLines.value.find((l) => l.line_id === focusedLineId.value);
        if (line) void onToggleTicked(line.line_id, !line.is_ticked);
    }

    useShortcut([
        { keys: 'n', scope: 'Shopping list', description: 'Add an item', handler: onOpenQuickAdd },
        { keys: 'space', scope: 'Shopping list', description: 'Tick / untick the focused line', handler: tickFocusedLine },
        { keys: 'arrowdown', scope: 'Shopping list', description: 'Focus next line', handler: () => moveLineFocus(1) },
        { keys: 'arrowup', scope: 'Shopping list', description: 'Focus previous line', handler: () => moveLineFocus(-1) },
    ]);

    // QuickAddSheet writes via shoppingListStore.refreshAsync but the
    // per-list detail isn't part of that refresh — reload it locally
    // whenever the sheet closes so a freshly-added line shows up.
    watch(quickAddOpen, (open, wasOpen) => {
        if (wasOpen && !open) void load();
    });

    // ── Swap with substitute ─────────────────────────────────────────
    async function onSwapSubstitute(line: ShoppingListLine) {
        // Pull substitutes from the stock item's detail — we don't keep
        // them in the line DTO because they're a per-item attribute and
        // would bloat every line.
        let subs: Substitute[] = [];
        try {
            const itemDetail = await stockItemApi.getDetailAsync(line.stock_item_id);
            subs = itemDetail.substitutes ?? [];
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load substitutes.',
                caption: describeApiError(err) || '',
            });
            return;
        }
        if (subs.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `No substitutes recorded for ${line.stock_item_name}.`,
                caption: 'Add some on the stock item\'s detail page.',
            });
            return;
        }
        // Filter out subs already on this list — swapping into a duplicate
        // would just delete the line.
        const onListIds = new Set(detail.value?.lines.map((l) => l.stock_item_id) ?? []);
        const choosable = subs.filter((s) => !onListIds.has(s.stock_item_id));
        if (choosable.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'All recorded substitutes are already on this list.',
            });
            return;
        }
        const targetId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: `Swap ${line.stock_item_name} with…`,
                options: {
                    type: 'radio',
                    model: '',
                    items: choosable.map((s) => ({
                        label: s.name + (s.stock_level_name ? ` (${s.stock_level_name})` : ''),
                        value: s.stock_item_id,
                    })),
                },
                ok: { label: 'Swap', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((value: string) => resolve(value || null))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!targetId) return;
        try {
            // Add-then-delete order: if the add fails we leave the original
            // line intact instead of silently emptying the slot.
            await api.addLineAsync(listId.value, {
                stock_item_id: targetId,
                quantity: line.quantity,
            });
            await api.deleteLineAsync(listId.value, line.line_id);
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Swapped with substitute.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not swap.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── Move single line to another list ─────────────────────────────
    async function onMoveLine(line: ShoppingListLine) {
        if (otherActiveLists.value.length === 0) return;
        const targetId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: `Move ${line.stock_item_name} to…`,
                options: {
                    type: 'radio',
                    model: '',
                    items: otherActiveLists.value.map((s) => ({
                        label: s.name,
                        value: s.shopping_list_id,
                    })),
                },
                ok: { label: 'Move', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((value: string) => resolve(value || null))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!targetId) return;
        try {
            const result = await api.addLineAsync(targetId, {
                stock_item_id: line.stock_item_id,
                quantity: line.quantity,
                selected_product_id: line.selected_product_id,
            });
            await api.deleteLineAsync(listId.value, line.line_id);
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: result.already_on_list
                    ? 'Already on target list — original line removed.'
                    : 'Moved.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move line.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onToggleTicked(lineId: string, value: boolean) {
        // Optimistic flip so the checkbox feels instant; if the request
        // fails we re-load the canonical state. Network errors specifically
        // are absorbed into the offline queue so ticking-off mid-shop keeps
        // working while we hunt for signal.
        const line = detail.value?.lines.find((l) => l.line_id === lineId);
        const wasTicked = line?.is_ticked ?? false;
        const itemName = line?.stock_item_name ?? 'item';
        if (line) line.is_ticked = value;
        try {
            const result = await tryWithQueue(
                () => api.updateLineAsync(listId.value, lineId, { is_ticked: value }),
                {
                    url: `${resolveBaseURL('dora')}/shopping-lists/${listId.value}/lines/${lineId}`,
                    method: 'PATCH',
                    body: { is_ticked: value },
                    kind: 'shopping_list_line_tick',
                    label: value ? 'Tick item' : 'Untick item',
                },
            );
            // If the request was queued, we keep the optimistic flip in
            // place — no re-load until the queue drains and the server
            // round-trip succeeds.
            void result;
            // F5: register a silent undo entry. Skipped when value didn't
            // actually change (defensive; checkbox events fire on identical
            // values during rapid taps).
            if (wasTicked !== value) {
                const applyTick = async (target: boolean) => {
                    await api.updateLineAsync(listId.value, lineId, { is_ticked: target });
                    const fresh = detail.value?.lines.find((l) => l.line_id === lineId);
                    if (fresh) fresh.is_ticked = target;
                };
                registerUndo({
                    label: value ? `Ticked ${itemName}` : `Unticked ${itemName}`,
                    inverse: () => applyTick(wasTicked),
                    redo: () => applyTick(value),
                });
            }
        } catch (err) {
            await load();
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update line.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── P2-02: actual price + merchant override ─────────────────────────
    // A small popover sits behind the price chip on each line. Users tap it
    // mid-shop or at finish time to type what the till actually charged and
    // (optionally) confirm which merchant they bought from. Both flow into
    // the assistant's purchase-history stats.
    const priceEditorDraft = reactive<{
        line_id: string | null;
        price: number | null;
        merchant_id: string | null;
    }>({ line_id: null, price: null, merchant_id: null });

    function onOpenPriceEditor(line: ShoppingListLine) {
        priceEditorDraft.line_id = line.line_id;
        // Seed with the existing override, or the chosen offer's price as a
        // helpful starting point (most edits are small tweaks from "what
        // the app said it'd be").
        if (line.actual_unit_price != null) {
            priceEditorDraft.price = line.actual_unit_price;
        } else {
            const offer = chosenOfferFor(line);
            priceEditorDraft.price = offer?.price_now ?? null;
        }
        if (line.purchased_merchant_id) {
            priceEditorDraft.merchant_id = line.purchased_merchant_id;
        } else {
            const offer = chosenOfferFor(line);
            priceEditorDraft.merchant_id = offer?.merchant_id ?? null;
        }
    }

    function merchantOptionsFor(line: ShoppingListLine) {
        const seen = new Map<string, string>();
        for (const offer of line.offers) {
            if (!seen.has(offer.merchant_id)) {
                seen.set(offer.merchant_id, offer.merchant_name);
            }
        }
        return Array.from(seen, ([value, label]) => ({ value, label }));
    }

    async function savePriceEditor(line: ShoppingListLine) {
        if (priceEditorDraft.line_id !== line.line_id) return;
        const nextPrice = priceEditorDraft.price;
        const nextMerchant = priceEditorDraft.merchant_id;
        // Empty/zero/negative input clears the override rather than storing
        // a meaningless number. The backend rejects negatives anyway; this
        // saves the round-trip.
        if (nextPrice == null || Number.isNaN(nextPrice) || nextPrice <= 0) {
            await clearPriceOverride(line);
            return;
        }
        const previousPrice = line.actual_unit_price;
        const previousMerchant = line.purchased_merchant_id;
        const previousMerchantName = line.purchased_merchant_name;
        line.actual_unit_price = nextPrice;
        line.purchased_merchant_id = nextMerchant ?? null;
        line.purchased_merchant_name =
            merchantOptionsFor(line).find((o) => o.value === nextMerchant)?.label ?? null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                actual_unit_price: nextPrice,
                ...(nextMerchant
                    ? { purchased_merchant_id: nextMerchant }
                    : { clear_purchased_merchant: true }),
            });
        } catch (err) {
            line.actual_unit_price = previousPrice;
            line.purchased_merchant_id = previousMerchant;
            line.purchased_merchant_name = previousMerchantName;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save the price.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function clearPriceOverride(line: ShoppingListLine) {
        const previousPrice = line.actual_unit_price;
        const previousMerchant = line.purchased_merchant_id;
        const previousMerchantName = line.purchased_merchant_name;
        if (previousPrice == null && previousMerchant == null) return;
        line.actual_unit_price = null;
        line.purchased_merchant_id = null;
        line.purchased_merchant_name = null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                clear_actual_unit_price: true,
                clear_purchased_merchant: true,
            });
        } catch (err) {
            line.actual_unit_price = previousPrice;
            line.purchased_merchant_id = previousMerchant;
            line.purchased_merchant_name = previousMerchantName;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear the price.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function setLineQuantity(line: ShoppingListLine, next: number | null) {
        const previous = line.quantity;
        if (previous === next) return;
        line.quantity = next;
        try {
            await api.updateLineAsync(listId.value, line.line_id, { quantity: next });
        } catch (err) {
            line.quantity = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update quantity.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onAdjustQuantity(line: ShoppingListLine, delta: number) {
        const current = line.quantity ?? 0;
        const next = Math.max(0, current + delta);
        await setLineQuantity(line, next);
    }

    function onQuantityBlur(line: ShoppingListLine, event: Event) {
        // Free-form quantity: blank input maps to `null` (spec: "I can set
        // the quantity of a stock item on a shopping list to nothing"). Any
        // valid integer >= 0 is persisted as-is. Garbage input is ignored
        // and the displayed value reverts to the prior persisted value.
        const target = event.target as HTMLInputElement;
        const raw = target.value.trim();
        if (raw === '') {
            void setLineQuantity(line, null);
            return;
        }
        const parsed = Number.parseInt(raw, 10);
        if (Number.isFinite(parsed) && parsed >= 0) {
            void setLineQuantity(line, parsed);
        } else {
            // Reset the visible value — bind is one-way for `model-value`
            // so we have to mutate the line ref explicitly.
            const current = line.quantity;
            line.quantity = null;
            // Next tick — assign back so the input re-renders the canonical value.
            void Promise.resolve().then(() => {
                line.quantity = current;
            });
        }
    }

    async function onPickOffer(lineId: string, productId: string) {
        const line = detail.value?.lines.find((l) => l.line_id === lineId);
        if (!line) return;
        const previous = line.selected_product_id;
        // Toggle: clicking the chosen offer clears the selection (falls
        // back to "cheapest" auto-selection).
        const next = previous === productId ? null : productId;
        line.selected_product_id = next;
        // Sync `is_selected` flags on the in-memory offers so chips repaint
        // without waiting for the round-trip.
        for (const offer of line.offers) {
            offer.is_selected = offer.product_id === next;
        }
        try {
            if (next === null) {
                await api.updateLineAsync(listId.value, lineId, {
                    clear_selected_product: true,
                });
            } else {
                await api.updateLineAsync(listId.value, lineId, {
                    selected_product_id: next,
                });
            }
        } catch (err) {
            line.selected_product_id = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not set offer.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onRemoveLine(lineId: string) {
        // F5: snapshot the line so undo can re-add it. We capture the
        // outward-facing shape (stock_item + qty + selected offer) — the
        // backend mints a fresh line_id on re-add, which is fine for the
        // user's purposes (they get the same item back at roughly the
        // same place; precise sequence isn't worth a reorder round-trip).
        const before = detail.value?.lines.find((l) => l.line_id === lineId);
        try {
            await api.deleteLineAsync(listId.value, lineId);
            await refreshAll();
            if (before) {
                const targetListId = listId.value;
                const snapshot = {
                    stock_item_id: before.stock_item_id,
                    quantity: before.quantity ?? null,
                    selected_product_id: before.selected_product_id ?? null,
                };
                notifyUndoable({
                    message: `Removed ${before.stock_item_name}.`,
                    undo: {
                        label: `Remove: ${before.stock_item_name}`,
                        inverse: async () => {
                            await api.addLineAsync(targetListId, snapshot);
                            await load();
                        },
                        redo: async () => {
                            // Re-removing by stock_item_id (the only stable
                            // handle now that the line_id has changed).
                            await api.removeByStockItemFromListAsync(
                                targetListId,
                                snapshot.stock_item_id,
                            );
                            await load();
                        },
                    },
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove line.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // Chunk 3 moved the finish-and-restock flow to ShoppingListShopMode.vue
    // (SHOPPING phase is the shop-mode surface; the detail's status watcher
    // routes the user there). The old `onFinish` on this page is gone with
    // the button that fired it.

    // ── Detail-page extra actions ─────────────────────────────────────

    const otherActiveLists = computed(() =>
        store.summaries.filter(
            (s) => s.status !== 'done' && s.shopping_list_id !== listId.value
        )
    );

    function addedViaLabel(via: string): string {
        switch (via) {
            case 'auto_low_stock':
                return 'auto: low stock';
            case 'auto_essential':
                return 'auto: essential';
            case 'auto_flagged':
                return 'auto: flagged';
            case 'auto_recipe':
                return 'auto: recipe';
            case 'auto_meal_plan':
                return 'auto: meal plan';
            case 'auto_frequently_added':
                return 'auto: often added';
            default:
                return via;
        }
    }

    async function onRefreshDeals() {
        try {
            const result = await api.refreshDealsAsync(listId.value);
            await load();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    result.selections_cleared > 0
                        ? `Refreshed. ${result.selections_cleared} stale selection${
                              result.selections_cleared === 1 ? '' : 's'
                          } cleared.`
                        : `Refreshed. ${result.lines_checked} line${
                              result.lines_checked === 1 ? '' : 's'
                          } checked, nothing changed.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not refresh deals.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // Export actions — both pull from the shared composable so this page
    // and ExportPrint.vue stay in lockstep on URL shape and filename.
    const exportActions = useShoppingListExport();

    function onExportCsv() {
        void exportActions.downloadCsv(listId.value);
    }

    function onPrint() {
        exportActions.openPrintView(listId.value);
    }

    async function onClearAll() {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Clear all items?',
                message: 'Every line on this list will be removed. The list stays.',
                ok: { label: 'Clear', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            const result = await api.clearListAsync(listId.value);
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Cleared ${result.removed_count} line${result.removed_count === 1 ? '' : 's'}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onSaveAsTemplate() {
        if (!detail.value) return;
        // Ask for a name and whether to include ticked items.
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Save as template',
                message:
                    'Snapshots the items on this list as a reusable template. ' +
                    'Quantities and selected merchant offers are reset on each use.',
                prompt: {
                    model: `Template from ${detail.value!.name}`,
                    type: 'text',
                    isValid: (val: string) => val.trim().length > 0,
                },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        // Include ticked items only when the list isn't archived and has
        // them — otherwise the default ("only unticked") is fine.
        const ticked = detail.value.lines.filter((l) => l.is_ticked).length;
        let includeTicked = false;
        if (ticked > 0) {
            includeTicked = await new Promise<boolean>((resolve) => {
                $q.dialog({
                    title: `${ticked} ticked item${ticked === 1 ? '' : 's'} — include?`,
                    message:
                        `Include ticked items in the template? Most users want "no" here — ticked items are usually one-offs.`,
                    ok: { label: 'Include ticked', noCaps: true },
                    cancel: { label: 'Skip ticked', noCaps: true },
                })
                    .onOk(() => resolve(true))
                    .onCancel(() => resolve(false))
                    .onDismiss(() => resolve(false));
            });
        }
        try {
            const result = await templateApi.snapshotFromListAsync(listId.value, {
                name,
                include_ticked: includeTicked,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Saved as template with ${result.line_count} item${
                    result.line_count === 1 ? '' : 's'
                }.`,
                actions: [
                    {
                        label: 'Open',
                        color: 'white',
                        handler: () => { void router.push('/shopping-lists/templates'); },
                    },
                ],
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save template.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onMoveUnticked() {
        if (untickedCount.value === 0 || otherActiveLists.value.length === 0) return;
        // Use Quasar's built-in `options` dialog (radio-style) rather than
        // building a custom picker — the user just needs to pick a target.
        const targetId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Move unticked items to…',
                message: `${untickedCount.value} unticked item${
                    untickedCount.value === 1 ? '' : 's'
                } will move. Duplicates already on the target list are skipped.`,
                options: {
                    type: 'radio',
                    model: '',
                    items: otherActiveLists.value.map((s) => ({
                        label: s.name,
                        value: s.shopping_list_id,
                    })),
                },
                ok: { label: 'Move', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((value: string) => resolve(value || null))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!targetId) return;
        try {
            const result = await api.moveUntickedToAsync(listId.value, targetId);
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Moved ${result.moved_count} item${
                        result.moved_count === 1 ? '' : 's'
                    }.` +
                    (result.skipped_duplicates > 0
                        ? ` ${result.skipped_duplicates} skipped (already on target).`
                        : ''),
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move items.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function copyAll() {
        try {
            const { shopping_list_id } = await api.copyAsync(listId.value, {
                include: 'all',
            });
            await store.refreshAsync();
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not copy.',
                caption: describeApiError(err) || '',
            });
        }
    }

    onMounted(async () => {
        if (stockItemStore.stockItems.length === 0) {
            await stockItemStore.getStockItemsAsync();
        }
        await load();
    });
</script>

<style scoped>
    .shopping-line-ticked {
        background-color: var(--overlay-hover);
    }
    .shopping-line-focused {
        outline: 2px dashed var(--q-accent);
        outline-offset: -2px;
    }
    .shopping-line-dragging {
        opacity: 0.4;
    }
    .shopping-line-drop-over {
        outline: 2px dashed var(--q-primary);
        outline-offset: -2px;
    }
    .shopping-line-drag-handle {
        cursor: grab;
    }
    .shopping-line-drag-handle:active {
        cursor: grabbing;
    }
    .bulk-bar {
        background: var(--overlay-hover);
    }
    .bulk-bar-active {
        background: var(--brand-primary-soft);
    }
    .shopping-line-name {
        font-weight: 500;
    }
    .shopping-line-ticked-content {
        opacity: 0.6;
    }
    .offer-savings {
        font-weight: 600;
        font-size: 0.92em;
    }
    .shopping-line-qty {
        min-width: 24px;
        text-align: center;
        font-weight: 500;
    }
    .shopping-line-qty-input {
        font-weight: 500;
        font-size: 0.95em;
        /* Hide the spinner controls from number inputs — they fight with our
           own +/- buttons and look noisy. */
        appearance: textfield;
        -moz-appearance: textfield;
    }
    .shopping-line-qty-input::-webkit-outer-spin-button,
    .shopping-line-qty-input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    .text-strike {
        text-decoration: line-through;
    }
</style>
