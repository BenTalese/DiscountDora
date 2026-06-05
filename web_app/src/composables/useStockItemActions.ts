import { storeToRefs } from 'pinia';
import { useQuasar } from 'quasar';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import { useStockItemStore } from 'src/stores/stockItemStore';
import { useStockLevelStore } from 'src/stores/stockLevelStore';
import { useRouter } from 'vue-router';

const shoppingListApi = new ShoppingListApiService();

/**
 * Cross-feature actions for a single stock item. Every screen that touches a
 * stock item routes through here so add-to-list / restock / expiry behave the
 * same everywhere (chips, bulk bars, detail toolbar, Dora quick-actions).
 *
 * Call from a component `setup` — it relies on the active router and Quasar
 * plugin for navigation and notifications.
 */
export function useStockItemActions() {
    const $q = useQuasar();
    const router = useRouter();
    const stockItemStore = useStockItemStore();
    const shoppingListStore = useShoppingListStore();
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    const notifyOk = (message: string) =>
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    const notifyErr = (message: string, caption?: string) =>
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            ...(caption ? { caption } : {}),
        });

    /** Add to the primary list (default) or a specific list. */
    async function addToList(stockItemId: string, listId?: string | null) {
        try {
            if (listId) {
                const result = await shoppingListApi.addLineAsync(listId, {
                    stock_item_id: stockItemId,
                });
                await shoppingListStore.refreshAsync();
                notifyOk(result.already_on_list ? 'Already on that list.' : 'Added to list.');
                return;
            }
            const result = await shoppingListApi.quickAddToPrimaryAsync(stockItemId);
            await shoppingListStore.refreshAsync();
            notifyOk(
                result.already_on_list
                    ? 'Already on your primary list.'
                    : 'Added to primary list.',
            );
        } catch {
            // Most likely cause: no primary list set.
            $q.dialog({
                title: 'No primary list',
                message: 'Pick or create a primary shopping list to use the cart shortcut.',
                ok: { label: 'Open lists', noCaps: true, color: 'primary' },
                cancel: { noCaps: true },
            }).onOk(() => void router.push('/shopping-lists'));
        }
    }

    /** Bump the level back to the most-stocked level (lowest sequence). */
    async function markRestocked(stockItemId: string) {
        const top = stockLevels.value[0];
        if (!top) {
            notifyErr('No stock levels configured.');
            return;
        }
        try {
            await stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId,
                stock_level_id: top.stock_level_id,
            });
            notifyOk('Marked restocked.');
        } catch (err) {
            notifyErr('Could not restock.', String(err));
        }
    }

    /** Push the expiry date forward by `days` from today. */
    async function pushExpiry(stockItemId: string, days = 7) {
        const next = new Date();
        next.setDate(next.getDate() + days);
        const iso = next.toISOString().slice(0, 10);
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: stockItemId,
                expiry_date: iso,
            });
            notifyOk(`Expiry pushed to ${iso}.`);
        } catch (err) {
            notifyErr('Could not update expiry.', String(err));
        }
    }

    function openDetail(stockItemId: string) {
        void router.push(`/stock/${stockItemId}`);
    }

    /** A stock item's substitutes live on its detail page (built in P2). */
    function findSubstitutes(stockItemId: string) {
        void router.push({ path: `/stock/${stockItemId}`, query: { section: 'substitutes' } });
    }

    /** Recipes that use this item — opens the recipes screen pre-filtered. */
    function seeRecipesUsing(stockItemId: string) {
        void router.push({ path: '/recipes', query: { usesStockItem: stockItemId } });
    }

    return {
        addToList,
        markRestocked,
        pushExpiry,
        openDetail,
        findSubstitutes,
        seeRecipesUsing,
    };
}
