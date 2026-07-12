// Store-layer coverage — stockItemStore, the richest client store: sorted
// collection cache, optimistic stock-level swap with rollback registration,
// offline-queue absorption (F3), canonical-row refetch, and the FU-511
// auto-add toast that reaches across into the shopping-list store.
//
// Mock boundary: the API service class, `tryWithQueue`, the shopping-list
// store, `resolveBaseURL`, and Quasar's Notify. The rollback registry is
// deliberately REAL — the optimistic-rollback contract (register → stale
// until the global error handler fires executeRollbacks → restored) is the
// behaviour under test, so we drive the real registry from the test.
import { createPinia, setActivePinia } from 'pinia';
import type { StockItem } from 'src/models/stockItem';
import {
    clearRollbacks,
    executeRollbacks,
} from 'src/services/errorHandling/rollbackRegistry';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useStockItemStore } from 'src/stores/stockItemStore';

const m = vi.hoisted(() => ({
    getAllPagesAsync: vi.fn(),
    getAsync: vi.fn(),
    createAsync: vi.fn(),
    updateAsync: vi.fn(),
    deleteAsync: vi.fn(),
    tryWithQueue: vi.fn(),
    notify: vi.fn(),
    slRefreshAsync: vi.fn(),
    slSummaries: [] as Array<{ shopping_list_id: string; display_name: string }>,
}));

vi.mock('src/services/api/stockItemApiService', () => ({
    default: class {
        getAllPagesAsync = m.getAllPagesAsync;
        getAsync = m.getAsync;
        createAsync = m.createAsync;
        updateAsync = m.updateAsync;
        deleteAsync = m.deleteAsync;
    },
}));
vi.mock('src/composables/useOfflineQueue', () => ({
    tryWithQueue: m.tryWithQueue,
}));
vi.mock('src/services/api/axiosHttpClient', () => ({
    resolveBaseURL: () => 'http://api.test',
}));
vi.mock('quasar', () => ({
    Notify: { create: m.notify },
}));
vi.mock('src/stores/shoppingListStore', () => ({
    useShoppingListStore: () => ({
        refreshAsync: m.slRefreshAsync,
        summaries: m.slSummaries,
    }),
}));

function item(id: string, name: string, level = 'LVL-good'): StockItem {
    return {
        stock_item_id: id,
        name,
        stock_group_id: null,
        stock_level_id: level,
        stock_location_id: null,
    };
}

function deferred<T>() {
    let resolve!: (v: T) => void;
    let reject!: (e: unknown) => void;
    const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
    return { promise, resolve, reject };
}

const levelOf = (store: ReturnType<typeof useStockItemStore>, id: string) =>
    store.stockItems.find((si) => si.stock_item_id === id)?.stock_level_id;

beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    clearRollbacks(); // real module-global registry — isolate tests
    m.slSummaries.length = 0;
    m.getAllPagesAsync.mockResolvedValue([]);
    m.updateAsync.mockResolvedValue({});
    m.deleteAsync.mockResolvedValue(undefined);
    m.slRefreshAsync.mockResolvedValue(undefined);
    // Default: online + no network error — behave like the real tryWithQueue
    // happy path (run the attempt, pass result/rejection through).
    m.tryWithQueue.mockImplementation(
        (attempt: () => Promise<unknown>) => attempt(),
    );
});

async function seedStore(items: StockItem[]) {
    m.getAllPagesAsync.mockResolvedValueOnce(items);
    const store = useStockItemStore();
    await store.getStockItemsAsync();
    return store;
}

describe('stockItemStore — collection cache', () => {
    it('sorts the fetched collection case-insensitively by name', async () => {
        const store = await seedStore([
            item('SI-3', 'cherry'), item('SI-1', 'Apple'), item('SI-2', 'banana'),
        ]);

        expect(store.stockItems.map((si) => si.name)).toEqual(['Apple', 'banana', 'cherry']);
    });

    it('ensureLoadedAsync dedupes concurrent callers and no-ops once hydrated', async () => {
        const gate = deferred<StockItem[]>();
        m.getAllPagesAsync.mockReturnValue(gate.promise);
        const store = useStockItemStore();

        const both = Promise.all([store.ensureLoadedAsync(), store.ensureLoadedAsync()]);
        gate.resolve([item('SI-1', 'Apple')]);
        await both;
        await store.ensureLoadedAsync();

        expect(m.getAllPagesAsync).toHaveBeenCalledTimes(1);
    });

    it('ensureLoadedAsync retries after a failed hydration', async () => {
        m.getAllPagesAsync.mockRejectedValueOnce(new Error('offline'));
        const store = useStockItemStore();

        await expect(store.ensureLoadedAsync()).rejects.toThrow('offline');

        m.getAllPagesAsync.mockResolvedValueOnce([item('SI-1', 'Apple')]);
        await store.ensureLoadedAsync();
        expect(store.stockItems).toHaveLength(1);
    });

    it('deleteStockItemAsync removes only the deleted row', async () => {
        const store = await seedStore([item('SI-1', 'Apple'), item('SI-2', 'Banana')]);

        await store.deleteStockItemAsync('SI-1');

        expect(m.deleteAsync).toHaveBeenCalledWith('SI-1');
        expect(store.stockItems.map((si) => si.stock_item_id)).toEqual(['SI-2']);
    });
});

