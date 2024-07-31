import { defineStore } from 'pinia';
import type { StockItem } from 'src/models/stockItem';
import StockItemApiService, { CreateStockItemCommand, UpdateStockItemCommand } from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import { computed, readonly, Ref, ref } from 'vue';
import { Product } from 'src/models/product';
import { useProductStore } from './productStore';

export type ProductStockItem = {
    Product: Product
    StockItem?: StockItem
};

const stockItemApiService = new StockItemApiService();

export const useStockItemStore = defineStore('stockItem', () => {

    //#region Composing Stores

    const productStore = useProductStore();

    //#endregion Composing Stores

    //#region Product Stock Items

    const productStockItems: Ref<ProductStockItem[]> = ref([])

    const createProductStockItem = (stockItem: StockItem): void => {
        const products = productStore.products?.filter(p =>
            stockItem.product_ids.some(pid => pid == p.product_id));

        // Possible UI binding downside. Products without stock items are not in the collection.
        products?.forEach(p => productStockItems.value.push({
            Product: p,
            StockItem: stockItem
        }))
    };

    //TODO: Compare with async performance
    const getProductStockItems = computed((): ProductStockItem[] => {
        stockItems.value.forEach(si => createProductStockItem(si));
        return productStockItems.value;
    });

    //#endregion Product Stock Items

    //#region Stock Items

    const stockItems: Ref<StockItem[]> = ref([])

    const createStockItemAsync = (stockItemToCreate: CreateStockItemCommand) => stockItemApiService
        .createAsync(stockItemToCreate)
        .then(async (resource) => stockItems.value.push((await stockItemApiService.getAsync(resource.id))[0]))

    const getStockItemsAsync = () => stockItemApiService
        .getAllAsync()
        .then((stockItemData) => {
            const collator = new Intl.Collator('en', { 'sensitivity': 'base' });

            stockItems.value = stockItemData.sort((si1, si2) =>
                collator.compare(si1.name, si2.name));
        })

    const getStockItemAsync = (stockItemID: string) => stockItemApiService
        .getAsync(stockItemID)

    async function updateStockLevelAsync(stockItemToUpdate: UpdateStockItemCommand) {
        const stockItemIndex = stockItems.value.findIndex(si => si.stock_item_id == stockItemToUpdate.stock_item_id);
        const originalStockLevel = stockItems.value[stockItemIndex].stock_level_id
        stockItems.value[stockItemIndex].stock_level_id = stockItemToUpdate.stock_level_id!

        registerRollback(() => {
            stockItems.value[stockItemIndex].stock_level_id = originalStockLevel;
        });

        stockItemApiService
            .updateAsync(stockItemToUpdate)
            .then(async () => stockItems.value[stockItemIndex] = (await getStockItemAsync(stockItemToUpdate.stock_item_id))[0])
            .then(clearRollbacks)
    }

    //#endregion Stock Items

    return {
        productStockItems: readonly(productStockItems),
        getProductStockItems,

        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync
    }
});
