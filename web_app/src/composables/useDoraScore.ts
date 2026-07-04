import { ref, type Ref } from 'vue';
import DashboardApiService from 'src/services/api/dashboardApiService';
import type { DoraScore } from 'src/models/doraScore';

/** P8-08 — module-level cache for the dashboard's Dora Score card.
 *  There's only ever one score for the current user, so a shared
 *  singleton is the right shape (no per-key Map). The card mounts and
 *  reads the cached value while a background refresh runs; explicit
 *  `invalidateDoraScore()` bumps the timestamp so the next mount
 *  refetches. STALE_AFTER_MS matches useBuyVerdict for consistency. */

const api = new DashboardApiService();

const value = ref<DoraScore | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
let fetchedAt = 0;
let inflight: Promise<void> | null = null;

const STALE_AFTER_MS = 5 * 60_000;

function refresh(): Promise<void> {
    if (inflight) return inflight;
    loading.value = true;
    error.value = null;
    const p = api.getDoraScoreAsync()
        .then((dto) => {
            value.value = dto;
            fetchedAt = Date.now();
        })
        .catch((err: unknown) => {
            // The card v-ifs itself away on error — a 500 shouldn't
            // block the rest of the dashboard from rendering.
            error.value = err instanceof Error ? err.message : String(err);
            value.value = null;
        })
        .finally(() => {
            loading.value = false;
            inflight = null;
        });
    inflight = p;
    return p;
}

/** Bumped after any mutation that could shift the score (log waste,
 *  finish a shopping list, mark an item checked, cook + drop level).
 *  Doesn't refetch — next `useDoraScore()` mount triggers the reload. */
export function invalidateDoraScore(): void {
    fetchedAt = 0;
}

export function clearDoraScoreCache(): void {
    value.value = null;
    fetchedAt = 0;
    inflight = null;
}

export function useDoraScore(): {
    doraScore: Ref<DoraScore | null>;
    loading: Ref<boolean>;
    error: Ref<string | null>;
    refresh: () => Promise<void>;
} {
    const isStale = Date.now() - fetchedAt > STALE_AFTER_MS;
    if (!value.value && !inflight) {
        void refresh();
    } else if (isStale && !inflight) {
        void refresh();
    }
    return {
        doraScore: value,
        loading,
        error,
        refresh,
    };
}
