import { defineStore } from 'pinia';
import type { StockItem } from 'src/models/StockItem';
import StockItemApiService from 'src/services/api/StockItemApiService';
import { Ref, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {
    // States
    const stockItems: Ref<StockItem[]> = ref([])

    // Getters

    // Actions
    const getStockItems = async () => await stockItemApiService
        .getAll()
        .then((res) => stockItems.value = res)

    return { stockItems, getStockItems }
});
