<template>
    <DashboardCard :icon="ICONS.list_alt" title="Shopping lists">
        <template #action>
            <router-link class="dora-card-action dora-card-link" to="/shopping-lists">
                All lists →
            </router-link>
        </template>

        <CardLoadError
            v-if="failed"
            line="I couldn't load your lists."
            @retry="emit('retry')"
        />

        <ul v-else-if="rows.length > 0" class="dora-cook-list">
            <li v-for="row in rows" :key="row.list.shopping_list_id" class="dora-lists-row">
                <router-link
                    class="dora-lists-link"
                    :to="`/shopping-lists/${row.list.shopping_list_id}`"
                >
                    <span class="dora-lists-tense">{{ row.tense }}</span>
                    <span class="dora-lists-name">{{ row.list.display_name }}</span>
                    <span class="dora-lists-meta">{{ metaFor(row) }}</span>
                </router-link>
            </li>
        </ul>

        <div v-else class="dora-empty">
            No lists yet.
            <router-link class="dora-empty-cta" to="/shopping-lists">Start one →</router-link>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The three shopping lists worth a shortcut: current · next · last
     * finished.
     *
     * Replaces "Primary shopping list" (owner, 2026-09-04). His objection was
     * two-part and both halves were right: the word *primary* was a fossil
     * from when a list's interesting property was being the cart button's
     * target, and *"why would I need to see my shopping list?"* — you don't,
     * on a dashboard. What you want is to **get to** the right one, and to be
     * told enough to know which that is.
     *
     * So each row is quick nav plus the two facts that identify a list at a
     * glance: how much is left to grab, and what it'll cost. Which list fills
     * which slot is a server decision (`/dashboard/lists`) — "current" is a
     * rule over status and three date fields, not something to re-derive in a
     * browser.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    // Layers the install flag with the per-user money opt-in — the same guard
    // every other dollar surface uses (ADR-005 / FU-823).
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { DashboardListCard } from 'src/services/api/dashboardApiService';

    const props = withDefaults(
        defineProps<{
            current: DashboardListCard | null;
            next: DashboardListCard | null;
            finished: DashboardListCard | null;
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{ (e: 'retry'): void }>();

    const { moneyEnabled } = useMoneyEnabled();

    type Row = { tense: string; list: DashboardListCard; done: boolean };

    /** Present, future, past — in that order, and any of the three may be
     *  absent. A household with one draft list gets one row, not two empty
     *  placeholders: an absent tense is not a state worth a slot. */
    const rows = computed<Row[]>(() => {
        const out: Row[] = [];
        if (props.current) {
            out.push({
                // A list somebody pressed Start shopping on says so — that is
                // the difference between "the one I'm holding" and "the one
                // I'll take".
                tense: props.current.status === 'shopping' ? 'Shopping now' : 'Current',
                list: props.current,
                done: false,
            });
        }
        if (props.next) out.push({ tense: 'Next', list: props.next, done: false });
        if (props.finished) {
            out.push({ tense: 'Last shop', list: props.finished, done: true });
        }
        return out;
    });

    /**
     * The one-line summary. Counts always; money only when it's on (ADR-005 —
     * a money-off household sees no dollar surface anywhere), and only when
     * the list actually priced something, so a list of unpriced lines says
     * "6 items" rather than a confident "$0.00".
     *
     * A finished list reports what it *cost*; an open one reports what's
     * *left to grab* — the same field would be the wrong number in the other
     * tense, which is why the server sends both.
     */
    function metaFor(row: Row): string {
        const l = row.list;
        const parts: string[] = [];
        if (row.done) {
            parts.push(l.line_count === 1 ? '1 item' : `${l.line_count} items`);
            if (moneyEnabled.value && l.total_price > 0) {
                parts.push(formatMoney(l.total_price));
            }
        } else {
            parts.push(
                l.unticked_count === 1 ? '1 to grab' : `${l.unticked_count} to grab`,
            );
            if (moneyEnabled.value && l.remaining_price > 0) {
                parts.push(formatMoney(l.remaining_price));
            }
        }
        return parts.join(' · ');
    }
</script>

<style scoped lang="scss">
    /* `.dora-cook-list` (the flex column) and the empty states come from
       `css/dashboardCards.scss`. The row here is its own shape rather than
       `.dora-cook-row`: that primitive is a name plus trailing *actions*, and
       every part of this row is the same single link, so it is one anchor
       rather than a grid with a control column. */
    .dora-lists-row {
        list-style: none;
    }
    .dora-lists-link {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        grid-template-areas:
            'tense meta'
            'name  meta';
        align-items: center;
        gap: 0 var(--space-3);
        padding: var(--space-2) var(--space-3);
        background: var(--surface-sunken);
        /* D-017 — a row nested inside a card is `--radius-md`. */
        border-radius: var(--radius-md);
        text-decoration: none;
        /* D-004 touch floor. The row is the tap target. */
        min-height: 44px;
    }
    .dora-lists-link:hover .dora-lists-name {
        text-decoration: underline;
    }
    .dora-lists-tense {
        grid-area: tense;
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        /* R-069: accent as text is `--accent-ink`, never the fill tone. */
        color: var(--accent-ink);
    }
    .dora-lists-name {
        grid-area: name;
        color: var(--text-primary);
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-lists-meta {
        grid-area: meta;
        font-size: calc(var(--font-size-xs) * 1rem);
        color: var(--text-secondary);
        white-space: nowrap;
    }
</style>
