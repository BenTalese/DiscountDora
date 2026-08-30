<template>
    <!-- "Where you'll spend it" — the plan-face store breakdown.
         Renders nothing at all unless the server resolved at least one real
         store, so it never nags installs that don't use stores. -->
    <CollapsibleCard
        v-if="buckets.length > 0"
        class="sl-store-card"
        :collapsible="collapsible"
        header-toggles
        reveals="store breakdown"
    >
        <template #header>
            <div class="row items-center no-wrap q-gutter-x-sm sl-store-card__title">
                <q-icon :name="ICONS.storefront" size="18px" class="dora-text-secondary" />
                <span class="text-subtitle2">{{ title }}</span>
            </div>
        </template>

        <template #collapsed>
            <div class="text-caption dora-text-muted ellipsis">{{ summaryLine }}</div>
        </template>

        <template #default>
            <div class="q-pt-sm q-pb-xs">
                <!-- Proportional bar. With money on, segments are spend
                     share; with money off there is no spend to share out, so
                     it falls back to how many items each store is carrying —
                     the same question, minus the dollars. Buckets that have
                     items but no value still get a floor width so they can't
                     vanish from a bar whose own legend lists them; see
                     `segments`. -->
                <div v-if="segments.length > 0" class="sl-store-bar" role="presentation">
                    <div
                        v-for="seg in segments"
                        :key="seg.key"
                        class="sl-store-bar__seg"
                        :class="{ 'sl-store-bar__seg--unassigned': seg.isUnassigned }"
                        :style="{ width: `${seg.width}%`, background: seg.colour }"
                    />
                </div>
            </div>

            <div class="q-pt-xs">
                <div class="row q-gutter-xs">
                    <q-chip
                        v-for="b in buckets"
                        :key="b.store_id ?? '__none__'"
                        dense
                        square
                        class="sl-store-chip"
                        :class="{ 'sl-store-chip--none': b.store_id === null }"
                    >
                        <span
                            v-if="b.store_id !== null"
                            class="sl-store-dot"
                            :style="{ background: segmentColour(b) }"
                        />
                        <span class="text-weight-medium q-mr-xs">{{ b.store_name }}</span>
                        <span class="dora-text-muted">
                            {{ b.line_count }} item{{ b.line_count === 1 ? '' : 's' }}
                            <template v-if="moneyEnabled && b.priced_line_count > 0">
                                · {{ approx(b) }}{{ formatMoney(b.subtotal) }}
                            </template>
                        </span>
                    </q-chip>
                </div>

                <div v-if="footnote" class="text-caption dora-text-muted q-mt-sm">
                    {{ footnote }}
                </div>
            </div>
        </template>
    </CollapsibleCard>
</template>

