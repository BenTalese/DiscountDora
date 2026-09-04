<template>
    <DashboardCard :icon="ICONS.shopping_cart" title="Before you shop">
        <template #action>
            <span v-if="shopInDays !== null" class="dora-card-action">
                {{ shopLabel }}
            </span>
            <router-link v-else class="dora-card-action dora-card-link" to="/shopping-lists">
                Lists →
            </router-link>
        </template>

        <CardLoadError
            v-if="failed"
            line="I couldn't work out what you'll need."
            @retry="emit('retry')"
        />

        <template v-else-if="runningOut.length > 0 || planGaps.length > 0">
            <!-- Running low, and on no list. The second half of that sentence is
                 the whole point of the card: the bell and the stock page both
                 say the first half already. -->
            <div v-if="runningOut.length > 0" class="dora-shop-group">
                <div class="dora-shop-group__head">Running low, not on a list</div>
                <ul class="dora-cook-list">
                    <li
                        v-for="row in runningOut"
                        :key="row.stock_item_id"
                        class="dora-cook-row"
                    >
                        <router-link class="dora-cook-name" :to="`/stock/${row.stock_item_id}`">
                            {{ row.name }}
                        </router-link>
                        <span class="dora-cook-meta">
                            {{ row.band === 'out' ? 'out' : 'low' }}<template v-if="row.is_essential"> · essential</template>
                        </span>
                        <!-- The stock overview's own cart button, in its `row`
                             variant: it owns the already-on-a-list toggle, the
                             multi-list popover and the toast (R-011). Which
                             matters more here than anywhere — this card's whole
                             premise is that it only lists things *not* on a
                             list, so the moment you add one the button and the
                             row agree without a round trip. -->
                        <AddToListButton variant="row" :stock-item-id="row.stock_item_id" />
                    </li>
                </ul>
            </div>

            <!-- What the plan needs and the pantry hasn't got. Distinct from the
                 group above: an item can be fully stocked for everyday use and
                 still short for a week that wants it three times. -->
            <div v-if="planGaps.length > 0" class="dora-shop-group">
                <div class="dora-shop-group__head">Your plan needs these</div>
                <ul class="dora-cook-list">
                    <li v-for="row in planGaps" :key="row.stock_item_id" class="dora-cook-row">
                        <router-link class="dora-cook-name" :to="`/stock/${row.stock_item_id}`">
                            {{ row.name }}
                        </router-link>
                        <span class="dora-cook-meta">{{ gapLabel(row) }}</span>
                        <AddToListButton variant="row" :stock-item-id="row.stock_item_id" />
                    </li>
                </ul>
            </div>
        </template>

        <div v-else class="dora-empty dora-empty-ok">
            <q-icon :name="ICONS.check_circle" size="20px" class="q-mr-sm" />
            Nothing's missing — your lists have it covered.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "Before you shop" — what won't survive until the next shop.
     *
     * The second of the two cards that replaced "Needs your attention" and
     * "Dora suggests" (owner, 2026-09-04), and it earns its place on one join
     * the rest of the app never makes: **is this already on a list?** The bell
     * says "you're low on flour". The stock page says "you're low on flour".
     * Neither knows you added it to Saturday's list ten minutes ago, so both
     * keep saying it. This card only shows what is still outstanding, which is
     * why its empty state is a genuine "you're done" rather than "no data".
     *
     * Both halves are server-picked (`/dashboard/before-you-shop`) — the
     * list-membership join, the recorded bands, and the plan's uncovered demand
     * (which is `gather_planned_demand`, the same signal the stock-item page's
     * planned-demand card reads, R-003).
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type {
        PlanGapRow,
        RunningOutRow,
    } from 'src/services/api/dashboardApiService';

    const props = withDefaults(
        defineProps<{
            runningOut: RunningOutRow[];
            planGaps: PlanGapRow[];
            /** Days until the nearest planned shop date on an active list, or
             *  null when no list names one. */
            shopInDays: number | null;
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();

    /** The card's frame: when the shop actually is. A passed date still reads
     *  honestly ("shop overdue") rather than as a negative countdown — an open
     *  list with Tuesday's date on Thursday is a real and common state. */
    const shopLabel = computed(() => {
        const days = props.shopInDays;
        if (days === null) return '';
        if (days < 0) return 'shop overdue';
        if (days === 0) return 'shopping today';
        if (days === 1) return 'shopping tomorrow';
        return `shopping in ${days} days`;
    });

    /** "3 meals · from Thu". The meal count is what makes this different from
     *  the group above — one meal short is a nudge, four is the week. */
    function gapLabel(row: PlanGapRow): string {
        const meals = row.needed_meals === 1 ? '1 meal' : `${row.needed_meals} meals`;
        if (!row.earliest_needed) return meals;
        const when = new Date(`${row.earliest_needed}T00:00:00`);
        return `${meals} · from ${when.toLocaleDateString(undefined, { weekday: 'short' })}`;
    }
</script>

<style scoped lang="scss">
    /* The row primitive and empty states come from `css/dashboardCards.scss`.
       The group heading is this card's own — it is the only dashboard card with
       two labelled sections, because it is the only one answering two questions
       that end in the same verb. */
    .dora-shop-group + .dora-shop-group {
        margin-top: var(--space-4);
    }
    .dora-shop-group__head {
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin-bottom: var(--space-2);
    }
</style>
