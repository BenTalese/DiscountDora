<template>
    <q-card flat bordered class="q-mb-md">
        <q-card-section class="row items-start q-gutter-sm no-wrap">
            <q-icon :name="ICONS.monitor_heart" size="22px" class="dora-text-muted" />
            <div class="col">
                <div class="text-caption dora-text-muted">
                    {{ basisLabel }}
                    <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                        <q-tooltip>
                            Summed from the foods your ingredients are linked
                            to, converted to grams. Link more ingredients to a
                            food on their stock item to fill the gaps.
                        </q-tooltip>
                    </q-icon>
                </div>

                <div v-if="nutrition.kcal !== null" class="text-body2">
                    <strong>{{ Math.round(nutrition.kcal) }}</strong>
                    <span class="dora-text-muted q-ml-xs">kcal</span>
                </div>
                <div v-else class="text-body2 dora-text-muted">
                    Nothing to add up yet
                </div>

                <div v-if="macros.length" class="text-caption dora-text-muted q-mt-xs">
                    <span v-for="(macro, index) in macros" :key="macro.label">
                        <span v-if="index > 0"> · </span>{{ macro.label }} {{ macro.value }}g
                    </span>
                </div>

                <!-- Health Star Rating (owner ask 2026-08-27). Renders only
                     when the install has it on; the server simply omits the
                     field otherwise, so there is no second gate here. -->
                <div v-if="rating" class="dora-hsr q-mt-sm">
                    <div class="dora-hsr__row">
                        <RecipeHealthStars :stars="rating.stars" qualifier="estimated" />
                        <BaseButton
                            variant="subtle"
                            dense
                            :icon="ICONS.help_outline"
                            :label="breakdownOpen ? 'Hide working' : 'How this was scored'"
                            :aria-expanded="breakdownOpen"
                            @click="breakdownOpen = !breakdownOpen"
                        />
                    </div>
                    <div class="text-caption dora-text-muted">{{ ratingCaption }}</div>

                    <q-slide-transition>
                        <div v-show="breakdownOpen" class="dora-hsr__working text-caption">
                            <!-- The point ledger, in the order the FSANZ
                                 method computes it. A star count nobody can
                                 interrogate is the one thing this feature
                                 must not be. -->
                            <div class="dora-hsr__ledger">
                                <span
                                    v-for="row in breakdown"
                                    :key="row.label"
                                    class="dora-hsr__cell"
                                >
                                    <span class="dora-hsr__k">{{ row.label }}</span>
                                    <span class="dora-hsr__v">{{ row.value }}</span>
                                </span>
                            </div>
                            <p class="dora-hsr__note">
                                Score {{ rating.score }} — {{ rating.baseline_points }} baseline
                                point{{ s(rating.baseline_points) }} less
                                {{ rating.baseline_points - rating.score }} for what the dish
                                has going for it. Lower scores earn more stars.
                            </p>
                            <p v-if="!rating.protein_counted" class="dora-hsr__note">
                                Protein didn't count towards this rating. The scheme only
                                credits protein on an energy-dense dish when at least 80%
                                of it is fruit, vegetables, nuts or legumes.
                            </p>
                            <p v-if="thinNutrients.length" class="dora-hsr__note">
                                Scored without a full picture:
                                {{ thinNutrients.join(', ') }}. A missing figure here scores
                                nothing, which flatters the rating rather than lowering it.
                            </p>
                            <p class="dora-hsr__note">
                                Health Star Rating, calculated the way FSANZ publishes it,
                                from the raw weight of the ingredients — a dish that reduces
                                down or is made with water you haven't listed will differ.
                            </p>
                        </div>
                    </q-slide-transition>
                </div>

                <!-- The coverage line is always visible, even at full
                     coverage: a number whose basis is invisible reads as
                     complete whether it is or not. -->
                <div class="text-caption dora-text-muted q-mt-xs">
                    {{ coverageLine }}
                </div>
                <ul v-if="gaps.length" class="dora-gaps text-caption dora-text-muted">
                    <li v-for="gap in gaps" :key="gap.reason">{{ gap.text }}</li>
                </ul>
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    /**
     * FU-635 — complex-mode recipe nutrition.
     *
     * Renders the server's rollup verbatim: no summing, no unit maths, no
     * rounding decisions beyond display (R-003 / the state-ownership rule —
     * the figure and its coverage are domain facts the server owns).
     *
     * The coverage line never hides. The owner's call was "partials shown and
     * marked", and a per-serving figure built from 5 of 12 ingredients is a
     * different claim from one built from 12 — the reader has to be able to
     * tell them apart at a glance (P3 Honest).
     */
    import { computed, ref } from 'vue';

    import BaseButton from 'src/components/BaseButton.vue';
    import RecipeHealthStars from 'src/components/recipes/RecipeHealthStars.vue';
    import type { RecipeNutrition, RecipeNutritionGap } from 'src/models/recipe';
    import { ICONS } from 'src/style/icons';

    const props = defineProps<{ nutrition: RecipeNutrition }>();

    const s = (count: number) => (count === 1 ? '' : 's');

    /** Copy per gap reason. Presentation, so it lives client-side; the ids
     *  themselves are the server's closed set. */
    const GAP_COPY: Record<RecipeNutritionGap, (count: number) => string> = {
        not_linked: (n) => `${n} ingredient${s(n)} not linked to a stock item`,
        no_food: (n) => `${n} stock item${s(n)} not linked to a food`,
        no_quantity: (n) => `${n} ingredient${s(n)} with no amount given`,
        no_conversion: (n) => `${n} amount${s(n)} we can't convert to a weight`,
        no_data: (n) => `${n} food${s(n)} with no calorie data`,
    };

    const basisLabel = computed(() =>
        props.nutrition.basis === 'serving'
            ? 'Nutrition (per serving)'
            : 'Nutrition (whole recipe)',
    );

    const macros = computed(() =>
        [
            { label: 'Protein', value: props.nutrition.protein_g },
            { label: 'Carbs', value: props.nutrition.carbs_g },
            { label: 'Fat', value: props.nutrition.fat_g },
        ].filter((macro): macro is { label: string; value: number } => macro.value !== null),
    );

    const coverageLine = computed(() => {
        const { counted_count: counted, total_count: total, basis } = props.nutrition;
        if (total === 0) return 'This recipe has no ingredients yet';
        if (counted === 0) return `From 0 of ${total} ingredient${s(total)}`;
        const suffix = basis === 'recipe' ? ' · add servings for a per-serving figure' : '';
        return `From ${counted} of ${total} ingredient${s(total)}${suffix}`;
    });

    const gaps = computed(() =>
        (Object.entries(props.nutrition.uncounted) as [RecipeNutritionGap, number][])
            .filter(([, count]) => count > 0)
            .map(([reason, count]) => ({ reason, text: GAP_COPY[reason](count) })),
    );

    // ── Health Star Rating ──────────────────────────────────────────────
    const breakdownOpen = ref(false);
    const rating = computed(() => props.nutrition.health_star_rating);

    const ratingCaption = computed(() => {
        const value = rating.value;
        if (!value) return '';
        const fvnl = value.fvnl_percent;
        // The fvnl figure is the one input worth stating outright: it is what
        // separates two dishes with the same calories, and it is the number a
        // cook can actually act on.
        const produce = fvnl === null
            ? ''
            : ` · ${Math.round(fvnl)}% fruit, veg, nuts or legumes`;
        return `Health Star Rating — estimated${produce}`;
    });

    /** The point ledger. Baseline points count against the recipe and
     *  modifying points count for it, so the signs are shown rather than left
     *  to the reader to infer from the label. */
    const breakdown = computed(() => {
        const value = rating.value;
        if (!value) return [];
        return [
            { label: 'Energy', value: `+${value.energy_points}` },
            { label: 'Sat fat', value: `+${value.saturated_fat_points}` },
            { label: 'Sugars', value: `+${value.total_sugars_points}` },
            { label: 'Sodium', value: `+${value.sodium_points}` },
            { label: 'Fruit & veg', value: `−${value.v_points}` },
            { label: 'Protein', value: `−${value.protein_points}` },
            { label: 'Fibre', value: `−${value.fibre_points}` },
        ];
    });

    // Which of the rating's four penalty nutrients were known for less than
    // most of the recipe's weight. Named individually rather than rolled into
    // one percentage because "we didn't know the sugar" and "we didn't know
    // the sodium" lead a cook to different conclusions.
    //
    // The threshold is a *display* choice — below this the figure is thin
    // enough to be worth mentioning — not the server's judge/don't-judge gate,
    // which is `is_reliable` and lives in the rollup (R-003).
    const THIN_COVERAGE = 0.9;
    const COVERAGE_LABELS: Record<string, string> = {
        kcal: 'energy',
        saturated_fat_g: 'saturated fat',
        sugars_g: 'sugars',
        sodium_mg: 'sodium',
    };

    const thinNutrients = computed(() => {
        const coverage = props.nutrition.nutrient_coverage ?? {};
        return Object.entries(COVERAGE_LABELS)
            .map(([key, label]) => ({ label, ratio: coverage[key] ?? 0 }))
            .filter((row) => row.ratio < THIN_COVERAGE)
            .map((row) => `${row.label} known for ${Math.round(row.ratio * 100)}% of it`);
    });
</script>

<style scoped>
    .dora-gaps {
        margin: 4px 0 0;
        padding-left: 18px;
    }

    .dora-hsr {
        padding-top: var(--space-2, 8px);
        border-top: 1px solid var(--divider);
    }
    .dora-hsr__row {
        display: flex;
        align-items: center;
        gap: var(--space-2, 8px);
        flex-wrap: wrap;
    }
    .dora-hsr__working { margin-top: var(--space-2, 8px); }
    .dora-hsr__ledger {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-1, 4px) var(--space-4, 16px);
    }
    .dora-hsr__cell {
        display: inline-flex;
        align-items: baseline;
        gap: var(--space-1, 4px);
    }
    .dora-hsr__k { color: var(--text-muted); }
    .dora-hsr__v {
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }
    .dora-hsr__note {
        margin: var(--space-2, 8px) 0 0;
        color: var(--text-muted);
        max-width: 62ch;
    }
</style>
