<template>
    <DashboardCard :icon="ICONS.replay" title="Restock radar">
        <template #action>
            <router-link
                v-if="items.length > 0"
                class="dora-card-action dora-card-link"
                to="/stock"
            >
                Pantry →
            </router-link>
        </template>
        <CardLoadError
            v-if="failed"
            line="I couldn't work out what you keep running out of."
            @retry="emit('retry')"
        />
        <ul v-else-if="items.length > 0" class="dora-cook-list">
            <li v-for="item in items" :key="item.stock_item_id" class="dora-cook-row">
                <router-link class="dora-cook-name" :to="`/stock/${item.stock_item_id}`">
                    {{ item.name }}
                </router-link>
                <span class="dora-cook-meta">ran out {{ item.times_out_when_added }}×</span>
                <BaseButton
                    variant="ghost"
                    dense
                    size="sm"
                    :icon="ICONS.shopping_cart"
                    label="Add"
                    @click="emit('add', item.stock_item_id)"
                />
            </li>
        </ul>
        <div v-else class="dora-empty">
            Once you've restocked the same things a few times, I'll flag what to
            keep an eye on.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * Items the household keeps running out of — the dashboard's one predictive
     * card.
     *
     * The signal is stronger than "went out of stock": the server walks every
     * shopping-list line that ever had an `added_at` and counts how often the
     * item was *already* out at the moment it was added. So it means **"you ran
     * out of this before you got around to restocking it"** — a planning
     * failure, not a stock state. `REPORTS_PAGE_REVIEW.md` §3.5 rates it the most
     * genuinely insightful thing on either surface, and notes the title
     * undersells it.
     *
     * Extracted from `DashboardPage.vue` (FU-829). The row anatomy comes from
     * `css/dashboardCards.scss`, shared with "Next to cook" — the reason those
     * classes are in a stylesheet rather than in either component. The Add
     * action is emitted so the page can route it through the shared
     * `useStockItemActions`, which owns the no-draft / multiple-draft branches
     * and the toast (R-011).
     */
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { KeepsRunningOutRow } from 'src/services/api/reportsApiService';

    withDefaults(
        defineProps<{
            items: KeepsRunningOutRow[];
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{
        (e: 'retry'): void;
        (e: 'add', stockItemId: string): void;
    }>();
</script>
