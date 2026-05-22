// Tri-mode load state primitive (F3).
//
// Stores and pages often conflate "no data yet" with "loaded empty",
// which leads to the offline-empty-page footgun: the user opens a screen
// while offline, the store fails silently, and they see a normal empty
// state with no hint that something went wrong.
//
// This composable forces the call sites to declare the difference:
//
//   - never_loaded : page first opened, fetch hasn't started/finished.
//   - loading       : fetch in flight (overlaps with never_loaded
//                     on first load and loaded on a refresh).
//   - loaded        : fetch succeeded; the data ref reflects the server.
//                     `loaded + 0 items` = a legitimate empty state.
//   - failed        : fetch threw; `error` carries the reason.
//
// Pages can pattern-match against `state` to decide between "skeleton",
// "you're offline" hint, "empty", or "retry button". F2's EmptyState
// component picks the right copy from this same enum.

import { computed, ref } from 'vue';

export type LoadStatus = 'never_loaded' | 'loading' | 'loaded' | 'failed';

export function useLoadState() {
    const status = ref<LoadStatus>('never_loaded');
    const error = ref<Error | null>(null);
    const lastLoadedAt = ref<Date | null>(null);

    function setLoading() {
        // Don't clobber 'never_loaded' awareness on refresh — the page can
        // tell whether *any* data has ever arrived by checking lastLoadedAt.
        status.value = 'loading';
    }

    function setLoaded() {
        status.value = 'loaded';
        error.value = null;
        lastLoadedAt.value = new Date();
    }

    function setFailed(err: unknown) {
        status.value = 'failed';
        error.value = err instanceof Error ? err : new Error(String(err));
    }

    function reset() {
        status.value = 'never_loaded';
        error.value = null;
        lastLoadedAt.value = null;
    }

    /**
     * Wrap a fetch in tri-mode bookkeeping. Returns the awaited result on
     * success, or `null` on failure (the page reads `state.failed`).
     */
    async function track<T>(fn: () => Promise<T>): Promise<T | null> {
        setLoading();
        try {
            const result = await fn();
            setLoaded();
            return result;
        } catch (err) {
            setFailed(err);
            return null;
        }
    }

    return {
        status,
        error,
        lastLoadedAt,
        // Convenience flags pages can bind to.
        isFirstLoad: computed(
            () => status.value === 'never_loaded' || status.value === 'loading',
        ),
        isLoaded: computed(() => status.value === 'loaded'),
        isFailed: computed(() => status.value === 'failed'),
        hasEverLoaded: computed(() => lastLoadedAt.value !== null),
        setLoading,
        setLoaded,
        setFailed,
        reset,
        track,
    };
}
