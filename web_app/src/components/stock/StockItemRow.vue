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
                    { 'stock-row__level-btn--needs-check': needsCheck },
                ]"
                :style="levelButtonStyle"
                :aria-label="`Stock level: ${levelName || 'unset'}`"
                @click.stop
            >
                <q-tooltip>
                    {{ levelName ? `Level: ${levelName}` : 'Set stock level' }}
                </q-tooltip>
                <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                    <q-list dense style="min-width: 200px">
                        <q-item-label header>Set level</q-item-label>
                        <q-item
                            v-for="level in stockLevels"
                            :key="level.stock_level_id"
                            clickable
                            v-close-popup
                            @click.stop="onSetLevel(level.stock_level_id)"
                        >
                            <q-item-section avatar>
                                <q-avatar
                                    :color="colourForSequence(level.sequence) ?? undefined"
                                    :class="{ 'dora-bg-neutral': !colourForSequence(level.sequence) }"
                                    size="14px"
                                />
                            </q-item-section>
                            <q-item-section>{{ level.name }}</q-item-section>
                            <q-item-section v-if="level.stock_level_id === item.stock_level_id" side>
                                <q-icon :name="ICONS.check" size="16px" />
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </BaseButton>

            <!-- ──────────────────────────────────────────────────────
                 Name (emphasised) + main zone (L79 / L81).
                 Zone is lightly clickable — bubble up filter-to-location;
                 full breadcrumb stays in the tooltip + detail page.
            ────────────────────────────────────────────────────────── -->
            <div class="stock-row__name-zone column items-start">
                <div class="stock-row__name">{{ item.name }}</div>
                <!-- flex `gap` (not q-gutter) so the wrapper can't collide
                     with any parent gutter scheme — R-027/ADR-023. Reserves a
                     stable min-height (DR-8 #52) so the async belief chip fades
                     into existing space instead of growing the row after paint. -->
                <div class="row items-center no-wrap stock-row__meta">
                    <button
                        v-if="locationName"
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
                    <!-- Zero-Input Pantry inferred level (additive;
                         beside the recorded level, never replacing it). -->
                    <PantryBeliefChip :belief="belief" />
                </div>
            </div>

            <q-space />

            <!-- "should I buy this?" verdict. Renders inline
                 left of the cart cluster because that's where the user
                 is deciding whether to add to the list. Silent on
                 low-confidence verdicts (Charter P3: don't dashboard
                 every row) and when the feature flag is off. Emits the
                 action up so the page can reuse the existing cart /
                 stock-level mutation seams — the oracle emits intent,
                 not new mutation paths. -->
            <BuyVerdictBadge
                v-if="verdictShouldShow"
                :verdict="verdict"
                @action="(kind) => emit('verdict-action', item.stock_item_id, kind)"
            />

            <!-- "Log a price" (G2: money-gated, left of
                 expiry). Opens the shared PriceEntry dialog. No emit
                 wiring beyond the optimistic close — the row's visible
                 surface doesn't depend on observations today; chunks 4/6
                 surface them in widgets/charts. -->
            <StockItemRowPriceButton
                v-if="moneyEnabled"
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
    import BuyVerdictBadge from 'src/components/stock/BuyVerdictBadge.vue';
    import StockItemRowPriceButton from 'src/components/stock/StockItemRowPriceButton.vue';
    import PantryBeliefChip from 'src/components/stock/PantryBeliefChip.vue';
    import MarkAsWastedDialog from 'src/components/stock/MarkAsWastedDialog.vue';
    import WasteApiService from 'src/services/api/wasteApiService';
    import type { WasteReason } from 'src/services/api/wasteApiService';
    import { useBuyVerdict } from 'src/composables/useBuyVerdict';
    import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { usePantryBeliefs } from 'src/composables/usePantryBeliefs';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import { isLowStockSequence, isOutOfStockSequence } from 'src/helpers/stockStatus';
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
        // buy-verdict badge emits its one-tap action up so the
        // page can reuse the existing cart / stock-level mutation seams.
        (e: 'verdict-action', stockItemId: string,
            kind: 'add_to_list' | 'skip' | 'mark_stocked'
                | 'remove_from_list' | 'none'): void;
    }>();

    const $q = useQuasar();
    const actions = useStockItemActions();
    const { moneyEnabled } = useMoneyEnabled();
    const { buyVerdictEnabled } = useBuyVerdictEnabled();
    // fetch the verdict for this row (per-item cache in the
    // composable keeps re-mounts free). Show only medium/high
    // confidence: low-confidence noise on every row breaks Charter P3.
    const { verdict } = useBuyVerdict(props.item.stock_item_id);
    // inferred belief for this row (shared module-level cache;
    // loaded once by the overview). Null when inference is off or absent.
    const { beliefFor } = usePantryBeliefs();
    const belief = computed(() => beliefFor(props.item.stock_item_id));
    const verdictShouldShow = computed(() =>
        buyVerdictEnabled.value
        && verdict.value !== null
        && verdict.value.confidence !== 'low',
    );
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
    // Drives both the right-cluster button and the row-outline tone
    // (status → whole-row outline, decision 6).
    type ExpiryTone = 'none' | 'ok' | 'soon' | 'expired';
    const expiryTone = computed<ExpiryTone>(() => {
        const date = props.item.expiry_date;
        if (!date) return 'none';
        const ms = new Date(date).getTime();
        if (ms < Date.now()) return 'expired';
        if ((ms - Date.now()) / 86_400_000 <= 7) return 'soon';
        return 'ok';
    });
    // R-002: neutral "no expiry" routes through `dora-text-muted` (no
    // colour prop); saturated branches stay on Quasar semantics.
    // `colour: null` signals "no Quasar colour — use cssClass for the
    // muted look".
    const expiry = computed<{
        icon: string;
        colour: string | null;
        cssClass: string | null;
        tooltip: string;
    }>(() => {
        const date = props.item.expiry_date;
        switch (expiryTone.value) {
            case 'none':
                return {
                    icon: ICONS.event_available,
                    colour: null,
                    cssClass: 'dora-text-muted',
                    tooltip: 'No expiry set — click to push or set one',
                };
            case 'expired':
                return { icon: ICONS.error, colour: 'negative', cssClass: null, tooltip: `Expired ${date}` };
            case 'soon':
                return { icon: ICONS.event_busy, colour: 'warning', cssClass: null, tooltip: `Expires ${date}` };
            case 'ok':
            default:
                return { icon: ICONS.event_available, colour: 'positive', cssClass: null, tooltip: `Expires ${date}` };
        }
    });

    // ── Whole-row outline + dim rules (Model C, round 8) ────────────────
    // Unified rule with `hasAlert` in useStockFilters so the row outline
    // and the "Needs attention" footer count + filter chip describe the
    // SAME set of items:
    //   • WARN (amber): essential AND Low, OR expiring within 7 days.
    //   • ALERT (red):  essential AND Out, OR already expired.
    // Dimming: non-essential Out items only. Essential Out items stay
    // full opacity so the loudest "go restock" signal isn't quieted by
    // the fade.
    const isOutOfStock = computed(
        () =>
            props.item.is_out_of_stock ?? isOutOfStockSequence(levelSequence.value),
    );
    const isLowStock = computed(
        () =>
            props.item.is_low_stock ?? isLowStockSequence(levelSequence.value),
    );
    const isEssential = computed(() => props.item.is_essential === true);

    const isAlertRow = computed(
        () =>
            (isEssential.value && isOutOfStock.value) ||
            expiryTone.value === 'expired',
    );
    const isWarnRow = computed(
        () =>
            !isAlertRow.value &&
            ((isEssential.value && isLowStock.value) ||
                expiryTone.value === 'soon'),
    );

    const rowClasses = computed(() => ({
        'stock-row--dim': isOutOfStock.value && !isEssential.value,
        'stock-row--peeking': props.peeking,
        'stock-row--focused': props.focused,
        // Selection (bulk-mode tick) fills the row — L91. "peeking"
        // (splitter detail) keeps its own treatment so the two states
        // don't collide.
        'stock-row--selected': !!props.selected,
        'stock-row--alert': isAlertRow.value,
        'stock-row--warn': isWarnRow.value,
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
        /* Feedback 2026-06-18 (round 3): rows felt too tall after the
           round-1 spacing bump. Bring the min-height down a notch while
           keeping the gap+padding that gave it breathing room. */
        min-height: 56px;
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
    }
    /* FU-365 round 2: essentials get a secondary-toned left-edge stripe
       — the sole row-level indicator now that the flag button has been
       retired from the right cluster (essential is set-and-forget). A
       little thicker than before so it scans without an accompanying
       icon. Colour matches the "Essential" footer count + filter chip. */
    .stock-row__essential-stripe {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 5px;
        background: var(--q-secondary);
        pointer-events: none;
    }

    /* Status outline-by-status (decision 6). Colours via theme tokens. */
    .stock-row--warn {
        border-color: var(--q-warning);
        box-shadow: inset 0 0 0 1px var(--q-warning);
    }
    .stock-row--alert {
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
       the runner. */
    .stock-row__level-btn--needs-check {
        animation: stock-row__level-needs-check-pulse 2s ease-in-out infinite;
    }
    @keyframes stock-row__level-needs-check-pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand-accent) 55%, transparent);
        }
        50% {
            box-shadow: 0 0 0 6px color-mix(in srgb, var(--brand-accent) 0%, transparent);
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .stock-row__level-btn--needs-check {
            animation: none;
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand-accent) 45%, transparent);
        }
    }

    /* Name + zone — emphasised name (L79), light zone with hover
       affordance (L81). */
    .stock-row__name-zone {
        flex: 1 1 auto;
        min-width: 0; /* allow ellipsis inside flex */
    }
    /* Second line under the name (location zone + async belief chip). The
       reserved min-height keeps the row a constant height whether or not a
       belief chip has arrived yet, so a late chip fades in without reflowing
       neighbours (DR-8 / FU-578 #52). `gap` lives here (not inline) so the
       chip and zone never touch. */
    .stock-row__meta {
        gap: 6px;
        min-height: 20px;
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
