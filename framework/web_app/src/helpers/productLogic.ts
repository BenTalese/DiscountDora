import { Product } from 'src/models/product';

export const isCurrentOfferOnSpecial = (product: Product): boolean =>
    product.price_now > 0 && product.price_now < product.price_was;
