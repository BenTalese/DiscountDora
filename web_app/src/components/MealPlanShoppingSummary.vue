<template>
    <div class="mp-shop">
        <!-- Owner feedback 2026-09-05 — *"rename 'this week's shopping' to
             'missing this week' and put that text in place of the 'what's
             needed (X)'… same size as the all ingredients text… put the
             shopping cart there to match the look."* So the card's own title
             row is gone: its words, its icon and its job all moved down onto
             the disclosure header, which is now the only heading here. The
             card had been announcing a section whose contents already
             announced themselves. -->
        <MealPlanRailDisclosure
            v-if="focusedPlan && needToBuy.length"
            :icon="ICONS.shopping_cart"
            label="Missing this week"
            :class="{ 'mp-shop--stale': ingredientsLoading }"
        >
            <!-- Owner feedback 2026-09-05 — the two level LINES became two
                 circles on the header row. They previously sat above the CTA
                 as "2 of 3 to buy" per level with a tooltip each; the owner
                 deleted the tooltips ("useless") and asked for the counts to
                 read as badges beside the chevron. The number is the week's
                 demand at that level — what's *missing* — which is what the
                 heading beside it now says. How much of it is still yours to
                 do is the CTA's job, one row below. -->
            <template #badges>
                <MealPlanRailCount
                    v-for="band in levelBadges"
                    :key="band.key"
                    :count="band.count"
                    :sequence="band.sequence"
                    :label="band.label"
                />
            </template>

            <!-- The CTA sits above the rows and outside the disclosure, so
                 collapsing them never hides the action they exist for (owner:
                 "collapsed by default… with the 'add x to list' always
                 visible", restated 2026-09-05 as "below the row that is icon,
                 text, circles, chevron, but above the low/out list"). -->
            <template #actions>
                <!-- Owner feedback 2026-08-27 — was "Generate shopping list for
                     this week", which swept the week server-side and dropped
                     you on a new list with no say in it. Now it opens the same
                     picker the recipe page opens (R-001). -->
                <BaseButton
                    class="full-width"
                    :icon="ICONS.add_shopping_cart"
                    :label="addToListLabel"
                    :loading="generating"
                    @click="emit('addToList')"
                />
            </template>

            <!-- Still lists everything the week needs, handled or not: the
                 rail is the "what does this week want" view, and hiding rows
                 the moment they land on a list would make it lie by omission.
                 Each row's cart button says which of the two it is. -->
            <MealPlanIngredientRow
                v-for="ing in needToBuy"
                :key="ing.stock_item_id"
                :ingredient="ing"
                @hover="emit('hoverIngredient', ing)"
                @clear-hover="emit('clearHover')"
            />
        </MealPlanRailDisclosure>

        <!-- Nothing to disclose — the three states that have no rows behind
             them keep the bordered card they always had, so the rail doesn't
             collapse to bare text when the week is handled. -->
        <q-card v-else flat bordered>
            <q-card-section class="mp-shop__note">
                <template v-if="!focusedPlan">
                    <span class="text-caption dora-text-muted">
                        No meals planned for this week yet — tap a day's slot, then a recipe.
                    </span>
                </template>
                <!-- Owner feedback 2026-09-03 — *"don't like how the 'x of x
                     still to buy' text flashes to Calculating."* Only a first
                     load with nothing to show yet says so; after that the
                     previous answer stays put, dimmed. -->
                <template v-else-if="showFirstLoad">
                    <span class="text-caption dora-text-muted">Calculating…</span>
                </template>
                <template v-else>
                    <q-icon :name="ICONS.shopping_cart" size="18px" class="text-positive" />
                    <span class="mp-shop__headline text-positive">
                        Fully stocked for this week
                    </span>
                </template>
            </q-card-section>
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
             card's own gutter. Owner 2026-09-05 asked for that header to sit
             thicker; it is now the shared `MealPlanRailDisclosure`, which is
             also what the card above it wears — same shape by construction
             rather than by two stylesheets agreeing.

             "Full ingredient demand" wrapped to two lines even after the count
             moved out of the label — measured live at the rail's 300px. Three
             words was one too many for the space between an avatar and a
             chevron, and the fix is fewer words: "All ingredients" is what the
             disclosure actually holds (this week's demand INCLUDING what you
             already have, as against "Missing this week" above it). -->
        <MealPlanRailDisclosure
            v-if="focusedPlan && ingredients.length"
            :icon="ICONS.receipt_long"
            label="All ingredients"
            class="q-mt-sm"
        >
            <template #badges>
                <MealPlanRailCount
                    :count="ingredients.length"
                    :label="`${ingredients.length} ingredients this week`"
                />
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
        </MealPlanRailDisclosure>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import MealPlanIngredientRow from 'src/components/MealPlanIngredientRow.vue';
    import MealPlanRailCount from 'src/components/MealPlanRailCount.vue';
    import MealPlanRailDisclosure from 'src/components/MealPlanRailDisclosure.vue';
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

    type LevelBadge = {
        key: string;
        sequence: number;
        count: number;
        label: string;
    };

    function countAtLevel(
        rows: MealPlanIngredient[], atLevel: (id: string) => boolean,
    ): number {
        return rows.filter((row) => atLevel(row.stock_item_id)).length;
    }

    const levelBadges = computed<LevelBadge[]>(() => {
        const bands: {
            key: string; sequence: number; noun: string;
            atLevel: (id: string) => boolean;
        }[] = [
            {
                key: 'out',
                sequence: OUT_OF_STOCK_SEQUENCE,
                noun: 'out of stock',
                atLevel: isMissing,
            },
            {
                key: 'low',
                sequence: LOW_STOCK_SEQUENCE,
                noun: 'running low',
                atLevel: isLowStock,
            },
        ];
        return bands.flatMap((band) => {
            const total = countAtLevel(props.needToBuy, band.atLevel);
            if (total === 0) return [];
            const left = countAtLevel(props.outstanding, band.atLevel);
            // The badge counts the week's demand at that level; the CTA below
            // counts what's still yours to do. The accessible name carries
            // both, because the digit alone can't say which of the two it is.
            return [{
                key: band.key,
                sequence: band.sequence,
                count: total,
                label: left > 0
                    ? `${total} ${band.noun}, ${left} not on a list yet`
                    : `${total} ${band.noun}, all on a list`,
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
    .mp-shop__note {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2);
        min-height: 44px;
    }
    /* One line at body weight — the figure it replaced was `text-h5`, which
       made a sidebar count the loudest thing on the page. */
    .mp-shop__headline {
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
    }
    /* Mid-recalculation the previous answer stays, very slightly dimmed — the
       one honest way to say "this is a moment out of date" without a flicker.
       It dims the whole card now that the counts live on its header. */
    .mp-shop--stale {
        opacity: 0.6;
        transition: opacity var(--motion-fast) var(--motion-ease);
    }
</style>
