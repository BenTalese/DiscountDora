// @vitest-environment jsdom
// FU-539 resilience layer — useOfflineQueue, THE highest-value target. A replay
// bug here duplicates or silently drops the user's grocery-run actions. This
// suite drives the module's singleton state through a fresh import per test
// (vi.resetModules) and pins: enqueue-on-network-error, rethrow-on-other-error,
// oldest-first replay, stop-on-network-error, non-network → conflicts, the
// re-entrancy guard, and the idempotency headers the backend dedups on.
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { NormalisedApiError as NAEType } from 'src/services/api/axiosHttpClient';

// ─── Module-boundary mocks ───────────────────────────────────────────
const h = vi.hoisted(() => ({
    notify: vi.fn(),
    request: vi.fn(),
}));

vi.mock('quasar', () => ({
    Notify: { create: h.notify },
}));
vi.mock('axios', () => ({
    default: { request: h.request },
}));
vi.mock('src/stores/authStore', () => ({
    useAuthStore: () => ({ currentUser: { user_id: 'u1' } }),
}));
vi.mock('src/composables/useNetworkStatus', async () => {
    const { ref } = await import('vue');
    return { useNetworkStatus: () => ({ apiReachable: ref(true) }) };
});

const KEY = 'dora.offlineQueue.u1';

type Mod = typeof import('src/composables/useOfflineQueue');
type NAECtor = typeof import('src/services/api/axiosHttpClient')['NormalisedApiError'];

// vi.resetModules() gives the queue module a FRESH axiosHttpClient (and thus a
// fresh NormalisedApiError class). `instanceof` inside the queue only matches
// errors built from THAT same fresh class — so we must mint test errors from
// the freshly-imported ctor, not one captured before the reset. (The documented
// module-boundary trap, offline-queue edition.)
async function freshModule(): Promise<{ mod: Mod; NAE: NAECtor }> {
    vi.resetModules();
    const mod = await import('src/composables/useOfflineQueue');
    const { NormalisedApiError } = await import('src/services/api/axiosHttpClient');
    return { mod, NAE: NormalisedApiError };
}

function netError(NAE: NAECtor, message = 'offline'): NAEType {
    return new NAE({
        status: 0,
        code: 'network_error',
        message,
        details: null,
        correlationId: 'c',
        isNetworkError: true,
        method: 'PATCH',
        url: '/x',
    });
}

function serverError(NAE: NAECtor, status = 422): NAEType {
    return new NAE({
        status,
        code: `http_${status}`,
        message: 'validation',
        details: null,
        correlationId: 'c',
        isNetworkError: false,
        method: 'PATCH',
        url: '/x',
    });
}

const enqueueArgs = (overrides: Record<string, unknown> = {}) => ({
    url: 'http://api.test/stock-items/SI-1',
    method: 'PATCH' as const,
    body: { is_open: true },
    kind: 'mark_open' as const,
    label: 'Mark opened',
    ...overrides,
});

/** Seed localStorage with a queue BEFORE boot() rehydrates from it. */
function seedQueue(mutations: Array<Record<string, unknown>>): void {
    localStorage.setItem(KEY, JSON.stringify(mutations));
}

function mutation(id: string, overrides: Record<string, unknown> = {}) {
    return {
        id,
        url: `http://api.test/stock-items/${id}`,
        method: 'PATCH',
        body: { level: id },
        label: `Update ${id}`,
        kind: 'stock_level_update',
        createdAt: '2026-07-12T00:00:00.000Z',
        attempts: 0,
        ...overrides,
    };
}

function readQueue(): Array<{ id: string }> {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
}

beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
});

