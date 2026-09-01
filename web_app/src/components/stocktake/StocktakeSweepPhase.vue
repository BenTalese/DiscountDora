<template>
    <!--
        Phase 3 of the three-phase stocktake — **Sweep** (D-4). Housekeeping:
        shrink → work → **tidy**.

        These are items that dropped out of rotation **since your last session** —
        not everything Dora has ever stopped tracking. That distinction is the
        whole design: the engagement gate correctly hides plenty of boring things
        (the tin you stopped buying two years ago is *supposed* to be invisible),
        and re-listing all of it every session is the nagging this plan removes.
        A departure is an event: a handful per session, and zero for a stable
        pantry.

        **Copy rule from D-4: never "dead items".** It judges something the user
        may still care about — the phrasing is "Dora's stopped tracking these".

        Three affordances, and the third one is the interesting one. The plan
        flagged a wiring risk: the engagement gate keys off in-stock /
        ever-opened / level-adjusted-in-60d / on-a-list-in-60d, and a plain
        check bumps only `last_checked_at` — **not one of those signals**. That
        was confirmed at implementation, so "I still keep this" does NOT write a
        check (which would have looked like it worked and changed nothing).
        It opens the level picker instead: setting a level writes a
        `StockLevelChange` and, for anything in stock, satisfies the gate
        outright. That's also the truthful action — the reason Dora lost track is
        that nobody has said what's on the shelf.
    -->
    <div class="stocktake-sweep">
        <div class="stocktake-sweep__head">
            <div class="text-h6">Dora's stopped tracking these</div>
            <div class="text-caption dora-text-muted-7 q-mt-xs">
                {{ items.length }} item{{ items.length === 1 ? '' : 's' }}
                {{ items.length === 1 ? 'hasn\'t' : "haven't" }} moved in a while, so
                {{ items.length === 1 ? "it's" : "they're" }} out of the stocktake
                rotation. Nothing's been deleted — this is just a chance to tidy up.
            </div>
        </div>

        <q-list separator class="stocktake-sweep__list">
            <q-item v-for="item in items" :key="item.stock_item_id">
                <q-item-section>
                    <q-item-label class="stocktake-sweep__name">
                        {{ item.name }}
                        <span v-if="locationOf(item)" class="dora-text-muted-7">
                            · {{ locationOf(item) }}
                        </span>
                    </q-item-label>
                    <!-- The evidence. "Dora's stopped tracking this" is only
                         fair if you can see what it's based on. -->
                    <q-item-label caption class="stocktake-sweep__why">
                        Last activity {{ formatDate(item.last_activity_at) }}
                        <template v-if="item.stock_level_name">
                            · {{ item.stock_level_name }}
                        </template>
                    </q-item-label>

                    <div class="stocktake-sweep__actions">
                        <BaseButton
                            variant="subtle"
                            dense
                            :icon="ICONS.check"
                            label="I still keep this…"
                            :disable="busy"
                            @click="emit('keep', item)"
                        />
                        <BaseButton
                            variant="subtle"
                            dense
                            :icon="ICONS.mute"
                            label="Mute"
                            :disable="busy"
                            @click="emit('mute', item)"
                        />
                        <BaseButton
                            variant="subtle"
                            dense
                            :icon="ICONS.delete"
                            label="Delete"
                            :disable="busy"
                            @click="emit('remove', item)"
                        />
                    </div>
                </q-item-section>
            </q-item>
        </q-list>

        <div class="stocktake-sweep__foot">
            <!-- Doing nothing is a perfectly good answer here, and the button
                 says so rather than implying an obligation. -->
            <BaseButton
                variant="primary"
                class="full-width"
                label="Leave them be"
                :loading="busy"
                @click="emit('finish')"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { formatDate } from 'src/composables/useDateFormat';
    import { formatLocation } from 'src/helpers/locationDisplay';
    import type { StocktakeSweptItem } from 'src/services/api/stocktakeApiService';

    defineProps<{
        items: StocktakeSweptItem[];
        busy?: boolean;
    }>();

    /** Full breadcrumb, not the leaf. Owner, 2026-09-01: "Top shelf" on its own
     *  names nothing — and deciding whether you still keep something is easier
     *  when you can see where it was meant to live. Falls back to the leaf name
     *  for rows that pre-date the breadcrumb field. */
    function locationOf(item: StocktakeSweptItem): string {
        return formatLocation(item.stock_location_breadcrumb, 'full')
            || (item.stock_location_name ?? '');
    }

    // The page performs every one of these — it owns the API service, the level
    // picker dialog and the summary counters. This component only reports the
    // gesture (same split the walk card uses).
    const emit = defineEmits<{
        (e: 'keep', item: StocktakeSweptItem): void;
        (e: 'mute', item: StocktakeSweptItem): void;
        (e: 'remove', item: StocktakeSweptItem): void;
        (e: 'finish'): void;
    }>();
</script>

<style scoped lang="scss">
    .stocktake-sweep {
        display: flex;
        flex-direction: column;
        max-height: 100%;
        width: 100%;
        max-width: 520px;
        margin: 0 auto;
        padding: 16px;
        gap: var(--space-3);
    }
    /* Page ink — the runner shell follows the theme now (owner, 2026-09-01)
       rather than being hard-coded dark under every theme. */
    .stocktake-sweep__head {
        text-align: center;
        color: var(--text-primary);
    }
    .stocktake-sweep__list {
        flex: 1 1 auto;
        overflow-y: auto;
        background: var(--surface-component);
        color: var(--text-primary);
        border-radius: 12px;
    }
    .stocktake-sweep__name {
        font-weight: 600;
    }
    .stocktake-sweep__why {
        color: var(--text-secondary);
        white-space: normal;
    }
    /* Wraps on a phone rather than squeezing three labelled buttons onto one
       line — D-rule tap targets win over keeping the row one line tall. */
    .stocktake-sweep__actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
        margin-top: var(--space-2);
    }
    .stocktake-sweep__foot {
        flex: 0 0 auto;
    }
</style>
