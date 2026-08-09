import { acceptHMRUpdate, defineStore } from 'pinia';
import { Notify } from 'quasar';
import {
    tryWithQueue,
    type QueueableMutationKind,
} from 'src/composables/useOfflineQueue';
import type { StockItem } from 'src/models/stockItem';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import type {
    CreateStockItemCommand,
    UpdateStockItemCommand,
    UpdateStockItemResponse
} from 'src/services/api/stockItemApiService';
import StockItemApiService from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

function stockItemUrl(stockItemId: string): string {
    return `${resolveBaseURL()}/stock-items/${stockItemId}`;
}

// Pick the queue kind that best describes a PATCH payload, so the queued
// label / drain notification reads naturally ("Marked restocked" vs
// "Push expiry" vs the catch-all). Falls back to generic stock_level_update.
function classifyUpdate(cmd: UpdateStockItemCommand): {
    kind: QueueableMutationKind;
    label: string;
} {
    if ('expiry_date' in cmd) {
        if (cmd.expiry_date === null) return { kind: 'clear_expiry', label: 'Clear expiry' };
        return { kind: 'push_expiry', label: 'Push expiry' };
    }
    if ('is_open' in cmd) return { kind: 'mark_open', label: 'Mark opened' };
    if ('stock_level_id' in cmd) {
        return { kind: 'stock_level_update', label: 'Update stock level' };
    }
    return { kind: 'stock_level_update', label: 'Update stock item' };
}

