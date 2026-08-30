<template>
    <CollapsibleCard
        class="sl-overview"
        :class="`sl-overview--${face}`"
        reveals="list details"
    >
        <template #header>
            <div class="sl-overview__head">
                <!-- Identity. The chip leads: it is the one thing on this row
                     that changes, and reading "Draft · Weekly shop" left to
                     right says what you're looking at before it says which one.
                     The name is desktop-only — on a phone the list picker
                     directly above this card is already showing it, and
                     printing it twice was the 2026-08-28 complaint. The pencil
                     follows the name for the same reason. -->
                <div class="sl-overview__identity">
                    <span class="sl-status-pill" :class="`sl-status-pill--${detail.status}`">
                        <q-icon :name="statusIcon" size="14px" />
                        {{ statusLabel }}
                    </span>
                    <span class="text-h5 ellipsis gt-sm sl-overview__name">
                        {{ detail.display_name }}
                    </span>
                    <BaseButton
                        variant="icon"
                        class="gt-sm"
                        :icon="ICONS.edit"
                        aria-label="Rename list"
                        @click="emit('rename')"
                    >
                        <q-tooltip>Rename — leave blank to label by date</q-tooltip>
                    </BaseButton>
                </div>

                <!-- The figure. One number, chosen by what the face is for:
                     planning asks what this will cost, shopping asks what's
                     left to spend, a receipt asks what it came to. With money
                     off there is no figure to lead with, so the size of the
                     list takes the slot rather than the card losing its
                     headline. -->
                <div class="sl-overview__figures">
                    <div class="sl-overview__figure">
                        <div class="sl-overview__amount">{{ headlineValue }}</div>
                        <div class="text-caption dora-text-muted">{{ headlineLabel }}</div>
                    </div>

                    <!-- Mid-shop the ring is the progress, so it sits with the
                         figure rather than in a footer of its own. -->
                    <div v-if="face === 'run'" class="sl-overview__progress">
                        <q-circular-progress
                            show-value
                            :value="progressPct"
                            size="52px"
                            :thickness="0.18"
                            color="positive"
                            track-color="separator"
                            class="sl-overview__ring text-weight-medium"
                        >
                            <span class="text-caption">
                                {{ tickedCount }}/{{ detail.lines.length }}
                            </span>
                        </q-circular-progress>
                        <span class="text-body2">{{ untickedCount }} left to pick</span>
                    </div>

                    <q-space />

                    <div class="sl-overview__when">
                        <div v-if="datelineLabel" class="row items-center no-wrap" :class="datelineClass">
                            <q-icon :name="datelineIcon" size="14px" class="q-mr-xs" />
                            {{ datelineLabel }}
                        </div>
                        <div class="dora-text-muted">
                            {{ detail.lines.length }} item{{ detail.lines.length === 1 ? '' : 's' }}
                        </div>
                    </div>
                </div>

                <!-- Controls. The sort control is a view preference that
                     belongs with the thing it reorders, and the primary action
                     is the one thing this face is for — both live on the card
                     rather than in the toolbar band, which was carrying four
                     mutually-exclusive lifecycle buttons in one slot. -->
                <div class="sl-overview__controls">
                    <div v-if="sortModes.length > 1" class="sl-overview__sort">
                        <span class="text-caption dora-text-muted">Order by</span>
                        <BaseButton
                            v-for="m in sortModes"
                            :key="m"
                            :variant="effectiveMode === m ? 'secondary' : 'ghost'"
                            dense
                            size="sm"
                            :label="SECTION_MODE_LABELS[m]"
                            :disable="!availableModes[m]"
                            :aria-pressed="effectiveMode === m"
                            @click="emit('update:mode', m)"
                        >
                            <q-tooltip v-if="!availableModes[m]">
                                Nothing on this list has a
                                {{ SECTION_MODE_LABELS[m].toLowerCase() }} set
                            </q-tooltip>
                        </BaseButton>
                    </div>

                    <q-space />

                    <!-- A finished list is a record, so correcting it is an
                         explicit mode rather than the default state. -->
                    <BaseButton
                        v-if="face === 'receipt'"
                        :variant="amending ? 'secondary' : 'ghost'"
                        :icon="ICONS.edit"
                        :label="amending ? 'Done amending' : 'Amend'"
                        @click="emit('update:amending', !amending)"
                    >
                        <q-tooltip>
                            Correct the price, store or quantity on a line.
                            Your pantry isn't restocked again.
                        </q-tooltip>
                    </BaseButton>

                    <BaseButton
                        v-if="face === 'plan'"
                        variant="primary"
                        :icon="ICONS.shopping_cart"
                        label="Start shopping"
                        :disable="detail.lines.length === 0"
                        :loading="starting"
                        @click="emit('start-shopping')"
                    >
                        <q-tooltip>
                            Tick items off as you grab them — prices you enter
                            become the receipt
                        </q-tooltip>
                    </BaseButton>
                    <!-- Always "Finish", never "Finish early" (2026-08-29:
                         *"people know if they are finishing early or not"*).
                         The button was reading the tick count back to someone
                         who had just been looking at it, and the leftovers are
                         a real decision made in the dialog, not a warning
                         needed on the control that opens it. -->
                    <BaseButton
                        v-else-if="face === 'run'"
                        variant="positive"
                        :icon="ICONS.check"
                        label="Finish"
                        :loading="finishing"
                        @click="emit('finish')"
                    >
                        <q-tooltip>
                            Marks this shop as done: every ticked item moves
                            back to Stocked in your pantry, and the list is
                            archived. Anything you didn't buy can move to
                            another list on the way out.
                        </q-tooltip>
                    </BaseButton>
                    <BaseButton
                        v-else
                        variant="primary"
                        :icon="ICONS.inventory_2"
                        label="Put away"
                        @click="emit('put-away')"
                    >
                        <q-tooltip>
                            Ephemeral checklist grouped by kitchen location so
                            you don't forget a corner. Doesn't save.
                        </q-tooltip>
                    </BaseButton>
                </div>
            </div>
        </template>

        <!-- The review half. Everything here answers a question you ask once,
             not one you ask at a glance — which is the whole reason it is
             behind a caret rather than stacked on the page. -->
        <div class="sl-overview__detail">
            <StoreSpendCard
                v-if="face !== 'receipt'"
                :buckets="detail.totals.by_store"
                :tense="face === 'run' ? 'shop' : 'plan'"
                :collapsible="false"
            />

            <div v-if="secondaryFigures.length > 0" class="sl-overview__secondary">
                <div v-for="fig in secondaryFigures" :key="fig.label" class="sl-overview__stat">
                    <span class="dora-text-muted">{{ fig.label }}</span>
                    <span :class="fig.tone">{{ fig.value }}</span>
                </div>
            </div>

            <!-- Not on the run face at any depth: when you are standing in a
                 shop, the day you created the list is the least useful fact
                 the app holds about it. -->
            <div v-if="face !== 'run'" class="text-caption dora-text-muted">
                Created {{ formatDate(detail.created_at) }}
            </div>
        </div>
    </CollapsibleCard>
