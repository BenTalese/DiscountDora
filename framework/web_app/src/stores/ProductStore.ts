import { defineStore } from 'pinia';
import { Loading } from 'quasar';
import NotSupportedError from 'src/exceptions/NotSupportedError';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { isOfferFavourited, isOfferOnSpecial } from 'src/helpers/ScrapedProductOfferLogic';
import { Merchant } from 'src/models/Merchant';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';
import { computed, reactive, readonly, ref } from 'vue';

const productApiService = new ProductApiService();

// TODO:
// New Features:
// - Create a relevance algorithm & set as default sortBy
// - Add ability to un-favourite a product
// - Add query functionality on get products.
    //In the .Then for addOfferToFavouritesAsync(),
    //add the new product to state using a query specifically for that product rather than getting all products.
// - Add quasar notify/toast OR other feedback for when a product is favourited

// TODO:
// Issues:
// - Scraped offers return merchant stock code as a number BUT get products returns it as a string

export interface IProductSearchFilters {
    showOnlyAvailable: boolean,
    showOnlyFavourites: boolean,
    showOnlySpecials: boolean,
    sortBy: IOfferSortByOption,
    stores: Merchant[]
}

export const useProductStore = defineStore('product', () => {

    //#region Filters

    const productSearchOfferFilters = reactive<IProductSearchFilters>({
        showOnlyAvailable: false,
        showOnlyFavourites: false,
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
    const setProductSearchStoresFilter = (merchantsData: Merchant[]): void => { productSearchOfferFilters.stores = merchantsData; };

    /**
     * Sets the sorting criteria for product search results.
     * @param sortBy An object representing the sorting options for product search results.
     */
    const setProductSearchSortByFilter = (sortBy: IOfferSortByOption): void => { productSearchOfferFilters.sortBy = sortBy };

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

    const ProductSearchFilterStoreNames = computed(() => productSearchOfferFilters.stores?.map(sto => sto.name))

    //#endregion Filters

    //#region Products

    const products = ref<Product[]>()

    const getProductsAsync = async () =>
        productApiService
            .getAllAsync()
            .then((productsData) => products.value = productsData);

    const addOfferToFavouritesAsync = async (offer: ScrapedProductOffer) =>
        productApiService
            .createAsync(offer)
            .then(() => getProductsAsync());

    //#endregion Products

    //#region Product Offers

    const productOffers = ref<ScrapedProductOffer[] | undefined>();

    const filteredProductOffers = computed(() => {
        if(productOffers.value === undefined)
            return undefined;

        let shallowOffersCopy = productOffers.value.slice();

        shallowOffersCopy = shallowOffersCopy.filter(off =>
            (productSearchOfferFilters.showOnlyAvailable ? off.is_available : true) &&
            (productSearchOfferFilters.showOnlyFavourites ? isOfferFavourited(off, products.value) : true) &&
            (productSearchOfferFilters.showOnlySpecials ? isOfferOnSpecial(off) : true) &&
            ProductSearchFilterStoreNames.value?.includes(off.merchant_name));

        productSearchOfferFilters.sortBy.sort(shallowOffersCopy);

        return shallowOffersCopy;
    });

    async function searchByTermAsync(query: SearchByTermQuery){
        if(!query.search_term?.trim())
            return;

        Loading.show();

        productApiService
            .searchByTermAsync(query)
            .then((offers) => productOffers.value = offers)
            .finally(() => Loading.hide());
    }

    //#endregion Product Offers

    return {
        productSearchOfferFilters,
        ProductSearchFilterStoreNames,
        addStoresToProductSearchFilter,
        setProductSearchStoresFilter,
        setProductSearchSortByFilter,
        toggleProductSearchFilter,

        products: readonly(products),
        addOfferToFavouritesAsync,
        getProductsAsync,

        productOffers: readonly(productOffers),
        filteredProductOffers,
        searchByTermAsync
    };

});
