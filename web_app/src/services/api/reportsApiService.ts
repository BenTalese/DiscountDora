import AxiosHttpClient from './axiosHttpClient';

export type ReportRange = '30d' | '90d' | '1y' | 'all';

export interface StockValuePoint {
    date: string;
    value: number;
}

export interface StockValueResponse {
    range: ReportRange;
    estimate_note: string;
    points: StockValuePoint[];
}

export interface MerchantSpendRow {
    merchant_id: string | null;
    merchant: string;
    spend: number;
    list_count: number;
}

export interface MerchantSpendResponse {
    range: ReportRange;
    rows: MerchantSpendRow[];
}

export interface MostBoughtRow {
    stock_item_id: string;
    name: string;
    appearances: number;
}

export interface MostBoughtResponse {
    range: ReportRange;
    rows: MostBoughtRow[];
}

export interface KeepsRunningOutRow {
    stock_item_id: string;
    name: string;
    times_out_when_added: number;
}

export interface KeepsRunningOutResponse {
    rows: KeepsRunningOutRow[];
}

export interface PricePoint {
    date: string;
    unit_price: number;
}

export interface PriceTrendSeries {
    product_id: string;
    name: string;
    merchant: string;
    points: PricePoint[];
}

export interface PriceTrendsResponse {
    range: ReportRange;
    series: PriceTrendSeries[];
}

export interface SavingsListBreakdown {
    shopping_list_id: string;
    name: string;
    completed_at: string | null;
    picked_total: number;
    list_total: number;
    savings: number;
}

export interface SavingsCapturedResponse {
    range: ReportRange;
    total_savings: number;
    total_spent: number;
    lists: SavingsListBreakdown[];
}

export default class ReportsApiService {
    private httpClient = new AxiosHttpClient();

    getStockValueAsync = (range: ReportRange) =>
        this.httpClient.get<StockValueResponse>(`/reports/stock-value-over-time?range=${range}`);

    getSpendByMerchantAsync = (range: ReportRange) =>
        this.httpClient.get<MerchantSpendResponse>(`/reports/spend-by-merchant?range=${range}`);

    getMostBoughtAsync = (range: ReportRange, limit = 10) =>
        this.httpClient.get<MostBoughtResponse>(`/reports/most-bought-items?range=${range}&limit=${limit}`);

    getKeepsRunningOutAsync = (limit = 10) =>
        this.httpClient.get<KeepsRunningOutResponse>(`/reports/keeps-running-out?limit=${limit}`);

    getPriceTrendsAsync = (productIds: string[], range: ReportRange) => {
        const csv = productIds.join(',');
        return this.httpClient.get<PriceTrendsResponse>(
            `/reports/price-trends?product_ids=${encodeURIComponent(csv)}&range=${range}`,
        );
    };

    getSavingsCapturedAsync = (range: ReportRange) =>
        this.httpClient.get<SavingsCapturedResponse>(`/reports/savings-captured?range=${range}`);
}
