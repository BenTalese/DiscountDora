// @vitest-environment jsdom
/**
 * Owner feedback 2026-08-27 — `AddToListDialog` is now the *only* bulk
 * add-to-a-list surface (recipes, the recipe overview, and the meal planner all
 * render it). Its default tick policy is the thing the owner reported twice —
 * "items already on a list should be unticked already" — so that rule, and the
 * bulk buttons that could quietly re-propose those items, are pinned here.
 *
 * Mocking sits at the store boundary, as in `addToListButton.spec.ts`. The real
 * `cartStateFor` runs, so membership fixtures exercise the model too.
 */
import { flushPromises, mount } from '@vue/test-utils';
import {
    QCard, QCardSection, QCheckbox, QChip, QIcon, QInput, QItem, QItemLabel,
    QItemSection, QList, QSelect, QSeparator, QSpace, Quasar,
} from 'quasar';
import type { Membership } from 'src/models/shoppingList';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AddToListDialog from 'src/components/shoppingList/AddToListDialog.vue';
import type { AddToListRow } from 'src/components/shoppingList/addToListTypes';

const m = vi.hoisted(() => ({
    state: {
        membership: null as Membership | null,
        summaries: [] as Array<{ shopping_list_id: string; display_name: string; status: string }>,
        quickAddTargetListId: null as string | null,
    },
}));

vi.mock('src/stores/shoppingListStore', async () => {
    const { computed, reactive } = await import('vue');
    return {
        useShoppingListStore: () => reactive({
            membership: computed(() => m.state.membership),
            summaries: computed(() => m.state.summaries),
            quickAddTargetListId: computed(() => m.state.quickAddTargetListId),
        }),
    };
});
// Level resolution belongs to the stock stores; the dialog only forwards ids.
vi.mock('src/composables/useStockStatus', () => ({
    useStockStatus: () => ({
        levelSequenceForItem: () => null,
        stockStatusLabel: () => 'Not tracked',
        stockStatusColour: () => null,
        needsBuying: () => true,
        isMissing: () => true,
        isLowStock: () => false,
    }),
}));

function row(over: Partial<AddToListRow> = {}): AddToListRow {
    return {
        stockItemId: 'si-1',
        name: 'Flour',
        isMissing: true,
        isLowStock: false,
        isOptional: false,
        quantityLabel: null,
        sources: [],
        ...over,
    };
}

function membershipWith(stockItemIds: string[]): Membership {
    return {
        quick_add_target_list_id: 'list-1',
        items: stockItemIds.map((id) => ({
            stock_item_id: id,
            unticked_list_ids: ['list-1'],
            on_quick_add_target: true,
        })),
        active_lists: [
            { shopping_list_id: 'list-1', name: 'Weekly shop', status: 'draft' },
        ],
    } as unknown as Membership;
}

// QDialog teleports its card out of the component tree, which would put every
// row beyond the wrapper's reach. Stubbing only the chrome keeps the rows,
// checkboxes and action buttons — the things under test — mounted for real.
const BaseDialogStub = {
    name: 'BaseDialog',
    props: ['modelValue', 'title', 'closable', 'cardStyle'],
    template: '<div><slot /><div class="stub-actions"><slot name="actions" /></div></div>',
};

async function mountDialog(props: Record<string, unknown>) {
    const wrapper = mount(AddToListDialog, {
        props: { modelValue: true, rows: [], ...props },
        global: {
            plugins: [Quasar],
            components: {
                QCard, QCardSection, QCheckbox, QChip, QIcon, QInput, QItem,
                QItemLabel, QItemSection, QList, QSelect, QSeparator, QSpace,
            },
            stubs: { BaseDialog: BaseDialogStub, QTooltip: true },
        },
    });
    await flushPromises();
    return wrapper;
}

/** The checkbox states, in render order. */
function ticks(wrapper: ReturnType<typeof mount>): boolean[] {
    return wrapper.findAllComponents(QCheckbox).map((c) => c.props('modelValue') as boolean);
}

beforeEach(() => {
    m.state.membership = null;
    m.state.summaries = [
        { shopping_list_id: 'list-1', display_name: 'Weekly shop', status: 'draft' },
    ];
    m.state.quickAddTargetListId = null;
});

