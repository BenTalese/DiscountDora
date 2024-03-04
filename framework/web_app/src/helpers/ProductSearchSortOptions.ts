import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import { ProductSearchSortOption } from './ProductSearchSortOption';

export const ProductSearchSortOptions: ProductSearchSortOption[] = [
    {
        Description: 'A - Z',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                const _OfferA = offerA.name.toLowerCase();
                const _OfferB = offerB.name.toLowerCase();

                if(_OfferA < _OfferB) return -1;
                else if(_OfferA > _OfferB) return 1;
                else return 0;
            })
    },
    {
        Description: 'Z - A',
        Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
            offers.sort((offerA, offerB) => {
                const _OfferA = offerA.name.toLowerCase();
                const _OfferB = offerB.name.toLowerCase();

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

// export class ProductSearchSortOptions {
//     SortOptions: [];

//     NameAsc: ProductSearchSortOption = {
//         Description: 'A - Z',
//         Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
//             offers.sort((a, b) => {
//                 const _A = a.name.toLowerCase();
//                 const _B = b.name.toLowerCase();

//                 if(_A < _B) return -1;
//                 else if(_A > _B) return 1;
//                 else return 0;
//             }),
//     };

//     NameDesc: ProductSearchSortOption = {
//         Description: 'Z - A',
//         Apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] =>
//             offers.sort((a, b) => {
//                 const _A = a.name.toLowerCase();
//                 const _B = b.name.toLowerCase();

//                 if(_A < _B) return 1;
//                 else if(_A > _B) return -1;
//                 else return 0;
//             }),
//     };

// }
