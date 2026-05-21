import { acceptHMRUpdate, defineStore } from 'pinia';
import StockLocationApiService, {
    type CreateStockLocationCommand,
    type StockLocation,
    type UpdateStockLocationCommand
} from 'src/services/api/stockLocationApiService';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockLocationApiService = new StockLocationApiService();

export const useStockLocationStore = defineStore('stockLocation', () => {
    const stockLocations: Ref<StockLocation[]> = ref([]);
    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    const sort = () =>
        stockLocations.value.sort((a, b) => collator.compare(a.name, b.name));

    const getStockLocationsAsync = () =>
        stockLocationApiService.getAllAsync().then((page) => {
            stockLocations.value = [...page.items];
            sort();
        });

    const createStockLocationAsync = async (command: CreateStockLocationCommand) => {
        const created = await stockLocationApiService.createAsync(command);
        const entity =
            'stock_location_id' in created
                ? (created as unknown as StockLocation)
                : { stock_location_id: created.id as string, name: command.name };
        stockLocations.value.push(entity);
        sort();
    };

    const updateStockLocationAsync = async (command: UpdateStockLocationCommand) => {
        await stockLocationApiService.updateAsync(command);
        const idx = stockLocations.value.findIndex(
            (l) => l.stock_location_id === command.stock_location_id
        );
        if (idx >= 0) {
            stockLocations.value[idx] = {
                ...stockLocations.value[idx]!,
                name: command.name
            };
            sort();
        }
    };

    const deleteStockLocationAsync = async (stockLocationId: string) => {
        await stockLocationApiService.deleteAsync(stockLocationId);
        stockLocations.value = stockLocations.value.filter(
            (l) => l.stock_location_id !== stockLocationId
        );
    };

    return {
        stockLocations: readonly(stockLocations),
        getStockLocationsAsync,
        createStockLocationAsync,
        updateStockLocationAsync,
        deleteStockLocationAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStockLocationStore, import.meta.hot));
}
