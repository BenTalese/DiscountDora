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
    import { computed } from 'vue';

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
</script>

<style scoped>
    .dora-gaps {
        margin: 4px 0 0;
        padding-left: 18px;
    }
</style>
