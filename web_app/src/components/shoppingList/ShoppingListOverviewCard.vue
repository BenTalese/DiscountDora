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
                        <BaseTooltip>Rename — leave blank to label by date</BaseTooltip>
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
                        <div class="sl-overview__amount">
                            <!-- The tilde is the same honesty marker
                                 `StoreSpendCard` already uses on a short
                                 bucket, raised to the figure it qualifies. -->
                            <span v-if="headlineIsPartial" class="sl-overview__approx">~</span>{{ headlineValue }}
                        </div>
                        <div class="text-caption dora-text-muted">{{ headlineLabel }}</div>
                        <div v-if="headlineIsPartial" class="sl-overview__partial">
                            <q-icon :name="ICONS.info" size="13px" />
                            {{ unpricedCount }} item{{ unpricedCount === 1 ? '' : 's' }}
                            with no price yet
                            <BaseTooltip>
                                This total only counts what Dora has a price
                                for, so the real figure is higher.
                            </BaseTooltip>
                        </div>
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
                        <!-- Four loose ghost buttons became one control. It is
                             a single choice from a fixed set, which is what a
                             segmented control is for, and `pill` is the shape
                             the owner picked for exactly this on 2026-08-31 —
                             so this doesn't invent a second one (D-015). -->
                        <!-- No `dense`/`size="sm"`: at that size the pill
                             collapsed into a single dark blob with the labels
                             touching, and it is the card's only view control —
                             it should read as a control, not as a smudge. Also
                             keeps every segment past D-004's tap floor. -->
                        <BaseSegmented
                            class="sl-overview__seg"
                            :model-value="effectiveMode"
                            :options="sortOptions"
                            @update:model-value="emit('update:mode', $event)"
                        >
                            <!-- One tooltip for the group rather than one per
                                 segment: `q-btn-toggle` has no per-option slot
                                 that isn't a dynamic name per value, and the
                                 information being preserved is *why* a mode is
                                 greyed out, which reads fine said once. -->
                            <BaseTooltip v-if="unavailableLabel">
                                {{ unavailableLabel }}
                            </BaseTooltip>
                        </BaseSegmented>
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
                        <BaseTooltip>
                            Correct the price, store or quantity on a line.
                            Your pantry isn't restocked again.
                        </BaseTooltip>
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
                        <BaseTooltip>
                            Tick items off as you grab them — prices you enter
                            become the receipt
                        </BaseTooltip>
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
                        <BaseTooltip>
                            Marks this shop as done: every ticked item moves
                            back to Stocked in your pantry, and the list is
                            archived. Anything you didn't buy can move to
                            another list on the way out.
                        </BaseTooltip>
                    </BaseButton>
                    <BaseButton
                        v-else
                        variant="primary"
                        :icon="ICONS.inventory_2"
                        label="Put away"
                        @click="emit('put-away')"
                    >
                        <BaseTooltip>
                            Ephemeral checklist grouped by kitchen location so
                            you don't forget a corner. Doesn't save.
                        </BaseTooltip>
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
    import BaseTooltip from 'src/components/BaseTooltip.vue';
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
    import BaseSegmented from 'src/components/BaseSegmented.vue';
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
    //
    // Tier-aware (v4 §3, closing §7.3). Both `money` and `products` default to
    // **false** in `health_check.py`, so the no-money install is not an edge
    // case — it is what a fresh install looks like, and the card has to lead
    // with something real there rather than a consolation. It used to print
    // the raw line count under "items on this list" on every face, which says
    // the same flat thing whether you are planning, mid-aisle or done. Each
    // face has a number it is actually about, and money only changes *which*
    // number, never whether there is one.
    const headlineValue = computed(() => {
        if (!moneyEnabled.value) {
            switch (face.value) {
                case 'run': return String(untickedCount.value);
                case 'receipt': return String(tickedCount.value);
                default: return String(props.detail.lines.length);
            }
        }
        switch (face.value) {
            case 'run': return formatMoney(props.detail.totals.remaining_price);
            default: return formatMoney(props.detail.totals.total_price);
        }
    });

    const headlineLabel = computed(() => {
        if (!moneyEnabled.value) {
            switch (face.value) {
                case 'run': return 'Left to pick';
                case 'receipt':
                    return tickedCount.value === 1 ? 'Item bought' : 'Items bought';
                default:
                    return props.detail.lines.length === 1 ? 'Item to buy' : 'Items to buy';
            }
        }
        switch (face.value) {
            case 'run': return 'Left to spend';
            case 'receipt': return 'Spent';
            default: return 'Estimated cost';
        }
    });

    /** How many lines carry no price at all. The server already publishes this
     *  per store bucket precisely so the UI can admit a total is short — but it
     *  was only ever read inside `StoreSpendCard`, which lives *inside* this
     *  card's disclosure. So the headline could be quietly incomplete while the
     *  top level said nothing (baseline §1.5 / S7). It says something now. */
    const unpricedCount = computed(() => props.detail.totals.by_store.reduce(
        (sum, b) => sum + (b.line_count - b.priced_line_count), 0,
    ));

    const headlineIsPartial = computed(
        () => moneyEnabled.value && unpricedCount.value > 0,
    );

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

    const sortOptions = computed(() => sortModes.value.map((m) => ({
        label: SECTION_MODE_LABELS[m],
        value: m,
        disable: !availableModes.value[m],
    })));

    /** Names the modes this list can't offer, so a greyed-out segment still
     *  says why — the per-button tooltips it replaces carried that. */
    const unavailableLabel = computed(() => {
        const missing = sortModes.value.filter((m) => !availableModes.value[m]);
        if (missing.length === 0) return null;
        const names = missing.map((m) => SECTION_MODE_LABELS[m].toLowerCase());
        const list = names.length === 1
            ? names[0]
            : `${names.slice(0, -1).join(', ')} or ${names.at(-1)}`;
        return `Nothing on this list has ${list === names[0] ? 'a ' : ''}${list} set`;
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
    /* The surface pass (v4 §4.2). This card used `--radius-md` (6px, the
       squarest non-trivial rung) and a flat 1px border with no elevation at
       all — the same treatment as the line list, the empty state and
       `StoreSpendCard`, so nothing on the page receded and the whole thing
       read as a stack of equal grey boxes. `--radius-xl`, `--elevation-card`
       and `--hero-gradient` were all already in `tokens.scss`, unused here.

       The hairline carries the dark themes. `--elevation-card` is a shadow,
       and a shadow does nothing on `pesto-dark`'s near-black page (5%
       lightness) — but there `--surface-component` is *lighter* than the page,
       so the card separates by luminance and the border draws its edge. In
       the light themes it is the other way round: the shadow does the work and
       the hairline is barely visible. One declaration, correct in both, and no
       `prefers-color-scheme` query — which would have been wrong anyway, since
       Dora's themes are `data-theme` attributes, not a media state. */
    .sl-overview {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-xl);
        background: var(--surface-component);
        box-shadow: var(--elevation-card), var(--elevation-2);
        margin-bottom: var(--space-5);
        overflow: hidden;
    }
    /* The band. Gradient on the faces where the list is still happening, flat
       on the receipt (owner call 2026-08-31) — so the surface itself carries
       state: a live list is a coloured band, a finished one is paper. The
       three faces end up differently *material*, not merely differently
       arranged, which is a stronger signal than the status pill alone. */
    .sl-overview :deep(.collapsible-card__header) {
        padding: var(--space-4) var(--space-4) var(--space-3) var(--space-5);
    }
    .sl-overview--plan :deep(.collapsible-card__header),
    .sl-overview--run :deep(.collapsible-card__header) {
        background: var(--hero-gradient);
    }
    .sl-overview :deep(.collapsible-card__body) {
        padding: var(--space-4) var(--space-5) var(--space-5);
        background: var(--surface-component);
        border-top: 1px solid var(--divider);
    }
    .sl-overview__head {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
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
    /* Was a magic `1.9rem` off the scale. The figure is the card's headline,
       so it takes the scale's top rung — and the name beside it stays `text-h5`,
       which is the hierarchy the owner asked for ("text feels small where it
       should be big"). */
    .sl-overview__amount {
        font-size: calc(var(--font-size-3xl) * 1rem);
        font-weight: 700;
        line-height: 1.05;
        letter-spacing: -0.025em;
        font-variant-numeric: tabular-nums;
    }
    .sl-overview__approx {
        font-weight: 500;
        opacity: 0.65;
    }
    .sl-overview__partial {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-top: 2px;
        font-size: calc(var(--font-size-xs) * 1rem);
        color: var(--text-secondary);
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
    /* Sits on the band, so the rule that separates it has to be a veil rather
       than `--divider` — a fixed hairline colour reads as a scratch across a
       gradient in some themes and vanishes in others. */
    .sl-overview__controls {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-2);
        padding-top: var(--space-3);
        border-top: 1px solid var(--overlay-dim);
    }
    .sl-overview--receipt .sl-overview__controls {
        border-top-color: var(--divider);
    }
    .sl-overview__sort {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-2);
    }
    /* The track sits on the gradient band, so `--surface-sunken` (the pill's
       default) reads as a grey patch stuck on the colour. A white veil belongs
       to the band instead of fighting it, and the receipt's flat face puts the
       normal sunken track back. */
    .sl-overview__seg {
        background: hsla(0, 0%, 100%, 0.5);
    }
    .sl-overview--receipt .sl-overview__seg {
        background: var(--surface-sunken);
    }
    .sl-overview__seg :deep(.q-btn) {
        min-height: 32px;
        padding: 0 var(--space-3);
        font-size: calc(var(--font-size-sm) * 1rem);
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
