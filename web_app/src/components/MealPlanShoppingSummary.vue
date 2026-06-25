<template>
    <div>
        <q-card flat bordered>
            <q-card-section class="q-pb-xs">
                <div class="text-subtitle1">This week's shopping</div>
                <template v-if="focusedPlan">
                    <div v-if="ingredientsLoading" class="text-caption dora-text-muted">Calculating…</div>
                    <div v-else class="text-h5" :class="needToBuy.length ? 'text-negative' : 'text-positive'">
                        {{ needToBuy.length }}
                    </div>
                    <div class="text-caption dora-text-muted">
                        {{ needToBuy.length ? "item(s) you'll need to buy" : 'fully stocked for this week' }}
                    </div>
                    <div v-if="batchEnabled && shortfallCount" class="row items-center q-mt-sm text-warning">
                        <q-icon :name="ICONS.chef_hat" class="q-mr-xs" />
                        <span class="text-subtitle2">{{ cookByLabel }}</span>
                    </div>
                </template>
                <div v-else class="text-caption dora-text-muted q-py-sm">
                    No meals planned for this week yet — tap a day's slot, then a recipe.
                </div>
            </q-card-section>

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
                                needs {{ ing.total_quantity }} {{ ing.unit ?? '' }} ·
                            </span>
                            {{ listStatusLabel(ing.stock_item_id) }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row items-center no-wrap q-gutter-xs">
                            <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
                                {{ stockStatusLabel(ing.stock_item_id) }}
                            </q-chip>
                            <AddToListButton variant="row" :stock-item-id="ing.stock_item_id" />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>

            <q-card-actions v-if="focusedPlan">
                <q-btn
                    color="primary"
                    no-caps
                    class="full-width"
                    :icon="ICONS.shopping_cart"
                    label="Generate shopping list for this week"
                    :loading="generating"
                    :disable="needToBuy.length === 0"
                    @click="emit('generateList')"
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
                        <q-chip dense :color="stockStatusColour(ing.stock_item_id)" text-color="white">
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
    import { ICONS } from 'src/style/icons';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import type { MealPlan, MealPlanIngredient } from 'src/models/mealPlan';

    const { batchEnabled } = useBatchEnabled();

    defineProps<{
        focusedPlan: MealPlan | null;
        ingredientsLoading: boolean;
        ingredients: MealPlanIngredient[];
        needToBuy: MealPlanIngredient[];
        shortfallCount: number;
        cookByLabel: string;
        generating: boolean;
        listStatusLabel: (stockItemId: string) => string;
        stockStatusLabel: (stockItemId: string) => string;
        stockStatusColour: (stockItemId: string) => string;
    }>();

    const emit = defineEmits<{
        (e: 'generateList'): void;
        (e: 'hoverIngredient', ing: MealPlanIngredient): void;
        (e: 'clearHover'): void;
    }>();
</script>
