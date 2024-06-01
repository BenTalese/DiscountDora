import { defineStore } from 'pinia';
import type { StockItem } from 'src/models/StockItem';
import StockItemApiService, { CreateStockItemCommand } from 'src/services/api/StockItemApiService';
import { readonly, Ref, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {

    //#region Stock Items

    const stockItems: Ref<StockItem[]> = ref([])

    const getStockItemsAsync = async () => await stockItemApiService
        .getAllAsync()
        .then((stockItemData) => {
            const collator = new Intl.Collator('en', { 'sensitivity': 'base' });

            stockItems.value = stockItemData.sort((si1, si2) =>
                collator.compare(si1.name, si2.name));
        })

    const getStockItemAsync = async (stockItemID: string) => await stockItemApiService
        .getAsync(stockItemID)

    const createStockItemAsync = async (stockItemToCreate: CreateStockItemCommand) => await stockItemApiService
        .createAsync(stockItemToCreate)
        .then(async (res) => stockItems.value.push((await stockItemApiService.getAsync(res.id))[0]))

    // TODO: Check Atif's idea for simpler actions
    async function updateStockLevelAsync(stockItemID: string, stockLevelID: string) {
        const stockItemIndex = stockItems.value.findIndex(si => si.stock_item_id == stockItemID);
        const originalStockLevel = stockItems.value[stockItemIndex].stock_level_id
        stockItems.value[stockItemIndex].stock_level_id = stockLevelID

        await stockItemApiService
            .updateAsync(stockItemID, { stock_level_id: stockLevelID })
            .then(async () => stockItems.value[stockItemIndex] = (await getStockItemAsync(stockItemID))[0])
            .catch(() => {
                stockItems.value[stockItemIndex].stock_level_id = originalStockLevel
            })
    }

    //#endregion Stock Items

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync
    }
});

