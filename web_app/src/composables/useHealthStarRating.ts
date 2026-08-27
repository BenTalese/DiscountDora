// The recipe Health Star Rating — whether this install shows one, and how to
// read a recipe's (owner ask 2026-08-27).
//
// Two conditions, and both are the server's answer rather than ours:
//
//   * `health_star_rating` — the install-wide switch. Off everywhere by
//     default, because HSR is an Australian/New Zealand government scheme and
//     an install in another country should not be handed a national rating as
//     though it were universal. Settings → Region's "Match this device" offers
//     to turn it on when it detects an AU/NZ locale.
//   * complex nutrition mode — a rating is computed from the foods the
//     ingredients link to, so simple mode (a typed kcal and nothing else) has
//     nothing to score. The flag being on in simple mode is a no-op, not an
//     error.
//
// Nothing here re-derives a rating. The FSANZ tables live server-side in
// `dora_api/domain/health_star_rating.py` and transcribing them a second time
// in TypeScript is exactly the drift R-003 exists to prevent.

import { computed } from 'vue';

import { useFeatureFlags } from 'src/composables/useFeatureFlags';
import { useNutritionMode } from 'src/composables/useNutritionMode';
import type { Recipe, RecipeHealthStarRating } from 'src/models/recipe';

export function useHealthStarRating() {
    const { healthStarRating } = useFeatureFlags();
    const { isComplex } = useNutritionMode();

    /** Whether the rating axis exists at all on this install. Every surface —
     *  the recipe panel, the cookbook chip, the filter and the sort axis —
     *  gates on this one computed rather than each re-assembling the pair. */
    const ratingAvailable = computed(() => healthStarRating.value && isComplex.value);

    /** A recipe's rating and whether it may be used to *judge* the recipe.
     *
     *  `judgeable` is the rollup's own `is_reliable` — the same coverage gate
     *  the kcal axis uses (R-041). Displaying a thin rating with its coverage
     *  is honest; hiding a recipe from a "3.5 stars and up" filter on the
     *  strength of a 2-of-9 estimate is not, so the filter lets those through
     *  rather than excluding them.
     *
     *  Note this gate is about *ingredient coverage*, not about which
     *  nutrients were known. The second gap — sugars is known for only ~77%
     *  of USDA foods, and a missing penalty nutrient makes a recipe rate
     *  better — is reported per nutrient in the panel instead of collapsing
     *  into this boolean, which was the owner's call. */
    function ratingOf(recipe: Recipe): {
        rating: RecipeHealthStarRating | null;
        judgeable: boolean;
    } {
        const nutrition = recipe.nutrition ?? null;
        return {
            rating: nutrition?.health_star_rating ?? null,
            judgeable: nutrition?.is_reliable === true,
        };
    }

    return { ratingAvailable, ratingOf };
}
