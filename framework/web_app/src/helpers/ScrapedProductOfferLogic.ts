import { Product } from 'src/models/Product';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';

/**
 * Determines whether the product matching the offer is active.
 * If no match, returns false.
 * @param offer the product offer
 * @param products the saved products
 * @returns boolean
 */
export function isOfferActive(offer: ScrapedProductOffer, products: Product[] | undefined): boolean {
    if(products === undefined)
        return false;

    const savedProduct = products?.find((product: Product) =>
        product.merchant_stockcode === offer.merchant_stockcode &&
        product.merchant_name === offer.merchant_name);

    return savedProduct?.is_active ?? false;
};

export const isOfferOnSpecial = (offer: ScrapedProductOffer): boolean =>
    offer.price_now > 0 && offer.price_now < offer.price_was;

export const sortOffersBySpecialBestToWorst = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.price_was - offerA.price_now;
        const _OfferB = offerB.price_was - offerB.price_now;

        if(_OfferA < _OfferB) return 1;
        else if(_OfferA > _OfferB) return -1;
        else return 0;
    });

export const sortOffersByFullNameAsc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.name.toLowerCase();
        const _OfferB = offerB.name.toLowerCase();

        if(_OfferA < _OfferB) return -1;
        else if(_OfferA > _OfferB) return 1;
        else return 0;
    });

export const sortOffersByFullNameDesc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.name.toLowerCase();
        const _OfferB = offerB.name.toLowerCase();

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
