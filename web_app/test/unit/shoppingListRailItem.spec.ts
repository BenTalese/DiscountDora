// @vitest-environment jsdom
/**
 * FU-520 component layer — ShoppingListRailItem.
 *
 * One row of the shopping-lists rail (UX-v2 §3.1): status icon, the
 * server-resolved display name, the "next up" marker, the effective-date
 * caption, and the copy/delete kebab. Quasar chrome mounts for real
 * (pattern from stockLevelDot / addToListButton specs); `BaseButton` and
 * `QMenu` are stubbed to render their slots inline so the kebab actions
 * are in the DOM without driving a real popover open.
 */
import { mount } from '@vue/test-utils';
import {
    QBadge, QIcon, QItem, QItemLabel, QItemSection, QList, Quasar,
} from 'quasar';
import type { ShoppingListSummary } from 'src/models/shoppingList';
import { describe, expect, it } from 'vitest';

import type { VueWrapper } from '@vue/test-utils';
import ShoppingListRailItem from 'src/components/shoppingList/ShoppingListRailItem.vue';

const SlotStub = { template: '<div class="slot-stub"><slot /></div>' };

/** The root row is itself a `.q-item` that wraps the kebab menu, so its
 *  text contains every menu label — scope lookups to the menu `.q-list`. */
function menuItem(wrapper: VueWrapper, label: string) {
    return wrapper.find('.q-list').findAll('.q-item')
        .find((i) => i.text().includes(label));
}

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
            stubs: { BaseButton: SlotStub, QMenu: SlotStub },
        },
    });
}

describe('ShoppingListRailItem', () => {
    it('renders the display name and the ticked-count caption', () => {
        const wrapper = mountRow(summaryOf());

        expect(wrapper.text()).toContain('Weekly shop');
        expect(wrapper.text()).toContain('2/5 ticked');
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

    it('offers "copy unticked" on an active list and emits with "unticked"', async () => {
        const wrapper = mountRow(summaryOf({ status: 'shopping', line_count: 5, ticked_count: 2 }));

        const copyItem = menuItem(wrapper, 'Copy unticked');
        expect(copyItem).toBeTruthy();

        await copyItem!.trigger('click');
        expect(wrapper.emitted('copy')?.[0]).toEqual(['unticked']);
    });

    it('disables "copy unticked" when everything is ticked', () => {
        const wrapper = mountRow(summaryOf({ status: 'shopping', line_count: 5, ticked_count: 5 }));

        expect(menuItem(wrapper, 'Copy unticked')!.classes()).toContain('disabled');
    });

    it('offers "copy all" on a done list and emits with "all"', async () => {
        const wrapper = mountRow(summaryOf({ status: 'done' }));

        const copyItem = menuItem(wrapper, 'Copy to new list');
        expect(copyItem).toBeTruthy();

        await copyItem!.trigger('click');
        expect(wrapper.emitted('copy')?.[0]).toEqual(['all']);
    });

    it('emits delete from the kebab', async () => {
        const wrapper = mountRow(summaryOf());

        await menuItem(wrapper, 'Delete list')!.trigger('click');
        expect(wrapper.emitted('delete')).toHaveLength(1);
    });
});
