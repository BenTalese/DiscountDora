import type { Product } from 'src/models/product';
import type { PriceHistory } from 'src/models/stockItemDetail';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import { FilterOperator, SortOrder, createQueryString, type Page } from './queryStringBuilder';

export default class ProductApiService {
    private httpClient = new AxiosHttpClient();

    createAsync = async (productToCreate: CreateProductCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/products', productToCreate);

    getAllAsync = async (): Promise<Page<Product>> =>
        await this.httpClient.get<Page<Product>>('/products');

    /** Name search, resolved server-side.
     *
     *  FU-668 — a picker that hydrates through `getAllAsync()` and then filters
     *  in the browser can only ever see the first page (`DEFAULT_LIMIT` is 50),
     *  so product 51 onward is unsearchable and nothing on screen says so.
     *  Third confirmed instance of that trap after stock items and the cookbook.
     */
    searchAsync = async (needle: string, limit = 20): Promise<Page<Product>> =>
        await this.httpClient.get<Page<Product>>(
            `/products${createQueryString(
                needle.trim()
                    ? [{ field: 'name', operator: FilterOperator.CONTAINS, value: needle.trim() }]
                    : [],
                { field: 'name', order: SortOrder.ASCENDING },
                { page: 1, limit },
            )}`,
        );

    /** Top-N on-special products by discount %, ranked + sliced server-side
     *  (state-ownership §8.2) so the dashboard needn't download every product. */
    getBestDealsAsync = async (limit = 3): Promise<Product[]> =>
        await this.httpClient.get<Product[]>(`/products/best-deals?limit=${limit}`);

    getPriceHistoryAsync = async (productId: string): Promise<PriceHistory> =>
        await this.httpClient.get<PriceHistory>(`/products/${productId}/price-history`);

    /** Hard delete (feedback L197). Takes the product's offers, price history,
     *  alerts, barcode and stock-item link with it; lines on *finished*
     *  shopping lists survive, naming the product from the snapshot frozen
     *  when the list was finished (FU-883). */
    deleteAsync = async (productId: string): Promise<void> =>
        await this.httpClient.delete(`/products/${productId}`);

    updateAsync = async (productToUpdate: UpdateProductCommand): Promise<Product> => {
        const { product_id, ...payload } = productToUpdate;
        return await this.httpClient.patch<Product>(`/products/${product_id}`, payload);
    };
}

export type CreateProductCommand = {
    brand: string | null;
    // `data:image/...;base64,...` string.
    image: string | null;
    is_active: boolean;
    is_available: boolean;
    store_name: string;
    merchant_stockcode: string;
    name: string;
    price_now: number;
    price_was: number;
    size: string;
    size_unit: string;
    size_value: number;
    web_url: string;
};

export type UpdateProductCommand = {
    is_active?: boolean;
    is_available?: boolean;
    price_now?: number;
    price_was?: number;
    product_id: string;
};
