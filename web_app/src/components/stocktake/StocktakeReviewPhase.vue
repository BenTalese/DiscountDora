<template>
    <!--
        Phase 1 of the three-phase stocktake — **Review** (D-3 / D-4).
        A desk screen: these items are worked out from logged evidence
        (purchases, cooks), so you don't need to be standing in the pantry to
        agree with them.

        **The critical constraint from D-3: this must NOT be a "Confirm all (12)"
        button.** Users tap that reflexively by session three, at which point it
        *is* the auto-check that was explicitly rejected, with a human-shaped fig
        leaf — and every risk that rejection was protecting against comes back.

        So the screen is built to be *read*: real item names, the level Dora
        believes, and her one-line reason, each on its own row. Everything is
        pre-ticked, so agreeing is still one tap. The value being delivered is
        not "confirm in bulk" — it's that **disagreeing is cheap**: untick a row
        and it flows into the walk, where you'll look at it properly.
    -->
    <div class="stocktake-review">
        <div class="stocktake-review__head">
            <div class="text-h6">Dora's fairly sure about these</div>
            <div class="text-caption dora-text-muted-7 q-mt-xs">
                Worked out from your shopping and cooking — no need to go and look.
                Untick anything you'd rather check yourself and it'll be waiting
                in the walk.
            </div>
        </div>

        <q-list separator class="stocktake-review__list">
            <q-item
                v-for="item in items"
                :key="item.stock_item_id"
                clickable
                @click="toggle(item.stock_item_id)"
            >
                <q-item-section side top>
                    <!-- DR-15 / D-010: the tick is the gesture this phase is
                         made of, repeated once per item. `dora-press`
                         (motion.scss) answers each one in 120ms. -->
                    <q-checkbox
                        class="dora-press"
                        :model-value="isTicked(item.stock_item_id)"
                        @update:model-value="toggle(item.stock_item_id)"
                        @click.stop
                    />
                </q-item-section>
                <q-item-section>
                    <q-item-label class="stocktake-review__name">
                        {{ item.name }}
                        <span v-if="item.stock_location_name" class="dora-text-muted-7">
                            · {{ item.stock_location_name }}
                        </span>
                    </q-item-label>
                    <q-item-label caption class="stocktake-review__believed">
                        Dora thinks
                        <strong>{{ bandWord(item.belief_band) }}</strong>
                        <template v-if="item.stock_level_name">
                            · recorded as {{ item.stock_level_name }}
                        </template>
                    </q-item-label>
                    <q-item-label v-if="item.belief_reason" caption class="stocktake-review__reason">
                        {{ item.belief_reason }}
                    </q-item-label>
                </q-item-section>
            </q-item>
        </q-list>

        <div class="stocktake-review__actions">
            <!-- The label counts what will actually be written, and says
                 "look at" for the rest, so the trade is visible before the tap
                 rather than discovered after it. -->
            <BaseButton
                variant="primary"
                class="full-width"
                :icon="ICONS.check"
                :label="confirmLabel"
                :loading="busy"
                @click="confirm"
            />
            <div v-if="untickedCount > 0" class="text-caption dora-text-muted-7 text-center q-mt-sm">
                {{ untickedCount }} will join the walk.
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref, watch } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import type { StocktakeSessionItem } from 'src/services/api/stocktakeApiService';

    const props = defineProps<{
        items: StocktakeSessionItem[];
        busy?: boolean;
    }>();

    const emit = defineEmits<{
        /**
         * `checked` get a bulk check written for them; `unchecked` flow into the
         * walk phase. The page owns both actions — it holds the API service and
         * the walk queue, and keeping the calls in one place is what stops this
         * component growing a second opinion about what a check means.
         */
        (e: 'confirm', payload: {
            checked: string[];
            unchecked: StocktakeSessionItem[];
        }): void;
    }>();

    // Pre-ticked, per D-3. Re-seeded if the item list is ever replaced under us
    // (a refetch) so a stale id set can't survive into a new session.
    const ticked = ref<Set<string>>(new Set());
    watch(
        () => props.items,
        (items) => { ticked.value = new Set(items.map((i) => i.stock_item_id)); },
        { immediate: true, deep: false },
    );

    function isTicked(id: string): boolean {
        return ticked.value.has(id);
    }
    function toggle(id: string): void {
        // Reassigned rather than mutated: a Set mutation isn't reactive.
        const next = new Set(ticked.value);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        ticked.value = next;
    }

    const tickedCount = computed(() => ticked.value.size);
    const untickedCount = computed(() => props.items.length - tickedCount.value);

    const BAND_WORD: Record<string, string> = {
        out: 'it\'s out',
        low: 'it\'s low',
        stocked: 'it\'s stocked',
    };
    function bandWord(band: string | null): string {
        if (!band) return 'the level is right';
        return BAND_WORD[band] ?? band;
    }

    const confirmLabel = computed(() => {
        if (tickedCount.value === 0) return 'Check them all myself';
        const noun = tickedCount.value === 1 ? 'item' : 'items';
        return `That's right for ${tickedCount.value} ${noun}`;
    });

    function confirm(): void {
        emit('confirm', {
            checked: [...ticked.value],
            unchecked: props.items.filter((i) => !ticked.value.has(i.stock_item_id)),
        });
    }
</script>

<style scoped lang="scss">
    /* Scrolls inside the runner's dark shell; the list is the only thing that
       moves, so the heading and the action stay put on a long list. */
    .stocktake-review {
        display: flex;
        flex-direction: column;
        max-height: 100%;
        width: 100%;
        max-width: 520px;
        margin: 0 auto;
        padding: 16px;
        gap: var(--space-3);
    }
    .stocktake-review__head {
        text-align: center;
        color: var(--text-inverse);
    }
    .stocktake-review__list {
        flex: 1 1 auto;
        overflow-y: auto;
        background: var(--surface-component);
        color: var(--text-primary);
        border-radius: 12px;
    }
    .stocktake-review__name {
        font-weight: 600;
    }
    /* Belief wording rides the same warning tone it uses on the stock row's
       level picker and the walk card, so "this is Dora talking" is one visual
       idea across the app rather than three. */
    .stocktake-review__believed {
        color: var(--semantic-warning);
    }
    .stocktake-review__reason {
        color: var(--text-secondary);
        white-space: normal;
    }
    .stocktake-review__actions {
        flex: 0 0 auto;
    }
</style>
