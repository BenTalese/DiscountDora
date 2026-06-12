<template>
    <div class="shop-mode-root" @keydown="onKeyDown" tabindex="0" ref="rootEl">
        <!-- Top strip — list name, exit button, progress bar.
             Sticky so the user always sees how far they've got
             without scrolling away from the next item. -->
        <header class="shop-mode-header">
            <q-btn
                flat
                round
                dense
                size="md"
                :icon="ICONS.arrow_back"
                :loading="exiting"
                aria-label="Back to editing"
                @click="exit"
            >
                <q-tooltip>← Back to editing (reopens the list for changes)</q-tooltip>
            </q-btn>
            <div class="col">
                <div class="text-subtitle1 ellipsis">
                    {{ detail?.name ?? 'Loading…' }}
                </div>
                <div class="text-caption dora-text-muted">
                    {{ pickedCount }} / {{ totalCount }} picked
                    <span v-if="estimatedRemainingTotal > 0">
                        · ${{ estimatedRemainingTotal.toFixed(2) }} left
                    </span>
                </div>
            </div>
            <!-- P6-01 Chunk 6 — "Peek list" lets the shopper see the full
                 remaining list without leaving shop mode (feedback
                 §SHOPPING MODE / proposal §2.5). -->
            <q-btn
                flat
                round
                dense
                size="md"
                :icon="ICONS.list_alt"
                aria-label="Peek the whole list"
                @click="peekOpen = true"
            >
                <q-tooltip>Peek the whole list</q-tooltip>
            </q-btn>
            <q-btn
                flat
                round
                dense
                size="md"
                :icon="ICONS.more_vert"
                aria-label="Shop-mode options"
            >
                <q-menu auto-close anchor="bottom right" self="top right">
                    <q-list dense style="min-width: 220px">
                        <q-item
                            clickable
                            @click="onFinish"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.check" color="positive" />
                            </q-item-section>
                            <q-item-section>Finish &amp; restock</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>
        </header>

        <q-linear-progress
            :value="progressFraction"
            color="positive"
            size="6px"
            class="shop-mode-progress"
        />

        <!-- Offline banner is rendered globally by MainLayout — we
             deliberately don't duplicate it here. Shop mode's writes
             go through `tryWithQueue` so they're queued silently when
             reception drops, and the global banner is what surfaces
             the queued-count badge. -->

        <!-- Main: big card for the current item ─────────────────────── -->
        <main class="shop-mode-main">
            <div v-if="loading && !detail" class="text-center q-pa-xl">
                <AppSpinner size="60px" />
            </div>

            <q-banner v-else-if="loadError" class="bg-negative dora-text-on-primary q-ma-md" rounded>
                {{ loadError }}
            </q-banner>

            <div
                v-else-if="!currentLine"
                class="shop-mode-empty"
            >
                <q-icon :name="ICONS.check_circle" size="80px" color="positive" />
                <div class="text-h5 q-mt-md">All done!</div>
                <div class="text-body2 dora-text-muted q-mt-sm">
                    Every item is ticked. You can finish the shop now or
                    head back to the full list.
                </div>
                <q-btn
                    unelevated
                    color="positive"
                    no-caps
                    :icon="ICONS.check"
                    label="Finish shopping"
                    class="q-mt-lg"
                    size="lg"
                    @click="onFinish"
                />
            </div>

            <div v-else class="shop-mode-card-wrap">
                <!-- Section header — derived from the line's stock-location
                     breadcrumb so the shopper sees "Fridge > Dairy" or
                     similar grouping if their locations describe a route.
                     Falls back to "Other" when unlocated. -->
                <div class="shop-mode-section text-caption dora-text-muted">
                    {{ currentSection }}
                    <q-tooltip v-if="currentSectionHasDetail">
                        {{ currentSectionFull }}
                    </q-tooltip>
                </div>

                <article class="shop-mode-card">
                    <div class="shop-mode-card-name">
                        {{ currentLine.stock_item_name }}
                    </div>

                    <div v-if="currentOffer" class="shop-mode-card-merchant text-caption">
                        <q-icon name="storefront" size="14px" class="q-mr-xs" />
                        {{ currentOffer.merchant_name }}
                        <span v-if="currentOffer.price_now != null">
                            · ${{ currentOffer.price_now.toFixed(2) }}
                        </span>
                    </div>

                    <!-- Quantity stepper — big tap targets, kept centered.
                         P6-01 Chunk 6 / feedback §SHOPPING MODE: the centre
                         number is now itself tappable to type the count
                         directly, instead of mashing + ten times. -->
                    <div class="shop-mode-qty-row">
                        <q-btn
                            unelevated
                            round
                            size="lg"
                            color="grey"
                            text-color="black"
                            :icon="ICONS.remove"
                            aria-label="Decrease quantity"
                            :disable="(currentLine.quantity ?? 0) <= 0"
                            @click="adjustQuantity(-1)"
                        />
                        <button
                            type="button"
                            class="shop-mode-qty-value shop-mode-qty-button"
                            aria-label="Type a quantity"
                            @click="openQtyEditor"
                        >
                            {{ currentLine.quantity ?? '—' }}
                        </button>
                        <q-btn
                            unelevated
                            round
                            size="lg"
                            color="grey"
                            text-color="black"
                            :icon="ICONS.add"
                            aria-label="Increase quantity"
                            @click="adjustQuantity(1)"
                        />
                    </div>

                    <!-- Primary action — fills the screen width. -->
                    <q-btn
                        class="shop-mode-pick-btn"
                        color="positive"
                        text-color="white"
                        :icon="ICONS.check"
                        unelevated
                        no-caps
                        label="Got it"
                        size="xl"
                        :loading="pickInFlight"
                        @click="markPicked"
                    />

                    <!-- Secondary actions row — small flat buttons. -->
                    <div class="shop-mode-actions-row">
                        <q-btn
                            flat
                            no-caps
                            :icon="ICONS.edit"
                            label="Price"
                            @click="openPriceEditor(currentLine)"
                        />
                        <q-btn
                            flat
                            no-caps
                            :icon="ICONS.swap_horiz"
                            label="Substitute"
                            :disable="!hasOffers"
                            @click="onPickOtherOffer"
                        />
                        <q-btn
                            flat
                            no-caps
                            class="dora-text-secondary"
                            :icon="ICONS.arrow_forward"
                            label="Skip"
                            @click="skipForNow"
                        >
                            <q-tooltip>
                                Move this item to the end so you can come
                                back to it.
                            </q-tooltip>
                        </q-btn>
                    </div>
                </article>

                <!-- Upcoming preview — two next items, muted, taps jump. -->
                <div
                    v-if="upcomingPreview.length > 0"
                    class="shop-mode-up-next"
                >
                    <div class="text-caption dora-text-muted">Up next</div>
                    <button
                        v-for="line in upcomingPreview"
                        :key="line.line_id"
                        class="shop-mode-up-row"
                        @click="jumpTo(line.line_id)"
                    >
                        {{ line.stock_item_name }}
                        <span class="text-caption dora-text-muted">
                            ×{{ line.quantity ?? 1 }}
                        </span>
                    </button>
                </div>
            </div>
        </main>

        <!-- Bottom toolbar — picked count + total + Finish CTA. -->
        <footer v-if="detail && detail.status !== 'done'" class="shop-mode-footer">
            <div class="shop-mode-footer-totals">
                <div>
                    <div class="text-caption dora-text-muted">Picked</div>
                    <div class="text-h6">{{ pickedCount }}</div>
                </div>
                <div>
                    <div class="text-caption dora-text-muted">Estimated</div>
                    <div class="text-h6">${{ estimatedTotalAll.toFixed(2) }}</div>
                </div>
            </div>
            <q-btn
                unelevated
                color="positive"
                no-caps
                :icon="ICONS.check"
                :label="remainingLines.length === 0 ? 'Finish &amp; restock' : 'Finish early &amp; restock'"
                size="lg"
                class="shop-mode-finish-btn"
                :loading="finishing"
                @click="onFinish"
            />
        </footer>

        <!-- Whole-list peek (Chunk 6). The user reviews the full remaining
             list without leaving shop mode; tapping an unticked item jumps
             it to the front (persisted via reorder). -->
        <BaseDialog v-model="peekOpen" card-style="min-width: 320px; max-width: 480px">
            <q-card-section>
                <div class="text-h6">Whole list</div>
                <div class="text-caption dora-text-muted">
                    {{ pickedCount }} / {{ totalCount }} picked.
                    Tap an unticked item to jump to it.
                </div>
            </q-card-section>
            <q-card-section style="max-height: 60vh; overflow: auto" class="q-pt-none">
                <q-list dense separator>
                    <q-item
                        v-for="line in sortedLines"
                        :key="line.line_id"
                        :clickable="!line.is_ticked"
                        :class="line.is_ticked ? 'dora-text-muted' : ''"
                        @click="onPeekJump(line)"
                    >
                        <q-item-section avatar>
                            <q-icon
                                :name="line.is_ticked ? ICONS.check_circle : ICONS.check_box_outline_blank"
                                :color="line.is_ticked ? 'positive' : 'grey'"
                            />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label :class="line.is_ticked ? 'text-strike' : ''">
                                {{ line.stock_item_name }}
                            </q-item-label>
                            <q-item-label v-if="line.quantity != null" caption>
                                ×{{ line.quantity }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Close" v-close-popup />
            </q-card-actions>
        </BaseDialog>

        <!-- Tap-to-type qty (Chunk 6) — opens when the centre number on
             the qty row is tapped. Lets the user enter "8" rather than
             tapping + eight times. -->
        <BaseDialog v-model="qtyEditorOpen" card-style="min-width: 240px">
            <q-card-section>
                <div class="text-h6">Quantity</div>
                <div v-if="qtyEditorLine" class="text-caption dora-text-muted">
                    {{ qtyEditorLine.stock_item_name }}
                </div>
            </q-card-section>
            <q-card-section>
                <q-input
                    v-model.number="qtyEditorDraft"
                    autofocus
                    outlined
                    type="number"
                    step="1"
                    min="0"
                    label="Quantity"
                    input-class="text-h5"
                    @keydown.enter.prevent="saveQtyEditor"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Save"
                    v-close-popup
                    @click="saveQtyEditor"
                />
            </q-card-actions>
        </BaseDialog>

        <!-- Inline price editor — reuses the same logic as the list page
             but with a larger touch target for shop-mode use. -->
        <BaseDialog v-model="priceEditorOpen" card-style="min-width: 280px">
                <q-card-section>
                    <div class="text-h6">Actual price paid</div>
                    <div v-if="priceEditorLine" class="text-caption dora-text-muted">
                        {{ priceEditorLine.stock_item_name }}
                    </div>
                </q-card-section>
                <q-card-section class="q-gutter-sm">
                    <q-input
                        v-model.number="priceEditorDraft.price"
                        autofocus
                        outlined
                        type="number"
                        step="0.01"
                        min="0"
                        prefix="$"
                        label="Unit price"
                        input-class="text-h5"
                        @keydown.enter.prevent="savePriceEditor"
                    />
                    <q-select
                        v-if="priceMerchantOptions.length > 0"
                        v-model="priceEditorDraft.merchant_id"
                        :options="priceMerchantOptions"
                        outlined
                        emit-value
                        map-options
                        clearable
                        label="Bought from (optional)"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton
                        v-if="priceEditorLine?.actual_unit_price != null"
                        variant="ghost"
                        class="text-negative"
                        label="Clear"
                        v-close-popup
                        @click="clearPriceOverride"
                    />
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton
                        variant="primary"
                        label="Save"
                        v-close-popup
                        @click="savePriceEditor"
                    />
                </q-card-actions>
        </BaseDialog>

        <!-- Substitute picker — list the line's known offers; the shopper
             swaps the merchant chip without leaving shop mode. -->
        <BaseDialog v-model="offerPickerOpen" card-style="min-width: 280px">
                <q-card-section>
                    <div class="text-h6">Substitute</div>
                    <div v-if="currentLine" class="text-caption dora-text-muted">
                        {{ currentLine.stock_item_name }}
                    </div>
                </q-card-section>
                <q-list separator>
                    <q-item
                        v-for="offer in (currentLine?.offers ?? [])"
                        :key="offer.product_id"
                        clickable
                        v-close-popup
                        @click="pickOffer(offer.product_id)"
                    >
                        <q-item-section avatar>
                            <q-icon
                                :name="offer.product_id === currentLine?.selected_product_id ? 'radio_button_checked' : 'radio_button_unchecked'"
                                :color="offer.product_id === currentLine?.selected_product_id ? 'primary' : undefined"
                            />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ offer.merchant_name }}</q-item-label>
                            <q-item-label caption>
                                {{ offer.brand ? `${offer.brand} — ` : '' }}{{ offer.name }}
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <div v-if="offer.price_now != null">
                                ${{ offer.price_now.toFixed(2) }}
                            </div>
                        </q-item-section>
                    </q-item>
                </q-list>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Close" v-close-popup />
                </q-card-actions>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { tryWithQueue } from 'src/composables/useOfflineQueue';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import {
        chosenOfferFor,
        type ShoppingListDetail,
        type ShoppingListLine,
    } from 'src/models/shoppingList';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { formatLocation, locationHasDetail } from 'src/helpers/locationDisplay';
    import { ICONS } from 'src/style/icons';
    import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const route = useRoute();
    const router = useRouter();
    const api = new ShoppingListApiService();

    const listId = computed(() => String(route.params.id));

    const detail = ref<ShoppingListDetail | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const rootEl = ref<HTMLElement | null>(null);
    const pickInFlight = ref(false);

    // P2-11 — order lines for the shopper. Sort:
    //  1. unticked before ticked
    //  2. stable by location breadcrumb (so groceries-by-section
    //     feels natural when locations describe a store walk)
    //  3. by the line's existing sequence
    function sortKey(line: ShoppingListLine): string {
        const ticked = line.is_ticked ? '1' : '0';
        const section = (line.stock_location_breadcrumb ?? []).join(' › ') || '~unsorted';
        return `${ticked}|${section}|${String(line.sequence).padStart(6, '0')}`;
    }

    const sortedLines = computed<ShoppingListLine[]>(() => {
        const lines = [...(detail.value?.lines ?? [])];
        lines.sort((a, b) => sortKey(a).localeCompare(sortKey(b)));
        return lines;
    });
    const remainingLines = computed(() => sortedLines.value.filter((l) => !l.is_ticked));
    const totalCount = computed(() => sortedLines.value.length);
    const pickedCount = computed(() => sortedLines.value.length - remainingLines.value.length);
    const progressFraction = computed(() =>
        totalCount.value === 0 ? 0 : pickedCount.value / totalCount.value,
    );

    const currentLine = computed<ShoppingListLine | null>(() => remainingLines.value[0] ?? null);
    const currentOffer = computed(() => currentLine.value ? chosenOfferFor(currentLine.value) : null);
    const hasOffers = computed(() => (currentLine.value?.offers.length ?? 0) > 1);
    // C-cross Chunk 4 — display the zone (top-level), not the full
    // breadcrumb. The full path is shown in a tooltip on the section
    // header in the template; the sortKey above still uses the full
    // breadcrumb as its stable grouping key.
    const currentSection = computed(() => {
        if (!currentLine.value) return '';
        const crumbs = currentLine.value.stock_location_breadcrumb ?? [];
        return crumbs.length > 0 ? formatLocation(crumbs, 'zone') : 'Other';
    });
    const currentSectionFull = computed(() => {
        const crumbs = currentLine.value?.stock_location_breadcrumb ?? [];
        return crumbs.length > 0 ? formatLocation(crumbs, 'full') : '';
    });
    const currentSectionHasDetail = computed(() =>
        locationHasDetail(currentLine.value?.stock_location_breadcrumb),
    );

    const upcomingPreview = computed(() => remainingLines.value.slice(1, 3));

    // Totals are server-owned (state-ownership Type B) — read them off
    // `detail.totals` rather than re-summing the lines. `total_price` covers
    // every line; `remaining_price` covers the un-ticked ones.
    const estimatedTotalAll = computed(() => detail.value?.totals?.total_price ?? 0);
    const estimatedRemainingTotal = computed(() => detail.value?.totals?.remaining_price ?? 0);

    async function load() {
        if (!listId.value) return;
        loading.value = true;
        loadError.value = null;
        // Clear stale data so the spinner shows, not the previous list,
        // while the new detail is in flight (FU-157).
        detail.value = null;
        try {
            detail.value = await api.getDetailAsync(listId.value);
        } catch (err) {
            loadError.value = `Could not load list: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    // FU-157 — same param-change pattern as ShoppingListDetail. Rare in
    // shop mode (you usually shop one list end-to-end) but free to wire.
    watch(listId, () => { void load(); });

    onMounted(async () => {
        await load();
        // SHOPPING is the only phase that should render this surface. If a
        // PWA shortcut or stale link lands here on a DRAFT/DONE list,
        // bounce to the detail page so editing/reopen is available.
        // **Important**: `nextTick` defers the redirect until after the
        // MainLayout's <FadeTransition> finishes entering — without
        // this, unmounting mid-transition wedges the global transition
        // state and renders subsequent pages blank.
        if (detail.value && detail.value.status !== 'shopping') {
            await nextTick();
            await router.replace(`/shopping-lists/${listId.value}`);
            return;
        }
        // Pull focus to the root so the global keyboard shortcuts fire
        // without the user having to tap first.
        setTimeout(() => rootEl.value?.focus(), 50);
    });

    // ── Pick / skip / quantity ──────────────────────────────────────────
    async function markPicked() {
        if (!currentLine.value) return;
        const line = currentLine.value;
        // Optimistic tick. The full-list page does the same — keeps
        // mid-shop interactions feeling instant on flaky reception.
        line.is_ticked = true;
        pickInFlight.value = true;
        try {
            await tryWithQueue(
                () => api.updateLineAsync(listId.value, line.line_id, { is_ticked: true }),
                {
                    url: `${resolveBaseURL('dora')}/shopping-lists/${listId.value}/lines/${line.line_id}`,
                    method: 'PATCH',
                    body: { is_ticked: true },
                    kind: 'shopping_list_line_tick',
                    label: 'Tick item',
                },
            );
        } catch (err) {
            line.is_ticked = false;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not tick item.',
                caption: describeApiError(err) || '',
            });
        } finally {
            pickInFlight.value = false;
        }
    }

    // Whole-list peek (Chunk 6).
    const peekOpen = ref(false);

    async function onPeekJump(line: ShoppingListLine) {
        if (line.is_ticked) return;
        peekOpen.value = false;
        await jumpTo(line.line_id);
    }

    // Tap-to-type qty editor (Chunk 6).
    const qtyEditorOpen = ref(false);
    const qtyEditorLine = ref<ShoppingListLine | null>(null);
    const qtyEditorDraft = ref<number | null>(null);

    function openQtyEditor() {
        if (!currentLine.value) return;
        qtyEditorLine.value = currentLine.value;
        qtyEditorDraft.value = currentLine.value.quantity ?? 0;
        qtyEditorOpen.value = true;
    }

    async function saveQtyEditor() {
        const line = qtyEditorLine.value;
        if (!line) return;
        const next = qtyEditorDraft.value;
        if (next == null || Number.isNaN(next) || next < 0) return;
        const previous = line.quantity;
        if (previous === next) return;
        line.quantity = next;
        try {
            await api.updateLineAsync(listId.value, line.line_id, { quantity: next });
        } catch (err) {
            line.quantity = previous;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not update quantity.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function adjustQuantity(delta: number) {
        if (!currentLine.value) return;
        const line = currentLine.value;
        const next = Math.max(0, (line.quantity ?? 0) + delta);
        const previous = line.quantity;
        if (previous === next) return;
        line.quantity = next;
        try {
            await api.updateLineAsync(listId.value, line.line_id, { quantity: next });
        } catch (err) {
            line.quantity = previous;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not update quantity.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function skipForNow() {
        // P6-01 Chunk 6 — skip now persists. Optimistic local sequence
        // bump (so the card visibly flips immediately) followed by a
        // reorder API call so the new order survives a refresh.
        // Pre-Chunk-6 this was client-only and reverted on refresh
        // (feedback §SHOPPING MODE "the position of the items keeps
        // changing").
        if (!detail.value || !currentLine.value) return;
        const line = currentLine.value;
        await persistMoveToEnd(line.line_id);
    }

    async function jumpTo(lineId: string) {
        // Move the chosen line to the *front* of the queue (next-up)
        // and persist. Same persistence story as skip — pre-Chunk-6
        // this was local-only.
        if (!detail.value) return;
        await persistMoveToFront(lineId);
    }

    async function persistReorderedIds(ids: string[]) {
        if (!detail.value) return;
        // Optimistic: rewrite local sequences so sortedLines re-orders
        // instantly; if the API call fails, reload from the server.
        const lookup = new Map(detail.value.lines.map((l) => [l.line_id, l]));
        ids.forEach((id, idx) => {
            const line = lookup.get(id);
            if (line) line.sequence = idx;
        });
        try {
            await api.reorderLinesAsync(listId.value, ids);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not save the new order.',
                caption: describeApiError(err) || '',
            });
            await load();
        }
    }

    async function persistMoveToEnd(lineId: string) {
        const allIds = [...sortedLines.value.map((l) => l.line_id)];
        const idx = allIds.indexOf(lineId);
        if (idx < 0) return;
        allIds.splice(idx, 1);
        allIds.push(lineId);
        await persistReorderedIds(allIds);
    }

    async function persistMoveToFront(lineId: string) {
        // "Front" = before the first un-ticked line, so jumped lines
        // become the next "Got it" candidate without leapfrogging
        // already-picked ones.
        const allIds = [...sortedLines.value.map((l) => l.line_id)];
        const idx = allIds.indexOf(lineId);
        if (idx < 0) return;
        allIds.splice(idx, 1);
        const firstUntickedIdx = allIds.findIndex(
            (id) => !(detail.value?.lines.find((l) => l.line_id === id)?.is_ticked),
        );
        const insertAt = firstUntickedIdx < 0 ? 0 : firstUntickedIdx;
        allIds.splice(insertAt, 0, lineId);
        await persistReorderedIds(allIds);
    }

    // ── Price editor ────────────────────────────────────────────────────
    const priceEditorOpen = ref(false);
    const priceEditorLine = ref<ShoppingListLine | null>(null);
    const priceEditorDraft = reactive<{ price: number | null; merchant_id: string | null }>({
        price: null,
        merchant_id: null,
    });

    function priceMerchantOptionsFor(line: ShoppingListLine | null) {
        if (!line) return [];
        const seen = new Map<string, string>();
        for (const offer of line.offers) {
            if (!seen.has(offer.merchant_id)) {
                seen.set(offer.merchant_id, offer.merchant_name);
            }
        }
        return Array.from(seen, ([value, label]) => ({ value, label }));
    }
    const priceMerchantOptions = computed(() => priceMerchantOptionsFor(priceEditorLine.value));

    function openPriceEditor(line: ShoppingListLine) {
        priceEditorLine.value = line;
        if (line.actual_unit_price != null) {
            priceEditorDraft.price = line.actual_unit_price;
        } else {
            priceEditorDraft.price = chosenOfferFor(line)?.price_now ?? null;
        }
        priceEditorDraft.merchant_id =
            line.purchased_merchant_id ?? chosenOfferFor(line)?.merchant_id ?? null;
        priceEditorOpen.value = true;
    }

    async function savePriceEditor() {
        const line = priceEditorLine.value;
        if (!line) return;
        const next = priceEditorDraft.price;
        if (next == null || Number.isNaN(next) || next <= 0) {
            await clearPriceOverride();
            return;
        }
        const previous = line.actual_unit_price;
        const prevMerchant = line.purchased_merchant_id;
        const prevMerchantName = line.purchased_merchant_name;
        line.actual_unit_price = next;
        line.purchased_merchant_id = priceEditorDraft.merchant_id ?? null;
        line.purchased_merchant_name =
            priceMerchantOptionsFor(line).find(
                (o) => o.value === priceEditorDraft.merchant_id,
            )?.label ?? null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                actual_unit_price: next,
                ...(priceEditorDraft.merchant_id
                    ? { purchased_merchant_id: priceEditorDraft.merchant_id }
                    : { clear_purchased_merchant: true }),
            });
        } catch (err) {
            line.actual_unit_price = previous;
            line.purchased_merchant_id = prevMerchant;
            line.purchased_merchant_name = prevMerchantName;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not save the price.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function clearPriceOverride() {
        const line = priceEditorLine.value;
        if (!line) return;
        const previous = line.actual_unit_price;
        const prevMerchant = line.purchased_merchant_id;
        const prevMerchantName = line.purchased_merchant_name;
        line.actual_unit_price = null;
        line.purchased_merchant_id = null;
        line.purchased_merchant_name = null;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                clear_actual_unit_price: true,
                clear_purchased_merchant: true,
            });
        } catch (err) {
            line.actual_unit_price = previous;
            line.purchased_merchant_id = prevMerchant;
            line.purchased_merchant_name = prevMerchantName;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not clear the price.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── Substitute / pick another offer ─────────────────────────────────
    const offerPickerOpen = ref(false);
    function onPickOtherOffer() {
        offerPickerOpen.value = true;
    }
    async function pickOffer(productId: string) {
        if (!currentLine.value) return;
        const line = currentLine.value;
        const previous = line.selected_product_id;
        line.selected_product_id = productId;
        try {
            await api.updateLineAsync(listId.value, line.line_id, {
                selected_product_id: productId,
            });
        } catch (err) {
            line.selected_product_id = previous;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not change offer.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── Finish ──────────────────────────────────────────────────────────
    const finishing = ref(false);
    const exiting = ref(false);

    async function onFinish() {
        if (!detail.value) return;
        const ticked = (detail.value.lines ?? []).filter((l) => l.is_ticked);
        const unticked = (detail.value.lines.length ?? 0) - ticked.length;
        // Fold the old standalone "review mode" into the finish confirmation
        // (Chunk 3): list the items that will bump to Well-Stocked so the
        // user can sanity-check before archiving the list.
        const tickedNames = ticked.map((l) => l.stock_item_name).slice(0, 8);
        const tickedSummary = ticked.length === 0
            ? 'No items are ticked — nothing will be restocked.'
            : `${ticked.length} item${ticked.length === 1 ? '' : 's'} will be bumped to ` +
              `Well-Stocked: ${tickedNames.join(', ')}` +
              (ticked.length > tickedNames.length ? `, and ${ticked.length - tickedNames.length} more.` : '.');
        const untickedMsg = unticked > 0
            ? `\n\n${unticked} unticked item${unticked === 1 ? '' : 's'} will be archived with the list.`
            : '';
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Finish & restock?',
                message: `${tickedSummary}${untickedMsg}`,
                ok: { label: 'Finish & restock', color: 'positive', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        finishing.value = true;
        try {
            await api.finishAsync(listId.value);
            $q.notify({
                type: 'positive',
                position: 'top',
                message: 'Shopping finished.',
            });
            await router.push('/shopping-lists');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not finish shopping.',
                caption: describeApiError(err) || '',
            });
        } finally {
            finishing.value = false;
        }
    }

    async function exit() {
        // "← Back to editing" reopens the list (SHOPPING → DRAFT) before
        // routing back to the detail page. If we skipped the status flip,
        // the detail page's status-watcher would bounce us straight back
        // into shop mode.
        if (!detail.value) {
            void router.push(`/shopping-lists/${listId.value}`);
            return;
        }
        if (detail.value.status !== 'shopping') {
            // Already not shopping (e.g. user landed here on a DONE list);
            // just navigate.
            void router.replace(`/shopping-lists/${listId.value}`);
            return;
        }
        exiting.value = true;
        try {
            await api.stopShoppingAsync(listId.value);
            void router.replace(`/shopping-lists/${listId.value}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not exit shop mode.',
                caption: describeApiError(err) || '',
            });
        } finally {
            exiting.value = false;
        }
    }

    // ── Keyboard shortcuts ─────────────────────────────────────────────
    // Space/Enter = pick. ArrowDown / "s" = skip. ArrowUp / "u" = undo
    // last pick. Esc = exit shop mode. Large focus ring on the root
    // div keeps these accessible to keyboard-only users.
    function onKeyDown(event: KeyboardEvent) {
        // Don't intercept while a dialog has focus — those have their
        // own Enter/Esc semantics (Save / Cancel).
        if (priceEditorOpen.value || offerPickerOpen.value || qtyEditorOpen.value || peekOpen.value) return;
        if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            void markPicked();
        } else if (event.key === 'ArrowDown' || event.key === 's') {
            event.preventDefault();
            void skipForNow();
        } else if (event.key === 'ArrowUp' || event.key === 'u') {
            event.preventDefault();
            void undoLastPick();
        } else if (event.key === 'Escape') {
            event.preventDefault();
            void exit();
        }
    }

    async function undoLastPick() {
        // The last picked line (highest sequence among ticked) gets
        // un-ticked and becomes the next-up. Useful for the very common
        // "wait, that's the wrong one" mid-shop.
        const tickedLines = (detail.value?.lines ?? []).filter((l) => l.is_ticked);
        if (tickedLines.length === 0) return;
        tickedLines.sort((a, b) => b.sequence - a.sequence);
        const line = tickedLines[0]!;
        line.is_ticked = false;
        try {
            await api.updateLineAsync(listId.value, line.line_id, { is_ticked: false });
        } catch (err) {
            line.is_ticked = true;
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not undo pick.',
                caption: describeApiError(err) || '',
            });
        }
    }
