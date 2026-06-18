import AxiosHttpClient from './axiosHttpClient';

export type PriceRange = '30d' | '90d' | '1y' | 'all';

export interface PriceHistoryPoint {
    date: string | null;
    unit_price: number | null;
    list_price: number | null;
    on_deal: boolean;
}

export interface PriceHistorySeries {
    product_id: string;
    name: string;
    store: string;
    points: PriceHistoryPoint[];
    current: {
        unit_price: number | null;
        list_price: number | null;
        deal_pct: number | null;
    } | null;
    all_time_low: { unit_price: number; date: string | null } | null;
}

export interface PriceAlert {
    price_alert_id: string;
    product_id: string;
    product_name: string;
    store_name: string;
    threshold_unit_price: number;
    created_at: string | null;
    last_fired_at: string | null;
}

export default class PriceHistoryApiService {
    private http = new AxiosHttpClient();

    seriesAsync = async (
        productIds: string[], range: PriceRange = '90d',
    ): Promise<{ series: PriceHistorySeries[] }> => {
        const ids = productIds.map(encodeURIComponent).join(',');
        return await this.http.get<{ series: PriceHistorySeries[] }>(
            `/price-history?product_ids=${ids}&range=${range}`,
        );
    };

    createAlertAsync = async (
        productId: string, thresholdUnitPrice: number,
    ): Promise<{ price_alert_id: string }> =>
        await this.http.post<
            { price_alert_id: string },
            { product_id: string; threshold_unit_price: number }
        >('/price-history/alerts', {
            product_id: productId,
            threshold_unit_price: thresholdUnitPrice,
        });

    listAlertsAsync = async (): Promise<{ items: PriceAlert[] }> =>
        await this.http.get<{ items: PriceAlert[] }>('/price-history/alerts');

    deleteAlertAsync = async (alertId: string): Promise<void> =>
        await this.http.delete<void>(
            `/price-history/alerts/${encodeURIComponent(alertId)}`,
        );
}