<script lang="ts" setup>
    /**
     * The store breakdown lifted out of the "Trip" direction (C) into the plan
     * face. It answers one question the rest of the page can't: *am I about to
     * spend $50 more at Coles than at Aldi?*
     *
     * The design constraint that shaped it: product offers are a power-user
     * feature most installs will never populate. The server's store ladder
     * resolves through `usual_store_id` and past purchases before it ever looks
     * at an offer, so this card is fully populated for someone who has simply
     * tagged items "I buy this at Aldi" and shopped twice.
     *
     * That makes partial data the normal case, not an edge case — hence the
     * explicit footnote when some lines have no price. A total that silently
     * omits a third of the list is worse than one that admits the gap.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import CollapsibleCard from 'src/components/CollapsibleCard.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { storeColour } from 'src/style/storeSwatch';
    import type { StoreSpend } from 'src/models/shoppingList';

    const props = withDefaults(defineProps<{
        buckets: StoreSpend[];
        /**
         * Whether this card can close at all — *not* whether it starts closed.
         * It always starts closed (`CollapsibleCard` owns that, and it is the
         * app-wide default).
         *
         * It used to be `ref(!collapsible)` with both callers passing
         * `$q.screen.lt.md`, which meant "expanded on desktop, collapsed on a
         * phone" — and, being a `ref` seeded once at setup, it never
         * re-evaluated when the window crossed the breakpoint (FU-783). The
         * screen-size question is gone entirely rather than fixed: the one
         * caller that genuinely shouldn't collapse is the plan face's, because
         * that card now sits *inside* the overview card's expanded region,
         * where a second tap to reach the same information is a tax.
         */
        collapsible?: boolean;
        /** Which face is asking. All three tenses are real: a draft hasn't
         *  spent anything, a receipt has spent all of it, and mid-shop is
         *  genuinely neither — some of the trolley is paid for and some isn't,
         *  so past tense there reads as a shop you've already finished. */
        tense?: 'plan' | 'shop' | 'receipt';
    }>(), { collapsible: true, tense: 'plan' });

    const { moneyEnabled } = useMoneyEnabled();

    /** 2026-08-26 feedback: *"'Where you spent it' is a bit odd when budgets
     *  and money are off"* — and it was, because the card kept its money
     *  wording while showing nothing but item counts. All six wordings live
     *  here so the callers can't drift: the face picks the tense, the money
     *  flag picks the verb. */
    const title = computed(() => {
        switch (props.tense) {
            case 'receipt':
                return moneyEnabled.value ? 'Where you spent it' : 'Where you shopped';
            case 'shop':
                return moneyEnabled.value ? "Where you're spending" : "Where you're shopping";
            default:
                return moneyEnabled.value ? "Where you'll spend it" : "Where you'll shop";
        }
    });

    /** What each segment's width is proportional to. Money when there is
     *  money; item count otherwise. */
    function barValue(bucket: StoreSpend): number {
        return moneyEnabled.value ? bucket.subtotal : bucket.line_count;
    }

    /** Floor width for a bucket that has items but nothing to weigh them by.
     *  Enough to read as a segment at a phone's width, small enough that it
     *  doesn't misrepresent a bucket carrying two unpriced items as a big
     *  share of the shop. */
    const MIN_SEGMENT_PCT = 7;

    /**
     * The bar's segments, with widths already resolved.
     *
     * Why this isn't just `value / total` inline: with money **on**, a bucket's
     * width is its *spend*, and a bucket can hold items while contributing no
     * money — the "No store set" catch-all whose lines are unpriced, or a real
     * store whose lines you haven't priced yet. Those computed to `0%` and
     * vanished from the bar while still being listed as a chip underneath it,
     * so the bar quietly disagreed with its own legend (2026-08-28 owner
     * feedback: *"also allocate space for 'no store'"*).
     *
     * So every bucket that has lines gets at least `MIN_SEGMENT_PCT`, and the
     * buckets that do carry value share what's left in true proportion. The
     * segments still sum to 100%, and the money comparison between two priced
     * stores stays honest — only the "this exists" floor is synthetic.
     */
    const segments = computed(() => {
        const present = props.buckets.filter((b) => b.line_count > 0);
        const valued = present.filter((b) => barValue(b) > 0);
        const total = valued.reduce((sum, b) => sum + barValue(b), 0);

        // Nothing anywhere has a value (money on, nothing priced yet): there is
        // no proportion to draw, so show the buckets as equal presences rather
        // than inventing a ranking out of item counts the bar isn't measuring.
        if (valued.length === 0) {
            return present.map((b) => ({
                key: b.store_id ?? '__none__',
                width: 100 / present.length,
                colour: segmentColour(b),
                isUnassigned: b.store_id === null,
            }));
        }

        const floors = (present.length - valued.length) * MIN_SEGMENT_PCT;
        const share = (100 - floors) / 100;
        return present.map((b) => ({
            key: b.store_id ?? '__none__',
            width: barValue(b) > 0
                ? (barValue(b) / total) * 100 * share
                : MIN_SEGMENT_PCT,
            colour: segmentColour(b),
            isUnassigned: b.store_id === null,
        }));
    });

    const unpricedCount = computed(() =>
        props.buckets.reduce((sum, b) => sum + (b.line_count - b.priced_line_count), 0)
    );

    /** A "~" marker whenever a bucket's money is an estimate rather than
     *  something the user actually typed for this trip. */
    function approx(bucket: StoreSpend): string {
        return bucket.priced_line_count < bucket.line_count ? '~' : '';
    }

    /** Identity, not state — a store's own colour, so Woolworths reads green
     *  and Coles red (2026-08-26 feedback). It used to come from the chart
     *  ramp indexed by *position in this list*, which meant a store changed
     *  colour whenever the spend order changed. `storeColour` resolves the
     *  logo-derived `brand_colour` first and falls back to the deterministic
     *  name hash; D-001 is satisfied because the colour never encodes a state
     *  and never travels without the store's name beside it. */
    /** `undefined` for the catch-all: it has no identity colour, and the
     *  stylesheet owns its fill (an inline `background` shorthand would clobber
     *  the hatch's `background-image`). Every real store keeps its own. */
    function segmentColour(bucket: StoreSpend): string | undefined {
        if (bucket.store_id === null) return undefined;
        return storeColour(bucket.store_name, bucket.brand_colour);
    }

    const summaryLine = computed(() => {
        const parts = props.buckets.map((b) => {
            if (moneyEnabled.value && b.priced_line_count > 0) {
                return `${b.store_name} ${approx(b)}${formatMoney(b.subtotal)}`;
            }
            return `${b.store_name} ${b.line_count}`;
        });
        return parts.join(' · ');
    });

    /** Two separate honesty notes, deliberately combined into one line so the
     *  card doesn't grow a second paragraph: the headline gap between the two
     *  biggest stores, and how much of the list isn't priced at all. */
    const footnote = computed(() => {
        const notes: string[] = [];
        const real = props.buckets.filter((b) => b.store_id !== null && b.priced_line_count > 0);
        if (moneyEnabled.value && real.length >= 2) {
            const gap = real[0]!.subtotal - real[real.length - 1]!.subtotal;
            if (gap > 0) {
                notes.push(
                    `${formatMoney(gap)} more at ${real[0]!.store_name} than ${real[real.length - 1]!.store_name}`
                );
            }
        }
        // Money-gated too: with money off nothing on this card is priced, so
        // "12 items unpriced, not counted" would be describing a total the
        // user can't see and never asked for.
        if (moneyEnabled.value && unpricedCount.value > 0) {
            notes.push(
                `${unpricedCount.value} item${unpricedCount.value === 1 ? '' : 's'} unpriced, not counted`
            );
        }
        return notes.join(' · ');
    });
