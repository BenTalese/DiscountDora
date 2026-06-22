import type { StockItem } from 'src/models/stockItem';
import type { StockItemDetail } from 'src/models/stockItemDetail';
import type { StockItemPriceHistory } from './priceHistoryApiService';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient, { resolveBaseURL } from './axiosHttpClient';
import { createQueryString, FilterOperator, type Page } from './queryStringBuilder';

/** C-1 Chunk 6 / FU-033 — URL for a stock item's image (served as raw
 *  bytes; falls back to a linked product's image server-side). Pass a
 *  `version` (e.g. a counter bumped after upload) to bust the
 *  browser cache after a re-upload. */
export function stockItemImageUrl(stockItemId: string, version?: number | string): string {
    const base = resolveBaseURL();
    const suffix = version !== undefined ? `?v=${encodeURIComponent(String(version))}` : '';
    return `${base}/stock-items/${stockItemId}/image${suffix}`;
}

export default class StockItemApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    createAsync = async (stockItemToCreate: CreateStockItemCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/stock-items', stockItemToCreate);

    deleteAsync = async (stockItemID: string): Promise<void> =>
        await this.httpClient.delete(`/stock-items/${stockItemID}`);

    getAsync = async (stockItemID: string): Promise<StockItem> => {
        const qs = createQueryString([
            { field: 'stock_item_id', operator: FilterOperator.EQUAL, value: stockItemID }
        ]);
        const page = await this.httpClient.get<Page<StockItem>>(`/stock-items${qs}`);
        return page.items[0]!;
    };

    /** Fetch a specific page of stock items. Callers that want every item
     *  use `getAllPagesAsync` below — `getAllAsync` keeps the original
     *  single-page shape for callers that only need page 1 (e.g. quick
     *  lookups that don't paginate). */
    getAllAsync = async (
        pagination?: { page: number; limit: number },
    ): Promise<Page<StockItem>> => {
        const qs = pagination
            ? createQueryString(undefined, undefined, pagination)
            : '';
        return await this.httpClient.get<Page<StockItem>>(`/stock-items${qs}`);
    };

    /** C-1 Stock Overview Chunk 1 — load every stock item by paging until
     *  the server stops returning a full page. The backend caps `limit`
     *  at 500 (`query_options.MAX_LIMIT`); we ask for that to minimise
     *  round-trips and stop as soon as a short page arrives (or we've
     *  collected `total`). The overview store calls this so a pantry of
     *  >50 items is no longer silently truncated (FU-035). */
    getAllPagesAsync = async (limit: number = 500): Promise<StockItem[]> => {
        const collected: StockItem[] = [];
        let page = 1;
        while (true) {
            const result = await this.getAllAsync({ page, limit });
            collected.push(...result.items);
            if (
                result.items.length < limit
                || collected.length >= (result.total ?? collected.length)
            ) {
                break;
            }
            page += 1;
        }
        return collected;
    };

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

    // FU-211 — preferred buys (free-text reminders on a stock item).
    addPreferredBuyAsync = async (stockItemID: string, label: string): Promise<void> =>
        await this.httpClient.post<void>(`/stock-items/${stockItemID}/preferred-buys`, { label });

    updatePreferredBuyAsync = async (
        stockItemID: string, preferredBuyID: string, label: string,
    ): Promise<void> =>
        await this.httpClient.patch<void>(
            `/stock-items/${stockItemID}/preferred-buys/${preferredBuyID}`, { label },
        );

    deletePreferredBuyAsync = async (stockItemID: string, preferredBuyID: string): Promise<void> =>
        await this.httpClient.delete<void>(
            `/stock-items/${stockItemID}/preferred-buys/${preferredBuyID}`,
        );

    // FU-225 (2026-06-18): `reorderPreferredBuysAsync` removed — the SPA now
    // sorts alphabetically client-side and the backend dropped `position` +
    // the `/preferred-buys/reorder` endpoint.

    // FU-227 chunk 2 — folded shape ({total_price, total_measure, unit}).
    // Optional store_id (A2). Provenance FK is only set by /finish harvest
    // server-side (chunk 5), not by this manual endpoint. Money-gated at UI.
    addPriceObservationAsync = async (
        stockItemID: string,
        observation: {
            total_price: number;
            total_measure: number;
            unit: string;
            observed_at?: string;
            store_id?: string | null;
        },
    ): Promise<void> =>
        await this.httpClient.post<void>(
            `/stock-items/${stockItemID}/price-observations`, observation,
        );

    deletePriceObservationAsync = async (stockItemID: string, observationID: string): Promise<void> =>
        await this.httpClient.delete<void>(
            `/stock-items/${stockItemID}/price-observations/${observationID}`,
        );

    // FU-227 chunk 6 — unioned price-history series (observations ∪ linked
    // offers, normalised per-unit server-side) for the "Full history"
    // bottom-sheet. Money-gated at the UI surface that opens the sheet.
    getPriceHistoryAsync = async (stockItemID: string): Promise<StockItemPriceHistory> =>
        await this.httpClient.get<StockItemPriceHistory>(
            `/stock-items/${stockItemID}/price-history`,
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
    /** C-1 Chunk 6 / FU-033 — image as a data-URL string, or
     *  null/omitted for none. */
    image?: string | null;
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
    /** C-1 Chunk 6 / FU-033 — data-URL string to set the image, null to
     *  clear, omit to leave untouched. */
    image?: string | null;
    /** FU-189 — usual store hint. UUID to bind; use `clear_usual_store` to clear. */
    usual_store_id?: string | null;
    clear_usual_store?: boolean;
    /** Explicit clear flags for nullable lazy-noload FKs — see
     *  `update_stock_item.py` for why the relationship-only null assignment
     *  doesn't actually persist. The SPA sends these from the picker's X. */
    clear_stock_location?: boolean;
    clear_stock_group?: boolean;
};
