// Offline-tolerant mutation queue (F3).
//
// Mutations that are safe to retry verbatim (the "user actions during a
// grocery run" set — ticking lines, bumping stock levels, marking
// opened/restocked, pushing expiry) get enqueued in localStorage when
// they fail with a network error. When the API becomes reachable again
// (per useNetworkStatus), we drain the queue oldest-first.
//
// Why localStorage and not IndexedDB: the payloads are small (a few
// strings each), the volume is low (handful per shop, not thousands),
// and being readable in DevTools is a debugging win.
//
// What's NOT supported: creates, deletes, and anything that changes
// identity. Those fail loudly when offline — the user almost always
// wants to know rather than have a phantom item appear later.

import axios, { type AxiosRequestConfig } from 'axios';
import { Notify } from 'quasar';
import {
    NormalisedApiError,
} from 'src/services/api/axiosHttpClient';
import { useAuthStore } from 'src/stores/authStore';
import { computed, readonly, ref, watch } from 'vue';
import { useNetworkStatus } from './useNetworkStatus';

// ─── Storage shape ───────────────────────────────────────────────────

export type QueueableMutationKind =
    | 'stock_level_update'
    | 'shopping_list_line_tick'
    | 'mark_open'
    | 'mark_restocked'
    | 'push_expiry'
    | 'clear_expiry';

export type QueuedMutation = {
    id: string;
    /** Full URL, NOT a relative path — replayed verbatim, possibly after
     *  hours, by which time the active backend port may differ. */
    url: string;
    method: 'POST' | 'PATCH' | 'PUT' | 'DELETE';
    body: unknown;
    label: string;
    kind: QueueableMutationKind;
    createdAt: string; // ISO
    attempts: number;
};

// Per-user so signing out → in as a different user doesn't drain
// someone else's queue. Falls back to "anonymous" pre-login (which is
// useless because all our mutations require auth, but keeps types clean).
function storageKey(userId: string): string {
    return `dora.offlineQueue.${userId || 'anonymous'}`;
}

function loadQueue(userId: string): QueuedMutation[] {
    try {
        const raw = localStorage.getItem(storageKey(userId));
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return [];
        return parsed as QueuedMutation[];
    } catch {
        return [];
    }
}

function saveQueue(userId: string, queue: QueuedMutation[]): void {
    try {
        localStorage.setItem(storageKey(userId), JSON.stringify(queue));
    } catch {
        // localStorage may be unavailable (private mode) — best effort.
    }
}

