import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';


export interface ProductSearchSortOption {
    Description: string;
    Apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
}