describe('stockItemStore — createStockItemAsync', () => {
    it('inserts a full-DTO create response in sorted position without a refetch', async () => {
        const store = await seedStore([item('SI-1', 'Apple'), item('SI-3', 'Cherry')]);
        m.createAsync.mockResolvedValueOnce(item('SI-2', 'banana'));

        const created = await store.createStockItemAsync({
            name: 'banana', stock_level_id: 'LVL-good', stock_location_id: null,
        });

        expect(created.stock_item_id).toBe('SI-2');
        expect(store.stockItems.map((si) => si.name)).toEqual(['Apple', 'banana', 'Cherry']);
        expect(m.getAsync).not.toHaveBeenCalled();
    });

    it('falls back to a getAsync round-trip when the API returns a bare id', async () => {
        const store = await seedStore([]);
        m.createAsync.mockResolvedValueOnce({ id: 'SI-9' });
        m.getAsync.mockResolvedValueOnce(item('SI-9', 'Zucchini'));

        const created = await store.createStockItemAsync({
            name: 'Zucchini', stock_level_id: 'LVL-good', stock_location_id: null,
        });

        expect(m.getAsync).toHaveBeenCalledWith('SI-9');
        expect(created.name).toBe('Zucchini');
        expect(store.stockItems).toHaveLength(1);
    });
});

describe('stockItemStore — updateStockLevelAsync (optimistic + rollback)', () => {
    it('applies the new level optimistically before the API answers', async () => {
        const store = await seedStore([item('SI-1', 'Apple', 'LVL-good')]);
        const gate = deferred<Record<string, never>>();
        m.updateAsync.mockReturnValueOnce(gate.promise);
        m.getAsync.mockResolvedValueOnce(item('SI-1', 'Apple', 'LVL-low'));

        const inFlight = store.updateStockLevelAsync({
            stock_item_id: 'SI-1', stock_level_id: 'LVL-low',
        });

        expect(levelOf(store, 'SI-1')).toBe('LVL-low'); // before resolve
        gate.resolve({});
        await inFlight;
        expect(levelOf(store, 'SI-1')).toBe('LVL-low');
    });

    it('replaces the row with the canonical server copy after an online success', async () => {
        const store = await seedStore([item('SI-1', 'Apple', 'LVL-good')]);
        m.getAsync.mockResolvedValueOnce({
            ...item('SI-1', 'Apple', 'LVL-low'),
            stock_level_last_updated: '2026-07-11T00:00:00Z',
        });

        await store.updateStockLevelAsync({ stock_item_id: 'SI-1', stock_level_id: 'LVL-low' });

        expect(m.getAsync).toHaveBeenCalledWith('SI-1');
        expect(store.stockItems[0]?.stock_level_last_updated).toBe('2026-07-11T00:00:00Z');
        // Success cleared the registered rollback — a later global-handler
        // sweep must NOT revert the committed level.
        executeRollbacks();
        expect(levelOf(store, 'SI-1')).toBe('LVL-low');
    });

    it('on API rejection the registered rollback restores the original level', async () => {
        const store = await seedStore([item('SI-1', 'Apple', 'LVL-good')]);
        m.updateAsync.mockRejectedValueOnce(new Error('422 validation'));

        await expect(
            store.updateStockLevelAsync({ stock_item_id: 'SI-1', stock_level_id: 'LVL-out' }),
        ).rejects.toThrow('422 validation');

        // Contract: the store leaves the optimistic value in place and relies
        // on the boot-level global error handler to run executeRollbacks().
        expect(levelOf(store, 'SI-1')).toBe('LVL-out');
        executeRollbacks(); // what globalErrorHandler.ts does on unhandledrejection
        expect(levelOf(store, 'SI-1')).toBe('LVL-good');
    });

    it('keeps the optimistic level and skips the canonical refetch when queued offline', async () => {
        const store = await seedStore([item('SI-1', 'Apple', 'LVL-good')]);
        m.tryWithQueue.mockResolvedValueOnce({ queued: true, mutation: {} });

        await store.updateStockLevelAsync({ stock_item_id: 'SI-1', stock_level_id: 'LVL-low' });

        expect(levelOf(store, 'SI-1')).toBe('LVL-low'); // trusted until drain
        expect(m.getAsync).not.toHaveBeenCalled();
    });

    it('is a silent no-op for an id that is not in the cache', async () => {
        const store = await seedStore([item('SI-1', 'Apple')]);

        await store.updateStockLevelAsync({ stock_item_id: 'SI-404', stock_level_id: 'LVL-low' });

        expect(m.tryWithQueue).not.toHaveBeenCalled();
        expect(m.updateAsync).not.toHaveBeenCalled();
    });

    it('fires the FU-511 auto-add toast and refreshes the shopping-list store', async () => {
        const store = await seedStore([item('SI-1', 'Apple', 'LVL-good')]);
        m.slSummaries.push({ shopping_list_id: 'SL-1', display_name: 'Groceries' });
        m.updateAsync.mockResolvedValueOnce({
            auto_added: { line_id: 'LN-1', shopping_list_id: 'SL-1' },
        });
        m.getAsync.mockResolvedValueOnce(item('SI-1', 'Apple', 'LVL-low'));

        await store.updateStockLevelAsync({ stock_item_id: 'SI-1', stock_level_id: 'LVL-low' });

        expect(m.slRefreshAsync).toHaveBeenCalledTimes(1);
        expect(m.notify).toHaveBeenCalledWith(expect.objectContaining({
            type: 'positive',
            message: 'Added Apple to Groceries.',
        }));
    });

    it('stays silent (no toast, no cross-store refresh) on the 204 no-trigger path', async () => {
        const store = await seedStore([item('SI-1', 'Apple')]);
        m.getAsync.mockResolvedValueOnce(item('SI-1', 'Apple', 'LVL-low'));

        await store.updateStockLevelAsync({ stock_item_id: 'SI-1', stock_level_id: 'LVL-low' });

        expect(m.notify).not.toHaveBeenCalled();
        expect(m.slRefreshAsync).not.toHaveBeenCalled();
    });
});