</script>

<style scoped>
    /* P2-11 — fullscreen mobile-first layout. Keeps tap targets >= 56px
       and the primary CTA reaches a usable width across all phones.
       We use simple flex stacking rather than Quasar's q-page so this
       stays free of the desktop drawer / header rhythm — shop mode
       wants to read as a focused tool, not a screen inside the app. */
    .shop-mode-root {
        display: flex;
        flex-direction: column;
        min-height: calc(100vh - 64px); /* leave room for the app header */
        outline: none;
    }
    .shop-mode-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        position: sticky;
        top: 0;
        background: var(--q-page-background, white);
        z-index: 2;
    }
    .shop-mode-progress {
        flex-shrink: 0;
    }
    .shop-mode-main {
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        align-items: stretch;
        padding: 16px;
        gap: 12px;
    }
    .shop-mode-empty {
        text-align: center;
        margin: auto;
        padding: 24px;
        max-width: 360px;
    }
    .shop-mode-card-wrap {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .shop-mode-section {
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .shop-mode-card {
        background: var(--surface-elevated);
        border-radius: 18px;
        padding: 24px 20px;
        display: flex;
        flex-direction: column;
        gap: 18px;
    }
    .shop-mode-card-name {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.15;
        word-break: break-word;
    }
    .shop-mode-card-merchant {
        color: var(--text-muted);
    }
    .shop-mode-qty-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
    }
    .shop-mode-qty-value {
        font-size: 2rem;
        font-weight: 700;
        min-width: 48px;
        text-align: center;
    }
    .shop-mode-qty-button {
        /* Make the centre number itself a tap target (Chunk 6). The
           button reset keeps the visual identical to the old <div>. */
        background: transparent;
        border: none;
        padding: 8px 4px;
        cursor: pointer;
        color: inherit;
        font: inherit;
        border-radius: 8px;
    }
    .shop-mode-qty-button:hover {
        background: var(--overlay-hover);
    }
    .shop-mode-qty-button:focus-visible {
        outline: 2px solid var(--q-primary);
        outline-offset: 2px;
    }
    .shop-mode-pick-btn {
        width: 100%;
        font-size: 1.2rem;
        padding: 18px 0;
        border-radius: 14px;
    }
    .shop-mode-actions-row {
        display: flex;
        justify-content: space-between;
        gap: 6px;
    }
    .shop-mode-up-next {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 8px 4px;
    }
    .shop-mode-up-row {
        all: unset;
        cursor: pointer;
        padding: 10px 12px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1rem;
    }
    .shop-mode-up-row:hover,
    .shop-mode-up-row:focus-visible {
        background: var(--overlay-active);
        outline: none;
    }
    .shop-mode-footer {
        position: sticky;
        bottom: 0;
        background: var(--q-page-background, white);
        border-top: 1px solid var(--overlay-active);
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 16px;
        z-index: 2;
    }
    .shop-mode-footer-totals {
        display: flex;
        gap: 24px;
        flex: 1;
    }
    .shop-mode-finish-btn {
        flex-shrink: 0;
        padding: 12px 18px;
        border-radius: 12px;
    }

    @media (min-width: 720px) {
        /* On wider screens (tablet+) center the card and cap its width
           so the buttons stay at "phone-thumb" reach rather than
           stretching the whole way across. */
        .shop-mode-card-wrap,
        .shop-mode-empty {
            max-width: 480px;
            margin: 0 auto;
            width: 100%;
        }
    }
</style>
