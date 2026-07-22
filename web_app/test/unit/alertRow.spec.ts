// @vitest-environment jsdom
/**
 * FU-520 component layer — AlertRow (C-9.3), the shared row for the bell
 * peek + alerts hub.
 *
 * Regression anchor: 2026-07-09 an UNKNOWN alert kind (backend shipped
 * `meal_reconcile_overdue` before the frontend switch knew it) crashed the
 * bell; the fix is the defensive `?? []` around `actionsFor` so an
 * unmapped kind degrades to a nav-only row. The first block pins exactly
 * that. Mounted with the real Quasar components (QItem/QAvatar/QBtn…),
 * per the stockLevelDot.spec.ts pattern; the component is purely
 * presentational so no module mocks are needed — the real
 * `src/models/alert` helpers run.
 */
import { mount } from '@vue/test-utils';
import { QAvatar, QBtn, QIcon, QItem, QItemLabel, QItemSection, Quasar } from 'quasar';
import type { Alert, AlertKind } from 'src/models/alert';
import { describe, expect, it } from 'vitest';

import AlertRow from 'src/components/AlertRow.vue';
import { kindLabel } from 'src/models/alert';
import { expectAccessible } from './_axe';

// Slotless stub — the snooze/dismiss tooltips would otherwise leak their
// text into the buttons' labels (nothing here asserts tooltip content).
const TooltipStub = { template: '<span class="tooltip-stub" />' };

function alertData(overrides: Partial<Alert>): Alert {
    return {
        alert_id: 'stock:1:expired',
        kind: 'expired',
        severity: 'medium',
        stock_item_id: null,
        stock_item_name: null,
        target_id: null,
        message: 'Something needs attention',
        detail: null,
        related_date: null,
        read: false,
        snoozed_until: null,
        tier: 'actionable',
        ...overrides,
    };
}

function mountRow(
    alertOverrides: Partial<Alert>,
    props: Record<string, unknown> = {},
) {
    return mount(AlertRow, {
        props: { alert: alertData(alertOverrides), ...props },
        global: {
            plugins: [Quasar],
            components: { QAvatar, QBtn, QIcon, QItem, QItemLabel, QItemSection },
            stubs: { QTooltip: TooltipStub },
        },
    });
}

function buttonLabels(wrapper: ReturnType<typeof mountRow>): string[] {
    return wrapper.findAll('button').map((b) => b.text());
}

describe('AlertRow — unknown alert kind degrades safely', () => {
    // A kind string the frontend switch has never heard of, as the backend
    // would ship it ahead of the client.
    const UNKNOWN = 'quantum_pantry_drift' as AlertKind;

    it('mounts without throwing and renders the message', () => {
        const wrapper = mountRow({ kind: UNKNOWN, message: 'New kind of trouble' });

        expect(wrapper.text()).toContain('New kind of trouble');
    });

    it('renders as a nav-only row — no inline action buttons', () => {
        const wrapper = mountRow({ kind: UNKNOWN });

        // Only the standard chrome survives; no kind-specific action.
        expect(buttonLabels(wrapper)).toEqual([
            'View in context',
            'Snooze 7d',
            'Dismiss',
            'Mark read',
        ]);
    });

    it('slim (bell peek) keeps just the read toggle', () => {
        const wrapper = mountRow({ kind: UNKNOWN }, { slim: true });

        expect(buttonLabels(wrapper)).toEqual(['Mark read']);
    });

    it('still emits open on row click', async () => {
        const wrapper = mountRow({ kind: UNKNOWN });

        await wrapper.find('.q-item').trigger('click');

        expect(wrapper.emitted('open')).toHaveLength(1);
    });
});

describe('AlertRow — known nav-only kind (meal_reconcile_overdue)', () => {
    it('renders its own icon and no inline actions', () => {
        const wrapper = mountRow({
            kind: 'meal_reconcile_overdue',
            severity: 'low',
            message: '3 meals to reconcile',
        });

        // ICONS.playlist_add_check for the kind, on the severity avatar.
        expect(wrapper.find('.q-avatar .q-icon').classes())
            .toContain('mdi-playlist-check');
        expect(wrapper.find('.q-avatar').classes()).toContain('bg-severity-low');
        expect(buttonLabels(wrapper)).toEqual([
            'View in context',
            'Snooze 7d',
            'Dismiss',
            'Mark read',
        ]);
    });
});

