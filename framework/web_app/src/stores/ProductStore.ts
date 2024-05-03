import { defineStore } from 'pinia';
import { Loading } from 'quasar';
import NotSupportedError from 'src/exceptions/NotSupportedError';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { isOfferOnSpecial, isOfferActive } from 'src/helpers/ScrapedProductOfferLogic';
import { PartialWithRequired } from 'src/helpers/UtilityTypes';
import { Merchant } from 'src/models/Merchant';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';
import { computed, reactive, readonly, ref } from 'vue';

const productApiService = new ProductApiService();

export interface IProductSearchFilters {
    showOnlyAvailable: boolean,
    showOnlySpecials: boolean,
    sortBy: IOfferSortByOption,
    stores: Merchant[]
}

export const useProductStore = defineStore('product', () => {

    //#region Filters

    const productSearchOfferFilters = reactive<IProductSearchFilters>({
        showOnlyAvailable: false,
        showOnlySpecials: false,
        sortBy: OfferSortByOptions.find(opts => opts.isDefault === true) as IOfferSortByOption,
        stores: []
    })

    /**
     * Adds stores to the product search filter.
     * @param merchantsData An array of Merchants representing the stores to add to the filter.
     * @returns The new length of the stores array after adding the new merchants.
     */
    const addStoresToProductSearchFilter = (merchantsData: Merchant[]): number => productSearchOfferFilters.stores.push(...merchantsData);

    /**
     * Replaces the product search filter for stores with the provided data.
     * @param merchantsData An array of Merchants representing the stores that are being filtered.
     */
    const setProductSearchStoresFilter = (merchantsData: Merchant[]): void => {
        productSearchOfferFilters.stores = merchantsData;
    }

    /**
     * Sets the sorting criteria for product search results.
     * @param sortBy An object representing the sorting options for product search results.
     */
    const setProductSearchSortByFilter = (sortBy: IOfferSortByOption): void => {
        productSearchOfferFilters.sortBy = sortBy;
    }

    /**
     * Toggles the specified boolean property of the product search filter.
     * @param propertyName The name of the property to toggle within the product search filters.
     * @throws {NotSupportedError} If the property type is not boolean.
     */
    function toggleProductSearchFilter(propertyName: keyof IProductSearchFilters): void {
        if(typeof productSearchOfferFilters[propertyName] === 'boolean')
            (productSearchOfferFilters[propertyName] as boolean) = !productSearchOfferFilters[propertyName];
        else
            throw new NotSupportedError('Filter to toggle is not of type boolean.');
    }

    const productSearchFilterStoreNames = computed(() => productSearchOfferFilters.stores.map(sto => sto.name))

    //#endregion Filters

    //#region Products

    const products = ref<Product[]>()

    const createProductAsync = (product: Partial<Product>): Promise<void> =>
        productApiService
            .createAsync(product)
            .then(() => getProductsAsync());

    const getProductsAsync = (): Promise<void> =>
        productApiService
            .getAllAsync()
            .then((productsData) => { products.value = productsData; });

    const updateProductAsync = (product: PartialWithRequired<Product, 'product_id'>): Promise<void> =>
        productApiService
            .updateAsync(product)
            .then(() => getProductsAsync());

    //#endregion Products

    //#region Product Offers

    const productOffers = ref<ScrapedProductOffer[] | undefined>();

    const updateProductOffer = (offer: PartialWithRequired<ScrapedProductOffer, 'merchant_name' | 'merchant_stockcode'>) => {
        const index = productOffers.value?.findIndex(off =>
            off.merchant_name === offer.merchant_name
            && off.merchant_stockcode === offer.merchant_stockcode)
            ?? -1;

        if(index > -1 && productOffers.value)
            productOffers.value[index] = {...productOffers.value[index], ...offer} ;
    };

    const filteredProductOffers = computed(() => {
        if(productOffers.value === undefined)
            return undefined;

        let shallowOffersCopy = productOffers.value.slice();

        shallowOffersCopy = shallowOffersCopy.filter(off =>
            (productSearchOfferFilters.showOnlyAvailable ? off.is_available : true) &&
            (productSearchOfferFilters.showOnlySpecials ? isOfferOnSpecial(off) : true) &&
            productSearchFilterStoreNames.value?.includes(off.merchant_name));

        productSearchOfferFilters.sortBy.sort(shallowOffersCopy);

        return shallowOffersCopy;
    });

    async function searchByTermAsync(query: SearchByTermQuery): Promise<void> {
        if(!query.search_term?.trim())
            return;

        Loading.show();

        productApiService
            .searchByTermAsync(query)
            .then((offers) => {
                productOffers.value = offers.map(off => {
                    off.is_active = isOfferActive(off, products.value);
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
