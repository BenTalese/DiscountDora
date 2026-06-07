import AxiosHttpClient from './axiosHttpClient';

export type BarcodeLookupResult =
    | { kind: 'stock_item'; id: string }
    | { kind: 'product'; id: string; stock_item_id: string | null }
    | { kind: 'unknown'; value: string };

export default class BarcodeApiService {
    private httpClient = new AxiosHttpClient();

    /** Disambiguate a scanned value — matches the server-side lookup
     *  table: dora:// link → stock_item, product_barcode hit → product
     *  (with linked stock item if any), otherwise unknown. A real-world
     *  barcode identifies a product, never a stock item directly. */
    lookupAsync = async (value: string): Promise<BarcodeLookupResult> =>
        await this.httpClient.get<BarcodeLookupResult>(
            `/data/barcodes/lookup?value=${encodeURIComponent(value)}`,
        );

    registerAgainstProductAsync = async (
        productId: string,
        barcode: string,
    ): Promise<{ product_barcode_id: string; product_id: string; barcode: string }> =>
        await this.httpClient.post<
            { product_barcode_id: string; product_id: string; barcode: string },
            { product_id: string; barcode: string }
        >('/data/barcodes/register-against-product', {
            product_id: productId,
            barcode,
        });
}
