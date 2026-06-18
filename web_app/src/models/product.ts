export type Product = {
    brand: string;
    // FU-014 — bytes never travel in list/detail JSON. Fetch via
    // `/api/products/${product_id}/image` when `has_image` is true.
    has_image: boolean;
    is_active: boolean;
    is_available: boolean;
    store_id?: string;
    store_name: string;
    // FU-189 carve-out: producer's SKU code, retained verbatim.
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
