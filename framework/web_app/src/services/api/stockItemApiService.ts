import type { StockItem } from 'src/models/stockItem';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import { createQueryString, FilterOperator } from './queryStringBuilder';

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    createAsync = async (stockItemToCreate: CreateStockItemCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/stock-items', stockItemToCreate);

    deleteAsync = async (stockItemID: string): Promise<void> =>
        await this.httpClient.delete(`/stock-items/${stockItemID}`);

    getAsync = async (stockItemID: string): Promise<StockItem[]> =>
        await this.httpClient.get<StockItem[]>(
            `/stock-items/${createQueryString([{ field: 'stock_item_id', operator: FilterOperator.EQUAL, value: stockItemID }])}`
        );

    getAllAsync = async (): Promise<StockItem[]> => await this.httpClient.get<StockItem[]>('/stock-items');

    // paginateAsync = async (page: number, pageSize: number): Promise<{ page: number; count: number; stockItems: StockItem[] }> =>
    //     await this.httpClient.get<{ page: number; count: number; stockItems: StockItem[] }>(
    //         `/stock-items?page=${page}&page-size=${pageSize}`
    //     );

    updateAsync = async (stockItemToUpdate: UpdateStockItemCommand): Promise<void> =>
        await this.httpClient.patch<void>(`/stock-items/${stockItemToUpdate.stock_item_id}`, stockItemToUpdate);
}

export type CreateStockItemCommand = {
    days_until_stocktake_alert: number;
    name: string;
    stock_group_id: string | null;
    stock_level_id: string;
    stock_location_id: string | null;
};

export type UpdateStockItemCommand = {
    name?: string;
    stock_item_id: string;
    stock_level_id?: string;
    stock_location_id?: string | null;
};
