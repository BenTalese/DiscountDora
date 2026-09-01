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
                    <div v-if="ingredientsLoading" class="text-caption dora-text-muted">
                        Calculating…
                    </div>
                    <!-- ONE line, not a display-size number over a caption.
                         The number is also no longer the outstanding half on
                         its own: as a bare figure it read as "what this week
                         needs" while measuring "what you haven't listed yet"
                         (owner: "feels wrong… it's only looking at what's not
                         on a list"). Saying "3 of 5" keeps the week's real
                         total visible and makes the handled half legible in
                         the same breath — which is what the separate
                         "N already on a list" line was for, now deleted.

                         The cook-shortfall line that sat here is gone too: it
                         is already in the week toolbar's status strip, three
                         hundred pixels away and about the same week. -->
                    <div v-else class="mp-shop__headline" :class="headlineClass">
                        {{ headline }}
                    </div>
                </template>
                <div v-else class="text-caption dora-text-muted q-py-sm">
                    No meals planned for this week yet — tap a day's slot, then a recipe.
                </div>
            </q-card-section>

            <!-- The CTA sits above the list and outside the disclosure, so
                 collapsing the rows never hides the action they exist for
                 (owner: "collapsed by default… with the 'add x to list' always
                 visible"). -->
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

        <q-expansion-item
            v-if="focusedPlan && ingredients.length"
            :icon="ICONS.receipt_long"
            :label="`Full ingredient demand (${ingredients.length})`"
            dense
            class="mp-shop__demand q-mt-sm"
        >
            <!-- Same row component as the list above, so hover-to-highlight
                 works here too — it used to be an inert name-and-chip list. -->
            <MealPlanIngredientRow
                v-for="ing in ingredients"
                :key="ing.stock_item_id"
                :ingredient="ing"
                @hover="emit('hoverIngredient', ing)"
                @clear-hover="emit('clearHover')"
            />
        </q-expansion-item>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import MealPlanIngredientRow from 'src/components/MealPlanIngredientRow.vue';
    import { ICONS } from 'src/style/icons';
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

    const headline = computed(() => {
        const need = props.needToBuy.length;
        const left = props.outstanding.length;
        if (need === 0) return 'Fully stocked for this week';
        if (left === 0) return `All ${need} on a list`;
        if (left === need) return `${need} to buy this week`;
        return `${left} of ${need} still to buy this week`;
    });
    const headlineClass = computed(() => (
        props.outstanding.length ? 'text-negative' : 'text-positive'
    ));

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
    /* Both disclosures pull their body padding in so the shared rows sit at
       the card's own gutter rather than Quasar's default indent. */
    .mp-shop :deep(.q-expansion-item__content) {
        padding: 0 var(--space-2) var(--space-2);
    }
</style>
