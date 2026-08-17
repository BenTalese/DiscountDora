// Shared recipe presentation model — the single authority for everything
// the cookbook derives from a Recipe *for display*: the meta line, the
// chip figures, the cook/cart button colour + wording, and the belief
// tooltip.
//
// Why it exists (R-003): the compact row view added 2026-08-17 renders
// the same recipe as `RecipeCard` in a different shape. Copying the card's
// dozen computeds into the row would mean every future wording or colour
// change had to be made twice, and the two views would silently disagree
// the first time one was missed. Both components now read from here and
// decide only *layout*.
//
// Domain facts (cookable, missing_count, kcal_is_reliable, inference_hint)
// are all server-owned and arrive on the DTO — nothing here re-derives
// them; this is presentation of data in hand.

import { computed, type ComputedRef } from 'vue';
import { storeToRefs } from 'pinia';
import type { Recipe } from 'src/models/recipe';
import { recipeImageUrl } from 'src/services/api/recipeApiService';
import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';

export interface RecipeDisplay {
    /** Prep + cook, or null when neither is set. */
    totalTime: ComputedRef<number | null>;
    /** Ingredient-line count (display of a hydrated list, not a domain rule). */
    ingredientCount: ComputedRef<number>;
    /** Per-serving kcal + whether the figure is solid enough to judge on. */
    kcal: ComputedRef<{ value: number | null; judgeable: boolean }>;
    /** "Weeknight dinners · Italian · Dinner · Evening" — collection first,
     *  case-insensitively de-duplicated (DR-4). */
    metaLine: ComputedRef<string>;
    /** Dietary-tag names resolved from the vocabulary store. */
    tagNames: ComputedRef<string[]>;
    /** Distinct stock-item ids the recipe is short of. */
    missingIds: ComputedRef<string[]>;
    /** Server's cookability verdict: true / false / null (unlinked). */
    cookable: ComputedRef<boolean | null>;
    cookButtonColor: ComputedRef<string>;
    cookButtonTooltip: ComputedRef<string>;
    addListTooltip: ComputedRef<string>;
    /** FU-653 — explains the belief chip, naming the items it's about. */
    inferenceTooltip: ComputedRef<string>;
    /** Fallback glyph + colour for a recipe with no photo. */
    initial: ComputedRef<string>;
    mediaStyle: ComputedRef<{ background: string }>;
    imageUrl: ComputedRef<string>;
}

export function useRecipeDisplay(recipe: () => Recipe): RecipeDisplay {
    const { dietaryTags } = storeToRefs(useRecipeVocabStore());

    const totalTime = computed<number | null>(() => {
        const r = recipe();
        if (r.prep_time_minutes === null && r.cook_time_minutes === null) return null;
        return (r.prep_time_minutes ?? 0) + (r.cook_time_minutes ?? 0);
    });

    const ingredientCount = computed(() => recipe().ingredients.length);

    // FU-637 — the server decides which figure this mode carries and whether
    // it's solid enough to judge on; the UI just renders the answer.
    const kcal = computed(() => ({
        value: recipe().kcal_per_serving ?? null,
        judgeable: recipe().kcal_is_reliable === true,
    }));

    const metaLine = computed(() => {
        // DR-4 (FU-578 #14): dedupe case-insensitively so a recipe whose
        // cuisine and category are the same word doesn't read "Dessert ·
        // Dessert".
        // The collection leads the line. It used to be the cookbook's
        // grouping *layout* (collapsible folders); those hid search results
        // below the fold in a large book, so the folders went and the
        // collection became a fact about the recipe like any other.
        const r = recipe();
        const seen = new Set<string>();
        return [r.recipe_collection_name, r.cuisine_name, r.category_name, r.time_of_day]
            .filter((p): p is string => Boolean(p))
            .filter((p) => {
                const key = p.toLowerCase();
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            })
            .join(' · ');
    });

    const tagNames = computed(() => {
        const byId = new Map(dietaryTags.value.map((t) => [t.dietary_tag_id, t.name]));
        return (recipe().dietary_tag_ids ?? [])
            .map((id) => byId.get(id))
            .filter((n): n is string => Boolean(n));
    });

    const missingIds = computed(() => [
        ...new Set(
            recipe().ingredients
                .filter((i) => i.is_missing && i.stock_item_id !== null)
                .map((i) => i.stock_item_id as string),
        ),
    ]);

    const cookable = computed(() => recipe().cookable);
    const unlinkedCount = computed(() => recipe().unlinked_ingredient_count ?? 0);

    // Tri-state cook-button colour (IMPL_PLAN_RECIPE_IMPORTER §Chunk 4):
    //   true  → primary ("ready to cook")
    //   false → warning ("missing some ingredients but you can try")
    //   null  → grey ("we don't know — link ingredients to check")
    const cookButtonColor = computed(() => {
        if (cookable.value === null) return 'grey';
        return cookable.value ? 'primary' : 'warning';
    });
    const cookButtonTooltip = computed(() => {
        if (cookable.value === null) {
            return `Link ${unlinkedCount.value} ingredient${unlinkedCount.value === 1 ? '' : 's'} to check cookability — this is a stock-item feature`;
        }
        return cookable.value
            ? 'Cook'
            : `Cook anyway — missing ${missingIds.value.length} ingredient(s)`;
    });
    const addListTooltip = computed(() => {
        if (cookable.value === null) {
            return `${unlinkedCount.value} ingredient${unlinkedCount.value === 1 ? '' : 's'} need linking first`;
        }
        return cookable.value
            ? 'Add ingredients to a list'
            : `Add ${missingIds.value.length} missing to a list`;
    });

    // FU-653 — names the items, because "may be short" without saying what
    // is a nudge with nowhere to go.
    const inferenceTooltip = computed(() => {
        const r = recipe();
        const list = (r.inference_stock_item_names ?? []).join(', ');
        return r.inference_hint === 'at_risk'
            ? `Everything's recorded as in stock, but Dora thinks you may have run out of ${list}. Nothing has changed — check the item if you want to be sure.`
            : `Recorded as missing ${list}, but Dora thinks you're back in stock. Your recorded levels still decide what counts as cookable.`;
    });

    const initial = computed(() => (recipe().name.trim()[0] ?? '?').toUpperCase());
    const mediaStyle = computed(() => {
        let hash = 0;
        for (const ch of recipe().name) hash = (hash * 31 + ch.charCodeAt(0)) % 360;
        return { background: `hsl(${hash}, 45%, 42%)` };
    });
    const imageUrl = computed(() => recipeImageUrl(recipe().recipe_id));

    return {
        totalTime,
        ingredientCount,
        kcal,
        metaLine,
        tagNames,
        missingIds,
        cookable,
        cookButtonColor,
        cookButtonTooltip,
        addListTooltip,
        inferenceTooltip,
        initial,
        mediaStyle,
        imageUrl,
    };
}
