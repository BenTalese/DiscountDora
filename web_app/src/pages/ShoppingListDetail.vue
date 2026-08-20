<template>
    <q-page padding>
        <!-- UX-v2 layout: main column + (desktop) lists rail. The rail and
             the mobile dropdown render the same server-ordered continuum
             (effective date ascending — past at top, future at bottom). -->
        <div class="row no-wrap q-col-gutter-md">
            <div class="col" style="min-width: 0">
                <!-- Toolbar (UX-v2 §8): page-consistent header with the
                     working actions VISIBLE, not behind an ellipsis. Only
                     rare/destructive actions live in "More". -->
                <PageToolbar title="Shopping lists">
                    <template #actions>
                        <BaseButton
                            variant="ghost"
                            :icon="ICONS.add"
                            label="Quick add"
                            :disable="!detail || detail.status === 'done'"
                            @click="onOpenQuickAdd"
                        >
                            <q-tooltip>Search every stock item and drop it onto this list</q-tooltip>
                        </BaseButton>
                        <BaseSegmented
                            v-model="groupBy"
                            dense
                            unelevated
                            class="sld-group-toggle"
                            :options="[
                                { label: 'No grouping', value: 'none' },
                                { label: 'Location', value: 'location' },
                                { label: 'Store', value: 'store' },
                            ]"
                        />
                        <BaseButton
                            variant="ghost"
                            :icon="ICONS.refresh"
                            label="Refresh deals"
                            :disable="!detail || detail.lines.length === 0"
                            @click="onRefreshDeals"
                        >
                            <q-tooltip>Re-check linked product offers</q-tooltip>
                        </BaseButton>
                        <BaseButton
                            v-if="detail && detail.lines.length > 0 && detail.status !== 'done'"
                            variant="ghost"
                            :icon="ICONS.checklist"
                            :label="bulkMode ? 'Done selecting' : 'Select'"
                            @click="bulkMode ? exitBulkMode() : enterBulkMode()"
                        >
                            <q-tooltip>Tick or untick a bunch at once</q-tooltip>
                        </BaseButton>
                        <BaseDropdown
                            flat
                            dense
                            :disable="!detail"
                            label="More"
                            :icon="ICONS.more_horiz"
                        >
                            <q-list dense style="min-width: 230px">
                                <q-item
                                    clickable
                                    v-close-popup
                                    :disable="!detail || detail.lines.length === 0"
                                    @click="onSaveAsTemplate"
                                >
                                    <q-item-section avatar><q-icon :name="ICONS.bookmark_add" /></q-item-section>
                                    <q-item-section>
                                        <q-item-label>Save as template</q-item-label>
                                        <q-item-label caption>Reusable snapshot of these items</q-item-label>
                                    </q-item-section>
                                </q-item>
                                <q-item
                                    clickable
                                    v-close-popup
                                    :disable="!detail || detail.lines.length === 0"
                                    @click="onPrint"
                                >
                                    <q-item-section avatar><q-icon :name="ICONS.print" /></q-item-section>
                                    <q-item-section>
                                        <q-item-label>Print / Save as PDF</q-item-label>
                                        <q-item-label caption>Opens a printable view</q-item-label>
                                    </q-item-section>
                                </q-item>
                                <q-item
                                    clickable
                                    v-close-popup
                                    :disable="untickedCount === 0 || otherActiveLists.length === 0"
                                    @click="onMoveUnticked"
                                >
                                    <q-item-section avatar><q-icon :name="ICONS.drive_file_move" /></q-item-section>
                                    <q-item-section>
                                        <q-item-label>Move unticked to another list</q-item-label>
                                        <q-item-label caption>
                                            {{
                                                otherActiveLists.length === 0
                                                    ? 'No other active lists'
                                                    : `${untickedCount} unticked item${untickedCount === 1 ? '' : 's'} can move`
                                            }}
                                        </q-item-label>
                                    </q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup @click="copyAll">
                                    <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                                    <q-item-section>Copy to new list</q-item-section>
                                </q-item>
                                <q-separator />
                                <q-item
                                    clickable
                                    v-close-popup
                                    :disable="!detail || detail.lines.length === 0"
                                    @click="onClearAll"
                                >
                                    <q-item-section avatar><q-icon :name="ICONS.playlist_remove" color="negative" /></q-item-section>
                                    <q-item-section class="text-negative">Clear all items</q-item-section>
                                </q-item>
                                <q-item
                                    clickable
                                    v-close-popup
                                    :disable="!currentSummary"
                                    @click="onDeleteCurrentList"
                                >
                                    <q-item-section avatar><q-icon :name="ICONS.delete" color="negative" /></q-item-section>
                                    <q-item-section class="text-negative">Delete list</q-item-section>
                                </q-item>
                            </q-list>
                        </BaseDropdown>
                        <!-- One primary action per lifecycle phase (UX-v2:
                             no Pause, no separate shop page — Start flips
                             the page itself into shopping state). -->
                        <BaseButton
                            v-if="detail && detail.status === 'draft'"
                            variant="primary"
                            :icon="ICONS.shopping_cart"
                            label="Start shopping"
                            :disable="detail.lines.length === 0"
                            :loading="togglingProgress"
                            @click="onStartShopping"
                        >
                            <q-tooltip>Tick items off as you grab them — prices you enter become the receipt</q-tooltip>
                        </BaseButton>
                        <BaseButton
                            v-else-if="detail && detail.status === 'shopping'"
                            variant="positive"
                            :icon="ICONS.check"
                            label="Finish & restock"
                            :loading="finishing"
                            @click="openFinishReview"
                        >
                            <q-tooltip>
                                Marks this shop as done: every ticked item moves
                                back to Stocked in your pantry, and the list is
                                archived. Untick anything you didn't actually buy
                                first.
                            </q-tooltip>
                        </BaseButton>
                        <BaseButton
                            v-if="detail && detail.status === 'done'"
                            variant="primary"
                            :icon="ICONS.inventory_2"
                            label="Put away"
                            @click="putAwayOpen = true"
                        >
                            <q-tooltip>
                                Ephemeral checklist grouped by kitchen location
                                so you don't forget a corner. Doesn't save.
                            </q-tooltip>
                        </BaseButton>
                        <BaseButton
                            v-if="detail && detail.status === 'done'"
                            variant="ghost"
                            :icon="ICONS.content_copy"
                            label="Copy to new list"
                            @click="copyAll"
                        />
                    </template>
                </PageToolbar>

                <!-- Mobile list switcher (UX-v2 §3.2): same date-ordered
                     continuum as the desktop rail, as a dropdown at the top
                     of the page. -->
                <BaseDropdown
                    class="lt-md full-width q-mb-md"
                    outline
                    :icon="ICONS.list_alt"
                    :label="detail?.display_name ?? 'Pick a list'"
                >
                    <q-list dense>
                        <q-item clickable v-close-popup @click="newListOpen = true">
                            <q-item-section avatar><q-icon :name="ICONS.add" color="primary" /></q-item-section>
                            <q-item-section class="text-primary text-weight-medium">New list</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-virtual-scroll
                            :items="railEntries"
                            :virtual-scroll-item-size="60"
                            style="max-height: 50vh"
                        >
                            <template #default="{ item: s }">
                                <ShoppingListRailItem
                                    :key="s.shopping_list_id"
                                    :summary="s"
                                    :active="s.shopping_list_id === listId"
                                    v-close-popup
                                    @select="switchToList(s.shopping_list_id)"
                                    @copy="(include) => copySummary(s, include)"
                                    @delete="deleteSummary(s)"
                                />
                            </template>
                        </q-virtual-scroll>
                        <q-separator />
                        <q-item clickable v-close-popup to="/shopping-lists/templates">
                            <q-item-section avatar><q-icon :name="ICONS.bookmarks" /></q-item-section>
                            <q-item-section>Manage templates…</q-item-section>
                        </q-item>
                    </q-list>
                </BaseDropdown>

                <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
                    <strong>Couldn't load this list.</strong>
                    {{ loadError }}
                    <template #action>
                        <BaseButton variant="ghost" label="Retry" @click="load" />
                    </template>
                </q-banner>

                <FadeTransition mode="out-in">
                <div v-if="loading && !detail" key="sld-loading">
                    <!-- Skeleton mirrors the info area + a few rows. `loading`
                         starts true so this branch (never the empty-state
                         fallback) is the first frame — kills the
                         flash-of-"no lists" (S6). -->
                    <div class="q-mb-lg">
                        <AppSkeleton type="line" width="240px" height="2rem" />
                        <AppSkeleton type="line" width="60%" height="1rem" class="q-mt-sm" />
                    </div>
                    <div v-for="n in 5" :key="n" class="row items-center q-gutter-sm q-py-sm">
                        <AppSkeleton type="circle" width="24px" height="24px" />
                        <AppSkeleton type="line" width="40%" height="1rem" />
                        <q-space />
                        <AppSkeleton type="line" width="64px" height="1rem" />
                    </div>
                </div>

                <div v-else-if="detail" key="sld-content">
                    <!-- Top info area (UX-v2 §4): big name + heading-scale
                         status badge, readable meta row, a real shop-day
                         button, and the resurrected completion doughnut with
                         the server-owned money totals beside it. -->
                    <div class="row items-start q-col-gutter-md q-mb-md">
                        <div class="col" style="min-width: 0">
                            <div class="row items-center q-gutter-x-sm no-wrap">
                                <template v-if="!editingName">
                                    <span class="text-h4 sld-title ellipsis">{{ detail.display_name }}</span>
                                    <q-badge
                                        :class="['sld-status-badge', { 'dora-bg-sunken dora-text-secondary': !statusBadgeColour }]"
                                        :color="statusBadgeColour ?? undefined"
                                        :label="statusBadgeLabel"
                                    />
                                    <BaseButton
                                        variant="icon"
                                        :icon="ICONS.edit"
                                        @click="startNameEdit"
                                    >
                                        <q-tooltip>Rename — leave blank to label by date</q-tooltip>
                                    </BaseButton>
                                </template>
                                <q-input
                                    v-else
                                    v-model="nameDraft"
                                    autofocus
                                    dense
                                    outlined
                                    clearable
                                    class="sld-name-input"
                                    :placeholder="dateFallbackName"
                                    hint="Leave blank to label this list by its shop / creation date"
                                    @blur="saveName"
                                    @keydown.enter.prevent="saveName"
                                    @keydown.esc.prevent="cancelName"
                                />
                            </div>
                            <div class="text-body2 dora-text-muted q-mt-xs">
                                {{ detail.lines.length }} item{{ detail.lines.length === 1 ? '' : 's' }} ·
                                {{ tickedCount }} ticked ·
                                Created {{ formatDate(detail.created_at) }}
                                <span v-if="detail.status === 'done' && detail.completed_at">
                                    · Completed {{ formatDate(detail.completed_at) }}
                                </span>
                            </div>
                            <!-- S14: a proper button, not a text link.
                                 Overdue/today fold into the button tone —
                                 one signal instead of button + banner. -->
                            <!-- ambiguous — dynamic color (positive/warning/undefined) with outline; no BaseButton variant covers all tones. Left as raw q-btn for review. -->
                            <q-btn
                                outline
                                no-caps
                                dense
                                :icon="ICONS.event"
                                :label="shopDayLabel"
                                :color="shopDayTone"
                                class="q-mt-sm q-px-sm"
                                @click="openPlannedDateEditor"
                            >
                                <!-- extended tooltip explains what the
                                     planned date drives beyond "next up". -->
                                <q-tooltip>
                                    Set the date you plan to shop this list. Helps
                                    Dora prioritise which list is your "active" one
                                    this week, and drives shop-day reminders if you
                                    have them on.
                                </q-tooltip>
                            </q-btn>
                        </div>
                        <div
                            v-if="detail.lines.length > 0"
                            class="col-auto row items-center q-gutter-md"
                        >
                            <q-circular-progress
                                show-value
                                :value="progressPct"
                                size="76px"
                                :thickness="0.18"
                                color="positive"
                                class="text-weight-medium"
                            >
                                {{ tickedCount }}/{{ detail.lines.length }}
                            </q-circular-progress>
                            <div class="text-body2">
                                <div>
                                    Remaining
                                    <span class="text-weight-medium">{{ formatMoney(remainingTotal) }}</span>
                                </div>
                                <div>
                                    Full list
                                    <span class="text-weight-medium">{{ formatMoney(fullTotal) }}</span>
                                </div>
                                <div v-if="savingsTotal > 0" class="text-positive">
                                    Savings {{ formatMoney(savingsTotal) }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Bulk-select action bar — only while selecting. The
                         entry point is the toolbar "Select" button. -->
                    <q-banner
                        v-if="bulkMode"
                        class="q-mb-sm bulk-bar bulk-bar-active"
                        dense
                        rounded
                    >
                        <template #avatar>
                            <q-icon :name="ICONS.checklist" />
                        </template>
                        {{ bulkSelection.size }} selected
                        <template #action>
                            <BaseButton variant="ghost" label="Select all" @click="selectAllLines" />
                            <BaseButton
                                variant="ghost"
                                :icon="ICONS.check_box"
                                label="Tick selected"
                                :disable="bulkSelection.size === 0"
                                :loading="bulkBusy"
                                @click="onBulkTick(true)"
                            />
                            <BaseButton
                                variant="ghost"
                                :icon="ICONS.check_box_outline_blank"
                                label="Untick"
                                :disable="bulkSelection.size === 0"
                                :loading="bulkBusy"
                                @click="onBulkTick(false)"
                            />
                            <BaseButton variant="ghost" label="Done" @click="exitBulkMode" />
                        </template>
                    </q-banner>

                    <!-- Budget-aware trim banner (money-gated + budget-set).
                         Fires when the projected active-list total exceeds the
                         user's period-remaining budget for this list's shop
                         date. Never mutates on load; every mutation is a user
                         tap. -->
                    <q-banner
                        v-if="trimBanner.visible"
                        class="q-mb-sm dora-bg-warning-soft"
                        rounded
                        dense
                    >
                        <template #avatar>
                            <q-icon :name="ICONS.savings" color="warning" />
                        </template>
                        <div v-if="trimBanner.state === 'applied'" class="text-body2">
                            Trimmed
                            <strong>{{ fmtMoney(trimBanner.savedApplied) }}</strong>
                            to fit —
                            <a
                                href="#deferred-by-budget"
                                class="text-primary"
                                @click.prevent="scrollToDeferred"
                            >
                                see deferred ({{ deferredLines.length }})
                            </a>
                        </div>
                        <div v-else class="text-body2">
                            <strong>
                                Projected {{ fmtMoney(trimBanner.projectedTotal) }} ·
                                budget remaining {{ fmtMoney(trimBanner.budgetTarget) }}
                            </strong>
                            — trim
                            <strong>{{ fmtMoney(trimBanner.overshoot) }}</strong>
                            to fit.
                            <div
                                v-if="trimBanner.state === 'previewed' && trimBanner.stillOver > 0"
                                class="text-caption text-negative q-mt-xs"
                            >
                                Trimmed everything safe. Still
                                {{ fmtMoney(trimBanner.stillOver) }} over —
                                this shop needs a hand from you.
                            </div>
                        </div>
                        <template #action>
                            <BaseButton
                                v-if="trimBanner.state === 'idle'"
                                variant="ghost"
                                label="Show what would be cut"
                                :loading="trimBanner.busy"
                                @click="previewTrim"
                            />
                            <BaseButton
                                v-if="trimBanner.state !== 'applied' && trimBanner.canApply"
                                :label="trimBanner.state === 'previewed' ? 'Apply trim' : 'Trim to fit'"
                                :loading="trimBanner.busy"
                                @click="applyTrim"
                            />
                            <BaseButton
                                v-if="trimBanner.state !== 'applied'"
                                variant="ghost"
                                label="Dismiss"
                                @click="dismissTrim"
                            />
                        </template>
                    </q-banner>

                    <!-- Preview: which lines would go, each with a "Keep" opt-out. -->
                    <q-card
                        v-if="trimBanner.state === 'previewed' && trimBanner.previewLines.length > 0"
                        flat
                        bordered
                        class="q-mb-sm"
                    >
                        <q-card-section class="q-py-sm">
                            <div class="text-caption dora-text-muted q-mb-xs">
                                Would trim {{ trimBanner.previewLines.length }} line{{ trimBanner.previewLines.length === 1 ? '' : 's' }}
                            </div>
                            <q-list dense>
                                <q-item
                                    v-for="p in trimBanner.previewLines"
                                    :key="p.line_id"
                                >
                                    <q-item-section>
                                        <q-item-label>{{ p.name }}</q-item-label>
                                        <q-item-label caption>
                                            <q-chip dense square color="warning-soft" text-color="warning" class="q-mr-xs">
                                                {{ p.reason_chip }}
                                            </q-chip>
                                            {{ fmtMoney(p.saved) }} saved
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <BaseButton
                                            variant="ghost"
                                            size="sm"
                                            label="Keep"
                                            @click="keepFromTrim(p.line_id)"
                                        />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-card-section>
                    </q-card>

                    <!-- FU-653 — Dora's suggestions, above the list and
                         visibly not part of it: chips you may tap to add,
                         never lines that appeared on their own. The whole
                         strip is dismissible for the session, because a
                         suggestion you've considered and rejected shouldn't
                         keep taking up the top of the page. Empty (and so
                         absent) unless the user opted the shopping surface in.
                    -->
                    <q-card
                        v-if="visibleSuggestions.length > 0"
                        flat
                        bordered
                        class="q-mb-md inferred-suggestions"
                    >
                        <q-card-section class="q-pb-xs row items-center no-wrap q-gutter-xs">
                            <q-icon :name="ICONS.inferred_hunch" size="18px" />
                            <span class="text-subtitle2">Dora thinks you may be out of…</span>
                            <q-space />
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.close"
                                aria-label="Hide suggestions"
                                @click="suggestionsDismissed = true"
                            >
                                <q-tooltip>Hide these for now</q-tooltip>
                            </BaseButton>
                        </q-card-section>
                        <q-card-section class="q-pt-none">
                            <div class="row q-gutter-xs">
                                <q-chip
                                    v-for="s in visibleSuggestions"
                                    :key="s.stock_item_id"
                                    clickable
                                    outline
                                    color="primary"
                                    :icon="ICONS.add"
                                    :disable="addingSuggestionId === s.stock_item_id"
                                    @click="onAddSuggestion(s)"
                                >
                                    {{ s.name }}
                                    <q-tooltip v-if="s.reason" max-width="280px">
                                        {{ s.reason }} Nothing has been added — tap to put it
                                        on this list.
                                    </q-tooltip>
                                </q-chip>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- Lines -->
                    <q-card v-if="detail.lines.length === 0" flat bordered>
                        <q-card-section class="text-center dora-text-muted">
                            No items yet. Use <strong>Quick add</strong> in the toolbar, or
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
                                    v-for="line in nestedLinesFor(group)"
                                    :key="line.line_id"
                                    :class="{
                                        'shopping-line-ticked': line.is_ticked,
                                        'shopping-line-focused': focusedLineId === line.line_id,
                                        'shopping-line-nested': isNestedChild(line),
                                        'shopping-line-product-only': isProductOnly(line),
                                        ...lineDnd.bind(line).rowClass,
                                    }"
                                    v-bind="{
                                        ...lineDnd.bind(line).handleProps,
                                        ...lineDnd.bind(line).rowProps,
                                    }"
                                >
                                    <!-- Decorative grip — whole-row mode, the
                                         row itself is the draggable element;
                                         this icon section just signals "you
                                         can grab here" via the shared handle
                                         class (grab cursor + sunken hover). -->
                                    <q-item-section
                                        v-if="canReorder"
                                        side
                                        top
                                        class="dora-dnd-handle"
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
                                        <!-- Bigger tap target mid-shop (M3).
                                             DR-15 / D-010: `dora-press` answers
                                             the tap on the tick itself — the
                                             most-repeated gesture on this page
                                             — while the ticked row's fade is
                                             transitioned below rather than
                                             snapping. -->
                                        <q-checkbox
                                            class="dora-press"
                                            :model-value="line.is_ticked"
                                            :disable="detail.status === 'done'"
                                            :size="detail.status === 'shopping' ? 'lg' : undefined"
                                            @update:model-value="onToggleTicked(line.line_id, $event)"
                                        />
                                    </q-item-section>

                                    <q-item-section>
                                        <!-- UX-v2 §6: plain name-link + level
                                             dot — StockItemChip is retired. -->
                                        <div
                                            class="row items-center q-gutter-x-sm no-wrap"
                                            :class="{
                                                'shopping-line-ticked-content': line.is_ticked,
                                            }"
                                        >
                                            <template v-if="!isNestedChild(line) && line.stock_item_id">
                                                <router-link
                                                    :to="`/stock/${line.stock_item_id}`"
                                                    class="shopping-line-name text-primary"
                                                    :class="{ 'text-strike': line.is_ticked }"
                                                >
                                                    {{ line.stock_item_name }}
                                                </router-link>
                                                <!-- in-shop "should I buy?" nudge.
                                                     Silent on low-confidence items so the
                                                     line list stays legible; when the pantry
                                                     says the item is stocked and the
                                                     user has a history of wasting it, the
                                                     'skip' verdict gives them a second chance
                                                     to remove it before checkout. Emits the
                                                     action up so the existing cart/level
                                                     controls own the mutation. -->
                                                <BuyVerdictBadgeInline
                                                    :stock-item-id="line.stock_item_id"
                                                    @action="onLineVerdictAction(line, $event)"
                                                />
                                            </template>
                                            <q-chip
                                                v-else-if="isNestedChild(line)"
                                                dense
                                                size="sm"
                                                :icon="ICONS.shopping_bag"
                                                class="dora-bg-sunken"
                                            >
                                                {{ line.stock_item_name }}
                                                <q-tooltip>Nested product</q-tooltip>
                                            </q-chip>
                                            <q-chip
                                                v-else
                                                dense
                                                :icon="isProductOnly(line) ? ICONS.shopping_bag : undefined"
                                                :class="isProductOnly(line) ? 'dora-bg-sunken' : 'dora-text-muted'"
                                            >
                                                {{ line.stock_item_name }}
                                                <q-tooltip v-if="isProductOnly(line)">
                                                    Product only — no linked stock item on this list
                                                </q-tooltip>
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
                                            <!-- C-cross Chunk 4 — zone-default + tooltip. -->
                                            <span
                                                v-if="line.stock_location_breadcrumb.length > 0"
                                                class="q-mr-sm"
                                            >
                                                <q-icon :name="ICONS.place" size="14px" />
                                                {{ formatLocation(line.stock_location_breadcrumb, 'zone') }}
                                                <q-tooltip v-if="locationHasDetail(line.stock_location_breadcrumb)">
                                                    {{ formatLocation(line.stock_location_breadcrumb, 'full') }}
                                                </q-tooltip>
                                            </span>
                                            <span v-if="line.offers.length > 0">
                                                {{ line.offers.length }} store offer{{
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
                                                    name="storefront"
                                                    size="14px"
                                                    class="q-mr-xs"
                                                />
                                                {{ offer.store_name }} ·
                                                {{ offer.price_now != null ? formatMoney(offer.price_now) : '—' }}
                                                <span
                                                    v-if="offerSavings(offer) > 0"
                                                    class="q-ml-xs offer-savings"
                                                    :class="
                                                        isChosen(line, offer.product_id)
                                                            ? 'text-amber-2'
                                                            : 'text-positive'
                                                    "
                                                >
                                                    save {{ formatMoney(offerSavings(offer)) }}
                                                </span>
                                                <q-tooltip>
                                                    {{ offer.brand ? `${offer.brand} — ` : '' }}{{ offer.name }}
                                                    <span v-if="offer.size"> ({{ offer.size }})</span>
                                                    <span v-if="offer.price_was != null && offer.price_now != null">
                                                        · RRP {{ formatMoney(offer.price_was) }}
                                                    </span>
                                                </q-tooltip>
                                            </q-chip>
                                        </div>
                                        <!-- PreferredBuy hint: pick one of
                                             the item's "what I buy" labels as a
                                             reminder for this line. -->
                                        <div
                                            v-if="line.preferred_buys && line.preferred_buys.length"
                                            class="row items-center q-mt-xs"
                                        >
                                            <BaseDropdown
                                                flat
                                                dense
                                                size="sm"
                                                :icon="ICONS.lightbulb"
                                                :label="buyHintLabel(line) || 'Add a buy hint'"
                                                :disable="detail.status === 'done'"
                                            >
                                                <q-list dense>
                                                    <q-item
                                                        v-for="pb in line.preferred_buys"
                                                        :key="pb.preferred_buy_id"
                                                        v-close-popup
                                                        clickable
                                                        :active="line.preferred_buy_id === pb.preferred_buy_id"
                                                        @click="onPickHint(line.line_id, pb.preferred_buy_id)"
                                                    >
                                                        <q-item-section>{{ pb.label }}</q-item-section>
                                                    </q-item>
                                                    <template v-if="line.preferred_buy_id">
                                                        <q-separator />
                                                        <q-item
                                                            v-close-popup
                                                            clickable
                                                            @click="onPickHint(line.line_id, null)"
                                                        >
                                                            <q-item-section class="dora-text-muted">
                                                                Clear hint
                                                            </q-item-section>
                                                        </q-item>
                                                    </template>
                                                </q-list>
                                            </BaseDropdown>
                                        </div>
                                    </q-item-section>

                                    <q-item-section side style="min-width: 150px">
                                        <div class="row items-center q-gutter-xs no-wrap">
                                            <BaseButton
                                                variant="icon"
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
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.add"
                                                :disable="detail.status === 'done'"
                                                @click="onAdjustQuantity(line, 1)"
                                            />
                                        </div>
                                        <!-- S17: a real outlined button with a
                                             caret so it reads as clickable. -->
                                        <!-- ambiguous — outline with conditional primary/undefined color; left as raw q-btn for review. -->
                                        <q-btn
                                            outline
                                            dense
                                            no-caps
                                            size="sm"
                                            class="sld-price-btn q-mt-xs"
                                            :icon-right="ICONS.expand_more"
                                            :disable="detail.status === 'done'"
                                            :color="line.actual_unit_price != null ? 'primary' : undefined"
                                            :label="
                                                priceForLine(line) > 0
                                                    ? formatMoney(priceForLine(line))
                                                    : 'Set price'
                                            "
                                        >
                                            <q-tooltip v-if="detail.status !== 'done'">
                                                {{
                                                    line.actual_unit_price != null
                                                        ? `You paid ${formatMoney(line.actual_unit_price)} per unit${line.purchased_store_name ? ` at ${line.purchased_store_name}` : ''}`
                                                        : 'Enter the price you actually paid'
                                                }}
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
                                                            :prefix="currencySymbol"
                                                            @keydown.enter.prevent="savePriceEditor(line)"
                                                        />
                                                        <!-- D3 — where the prefilled
                                                             number came from, so the user
                                                             knows it's a starting point. -->
                                                        <div
                                                            v-if="line.actual_unit_price == null && line.prefill_source_label"
                                                            class="text-caption dora-text-muted"
                                                        >
                                                            <q-icon :name="ICONS.info" size="14px" class="q-mr-xs" />
                                                            Prefilled {{ line.prefill_source_label }}
                                                        </div>
                                                        <q-select
                                                            v-if="storeOptionsFor(line).length > 0"
                                                            v-model="priceEditorDraft.store_id"
                                                            :options="storeOptionsFor(line)"
                                                            dense
                                                            outlined
                                                            emit-value
                                                            map-options
                                                            clearable
                                                            label="Bought from (optional)"
                                                        />
                                                    </q-card-section>
                                                    <q-card-actions align="right">
                                                        <BaseButton
                                                            v-if="line.actual_unit_price != null"
                                                            variant="danger-ghost"
                                                            label="Clear"
                                                            v-close-popup
                                                            @click="clearPriceOverride(line)"
                                                        />
                                                        <BaseButton
                                                            variant="ghost"
                                                            label="Cancel"
                                                            v-close-popup
                                                        />
                                                        <BaseButton
                                                            variant="primary"
                                                            label="Save"
                                                            v-close-popup
                                                            @click="savePriceEditor(line)"
                                                        />
                                                    </q-card-actions>
                                                </q-card>
                                            </q-popup-proxy>
                                        </q-btn>
                                        <div
                                            v-if="line.purchased_store_name"
                                            class="text-caption dora-text-muted text-right"
                                        >
                                            {{ line.purchased_store_name }}
                                        </div>
                                        <!-- E2 — show where an un-entered price would
                                             prefill from, so the hint is visible before
                                             opening the editor (money surfaces only). -->
                                        <div
                                            v-else-if="
                                                moneyEnabled
                                                    && detail.status !== 'done'
                                                    && line.actual_unit_price == null
                                                    && line.prefill_source_label
                                            "
                                            class="text-caption dora-text-muted text-right"
                                        >
                                            {{ line.prefill_source_label }}
                                        </div>
                                    </q-item-section>

                                    <!-- S12: direct row actions, no kebab.
                                         "Move to another list" was axed
                                         (§12 Q2) — remove + re-add covers it. -->
                                    <q-item-section side>
                                        <div class="column items-center q-gutter-xs">
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.swap_horiz"
                                                :disable="detail.status === 'done' || !line.stock_item_id || !line.has_substitutes"
                                                @click="onSwapSubstitute(line)"
                                            >
                                                <q-tooltip>
                                                    {{ line.has_substitutes
                                                        ? 'Swap for a substitute item'
                                                        : 'No substitutes recorded for this item' }}
                                                </q-tooltip>
                                            </BaseButton>
                                            <BaseButton
                                                variant="danger-icon"
                                                size="sm"
                                                :icon="ICONS.delete_outline"
                                                :disable="detail.status === 'done'"
                                                @click="onRemoveLine(line.line_id)"
                                            >
                                                <q-tooltip>Remove from list</q-tooltip>
                                            </BaseButton>
                                        </div>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </div>
                    </template>

                    <!-- Deferred-to-fit-budget section
                         (PROPOSAL_BUDGET_AWARE_LISTS §6.3). Renders when the
                         list has any lines with `deferred_by_budget=true`.
                         Collapsible; each row shows the frozen reason chip
                         and a one-tap "Add back" that flips the flag off
                         via PATCH /lines/<id>. -->
                    <q-expansion-item
                        v-if="deferredLines.length > 0"
                        id="deferred-by-budget"
                        :label="`Deferred to fit budget (${deferredLines.length})`"
                        :caption="`${fmtMoney(deferredTotal)} saved`"
                        default-opened
                        class="q-mt-md dora-bg-sunken rounded-borders"
                    >
                        <q-list dense>
                            <q-item
                                v-for="line in deferredLines"
                                :key="line.line_id"
                            >
                                <q-item-section>
                                    <q-item-label>{{ line.stock_item_name }}</q-item-label>
                                    <q-item-label caption>
                                        <q-chip
                                            v-if="line.deferred_reason"
                                            dense
                                            square
                                            color="warning-soft"
                                            text-color="warning"
                                            class="q-mr-xs"
                                        >
                                            {{ line.deferred_reason }}
                                        </q-chip>
                                        {{ fmtMoney(priceOfLine(line)) }}
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <BaseButton
                                        variant="ghost"
                                        size="sm"
                                        label="Add back"
                                        :loading="addingBackLineIds.has(line.line_id)"
                                        @click="addLineBackToActive(line.line_id)"
                                    />
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-expansion-item>

                    <!-- receipt-photo record-keeping. Visible only
                         once the list is being shopped or finished; pure
                         record-keeping (no OCR, no parsing). Multi-photo;
                         tap to zoom, trash to remove. Source-pick UX
                         (Take photo vs Choose image) is delegated to the
                         shared ImageSourcePicker primitive (R-0NN). -->
                    <div
                        v-if="attachmentSectionVisible"
                        class="sld-receipts q-mt-lg"
                    >
                        <div class="row items-center q-mb-sm">
                            <div class="text-subtitle2 text-weight-medium">
                                Receipts
                            </div>
                            <q-space />
                            <ImageSourcePicker
                                variant="ghost"
                                take-photo-label="Take photo"
                                pick-label="Choose receipt"
                                :loading="attachmentUploading"
                                @pick="onAttachmentPicked"
                                @error="onAttachmentError"
                            />
                        </div>
                        <div
                            v-if="(detail.attachments?.length ?? 0) === 0"
                            class="text-caption dora-text-muted"
                        >
                            No receipts yet. Snap one (or pick one you've already taken) — no OCR, just kept on the list.
                        </div>
                        <div v-else class="sld-receipt-strip row q-gutter-sm">
                            <div
                                v-for="att in detail.attachments"
                                :key="att.attachment_id"
                                class="sld-receipt-thumb"
                            >
                                <img
                                    :src="attachmentSrc(att.attachment_id)"
                                    alt="Receipt"
                                    @click="attachmentZoomId = att.attachment_id"
                                />
                                <BaseButton
                                    variant="ghost"
                                    :icon="ICONS.delete"
                                    class="sld-receipt-delete"
                                    dense
                                    @click="onDeleteAttachment(att.attachment_id)"
                                >
                                    <q-tooltip>Remove receipt</q-tooltip>
                                </BaseButton>
                            </div>
                        </div>
                    </div>

                    <!-- Full-screen receipt viewer (lightbox). Tap thumb to
                         open; tap the dialog backdrop or hit Esc to close. -->
                    <BaseDialog
                        :model-value="attachmentZoomId !== null"
                        max-width="900px"
                        @update:model-value="(v) => { if (!v) attachmentZoomId = null }"
                    >
                        <img
                            v-if="attachmentZoomId"
                            :src="attachmentSrc(attachmentZoomId)"
                            alt="Receipt"
                            class="sld-receipt-zoom"
                        />
                    </BaseDialog>

                    <!-- Mid-shop sticky footer (M10–M12): live progress +
                         remaining spend + the finish CTA, always in reach. -->
                    <div
                        v-if="detail.status === 'shopping'"
                        class="sld-shop-footer row items-center q-gutter-md q-pa-sm"
                    >
                        <q-circular-progress
                            :value="progressPct"
                            size="40px"
                            :thickness="0.22"
                            color="positive"
                        />
                        <div>
                            <div class="text-body2 text-weight-medium">
                                Picked {{ tickedCount }} of {{ detail.lines.length }}
                            </div>
                            <div class="text-caption dora-text-muted">
                                Remaining {{ formatMoney(remainingTotal) }}
                            </div>
                        </div>
                        <q-space />
                        <BaseButton
                            variant="positive"
                            :icon="ICONS.check"
                            :label="untickedCount > 0 ? 'Finish early & restock' : 'Finish & restock'"
                            :loading="finishing"
                            @click="openFinishReview"
                        />
                    </div>
                </div>

                <!-- Fallback so the content area is never blank — e.g. when
                     load() fails (loadError banner above carries the message)
                     or the listId in the URL doesn't resolve. -->
                <div v-else key="sld-empty" class="text-center dora-text-muted q-py-xl">
                    <q-icon :name="ICONS.shopping_cart" size="60px" class="q-mb-sm" />
                    <div v-if="loadError" class="text-h6">Couldn't open this list.</div>
                    <div v-else class="text-h6">This list isn't available.</div>
                    <div class="q-mt-md">
                        Pick another list from the panel, or create a new one.
                    </div>
                    <div class="q-mt-md">
                        <BaseButton
                            variant="primary"
                            :icon="ICONS.add"
                            label="New list"
                            @click="newListOpen = true"
                        />
                    </div>
                </div>
                </FadeTransition>
            </div>

            <!-- Desktop lists rail (UX-v2 §3.1): every list, active and done,
                 one continuum ordered by effective date (server-owned order),
                 virtualised because it accretes forever, auto-scrolled to the
                 selection. -->
            <div class="col-auto gt-sm">
                <div class="sld-rail column">
                    <BaseButton
                        variant="ghost"
                        :icon="ICONS.add"
                        label="New list"
                        class="full-width q-mb-sm"
                        @click="newListOpen = true"
                    />
                    <q-virtual-scroll
                        ref="railScrollRef"
                        :items="railEntries"
                        :virtual-scroll-item-size="60"
                        class="col sld-rail-scroll"
                    >
                        <template #default="{ item: s }">
                            <ShoppingListRailItem
                                :key="s.shopping_list_id"
                                :summary="s"
                                :active="s.shopping_list_id === listId"
                                @select="switchToList(s.shopping_list_id)"
                                @copy="(include) => copySummary(s, include)"
                                @delete="deleteSummary(s)"
                            />
                        </template>
                    </q-virtual-scroll>
                    <div class="q-mt-sm text-center">
                        <router-link
                            to="/shopping-lists/templates"
                            class="text-primary text-caption"
                        >
                            Manage templates…
                        </router-link>
                    </div>
                </div>
            </div>
        </div>

        <!-- the New-list dialog lives on the detail page now
             that Detail is the canonical surface. The router landing page
             also mounts this dialog for the no-lists empty state. -->
        <NewListDialog
            v-model="newListOpen"
            @created="onListCreated"
        />

        <PutAwayDialog
            v-if="detail && detail.status === 'done'"
            v-model="putAwayOpen"
            :lines="detail.lines"
            @assigned="onPutAwayAssigned"
        />

        <!-- planned-shop-date editor. Sets/changes/clears
             the planned day for this list. Sort + next-up + button tone
             all read from it. -->
        <BaseDialog v-model="plannedDateOpen" title="Plan this shop for" closable card-style="min-width: 280px">
            <q-card-section>
                <div class="text-caption dora-text-muted">
                    Sets which list opens first on shopping day, and labels
                    self-named lists with the date.
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
            <template #actions>
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
            </template>
        </BaseDialog>

        <!-- UX-v2 M12 — restock review. One-click "Restock & finish" with
             every ticked item listed and individually adjustable (default
             Stocked). Replaces the old text-only confirm dialog. -->
        <BaseDialog v-model="finishReviewOpen" title="Finish & restock" closable card-style="min-width: 320px; max-width: 480px">
            <q-card-section>
                <div class="text-body2 dora-text-muted">
                    {{
                        finishEntries.length === 0
                            ? 'No items are ticked — the list is marked done and nothing is restocked.'
                            : 'These ticked items will be restocked:'
                    }}
                </div>
            </q-card-section>
            <q-card-section v-if="finishEntries.length > 0" class="q-pt-none scroll" style="max-height: 50vh">
                <q-list separator dense>
                    <q-item v-for="entry in finishEntries" :key="entry.line_id">
                        <q-item-section>
                            <q-item-label>{{ entry.name }}</q-item-label>
                        </q-item-section>
                        <q-item-section v-if="!entry.stock_item_id" side>
                            <span class="text-caption dora-text-muted">
                                Not stock-tracked
                            </span>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
            <q-card-section v-if="untickedCount > 0" class="q-pt-none">
                <div class="text-caption dora-text-muted">
                    {{ untickedCount }} unticked item{{ untickedCount === 1 ? '' : 's' }}
                    stay{{ untickedCount === 1 ? 's' : '' }} on the list — copy or move
                    them later if they're still wanted.
                </div>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="positive"
                    :icon="ICONS.check"
                    label="Restock & finish"
                    :loading="finishing"
                    @click="confirmFinish"
                />
            </template>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDropdown from 'src/components/BaseDropdown.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import NewListDialog from 'src/components/dialogs/NewListDialog.vue';
    import PutAwayDialog from 'src/components/dialogs/PutAwayDialog.vue';
    import PageToolbar from 'src/components/PageToolbar.vue';
    import ShoppingListRailItem from 'src/components/shoppingList/ShoppingListRailItem.vue';
    import BuyVerdictBadgeInline from 'src/components/stock/BuyVerdictBadgeInline.vue';
    import BuyVerdictApiService from 'src/services/api/buyVerdictApiService';
    import {
        invalidateBuyVerdict, primeBuyVerdicts,
    } from 'src/composables/useBuyVerdict';
    import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';
    import { useBuyVerdictActions } from 'src/composables/useBuyVerdictActions';
    import { useQuasar, type QVirtualScroll } from 'quasar';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useMoney, formatMoney } from 'src/composables/useMoney';
    const { currencySymbol } = useMoney();
    import { useDragDropList } from 'src/composables/useDragDropList';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { useShoppingListExport } from 'src/composables/useShoppingListExport';
    import { useShortcut } from 'src/composables/useShortcut';
    import { tryWithQueue } from 'src/composables/useOfflineQueue';
    import { useWakeLock } from 'src/composables/useWakeLock';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import {
        chosenOfferFor,
        priceOfLine,
        type InferredSuggestion,
        type LineProductOffer,
        type ShoppingListDetail,
        type ShoppingListLine,
        type ShoppingListSummary
    } from 'src/models/shoppingList';
    import type { Substitute } from 'src/models/stockItemDetail';
    import ShoppingListApiService, {
        shoppingListAttachmentUrl,
        type TrimToBudgetResult,
    } from 'src/services/api/shoppingListApiService';
    import ImageSourcePicker from 'src/components/ImageSourcePicker.vue';
    import type { ProcessedImage } from 'src/services/files/imageService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useProductStore } from 'src/stores/productStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useListState } from 'src/composables/useListState';
    import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError, toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { formatLocation, locationHasDetail } from 'src/helpers/locationDisplay';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const api = new ShoppingListApiService();
    const templateApi = new ShoppingListTemplateApiService();
    const stockItemApi = new StockItemApiService();
    const store = useShoppingListStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const productStore = useProductStore();
    const { moneyEnabled } = useMoneyEnabled();
    // Per-user display opt-out (D-12). Gates the bulk verdict prefetch below;
    // `BuyVerdictBadgeInline` checks it again for the render.
    const { buyVerdictEnabled } = useBuyVerdictEnabled();
    const { openQuickAdd, isOpen: quickAddOpen } = useQuickAdd();

    const listId = computed(() => String(route.params.id ?? ''));
    const detail = ref<ShoppingListDetail | null>(null);

    // shop-mode wake lock. Holds the screen on while the list is
    // in 'shopping' status so the phone doesn't blank between aisles. The
    // computed reads `detail.value?.status` so entering / leaving shop
    // mode toggles the lock without any explicit acquire/release call.
    const shopModeActive = computed(() => detail.value?.status === 'shopping');
    useWakeLock(shopModeActive);
    // Starts true: the first painted frame must be the skeleton, never the
    // "list isn't available" fallback (the S6 flash) — onMounted's load()
    // hasn't had a chance to set it yet on that first frame.
    const loading = ref(true);
    const loadError = ref<string | null>(null);
    const editingName = ref(false);
    const nameDraft = ref('');

    // Group lines by nothing, by stock location or by chosen merchant.
    // UX-v2 M2 revision: grouping is a *manual* view preference only —
    // shopping does NOT default to location (stock location is where the
    // item lives at home, not where it sits on a shelf).
    //
    // FU-354 — wrapped in `useListState` so the picked grouping survives
    // navigate-away-and-back within the session (A8 §3 nav-state
    // policy). Full reload / sign-out (via `clearAllListState` from
    // FU-355) still resets to `'none'`. Single scope, not per-list — the
    // groupBy is a *view* preference the user re-uses across lists; a
    // per-list scope would silently reset the moment they open a new
    // list, defeating the point.
    type GroupByMode = 'none' | 'location' | 'store';
    const { groupBy } = useListState('shopping-list-detail', () => ({
        groupBy: ref<GroupByMode>('none'),
    }));

    // ── Lifecycle: start / finish ────────────────────────────────────
    const togglingProgress = ref(false);

    async function onStartShopping() {
        togglingProgress.value = true;
        try {
            await api.startShoppingAsync(listId.value);
            // UX-v2: no separate shop page — the page itself flips into the
            // shopping state (sticky footer, big ticks, Finish CTA).
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Shopping started — tick items off as you grab them.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not start shopping.',
                caption: toastCaption(err),
            });
        } finally {
            togglingProgress.value = false;
        }
    }

    // ── Finish & restock ────────────────────────────────────────────
    // The dialog previously let you pick a per-item stock level (in case
    // you'd only partly topped something up). With levels simplified, every
    // ticked item just restocks to Stocked — the server default when no
    // overrides are sent.
    const finishReviewOpen = ref(false);
    const finishing = ref(false);
    type FinishEntry = {
        line_id: string;
        stock_item_id: string | null;
        name: string;
    };
    const finishEntries = ref<FinishEntry[]>([]);

    function openFinishReview() {
        if (!detail.value) return;
        const seen = new Set<string>();
        finishEntries.value = detail.value.lines
            .filter((l) => l.is_ticked)
            .filter((l) => {
                // One row per stock item — duplicate anchors (nested
                // product lines) collapse into the parent's entry.
                if (!l.stock_item_id) return true;
                if (seen.has(l.stock_item_id)) return false;
                seen.add(l.stock_item_id);
                return true;
            })
            .map((l) => ({
                line_id: l.line_id,
                stock_item_id: l.stock_item_id,
                name: l.stock_item_name,
            }));
        finishReviewOpen.value = true;
    }

    async function confirmFinish() {
        finishing.value = true;
        try {
            const result = await api.finishAsync(listId.value);
            finishReviewOpen.value = false;
            await Promise.all([
                refreshAll(),
                stockItemStore.getStockItemsAsync(),
            ]);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Shopping finished — ${result.items_restocked} item${
                    result.items_restocked === 1 ? '' : 's'
                } restocked.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not finish shopping.',
                caption: toastCaption(err),
            });
        } finally {
            finishing.value = false;
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
                caption: toastCaption(err),
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Drag-to-reorder ───────────────────────────────────────────────
    // Reorder is only available when the list isn't done AND isn't
    // mid-shop AND there's no grouping active (reordering *within* a
    // group would be confusing — disable the affordance rather than try
    // to be smart).
    const canReorder = computed(() =>
        !!detail.value
            && detail.value.status !== 'done'
            && detail.value.status !== 'shopping'
            && groupBy.value === 'none'
            && !bulkMode.value
    );

    // R-022 — whole-row DnD via `useDragDropList`. `canDragStart` is gated
    // on `canReorder` (list not done/shopping, no grouping, not in bulk
    // mode), so the `draggable` attribute reactively turns off the
    // browser's drag affordance when reorder isn't allowed. The drop
    // effect mirrors the historical insert-at-target's-slot pattern
    // (fixed the off-by-one in P6-01 Chunk 6 / feedback L414).
    const lineDnd = useDragDropList<ShoppingListLine>({
        mime: 'application/x-dora-shopping-line',
        getId: (line) => line.line_id,
        canDragStart: () => canReorder.value,
        onDrop: ({ id: draggedId }, { id: targetLineId }) => {
            if (!detail.value) return;
            const lines = detail.value.lines;
            const ids = lines.map((l) => l.line_id);
            const fromIdx = ids.indexOf(draggedId);
            const toIdx = ids.indexOf(targetLineId);
            if (fromIdx < 0 || toIdx < 0) return;
            ids.splice(fromIdx, 1);
            ids.splice(toIdx, 0, draggedId);

            // Optimistic local update so the UI reflects the move
            // immediately; if the server call fails we reload.
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

            void (async () => {
                try {
                    await api.reorderLinesAsync(listId.value, ids);
                } catch (err) {
                    await load();
                    $q.notify({
                        type: 'negative',
                        position: 'bottom-right',
                        message: 'Could not reorder.',
                        caption: toastCaption(err),
                    });
                }
            })();
        },
    });

    // ── Line grouping ────────────────────────────────────────────────
    // One flat list, or one bucket per stock location, or one bucket per
    // chosen merchant. "No location" / "No merchant" lines drop into a
    // labelled bucket at the end so they don't vanish.
    type LineGroup = { key: string; label: string | null; lines: ShoppingListLine[] };

    function locationKeyFor(line: ShoppingListLine): string {
        if (line.stock_location_breadcrumb.length === 0) return '__no_location__';
        return line.stock_location_breadcrumb.join(' › ');
    }

    // deferred-by-budget lines render under their own collapsible
    // section, not the active list. Server-side totals already skip them.
    const baseLines = computed(() =>
        (detail.value?.lines ?? []).filter((l) => !l.deferred_by_budget),
    );
    const deferredLines = computed(() =>
        (detail.value?.lines ?? []).filter((l) => l.deferred_by_budget),
    );
    const deferredTotal = computed(() =>
        deferredLines.value.reduce((sum, l) => sum + priceOfLine(l), 0),
    );
    const addingBackLineIds = ref<Set<string>>(new Set());

    async function addLineBackToActive(lineId: string): Promise<void> {
        if (addingBackLineIds.value.has(lineId)) return;
        addingBackLineIds.value = new Set(addingBackLineIds.value).add(lineId);
        try {
            await api.updateLineAsync(listId.value, lineId, {
                deferred_by_budget: false,
            });
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                message: describeApiError(err) ?? 'Could not add that line back.',
            });
        } finally {
            const next = new Set(addingBackLineIds.value);
            next.delete(lineId);
            addingBackLineIds.value = next;
        }
    }

    // ── FU-448 trim-to-budget banner (PROPOSAL_BUDGET_AWARE_LISTS §6) ──

    type TrimState = 'idle' | 'previewed' | 'applied';
    type TrimPreviewLine = {
        line_id: string;
        name: string;
        reason_chip: string;
        saved: number;
    };
    const trimState = reactive({
        state: 'idle' as TrimState,
        busy: false,
        loaded: false,                    // true once we've fetched the initial preview
        projectedTotal: 0,
        budgetTarget: 0,
        overshoot: 0,
        stillOver: 0,
        savedApplied: 0,
        previewLines: [] as TrimPreviewLine[],
        excluded: new Set<string>(),
        dismissed: false,
    });

    function fmtMoney(v: number | null | undefined): string {
        return formatMoney(v ?? 0);
    }

    const trimBanner = computed(() => {
        // Money features off, no budget set, list not auto-generated,
        // dismissed, or nothing to trim → banner stays hidden.
        const anyDeferredAlready = deferredLines.value.length > 0;
        const applied = trimState.state === 'applied' && anyDeferredAlready;
        const hasOvershoot = trimState.overshoot > 0;
        return {
            visible: moneyEnabled.value
                && !trimState.dismissed
                && trimState.loaded
                && (hasOvershoot || applied),
            state: trimState.state,
            busy: trimState.busy,
            projectedTotal: trimState.projectedTotal,
            budgetTarget: trimState.budgetTarget,
            overshoot: trimState.overshoot,
            stillOver: trimState.stillOver,
            savedApplied: trimState.savedApplied,
            previewLines: trimState.previewLines,
            canApply: trimState.overshoot > 0 && trimState.previewLines.length > 0,
        };
    });

    async function refreshTrimStatus(): Promise<void> {
        // Only fetch when money features are on and the list has active lines
        // — the endpoint gracefully returns overshoot=0 when there's no budget,
        // but skipping the call altogether keeps a fresh install quiet.
        if (!moneyEnabled.value || !detail.value) return;
        if (baseLines.value.length === 0) {
            trimState.loaded = true;
            trimState.overshoot = 0;
            return;
        }
        try {
            const result = await api.trimToBudgetAsync(listId.value, {
                mode: 'preview',
                exclude_line_ids: [...trimState.excluded],
            });
            applyTrimResult(result);
        } catch {
            // Non-fatal; the banner just stays hidden.
            trimState.loaded = true;
        }
    }

    function applyTrimResult(result: TrimToBudgetResult): void {
        trimState.loaded = true;
        trimState.projectedTotal = result.projected_total;
        trimState.budgetTarget = result.budget_target ?? 0;
        trimState.overshoot = result.overshoot;
        trimState.stillOver = result.still_over;
        // Freeze display names + saved amounts so the preview card doesn't
        // desync from the server (the SPA has all the info it needs).
        const nameByLine = new Map<string, string>();
        for (const l of detail.value?.lines ?? []) nameByLine.set(l.line_id, l.stock_item_name);
        trimState.previewLines = result.trimmed.map((t) => ({
            line_id: t.line_id,
            name: nameByLine.get(t.line_id) ?? 'Item',
            reason_chip: t.reason_chip,
            saved: t.saved,
        }));
    }

    async function previewTrim(): Promise<void> {
        if (trimState.busy) return;
        trimState.busy = true;
        try {
            const result = await api.trimToBudgetAsync(listId.value, {
                mode: 'preview',
                exclude_line_ids: [...trimState.excluded],
            });
            applyTrimResult(result);
            trimState.state = 'previewed';
        } catch (err) {
            $q.notify({
                type: 'negative',
                message: describeApiError(err) ?? 'Could not preview the trim.',
            });
        } finally {
            trimState.busy = false;
        }
    }

    async function applyTrim(): Promise<void> {
        if (trimState.busy) return;
        trimState.busy = true;
        try {
            const result = await api.trimToBudgetAsync(listId.value, {
                mode: 'apply',
                exclude_line_ids: [...trimState.excluded],
            });
            trimState.savedApplied = result.trimmed.reduce((s, t) => s + t.saved, 0);
            trimState.state = 'applied';
            trimState.previewLines = [];
            await load();
            // After apply the list has fewer active lines and totals shift;
            // re-check whether we still overshoot so the banner updates
            // ("still over" fallback vs. done).
            await refreshTrimStatus();
        } catch (err) {
            $q.notify({
                type: 'negative',
                message: describeApiError(err) ?? 'Could not trim to fit.',
            });
        } finally {
            trimState.busy = false;
        }
    }

    function keepFromTrim(lineId: string): void {
        trimState.excluded = new Set(trimState.excluded).add(lineId);
        // Re-preview so the totals + cut set update in-place.
        void previewTrim();
    }

    function dismissTrim(): void {
        trimState.dismissed = true;
    }

    function scrollToDeferred(): void {
        document.getElementById('deferred-by-budget')?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    }

    // Mid-shop, ticked lines sink to the bottom of their group (still
    // visible, struck through) so the remaining work floats up. Array sort
    // is stable, so the user's sequence is preserved within each half.
    function sinkTickedWhileShopping(lines: ShoppingListLine[]): ShoppingListLine[] {
        if (detail.value?.status !== 'shopping') return lines;
        return [...lines].sort((a, b) => Number(a.is_ticked) - Number(b.is_ticked));
    }

    const lineGroups = computed<LineGroup[]>(() => {
        const lines = baseLines.value;
        if (groupBy.value === 'none') {
            return [{ key: 'all', label: null, lines: sinkTickedWhileShopping(lines) }];
        }
        const buckets = new Map<string, LineGroup>();
        for (const line of lines) {
            let key: string;
            let label: string;
            if (groupBy.value === 'store') {
                const chosen = chosenOfferFor(line);
                key = chosen?.store_name ?? '__no_store__';
                label = chosen?.store_name ?? 'No store linked';
            } else {
                key = locationKeyFor(line);
                label = key === '__no_location__' ? 'No location set' : key;
            }
            if (!buckets.has(key)) buckets.set(key, { key, label, lines: [] });
            buckets.get(key)!.lines.push(line);
        }
        // Sort lines inside each bucket alphabetically — within a bucket,
        // sequence is irrelevant because grouping has already broken the
        // shopper's manual ordering.
        for (const bucket of buckets.values()) {
            bucket.lines.sort((a, b) =>
                a.stock_item_name.localeCompare(b.stock_item_name)
            );
            bucket.lines = sinkTickedWhileShopping(bucket.lines);
        }
        return [...buckets.values()].sort((a, b) => {
            const aMissing = a.key.startsWith('__');
            const bMissing = b.key.startsWith('__');
            if (aMissing && !bMissing) return 1;
            if (!aMissing && bMissing) return -1;
            return (a.label ?? '').localeCompare(b.label ?? '');
        });
    });

    // nested display. A line with both `stock_item_id` and
    // `product_id` set is a *nested* product under the matching
    // stock-item line; a line with only `product_id` is a *standalone*
    // product-only line. `nestedLinesFor` reorders a group so each parent
    // is immediately followed by its nested children, and `isNestedChild`
    // drives the CSS indent on the child rows.
    function nestedLinesFor(group: LineGroup): ShoppingListLine[] {
        const lines = group.lines;
        // Map stock_item_id -> parent (product_id IS NULL, stock_item_id set)
        const parentByStockItem = new Map<string, ShoppingListLine>();
        for (const l of lines) {
            if (l.stock_item_id && !l.product_id) {
                parentByStockItem.set(l.stock_item_id, l);
            }
        }
        // Group children by parent line id
        const childrenByParent = new Map<string, ShoppingListLine[]>();
        const orphans: ShoppingListLine[] = [];
        for (const l of lines) {
            if (l.stock_item_id && l.product_id) {
                const parent = parentByStockItem.get(l.stock_item_id);
                if (parent) {
                    const bucket = childrenByParent.get(parent.line_id) ?? [];
                    bucket.push(l);
                    childrenByParent.set(parent.line_id, bucket);
                    continue;
                }
            }
            // Either: parent-style line (placed by main loop below) OR
            // standalone product-only line OR a nested child whose parent
            // isn't in this group — keep at natural position.
            orphans.push(l);
        }
        // Stable rebuild: walk the original ordering of `orphans` (which
        // already contains every parent and every uncoupled line in
        // sequence). For each parent, splice its children immediately
        // after.
        const out: ShoppingListLine[] = [];
        for (const l of orphans) {
            out.push(l);
            const kids = childrenByParent.get(l.line_id);
            if (kids) out.push(...kids);
        }
        return out;
    }
    function isNestedChild(line: ShoppingListLine): boolean {
        return !!(line.stock_item_id && line.product_id);
    }
    function isProductOnly(line: ShoppingListLine): boolean {
        return !line.stock_item_id && !!line.product_id;
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
    // Savings vs RRP across the whole shop (ticked + unticked).
    const savingsTotal = computed(() => detail.value?.totals?.total_savings ?? 0);
    // Doughnut % — pure display math over the server-owned counts.
    const progressPct = computed(() => {
        const count = detail.value?.lines.length ?? 0;
        if (count === 0) return 0;
        return (tickedCount.value / count) * 100;
    });

    const statusBadgeLabel = computed(() => {
        switch (detail.value?.status) {
            case 'shopping':
                return 'Shopping';
            case 'done':
                // I1 — a finished list is the receipt of the shop when money
                // surfaces are on. Pure label swap; status stays 'done'.
                return moneyEnabled.value ? 'Receipt' : 'Done';
            default:
                return 'Draft';
        }
    });
    // R-002: "done" routes through the neutral chip class (template
    // binding below), not a `grey-N` literal.
    const statusBadgeColour = computed<string | null>(() => {
        switch (detail.value?.status) {
            case 'shopping':
                return 'positive';
            case 'done':
                return null;
            default:
                return 'primary';
        }
    });

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
            return formatLocaleDate(iso) || iso;
        } catch {
            return iso;
        }
    }

    // ── Planned shop date (Chunk 7 / UX-v2 §4) ───────────────────────
    // A real outlined button now (S14) — today/overdue tint the button
    // instead of stacking a separate banner on the page.
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

    const shopDayLabel = computed(() => {
        const d = detail.value?.planned_shop_date ?? null;
        if (!d) return 'Set shop day';
        if (d === todayIso()) return 'Shop day: today';
        if (d === tomorrowIso()) return 'Shop day: tomorrow';
        const days = daysFromToday(d);
        if (days < 0 && detail.value?.status !== 'done') {
            return `Shop day: ${formatDate(d)} (overdue)`;
        }
        return `Shop day: ${formatDate(d)}`;
    });
    const shopDayTone = computed<string | undefined>(() => {
        const d = detail.value?.planned_shop_date ?? null;
        if (!d || detail.value?.status === 'done') return undefined;
        if (d === todayIso()) return 'positive';
        if (daysFromToday(d) < 0) return 'warning';
        return undefined;
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
            await refreshAll();
            plannedDateOpen.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save shop day.',
                caption: toastCaption(err),
            });
        }
    }

    async function clearPlannedDate() {
        if (!detail.value) return;
        try {
            await api.updateAsync(listId.value, { planned_shop_date: null });
            await refreshAll();
            plannedDateOpen.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear shop day.',
                caption: toastCaption(err),
            });
        }
    }

    // ── Lists rail / mobile dropdown (UX-v2 §3) ──────────────────────
    // One continuum, server-ordered by effective date ascending (R-003:
    // the ordering rule lives in get_shopping_lists.py, not here) — the
    // client renders the payload order verbatim.
    const newListOpen = ref(false);
    const putAwayOpen = ref(false);
    const railEntries = computed(() => store.summaries);
    const currentSummary = computed(() =>
        store.summaries.find((s) => s.shopping_list_id === listId.value) ?? null,
    );

    const railScrollRef = ref<QVirtualScroll | null>(null);

    function scrollRailToSelection() {
        const idx = railEntries.value.findIndex(
            (s) => s.shopping_list_id === listId.value,
        );
        if (idx < 0) return;
        void nextTick(() => {
            railScrollRef.value?.scrollTo(idx, 'center');
        });
    }
    watch([listId, () => railEntries.value.length], scrollRailToSelection);

    function switchToList(id: string) {
        if (id === listId.value) return;
        void router.push(`/shopping-lists/${id}`);
    }

    function onListCreated({ listId: newId }: { listId: string }) {
        void store.refreshAsync();
        switchToList(newId);
    }

    async function deleteSummary(s: ShoppingListSummary) {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${s.display_name}"?`,
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
                caption: toastCaption(err),
            });
        }
    }

    function onDeleteCurrentList() {
        if (currentSummary.value) void deleteSummary(currentSummary.value);
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
                caption: toastCaption(err),
            });
        }
    }

    async function load() {
        if (!listId.value) return;
        loading.value = true;
        loadError.value = null;
        // Clear the previous list's data so the user sees a loading spinner
        // — not stale rows from the list they navigated away from —
        // while the new list's detail is in flight.
        detail.value = null;
        try {
            detail.value = await api.getDetailAsync(listId.value);
            primeVerdicts(listId.value);
        } catch (err) {
            loadError.value = `Could not load list: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
        // refresh the trim-to-budget banner state as soon as the
        // list is available. Own try/catch inside; failures never bubble.
        void refreshTrimStatus();
    }

    // B6 — one request for the whole list's verdicts, marked in-flight before
    // the lines paint so each `BuyVerdictBadgeInline` reads the shared answer
    // instead of asking for its own. Called synchronously after `detail` is
    // assigned (Vue renders on the next tick, so the marks land first).
    // Fire-and-forget: `primeBuyVerdicts` swallows its own failure, and a list
    // that can't fetch verdicts still shows its items.
    function primeVerdicts(shoppingListId: string): void {
        if (!buyVerdictEnabled.value) return;
        const ids = (detail.value?.lines ?? [])
            .map((line) => line.stock_item_id)
            .filter((id): id is string => !!id);
        void primeBuyVerdicts(
            ids,
            () => new BuyVerdictApiService().getForListAsync(shoppingListId),
        );
    }

    async function refreshAll() {
        // Refresh detail + the store-level summaries/membership in
        // parallel so the rail order, next-up marker and cart-button
        // state elsewhere stay accurate.
        await Promise.all([load(), store.refreshAsync()]);
    }

    async function onPutAwayAssigned(): Promise<void> {
        // The dialog just persisted a new stock_location for one line's
        // item. Reload the list detail so the line's breadcrumb + group
        // membership move with it — the dialog re-reads via v-model on
        // detail.lines.
        await load();
    }

    // ── Name editing (UX-v2 §5: clearable custom name) ────────────────
    // The fallback chain (custom > shop day > created) is server-owned
    // (`display_name`); this only edits the raw custom `name`.
    const dateFallbackName = computed(() => {
        const d = detail.value?.planned_shop_date;
        if (d) return formatDate(`${d}T00:00:00`);
        return detail.value ? formatDate(detail.value.created_at) : '';
    });

    function startNameEdit() {
        nameDraft.value = detail.value?.name ?? '';
        editingName.value = true;
    }

    function cancelName() {
        editingName.value = false;
    }

    async function saveName() {
        if (!detail.value) return;
        const next = (nameDraft.value ?? '').trim();
        const current = detail.value.name ?? '';
        if (next === current) {
            editingName.value = false;
            return;
        }
        try {
            // Blank = clear the custom name (explicit null on the wire); the
            // list re-labels itself from its dates.
            await api.updateAsync(listId.value, { name: next === '' ? null : next });
            await refreshAll();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not rename.',
                caption: toastCaption(err),
            });
        } finally {
            editingName.value = false;
        }
    }

    function onOpenQuickAdd() {
        // Pre-target this list so the sheet skips its list picker default.
        openQuickAdd({ listId: listId.value });
    }

    // ── Keyboard shortcuts ────────────────────────────────────────────
    const orderedLines = computed(() => lineGroups.value.flatMap((g) => g.lines));
    const focusedLineId = ref<string | null>(null);
    // Shop-mode merge (M14): 'u' unticks the most recent tick from this
    // session — the in-store "oops, wrong item" key.
    const recentTickStack = ref<string[]>([]);

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
    function untickLastTicked() {
        if (detail.value?.status === 'done') return;
        while (recentTickStack.value.length > 0) {
            const lineId = recentTickStack.value.pop()!;
            const line = detail.value?.lines.find((l) => l.line_id === lineId);
            if (line?.is_ticked) {
                void onToggleTicked(lineId, false);
                return;
            }
        }
    }

    useShortcut([
        { keys: 'n', scope: 'Shopping list', description: 'Add an item', handler: onOpenQuickAdd },
        { keys: 'space', scope: 'Shopping list', description: 'Tick / untick the focused line', handler: tickFocusedLine },
        { keys: 'u', scope: 'Shopping list', description: 'Untick the last item you ticked', handler: untickLastTicked },
        { keys: 'arrowdown', scope: 'Shopping list', description: 'Focus next line', handler: () => moveLineFocus(1) },
        { keys: 'arrowup', scope: 'Shopping list', description: 'Focus previous line', handler: () => moveLineFocus(-1) },
    ]);

    // QuickAddSheet writes via shoppingListStore.refreshAsync but the
    // per-list detail isn't part of that refresh — reload it locally
    // whenever the sheet closes so a freshly-added line shows up.
    watch(quickAddOpen, (open, wasOpen) => {
        if (wasOpen && !open) void load();
    });

    // react to URL list-id changes. The merged overview-into-
    // detail design means switching lists (rail, dropdown, rail kebab)
    // only changes `route.params.id` without unmounting this component,
    // so `onMounted` doesn't re-fire.
    watch(listId, () => { void load(); });

    // ── Swap with substitute ─────────────────────────────────────────
    async function onSwapSubstitute(line: ShoppingListLine) {
        // Pull substitutes from the stock item's detail — we don't keep
        // them in the line DTO because they're a per-item attribute and
        // would bloat every line.
        // product-only lines have no stock_item_id;
        // substitutes don't apply, so bail early.
        if (!line.stock_item_id) return;
        let subs: Substitute[] = [];
        try {
            const itemDetail = await stockItemApi.getDetailAsync(line.stock_item_id);
            subs = itemDetail.substitutes ?? [];
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load substitutes.',
                caption: toastCaption(err),
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
        // drop product-only lines (null stock_item_id) from
        // the dedupe set; they don't anchor a substitute swap.
        const onListIds = new Set(
            (detail.value?.lines ?? [])
                .map((l) => l.stock_item_id)
                .filter((id): id is string => !!id),
        );
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
                caption: toastCaption(err),
            });
        }
    }

    // ── FU-653: Dora's inferred suggestions ───────────────────────────
    // Dismissal is deliberately in-memory only: the suggestion set changes as
    // the belief does, so persisting "hidden" would need a per-item ledger and
    // an expiry policy to answer "hidden until when?" — for a strip you can
    // also just ignore, that's machinery for nothing. It comes back next visit.
    const suggestionsDismissed = ref(false);
    const addingSuggestionId = ref<string | null>(null);

    const visibleSuggestions = computed<InferredSuggestion[]>(() =>
        suggestionsDismissed.value ? [] : (detail.value?.inferred_suggestions ?? []),
    );

    async function onAddSuggestion(suggestion: InferredSuggestion) {
        addingSuggestionId.value = suggestion.stock_item_id;
        try {
            await api.addLineAsync(listId.value, {
                stock_item_id: suggestion.stock_item_id,
            });
            await refreshAll();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Added ${suggestion.name}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: `Could not add ${suggestion.name}.`,
                caption: toastCaption(err),
            });
        } finally {
            addingSuggestionId.value = null;
        }
    }

    async function onToggleTicked(lineId: string, value: boolean) {
        // Optimistic flip so the checkbox feels instant; if the request
        // fails we re-load the canonical state. Network errors specifically
        // are absorbed into the offline queue so ticking-off mid-shop keeps
        // working while we hunt for signal.
        const line = detail.value?.lines.find((l) => l.line_id === lineId);
        if (line) line.is_ticked = value;
        if (value) recentTickStack.value.push(lineId);
        try {
            const result = await tryWithQueue(
                () => api.updateLineAsync(listId.value, lineId, { is_ticked: value }),
                {
                    url: `${resolveBaseURL()}/shopping-lists/${listId.value}/lines/${lineId}`,
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
        } catch (err) {
            await load();
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update line.',
                caption: toastCaption(err),
            });
        }
    }

    // ── P2-02: actual price + merchant override ─────────────────────────
    // A small popover sits behind the price button on each line. Users tap
    // it mid-shop or at finish time to type what the till actually charged
    // and (optionally) confirm which merchant they bought from. Both flow
    // into the assistant's purchase-history stats.
    const priceEditorDraft = reactive<{
        line_id: string | null;
        price: number | null;
        store_id: string | null;
    }>({ line_id: null, price: null, store_id: null });

    function onOpenPriceEditor(line: ShoppingListLine) {
        priceEditorDraft.line_id = line.line_id;
        // Seed with the existing override, else the server-resolved prefill
        // (D3: prior receipt, else chosen offer — source-labelled), so the
        // common case is "confirm one number".
        if (line.actual_unit_price != null) {
            priceEditorDraft.price = line.actual_unit_price;
        } else {
            priceEditorDraft.price =
                line.prefill_unit_price ?? chosenOfferFor(line)?.price_now ?? null;
        }
        if (line.purchased_store_id) {
            priceEditorDraft.store_id = line.purchased_store_id;
        } else {
            const offer = chosenOfferFor(line);
            priceEditorDraft.store_id = offer?.store_id ?? null;
        }
    }

    function storeOptionsFor(line: ShoppingListLine) {
        const seen = new Map<string, string>();
        for (const offer of line.offers) {
            if (!seen.has(offer.store_id)) {
                seen.set(offer.store_id, offer.store_name);
            }
        }
        return Array.from(seen, ([value, label]) => ({ value, label }));
    }

    async function savePriceEditor(line: ShoppingListLine) {
        if (priceEditorDraft.line_id !== line.line_id) return;
        const nextPrice = priceEditorDraft.price;
        const nextStore = priceEditorDraft.store_id;
        // Empty/zero/negative input clears the override rather than storing
        // a meaningless number. The backend rejects negatives anyway; this
        // saves the round-trip.
        if (nextPrice == null || Number.isNaN(nextPrice) || nextPrice <= 0) {
            await clearPriceOverride(line);
            return;
        }
        const previousPrice = line.actual_unit_price;
        const previousStore = line.purchased_store_id;
        const previousStoreName = line.purchased_store_name;
        line.actual_unit_price = nextPrice;
        line.purchased_store_id = nextStore ?? null;
        line.purchased_store_name =
            storeOptionsFor(line).find((o) => o.value === nextStore)?.label ?? null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                actual_unit_price: nextPrice,
                ...(nextStore
                    ? { purchased_store_id: nextStore }
                    : { clear_purchased_store: true }),
            });
        } catch (err) {
            line.actual_unit_price = previousPrice;
            line.purchased_store_id = previousStore;
            line.purchased_store_name = previousStoreName;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save the price.',
                caption: toastCaption(err),
            });
        }
    }

    async function clearPriceOverride(line: ShoppingListLine) {
        const previousPrice = line.actual_unit_price;
        const previousStore = line.purchased_store_id;
        const previousStoreName = line.purchased_store_name;
        if (previousPrice == null && previousStore == null) return;
        line.actual_unit_price = null;
        line.purchased_store_id = null;
        line.purchased_store_name = null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                clear_actual_unit_price: true,
                clear_purchased_store: true,
            });
        } catch (err) {
            line.actual_unit_price = previousPrice;
            line.purchased_store_id = previousStore;
            line.purchased_store_name = previousStoreName;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear the price.',
                caption: toastCaption(err),
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
                caption: toastCaption(err),
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

    // the chosen preferred-buy label for a line's hint chip.
    function buyHintLabel(line: ShoppingListLine): string | null {
        if (!line.preferred_buy_id) return null;
        return (line.preferred_buys ?? []).find(
            (pb) => pb.preferred_buy_id === line.preferred_buy_id,
        )?.label ?? null;
    }
    async function onPickHint(lineId: string, preferredBuyId: string | null) {
        const line = detail.value?.lines.find((l) => l.line_id === lineId);
        if (!line) return;
        const previous = line.preferred_buy_id ?? null;
        // Toggle: re-picking the chosen hint clears it.
        const next = preferredBuyId === previous ? null : preferredBuyId;
        line.preferred_buy_id = next;
        try {
            if (next === null) {
                await api.updateLineAsync(listId.value, lineId, { clear_preferred_buy: true });
            } else {
                await api.updateLineAsync(listId.value, lineId, { preferred_buy_id: next });
            }
        } catch (err) {
            line.preferred_buy_id = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not set the hint.',
                caption: toastCaption(err),
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
                caption: toastCaption(err),
            });
        }
    }

    // buy-verdict action for an in-shop line.
    // - `remove_from_list` targets THIS specific line (line-level intent).
    // - `mark_stocked` closes FU-454: routes through the shared
    //   `useBuyVerdictActions.markStocked` seam so the item flips to the
    //   Well-Stocked band and the verdict cache refreshes.
    // - `add_to_list` / `skip` / `none` are no-ops here — the line is
    //   already on this list; no meaningful mutation.
    const verdictActions = useBuyVerdictActions();
    async function onLineVerdictAction(
        line: ShoppingListLine,
        kind: 'add_to_list' | 'skip' | 'mark_stocked'
            | 'remove_from_list' | 'none',
    ) {
        if (kind === 'remove_from_list') {
            await onRemoveLine(line.line_id);
            if (line.stock_item_id) invalidateBuyVerdict(line.stock_item_id);
            return;
        }
        if (kind === 'mark_stocked' && line.stock_item_id) {
            await verdictActions.markStocked(line.stock_item_id);
            return;
        }
        // `add_to_list` / `skip` / `none` — no mutation. Silent by design.
    }

    async function onRemoveLine(lineId: string) {
        const before = detail.value?.lines.find((l) => l.line_id === lineId);

        // removing a product-only line (no
        // stock_item_id) prompts to also remove the *linked* stock-item
        // line, if one is also on this list. The user added the product
        // intent; removing it usually implies the stock-item placeholder
        // goes too, but they may want to keep the generic line.
        let alsoRemoveStockItemId: string | null = null;
        if (before && !before.stock_item_id && before.product_id) {
            const linkedStockItemId = productStore.products?.find(
                (p) => p.product_id === before.product_id,
            )?.linked_stock_item_id ?? null;
            if (linkedStockItemId) {
                const parentLine = detail.value?.lines.find(
                    (l) =>
                        l.stock_item_id === linkedStockItemId
                        && l.line_id !== lineId,
                );
                if (parentLine) {
                    // Yes → remove both; No/dismiss → just the product. The
                    // product line is going regardless (the user already
                    // clicked Remove); the prompt is purely about whether the
                    // generic stock-item placeholder rides along.
                    const removeBoth = await new Promise<boolean>((resolve) => {
                        $q.dialog({
                            title: 'Also remove the stock item?',
                            message: `${parentLine.stock_item_name} is on this list as its own line. Remove it too?`,
                            ok: { label: 'Yes, remove both', noCaps: true, color: 'primary' },
                            cancel: { label: 'No, just the product', noCaps: true, flat: true },
                            persistent: false,
                        })
                            .onOk(() => resolve(true))
                            .onCancel(() => resolve(false))
                            .onDismiss(() => {});
                    });
                    if (removeBoth) alsoRemoveStockItemId = linkedStockItemId;
                }
            }
        }

        try {
            await api.deleteLineAsync(listId.value, lineId);
            if (alsoRemoveStockItemId) {
                await api.removeByStockItemFromListAsync(
                    listId.value,
                    alsoRemoveStockItemId,
                );
            }
            await refreshAll();
            // UX-v2 §12 Q4: no undo toast — re-adding is one quick-add away,
            // and the app-wide undo posture is under review (FU-163).
            if (before) {
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Removed ${before.stock_item_name}.`,
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove line.',
                caption: toastCaption(err),
            });
        }
    }

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
                caption: toastCaption(err),
            });
        }
    }

    // Print pulls from the shared composable so every caller stays in
    // lockstep on URL shape. (CSV export was removed app-wide — §12 Q1.)
    const exportActions = useShoppingListExport();

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
                caption: toastCaption(err),
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
                    model: `Template from ${detail.value!.display_name}`,
                    type: 'text',
                    isValid: (val: string) => val.trim().length > 0,
                },
                cancel: { noCaps: true },
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
                caption: toastCaption(err),
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
                        label: s.display_name,
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
                caption: toastCaption(err),
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
                caption: toastCaption(err),
            });
        }
    }

    // ── Receipt attachments (FU-334) ────────────────────────────────────
    // Pure record-keeping: attach 1..N receipt photos to a `shopping` or
    // `done` list; tap to zoom; trash to remove. No OCR. ImageSourcePicker
    // owns the source-pick UX (Take photo vs Choose image) AND the
    // `processImageFile` chokepoint (R-003) — this handler just receives
    // a `ProcessedImage` and POSTs the data URL.
    const attachmentUploading = ref(false);
    const attachmentZoomId = ref<string | null>(null);

    const attachmentSectionVisible = computed(
        () => !!detail.value && detail.value.status !== 'draft',
    );

    function attachmentSrc(attachmentId: string): string {
        if (!listId.value) return '';
        return shoppingListAttachmentUrl(listId.value, attachmentId);
    }

    async function onAttachmentPicked(image: ProcessedImage) {
        if (!detail.value || !listId.value) return;
        attachmentUploading.value = true;
        try {
            await api.addAttachmentAsync(listId.value, image.dataUrl);
            // Re-fetch to pick up the server-assigned id + sequence.
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not attach receipt.',
                caption: toastCaption(err),
            });
        } finally {
            attachmentUploading.value = false;
        }
    }

    function onAttachmentError(message: string) {
        // ImageSourcePicker has already surfaced the inline error caption;
        // mirror it as a toast so the failure is visible even if the user
        // scrolled past the picker.
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message: 'Could not read that image.',
            caption: message,
        });
    }

    async function onDeleteAttachment(attachmentId: string) {
        if (!detail.value) return;
        try {
            await api.deleteAttachmentAsync(listId.value, attachmentId);
            // Optimistic local removal so the strip updates without a re-fetch
            // round-trip; load() runs anyway to stay authoritative.
            detail.value.attachments = (detail.value.attachments ?? []).filter(
                (a) => a.attachment_id !== attachmentId,
            );
            if (attachmentZoomId.value === attachmentId) {
                attachmentZoomId.value = null;
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove receipt.',
                caption: toastCaption(err),
            });
            await load();
        }
    }

    onMounted(async () => {
        await stockItemStore.ensureLoadedAsync();
        // Levels power the inline StockLevelDot on shopping-list rows.
        await stockLevelStore.ensureLoadedAsync();
        // needed to resolve a product-only line's
        // linked stock item for the rule-4 modal and for nested-display
        // grouping.
        await productStore.ensureLoadedAsync();
        await store.ensureLoadedAsync();
        await load();
        scrollRailToSelection();
    });
