<template>
    <DashboardCard :icon="ICONS.wasted" title="Waste & run-outs">
        <CardLoadError
            v-if="wasteFailed && runOutsFailed"
            line="I couldn't load your waste or run-outs."
            @retry="retryBoth"
        />
        <template v-else>
            <!-- ── Thrown out ─────────────────────────────────────────── -->
            <CardLoadError
                v-if="wasteFailed"
                line="I couldn't load your wastage."
                @retry="emit('retry-waste')"
            />
            <template v-else-if="waste">
                <div class="wr-summary">
                    <span class="wr-summary__figure">{{ waste.total_events }}</span>
                    <span class="wr-summary__caption">
                        item{{ waste.total_events === 1 ? '' : 's' }} thrown out
                        in the last {{ waste.window_days }} day{{ waste.window_days === 1 ? '' : 's' }}
                    </span>
                </div>

                <!-- The best-designed thing on the old page, kept verbatim: a
                     fixed 5-up grid where zero-count tiles still render, dimmed,
                     so the shape is stable and "you haven't logged any of these"
                     reads as intentional rather than as missing data. -->
                <div class="wr-reasons">
                    <div
                        v-for="tile in reasonTiles"
                        :key="tile.reason"
                        class="wr-reason"
                        :class="{ 'wr-reason--zero': tile.count === 0 }"
                    >
                        <q-icon :name="tile.icon" size="20px" class="wr-reason__icon" />
                        <span class="wr-reason__count">{{ tile.count }}</span>
                        <span class="wr-reason__label">{{ tile.label }}</span>
                    </div>
                </div>

                <ul v-if="wastedShown.length > 0" class="wr-list">
                    <li
                        v-for="row in wastedShown"
                        :key="row.stock_item_id ?? row.stock_item_name"
                    >
                        <component
                            :is="row.stock_item_id ? 'a' : 'span'"
                            class="wr-list__name"
                            :href="row.stock_item_id ? `#/stock/${row.stock_item_id}` : undefined"
                        >{{ row.stock_item_name }}</component>
                        <span class="wr-list__count">×{{ row.event_count }}</span>
                    </li>
                </ul>
                <!-- §3.4 — `most_wasted` returns up to 25 rows and the list had
                     no cap, so at ~37px a row this card could reach ~1200px and
                     drag its grid partner to the same height (D-011). Capped,
                     with the remainder counted rather than silently dropped. -->
                <div v-if="hiddenWastedCount > 0" class="wr-more">
                    + {{ hiddenWastedCount }} more, not shown
                </div>
                <div v-if="waste.most_wasted.length === 0" class="dora-empty">
                    Nothing wasted in this range — nicely played.
                </div>
            </template>

            <!-- ── Ran out before you restocked ───────────────────────── -->
            <h4 class="wr-heading">Ran out before you restocked</h4>
            <!-- §3.5 — the widget's title used to describe the symptom. What it
                 actually knows is narrower and more useful: it resolves what
                 level an item was at *the moment it went on a list*, so this is
                 a planning failure, not a stock state. -->
            <p class="wr-note">
                Items you added to a list when they were already out — you noticed
                after you'd run dry.
            </p>
            <CardLoadError
                v-if="runOutsFailed"
                line="I couldn't load your run-outs."
                @retry="emit('retry-run-outs')"
            />
            <ul v-else-if="runOutRows.length > 0" class="wr-list">
                <li v-for="row in runOutRows" :key="row.stock_item_id">
                    <a class="wr-list__name" :href="`#/stock/${row.stock_item_id}`">
                        {{ row.name }}
                    </a>
                    <span class="wr-list__count">{{ row.times_out_when_added }}×</span>
                </li>
            </ul>
            <div v-else class="dora-empty">
                Nothing's been added to a list while out of stock — nicely played.
            </div>
        </template>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "What am I mismanaging?" — wastage and run-outs, merged.
     *
     * `REPORTS_PAGE_REVIEW.md` §5: *"they are the same story"*. Food you threw
     * away and food you ran out of before restocking are the two ends of buying
     * the wrong amount, and reading them side by side is the only way the pair
     * says anything — a household with both problems is buying erratically, one
     * with only the second is buying too little.
     *
     * **"Mark all essential" is deliberately gone** (§3.5): an unconfirmed bulk
     * mutation across ten items, with no undo, no per-row control and no
     * awareness of current state — it re-set items that were already essential
     * and still toasted "Marked 10 items essential". `D-008` wants a confirm on
     * a state change that size, and INV-10 already concluded the right home for
     * setting the flag is the stock-overview multi-select, where the "Essentials"
     * filter chip lives so setting and filtering sit together. Rows link to the
     * item instead.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import type { KeepsRunningOutResponse } from 'src/services/api/reportsApiService';
    import type { WasteInsights } from 'src/services/api/wasteApiService';

    const props = withDefaults(defineProps<{
        waste: WasteInsights | null;
        keepsOut: KeepsRunningOutResponse | null;
        wasteFailed?: boolean;
        runOutsFailed?: boolean;
    }>(), { wasteFailed: false, runOutsFailed: false });

    const emit = defineEmits<{
        (e: 'retry-waste'): void;
        (e: 'retry-run-outs'): void;
    }>();

    function retryBoth() {
        emit('retry-waste');
        emit('retry-run-outs');
    }

    const WASTE_REASON_TILES: {
        reason: 'expired' | 'spoiled' | 'did_not_like' | 'overbought' | 'other';
        label: string;
        icon: string;
    }[] = [
        { reason: 'expired', label: 'Expired', icon: ICONS.wasteExpired },
        { reason: 'spoiled', label: 'Spoiled', icon: ICONS.wasteSpoiled },
        { reason: 'did_not_like', label: "Didn't like", icon: ICONS.wasteDidNotLike },
        { reason: 'overbought', label: 'Overbought', icon: ICONS.wasteOverbought },
        { reason: 'other', label: 'Other', icon: ICONS.wasteOther },
    ];
    const reasonTiles = computed(() =>
        WASTE_REASON_TILES.map((t) => ({
            ...t,
            count: props.waste?.by_reason[t.reason] ?? 0,
        })),
    );

    /** Both lists cap at the same number so neither half of the card can push
     *  the other off the bottom of a shared grid row (§3.4 / D-011). */
    const VISIBLE_ROWS = 6;
    const wastedShown = computed(
        () => (props.waste?.most_wasted ?? []).slice(0, VISIBLE_ROWS),
    );
    const hiddenWastedCount = computed(
        () => Math.max(0, (props.waste?.most_wasted.length ?? 0) - VISIBLE_ROWS),
    );
    const runOutRows = computed(
        () => (props.keepsOut?.rows ?? []).slice(0, VISIBLE_ROWS),
    );
