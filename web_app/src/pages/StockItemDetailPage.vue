<template>
    <div class="q-pa-md">
        <!-- Header — back/close · name · spacer · (Show QR) · Delete top-right.
             Feedback 2026-06-18: the level chip moves down to the overview
             (under the name field, combined with "Level updated"); the top
             Mark-open / Set-expiry / Add-to-list trio is gone because all
             three actions live inline on the page already. Show QR stays
             since it's not reachable elsewhere. -->
        <div class="row items-center q-mb-md q-gutter-sm stock-detail__header">
            <BaseButton v-if="!embedded" variant="icon" :icon="ICONS.arrow_back" @click="goBack" />
            <BaseButton v-else variant="icon" :icon="ICONS.close" @click="emit('close')">
                <q-tooltip>Close panel</q-tooltip>
            </BaseButton>
            <div class="text-h5 q-mr-sm" style="min-width: 160px">
                <AppSkeleton v-if="loading && !detail" type="line" width="180px" height="1.6rem" />
                <template v-else>{{ detail?.name || 'Stock item' }}</template>
            </div>
            <q-space />
            <BaseButton
                v-if="detail && scanningEnabled"
                variant="secondary"
                icon="qr_code_2"
                label="Show QR"
                @click="showQrOpen = true"
            >
                <q-tooltip max-width="280px">
                    Prints Dora's own label for this item — a scannable QR
                    that opens this page. It's *not* the product's real
                    EAN/UPC barcode (barcodes register a Product, and any
                    linkage to this stock item is managed on this page).
                </q-tooltip>
            </BaseButton>
            <BaseButton
                v-if="detail"
                variant="danger-ghost"
                :icon="ICONS.delete"
                label="Delete"
                @click="confirmDelete"
            />
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <FadeTransition mode="out-in">
        <div v-if="loading && !detail" key="sid-loading">
            <!-- Skeleton mirrors the toolbar row + content cards below. -->
            <div class="row q-gutter-sm q-mb-md">
                <AppSkeleton type="rect" width="120px" height="36px" />
                <AppSkeleton type="rect" width="110px" height="36px" />
                <AppSkeleton type="rect" width="130px" height="36px" />
            </div>
            <AppSkeleton type="rect" width="100%" height="160px" class="q-mb-md" />
            <AppSkeleton type="rect" width="100%" height="220px" />
        </div>

        <div v-else-if="detail" key="sid-content">
            <!-- ── QR dialog ────────────────────────────────────────── -->
            <BaseDialog v-model="showQrOpen" :title="detail.name" closable card-style="min-width: 280px; max-width: 400px">
                    <q-card-section class="text-center">
                        <img
                            :src="qrSrc"
                            alt="QR code"
                            style="width: 256px; height: 256px; max-width: 100%;"
                        />
                    </q-card-section>
                    <template #actions>
                        <BaseButton variant="ghost" label="Close" v-close-popup />
                        <BaseButton
                            variant="primary"
                            :icon="ICONS.print"
                            label="Print one"
                            @click="openSingleQrSheet"
                        />
                    </template>
            </BaseDialog>

            <!-- Feedback 2026-06-18: replaced q-tabs with DoraTabs so the
                 active-tab underline uses the same sliding accent indicator
                 as the main menu (shrunk to tab-row scale). The per-tab
                 colour saturation is gone — the indicator carries the colour. -->
            <DoraTabs v-model="tab" :tabs="tabDefinitions" class="q-mb-sm" />

            <q-tab-panels v-model="tab" animated>
                <!-- ── Overview ───────────────────────────────────────────
                     C-1b.1: single-column inline-edit fact list. Each row
                     IS its editor; toggles/selects/dates save immediately
                     on change, text rows save on blur. No separate q-form
                     + Save/Reset (the old 2-col "facts | edit form" split
                     is what L127 called "messy"). Level dedupe (L121): the
                     header chip is the only level editor.
                -->
                <!-- Feedback 2026-06-18 (round 2): q-pa-md on every
                     q-tab-panel so the inner content (image, list of
                     editors, all per-tab content) has consistent
                     breathing room on every side. The outer wrapper
                     keeps q-pa-md too for the header/toolbar row. -->
                <q-tab-panel name="overview" class="q-pa-md">
                    <!-- the buy-verdict oracle (row/line
                         badges elsewhere; the full detail card here per
                         FU-437). The card no-ops when the composable hasn't
                         resolved yet or the install-wide flag is off, so
                         the overview stays quiet on thin data. -->
                    <BuyVerdictCard
                        v-if="buyVerdict"
                        :verdict="buyVerdict"
                        class="q-mb-md"
                        @action="onBuyVerdictAction"
                    />
                    <div class="row q-col-gutter-md items-start">
                        <div class="col-12">
                            <q-list separator class="dora-inline-edit">
                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Name</q-item-section>
                                    <q-item-section>
                                        <q-input
                                            v-model="form.name"
                                            dense
                                            borderless
                                            placeholder="Name this item"
                                            :rules="[(v: string) => (!!v && v.length > 0) || 'Name required']"
                                            hide-bottom-space
                                            @blur="saveNameIfDirty"
                                            @keyup.enter="saveNameIfDirty"
                                        />
                                    </q-item-section>
                                </q-item>

                                <!-- Feedback 2026-06-18: level picker moved out
                                     of the header into the second overview row,
                                     combined with the level-updated timestamp
                                     to its right. The picker uses the same
                                     stock-level palette as the row buttons. -->
                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Level</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-sm">
                                            <!-- Round 9: render the level
                                                 colour as a coloured swatch
                                                 INSIDE the button (matching
                                                 the menu items' avatars)
                                                 rather than as the button's
                                                 own `color=` prop. The
                                                 outline + filled swatch
                                                 patterns rendered the same
                                                 Quasar palette name very
                                                 differently — looked like
                                                 a colour mismatch. With the
                                                 swatch approach both the
                                                 trigger and the menu rows
                                                 render the colour the same
                                                 way. -->
                                            <BaseDropdown
                                                flat
                                                dense
                                                class="dora-level-picker"
                                            >
                                                <template #label>
                                                    <StockLevelDot
                                                        :sequence="detailLevelSequence"
                                                        dot-class="q-mr-sm"
                                                    />
                                                    {{ detail.stock_level_name ?? '—' }}
                                                </template>
                                                <q-list dense>
                                                    <q-item
                                                        v-for="level in stockLevelStore.stockLevels"
                                                        :key="level.stock_level_id"
                                                        clickable
                                                        v-close-popup
                                                        @click="onChangeStockLevel(level.stock_level_id)"
                                                    >
                                                        <q-item-section avatar>
                                                            <StockLevelDot :sequence="level.sequence" />
                                                        </q-item-section>
                                                        <q-item-section>{{ level.name }}</q-item-section>
                                                    </q-item>
                                                </q-list>
                                            </BaseDropdown>
                                            <q-space />
                                            <span class="dora-text-secondary text-caption">
                                                Updated {{ relativeTime(detail.stock_level_last_updated) }}
                                            </span>
                                        </div>
                                        <!-- inferred level (additive;
                                             beside the recorded level above). -->
                                        <div v-if="belief" class="q-mt-xs">
                                            <PantryBeliefChip :belief="belief" />
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Location</q-item-section>
                                    <q-item-section>
                                        <q-select
                                            v-model="form.stock_location_id"
                                            :options="locationOptions"
                                            emit-value
                                            map-options
                                            use-input
                                            fill-input
                                            hide-selected
                                            input-debounce="200"
                                            clearable
                                            dense
                                            borderless
                                            placeholder="—"
                                            @filter="filterLocations"
                                            @clear="onClearLocation"
                                            @update:model-value="onChangeLocation"
                                        />
                                    </q-item-section>
                                </q-item>

                                <!-- Empty-state dash via `display-value`:
                                     q-select's `placeholder` only renders
                                     under `use-input`, which these don't
                                     need. `display-value=undefined` lets
                                     q-select pick the normal label when a
                                     value is set; a string forces that
                                     string into the field. -->
                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Stock group</q-item-section>
                                    <q-item-section>
                                        <q-select
                                            v-model="form.stock_group_id"
                                            :options="groupOptions"
                                            emit-value
                                            map-options
                                            clearable
                                            dense
                                            borderless
                                            :display-value="form.stock_group_id ? undefined : '—'"
                                            @clear="onClearGroup"
                                            @update:model-value="onChangeGroup"
                                        />
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Usual store</q-item-section>
                                    <q-item-section>
                                        <q-select
                                            v-model="form.usual_store_id"
                                            :options="storeOptions"
                                            emit-value
                                            map-options
                                            clearable
                                            dense
                                            borderless
                                            :display-value="form.usual_store_id ? undefined : '—'"
                                            @update:model-value="onChangeUsualStore"
                                        >
                                            <!-- Feedback 2026-08-08: show each store's logo
                                                 (real image when uploaded, deterministic
                                                 swatch otherwise) in the option list. -->
                                            <template #option="{ opt, itemProps }">
                                                <q-item v-bind="itemProps">
                                                    <q-item-section
                                                        avatar
                                                        style="min-width: 0; padding-right: 8px"
                                                    >
                                                        <StoreLogo
                                                            :name="opt.label"
                                                            :store-id="opt.value"
                                                            :has-image="opt.has_image"
                                                            :height="20"
                                                            :width="34"
                                                        />
                                                    </q-item-section>
                                                    <q-item-section>
                                                        <q-item-label>{{ opt.label }}</q-item-label>
                                                    </q-item-section>
                                                </q-item>
                                            </template>
                                        </q-select>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Expiry</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-xs">
                                            <span class="dora-text-primary">
                                                {{ detail.expiry_date || '—' }}
                                            </span>
                                            <q-space />
                                            <!-- Feedback 2026-08-08: Clear sits at the left
                                                 edge of the right-aligned cluster so showing/
                                                 hiding it (it only exists when there's a date)
                                                 doesn't nudge the +Nd / Set buttons — those
                                                 stay anchored to the right. -->
                                            <BaseButton
                                                v-if="detail.expiry_date"
                                                variant="danger-icon"
                                                size="sm"
                                                :icon="ICONS.close"
                                                :disable="busy"
                                                @click="clearExpiry"
                                            >
                                                <q-tooltip>Clear expiry</q-tooltip>
                                            </BaseButton>
                                            <BaseButton variant="ghost" dense size="sm" label="+1d" :disable="busy" @click="shiftExpiry(1)" />
                                            <BaseButton variant="ghost" dense size="sm" label="+7d" :disable="busy" @click="shiftExpiry(7)" />
                                            <BaseButton variant="ghost" dense size="sm" label="+14d" :disable="busy" @click="shiftExpiry(14)" />
                                            <!-- Feedback 2026-06-18: the calendar-only icon
                                                 button picks up the "Set" label that used to
                                                 live in the top toolbar. -->
                                            <BaseButton variant="ghost" dense size="sm" :icon="ICONS.event" label="Set" @click="expiryDialogOpen = true">
                                                <q-tooltip>Pick a date</q-tooltip>
                                            </BaseButton>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Open / in-use</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-sm">
                                            <q-toggle
                                                :model-value="detail.is_open"
                                                :disable="busy"
                                                @update:model-value="onToggleOpen"
                                            />
                                            <span v-if="detail.is_open && detail.opened_on" class="dora-text-secondary text-caption">
                                                Opened {{ detail.opened_on }}
                                            </span>
                                            <q-icon :name="ICONS.info_outline" size="16px" class="dora-text-secondary">
                                                <q-tooltip max-width="320px">
                                                    Opening an item doesn't
                                                    change its expiry date —
                                                    but for perishables it's
                                                    the cue to set or shorten
                                                    one. Use the expiry row
                                                    above to do that.
                                                </q-tooltip>
                                            </q-icon>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Essential</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-sm">
                                            <q-toggle
                                                :model-value="detail.is_essential"
                                                :disable="busy"
                                                @update:model-value="onToggleFlagged"
                                            />
                                            <q-icon :name="ICONS.info_outline" size="16px" class="dora-text-secondary">
                                                <q-tooltip max-width="320px">
                                                    Flagged items show up in
                                                    "essentials" auto-generate
                                                    sources even when they're
                                                    stocked. Different
                                                    from auto-add: this one
                                                    only matters when you run
                                                    auto-generate, not on
                                                    every stock change.
                                                </q-tooltip>
                                            </q-icon>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <!-- FU-511 — per-item "Auto-add when low"
                                     toggle removed. Auto-add is now a
                                     single install-wide setting managed at
                                     Settings → Admin → System → Stock
                                     (off / essential-only / all), which
                                     branches on this item's Essential flag
                                     above. Rationale: the per-item toggle
                                     was redundant with `is_essential` for
                                     the "staple you never want to run
                                     out of" use it was designed for. -->

                                <!-- Feedback 2026-06-18 (round 3): notes
                                     gets a real outlined input so the
                                     empty state reads as "type here"
                                     rather than a dash. Autogrow lets the
                                     row expand vertically as the user
                                     types. -->
                                <q-item>
                                    <q-item-section class="dora-text-secondary text-weight-bold" style="max-width:160px">Notes</q-item-section>
                                    <q-item-section>
                                        <q-input
                                            v-model="form.notes"
                                            dense
                                            outlined
                                            type="textarea"
                                            autogrow
                                            placeholder="Things to remember..."
                                            @blur="saveNotesIfDirty"
                                        />
                                    </q-item-section>
                                </q-item>
                            </q-list>

                            <!-- Preferred buys (FU-211) — free-text "what I
                                 actually buy" reminders. Always shown; not a
                                 product/SKU, just a personal memory aid (and a
                                 future shopping-list hint). -->
                            <!-- Feedback 2026-06-18 (round 4): the explainer
                                 ("What you actually buy for this — e.g.
                                 Vitasoy Oat Milky 1L") moves to an info-hover
                                 next to the heading. Same pattern as the
                                 toggle rows in the basics list. -->
                            <div class="q-mt-md dora-text-secondary text-caption q-mb-sm row items-center q-gutter-xs">
                                <span>Preferred buys</span>
                                <q-icon :name="ICONS.info_outline" size="14px" class="dora-text-muted">
                                    <q-tooltip max-width="320px">
                                        What you actually buy for this — e.g.
                                        “Vitasoy Oat Milky 1L”.
                                    </q-tooltip>
                                </q-icon>
                            </div>
                            <!-- Feedback 2026-06-18 (round 3): the manual
                                 reorder buttons are gone — these reminders
                                 are scanned alphabetically more often than
                                 they're ranked. Backend still stores a
                                 position (kept so historical data isn't
                                 disturbed), but the UI sorts the list
                                 A-Z client-side. -->
                            <q-list
                                v-if="preferredBuys.length"
                                separator
                                bordered
                                class="rounded-borders q-mb-sm"
                            >
                                <q-item
                                    v-for="pb in preferredBuys"
                                    :key="pb.preferred_buy_id"
                                >
                                    <q-item-section>
                                        <q-input
                                            v-if="editingBuyId === pb.preferred_buy_id"
                                            v-model="editingBuyLabel"
                                            dense
                                            outlined
                                            autofocus
                                            maxlength="255"
                                            @blur="saveBuyRename(pb)"
                                            @keydown.enter.prevent="saveBuyRename(pb)"
                                            @keydown.esc.prevent="editingBuyId = null"
                                        />
                                        <q-item-label v-else>{{ pb.label }}</q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <div class="row items-center no-wrap">
                                            <BaseButton
                                                variant="icon"
                                                :icon="ICONS.edit"
                                                :disable="busy"
                                                @click="startBuyRename(pb)"
                                            >
                                                <q-tooltip>Rename</q-tooltip>
                                            </BaseButton>
                                            <BaseButton
                                                variant="icon"
                                                :icon="ICONS.delete_outline"
                                                :disable="busy"
                                                @click="deleteBuy(pb)"
                                            >
                                                <q-tooltip>Remove</q-tooltip>
                                            </BaseButton>
                                        </div>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                            <div class="row items-center no-wrap q-gutter-sm">
                                <q-input
                                    v-model="newBuyLabel"
                                    dense
                                    outlined
                                    class="col"
                                    maxlength="255"
                                    placeholder="Add a preferred buy"
                                    @keydown.enter.prevent="addBuy"
                                />
                                <BaseButton
                                    variant="primary"
                                    :icon="ICONS.add"
                                    label="Add"
                                    :disable="!newBuyLabel.trim() || busy"
                                    @click="addBuy"
                                />
                            </div>

                            <!-- "Your prices" widget (C5
                                 revised) replaces the inline price entry
                                 form. The widget contains its own [Log a
                                 price] action that opens the shared
                                 PriceEntry dialog. Chunk 4 lights up the
                                 real baseline; chunk 6 wires Full history. -->
                            <template v-if="moneyEnabled">
                                <YourPricesWidget
                                    :your-prices="detail.your_prices ?? null"
                                    :prefill="detail.price_entry_prefill ?? null"
                                    :stores="storesList"
                                    :busy="busy"
                                    :stock-item-id="stockItemId"
                                    :item-name="detail.name"
                                    @submit="addObservation"
                                />
                                <q-list
                                    v-if="priceObservations.length"
                                    separator
                                    bordered
                                    class="rounded-borders q-mb-sm"
                                >
                                    <q-item
                                        v-for="obs in priceObservations"
                                        :key="obs.observation_id"
                                    >
                                        <q-item-section>
                                            <q-item-label>
                                                {{ formatMoney(obs.total_price) }}
                                                <span class="dora-text-muted">for {{ formatObsMeasure(obs) }}</span>
                                            </q-item-label>
                                            <q-item-label caption>
                                                {{ relativeTime(obs.observed_at) }}
                                                <span v-if="obs.store_name"> · {{ obs.store_name }}</span>
                                                <span v-if="obs.shopping_list_name"> · from {{ obs.shopping_list_name }}</span>
                                            </q-item-label>
                                        </q-item-section>
                                        <q-item-section side>
                                            <BaseButton
                                                variant="icon"
                                                :icon="ICONS.delete_outline"
                                                :disable="busy"
                                                @click="deleteObservation(obs)"
                                            >
                                                <q-tooltip>Remove</q-tooltip>
                                            </BaseButton>
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </template>
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Linked products ──────────────────────────────────
                     C-1b.3 (L125, L130, L131): Find-deals lives here now,
                     not in the toolbar. Empty state = a primary CTA; when
                     products exist, header carries a quieter "Link another"
                     that goes to the same place. The "Get cheapest" button
                     is gone — cheaper option is emphasised via card style
                     and each product carries its own Add-to-list (per §2.4).
                     Hidden entirely when `products` is off (§2.5). -->
                <q-tab-panel v-if="productsEnabled" name="products">
                    <div v-if="detail.products.length > 0" class="row items-center q-mb-sm q-gutter-sm">
                        <div class="text-subtitle1">Linked products</div>
                        <q-space />
                        <BaseButton
                            variant="ghost"
                            :icon="ICONS.add"
                            label="Link another"
                            @click="onFindAndLink"
                        />
                    </div>

                    <div v-if="detail.products.length === 0" class="column items-center q-py-xl q-gutter-md">
                        <q-icon :name="ICONS.local_offer" size="48px" class="dora-text-secondary" />
                        <div class="text-subtitle1">No products linked yet</div>
                        <div class="dora-text-secondary text-caption text-center" style="max-width: 360px">
                            Link a product to surface live deals and price
                            history for this stock item.
                        </div>
                        <BaseButton
                            variant="primary"
                            :icon="ICONS.local_offer"
                            label="Find &amp; link a product"
                            @click="onFindAndLink"
                        />
                    </div>

                    <div v-else class="row q-col-gutter-md">
                        <div
                            v-for="prod in sortedProducts"
                            :key="prod.product_id"
                            class="col-12 col-md-6"
                        >
                            <!-- cheapest card carries a "Cheapest"
                                 chip + a subtle highlight class so the
                                 cheaper option pops without needing a
                                 separate "Add cheapest" button (§2.4). -->
                            <q-card
                                bordered
                                flat
                                :class="{ 'dora-product-card--cheapest': isCheapest(prod) }"
                            >
                                <q-card-section class="row items-center no-wrap q-pb-xs">
                                    <StoreLogo
                                        :name="prod.store_name"
                                        :store-id="prod.store_id"
                                        :has-image="false"
                                        :height="20"
                                        :width="34"
                                        class="q-mr-sm"
                                    />
                                    <div class="col">
                                        <div class="ellipsis text-weight-medium">{{ prod.name }}</div>
                                        <div class="text-caption dora-text-muted">
                                            {{ prod.store_name }}
                                            <span v-if="prod.size"> · {{ prod.size }}</span>
                                        </div>
                                    </div>
                                    <q-chip
                                        v-if="isCheapest(prod)"
                                        dense
                                        color="positive"
                                        text-color="white"
                                    >
                                        Cheapest
                                    </q-chip>
                                    <q-chip
                                        v-if="discountPct(prod) !== null"
                                        dense
                                        color="negative"
                                        text-color="white"
                                    >
                                        {{ discountPct(prod) }}% off
                                    </q-chip>
                                </q-card-section>

                                <q-card-section class="row items-center q-py-xs">
                                    <div>
                                        <span v-if="prod.price_now !== null" class="text-h6">
                                            {{ formatMoney(prod.price_now) }}
                                        </span>
                                        <span
                                            v-if="prod.price_was !== null && prod.price_now !== null && prod.price_was > prod.price_now"
                                            class="text-caption dora-text-muted strike q-ml-xs"
                                        >
                                            {{ formatMoney(prod.price_was) }}
                                        </span>
                                    </div>
                                    <q-space />
                                    <TrendSparkline :values="priceHistory.get(prod.product_id) ?? []" />
                                </q-card-section>

                                <q-separator />
                                <q-card-actions align="right">
                                    <BaseButton
                                        variant="ghost"
                                        dense
                                        :icon="ICONS.add_shopping_cart"
                                        label="Add to list"
                                        :loading="busy"
                                        @click="onAddProductToList(prod.product_id)"
                                    />
                                    <BaseButton
                                        v-if="prod.web_url"
                                        variant="icon"
                                        :icon="ICONS.open_in_new"
                                        :href="prod.web_url"
                                        target="_blank"
                                        rel="noopener"
                                    >
                                        <q-tooltip>Open on {{ prod.store_name }}</q-tooltip>
                                    </BaseButton>
                                    <BaseButton variant="icon" :icon="ICONS.link_off" class="text-negative" @click="onUnlink(prod.product_id)">
                                        <q-tooltip>Unlink</q-tooltip>
                                    </BaseButton>
                                </q-card-actions>
                            </q-card>
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Recipes using this ─────────────────────────────── -->
                <q-tab-panel name="recipes">
                    <div v-if="recipesForDetail.length === 0" class="dora-text-muted text-caption q-pa-md">
                        Not used in any saved recipe.
                    </div>
                    <!-- Feedback 2026-08-08: reflow by column count, not by
                         stretching a fixed 3-up breakpoint grid. An auto-fill
                         grid keeps each card near its natural width and adds/
                         removes a whole column as the window resizes, instead
                         of the cards continuously growing/shrinking. -->
                    <div v-else class="stock-detail__recipe-grid">
                        <div
                            v-for="r in recipesForDetail"
                            :key="r.recipe_id"
                        >
                            <!-- wire the
                                 favourite-toggle + add-all-to-list events
                                 RecipeCard emits. Previously dropped, so
                                 "remove from favourites does nothing" and
                                 "every recipe action except Cook is dead"
                                 (feedback L132 / L134) were live defects
                                 on this surface. -->
                            <RecipeCard
                                :recipe="r"
                                :show-filter-by-ingredients="true"
                                @open="goToRecipe"
                                @cook="goToCook"
                                @toggle-favourite="onToggleFavourite"
                                @add-missing="onAddMissing"
                                @add-all-to-list="onAddAllToList"
                                @filter-by-ingredients="onFilterStockByRecipe"
                            />
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Substitutes ──────────────────────────────────────
                     Round-17: row redesign per feedback —
                     • dot-only level indicator on the LEFT (no "OK/Mid"
                       short labels);
                     • name in default text colour, not text-primary;
                     • whole row is clickable; opens in the same peek
                       panel (when embedded) or navigates full-page
                       (`open-detail` event from the page lets
                       StockOverview redirect the peek's id without
                       losing the splitter context). -->
                <q-tab-panel name="substitutes">
                    <div class="row items-center q-mb-sm">
                        <div class="text-subtitle1">Substitutes</div>
                        <q-space />
                        <BaseButton variant="primary" dense :icon="ICONS.add" label="Add substitute" @click="openSubstitutePicker" />
                    </div>

                    <div v-if="detail.substitutes.length === 0" class="dora-text-muted text-caption q-pa-md">
                        No substitutes yet. Add items that can stand in for this one.
                    </div>

                    <q-list v-else separator>
                        <q-item
                            v-for="sub in detail.substitutes"
                            :key="sub.stock_item_id"
                            clickable
                            @click="onOpenSubstitute(sub.stock_item_id)"
                        >
                            <q-item-section avatar style="min-width: 28px">
                                <q-icon
                                    name="circle"
                                    size="12px"
                                    :color="colourForSequence(stockItemFor(sub).stock_level_sequence ?? null) ?? undefined"
                                    :class="{ 'dora-text-muted': !colourForSequence(stockItemFor(sub).stock_level_sequence ?? null) }"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ stockItemFor(sub).name }}</q-item-label>
                                <!-- optional ratio shown above
                                     notes; cook-mode picker mirrors this
                                     same layout so the user reads the
                                     swap the same way in both places. -->
                                <q-item-label v-if="substituteRatioText(sub)" caption class="dora-text-secondary">
                                    {{ substituteRatioText(sub) }}
                                </q-item-label>
                                <q-item-label v-if="sub.notes" caption class="dora-text-muted">
                                    {{ sub.notes }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <!-- pencil icon opens the metadata
                                     edit dialog (notes + ratio). Sits next
                                     to the unlink action so the substitute
                                     row carries both lifecycle controls
                                     without the row getting cluttered. -->
                                <div class="row no-wrap items-center">
                                    <BaseButton
                                        variant="icon"
                                        :icon="ICONS.edit"
                                        @click.stop="onEditSubstituteMetadata(sub)"
                                    >
                                        <q-tooltip>Edit note / ratio</q-tooltip>
                                    </BaseButton>
                                    <BaseButton
                                        variant="icon"
                                        :icon="ICONS.link_off"
                                        class="text-negative"
                                        @click.stop="onRemoveSubstitute(sub.stock_item_id)"
                                    >
                                        <q-tooltip>Remove substitute</q-tooltip>
                                    </BaseButton>
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>

                    <!-- metadata edit dialog. v-model-controlled
                         open state + a snapshot of the substitute being
                         edited (driven by `onEditSubstituteMetadata`). -->
                    <SubstituteMetadataDialog
                        v-if="editingSubstitute"
                        v-model="substituteMetadataOpen"
                        :from-name="detail.name"
                        :to-name="editingSubstitute.name"
                        :initial-notes="editingSubstitute.notes"
                        :initial-ratio-quantity-in="editingSubstitute.ratio_quantity_in"
                        :initial-ratio-unit-in="editingSubstitute.ratio_unit_in"
                        :initial-ratio-quantity-out="editingSubstitute.ratio_quantity_out"
                        :initial-ratio-unit-out="editingSubstitute.ratio_unit_out"
                        :saving="substituteMetadataSaving"
                        @save="onSaveSubstituteMetadata"
                    />

                    <!-- Barcodes section. Gated on the install-wide
                         scanning flag (R-029: when off, the surface stays
                         hidden — scanning isn't an active capability on
                         this install). Shows direct registrations +
                         via-Product derivations; Add/Remove available for
                         direct rows only (via-Product live on the
                         Product). -->
                    <div v-if="scanningEnabled" class="q-mt-lg">
                        <div class="row items-center q-mb-sm">
                            <div class="text-subtitle1">Barcodes</div>
                            <q-space />
                            <BaseButton
                                variant="primary"
                                dense
                                :icon="ICONS.add"
                                label="Add barcode"
                                @click="onAddBarcodeClick"
                            />
                        </div>
                        <div
                            v-if="detail.barcodes.length === 0"
                            class="dora-text-muted text-caption q-pa-md"
                        >
                            No barcodes yet. Add an EAN/UPC to make this item
                            open when you scan that code.
                        </div>
                        <q-list v-else separator>
                            <q-item
                                v-for="bc in detail.barcodes"
                                :key="bc.barcode_id"
                            >
                                <q-item-section>
                                    <q-item-label class="dora-text-monospace">
                                        {{ bc.barcode }}
                                    </q-item-label>
                                    <q-item-label
                                        v-if="bc.source === 'via_product'"
                                        caption
                                        class="dora-text-muted"
                                    >
                                        via product · {{ bc.product_name ?? '—' }}
                                    </q-item-label>
                                    <q-item-label
                                        v-else
                                        caption
                                        class="dora-text-muted"
                                    >
                                        direct
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <BaseButton
                                        v-if="bc.source === 'direct'"
                                        variant="icon"
                                        :icon="ICONS.delete"
                                        class="text-negative"
                                        @click="onRemoveBarcode(bc.barcode_id)"
                                    >
                                        <q-tooltip>Remove barcode</q-tooltip>
                                    </BaseButton>
                                </q-item-section>
                            </q-item>
                        </q-list>

                        <!-- Add-barcode dialog. Textbox by default;
                             a future polish slot could add a "scan" button
                             when the camera is available. -->
                        <BaseDialog
                            v-model="addBarcodeOpen"
                            title="Add a barcode"
                            closable
                            card-style="min-width: 320px; max-width: 420px"
                        >
                            <q-card-section>
                                <div class="text-caption dora-text-muted q-mb-sm">
                                    Scanning this code will open
                                    <strong>{{ detail.name }}</strong>.
                                </div>
                                <q-input
                                    v-model="addBarcodeValue"
                                    outlined
                                    dense
                                    autofocus
                                    placeholder="e.g. 9300675001120"
                                    label="Barcode (EAN / UPC)"
                                    :error="!!addBarcodeError"
                                    :error-message="addBarcodeError ?? undefined"
                                    @keydown.enter.prevent="onConfirmAddBarcode"
                                />
                            </q-card-section>
                            <template #actions>
                                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                                <BaseButton
                                    variant="primary"
                                    label="Add"
                                    :loading="addBarcodeSaving"
                                    :disable="addBarcodeValue.trim().length === 0"
                                    @click="onConfirmAddBarcode"
                                />
                            </template>
                        </BaseDialog>
                    </div>
                </q-tab-panel>

                <!-- ── On shopping lists ──────────────────────────────────
                     Round-17: dropped the bright primary-coloured
                     "Primary" pill; the quick-add target now reads as a
                     small warning-toned star icon (same idiom as
                     favourites elsewhere). Rows use the cart icon in the
                     avatar slot, default text colour everywhere. -->
                <q-tab-panel name="lists">
                    <div v-if="onLists.length === 0" class="column items-start q-gutter-sm q-pa-md">
                        <div class="dora-text-muted text-caption">
                            Not on any active shopping list.
                        </div>
                        <BaseButton
                            variant="ghost"
                            :icon="ICONS.add_shopping_cart"
                            label="Add to a list"
                            @click="onAddToList"
                        />
                    </div>
                    <q-list v-else separator>
                        <q-item
                            v-for="l in onLists"
                            :key="l.shopping_list_id"
                            clickable
                            @click="goToList(l.shopping_list_id)"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.shopping_cart" />
                            </q-item-section>
                            <q-item-section>{{ l.name }}</q-item-section>
                            <q-item-section
                                v-if="l.shopping_list_id === primaryListId"
                                side
                            >
                                <q-icon :name="ICONS.star" color="warning" size="18px">
                                    <q-tooltip>Quick-add target list</q-tooltip>
                                </q-icon>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-tab-panel>

                <!-- ── History (lifecycle timeline) ────────────────────────
                     C-1b.5 / INV-7 / L139: rework the level-only log into a
                     unified item lifecycle. Merges level changes, waste
                     events, list-add provenance, and synthesises Opened /
                     Checked rows from current state. Date-sorted, newest
                     first; entries colour-keyed by event kind. -->
                <!-- Round-17: q-pl-md so the q-timeline's left-positioned
                     icons aren't flush against the inner panel edge. -->
                <q-tab-panel name="history" class="q-pl-md">
                    <div v-if="lifecycleEvents.length === 0" class="dora-text-muted text-caption q-pa-md">
                        Nothing logged for this item yet — once you change
                        its stock level, add it to a list, mark it open or
                        log waste, it'll show up here.
                    </div>
                    <q-timeline v-else color="primary">
                        <q-timeline-entry
                            v-for="ev in lifecycleEvents"
                            :key="ev.id"
                            :title="ev.title"
                            :subtitle="formatDateTime(ev.at)"
                            :icon="ev.icon"
                            :color="ev.color"
                        >
                            <div v-if="ev.body" class="dora-text-secondary">
                                {{ ev.body }}
                            </div>
                        </q-timeline-entry>
                    </q-timeline>
                    <!-- 2026-06-30 — honest truncation footer. Server caps
                         each event kind at HISTORY_PER_KIND_CAP (50) and
                         reports what got dropped as `history_older_count`.
                         When the number is 0 the footer is silent; the old
                         behaviour was a silent client-side slice(0, 60)
                         which hid arbitrary truncation. -->
                    <div
                        v-if="detail && (detail.history_older_count ?? 0) > 0"
                        class="dora-text-muted text-caption q-pa-md q-pl-none text-center"
                    >
                        {{ detail.history_older_count }} older event{{ (detail.history_older_count ?? 0) === 1 ? '' : 's' }} not shown
                    </div>
                </q-tab-panel>
            </q-tab-panels>
        </div>
        </FadeTransition>

        <!-- ── Set-expiry dialog ──────────────────────────────────────── -->
        <BaseDialog v-model="expiryDialogOpen" title="Set expiry" closable card-style="min-width: 320px">
                <q-card-section>
                    <q-date v-model="expiryDraft" mask="YYYY-MM-DD" />
                </q-card-section>
                <template #actions>
                    <BaseButton variant="danger-ghost" label="Clear" @click="onSetExpiry(null)" />
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton variant="primary" label="Save" :loading="busy" @click="onSetExpiry(expiryDraft)" />
                </template>
        </BaseDialog>

        <!-- ── Add-substitute picker dialog ───────────────────────────── -->
        <BaseDialog v-model="subPickerOpen" title="Add a substitute" closable card-style="width: 560px; max-width: 95vw">
                <q-card-section>
                    <q-input v-model="subSearch" outlined dense autofocus debounce="150" placeholder="Search stock items" clearable>
                        <template #prepend><q-icon :name="ICONS.search" /></template>
                    </q-input>
                </q-card-section>
                <q-card-section class="q-pt-none" style="max-height: 60vh; overflow: auto">
                    <q-list separator>
                        <q-item v-for="si in substituteCandidates" :key="si.stock_item_id" clickable @click="onAddSubstitute(si.stock_item_id)">
                            <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
                            <q-item-section>{{ si.name }}</q-item-section>
                            <q-item-section side><BaseButton variant="icon" :icon="ICONS.add" color="primary" /></q-item-section>
                        </q-item>
                        <q-item v-if="substituteCandidates.length === 0">
                            <q-item-section class="dora-text-muted">No matching items.</q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseDropdown from 'src/components/BaseDropdown.vue';
    import BuyVerdictCard from 'src/components/stock/BuyVerdictCard.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import PantryBeliefChip from 'src/components/stock/PantryBeliefChip.vue';
    import { usePantryBeliefs } from 'src/composables/usePantryBeliefs';
    import { formatMoney } from 'src/composables/useMoney';
    import SubstituteMetadataDialog from 'src/components/stock/SubstituteMetadataDialog.vue';
    import DoraTabs, { type DoraTab } from 'src/components/DoraTabs.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import StoreLogo from 'src/components/StoreLogo.vue';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import TrendSparkline from 'src/components/TrendSparkline.vue';
    import YourPricesWidget from 'src/components/dora/YourPricesWidget.vue';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import { relativeTime } from 'src/helpers/relativeTime';
    import { humaniseWasteReason } from 'src/helpers/wasteReasons';
    import { useBuyVerdict } from 'src/composables/useBuyVerdict';
    import { useBuyVerdictActions } from 'src/composables/useBuyVerdictActions';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { openProductSearch } from 'src/composables/useProductSearchUrl';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { useUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { LocationNode } from 'src/models/location';
    import type { StockGroup } from 'src/models/stockGroup';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import type { Recipe } from 'src/models/recipe';
    import type { LinkedProduct, PreferredBuy, PriceObservation, StockItemDetail, Substitute } from 'src/models/stockItemDetail';
    import type { StockItem } from 'src/models/stockItem';
    import ProductApiService from 'src/services/api/productApiService';
    import { resolveBaseURL, NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useStoresStore } from 'src/stores/storesStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError, toastCaption } from 'src/services/errorHandling/apiErrorHandler';

    const props = defineProps<{ idOverride?: string; embedded?: boolean }>();
    const emit = defineEmits<{
        (e: 'close'): void;
        /** Round-17: emitted when the user clicks a substitute inside the
         *  embedded peek panel. The parent (StockOverview) listens and
         *  switches the peek's id rather than letting the row routerlink
         *  the user out to a full-page view, which breaks the splitter
         *  context. In full-page mode the handler falls back to router. */
        (e: 'open-detail', stockItemId: string): void;
    }>();

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    const stockItemApi = new StockItemApiService();
    const barcodeApi = new BarcodeApiService();
    const productApi = new ProductApiService();
    const stockGroupApi = new StockGroupApiService();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    // inferred belief for this item (shared cache).
    const pantryBeliefs = usePantryBeliefs();
    const belief = computed(() =>
        detail.value ? pantryBeliefs.beliefFor(detail.value.stock_item_id) : null,
    );
    const locationStore = useLocationStore();
    const recipeStore = useRecipeStore();
    const shoppingListStore = useShoppingListStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { recipes } = storeToRefs(recipeStore);

    const actions = useStockItemActions();
    const slActions = useShoppingListActions();
    // shared handlers for the BuyVerdictCard's mark_stocked +
    // remove_from_list actions. Same seams the row card uses.
    const verdictActions = useBuyVerdictActions();

    const stockItemId = computed(() => props.idOverride ?? (route.params.id as string));

    // buy-verdict oracle (row/line badges elsewhere; the full
    // card renders on the overview tab, per FU-437). The composable
    // fetches on mount, caches for 5 min, and yields a computed we can
    // v-if in the template. `.value` at wire time so the string overload
    // fires — the id is stable for the page's lifetime.
    const { verdict: buyVerdict, invalidate: buyVerdictInvalidate } =
        useBuyVerdict(stockItemId.value);

    const detail = ref<StockItemDetail | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const busy = ref(false);

    // ── QR labels (gated by the install-wide scanning flag) ──────────
    const { scanningEnabled } = useScanningEnabled();
    // when `products` is off the Products tab + per-product
    // surfaces disappear entirely; FU-182 owns the app-wide sweep, this
    // page just consumes the flag.
    const { products: productsEnabled } = useFeatureFlags();
    const { moneyEnabled } = useMoneyEnabled();
    const showQrOpen = ref(false);
    const qrSrc = computed(() => {
        const baseUrl = resolveBaseURL();
        // size 512 looks crisp on retina; the dialog box clamps to 256.
        return `${baseUrl}/stock-items/${stockItemId.value}/qr?size=512`;
    });

    function openSingleQrSheet() {
        const baseUrl = resolveBaseURL();
        window.open(
            `${baseUrl}/stock-items/qr/sheet?ids=${stockItemId.value}`,
            '_blank', 'noopener',
        );
    }

    const tab = ref<string>(
        typeof route.query.section === 'string' ? route.query.section : 'overview',
    );
    // if the URL pointed at ?section=products but products
    // is off (or the admin flips it off later), fall back to Overview so
    // we don't strand the user on an invisible tab.
    watch(
        [productsEnabled, tab],
        ([enabled, current]) => {
            if (!enabled && current === 'products') tab.value = 'overview';
        },
        { immediate: true },
    );

    // Full-path location options (e.g. "Pantry › Middle shelf › Left side"),
    // built once from the location tree so the picker reads like the other
    // location pickers — searchable + path-labelled rather than leaf-only.
    type LocationOption = { label: string; value: string };
    const allLocationOptions = computed<LocationOption[]>(() => {
        const out: LocationOption[] = [];
        const walk = (nodes: LocationNode[], prefix: string) => {
            for (const n of nodes) {
                const path = prefix ? `${prefix} › ${n.name}` : n.name;
                out.push({ label: path, value: n.location_id });
                walk(n.children, path);
            }
        };
        walk(locationStore.tree, '');
        return out.sort((a, b) => a.label.localeCompare(b.label));
    });

    // Quasar local-filter pattern: the bound list narrows on type, reset to
    // the full set when the query is cleared.
    const locationOptions = ref<LocationOption[]>([]);
    watch(allLocationOptions, (v) => { locationOptions.value = v; }, { immediate: true });
    function filterLocations(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            locationOptions.value = needle
                ? allLocationOptions.value.filter((o) => o.label.toLowerCase().includes(needle))
                : allLocationOptions.value;
        });
    }

    // ── Inline-edit state (C-1b.1) ──────────────────────────────────────
    // Text rows (name/notes) live in `form` and save on blur if changed;
    // toggles/selects/dates save immediately on change (see handlers
    // below). The Save/Reset coupling from the old 2-col form is gone —
    // each row IS its editor.
    type BasicsForm = {
        name: string;
        notes: string;
        stock_location_id: string | null;
        stock_group_id: string | null;
        usual_store_id: string | null;
    };
    const emptyBasics = (): BasicsForm => ({
        name: '', notes: '', stock_location_id: null, stock_group_id: null,
        usual_store_id: null,
    });
    const form = reactive<BasicsForm>(emptyBasics());

    function hydrateForm(d: StockItemDetail) {
        form.name = d.name;
        form.notes = d.notes ?? '';
        form.stock_location_id = d.stock_location_id;
        form.stock_group_id = d.stock_group_id;
        form.usual_store_id = d.usual_store_id;
    }
    // The unsaved-changes guard now only covers text rows — selects/toggles/
    // dates persist on change, so they can never be "dirty but not saved."
    const isDirty = computed(() => {
        if (!detail.value) return false;
        return (
            form.name.trim() !== detail.value.name ||
            (form.notes ?? '') !== (detail.value.notes ?? '')
        );
    });
    // R-020 — deferred-save surface, must wire the unsaved-changes guard.
    useUnsavedChangesGuard(isDirty);

    // Stock groups — loaded once for the inline picker. (Owned locally
    // rather than via a store; this is the only consumer on this page
    // and the list is small.)
    const stockGroups = ref<StockGroup[]>([]);
    const groupOptions = computed(() =>
        stockGroups.value.map((g) => ({ label: g.name, value: g.stock_group_id })),
    );

    // Stores picker. Hydrate lazily via R-016 ensureLoadedAsync; the
    // store dropdown shows whatever the user has curated under Settings →
    // Stores. Empty list ⇒ the picker reads "no stores set up yet" and the
    // user is invited to add some.
    const storesStore = useStoresStore();
    const storeOptions = computed(() =>
        storesStore.stores.map((s) => ({
            label: s.name,
            value: s.store_id,
            has_image: s.has_image,
        })),
    );
    // resolve the level *sequence* (StockLevelDot maps it to a
    // colour, or the sunken fallback when null). Untracked items (no
    // level_id) get null → muted bg via the component's internal
    // fallback.
    const detailLevelSequence = computed<number | null>(() => {
        const levelId = detail.value?.stock_level_id;
        if (!levelId) return null;
        const seq = stockLevelStore.stockLevels.find((l) => l.stock_level_id === levelId)?.sequence;
        return typeof seq === 'number' ? seq : null;
    });

    // ── Inline-edit field savers (C-1b.1) ───────────────────────────────
    // Each row's editor calls one of these; the partial PATCH already
    // supports per-field updates so we don't need a Save button. Reloads
    // detail to pick up any server-derived state changes (e.g. auto-add
    // hook firing when level transitions).
    type FieldPatch = {
        name?: string;
        notes?: string | null;
        stock_location_id?: string | null;
        stock_group_id?: string | null;
        is_essential?: boolean;
        expiry_date?: string | null;
        usual_store_id?: string | null;
        clear_usual_store?: boolean;
        // Explicit clear flags — see `update_stock_item.py` for why the
        // relationship-only null assignment doesn't dirty the FK column.
        clear_stock_location?: boolean;
        clear_stock_group?: boolean;
    };
    async function saveField(patch: FieldPatch) {
        if (!detail.value) return;
        busy.value = true;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                ...patch,
            });
            await loadDetail();
        } catch (err) {
            notifyErr('Save failed.', err);
        } finally {
            busy.value = false;
        }
    }
    async function saveNameIfDirty() {
        if (!detail.value) return;
        const next = form.name.trim();
        if (!next || next === detail.value.name) return;
        await saveField({ name: next });
    }
    async function saveNotesIfDirty() {
        if (!detail.value) return;
        const next = form.notes ?? '';
        if (next === (detail.value.notes ?? '')) return;
        await saveField({ notes: next.length > 0 ? next : null });
    }
    async function onChangeLocation(value: string | null) {
        if (!detail.value || value === detail.value.stock_location_id) return;
        // Route null through the explicit clear flag — the relationship is
        // mapped `lazy="noload"` so a present-but-null FK can silently
        // no-op server-side, leaving the picker rebounding to its prior
        // value after refresh.
        if (value === null) {
            await saveField({ clear_stock_location: true });
        } else {
            await saveField({ stock_location_id: value });
        }
    }
    async function onClearLocation() {
        if (!detail.value || detail.value.stock_location_id === null) return;
        await saveField({ clear_stock_location: true });
    }
    async function onChangeGroup(value: string | null) {
        if (!detail.value || value === detail.value.stock_group_id) return;
        if (value === null) {
            await saveField({ clear_stock_group: true });
        } else {
            await saveField({ stock_group_id: value });
        }
    }
    async function onClearGroup() {
        if (!detail.value || detail.value.stock_group_id === null) return;
        await saveField({ clear_stock_group: true });
    }
    async function onChangeUsualStore(value: string | null) {
        if (!detail.value || value === detail.value.usual_store_id) return;
        if (value === null) {
            await saveField({ clear_usual_store: true });
        } else {
            await saveField({ usual_store_id: value });
        }
    }
    async function onToggleFlagged(value: boolean) {
        await saveField({ is_essential: value });
    }
    function shiftExpiry(days: number) {
        // From the current expiry if set, otherwise from today. Date math in
        // UTC so DST boundaries don't shift the displayed day.
        const baseISO = detail.value?.expiry_date ?? new Date().toISOString().slice(0, 10);
        const [y, m, d] = baseISO.split('-').map(Number) as [number, number, number];
        const t = new Date(Date.UTC(y, m - 1, d));
        t.setUTCDate(t.getUTCDate() + days);
        void saveField({ expiry_date: t.toISOString().slice(0, 10) });
    }
    function clearExpiry() {
        void saveField({ expiry_date: null });
    }

    // ── Toolbar actions ──────────────────────────────────────────────────
    async function withBusyReload(fn: () => Promise<void>) {
        busy.value = true;
        try {
            await fn();
            await loadDetail();
        } finally {
            busy.value = false;
        }
    }

    // ── Preferred buys (FU-211) — free-text "what I actually buy" reminders.
    // Separate from the Product overlay; always available. Mutations reuse
    // withBusyReload so the list reflects the server after each change.
    // Round-3 feedback: sort alphabetically client-side. The server still
    // stores a `position` for historical compatibility, but the UI never
    // surfaces it — manual reorder buttons are gone.
    const preferredBuys = computed(() => {
        const list = [...(detail.value?.preferred_buys ?? [])];
        list.sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' }));
        return list;
    });
    const newBuyLabel = ref('');
    const editingBuyId = ref<string | null>(null);
    const editingBuyLabel = ref('');

    async function addBuy() {
        const label = newBuyLabel.value.trim();
        if (!label) return;
        await withBusyReload(() => stockItemApi.addPreferredBuyAsync(stockItemId.value, label));
        newBuyLabel.value = '';
    }
    function startBuyRename(pb: PreferredBuy) {
        editingBuyId.value = pb.preferred_buy_id;
        editingBuyLabel.value = pb.label;
    }
    async function saveBuyRename(pb: PreferredBuy) {
        if (editingBuyId.value !== pb.preferred_buy_id) return;
        const label = editingBuyLabel.value.trim();
        editingBuyId.value = null;
        if (!label || label === pb.label) return;
        await withBusyReload(() =>
            stockItemApi.updatePreferredBuyAsync(stockItemId.value, pb.preferred_buy_id, label),
        );
    }
    async function deleteBuy(pb: PreferredBuy) {
        await withBusyReload(() =>
            stockItemApi.deletePreferredBuyAsync(stockItemId.value, pb.preferred_buy_id),
        );
    }

    // ── Prices (FU-227 chunk 3) — YourPricesWidget owns the entry UX via
    // the shared PriceEntry component. This page just exposes the list (with
    // delete) and a submit handler that talks to the API. R-003: server
    // derives per-unit cost; we never divide here.
    const priceObservations = computed(() => detail.value?.price_observations ?? []);

    // Stores list for the optional store picker in PriceEntry (A2). Reuses
    // the existing `storesStore` instance declared above (FU-189 — usual
    // store picker). Lazy-hydration triggered earlier on this page.
    const storesList = computed(() => storesStore.stores);

    async function addObservation(value: {
        total_price: number;
        total_measure: number;
        unit: string;
        store_id: string | null;
        pack_count: number | null;
    }) {
        await withBusyReload(() => stockItemApi.addPriceObservationAsync(stockItemId.value, {
            total_price: value.total_price,
            total_measure: value.total_measure,
            unit: value.unit,
            store_id: value.store_id ?? null,
            pack_count: value.pack_count ?? null,
        }));
    }
    // Multipack (FU-227 follow-up): render "4 × 125g" instead of "500g
    // flat" when the obs carries a pack_count. Per-pack = total/count.
    // Trims trailing zeros so "4 × 125g" reads cleaner than "4 × 125.0g".
    function formatObsMeasure(obs: PriceObservation): string {
        const total = obs.total_measure;
        const unit = obs.unit;
        if (obs.pack_count != null && obs.pack_count > 1) {
            const perPack = total / obs.pack_count;
            return `${obs.pack_count} × ${trimZero(perPack)} ${unit}`;
        }
        return `${trimZero(total)} ${unit}`;
    }
    function trimZero(n: number): string {
        return Number.isInteger(n) ? n.toString() : n.toFixed(2).replace(/\.?0+$/, '');
    }

    async function deleteObservation(obs: PriceObservation) {
        await withBusyReload(() =>
            stockItemApi.deletePriceObservationAsync(stockItemId.value, obs.observation_id),
        );
    }
    async function onToggleOpen() {
        if (!detail.value) return;
        const next = !detail.value.is_open;
        // FU-507 — prompt for an updated effective expiry when marking as
        // opened (default: unchanged). Mirrors StockItemRow.onToggleOpen.
        let expiryPatch: string | null | undefined = undefined;
        if (next) {
            const currentExpiry = detail.value.expiry_date ?? '';
            const picked = await new Promise<string | null | undefined>((resolve) => {
                $q.dialog({
                    title: `Marking "${detail.value!.name}" as open`,
                    message: 'Update its effective expiry? Leave as-is if opening doesn\'t change how fast it goes off.',
                    prompt: {
                        model: currentExpiry,
                        type: 'date',
                        isValid: (v: string) => v === '' || /^\d{4}-\d{2}-\d{2}$/.test(v),
                    },
                    cancel: 'Skip',
                    ok: 'Update expiry',
                })
                    .onOk((val: string) => resolve(val || null))
                    .onCancel(() => resolve(undefined))
                    .onDismiss(() => {});
            });
            if (picked !== undefined && picked !== currentExpiry) {
                expiryPatch = picked;
            }
        }
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({
                stock_item_id: stockItemId.value,
                is_open: next,
                ...(expiryPatch !== undefined ? { expiry_date: expiryPatch } : {}),
            }),
        );
    }
    async function onAddToList() {
        await withBusyReload(() => actions.addToList(stockItemId.value));
        // the verdict's stock-band + open-list state both
        // changed. Invalidate so a re-render fetches a fresh answer.
        buyVerdictInvalidate();
    }
    // closes FU-437 (add_to_list) and FU-454 (mark_stocked +
    // remove_from_list). Delegates to the shared `useBuyVerdictActions`
    // composable so the same math runs from every card mount (row card,
    // detail-page card, shopping-list card).
    async function onBuyVerdictAction(
        kind: 'add_to_list' | 'skip' | 'mark_stocked' | 'remove_from_list' | 'none',
    ) {
        if (kind === 'add_to_list') {
            await onAddToList();  // already invalidates
            return;
        }
        if (kind === 'mark_stocked') {
            const ok = await verdictActions.markStocked(stockItemId.value);
            if (ok) await loadDetail();  // reload so the level chip repaints
            return;
        }
        if (kind === 'remove_from_list') {
            await verdictActions.removeFromAllOpenLists(stockItemId.value);
            return;
        }
        // `skip` / `none` — nothing to do.
    }
    async function onChangeStockLevel(stockLevelId: string) {
        await withBusyReload(() =>
            stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId.value,
                stock_level_id: stockLevelId,
            }),
        );
        // stock band feeds `_need_axis`; drop the cached
        // verdict so the card re-fetches the new answer.
        buyVerdictInvalidate();
        // a manual level change is a fresh hard signal; refresh the
        // belief so the chip reflects "override wins" immediately.
        pantryBeliefs.invalidate();
        void pantryBeliefs.loadAsync(true);
    }

    // ── Expiry ───────────────────────────────────────────────────────────
    const expiryDialogOpen = ref(false);
    const expiryDraft = ref<string | null>(null);
    watch(expiryDialogOpen, (open) => {
        if (open) expiryDraft.value = detail.value?.expiry_date ?? null;
    });
    async function onSetExpiry(value: string | null) {
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({ stock_item_id: stockItemId.value, expiry_date: value }),
        );
        expiryDialogOpen.value = false;
    }

    // ── Linked products ──────────────────────────────────────────────────
    const priceHistory = ref<Map<string, number[]>>(new Map());

    function discountPct(p: LinkedProduct): number | null {
        if (p.price_now == null || p.price_was == null || p.price_was <= 0 || p.price_now >= p.price_was)
            return null;
        return Math.round(((p.price_was - p.price_now) / p.price_was) * 100);
    }

    // Cheapest first, then by name.
    const sortedProducts = computed(() =>
        [...(detail.value?.products ?? [])].sort((a, b) => {
            const priceDiff = (a.price_now ?? Infinity) - (b.price_now ?? Infinity);
            if (priceDiff !== 0) return priceDiff;
            return a.name.localeCompare(b.name);
        }),
    );
    const cheapestProduct = computed<LinkedProduct | null>(() => {
        const withPrice = (detail.value?.products ?? []).filter((p) => p.price_now != null);
        if (withPrice.length === 0) return null;
        return withPrice.reduce((min, p) => (p.price_now! < min.price_now! ? p : min));
    });

    async function loadPriceHistories(products: LinkedProduct[]) {
        const map = new Map<string, number[]>();
        await Promise.all(
            products.map(async (p) => {
                try {
                    const h = await productApi.getPriceHistoryAsync(p.product_id);
                    map.set(
                        p.product_id,
                        h.points.map((pt) => pt.price_now ?? 0).filter((n) => n > 0),
                    );
                } catch {
                    // Sparkline just renders empty if history can't be loaded.
                }
            }),
        );
        priceHistory.value = map;
    }


    // the cheapest product gets a chip + highlight
    // style rather than a separate "Add cheapest" button — each product
    // carries its own Add-to-list.
    function isCheapest(p: LinkedProduct): boolean {
        return cheapestProduct.value?.product_id === p.product_id;
    }

    // Find-deals now lives only inside the Products tab (empty-state CTA +
    // "Link another" when products exist). FU-186 retired the in-app
    // `/product-search` route; both entry points now open the external
    // Product Search companion (or the Features setup page when unset).
    function onFindAndLink() {
        openProductSearch(router);
    }

    async function onAddProductToList(productId: string) {
        const primary = shoppingListStore.quickAddTargetListId;
        busy.value = true;
        try {
            if (primary) {
                await slActions.addItems(primary, [
                    {
                        stock_item_id: stockItemId.value,
                        selected_product_id: productId,
                    },
                ]);
            } else {
                await actions.addToList(stockItemId.value);
            }
        } finally {
            busy.value = false;
        }
    }

    // ── Recipes ──────────────────────────────────────────────────────────
    const recipesForDetail = computed<Recipe[]>(() => {
        const ids = new Set((detail.value?.recipes ?? []).map((r) => r.recipe_id));
        return recipes.value.filter((r) => ids.has(r.recipe_id)) as unknown as Recipe[];
    });
    function goToRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }
    function goToCook(recipeId: string) {
        void router.push(`/cookbook/${recipeId}/cook`);
    }
    async function onAddMissing(_recipeId: string, stockItemIds: string[]) {
        const primary = shoppingListStore.quickAddTargetListId;
        if (!primary) {
            await actions.addToList(stockItemIds[0] ?? stockItemId.value);
            return;
        }
        busy.value = true;
        try {
            await slActions.addItems(primary, stockItemIds.map((id) => ({ stock_item_id: id })));
        } finally {
            busy.value = false;
        }
    }
    // Jump back to the stock overview pre-filtered to the recipe's
    // ingredient set. The query param is read by StockOverview on mount;
    // the filter chip surfaces a removable "Ingredients of: <recipe>"
    // pill so the user can clear it without round-tripping.
    function onFilterStockByRecipe(recipeId: string) {
        void router.push({ path: '/stock', query: { recipe: recipeId } });
    }

    // the favourite toggle on this surface
    // was wired to a dead listener. Mirror RecipesOverview's handler shape
    // (toggle on the recipe store; the card re-renders via the store).
    function onToggleFavourite(recipeId: string) {
        const r = recipes.value.find((x) => x.recipe_id === recipeId);
        if (r) void recipeStore.toggleFavouriteAsync(r as unknown as Recipe);
    }
    // Cookable card → "Add all" pushes every ingredient onto the primary
    // draft. Matches the existing onAddMissing pattern (no picker dialog
    // on this surface — RecipesOverview's richer picker is overkill here).
    async function onAddAllToList(recipeId: string) {
        const recipe = recipes.value.find((r) => r.recipe_id === recipeId);
        if (!recipe || recipe.ingredients.length === 0) return;
        const ids = recipe.ingredients
            .map((ing) => ing.stock_item_id)
            .filter((id): id is string => !!id);
        if (ids.length === 0) return;
        const primary = shoppingListStore.quickAddTargetListId;
        if (!primary) {
            await actions.addToList(ids[0] ?? stockItemId.value);
            return;
        }
        busy.value = true;
        try {
            await slActions.addItems(primary, ids.map((id) => ({ stock_item_id: id })));
        } finally {
            busy.value = false;
        }
    }

    // ── Substitutes ──────────────────────────────────────────────────────
    function stockItemFor(sub: Substitute): StockItem {
        const full = stockItems.value.find((si) => si.stock_item_id === sub.stock_item_id);
        if (full) return full;
        return {
            stock_item_id: sub.stock_item_id,
            name: sub.name,
            stock_level_id: sub.stock_level_id ?? '',
            stock_location_id: null,
            stock_group_id: null,
        };
    }
    const subPickerOpen = ref(false);
    const subSearch = ref('');
    const substituteCandidates = computed(() => {
        const existing = new Set((detail.value?.substitutes ?? []).map((s) => s.stock_item_id));
        const q = subSearch.value.trim().toLowerCase();
        return stockItems.value
            .filter(
                (si) =>
                    si.stock_item_id !== stockItemId.value &&
                    !existing.has(si.stock_item_id) &&
                    (!q || si.name.toLowerCase().includes(q)),
            )
            .slice(0, 30);
    });
    function openSubstitutePicker() {
        subSearch.value = '';
        subPickerOpen.value = true;
    }
    async function onAddSubstitute(substituteId: string) {
        subPickerOpen.value = false;
        await withBusyReload(() => stockItemApi.addSubstituteAsync(stockItemId.value, substituteId));
    }
    async function onRemoveSubstitute(substituteId: string) {
        await withBusyReload(() => stockItemApi.removeSubstituteAsync(stockItemId.value, substituteId));
    }

    // ── FU-034: substitute metadata edit dialog ─────────────────────────
    const substituteMetadataOpen = ref(false);
    const substituteMetadataSaving = ref(false);
    const editingSubstitute = ref<Substitute | null>(null);

    function onEditSubstituteMetadata(sub: Substitute) {
        editingSubstitute.value = sub;
        substituteMetadataOpen.value = true;
    }
    async function onSaveSubstituteMetadata(payload: {
        notes: string | null;
        ratio_quantity_in: number | null;
        ratio_unit_in: string | null;
        ratio_quantity_out: number | null;
        ratio_unit_out: string | null;
    }) {
        const sub = editingSubstitute.value;
        if (!sub) return;
        substituteMetadataSaving.value = true;
        try {
            await withBusyReload(() =>
                stockItemApi.updateSubstituteAsync(
                    stockItemId.value,
                    sub.stock_item_id,
                    payload,
                ),
            );
            substituteMetadataOpen.value = false;
            editingSubstitute.value = null;
        } finally {
            substituteMetadataSaving.value = false;
        }
    }
    /** FU-034 — compact "1 tsp → 1 tsp" caption for the substitute list.
     *  Mirrors the cook-mode swap picker's layout so the user reads the
     *  same shape in both places. Returns null when no ratio is set. */
    function substituteRatioText(sub: Substitute): string | null {
        if (sub.ratio_quantity_in == null || sub.ratio_unit_in == null
            || sub.ratio_quantity_out == null || sub.ratio_unit_out == null) {
            return null;
        }
        const from = formatQuantity(sub.ratio_quantity_in, sub.ratio_unit_in);
        const to = formatQuantity(sub.ratio_quantity_out, sub.ratio_unit_out);
        return `${from} → ${to}`;
    }

    // ── FU-056: barcode add / remove ────────────────────────────────────
    const addBarcodeOpen = ref(false);
    const addBarcodeValue = ref('');
    const addBarcodeError = ref<string | null>(null);
    const addBarcodeSaving = ref(false);

    function onAddBarcodeClick() {
        addBarcodeValue.value = '';
        addBarcodeError.value = null;
        addBarcodeOpen.value = true;
    }
    async function onConfirmAddBarcode() {
        const raw = addBarcodeValue.value.trim();
        if (!raw) return;
        addBarcodeError.value = null;
        addBarcodeSaving.value = true;
        try {
            await withBusyReload(() => barcodeApi.registerAsync({
                barcode: raw,
                stock_item_id: stockItemId.value,
            }).then(() => undefined));
            addBarcodeOpen.value = false;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Barcode added.',
            });
        } catch (err) {
            addBarcodeError.value = describeApiError(err) || 'Could not add barcode.';
        } finally {
            addBarcodeSaving.value = false;
        }
    }
    async function onRemoveBarcode(barcodeId: string) {
        try {
            await withBusyReload(() => barcodeApi.deleteAsync(barcodeId));
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Barcode removed.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove barcode.',
                caption: toastCaption(err),
            });
        }
    }
    /** Click on a substitute row. When the detail page is hosted inside
     *  the splitter peek (embedded mode), emit up so the parent can flip
     *  the peek id in-place — preserves the splitter context. In
     *  full-page mode, fall back to a normal router navigation. */
    function onOpenSubstitute(substituteId: string) {
        if (props.embedded) {
            emit('open-detail', substituteId);
        } else {
            actions.openDetail(substituteId);
        }
    }

    // ── On shopping lists ────────────────────────────────────────────────
    // Round-18: defensively drop any 'done' lists. `unticked_list_ids`
    // shouldn't include finished lists in the first place (items there
    // are ticked off), but the client-side guard means a stray
    // historical id never shows up in the Lists tab as a phantom row.
    const onLists = computed(() => {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === stockItemId.value);
        const ids = entry?.unticked_list_ids ?? [];
        const lookup = new Map((m?.active_lists ?? []).map((l) => [l.shopping_list_id, l]));
        return ids
            .map((lid) => lookup.get(lid) ?? { shopping_list_id: lid, name: lid, status: 'draft' as const })
            .filter((l) => l.status !== 'done');
    });
    // the server-inferred primary draft list (R-003) — the
    // Lists tab decorates that row with a styled "Primary" badge instead
    // of plain text.
    const primaryListId = computed(() => shoppingListStore.quickAddTargetListId ?? null);

    // Tab definitions for DoraTabs — counts re-evaluate as detail loads /
    // mutates. Products tab is gated by the install-wide feature flag.
    const tabDefinitions = computed<DoraTab[]>(() => {
        const d = detail.value;
        const out: DoraTab[] = [{ name: 'overview', label: 'Overview', icon: ICONS.info }];
        if (productsEnabled.value) {
            out.push({ name: 'products', label: `Products (${d?.products.length ?? 0})`, icon: ICONS.local_offer });
        }
        out.push({ name: 'recipes', label: `Recipes (${d?.recipes.length ?? 0})`, icon: ICONS.menu_book });
        out.push({ name: 'substitutes', label: `Substitutes (${d?.substitutes.length ?? 0})`, icon: ICONS.swap_horiz });
        out.push({ name: 'lists', label: `Lists (${onLists.value.length})`, icon: ICONS.shopping_cart });
        out.push({ name: 'history', label: 'History', icon: ICONS.history });
        return out;
    });
    function goToList(listId: string) {
        void router.push(`/shopping-lists/${listId}`);
    }

    // ── Lifecycle timeline (C-1b.5 / INV-7) ─────────────────────────────
    // Merge the per-kind event lists into one date-sorted timeline. Each
    // entry carries its own colour + icon so the user can scan an item's
    // purchase → use → waste → restock loop at a glance (P5).
    type LifecycleEvent = {
        id: string;
        at: string;
        title: string;
        body?: string;
        icon: string;
        color: string;
    };
    const ADDED_VIA_LABELS: Record<string, string> = {
        manual: 'Added manually',
        auto_low_stock: 'Auto-added: low stock',
        auto_essential: 'Auto-added: essential',
        auto_flagged: 'Auto-added: essential',
        auto_recipe: 'Auto-added from a recipe',
        auto_meal_plan: 'Auto-added from meal plan',
        auto_frequently_added: 'Auto-added: frequently added',
    };
    function humaniseAddedVia(via: string): string {
        return ADDED_VIA_LABELS[via] ?? 'Added to a list';
    }
    const lifecycleEvents = computed<LifecycleEvent[]>(() => {
        const d = detail.value;
        if (!d) return [];
        const out: LifecycleEvent[] = [];

        // Level history — newest level at top of `level_history` already.
        // Walk *forwards in time* (older→newer) so we can infer "restocked"
        // vs "dropped to X" by comparing to the previous level name.
        const levels = [...d.level_history].sort(
            (a, b) => new Date(a.changed_at).getTime() - new Date(b.changed_at).getTime(),
        );
        for (let i = 0; i < levels.length; i++) {
            const cur = levels[i]!;
            const prev = i > 0 ? levels[i - 1] : null;
            const name = cur.stock_level_name ?? 'Level changed';
            let title = `Level → ${name}`;
            if (prev && prev.stock_level_name && cur.stock_level_name) {
                // Cheap heuristic: any move from Low/Out → not-Low/Out reads as
                // "restocked"; the opposite reads as "dropped to X". Otherwise
                // just show the destination.
                const wasShort = /^(low|out)/i.test(prev.stock_level_name);
                const nowShort = /^(low|out)/i.test(cur.stock_level_name);
                if (wasShort && !nowShort) title = `Restocked → ${name}`;
                else if (!wasShort && nowShort) title = `Dropped to ${name}`;
            }
            out.push({
                id: `level-${cur.changed_at}-${i}`,
                at: cur.changed_at,
                title,
                icon: ICONS.refresh,
                color: 'primary',
            });
        }

        // Waste events. C-waste slim: reason-only — no quantity / value /
        // note. The timeline entry is a single line.
        for (const w of d.waste_events ?? []) {
            const reason = humaniseWasteReason(w.reason);
            out.push({
                id: `waste-${w.occurred_at}-${reason}`,
                at: w.occurred_at,
                title: `Wasted: ${reason}`,
                icon: ICONS.delete_outline,
                color: 'negative',
            });
        }

        // Past list-adds — list name + provenance ("auto: low stock").
        for (const a of d.recent_list_adds ?? []) {
            out.push({
                id: `add-${a.added_at}-${a.shopping_list_id}`,
                at: a.added_at,
                title: `${humaniseAddedVia(a.added_via)} → ${a.shopping_list_name}`,
                icon: ICONS.shopping_cart,
                color: 'accent',
            });
        }

        // Purchase events (2026-06-30) — every ticked line on a
        // finished shopping list. Answers "when did I last actually
        // buy this and for how much?" — a question the list-add
        // entries can't. Price + store are both optional; render
        // whichever the /finish flow captured.
        for (const p of d.purchase_events ?? []) {
            const bits: string[] = [];
            if (p.quantity && p.quantity !== 1) bits.push(`${p.quantity}×`);
            if (p.actual_unit_price != null) {
                bits.push(`${formatMoney(p.actual_unit_price)}${p.quantity > 1 ? '/ea' : ''}`);
            }
            if (p.store_name) bits.push(`at ${p.store_name}`);
            const entry: LifecycleEvent = {
                id: `bought-${p.occurred_at}-${p.shopping_list_id}`,
                at: p.occurred_at,
                title: `Bought · ${p.shopping_list_name}`,
                icon: ICONS.shopping_bag,
                // was 'teal-8'; now theme-aware via --lifecycle-bought.
                color: 'lifecycle-bought',
            };
            if (bits.length > 0) entry.body = bits.join(' · ');
            out.push(entry);
        }

        // Cook events (2026-06-30) — every recipe you cooked that
        // uses this ingredient. `meals_cooked > 1` badges the entry
        // as a batch cook. Recipe id may be null (SET NULL on delete);
        // denormalised name still renders.
        for (const c of d.cook_events ?? []) {
            const badge = c.meals_cooked > 1 ? ` · ${c.meals_cooked} meals` : '';
            out.push({
                id: `cook-${c.occurred_at}-${c.recipe_id ?? 'unknown'}`,
                at: c.occurred_at,
                title: `Used in ${c.recipe_name}${badge}`,
                icon: ICONS.local_fire_department,
                // was 'deep-orange-6'; reuses the severity-high
                // token (same visual weight as the essential-low alert kind).
                color: 'severity-high',
            });
        }

        // Expiry events (2026-06-30) — set / pushed / cleared trail.
        // Repeat pushes tell the user "this is stale in your fridge".
        for (const e of d.expiry_events ?? []) {
            let title: string;
            let body: string | null = null;
            let color: string;
            const fmt = (iso: string | null) => (iso ? iso : '—');
            if (e.kind === 'cleared') {
                title = 'Cleared expiry';
                body = e.previous_expiry_date
                    ? `Was ${fmt(e.previous_expiry_date)}`
                    : null;
                // was 'grey-7'; theme-aware --lifecycle-cleared
                // (a muted neutral, distinct from severity-*). Cleared
                // is a "wound-down" state, not part of the severity ladder.
                color = 'lifecycle-cleared';
            } else if (e.kind === 'pushed') {
                const delta = e.delta_days ?? 0;
                title = delta >= 0 ? `Pushed expiry +${delta} day${delta === 1 ? '' : 's'}`
                                   : `Expiry moved ${delta} day${delta === -1 ? '' : 's'}`;
                body = `${fmt(e.previous_expiry_date)} → ${fmt(e.new_expiry_date)}`;
                // was 'orange-8'; theme-aware --lifecycle-expiry-changed.
                color = 'lifecycle-expiry-changed';
            } else {
                title = 'Set expiry';
                body = e.new_expiry_date;
                color = 'lifecycle-expiry-changed';
            }
            const entry: LifecycleEvent = {
                id: `expiry-${e.occurred_at}-${e.kind}`,
                at: e.occurred_at,
                title,
                icon: ICONS.event,
                color,
            };
            if (body) entry.body = body;
            out.push(entry);
        }

        // Synthetic "Opened" — single entry derived from current state.
        // opened_on is a date; widen to start-of-day for ordering.
        if (d.is_open && d.opened_on) {
            out.push({
                id: `opened-${d.opened_on}`,
                at: `${d.opened_on}T00:00:00`,
                title: 'Opened',
                icon: 'lock_open',
                // was 'amber-9'; reuses the --severity-attention
                // token (same visual weight as the AddToList "on multiple
                // lists" hint — both grabby-but-not-urgent).
                color: 'severity-attention',
            });
        }

        // Synthetic "Checked" — only if last_checked_at differs from the
        // most recent level change (otherwise it's the same event).
        const lastLevelAt = levels.length > 0
            ? levels[levels.length - 1]!.changed_at
            : null;
        if (d.last_checked_at && d.last_checked_at !== lastLevelAt) {
            out.push({
                id: `checked-${d.last_checked_at}`,
                at: d.last_checked_at,
                title: 'Checked (still correct)',
                icon: ICONS.event,
                color: 'positive',
            });
        }

        // Sort newest first. Truncation is server-owned now (per-kind
        // cap in get_stock_item_detail.py, reported via
        // `history_older_count`); we render everything the server
        // sends and surface the drop count in the timeline footer.
        out.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
        return out;
    });

    // ── Unlink products ──────────────────────────────────────────────────
    // The saved-products picker dialog was retired; the Find-&-link CTA
    // opens the external Product Search companion (FU-186), and products are
    // linked back from the My Products "Link to stock item…" dialog.
    async function onUnlink(productId: string) {
        await withBusyReload(() => stockItemApi.unlinkProductAsync(stockItemId.value, productId));
    }

    // ── Delete ───────────────────────────────────────────────────────────
    function confirmDelete() {
        if (!detail.value) return;
        const item = detail.value;
        $q.dialog({
            title: 'Delete stock item',
            message: `Delete "${item.name}"?`,
            cancel: true,
        }).onOk(() => void doDelete(item.stock_item_id));
    }
    async function doDelete(id: string) {
        try {
            await stockItemStore.deleteStockItemAsync(id);
            // The item is gone — drop the form's reference so the
            // unsaved-changes guard (FU-156) doesn't prompt about edits
            // to a now-deleted row on the way out.
            detail.value = null;
            if (props.embedded) emit('close');
            else void router.push('/stock');
        } catch (err) {
            // backend refuses delete when the item is still on a recipe,
            // returning 422 with a structured `blocked_by_recipes` list.
            // Surface the recipe names in a dialog rather than a vague toast
            // so the user knows where to act.
            if (err instanceof NormalisedApiError) {
                const blocked = err.details?.blocked_by_recipes;
                if (Array.isArray(blocked) && blocked.length > 0) {
                    const lines = (blocked as Array<{ name: string }>)
                        .map((r) => `<li>${r.name}</li>`)
                        .join('');
                    $q.dialog({
                        title: 'Still used by recipes',
                        message:
                            `<p>Can't delete this stock item — it's an ingredient on ${blocked.length} recipe(s):</p>` +
                            `<ul>${lines}</ul>` +
                            `<p>Remove it from those recipes first, then try again.</p>`,
                        html: true,
                        ok: { label: 'OK', flat: true },
                    });
                    return;
                }
            }
            notifyErr('Could not delete this stock item.', err);
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────
    function notifyErr(message: string, err: unknown) {
        $q.notify({ type: 'negative', position: 'bottom-right', message, caption: toastCaption(err) });
    }
    function formatDateTime(iso: string): string {
        if (!iso) return '';
        return new Date(iso).toLocaleString();
    }
    // relativeTime extracted to src/helpers/relativeTime.ts (R-003) — see
    // imports at the top of the script block.

    function goBack() {
        if (window.history.length > 1) router.back();
        else void router.push('/stock');
    }

    async function loadDetail() {
        loading.value = true;
        loadError.value = null;
        try {
            const d = await stockItemApi.getDetailAsync(stockItemId.value);
            detail.value = d;
            hydrateForm(d);
            void loadPriceHistories(d.products);
            // Membership feeds the "on lists" tab and chips.
            void shoppingListStore.refreshAsync();
        } catch (err) {
            loadError.value = 'Could not load this stock item.';
            console.warn('stock-item detail load failed', err);
        } finally {
            loading.value = false;
        }
    }

    watch(stockItemId, () => {
        if (stockItemId.value) void loadDetail();
    });

    // when the row's expiry / open / flag / level toggles fire
    // while this page is open as a peek, the store's StockItem updates
    // but `detail.value` (loaded as a one-shot) goes stale. Sync the
    // handful of fields the row can mutate from the store version onto
    // detail.value so the peek reflects external edits without a
    // refresh. The store always re-fetches the canonical row after a
    // mutation (stockItemStore.updateStockItemAsync /
    // updateStockLevelAsync), so the assignments here are authoritative.
    // Self-triggered edits on the detail page also flow through the
    // store, but the value already matches by the time the watcher
    // fires — the assignment is a no-op, not a loop.
    const storeItem = computed(() =>
        stockItems.value.find((si) => si.stock_item_id === stockItemId.value) ?? null,
    );
    watch(storeItem, (si) => {
        if (!si || !detail.value || detail.value.stock_item_id !== si.stock_item_id) return;
        if (si.expiry_date !== undefined && si.expiry_date !== detail.value.expiry_date) {
            detail.value.expiry_date = si.expiry_date;
        }
        if (si.is_open !== undefined && si.is_open !== detail.value.is_open) {
            detail.value.is_open = si.is_open;
        }
        if (si.opened_on !== undefined && si.opened_on !== detail.value.opened_on) {
            detail.value.opened_on = si.opened_on;
        }
        if (si.is_essential !== undefined && si.is_essential !== detail.value.is_essential) {
            detail.value.is_essential = si.is_essential;
        }
        if (si.stock_level_id && si.stock_level_id !== detail.value.stock_level_id) {
            detail.value.stock_level_id = si.stock_level_id;
        }
        if (si.stock_level_name !== undefined && si.stock_level_name !== detail.value.stock_level_name) {
            detail.value.stock_level_name = si.stock_level_name;
        }
    }, { deep: true });

    onMounted(async () => {
        // Stock groups are page-local (only consumer); load alongside the
        // other dropdowns so the inline picker has options on first paint.
        void stockGroupApi.getAllAsync().then((g) => { stockGroups.value = g; });
        // populate the usual-store picker. R-016 ensureLoaded.
        void storesStore.ensureLoadedAsync();
        await Promise.all([
            stockLevelStore.ensureLoadedAsync(),
            locationStore.ensureLoadedAsync(),
            stockItemStore.ensureLoadedAsync(),
            recipeStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
            // load inferred beliefs (shared cache; idempotent when
            // the overview already loaded them).
            pantryBeliefs.loadAsync(),
        ]);
        await loadDetail();
    });
</script>

<style scoped>
    .strike {
        text-decoration: line-through;
    }
    /* C-1b.3 — emphasise the cheapest linked product per §2.4 (style, not a
       separate "Add cheapest" button). Subtle outline + tinted background
       via the brand-primary token so it follows the active theme. */
    .dora-product-card--cheapest {
        border-color: var(--brand-primary) !important;
        background: color-mix(in srgb, var(--brand-primary) 8%, transparent);
    }

    /* Round-13: the level picker's `outline` prop drew the border in
       `currentColor` (full-strength text) which read as a glaring
       bright-white box against the other softer outlined inputs on the
       page. Switched to `flat` + this custom border that mirrors the
       q-field--outlined treatment (muted text-tint, primary on
       focus-within) so the picker sits visually alongside the other
       fields. */
    .dora-level-picker {
        border: 1px solid color-mix(in srgb, var(--text-primary) 22%, transparent);
        border-radius: 4px;
        transition: border-color 0.2s ease;
    }
    .dora-level-picker:hover,
    .dora-level-picker:focus-within {
        border-color: var(--brand-primary);
    }

    /* Feedback 2026-08-08: recipe cards reflow by column count rather than
       stretching within a Quasar breakpoint grid. auto-fill keeps each card
       within a bounded width band and drops/adds a whole column on resize. */
    .stock-detail__recipe-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 16px;
    }
</style>
