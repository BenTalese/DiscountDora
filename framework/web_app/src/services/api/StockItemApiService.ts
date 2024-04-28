import type { StockItem } from "src/models/StockItem";
import AxiosHttpClient from "./AxiosHttpClient";
import type { CreatedResponse } from "./AxiosHttpClient"

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    createAsync = async (stockItem: CreateStockItemCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>("/stock-items", stockItem);

    deleteAsync = async (stockItemID: string): Promise<void> =>
        await this.httpClient.delete(`/stock-items/${stockItemID}`);

    getAsync = async (stockItemID: string): Promise<StockItem[]> =>
        await this.httpClient.get<StockItem[]>(`/stock-items/filter=stock_item_id:eq:${stockItemID}`); // TODO: Construct string using methods

    getAllAsync = async (): Promise<StockItem[]> =>
        await this.httpClient.get<StockItem[]>('/stock-items');

    // paginateAsync = async (page: number, pageSize: number): Promise<{ page: number; count: number; stockItems: StockItem[] }> =>
    //     await this.httpClient.get<{ page: number; count: number; stockItems: StockItem[] }>(
    //         `/stock-items?page=${page}&page-size=${pageSize}`
    //     );

    updateAsync = async (stockItemID: string, stockItem: Partial<UpdateStockItemCommand>): Promise<void> =>
        await this.httpClient.patch<void>(`/stock-items/${stockItemID}`, stockItem);
}

export type CreateStockItemCommand = {
    name: string;
    stock_level_id: string;
    stock_location_id: string | null;
}

export type UpdateStockItemCommand = {
    name: string | null;
    stock_level_id: string | null;
    stock_location_id: string | null;
}
