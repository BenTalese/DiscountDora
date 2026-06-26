<template>
    <q-card
        bordered
        flat
        class="recipe-card cursor-pointer column no-wrap"
        @click="onCardClick"
    >
        <div class="recipe-card__media" :style="mediaStyle">
            <img
                v-if="showRecipeImages && recipe.has_image && !imgFailed"
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
                <q-chip v-if="recipe.difficulty" dense :icon="ICONS.star_outline">
                    {{ recipe.difficulty }}
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
            <q-btn
                unelevated
                round
                dense
                :icon="ICONS.chef_hat"
                :color="cookable ? 'primary' : 'warning'"
                @click.stop="emit('cook', recipe.recipe_id)"
            >
                <q-tooltip>
                    {{ cookable ? 'Cook' : `Cook anyway — missing ${missingIds.length} ingredient(s)` }}
                </q-tooltip>
            </q-btn>
            <q-space />
            <BaseButton
                variant="icon"
                :icon="cookable ? ICONS.add_shopping_cart : ICONS.remove_shopping_cart"
                :color="cookable ? undefined : 'warning'"
                :disable="recipe.ingredients.length === 0"
                @click.stop="onAddToList"
            >
                <q-tooltip>
                    {{ cookable
                        ? 'Add ingredients to a list'
                        : `Add ${missingIds.length} missing to a list` }}
                </q-tooltip>
            </BaseButton>
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { storeToRefs } from 'pinia';
    import { computed, ref } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            highlightStockItemIds?: string[];
            /** C-waste W4 — when true, render the "Uses N expiring"
             *  chip if the recipe carries a positive count. Off by
             *  default; the cookbook flips it on while its filter is
             *  active so the badge stays scoped to that intent. */
            showExpiringBadge?: boolean;
        }>(),
        {
            highlightStockItemIds: () => [],
            showExpiringBadge: false,
        },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'toggle-favourite', recipeId: string): void;
        (e: 'add-missing', recipeId: string, stockItemIds: string[]): void;
        (e: 'add-all-to-list', recipeId: string): void;
    }>();

    const imgFailed = ref(false);
    const imageUrl = computed(() => recipeImageUrl(props.recipe.recipe_id));
    const { showRecipeImages } = useImagePrefs();
    const initial = computed(() => (props.recipe.name.trim()[0] ?? '?').toUpperCase());
    const mediaStyle = computed(() => {
        let hash = 0;
        for (const ch of props.recipe.name) hash = (hash * 31 + ch.charCodeAt(0)) % 360;
        return { background: `hsl(${hash}, 45%, 42%)` };
    });

    const { dietaryTags } = storeToRefs(useRecipeVocabStore());
    const tagNames = computed(() => {
        const byId = new Map(dietaryTags.value.map((t) => [t.dietary_tag_id, t.name]));
        return (props.recipe.dietary_tag_ids ?? [])
            .map((id) => byId.get(id))
            .filter((n): n is string => Boolean(n));
    });

    const missingIds = computed(() => [
        ...new Set(
            props.recipe.ingredients
                .filter((i) => i.is_missing)
                .map((i) => i.stock_item_id)
                .filter(Boolean),
        ),
    ]);

    const cookable = computed(() => props.recipe.cookable);

    const totalTime = computed(() => {
        if (
            props.recipe.prep_time_minutes === null
            && props.recipe.cook_time_minutes === null
        ) {
            return null;
        }
        return (props.recipe.prep_time_minutes ?? 0) + (props.recipe.cook_time_minutes ?? 0);
    });

    const metaLine = computed(() => {
        const parts = [
            props.recipe.cuisine_name,
            props.recipe.category_name,
            props.recipe.time_of_day,
        ].filter((p): p is string => Boolean(p));
        return parts.join(' · ');
    });

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
