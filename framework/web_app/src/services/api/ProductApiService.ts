import type { ScrapedProductOffer } from "src/models/ScrapedProductOffer";
import type { CreatedResponse } from "./AxiosHttpClient";
import AxiosHttpClient from "./AxiosHttpClient";
import { Product } from "src/models/Product";

export default class ProductApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient(5170);
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    createAsync = async (command: CreateProductCommand): Promise<CreatedResponse> =>
        await this.dapiHttpClient.post<CreatedResponse>('/products', command);

    getAllAsync = async (): Promise<Product[]> =>
        await this.dapiHttpClient.get<Product[]>('/products');

    searchByTermAsync = async (query: SearchByTermQuery): Promise<ScrapedProductOffer[]> =>
        await this.mapiHttpClient.get<ScrapedProductOffer[]>(`/products/search/${query.search_term}`);

    updateAsync = async (command: UpdateProductCommand): Promise<Product> =>
        await this.dapiHttpClient.patch<Product>(`/products/${command.product_id}`, command);
}

export type SearchByTermQuery = {
    search_term: string
    start_page: number
}

export type CreateProductCommand = {
    brand: string | null
    image: string //TODO: Check if img is good before saving it, prob in use case
    is_active: boolean
    is_available: boolean
    merchant_name: string
    merchant_stockcode: string
    name: string
    price_now: number
    price_was: number
    size: string
    size_unit: string
    size_value: number
    web_url: string
}

export type UpdateProductCommand = {
    is_active?: boolean
    is_available?: boolean
    price_now?: number
    price_was?: number
    product_id: string
}
