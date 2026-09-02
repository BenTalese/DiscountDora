import AxiosHttpClient from './axiosHttpClient';

export type ReportRange = '30d' | '90d' | '1y' | '2y' | '5y' | 'all';

// YoY only accepts bounded windows. Enforce at the type level
// so callers can't hand the endpoint a range=all it will reject.
export type YoYReportRange = Exclude<ReportRange, 'all'>;

export interface StockValuePoint {
    date: string;
    value: number;
}

export interface StockValueResponse {
    range: ReportRange;
    estimate_note: string;
    points: StockValuePoint[];
}

export interface StoreSpendRow {
    store_id: string | null;
    store: string;
    spend: number;
    list_count: number;
}

export interface StoreSpendResponse {
    range: ReportRange;
    rows: StoreSpendRow[];
    /** Total across **every** row, server-computed (R-041). The dashboard shows
     *  only the top few stores, so it must not sum `rows` itself — that both
     *  moves a cross-collection aggregate into the browser and produces a total
     *  whose coverage the reader can't see. */
    total_spend: number;
    /** How many stores the total was built from, so a truncated list can say
     *  "top 3 of 5" rather than presenting a partial view as the whole. */
    store_count: number;
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
    store: string;
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

export interface PriceDropRow {
    product_id: string;
    name: string;
    store_id: string | null;
    store_name: string;
    has_image: boolean;
    price_now: number;
    previous_low: number;
    drop_amount: number;
    drop_percent: number;
    linked_stock_item_id: string | null;
    linked_stock_item_name: string | null;
}

export interface PriceDropsResponse {
    rows: PriceDropRow[];
}

export interface SavingsCapturedResponse {
    range: ReportRange;
    total_savings: number;
    total_spent: number;
    lists: SavingsListBreakdown[];
}

// culinary memory. Three new report shapes that back the new
// "Memory" section on /reports.
export interface MealsCookedTopRow {
    recipe_id: string | null;
    recipe_name: string;
    cook_count: number;
    meals_total: number;
}
export interface MealsCookedBucketPoint {
    date: string;   // ISO date at the start of the bucket
    cook_count: number;
    meals_total: number;
}
export interface MealsCookedResponse {
    range: ReportRange;
    cook_count: number;
    meals_total: number;
    top_recipes: MealsCookedTopRow[];
    timeline: MealsCookedBucketPoint[];
}

export interface SpendByCategoryRow {
    category: string;
    spent: number;
    item_count: number;
    share_pct: number;
}
export interface SpendByCategoryResponse {
    range: ReportRange;
    total_spent: number;
    rows: SpendByCategoryRow[];
}

export interface SpendYoYCategoryRow {
    category: string;
    current: number;
    previous: number;
    delta: number;
    /** null when previous == 0 — a new-category is undefined YoY, not
     *  +∞% or +100%. UI renders "new" in that case. */
    delta_pct: number | null;
}
export interface SpendYoYResponse {
    range: YoYReportRange;
    window_days: number;
    current_total: number;
    previous_total: number;
    delta: number;
    delta_pct: number | null;
    rows: SpendYoYCategoryRow[];
}

export default class ReportsApiService {
    private httpClient = new AxiosHttpClient();

    getStockValueAsync = (range: ReportRange) =>
        this.httpClient.get<StockValueResponse>(`/reports/stock-value-over-time?range=${range}`);

    getSpendByStoreAsync = (range: ReportRange) =>
        this.httpClient.get<StoreSpendResponse>(`/reports/spend-by-store?range=${range}`);

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

    getPriceDropsAsync = (limit = 5) =>
        this.httpClient.get<PriceDropsResponse>(`/reports/price-drops?limit=${limit}`);

    // ── P8-09 memory ────────────────────────────────────────────────
    getMealsCookedAsync = (range: ReportRange, limit = 10) =>
        this.httpClient.get<MealsCookedResponse>(
            `/reports/meals-cooked?range=${range}&limit=${limit}`,
        );

    getSpendByCategoryAsync = (range: ReportRange) =>
        this.httpClient.get<SpendByCategoryResponse>(
            `/reports/spend-by-category?range=${range}`,
        );

    getSpendYearOverYearAsync = (range: YoYReportRange) =>
        this.httpClient.get<SpendYoYResponse>(
            `/reports/spend-year-over-year?range=${range}`,
        );
}
