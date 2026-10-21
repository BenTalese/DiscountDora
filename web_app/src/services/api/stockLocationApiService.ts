import AxiosHttpClient, { type CreatedResponse } from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type StockLocation = {
    name: string;
    stock_location_id: string;
};

export type CreateStockLocationCommand = { name: string };
export type UpdateStockLocationCommand = { stock_location_id: string; name: string };

export default class StockLocationApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getAllAsync = async (): Promise<Page<StockLocation>> =>
        await this.httpClient.get<Page<StockLocation>>('/stock-locations');

    createAsync = async (command: CreateStockLocationCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/stock-locations', command);

    updateAsync = async (command: UpdateStockLocationCommand): Promise<void> => {
        const { stock_location_id, ...payload } = command;
        await this.httpClient.patch<void>(`/stock-locations/${stock_location_id}`, payload);
    };

    deleteAsync = async (stockLocationId: string): Promise<void> =>
        await this.httpClient.delete<void>(`/stock-locations/${stockLocationId}`);
}