describe('stockItemStore — updateStockItemAsync (general PATCH)', () => {
    it('refetches the canonical row and re-sorts when a rename changes order', async () => {
        const store = await seedStore([item('SI-1', 'Apple'), item('SI-2', 'Banana')]);
        m.getAsync.mockResolvedValueOnce(item('SI-1', 'Zucchini'));

        await store.updateStockItemAsync({ stock_item_id: 'SI-1', name: 'Zucchini' });

        expect(store.stockItems.map((si) => si.name)).toEqual(['Banana', 'Zucchini']);
    });

    it('classifies the PATCH so the offline-queue label reads naturally', async () => {
        const store = await seedStore([item('SI-1', 'Apple')]);
        m.getAsync.mockResolvedValue(item('SI-1', 'Apple'));

        await store.updateStockItemAsync({ stock_item_id: 'SI-1', expiry_date: '2026-08-01' });
        await store.updateStockItemAsync({ stock_item_id: 'SI-1', expiry_date: null });
        await store.updateStockItemAsync({ stock_item_id: 'SI-1', is_open: true });
        await store.updateStockItemAsync({ stock_item_id: 'SI-1', name: 'Apple sauce' });

        const kinds = m.tryWithQueue.mock.calls.map(
            (c) => (c[1] as { kind: string; label: string }),
        );
        expect(kinds[0]).toMatchObject({ kind: 'push_expiry', label: 'Push expiry' });
        expect(kinds[1]).toMatchObject({ kind: 'clear_expiry', label: 'Clear expiry' });
        expect(kinds[2]).toMatchObject({ kind: 'mark_open', label: 'Mark opened' });
        expect(kinds[3]).toMatchObject({ kind: 'stock_level_update', label: 'Update stock item' });
        // Replay URL must be absolute (queue drains hours later; FU comment
        // in useOfflineQueue) and the id must NOT leak into the body.
        expect(m.tryWithQueue.mock.calls[0]?.[1]).toMatchObject({
            url: 'http://api.test/stock-items/SI-1',
            method: 'PATCH',
            body: { expiry_date: '2026-08-01' },
        });
    });

    it('returns early on the queued path — optimistic UI, no canonical refetch', async () => {
        const store = await seedStore([item('SI-1', 'Apple')]);
        m.tryWithQueue.mockResolvedValueOnce({ queued: true, mutation: {} });

        await store.updateStockItemAsync({ stock_item_id: 'SI-1', is_open: true });

        expect(m.getAsync).not.toHaveBeenCalled();
        expect(m.notify).not.toHaveBeenCalled();
    });
});
