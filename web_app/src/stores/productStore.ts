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
    const products = ref<Product[]>();

    const getProductsAsync = (): Promise<void> =>
        productApiService.getAllAsync().then((page) => {
            products.value = page.items;
        });

    const createProductAsync = (command: CreateProductCommand): Promise<void> =>
        productApiService.createAsync(command).then(() => getProductsAsync());

    const updateProductAsync = (command: UpdateProductCommand): Promise<void> =>
        productApiService.updateAsync(command).then(() => getProductsAsync());

    return {
        products: readonly(products),
        createProductAsync,
        getProductsAsync,
        updateProductAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useProductStore, import.meta.hot));
}
