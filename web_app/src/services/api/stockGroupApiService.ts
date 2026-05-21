import type { StockGroup } from 'src/models/stockGroup';
import AxiosHttpClient from './axiosHttpClient';

export type CreateStockGroupCommand = { name: string };
export type UpdateStockGroupCommand = { name: string };

export default class StockGroupApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<StockGroup[]> =>
        await this.httpClient.get<StockGroup[]>('/stock-groups');

    createAsync = async (
        command: CreateStockGroupCommand,
    ): Promise<{ stock_group_id: string }> =>
        await this.httpClient.post<{ stock_group_id: string }, CreateStockGroupCommand>(
            '/stock-groups',
            command,
        );

    updateAsync = async (
        id: string,
        command: UpdateStockGroupCommand,
    ): Promise<void> =>
        await this.httpClient.patch<void, UpdateStockGroupCommand>(
            `/stock-groups/${id}`,
            command,
        );

    deleteAsync = async (id: string): Promise<{ items_affected: number }> =>
        await this.httpClient.delete<{ items_affected: number }>(`/stock-groups/${id}`);
}
