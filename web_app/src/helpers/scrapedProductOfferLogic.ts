import type { Product } from 'src/models/product';
import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';

/**
 * Finds the saved product matching the merchant name & merchant stockcode of the product offer.
 * If no match, returns undefined.
 * @param offer the product offer
 * @param products all saved products
 * @returns the saved product or undefined
 */
export const findSavedProduct = (offer: ScrapedProductOffer, products: Product[] | undefined): Product | undefined =>
    products?.find(
        (product: Product) =>
            product.merchant_stockcode === offer.merchant_stockcode && product.merchant_name === offer.merchant_name
    );

export const isOfferOnSpecial = (offer: ScrapedProductOffer): boolean =>
    offer.price_now > 0 && offer.price_now < offer.price_was;

export const sortOffersBySpecialBestToWorst = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.price_was - offerA.price_now;
        const _OfferB = offerB.price_was - offerB.price_now;

        if (_OfferA < _OfferB) return 1;
        else if (_OfferA > _OfferB) return -1;
        else return 0;
    });

export const sortOffersByFullNameAsc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.name.toLowerCase();
        const _OfferB = offerB.name.toLowerCase();

        if (_OfferA < _OfferB) return -1;
        else if (_OfferA > _OfferB) return 1;
        else return 0;
    });

export const sortOffersByFullNameDesc = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        const _OfferA = offerA.name.toLowerCase();
        const _OfferB = offerB.name.toLowerCase();

        if (_OfferA < _OfferB) return 1;
        else if (_OfferA > _OfferB) return -1;
        else return 0;
    });

export const sortOffersByPriceHighToLow = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        if (offerA.price_now < offerB.price_now) return 1;
        else if (offerA.price_now > offerB.price_now) return -1;
        else return 0;
    });

export const sortOffersByPriceLowToHigh = (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
    offers.sort((offerA, offerB) => {
        if (offerA.price_now < offerB.price_now) return -1;
        else if (offerA.price_now > offerB.price_now) return 1;
        else return 0;
    });

/**
 * Normalises a product's size to a base unit so unit-price comparisons across
 * products are vaguely apples-to-apples. Returns:
 *   - grams for mass (g, kg)
 *   - millilitres for volume (ml, l)
 *   - the raw count for unit/each products
 *
 * Returns null when the unit is unrecognised, so sorts can push those items
 * to the end of their group rather than treat them as free.
 */
function normaliseSize(offer: ScrapedProductOffer): { base: number; group: string } | null {
    const value = offer.size_value;
    const unit = (offer.size_unit ?? '').toLowerCase();
    if (!value || value <= 0) return null;

    if (unit === 'g' || unit === 'gram' || unit === 'grams') return { base: value, group: 'mass' };
    if (unit === 'kg' || unit === 'kilogram' || unit === 'kilograms') {
        return { base: value * 1000, group: 'mass' };
    }
    if (unit === 'ml' || unit === 'millilitre' || unit === 'milliliters') {
        return { base: value, group: 'volume' };
    }
    if (
        unit === 'l' ||
        unit === 'litre' ||
        unit === 'litres' ||
        unit === 'liter' ||
        unit === 'liters'
    ) {
        return { base: value * 1000, group: 'volume' };
    }
    if (unit === 'each' || unit === 'ea' || unit === 'pk' || unit === 'pack') {
        return { base: value, group: 'count' };
    }
    return null;
}

/** Per-base-unit price ($ per gram, $ per ml, $ per each). Unparseable items
 *  return Infinity so they sort to the end. */
function unitPrice(offer: ScrapedProductOffer): { price: number; group: string } {
    const normalised = normaliseSize(offer);
    if (!normalised || offer.price_now <= 0) {
        return { price: Number.POSITIVE_INFINITY, group: 'unknown' };
    }
    return { price: offer.price_now / normalised.base, group: normalised.group };
}

/** Sort by unit price ascending, keeping groups (mass / volume / count) intact
 *  so a $/gram never compares against a $/each. */
export const sortOffersByUnitPriceLowToHigh = (
    offers: ScrapedProductOffer[]
): ScrapedProductOffer[] =>
    offers.sort((a, b) => {
        const ua = unitPrice(a);
        const ub = unitPrice(b);
        if (ua.group !== ub.group) return ua.group.localeCompare(ub.group);
        if (ua.price < ub.price) return -1;
        if (ua.price > ub.price) return 1;
        return 0;
    });

export const sortOffersByUnitPriceHighToLow = (
    offers: ScrapedProductOffer[]
): ScrapedProductOffer[] =>
    offers.sort((a, b) => {
        const ua = unitPrice(a);
        const ub = unitPrice(b);
        if (ua.group !== ub.group) return ua.group.localeCompare(ub.group);
        // Within a group, descending — but Infinity-priced items stay at the end.
        if (ua.price === Number.POSITIVE_INFINITY && ub.price !== Number.POSITIVE_INFINITY) return 1;
        if (ub.price === Number.POSITIVE_INFINITY && ua.price !== Number.POSITIVE_INFINITY) return -1;
        if (ua.price < ub.price) return 1;
        if (ua.price > ub.price) return -1;
        return 0;
    });
