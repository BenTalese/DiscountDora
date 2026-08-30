// @vitest-environment jsdom
/**
 * FU-520 component layer — ShoppingListRailItem.
 *
 * One row of the shopping-lists rail (UX-v2 §3.1): status icon, the
 * server-resolved display name, the "next up" marker and the effective-date
 * caption. Quasar chrome mounts for real (pattern from stockLevelDot /
 * addToListButton specs).
 *
 * The four copy/delete kebab cases were deleted on 2026-08-28 along with the
 * kebab itself — both actions were already reachable from the list you're
 * looking at, and copy went entirely in favour of Save as template.
 */
import { mount } from '@vue/test-utils';
import {
    QBadge, QIcon, QItem, QItemLabel, QItemSection, QList, Quasar,
} from 'quasar';
import type { ShoppingListSummary } from 'src/models/shoppingList';
import { describe, expect, it } from 'vitest';

import ShoppingListRailItem from 'src/components/shoppingList/ShoppingListRailItem.vue';

function summaryOf(overrides: Partial<ShoppingListSummary> = {}): ShoppingListSummary {
    return {
        shopping_list_id: 'L1',
        name: null,
        display_name: 'Weekly shop',
        status: 'shopping',
        created_at: '2026-07-01T00:00:00Z',
        completed_at: null,
        planned_shop_date: null,
        effective_date: '2026-07-10',
        is_next_up: false,
        line_count: 5,
        ticked_count: 2,
        ...overrides,
    };
}

function mountRow(summary: ShoppingListSummary, active = false) {
    return mount(ShoppingListRailItem, {
        props: { summary, active },
        global: {
            plugins: [Quasar],
            components: { QItem, QItemSection, QItemLabel, QIcon, QBadge, QList },
        },
    });
}

describe('ShoppingListRailItem', () => {
    it('renders the display name and the ticked-count caption', () => {
        const wrapper = mountRow(summaryOf());

        expect(wrapper.text()).toContain('Weekly shop');
        expect(wrapper.text()).toContain('2/5 ticked');
    });

    it('shows a plain item count on a draft, not a ticked ratio', () => {
        // A draft can no longer hold ticks (2026-08-28), so "0/5 ticked" there
        // was a progress reading that could only ever say zero.
        const wrapper = mountRow(summaryOf({ status: 'draft', line_count: 5, ticked_count: 0 }));

        expect(wrapper.text()).toContain('5 items');
        expect(wrapper.text()).not.toContain('ticked');
    });

    it('singularises the draft item count', () => {
        const wrapper = mountRow(summaryOf({ status: 'draft', line_count: 1, ticked_count: 0 }));

        expect(wrapper.text()).toContain('1 item');
        expect(wrapper.text()).not.toContain('1 items');
    });

    it('shows the "next up" badge only when flagged', () => {
        expect(mountRow(summaryOf({ is_next_up: false })).text()).not.toContain('next up');
        expect(mountRow(summaryOf({ is_next_up: true })).text()).toContain('next up');
    });

    it('colours the status icon by status (shopping → positive)', () => {
        const icon = mountRow(summaryOf({ status: 'shopping' })).find('.q-icon');
        expect(icon.classes()).toContain('text-positive');
    });

    it('mutes the status icon and dims the row when done', () => {
        const wrapper = mountRow(summaryOf({ status: 'done' }));
        // R-002: done is the neutral state — no palette colour, muted text.
        expect(wrapper.find('.q-icon').classes()).toContain('dora-text-muted');
        expect(wrapper.find('.q-item').classes()).toContain('sl-rail-item-done');
    });

    it('emits select when the row is clicked', async () => {
        const wrapper = mountRow(summaryOf());

        await wrapper.find('.q-item').trigger('click');

        expect(wrapper.emitted('select')).toHaveLength(1);
    });
});
