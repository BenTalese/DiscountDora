// @vitest-environment jsdom
/**
 * DiscountChip — the one "% off" badge (FU-885 / feedback PH-6).
 *
 * Worth pinning because it replaced FOUR implementations that had quietly
 * drifted apart: two rendered red, one green, one was a smaller size, and
 * their "is there a discount?" guards disagreed at the edges. Those edges are
 * what this file is mostly about — a badge that appears when `price_was`
 * equals `price_now`, or when the "was" price is lower, is worse than no badge
 * at all, because it advertises a saving that doesn't exist.
 */
import { mount } from '@vue/test-utils';
import { QBadge, Quasar } from 'quasar';
import { describe, expect, it } from 'vitest';

import DiscountChip from 'src/components/chips/DiscountChip.vue';

function mountChip(props: Record<string, unknown>) {
    return mount(DiscountChip, {
        props,
        global: { plugins: [Quasar], components: { QBadge } },
    });
}

describe('DiscountChip — when it appears', () => {
    it('renders the rounded percentage off', () => {
        const wrapper = mountChip({ priceNow: 3, priceWas: 4 });

        expect(wrapper.text()).toBe('25% off');
    });

    it('rounds to the nearest whole percent', () => {
        // 2.99 off 3.99 is 25.06…% — a badge reading "25.06% off" would be
        // noise, and two surfaces rounding differently is how this drifted.
        const wrapper = mountChip({ priceNow: 2.99, priceWas: 3.99 });

        expect(wrapper.text()).toBe('25% off');
    });

    it('renders nothing when the prices are equal', () => {
        const wrapper = mountChip({ priceNow: 4, priceWas: 4 });

        expect(wrapper.text()).toBe('');
    });

    it('renders nothing when the "was" price is lower than now', () => {
        // A price rise is not a discount. One of the old copies compared
        // loosely enough to badge this.
        const wrapper = mountChip({ priceNow: 5, priceWas: 4 });

        expect(wrapper.text()).toBe('');
    });

    it('renders nothing when either price is missing', () => {
        expect(mountChip({ priceNow: 3, priceWas: null }).text()).toBe('');
        expect(mountChip({ priceNow: null, priceWas: 4 }).text()).toBe('');
        expect(mountChip({}).text()).toBe('');
    });

    it('renders nothing when the "was" price is zero', () => {
        // Guards the division, and a $0 "was" is bad data rather than a 100%
        // saving.
        expect(mountChip({ priceNow: 0, priceWas: 0 }).text()).toBe('');
    });
});

describe('DiscountChip — a server-supplied percentage', () => {
    it('uses `pct` when given, without needing prices', () => {
        // Price History's series carries a server-computed `deal_pct` and no
        // "was" price; the client must not invent a second answer (R-003).
        const wrapper = mountChip({ pct: 12 });

        expect(wrapper.text()).toBe('12% off');
    });

    it('prefers `pct` over locally derivable prices', () => {
        const wrapper = mountChip({ pct: 40, priceNow: 3, priceWas: 4 });

        expect(wrapper.text()).toBe('40% off');
    });

    it('renders nothing for a zero or negative server percentage', () => {
        expect(mountChip({ pct: 0 }).text()).toBe('');
        expect(mountChip({ pct: -5 }).text()).toBe('');
    });
});

describe('DiscountChip — presentation', () => {
    it('is green, not red', () => {
        // The tie-break that settled the four-way disagreement: D-001 reserves
        // red for escalation (out of stock, destructive, error). A discount is
        // good news, and on the My Products card the old red badge sat beside
        // an amber "out of stock" — exactly inverting the escalation.
        const wrapper = mountChip({ priceNow: 3, priceWas: 4 });

        expect(wrapper.find('.bg-positive').exists()).toBe(true);
        expect(wrapper.find('.bg-negative').exists()).toBe(false);
    });

    it('defaults to the larger size', () => {
        // MP-10 / PH-5 were both "this chip is too small to read".
        const wrapper = mountChip({ priceNow: 3, priceWas: 4 });

        expect(wrapper.find('.discount-chip--md').exists()).toBe(true);
    });

    it('honours the small size when a caller asks for it', () => {
        const wrapper = mountChip({ priceNow: 3, priceWas: 4, size: 'sm' });

        expect(wrapper.find('.discount-chip--sm').exists()).toBe(true);
    });
});
