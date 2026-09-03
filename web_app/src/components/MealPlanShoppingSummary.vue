<template>
    <div class="mp-shop">
        <q-card flat bordered>
            <q-card-section class="q-pb-sm">
                <!-- Owner feedback 2026-09-01 — the heading takes an icon, so
                     it reads as a titled section rather than a bare line of
                     bold text beside the icon-led "Full ingredient demand"
                     expansion below it. -->
                <div class="mp-shop__heading">
                    <q-icon :name="ICONS.shopping_cart" size="18px" />
                    <span class="text-subtitle1">This week's shopping</span>
                </div>

                <template v-if="focusedPlan">
                    <!-- Owner feedback 2026-09-03 — *"don't like how the 'x of
                         x still to buy' text flashes to Calculating. Just
                         transition smoothly between x of x."* The recalculation
                         after a plan edit is fast, so swapping the answer for
                         the word "Calculating…" was a flicker rather than
                         information. The lines below stay on the last answer
                         while a new one is on its way — only a first load with
                         nothing to show yet says so. -->
                    <div v-if="showFirstLoad" class="text-caption dora-text-muted">
                        Calculating…
                    </div>
                    <!-- Owner feedback 2026-09-03 — one red sentence became two
                         level-led lines: *"replace with two lines, one starting
                         with a red stock-level indicator dot followed by the
                         number of ingredients not on a list that are out of
                         stock… the 'of X' number should be the total of THAT
                         level missing, not the total missing."* Which is the
                         honest split — "3 of 8" mixed two different jobs (buy
                         the things you have none of; top up the things running
                         low) — and the dot is the same signal every other stock
                         surface in the app uses for them. -->
                    <div
                        v-else-if="levelLines.length"
                        class="mp-shop__lines"
                        :class="{ 'mp-shop__lines--stale': ingredientsLoading }"
                    >
                        <div
                            v-for="line in levelLines"
                            :key="line.key"
                            class="mp-shop__line"
                        >
                            <StockLevelDot
                                :sequence="line.sequence"
                                size="10px"
                                dot-class="mp-shop__dot"
                            />
                            <span :class="line.textClass">{{ line.text }}</span>
                            <q-tooltip>{{ line.tooltip }}</q-tooltip>
                        </div>
                    </div>
                    <div v-else class="mp-shop__headline text-positive">
                        Fully stocked for this week
                    </div>
                </template>
                <div v-else class="text-caption dora-text-muted q-py-sm">
                    No meals planned for this week yet — tap a day's slot, then a recipe.
                </div>
            </q-card-section>

            <!-- The CTA sits above the list and outside the disclosure, so
                 collapsing the rows never hides the action they exist for
                 (owner: "collapsed by default… with the 'add x to list'
                 always visible"). -->
            <q-card-actions v-if="focusedPlan" class="q-pt-none">
                <!-- Owner feedback 2026-08-27 — was "Generate shopping list for
                     this week", which swept the week server-side and dropped
                     you on a new list with no say in it. Now it opens the same
                     picker the recipe page opens (R-001). Still enabled when
                     everything is already handled, because the picker is also
                     how you deliberately add a second line or an optional
                     ingredient. -->
                <BaseButton
                    class="full-width"
                    :icon="ICONS.add_shopping_cart"
                    :label="addToListLabel"
                    :loading="generating"
                    :disable="needToBuy.length === 0"
                    @click="emit('addToList')"
                />
            </q-card-actions>

            <!-- Still lists everything the week needs, handled or not: the
                 rail is the "what does this week want" view, and hiding rows
                 the moment they land on a list would make it lie by omission.
                 Each row's cart button says which of the two it is. -->
            <q-expansion-item
                v-if="focusedPlan && needToBuy.length"
                :label="`What's needed (${needToBuy.length})`"
                dense
                class="mp-shop__rows"
            >
                <MealPlanIngredientRow
                    v-for="ing in needToBuy"
                    :key="ing.stock_item_id"
                    :ingredient="ing"
                    @hover="emit('hoverIngredient', ing)"
                    @clear-hover="emit('clearHover')"
                />
            </q-expansion-item>
        </q-card>

        <!-- Owner feedback 2026-09-03 — *"full ingredient demand could be
             designed a bit better (the text of it is wrapped and seems to have
             no margin around the text)"*. Both were true, and both came from
             wearing Quasar's raw expansion header in a 300px rail: the header
             is a `q-item` whose label had no room beside a leading icon and a
             chevron, so "Full ingredient demand (24)" wrapped hard against the
             card edge. It now sits in the same bordered card language as its
             neighbour, the count moves out of the label into its own badge (so
             the label is short enough not to wrap), and the header keeps the
             card's own gutter. -->
        <q-card
            v-if="focusedPlan && ingredients.length"
            flat bordered
            class="mp-shop__demand q-mt-sm"
        >
            <q-expansion-item dense>
                <template #header>
                    <q-item-section avatar class="mp-shop__demand-avatar">
                        <q-icon :name="ICONS.receipt_long" size="18px" />
                    </q-item-section>
                    <!-- "Full ingredient demand" wrapped to two lines even after
                         the count moved out of the label — measured live at the
                         rail's 300px. Three words was one too many for the
                         space between an avatar and a chevron, and the fix for
                         "the text of it is wrapped" is fewer words, not a
                         smaller font: "All ingredients" is what the disclosure
                         actually holds (this week's demand INCLUDING what you
                         already have, as against "What's needed" above it). -->
                    <q-item-section class="mp-shop__demand-label">
                        All ingredients
                    </q-item-section>
                    <q-item-section side>
                        <span class="mp-shop__demand-count">{{ ingredients.length }}</span>
                    </q-item-section>
                </template>
                <!-- Same row component as the list above, so hover-to-highlight
                     works here too — it used to be an inert name-and-chip
                     list. -->
                <MealPlanIngredientRow
                    v-for="ing in ingredients"
                    :key="ing.stock_item_id"
                    :ingredient="ing"
                    @hover="emit('hoverIngredient', ing)"
                    @clear-hover="emit('clearHover')"
                />
            </q-expansion-item>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import MealPlanIngredientRow from 'src/components/MealPlanIngredientRow.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import { ICONS } from 'src/style/icons';
    import { LOW_STOCK_SEQUENCE, OUT_OF_STOCK_SEQUENCE } from 'src/helpers/stockStatus';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type { MealPlan, MealPlanIngredient } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const props = defineProps<{
        focusedPlan: MealPlan | null;
        ingredientsLoading: boolean;
        ingredients: MealPlanIngredient[];
        /** Everything the week needs that isn't in the pantry. */
        needToBuy: MealPlanIngredient[];
        /** …of those, the ones not yet on any open list. */
        outstanding: MealPlanIngredient[];
        generating: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'addToList'): void;
        (e: 'hoverIngredient', ing: MealPlanIngredient): void;
        (e: 'clearHover'): void;
    }>();

    // R-003 — the level split reads the app-wide stock composable, the same
    // authority the rows' own dots use, so a row's colour and the count above
    // it cannot disagree.
    const { isMissing, isLowStock } = useStockStatus();

    /** Only the very first calculation may say "Calculating…" — after that
     *  there is a previous answer worth keeping on screen. */
    const showFirstLoad = computed(
        () => props.ingredientsLoading && props.ingredients.length === 0,
    );

    type LevelLine = {
        key: string;
        sequence: number;
        text: string;
        textClass: string;
        tooltip: string;
    };

    function countAtLevel(
        rows: MealPlanIngredient[], atLevel: (id: string) => boolean,
    ): number {
        return rows.filter((row) => atLevel(row.stock_item_id)).length;
    }

    const levelLines = computed<LevelLine[]>(() => {
        const bands: {
            key: string; sequence: number; textClass: string; noun: string;
            atLevel: (id: string) => boolean;
        }[] = [
            {
                key: 'out',
                sequence: OUT_OF_STOCK_SEQUENCE,
                textClass: 'text-negative',
                noun: 'out of stock',
                atLevel: isMissing,
            },
            {
                key: 'low',
                sequence: LOW_STOCK_SEQUENCE,
                textClass: 'text-warning',
                noun: 'running low',
                atLevel: isLowStock,
            },
        ];
        return bands.flatMap((band) => {
            const total = countAtLevel(props.needToBuy, band.atLevel);
            if (total === 0) return [];
            const left = countAtLevel(props.outstanding, band.atLevel);
            // A level with nothing left to do still earns its line: the week's
            // demand at that level is a fact, and dropping the line would make
            // the remaining one look like the whole story.
            return [{
                key: band.key,
                sequence: band.sequence,
                text: left > 0 ? `${left} of ${total} to buy` : `all ${total} on a list`,
                textClass: left > 0 ? band.textClass : 'dora-text-muted',
                tooltip: left > 0
                    ? `${left} of the ${total} ingredient${total === 1 ? '' : 's'} `
                        + `this week needs that ${total === 1 ? 'is' : 'are'} ${band.noun} `
                        + 'are not on a shopping list yet.'
                    : `All ${total} ${band.noun} ingredient${total === 1 ? '' : 's'} `
                        + 'this week needs are on a list.',
            }];
        });
    });

    // Names the button by what's actually left, the way the recipe page's
    // "Add N missing" button does.
    const addToListLabel = computed(() => (
        props.outstanding.length > 0
            ? `Add ${props.outstanding.length} to a list`
            : 'Add to a list'
    ));
