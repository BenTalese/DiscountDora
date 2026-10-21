import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Product } from 'src/models/product';
import type { CreateProductCommand, UpdateProductCommand } from 'src/services/api/productApiService';
import ProductApiService from 'src/services/api/productApiService';
import { readonly, ref } from 'vue';

const productApiService = new ProductApiService();

/**
 * Post-Phase-D shape: only what surfaces today reading `Product` rows out of
 * Dora's catalogue need. The in-app live product search + its filter / sort
 * state moved to the companion app along with the scraper itself.
 */
export const useProductStore = defineStore('product', () => {
    // initialised to `[]` (not `undefined`) so consumers reading
    // `productStore.products.value` before the first hydration get a stable
    // empty array instead of an "is it undefined yet?" tri-state.
    const products = ref<Product[]>([]);
    let hydrated = false;
    let inflight: Promise<void> | null = null;

    const getProductsAsync = (): Promise<void> =>
        productApiService.getAllAsync().then((page) => {
            products.value = page.items;
            hydrated = true;
        });

    /** R-016 — lazy hydration. See sibling stores. */
    const ensureLoadedAsync = (): Promise<void> => {
        if (hydrated) return Promise.resolve();
        inflight ??= getProductsAsync().finally(() => { inflight = null; });
        return inflight;
    };

    const createProductAsync = (command: CreateProductCommand): Promise<void> =>
        productApiService.createAsync(command).then(() => getProductsAsync());

    const updateProductAsync = (command: UpdateProductCommand): Promise<void> =>
        productApiService.updateAsync(command).then(() => getProductsAsync());

    return {
        products: readonly(products),
        createProductAsync,
        getProductsAsync,
        ensureLoadedAsync,
        updateProductAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useProductStore, import.meta.hot));
}
