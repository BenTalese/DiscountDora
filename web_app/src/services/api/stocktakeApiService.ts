import AxiosHttpClient from './axiosHttpClient';

export interface StocktakeQueueItem {
    stock_item_id: string;
    name: string;
    stock_level_name: string | null;
    stock_location_name: string | null;
    days_until_stocktake_alert: number;
    last_checked_at: string | null;
    /** -1 sentinel for "never checked" so the UI can render that
     *  specially instead of showing a confusing day count. */
    overdue_days: number;
}

export interface StocktakeQueueResponse {
    items: StocktakeQueueItem[];
    total: number;
}

export default class StocktakeApiService {
    private http = new AxiosHttpClient();

    queueAsync = async (limit = 50): Promise<StocktakeQueueResponse> =>
        await this.http.get<StocktakeQueueResponse>(`/stocktake/queue?limit=${limit}`);

    checkOneAsync = async (stockItemId: string): Promise<{ last_checked_at: string }> =>
        await this.http.post<{ last_checked_at: string }, Record<string, never>>(
            `/stock-items/${encodeURIComponent(stockItemId)}/check`, {},
        );

    bulkCheckAsync = async (ids: string[]): Promise<{ checked: number }> =>
        await this.http.post<{ checked: number }, { ids: string[] }>(
            '/stocktake/bulk-check', { ids },
        );

    reviewCompleteAsync = async (
        shoppingListId: string, setWellStocked = true,
    ): Promise<{ set_well_stocked: number; checked: number }> =>
        await this.http.post<
            { set_well_stocked: number; checked: number },
            { set_well_stocked: boolean }
        >(
            `/shopping-lists/${encodeURIComponent(shoppingListId)}/review/complete`,
            { set_well_stocked: setWellStocked },
        );
}
