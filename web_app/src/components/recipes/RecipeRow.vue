<template>
    <!--
        Compact cookbook row — one line per recipe, the Stock Overview
        shape (2026-08-17 feedback). Same data and the same actions as
        `RecipeCard`; only the layout differs, and every derived figure
        comes from the shared `useRecipeDisplay` so the two views can't
        drift (R-003).

        Left → right:
          Name              · · ·  [chips] [expiring?] [♥] [👨‍🍳] [🛒]
          ⏱ 25m · 🔢 8
        Chrome mirrors `StockItemRow`: bordered flat card, 8px radius,
        accent-tinted hover, no lift — and, from 2026-08-20, the same
        name type size and the same name-plus-second-line shape.
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

            <!-- The old meta line (collection · cuisine · category · …) was
                 removed 2026-08-19 — owner: "remove the second info line under
                 the recipe name in compact view, looks too cluttered". It is
                 back on 2026-08-20, but as two facts rather than five:
                 "in desktop view put time and ingredient count right or
                 underneath of recipe name". Underneath, because the chip
                 cluster's width varies with how many chips a given recipe has,
                 so anything in it never lands twice in the same place (the
                 same reasoning that moved the expiring chip to the right edge)
                 — whereas a second line under the name starts at a fixed x.
                 Desktop only: on a phone these were already suppressed for
                 width, and that hasn't changed.
                 Icons: `timer` for a duration, `ingredientCount` for a count —
                 see the filter row for why each. -->
            <div class="recipe-row__name-zone column items-start justify-center">
                <div class="recipe-row__name">{{ recipe.name }}</div>
                <div
                    v-if="!compact && (totalTime !== null || ingredientCount > 0)"
                    class="recipe-row__meta row items-center no-wrap"
                >
                    <span v-if="totalTime !== null" class="recipe-row__fact">
                        <q-icon :name="ICONS.timer" size="14px" />{{ totalTime }}m
                    </span>
                    <span v-if="ingredientCount > 0" class="recipe-row__fact">
                        <q-icon :name="ICONS.ingredientCount" size="14px" />{{ ingredientCount }}
                    </span>
                </div>
            </div>

            <!-- Figures. On phones only the two that change a decision
                 survive (time, and the belief/expiring flags) — the rest
                 would take width the row hasn't got, and they're all on the
                 recipe's own page a tap away. -->
            <!-- What's left in the cluster: the two chips that are opinions
                 rather than plain facts (a kcal figure that may be partial,
                 and Dora's belief). Time + ingredient count moved under the
                 name — see above. -->
            <div class="row items-center no-wrap recipe-row__chips">
                <!-- Health Star Rating (owner ask 2026-08-27). Stars rather
                     than a number, and no chip around them: the row already
                     carries two chips, and a third box would read as a third
                     opinion when this is the one that's meant to be scannable
                     while browsing. Survives `compact` — on a phone it is the
                     most compressible way to say the most. -->
                <span
                    v-if="rating"
                    class="recipe-row__hsr"
                    :class="{ 'recipe-row__hsr--part': !ratingJudgeable }"
                >
                    <RecipeHealthStars
                        :stars="rating.stars"
                        size="sm"
                        :show-value="false"
                        :qualifier="ratingJudgeable ? 'estimated' : 'estimated from part of the recipe'"
                    />
                    <q-tooltip>
                        Health Star Rating {{ rating.stars.toFixed(1) }} of 5{{
                            ratingJudgeable
                                ? ''
                                : ' — worked out from only part of this recipe'
                        }}
                    </q-tooltip>
                </span>
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
            </div>

            <q-space />

            <!-- Owner 2026-08-19: "put the expiring ingredients chip with the
                 buttons on the right, otherwise in compact view it goes all
                 over the place (not consistently lined up)". It used to sit in
                 the left-hand `__chips` group, whose width varies with how
                 many of the other chips a given recipe has — so the one chip
                 that only appears sometimes never landed in the same place
                 twice. Anchored to the right edge it's always in one spot. -->
            <ExpiringChip
                v-if="showExpiringBadge && (recipe.expiring_ingredient_count ?? 0) > 0"
                :count="recipe.expiring_ingredient_count ?? 0"
                :soonest-date="recipe.expiring_soonest_date"
                compact
                class="recipe-row__expiring q-mr-xs"
            />

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
    import RecipeHealthStars from 'src/components/recipes/RecipeHealthStars.vue';
    import { useHealthStarRating } from 'src/composables/useHealthStarRating';
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

    // `metaLine` deliberately not destructured — the compact row no longer
    // renders a second line (see the template note). RecipeCard still uses it.
    const {
        totalTime, ingredientCount, kcal, missingIds, cookable,
        cookButtonColor, cookButtonTooltip, addListTooltip, inferenceTooltip,
    } = useRecipeDisplay(() => props.recipe);

    // The rating axis, if the install has it. `ratingOf` reads the server's
    // answer off the list DTO — the rollup already runs for the whole page to
    // feed the kcal chip, so the stars cost nothing extra (R-003).
    const { ratingAvailable, ratingOf } = useHealthStarRating();
    const rating = computed(() =>
        (ratingAvailable.value ? ratingOf(props.recipe).rating : null));
    const ratingJudgeable = computed(() => ratingOf(props.recipe).judgeable);

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
    /* Owner feedback 2026-08-20: "in compact view, recipe name should be
       same font style as stock item name". Values copied from
       `StockItemRow.vue`'s `.stock-row__name`; the only difference was the
       missing font-size, which left the recipe name a step smaller than the
       stock one on the same-shaped row.

       D-003 carve-out: `1.05rem` is a raw size, and the rule says use the
       `--font-size-*` ratios. It is deliberately raw here because the request
       was *parity with the stock row*, and that row is 1.05rem — a value with
       no token (md = 1, lg = 1.125). Tokenising one of the pair would break
       the parity this line exists to create, and tokenising both changes the
       Stock Overview type the owner signed off on last week. Logged as FU-693
       to move the pair together. */
    .recipe-row__name {
        font-weight: 600;
        font-size: 1.05rem;
        line-height: 1.25;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    /* Second line under the name. Plain text + inline icons rather than
       chips: chip chrome at this size is heavier than the facts warrant, and
       the old chip version is what read as cluttered. */
    /* A partial rating is drawn at reduced opacity rather than with a "(part)"
       suffix like the kcal chip: there is no room for the word, and the stars
       still have to read as stars. The tooltip carries the detail. */
    .recipe-row__hsr { display: inline-flex; align-items: center; }
    .recipe-row__hsr--part { opacity: 0.55; }
    .recipe-row__meta {
        gap: 10px;
        margin-top: 2px;
        /* D-003: `--font-size-sm` (14), not the 12 caption floor — cook time
           and ingredient count are values you act on ("can I make this
           tonight?"), and the rule reserves 12 for non-actionable captions. */
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }
    .recipe-row__fact {
        display: inline-flex;
        align-items: center;
        gap: 3px;
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
