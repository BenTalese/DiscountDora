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
                aria-label="Exit shop mode"
                @click="exit"
            />
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
                            :disable="remainingLines.length === 0"
                            @click="onFinish"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.check" color="positive" />
                            </q-item-section>
                            <q-item-section>Finish shopping</q-item-section>
                        </q-item>
                        <q-item clickable @click="goToFullList">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.list_alt ?? ICONS.menu" />
                            </q-item-section>
                            <q-item-section>Open full list</q-item-section>
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

                    <!-- Quantity stepper — big tap targets, kept centered. -->
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
                        <div class="shop-mode-qty-value">
                            {{ currentLine.quantity ?? '—' }}
                        </div>
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
                v-if="remainingLines.length === 0"
                unelevated
                color="positive"
                no-caps
                :icon="ICONS.check"
                label="Finish"
                size="lg"
                class="shop-mode-finish-btn"
                @click="onFinish"
            />
        </footer>

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
    import { ICONS } from 'src/style/icons';
    import { computed, onMounted, reactive, ref } from 'vue';
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
    const currentSection = computed(() => {
        if (!currentLine.value) return '';
        const crumbs = currentLine.value.stock_location_breadcrumb ?? [];
        return crumbs.length > 0 ? crumbs.join(' › ') : 'Other';
    });

    const upcomingPreview = computed(() => remainingLines.value.slice(1, 3));

    // Totals are server-owned (state-ownership Type B) — read them off
    // `detail.totals` rather than re-summing the lines. `total_price` covers
    // every line; `remaining_price` covers the un-ticked ones.
    const estimatedTotalAll = computed(() => detail.value?.totals?.total_price ?? 0);
    const estimatedRemainingTotal = computed(() => detail.value?.totals?.remaining_price ?? 0);

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

    onMounted(() => {
        void load();
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

    function skipForNow() {
        // "Skip" in shop mode just moves to the next item without
        // touching the data. The current line stays unticked; we
        // rely on the order coming back the same way from the
        // server, so we re-sort with the skipped line shoved
        // alphabetically to the end of its section by mutating its
        // local sequence — purely client-side so it's instantly
        // visible and we don't need a backend round-trip for a
        // "I'll come back to this" gesture.
        if (!currentLine.value) return;
        const line = currentLine.value;
        const max = Math.max(...sortedLines.value.map((l) => l.sequence), 0);
        line.sequence = max + 1;
    }

    function jumpTo(lineId: string) {
        // Re-order so the chosen line becomes the next-up. Local-only
        // (same reasoning as skipForNow); the canonical sequence on
        // the server stays whatever it was.
        const line = (detail.value?.lines ?? []).find((l) => l.line_id === lineId);
        if (!line) return;
        const min = Math.min(...sortedLines.value.map((l) => l.sequence), 0);
        line.sequence = min - 1;
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
    async function onFinish() {
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
        }
    }

    function exit() {
        // Send the user back to the full list view of this shop, not
        // to the lists overview — that's where they came from.
        void router.push(`/shopping-lists/${listId.value}`);
    }

    function goToFullList() {
        void router.push(`/shopping-lists/${listId.value}`);
    }

    // ── Keyboard shortcuts ─────────────────────────────────────────────
    // Space/Enter = pick. ArrowDown / "s" = skip. ArrowUp / "u" = undo
    // last pick. Esc = exit shop mode. Large focus ring on the root
    // div keeps these accessible to keyboard-only users.
    function onKeyDown(event: KeyboardEvent) {
        // Don't intercept while a dialog has focus — those have their
        // own Enter/Esc semantics (Save / Cancel).
        if (priceEditorOpen.value || offerPickerOpen.value) return;
        if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            void markPicked();
        } else if (event.key === 'ArrowDown' || event.key === 's') {
            event.preventDefault();
            skipForNow();
        } else if (event.key === 'ArrowUp' || event.key === 'u') {
            event.preventDefault();
            void undoLastPick();
        } else if (event.key === 'Escape') {
            event.preventDefault();
            exit();
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
