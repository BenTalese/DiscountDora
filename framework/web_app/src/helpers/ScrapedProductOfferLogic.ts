import { Product } from 'src/models/Product';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';

/**
 * Determines whether a scraped product offer exists as a product, infering that it is saved.
 * @param offer the scraped product offer that requires determination
 * @param products the saved products
 * @returns boolean, always false if products are undefined
 */
export function isOfferFavourited(offer: ScrapedProductOffer, products: Product[] | undefined): boolean {
    if(products === undefined){
        return false;
    }

    const savedProduct = products?.find((product: Product) =>
        product.merchant_stockcode == offer.merchant_stockcode &&
        product.merchant_name === offer.merchant_name)

    return savedProduct != undefined;
};

export const isOfferOnSpecial = (offer: ScrapedProductOffer): boolean =>
    offer.price_now > 0 && offer.price_now < offer.price_was;

export const sortOffersBySpecialBestToWorst = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = (offerA.price_was ?? 0) - (offerA.price_now ?? 0);
        const _OfferB = (offerB.price_was ?? 0) - (offerB.price_now ?? 0);

        if(_OfferA < _OfferB) return 1;
        else if(_OfferA > _OfferB) return -1;
        else return 0;
    });

export const sortOffersByFullNameAsc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = getOfferFullName(offerA.brand?.toLowerCase() ?? null, offerA.name.toLowerCase());
        const _OfferB = getOfferFullName(offerB.brand?.toLowerCase() ?? null, offerB.name.toLowerCase());

        if(_OfferA < _OfferB) return -1;
        else if(_OfferA > _OfferB) return 1;
        else return 0;
    });

export const sortOffersByFullNameDesc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = getOfferFullName(offerA.brand?.toLowerCase() ?? null, offerA.name.toLowerCase());
        const _OfferB = getOfferFullName(offerB.brand?.toLowerCase() ?? null, offerB.name.toLowerCase());

        if(_OfferA < _OfferB) return 1;
        else if(_OfferA > _OfferB) return -1;
        else return 0;
    });

export const sortOffersByPriceHighToLow = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        if(offerA.price_now < offerB.price_now) return 1;
        else if(offerA.price_now > offerB.price_now) return -1;
        else return 0;
    });

export const sortOffersByPriceLowToHigh = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        if(offerA.price_now < offerB.price_now) return -1;
        else if(offerA.price_now > offerB.price_now) return 1;
        else return 0;
    });
