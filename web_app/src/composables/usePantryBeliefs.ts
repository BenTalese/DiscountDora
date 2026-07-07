import { readonly, ref } from 'vue';
import StockItemApiService from 'src/services/api/stockItemApiService';
import type { PantryBelief } from 'src/models/pantryBelief';

// module-level cache of the Zero-Input Pantry beliefs so the stock
// overview (many rows) and the detail page share one fetch. Additive: the
// belief is an overlay beside the recorded level, never a replacement.
//
// Gated server-side on the per-user `inferred_pantry_enabled` pref — when
// off, the endpoint returns `enabled: false` and we hold an empty map so no
// chip renders.

const stockItemApi = new StockItemApiService();

const enabled = ref(false);
const beliefs = ref<Record<string, PantryBelief>>({});
const loaded = ref(false);
const loading = ref(false);

export function usePantryBeliefs() {
    async function loadAsync(force = false): Promise<void> {
        if (loading.value) return;
        if (loaded.value && !force) return;
        loading.value = true;
        try {
            const result = await stockItemApi.getPantryBeliefsAsync();
            enabled.value = result.enabled;
            beliefs.value = result.beliefs ?? {};
            loaded.value = true;
        } catch {
            // Non-fatal — the chip just doesn't render. The recorded level
            // (the source of truth for shopping/cooking) is unaffected.
            enabled.value = false;
            beliefs.value = {};
        } finally {
            loading.value = false;
        }
    }

    function beliefFor(stockItemId: string): PantryBelief | null {
        if (!enabled.value) return null;
        return beliefs.value[stockItemId] ?? null;
    }

    /** Invalidate the cache (e.g. after a level change / quick-check) so the
     *  next `loadAsync` refetches. */
    function invalidate(): void {
        loaded.value = false;
    }

    return {
        enabled: readonly(enabled),
        loaded: readonly(loaded),
        loadAsync,
        beliefFor,
        invalidate,
    };
}
