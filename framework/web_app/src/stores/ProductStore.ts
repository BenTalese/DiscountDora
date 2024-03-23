import { defineStore } from 'pinia';
import { Loading } from 'quasar';
import { OfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { isOfferSaved } from 'src/helpers/ProductLogic';
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
// - Add ability to unsave a product
// - Query functionality on get products. After the saveProduct(), add the new product to state using query.

// TODO:
// Issues:
// - Scraped offers return merchant stock code as a number BUT get products returns it as a string
// Consider:
// - PRICE NOW is null sometimes (encountered in Woolies response). What should we display instead?
// Future:
// - Ability to unsave product
// Do:
// - Have a display for when 0 search results are found.
// - Add specials filter (show price was). Could also sort by specials biggest/smallest
// - Transition on filter section toggle


export const useProductStore = defineStore('product', () => {

    //#region Filters

    interface IOfferFilters {
        showOnlyAvailable: boolean,
        showOnlySaved: boolean,
        sortBy: OfferSortByOption,
        stores: Merchant[]
    }

    const offerFilters = reactive<IOfferFilters>({
        showOnlyAvailable: false,
        showOnlySaved: false,
        sortBy: OfferSortByOptions.find(opts => opts.Description === 'A - Z') as OfferSortByOption,
        stores: []
    })

    const pushToStoresFilter = (merchantsData: Merchant[]): void => { offerFilters.stores.push(...merchantsData); };

    const setStoresFilter = (merchantsData: Merchant[]): void => { offerFilters.stores = merchantsData; };

    const setSortByFilter = (sortBy: OfferSortByOption) => { offerFilters.sortBy = sortBy };

    const toggleIsAvailableFilter = (): void => { offerFilters.showOnlyAvailable = !offerFilters.showOnlyAvailable; };

    const toggleIsSavedFilter = (): void => { offerFilters.showOnlySaved = !offerFilters.showOnlySaved; };

    //#endregion Filters

    //#region Merchants

    const merchants = ref<Merchant[]>();

    const merchantNames = computed(() => offerFilters.stores?.map(sto => sto.name))

    function getMerchants(){
        merchantApiService.getAll()
            .then((merchantsData) => {
                const collator = new Intl.Collator('en', {'sensitivity': 'base'});

                merchants.value = merchantsData.sort((merchant1, merchant2) =>
                    collator.compare(merchant1.name, merchant2.name))

                pushToStoresFilter(merchants.value);
            });
    };

    //#endregion Merchants

    //#region Products

    const products = ref<Product[]>()

    //TODO: Async
    function getProducts(){
        productApiService.getAll()
            .then((productsData) => products.value = productsData);
    };

    function saveProduct(productOffer: ScrapedProductOffer){
        productApiService.create({
            brand: productOffer.brand,
            image: productOffer.image,
            is_available: productOffer.is_available,
            merchant_name: productOffer.merchant,
            merchant_stockcode: productOffer.merchant_stockcode,
            name: productOffer.name,
            price_now: productOffer.price_now,
            price_was: productOffer.price_was,
            size_unit: productOffer.size_unit,
            size_value: productOffer.size_value,
            web_url: productOffer.web_url
        })
        .then(() => getProducts());
    };

    //#endregion

    //#region Product Offers

    const productOffers = ref<ScrapedProductOffer[]>();

    // TODO: Investigate whether filteredProductOffers executed twice
    //  on sort update is due to binding state direct to component.
    const filteredProductOffers = computed(() => {
        if(productOffers.value === undefined)
            return undefined;

        let shallowOffersCopy = productOffers.value.slice();

        shallowOffersCopy = shallowOffersCopy.filter(off => {
            //TODO: review naming conventions
            //TODO: Should logic be modified to only apply the saved filter if products is not undefined
            return (off.is_available === offerFilters.showOnlyAvailable || off.is_available === true)
                && (offerFilters.showOnlySaved ? isOfferSaved(off, products.value) : true)
                && merchantNames.value?.includes(off.merchant)
        });

        offerFilters.sortBy.Apply(shallowOffersCopy);

        return shallowOffersCopy;
    });

    function searchByTerm(query: SearchByTermQuery){

        if(!query.search_term?.trim()){
            return;
        }

        Loading.show();

        productApiService.searchByTerm(query)
            .then((offers) => productOffers.value = offers)
            .catch(() => {})
            .finally(() => Loading.hide());
    }

    //#endregion

    return {
        filterOptions: offerFilters,
        pushFilterStores: pushToStoresFilter,
        setStoresFilter,
        setSortByFilter,
        toggleIsAvailableFilter,
        toggleIsSavedFilter,

        merchants,
        merchantNames,
        getMerchants,

        products,
        getProducts,
        saveProduct,

        productOffers,
        filteredProductOffers,
        searchByTerm,
    };

});
