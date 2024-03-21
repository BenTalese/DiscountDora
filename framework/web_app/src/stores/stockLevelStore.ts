import { defineStore } from 'pinia';
import { StockLevel } from 'src/models/StockLevel';
import StockLevelApiService from 'src/services/api/StockLevelApiService';
import { Ref, ref } from 'vue';

const stockLevelApiService = new StockLevelApiService();

export const useStockLevelStore = defineStore('stockLevel', () => {
    // States
    const stockLevels: Ref<StockLevel[]> = ref([])

    // Getters

    // Actions
    const getStockLevels = async () => await stockLevelApiService
        .getAll()
        .then((res) => stockLevels.value = res)

    return { stockLevels, getStockLevels }
});
