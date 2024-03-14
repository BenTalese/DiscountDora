import { Product } from "src/models/Product";
import { ScrapedProductOffer } from "src/models/ScrapedProductOffer";

export interface ProductSearchFilterOption
{
    apply: (offers: ScrapedProductOffer[]) => ScrapedProductOffer[];
    description: string;
}

export const ProductSearchFilterOptions: ProductSearchFilterOption[] = [
    {
        apply: (offers: ScrapedProductOffer[]): ScrapedProductOffer[] => {
            // TODO: Check if filter mutates & if there are better alternatives
            return offers.filter(off => off.is_available);
        },
        description: 'In Stock'
    },
    {
        apply: (offers: ScrapedProductOffer[], products: Product[]): ScrapedProductOffer[] => {
            // TODO: Check if filter mutates & if there are better alternatives
            // TODO: Check the mismatch in naming for merchant, either i butchered or somewhere needs to change
            return offers.filter(off =>
                products.find(pro => off.merchant === pro.merchant_name
                    && off.merchant_stockcode === pro.merchant_stockcode));
        },
        description: 'Saved'
    },
    {
        apply: (offers: ScrapedProductOffer[], stores: string[]): ScrapedProductOffer[] => {
            return offers.filter(off => stores.includes(off.merchant));
        },
        description: 'By Store'
    }
]
