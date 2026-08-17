<template>
    <q-card
        bordered
        flat
        class="recipe-card cursor-pointer column no-wrap"
        @click="onCardClick"
    >
        <div v-if="showRecipeImages" class="recipe-card__media" :style="mediaStyle">
            <img
                v-if="recipe.has_image && !imgFailed"
                class="recipe-card__img"
                :src="imageUrl"
                alt=""
                @error="imgFailed = true"
            />
            <span v-else class="recipe-card__initial">{{ initial }}</span>
        </div>

        <q-card-section class="q-pb-xs">
            <div class="text-h6 ellipsis-2-lines">{{ recipe.name }}</div>
        </q-card-section>

        <q-card-section class="q-pt-none q-pb-xs">
            <div class="row q-gutter-xs items-center">
                <q-chip v-if="totalTime !== null" dense :icon="ICONS.schedule">
                    {{ totalTime }}m
                </q-chip>
                <q-chip v-if="recipe.servings" dense :icon="ICONS.restaurant">
                    Serves {{ recipe.servings }}
                </q-chip>
                <q-chip v-if="ingredientCount > 0" dense :icon="ICONS.ingredients">
                    {{ ingredientCount }}
                    {{ ingredientCount === 1 ? 'ingredient' : 'ingredients' }}
                </q-chip>
                <q-chip v-if="recipe.difficulty" dense :icon="ICONS.star_outline">
                    {{ recipe.difficulty }}
                </q-chip>
                <!-- FU-637 — kcal per serving while you're choosing, which is
                     where it's actually useful. A thin complex-mode estimate
                     still shows (hiding it would be its own kind of lie) but
                     says so, rather than passing for a solid figure. -->
                <q-chip
                    v-if="kcal.value !== null"
                    dense
                    :icon="ICONS.monitor_heart"
                    :outline="!kcal.judgeable"
                >
                    {{ Math.round(kcal.value) }} kcal
                    <span v-if="!kcal.judgeable" class="q-ml-xs">(part)</span>
                    <q-tooltip v-if="!kcal.judgeable">
                        Worked out from only part of this recipe — open it to
                        see what's missing.
                    </q-tooltip>
                </q-chip>
                <q-chip
                    v-if="(recipe.section_count ?? 0) > 1"
                    dense
                    outline
                    color="primary"
                    :icon="ICONS.list"
                >
                    {{ recipe.section_count }} parts
                </q-chip>
                <!-- C-waste W4 — surfaced only when the cookbook's
                     "Uses expiring ingredients" filter is active (the
                     parent passes `showExpiringBadge`). Off-filter, the
                     count is meaningless noise; we hide it. -->
                <!-- FU-653 — Dora's belief, as a remark. Outline, not filled:
                     the filled chips on this row state facts about the recipe,
                     and this is an opinion that hasn't changed any of them
                     (the cook button's colour and the cookable badge are
                     deliberately untouched). Server sends it only when the
                     user opted the recipes surface in. -->
                <q-chip
                    v-if="recipe.inference_hint"
                    dense
                    outline
                    :color="recipe.inference_hint === 'at_risk' ? 'warning' : 'positive'"
                    :icon="ICONS.inferred_hunch"
                >
                    {{ recipe.inference_hint === 'at_risk' ? 'May be short' : 'May be cookable' }}
                    <q-tooltip max-width="300px">{{ inferenceTooltip }}</q-tooltip>
                </q-chip>
                <q-chip
                    v-if="showExpiringBadge && (recipe.expiring_ingredient_count ?? 0) > 0"
                    dense
                    color="warning"
                    text-color="white"
                    :icon="ICONS.wasteExpired"
                >
                    Uses {{ recipe.expiring_ingredient_count }} expiring
                </q-chip>
            </div>
        </q-card-section>

        <q-card-section v-if="metaLine" class="q-pt-none q-pb-xs">
            <div class="text-caption dora-text-muted">{{ metaLine }}</div>
        </q-card-section>

        <q-card-section v-if="tagNames.length > 0" class="q-pt-none q-pb-xs">
            <div class="row q-gutter-xs">
                <q-chip
                    v-for="tag in tagNames"
                    :key="tag"
                    outline
                    color="primary"
                    class="recipe-card-tag"
                >
                    {{ tag }}
                </q-chip>
            </div>
        </q-card-section>

        <q-space />
        <q-separator />
        <q-card-actions class="row items-center no-wrap q-px-sm">
            <BaseButton
                variant="icon"
                :icon="recipe.is_favourite ? ICONS.favorite : ICONS.favorite_border"
                :color="recipe.is_favourite ? 'red' : undefined"
                @click.stop="emit('toggle-favourite', recipe.recipe_id)"
            >
                <q-tooltip>
                    {{ recipe.is_favourite ? 'Remove from favourites' : 'Mark favourite' }}
                </q-tooltip>
            </BaseButton>
            <BaseButton
                v-if="showFilterByIngredients"
                variant="icon"
                :icon="ICONS.filter_list"
                @click.stop="emit('filter-by-ingredients', recipe.recipe_id)"
            >
                <q-tooltip>Filter stock to this recipe's ingredients</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="filled-icon"
                :icon="ICONS.chef_hat"
                :color="cookButtonColor"
                @click.stop="emit('cook', recipe.recipe_id)"
            >
                <q-tooltip>{{ cookButtonTooltip }}</q-tooltip>
            </BaseButton>
            <q-space />
            <BaseButton
                variant="icon"
                :icon="cookable === true ? ICONS.add_shopping_cart : ICONS.remove_shopping_cart"
                :color="cookable === false ? 'warning' : undefined"
                :disable="recipe.ingredients.length === 0"
                @click.stop="onAddToList"
            >
                <q-tooltip>{{ addListTooltip }}</q-tooltip>
            </BaseButton>
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useRecipeDisplay } from 'src/composables/useRecipeDisplay';
    import { ref } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            /** C-waste W4 — when true, render the "Uses N expiring"
             *  chip if the recipe carries a positive count. Off by
             *  default; the cookbook flips it on while its filter is
             *  active so the badge stays scoped to that intent. */
            showExpiringBadge?: boolean;
            /** When true, render a "Filter stock to this recipe's
             *  ingredients" action in the card footer. Off by default;
             *  the stock-item detail page flips it on inside its
             *  "Recipes using this" tab so the user can jump from a
             *  recipe back to the rest of its pantry footprint. */
            showFilterByIngredients?: boolean;
        }>(),
        {
            showExpiringBadge: false,
            showFilterByIngredients: false,
        },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'toggle-favourite', recipeId: string): void;
        (e: 'add-missing', recipeId: string, stockItemIds: string[]): void;
        (e: 'add-all-to-list', recipeId: string): void;
        (e: 'filter-by-ingredients', recipeId: string): void;
    }>();

    const imgFailed = ref(false);
    const { showRecipeImages } = useImagePrefs();

    // Everything derived from the recipe for display lives in one place,
    // shared with the compact `RecipeRow` (R-003) — the card decides only
    // how to lay it out.
    const {
        totalTime, ingredientCount, kcal, metaLine, tagNames, missingIds,
        cookable, cookButtonColor, cookButtonTooltip, addListTooltip,
        inferenceTooltip, initial, mediaStyle, imageUrl,
    } = useRecipeDisplay(() => props.recipe);

    function onAddToList() {
        if (cookable.value) {
            emit('add-all-to-list', props.recipe.recipe_id);
        } else {
            emit('add-missing', props.recipe.recipe_id, missingIds.value);
        }
    }

    function onCardClick() {
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
    .recipe-card__media {
        position: relative;
        height: 110px;
        border-radius: 10px 10px 0 0;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .recipe-card__img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .recipe-card__initial {
        font-size: 2.75rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.92);
        user-select: none;
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
