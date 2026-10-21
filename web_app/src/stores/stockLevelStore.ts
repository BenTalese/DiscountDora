import { acceptHMRUpdate, defineStore } from 'pinia';
import type { StockLevel } from 'src/models/stockLevel';
import StockLevelApiService from 'src/services/api/stockLevelApiService';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockLevelApiService = new StockLevelApiService();

export const useStockLevelStore = defineStore('stockLevel', () => {
    //#region Stock Levels

    const stockLevels: Ref<StockLevel[]> = ref([]);
    let hydrated = false;
    let inflight: Promise<void> | null = null;

    const getStockLevelsAsync = (): Promise<void> =>
        stockLevelApiService
            .getAllAsync()
            .then((page) => {
                stockLevels.value = [...page.items].sort((sl1, sl2) => sl1.sequence - sl2.sequence);
                hydrated = true;
            });

    /** R-016 — lazy hydration. Returns the cached collection if it's already
     *  populated, dedupes concurrent first-time loads. Force a refetch by
     *  calling `getStockLevelsAsync` directly. */
    const ensureLoadedAsync = (): Promise<void> => {
        if (hydrated) return Promise.resolve();
        inflight ??= getStockLevelsAsync().finally(() => { inflight = null; });
        return inflight;
    };

    //#endregion Stock Levels

    return {
        stockLevels: readonly(stockLevels),
        getStockLevelsAsync,
        ensureLoadedAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStockLevelStore, import.meta.hot));
}
