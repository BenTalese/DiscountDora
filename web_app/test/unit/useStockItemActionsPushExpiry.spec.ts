// @vitest-environment jsdom
/**
 * FU-123 — pushExpiry's date semantics (verify-campaign Batch 3, Stock
 * Overview Chunk 4). The "+N days" expiry push works from
 * `max(today, current expiry)`:
 *   * a FUTURE expiry pushes from that expiry (+1 on "in 5 days" = in 6),
 *   * a PAST expiry pushes from today (+1 never lands in the past),
 *   * no expiry at all falls back to today + N,
 *   * an unparseable stored date degrades to today + N.
 * The composable needs a component context (Quasar, router, stores) — all
 * mocked at the module boundary; the date math + the PATCH payload are the
 * behaviour under test.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const h = vi.hoisted(() => ({
    notify: vi.fn(),
    updateStockItemAsync: vi.fn(),
    stockItems: [] as { stock_item_id: string; expiry_date: string | null }[],
}));

vi.mock('quasar', () => ({ useQuasar: () => ({ notify: h.notify }) }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }));
// storeToRefs is only used to pluck refs off the level/auth stores; the
// fakes below already hold refs, so identity is a faithful stand-in.
vi.mock('pinia', () => ({ storeToRefs: (s: unknown) => s }));
vi.mock('src/stores/stockItemStore', () => ({
    useStockItemStore: () => ({
        stockItems: h.stockItems,
        updateStockItemAsync: h.updateStockItemAsync,
    }),
}));
vi.mock('src/stores/shoppingListStore', () => ({
    useShoppingListStore: () => ({ summaries: [] }),
}));
vi.mock('src/stores/stockLevelStore', () => ({
    useStockLevelStore: () => ({ stockLevels: ref([]) }),
}));
vi.mock('src/stores/authStore', () => ({
    useAuthStore: () => ({ currentUser: ref(null) }),
}));
vi.mock('src/composables/useBuyVerdict', () => ({ invalidateBuyVerdict: vi.fn() }));
vi.mock('src/composables/useQuickAddTargetPick', () => ({
    useQuickAddTargetPick: () => ({}),
}));
vi.mock('src/services/api/shoppingListApiService', () => ({ default: class {} }));

import { useStockItemActions } from 'src/composables/useStockItemActions';

const ID = 'item-1';

function withExpiry(expiry: string | null) {
    h.stockItems.length = 0;
    h.stockItems.push({ stock_item_id: ID, expiry_date: expiry });
}

async function pushedIso(days: number): Promise<string> {
    await useStockItemActions().pushExpiry(ID, days);
    expect(h.updateStockItemAsync).toHaveBeenCalledTimes(1);
    const call = h.updateStockItemAsync.mock.calls[0]![0] as {
        stock_item_id: string; expiry_date: string;
    };
    expect(call.stock_item_id).toBe(ID);
    return call.expiry_date;
}

describe('pushExpiry — FU-123 max(today, current) + N', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-07-18T10:00:00'));
        h.notify.mockClear();
        h.updateStockItemAsync.mockClear().mockResolvedValue(undefined);
    });
    afterEach(() => {
        vi.useRealTimers();
    });

    it('a future expiry pushes from that expiry, not from today', async () => {
        withExpiry('2026-07-23');                       // in 5 days
        expect(await pushedIso(1)).toBe('2026-07-24');  // +1 on the expiry
    });

    it('a future expiry +7 lands exactly a week past the expiry', async () => {
        withExpiry('2026-07-23');
        expect(await pushedIso(7)).toBe('2026-07-30');
    });

    it('a past expiry pushes from today — "+1 day" is tomorrow, never yesterday', async () => {
        withExpiry('2026-07-01');                       // long stale
        expect(await pushedIso(1)).toBe('2026-07-19');
    });

    it('no expiry set falls back to today + N', async () => {
        withExpiry(null);
        expect(await pushedIso(7)).toBe('2026-07-25');
    });

    it('an unparseable stored date degrades to today + N', async () => {
        withExpiry('not-a-date');
        expect(await pushedIso(14)).toBe('2026-08-01');
    });

    it('a same-day expiry pushes from it (tie goes to the expiry, same result as today)', async () => {
        withExpiry('2026-07-18');
        expect(await pushedIso(1)).toBe('2026-07-19');
    });

    it('confirms the push with a toast naming the new date', async () => {
        withExpiry(null);
        await useStockItemActions().pushExpiry(ID, 1);
        expect(h.notify).toHaveBeenCalledWith(
            expect.objectContaining({ type: 'positive', message: 'Expiry pushed to 2026-07-19.' }),
        );
    });

    it('a failed PATCH surfaces the error toast instead of throwing', async () => {
        withExpiry(null);
        h.updateStockItemAsync.mockRejectedValue(new Error('offline'));
        await useStockItemActions().pushExpiry(ID, 1);
        expect(h.notify).toHaveBeenCalledWith(
            expect.objectContaining({ type: 'negative', message: 'Could not update expiry.' }),
        );
    });
});
