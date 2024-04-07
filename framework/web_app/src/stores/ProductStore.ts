import { defineStore } from 'pinia';
import { Loading } from 'quasar';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { isOfferFavourited } from 'src/helpers/ScrapedProductOfferLogic';
import { Merchant } from 'src/models/Merchant';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import MerchantApiService from 'src/services/api/MerchantApiService';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';
import { computed, reactive, ref } from 'vue';

const merchantApiService = new MerchantApiService();
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

export const useProductStore = defineStore('product', () => {

    //#region Filters

    interface IOfferFilters {
        showOnlyAvailable: boolean,
        showOnlyFavourites: boolean,
        showOnlySpecials: boolean,
        sortBy: IOfferSortByOption,
        stores: Merchant[]
    }

    const offerFilters = reactive<IOfferFilters>({
        showOnlyAvailable: false,
        showOnlyFavourites: false,
        showOnlySpecials: false,
        sortBy: OfferSortByOptions.find(opts => opts.IsDefault === true) as IOfferSortByOption,
        stores: []
    })

    const pushToStoresFilter = (merchantsData: Merchant[]): void => { offerFilters.stores.push(...merchantsData); };

    const setStoresFilter = (merchantsData: Merchant[]): void => { offerFilters.stores = merchantsData; };

    const setSortByFilter = (sortBy: IOfferSortByOption) => { offerFilters.sortBy = sortBy };

    const toggleShowOnlyAvailable = (): void => { offerFilters.showOnlyAvailable = !offerFilters.showOnlyAvailable; };

    const toggleShowOnlyFavourites = (): void => { offerFilters.showOnlyFavourites = !offerFilters.showOnlyFavourites; };

    const toggleShowOnlySpecials = (): void => { offerFilters.showOnlySpecials = !offerFilters.showOnlySpecials; };

    //#endregion Filters

    //#region Merchants

    const merchants = ref<Merchant[]>();

    const merchantNames = computed(() => offerFilters.stores?.map(sto => sto.name))

    async function getMerchantsAsync(){
        merchantApiService
            .getAllAsync()
            .then((merchantsData) => {
                const collator = new Intl.Collator('en', {'sensitivity': 'base'});

                merchants.value = merchantsData.sort((merchant1, merchant2) =>
                    collator.compare(merchant1.name, merchant2.name))

                // TODO: test the push vs set one more time, if push add helpful comment here
                // The merchants are options but not selected if Set rather than push
                // setStoresFilter(merchants.value);
                if(!offerFilters.stores.length)
                    pushToStoresFilter(merchants.value);
            });
    };

    //#endregion Merchants

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

    const productOffers = ref<ScrapedProductOffer[]>();

    const filteredProductOffers = computed(() => {
        if(productOffers.value === undefined)
            return undefined;

        let shallowOffersCopy = productOffers.value.slice();

        shallowOffersCopy = shallowOffersCopy.filter(off =>
            (offerFilters.showOnlyAvailable ? off.is_available === true : true) &&
            (offerFilters.showOnlyFavourites ? isOfferFavourited(off, products.value) : true) &&
            (offerFilters.showOnlySpecials ?  off.price_now < off.price_was : true) &&
            merchantNames.value?.includes(off.merchant_name) &&
            // Don't display products that don't have a current price
            off.price_now != null);

        offerFilters.sortBy.Apply(shallowOffersCopy);

        return shallowOffersCopy;
    });

    async function searchByTermAsync(query: SearchByTermQuery){
        if(!query.search_term?.trim())
            return;

        Loading.show();

        productApiService
            .searchByTermAsync(query)
            .then((offers) => productOffers.value = offers)
            .catch(() => {})
            .finally(() => Loading.hide());
    }

    //#endregion Product Offers

    return {
        offerFilters,
        pushToStoresFilter,
        setStoresFilter,
        setSortByFilter,
        toggleShowOnlyAvailable,
        toggleShowOnlyFavourites,
        toggleShowOnlySpecials,

        merchants,
        merchantNames,
        getMerchantsAsync,

        products,
        addOfferToFavouritesAsync,
        getProductsAsync,

        productOffers,
        filteredProductOffers,
        searchByTermAsync
    };

});
