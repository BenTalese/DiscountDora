<template>
    <!--
        Compact cookbook row — one line per recipe, the Stock Overview
        shape (2026-08-17 feedback). Same data and the same actions as
        `RecipeCard`; only the layout differs, and every derived figure
        comes from the shared `useRecipeDisplay` so the two views can't
        drift (R-003).

        Left → right:
          [thumb?]  Name · meta  ·[chips]·  · · ·  [♥] [👨‍🍳] [🛒]
        Chrome mirrors `StockItemRow`: bordered flat card, 8px radius,
        accent-tinted hover, no lift.
    -->
    <q-card
        bordered
        flat
        class="recipe-row cursor-pointer"
        @click="emit('open', recipe.recipe_id)"
    >
        <q-card-section class="row items-center no-wrap recipe-row__body">
            <!-- No thumbnail, by definition. Owner call 2026-08-18 merged the
                 separate "show/hide photos" toggle into the cards/compact
                 switch: compact IS the without-photos shape, so the row no
                 longer consults `show_recipe_images` (nor renders an initial
                 tile in its place — that was the photo slot's stand-in). -->

            <div class="recipe-row__name-zone column items-start justify-center">
                <div class="recipe-row__name">{{ recipe.name }}</div>
                <div v-if="metaLine" class="recipe-row__meta">{{ metaLine }}</div>
            </div>

            <!-- Figures. On phones only the two that change a decision
                 survive (time, and the belief/expiring flags) — the rest
                 would take width the row hasn't got, and they're all on the
                 recipe's own page a tap away. -->
            <div class="row items-center no-wrap recipe-row__chips">
                <q-chip v-if="totalTime !== null && !compact" dense :icon="ICONS.schedule">
                    {{ totalTime }}m
                </q-chip>
                <q-chip v-if="ingredientCount > 0 && !compact" dense :icon="ICONS.ingredients">
                    {{ ingredientCount }}
                </q-chip>
                <q-chip
                    v-if="kcal.value !== null && !compact"
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
                <!-- FU-653 — Dora's belief, as a remark. Outline, not filled:
                     it's an opinion that hasn't changed any of the facts. -->
                <q-chip
                    v-if="recipe.inference_hint"
                    dense
                    outline
                    :color="recipe.inference_hint === 'at_risk' ? 'warning' : 'positive'"
                    :icon="ICONS.inferred_hunch"
                >
                    <span v-if="!compact">
                        {{ recipe.inference_hint === 'at_risk' ? 'May be short' : 'May be cookable' }}
                    </span>
                    <q-tooltip max-width="300px">{{ inferenceTooltip }}</q-tooltip>
                </q-chip>
                <ExpiringChip
                    v-if="showExpiringBadge && (recipe.expiring_ingredient_count ?? 0) > 0"
                    :count="recipe.expiring_ingredient_count ?? 0"
                    :soonest-date="recipe.expiring_soonest_date"
                    compact
                />
            </div>

            <q-space />

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
                variant="filled-icon"
                :icon="ICONS.chef_hat"
                :color="cookButtonColor"
                @click.stop="emit('cook', recipe.recipe_id)"
            >
                <q-tooltip>{{ cookButtonTooltip }}</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="icon"
                :icon="cookable === true ? ICONS.add_shopping_cart : ICONS.remove_shopping_cart"
                :color="cookable === false ? 'warning' : undefined"
                :disable="recipe.ingredients.length === 0"
                @click.stop="onAddToList"
            >
                <q-tooltip>{{ addListTooltip }}</q-tooltip>
            </BaseButton>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import ExpiringChip from 'src/components/recipes/ExpiringChip.vue';
    import { useQuasar } from 'quasar';
    import BaseButton from 'src/components/BaseButton.vue';
    import type { Recipe } from 'src/models/recipe';
    import { useRecipeDisplay } from 'src/composables/useRecipeDisplay';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            /** C-waste W4 — render the expiring count when the cookbook's
             *  "Uses expiring ingredients" filter is active. */
            showExpiringBadge?: boolean;
        }>(),
        { showExpiringBadge: false },
    );

    const emit = defineEmits<{
        (e: 'open', recipeId: string): void;
        (e: 'cook', recipeId: string): void;
        (e: 'toggle-favourite', recipeId: string): void;
        (e: 'add-missing', recipeId: string, stockItemIds: string[]): void;
        (e: 'add-all-to-list', recipeId: string): void;
    }>();

    const $q = useQuasar();
    const compact = computed(() => $q.screen.lt.sm);

    const {
        totalTime, ingredientCount, kcal, metaLine, missingIds, cookable,
        cookButtonColor, cookButtonTooltip, addListTooltip, inferenceTooltip,
    } = useRecipeDisplay(() => props.recipe);

    function onAddToList() {
        if (cookable.value) emit('add-all-to-list', props.recipe.recipe_id);
        else emit('add-missing', props.recipe.recipe_id, missingIds.value);
    }
</script>

<style scoped>
    /* Chrome deliberately matches `StockItemRow` — the two compact lists
       should read as the same control in two places. */
    .recipe-row {
        margin-bottom: 8px;
        border-radius: 8px;
        overflow: hidden;
        transition:
            box-shadow var(--motion-fast) var(--motion-ease),
            background-color var(--motion-fast) var(--motion-ease),
            border-color var(--motion-fast) var(--motion-ease);
        border: 1px solid var(--border-default, color-mix(in srgb, var(--text-primary) 12%, transparent));
    }
    .recipe-row:hover {
        background: color-mix(in srgb, var(--q-accent) 4%, var(--surface-component));
        border-color: color-mix(in srgb, var(--q-accent) 38%, transparent);
        box-shadow: 0 1px 6px color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .recipe-row__body {
        padding: 6px 12px;
        gap: 12px;
        min-height: 56px;
    }
    /* The name zone is the only part allowed to shrink, so a long recipe
       name truncates instead of pushing the action cluster off the row. */
    .recipe-row__name-zone {
        min-width: 0;
        flex: 1 1 auto;
    }
    .recipe-row__name {
        font-weight: 600;
        line-height: 1.25;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .recipe-row__meta {
        font-size: 0.75rem;
        color: var(--text-secondary);
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .recipe-row__chips {
        flex: 0 0 auto;
        gap: 4px;
    }
    /* Phones: same squeeze StockItemRow applies — tighter gap and smaller
       icon buttons, so the trailing cluster doesn't eat half the row. */
    @media (max-width: 599px) {
        .recipe-row__body {
            padding: 4px 8px;
            gap: 8px;
        }
        .recipe-row__body :deep(.dora-btn--icon) {
            min-width: 30px;
            min-height: 30px;
            width: 30px;
            height: 30px;
        }
        .recipe-row__body :deep(.dora-btn--icon .q-icon) {
            font-size: 19px;
        }
    }
</style>
