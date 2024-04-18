import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import { sortOffersByFullNameAsc, sortOffersByFullNameDesc, sortOffersByPriceHighToLow, sortOffersByPriceLowToHigh, sortOffersBySpecialBestToWorst } from './ScrapedProductOfferLogic';

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
        description: 'Price (low to high)',
        isDefault: false,
        sort: sortOffersByPriceLowToHigh
    },
    {
        description: 'Price (high to low)',
        isDefault: false,
        sort: sortOffersByPriceHighToLow
    },
    {
        description: 'Special (best to worst)',
        isDefault: false,
        sort: sortOffersBySpecialBestToWorst
    }
];
