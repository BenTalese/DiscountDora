import { acceptHMRUpdate, defineStore } from 'pinia';
import type { StockItem } from 'src/models/stockItem';
import type {
    CreateStockItemCommand,
    UpdateStockItemCommand
} from 'src/services/api/stockItemApiService';
import StockItemApiService from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {
    const stockItems: Ref<StockItem[]> = ref([]);
    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    const getStockItemsAsync = () =>
        stockItemApiService.getAllAsync().then((page) => {
            stockItems.value = [...page.items].sort((si1, si2) =>
                collator.compare(si1.name, si2.name)
            );
        });

    const createStockItemAsync = async (stockItemToCreate: CreateStockItemCommand) => {
        const created = await stockItemApiService.createAsync(stockItemToCreate);
        // The API returns the full DTO body when available.
        const entity =
            'stock_item_id' in created
                ? (created as unknown as StockItem)
                : await stockItemApiService.getAsync(created.id as string);
        stockItems.value.push(entity);
        stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
    };

    /** Optimistic stock-level swap with rollback if the API rejects. */
    async function updateStockLevelAsync(stockItemToUpdate: UpdateStockItemCommand) {
        const stockItemIndex = stockItems.value.findIndex(
            (si) => si.stock_item_id == stockItemToUpdate.stock_item_id
        );
        if (stockItemIndex < 0) return;

        const originalStockLevel = stockItems.value[stockItemIndex]!.stock_level_id;
        stockItems.value[stockItemIndex]!.stock_level_id = stockItemToUpdate.stock_level_id!;

        registerRollback(() => {
            stockItems.value[stockItemIndex]!.stock_level_id = originalStockLevel;
        });

        await stockItemApiService
            .updateAsync(stockItemToUpdate)
            .then(
                async () =>
                    (stockItems.value[stockItemIndex] = await stockItemApiService.getAsync(
                        stockItemToUpdate.stock_item_id
                    ))
            )
            .then(clearRollbacks);
    }

    /** General-purpose update for the detail page (name/notes/location/etc). */
    const updateStockItemAsync = async (cmd: UpdateStockItemCommand) => {
        await stockItemApiService.updateAsync(cmd);
        const refreshed = await stockItemApiService.getAsync(cmd.stock_item_id);
        const idx = stockItems.value.findIndex((si) => si.stock_item_id === cmd.stock_item_id);
        if (idx >= 0) {
            stockItems.value[idx] = refreshed;
            stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
        }
    };

    const deleteStockItemAsync = async (stockItemID: string) => {
        await stockItemApiService.deleteAsync(stockItemID);
        stockItems.value = stockItems.value.filter((si) => si.stock_item_id !== stockItemID);
    };

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync,
        updateStockItemAsync,
        deleteStockItemAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStockItemStore, import.meta.hot));
}
