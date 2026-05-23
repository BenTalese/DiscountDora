<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <q-btn flat round dense icon="arrow_back" @click="goBack" />
            <div class="q-ml-sm col">
                <div class="text-h5">
                    <span v-if="!editingName">{{ detail?.name ?? 'Loading…' }}</span>
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
                    <q-btn
                        v-if="detail && !editingName"
                        flat
                        round
                        dense
                        size="sm"
                        icon="edit"
                        @click="startNameEdit"
                    >
                        <q-tooltip>Rename</q-tooltip>
                    </q-btn>
                </div>
                <div v-if="detail" class="text-caption text-grey">
                    {{ detail.lines.length }} item{{ detail.lines.length === 1 ? '' : 's' }} ·
                    {{ tickedCount }} ticked ·
                    Created {{ formatDate(detail.created_at) }}
                    <span v-if="detail.is_archived"> · Archived</span>
                </div>
            </div>

            <div v-if="detail && !detail.is_archived" class="row q-gutter-sm items-center">
                <q-btn
                    v-if="!detail.is_primary"
                    flat
                    no-caps
                    icon="star_outline"
                    label="Set primary"
                    @click="setPrimary"
                />
                <q-chip
                    v-else
                    dense
                    color="primary"
                    text-color="white"
                    icon="star"
                >
                    Primary
                </q-chip>
                <q-btn
                    flat
                    round
                    dense
                    icon="more_vert"
                >
                    <q-menu anchor="bottom right" self="top right">
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
                                    <q-icon name="refresh" />
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
                                    <q-icon name="drive_file_move" />
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
                                    <q-icon name="bookmark_add" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Save as template</q-item-label>
                                    <q-item-label caption>
                                        Snapshot the current items into a reusable template
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                v-close-popup
                                :disable="detail.lines.length === 0"
                                @click="onClearAll"
                            >
                                <q-item-section avatar>
                                    <q-icon name="playlist_remove" color="negative" />
                                </q-item-section>
                                <q-item-section class="text-negative">
                                    Clear all items
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </q-btn>
                <q-btn
                    flat
                    no-caps
                    :icon="reviewMode ? 'visibility_off' : 'preview'"
                    :label="reviewMode ? 'Exit review' : 'Review mode'"
                    :disable="tickedCount === 0"
                    @click="toggleReviewMode"
                >
                    <q-tooltip>
                        Show only ticked items and preview what will restock
                        when you finish.
                    </q-tooltip>
                </q-btn>
                <q-btn
                    v-if="!detail.is_in_progress"
                    color="primary"
                    no-caps
                    icon="play_arrow"
                    label="Start shopping"
                    :loading="togglingProgress"
                    @click="onStartShopping"
                />
                <q-btn
                    v-else
                    flat
                    no-caps
                    icon="pause"
                    label="Stop shopping"
                    :loading="togglingProgress"
                    @click="onStopShopping"
                />
                <q-btn
                    color="positive"
                    no-caps
                    icon="check_circle"
                    label="Finish shopping"
                    :loading="finishing"
                    @click="onFinish"
                />
            </div>
            <div v-else-if="detail" class="row q-gutter-sm">
                <q-btn
                    flat
                    no-caps
                    icon="content_copy"
                    label="Copy to new list"
                    @click="copyAll"
                />
            </div>
        </div>

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div v-if="loading && !detail" class="text-center q-py-xl">
            <q-spinner color="primary" size="48px" />
        </div>

        <template v-else-if="detail">
            <!-- In-progress banner — emphasises tick-mode + offers
                 a one-click stop. The picker hides while in progress. -->
            <q-banner
                v-if="detail.is_in_progress"
                class="bg-primary text-white q-mb-md"
                rounded
            >
                <template #avatar>
                    <q-icon name="shopping_cart_checkout" size="24px" />
                </template>
                <strong>Shopping in progress.</strong>
                Tick items off as you grab them. The list is locked from edits.
                <template #action>
                    <q-btn
                        flat
                        no-caps
                        color="white"
                        icon="pause"
                        label="Stop shopping"
                        :loading="togglingProgress"
                        @click="onStopShopping"
                    />
                </template>
            </q-banner>

            <!-- Add-item bar (hidden mid-shop and during review). The actual
                 picker lives in <QuickAddSheet> so search, frequently-added
                 suggestions and offer selection behave identically wherever
                 they're triggered from. -->
            <q-card
                v-if="!detail.is_in_progress && !reviewMode"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section class="row items-center q-gutter-sm">
                    <q-btn
                        color="primary"
                        no-caps
                        icon="add"
                        label="Quick add an item"
                        :disable="detail.is_archived"
                        @click="onOpenQuickAdd"
                    />
                    <span class="text-caption text-grey">
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
                        && !detail.is_archived
                        && !detail.is_in_progress
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
                            icon="checklist"
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
                            icon="check_box"
                            label="Tick selected"
                            :disable="bulkSelection.size === 0"
                            :loading="bulkBusy"
                            @click="onBulkTick(true)"
                        />
                        <q-btn
                            flat
                            no-caps
                            icon="check_box_outline_blank"
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
                <q-card-section class="text-center text-grey">
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
                        class="text-subtitle2 text-grey q-mb-xs row items-center q-gutter-xs"
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
                                <q-icon name="drag_indicator" color="grey-5" />
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
                                    :disable="detail.is_archived"
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
                                        color="grey-4"
                                    >
                                        {{ line.stock_item_name }}
                                    </q-chip>
                                </div>
                                <q-item-label caption class="q-mt-xs">
                                    <span
                                        v-if="line.stock_location_breadcrumb.length > 0"
                                        class="q-mr-sm"
                                    >
                                        <q-icon name="place" size="14px" />
                                        {{ line.stock_location_breadcrumb.join(' › ') }}
                                    </span>
                                    <span v-if="line.offers.length > 0">
                                        {{ line.offers.length }} merchant offer{{
                                            line.offers.length === 1 ? '' : 's'
                                        }}
                                    </span>
                                    <span v-else class="text-grey">
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
                                        :disable="detail.is_archived"
                                        @click="onPickOffer(line.line_id, offer.product_id)"
                                    >
                                        <q-icon
                                            v-if="offer.is_preferred"
                                            name="star"
                                            size="14px"
                                            color="amber-7"
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
                                        icon="remove"
                                        :disable="detail.is_archived || (line.quantity ?? 0) <= 0"
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
                                        :disable="detail.is_archived"
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
                                        icon="add"
                                        :disable="detail.is_archived"
                                        @click="onAdjustQuantity(line, 1)"
                                    />
                                </div>
                                <div class="text-caption text-grey text-right">
                                    {{
                                        priceForLine(line) > 0
                                            ? `$${priceForLine(line).toFixed(2)}`
                                            : '—'
                                    }}
                                </div>
                            </q-item-section>

                            <q-item-section side>
                                <q-btn
                                    flat
                                    round
                                    dense
                                    icon="more_vert"
                                    :disable="detail.is_archived"
                                >
                                    <q-menu auto-close>
                                        <q-list dense style="min-width: 220px">
                                            <q-item
                                                clickable
                                                @click="onSwapSubstitute(line)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon name="swap_horiz" />
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
                                                    <q-icon name="drive_file_move" />
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
                                                    <q-icon name="delete_outline" color="negative" />
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

            <!-- Review-mode preview: what will bump to Well-Stocked on
                 finish, so the user can sanity-check before archiving. -->
            <q-card
                v-if="reviewMode && detail.lines.length > 0"
                flat
                bordered
                class="q-mt-md bg-blue-1"
            >
                <q-card-section>
                    <div class="row items-center q-mb-sm">
                        <q-icon name="preview" class="q-mr-sm" />
                        <div class="text-subtitle1">
                            Review — {{ tickedCount }} item{{ tickedCount === 1 ? '' : 's' }} ready to finish
                        </div>
                    </div>
                    <div v-if="tickedCount === 0" class="text-grey">
                        Nothing is ticked yet — tick the items you've actually
                        picked up to preview what will restock.
                    </div>
                    <div v-else>
                        <div class="text-caption text-grey q-mb-xs">
                            These items will be bumped to <strong>Well-Stocked</strong>
                            when you finish:
                        </div>
                        <div class="row q-gutter-xs">
                            <template
                                v-for="line in tickedLines"
                                :key="line.line_id"
                            >
                                <StockItemChip
                                    v-if="stockItemFor(line.stock_item_id)"
                                    :stock-item="stockItemFor(line.stock_item_id)!"
                                />
                            </template>
                        </div>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Totals -->
            <q-card v-if="detail.lines.length > 0" flat bordered class="q-mt-md">
                <q-card-section class="row items-center q-gutter-md">
                    <div class="col">
                        <div class="text-caption text-grey">Remaining (unticked)</div>
                        <div class="text-h6">${{ remainingTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator vertical />
                    <div class="col">
                        <div class="text-caption text-grey">Picked up so far</div>
                        <div class="text-h6">${{ tickedTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator vertical />
                    <div class="col">
                        <div class="text-caption text-grey">Full list total</div>
                        <div class="text-h6">${{ fullTotal.toFixed(2) }}</div>
                    </div>
                    <q-separator v-if="savingsTotal > 0" vertical />
                    <div v-if="savingsTotal > 0" class="col">
                        <div class="text-caption text-grey">Savings vs RRP</div>
                        <div class="text-h6 text-positive">
                            ${{ savingsTotal.toFixed(2) }}
                        </div>
                    </div>
                </q-card-section>
            </q-card>
        </template>
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import { notifyUndoable } from 'src/composables/useNotifyUndoable';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { useShortcut } from 'src/composables/useShortcut';
    import { tryWithQueue } from 'src/composables/useOfflineQueue';
    import { register as registerUndo } from 'src/composables/useUndo';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import {
        chosenOfferFor,
        priceOfLine,
        savingsOfLine,
        type LineProductOffer,
        type ShoppingListDetail,
        type ShoppingListLine
    } from 'src/models/shoppingList';
    import type { StockItem } from 'src/models/stockItem';
    import type { Substitute } from 'src/models/stockItemDetail';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

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
    const finishing = ref(false);

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

    // Review mode: hides unticked lines and surfaces the bump-to-Well-Stocked
    // preview so the user can sanity-check before pulling the trigger on
    // Finish shopping.
    const reviewMode = ref(false);
    function toggleReviewMode() {
        reviewMode.value = !reviewMode.value;
    }

    // ── Start/stop shopping ───────────────────────────────────────────
    const togglingProgress = ref(false);

    async function onStartShopping() {
        togglingProgress.value = true;
        try {
            await api.startShoppingAsync(listId.value);
            await load();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Shopping started. Tick items off as you go.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not start shopping.',
                caption: String(err),
            });
        } finally {
            togglingProgress.value = false;
        }
    }

    async function onStopShopping() {
        togglingProgress.value = true;
        try {
            await api.stopShoppingAsync(listId.value);
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not stop shopping.',
                caption: String(err),
            });
        } finally {
            togglingProgress.value = false;
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
                caption: String(err),
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
            && !detail.value.is_archived
            && !detail.value.is_in_progress
            && groupBy.value === 'none'
            && !bulkMode.value
            && !reviewMode.value
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

        // Build the new ordering: take the current line ids, remove the
        // dragged one, re-insert it before the target.
        const lines = detail.value.lines;
        const ids = lines.map((l) => l.line_id);
        const fromIdx = ids.indexOf(draggedId);
        const toIdx = ids.indexOf(targetLineId);
        if (fromIdx < 0 || toIdx < 0) return;
        ids.splice(fromIdx, 1);
        // If we removed before the target, the target index shifts back by 1.
        const insertAt = fromIdx < toIdx ? toIdx - 1 : toIdx;
        ids.splice(insertAt, 0, draggedId);

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
                caption: String(err),
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

    const baseLines = computed(() => {
        const lines = detail.value?.lines ?? [];
        return reviewMode.value ? lines.filter((l) => l.is_ticked) : lines;
    });

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
    const tickedLines = computed(() =>
        (detail.value?.lines ?? []).filter((l) => l.is_ticked)
    );
    const remainingTotal = computed(() =>
        (detail.value?.lines ?? [])
            .filter((l) => !l.is_ticked)
            .reduce((sum, l) => sum + priceOfLine(l), 0)
    );
    const tickedTotal = computed(() =>
        (detail.value?.lines ?? [])
            .filter((l) => l.is_ticked)
            .reduce((sum, l) => sum + priceOfLine(l), 0)
    );
    const fullTotal = computed(() => remainingTotal.value + tickedTotal.value);
    // List-level savings vs RRP — sum across every line (ticked + unticked)
    // so the headline reflects the whole shop, not just what's left.
    const savingsTotal = computed(() =>
        (detail.value?.lines ?? []).reduce((sum, l) => sum + savingsOfLine(l), 0)
    );

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

    function goBack() {
        void router.push('/shopping-lists');
    }

    async function load() {
        loading.value = true;
        loadError.value = null;
        try {
            detail.value = await api.getDetailAsync(listId.value);
        } catch (err) {
            loadError.value = `Could not load list: ${String(err)}`;
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
                caption: String(err),
            });
        } finally {
            editingName.value = false;
        }
    }

    async function setPrimary() {
        try {
            await api.updateAsync(listId.value, { is_primary: true });
            await refreshAll();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not set primary.',
                caption: String(err),
            });
        }
    }

    function onOpenQuickAdd() {
        // Pre-target this list so the sheet skips its list picker default.
        openQuickAdd({ listId: listId.value });
    }

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
        if (detail.value?.is_archived) return;
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
                caption: String(err),
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
                caption: String(err),
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
                        label: s.name + (s.is_primary ? ' (primary)' : ''),
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
                caption: String(err),
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
                caption: String(err),
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
                caption: String(err),
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
                caption: String(err),
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
                caption: String(err),
            });
        }
    }

    async function onFinish() {
        if (!detail.value) return;
        const unticked = detail.value.lines.length - tickedCount.value;

        // When there are unticked items, give the user a three-way choice:
        //   - Cancel
        //   - Copy unticked to a new list (carries them over) then finish
        //   - Finish anyway (unticked are archived with the list)
        let copyUnticked = false;
        if (unticked > 0) {
            const choice = await new Promise<'copy' | 'finish' | null>((resolve) => {
                $q.dialog({
                    title: 'Finish shopping?',
                    message:
                        `${unticked} unticked item${unticked === 1 ? '' : 's'} ` +
                        `${unticked === 1 ? 'is' : 'are'} still on this list. ` +
                        `Copy ${unticked === 1 ? 'it' : 'them'} to a new active list, ` +
                        `or finish anyway?`,
                    options: {
                        type: 'radio',
                        model: 'copy',
                        items: [
                            {
                                label: `Copy unticked to a new list, then finish`,
                                value: 'copy',
                            },
                            {
                                label: `Finish anyway (unticked archived too)`,
                                value: 'finish',
                            },
                        ],
                    },
                    ok: { label: 'Finish', color: 'positive', noCaps: true },
                    cancel: { noCaps: true },
                    persistent: true,
                })
                    .onOk((value: 'copy' | 'finish') => resolve(value || 'finish'))
                    .onCancel(() => resolve(null))
                    .onDismiss(() => resolve(null));
            });
            if (choice === null) return;
            copyUnticked = choice === 'copy';
        } else {
            const ok = await new Promise<boolean>((resolve) => {
                $q.dialog({
                    title: 'Finish shopping?',
                    message:
                        'Archives the list and resets ticked items\' stock level to Well-Stocked.',
                    ok: { label: 'Finish', color: 'positive', noCaps: true },
                    cancel: { noCaps: true },
                    persistent: true,
                })
                    .onOk(() => resolve(true))
                    .onCancel(() => resolve(false))
                    .onDismiss(() => resolve(false));
            });
            if (!ok) return;
        }

        finishing.value = true;
        // F5: capture the pre-finish snapshot so undo can roll the levels
        // (and the archived flag, and primary status) back. We capture
        // *before* the finish API call so the read can't race with the
        // restock writes.
        const wasPrimary = detail.value.is_primary;
        const listName = detail.value.name;
        const sourceListId = listId.value;
        const levelRestores: { stock_item_id: string; stock_level_id: string }[] = [];
        for (const line of detail.value.lines) {
            if (!line.is_ticked) continue;
            const item = stockItemStore.stockItems.find(
                (si) => si.stock_item_id === line.stock_item_id,
            );
            if (!item) continue;
            levelRestores.push({
                stock_item_id: line.stock_item_id,
                stock_level_id: item.stock_level_id,
            });
        }
        try {
            // Copy first — if the copy fails we'd rather leave the list
            // unarchived so the user can retry, than silently lose lines.
            let copiedListId: string | null = null;
            if (copyUnticked) {
                const copy = await api.copyAsync(listId.value, { include: 'unticked' });
                copiedListId = copy.shopping_list_id;
            }
            const result = await api.finishAsync(listId.value);
            // Register the undo *after* we know the server succeeded —
            // includes the new-primary-list-id so undo can demote it.
            registerUndo({
                label: `Finish: ${listName}`,
                inverse: async () => {
                    await api.unfinishAsync(sourceListId, {
                        was_primary: wasPrimary,
                        demote_primary_list_id: result.new_primary_list_id ?? null,
                        level_restores: levelRestores,
                    });
                    await Promise.all([
                        store.refreshAsync(),
                        stockItemStore.getStockItemsAsync(),
                    ]);
                    // After unfinishing we're back on an active list —
                    // route the user there so they can resume.
                    void router.push(`/shopping-lists/${sourceListId}`);
                },
                // Redo is the same shape as finish, but the list-promotion
                // logic on the server side might pick a different "new
                // primary" candidate this time — that's acceptable for a
                // redo (user explicitly asked to refire the action).
                redo: async () => {
                    await api.finishAsync(sourceListId);
                    await Promise.all([
                        store.refreshAsync(),
                        stockItemStore.getStockItemsAsync(),
                    ]);
                },
            });
            if (copiedListId) {
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message:
                        `Finished. ${result.items_restocked} item${
                            result.items_restocked === 1 ? '' : 's'
                        } restocked. Unticked items copied to a new list.`,
                    actions: [
                        {
                            label: 'Open new list',
                            color: 'white',
                            handler: () => router.push(`/shopping-lists/${copiedListId}`),
                        },
                    ],
                });
                await Promise.all([store.refreshAsync(), stockItemStore.getStockItemsAsync()]);
                void router.push(`/shopping-lists/${copiedListId}`);
                return;
            }
            await Promise.all([store.refreshAsync(), stockItemStore.getStockItemsAsync()]);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Finished. ${result.items_restocked} item${
                    result.items_restocked === 1 ? '' : 's'
                } restocked.${
                    result.new_primary_list_id
                        ? ' Primary moved to next active list.'
                        : ''
                }`,
            });
            void router.push('/shopping-lists');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not finish.',
                caption: String(err),
            });
        } finally {
            finishing.value = false;
        }
    }

    // ── Detail-page extra actions ─────────────────────────────────────

    const otherActiveLists = computed(() =>
        store.summaries.filter(
            (s) => !s.is_archived && s.shopping_list_id !== listId.value
        )
    );

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
                caption: String(err),
            });
        }
    }

    async function onClearAll() {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Clear all items?',
                message: 'Every line on this list will be removed. The list stays.',
                ok: { label: 'Clear', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
                persistent: true,
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
                caption: String(err),
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
                        handler: () => router.push('/shopping-lists/templates'),
                    },
                ],
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save template.',
                caption: String(err),
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
                        label: s.name + (s.is_primary ? ' (primary)' : ''),
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
                caption: String(err),
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
                caption: String(err),
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
        background-color: rgba(0, 0, 0, 0.02);
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
        background: rgba(0, 0, 0, 0.03);
    }
    .bulk-bar-active {
        background: rgba(23, 176, 115, 0.12);
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
