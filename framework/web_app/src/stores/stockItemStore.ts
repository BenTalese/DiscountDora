import { defineStore, acceptHMRUpdate } from 'pinia';
import type { StockItem } from 'src/models/stockItem';
import StockItemApiService, { CreateStockItemCommand, UpdateStockItemCommand } from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import { readonly, Ref, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {

    //#region Stock Items

    const stockItems: Ref<StockItem[]> = ref([])

    const getStockItemsAsync = () => stockItemApiService
        .getAllAsync()
        .then((stockItemData) => {
            const collator = new Intl.Collator('en', { 'sensitivity': 'base' });

            stockItems.value = stockItemData.sort((si1, si2) =>
                collator.compare(si1.name, si2.name));
        })

    const getStockItemAsync = (stockItemID: string) => stockItemApiService
        .getAsync(stockItemID)

    const createStockItemAsync = (stockItemToCreate: CreateStockItemCommand) => stockItemApiService
        .createAsync(stockItemToCreate)
        .then(async (resource) => stockItems.value.push((await stockItemApiService.getAsync(resource.id))[0]))

    async function updateStockLevelAsync(stockItemToUpdate: UpdateStockItemCommand) {
        const stockItemIndex = stockItems.value.findIndex(si => si.stock_item_id == stockItemToUpdate.stock_item_id);
        const originalStockLevel = stockItems.value[stockItemIndex].stock_level_id
        stockItems.value[stockItemIndex].stock_level_id = stockItemToUpdate.stock_level_id!

        registerRollback(() => {
            stockItems.value[stockItemIndex].stock_level_id = originalStockLevel;
        });

        stockItemApiService
            .updateAsync(stockItemToUpdate)
            .then(async () => stockItems.value[stockItemIndex] = (await getStockItemAsync(stockItemToUpdate.stock_item_id))[0])
            .then(clearRollbacks)
    }

    //#endregion Stock Items

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync
    }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useStockItemStore, import.meta.hot));
}

