import type { CreateStockItemCommand, StockItem } from "@/models/StockItem";
import AxiosHttpClient from "./AxiosHttpClient";

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    create = async (stockItem: CreateStockItemCommand): Promise<number> =>
        await this.httpClient.post<number>("/stockItems", stockItem);

    delete = async (stockItemID: number): Promise<void> =>
        await this.httpClient.delete(`/stockItems/${stockItemID}`);

    get = async (stockItemID: number): Promise<StockItem> =>
        await this.httpClient.get<StockItem>(`/stockItems/${stockItemID}`);

    getAll = async (): Promise<StockItem[]> =>
        await this.httpClient.get<StockItem[]>('/stockItems');

    paginate = async (page: number, pageSize: number): Promise<{ page: number; count: number; stockItems: StockItem[] }> =>
        await this.httpClient.get<{ page: number; count: number; stockItems: StockItem[] }>(
            `/stockItems?page=${page}&pageSize=${pageSize}`
        );

    update = async (stockItemId: number, stockItem: Partial<StockItem>): Promise<StockItem> =>
        await this.httpClient.patch<StockItem>(`/stockItems/${stockItemId}`, stockItem);
}
