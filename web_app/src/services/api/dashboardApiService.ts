import type { DashboardSummary } from 'src/models/dashboard';
import type { DoraScore } from 'src/models/doraScore';
import AxiosHttpClient from './axiosHttpClient';

export type UseItUpItem = {
    stock_item_id: string;
    name: string;
    expiry_date: string;
    /** Negative when already past. Server-computed against the *household's*
     *  today, so "today" doesn't shift with the browser's clock (R-021). */
    days_remaining: number;
    is_expired: boolean;
};

export type UseItUpRecipe = {
    recipe_id: string;
    name: string;
    /** Names of the expiring items this recipe would use up. */
    uses: string[];
};

export type UseItUpResponse = {
    items: UseItUpItem[];
    recipes: UseItUpRecipe[];
    /** The household's own `expiring_soon_window_days`, so the card can name
     *  its window instead of hardcoding "this week" over a setting that might
     *  say 3 days or 30. */
    window_days: number;
};

export type RestockRow = {
    stock_item_id: string;
    name: string;
    /** When the item's band last changed — what "recently" is ordered on. */
    changed_at: string;
    is_essential: boolean;
    /** The recorded level, so the row renders the app's own `StockLevelDot`
     *  rather than the words "out" / "low" (owner, 2026-09-08 — *"use
     *  consistent level indicator at the start of the row instead of out/etc
     *  text"*). `band` travels alongside it because the client must not decide
     *  which sequence is the out rung. */
    level_sequence: number;
    level_name: string;
    band: 'low' | 'out';
    /** Does the coming fortnight's plan still need this? The one signal that
     *  survived the retired "Before you shop" card — same
     *  `gather_planned_demand` it read, never re-derived here (R-003). */
    is_planned: boolean;
};

/** Present-tense restock radar: what's *currently* out or low, most recently
 *  changed first. Distinct from `/reports/keeps-running-out`, which ranks on a
 *  lifetime count and still backs the reports page.
 *
 *  One list since 2026-09-08 — it was `recently_out` / `recently_low`, two
 *  columns each ordered by recency *within* the column, so the single most
 *  recent change wasn't necessarily the top row. The band is the level dot
 *  now, not which column you're reading. */
export type RestockRadarResponse = {
    rows: RestockRow[];
    /** How far back "recently" reaches, so the empty copy can name the window
     *  rather than hardcoding a number the server owns. */
    window_days: number;
};

/** Cumulative "how much have you used Dora" counts for the About page.
 *  Mirrors `UsageStatsDto` in `get_usage_stats.py`. Unlike everything else on
 *  this service these only ever go up — they are a record of use, not a
 *  snapshot of what needs doing.
 *
 *  The two money fields are `null` (never 0) when the money opt-in is off:
 *  "you've tracked no spend" and "this install doesn't do money" are different
 *  statements and the page renders them differently. */
export type UsageStats = {
    stock_items: number;
    recipes: number;
    meals_planned: number;
    meals_cooked: number;
    shopping_lists: number;
    shops_completed: number;
    total_spend: number | null;
    prices_recorded: number | null;
};

export default class DashboardApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getSummaryAsync = async (): Promise<DashboardSummary> =>
        await this.httpClient.get<DashboardSummary>('/dashboard/summary');

    /** Owner 2026-09-05 — the About page's "at a glance" block. Its own
     *  endpoint rather than more fields on `/dashboard/summary`, because it
     *  asks the opposite question: the summary is what needs doing now, this
     *  is what the household has accumulated. */
    getUsageStatsAsync = async (): Promise<UsageStats> =>
        await this.httpClient.get<UsageStats>('/dashboard/usage-stats');

    /** P8-08 — the dashboard's kitchen-health card fetches this
     *  separately from the summary so a slow score query (waste +
     *  consumption event scans) doesn't gate the rest of the page. */
    getDoraScoreAsync = async (): Promise<DoraScore> =>
        await this.httpClient.get<DoraScore>('/dashboard/dora-score');

    /** Near-expiry stock joined to the recipes that would use it up. One of
     *  the two cards that replaced "Needs your attention" + "Dora suggests";
     *  its sibling `/dashboard/before-you-shop` was deleted on 2026-09-08 when
     *  the owner folded that card into Restock radar. */
    getUseItUpAsync = async (): Promise<UseItUpResponse> =>
        await this.httpClient.get<UseItUpResponse>('/dashboard/use-it-up');

    /** What recently went low or out, most recent first. */
    getRestockRadarAsync = async (): Promise<RestockRadarResponse> =>
        await this.httpClient.get<RestockRadarResponse>('/dashboard/restock-radar');
}
