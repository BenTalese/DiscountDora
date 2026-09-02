<template>
    <DashboardCard :icon="ICONS.restaurant_menu" title="Kitchen memory">
        <CardLoadError
            v-if="cooksFailed && boughtFailed"
            line="I couldn't load your kitchen memory."
            @retry="retryBoth"
        />
        <template v-else>
            <CardLoadError
                v-if="cooksFailed"
                line="I couldn't load your cook history."
                @retry="emit('retry-cooks')"
            />
            <template v-else>
                <!-- The sellable number, at a sellable size. It used to be the
                     SMALLEST text on the card — "14 cooks · 31 meals-worth" in an
                     11.5px note, below the legibility floor (§3.8, D-003). -->
                <p class="km-headline">{{ headline }}</p>
                <p v-if="repertoireLine" class="km-note">{{ repertoireLine }}</p>

                <!-- Columns, not a smoothed area line. `cook_count` per bucket is
                     0, 1 or 2 for a normal household, and a smoothed curve through
                     integers implies 1.4 cooks happened on Tuesday (§3.8.1,
                     §4.10.5). No chart library involved. -->
                <ul v-if="columns.length > 0" class="km-columns" role="presentation">
                    <li v-for="col in columns" :key="col.date" class="km-column">
                        <span
                            class="km-column__bar"
                            :style="{ height: `${col.heightPct}%` }"
                        >
                            <q-tooltip>
                                {{ col.date }} — {{ col.cookCount }}
                                cook{{ col.cookCount === 1 ? '' : 's' }}
                            </q-tooltip>
                        </span>
                    </li>
                </ul>
            </template>

            <div v-if="!cooksFailed && (mealsCooked?.top_recipes.length ?? 0) > 0" class="km-lists">
                <section>
                    <h4 class="km-heading">Cooked most</h4>
                    <ul class="km-list">
                        <li
                            v-for="row in mealsCooked!.top_recipes.slice(0, 5)"
                            :key="row.recipe_id ?? row.recipe_name"
                        >
                            <component
                                :is="row.recipe_id ? 'a' : 'span'"
                                class="km-list__name"
                                :href="row.recipe_id ? `#/cookbook/${row.recipe_id}` : undefined"
                            >{{ row.recipe_name }}</component>
                            <span class="km-list__count">×{{ row.cook_count }}</span>
                        </li>
                    </ul>
                </section>
                <section>
                    <h4 class="km-heading">Bought most</h4>
                    <CardLoadError
                        v-if="boughtFailed"
                        line="I couldn't load what you buy most."
                        @retry="emit('retry-bought')"
                    />
                    <ul v-else-if="(mostBought?.rows.length ?? 0) > 0" class="km-list">
                        <li v-for="row in mostBought!.rows.slice(0, 5)" :key="row.stock_item_id">
                            <a class="km-list__name" :href="`#/stock/${row.stock_item_id}`">
                                {{ row.name }}
                            </a>
                            <span class="km-list__count">×{{ row.appearances }}</span>
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        No archived lists in this range yet.
                    </div>
                </section>
            </div>

            <div v-else-if="!cooksFailed" class="dora-empty">
                No cooks logged in this range yet. Finish a recipe in cook mode to
                start building your memory.
            </div>
        </template>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "What do we actually eat?" — cooks, repertoire, and what you keep buying.
     *
     * `REPORTS_PAGE_REVIEW.md` §5 merges meals-cooked with a repertoire count;
     * §3.8 is the argument for the repertoire specifically — *"nothing else in
     * the app can answer that, and it drives people back into the cookbook"*.
     *
     * **Most-bought lands here rather than in Spend**, which the §5 preview left
     * open. Two reasons: it is the same question in the other tense (what you
     * buy is what you eat), and — the deciding one — it is **count-based and
     * therefore ungated**. Folding it into the money card would delete it from a
     * money-off install, leaving that household two cards instead of the four
     * working reports the nav entry is justified by (FU-816).
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import type {
        MealsCookedResponse,
        MostBoughtResponse,
        ReportRange,
    } from 'src/services/api/reportsApiService';

    const props = withDefaults(defineProps<{
        range: ReportRange;
        mealsCooked: MealsCookedResponse | null;
        mostBought: MostBoughtResponse | null;
        cooksFailed?: boolean;
        boughtFailed?: boolean;
    }>(), { cooksFailed: false, boughtFailed: false });

    const emit = defineEmits<{
        (e: 'retry-cooks'): void;
        (e: 'retry-bought'): void;
    }>();

    function retryBoth() {
        emit('retry-cooks');
        emit('retry-bought');
    }

    const WINDOW_WORDS: Record<ReportRange, string> = {
        '30d': 'in the last 30 days',
        '90d': 'in the last 90 days',
        '1y': 'in the last year',
        '2y': 'in the last 2 years',
        '5y': 'in the last 5 years',
        'all': 'all time',
    };

    const headline = computed(() => {
        const m = props.mealsCooked;
        if (!m || m.cook_count === 0) return 'Nothing cooked in this range yet.';
        const parts = [
            `You cooked ${m.cook_count} time${m.cook_count === 1 ? '' : 's'} `
            + `${WINDOW_WORDS[props.range]} — ${m.meals_total} meals`,
        ];
        if (m.distinct_recipes > 0) {
            parts.push(
                `, ${m.distinct_recipes} different `
                + `recipe${m.distinct_recipes === 1 ? '' : 's'}`,
            );
        }
        parts.push('.');
        return parts.join('');
    });

    /** The untouched tail. Deliberately not range-scoped — the server measures it
     *  over the last 365 days, so a 30-day view doesn't announce that you've
     *  abandoned almost everything you own. */
    const repertoireLine = computed(() => {
        const m = props.mealsCooked;
        if (!m || m.total_recipes <= 0 || m.uncooked_recipes <= 0) return null;
        return `${m.uncooked_recipes} of your ${m.total_recipes} saved `
            + `recipe${m.total_recipes === 1 ? '' : 's'} `
            + `${m.uncooked_recipes === 1 ? 'hasn\'t' : 'haven\'t'} been cooked in a year.`;
    });

    const columns = computed(() => {
        const timeline = props.mealsCooked?.timeline ?? [];
        const peak = Math.max(1, ...timeline.map((p) => p.cook_count));
        return timeline.map((p) => ({
            date: p.date,
            cookCount: p.cook_count,
            // A floor so a bucket with one cook is visibly a column rather than
            // a hairline, without misreporting its share of the peak.
            heightPct: p.cook_count === 0 ? 0 : Math.max(8, (p.cook_count / peak) * 100),
        }));
    });
