<template>
    <q-card
        bordered
        flat
        class="recipe-card cursor-pointer"
        :class="{
            'recipe-card--dim': dim,
            'recipe-card--selected': selected,
            'recipe-card--selectable': selectable,
        }"
        @click="onCardClick"
    >
        <q-card-section class="q-pb-xs">
            <div class="row items-start no-wrap q-gutter-xs">
                <q-checkbox
                    v-if="selectable"
                    :model-value="selected"
                    dense
                    class="q-mr-xs"
                    @click.stop
                    @update:model-value="emit('toggle-select', recipe.recipe_id)"
                />
                <q-icon v-else :name="ICONS.menu_book" size="20px" class="q-mr-xs q-mt-xs" />
                <div class="col">
                    <div class="text-subtitle1 ellipsis-2-lines">
                        {{ recipe.name }}
                    </div>
                    <div class="text-caption dora-text-muted">
                        <span v-if="recipe.cuisine">{{ recipe.cuisine }}</span>
                        <span v-if="recipe.cuisine && recipe.category"> · </span>
                        <span v-if="recipe.category">{{ recipe.category }}</span>
                    </div>
                </div>
                <q-btn
                    :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                    :color="recipe.is_favourite ? 'red' : undefined"
                    :class="recipe.is_favourite ? undefined : 'dora-text-muted'"
                    flat
                    round
                    dense
                    size="sm"
                    @click.stop="emit('toggle-favourite', recipe.recipe_id)"
                >
                    <q-tooltip>
                        {{ recipe.is_favourite ? 'Remove from favourites' : 'Mark favourite' }}
                    </q-tooltip>
                </q-btn>
            </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
            <div class="row q-gutter-xs items-center">
                <q-chip v-if="totalTime !== null" dense :icon="ICONS.schedule">
                    {{ totalTime }}m
                </q-chip>
                <q-chip v-if="recipe.servings" dense :icon="ICONS.restaurant">
                    Serves {{ recipe.servings }}
                </q-chip>
                <q-chip v-if="recipe.difficulty" dense :icon="ICONS.star_outline">
                    {{ recipe.difficulty }}
                </q-chip>
                <q-chip
                    v-if="recipe.available_meals > 0"
                    dense
                    :icon="ICONS.inventory"
                    :color="recipe.unallocated_meals > 0 ? 'positive' : undefined"
                    :text-color="recipe.unallocated_meals > 0 ? 'white' : undefined"
                    :class="recipe.unallocated_meals > 0 ? undefined : 'dora-bg-sunken dora-text-secondary'"
                >
                    {{ recipe.available_meals }}
                    <span class="q-ml-xs text-caption">
                        ({{ recipe.unallocated_meals }} free)
                    </span>
                    <q-tooltip>
                        {{ recipe.available_meals }} cooked,
                        {{ recipe.unallocated_meals }} not yet on a plan
                    </q-tooltip>
                </q-chip>
            </div>
        </q-card-section>

        <!-- P2-08 — dietary tag chips. Render only when the recipe is
             tagged; muted styling so they sit alongside the time /
             serves / difficulty chips without competing visually. -->
        <q-card-section
            v-if="recipe.tags && recipe.tags.length > 0"
            class="q-pt-none"
        >
            <div class="row q-gutter-xs">
                <q-chip
                    v-for="tag in recipe.tags"
                    :key="tag"
                    dense
                    outline
                    color="primary"
                    size="sm"
                    class="recipe-card-tag"
                >
                    {{ tag }}
                </q-chip>
            </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
            <q-chip
                v-if="cookableNow"
                dense
                color="positive"
                text-color="white"
                :icon="ICONS.check_circle"
            >
                Cookable now
            </q-chip>
            <q-chip
                v-else
                dense
                clickable
                color="warning"
                text-color="white"
                :icon="ICONS.remove_shopping_cart"
                @click.stop="emit('add-missing', recipe.recipe_id, missingIds)"
            >
                Missing {{ missingIds.length }}
                <q-tooltip>Add missing ingredients to a list</q-tooltip>
            </q-chip>
            <q-chip
                v-if="lowCount > 0"
                dense
                outline
                color="warning"
                :icon="ICONS.warning"
                class="q-ml-xs"
            >
                {{ lowCount }} low
            </q-chip>
        </q-card-section>

        <q-separator />
        <q-card-actions align="right">
            <q-btn
                flat
                dense
                no-caps
                :icon="ICONS.restaurant"
                label="Cook"
                color="primary"
                @click.stop="emit('cook', recipe.recipe_id)"
            />
            <q-btn flat round dense :icon="ICONS.more_vert" @click.stop>
                <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                    <q-list dense style="min-width: 220px">
                        <q-item clickable @click="emit('edit', recipe.recipe_id)">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.edit" />
                            </q-item-section>
                            <q-item-section>Edit</q-item-section>
                        </q-item>
                        <q-item clickable @click="emit('duplicate', recipe.recipe_id)">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.content_copy" />
                            </q-item-section>
                            <q-item-section>Duplicate</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item
                            clickable
                            :disable="recipe.ingredients.length === 0"
                            @click="emit('add-all-to-list', recipe.recipe_id)"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.add_shopping_cart" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Add all ingredients to a list</q-item-label>
                                <q-item-label
                                    v-if="recipe.ingredients.length === 0"
                                    caption
                                >
                                    No ingredients
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item
                            clickable
                            @click="emit('add-to-meal-plan', recipe.recipe_id)"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.event_note" />
                            </q-item-section>
                            <q-item-section>Add to a meal plan…</q-item-section>
                        </q-item>
                        <q-separator />
                        <q-item clickable @click="emit('delete', recipe.recipe_id)">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.delete" color="negative" />
                            </q-item-section>
                            <q-item-section class="text-negative">
                                Delete recipe
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
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
            // Comparison-mode plumbing: when `selectable` is true, the card
            // shows a checkbox instead of the book icon and clicks toggle
            // selection rather than emitting `open`.
            selectable?: boolean;
            selected?: boolean;
        }>(),
        {
            highlightStockItemId: '',
            selectable: false,
            selected: false,
        },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'edit', recipeId: string): void;
        (e: 'duplicate', recipeId: string): void;
        (e: 'delete', recipeId: string): void;
        (e: 'toggle-favourite', recipeId: string): void;
        (e: 'toggle-select', recipeId: string): void;
        (e: 'add-missing', recipeId: string, stockItemIds: string[]): void;
        (e: 'add-all-to-list', recipeId: string): void;
        (e: 'add-to-meal-plan', recipeId: string): void;
    }>();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    function levelNameFor(stockItemId: string): string | null {
        const item = stockItems.value.find((si) => si.stock_item_id === stockItemId);
        if (!item) return null;
        return (
            stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)?.name
                ?? null
        );
    }

    // "Missing" — out of stock OR not tracked. Matches what the spec calls
    // the "missing N" chip and what cook mode treats as unavailable.
    function isMissing(stockItemId: string): boolean {
        const name = levelNameFor(stockItemId);
        return name === null || name === 'Out of Stock';
    }

    const missingIds = computed(() =>
        [...new Set(props.recipe.ingredients.map((i) => i.stock_item_id))]
            .filter((id) => Boolean(id) && isMissing(id)),
    );

    const lowCount = computed(
        () =>
            new Set(
                props.recipe.ingredients
                    .map((i) => i.stock_item_id)
                    .filter((id) => Boolean(id) && levelNameFor(id) === 'Low Stock'),
            ).size,
    );

    const cookableNow = computed(() => missingIds.value.length === 0);

    const totalTime = computed(() => {
        if (
            props.recipe.prep_time_minutes === null
            && props.recipe.cook_time_minutes === null
        ) {
            return null;
        }
        return (props.recipe.prep_time_minutes ?? 0) + (props.recipe.cook_time_minutes ?? 0);
    });

    // Dim when ingredients *other than* the highlighted one are also missing,
    // i.e. restocking this item alone wouldn't make the recipe cookable.
    const dim = computed(
        () =>
            missingIds.value.filter((id) => id !== props.highlightStockItemId).length > 0
            && props.highlightStockItemId !== '',
    );

    function onCardClick() {
        if (props.selectable) {
            emit('toggle-select', props.recipe.recipe_id);
            return;
        }
        emit('open', props.recipe.recipe_id);
    }
</script>

<style scoped>
    .recipe-card {
        transition: box-shadow var(--motion-fast) var(--motion-ease),
            outline-color var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease);
        outline: 2px solid transparent;
        outline-offset: -2px;
        height: 100%;
    }
    .recipe-card:hover {
        box-shadow: var(--elevation-card-hover);
        transform: translateY(-1px);
    }
    .recipe-card--dim {
        opacity: 0.55;
    }
    .recipe-card--selectable {
        cursor: pointer;
    }
    .recipe-card--selected {
        outline-color: var(--q-primary);
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
