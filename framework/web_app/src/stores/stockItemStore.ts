import { defineStore } from 'pinia';
import type { StockItem } from 'src/models/StockItem';
import StockItemApiService, { CreateStockItemCommand } from 'src/services/api/StockItemApiService';
import { Ref, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {
    // States
    const stockItems: Ref<StockItem[]> = ref([])

    // Getters

    // Actions
    const getStockItemsAsync = async () => await stockItemApiService
        .getAllAsync()
        .then((res) => stockItems.value = res)

    const createStockItemAsync = async (stockItemToCreate: CreateStockItemCommand) => await stockItemApiService
        .createAsync(stockItemToCreate)
        .then(async (res) => stockItems.value.push(await stockItemApiService.getAsync(res.id)))

    const updateStockLevelAsync = async (stockItemID: string, stockLevelID: string) => await stockItemApiService
        .updateAsync(stockItemID, { stock_level_id: stockLevelID })
        .then(async () => {
            // TODO: Loading
            const stockItemIndex = stockItems.value.findIndex(si => si.stock_item_id == stockItemID);
            stockItems.value[stockItemIndex] = await stockItemApiService.getAsync(stockItemID);
        })

    return { stockItems, getStockItemsAsync, createStockItemAsync, updateStockLevelAsync }
});
