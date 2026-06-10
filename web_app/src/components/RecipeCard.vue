<template>
    <q-card
        bordered
        flat
        class="recipe-card cursor-pointer column no-wrap"
        @click="onCardClick"
    >
        <!-- Image (FU-039). Falls back to a coloured initial tile when the
             recipe has no image or the fetch fails. Favourite toggle floats. -->
        <div class="recipe-card__media" :style="mediaStyle">
            <!-- C-cross Chunk 5 — gated on the per-user `show_recipe_images`
                 opt-in. When off the `<img>` never mounts, so the bytes
                 endpoint isn't fetched at all (real bandwidth saving). -->
            <img
                v-if="showRecipeImages && recipe.has_image && !imgFailed"
                class="recipe-card__img"
                :src="imageUrl"
                alt=""
                @error="imgFailed = true"
            />
            <span v-else class="recipe-card__initial">{{ initial }}</span>
            <q-btn
                :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                :color="recipe.is_favourite ? 'red' : undefined"
                class="recipe-card__fav"
                :class="recipe.is_favourite ? undefined : 'text-white'"
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

        <q-card-section class="q-pb-xs">
            <div class="text-h6 ellipsis-2-lines">{{ recipe.name }}</div>
            <div v-if="recipe.cuisine_name || recipe.category_name" class="text-caption dora-text-muted">
                <span v-if="recipe.cuisine_name">{{ recipe.cuisine_name }}</span>
                <span v-if="recipe.cuisine_name && recipe.category_name"> · </span>
                <span v-if="recipe.category_name">{{ recipe.category_name }}</span>
            </div>
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
            </div>
        </q-card-section>

        <!-- Dietary tag chips, when tagged. -->
        <q-card-section v-if="tagNames.length > 0" class="q-pt-none q-pb-xs">
            <div class="row q-gutter-xs">
                <q-chip
                    v-for="tag in tagNames"
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

        <q-card-section class="q-pt-none q-pb-xs">
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

        <!-- Meals box: editable cooked-pool stepper + allocated indicator.
             Allocated goes red on a shortfall (committed > available). -->
        <q-card-section class="q-pt-none q-pb-xs">
            <div class="recipe-card__meals row items-center justify-between no-wrap">
                <div class="column">
                    <div class="text-caption dora-text-muted">Meals cooked</div>
                    <MealStepper
                        :available="recipe.available_meals"
                        @adjust="(d) => emit('adjust-meals', recipe.recipe_id, d)"
                    />
                </div>
                <div
                    v-if="recipe.committed_meals > 0"
                    class="recipe-card__allocated column items-center justify-center"
                    :class="shortfall ? 'dora-bg-negative-soft text-negative' : 'dora-bg-sunken dora-text-secondary'"
                >
                    <div class="text-h6 line-height-1">{{ recipe.committed_meals }}</div>
                    <div class="text-caption">allocated</div>
                    <q-tooltip>
                        {{ recipe.committed_meals }} meal(s) committed to upcoming plans;
                        {{ recipe.unallocated_meals }} of your cooked pool still free<span v-if="shortfall">. Short by {{ recipe.committed_meals - recipe.available_meals }} — cook more.</span>
                    </q-tooltip>
                </div>
            </div>
        </q-card-section>

        <q-space />
        <q-separator />
        <q-card-actions align="right">
            <q-btn
                unelevated
                no-caps
                :icon="ICONS.restaurant"
                label="Cook"
                color="primary"
                @click.stop="emit('cook', recipe.recipe_id)"
            />
            <q-btn flat round dense :icon="ICONS.more_vert" @click.stop>
                <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                    <q-list dense style="min-width: 220px">
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
                    </q-list>
                </q-menu>
            </q-btn>
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { storeToRefs } from 'pinia';
    import { computed, ref } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            // When set, these ingredients are excluded from the "others
            // missing" dim check (the card is shown *because* of these
            // items — restocking any of them is the user's goal here).
            highlightStockItemIds?: string[];
        }>(),
        {
            highlightStockItemIds: () => [],
        },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'toggle-favourite', recipeId: string): void;
        (e: 'adjust-meals', recipeId: string, delta: number): void;
        (e: 'add-missing', recipeId: string, stockItemIds: string[]): void;
        (e: 'add-all-to-list', recipeId: string): void;
        (e: 'add-to-meal-plan', recipeId: string): void;
    }>();

    // Image via the recipe image endpoint (when present); falls back to the
    // coloured-initial tile on no-image or load error.
    const imgFailed = ref(false);
    const imageUrl = computed(() => recipeImageUrl(props.recipe.recipe_id));
    // C-cross Chunk 5 — recipe-image render gate.
    const { showRecipeImages } = useImagePrefs();
    const initial = computed(() => (props.recipe.name.trim()[0] ?? '?').toUpperCase());
    const mediaStyle = computed(() => {
        let hash = 0;
        for (const ch of props.recipe.name) hash = (hash * 31 + ch.charCodeAt(0)) % 360;
        return { background: `hsl(${hash}, 45%, 42%)` };
    });

    // Shortfall: more meals committed to upcoming plans than are cooked.
    const shortfall = computed(() => props.recipe.available_meals < props.recipe.committed_meals);

    // Resolve dietary tag ids → names via the shared vocab store. Falls back
    // to empty (no chips) when the store hasn't been loaded on a given page.
    const { dietaryTags } = storeToRefs(useRecipeVocabStore());
    const tagNames = computed(() => {
        const byId = new Map(dietaryTags.value.map((t) => [t.dietary_tag_id, t.name]));
        return (props.recipe.dietary_tag_ids ?? [])
            .map((id) => byId.get(id))
            .filter((n): n is string => Boolean(n));
    });

    // Cookability is server-owned (§3.2): each ingredient carries
    // `is_missing` / `is_low_stock`, and the recipe carries `cookable`.
    // "Missing" = out of stock OR not tracked. We derive the deduped id
    // list locally only because the add-missing emit needs the ids.
    const missingIds = computed(() => [
        ...new Set(
            props.recipe.ingredients
                .filter((i) => i.is_missing)
                .map((i) => i.stock_item_id)
                .filter(Boolean),
        ),
    ]);

    const lowCount = computed(
        () =>
            new Set(
                props.recipe.ingredients
                    .filter((i) => i.is_low_stock)
                    .map((i) => i.stock_item_id)
                    .filter(Boolean),
            ).size,
    );

    const cookableNow = computed(() => props.recipe.cookable);

    const totalTime = computed(() => {
        if (
            props.recipe.prep_time_minutes === null
            && props.recipe.cook_time_minutes === null
        ) {
            return null;
        }
        return (props.recipe.prep_time_minutes ?? 0) + (props.recipe.cook_time_minutes ?? 0);
    });

    // FU-083 — the previous `dim` computed (restocking this item alone
    // wouldn't make the recipe cookable) was removed. It wasn't legible
    // without a legend and the card already shows "missing N ingredients"
    // on its face. `highlightStockItemIds` stays as a prop because the
    // RecipesOverview deep-link from a stock item still passes it; we
    // just no longer use it for visual dimming.

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
    .recipe-card__fav {
        position: absolute;
        top: 4px;
        right: 4px;
        background: rgba(0, 0, 0, 0.28);
    }
    .recipe-card__allocated {
        min-width: 64px;
        padding: 4px 8px;
        border-radius: 8px;
        text-align: center;
    }
    .line-height-1 {
        line-height: 1;
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
