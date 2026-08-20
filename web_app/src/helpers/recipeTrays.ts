import type { Recipe } from 'src/models/recipe';

/**
 * The recipe-picker trays, in one place.
 *
 * R-003: this logic existed **twice**, character-for-character — in
 * `useMealPlanner.ts` (the planner rail) and in `MealPlanBuilderDialog.vue`
 * (the step-by-step wizard). Both feed the same `MealPlanRecipePicker`, so a
 * change to one silently disagreed with the other; the FU-578 #47 dedupe below
 * would have had to be written twice to hold. Both now call this.
 *
 * FU-578 #47 — **one selectable instance per recipe.** The trays used to
 * overlap: a favourite appeared under `Favourites` *and* again in the complete
 * `All recipes` tray, each rendering its own checkbox, so the wizard looked
 * like it was offering the same recipe twice. Every recipe now lands in
 * exactly one tray — the highest-priority one it qualifies for — and the final
 * tray is named for what it actually holds.
 *
 * Priority: Favourites → Haven't had in a while → Frequently planned →
 * Everything else. Favourites wins because it is the tray users open first and
 * the one they expect their own picks in; the two behavioural trays are
 * discovery shortcuts, so a recipe that is *both* stale and a favourite is
 * more useful under the label the user chose themselves.
 *
 * Findability under dedupe: nothing can hide, because the caps are applied
 * *before* the claim — a recipe squeezed out of a capped tray falls through to
 * the next one rather than disappearing — and search bypasses trays entirely,
 * returning one flat `Results` tray over the whole cookbook.
 */
export type RecipeTray = {
    key: string;
    title: string;
    recipes: Recipe[];
    defaultOpen: boolean;
};

/** How many recipes the two behavioural shortcut trays will show. A shortcut
 *  stops being one once you have to scroll it. */
export const RECIPE_TRAY_CAP = 10;

function madeMs(r: Recipe): number {
    return r.last_made_on ? new Date(r.last_made_on).getTime() : 0;
}

/**
 * @param recipes    the full candidate set (already filtered by whatever the
 *                   caller considers in-scope).
 * @param searchTerm the live search box value. Non-empty collapses the trays
 *                   to a single flat result list — searching is an explicit
 *                   "show me anything matching", so grouping it would hide
 *                   matches behind collapsed headers.
 */
export function buildRecipeTrays(recipes: Recipe[], searchTerm = ''): RecipeTray[] {
    const query = searchTerm.trim().toLowerCase();
    if (query) {
        const matches = recipes.filter((r) => r.name.toLowerCase().includes(query));
        return [{
            key: 'results',
            title: `Results (${matches.length})`,
            recipes: matches,
            defaultOpen: true,
        }];
    }

    const out: RecipeTray[] = [];
    // Claimed ids, not claimed recipes — the same recipe object identity isn't
    // guaranteed across the store refreshes these lists are derived from.
    const claimed = new Set<string>();
    const claim = (list: Recipe[]): Recipe[] => {
        const kept = list.filter((r) => !claimed.has(r.recipe_id));
        kept.forEach((r) => claimed.add(r.recipe_id));
        return kept;
    };

    const favs = claim(recipes.filter((r) => r.is_favourite));
    if (favs.length) {
        out.push({ key: 'fav', title: 'Favourites', recipes: favs, defaultOpen: true });
    }

    // Cap first, then claim: an over-cap recipe must stay available further
    // down the list rather than being consumed by a tray that won't show it.
    const stale = claim(
        recipes
            .filter((r) => r.not_made_recently)
            .sort((a, b) => madeMs(a) - madeMs(b))
            .slice(0, RECIPE_TRAY_CAP),
    );
    if (stale.length) {
        out.push({
            key: 'stale',
            title: "Haven't had in a while",
            recipes: stale,
            defaultOpen: false,
        });
    }

    const freq = claim(
        recipes
            .filter((r) => r.plan_count > 0)
            .sort((a, b) => b.plan_count - a.plan_count)
            .slice(0, RECIPE_TRAY_CAP),
    );
    if (freq.length) {
        out.push({
            key: 'freq',
            title: 'Frequently planned',
            recipes: freq,
            defaultOpen: false,
        });
    }

    // The remainder. Titled "Everything else" only when a shortcut tray
    // actually took something — on a cookbook with no favourites and no
    // history this IS the whole list, and "Everything else (12)" above a
    // complete list would read as if 12 were a subset.
    const rest = claim(recipes);
    out.push({
        key: 'all',
        title: out.length
            ? `Everything else (${rest.length})`
            : `All recipes (${rest.length})`,
        recipes: rest,
        defaultOpen: true,
    });
    return out;
}
