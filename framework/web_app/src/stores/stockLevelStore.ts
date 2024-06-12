import { defineStore } from 'pinia';
import { StockLevel } from 'src/models/stockLevel';
import StockLevelApiService from 'src/services/api/stockLevelApiService';
import { readonly, Ref, ref } from 'vue';

const stockLevelApiService = new StockLevelApiService();

export const useStockLevelStore = defineStore('stockLevel', () => {

    //#region Stock Levels

    const stockLevels: Ref<StockLevel[]> = ref([])

    const getStockLevelsAsync = () => stockLevelApiService
        .getAllAsync()
        .then((res) => stockLevels.value = res.sort((sl1, sl2) => sl1.sequence - sl2.sequence))

    //#endregion Stock Levels

    return {
        stockLevels: readonly(stockLevels),
        getStockLevelsAsync
    }
});
