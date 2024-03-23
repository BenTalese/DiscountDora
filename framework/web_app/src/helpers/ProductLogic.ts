import { Product } from 'src/models/Product';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';

/**
 * E.g., the Coles offers don't always contain the brand in the name.
 */
export const getOfferFullName = (brand: string, name: string): string =>
    name.includes(brand) ? name : `${brand} ${name}`;

/**
 * Determines whether a scraped product offer exists as a product, infering that it is saved.
 * @param offer the scraped product offer that requires determination
 * @param products the saved products
 * @returns boolean
 */
export function isOfferSaved(offer: ScrapedProductOffer, products: Product[] | undefined){
    const savedProduct = products?.find((product: Product) =>
        product.merchant_stockcode == offer.merchant_stockcode &&
        product.merchant_name === offer.merchant)

    return savedProduct != undefined;
};