</script>

<style scoped>
    .sld-title {
        min-width: 0;
    }
    .sld-name-input {
        min-width: 260px;
    }
    .sld-status-badge {
        font-size: 0.85rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 4px 12px;
    }
    .sld-group-toggle {
        border: 1px solid var(--surface-component);
        border-radius: 6px;
    }
    .sld-rail {
        width: 300px;
        position: sticky;
        top: 60px;
        height: calc(100vh - 110px);
    }
    .sld-rail-scroll {
        min-height: 0;
        overflow: auto;
    }
    .sld-shop-footer {
        position: sticky;
        bottom: 8px;
        z-index: 3;
        background: var(--surface-component);
        border-radius: 8px;
        box-shadow: 0 2px 8px var(--overlay-pressed, rgba(0, 0, 0, 0.2));
    }
    /* FU-334 — receipt thumb strip + lightbox viewer. */
    .sld-receipt-strip {
        flex-wrap: wrap;
    }
    .sld-receipt-thumb {
        position: relative;
        width: 96px;
        height: 96px;
        border-radius: 6px;
        overflow: hidden;
        background: var(--surface-component);
        box-shadow: 0 1px 3px var(--overlay-pressed, rgba(0, 0, 0, 0.15));
    }
    .sld-receipt-thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        cursor: zoom-in;
        display: block;
    }
    .sld-receipt-delete {
        position: absolute;
        top: 2px;
        right: 2px;
        background: var(--surface-component);
        border-radius: 50%;
    }
    .sld-receipt-zoom {
        max-width: 100%;
        max-height: 80vh;
        display: block;
        margin: 0 auto;
    }
    .sld-price-btn {
        min-width: 96px;
    }
    .shopping-line-name {
        font-weight: 500;
        text-decoration: none;
    }
    .shopping-line-name:hover {
        text-decoration: underline;
    }
    .shopping-line-ticked {
        background-color: var(--overlay-hover);
    }
    .shopping-line-focused {
        outline: 2px dashed var(--q-accent);
        outline-offset: -2px;
    }
    /* R-022 — DnD affordances live in src/css/dnd.scss
       (.dora-dnd-row / --dragging / --drop-over). The decorative
       handle icon-section is non-interactive (whole-row mode), so
       the grab/grabbing cursors aren't needed here. */
    .bulk-bar {
        background: var(--overlay-hover);
    }
    .bulk-bar-active {
        background: var(--brand-primary-soft);
    }
    .shopping-line-ticked-content {
        opacity: 0.6;
    }
    /* DR-15 / D-010: ticking a line used to snap straight to the dimmed state.
       The fade is what makes a tick feel like the line was *put away* rather
       than redrawn, and it reads both directions (untick fades back up). Only
       opacity is transitioned — `text-strike` is a text-decoration, which is
       not usefully animatable, and transitioning layout on a list this long
       would cost more than the polish is worth. */
    .shopping-line-ticked-content,
    .shopping-line-name {
        transition: opacity var(--motion-fast) var(--motion-ease);
    }
    /* C-7 Chunk 3 — nested product line sits indented under its
     * stock-item parent, with a left rail so the relationship reads at
     * a glance. */
    .shopping-line-nested {
        padding-left: 2.25rem;
        border-left: 3px solid var(--surface-component);
    }
    /* Product-only line (no linked stock item on this list) — softly
     * tinted background so it reads as a "to be linked later" signal,
     * not as a normal stock-anchored line. */
    .shopping-line-product-only {
        background-color: var(--overlay-pressed, var(--surface-component));
    }
    .offer-savings {
        font-weight: 600;
        font-size: 0.92em;
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
