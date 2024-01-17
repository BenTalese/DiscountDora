import type { CreateStockItemCommand, StockItem } from "@/models/StockItem";
import AxiosHttpClient, { CreatedResponse } from "./AxiosHttpClient";

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    create = async (stockItem: CreateStockItemCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>("/stockItems", stockItem);

    delete = async (stockItemID: string): Promise<void> =>
        await this.httpClient.delete(`/stockItems/${stockItemID}`);

    get = async (stockItemID: string): Promise<StockItem> =>
        await this.httpClient.get<StockItem>(`/stockItems/${stockItemID}`);

    getAll = async (): Promise<StockItem[]> =>
        await this.httpClient.get<StockItem[]>('/stockItems');

    paginate = async (page: number, pageSize: number): Promise<{ page: number; count: number; stockItems: StockItem[] }> =>
        await this.httpClient.get<{ page: number; count: number; stockItems: StockItem[] }>(
            `/stockItems?page=${page}&pageSize=${pageSize}`
        );

    update = async (stockItemId: string, stockItem: Partial<StockItem>): Promise<StockItem> =>
        await this.httpClient.patch<StockItem>(`/stockItems/${stockItemId}`, stockItem);
}
