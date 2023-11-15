import type { Product } from "@/models/Product";
import AxiosHttpClient from "./AxiosHttpClient";

export default class ProductApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    searchByTerm = async (searchTerm: string, startPage: number): Promise<Product[]> =>
        await this.httpClient.post<Product[]>("/webScraper/search", {"searchTerm": searchTerm, "startPage": startPage});
}
