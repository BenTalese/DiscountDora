import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
import {
    sortOffersByFullNameAsc,
    sortOffersByFullNameDesc,
    sortOffersByPriceHighToLow,
    sortOffersByPriceLowToHigh,
    sortOffersBySpecialBestToWorst
} from './scrapedProductOfferLogic';

export interface IOfferSortByOption {
    description: string;
    isDefault: boolean;
    sort: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}

export const OfferSortByOptions: IOfferSortByOption[] = [
    {
        description: 'Name (A - Z)',
        isDefault: true,
        sort: sortOffersByFullNameAsc
    },
    {
        description: 'Name (Z - A)',
        isDefault: false,
        sort: sortOffersByFullNameDesc
    },
    {
        description: 'Price (Low to High)',
        isDefault: false,
        sort: sortOffersByPriceLowToHigh
    },
    {
        description: 'Price (High to Low)',
        isDefault: false,
        sort: sortOffersByPriceHighToLow
    },
    {
        description: 'Specials',
        isDefault: false,
        sort: sortOffersBySpecialBestToWorst
    }
];
