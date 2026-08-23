import AxiosHttpClient from './axiosHttpClient';

/**
 * C-waste — slim waste log + expiry rescue.
 *
 * Capture is reason-only (no quantity/value/note). The expiry-rescue
 * feed is unchanged — the dashboard's "Needs your attention" card and
 * Dora's `expiry_rescue` tool both still read it.
 */

export type WasteReason =
    | 'expired'
    | 'spoiled'
    | 'did_not_like'
    | 'overbought'
    | 'other';

export type ExpiringItem = {
    stock_item_id: string;
    name: string;
    expiry_date: string;
    days_until_expiry: number;
    is_expired: boolean;
    stock_level_name: string | null;
    estimated_value: number | null;
};

export type RescueRecipe = {
    recipe_id: string;
    name: string;
    cook_time_minutes: number | null;
    difficulty: string | null;
    matching_expiring_items: string[];
    matching_count: number;
    missing_ingredients: string[];
    is_favourite: boolean;
};

export type WasteRescue = {
    horizon_days: number;
    items: ExpiringItem[];
    recipes: RescueRecipe[];
};

export type LogWasteEventCommand = {
    stock_item_id: string;
    reason: WasteReason;
};

export type BulkLogWasteCommand = {
    stock_item_ids: string[];
    reason: WasteReason;
    /** Defaults to true server-side, matching the single-item row flow. */
    clear_expiry?: boolean;
};

export type BulkLoggedWasteEvent = {
    event_id: string;
    stock_item_id: string;
    /** The expiry this call cleared, echoed back so Undo can restore it. */
    previous_expiry_date: string | null;
};

export type BulkLogWasteResult = {
    events: BulkLoggedWasteEvent[];
    /** Ids that no longer exist — reported, not fatal. */
    missing_ids: string[];
};

export type BulkDeleteWasteCommand = {
    events: Array<{ event_id: string; restore_expiry_date: string | null }>;
};

export type WasteEvent = {
    event_id: string;
    stock_item_id: string | null;
    stock_item_name: string;
    reason: WasteReason;
    occurred_at: string | null;
};

export type MostWastedRow = {
    stock_item_id: string | null;
    stock_item_name: string;
    event_count: number;
    last_occurred_at: string | null;
};

export type MostRecentRow = {
    event_id: string;
    stock_item_id: string | null;
    stock_item_name: string;
    reason: WasteReason;
    occurred_at: string | null;
};

export type WasteInsights = {
    window_days: number;
    total_events: number;
    by_reason: Record<WasteReason, number>;
    most_wasted: MostWastedRow[];
    most_recent: MostRecentRow[];
};

export default class WasteApiService {
    private httpClient = new AxiosHttpClient();

    getRescueAsync = async (horizonDays = 7): Promise<WasteRescue> =>
        await this.httpClient.get<WasteRescue>(
            `/waste/rescue?horizon_days=${horizonDays}`,
        );

    logEventAsync = async (
        command: LogWasteEventCommand,
    ): Promise<{ event_id: string }> =>
        await this.httpClient.post<{ event_id: string }, LogWasteEventCommand>(
            '/waste/events',
            command,
        );

    /** One round-trip for a whole bulk-bar selection. The server also clears
     *  each item's expiry (unless told not to) and echoes the old date back,
     *  which is what the single-item flow spent a second and third request
     *  per item doing. */
    logEventsBulkAsync = async (
        command: BulkLogWasteCommand,
    ): Promise<BulkLogWasteResult> =>
        await this.httpClient.post<BulkLogWasteResult, BulkLogWasteCommand>(
            '/waste/events/bulk',
            command,
        );

    /** Undo for the above. POST, not DELETE, because it carries a body. */
    deleteEventsBulkAsync = async (
        command: BulkDeleteWasteCommand,
    ): Promise<{ deleted_count: number; restored_count: number }> =>
        await this.httpClient.post<
            { deleted_count: number; restored_count: number },
            BulkDeleteWasteCommand
        >('/waste/events/bulk-delete', command);

    listEventsAsync = async (limit = 25): Promise<{ events: WasteEvent[] }> =>
        await this.httpClient.get<{ events: WasteEvent[] }>(
            `/waste/events?limit=${limit}`,
        );

    deleteEventAsync = async (eventId: string): Promise<void> =>
        await this.httpClient.delete<void>(`/waste/events/${eventId}`);

    getInsightsAsync = async (windowDays = 90): Promise<WasteInsights> =>
        await this.httpClient.get<WasteInsights>(
            `/waste/insights?window_days=${windowDays}`,
        );
}
