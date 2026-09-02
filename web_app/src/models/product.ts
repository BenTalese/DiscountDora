export type Product = {
    brand: string;
    // Image bytes never travel in list/detail JSON. Render the photo with
    // `<ProductThumb :product-id :has-image>`, which fetches through the
    // authenticated HTTP client and hands the browser an object URL. Do NOT
    // bind the API path into an `<img src>` — that is unauthenticated by
    // construction and fails silently on a split host and in the Capacitor
    // shell (R-045; three surfaces did exactly that until FU-827).
    has_image: boolean;
    is_active: boolean;
    is_available: boolean;
    store_id?: string;
    store_name: string;
    // producer's SKU code, retained verbatim.
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
