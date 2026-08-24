// @vitest-environment jsdom
/**
 * B6 (`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`) — `primeBuyVerdicts` seeds the
 * verdict cache from one bulk response so a list of rows stops fetching one
 * verdict per row.
 *
 * Worth an automated test rather than a browser walk: the whole behaviour is
 * "how many requests were made", which is invisible on screen — a regression
 * here looks exactly like success, just slower. The load-bearing case is the
 * mid-flight one: a badge mounting *while* the bulk request is open must wait
 * on it rather than start its own, which is why the priming marks its entries
 * in-flight up front.
 */
import { flushPromises } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
    clearBuyVerdictCache, primeBuyVerdicts, useBuyVerdict,
} from 'src/composables/useBuyVerdict';
import type { BuyVerdict } from 'src/services/api/buyVerdictApiService';

const m = vi.hoisted(() => ({ getAsync: vi.fn() }));

vi.mock('src/services/api/buyVerdictApiService', () => ({
    default: class {
        getAsync = m.getAsync;
    },
}));
// The composable gates its fetches on the per-user display preference (D-12);
// on, so the fetch path is live and a stray request would show up.
vi.mock('src/composables/useBuyVerdictEnabled', async () => {
    const { computed } = await import('vue');
    return {
        useBuyVerdictEnabled: () => ({ buyVerdictEnabled: computed(() => true) }),
    };
});


function verdictFor(name: string): BuyVerdict {
    return {
        verdict: 'buy',
        confidence: 'high',
        strength: 3,
        reasons: [{ axis: 'need', signal: 'out_of_stock', label: name }],
        one_tap_action: { kind: 'add_to_list', label: 'Add to primary list' },
        data_used: {
            price_samples: 0,
            price_average: null,
            price_last: null,
            price_last_at: null,
            days_since_last_purchase: null,
            average_days_between_purchase: null,
            waste_events_last_12mo: 0,
            purchases_last_12mo: 0,
            stock_level_band: 'out',
        },
        wait_hint: null,
    };
}

/** A fetcher whose promise this test resolves by hand, so "mid-flight" is a
 *  real state rather than a timing guess. */
function deferredFetcher() {
    let release!: (value: Record<string, BuyVerdict>) => void;
    let fail!: (err: Error) => void;
    const promise = new Promise<Record<string, BuyVerdict>>((resolve, reject) => {
        release = resolve;
        fail = reject;
    });
    const fetcher = vi.fn(() => promise);
    return { fetcher, release, fail };
}

beforeEach(() => {
    clearBuyVerdictCache();
    m.getAsync.mockReset();
    m.getAsync.mockResolvedValue(verdictFor('per-item'));
});


describe('primeBuyVerdicts', () => {
    it('serves consumers from the bulk response without a per-item request', async () => {
        await primeBuyVerdicts(['a', 'b'], () => Promise.resolve({
            a: verdictFor('a'),
            b: verdictFor('b'),
        }));

        const a = useBuyVerdict('a');
        const b = useBuyVerdict('b');

        expect(a.verdict.value?.reasons[0]?.label).toBe('a');
        expect(b.verdict.value?.reasons[0]?.label).toBe('b');
        expect(m.getAsync).not.toHaveBeenCalled();
    });

    it('makes a consumer that mounts mid-flight wait on the bulk request', async () => {
        const { fetcher, release } = deferredFetcher();
        const priming = primeBuyVerdicts(['a'], fetcher);

        // This is the row painting while the bulk call is still open.
        const a = useBuyVerdict('a');
        expect(m.getAsync).not.toHaveBeenCalled();
        expect(a.loading.value).toBe(true);

        release({ a: verdictFor('a') });
        await priming;

        expect(a.verdict.value?.reasons[0]?.label).toBe('a');
        expect(a.loading.value).toBe(false);
        expect(m.getAsync).not.toHaveBeenCalled();
        expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('leaves an id the response omitted empty rather than guessing', async () => {
        await primeBuyVerdicts(['a', 'missing'], () => Promise.resolve({ a: verdictFor('a') }));
        // A line whose item the server had nothing to say about: the badge hides.
        expect(useBuyVerdict('missing').verdict.value).toBeNull();
    });

    it('deduplicates ids and asks once', async () => {
        const fetcher = vi.fn(() => Promise.resolve({ a: verdictFor('a') }));
        await primeBuyVerdicts(['a', 'a', 'a'], fetcher);
        expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('does not call the fetcher at all for an empty list', async () => {
        const fetcher = vi.fn(() => Promise.resolve({}));
        await primeBuyVerdicts([], fetcher);
        expect(fetcher).not.toHaveBeenCalled();
    });

    it('recovers from a failed bulk fetch instead of wedging the entries', async () => {
        const { fetcher, fail } = deferredFetcher();
        const priming = primeBuyVerdicts(['a'], fetcher);
        fail(new Error('bulk exploded'));
        await priming;

        // The entry is left empty and no longer holds a dead in-flight promise,
        // so the next consumer transparently falls back to asking for itself —
        // a failed prefetch costs a round-trip, not the badge.
        const a = useBuyVerdict('a');
        expect(m.getAsync).toHaveBeenCalledWith('a');
        await flushPromises();
        expect(a.verdict.value?.reasons[0]?.label).toBe('per-item');
        expect(a.loading.value).toBe(false);
    });
});
