import type { StockLevel } from "@/models/StockLevel";
import AxiosHttpClient from "./AxiosHttpClient";

export default class StockLevelApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getAll = async (): Promise<StockLevel[]> =>
        await this.httpClient.get<StockLevel[]>('/stock-levels');
}
