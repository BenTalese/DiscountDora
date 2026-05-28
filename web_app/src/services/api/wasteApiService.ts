import AxiosHttpClient from './axiosHttpClient';

/** P2-06 — expiry rescue + waste log. */

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
    quantity?: number | null;
    estimated_value?: number | null;
    note?: string | null;
    mark_out_of_stock?: boolean;
};

export type WasteEvent = {
    event_id: string;
    stock_item_id: string | null;
    stock_item_name: string;
    reason: WasteReason;
    quantity: number | null;
    estimated_value: number | null;
    note: string | null;
    occurred_at: string | null;
};

export type WasteInsightItem = {
    stock_item_id: string | null;
    stock_item_name: string;
    event_count: number;
    total_quantity: number;
    estimated_value: number;
    reasons: Record<string, number>;
    last_occurred_at: string | null;
};

export type WasteInsights = {
    window_days: number;
    total_events: number;
    total_estimated_value: number;
    by_item: WasteInsightItem[];
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