function newId(): string {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        return (crypto as Crypto & { randomUUID: () => string }).randomUUID();
    }
    return `q-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

// ─── Module state ────────────────────────────────────────────────────

const queue = ref<QueuedMutation[]>([]);
const draining = ref(false);
const lastDrainAt = ref<Date | null>(null);
// Per-item conflict surface: when a queued mutation drains but the
// server rejects it for non-network reasons, we stash it here for the
// user to resolve. Keeps the queue itself uncorrupted.
const conflicts = ref<QueuedMutation[]>([]);
let booted = false;
let currentUserId = '';

function rehydrate(userId: string) {
    currentUserId = userId;
    queue.value = loadQueue(userId);
}

// Network-status watcher: trigger drain when apiReachable flips true.
function boot() {
    if (booted) return;
    booted = true;
    const auth = useAuthStore();
    rehydrate(auth.currentUser?.user_id ?? '');
    watch(
        () => auth.currentUser?.user_id ?? '',
        (userId) => rehydrate(userId),
    );
    const { apiReachable } = useNetworkStatus();
    watch(apiReachable, (now, was) => {
        if (now && !was && queue.value.length > 0) {
            void drain();
        }
    });
}

// ─── Public API ──────────────────────────────────────────────────────

/**
 * Try `attempt`. If it fails with a NormalisedApiError marked as a
 * network error AND it's a registered kind, enqueue it and resolve
 * (the UI was already optimistic, so it should treat this as success).
 * Any other failure rethrows.
 */
export async function tryWithQueue<T>(
    attempt: () => Promise<T>,
    enqueueIfOffline: {
        url: string;
        method: QueuedMutation['method'];
        body: unknown;
        kind: QueueableMutationKind;
        label: string;
    },
): Promise<T | { queued: true; mutation: QueuedMutation }> {
    boot();
    try {
        return await attempt();
    } catch (err) {
        if (err instanceof NormalisedApiError && err.isNetworkError) {
            const mutation = enqueue(enqueueIfOffline);
            return { queued: true, mutation };
        }
        throw err;
    }
}

function enqueue(args: {
    url: string;
    method: QueuedMutation['method'];
    body: unknown;
    kind: QueueableMutationKind;
    label: string;
}): QueuedMutation {
    const mutation: QueuedMutation = {
        id: newId(),
        url: args.url,
        method: args.method,
        body: args.body,
        label: args.label,
        kind: args.kind,
        createdAt: new Date().toISOString(),
        attempts: 0,
    };
    queue.value = [...queue.value, mutation];
    saveQueue(currentUserId, queue.value);
    Notify.create({
        type: 'info',
        position: 'bottom-right',
        message: `Queued: ${args.label}`,
        caption: 'Will sync when we reconnect.',
        timeout: 2500,
    });
    return mutation;
}

/**
 * Replay queued mutations oldest-first. Stops on the first network
 * error (we're still offline / the API is flaky). On non-network
 * failures the mutation moves to `conflicts` so the user can resolve it.
 */
export async function drain(): Promise<void> {
    boot();
    if (draining.value) return;
    if (queue.value.length === 0) return;
    draining.value = true;
    try {
        // Iterate over a snapshot so changes don't trip us up. We mutate
        // `queue.value` after each attempt to persist progress.
        const snapshot = [...queue.value];
        for (const mutation of snapshot) {
            try {
                await replayOnce(mutation);
                // Success — drop it from the queue.
                queue.value = queue.value.filter((q) => q.id !== mutation.id);
                saveQueue(currentUserId, queue.value);
            } catch (err) {
                mutation.attempts++;
                if (err instanceof NormalisedApiError && err.isNetworkError) {
                    // Still offline — leave the rest for later.
                    saveQueue(currentUserId, queue.value);
                    break;
                }
                // Non-network failure: hand it off to the conflict pile so
                // the user can decide what to do. Don't keep retrying
                // forever in a loop.
                conflicts.value = [...conflicts.value, mutation];
                queue.value = queue.value.filter((q) => q.id !== mutation.id);
                saveQueue(currentUserId, queue.value);
                Notify.create({
                    type: 'negative',
                    position: 'bottom-right',
                    message: `Couldn't sync "${mutation.label}".`,
                    caption: err instanceof NormalisedApiError
                        ? `${err.code} (${err.status})`
                        : String(err),
                    timeout: 5000,
                });
            }
        }
        lastDrainAt.value = new Date();
        if (queue.value.length === 0 && conflicts.value.length === 0) {
            Notify.create({
                type: 'positive',
                position: 'bottom-right',
                message: 'Synced everything.',
                timeout: 2000,
            });
        }
    } finally {
        draining.value = false;
    }
}

// Replay a single queued mutation. We use raw axios so the request goes
// through *without* being re-enqueued by our `tryWithQueue` wrapper, and
// we route errors back through NormalisedApiError-compatible shape so
// the drain loop can branch correctly.
async function replayOnce(mutation: QueuedMutation): Promise<void> {
    const config: AxiosRequestConfig = {
        url: mutation.url,
        method: mutation.method,
        data: mutation.body,
        withCredentials: true,
        headers: {
            'Content-Type': 'application/json',
            'X-Request-Id': `replay-${mutation.id}`,
            'X-Offline-Replay': '1',
        },
        timeout: 10_000,
    };
    try {
        await axios.request(config);
    } catch (err) {
        // Convert axios error → NormalisedApiError so the loop's
        // network-vs-other branch can read `.isNetworkError`.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const e = err as any;
        const status = e?.response?.status ?? 0;
        throw new NormalisedApiError({
            status,
            code: status > 0 ? `http_${status}` : 'network_error',
            message: e?.message ?? 'Replay failed',
            details: null,
            correlationId: `replay-${mutation.id}`,
            isNetworkError: !e?.response,
            method: mutation.method,
            url: mutation.url,
        });
    }
}

/** Discard a conflicted mutation (user decided it's no longer relevant). */
export function discardConflict(mutationId: string): void {
    conflicts.value = conflicts.value.filter((m) => m.id !== mutationId);
}

/** Retry a conflicted mutation (e.g. after the user fixed the underlying state). */
export async function retryConflict(mutationId: string): Promise<void> {
    const target = conflicts.value.find((m) => m.id === mutationId);
    if (!target) return;
    conflicts.value = conflicts.value.filter((m) => m.id !== mutationId);
    queue.value = [...queue.value, target];
    saveQueue(currentUserId, queue.value);
    await drain();
}

export function useOfflineQueue() {
    boot();
    return {
        queue: readonly(queue),
        queuedCount: computed(() => queue.value.length),
        draining: readonly(draining),
        conflicts: readonly(conflicts),
        conflictCount: computed(() => conflicts.value.length),
        lastDrainAt: readonly(lastDrainAt),
        drain,
        discardConflict,
        retryConflict,
    };
}
