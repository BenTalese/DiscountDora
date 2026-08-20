// @vitest-environment jsdom
/**
 * Compact cookbook row layout — the structural changes from the owner's
 * 2026-08-19 and 2026-08-20 feedback:
 *
 *   - 2026-08-19: "Remove the second info line under the recipe name in compact
 *      view, looks too cluttered." (The line held five facts: collection ·
 *      cuisine · category · time · count.)
 *   - 2026-08-20: "In compact view, in desktop view put time and ingredient
 *      count right or underneath of recipe name." So the second line is back —
 *      as exactly two facts, desktop only. These two supersede each other on
 *      the *contents* of the line, not on the principle: the assertions below
 *      pin the line to those two facts so it cannot re-accumulate the other
 *      three.
 *   - "Put the expiring ingredients chip with the buttons on the right,
 *      otherwise in compact view it goes all over the place (not consistently
 *      lined up)."
 *
 * Tested rather than eyeballed because the browser pane can't render this list
 * (its `<Transition>` wedges mid-leave — a documented environment artefact, see
 * DORA_VERIFY_TRIAGE), and because "the chip is on the right" is a positional
 * fact that a later edit can undo without anything failing. The chip's *own*
 * appearance is a visual check and stays in DORA_VERIFY.
 *
 * Mount pattern follows shoppingListRailItem / stockLevelDot: real Quasar
 * chrome, `BaseButton` stubbed so the trailing cluster is inspectable without
 * driving real buttons.
 */
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { QCard, QCardSection, QChip, QIcon, QSpace, QTooltip, Quasar } from 'quasar';
import { beforeEach, describe, expect, it } from 'vitest';

import RecipeRow from 'src/components/recipes/RecipeRow.vue';
import type { Recipe } from 'src/models/recipe';

const SlotStub = { template: '<div class="slot-stub"><slot /></div>' };

function recipeOf(overrides: Partial<Recipe> = {}): Recipe {
    return {
        recipe_id: 'r1',
        name: 'Lasagne',
        cookable: true,
        is_favourite: false,
        unlinked_ingredient_count: 0,
        ingredients: [],
        collection_name: 'Weeknights',
        cuisine_name: 'Italian',
        prep_time_minutes: 15,
        cook_time_minutes: 30,
        total_time_minutes: 45,
        expiring_ingredient_count: 0,
        expiring_soonest_date: null,
        ...overrides,
    } as unknown as Recipe;
}

function mountRow(recipe: Recipe, showExpiringBadge = false) {
    return mount(RecipeRow, {
        props: { recipe, showExpiringBadge },
        global: {
            plugins: [Quasar],
            components: { QCard, QCardSection, QChip, QIcon, QSpace, QTooltip },
            stubs: { BaseButton: SlotStub, QTooltip: SlotStub },
        },
    });
}

beforeEach(() => {
    setActivePinia(createPinia());
});

describe('RecipeRow — compact layout', () => {
    it('renders the recipe name', () => {
        expect(mountRow(recipeOf()).find('.recipe-row__name').text()).toBe('Lasagne');
    });

    it('puts time and ingredient count under the name, and only those two', () => {
        // jsdom reports a desktop viewport, so `compact` is false — the branch
        // the owner's note is about.
        const wrapper = mountRow(recipeOf({
            ingredients: [{ stock_item_id: 's1' }, { stock_item_id: 's2' }],
        } as Partial<Recipe>));

        const facts = wrapper.findAll('.recipe-row__meta .recipe-row__fact');
        expect(facts.map((f) => f.text())).toEqual(['45m', '2']);
    });

    it('drops the whole line when neither fact has a value', () => {
        // Not an empty band: the row falls back to one line, as it does on a
        // phone. `total_time_minutes: null` + no ingredients = nothing to say.
        const wrapper = mountRow(recipeOf({
            prep_time_minutes: null,
            cook_time_minutes: null,
        } as Partial<Recipe>));
        expect(wrapper.find('.recipe-row__meta').exists()).toBe(false);
    });

    it('keeps the second line to the name zone, not the chip cluster', () => {
        // The 2026-08-19 clutter complaint in its durable form: whatever the
        // line holds, it belongs under the name (fixed left edge) and the chip
        // cluster keeps only the opinion chips.
        const wrapper = mountRow(recipeOf({
            ingredients: [{ stock_item_id: 's1' }],
        } as Partial<Recipe>));

        expect(wrapper.find('.recipe-row__name-zone .recipe-row__meta').exists())
            .toBe(true);
        expect(wrapper.findAll('.recipe-row__chips .recipe-row__fact')).toHaveLength(0);
    });

    it('omits the expiring chip unless the cookbook asked for it', () => {
        const wrapper = mountRow(
            recipeOf({ expiring_ingredient_count: 3 } as Partial<Recipe>),
            false,
        );
        expect(wrapper.findComponent({ name: 'ExpiringChip' }).exists()).toBe(false);
    });

    it('places the expiring chip after the spacer, with the action buttons', () => {
        const wrapper = mountRow(
            recipeOf({
                expiring_ingredient_count: 3,
                expiring_soonest_date: '2026-08-21',
            } as Partial<Recipe>),
            true,
        );

        expect(wrapper.findComponent({ name: 'ExpiringChip' }).exists()).toBe(true);

        // The positional contract. It must NOT be inside `.recipe-row__chips` —
        // that left-hand group's width varies with how many of the other chips
        // (time, count, kcal, hunch) a given recipe has, which is exactly why
        // the one sometimes-present chip never landed in the same place twice.
        expect(wrapper.find('.recipe-row__chips .recipe-row__expiring').exists())
            .toBe(false);

        // …and it must sit after the spacer, i.e. in the right-hand cluster.
        const kids = [...wrapper.find('.recipe-row__body').element.children];
        const spacerIndex = kids.findIndex((el) => el.classList.contains('q-space'));
        const chipIndex = kids.findIndex(
            (el) => el.classList.contains('recipe-row__expiring'),
        );
        expect(spacerIndex).toBeGreaterThanOrEqual(0);
        expect(chipIndex).toBeGreaterThan(spacerIndex);
    });
});