</script>

<style scoped lang="scss">
    .wr-summary {
        display: flex;
        align-items: baseline;
        gap: var(--space-2);
        margin-bottom: var(--space-3);
    }
    .wr-summary__figure {
        font-size: calc(var(--font-size-3xl) * 1rem);
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }
    .wr-summary__caption {
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }
    .wr-reasons {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: var(--space-2);
        margin-bottom: var(--space-3);
    }
    @media (max-width: 599px) {
        .wr-reasons { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    .wr-reason {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: var(--space-2) var(--space-1);
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
        text-align: center;
    }
    .wr-reason--zero { opacity: 0.55; }
    .wr-reason__icon { color: var(--text-secondary); }
    .wr-reason__count {
        font-size: calc(var(--font-size-lg) * 1rem);
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }
    .wr-reason__label {
        /* D-003 floor. The old tile ran this at 11.5px on a ~95px square, so a
           two-word label ("Didn't like") wrapped inside its own tile. */
        font-size: calc(var(--font-size-xs) * 1rem);
        color: var(--text-secondary);
        line-height: 1.15;
    }
    .wr-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
    }
    .wr-list li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-2) var(--space-3);
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
    }
    /* A real <a href> rather than a click handler on a bare element: keyboard
       focusable, middle-clickable, and visible to a screen reader's link list
       (§4.9, A6, R-011). */
    .wr-list__name {
        color: var(--text-primary);
        font-weight: 500;
        text-decoration: none;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    a.wr-list__name:hover { text-decoration: underline; }
    .wr-list__count {
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }
    .wr-more {
        margin-top: var(--space-2);
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }
    .wr-heading {
        margin: var(--space-5) 0 0;
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
    }
    .wr-note {
        margin: var(--space-1) 0 var(--space-3);
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }
</style>
