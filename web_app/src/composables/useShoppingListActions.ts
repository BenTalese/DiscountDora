import { useQuasar } from 'quasar';
import type { AddLineCommand } from 'src/services/api/shoppingListApiService';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { useShoppingListStore } from 'src/stores/shoppingListStore';

const api = new ShoppingListApiService();

/**
 * Cross-feature actions for a shopping list. Screens compose these so
 * add-items / finish-shopping behave identically wherever they are triggered
 * (lists overview, list detail, QuickAddSheet, cook mode).
 *
 * Call from a component `setup`.
 *
 * Chunk 2: `setPrimary` is gone — "primary" is now inferred from DRAFT-count
 * by the server resolver and the client's sessionStorage pick.
 */
export function useShoppingListActions() {
    const $q = useQuasar();
    const shoppingListStore = useShoppingListStore();

    const notifyOk = (message: string) =>
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    const notifyErr = (message: string, caption?: string) =>
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            ...(caption ? { caption } : {}),
        });

    /**
     * Add one or more stock items to a list. Each entry may carry a quantity
     * and a pre-selected merchant offer. Returns counts so callers can phrase
     * their own messaging if they want.
     */
    async function addItems(
        listId: string,
        items: AddLineCommand[],
    ): Promise<{ added: number; already: number }> {
        let added = 0;
        let already = 0;
        try {
            for (const item of items) {
                const result = await api.addLineAsync(listId, item);
                if (result.already_on_list) already++;
                else added++;
            }
            await shoppingListStore.refreshAsync();
            notifyOk(
                `${added} added${already > 0 ? `, ${already} already on list` : ''}.`,
            );
        } catch (err) {
            notifyErr('Could not add all items.', String(err));
        }
        return { added, already };
    }

    /**
     * C-7 Chunk 1 — remove a stock item from a single list. Returns true on
     * success, false on failure. The caller composes higher-level UX
     * (toast, multi-list popover); this helper handles the API round-trip
     * + store refresh in one place so every consumer reads the same
     * membership state afterward.
     */
    async function removeFromList(
        listId: string,
        stockItemId: string,
    ): Promise<boolean> {
        try {
            await api.removeByStockItemFromListAsync(listId, stockItemId);
            await shoppingListStore.refreshAsync();
            return true;
        } catch (err) {
            notifyErr('Could not remove from list.', String(err));
            return false;
        }
    }

    /**
     * C-7 Chunk 1 — remove a stock item from every unticked list it's on.
     * One summary toast at the end (decision 6 — even for the "remove from
     * all" branch in the multi-list popover). Returns the count actually
     * removed.
     */
    async function removeFromAllLists(
        stockItemId: string,
        listIds: string[],
    ): Promise<number> {
        let removed = 0;
        for (const listId of listIds) {
            try {
                await api.removeByStockItemFromListAsync(listId, stockItemId);
                removed++;
            } catch {
                // Continue; one bad list shouldn't block the others.
            }
        }
        if (removed > 0) await shoppingListStore.refreshAsync();
        if (removed === listIds.length && removed > 0) {
            notifyOk(`Removed from ${removed} list${removed === 1 ? '' : 's'}.`);
        } else if (removed > 0) {
            notifyOk(`Removed from ${removed} of ${listIds.length} lists.`);
        } else if (listIds.length > 0) {
            notifyErr('Could not remove from any list.');
        }
        return removed;
    }

    /**
     * Finish shopping: archives the list, bumps stock levels for ticked items.
     */
    async function finishShopping(listId: string) {
        try {
            const result = await api.finishAsync(listId);
            await shoppingListStore.refreshAsync();
            notifyOk(
                `Shopping finished — ${result.items_restocked} item${
                    result.items_restocked === 1 ? '' : 's'
                } restocked.`,
            );
            return result;
        } catch (err) {
            notifyErr('Could not finish shopping.', String(err));
            return null;
        }
    }

    return { addItems, finishShopping, removeFromList, removeFromAllLists };
}
