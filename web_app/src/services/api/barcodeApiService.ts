import AxiosHttpClient from './axiosHttpClient';

/** FU-056 — four lookup result kinds. The schema guarantees
 *  `UNIQUE(StockItemProduct.product_id)` so a barcode resolves to at most
 *  one stock item; no caller disambiguation. */
export type BarcodeLookupResult =
    | {
        kind: 'stock_item';
        id: string;
        barcode_id?: string;
        product_id?: string | null;
    }
    | {
        kind: 'stock_item_via_product';
        id: string;
        product_id: string;
        barcode_id: string;
    }
    | {
        kind: 'product_no_link';
        product_id: string;
        barcode_id: string;
    }
    | { kind: 'unknown'; value: string };

export interface RegisterBarcodeBody {
    barcode: string;
    /** At least one of `product_id` / `stock_item_id` must be provided. */
    product_id?: string | null;
    stock_item_id?: string | null;
}

export interface BarcodeRegistration {
    barcode_id: string;
    barcode: string;
    product_id: string | null;
    stock_item_id: string | null;
}

/** P8-02 — Open Food Facts suggestion. Every field is optional so the
 *  caller can render whatever OFF provided without treating gaps as an
 *  error. `found: false` covers both "OFF has no entry" and "OFF was
 *  unreachable"; the SPA falls through to the manual-entry path in
 *  either case. */
export type OpenFoodFactsSuggestion =
    | {
        found: true;
        name?: string | null;
        brand?: string | null;
        image_url?: string | null;
        categories?: string | null;
        quantity?: string | null;
    }
    | { found: false };

export default class BarcodeApiService {
    private httpClient = new AxiosHttpClient();

    /** Resolve a scanned value to one of five kinds.
     *  - `stock_item`              — dora:// QR, or a real EAN registered
     *                                 directly against a stock item.
     *  - `stock_item_via_product`  — EAN matches a Product linked to one
     *                                 stock item.
     *  - `product_multi_linked`    — EAN matches a Product linked to many
     *                                 stock items; caller picks.
     *  - `product_no_link`         — EAN matches a Product the user has but
     *                                 no stock item is linked yet.
     *  - `unknown`                 — nothing matched. */
    lookupAsync = async (value: string): Promise<BarcodeLookupResult> =>
        await this.httpClient.get<BarcodeLookupResult>(
            `/data/barcodes/lookup?value=${encodeURIComponent(value)}`,
        );

    /** Register a real-world EAN. At least one target required. Direction
     *  is the caller's perspective; the server applies the all-or-none CHECK
     *  and the per-product UNIQUE rule (one Product = one EAN). */
    registerAsync = async (body: RegisterBarcodeBody): Promise<BarcodeRegistration> =>
        await this.httpClient.post<BarcodeRegistration, RegisterBarcodeBody>(
            '/data/barcodes',
            body,
        );

    /** Remove a registration. The barcode value is freed for re-registration. */
    deleteAsync = async (barcodeId: string): Promise<void> =>
        await this.httpClient.delete<void>(`/data/barcodes/${barcodeId}`);

    /** P8-02 — Open Food Facts lookup for a genuinely-unknown EAN. Only
     *  callable after `lookupAsync` returned `kind: 'unknown'`; already-
     *  mapped EANs must never round-trip through OFF (invariant defended
     *  in the caller, not enforced by the server — the SPA is the one
     *  place that knows what "unknown" means for the scan flow). */
    offLookupAsync = async (value: string): Promise<OpenFoodFactsSuggestion> =>
        await this.httpClient.get<OpenFoodFactsSuggestion>(
            `/data/products/off-lookup?value=${encodeURIComponent(value)}`,
        );
}
