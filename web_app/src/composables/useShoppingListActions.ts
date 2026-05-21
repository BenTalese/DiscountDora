import { useQuasar } from 'quasar';
import type { AddLineCommand } from 'src/services/api/shoppingListApiService';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import { useRouter } from 'vue-router';

const api = new ShoppingListApiService();

/**
 * Cross-feature actions for a shopping list. Screens compose these so
 * add-items / set-primary / finish-shopping behave identically wherever they
 * are triggered (lists overview, list detail, QuickAddSheet, cook mode).
 *
 * Call from a component `setup`.
 */
export function useShoppingListActions() {
    const $q = useQuasar();
    const router = useRouter();
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

    /** Make this list the user's primary list. */
    async function setPrimary(listId: string) {
        try {
            await api.updateAsync(listId, { is_primary: true });
            await shoppingListStore.refreshAsync();
            notifyOk('Set as primary list.');
        } catch (err) {
            notifyErr('Could not set primary.', String(err));
        }
    }

    /**
     * Finish shopping: archives the list, bumps stock levels for ticked items,
     * and (if the backend opened one) navigates to the new primary list.
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
            if (result.new_primary_list_id) {
                void router.push(`/shopping-lists/${result.new_primary_list_id}`);
            }
            return result;
        } catch (err) {
            notifyErr('Could not finish shopping.', String(err));
            return null;
        }
    }

    return { addItems, setPrimary, finishShopping };
}
