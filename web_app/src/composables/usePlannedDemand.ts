import { readonly, ref } from 'vue';
import StockItemApiService from 'src/services/api/stockItemApiService';
import type { PlannedDemand } from 'src/models/plannedDemand';

// Module-level cache of the planned-demand overlay, so the stock overview
// (many rows) and the detail page share one fetch. Same shape as
// `usePantryBeliefs` on purpose — they are two overlays on the same surfaces
// and one pattern for both is one thing to understand rather than two.
//
// Gated server-side on the install-wide meal-planner switch: with no planner
// there is no plan, so the endpoint returns `enabled: false` and we hold an
// empty map. Note this is a *feature* gate, not a preference — unlike the
// belief, planned demand is a plain fact about the user's own plan rather
// than an inference, so there is nothing to opt out of.

const stockItemApi = new StockItemApiService();

const enabled = ref(false);
const horizonDays = ref(0);
const demand = ref<Record<string, PlannedDemand>>({});
const loaded = ref(false);
const loading = ref(false);

export function usePlannedDemand() {
    async function loadAsync(force = false): Promise<void> {
        if (loading.value) return;
        if (loaded.value && !force) return;
        loading.value = true;
        try {
            const result = await stockItemApi.getPlannedDemandAsync();
            enabled.value = result.enabled;
            horizonDays.value = result.horizon_days ?? 0;
            demand.value = result.demand ?? {};
            loaded.value = true;
        } catch {
            // Non-fatal — the card just doesn't render. Nothing downstream
            // reads this; it is commentary beside the recorded level.
            enabled.value = false;
            demand.value = {};
        } finally {
            loading.value = false;
        }
    }

    function demandFor(stockItemId: string): PlannedDemand | null {
        if (!enabled.value) return null;
        return demand.value[stockItemId] ?? null;
    }

    /** Invalidate the cache — after a plan edit, a cook, or a level change
     *  (which can move the urgency grade without moving the counts). */
    function invalidate(): void {
        loaded.value = false;
    }

    return {
        enabled: readonly(enabled),
        horizonDays: readonly(horizonDays),
        loaded: readonly(loaded),
        loadAsync,
        demandFor,
        invalidate,
    };
}
