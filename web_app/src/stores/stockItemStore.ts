import { acceptHMRUpdate, defineStore } from 'pinia';
import { Notify } from 'quasar';
import type { StockItem } from 'src/models/stockItem';
import type {
    CreateStockItemCommand,
    UpdateStockItemCommand,
    UpdateStockItemResponse
} from 'src/services/api/stockItemApiService';
import StockItemApiService from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import { useRecipeStore } from 'src/stores/recipeStore';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

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
        result: UpdateStockItemResponse,
    ): Promise<void> {
        if (
            !result || typeof result !== 'object'
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

    /** Every recipe DTO carries pantry-derived facts — cookability, the
     *  missing/expiring counts, the Zero-Input hint, and in complex nutrition
     *  mode the rollup behind the kcal figure and the front-of-pack rating.
     *  A stock write can move any of them, so the recipe list is marked stale
     *  here rather than each recipe surface guessing which writes matter
     *  (R-003). Called from every mutation below, not just the nutrition
     *  link: a level change moves `cookable`, a delete moves `missing_count`.
     *
     *  This only sets a flag — the refetch happens on the next
     *  `ensureLoadedAsync`, so a stocktake run doesn't fire one request per
     *  item. Store lookup is inside the function (not module scope) because
     *  Pinia stores can only be resolved once the active pinia exists. */
    function invalidateDerivedRecipeFacts(): void {
        useRecipeStore().invalidateRecipes();
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
        invalidateDerivedRecipeFacts();
        return entity;
    };

    /** Optimistic stock-level swap with rollback if the API rejects.
     *  Offline is read-only (2026-08-23): a network failure rejects like any
     *  other, the registered rollback restores the previous level, and the
     *  user is told — nothing is buffered and re-promised. */
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

        const { stock_item_id } = stockItemToUpdate;
        const result = await stockItemApiService.updateAsync(stockItemToUpdate);
        // Refetch the canonical row so any server-derived fields
        // (timestamps, normalised values, the attention flag) are picked up.
        stockItems.value[stockItemIndex] = await stockItemApiService.getAsync(stock_item_id);
        clearRollbacks();
        invalidateDerivedRecipeFacts();
        // level transition may have triggered the auto-add hook.
        await handleAutoAddedResponse(stock_item_id, result);
    }

    /** General-purpose update for the detail page (name/notes/location/etc).
     *  Rejects on a network failure like any other error — callers own the
     *  toast and any UI they optimistically moved. */
    const updateStockItemAsync = async (cmd: UpdateStockItemCommand) => {
        const { stock_item_id } = cmd;
        const result = await stockItemApiService.updateAsync(cmd);
        const refreshed = await stockItemApiService.getAsync(stock_item_id);
        const idx = stockItems.value.findIndex((si) => si.stock_item_id === stock_item_id);
        if (idx >= 0) {
            stockItems.value[idx] = refreshed;
            stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
        }
        invalidateDerivedRecipeFacts();
        // `saveField`-style level changes on the detail page also
        // go through this path (they carry `stock_level_id`), so the
        // auto-add hook can fire here too.
        await handleAutoAddedResponse(stock_item_id, result);
    };

    const deleteStockItemAsync = async (stockItemID: string) => {
        await stockItemApiService.deleteAsync(stockItemID);
        stockItems.value = stockItems.value.filter((si) => si.stock_item_id !== stockItemID);
        invalidateDerivedRecipeFacts();
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
