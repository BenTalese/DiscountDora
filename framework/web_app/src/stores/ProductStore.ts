import { defineStore } from 'pinia';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';

const productApiService = new ProductApiService();

// TODO: store IDs must be unique, can we foresee any clashes?
// Should we make more specific/unique IDs?
export const useProductStore = defineStore('product', {
    state: () => ({
        //TODO: Can i strongly type this?
        scrapedProductOffers: new Array<ScrapedProductOffer>,
    }),
    getters: {

    },
    actions: {
        // TODO: Do i need to await?
        // TODO: should searchByTerm be named searchByTermAsync?
        searchByTerm(searchByTermQuery: SearchByTermQuery) {
            productApiService.searchByTerm(searchByTermQuery)
                // TODO: this is overwriting, we may want to only add new & keep previous search data
                // Can't see how this would be helpful though, maintaining stale data...
                .then((scrapedProductOffers) => this.scrapedProductOffers = scrapedProductOffers)
                .catch(() => {})
                .finally(() => {});

            // TODO: check this does not violate flux pattern, may not be useful anyways
            return this.scrapedProductOffers;
        },
    }
})
