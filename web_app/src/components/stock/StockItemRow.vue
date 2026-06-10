<template>
    <!--
        C-1 Stock Overview Chunk 3 — row rebuild ("kill the chip, one focus action").
        Closes §2.1 + §2.2 + L70 / L75 / L76 / L77 / L78 / L79 / L80 / L82 / L85 /
        L90 / L91 (+ L81 main-zone display, L66 essential-as-filter).

        Left → right:
          [bulk?]  [■ LEVEL button]  Name (emphasised) · Zone  [img?]
            · · · spacer · · ·  [⏰ expiry] [🍽 #recipes] [open] [🛒 cart]

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
        <q-card-section class="row items-center no-wrap q-py-sm q-gutter-x-sm">
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
            <q-btn
                flat
                dense
                class="stock-row__level-btn"
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
                                    :color="colourForSequence(level.sequence)"
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
            </q-btn>

            <!-- ──────────────────────────────────────────────────────
                 Name (emphasised) + main zone (L79 / L81).
                 Zone is lightly clickable — bubble up filter-to-location;
                 full breadcrumb stays in the tooltip + detail page.
            ────────────────────────────────────────────────────────── -->
            <div class="stock-row__name-zone column items-start">
                <div class="stock-row__name">{{ item.name }}</div>
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
            </div>

            <!-- ──────────────────────────────────────────────────────
                 Image slot (FU-106 + C-cross §2.8 + FU-033).
                 Renders only when the user opts in (showStockImages).
                 Server falls back to a linked product's image when the
                 stock item has none of its own; if both are absent the
                 server 404s and the SPA shows the placeholder.
            ────────────────────────────────────────────────────────── -->
            <div
                v-if="showStockImages"
                class="stock-row__image"
                :aria-hidden="true"
            >
                <img
                    v-if="item.has_image && !imgFailed"
                    :src="stockItemImageUrl(item.stock_item_id)"
                    :alt="item.name"
                    @error="imgFailed = true"
                />
                <q-icon
                    v-else
                    :name="ICONS.image"
                    size="20px"
                    class="dora-text-muted"
                />
            </div>

            <q-space />

            <!-- ──────────────────────────────────────────────────────
                 Right cluster — expiry / #recipes / open / cart.
                 C-1 Chunk 4 / L86–L88: expiry button in the right
                 cluster. Two behaviours by state:
                   - **No expiry set** → q-date picker (L87) so the
                     user can pin a real date in one tap.
                   - **Expiry set** → +1 / +7 / +14 / Clear menu
                     (L88), replacing the old +7/+30/Clear.
            ────────────────────────────────────────────────────────── -->
            <q-btn
                flat
                dense
                round
                size="sm"
                :icon="expiry.icon"
                :color="expiry.colour"
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
                            <q-btn flat no-caps label="Cancel" v-close-popup />
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
                    <q-list dense style="min-width: 180px">
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 1)">
                            <q-item-section>Push expiry +1 day</q-item-section>
                        </q-item>
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 7)">
                            <q-item-section>Push expiry +7 days</q-item-section>
                        </q-item>
                        <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 14)">
                            <q-item-section>Push expiry +14 days</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item clickable @click="clearExpiry">
                            <q-item-section class="text-negative">Clear expiry</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>

            <!-- # recipes (decision 5 — kept; relabel later in C-2). -->
            <q-btn
                v-if="recipesUsingItem.length > 0"
                flat
                dense
                round
                size="sm"
                :icon="ICONS.restaurant"
                color="primary"
                :aria-label="`Used in ${recipesUsingItem.length} recipe(s)`"
                @click.stop="actions.seeRecipesUsing(item.stock_item_id)"
            >
                <q-badge floating color="primary">
                    {{ recipesUsingItem.length }}
                </q-badge>
                <q-tooltip>
                    <div class="text-weight-bold q-mb-xs">Used in recipes</div>
                    <div
                        v-for="r in recipesUsingItem"
                        :key="r.recipe_id"
                    >
                        {{ r.name }}
                    </div>
                </q-tooltip>
            </q-btn>

            <!-- Open / in-use toggle (decision 3 — kept in-row). -->
            <q-btn
                flat
                dense
                size="sm"
                :icon="item.is_open ? ICONS.lock_open : ICONS.lock"
                :color="item.is_open ? 'secondary' : undefined"
                :loading="openBusy"
                @click.stop="onToggleOpen"
            >
                <q-tooltip>
                    {{ item.is_open ? 'Mark as sealed' : 'Mark as open / in-use' }}
                </q-tooltip>
            </q-btn>

            <!-- Cart button — unified AddToListButton (C-7 Chunk 1).
                 Owns the state-aware render + already-on-list toggle
                 (popover when on multiple lists); kills the row's
                 hand-rolled double-toast path (FU-038). -->
            <AddToListButton
                variant="row"
                :stock-item-id="item.stock_item_id"
            />
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { stockItemImageUrl } from 'src/services/api/stockItemApiService';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import { isOutOfStockSequence } from 'src/helpers/stockStatus';
    import type { StockItem } from 'src/models/stockItem';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useRecipeStore } from 'src/stores/recipeStore';
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
    }>();

    const emit = defineEmits<{
        (e: 'click', stockItemId: string): void;
        (e: 'bulk-toggle', stockItemId: string): void;
        (e: 'filter-location', stockLocationId: string): void;
        // C-1 Chunk 5 / L72 — long-press enters bulk-select on mobile.
        // The page owns the mode toggle; the row just reports the gesture.
        (e: 'long-press', stockItemId: string): void;
        // C-1 Chunk 3 — `go-to-list` retired with the "On N lists" chip.
        // The cart button owns the list interaction now.
    }>();

    const $q = useQuasar();
    const actions = useStockItemActions();
    // C-1 Chunk 6 / FU-033 — defensive fallback. If the bytes endpoint
    // 404s mid-render (race with a delete, transient error), drop the
    // <img> rather than show a broken icon — placeholder takes over.
    const imgFailed = ref(false);

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const locationStore = useLocationStore();
    const recipeStore = useRecipeStore();
    const { showStockImages } = useImagePrefs();

    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);
    const { recipes } = storeToRefs(recipeStore);

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
    // The level button is text-less but coloured by the stock level. The
    // colour is sourced from `colourForSequence` so light/dark themes
    // (Pesto, Cherry Cola) both inherit the palette correctly, and renaming
    // a level doesn't change its colour.
    const levelButtonStyle = computed(() => {
        const seq = levelSequence.value;
        const colour = seq !== null ? colourForSequence(seq) : null;
        // `getStockLevelColour` returns Quasar palette names ("positive",
        // "warning"…); we map those to the CSS variables Quasar exposes
        // so a single style binding covers all themes.
        if (!colour) {
            return {
                background: 'var(--surface-component)',
                border: '1px dashed color-mix(in srgb, var(--text-primary) 24%, transparent)',
            };
        }
        return { background: `var(--q-${colour})` };
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

    // ── Recipes referencing this item ───────────────────────────────────
    const recipesUsingItem = computed(() => {
        const id = props.item.stock_item_id;
        const out: { recipe_id: string; name: string }[] = [];
        for (const r of recipes.value) {
            if (r.ingredients.some((ing) => ing.stock_item_id === id)) {
                out.push({ recipe_id: r.recipe_id, name: r.name });
            }
        }
        return out;
    });

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
    const expiry = computed(() => {
        const date = props.item.expiry_date;
        switch (expiryTone.value) {
            case 'none':
                return {
                    icon: ICONS.event_available,
                    colour: 'grey-5',
                    tooltip: 'No expiry set — click to push or set one',
                };
            case 'expired':
                return { icon: ICONS.error, colour: 'negative', tooltip: `Expired ${date}` };
            case 'soon':
                return { icon: ICONS.event_busy, colour: 'orange-9', tooltip: `Expires ${date}` };
            case 'ok':
            default:
                return { icon: ICONS.event_available, colour: 'positive', tooltip: `Expires ${date}` };
        }
    });

    // ── Whole-row outline + dim rules (decision 6 + L91) ────────────────
    const isOutOfStock = computed(
        () =>
            props.item.is_out_of_stock ?? isOutOfStockSequence(levelSequence.value),
    );
    const rowClasses = computed(() => ({
        'stock-row--dim': isOutOfStock.value,
        'stock-row--peeking': props.peeking,
        'stock-row--focused': props.focused,
        // Selection (bulk-mode tick) fills the row — L91. "peeking"
        // (splitter detail) keeps its own treatment so the two states
        // don't collide.
        'stock-row--selected': !!props.selected,
        // Outline-by-status: amber expiring-soon / red out-or-expired.
        // "Out" takes the same tone as "expired" because both demand
        // the same action (restock / discard).
        'stock-row--alert': isOutOfStock.value || expiryTone.value === 'expired',
        'stock-row--warn': !isOutOfStock.value && expiryTone.value === 'soon',
    }));

    // C-1 Chunk 4 / L87 — restrict the date picker to today + future.
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
                caption: describeApiError(err) || '',
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
                caption: describeApiError(err) || '',
            });
        }
    }

    // C-7 Chunk 1 — cart button is now `AddToListButton`; the dead
    // `cart` computed + `onCartClick` + `cartStateFor` import retired.

    // ── Open / in-use toggle ────────────────────────────────────────────
    const openBusy = ref(false);
    async function onToggleOpen() {
        const next = !props.item.is_open;
        openBusy.value = true;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: props.item.stock_item_id,
                is_open: next,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next
                    ? `Marked "${props.item.name}" as open.`
                    : `Marked "${props.item.name}" as sealed.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            openBusy.value = false;
        }
    }

    // C-1 Chunk 5 / L72 — long-press handler. Bubbles up so the parent
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
</script>

<style scoped lang="scss">
    .stock-row {
        /* L78: rows get taller. ~64px target with comfortable padding. */
        min-height: 64px;
        transition:
            box-shadow var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease),
            background-color var(--motion-fast) var(--motion-ease),
            border-color var(--motion-fast) var(--motion-ease);
        border: 1px solid var(--border-default, color-mix(in srgb, var(--text-primary) 12%, transparent));
    }
    .stock-row:hover {
        box-shadow: var(--elevation-card-hover);
        transform: translateY(-1px);
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
    }

    /* Name + zone — emphasised name (L79), light zone with hover
       affordance (L81). */
    .stock-row__name-zone {
        flex: 1 1 auto;
        min-width: 0; /* allow ellipsis inside flex */
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

    /* Image slot. Renders an <img> when has_image; otherwise a neutral
       placeholder (sunken square with an "image" glyph). */
    .stock-row__image {
        width: 40px;
        height: 40px;
        flex: 0 0 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: var(--radius-sm, 4px);
        background: var(--surface-sunken, color-mix(in srgb, var(--text-primary) 6%, transparent));
        overflow: hidden;
    }
    .stock-row__image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
</style>
