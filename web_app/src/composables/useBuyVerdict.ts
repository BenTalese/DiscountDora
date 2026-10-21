import { computed, ref, watch, type Ref, type ComputedRef } from 'vue';
import BuyVerdictApiService, {
    type BuyVerdict,
} from 'src/services/api/buyVerdictApiService';
import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';

/** P8-05 — per-item verdict fetcher with a coarse module-level cache
 *  keyed by stock-item id, living for the lifetime of the tab. The SPA
 *  invalidates a single entry via `invalidateBuyVerdict(id)` after any
 *  mutation that could change the verdict (add to list, mark stocked,
 *  log waste).
 *
 *  What the cache does NOT do (B5 — this comment used to claim the
 *  opposite): it does not stop a list of rows fanning out. Deduping by
 *  id only helps on *remount* — 100 rows for 100 distinct items still
 *  fire 100 requests the first time they render. For a whole collection,
 *  fetch verdicts in bulk (`GET /api/shopping-lists/<id>/buy-verdicts`)
 *  and let this cache serve the rows from the one response.
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


/** Seed the cache from one bulk response instead of a request per row (B6).
 *  Call it with the ids you are about to render, **synchronously**, before the
 *  rows mount: every id is marked in-flight against the shared promise up
 *  front, so a badge mounting mid-flight waits on it rather than starting its
 *  own fetch. That ordering is the whole point — priming after the rows paint
 *  saves nothing, because they will already have asked.
 *
 *  An id the response doesn't mention (no verdict computed for it) is left with
 *  a null value, which reads as "nothing to show" — the badge hides. A failed
 *  bulk fetch clears the in-flight marks and leaves the entries empty; the next
 *  mount or the staleness path falls back to per-item fetches on its own. */
export function primeBuyVerdicts(
    stockItemIds: string[],
    fetcher: () => Promise<Record<string, BuyVerdict>>,
): Promise<void> {
    const ids = [...new Set(stockItemIds)];
    if (ids.length === 0) return Promise.resolve();

    const entries = ids.map((id) => ({ id, entry: ensureEntry(id) }));
    const shared = fetcher()
        .then((verdicts) => {
            const now = Date.now();
            for (const { id, entry } of entries) {
                entry.value.value = verdicts[id] ?? null;
                entry.fetchedAt = now;
            }
        })
        .catch((err: unknown) => {
            // Same posture as `refresh`: a hiccup hides the badges rather than
            // surfacing a red strip over someone's shopping list.
            const message = err instanceof Error ? err.message : String(err);
            for (const { entry } of entries) entry.error.value = message;
        })
        .finally(() => {
            for (const { entry } of entries) {
                entry.loading.value = false;
                entry.inflight = null;
            }
        });

    for (const { entry } of entries) {
        entry.loading.value = true;
        entry.error.value = null;
        entry.inflight = shared;
    }
    return shared;
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


export function useBuyVerdict(
    stockItemId: Ref<string | null> | ComputedRef<string | null> | ComputedRef<string> | string,
) {
    const { buyVerdictEnabled } = useBuyVerdictEnabled();

    // Accept either a plain string (row on Stock Overview, id known
    // and stable) or a reactive ref/computed (detail page router param,
    // or the peek panel's `idOverride` prop — which swaps in place while
    // the page component stays mounted, so a snapshot string there
    // leaves the card showing the previous item's verdict).
    const idRef: Ref<string | null> | ComputedRef<string | null> =
        typeof stockItemId === 'string' ? ref<string | null>(stockItemId) : stockItemId;

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
    //
    // The disabled check is on the *read*, not just on `fetchIfNeeded`: the
    // module cache outlives a flag flip, so an admin turning money off (or the
    // user flipping their own opt-out) mid-session would otherwise leave
    // already-fetched verdicts painted until remount. Gating here means every
    // consumer — card and both badges — goes quiet on the same tick.
    const verdict: ComputedRef<BuyVerdict | null> = computed(() => {
        if (!buyVerdictEnabled.value) return null;
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