describe('tryWithQueue', () => {
    it('returns the attempt value and queues nothing on success', async () => {
        const { mod } = await freshModule();
        const result = await mod.tryWithQueue(async () => 'ok', enqueueArgs());

        expect(result).toBe('ok');
        expect(h.request).not.toHaveBeenCalled();
        expect(localStorage.getItem(KEY)).toBeNull();
    });

    it('enqueues + persists on a network NormalisedApiError for a registered kind', async () => {
        const { mod, NAE } = await freshModule();
        const result = await mod.tryWithQueue(
            async () => { throw netError(NAE); },
            enqueueArgs(),
        );

        expect(result).toMatchObject({ queued: true });
        const mutation = (result as { queued: true; mutation: Record<string, unknown> }).mutation;
        expect(mutation).toMatchObject({
            url: 'http://api.test/stock-items/SI-1',
            method: 'PATCH',
            body: { is_open: true },
            kind: 'mark_open',
        });

        const persisted = readQueue();
        expect(persisted).toHaveLength(1);
        expect(persisted[0]).toMatchObject({
            url: 'http://api.test/stock-items/SI-1',
            method: 'PATCH',
            body: { is_open: true },
            kind: 'mark_open',
        });
    });

    it('rethrows a non-network NormalisedApiError and queues nothing', async () => {
        const { mod, NAE } = await freshModule();
        await expect(
            mod.tryWithQueue(async () => { throw serverError(NAE); }, enqueueArgs()),
        ).rejects.toBeInstanceOf(NAE);

        expect(localStorage.getItem(KEY)).toBeNull();
    });

    it('rethrows a plain Error (not a NormalisedApiError) and queues nothing', async () => {
        const { mod } = await freshModule();
        await expect(
            mod.tryWithQueue(async () => { throw new Error('boom'); }, enqueueArgs()),
        ).rejects.toThrow('boom');

        expect(localStorage.getItem(KEY)).toBeNull();
    });
});

describe('drain — replay', () => {
    it('replays oldest-first, drops each on success, ends empty + persists []', async () => {
        seedQueue([mutation('a'), mutation('b'), mutation('c')]);
        h.request.mockResolvedValue({ data: {} });
        const { mod } = await freshModule();

        await mod.drain();

        const urls = h.request.mock.calls.map((c) => (c[0] as { url: string }).url);
        expect(urls).toEqual([
            'http://api.test/stock-items/a',
            'http://api.test/stock-items/b',
            'http://api.test/stock-items/c',
        ]);
        expect(readQueue()).toEqual([]);
    });

    it('replays carry the idempotency seam: X-Offline-Replay + stable replay-<id> request id', async () => {
        seedQueue([mutation('a')]);
        h.request.mockResolvedValue({ data: {} });
        const { mod } = await freshModule();

        await mod.drain();

        const config = h.request.mock.calls[0]![0] as {
            headers: Record<string, string>;
            method: string;
            data: unknown;
        };
        expect(config.headers['X-Offline-Replay']).toBe('1');
        expect(config.headers['X-Request-Id']).toBe('replay-a');
        expect(config.method).toBe('PATCH');
    });

    it('stops on a network error: earlier item drops, the failed one + rest stay queued', async () => {
        seedQueue([mutation('a'), mutation('b'), mutation('c')]);
        h.request
            .mockResolvedValueOnce({ data: {} }) // a succeeds
            .mockRejectedValueOnce({ message: 'still offline', response: undefined }); // b = network
        const { mod } = await freshModule();

        await mod.drain();

        // c is never attempted (loop broke on b).
        expect(h.request).toHaveBeenCalledTimes(2);
        expect(readQueue().map((m) => m.id)).toEqual(['b', 'c']);
    });

    it('moves a non-network failure to conflicts and keeps draining the rest', async () => {
        seedQueue([mutation('a'), mutation('b'), mutation('c')]);
        h.request
            .mockRejectedValueOnce({ response: { status: 409 }, message: 'conflict' }) // a = 409
            .mockResolvedValueOnce({ data: {} }) // b ok
            .mockResolvedValueOnce({ data: {} }); // c ok
        const { mod } = await freshModule();

        await mod.drain();

        expect(h.request).toHaveBeenCalledTimes(3);
        expect(readQueue()).toEqual([]); // a left the queue → conflicts; b, c synced
        const { conflicts } = mod.useOfflineQueue();
        expect(conflicts.value.map((m) => m.id)).toEqual(['a']);
    });

    it('re-entrancy guard: a second drain while one is in-flight is a no-op', async () => {
        seedQueue([mutation('a')]);
        // Never resolves — the first drain parks on item a's replay.
        h.request.mockReturnValue(new Promise(() => {}));
        const { mod } = await freshModule();

        const first = mod.drain(); // do not await — leaves draining=true
        await mod.drain(); // returns immediately via the guard

        expect(h.request).toHaveBeenCalledTimes(1);
        void first;
    });

    it('drain on an empty queue is a no-op (no replay, no toast)', async () => {
        const { mod } = await freshModule();
        await mod.drain();

        expect(h.request).not.toHaveBeenCalled();
        expect(h.notify).not.toHaveBeenCalled();
    });
});
