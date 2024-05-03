import type { ScrapedProductOffer } from "src/models/ScrapedProductOffer";
import type { CreatedResponse } from "./AxiosHttpClient";
import AxiosHttpClient from "./AxiosHttpClient";
import { Product } from "src/models/Product";
import { PartialWithRequired } from "src/helpers/UtilityTypes";

export default class ProductApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient(5170);
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    createAsync = async (product: Partial<Product>): Promise<CreatedResponse> =>
        await this.dapiHttpClient.post<CreatedResponse>('/products', product);

    getAllAsync = async (): Promise<Product[]> =>
        await this.dapiHttpClient.get<Product[]>('/products');

    searchByTermAsync = async (query: SearchByTermQuery): Promise<ScrapedProductOffer[]> =>
        await this.mapiHttpClient.get<ScrapedProductOffer[]>(`/products/search/${query.search_term}`);

    updateAsync = async (product: PartialWithRequired<Product, 'product_id'>): Promise<Product> =>
        await this.dapiHttpClient.patch<Product>(`/products/${product.product_id}`, product);
}

export type SearchByTermQuery = {
    search_term: string
    start_page: number
}
