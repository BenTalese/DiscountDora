import type { StockItem } from 'src/models/stockItem';
import type { StockItemDetail } from 'src/models/stockItemDetail';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import { createQueryString, FilterOperator, type Page } from './queryStringBuilder';

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    createAsync = async (stockItemToCreate: CreateStockItemCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/stock-items', stockItemToCreate);

    deleteAsync = async (stockItemID: string): Promise<void> =>
        await this.httpClient.delete(`/stock-items/${stockItemID}`);

    /** Restore a previously-deleted stock item from a captured snapshot.
     *  Used by F5's Undo flow — preserves the original id so any
     *  cross-references that haven't already been cascaded still resolve. */
    restoreAsync = async (
        snapshot: RestoreStockItemCommand,
    ): Promise<{ stock_item_id: string; already_exists: boolean }> =>
        await this.httpClient.post<
            { stock_item_id: string; already_exists: boolean },
            RestoreStockItemCommand
        >('/stock-items/restore', snapshot);

    getAsync = async (stockItemID: string): Promise<StockItem> => {
        const qs = createQueryString([
            { field: 'stock_item_id', operator: FilterOperator.EQUAL, value: stockItemID }
        ]);
        const page = await this.httpClient.get<Page<StockItem>>(`/stock-items${qs}`);
        return page.items[0]!;
    };

    getAllAsync = async (): Promise<Page<StockItem>> =>
        await this.httpClient.get<Page<StockItem>>('/stock-items');

    getDetailAsync = async (stockItemID: string): Promise<StockItemDetail> =>
        await this.httpClient.get<StockItemDetail>(`/stock-items/${stockItemID}/detail`);

    updateAsync = async (stockItemToUpdate: UpdateStockItemCommand): Promise<void> => {
        const { stock_item_id, ...payload } = stockItemToUpdate;
        await this.httpClient.patch<void>(`/stock-items/${stock_item_id}`, payload);
    };

    linkProductAsync = async (stockItemID: string, productID: string): Promise<void> =>
        await this.httpClient.post<void>(`/stock-items/${stockItemID}/products`, {
            product_id: productID
        });

    unlinkProductAsync = async (stockItemID: string, productID: string): Promise<void> =>
        await this.httpClient.delete<void>(`/stock-items/${stockItemID}/products/${productID}`);

    moveAsync = async (
        stockItemID: string,
        destinationLocationId: string | null
    ): Promise<void> =>
        await this.httpClient.patch<void>(`/stock-items/${stockItemID}/move`, {
            destination_location_id: destinationLocationId
        });

    addSubstituteAsync = async (stockItemID: string, substituteID: string): Promise<void> =>
        await this.httpClient.post<void>(`/stock-items/${stockItemID}/substitutes`, {
            substitute_id: substituteID
        });

    removeSubstituteAsync = async (stockItemID: string, substituteID: string): Promise<void> =>
        await this.httpClient.delete<void>(
            `/stock-items/${stockItemID}/substitutes/${substituteID}`
        );
}

export type CreateStockItemCommand = {
    name: string;
    stock_level_id: string;
    stock_location_id: string | null;
    stock_group_id?: string | null;
    expiry_date?: string | null;
    is_flagged?: boolean;
    auto_add_when_low?: boolean;
    is_open?: boolean;
};

export type RestoreStockItemCommand = {
    stock_item_id: string;
    name: string;
    stock_level_id: string;
    stock_location_id: string | null;
    stock_group_id?: string | null;
    expiry_date?: string | null;
    is_flagged?: boolean;
    auto_add_when_low?: boolean;
    is_open?: boolean;
};

export type UpdateStockItemCommand = {
    stock_item_id: string;
    name?: string;
    notes?: string | null;
    days_until_stocktake_alert?: number;
    stocktake_alerts_are_enabled?: boolean;
    stock_level_id?: string;
    stock_location_id?: string | null;
    stock_group_id?: string | null;
    expiry_date?: string | null;
    is_flagged?: boolean;
    auto_add_when_low?: boolean;
    is_open?: boolean;
    opened_on?: string | null;
    preferred_product_id?: string | null;
};
