import { acceptHMRUpdate, defineStore } from 'pinia';
import { Loading } from 'quasar';
import NotSupportedError from 'src/exceptions/notSupportedError';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/offerSortByOptions';
import { findSavedProduct, isOfferOnSpecial } from 'src/helpers/scrapedProductOfferLogic';
import { Merchant } from 'src/models/merchant';
import type { Product } from 'src/models/product';
import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
import ProductApiService, {
    CreateProductCommand,
    SearchByTermQuery,
    UpdateProductCommand
} from 'src/services/api/productApiService';
import { computed, reactive, readonly, ref } from 'vue';

const productApiService = new ProductApiService();

export interface IProductSearchFilters {
    showOnlyAvailable: boolean;
    showOnlySpecials: boolean;
    sortBy: IOfferSortByOption;
    stores: Merchant[];
}

export type UpdateScrapedProductOfferCommand = {
    is_saved?: boolean;
    is_saved_product_active?: boolean;
    merchant_name: string;
    merchant_stockcode: string;
};

export const useProductStore = defineStore('product', () => {
    //#region Filters

    const productSearchOfferFilters = reactive<IProductSearchFilters>({
        showOnlyAvailable: false,
        showOnlySpecials: false,
        sortBy: OfferSortByOptions.find((opts) => opts.isDefault === true) as IOfferSortByOption,
        stores: []
    });

    /**
     * Adds stores to the product search filter.
     * @param merchantsData An array of Merchants representing the stores to add to the filter.
     * @returns The new length of the stores array after adding the new merchants.
     */
    const addStoresToProductSearchFilter = (merchantsData: Merchant[]): number =>
        productSearchOfferFilters.stores.push(...merchantsData);

    /**
     * Replaces the product search filter for stores with the provided data.
     * @param merchantsData An array of Merchants representing the stores that are being filtered.
     */
    const setProductSearchStoresFilter = (merchantsData: Merchant[]): void => {
        productSearchOfferFilters.stores = merchantsData;
    };

    /**
     * Sets the sorting criteria for product search results.
     * @param sortBy An object representing the sorting options for product search results.
     */
    const setProductSearchSortByFilter = (sortBy: IOfferSortByOption): void => {
        productSearchOfferFilters.sortBy = sortBy;
    };

    /**
     * Toggles the specified boolean property of the product search filter.
     * @param propertyName The name of the property to toggle within the product search filters.
     * @throws {NotSupportedError} If the property type is not boolean.
     */
    function toggleProductSearchFilter(propertyName: keyof IProductSearchFilters): void {
        if (typeof productSearchOfferFilters[propertyName] === 'boolean')
            (productSearchOfferFilters[propertyName] as boolean) = !productSearchOfferFilters[propertyName];
        else throw new NotSupportedError('Filter to toggle is not of type boolean.');
    }

    const productSearchFilterStoreNames = computed(() => productSearchOfferFilters.stores.map((sto) => sto.name));

    //#endregion Filters

    //#region Products

    const products = ref<Product[]>();

    const createProductAsync = (command: CreateProductCommand): Promise<void> =>
        productApiService.createAsync(command).then(() => getProductsAsync());

    const getProductsAsync = (): Promise<void> =>
        productApiService.getAllAsync().then((productsData) => {
            products.value = productsData;
        });

    const updateProductAsync = (command: UpdateProductCommand): Promise<void> =>
        productApiService.updateAsync(command).then(() => getProductsAsync());

    //#endregion Products

    //#region Product Offers

    const productOffers = ref<ScrapedProductOffer[] | undefined>();

    const updateProductOffer = (command: UpdateScrapedProductOfferCommand) => {
        const index =
            productOffers.value?.findIndex(
                (off) =>
                    off.merchant_name === command.merchant_name && off.merchant_stockcode === command.merchant_stockcode
            ) ?? -1;

        if (index > -1 && productOffers.value)
            productOffers.value[index] = { ...productOffers.value[index], ...command };
    };

    const filteredProductOffers = computed(() => {
        if (productOffers.value === undefined) return undefined;

        let shallowOffersCopy = productOffers.value.slice();

        shallowOffersCopy = shallowOffersCopy.filter(
            (off) =>
                (productSearchOfferFilters.showOnlyAvailable ? off.is_available : true) &&
                (productSearchOfferFilters.showOnlySpecials ? isOfferOnSpecial(off) : true) &&
                productSearchFilterStoreNames.value?.includes(off.merchant_name)
        );

        productSearchOfferFilters.sortBy.sort(shallowOffersCopy);

        return shallowOffersCopy;
    });

    async function searchByTermAsync(query: SearchByTermQuery): Promise<void> {
        if (!query.search_term?.trim()) return;

        Loading.show();

        productApiService
            .searchByTermAsync(query)
            .then((offers) => {
                productOffers.value = offers.map((off) => {
                    const savedProduct = findSavedProduct(off, products.value);
                    off.is_saved = !!savedProduct;
                    off.is_saved_product_active = savedProduct?.is_active;
                    return off;
                });
            })
            .finally(() => Loading.hide());
    }

    //#endregion Product Offers

    return {
        productSearchOfferFilters,
        productSearchFilterStoreNames,
        addStoresToProductSearchFilter,
        setProductSearchStoresFilter,
        setProductSearchSortByFilter,
        toggleProductSearchFilter,

        products: readonly(products),
        createProductAsync,
        getProductsAsync,
        updateProductAsync,

        productOffers: readonly(productOffers),
        filteredProductOffers,
        updateProductOffer,
        searchByTermAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useProductStore, import.meta.hot));
}
