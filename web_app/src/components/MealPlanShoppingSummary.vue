<template>
    <div>
        <q-card flat bordered>
            <q-card-section class="q-pb-xs">
                <div class="text-subtitle1">This week's shopping</div>
                <template v-if="focusedPlan">
                    <div v-if="ingredientsLoading" class="text-caption dora-text-muted">Calculating…</div>
                    <template v-else>
                        <!-- Owner feedback 2026-08-27 — the headline is what's
                             left to do, not what the week needs. Adding three
                             items to a list used to leave this reading "3"
                             forever. -->
                        <div
                            class="text-h5"
                            :class="outstanding.length ? 'text-negative' : 'text-positive'"
                        >
                            {{ outstanding.length }}
                        </div>
                        <div class="text-caption dora-text-muted">
                            {{ outstandingCaption }}
                        </div>
                        <div v-if="onListCount" class="text-caption dora-text-muted">
                            {{ onListCount }} already on a list
                        </div>
                    </template>
                    <div v-if="batchEnabled && shortfallCount" class="row items-center q-mt-sm text-warning">
                        <q-icon :name="ICONS.chef_hat" class="q-mr-xs" />
                        <span class="text-subtitle2">{{ cookByLabel }}</span>
                    </div>
                </template>
                <div v-else class="text-caption dora-text-muted q-py-sm">
                    No meals planned for this week yet — tap a day's slot, then a recipe.
                </div>
            </q-card-section>

            <!-- Still lists everything the week needs, handled or not: the
                 rail is the "what does this week want" view, and hiding rows
                 the moment they land on a list would make it lie by omission.
                 The per-row caption says which list each one is on. -->
            <q-list v-if="focusedPlan && needToBuy.length" dense separator>
                <q-item
                    v-for="ing in needToBuy"
                    :key="ing.stock_item_id"
                    @mouseenter="emit('hoverIngredient', ing)"
                    @mouseleave="emit('clearHover')"
                >
                    <q-item-section>
                        <q-item-label>{{ ing.stock_item_name }}</q-item-label>
                        <q-item-label caption>
                            <span v-if="ing.total_quantity !== null">
                                needs {{ formatQuantity(ing.total_quantity, ing.unit) }} ·
                            </span>
                            {{ listStatusLabel(ing.stock_item_id) }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row items-center no-wrap q-gutter-xs">
                            <q-chip
                                dense
                                :color="stockStatusColour(ing.stock_item_id) ?? undefined"
                                :text-color="stockStatusColour(ing.stock_item_id) ? 'white' : undefined"
                                :class="{ 'dora-bg-sunken dora-text-secondary': !stockStatusColour(ing.stock_item_id) }"
                            >
                                {{ stockStatusLabel(ing.stock_item_id) }}
                            </q-chip>
                            <AddToListButton variant="row" :stock-item-id="ing.stock_item_id" />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>

            <q-card-actions v-if="focusedPlan">
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
        </q-card>

        <q-expansion-item
            v-if="focusedPlan && ingredients.length"
            :icon="ICONS.receipt_long"
            label="Full ingredient demand"
            class="q-mt-sm"
        >
            <q-list dense separator>
                <q-item v-for="ing in ingredients" :key="ing.stock_item_id">
                    <q-item-section>{{ ing.stock_item_name }}</q-item-section>
                    <q-item-section side>
                        <q-chip
                            dense
                            :color="stockStatusColour(ing.stock_item_id) ?? undefined"
                            :text-color="stockStatusColour(ing.stock_item_id) ? 'white' : undefined"
                            :class="{ 'dora-bg-sunken dora-text-secondary': !stockStatusColour(ing.stock_item_id) }"
                        >
                            {{ stockStatusLabel(ing.stock_item_id) }}
                        </q-chip>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-expansion-item>
    </div>
</template>

<script lang="ts" setup>
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import type { MealPlan, MealPlanIngredient } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const { batchEnabled } = useBatchEnabled();

    const props = defineProps<{
        focusedPlan: MealPlan | null;
        ingredientsLoading: boolean;
        ingredients: MealPlanIngredient[];
        /** Everything the week needs that isn't in the pantry. */
        needToBuy: MealPlanIngredient[];
        /** …of those, the ones not yet on any open list. */
        outstanding: MealPlanIngredient[];
        shortfallCount: number;
        cookByLabel: string;
        generating: boolean;
        listStatusLabel: (stockItemId: string) => string;
        stockStatusLabel: (stockItemId: string) => string;
        stockStatusColour: (stockItemId: string) => string | null;
    }>();

    const emit = defineEmits<{
        (e: 'addToList'): void;
        (e: 'hoverIngredient', ing: MealPlanIngredient): void;
        (e: 'clearHover'): void;
    }>();

    const onListCount = computed(
        () => props.needToBuy.length - props.outstanding.length,
    );
    const outstandingCaption = computed(() => {
        if (props.outstanding.length) return "item(s) you'll need to buy";
        return onListCount.value > 0
            ? 'left to buy — the rest are on a list'
            : 'fully stocked for this week';
    });
    // Names the button by what's actually left, the way the recipe page's
    // "Add N missing" button does.
    const addToListLabel = computed(() => (
        props.outstanding.length > 0
            ? `Add ${props.outstanding.length} to a list`
            : 'Add to a list'
    ));
</script>
