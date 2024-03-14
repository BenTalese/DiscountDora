import { defineStore } from 'pinia';
import { ProductSearchSortByOption } from 'src/helpers/ProductSearchSortByOption';
import { ProductSearchSortByOptions } from 'src/helpers/ProductSearchSortByOptions';
import { Merchant } from 'src/models/Merchant';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import MerchantApiService from 'src/services/api/MerchantApiService';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';

const merchantApiService = new MerchantApiService();
const productApiService = new ProductApiService();

export const useProductStore = defineStore('product', {
    state: () => ({
        //TODO: We can use an interface instead of type assertions like below.
        //Architecture decision.
        merchants: undefined as Merchant[] | undefined,
        filterOptions: {
            isAvailable: false as boolean,
            isSaved: false as boolean,
            // TODO: Create relevance algorithm & set as default sortBy
            sortBy: ProductSearchSortByOptions.find(opts => opts.Description === 'A - Z') as ProductSearchSortByOption,
            stores: [] as Merchant[]
        },
        productOffers: undefined as Array<ScrapedProductOffer> | undefined,
        products: undefined as Array<Product> | undefined
    }),
    // TODO: Investigate sortedProductOffers executed twice on sort update
    getters: {
        filteredProductOffers(state): Array<ScrapedProductOffer> | undefined {
            if(state.productOffers === undefined)
                return undefined;

            let shallowOffersCopy = state.productOffers.slice();

            shallowOffersCopy = shallowOffersCopy.filter(off => {
                //TODO: my naming conventions are likely off
                //TODO: readability of this logic is bad
                return (off.is_available === state.filterOptions.isAvailable || off.is_available === true)
                && (state.filterOptions.isSaved ?
                    state.products?.find(pro => off.merchant_stockcode == pro.merchant_stockcode
                        && off.merchant === pro.merchant_name)
                        != undefined
                    : true)
                    //TODO: pinia, getter accessing getter
                && this.merchantNames?.includes(off.merchant)
            });

            state.filterOptions.sortBy.Apply(shallowOffersCopy);

            return shallowOffersCopy;
        },
        merchantNames(): string[] | undefined {
            return this.filterOptions.stores?.map(sto => sto.name);
        }
    },
    actions: {
        getMerchants(){
            merchantApiService.getAll()
                .then((merchants) => {
                    const collator = new Intl.Collator('en', {'sensitivity': 'base'});

                    this.merchants = merchants.sort((merchant1, merchant2) =>
                        collator.compare(merchant1.name, merchant2.name))

                    this.filterOptions.stores?.push(...this.merchants);
                });
        },
        getProducts(){
            productApiService.getAll()
                .then((products) => this.products = products);
        },
        saveProduct(productOffer: ScrapedProductOffer){
            // TODO: offers return merchant stock code as number BUT get products returns it as a string
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
                .then(() => {
                    // TODO: need to query by the newly created product when getting products
                    // Otherwise, manually create the new product & add it to state
                    this.getProducts()
                });
        },
        // TODO: offers return merchant stock code as number BUT get products returns it as a string
        searchByTerm(searchByTermQuery: SearchByTermQuery){
            productApiService.searchByTerm(searchByTermQuery)
                .then((offers) => this.productOffers = offers)
                .catch(() => {})
                .finally(() => {});

            return this.productOffers;
        },
        toggleIsSavedFilter(){
            this.filterOptions.isSaved = !this.filterOptions.isSaved;
        },
        toggleIsAvailableFilter(){
            this.filterOptions.isAvailable = !this.filterOptions.isAvailable;
        },
    }
})
