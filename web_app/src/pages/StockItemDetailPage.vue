<template>
    <div :class="embedded ? 'q-pa-sm' : 'q-pa-md'">
        <!-- Header — back/close · name · level (chip = editor) · Delete top-right.
             C-1b.1 (L121): level lives once, in the header. C-1b.1 (L122):
             Delete moves out of the toolbar to a destructive top-right slot. -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <BaseButton v-if="!embedded" variant="icon" :icon="ICONS.arrow_back" @click="goBack" />
            <BaseButton v-else variant="icon" :icon="ICONS.close" @click="emit('close')">
                <q-tooltip>Close panel</q-tooltip>
            </BaseButton>
            <div class="text-h5 q-mr-sm" style="min-width: 160px">
                <AppSkeleton v-if="loading && !detail" type="line" width="180px" height="1.6rem" />
                <template v-else>{{ detail?.name || 'Stock item' }}</template>
            </div>
            <q-btn-dropdown
                v-if="detail"
                outline
                dense
                no-caps
                :color="getStockLevelColour(detail.stock_level_name ?? 'Well-Stocked')"
                :label="detail.stock_level_name ?? 'Set level'"
            >
                <q-list dense>
                    <q-item
                        v-for="level in stockLevelStore.stockLevels"
                        :key="level.stock_level_id"
                        clickable
                        v-close-popup
                        @click="onChangeStockLevel(level.stock_level_id)"
                    >
                        <q-item-section avatar>
                            <q-avatar :color="getStockLevelColour(level.name)" size="16px" />
                        </q-item-section>
                        <q-item-section>{{ level.name }}</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
            <q-space />
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
            <!-- Toolbar — C-1b.1 (L123, L125): pared to Mark open · Set expiry ·
                 Add-to-list · (Show QR). Restock belongs to list-finalisation,
                 not here. Find-deals moves to the Products tab in C-1b.3. -->
            <div class="row q-gutter-sm q-mb-md items-center">
                <BaseButton
                    variant="secondary"
                    :icon="detail.is_open ? 'lock_open' : 'lock'"
                    :label="detail.is_open ? 'Opened' : 'Mark open'"
                    :loading="busy"
                    @click="onToggleOpen"
                />
                <BaseButton variant="secondary" :icon="ICONS.event" label="Set expiry" @click="expiryDialogOpen = true" />
                <AddToListButton
                    v-if="detail"
                    variant="toolbar"
                    :stock-item-id="detail.stock_item_id"
                />
                <q-space />
                <BaseButton
                    v-if="scanningEnabled"
                    variant="secondary"
                    icon="qr_code_2"
                    label="Show QR"
                    @click="showQrOpen = true"
                >
                    <q-tooltip max-width="280px">
                        Prints Dora's own label for this item — a scannable QR
                        that opens this page. It's *not* the product's real
                        EAN/UPC barcode (that's managed on Data → Barcodes and
                        links a barcode to a Product, not a stock item).
                    </q-tooltip>
                </BaseButton>
            </div>

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

            <!-- L120 / R-002: route tab colours through theme tokens so the
                 active tab + indicator stay legible in every theme. -->
            <q-tabs
                v-model="tab"
                dense
                align="left"
                class="text-primary q-mb-sm"
                active-color="primary"
                indicator-color="primary"
                no-caps
            >
                <q-tab name="overview" :icon="ICONS.info" label="Overview" />
                <q-tab v-if="productsEnabled" name="products" :icon="ICONS.local_offer" :label="`Products (${detail.products.length})`" />
                <q-tab name="recipes" :icon="ICONS.menu_book" :label="`Recipes (${detail.recipes.length})`" />
                <q-tab name="substitutes" :icon="ICONS.swap_horiz" :label="`Substitutes (${detail.substitutes.length})`" />
                <q-tab name="lists" :icon="ICONS.shopping_cart" :label="`Lists (${onLists.length})`" />
                <q-tab name="history" :icon="ICONS.history" label="History" />
            </q-tabs>
            <q-separator />

            <q-tab-panels v-model="tab" animated>
                <!-- ── Overview ───────────────────────────────────────────
                     C-1b.1: single-column inline-edit fact list. Each row
                     IS its editor; toggles/selects/dates save immediately
                     on change, text rows save on blur. No separate q-form
                     + Save/Reset (the old 2-col "facts | edit form" split
                     is what L127 called "messy"). Level dedupe (L121): the
                     header chip is the only level editor.
                -->
                <q-tab-panel name="overview" class="q-pa-none q-pt-md">
                    <div class="row q-col-gutter-md items-start">
                        <div class="col-12 col-sm-5 col-md-4">
                            <ImageUploadField
                                :preview-url="imagePreviewUrl"
                                :name="detail?.name"
                                :alt="detail?.name ?? 'Stock item image'"
                                :can-clear="!!pendingImage || !!detail?.has_own_image"
                                @pick="onPickImage"
                                @clear="onClearImage"
                            />
                        </div>
                        <div class="col-12 col-sm-7 col-md-8">
                            <q-list separator class="dora-inline-edit">
                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Name</q-item-section>
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

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Location</q-item-section>
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
                                            placeholder="Not set"
                                            @filter="filterLocations"
                                            @update:model-value="onChangeLocation"
                                        />
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Stock group</q-item-section>
                                    <q-item-section>
                                        <q-select
                                            v-model="form.stock_group_id"
                                            :options="groupOptions"
                                            emit-value
                                            map-options
                                            clearable
                                            dense
                                            borderless
                                            placeholder="Not set"
                                            @update:model-value="onChangeGroup"
                                        />
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Expiry</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-xs">
                                            <span class="dora-text-primary">
                                                {{ detail.expiry_date || 'Not set' }}
                                            </span>
                                            <q-space />
                                            <q-btn flat dense no-caps size="sm" label="+1d" :disable="busy" @click="shiftExpiry(1)" />
                                            <q-btn flat dense no-caps size="sm" label="+7d" :disable="busy" @click="shiftExpiry(7)" />
                                            <q-btn flat dense no-caps size="sm" label="+14d" :disable="busy" @click="shiftExpiry(14)" />
                                            <q-btn flat dense no-caps size="sm" :icon="ICONS.event" @click="expiryDialogOpen = true">
                                                <q-tooltip>Pick a date</q-tooltip>
                                            </q-btn>
                                            <q-btn
                                                v-if="detail.expiry_date"
                                                flat
                                                dense
                                                round
                                                size="sm"
                                                :icon="ICONS.close"
                                                color="negative"
                                                :disable="busy"
                                                @click="clearExpiry"
                                            >
                                                <q-tooltip>Clear expiry</q-tooltip>
                                            </q-btn>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Open / in-use</q-item-section>
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
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Essential</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-sm">
                                            <q-toggle
                                                :model-value="detail.is_flagged"
                                                :disable="busy"
                                                @update:model-value="onToggleFlagged"
                                            />
                                            <q-icon :name="ICONS.info_outline" size="16px" class="dora-text-secondary">
                                                <q-tooltip max-width="320px">
                                                    Flagged items show up in
                                                    "essentials" auto-generate
                                                    sources even when they're
                                                    well-stocked. Different
                                                    from auto-add: this one
                                                    only matters when you run
                                                    auto-generate, not on
                                                    every stock change.
                                                </q-tooltip>
                                            </q-icon>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Auto-add when low</q-item-section>
                                    <q-item-section>
                                        <div class="row items-center q-gutter-sm">
                                            <q-toggle
                                                :model-value="detail.auto_add_when_low"
                                                :disable="busy"
                                                @update:model-value="onToggleAutoAdd"
                                            />
                                            <q-icon :name="ICONS.info_outline" size="16px" class="dora-text-secondary">
                                                <q-tooltip max-width="320px">
                                                    Drops this item onto your
                                                    primary shopping list the
                                                    moment its level falls to
                                                    Low or Out — silent, with
                                                    an undoable toast. Use for
                                                    essentials you never want
                                                    to run out of.
                                                </q-tooltip>
                                            </q-icon>
                                        </div>
                                    </q-item-section>
                                </q-item>

                                <q-item>
                                    <q-item-section class="dora-text-secondary" style="max-width:160px">Level updated</q-item-section>
                                    <q-item-section class="dora-text-primary">
                                        {{ relativeTime(detail.stock_level_last_updated) }}
                                    </q-item-section>
                                </q-item>
                            </q-list>

                            <!-- Notes — calm/secondary (L129). Kept because
                                 it's cheap and occasionally useful; not a
                                 headline. Save on blur. -->
                            <div class="q-mt-md dora-text-secondary text-caption q-mb-xs">Notes</div>
                            <q-input
                                v-model="form.notes"
                                outlined
                                dense
                                type="textarea"
                                autogrow
                                placeholder="Anything you want to remember about this item"
                                class="dora-notes-calm"
                                @blur="saveNotesIfDirty"
                            />
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
                            <!-- C-1b.3: cheapest card carries a "Cheapest"
                                 chip + a subtle highlight class so the
                                 cheaper option pops without needing a
                                 separate "Add cheapest" button (§2.4). -->
                            <q-card
                                bordered
                                flat
                                :class="{ 'dora-product-card--cheapest': isCheapest(prod) }"
                            >
                                <q-card-section class="row items-center no-wrap q-pb-xs">
                                    <MerchantLogo :name="prod.merchant_name" :height="20" :width="34" class="q-mr-sm" />
                                    <div class="col">
                                        <div class="ellipsis text-weight-medium">{{ prod.name }}</div>
                                        <div class="text-caption dora-text-muted">
                                            {{ prod.merchant_name }}
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
                                            ${{ prod.price_now.toFixed(2) }}
                                        </span>
                                        <span
                                            v-if="prod.price_was !== null && prod.price_now !== null && prod.price_was > prod.price_now"
                                            class="text-caption dora-text-muted strike q-ml-xs"
                                        >
                                            ${{ prod.price_was.toFixed(2) }}
                                        </span>
                                    </div>
                                    <q-space />
                                    <TrendSparkline :values="priceHistory.get(prod.product_id) ?? []" />
                                </q-card-section>

                                <q-separator />
                                <q-card-actions align="right">
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        :icon="ICONS.add_shopping_cart"
                                        label="Add to list"
                                        color="primary"
                                        :loading="busy"
                                        @click="onAddProductToList(prod.product_id)"
                                    />
                                    <q-btn
                                        v-if="prod.web_url"
                                        flat
                                        dense
                                        round
                                        :icon="ICONS.open_in_new"
                                        :href="prod.web_url"
                                        target="_blank"
                                        rel="noopener"
                                    >
                                        <q-tooltip>Open on {{ prod.merchant_name }}</q-tooltip>
                                    </q-btn>
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
                    <div v-else class="row q-col-gutter-md">
                        <div
                            v-for="r in recipesForDetail"
                            :key="r.recipe_id"
                            class="col-12 col-sm-6 col-md-4"
                        >
                            <!-- C-1b.4 / FU-185 / B8 residue: wire the
                                 favourite-toggle + add-all-to-list events
                                 RecipeCard emits. Previously dropped, so
                                 "remove from favourites does nothing" and
                                 "every recipe action except Cook is dead"
                                 (feedback L132 / L134) were live defects
                                 on this surface. -->
                            <RecipeCard
                                :recipe="r"
                                :highlight-stock-item-ids="[detail.stock_item_id]"
                                @open="goToRecipe"
                                @cook="goToCook"
                                @toggle-favourite="onToggleFavourite"
                                @add-missing="onAddMissing"
                                @add-all-to-list="onAddAllToList"
                            />
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Substitutes ────────────────────────────────────── -->
                <q-tab-panel name="substitutes">
                    <div class="row items-center q-mb-sm">
                        <div class="text-subtitle1">Substitutes</div>
                        <q-space />
                        <q-btn color="primary" dense no-caps :icon="ICONS.add" label="Add substitute" @click="openSubstitutePicker" />
                    </div>

                    <div v-if="detail.substitutes.length === 0" class="dora-text-muted text-caption q-pa-md">
                        No substitutes yet. Add items that can stand in for this one.
                    </div>

                    <q-list v-else separator>
                        <q-item v-for="sub in detail.substitutes" :key="sub.stock_item_id">
                            <q-item-section>
                                <!-- UX-v2: StockItemChip retired — plain
                                     name-link + level dot; the substitute's
                                     own page has everything else. -->
                                <div class="row items-center q-gutter-x-sm no-wrap">
                                    <a
                                        class="text-primary cursor-pointer text-body2"
                                        @click="actions.openDetail(sub.stock_item_id)"
                                    >
                                        {{ stockItemFor(sub).name }}
                                    </a>
                                    <StockLevelDot :stock-item="stockItemFor(sub)" />
                                </div>
                            </q-item-section>
                            <!-- C-1b.4 (L136): the "Swap into list" affordance
                                 moves to Shop Mode (INV-8) — the moment a
                                 substitute swap actually makes sense is when
                                 you're at the shelf and the original is out,
                                 not when browsing the substitute roster.
                                 Removed from this surface; the per-item
                                 substitutes list itself stays (L137). -->
                            <q-item-section side>
                                <BaseButton variant="icon" :icon="ICONS.link_off" class="text-negative" @click="onRemoveSubstitute(sub.stock_item_id)">
                                    <q-tooltip>Remove substitute</q-tooltip>
                                </BaseButton>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-tab-panel>

                <!-- ── On shopping lists ──────────────────────────────── -->
                <q-tab-panel name="lists">
                    <div v-if="onLists.length === 0" class="dora-text-muted text-caption q-pa-md">
                        Not on any active shopping list.
                        <q-btn flat dense no-caps color="primary" label="Add to primary" @click="onAddToList" />
                    </div>
                    <!-- C-1b.4 (L138): rows already navigate to the list,
                         so the inert open_in_new arrow on the right was
                         decoration only — gone. "(primary)" is now a real
                         styled badge instead of plain text, surfacing the
                         inferred primary draft from the shopping-list
                         membership (R-003 — server decides primary). -->
                    <q-list v-else separator>
                        <q-item
                            v-for="l in onLists"
                            :key="l.shopping_list_id"
                            clickable
                            @click="goToList(l.shopping_list_id)"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.shopping_cart" /></q-item-section>
                            <q-item-section>
                                <div class="row items-center q-gutter-sm">
                                    <span>{{ l.name }}</span>
                                    <q-badge
                                        v-if="l.shopping_list_id === primaryListId"
                                        color="primary"
                                        text-color="white"
                                        label="Primary"
                                    />
                                </div>
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
                <q-tab-panel name="history">
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
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn color="primary" no-caps label="Save" :loading="busy" @click="onSetExpiry(expiryDraft)" />
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
                            <q-item-section side><q-btn flat round dense :icon="ICONS.add" color="primary" /></q-item-section>
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
    import AddToListButton from 'src/components/AddToListButton.vue';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import MerchantLogo from 'src/components/MerchantLogo.vue';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import TrendSparkline from 'src/components/TrendSparkline.vue';
    import StockLevelDot from 'src/components/StockLevelDot.vue';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { useUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { LocationNode } from 'src/models/location';
    import type { StockGroup } from 'src/models/stockGroup';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import type { Recipe } from 'src/models/recipe';
    import type { LinkedProduct, StockItemDetail, Substitute } from 'src/models/stockItemDetail';
    import type { StockItem } from 'src/models/stockItem';
    import ProductApiService from 'src/services/api/productApiService';
    import { resolveBaseURL, NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import StockItemApiService, { stockItemImageUrl } from 'src/services/api/stockItemApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useLocationStore } from 'src/stores/locationStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const props = defineProps<{ idOverride?: string; embedded?: boolean }>();
    const emit = defineEmits<{ (e: 'close'): void }>();

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    const stockItemApi = new StockItemApiService();
    const productApi = new ProductApiService();
    const stockGroupApi = new StockGroupApiService();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const locationStore = useLocationStore();
    const recipeStore = useRecipeStore();
    const shoppingListStore = useShoppingListStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { recipes } = storeToRefs(recipeStore);

    const actions = useStockItemActions();
    const slActions = useShoppingListActions();

    const stockItemId = computed(() => props.idOverride ?? (route.params.id as string));

    const detail = ref<StockItemDetail | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const busy = ref(false);

    // ── QR labels (gated by the install-wide scanning flag) ──────────
    const { scanningEnabled } = useScanningEnabled();
    // C-1b.3 (§2.5): when `products` is off the Products tab + per-product
    // surfaces disappear entirely; FU-182 owns the app-wide sweep, this
    // page just consumes the flag.
    const { products: productsEnabled } = useFeatureFlags();
    const showQrOpen = ref(false);
    const qrSrc = computed(() => {
        const baseUrl = resolveBaseURL('dora');
        // size 512 looks crisp on retina; the dialog box clamps to 256.
        return `${baseUrl}/stock-items/${stockItemId.value}/qr?size=512`;
    });

    function openSingleQrSheet() {
        const baseUrl = resolveBaseURL('dora');
        window.open(
            `${baseUrl}/stock-items/qr/sheet?ids=${stockItemId.value}`,
            '_blank', 'noopener',
        );
    }

    const tab = ref<string>(
        typeof route.query.section === 'string' ? route.query.section : 'overview',
    );
    // C-1b.3 (§2.5): if the URL pointed at ?section=products but products
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
    };
    const emptyBasics = (): BasicsForm => ({
        name: '', notes: '', stock_location_id: null, stock_group_id: null,
    });
    const form = reactive<BasicsForm>(emptyBasics());

    function hydrateForm(d: StockItemDetail) {
        form.name = d.name;
        form.notes = d.notes ?? '';
        form.stock_location_id = d.stock_location_id;
        form.stock_group_id = d.stock_group_id;
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
    useUnsavedChangesGuard(isDirty);

    // Stock groups — loaded once for the inline picker. (Owned locally
    // rather than via a store; this is the only consumer on this page
    // and the list is small.)
    const stockGroups = ref<StockGroup[]>([]);
    const groupOptions = computed(() =>
        stockGroups.value.map((g) => ({ label: g.name, value: g.stock_group_id })),
    );
    // ── Image (C-1 Chunk 6 / FU-033) ────────────────────────────────────
    // Saves immediately — uploading a photo isn't coupled to the basics
    // form's Save button. Cache-bust is owned by the store now (FU-125
    // `imageVersionOf`) so a save here reactively refreshes every row /
    // surface displaying the same item, not just this detail page.
    const pendingImage = ref<string | null>(null);
    const imageCleared = ref(false);
    const imagePreviewUrl = computed<string | null>(() => {
        if (pendingImage.value) return pendingImage.value;
        if (imageCleared.value) return null;
        if (!detail.value?.has_image) return null;
        return stockItemImageUrl(
            detail.value.stock_item_id,
            stockItemStore.imageVersionOf(detail.value.stock_item_id),
        );
    });
    async function onPickImage(dataUrl: string) {
        if (!detail.value) return;
        pendingImage.value = dataUrl;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                image: dataUrl,
            });
            imageCleared.value = false;
            pendingImage.value = null;
            await loadDetail();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Image updated.' });
        } catch (err) {
            pendingImage.value = null;
            notifyErr('Could not save image.', err);
        }
    }
    async function onClearImage() {
        if (!detail.value) return;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                image: null,
            });
            imageCleared.value = true;
            await loadDetail();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Image removed.' });
        } catch (err) {
            notifyErr('Could not remove image.', err);
        }
    }

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
        is_flagged?: boolean;
        auto_add_when_low?: boolean;
        expiry_date?: string | null;
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
        await saveField({ stock_location_id: value });
    }
    async function onChangeGroup(value: string | null) {
        if (!detail.value || value === detail.value.stock_group_id) return;
        await saveField({ stock_group_id: value });
    }
    async function onToggleFlagged(value: boolean) {
        await saveField({ is_flagged: value });
    }
    async function onToggleAutoAdd(value: boolean) {
        await saveField({ auto_add_when_low: value });
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
    async function onToggleOpen() {
        if (!detail.value) return;
        const next = !detail.value.is_open;
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({ stock_item_id: stockItemId.value, is_open: next }),
        );
    }
    async function onAddToList() {
        await withBusyReload(() => actions.addToList(stockItemId.value));
    }
    async function onChangeStockLevel(stockLevelId: string) {
        await withBusyReload(() =>
            stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId.value,
                stock_level_id: stockLevelId,
            }),
        );
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


    // C-1b.3 (L130 emphasis): the cheapest product gets a chip + highlight
    // style rather than a separate "Add cheapest" button — each product
    // carries its own Add-to-list.
    function isCheapest(p: LinkedProduct): boolean {
        return cheapestProduct.value?.product_id === p.product_id;
    }

    // C-1b.3 (L125): Find-deals now lives only inside the Products tab
    // (empty-state CTA + "Link another" when products exist). Both route
    // to product-search seeded with the item name; that page already owns
    // the link flow.
    function onFindAndLink() {
        void router.push({
            path: '/product-search',
            query: { q: detail.value?.name ?? '' },
        });
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
    // C-1b.4 / FU-185 — B8 residue: the favourite toggle on this surface
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

    // ── On shopping lists ────────────────────────────────────────────────
    const onLists = computed(() => {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === stockItemId.value);
        const ids = entry?.unticked_list_ids ?? [];
        const lookup = new Map((m?.active_lists ?? []).map((l) => [l.shopping_list_id, l]));
        return ids.map(
            (lid) => lookup.get(lid) ?? { shopping_list_id: lid, name: lid, status: 'draft' as const },
        );
    });
    // C-1b.4 (L138): the server-inferred primary draft list (R-003) — the
    // Lists tab decorates that row with a styled "Primary" badge instead
    // of plain text.
    const primaryListId = computed(() => shoppingListStore.quickAddTargetListId ?? null);
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
    const WASTE_REASON_LABELS: Record<string, string> = {
        expired: 'expired',
        spoiled: 'spoiled',
        did_not_like: "didn't like",
        overbought: 'overbought',
        other: 'other reason',
    };
    function humaniseAddedVia(via: string): string {
        return ADDED_VIA_LABELS[via] ?? 'Added to a list';
    }
    function humaniseWasteReason(reason: string): string {
        return WASTE_REASON_LABELS[reason] ?? reason;
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

        // Waste events.
        for (const w of d.waste_events ?? []) {
            const reason = humaniseWasteReason(w.reason);
            const qty = w.quantity != null ? `${w.quantity} ` : '';
            const value = w.estimated_value != null
                ? ` (~$${w.estimated_value.toFixed(2)})`
                : '';
            const entry: LifecycleEvent = {
                id: `waste-${w.occurred_at}-${reason}`,
                at: w.occurred_at,
                title: `Wasted: ${qty}${reason}${value}`.trim(),
                icon: ICONS.delete_outline,
                color: 'negative',
            };
            if (w.note) entry.body = w.note;
            out.push(entry);
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

        // Synthetic "Opened" — single entry derived from current state.
        // opened_on is a date; widen to start-of-day for ordering.
        if (d.is_open && d.opened_on) {
            out.push({
                id: `opened-${d.opened_on}`,
                at: `${d.opened_on}T00:00:00`,
                title: 'Opened',
                icon: 'lock_open',
                color: 'amber-9',
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

        // Sort newest first and cap so a chatty item doesn't blow the tab.
        out.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
        return out.slice(0, 60);
    });

    // ── Unlink products ──────────────────────────────────────────────────
    // C-1b.3 retired the saved-products picker dialog in favour of the
    // single Find-&-link CTA → /product-search (which owns the link flow).
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
            // B4: backend refuses delete when the item is still on a recipe,
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
        $q.notify({ type: 'negative', position: 'bottom-right', message, caption: describeApiError(err) || '' });
    }
    function formatDateTime(iso: string): string {
        if (!iso) return '';
        return new Date(iso).toLocaleString();
    }
    function relativeTime(iso: string): string {
        if (!iso) return '';
        const diffMs = Date.now() - new Date(iso).getTime();
        const mins = Math.floor(diffMs / 60_000);
        if (mins < 1) return 'just now';
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        const weeks = Math.floor(days / 7);
        if (weeks < 5) return `${weeks}w ago`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months}mo ago`;
        return `${Math.floor(days / 365)}y ago`;
    }

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

    onMounted(async () => {
        // Stock groups are page-local (only consumer); load alongside the
        // other dropdowns so the inline picker has options on first paint.
        void stockGroupApi.getAllAsync().then((g) => { stockGroups.value = g; });
        await Promise.all([
            stockLevelStore.getStockLevelsAsync(),
            locationStore.refreshAsync(),
            stockItemStore.getStockItemsAsync(),
            recipeStore.getRecipesAsync(),
            shoppingListStore.refreshAsync(),
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
</style>
