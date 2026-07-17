import { computed, ref, watch, type Ref, type ComputedRef } from 'vue';
import BuyVerdictApiService, {
    type BuyVerdict,
} from 'src/services/api/buyVerdictApiService';
import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';

/** P8-05 — per-item verdict fetcher with a coarse module-level cache
 *  so a page rendering 100 rows doesn't fire 100 requests when each
 *  row mounts. The cache is keyed by stock-item id and lives for the
 *  lifetime of the tab; the SPA invalidates a single entry via
 *  `invalidateBuyVerdict(id)` after any mutation that could change the
 *  verdict (add to list, mark stocked, log waste).
 *
 *  Not a Pinia store: verdicts are per-item, read-only, and don't need
 *  cross-page reactive fan-out beyond "the badge on this row shows the
 *  fresh value once the fetch resolves". A Map + a tiny composable
 *  gives us that with less ceremony.
 */

const api = new BuyVerdictApiService();

interface CacheEntry {
    value: Ref<BuyVerdict | null>;
    loading: Ref<boolean>;
    error: Ref<string | null>;
    /** Milliseconds since epoch; the composable treats entries older
     *  than STALE_AFTER_MS as stale-but-usable — the badge stays on
     *  screen while a fresh fetch runs in the background. */
    fetchedAt: number;
    inflight: Promise<void> | null;
}

const cache = new Map<string, CacheEntry>();
const STALE_AFTER_MS = 5 * 60_000;   // 5 minutes; verdicts don't churn


function ensureEntry(stockItemId: string): CacheEntry {
    let entry = cache.get(stockItemId);
    if (!entry) {
        entry = {
            value: ref<BuyVerdict | null>(null),
            loading: ref(false),
            error: ref<string | null>(null),
            fetchedAt: 0,
            inflight: null,
        };
        cache.set(stockItemId, entry);
    }
    return entry;
}


function refresh(stockItemId: string): Promise<void> {
    const entry = ensureEntry(stockItemId);
    if (entry.inflight) return entry.inflight;
    entry.loading.value = true;
    entry.error.value = null;
    const p = api.getAsync(stockItemId)
        .then((verdict) => {
            entry.value.value = verdict;
            entry.fetchedAt = Date.now();
        })
        .catch((err: unknown) => {
            // A 404 (item deleted) or a 500 (server hiccup) should hide
            // the badge, not surface a red error strip in the list.
            // Log for diagnostics; leave value null so the caller can
            // v-if it away.
            entry.error.value = err instanceof Error ? err.message : String(err);
            entry.value.value = null;
        })
        .finally(() => {
            entry.loading.value = false;
            entry.inflight = null;
        });
    entry.inflight = p;
    return p;
}


/** Invalidate a single item's cached verdict — call this after any
 *  mutation that could change the answer (add to list, mark stocked,
 *  log a waste event, finish a shopping list). If the entry is live
 *  (some card/badge has already displayed it), refetch immediately so
 *  mounted consumers repaint with the fresh answer — an entry-only
 *  stamp reset left mounted cards stale until remount (FU-572).
 *  `refresh` dedupes on its inflight promise, so double-invalidation
 *  from nested seams costs one request. */
export function invalidateBuyVerdict(stockItemId: string): void {
    const entry = cache.get(stockItemId);
    if (entry) {
        entry.fetchedAt = 0;
        if (entry.value.value !== null) void refresh(stockItemId);
    }
}


/** Drop *every* cached verdict — used on sign-out and by tests. */
export function clearBuyVerdictCache(): void {
    cache.clear();
}


export function useBuyVerdict(stockItemId: Ref<string | null> | string) {
    const { buyVerdictEnabled } = useBuyVerdictEnabled();

    // Accept either a plain string (row on Stock Overview, id known
    // and stable) or a reactive ref (detail page router param).
    const idRef: Ref<string | null> =
        typeof stockItemId === 'string' ? ref(stockItemId) : stockItemId;

    function fetchIfNeeded(id: string | null): void {
        if (!buyVerdictEnabled.value) return;
        if (!id) return;
        const entry = ensureEntry(id);
        const isStale = Date.now() - entry.fetchedAt > STALE_AFTER_MS;
        if (!entry.value.value && !entry.inflight) {
            void refresh(id);
        } else if (isStale && !entry.inflight) {
            // Background refresh — keep the current value on screen.
            void refresh(id);
        }
    }

    watch(idRef, (id) => fetchIfNeeded(id), { immediate: true });
    watch(buyVerdictEnabled, (on) => {
        if (on) fetchIfNeeded(idRef.value);
    });

    // Computed refs so consumers stay reactive when `idRef` changes.
    const verdict: ComputedRef<BuyVerdict | null> = computed(() => {
        const id = idRef.value;
        return id ? ensureEntry(id).value.value : null;
    });
    const loading: ComputedRef<boolean> = computed(() => {
        const id = idRef.value;
        return id ? ensureEntry(id).loading.value : false;
    });
    const error: ComputedRef<string | null> = computed(() => {
        const id = idRef.value;
        return id ? ensureEntry(id).error.value : null;
    });

    return {
        verdict,
        loading,
        error,
        refresh: () => {
            const id = idRef.value;
            if (id) return refresh(id);
            return Promise.resolve();
        },
        invalidate: () => {
            const id = idRef.value;
            if (id) invalidateBuyVerdict(id);
        },
    };
}
