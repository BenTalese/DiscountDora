<template>
    <div
        class="sl-row sl-row--hoverable"
        :class="{
            'sl-row--reorderable': canReorder,
            'sl-row--ticked': line.is_ticked,
            'sl-row--focused': focused,
            'sl-row--nested': nested,
            'sl-row--product-only': productOnly,
        }"
    >
        <!-- Decorative grip only — the whole row is the draggable element
             (R-022, whole-row mode). Hidden on touch, where pointer DnD does
             not exist and the arrows in the action cell are the real path. -->
        <div v-if="canReorder" class="sl-row__grip dora-dnd-handle">
            <q-icon :name="ICONS.drag_indicator" size="16px" />
            <BaseTooltip>Drag to reorder</BaseTooltip>
        </div>

        <!-- Quantity. A tile at rest, a stepper on approach (owner call
             2026-08-31). The stepper buttons are always in the layout and only
             their opacity changes, so revealing them cannot reflow the row —
             a hover that shoved the money column sideways would have
             reintroduced the very misalignment this chunk exists to fix.
             Touch has no hover, so tapping the tile arms the row instead. -->
        <div class="sl-row__qty" :class="{ 'sl-row__qty--armed': qtyArmed }">
            <BaseButton
                variant="icon"
                size="sm"
                class="sl-row__step"
                :icon="ICONS.remove"
                aria-label="One fewer"
                :disable="lineDone || (line.quantity ?? 0) <= 0"
                @click="emit('adjust-quantity', -1)"
            />
            <button
                type="button"
                class="sl-row__tile"
                :disabled="lineDone"
                :aria-label="`Quantity ${line.quantity ?? 0} — edit`"
                @click="onTileClick"
            >
                <input
                    v-if="editingQty"
                    ref="qtyInput"
                    class="sl-row__tile-input"
                    type="number"
                    min="0"
                    :value="line.quantity ?? ''"
                    @blur="onQtyCommit"
                    @keydown.enter.prevent="($event.target as HTMLInputElement).blur()"
                />
                <span v-else>{{ line.quantity ?? '—' }}</span>
            </button>
            <BaseButton
                variant="icon"
                size="sm"
                class="sl-row__step"
                :icon="ICONS.add"
                aria-label="One more"
                :disable="lineDone"
                @click="emit('adjust-quantity', 1)"
            />
        </div>

        <!-- The name leads, at the size of the thing you actually read. It was
             losing to a larger money figure and three chip variants; the
             metadata below it is now typographically subordinate rather than
             competing. -->
        <div class="sl-row__main">
            <div class="sl-row__namerow">
                <router-link
                    v-if="!nested && line.stock_item_id"
                    :to="`/stock/${line.stock_item_id}`"
                    class="sl-row__name"
                    :class="{ 'sl-row__name--struck': line.is_ticked }"
                >
                    {{ line.stock_item_name }}
                </router-link>
                <span v-else class="sl-row__name sl-row__name--plain">
                    <q-icon
                        v-if="nested || productOnly"
                        :name="ICONS.shopping_bag"
                        size="14px"
                        class="q-mr-xs dora-text-muted"
                    />
                    {{ line.stock_item_name }}
                    <BaseTooltip v-if="productOnly">
                        Product only — no linked stock item on this list
                    </BaseTooltip>
                    <BaseTooltip v-else-if="nested">Nested product</BaseTooltip>
                </span>
                <BuyVerdictBadgeInline
                    v-if="!nested && line.stock_item_id"
                    :stock-item-id="line.stock_item_id"
                    @action="emit('verdict-action', $event)"
                />
            </div>

            <!-- One caption line carrying what used to be three chip shapes
                 plus an outlined select. These are all *about* the line rather
                 than actions on it, so they read as one subordinate sentence
                 instead of four competing blocks. -->
            <div class="sl-row__meta">
                <BaseDropdown
                    v-if="storeOptions.length > 0"
                    flat
                    dense
                    no-caps
                    class="sl-row__metabtn"
                    :disable="lineDone"
                    :label="storeLabel"
                >
                    <q-list dense style="min-width: 180px">
                        <q-item
                            v-close-popup
                            clickable
                            :active="!line.planned_store_id"
                            @click="emit('planned-store', null)"
                        >
                            <q-item-section class="dora-text-muted">
                                {{ storeEmptyText }}
                            </q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item
                            v-for="opt in storeOptions"
                            :key="opt.value"
                            v-close-popup
                            clickable
                            :active="line.planned_store_id === opt.value"
                            @click="emit('planned-store', opt.value)"
                        >
                            <q-item-section>{{ opt.label }}</q-item-section>
                        </q-item>
                    </q-list>
                    <BaseTooltip>
                        Where you plan to buy this. Follow the usual store to
                        leave it unset.
                    </BaseTooltip>
                </BaseDropdown>

                <BaseDropdown
                    v-if="line.preferred_buys && line.preferred_buys.length > 0"
                    flat
                    dense
                    no-caps
                    class="sl-row__metabtn"
                    :icon="ICONS.lightbulb"
                    :disable="lineDone"
                    :label="buyHintLabel ?? 'Buy hint'"
                >
                    <q-list dense>
                        <q-item
                            v-for="pb in line.preferred_buys"
                            :key="pb.preferred_buy_id"
                            v-close-popup
                            clickable
                            :active="line.preferred_buy_id === pb.preferred_buy_id"
                            @click="emit('pick-hint', pb.preferred_buy_id)"
                        >
                            <q-item-section>{{ pb.label }}</q-item-section>
                        </q-item>
                        <template v-if="line.preferred_buy_id">
                            <q-separator />
                            <q-item v-close-popup clickable @click="emit('pick-hint', null)">
                                <q-item-section class="dora-text-muted">
                                    Clear hint
                                </q-item-section>
                            </q-item>
                        </template>
                    </q-list>
                </BaseDropdown>

                <span v-if="addedViaLabel" class="sl-row__note">
                    <q-icon :name="ICONS.auto_awesome" size="12px" />
                    {{ addedViaLabel }}
                </span>
                <span v-if="provenanceLabel" class="sl-row__note">
                    {{ provenanceLabel }}
                </span>
            </div>

            <!-- Online offers. Deliberately still their own row and their own
                 grammar: they answer "there is a deal on this", feed no total,
                 and only exist on a products install (T2). Absent leaves no
                 hole — the caption above is the row's normal resting state. -->
            <div v-if="line.offers.length > 0" class="sl-row__offers">
                <q-chip
                    v-for="offer in line.offers"
                    :key="offer.product_id"
                    dense
                    square
                    size="sm"
                    clickable
                    :outline="!isChosen(offer.product_id)"
                    class="sl-row__offer"
                    :class="{ 'sl-row__offer--chosen': isChosen(offer.product_id) }"
                    :icon="ICONS.local_offer"
                    :disable="lineDone"
                    @click="emit('pick-offer', offer.product_id)"
                >
                    {{ offer.price_now != null ? formatMoney(offer.price_now) : '—' }}
                    at {{ offer.store_name }}
                    <span v-if="offerSavings(offer) > 0" class="sl-row__offersave">
                        save {{ formatMoney(offerSavings(offer)) }}
                    </span>
                    <BaseTooltip>
                        {{ offer.brand ? `${offer.brand} — ` : '' }}{{ offer.name }}
                        <span v-if="offer.size"> ({{ offer.size }})</span>
                        <span v-if="offer.price_was != null && offer.price_now != null">
                            · RRP {{ formatMoney(offer.price_was) }}
                        </span>
                        · Tap to buy this one — it becomes the line's store
                    </BaseTooltip>
                </q-chip>
            </div>
        </div>

        <!-- Money reads as type, not as a control: a draft price is a
             server-resolved estimate, and the thing that edits it is the shop
             face. Tabular so the column scans down the list. -->
        <div v-if="moneyEnabled" class="sl-row__money">
            <div v-if="price > 0" class="sl-row__amount">~{{ formatMoney(price) }}</div>
            <div v-if="price > 0 && line.prefill_source_label" class="sl-row__amountnote">
                {{ line.prefill_source_label }}
            </div>
        </div>

        <!-- Reorder arrows sit with delete rather than in a stacked column of
             their own. Revealed on approach where there is a pointer; always
             present where there isn't, because hover-only is a loss on touch
             and the arrows are the only reorder path a thumb has. -->
        <div class="sl-row__actions">
            <template v-if="canReorder">
                <BaseButton
                    variant="icon"
                    size="sm"
                    class="sl-row__act"
                    :icon="ICONS.collapse"
                    aria-label="Move up"
                    :disable="isFirst"
                    @click="emit('move', -1)"
                >
                    <BaseTooltip>Move up</BaseTooltip>
                </BaseButton>
                <BaseButton
                    variant="icon"
                    size="sm"
                    class="sl-row__act"
                    :icon="ICONS.expand"
                    aria-label="Move down"
                    :disable="isLast"
                    @click="emit('move', 1)"
                >
                    <BaseTooltip>Move down</BaseTooltip>
                </BaseButton>
            </template>
            <BaseButton
                variant="danger-icon"
                size="sm"
                :icon="ICONS.delete_outline"
                aria-label="Remove from list"
                :disable="lineDone"
                @click="emit('remove')"
            >
                <BaseTooltip>Remove from list</BaseTooltip>
            </BaseButton>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    /**
     * One line on the shopping list's plan face.
     *
     * Extracted from `ShoppingListDetail.vue` (v4 chunk 1), where it was an
     * inline `q-item` laying out with flex against four competing `min-width`
     * floors — name `flex: 1 1 0`, quantity 150px, store select 132px, price
     * button 96px. Because nothing shared a column, every row measured itself
     * and the money, quantity and store positions drifted by name length. That
     * is the whole of the "elements all over the place, misaligned and weirdly
     * offset" report, and it is why this is a **grid** rather than a tidier
     * flex row.
     *
     * `q-item` is gone on purpose (R-001 / v4 §5). It ships its own padding,
     * min-heights and `--side` alignment rules, and the page's stylesheet was
     * already spending a whole media block undoing them — building a new
     * surface on top of that would have landed as "slightly nicer than before".
     * The row owns its own structure now, the same trade `CollapsibleCard`
     * makes.
     *
     * Nothing was cut. Every affordance catalogued in
     * `05_investigations/SHOPPING_LIST_BASELINE.md` §5.1 is still here; three
     * moved: the store select became a menu button on the caption line, the
     * three chip variants became caption text, and the reorder arrows joined
     * delete instead of forming a stacked column of their own.
     */
    import { computed, nextTick, ref, useTemplateRef } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDropdown from 'src/components/BaseDropdown.vue';
    import BuyVerdictBadgeInline from 'src/components/stock/BuyVerdictBadgeInline.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import type { LineProductOffer, ShoppingListLine } from 'src/models/shoppingList';
    import type { BuyVerdict } from 'src/services/api/buyVerdictApiService';

    const props = defineProps<{
        line: ShoppingListLine;
        /** The list is finished — every mutation on the row is closed. */
        lineDone: boolean;
        canReorder: boolean;
        isFirst: boolean;
        isLast: boolean;
        focused: boolean;
        nested: boolean;
        productOnly: boolean;
        /** Server-resolved line estimate; the row never derives it (R-003). */
        price: number;
        storeOptions: { value: string; label: string }[];
        storeEmptyText: string;
        addedViaLabel: string | null;
        chosenProductId: string | null;
    }>();

    const emit = defineEmits<{
        move: [delta: -1 | 1];
        remove: [];
        'adjust-quantity': [delta: -1 | 1];
        'set-quantity': [value: number | null];
        'planned-store': [value: string | null];
        'pick-offer': [productId: string];
        'pick-hint': [preferredBuyId: string | null];
        'verdict-action': [action: BuyVerdict['one_tap_action']['kind']];
    }>();

    const { moneyEnabled } = useMoneyEnabled();

    // ── Quantity: tile at rest, stepper on approach ───────────────────
    // `armed` is the touch path for a reveal that CSS drives by `:hover` on a
    // pointer device. Without it the stepper would be unreachable on a phone,
    // which is the "hover-only is a loss on touch" rule the baseline sets.
    const armed = ref(false);
    const editingQty = ref(false);
    const qtyInput = useTemplateRef<HTMLInputElement>('qtyInput');

    const qtyArmed = computed(() => armed.value || editingQty.value);

    async function onTileClick(): Promise<void> {
        if (props.lineDone) return;
        // First tap arms the stepper, second opens the field. On a pointer
        // device the stepper is already showing, so the first tap types.
        if (!armed.value && window.matchMedia('(hover: none)').matches) {
            armed.value = true;
            return;
        }
        editingQty.value = true;
        await nextTick();
        qtyInput.value?.focus();
        qtyInput.value?.select();
    }

    function onQtyCommit(event: Event): void {
        editingQty.value = false;
        armed.value = false;
        const raw = (event.target as HTMLInputElement).value.trim();
        const next = raw === '' ? null : Number(raw);
        if (next !== null && (Number.isNaN(next) || next < 0)) return;
        if (next === (props.line.quantity ?? null)) return;
        emit('set-quantity', next);
    }

    // ── Caption content ───────────────────────────────────────────────
    const storeLabel = computed(
        () => props.storeOptions.find((o) => o.value === props.line.planned_store_id)?.label
            ?? props.storeEmptyText,
    );

    const buyHintLabel = computed(() => {
        if (!props.line.preferred_buy_id) return null;
        return (props.line.preferred_buys ?? []).find(
            (pb) => pb.preferred_buy_id === props.line.preferred_buy_id,
        )?.label ?? null;
    });

    /** Where the money on this row came from. An estimate off past purchases is
     *  marked as such so a rough number is never mistaken for one you typed. */
    const provenanceLabel = computed(() => {
        if (props.line.estimate_source !== 'historic') return null;
        return props.line.last_paid_store_name
            ? `last paid at ${props.line.last_paid_store_name}`
            : 'from what you last paid';
    });

    function isChosen(productId: string): boolean {
        return props.chosenProductId === productId;
    }

    function offerSavings(offer: LineProductOffer): number {
        if (offer.price_now == null || offer.price_was == null) return 0;
        const diff = offer.price_was - offer.price_now;
        return diff > 0 ? diff : 0;
    }