describe('AddToListDialog — default tick policy', () => {
    it('ticks a missing item that is not on any list', async () => {
        const wrapper = await mountDialog({ rows: [row()] });

        expect(ticks(wrapper)).toEqual([true]);
    });

    it('leaves an item that is already on a list unticked', async () => {
        // The reported bug: "add all missing" proposed adding things the user
        // had already added.
        m.state.membership = membershipWith(['si-1']);

        const wrapper = await mountDialog({ rows: [row()] });

        expect(ticks(wrapper)).toEqual([false]);
    });

    it('leaves an optional item unticked even when it is missing', async () => {
        const wrapper = await mountDialog({ rows: [row({ isOptional: true })] });

        expect(ticks(wrapper)).toEqual([false]);
    });

    it('leaves a well-stocked item unticked', async () => {
        const wrapper = await mountDialog({
            rows: [row({ isMissing: false, isLowStock: false })],
        });

        expect(ticks(wrapper)).toEqual([false]);
    });

    it('honours initialCheckedIds — but still not for an item already on a list', async () => {
        m.state.membership = membershipWith(['si-2']);

        const wrapper = await mountDialog({
            rows: [row(), row({ stockItemId: 'si-2', name: 'Sugar' })],
            initialCheckedIds: ['si-1', 'si-2'],
        });

        expect(ticks(wrapper)).toEqual([true, false]);
    });

    it('re-applies the policy when rows arrive after the dialog opened', async () => {
        // The meal-plan aggregate is fetched, so an open dialog can be handed
        // its rows a moment later; without this it would sit fully unticked.
        const wrapper = await mountDialog({ rows: [] });
        await wrapper.setProps({ rows: [row()] });
        await flushPromises();

        expect(ticks(wrapper)).toEqual([true]);
    });
});

describe('AddToListDialog — bulk selection', () => {
    it('"Select all" skips items already on a list and optional ones', async () => {
        m.state.membership = membershipWith(['si-2']);
        const wrapper = await mountDialog({
            rows: [
                row({ isMissing: false }),
                row({ stockItemId: 'si-2', name: 'Sugar', isMissing: false }),
                row({ stockItemId: 'si-3', name: 'Nutmeg', isOptional: true }),
            ],
        });

        await wrapper.findAllComponents({ name: 'BaseButton' })
            .find((b) => b.props('label') === 'Select all')!
            .trigger('click');
        await flushPromises();

        // Optional rows render last, under their separator.
        expect(ticks(wrapper)).toEqual([true, false, false]);
    });

    it('"Select missing" ticks missing and low rows only', async () => {
        const wrapper = await mountDialog({
            rows: [
                row({ isMissing: true }),
                row({ stockItemId: 'si-2', name: 'Sugar', isMissing: false, isLowStock: true }),
                row({ stockItemId: 'si-3', name: 'Salt', isMissing: false, isLowStock: false }),
            ],
        });

        await wrapper.findAllComponents({ name: 'BaseButton' })
            .find((b) => b.props('label') === 'Select missing')!
            .trigger('click');
        await flushPromises();

        expect(ticks(wrapper)).toEqual([true, true, false]);
    });
});

describe('AddToListDialog — confirm payload', () => {
    it('emits the ticked ids and the chosen list', async () => {
        const wrapper = await mountDialog({ rows: [row()] });

        await wrapper.findAllComponents({ name: 'BaseButton' })
            .find((b) => b.props('label') === 'Add')!
            .trigger('click');

        expect(wrapper.emitted('confirm')?.[0]?.[0]).toEqual({
            stockItemIds: ['si-1'],
            targetListId: 'list-1',
        });
    });

    it('reports a null target for "+ New list" so the caller creates it', async () => {
        // No open lists at all — the old flow dead-ended here with a "go make
        // a list first" bounce.
        m.state.summaries = [];
        const wrapper = await mountDialog({
            rows: [row()],
            defaultNewListName: 'Meals: week of 25 Aug',
        });

        await wrapper.findAllComponents({ name: 'BaseButton' })
            .find((b) => b.props('label') === 'Add')!
            .trigger('click');

        expect(wrapper.emitted('confirm')?.[0]?.[0]).toEqual({
            stockItemIds: ['si-1'],
            targetListId: null,
        });
        expect(wrapper.vm.newListName).toBe('Meals: week of 25 Aug');
    });
});
