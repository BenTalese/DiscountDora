// @vitest-environment jsdom
/**
 * AlertRow, the one alert row (the bell is the only alerts surface since
 * 2026-10-15).
 *
 * Two rows of buttons: the top acts on the thing the alert is about, the
 * bottom on the alert itself (snooze / dismiss). There is no read state.
 *
 * Regression anchor: 2026-07-09 an UNKNOWN alert kind (backend shipped
 * `meal_reconcile_overdue` before the frontend knew it) crashed the bell; an
 * unmapped kind must degrade to a row with only the alert's own buttons.
 */
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { QAvatar, QBtn, QIcon, QItem, QItemLabel, QItemSection, Quasar } from 'quasar';
import type { Alert, AlertKind } from 'src/models/alert';
import { beforeEach, describe, expect, it } from 'vitest';

import AlertRow from 'src/components/AlertRow.vue';
import { expectAccessible } from './_axe';

// Slotless stubs: tooltips would leak their text into button labels, and the
// stock controls are covered by their own specs.
const TooltipStub = { template: '<span class="tooltip-stub" />' };
const LevelPickerStub = { template: '<button class="level-picker-stub" aria-label="Change level">Level</button>' };
const CartStub = { template: '<button class="cart-stub" aria-label="Add to list">Cart</button>' };

function alertData(overrides: Partial<Alert>): Alert {
    return {
        alert_id: 'stock:1:expired:2026-07-01',
        kind: 'expired',
        severity: 'medium',
        stock_item_id: null,
        stock_item_name: null,
        target_id: null,
        message: 'Something needs attention',
        detail: null,
        related_date: null,
        started_on: null,
        amount: null,
        snoozed_until: null,
        tier: 'actionable',
        ...overrides,
    };
}

function mountRow(alertOverrides: Partial<Alert>, props: Record<string, unknown> = {}) {
    return mount(AlertRow, {
        props: { alert: alertData(alertOverrides), ...props },
        global: {
            plugins: [Quasar],
            components: { QAvatar, QBtn, QIcon, QItem, QItemLabel, QItemSection },
            stubs: {
                QTooltip: TooltipStub,
                StockLevelPicker: LevelPickerStub,
                AddToListButton: CartStub,
            },
        },
    });
}

function buttonLabels(wrapper: ReturnType<typeof mountRow>): string[] {
    return wrapper.findAll('button').map((b) => b.text());
}

beforeEach(() => {
    setActivePinia(createPinia());
});

describe('AlertRow, unknown alert kind degrades safely', () => {
    const UNKNOWN = 'quantum_pantry_drift' as AlertKind;

    it('mounts and renders only the alert buttons', () => {
        const wrapper = mountRow({ kind: UNKNOWN, message: 'New kind of trouble' });
        expect(wrapper.text()).toContain('New kind of trouble');
        expect(buttonLabels(wrapper)).toEqual(['Snooze 7d', 'Dismiss']);
    });

    it('still emits open on row click', async () => {
        const wrapper = mountRow({ kind: UNKNOWN });
        await wrapper.find('.q-item').trigger('click');
        expect(wrapper.emitted('open')).toHaveLength(1);
    });
});

describe('AlertRow, expiring ingredient', () => {
    it('offers the expiry actions and a jump to recipes using it', () => {
        const wrapper = mountRow({ kind: 'expired', severity: 'high', stock_item_id: 'si-1' });
        expect(buttonLabels(wrapper)).toEqual([
            'Push 7 days', 'Clear expiry', 'Recipes', 'Snooze 7d', 'Dismiss',
        ]);
        expect(wrapper.find('.q-avatar').classes()).toContain('bg-severity-critical');
    });

    it('navigates to the cookbook filtered to the item', async () => {
        const wrapper = mountRow({ kind: 'expiring_soon', stock_item_id: 'si-1' });
        const recipes = wrapper.findAll('button').find((b) => b.text() === 'Recipes')!;
        await recipes.trigger('click');
        expect(wrapper.emitted('navigate')).toEqual([['/cookbook?usesStockItem=si-1']]);
        expect(wrapper.emitted('open')).toBeUndefined();
    });

    it('emits a server action without also opening the row', async () => {
        const wrapper = mountRow({ kind: 'expired', stock_item_id: 'si-1' });
        const push = wrapper.findAll('button').find((b) => b.text() === 'Push 7 days')!;
        await push.trigger('click');
        expect(wrapper.emitted('action')).toEqual([['extend_expiry']]);
        expect(wrapper.emitted('open')).toBeUndefined();
    });
});

describe('AlertRow, essential running low', () => {
    it('offers the level picker and the cart on the top row', () => {
        const wrapper = mountRow({
            kind: 'essential_low', severity: 'high',
            stock_item_id: 'si-2', stock_item_name: 'Milk',
        });
        expect(wrapper.find('.level-picker-stub').exists()).toBe(true);
        expect(wrapper.find('.cart-stub').exists()).toBe(true);
        expect(buttonLabels(wrapper)).not.toContain('Mark restocked');
    });
});

describe('AlertRow, nudges', () => {
    it('a missed shopping day opens its list', async () => {
        const wrapper = mountRow({ kind: 'shopping_overdue', target_id: 'list-9' });
        const open = wrapper.findAll('button').find((b) => b.text() === 'Open list')!;
        await open.trigger('click');
        expect(wrapper.emitted('navigate')).toEqual([['/shopping-lists/list-9']]);
    });

    it('a price drop shows the price it hit', () => {
        const wrapper = mountRow({ kind: 'price_drop', target_id: 'p-1', amount: 3.5, detail: 'At Coles.' });
        const caption = wrapper.find('.q-item__label--caption').text();
        expect(caption).toContain('3.50');
        expect(caption).toContain('At Coles.');
    });
});

describe('AlertRow, the alert row of buttons', () => {
    it('emits snooze and dismiss', async () => {
        const wrapper = mountRow({ kind: 'expiring_soon' });
        const byLabel = (label: string) => wrapper.findAll('button').find((b) => b.text() === label)!;
        await byLabel('Snooze 7d').trigger('click');
        await byLabel('Dismiss').trigger('click');
        expect(wrapper.emitted('snooze')).toHaveLength(1);
        expect(wrapper.emitted('dismiss')).toHaveLength(1);
    });

    it('a snoozed alert offers to unsnooze instead', () => {
        const wrapper = mountRow({ kind: 'expiring_soon', snoozed_until: '2026-07-08T00:00:00Z' });
        expect(buttonLabels(wrapper)).toContain('Unsnooze');
        expect(buttonLabels(wrapper)).not.toContain('Snooze 7d');
    });

    it('has no read toggle', () => {
        const wrapper = mountRow({ kind: 'expiring_soon' });
        expect(buttonLabels(wrapper).some((l) => /read/i.test(l))).toBe(false);
    });

    it('renders detail and the localised related date in the caption', () => {
        const wrapper = mountRow({
            kind: 'expiring_soon',
            detail: 'Greek yoghurt',
            related_date: '2026-07-01',
        });
        const caption = wrapper.find('.q-item__label--caption').text();
        expect(caption).toContain('Greek yoghurt');
        // FU-820: assert the day the string names, not a re-parsed date.
        expect(caption).toContain('01/07/2026');
    });

    it('has no accessibility violations', async () => {
        const wrapper = mountRow({ kind: 'expired', stock_item_id: 'si-1' });
        await expectAccessible(wrapper.element, { wrapRole: 'list' });
    });
});
