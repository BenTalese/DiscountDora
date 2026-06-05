import type { Product } from 'src/models/product';
import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
import type { PriceHistory } from 'src/models/stockItemDetail';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export default class ProductApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient('dora');
        this.mapiHttpClient = new AxiosHttpClient('merchant');
    }

    createAsync = async (productToCreate: CreateProductCommand): Promise<CreatedResponse> =>
        await this.dapiHttpClient.post<CreatedResponse>('/products', productToCreate);

    getAllAsync = async (): Promise<Page<Product>> =>
        await this.dapiHttpClient.get<Page<Product>>('/products');

    getPriceHistoryAsync = async (productId: string): Promise<PriceHistory> =>
        await this.dapiHttpClient.get<PriceHistory>(`/products/${productId}/price-history`);

    searchByTermAsync = async (searchQuery: SearchByTermQuery): Promise<ScrapedProductOffer[]> =>
        await this.mapiHttpClient.post<ScrapedProductOffer[]>('/products/search', searchQuery);

    updateAsync = async (productToUpdate: UpdateProductCommand): Promise<Product> => {
        const { product_id, ...payload } = productToUpdate;
        return await this.dapiHttpClient.patch<Product>(`/products/${product_id}`, payload);
    };
}

export type SearchByTermQuery = {
    merchants_to_search: Array<string>;
    result_limit: number;
    search_term: string;
};

export type CreateProductCommand = {
    brand: string | null;
    image: string; //TODO: Check if img is good before saving it, prob in use case
    is_active: boolean;
    is_available: boolean;
    merchant_name: string;
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
