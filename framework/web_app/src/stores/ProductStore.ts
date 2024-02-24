import { defineStore } from 'pinia';
import type { Product } from 'src/models/Product';
import type { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ProductApiService, { SearchByTermQuery } from 'src/services/api/ProductApiService';

const productApiService = new ProductApiService();

// TODO: store IDs must be unique, can we foresee any clashes?
// Should we make more specific/unique IDs?
export const useProductStore = defineStore('product', {
    state: () => ({
        //TODO: Can i strongly type this?
        savedProducts: new Array<Product>,
        scrapedProductOffers: new Array<ScrapedProductOffer>
    }),
    getters: {
    },
    actions: {
        saveProduct(productOffer: ScrapedProductOffer){
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

            .then((createdResponse) => {
                console.log(createdResponse)
                // TODO: Utilise the ID on the createdResponse to query only the single product.
                // Then push to the savedProducts array rather than replacing it.
                // productApiService.getAll()
                    // .then((products) => this.savedProducts = products)
            })
            // TODO: How do i know the a scraped product offer & a product is the same?
            // Do we want scraped products to appear favorited on the search if i have it saved?
        },
        // TODO: Do i need to await?
        // TODO: should searchByTerm be named searchByTermAsync?
        searchByTerm(searchByTermQuery: SearchByTermQuery){
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
