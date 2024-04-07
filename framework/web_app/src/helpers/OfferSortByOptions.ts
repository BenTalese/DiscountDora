import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import { sortOffersByFullNameAsc, sortOffersByFullNameDesc, sortOffersByPriceHighToLow, sortOffersByPriceLowToHigh, sortOffersBySpecialBestToWorst } from './ScrapedProductOfferLogic';

export interface IOfferSortByOption {
    Description: string;
    IsDefault: boolean;
    Apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}

export const OfferSortByOptions: IOfferSortByOption[] = [
    {
        Description: 'Name (A - Z)',
        IsDefault: true,
        Apply: sortOffersByFullNameAsc
    },
    {
        Description: 'Name (Z - A)',
        IsDefault: false,
        Apply: sortOffersByFullNameDesc
    },
    {
        Description: 'Price (low to high)',
        IsDefault: false,
        Apply: sortOffersByPriceLowToHigh
    },
    {
        Description: 'Price (high to low)',
        IsDefault: false,
        Apply: sortOffersByPriceHighToLow
    },
    {
        Description: 'Special (best to worst)',
        IsDefault: false,
        Apply: sortOffersBySpecialBestToWorst
    }
];
