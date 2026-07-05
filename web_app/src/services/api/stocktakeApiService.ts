import AxiosHttpClient from './axiosHttpClient';

/**
 * PROPOSAL_STOCKTAKE_MODE §7 — server-owned cadence bands (R-003 SoT).
 * The SPA renders these, never re-derives them. `cadence_band` is the
 * resolved band after global default + Auto + Low/Out + Essential; the
 * matching `cadence_days` (7/14/30) travels alongside for convenience.
 */
export type CadenceBand = 'weekly' | 'fortnightly' | 'monthly';

export interface StocktakeQueueItem {
    stock_item_id: string;
    name: string;
    stock_level_name: string | null;
    stock_location_name: string | null;
    cadence_band: CadenceBand;
    cadence_days: number;
    last_checked_at: string | null;
    /** Whole days past the resolved band's window. Under Chunk 1's
     *  grace-period rule this is always ≥ 1 for anything in the
     *  queue (0-or-negative rows are filtered server-side). */
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

    /** PROPOSAL_STOCKTAKE_MODE §5 — Push (3-day snooze). Server sets a
     *  fixed 3-day `snoozed_until`; makes no truth claim about the
     *  stock, so `last_checked_at` is deliberately NOT bumped. */
    snoozeAsync = async (stockItemId: string): Promise<{ snoozed_until: string }> =>
        await this.http.post<{ snoozed_until: string }, Record<string, never>>(
            `/stock-items/${encodeURIComponent(stockItemId)}/snooze`, {},
        );

    bulkCheckAsync = async (ids: string[]): Promise<{ checked: number }> =>
        await this.http.post<{ checked: number }, { ids: string[] }>(
            '/stocktake/bulk-check', { ids },
        );

    reviewCompleteAsync = async (
        shoppingListId: string, setStocked = true,
    ): Promise<{ set_stocked: number; checked: number }> =>
        await this.http.post<
            { set_stocked: number; checked: number },
            { set_stocked: boolean }
        >(
            `/shopping-lists/${encodeURIComponent(shoppingListId)}/review/complete`,
            { set_stocked: setStocked },
        );
}
