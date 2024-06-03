import { defineStore } from 'pinia';
import type { StockItem } from 'src/models/StockItem';
import StockItemApiService, { CreateStockItemCommand } from 'src/services/api/StockItemApiService';
import { registerRollback } from 'src/services/errorHandling/rollbackRegistry';
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

    // TODO: Check Atif's idea for simpler actions
    async function updateStockLevelAsync(stockItemID: string, stockLevelID: string) {
        const stockItemIndex = stockItems.value.findIndex(si => si.stock_item_id == stockItemID);
        const originalStockLevel = stockItems.value[stockItemIndex].stock_level_id
        stockItems.value[stockItemIndex].stock_level_id = stockLevelID

        registerRollback(() => {
            stockItems.value[stockItemIndex].stock_level_id = originalStockLevel;
        });

        await stockItemApiService
            .updateAsync(stockItemID, { stock_level_id: stockLevelID })
            .then(async () => stockItems.value[stockItemIndex] = (await getStockItemAsync(stockItemID))[0])
    }

    //#endregion Stock Items

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync
    }
});
