// @vitest-environment jsdom
/**
 * FU-520 component/composable layer — useOfflineQueue (F3).
 *
 * The offline-tolerant mutation queue is the last opportunistic remnant of
 * FU-520's item 3. It carries real behavioural contracts worth pinning:
 *   * tryWithQueue only swallows a *network* NormalisedApiError (the UI was
 *     optimistic, so a queued write reads as success); any other failure
 *     rethrows,
 *   * drain replays oldest-first, STOPS on the first network error (still
 *     offline) leaving the rest queued, but shunts a *non-network* rejection
 *     into the conflict pile and keeps going,
 *   * the queue is per-user (signing in as someone else must not drain the
 *     previous user's writes) and survives a page reload via localStorage,
 *   * flipping useNetworkStatus.apiReachable false→true auto-drains,
 *   * conflicts can be discarded or retried (retry re-queues + drains).
 *
 * The module holds singleton state (queue / booted latch), so every test
 * gets a fresh copy via vi.resetModules() + a dynamic import. axios, quasar
 * Notify, useAuthStore and useNetworkStatus are mocked at the module
 * boundary; the REAL NormalisedApiError is imported fresh alongside the
 * composable so the `instanceof` branch inside drain/tryWithQueue matches the
 * class the (re-evaluated) composable actually sees.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { reactive, ref, type Ref } from 'vue';

// Shared spies (call-count is cleared each test). axios + quasar are pure
// sinks, so a static mock is fine.
const h = vi.hoisted(() => ({ request: vi.fn(), notify: vi.fn() }));
vi.mock('axios', () => ({ default: { request: h.request } }));
vi.mock('quasar', () => ({ Notify: { create: h.notify } }));

// The reactive seams get a FRESH ref/reactive per test (wired via vi.doMock in
// beforeEach). This matters because boot() registers module-level watchers on
// them that are never torn down — a shared ref would let a previous test's
// zombie watcher fire on the current test's flip and drain its stale queue.
let apiReachable: Ref<boolean>;
let auth: { currentUser: { user_id: string } | null };

type OfflineQueueModule = typeof import('src/composables/useOfflineQueue');
type ApiErrorClass = typeof import('src/services/api/axiosHttpClient').NormalisedApiError;

let mod: OfflineQueueModule;
let ApiError: ApiErrorClass;

// Give Vue's microtask scheduler a full macrotask to flush watchers.
const tick = () => new Promise((res) => setTimeout(res, 0));

function networkError(url = 'http://api.test/x'): InstanceType<ApiErrorClass> {
    return new ApiError({
        status: 0,
        code: 'network_error',
        message: 'Network request failed',
        details: null,
        correlationId: '',
        isNetworkError: true,
        method: 'PATCH',
        url,
    });
}

function serverError(status = 409): InstanceType<ApiErrorClass> {
    return new ApiError({
        status,
        code: `http_${status}`,
        message: 'Conflict',
        details: null,
        correlationId: '',
        isNetworkError: false,
        method: 'PATCH',
        url: 'http://api.test/x',
    });
}

// Enqueue one mutation by failing an optimistic attempt with a network error.
async function enqueueOne(
    label = 'Tick line',
    url = 'http://api.test/x',
): Promise<void> {
    await mod.tryWithQueue(() => Promise.reject(networkError(url)), {
        url,
        method: 'PATCH',
        body: { done: true },
        kind: 'shopping_list_line_tick',
        label,
    });
}

function storageKey(userId: string): string {
    return `dora.offlineQueue.${userId || 'anonymous'}`;
}

function readStore(userId = 'anonymous'): unknown[] {
    const raw = localStorage.getItem(storageKey(userId));
    return raw ? JSON.parse(raw) : [];
}

beforeEach(async () => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.resetModules();

    // Fresh reactive seams per test, re-mocked so the freshly-imported
    // composable watches THESE (not a previous test's leftover refs).
    apiReachable = ref(true);
    auth = reactive({ currentUser: null }) as typeof auth;
    vi.doMock('src/composables/useNetworkStatus', () => ({
        useNetworkStatus: () => ({ apiReachable }),
    }));
    vi.doMock('src/stores/authStore', () => ({ useAuthStore: () => auth }));

    // Import the composable first so its dependency graph (incl. the real
    // axiosHttpClient) is evaluated once; then pull NormalisedApiError from
    // that SAME evaluation so instanceof checks line up.
    mod = await import('src/composables/useOfflineQueue');
    ({ NormalisedApiError: ApiError } = await import(
        'src/services/api/axiosHttpClient'
    ));
});

describe('tryWithQueue — the optimistic write wrapper', () => {
    it('enqueues on a network error and reports success to the caller', async () => {
        const result = await mod.tryWithQueue(
            () => Promise.reject(networkError()),
            {
                url: 'http://api.test/x',
                method: 'PATCH',
                body: { done: true },
                kind: 'shopping_list_line_tick',
                label: 'Tick milk',
            },
        );

        expect(result).toMatchObject({ queued: true });
        expect(mod.useOfflineQueue().queuedCount.value).toBe(1);
        expect(readStore()).toHaveLength(1);
        expect(h.notify).toHaveBeenCalledWith(
            expect.objectContaining({ type: 'info', message: 'Queued: Tick milk' }),
        );
    });

    it('returns the value and queues nothing when the attempt succeeds', async () => {
        const result = await mod.tryWithQueue(() => Promise.resolve('ok'), {
            url: 'http://api.test/x',
            method: 'PATCH',
            body: {},
            kind: 'stock_level_update',
            label: 'Bump',
        });

        expect(result).toBe('ok');
        expect(mod.useOfflineQueue().queuedCount.value).toBe(0);
        expect(h.notify).not.toHaveBeenCalled();
    });

    it('rethrows a non-network failure instead of queueing it', async () => {
        await expect(
            mod.tryWithQueue(() => Promise.reject(serverError(422)), {
                url: 'http://api.test/x',
                method: 'PATCH',
                body: {},
                kind: 'mark_open',
                label: 'Open',
            }),
        ).rejects.toBeInstanceOf(ApiError);

        expect(mod.useOfflineQueue().queuedCount.value).toBe(0);
        expect(readStore()).toHaveLength(0);
    });
});

describe('drain — replaying the queue', () => {
    it('replays every mutation on success and clears the queue', async () => {
        await enqueueOne('Tick A', 'http://api.test/a');
        await enqueueOne('Tick B', 'http://api.test/b');
        h.request.mockResolvedValue({ status: 200 });

        await mod.drain();

        expect(mod.useOfflineQueue().queuedCount.value).toBe(0);
        expect(readStore()).toHaveLength(0);
        expect(h.request).toHaveBeenCalledTimes(2);
        // Replays go through raw axios with the offline-replay markers.
        expect(h.request).toHaveBeenCalledWith(
            expect.objectContaining({
                url: 'http://api.test/a',
                method: 'PATCH',
                data: { done: true },
                withCredentials: true,
                headers: expect.objectContaining({ 'X-Offline-Replay': '1' }),
            }),
        );
        expect(h.notify).toHaveBeenCalledWith(
            expect.objectContaining({ type: 'positive', message: 'Synced everything.' }),
        );
    });

    it('stops on the first network error and leaves the rest queued', async () => {
        await enqueueOne('Tick A');
        await enqueueOne('Tick B');
        h.request.mockRejectedValue({ message: 'still offline' }); // no .response

        await mod.drain();

        const q = mod.useOfflineQueue();
        expect(q.queuedCount.value).toBe(2); // nothing drained
        expect(h.request).toHaveBeenCalledTimes(1); // broke after the first
        expect(q.queue.value[0]?.attempts).toBe(1); // attempt was counted
        expect(h.notify).not.toHaveBeenCalledWith(
            expect.objectContaining({ message: 'Synced everything.' }),
        );
    });

    it('shunts a non-network rejection into the conflict pile and continues', async () => {
        await enqueueOne('Bad write');
        h.request.mockRejectedValue({ response: { status: 409 }, message: 'conflict' });

        await mod.drain();

        const q = mod.useOfflineQueue();
        expect(q.queuedCount.value).toBe(0); // removed from the live queue
        expect(q.conflictCount.value).toBe(1); // parked for the user to resolve
        expect(readStore()).toHaveLength(0);
        expect(h.notify).toHaveBeenCalledWith(
            expect.objectContaining({ type: 'negative' }),
        );
    });

    it('is a no-op with an empty queue', async () => {
        await mod.drain();

        expect(h.request).not.toHaveBeenCalled();
        expect(h.notify).not.toHaveBeenCalled();
    });
});

describe('auto-drain on reconnect', () => {
    it('drains when apiReachable flips false→true with a pending queue', async () => {
        await enqueueOne('Tick A');
        h.request.mockResolvedValue({ status: 200 });

        // A clean false→true edge (boot starts it true) is what the watcher keys on.
        apiReachable.value = false;
        await tick();
        apiReachable.value = true;

        await vi.waitFor(() =>
            expect(mod.useOfflineQueue().queuedCount.value).toBe(0),
        );
        expect(h.request).toHaveBeenCalledTimes(1);
    });
});

describe('conflict resolution', () => {
    beforeEach(async () => {
        await enqueueOne('Bad write');
        h.request.mockRejectedValue({ response: { status: 409 }, message: 'conflict' });
        await mod.drain();
    });

    it('discardConflict drops the parked mutation', () => {
        const q = mod.useOfflineQueue();
        const id = q.conflicts.value[0]!.id;

        mod.discardConflict(id);

        expect(q.conflictCount.value).toBe(0);
    });

    it('retryConflict re-queues the mutation and drains it', async () => {
        const q = mod.useOfflineQueue();
        const id = q.conflicts.value[0]!.id;
        h.request.mockReset();
        h.request.mockResolvedValue({ status: 200 }); // server recovered

        await mod.retryConflict(id);

        expect(q.conflictCount.value).toBe(0);
        expect(q.queuedCount.value).toBe(0); // drained clean
        expect(h.request).toHaveBeenCalledTimes(1);
    });
});

describe('per-user isolation + persistence', () => {
    it('keeps each user\'s queue separate and rehydrates on user switch', async () => {
        auth.currentUser = { user_id: 'user-A' };
        await enqueueOne('A only');
        expect(readStore('user-A')).toHaveLength(1);

        // Sign in as someone else — the watcher rehydrates to B's (empty) queue
        // without touching A's persisted writes.
        auth.currentUser = { user_id: 'user-B' };
        await tick();
        expect(mod.useOfflineQueue().queuedCount.value).toBe(0);
        expect(readStore('user-A')).toHaveLength(1);

        // Back to A — the write is still there.
        auth.currentUser = { user_id: 'user-A' };
        await tick();
        expect(mod.useOfflineQueue().queuedCount.value).toBe(1);
    });

    it('survives a reload by loading the persisted queue on boot', async () => {
        auth.currentUser = { user_id: 'user-A' };
        localStorage.setItem(
            storageKey('user-A'),
            JSON.stringify([
                {
                    id: 'q-1',
                    url: 'http://api.test/x',
                    method: 'PATCH',
                    body: { done: true },
                    label: 'Restored',
                    kind: 'shopping_list_line_tick',
                    createdAt: '2026-07-15T00:00:00Z',
                    attempts: 0,
                },
            ]),
        );

        // First public call boots + rehydrates from storage.
        expect(mod.useOfflineQueue().queuedCount.value).toBe(1);
    });

    it('degrades to an empty queue when the stored payload is corrupt', async () => {
        auth.currentUser = { user_id: 'user-A' };
        localStorage.setItem(storageKey('user-A'), '{not valid json');

        expect(() => mod.useOfflineQueue()).not.toThrow();
        expect(mod.useOfflineQueue().queuedCount.value).toBe(0);
    });
});
