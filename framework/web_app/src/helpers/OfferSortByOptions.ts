import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import { sortOffersByFullNameAsc, sortOffersByFullNameDesc, sortOffersByPriceHighToLow, sortOffersByPriceLowToHigh, sortOffersBySpecialBestToWorst } from './ScrapedProductOfferLogic';

export interface IOfferSortByOption {
    Description: string;
    Apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}

export const OfferSortByOptions: IOfferSortByOption[] = [
    {
        Description: 'Name (A - Z)',
        Apply: sortOffersByFullNameAsc
    },
    {
        Description: 'Name (Z - A)',
        Apply: sortOffersByFullNameDesc
    },
    {
        Description: 'Price (low to high)',
        Apply: sortOffersByPriceLowToHigh
    },
    {
        Description: 'Price (high to low)',
        Apply: sortOffersByPriceHighToLow
    },
    {
        Description: 'Special (best to worst)',
        Apply: sortOffersBySpecialBestToWorst
    }
];
