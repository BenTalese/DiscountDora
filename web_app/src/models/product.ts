export type Product = {
    brand: string;
    image: string;
    is_active: boolean;
    is_available: boolean;
    merchant_id?: string;
    merchant_name: string;
    merchant_stockcode: string;
    name: string;
    price_now: number;
    price_was: number;
    product_id: string;
    size: string;
    size_unit: string;
    size_value: number;
    web_url: string;
    // Set when the product is linked to a stock item via the
    // StockItemProduct m2m. Null for orphaned/unlinked products.
    linked_stock_item_id: string | null;
    linked_stock_item_name: string | null;
};
