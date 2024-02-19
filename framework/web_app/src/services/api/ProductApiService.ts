import type { ScrapedProductOffer } from "src/models/ScrapedProductOffer";
import type { CreatedResponse } from "./AxiosHttpClient";
import AxiosHttpClient from "./AxiosHttpClient";

export default class ProductApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient(5170);
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    create = async (command: CreateProductCommand): Promise<CreatedResponse> =>
        await this.dapiHttpClient.post<CreatedResponse>("/products", command);

    searchByTerm = async (query: SearchByTermQuery): Promise<ScrapedProductOffer[]> =>
        await this.mapiHttpClient.get<ScrapedProductOffer[]>(`/products/search/${query.search_term}`);
}

export type SearchByTermQuery = {
    search_term: string
    start_page: number
}

export type CreateProductCommand = {
    brand: string
    image: string
    is_available: boolean
    merchant_name: string
    merchant_stockcode: string
    name: string
    price_now: number
    price_was: number
    size_unit: string
    size_value: number
    web_url: string
}
