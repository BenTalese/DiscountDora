import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';


export interface ProductSearchSortByOption {
    Description: string;
    Apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}
