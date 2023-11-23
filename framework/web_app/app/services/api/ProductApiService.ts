import type { ScrapedProductOffer } from "@/models/ScrapedProductOffer";
import AxiosHttpClient from "./AxiosHttpClient";

export default class ProductApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    create = async (command: CreateProductCommand): Promise<void> =>
        await this.httpClient.post<void>("/products", command);

    searchByTerm = async (searchByTermQuery: SearchByTermQuery): Promise<ScrapedProductOffer[]> =>
        await this.httpClient.post<ScrapedProductOffer[]>("/webScraper/search", searchByTermQuery);
}

export type SearchByTermQuery = {
    search_term: string
    start_page: number
}

export type CreateProductCommand = {
    brand: string
    image: string
    is_available: boolean
    merchant_id: string
    merchant_stockcode: string
    name: string
    price_now: number
    price_was: number
    size_unit: string
    size_value: number
    web_url: string
}
