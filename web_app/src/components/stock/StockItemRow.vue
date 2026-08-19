<template>
    <!--
        C-1 Stock Overview Chunk 3 — row rebuild ("kill the chip, one focus action").
        Closes §2.1 + §2.2 + L70 / L75 / L76 / L77 / L78 / L79 / L80 / L82 / L85 /
        L90 / L91 (+ L81 main-zone display, L66 essential-as-filter).

        Left → right:
          [img?]  [bulk?]  [■ LEVEL button]  Name (emphasised) · Zone
            · · · spacer · · ·  [⏰ expiry] [🍽 #recipes] [open] [🛒 cart]
        Image (FU-125) is the first slot so its left edge inherits the
        section's natural left padding — same x where the level button
        sits when the image is hidden. Square, stretched to the row
        content height minus a small margin so it stays inside the
        row's status outline.

        Status drives a whole-row outline (decision 6); selection fills
        the row (L91). All colours via theme tokens — no raw values.
    -->
    <q-card
        v-touch-hold:600.mouse="onLongPress"
        bordered
        flat
        class="stock-row cursor-pointer"
        :class="rowClasses"
        @click="emit('click', item.stock_item_id)"
    >
        <!-- FU-365 round 2: essential is set-and-forget (managed on the
             detail page), so the row-level toggle button was dropped from
             the right cluster. The left-edge stripe is now the sole row
             indicator — thicker + secondary-toned so it scans without an
             accompanying icon. Colour matches the "Essential" footer count
             + filter chip so the concept reads as one visual family. -->
        <div v-if="item.is_essential" class="stock-row__essential-stripe" aria-hidden="true" />
        <q-card-section class="row items-center no-wrap stock-row__body">
            <!-- ──────────────────────────────────────────────────────
                 Leading image slot (FU-125). First child so its left
                 edge sits at the section's natural left padding —
                 i.e. exactly where the stock-level button sits when
                 the image is hidden. Square, stretches to the row
                 content height minus a small margin so it stays
                 inside the row's status outline.
            ────────────────────────────────────────────────────────── -->
            <!-- Round-18: in bulk mode the checkbox sits to the LEFT of
                 the image — tap target is closer to the row's natural
                 entry point, and the image still anchors the row's
                 visual identity. -->
            <q-checkbox
                v-if="bulkMode"
                :model-value="selected"
                @click.stop
                @update:model-value="emit('bulk-toggle', item.stock_item_id)"
            />

            <!-- ──────────────────────────────────────────────────────
                 Stock-level button (L70): big, coloured, text-less.
                 Replaces both the chip avatar and the old right-side
                 dropdown — one focus action for "what level is this".
            ────────────────────────────────────────────────────────── -->
            <BaseButton
                variant="ghost"
                dense
                :class="[
                    'stock-row__level-btn',
                    levelButtonClass,
                    {
                        'stock-row__level-btn--needs-check': needsCheck,
                        'stock-row__level-btn--belief': hasBelief,
                    },
                ]"
                :style="levelButtonStyle"
                :aria-label="levelButtonAriaLabel"
                @click.stop
            >
                <q-tooltip>
                    {{ levelName ? `Level: ${levelName}` : 'Set stock level' }}
                    <template v-if="belief && hasBelief">
                        <br />
                        Dora thinks {{ beliefBandWord }} — {{ belief.reason }}
                    </template>
                </q-tooltip>
                <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                    <q-list dense style="min-width: 200px">
                        <!-- 2026-08-15 feedback: the belief hint used to be a
                             separate "Dora thinks…" pill sitting in the row,
                             which is a second element saying something about
                             the level the picker already owns. It now rides
                             the picker itself: an offset ring on the button,
                             and this header — which was a redundant "Set
                             level" caption — carrying what she thinks and
                             why. Falls back to "Set level" when she has
                             nothing to add. -->
                        <q-item-label v-if="hasBelief" header class="stock-row__belief-header">
                            <div class="row items-center no-wrap">
                                <q-icon :name="ICONS.inferred_hunch" size="16px" class="q-mr-xs" />
                                Dora thinks {{ beliefBandWord }}
                            </div>
                            <div class="stock-row__belief-reason">{{ belief?.reason }}</div>
                        </q-item-label>
                        <q-item-label v-else header>Set level</q-item-label>
                        <q-item
                            v-for="level in stockLevels"
                            :key="level.stock_level_id"
                            clickable
                            v-close-popup
                            :active="level.stock_level_id === item.stock_level_id"
                            active-class="stock-row__level-option--active"
                            @click.stop="onSetLevel(level.stock_level_id)"
                        >
                            <q-item-section avatar>
                                <q-avatar
                                    :color="colourForSequence(level.sequence) ?? undefined"
                                    :class="{ 'dora-bg-neutral': !colourForSequence(level.sequence) }"
                                    size="14px"
                                />
                            </q-item-section>
                            <!-- 2026-08-15 feedback: the current level is
                                 shown by highlighting the whole row (the
                                 `active` + `active-class` pattern used by
                                 the settings nav and the shopping-list rail),
                                 not a trailing tick. -->
                            <q-item-section>{{ level.name }}</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </BaseButton>

            <!-- ──────────────────────────────────────────────────────
                 Name (emphasised) + main zone (L79 / L81).
                 Zone is lightly clickable — bubble up filter-to-location;
                 full breadcrumb stays in the tooltip + detail page.
            ────────────────────────────────────────────────────────── -->
            <div class="stock-row__name-zone column items-start justify-center">
                <div class="stock-row__name">{{ item.name }}</div>
                <!-- 2026-08-15 feedback: the meta line no longer reserves a
                     min-height. It used to hold the async "Dora thinks" chip
                     (which needed the reserve so a late arrival didn't reflow
                     the row) — that has moved onto the level picker, leaving
                     only the location. An item with no location was still
                     paying for the empty line, which shoved its name up off
                     centre; now the line simply isn't rendered.
                     Location is also hidden on phones (`showLocation`): it
                     costs width the row doesn't have, and it's a tap target
                     that silently applies a filter when fat-fingered. -->
                <div v-if="showLocation" class="row items-center no-wrap stock-row__meta">
                    <button
                        type="button"
                        class="stock-row__zone"
                        @click.stop="emit('filter-location', item.stock_location_id!)"
                    >
                        <q-icon :name="ICONS.place" size="14px" class="q-mr-xs" />
                        {{ locationName }}
                        <q-tooltip v-if="locationHasFullDetail">
                            {{ locationFull }} · Filter to this location
                        </q-tooltip>
                        <q-tooltip v-else>Filter to this location</q-tooltip>
                    </button>
                </div>
            </div>

            <q-space />

            <!-- D-10 (2026-08-19): no buy verdict on this row, in any form.
                 It was a chip, then a ring on the cart button; both were a
                 derived signal decorating a row that already carries the
                 level, the essential marker, the expiry and the attention
                 outline — and its amber/red vocabulary inverted theirs (red
                 level square = "buy this now", red cart ring = "don't"). It
                 survives on the two surfaces the user opens *to ask*: the
                 stock-item detail card and the shopping list. -->

            <!-- "Log a price" (G2: money-gated, left of
                 expiry). Opens the shared PriceEntry dialog. No emit
                 wiring beyond the optimistic close — the row's visible
                 surface doesn't depend on observations today; chunks 4/6
                 surface them in widgets/charts.
                 Hidden on phones (2026-08-15 feedback) — the row cluster was
                 taking half the width there; the page toolbar's "Log price"
                 button covers the case. -->
            <StockItemRowPriceButton
                v-if="moneyEnabled && !compact"
                :stock-item-id="item.stock_item_id"
                :item-name="item.name"
            />

            <!-- ──────────────────────────────────────────────────────
                 Right cluster — expiry / essential / open / cart.
                 Feedback 2026-06-18 (round 2): every button is `flat dense
                 round size="md"` so they read as a uniform cluster
                 (previously expiry was round, open was a square, cart was
                 sm — three different visual languages). The essential
                 flag is now interactive (toggles `is_essential`) and
                 rendered alongside the others.
            ────────────────────────────────────────────────────────── -->
            <RowActionButton
                :icon="expiry.icon"
                :color="expiry.colour ?? undefined"
                :class="expiry.cssClass ?? undefined"
                :aria-label="expiry.tooltip"
                @click.stop
            >
                <q-tooltip>{{ expiry.tooltip }}</q-tooltip>

                <!-- Unset → date picker. q-popup-proxy auto-uses a
                     dialog on mobile and a menu on desktop. -->
                <q-popup-proxy
                    v-if="!item.expiry_date"
                    transition-show="scale"
                    transition-hide="scale"
                    cover
                >
                    <q-date
                        :model-value="null"
                        mask="YYYY-MM-DD"
                        :options="dateOptionsFuture"
                        @update:model-value="onPickExpiryDate"
                    >
                        <div class="row items-center justify-end q-gutter-sm">
                            <BaseButton variant="ghost" label="Cancel" v-close-popup />
                        </div>
                    </q-date>
                </q-popup-proxy>

                <!-- Set → push-shortcut menu. -->
                <q-menu
                    v-else
                    auto-close
                    transition-show="jump-down"
                    transition-hide="jump-up"
                >
                    <q-list dense class="expiry-menu-list">
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 1)">
                            <q-item-section
                                avatar
                                style="min-width: 0; padding-right: 8px"
                            >
                                <q-icon :name="ICONS.add" size="20px" />
                            </q-item-section>
                            <q-item-section>Push expiry by 1 day</q-item-section>
                        </q-item>
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 7)">
                            <q-item-section
                                avatar
                                style="min-width: 0; padding-right: 8px"
                            >
                                <q-icon :name="ICONS.add" size="20px" />
                            </q-item-section>
                            <q-item-section>Push expiry by 7 days</q-item-section>
                        </q-item>
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 14)">
                            <q-item-section
                                avatar
                                style="min-width: 0; padding-right: 8px"
                            >
                                <q-icon :name="ICONS.add" size="20px" />
                            </q-item-section>
                            <q-item-section>Push expiry by 14 days</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item clickable class="text-negative" @click="clearExpiry">
                            <q-item-section
                                avatar
                                style="min-width: 0; padding-right: 8px"
                            >
                                <q-icon :name="ICONS.clear" size="20px" color="negative" />
                            </q-item-section>
                            <q-item-section>Clear expiry</q-item-section>
                        </q-item>
                        <q-item clickable class="text-negative" @click="openMarkAsWasted">
                            <q-item-section
                                avatar
                                style="min-width: 0; padding-right: 8px"
                            >
                                <q-icon :name="ICONS.wasted" size="20px" color="negative" />
                            </q-item-section>
                            <q-item-section>Log waste</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </RowActionButton>

            <!-- FU-365 round 2: essential-flag button removed here.
                 Essential is set-and-forget; managed on the item's detail
                 page. Row indication is the left-edge stripe. -->

            <!-- Open / in-use toggle. Primary when open so the state pops. -->
            <RowActionButton
                :icon="item.is_open ? ICONS.opened : ICONS.sealed"
                :color="item.is_open ? 'primary' : undefined"
                :loading="openBusy"
                :aria-label="item.is_open ? 'Mark as sealed' : 'Mark as open / in-use'"
                @click.stop="onToggleOpen"
            >
                <q-tooltip>
                    {{ item.is_open ? 'Mark as sealed' : 'Mark as open / in-use' }}
                </q-tooltip>
            </RowActionButton>

            <!-- Cart button — unified AddToListButton (C-7 Chunk 1).
                 Owns the state-aware render + already-on-list toggle
                 (popover when on multiple lists); kills the row's
                 hand-rolled double-toast path (FU-038). -->
            <AddToListButton
                variant="row"
                :stock-item-id="item.stock_item_id"
            />
        </q-card-section>

        <!-- C-waste — reason-only capture, fired from the expiry dropdown.
             Owned by the row so the toast + Undo closure can reach into
             both the waste API and the row's expiry data. -->
        <MarkAsWastedDialog
            v-model="markAsWastedOpen"
            :item-name="item.name"
            :subline="markAsWastedSubline"
            @submit="onMarkAsWasted"
        />
    </q-card>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import RowActionButton from 'src/components/RowActionButton.vue';
    import StockItemRowPriceButton from 'src/components/stock/StockItemRowPriceButton.vue';
    import MarkAsWastedDialog from 'src/components/stock/MarkAsWastedDialog.vue';
    import WasteApiService from 'src/services/api/wasteApiService';
    import type { WasteReason } from 'src/services/api/wasteApiService';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { usePantryBeliefs } from 'src/composables/usePantryBeliefs';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { expiryIndicatorFor } from 'src/helpers/expiryIndicator';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import { isOutOfStockSequence } from 'src/helpers/stockStatus';
    import type { StockItem } from 'src/models/stockItem';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { useLocationStore } from 'src/stores/locationStore';
    import { formatLocation, locationHasDetail } from 'src/helpers/locationDisplay';
    import { computed, ref } from 'vue';

    const props = defineProps<{
        item: StockItem;
        bulkMode?: boolean;
        selected?: boolean;
        focused?: boolean;
        peeking?: boolean;
        /**
         * PROPOSAL_STOCKTAKE_MODE §7 — passes the "this item is currently
         * in the stocktake queue" signal down from the page (the page
         * owns the server round-trip; the row just draws the outline).
         * When true, the stock-level button gets a pulsing outline that
         * matches the toolbar's Stocktake attention glow so overdue rows
         * are discoverable without opening the runner.
         */
        needsCheck?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'click', stockItemId: string): void;
        (e: 'bulk-toggle', stockItemId: string): void;
        (e: 'filter-location', stockLocationId: string): void;
        // long-press enters bulk-select on mobile.
        // The page owns the mode toggle; the row just reports the gesture.
        (e: 'long-press', stockItemId: string): void;
        // `go-to-list` retired with the "On N lists" chip.
        // The cart button owns the list interaction now.
        // `verdict-action` retired 2026-08-15 with the standalone verdict
        // chip; the ring that replaced it went too (D-10, 2026-08-19). The
        // detail page + shopping list still drive `useBuyVerdictActions` for
        // their richer surfaces.
    }>();

    const $q = useQuasar();
    const actions = useStockItemActions();
    const { moneyEnabled } = useMoneyEnabled();
    // B5 (D-10): this row used to call `useBuyVerdict(...)` here, which
    // fired one request per rendered row — the composable's cache dedupes by
    // id, so 200 distinct items meant 200 requests, to draw a ring that was
    // suppressed at low confidence (the common case). The row asks for
    // nothing now.
    // inferred belief for this row (shared module-level cache;
    // loaded once by the overview). Null when inference is off or absent.
    const { beliefFor } = usePantryBeliefs();
    const belief = computed(() => beliefFor(props.item.stock_item_id));

    // Phones drop the location line and the per-row price button — see the
    // template comments. `lt.sm` (xs) matches the 599px CSS breakpoints
    // below, so the JS-gated and CSS-gated halves flip together.
    const compact = computed(() => $q.screen.lt.sm);
    const showLocation = computed(() => !!locationName.value && !compact.value);

    // ── "Dora thinks" (P8-07) ───────────────────────────────────────────
    // Same rule PantryBeliefChip applied when this lived in the row as its
    // own pill: speak up ONLY when a genuine inference DISAGREES with the
    // recorded level. Agreement carries no new information. The hint is now
    // rendered *by the level picker* (ring + menu header) rather than beside
    // it, because it is a statement about the level, and the picker is the
    // thing that owns the level.
    const hasBelief = computed(
        () => !!belief.value
            && belief.value.is_inferred
            && belief.value.differs_from_recorded,
    );
    const BELIEF_BAND_WORD: Record<string, string> = {
        out: 'out',
        low: 'low',
        stocked: 'stocked',
    };
    const beliefBandWord = computed(() => {
        const band = belief.value?.believed_band;
        if (!band) return '';
        return BELIEF_BAND_WORD[band] ?? band;
    });
    const levelButtonAriaLabel = computed(() => {
        const base = `Stock level: ${levelName.value || 'unset'}`;
        return hasBelief.value
            ? `${base}. Dora thinks ${beliefBandWord.value}`
            : base;
    });
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const locationStore = useLocationStore();

    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);

    // ── Level / location names ──────────────────────────────────────────
    const levelName = computed(() => {
        const id = props.item.stock_level_id;
        if (!id) return '';
        return stockLevels.value.find((l) => l.stock_level_id === id)?.name ?? '';
    });
    const levelSequence = computed<number | null>(() => {
        const seq = props.item.stock_level_sequence;
        if (typeof seq === 'number') return seq;
        const id = props.item.stock_level_id;
        return stockLevels.value.find((l) => l.stock_level_id === id)?.sequence ?? null;
    });
    // The level button is text-less but coloured by the stock level.
    // Saturated branches (well/sufficient/low) ride Quasar's brand
    // semantics via the `bg-{positive|warning|negative}` utility class
    // — those are theme-tokenised. The neutral / out-of-stock branch
    // routes through `dora-bg-sunken` per R-002 (the previous
    // `bg-grey-5` was a hardcoded palette literal and broke dark
    // themes).
    const levelButtonClass = computed<string>(() => {
        const seq = levelSequence.value;
        if (seq === null) return '';
        const colour = colourForSequence(seq);
        return colour ? `bg-${colour}` : 'dora-bg-neutral';
    });
    const levelButtonStyle = computed(() => {
        // Empty-level fallback — dashed outline + page surface so the
        // button reads as "unset" without competing with a colour.
        if (levelSequence.value === null) {
            return {
                background: 'var(--surface-component)',
                border: '1px dashed color-mix(in srgb, var(--text-primary) 24%, transparent)',
            };
        }
        return {};
    });

    // C-cross Chunk 4 — show the *zone* (top-level breadcrumb node), not
    // the leaf location name. "Right shelf" → "Pantry"; full breadcrumb
    // remains in the tooltip + detail page.
    const locationBreadcrumb = computed<readonly string[]>(() => {
        const id = props.item.stock_location_id;
        if (!id) return [];
        const path = locationStore.breadcrumb(id);
        if (path.length > 0) return path;
        const flat = stockLocations.value.find((l) => l.stock_location_id === id)?.name;
        return flat ? [flat] : [];
    });
    const locationName = computed(() => formatLocation(locationBreadcrumb.value, 'zone'));
    const locationFull = computed(() => formatLocation(locationBreadcrumb.value, 'full'));
    const locationHasFullDetail = computed(() => locationHasDetail(locationBreadcrumb.value));

    // ── Expiry derived state ────────────────────────────────────────────
    // Drives the right-cluster button only. It no longer feeds the row
    // outline — that reads the server's `needs_attention` now, so the row's
    // expiry threshold and the server's can't drift (B1).
    // R-002: tone + icon + colour live in `helpers/expiryIndicator` so the
    // stock-item detail page renders the identical indicator.
    const expiry = computed(() => expiryIndicatorFor(props.item.expiry_date));

    // ── Whole-row outline + dim rules ───────────────────────────────────
    // ONE outline, server-decided (D-7). The row used to carry two —
    // WARN-amber and ALERT-red, "sort of needs attention" and "really needs
    // attention" — and a hedged alarm gets ignored. Worse, amber was the
    // collision case: an essential-low item wore an amber outline wrapped
    // around an amber level square, two different ambers touching.
    //
    // `needs_attention` comes off the DTO; severity still orders the outlined
    // set in the sort (D-9), which is where a gradient pays off without
    // spending a second colour.
    //
    // Dimming: non-essential Out items only, and it is NOT an attention
    // signal — it's the bottom of the same ramp (D-8): outlined = needs you,
    // normal = fine, dim = out but you never flagged it. Essential Out items
    // stay full opacity so the loudest "go restock" isn't quieted by a fade.
    const isOutOfStock = computed(
        () =>
            props.item.is_out_of_stock ?? isOutOfStockSequence(levelSequence.value),
    );
    const isEssential = computed(() => props.item.is_essential === true);

    const needsAttention = computed(() => props.item.needs_attention === true);

    const rowClasses = computed(() => ({
        'stock-row--dim': isOutOfStock.value && !isEssential.value,
        'stock-row--peeking': props.peeking,
        'stock-row--focused': props.focused,
        // Selection (bulk-mode tick) fills the row — L91. "peeking"
        // (splitter detail) keeps its own treatment so the two states
        // don't collide.
        'stock-row--selected': !!props.selected,
        'stock-row--attention': needsAttention.value,
    }));

    // restrict the date picker to today + future.
    // q-date passes each candidate date as `YYYY/MM/DD`; compare via
    // string ordering against today's ISO date for cheap correctness.
    const todayIsoSlash = computed(() => {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}/${mm}/${dd}`;
    });
    function dateOptionsFuture(date: string): boolean {
        return date >= todayIsoSlash.value;
    }

    async function onPickExpiryDate(value: string | null) {
        if (!value) return;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: props.item.stock_item_id,
                expiry_date: value,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Expiry set to ${value}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not set expiry.',
                caption: toastCaption(err),
            });
        }
    }

    async function clearExpiry() {
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: props.item.stock_item_id,
                expiry_date: null,
            });
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Expiry cleared.' });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear expiry.',
                caption: toastCaption(err),
            });
        }
    }

    // cart button is now `AddToListButton`; the dead
    // `cart` computed + `onCartClick` + `cartStateFor` import retired.

    // FU-365 round 2: `onToggleFlagged` + `flagBusy` retired with the
    // row-level essential button. Detail page still owns the toggle.

    // ── Open / in-use toggle ────────────────────────────────────────────
    const openBusy = ref(false);
    async function onToggleOpen() {
        // DR-5 (FU-578 #2) — opening prompts for an updated effective expiry
        // (opened milk shortens fast, opened jam barely moves — a universal
        // rule is wrong per-item). The mutation is now a *product* of the
        // dialog: a null plan means the user dismissed/cancelled it, so we
        // write nothing and leave the item sealed.
        const patch = await actions.planOpenToggle(props.item);
        if (!patch) return;
        openBusy.value = true;
        try {
            await stockItemStore.updateStockItemAsync(patch);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: patch.is_open
                    ? `Marked "${props.item.name}" as open.`
                    : `Marked "${props.item.name}" as sealed.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: toastCaption(err),
            });
        } finally {
            openBusy.value = false;
        }
    }

    // long-press handler. Bubbles up so the parent
    // can decide whether to enter bulk-mode (mobile) or ignore (desktop).
    function onLongPress() {
        emit('long-press', props.item.stock_item_id);
    }

    // ── Stock-level set ─────────────────────────────────────────────────
    async function onSetLevel(stockLevelId: string) {
        await stockItemStore.updateStockLevelAsync({
            stock_item_id: props.item.stock_item_id,
            stock_level_id: stockLevelId,
        });
    }

    // ── Mark as wasted (C-waste) ────────────────────────────────────────
    // Capture is reason-only (PROPOSAL_WASTE_MINIMISATION §5). Submit
    // posts the event + clears the row's expiry; a 5s Undo toast reverts
    // both. The dialog is owned by the row so the Undo closure can
    // remember the original expiry date independently of any prop
    // refresh that may overwrite the row during the toast window.
    const markAsWastedOpen = ref(false);
    const wasteApi = new WasteApiService();
    const markAsWastedSubline = computed<string | null>(() => {
        const parts: string[] = [];
        if (levelName.value) parts.push(levelName.value);
        if (locationName.value) parts.push(locationName.value);
        return parts.length > 0 ? parts.join(' · ') : null;
    });
    function openMarkAsWasted() {
        markAsWastedOpen.value = true;
    }
    async function onMarkAsWasted(reason: WasteReason) {
        // Capture into a local before any await — the row's props may
        // re-render with stale data while the request is in flight.
        const stockItemId = props.item.stock_item_id;
        const itemName = props.item.name;
        const originalExpiry = props.item.expiry_date ?? null;
        try {
            const { event_id } = await wasteApi.logEventAsync({
                stock_item_id: stockItemId,
                reason,
            });
            if (originalExpiry) {
                await stockItemStore.updateStockItemAsync({
                    stock_item_id: stockItemId,
                    expiry_date: null,
                });
            }
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `Logged "${itemName}" as wasted.`,
                timeout: 5000,
                actions: [
                    {
                        label: 'Undo',
                        color: 'white',
                        handler: () => {
                            void (async () => {
                                try {
                                    await wasteApi.deleteEventAsync(event_id);
                                    if (originalExpiry) {
                                        await stockItemStore.updateStockItemAsync({
                                            stock_item_id: stockItemId,
                                            expiry_date: originalExpiry,
                                        });
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
                    },
                ],
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log as wasted.',
                caption: toastCaption(err),
            });
        }
    }
</script>

<style scoped lang="scss">
    /* Expiry push-shortcut menu. Widened from the old 180px floor so the
       longest option ("Push expiry by 14 days") fits on one line, and the
       label sections never wrap regardless of font/locale — the row grows
       to fit instead. `:deep` because q-menu teleports its list to body. */
    .expiry-menu-list {
        min-width: 224px;
    }
    .expiry-menu-list :deep(.q-item__section:not(.q-item__section--avatar)) {
        white-space: nowrap;
    }

    .stock-row {
        /* 2026-08-15 feedback ("scrolling feels like it's snapping"): the
           row is now a FIXED height, not a min-height, and that height comes
           from `--stock-row-height` — the same number the page hands
           `q-virtual-scroll` as its item size (see `helpers/stockRowMetrics`).
           Uniform rows are what let the virtual scroller's arithmetic be
           exact; when it guessed 72px at a 64px row it re-measured mid-scroll
           and re-padded the spacer, which is the snap the user was seeing.
           The fallback keeps a sane height for the non-overview consumers
           that don't set the property. Bottom margin is the row gap and is
           included in the metric, so it's subtracted here. */
        height: calc(var(--stock-row-height, 64px) - 8px);
        /* Intrinsic row gap. The parent used to rely on `q-gutter-y-sm`,
           but that class is a no-op inside `q-virtual-scroll` (the virtual
           scroller sets its own item spacing and swallows container
           gutters), so once a pantry crosses the virtualisation threshold
           the rows go flush. Owning the gap on the row itself keeps the
           spacing consistent in both the ListTransition and virtual paths. */
        margin-bottom: 8px;
        position: relative;
        border-radius: 8px;
        overflow: hidden; /* clip the essential stripe to the rounded border */
        transition:
            box-shadow var(--motion-fast) var(--motion-ease),
            background-color var(--motion-fast) var(--motion-ease),
            border-color var(--motion-fast) var(--motion-ease);
        border: 1px solid var(--border-default, color-mix(in srgb, var(--text-primary) 12%, transparent));
    }
    /* Feedback 2026-06-18: the prior `translateY(-1px)` lift clipped the
       first row's outline under the page's sticky chrome and looked janky
       at the edges. Swap for a no-translation hover treatment: surface
       brightens + accent-tinted shadow + 1px border accent. Reads as a
       polished card hover without the layout jitter. */
    .stock-row:hover {
        background: color-mix(in srgb, var(--q-accent) 4%, var(--surface-component));
        border-color: color-mix(in srgb, var(--q-accent) 38%, transparent);
        box-shadow: 0 1px 6px color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .stock-row__body {
        padding: 6px 12px;
        gap: 14px; /* breathing room between image / level / name / cluster */
        height: 100%;
    }
    /* Phones: the trailing action cluster was eating roughly half the row's
       width (2026-08-15 feedback). Tighten both the gap between the row's
       sections and the buttons themselves — the price button is already gone
       there (page toolbar owns it), so this is the remaining squeeze.
       Left padding is the exception and stays at the desktop 12px: the
       essential stripe is absolutely positioned on the row's left edge, so
       the tightened 8px left only 3px between stripe and level button and
       the two read as one squished blob (2026-08-16 feedback). Desktop's
       7px was never reported — this restores that gap rather than opening
       a new one. */
    @media (max-width: 599px) {
        .stock-row__body {
            padding: 4px 8px 4px 12px;
            gap: 8px;
        }
        .stock-row__body :deep(.dora-btn--icon) {
            min-width: 30px;
            min-height: 30px;
            width: 30px;
            height: 30px;
            margin-left: -2px;
        }
        .stock-row__body :deep(.dora-btn--icon .q-icon) {
            font-size: 19px;
        }
    }
    /* FU-365 round 2: essentials get a secondary-toned left-edge stripe
       — the sole row-level indicator now that the flag button has been
       retired from the right cluster (essential is set-and-forget). A
       little thicker than before so it scans without an accompanying
       icon. Colour matches the "Essential" footer count + filter chip.
       2026-08-16 feedback: paints in the indicator-grade secondary, not
       `--q-secondary` — the latter is the toolbar background in every
       dark theme, which left the stripe all but invisible there.
       2026-08-20 feedback: the 2026-08-17 tapered bracket (16px wide,
       clipped back to 5px over the first/last 14px) is reverted — at a
       56px painted row height half the element was taper, so it read as
       a lopsided hexagon rather than a tab, and its diagonals crossed
       the warn/alert ring at an angle. Back to the straight bar, one
       pixel thicker. The row's `overflow: hidden` + 8px radius rounds
       the two outer corners for free. */
    .stock-row__essential-stripe {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 6px;
        background: var(--brand-secondary-strong);
        pointer-events: none;
    }

    /* One attention outline, one token (D-7). Amber's gone: it meant "sort
       of needs attention", and it sat directly around the amber Low level
       square. An outline firing on 5% of rows works; one firing on 40% is
       wallpaper, which is what two tiers produced. */
    .stock-row--attention {
        border-color: var(--q-negative);
        box-shadow: inset 0 0 0 1px var(--q-negative);
    }

    /* Selection fills the row (L91). Peek + focused keep their own
       outline treatments so the three states are visually distinct. */
    .stock-row--selected {
        background: color-mix(in srgb, var(--q-primary) 14%, var(--surface-component));
    }
    .stock-row--peeking {
        outline: 2px solid var(--q-primary);
        outline-offset: -2px;
    }
    .stock-row--focused {
        outline: 2px dashed var(--q-accent);
        outline-offset: -2px;
    }
    .stock-row--dim {
        opacity: 0.62;
    }

    /* Big text-less level button — colour comes from `levelButtonStyle`
       (Quasar palette CSS variables), so light/dark themes inherit it. */
    .stock-row__level-btn {
        width: 32px;
        height: 32px;
        min-width: 32px;
        min-height: 32px;
        border-radius: var(--radius-sm, 4px);
        padding: 0;
        /* Needed so the pulse box-shadow doesn't get clipped by any
           overflow parent — the shadow radiates outside the 32px box. */
        position: relative;
    }

    /* PROPOSAL_STOCKTAKE_MODE §7 — passive discovery outline for items
       currently in the stocktake queue. Same "brand-accent pulse" the
       toolbar's Stocktake attention glow uses (see BaseButton
       `dora-btn--attention`), scoped to the tiny 32px level button.
       Users notice a due item on the Overview without having to open
       the runner.

       2026-08-15 feedback: the original pulse was a ring expanding from 0 to
       6px while fading to nothing — at a 32px button that is a faint halo
       most people never notice. Strengthened rather than replaced (the user
       asked for more of the same effect, not a different one): the ring now
       *rests* at a visible 2px hold and expands to 7px, the accent mix runs
       85% → 20% instead of 55% → 0%, and the button itself breathes a hair
       (scale 1.06) so the movement registers in peripheral vision. It's a
       slow 2.2s ease so it reads as a heartbeat, not a blink — the thing
       that makes a pulse annoying is frequency, not amplitude. */
    .stock-row__level-btn--needs-check {
        animation: stock-row__level-needs-check-pulse 2.2s ease-in-out infinite;
    }
    @keyframes stock-row__level-needs-check-pulse {
        0%, 100% {
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand-accent) 85%, transparent);
            transform: scale(1);
        }
        50% {
            box-shadow: 0 0 0 7px color-mix(in srgb, var(--brand-accent) 20%, transparent);
            transform: scale(1.06);
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .stock-row__level-btn--needs-check {
            animation: none;
            transform: none;
            box-shadow: 0 0 0 2px var(--brand-accent);
        }
    }

    /* ── "Dora thinks" on the picker (2026-08-15 feedback) ───────────────
       The user's own sketch: border the picker with a GAP between the line
       and the box edge. Two stacked rings do that with one box-shadow — the
       inner ring paints the page surface as the gap, the outer is the amber
       line. Amber matches the pill this replaced, and the same
       `--semantic-warning` the belief hint used, so the meaning carries over.
       Loses to the stocktake pulse when both apply: that one is an
       instruction ("check this"), this one is an observation. */
    .stock-row__level-btn--belief:not(.stock-row__level-btn--needs-check) {
        box-shadow:
            0 0 0 2px var(--surface-component),
            0 0 0 4px var(--semantic-warning);
    }

    /* Belief header inside the level menu — replaces the redundant "Set
       level" caption when Dora has something to say. */
    .stock-row__belief-header {
        color: var(--text-primary);
        font-weight: 600;
        line-height: 1.3;
        padding-bottom: var(--space-2);
    }
    .stock-row__belief-reason {
        font-weight: 400;
        font-size: calc(var(--font-size-xs) * 1rem);
        color: var(--text-secondary);
        white-space: normal;
    }
    /* Current level = highlighted row, matching the `active-class` pattern
       used by the settings nav + shopping-list rail. `:deep` because q-menu
       teleports its list to body. */
    :deep(.stock-row__level-option--active) {
        background: var(--surface-sunken);
        font-weight: 600;
        color: var(--text-primary);
    }

    /* Name + zone — emphasised name (L79), light zone with hover
       affordance (L81). */
    .stock-row__name-zone {
        flex: 1 1 auto;
        min-width: 0; /* allow ellipsis inside flex */
    }
    /* Second line under the name (the location zone). The DR-8 min-height
       reserve that used to sit here is gone: it existed to stop the async
       belief chip reflowing the row on arrival, and that chip has moved onto
       the level picker. What's left is synchronous, so the line is simply
       absent when there's no location instead of holding an empty 20px that
       pushed the name off centre (2026-08-15 feedback). Row height is fixed
       regardless, so nothing reflows either way. */
    .stock-row__meta {
        gap: 6px;
    }
    .stock-row__name {
        font-weight: 600;
        font-size: 1.05rem;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    /* DR-9 (FU-578 #15b): on phones the trailing action cluster squeezes the
       name column so hard that names truncate at ~10 chars ("Barilla Pa…").
       Let the name wrap to two lines there instead of a single ellipsised line
       so it's actually readable; desktop keeps the one-line ellipsis. */
    @media (max-width: 600px) {
        .stock-row__name {
            white-space: normal;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            line-clamp: 2;
            -webkit-box-orient: vertical;
        }
    }
    .stock-row__zone {
        all: unset;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        font-size: 0.8rem;
        color: var(--text-secondary, color-mix(in srgb, var(--text-primary) 64%, transparent));
        padding: 2px 4px;
        margin-left: -4px;
        border-radius: 4px;
        transition: background-color var(--motion-fast) var(--motion-ease);
    }
    .stock-row__zone:hover {
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        color: var(--text-primary);
    }

</style>
