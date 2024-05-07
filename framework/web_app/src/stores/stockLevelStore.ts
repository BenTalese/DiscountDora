import { defineStore } from 'pinia';
import { StockLevel } from 'src/models/StockLevel';
import StockLevelApiService from 'src/services/api/StockLevelApiService';
import { Ref, ref } from 'vue';

const stockLevelApiService = new StockLevelApiService();

export const useStockLevelStore = defineStore('stockLevel', () => {

    // region Stock Levels

    const stockLevels: Ref<StockLevel[]> = ref([])

    const getStockLevelsAsync = async () => await stockLevelApiService
        .getAllAsync()
        .then((res) => stockLevels.value = res.sort((sl1, sl2) => sl1.sequence - sl2.sequence))

    // endregion Stock Levels

    return {
        stockLevels,
        getStockLevelsAsync
    }
});
