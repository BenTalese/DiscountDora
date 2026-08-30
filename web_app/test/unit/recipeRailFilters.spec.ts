// BRIEF_MEAL_PLANNER_RAIL_AND_SHELL §4.3 — the recipe rail's filter contract.
//
// Replaces `recipeTrays.spec.ts`, deleted with the tray builder on 2026-08-30.
// Worth an automated test under the lean verification stance (DORA_VERIFY
// banner): these are pure predicates with no pinia and no network, they are
// shared by three pickers (planner rail, mobile sheet, build-my-week wizard),
// and re-checking them by hand means constructing a cookbook with exactly the
// right mix of favourites/history/plan-counts every single time.
//
// The headline case is the one that INVERTS the old contract: trays gave each
// recipe exactly one home (FU-578 #47), filters deliberately do not.
import { describe, expect, it } from 'vitest';

import { buildFilterChips, filterRecipes } from 'src/helpers/recipeRailFilters';
import type { Recipe } from 'src/models/recipe';

function recipe(over: Partial<Recipe> & { recipe_id: string; name: string }): Recipe {
    return {
        is_favourite: false,
        not_made_recently: false,
        plan_count: 0,
        last_made_on: null,
        ...over,
    } as Recipe;
}

const FAV_AND_REGULAR = recipe({
    recipe_id: 'a', name: 'Aglio e Olio', is_favourite: true, plan_count: 5,
});
const STALE = recipe({ recipe_id: 'b', name: 'Bolognese', not_made_recently: true });
const PLAIN = recipe({ recipe_id: 'c', name: 'Congee' });
const ALL = [FAV_AND_REGULAR, STALE, PLAIN];

describe('filterRecipes', () => {
    it('lets one recipe qualify for several chips (supersedes the FU-578 #47 dedupe)', () => {
        // The tray builder claimed each recipe for exactly one tray, so a
        // favourite that was also frequently planned vanished from "Regulars".
        // As filters that is wrong: you asked for regulars, so every regular
        // shows — and it cannot double-render because only one filter is ever
        // active.
        expect(filterRecipes(ALL, 'favourites').map((r) => r.recipe_id)).toEqual(['a']);
        expect(filterRecipes(ALL, 'regulars').map((r) => r.recipe_id)).toEqual(['a']);
    });

    it('selects on the server flag, never a client recency computation', () => {
        // `not_made_recently` is the server's 21-day household window. The old
        // builder additionally sorted by `last_made_on` client-side, which was
        // the R-003 leak this replacement removes.
        const withDates = [
            recipe({ recipe_id: 'x', name: 'Xacuti', not_made_recently: true, last_made_on: '2020-01-01' }),
            recipe({ recipe_id: 'y', name: 'Ayam', not_made_recently: true, last_made_on: '2026-01-01' }),
            recipe({ recipe_id: 'z', name: 'Zuppa', not_made_recently: false, last_made_on: null }),
        ];
        const out = filterRecipes(withDates, 'not_lately');
        expect(out.map((r) => r.recipe_id)).toEqual(['y', 'x']); // by NAME, not by date
    });

    it('orders regulars by plan_count, most-planned first', () => {
        const many = [
            recipe({ recipe_id: 'low', name: 'Aaa', plan_count: 1 }),
            recipe({ recipe_id: 'high', name: 'Zzz', plan_count: 9 }),
        ];
        expect(filterRecipes(many, 'regulars').map((r) => r.recipe_id)).toEqual(['high', 'low']);
    });

    it('narrows the active chip by search rather than replacing it', () => {
        // L99 — search is separate from the chips, so it applies ON TOP of the
        // filter. "Bolognese" matches the query but is not a favourite.
        expect(filterRecipes(ALL, 'favourites', 'bolog')).toEqual([]);
        expect(filterRecipes(ALL, 'all', 'bolog').map((r) => r.recipe_id)).toEqual(['b']);
    });

    it('matches search case-insensitively', () => {
        expect(filterRecipes(ALL, 'all', 'AGLIO').map((r) => r.recipe_id)).toEqual(['a']);
    });

    it('treats the suggests chip as unfiltered — the caller supplies the ranking', () => {
        expect(filterRecipes(ALL, 'suggests')).toHaveLength(3);
    });
});

describe('buildFilterChips', () => {
    it('keeps an empty chip in place, disabled and explained (B2a)', () => {
        // The old trays hid themselves when empty, so the row reflowed as the
        // cookbook grew and the user lost their spatial memory of the controls.
        const chips = buildFilterChips([PLAIN]);
        const favourites = chips.find((c) => c.key === 'favourites');

        expect(favourites).toBeDefined();
        expect(favourites?.disabled).toBe(true);
        expect(favourites?.disabledReason).toBeTruthy();
    });

    it('never disables All, so at least one chip is always usable', () => {
        expect(buildFilterChips([]).find((c) => c.key === 'all')?.disabled).toBe(false);
    });

    it('puts Dora suggests first, since the brief requires it be marked out', () => {
        expect(buildFilterChips(ALL)[0]?.key).toBe('suggests');
    });

    it('counts each chip independently of the others', () => {
        const counts = Object.fromEntries(
            buildFilterChips(ALL).map((c) => [c.key, c.count]),
        );
        expect(counts.all).toBe(3);
        expect(counts.favourites).toBe(1);
        expect(counts.not_lately).toBe(1);
        expect(counts.regulars).toBe(1);
    });
});