</template>

<script lang="ts" setup>
    /**
     * The shopping list's overview card — one component across all three faces.
     *
     * It replaces a top section that had accreted into five separate blocks: a
     * header cluster (name, pill, pencil, a meta row carrying the item count,
     * the shop day and the creation date), a `TripCard`, a `StoreSpendCard`, an
     * "Order by" bar, and — mid-shop — a sticky footer repeating the money and
     * the primary action. Five containers, no hierarchy, and the same numbers
     * in two of them.
     *
     * The shape is a disclosure, because the information genuinely splits in
     * two: **one figure and one action** you want at a glance, and a review you
     * want once. Collapsed, the card answers "what is this, what will it cost,
     * when am I going, what do I do next". Expanded, it answers "where is the
     * money going, how much am I saving, how firm are these numbers".
     *
     * Every figure it shows is read from `detail.totals`, which the server owns
     * (R-003). Nothing here re-sums a line.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import CollapsibleCard from 'src/components/CollapsibleCard.vue';
    import StoreSpendCard from 'src/components/shoppingList/StoreSpendCard.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import {
        PLAN_SECTION_MODES, SECTION_MODES, SECTION_MODE_LABELS, useLineSections,
        type SectionMode,
    } from 'src/composables/useLineSections';
    import type { ShoppingListDetail, ShoppingListLine } from 'src/models/shoppingList';

    const props = defineProps<{
        detail: ShoppingListDetail;
        /** Active lines only (deferred-by-budget excluded) — the same set the
         *  server's totals describe, and the set the sort control sorts. */
        lines: ShoppingListLine[];
        mode: SectionMode;
        amending: boolean;
        starting: boolean;
        finishing: boolean;
    }>();

    const emit = defineEmits<{
        rename: [];
        'start-shopping': [];
        finish: [];
        'put-away': [];
        'update:amending': [value: boolean];
        'update:mode': [mode: SectionMode];
    }>();

    const { moneyEnabled } = useMoneyEnabled();

    const face = computed<'plan' | 'run' | 'receipt'>(() => {
        switch (props.detail.status) {
            case 'shopping': return 'run';
            case 'done': return 'receipt';
            default: return 'plan';
        }
    });

    // ── Identity ──────────────────────────────────────────────────────
    const statusLabel = computed(() => {
        switch (props.detail.status) {
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

    /** The pill carries a glyph as well as a colour, so the three states are
     *  still three states in greyscale (D-013 — colour never alone). */
    const statusIcon = computed(() => {
        switch (props.detail.status) {
            case 'shopping': return ICONS.shopping_cart;
            case 'done': return ICONS.check;
            default: return ICONS.edit;
        }
    });

    // ── The headline figure ───────────────────────────────────────────
    // Server-owned totals, read not derived (R-003).
    const headlineValue = computed(() => {
        if (!moneyEnabled.value) return String(props.detail.lines.length);
        switch (face.value) {
            case 'run': return formatMoney(props.detail.totals.remaining_price);
            default: return formatMoney(props.detail.totals.total_price);
        }
    });

    const headlineLabel = computed(() => {
        if (!moneyEnabled.value) {
            return props.detail.lines.length === 1 ? 'item on this list' : 'items on this list';
        }
        switch (face.value) {
            case 'run': return 'Left to spend';
            case 'receipt': return 'Spent';
            default: return 'Estimated cost';
        }
    });

    const tickedCount = computed(() => props.detail.lines.filter((l) => l.is_ticked).length);
    const untickedCount = computed(() => props.detail.lines.filter((l) => !l.is_ticked).length);
    /** Pure display math over server-owned counts — the sanctioned Type-C case. */
    const progressPct = computed(() => {
        const count = props.detail.lines.length;
        return count === 0 ? 0 : (tickedCount.value / count) * 100;
    });

    // ── The dateline ──────────────────────────────────────────────────
    // Plain text on every face now. Setting the day is the toolbar's job while
    // it is still settable, so this stopped being a button — a control and a
    // fact were sharing one slot, and the fact is what you read here.
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

    function formatDate(iso: string): string {
        try {
            return formatLocaleDate(iso) || iso;
        } catch {
            return iso;
        }
    }

    /** A finished list reports when it happened; an unfinished one reports when
     *  it is meant to. "Planned for Saturday" is not what you want to read on a
     *  receipt. */
    const datelineLabel = computed(() => {
        if (face.value === 'receipt') {
            return props.detail.completed_at
                ? `Shopped ${formatDate(props.detail.completed_at)}`
                : null;
        }
        const d = props.detail.planned_shop_date;
        if (!d) return face.value === 'plan' ? 'No shop day set' : null;
        if (d === todayIso()) return 'Shop day: today';
        if (d === tomorrowIso()) return 'Shop day: tomorrow';
        if (daysFromToday(d) < 0) return `Shop day: ${formatDate(d)} (overdue)`;
        return `Shop day: ${formatDate(d)}`;
    });

    const datelineIcon = computed(() =>
        face.value === 'receipt' ? ICONS.event_available : ICONS.event
    );

    /** Tone is Dora's own text-colour helper, never a Quasar palette name in
     *  the template (R-002). Never toned on a receipt: the date is history. */
    const datelineClass = computed(() => {
        const d = props.detail.planned_shop_date;
        if (!d || face.value === 'receipt') return '';
        if (d === todayIso()) return 'text-positive';
        return daysFromToday(d) < 0 ? 'text-negative' : '';
    });

    // ── The sort control ──────────────────────────────────────────────
    // Was two identical bars — one on the plan face, one inside
    // `ShoppingListRunFace` — which is how they were free to drift. The mode
    // lists still differ by face (curating a list is a different job from
    // walking a shop), so that difference is stated here rather than duplicated.
    const sortModes = computed<SectionMode[]>(() => {
        if (face.value === 'run') return SECTION_MODES;
        // A receipt is a record. There is nothing to reorder for, and an empty
        // list means the control never renders.
        if (face.value === 'receipt') return [];
        return PLAN_SECTION_MODES;
    });

    const linesRef = computed(() => props.lines);
    const modeRef = computed(() => props.mode);
    const { availableModes, effectiveMode } = useLineSections(linesRef, modeRef, {
        allowedModes: sortModes,
    });

    // ── The review half ───────────────────────────────────────────────
    const estimatedCount = computed(() =>
        props.lines.filter((l) => l.estimate_source === 'historic').length
    );

    /** The figures that don't earn the headline slot. Built as a list because
     *  which of them apply is a per-face question, and a template full of
     *  `v-if`s over three faces is how the old header got the way it was. */
    const secondaryFigures = computed(() => {
        const figures: { label: string; value: string; tone: string }[] = [];
        if (!moneyEnabled.value) return figures;
        const totals = props.detail.totals;

        // Mid-shop the headline is what's *left*, so the whole trip's figure
        // moves down here rather than disappearing.
        if (face.value === 'run') {
            figures.push({
                label: 'Trip total',
                value: formatMoney(totals.total_price),
                tone: '',
            });
        }
        // Savings render on the receipt for the first time. They were on the
        // plan face's trip card and nowhere else, so you found out what you
        // saved while planning the shop and never again after doing it.
        if (totals.total_savings > 0) {
            figures.push({
                label: face.value === 'receipt' ? 'You saved' : 'Saving',
                value: formatMoney(totals.total_savings),
                tone: 'text-positive',
            });
        }
        // Says out loud when a figure above is built from past purchases rather
        // than prices entered for this trip, so a rough number is never mistaken
        // for a firm one.
        if (estimatedCount.value > 0) {
            figures.push({
                label: 'From what you last paid',
                value: `${estimatedCount.value} item${estimatedCount.value === 1 ? '' : 's'}`,
                tone: 'dora-text-muted',
            });
        }
        return figures;
    });
</script>

<style scoped>
    .sl-overview {
        padding: var(--space-3);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        background: var(--surface-elevated);
        margin-bottom: var(--space-4);
    }
    .sl-overview__head {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        min-width: 0;
    }
    .sl-overview__identity {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        min-width: 0;
        min-height: 44px;
    }
    .sl-overview__name {
        min-width: 0;
    }
    /* Wraps rather than scrolls: this is content, not a control band, and a
       figure that runs off the edge of a phone is a figure you can't read
       (D-011). */
    .sl-overview__figures {
        display: flex;
        align-items: flex-end;
        flex-wrap: wrap;
        gap: var(--space-3);
        min-width: 0;
    }
    .sl-overview__amount {
        font-size: 1.9rem;
        font-weight: 600;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }
    .sl-overview__progress {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding-bottom: 2px;
    }
    .sl-overview__when {
        text-align: right;
        font-size: calc(var(--font-size-xs) * 1rem);
        line-height: 1.5;
    }
    .sl-overview__controls {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-2);
        padding-top: var(--space-2);
        border-top: 1px solid var(--divider);
    }
    .sl-overview__sort {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-1);
    }
    .sl-overview__detail {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        padding-top: var(--space-3);
    }
    .sl-overview__secondary {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-1) var(--space-4);
    }
    .sl-overview__stat {
        display: flex;
        align-items: baseline;
        gap: var(--space-1);
        font-size: calc(var(--font-size-sm) * 1rem);
        font-variant-numeric: tabular-nums;
    }

    /* B2 status pill. Bigger and better-dressed than the bare text pill it
       replaces (2026-08-29 feedback): a glyph, a real chip height, and
       `--font-size-sm` — D-003's floor for a chip carrying a value. Soft
       background + full-strength semantic ink, never the soft token on both
       (the D-002 badge failure). */
    .sl-status-pill {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        flex: none;
        border-radius: var(--radius-pill);
        padding: var(--space-1) var(--space-3);
        min-height: 28px;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        line-height: 1.2;
        white-space: nowrap;
        border: 1px solid transparent;
    }
    /* A draft hasn't happened yet — neutral, and quiet enough not to compete
       with the "Start shopping" button on the row below it. */
    .sl-status-pill--draft {
        background: var(--surface-sunken);
        color: var(--text-secondary);
        border-color: var(--border-default);
    }
    /* Mid-shop is a state you're in, not an achievement. */
    .sl-status-pill--shopping {
        background: var(--semantic-info-soft);
        color: var(--semantic-info);
        border-color: var(--semantic-info);
    }
    /* Finishing the shop is the success in this lifecycle, so this is the one
       that earns the positive token. */
    .sl-status-pill--done {
        background: var(--semantic-positive-soft);
        color: var(--semantic-positive);
        border-color: var(--semantic-positive);
    }

    .sl-overview__ring :deep(.q-circular-progress__text) {
        font-variant-numeric: tabular-nums;
    }
    /* The arc grows into place as items are picked rather than snapping, so a
       tick reads as progress. Motion-safe per D-018. */
    .sl-overview__ring :deep(.q-circular-progress__circle) {
        transition: stroke-dashoffset 320ms ease-out;
    }
    @media (prefers-reduced-motion: reduce) {
        .sl-overview__ring :deep(.q-circular-progress__circle) {
            transition: none;
        }
    }
</style>