</script>

<style scoped>
    /* The grid shell, the divider and the name/money type scale live in
       `src/css/shoppingRow.scss` — the receipt face is built on the same
       skeleton (v4 chunk 3). What this block owns is the plan face's own
       track list and its controls.

       The quantity and action cells are sized for their *revealed* state, so
       a hover reveals opacity and nothing else. Reserving that space is
       deliberate: a reveal that reflowed the row would put the misalignment
       back as a motion bug. */
    .sl-row {
        --sl-cols: var(--sl-qty-w) minmax(0, 1fr) auto var(--sl-act-w);
        --sl-qty-w: 104px;
        --sl-act-w: 36px;
    }
    /* The grip is absolutely positioned in the row's own left padding rather
       than taking a grid column. It was a fifth column, hidden by
       `@media (hover: none)` while the column count changed on
       `max-width: 599px` — two different conditions for one layout, so a
       375px hover-capable viewport rendered five children into four columns
       and the quantity tile landed on top of the caption. Out of the grid,
       that class of mismatch cannot happen again. */
    .sl-row--reorderable {
        padding-left: calc(var(--space-4) + 16px);
        --sl-act-w: 104px;
    }
    .sl-row--ticked .sl-row__main {
        opacity: 0.6;
    }
    .sl-row--nested {
        padding-left: var(--space-8);
    }
    .sl-row--product-only {
        background: var(--surface-sunken);
    }

    .sl-row__grip {
        position: absolute;
        left: var(--space-1);
        top: 0;
        bottom: 0;
        width: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-muted);
        opacity: 0;
        transition: opacity var(--motion-fast, 120ms) var(--motion-ease, ease);
    }

    /* ── Quantity ───────────────────────────────────────────────────── */
    .sl-row__qty {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--space-1);
    }
    .sl-row__step {
        opacity: 0;
        transition: opacity var(--motion-fast, 120ms) var(--motion-ease, ease);
    }
    .sl-row__tile {
        width: 44px;
        height: 44px;
        flex: none;
        border: 1px solid transparent;
        border-radius: var(--radius-lg);
        background: var(--surface-sunken);
        color: var(--text-primary);
        font: inherit;
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
        cursor: pointer;
        display: grid;
        place-items: center;
        padding: 0;
    }
    .sl-row__tile:hover:not(:disabled) {
        border-color: var(--border-strong);
    }
    .sl-row__tile:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .sl-row__tile-input {
        width: 100%;
        height: 100%;
        border: 0;
        background: none;
        text-align: center;
        font: inherit;
        color: inherit;
        appearance: textfield;
        -moz-appearance: textfield;
        padding: 0;
    }
    .sl-row__tile-input::-webkit-outer-spin-button,
    .sl-row__tile-input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }

    /* ── Main ───────────────────────────────────────────────────────── */
    .sl-row__main {
        min-width: 0;
        transition: opacity var(--motion-fast, 120ms) var(--motion-ease, ease);
    }
    .sl-row__namerow {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-wrap: wrap;
        min-width: 0;
    }
    /* The two menu buttons on the caption line read as caption text that
       happens to be pressable — they were an outlined select and a bordered
       dropdown, i.e. two more boxes on a row that had too many.

       Quasar's `.q-btn` ships `min-height: 2.572em`, its own padding and a
       `q-btn-dropdown` caret sized for a real button. Left alone they stayed
       button-shaped and the caption line still read as a row of form
       controls — the exact "slightly nicer than before" outcome v4 §5 warns
       about. Scoped specificity beats `.q-btn`, so these land. */
    .sl-row__metabtn {
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 400;
        color: var(--text-secondary);
        min-height: 20px;
        padding: 0 2px;
        border-radius: var(--radius-sm);
    }
    .sl-row__metabtn:hover {
        background: var(--surface-sunken);
    }
    .sl-row__metabtn :deep(.q-btn__content) {
        gap: 2px;
        flex-wrap: nowrap;
    }
    .sl-row__metabtn :deep(.q-icon) {
        font-size: 13px;
    }
    /* The caret is the only thing saying "there are options", so it stays —
       but at the weight of a caption, not of a select. */
    .sl-row__metabtn :deep(.q-btn-dropdown__arrow) {
        margin-left: 0;
        font-size: 14px;
        opacity: 0.55;
    }
    /* Offers are the T2 tier — most installs never render this row at all
       (`products` is off by default). They stay visually quiet so the row's
       resting state without them is the designed one, not a gap. */
    .sl-row__offers {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-1);
        margin-top: var(--space-1);
    }
    .sl-row__offer {
        font-size: calc(var(--font-size-xs) * 1rem);
        border-radius: var(--radius-sm);
    }
    .sl-row__offer--chosen {
        font-weight: 600;
    }
    .sl-row__offersave {
        margin-left: var(--space-1);
        font-weight: 600;
        color: var(--savings-accent);
    }

    /* ── Actions ────────────────────────────────────────────────────── */
    .sl-row__actions {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: var(--space-1);
    }
    .sl-row__act {
        opacity: 0;
        transition: opacity var(--motion-fast, 120ms) var(--motion-ease, ease);
    }

    /* Reveal-on-approach, but only where there is something to approach with.
       On a touch device every one of these is permanently visible: the arrows
       are a thumb's only reorder path, and the stepper is armed by tapping the
       tile. */
    @media (hover: hover) {
        .sl-row:hover .sl-row__grip,
        .sl-row:focus-within .sl-row__grip,
        .sl-row:hover .sl-row__act,
        .sl-row:focus-within .sl-row__act,
        .sl-row:hover .sl-row__step,
        .sl-row:focus-within .sl-row__step {
            opacity: 1;
        }
    }
    @media (hover: none) {
        .sl-row__act {
            opacity: 1;
        }
        .sl-row__grip {
            display: none;
        }
    }
    /* The armed state is the touch equivalent of hover, and also covers a
       pointer user who tabbed here. */
    .sl-row__qty--armed .sl-row__step {
        opacity: 1;
    }

    @media (prefers-reduced-motion: reduce) {
        .sl-row__grip,
        .sl-row__act,
        .sl-row__step,
        .sl-row__main {
            transition: none;
        }
    }

    /* ── Phone ──────────────────────────────────────────────────────
       The old rule wrapped this row to two lines and kept all nine controls,
       so the phone row was twice as tall and just as noisy. It doesn't need
       to wrap any more: the quantity is one tile, the money is type, and the
       metadata is a caption. Only the reserved widths shrink. */
    @media (max-width: 599px) {
        /* The reserved columns that guarantee alignment on a desktop cost
           more than a phone has: 96px of quantity + 96px of money + 96px of
           actions left the name about 60px and it wrapped to a 483px row.
           So on a phone the quantity reserves the *tile* only and the armed
           stepper floats over the row instead of sitting in the flow — still
           zero reflow, because absolute positioning is out of the flow
           entirely. */
        .sl-row {
            --sl-qty-w: 44px;
            --sl-act-w: 32px;
        }
        .sl-row--reorderable {
            padding-left: calc(var(--space-3) + 14px);
            --sl-act-w: 76px;
        }
        .sl-row__qty {
            position: relative;
        }
        .sl-row__step {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            z-index: 2;
            background: var(--surface-component);
            border-radius: var(--radius-full, 50%);
            box-shadow: var(--elevation-2);
        }
        .sl-row__qty > .sl-row__step:first-child {
            right: calc(100% + var(--space-1));
        }
        .sl-row__qty > .sl-row__step:last-child {
            left: calc(100% + var(--space-1));
        }
        /* Out of the flow, so it must not catch taps while invisible. */
        .sl-row__step {
            pointer-events: none;
        }
        .sl-row__qty--armed .sl-row__step {
            pointer-events: auto;
        }
        .sl-row--nested {
            padding-left: var(--space-6);
        }
        /* The provenance caption is the least urgent thing on the row and the
           first to cost a line; it stays available in the price editor. */
        .sl-row__meta .sl-row__note:last-child {
            display: none;
        }
    }
</style>
