<template>
    <!-- No primary list set is a real state, not an absence of data, so it gets
         its own whole-card treatment: the card becomes a link to go and pick
         one, because that is the only useful thing to do here. -->
    <DashboardCard
        v-if="!list"
        :icon="ICONS.shopping_cart"
        title="Primary shopping list"
        :to="'/shopping-lists'"
    >
        <template #action>
            <span class="dora-card-action">Pick one →</span>
        </template>
        <div class="dora-empty">
            No primary set — the cart button needs one to one-tap items in.
        </div>
    </DashboardCard>

    <DashboardCard v-else :icon="ICONS.shopping_cart" title="Primary shopping list">
        <template #action>
            <router-link
                class="dora-card-action dora-card-link"
                :to="`/shopping-lists/${list.shopping_list_id}`"
            >
                Open list →
            </router-link>
        </template>
        <div class="dora-primary-list-name">{{ list.display_name }}</div>

        <!-- FU-840 — a failed detail fetch used to leave the skeleton spinning
             forever, because `stats` simply stayed null and the `v-else` branch
             is the skeleton. -->
        <CardLoadError
            v-if="failed"
            line="I couldn't load this list's totals."
            class="q-mt-sm"
            @retry="emit('retry')"
        />
        <div v-else-if="stats" class="dora-stat-grid q-mt-sm">
            <div class="dora-stat">
                <div class="dora-stat-num">
                    <AnimatedNumber :value="stats.unticked" />
                </div>
                <div class="dora-stat-label">to grab</div>
            </div>
            <div class="dora-stat">
                <div class="dora-stat-num">
                    <!-- FU-821 / D-006: money renders through `formatMoney`, not
                         a bare symbol prefix. This used to be `:prefix` with no
                         `:decimals`, so $47.30 read "$47". -->
                    <AnimatedNumber :value="stats.remaining" :format="formatMoney" />
                </div>
                <div class="dora-stat-label">remaining</div>
            </div>
            <div v-if="stats.savings > 0" class="dora-stat dora-stat-ok">
                <div class="dora-stat-num">
                    <AnimatedNumber :value="stats.savings" :format="formatMoney" />
                </div>
                <div class="dora-stat-label">saved vs RRP</div>
            </div>
        </div>
        <!-- D-007 (DR-8): the skeleton mirrors the stat grid, so the totals fade
             into reserved space instead of replacing a "Loading totals…" string
             and shoving the layout. -->
        <div v-else class="dora-stat-grid q-mt-sm" aria-hidden="true">
            <div v-for="n in 2" :key="n" class="dora-stat">
                <AppSkeleton type="line" width="34px" height="1.5em" class="dash-skel-line" />
                <AppSkeleton type="line" width="44px" />
            </div>
        </div>

        <router-link
            v-if="otherActiveCount > 0"
            class="dora-card-footer-link"
            to="/shopping-lists"
        >
            +{{ otherActiveCount }} other active
            {{ otherActiveCount === 1 ? 'list' : 'lists' }} →
        </router-link>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The primary shopping list's live totals.
     *
     * This card absorbed the standalone "Shopping lists" counter in the
     * rebuild's Phase 1 (§2.6 — raw totals answer no question the user has); the
     * count survives as the "+N other active lists" footer link, which is the
     * same information attached to something actionable.
     *
     * The totals are **server-owned** (state-ownership Type B): they come off the
     * detail's `totals`, not from summing `priceOfLine` in the browser.
     *
     * Extracted from `DashboardPage.vue` (FU-829). The two branches were two
     * sibling `<div>`s in the page, each with its own column classes and order
     * style — they are one component with a `v-if` now, which is what stops the
     * grid maths having to know there are two.
     */
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    import AnimatedNumber from 'src/components/AnimatedNumber.vue';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';

    export type PrimaryListStats = {
        remaining: number;
        savings: number;
        unticked: number;
    };

    withDefaults(
        defineProps<{
            /** The quick-add target summary, or null when no primary is set. */
            list: { shopping_list_id: string; display_name: string } | null;
            /** Server-owned totals, or null while the detail is still loading. */
            stats: PrimaryListStats | null;
            /** Active lists other than this one. */
            otherActiveCount: number;
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();
</script>

<style scoped lang="scss">
    /* The stat-grid primitive is shared with Pantry value, so it lives in
       `css/dashboardCards.scss`. These two are this card's own. */
    .dora-primary-list-name {
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
        color: var(--text-primary);
    }
    /* Footer link ("+N other lists →"). */
    .dora-card-footer-link {
        display: inline-block;
        margin-top: var(--space-3);
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 600;
        /* R-069: accent as text is `--accent-ink`. */
        color: var(--accent-ink);
        text-decoration: none;
    }
    .dora-card-footer-link:hover {
        text-decoration: underline;
    }
    /* `.dash-skel-line` is in `css/dashboardCards.scss` — the page's whole-grid
       loading skeleton uses it too. */
</style>
