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
                 switch: compact IS the without-photos shape. (The
                 `show_recipe_images` preference that toggle wrote was cut
                 entirely on 2026-08-29.) -->

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
                 Icons, owner 2026-08-28: `timer` for a duration stays — a bare
                 "25m" is ambiguous. The ingredient count *lost* its icon and
                 gained the word instead ("6 ingredients"): the counter glyph
                 read as clutter at 14px and still needed explaining, whereas
                 the word explains itself and costs about the same width.
                 kcal joined this line rather than the chip cluster — it's a
                 plain fact about the dish, same species as the other two, and
                 the cluster is for opinions. -->
            <div class="recipe-row__name-zone column items-start justify-center">
                <div class="recipe-row__name">{{ recipe.name }}</div>
                <div
                    v-if="!compact && metaFacts"
                    class="recipe-row__meta row items-center no-wrap"
                >
                    <span v-if="totalTime !== null" class="recipe-row__fact">
                        <q-icon :name="ICONS.timer" size="14px" />{{ totalTime }}m
                    </span>
                    <span v-if="ingredientCount > 0" class="recipe-row__fact">
                        {{ ingredientCount }}
                        {{ ingredientCount === 1 ? 'ingredient' : 'ingredients' }}
                    </span>
                    <span v-if="kcal.value !== null" class="recipe-row__fact">
                        <q-icon :name="ICONS.monitor_heart" size="14px" />
                        <!-- One node, so `.recipe-row__fact`'s flex gap
                             doesn't push the asterisk off its number. -->
                        <span>
                            {{ Math.round(kcal.value) }} kcal<span
                                v-if="!kcal.judgeable"
                                aria-hidden="true"
                            >*</span>
                        </span>
                        <q-tooltip v-if="!kcal.judgeable">
                            Worked out from only part of this recipe — open it
                            to see what's missing.
                        </q-tooltip>
                    </span>
                </div>
            </div>

            <!-- Figures. On phones only the two that change a decision
                 survive (time, and the belief/expiring flags) — the rest
                 would take width the row hasn't got, and they're all on the
                 recipe's own page a tap away. -->
            <!-- What's left in the cluster: Dora's belief, which is the one
                 thing here that is an opinion rather than a fact. Time,
                 ingredient count and kcal all moved under the name; the rating
                 moved to the action cluster beside the favourite button. -->
            <div class="row items-center no-wrap recipe-row__chips">
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

            <!-- Anchored beside the favourite button, matching `RecipeCard`
                 (owner 2026-08-28). Survives `compact`: on a phone the pill is
                 the most compressible way to say the most, and it's the one
                 figure a browse is scanning down the list for. -->
            <RecipeRatingChip :recipe="recipe" class="q-mr-xs" />
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
    import RecipeRatingChip from 'src/components/recipes/RecipeRatingChip.vue';
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

    // `metaLine` deliberately not destructured — the compact row renders its
    // own two-or-three-fact second line rather than the card's prose one.
    const {
        totalTime, ingredientCount, kcal, missingIds, cookable,
        cookButtonColor, cookButtonTooltip, addListTooltip, inferenceTooltip,
    } = useRecipeDisplay(() => props.recipe);

    /** Whether the line under the name has anything on it. Computed rather
     *  than spelled out in the `v-if` so the three facts can't drift out of
     *  sync with the three `v-if`s inside it. */
    const metaFacts = computed(
        () => totalTime.value !== null || ingredientCount.value > 0 || kcal.value.value !== null);

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
