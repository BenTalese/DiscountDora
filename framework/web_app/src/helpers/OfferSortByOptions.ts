import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import { getOfferFullName } from './ProductLogic';

export interface OfferSortByOption {
    Description: string;
    Apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}

export const OfferSortByOptions: OfferSortByOption[] = [
    {
        Description: 'A - Z',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                const _OfferA = getOfferFullName(offerA.brand.toLowerCase(), offerA.name.toLowerCase());
                const _OfferB = getOfferFullName(offerB.brand.toLowerCase(), offerB.name.toLowerCase());

                if(_OfferA < _OfferB) return -1;
                else if(_OfferA > _OfferB) return 1;
                else return 0;
            })
    },
    {
        Description: 'Z - A',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                const _OfferA = getOfferFullName(offerA.brand.toLowerCase(), offerA.name.toLowerCase());
                const _OfferB = getOfferFullName(offerB.brand.toLowerCase(), offerB.name.toLowerCase());

                if(_OfferA < _OfferB) return 1;
                else if(_OfferA > _OfferB) return -1;
                else return 0;
            })
    },
    {
        Description: 'Price low to high',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                if(offerA.price_now < offerB.price_now) return -1;
                else if(offerA.price_now > offerB.price_now) return 1;
                else return 0;
            })
    },
    {
        Description: 'Price high to low',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                if(offerA.price_now < offerB.price_now) return 1;
                else if(offerA.price_now > offerB.price_now) return -1;
                else return 0;
            })
    }
]
