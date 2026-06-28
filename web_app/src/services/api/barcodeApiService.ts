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
}
