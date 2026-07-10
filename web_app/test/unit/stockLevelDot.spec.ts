// @vitest-environment jsdom
/**
 * FU-520 workstream 1, component layer — the two StockLevelDot components.
 *
 * - `components/StockLevelDot.vue` — the UX-v2 stock-level signal (dot +
 *   short label + alert state + tooltip). Mounted with the real Quasar
 *   plugin (QIcon renders as a real component) and a fresh Pinia; the
 *   level is driven through `stock_item.stock_level_sequence`, which the
 *   component prefers over the store lookup. QTooltip is stubbed with a
 *   passthrough so its slot content is assertable without activation.
 * - `components/stock/StockLevelDot.vue` — the simple level-dot avatar
 *   shared by the three stock-level pickers (R-001).
 *
 * Determinism: the expiring-soon computation reads `Date.now()`, so every
 * expiry test pins the clock with vi.setSystemTime.
 */
import { mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { QAvatar, QIcon, Quasar } from 'quasar';
import type { StockItem } from 'src/models/stockItem';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DotAvatar from 'src/components/stock/StockLevelDot.vue';
import StockLevelDot from 'src/components/StockLevelDot.vue';

const TooltipStub = { template: '<div class="tooltip-stub"><slot /></div>' };

// The app build auto-registers Quasar components via its vite plugin;
// under plain @vitejs/plugin-vue the template's <q-icon>/<q-avatar> stay
// unresolved, so the real components are registered explicitly here.
function mountDot(stockItem: Partial<StockItem> | null) {
    return mount(StockLevelDot, {
        props: { stockItem: stockItem as StockItem | null },
        global: {
            plugins: [Quasar, createPinia()],
            components: { QIcon },
            stubs: { QTooltip: TooltipStub },
        },
    });
}

function item(overrides: Partial<StockItem>): Partial<StockItem> {
    return {
        stock_item_id: '00000000-0000-0000-0000-000000000001',
        name: 'Test item',
        needs_restock: false,
        is_flagged: false,
        ...overrides,
    };
}

afterEach(() => {
    vi.useRealTimers();
});

describe('StockLevelDot (UX-v2 signal)', () => {
    it('renders a calm positive dot with an OK label when stocked', () => {
        const wrapper = mountDot(item({ stock_level_sequence: 0 }));

        const icon = wrapper.find('.q-icon');
        expect(icon.classes()).toContain('text-positive');
        expect(icon.attributes('style')).toContain('font-size: 9px');
        expect(wrapper.find('.text-caption').text()).toBe('OK');
        expect(wrapper.find('.text-caption').classes()).toContain('dora-text-muted');
    });

    it('escalates to the enlarged negative alert dot when low', () => {
        const wrapper = mountDot(
            item({ stock_level_sequence: 1, needs_restock: true }),
        );

        const icon = wrapper.find('.q-icon');
        expect(icon.classes()).toContain('text-negative');
        expect(icon.attributes('style')).toContain('font-size: 11px');
        expect(wrapper.find('.text-caption').text()).toBe('Low');
        expect(wrapper.find('.text-caption').classes()).toContain('text-negative');
    });

    it('labels out-of-stock as Out and alerts', () => {
        const wrapper = mountDot(
            item({ stock_level_sequence: 2, needs_restock: true }),
        );

        expect(wrapper.find('.text-caption').text()).toBe('Out');
        expect(wrapper.find('.q-icon').classes()).toContain('text-negative');
    });

    it('renders no label and a muted dot for an unknown level', () => {
        const wrapper = mountDot(item({}));

        expect(wrapper.find('.text-caption').exists()).toBe(false);
        expect(wrapper.find('.q-icon').classes()).toContain('dora-text-muted');
    });

    it('alerts with an Expiring soon tooltip when expiry is inside 7 days', () => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-07-10T12:00:00Z'));

        const wrapper = mountDot(
            item({ stock_level_sequence: 0, expiry_date: '2026-07-13' }),
        );

        expect(wrapper.find('.q-icon').classes()).toContain('text-negative');
        expect(wrapper.find('.tooltip-stub').text()).toContain('Expiring soon');
    });

    it('stays calm when expiry is comfortably in the future', () => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-07-10T12:00:00Z'));

        const wrapper = mountDot(
            item({ stock_level_sequence: 0, expiry_date: '2026-09-01' }),
        );

        expect(wrapper.find('.q-icon').classes()).toContain('text-positive');
        // No alert reasons and no store-resolved level name → the tooltip
        // has nothing to say and isn't rendered at all.
        expect(wrapper.find('.tooltip-stub').exists()).toBe(false);
    });

    it('flags essentials: alert dot + Essential in the tooltip', () => {
        const wrapper = mountDot(
            item({ stock_level_sequence: 0, is_flagged: true }),
        );

        expect(wrapper.find('.q-icon').classes()).toContain('text-negative');
        expect(wrapper.find('.tooltip-stub').text()).toContain('Essential');
    });

    it('renders a bare muted dot for a null item', () => {
        const wrapper = mountDot(null);

        expect(wrapper.find('.q-icon').exists()).toBe(true);
        expect(wrapper.find('.text-caption').exists()).toBe(false);
        expect(wrapper.find('.tooltip-stub').exists()).toBe(false);
    });
});

describe('StockLevelDot (picker avatar)', () => {
    function mountAvatar(props: Record<string, unknown>) {
        return mount(DotAvatar, {
            props: { sequence: null, ...props },
            global: { plugins: [Quasar], components: { QAvatar } },
        });
    }

    it('colours by canonical sequence (stocked → positive, low → negative)', () => {
        expect(mountAvatar({ sequence: 0 }).find('.q-avatar').classes())
            .toContain('bg-positive');
        expect(mountAvatar({ sequence: 1 }).find('.q-avatar').classes())
            .toContain('bg-negative');
    });

    it('falls back to the sunken neutral for out-of-stock and unknown', () => {
        // Out-of-stock deliberately maps to no palette colour.
        expect(mountAvatar({ sequence: 2 }).find('.q-avatar').classes())
            .toContain('dora-bg-neutral');
        expect(mountAvatar({ sequence: null }).find('.q-avatar').classes())
            .toContain('dora-bg-neutral');
    });

    it('passes size and extra classes through', () => {
        const avatar = mountAvatar({ sequence: 0, size: '24px', dotClass: 'q-mr-sm' })
            .find('.q-avatar');

        expect(avatar.attributes('style')).toContain('font-size: 24px');
        expect(avatar.classes()).toContain('q-mr-sm');
    });
});
