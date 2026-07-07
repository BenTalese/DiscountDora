// end-to-end wiring for the BuyVerdictCard's `mark_stocked` +
// `remove_from_list` one-tap actions.
//
// The verdict endpoint (`_pick_action` in `get_buy_verdict.py`) returns
// one of five action kinds; three are already handled by every consumer
// (`add_to_list` via the quick-add / cart button seams, `skip` = user
// dismisses, `none` = no action). The two remaining kinds needed shared
// mutation seams — same math in every caller — so they live here as one
// R-001 composable and every page (`StockOverview`, `StockItemDetailPage`,
// `ShoppingListDetail`) delegates.
//
// R-003 — no duplicated mutation paths: `markStocked` reuses
// `stockItemStore.updateStockLevelAsync` (the same call the row's stock-
// level dropdown makes), and `removeFromAllOpenLists` reuses
// `useShoppingListActions.removeFromAllLists` (the same call the "remove
// from every list" popover uses).

import { Notify } from 'quasar';
import { STOCKED_SEQUENCE } from 'src/helpers/stockStatus';
import { invalidateBuyVerdict } from 'src/composables/useBuyVerdict';
import { usePantryBeliefs } from 'src/composables/usePantryBeliefs';
import { useShoppingListActions } from 'src/composables/useShoppingListActions';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import { useStockItemStore } from 'src/stores/stockItemStore';
import { useStockLevelStore } from 'src/stores/stockLevelStore';
import { storeToRefs } from 'pinia';

export function useBuyVerdictActions() {
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { summaries } = storeToRefs(shoppingListStore);
    const slActions = useShoppingListActions();
    const pantryBeliefs = usePantryBeliefs();

    /**
     * Move a stock item to the "Well-Stocked" level (sequence 0) and
     * invalidate any dependent belief/verdict caches. Returns `true` on
     * success. The consumer decides whether to also reload page-local
     * detail state; this helper stays store-agnostic beyond the mutation.
     */
    async function markStocked(stockItemId: string): Promise<boolean> {
        await stockLevelStore.ensureLoadedAsync();
        const stockedLevel = stockLevels.value.find(
            (sl) => sl.sequence === STOCKED_SEQUENCE,
        );
        if (!stockedLevel) {
            // A brand-new install could theoretically hit this before the
            // seed runs; the seed always produces the three canonical bands
            // so it's a genuine misconfiguration signal, not a UX case.
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't find the Well-Stocked band — check Settings → Stock levels.",
                timeout: 4000,
            });
            return false;
        }
        try {
            await stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId,
                stock_level_id: stockedLevel.stock_level_id,
            });
            invalidateBuyVerdict(stockItemId);
            pantryBeliefs.invalidate();
            void pantryBeliefs.loadAsync(true);
            Notify.create({
                type: 'positive',
                position: 'bottom-right',
                message: 'Marked as Well-Stocked.',
                timeout: 2000,
            });
            return true;
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't update the stock level.",
                caption: err instanceof Error ? err.message : String(err),
                timeout: 4000,
            });
            return false;
        }
    }

    /**
     * Remove a stock item from every open (non-`done`) shopping list. The
     * server's `remove-by-stock-item` endpoint is a no-op when the list
     * doesn't contain the item, so it's safe to fan out over every open
     * summary — `removeFromAllLists` already tolerates per-list errors and
     * summarises the outcome in a single toast.
     *
     * Returns the count actually removed (0 if nothing matched — the
     * verdict card only surfaces this action when the server saw at least
     * one hit, so 0 means the state changed between verdict and tap).
     */
    async function removeFromAllOpenLists(stockItemId: string): Promise<number> {
        await shoppingListStore.ensureLoadedAsync();
        const openListIds = summaries.value
            .filter((s) => s.status !== 'done')
            .map((s) => s.shopping_list_id);
        if (openListIds.length === 0) return 0;
        const removed = await slActions.removeFromAllLists(stockItemId, openListIds);
        if (removed > 0) invalidateBuyVerdict(stockItemId);
        return removed;
    }

    return { markStocked, removeFromAllOpenLists };
}
