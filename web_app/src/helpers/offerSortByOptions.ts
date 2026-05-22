import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
import {
    sortOffersByFullNameAsc,
    sortOffersByFullNameDesc,
    sortOffersByPriceHighToLow,
    sortOffersByPriceLowToHigh,
    sortOffersBySpecialBestToWorst,
    sortOffersByUnitPriceHighToLow,
    sortOffersByUnitPriceLowToHigh
} from './scrapedProductOfferLogic';

export interface IOfferSortByOption {
    description: string;
    isDefault: boolean;
    sort: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}

export const OfferSortByOptions: IOfferSortByOption[] = [
    {
        // Relevancy = the order the merchant scrapers returned results in.
        description: 'Relevancy',
        isDefault: true,
        sort: (offers) => offers
    },
    {
        description: 'Name (A → Z)',
        isDefault: false,
        sort: sortOffersByFullNameAsc
    },
    {
        description: 'Name (Z → A)',
        isDefault: false,
        sort: sortOffersByFullNameDesc
    },
    {
        description: 'Price (low → high)',
        isDefault: false,
        sort: sortOffersByPriceLowToHigh
    },
    {
        description: 'Price (high → low)',
        isDefault: false,
        sort: sortOffersByPriceHighToLow
    },
    {
        description: 'Unit price (low → high)',
        isDefault: false,
        sort: sortOffersByUnitPriceLowToHigh
    },
    {
        description: 'Unit price (high → low)',
        isDefault: false,
        sort: sortOffersByUnitPriceHighToLow
    },
    {
        description: 'Best specials first',
        isDefault: false,
        sort: sortOffersBySpecialBestToWorst
    }
];
