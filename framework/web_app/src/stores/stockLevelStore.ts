import { defineStore } from 'pinia';
import { StockLevel } from 'src/models/StockLevel';
import StockLevelApiService from 'src/services/api/StockLevelApiService';
import { readonly, Ref, ref } from 'vue';

const stockLevelApiService = new StockLevelApiService();

export const useStockLevelStore = defineStore('stockLevel', () => {

    //#region Stock Levels

    const stockLevels: Ref<StockLevel[]> = ref([])

    function getStockLevelColour(stockLevelID: string) {
        const stockLevel = stockLevels.value.find(
            (sl) => sl.stock_level_id == stockLevelID
        );

        if (stockLevel?.name == 'Well-Stocked') {
            return 'green';
        }

        if (stockLevel?.name == 'Sufficient Stock') {
            return 'yellow';
        }

        if (stockLevel?.name == 'Low Stock') {
            return 'red';
        }

        if (stockLevel?.name == 'Out of Stock') {
            return 'grey';
        }

        console.error(`Colour not configured for stock level '${stockLevel?.name}'.`)
    }

    const getStockLevelsAsync = async () => await stockLevelApiService
        .getAllAsync()
        .then((res) => stockLevels.value = res.sort((sl1, sl2) => sl1.sequence - sl2.sequence))

    //#endregion Stock Levels

    return {
        stockLevels: readonly(stockLevels),
        getStockLevelColour,
        getStockLevelsAsync
    }
});
