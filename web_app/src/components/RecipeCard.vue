<template>
    <q-card
        bordered
        flat
        class="recipe-card cursor-pointer"
        :class="{ 'recipe-card--dim': dim }"
        @click="emit('open', recipe.recipe_id)"
    >
        <q-card-section class="q-pb-xs">
            <div class="row items-start no-wrap">
                <q-icon name="menu_book" size="20px" class="q-mr-sm q-mt-xs" />
                <div class="col">
                    <div class="text-subtitle2 ellipsis-2-lines">{{ recipe.name }}</div>
                    <div class="text-caption text-grey">
                        <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
                        <span v-if="recipe.cook_time_minutes"> · {{ recipe.cook_time_minutes }}m</span>
                    </div>
                </div>
            </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
            <q-chip
                v-if="cookableNow"
                dense
                color="positive"
                text-color="white"
                icon="check_circle"
            >
                Cookable now
            </q-chip>
            <q-chip
                v-else
                dense
                clickable
                color="orange-9"
                text-color="white"
                icon="remove_shopping_cart"
                @click.stop="emit('add-missing', missingIds)"
            >
                Missing {{ missingIds.length }}
                <q-tooltip>Add missing ingredients to a list</q-tooltip>
            </q-chip>
        </q-card-section>

        <q-separator />
        <q-card-actions align="right">
            <q-btn flat dense no-caps icon="restaurant" label="Cook" @click.stop="emit('cook', recipe.recipe_id)" />
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import type { Recipe } from 'src/models/recipe';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            // When set, this ingredient is excluded from the "others missing"
            // dim check (the card is being shown *because* of this item).
            highlightStockItemId?: string;
        }>(),
        { highlightStockItemId: '' },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'add-missing', stockItemIds: string[]): void;
    }>();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    // An ingredient is "missing" when its stock item is out of stock or not
    // tracked at all.
    function isMissing(stockItemId: string): boolean {
        const item = stockItems.value.find((si) => si.stock_item_id === stockItemId);
        if (!item) return true;
        const level = stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id);
        return level?.name === 'Out of Stock';
    }

    const missingIds = computed(() =>
        [...new Set(props.recipe.ingredients.map((i) => i.stock_item_id))].filter(isMissing),
    );
    const cookableNow = computed(() => missingIds.value.length === 0);

    // Dim when ingredients *other than* the highlighted one are also missing,
    // i.e. restocking this item alone wouldn't make the recipe cookable.
    const dim = computed(
        () => missingIds.value.filter((id) => id !== props.highlightStockItemId).length > 0,
    );
</script>

<style scoped>
    .recipe-card {
        transition: box-shadow 0.15s ease;
    }
    .recipe-card:hover {
        box-shadow: 0 6px 18px -14px rgba(0, 0, 0, 0.4);
    }
    .recipe-card--dim {
        opacity: 0.55;
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