export const useStockItemStore = defineStore('stockItem', () => {
    const stockItems: Ref<StockItem[]> = ref([]);
    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    /** When a level-change PATCH transitions a stock item to Low/Out and
     *  the install-wide auto-add mode says fire (FU-511: `off` never,
     *  `essential_only` iff `is_essential`, `all` always), the server drops
     *  it onto the unambiguous draft list and returns
     *  `{ auto_added: { line_id, shopping_list_id } }`. Fire a positive
     *  toast naming the list + the item, and refresh the shopping-list
     *  store so the new line renders everywhere it's watched. Silent
     *  no-op for the 204 no-trigger case. */
    async function handleAutoAddedResponse(
        stockItemId: string,
        result: UpdateStockItemResponse | { queued: true },
    ): Promise<void> {
        if (
            !result || typeof result !== 'object' || 'queued' in result
            || !('auto_added' in result) || !result.auto_added
        ) {
            return;
        }
        const shoppingListStore = useShoppingListStore();
        await shoppingListStore.refreshAsync();
        const item = stockItems.value.find((si) => si.stock_item_id === stockItemId);
        const itemName = item?.name ?? 'that item';
        const listSummary = shoppingListStore.summaries.find(
            (s) => s.shopping_list_id === result.auto_added!.shopping_list_id,
        );
        const listName = listSummary?.display_name ?? 'your list';
        Notify.create({
            type: 'positive',
            position: 'bottom-right',
            message: `Added ${itemName} to ${listName}.`,
            caption: 'Auto-added because it went low.',
            timeout: 3000,
        });
    }

    let hydrated = false;
    let inflight: Promise<void> | null = null;

    /** C-1 Stock Overview Chunk 1 — page until exhausted so a pantry of
     *  >50 items doesn't silently get truncated to the first page
     *  (FU-035). Callers that only need a quick prefix (autocomplete-
     *  style) should hit `getAllAsync` on the service directly. */
    const getStockItemsAsync = (): Promise<void> =>
        stockItemApiService.getAllPagesAsync().then((items) => {
            stockItems.value = [...items].sort((si1, si2) =>
                collator.compare(si1.name, si2.name)
            );
            hydrated = true;
        });

    /** R-016 — lazy hydration. Use this in `onMounted` / `beforeRouteEnter`
     *  when you need the collection populated but don't care about a forced
     *  refresh. Call `getStockItemsAsync` directly for an explicit refetch
     *  (post-mutation, pull-to-refresh). */
    const ensureLoadedAsync = (): Promise<void> => {
        if (hydrated) return Promise.resolve();
        inflight ??= getStockItemsAsync().finally(() => { inflight = null; });
        return inflight;
    };

    const createStockItemAsync = async (
        stockItemToCreate: CreateStockItemCommand,
    ): Promise<StockItem> => {
        const created = await stockItemApiService.createAsync(stockItemToCreate);
        // The API returns the full DTO body when available.
        const entity =
            'stock_item_id' in created
                ? (created as unknown as StockItem)
                : await stockItemApiService.getAsync(created.id as string);
        stockItems.value.push(entity);
        stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
        return entity;
    };

    /** Optimistic stock-level swap with rollback if the API rejects.
     *  Network failures are absorbed into the offline queue so the user
     *  can keep ticking the kitchen over without internet. */
    async function updateStockLevelAsync(stockItemToUpdate: UpdateStockItemCommand) {
        const stockItemIndex = stockItems.value.findIndex(
            (si) => si.stock_item_id == stockItemToUpdate.stock_item_id
        );
        if (stockItemIndex < 0) return;

        const originalStockLevel = stockItems.value[stockItemIndex]!.stock_level_id;
        const nextStockLevel = stockItemToUpdate.stock_level_id!;
        stockItems.value[stockItemIndex]!.stock_level_id = nextStockLevel;

        registerRollback(() => {
            stockItems.value[stockItemIndex]!.stock_level_id = originalStockLevel;
        });

        const { stock_item_id, ...payload } = stockItemToUpdate;
        const result = await tryWithQueue(
            () => stockItemApiService.updateAsync(stockItemToUpdate),
            {
                url: stockItemUrl(stock_item_id),
                method: 'PATCH',
                body: payload,
                kind: 'stock_level_update',
                label: 'Update stock level',
            },
        );
        // Online path: refetch the canonical row so any server-derived
        // fields (timestamps, normalised values) are picked up. Offline
        // path: trust the optimistic value until the queue drains.
        if (typeof result !== 'object' || result === null || !('queued' in result)) {
            stockItems.value[stockItemIndex] = await stockItemApiService.getAsync(stock_item_id);
        }
        clearRollbacks();
        // level transition may have triggered the auto-add hook.
        await handleAutoAddedResponse(stock_item_id, result);
    }

    /** General-purpose update for the detail page (name/notes/location/etc).
     *  Same offline-queue treatment as the level swap above for the kinds
     *  registered (mark opened/restocked, push/clear expiry). */
    const updateStockItemAsync = async (cmd: UpdateStockItemCommand) => {
        const { stock_item_id, ...payload } = cmd;
        const { kind, label } = classifyUpdate(cmd);
        const result = await tryWithQueue(
            () => stockItemApiService.updateAsync(cmd),
            {
                url: stockItemUrl(stock_item_id),
                method: 'PATCH',
                body: payload,
                kind,
                label,
            },
        );
        if (typeof result === 'object' && result !== null && 'queued' in result) {
            // Optimistic only — caller's UI already reflects intent; we
            // don't have a canonical refresh until the queue drains.
            return;
        }
        const refreshed = await stockItemApiService.getAsync(stock_item_id);
        const idx = stockItems.value.findIndex((si) => si.stock_item_id === stock_item_id);
        if (idx >= 0) {
            stockItems.value[idx] = refreshed;
            stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
        }
        // `saveField`-style level changes on the detail page also
        // go through this path (they carry `stock_level_id`), so the
        // auto-add hook can fire here too.
        await handleAutoAddedResponse(stock_item_id, result);
    };

    const deleteStockItemAsync = async (stockItemID: string) => {
        await stockItemApiService.deleteAsync(stockItemID);
        stockItems.value = stockItems.value.filter((si) => si.stock_item_id !== stockItemID);
    };

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        ensureLoadedAsync,
        createStockItemAsync,
        updateStockLevelAsync,
        updateStockItemAsync,
        deleteStockItemAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStockItemStore, import.meta.hot));
}
