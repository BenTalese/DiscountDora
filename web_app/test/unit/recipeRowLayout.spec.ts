// @vitest-environment jsdom
/**
 * Compact cookbook row layout — the two structural changes from the owner's
 * 2026-08-19 feedback:
 *
 *   - "Remove the second info line under the recipe name in compact view,
 *      looks too cluttered."
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
    it('renders the recipe name and no second info line', () => {
        const wrapper = mountRow(recipeOf());

        expect(wrapper.find('.recipe-row__name').text()).toBe('Lasagne');
        expect(wrapper.find('.recipe-row__meta').exists()).toBe(false);
    });

    it('keeps the name zone to a single child, so nothing re-grows under it', () => {
        // Guards the shape rather than one class name: the clutter complaint was
        // about a *second line*, whatever it ends up being called.
        const zone = mountRow(recipeOf()).find('.recipe-row__name-zone');
        expect(zone.element.children).toHaveLength(1);
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