</script>

<style scoped>
    /* Was `q-card flat bordered`. `CollapsibleCard` owns the disclosure and
       nothing else, so the surface is stated here — the same flat-bordered
       look, minus a component wrapper that only ever contributed padding. */
    .sl-store-card {
        padding: var(--space-3);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        background: var(--surface-component);
    }
    .sl-store-card__title {
        min-height: 44px;
    }
    .sl-store-bar {
        display: flex;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        background: var(--surface-sunken);
    }
    .sl-store-bar__seg {
        height: 100%;
        min-width: 2px;
    }
    /* The catch-all: a themed grey, hatched.

       The grey alone is `--border-strong`, the neutral every theme defines to
       be seen against a surface — which is right in light themes and measurably
       wrong in dark ones. Measured against the store fills either side of it:
       3.55:1 in Pesto light, but **1.19:1** in Pesto Dark and **1.02:1** in
       Cherry Cola Dark, i.e. the same lightness as its neighbour. That isn't
       fixable by picking a better grey, because the fills it competes with are
       partly *logo-derived brand colours* — arbitrary, and free to be grey
       themselves. No single neutral can be guaranteed to separate from them.

       So the segment is distinguished by **texture**, which no neighbouring
       colour can collide with, and which says the right thing: a hatch reads as
       unallocated rather than as one more store. Both stripe colours are theme
       tokens, so it inverts correctly — dark stripes on grey in light themes,
       light stripes on grey in dark ones. Colour is still carrying the message
       for anyone who sees it, but it is no longer carrying it alone (D-001). */
    .sl-store-bar__seg--unassigned {
        background-color: var(--border-strong);
        background-image: repeating-linear-gradient(
            135deg,
            transparent 0 3px,
            var(--surface-component) 3px 5px
        );
    }
    .sl-store-chip {
        background: var(--surface-sunken);
    }
    .sl-store-chip--none {
        opacity: 0.75;
    }
    .sl-store-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        flex: none;
    }
</style>
