<template>
    <DashboardCard :icon="ICONS.replay" title="Restock radar">
        <template #action>
            <router-link class="dora-card-action dora-card-link" to="/stock">
                Stock →
            </router-link>
        </template>

        <CardLoadError
            v-if="failed"
            line="I couldn't work out what needs restocking."
            @retry="emit('retry')"
        />

        <div v-else-if="hasRows" class="dora-radar">
            <!-- Two columns on desktop, stacked on phones. Out on the left
                 because it is the worse state and the eye starts there. -->
            <section class="dora-radar__col">
                <div class="dora-radar__head">
                    <q-icon :name="ICONS.error" size="14px" />
                    Just ran out
                </div>
                <ul v-if="recentlyOut.length > 0" class="dora-cook-list">
                    <li v-for="row in recentlyOut" :key="row.stock_item_id" class="dora-radar__row">
                        <router-link class="dora-cook-name" :to="`/stock/${row.stock_item_id}`">
                            {{ row.name }}
                        </router-link>
                        <span class="dora-cook-meta">{{ whenLabel(row) }}</span>
                        <!-- The owner asked for "the same shopping cart button
                             from the stock overview rows" — this is literally
                             that component, in its `row` variant. It owns the
                             already-on-a-list toggle, the multi-list popover and
                             the toast, so the card emits nothing (R-011). -->
                        <AddToListButton variant="row" :stock-item-id="row.stock_item_id" />
                    </li>
                </ul>
                <p v-else class="dora-radar__none">Nothing's out.</p>
            </section>

            <section class="dora-radar__col">
                <div class="dora-radar__head">
                    <q-icon :name="ICONS.warning_amber" size="14px" />
                    Getting low
                </div>
                <ul v-if="recentlyLow.length > 0" class="dora-cook-list">
                    <li v-for="row in recentlyLow" :key="row.stock_item_id" class="dora-radar__row">
                        <router-link class="dora-cook-name" :to="`/stock/${row.stock_item_id}`">
                            {{ row.name }}
                        </router-link>
                        <span class="dora-cook-meta">{{ whenLabel(row) }}</span>
                        <AddToListButton variant="row" :stock-item-id="row.stock_item_id" />
                    </li>
                </ul>
                <p v-else class="dora-radar__none">Nothing's low.</p>
            </section>
        </div>

        <div v-else class="dora-empty dora-empty-ok">
            <q-icon :name="ICONS.check_circle" size="20px" class="q-mr-sm" />
            Everything's stocked.
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * Restock radar — what just ran out (left) and what just went low (right).
     *
     * Reworked on the owner's ask, 2026-09-04. It used to render
     * `/reports/keeps-running-out`: how often an item was already out at the
     * moment somebody put it on a list. A sharp signal, and the reports review
     * rated it the best thing on either surface — but it ranks on a *lifetime*
     * count, so the card looked the same every week and the radar never swept.
     * It also says nothing at all until an install has months of list history.
     *
     * This is the present tense of the same idea, and it keeps the verb: every
     * row ends in the stock overview's own cart button. The lifetime ranking
     * still lives on the reports page, which is where a history belongs.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { RestockRow } from 'src/services/api/dashboardApiService';

    const props = withDefaults(
        defineProps<{
            recentlyOut: RestockRow[];
            recentlyLow: RestockRow[];
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();

    const hasRows = computed(
        () => props.recentlyOut.length > 0 || props.recentlyLow.length > 0,
    );

    /**
     * How long it has been in this state. Coarse on purpose — "3 days ago" is
     * the actionable resolution, and an item that went low in March wants
     * "months ago", not a date nobody reads on a dashboard.
     *
     * Not `formatRelativeDay`: that names the *day* ("Tuesday"), and after a
     * fortnight a weekday name is useless. This answers "how long has this been
     * sitting there", which is the question the card is asking.
     */
    function whenLabel(row: RestockRow): string {
        const then = new Date(row.changed_at).getTime();
        const days = Math.floor((Date.now() - then) / 86_400_000);
        if (days <= 0) return 'today';
        if (days === 1) return 'yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 14) return 'last week';
        if (days < 60) return `${Math.round(days / 7)} weeks ago`;
        return `${Math.round(days / 30)} months ago`;
    }
</script>

<style scoped lang="scss">
    /* `.dora-cook-list`, `.dora-cook-name`, `.dora-cook-meta` and the empty
       states come from `css/dashboardCards.scss`. The two-column shell and the
       row's own grid are this card's. */

    .dora-radar {
        display: grid;
        /* R-078: the card is a container, so it sizes on its own width, never
           on the viewport — a two-up card in a half-width column must stack
           exactly as it does on a phone. `auto-fit` + a min track does that
           without the card knowing what a breakpoint is. */
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--space-4);
    }
    .dora-radar__col {
        min-width: 0;
    }
    .dora-radar__head {
        display: flex;
        align-items: center;
        gap: var(--space-1);
        margin-bottom: var(--space-2);
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-secondary);
    }
    /* D-014 — the icons carry the band, the words carry the meaning; neither
       column relies on colour alone. Tinting only the glyph keeps the heading
       text on the readable secondary token (D-002). */
    .dora-radar__col:first-child .dora-radar__head .q-icon {
        color: var(--semantic-negative);
    }
    .dora-radar__col:last-child .dora-radar__head .q-icon {
        color: var(--semantic-warning);
    }
    /* Same anatomy as `.dora-cook-row` but with the cart button as the only
       trailing control — three columns, not four. Declared here rather than
       adding a third modifier to the shared primitive: two consumers with a
       badge and one without is not yet a pattern. */
    .dora-radar__row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-1) var(--space-2);
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
    }
    .dora-radar__none {
        margin: 0;
        padding: var(--space-2) var(--space-3);
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }
</style>