describe('AlertRow — kind with inline actions (expired)', () => {
    it('renders both expiry actions ahead of the standard chrome', () => {
        const wrapper = mountRow({ kind: 'expired', severity: 'high' });

        expect(buttonLabels(wrapper)).toEqual([
            'Push 7 days',
            'Clear expiry',
            'View in context',
            'Snooze 7d',
            'Dismiss',
            'Mark read',
        ]);
        expect(wrapper.find('.q-avatar').classes())
            .toContain('bg-severity-critical');
    });

    it('slim keeps only the first inline action + read toggle', () => {
        const wrapper = mountRow({ kind: 'expired' }, { slim: true });

        expect(buttonLabels(wrapper)).toEqual(['Push 7 days', 'Mark read']);
    });

    it('clicking an action emits it without also firing open', async () => {
        const wrapper = mountRow({ kind: 'expired' });

        const push = wrapper.findAll('button')
            .find((b) => b.text() === 'Push 7 days')!;
        await push.trigger('click');

        expect(wrapper.emitted('action')).toEqual([['extend_expiry']]);
        // @click.stop on the action bar — the row's open must NOT fire.
        expect(wrapper.emitted('open')).toBeUndefined();
    });

    it('marks the inline action busy while the parent works', () => {
        const wrapper = mountRow({ kind: 'expired' }, { busy: true });

        const push = wrapper.findAll('button')
            .find((b) => b.text().includes('Push 7 days'))!;
        expect(push.find('.q-spinner').exists()).toBe(true);
    });
});

describe('AlertRow — chrome emits and read state', () => {
    it('emits snooze / dismiss / view-in-context from their buttons', async () => {
        const wrapper = mountRow({ kind: 'low_stock' });
        const byLabel = (label: string) =>
            wrapper.findAll('button').find((b) => b.text() === label)!;

        await byLabel('View in context').trigger('click');
        await byLabel('Snooze 7d').trigger('click');
        await byLabel('Dismiss').trigger('click');

        expect(wrapper.emitted('view-in-context')).toHaveLength(1);
        expect(wrapper.emitted('snooze')).toHaveLength(1);
        expect(wrapper.emitted('dismiss')).toHaveLength(1);
    });

    it('unread row: bold message, Mark read emits toggle-read true', async () => {
        const wrapper = mountRow({ kind: 'low_stock', read: false });

        expect(wrapper.find('.q-item').classes()).not.toContain('alert-row--read');
        expect(wrapper.find('.q-item__label').classes())
            .toContain('text-weight-medium');

        const toggle = wrapper.findAll('button')
            .find((b) => b.text() === 'Mark read')!;
        await toggle.trigger('click');
        expect(wrapper.emitted('toggle-read')).toEqual([[true]]);
    });

    it('read row: receded styling, Unread emits toggle-read false', async () => {
        const wrapper = mountRow({ kind: 'low_stock', read: true });

        expect(wrapper.find('.q-item').classes()).toContain('alert-row--read');

        const toggle = wrapper.findAll('button')
            .find((b) => b.text() === 'Unread')!;
        await toggle.trigger('click');
        expect(wrapper.emitted('toggle-read')).toEqual([[false]]);
    });

    it('renders detail and the localised related date in the caption', () => {
        const related = '2026-07-01';
        const wrapper = mountRow({
            kind: 'expiring_soon',
            detail: 'Greek yoghurt',
            related_date: related,
        });

        const caption = wrapper.find('.q-item__label--caption').text();
        expect(caption).toContain('Greek yoghurt');
        expect(caption).toContain(new Date(related).toLocaleDateString());
    });

    // FU-542 — accessibility. AlertRow renders icon-only action buttons
    // (extend expiry / snooze / dismiss), a prime spot for unlabelled
    // controls; axe verifies every control has an accessible name. The row is
    // a `listitem`, so it's scanned inside a `list` wrapper (its real context —
    // both the bell and the hub render it inside a QList).
    it('has no accessibility violations (with inline actions)', async () => {
        const wrapper = mountRow({ kind: 'expired' });
        await expectAccessible(wrapper.element, { wrapRole: 'list' });
    });

    it('has no accessibility violations (unread, read-toggle present)', async () => {
        const wrapper = mountRow({ kind: 'expiring_soon', read: false });
        await expectAccessible(wrapper.element, { wrapRole: 'list' });
    });
});

/**
 * `kindLabel` — the prose label for an alert kind, used by the hub's History
 * rows (which hold the kind as a bare string, since a stored row can outlive
 * its kind). Regression anchor: 2026-07-22 the History caption used a
 * hand-rolled `kind.replace('_', ' ')`, and `String.replace` with a string
 * pattern swaps only the FIRST match — so `out_of_stock` rendered as
 * "out of_stock" while the manage panel, reading the same kind from
 * ALERT_KIND_META, correctly showed "out of stock".
 */
describe('kindLabel', () => {
    it('reads known kinds from the shared meta, not by munging the key', () => {
        expect(kindLabel('out_of_stock')).toBe('out of stock');
        expect(kindLabel('essential_low')).toBe('essential low');
        expect(kindLabel('meal_reconcile_overdue')).toBe('meals to reconcile');
        expect(kindLabel('no_planned_meals')).toBe('meals to plan');
    });

    it('humanises EVERY underscore of an unknown kind, not just the first', () => {
        // A kind retired from the union can still sit in stored history.
        expect(kindLabel('some_retired_kind')).toBe('some retired kind');
    });

    it('never leaves a raw snake_case key on screen', () => {
        const kinds = ['out_of_stock', 'low_stock', 'stocktake_overdue', 'shopping_day', 'a_b_c_d'];
        for (const k of kinds) expect(kindLabel(k)).not.toContain('_');
    });
});