</script>

<style scoped lang="scss">
    .km-headline {
        margin: 0;
        font-size: calc(var(--font-size-md) * 1rem);
        line-height: 1.4;
    }
    .km-note {
        margin: var(--space-1) 0 0;
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }
    .km-columns {
        list-style: none;
        margin: var(--space-4) 0 0;
        padding: 0;
        display: flex;
        align-items: flex-end;
        gap: 2px;
        height: 72px;
    }
    .km-column {
        flex: 1 1 0;
        min-width: 2px;
        height: 100%;
        display: flex;
        align-items: flex-end;
    }
    .km-column__bar {
        display: block;
        width: 100%;
        min-height: 2px;
        background: var(--brand-primary);
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    }
    .km-lists {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: var(--space-4);
        margin-top: var(--space-4);
    }
    @media (max-width: 599px) {
        .km-lists { grid-template-columns: 1fr; }
    }
    .km-heading {
        margin: 0 0 var(--space-2);
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .km-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
    }
    .km-list li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-2) var(--space-3);
        /* D-004 tap-target floor — see the sibling note in
           `WasteAndRunOutsCard`. Every row is a link. */
        min-height: 44px;
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
    }
    .km-list__name {
        color: var(--text-primary);
        font-weight: 500;
        text-decoration: none;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    a.km-list__name:hover { text-decoration: underline; }
    .km-list__count {
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
        font-variant-numeric: tabular-nums;
    }
</style>
