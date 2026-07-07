import AxiosHttpClient from './axiosHttpClient';

/** P8-05 — one axis-worth of reasoning behind a buy verdict. See
 *  `PROPOSAL_BUY_VERDICT_ORACLE.md` §2.1 for the full signal table. */
export interface BuyVerdictReason {
    axis: 'price' | 'need' | 'waste';
    signal: string;
    label: string;
    detail?: string | null;
}

/** The verdict's suggested next tap. The mutation itself uses existing
 *  endpoints (cart button flow, stock-level PATCH); the server just
 *  emits the intent + label so the UI stays honest about the reasoning
 *  and the action side-by-side. */
export interface BuyVerdictAction {
    kind:
        | 'add_to_list'
        | 'skip'
        | 'mark_stocked'
        | 'remove_from_list'
        | 'none';
    label: string;
}

/** The transparency payload — what data the composer reasoned from.
 *  Powers the "why?" tooltip (Charter P7 preview/explain). */
export interface BuyVerdictDataUsed {
    price_samples: number;
    price_average: number | null;
    price_last: number | null;
    price_last_at: string | null;               // ISO date
    days_since_last_purchase: number | null;
    average_days_between_purchase: number | null;
    waste_events_last_12mo: number;
    purchases_last_12mo: number;
    stock_level_band: 'out' | 'low' | 'stocked' | 'unknown';
}

/** P8-06 — the time-boxed "when" attached to a `wait` verdict. Populated
 *  server-side only when the composer landed on `wait` and `_wait_hint`
 *  found a confident cycle (thin/erratic/overdue history → `null`). The
 *  reason string is the human explanation; `until` is the machine date. */
export interface BuyVerdictWaitHint {
    until: string;      // ISO date (yyyy-mm-dd)
    reason: string;
}

export interface BuyVerdict {
    verdict: 'buy' | 'wait' | 'skip' | 'unsure';
    confidence: 'high' | 'medium' | 'low';
    reasons: BuyVerdictReason[];
    one_tap_action: BuyVerdictAction;
    data_used: BuyVerdictDataUsed;
    // populated only on `wait` verdicts when a confident cycle
    // is detected; `null` otherwise.
    wait_hint: BuyVerdictWaitHint | null;
}

export default class BuyVerdictApiService {
    private httpClient = new AxiosHttpClient();

    /** Ask the oracle. Server composes over the user's own data only —
     *  no external calls, no crowd baselines. Returns quickly (~1 KB
     *  payload); the SPA still caches per-item to avoid re-asking on
     *  every render pass. */
    getAsync = async (stockItemId: string): Promise<BuyVerdict> =>
        await this.httpClient.get<BuyVerdict>(
            `/stock-items/${encodeURIComponent(stockItemId)}/buy-verdict`,
        );
}
