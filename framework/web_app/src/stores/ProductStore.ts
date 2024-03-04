import { defineStore } from 'pinia';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';
import { ProductSearchSortOptions } from 'src/helpers/ProductSearchSortOptions';
import { ProductSearchSortOption } from 'src/helpers/ProductSearchSortOption';

const productApiService = new ProductApiService();

// TODO: store IDs must be unique, can we foresee any clashes?
// Should we make more specific/unique IDs?
export const useProductStore = defineStore('product', {
    state: () => ({
        // TODO: Switch this with sort by relevance, this is the default
        activeSortOption: ProductSearchSortOptions.find(opts => opts.Description === 'A - Z') as ProductSearchSortOption,
        savedProducts: null as Array<Product> | null,
        scrapedProductOffers: null as Array<ScrapedProductOffer> | null,
    }),
    // TODO: Investigate sortedProductOffers executed twice on sort update
    getters: {
        sortedProductOffers: (state): Array<ScrapedProductOffer> | null => {
            if(state.scrapedProductOffers === null)
                return null;

            return state.activeSortOption.Apply(state.scrapedProductOffers)
        }
    },
    actions: {
        async getProducts(){
            productApiService.getAll()
                .then((products) => this.savedProducts = products)
        },
        async saveProduct(productOffer: ScrapedProductOffer){
            await productApiService.create({
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

            // TODO: need to query by the newly created product when getting products
            // Otherwise, manually create the new product & add it to state
            await this.getProducts()
        },
        // TODO: Do i need to await?
        // TODO: should searchByTerm be named searchByTermAsync?
        searchByTerm(searchByTermQuery: SearchByTermQuery){
            productApiService.searchByTerm(searchByTermQuery)
                // TODO: this is overwriting, we may want to only add new & keep previous search data
                // Can't see how this would be helpful though, maintaining stale data...
                .then((offers) => {
                    this.scrapedProductOffers = offers
                    //TODO: These share the same reference. Need to deep clone.
                })
                .catch(() => {})
                .finally(() => {});

            // TODO: check this does not violate flux pattern, may not be useful anyways
            return this.scrapedProductOffers;
        }
    }
})
