// @vitest-environment jsdom
/**
 * The cookbook's front-of-pack rating chip, after the owner's 2026-08-28 note
 * ("the star rating looks a bit meh — show me better designs").
 *
 * What changed: health stars stopped rendering as five inline glyphs in the
 * card's chip run and became a score pill — one star plus the number — with
 * the full five-star render moved into the hover. Nutri-Score kept its badge,
 * because the A–E strip is already compact and its colour is the signal.
 *
 * Tested rather than eyeballed for two reasons. The chip only renders on an
 * install in *complex* nutrition mode with a scheme picked, which needs an
 * imported food catalogue — not something a scratch verify instance has, so
 * there is no running app to point at. And the partial case (`is_reliable`
 * false) is the one the owner actually hit, which no amount of clicking on a
 * healthy pantry reproduces.
 *
 * The scheme arithmetic is emphatically not tested here — it is server-side,
 * pinned against the published tables in `tests/test_health_star_rating.py`
 * and `tests/test_nutri_score.py`.
 */
import { mount } from '@vue/test-utils';
import { QIcon, QTooltip, Quasar } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref, type Ref } from 'vue';

import type { Recipe } from 'src/models/recipe';

let scheme: Ref<string>;
vi.mock('src/composables/useFeatureFlags', () => ({
    useFeatureFlags: () => ({ nutritionRatingScheme: scheme }),
}));

let complex: Ref<boolean>;
vi.mock('src/composables/useNutritionMode', () => ({
    useNutritionMode: () => ({ isComplex: complex }),
}));

// Imported after the mocks so the composable picks them up.
const { default: RecipeRatingChip } = await import(
    'src/components/recipes/RecipeRatingChip.vue');

function recipeWith(nutrition: Record<string, unknown> | null): Recipe {
    return { recipe_id: 'r1', name: 'Cheesy Garlic Bread', nutrition } as unknown as Recipe;
}

function withStars(stars: number, isReliable = true) {
    return recipeWith({
        is_reliable: isReliable,
        health_star_rating: { stars },
        nutri_score: null,
    });
}

function mountChip(recipe: Recipe) {
    return mount(RecipeRatingChip, {
        props: { recipe },
        global: {
            plugins: [Quasar],
            components: { QIcon, QTooltip },
            // The tooltip renders through a teleport it never opens in jsdom;
            // stubbing it inline is what makes its contents assertable.
            stubs: { QTooltip: { template: '<div class="tip-stub"><slot /></div>' } },
        },
    });
}

beforeEach(() => {
    scheme = ref('health_star');
    complex = ref(true);
});

describe('RecipeRatingChip — health stars', () => {
    it('renders one glyph and the number, not five stars', () => {
        const wrapper = mountChip(withStars(4.5));

        expect(wrapper.find('.rating-chip--score').exists()).toBe(true);
        expect(wrapper.find('.rating-chip__value').text()).toBe('4.5');
        // The five-star component belongs in the hover now. One star icon in
        // the pill itself; anything more means the old inline render is back.
        expect(wrapper.findAll('.rating-chip--score > .q-icon')).toHaveLength(1);
    });

    it('always shows one decimal, so the pill width does not jump per card', () => {
        expect(mountChip(withStars(4)).find('.rating-chip__value').text()).toBe('4.0');
    });

    it('puts the full five-star render in the hover', () => {
        const wrapper = mountChip(withStars(0.5));

        const tip = wrapper.find('.tip-stub');
        expect(tip.findComponent({ name: 'RecipeHealthStars' }).exists()).toBe(true);
        expect(tip.text()).toContain('Health Star Rating 0.5 of 5');
    });

    it('marks a partial rating with an asterisk rather than dimming it', () => {
        const wrapper = mountChip(withStars(2, false));

        expect(wrapper.find('.rating-chip__part').exists()).toBe(true);
        // The old treatment was `opacity: .55` on the whole block, which reads
        // as "disabled" rather than "approximate".
        expect(wrapper.find('.rating-chip--part').exists()).toBe(false);
        expect(wrapper.find('.tip-stub').text())
            .toContain('worked out from only part of this recipe');
    });

    it('says nothing when the recipe has no rating', () => {
        expect(mountChip(recipeWith(null)).find('.rating-chip').exists()).toBe(false);
    });
});

describe('RecipeRatingChip — gating', () => {
    it('renders nothing in simple nutrition mode, rating data or not', () => {
        complex.value = false;
        expect(mountChip(withStars(4.5)).find('.rating-chip').exists()).toBe(false);
    });

    it('renders nothing when the install picked no scheme', () => {
        scheme.value = 'none';
        expect(mountChip(withStars(4.5)).find('.rating-chip').exists()).toBe(false);
    });

    it('renders nothing for a scheme this build has no badge for', () => {
        // Recognised-or-none, not "anything that isn't 'none'" — otherwise a
        // future scheme lights the chip up and draws nothing into it.
        scheme.value = 'traffic_light';
        expect(mountChip(withStars(4.5)).find('.rating-chip').exists()).toBe(false);
    });
});

describe('RecipeRatingChip — Nutri-Score', () => {
    it('keeps the A–E badge rather than collapsing it into the score pill', () => {
        scheme.value = 'nutri_score';
        const wrapper = mountChip(recipeWith({
            is_reliable: true,
            health_star_rating: null,
            nutri_score: { grade: 'B' },
        }));

        expect(wrapper.find('.rating-chip--score').exists()).toBe(false);
        expect(wrapper.findComponent({ name: 'RecipeNutriScore' }).exists()).toBe(true);
    });
});
