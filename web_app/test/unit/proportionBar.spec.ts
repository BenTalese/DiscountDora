// @vitest-environment jsdom
/**
 * `ProportionBar` — the two hard cases the shopping list had already solved,
 * now shared with Reports (`REPORTS_PAGE_REVIEW.md` §4.6, chunk 3).
 *
 * Worth pinning because the width maths **moved between components**: it used to
 * live in `StoreSpendCard.vue` and was verified only by looking at a shopping
 * list. It is pure arithmetic over props, so it is cheap and stable to test,
 * which is exactly the bar the lean verification stance sets. The two behaviours
 * that are not obvious from `value / total`:
 *
 *   1. a bucket with items but **no value** must not vanish from a bar whose own
 *      legend still lists it (2026-08-28 owner feedback: *"also allocate space
 *      for 'no store'"*), and
 *   2. the catch-all bucket is drawn as a **hatch**, not a colour, because the
 *      fills either side of it are logo-derived and free to be grey (D-001).
 */
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import ProportionBar, { type ProportionSegment } from 'src/components/ProportionBar.vue';

const global = { stubs: { 'q-tooltip': { template: '<span />' } } };

function widths(segments: ProportionSegment[]): number[] {
    const bar = mount(ProportionBar, { props: { segments }, global });
    return bar.findAll('.proportion-bar__seg')
        .map((el) => parseFloat((el.attributes('style') ?? '').replace(/.*width:\s*([\d.]+)%.*/, '$1')));
}

describe('ProportionBar', () => {
    it('splits two valued buckets in true proportion', () => {
        const [a, b] = widths([
            { key: 'a', value: 75 },
            { key: 'b', value: 25 },
        ]);
        expect(a).toBeCloseTo(75, 5);
        expect(b).toBeCloseTo(25, 5);
    });

    it('gives a valueless bucket a visible floor and still sums to 100%', () => {
        const [a, b, none] = widths([
            { key: 'a', value: 60 },
            { key: 'b', value: 40 },
            { key: '__none__', value: 0, isUnassigned: true },
        ]);
        // The floor is the synthetic part; the two priced buckets keep their
        // honest 60/40 ratio inside what's left.
        expect(none).toBeCloseTo(7, 5);
        expect(a! + b! + none!).toBeCloseTo(100, 5);
        expect(a! / b!).toBeCloseTo(60 / 40, 5);
    });

    it('shows equal presences when nothing anywhere carries a value', () => {
        // Money on, nothing priced yet: there is no proportion to draw, so the
        // bar must not invent a ranking out of something it isn't measuring.
        expect(widths([
            { key: 'a', value: 0 },
            { key: 'b', value: 0 },
            { key: 'c', value: 0 },
        ])).toEqual([100 / 3, 100 / 3, 100 / 3]);
    });

    it('renders nothing at all when there are no buckets', () => {
        const bar = mount(ProportionBar, { props: { segments: [] }, global });
        expect(bar.find('.proportion-bar').exists()).toBe(false);
    });

    it('draws the catch-all as a hatch with no colour of its own', () => {
        const bar = mount(ProportionBar, {
            props: {
                segments: [
                    { key: 'a', value: 10, colour: 'rgb(23, 136, 65)' },
                    { key: '__none__', value: 5, colour: 'rgb(1, 2, 3)', isUnassigned: true },
                ],
            },
            global,
        });
        const [store, none] = bar.findAll('.proportion-bar__seg');
        expect(store!.attributes('style')).toContain('rgb(23, 136, 65)');
        expect(none!.classes()).toContain('proportion-bar__seg--unassigned');
        // Even when a colour is handed in, the unassigned segment refuses it —
        // the hatch is the channel, so it can't be mistaken for a real store.
        expect(none!.attributes('style') ?? '').not.toContain('rgb(1, 2, 3)');
    });
});
