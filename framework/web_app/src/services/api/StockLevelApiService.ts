import type { StockLevel } from "src/models/StockLevel";
import AxiosHttpClient from "./AxiosHttpClient";

export default class StockLevelApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    getAll = async (): Promise<StockLevel[]> =>
        await this.httpClient.get<StockLevel[]>('/stock-levels');
}