</script>

<style scoped>
    .mp-shop__heading {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        color: var(--text-primary);
        margin-bottom: var(--space-1);
    }
    /* One line at body weight — the figure it replaced was `text-h5`, which
       made a sidebar count the loudest thing on the page. */
    .mp-shop__headline {
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
    }
    .mp-shop__lines {
        display: flex;
        flex-direction: column;
        gap: 2px;
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
        transition: opacity var(--motion-fast) var(--motion-ease);
    }
    /* Mid-recalculation the previous answer stays, very slightly dimmed — the
       one honest way to say "this is a moment out of date" without a flicker. */
    .mp-shop__lines--stale {
        opacity: 0.6;
    }
    .mp-shop__line {
        display: flex;
        align-items: center;
        gap: var(--space-2);
    }
    .mp-shop__dot {
        flex: 0 0 auto;
    }
    /* Both disclosures pull their body padding in so the shared rows sit at
       the card's own gutter rather than Quasar's default indent. */
    .mp-shop :deep(.q-expansion-item__content) {
        padding: 0 var(--space-2) var(--space-2);
    }
    /* The demand header wears the card's gutter, and its label is free to use
       the full width because the count sits in its own side section. */
    .mp-shop__demand :deep(.q-item) {
        padding-left: var(--space-2);
        padding-right: var(--space-2);
    }
    .mp-shop__demand-avatar {
        min-width: 0;
        padding-right: var(--space-2);
    }
    .mp-shop__demand-label {
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 500;
        line-height: 1.3;
    }
    .mp-shop__demand-count {
        font-size: calc(var(--font-size-sm) * 1rem);
        font-variant-numeric: tabular-nums;
        color: var(--text-secondary);
        background: var(--surface-sunken);
        border-radius: var(--radius-pill);
        padding: 1px var(--space-2);
    }
</style>
