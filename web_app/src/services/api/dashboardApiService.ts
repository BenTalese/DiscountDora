import type { DashboardSummary } from 'src/models/dashboard';
import type { DoraScore } from 'src/models/doraScore';
import AxiosHttpClient from './axiosHttpClient';

/** One of the three shopping lists the dashboard offers quick nav to.
 *  Mirrors `DashboardListCard` in `get_dashboard_lists.py`. */
export type DashboardListCard = {
    shopping_list_id: string;
    display_name: string;
    status: string;
    /** Server-resolved: completed date > planned shop date > created. */
    effective_date: string;
    line_count: number;
    unticked_count: number;
    /** Money always travels; the *card* gates it on the money opt-in, exactly
     *  as the shopping-list page does. */
    total_price: number;
    remaining_price: number;
    total_savings: number;
};

/** Current · next · most recently finished. Any of the three may be null —
 *  a household with one draft list has a `current` and nothing else. */
export type DashboardListsResponse = {
    current: DashboardListCard | null;
    next: DashboardListCard | null;
    finished: DashboardListCard | null;
};

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

export type RunningOutRow = {
    stock_item_id: string;
    name: string;
    /** 'low' | 'out' — the *recorded* band. Not a belief: the inference
     *  overlay is opt-in and this card isn't. */
    band: 'low' | 'out';
    is_essential: boolean;
};

export type PlanGapRow = {
    stock_item_id: string;
    name: string;
    needed_meals: number;
    earliest_needed: string | null;
    recipe_names: string[];
    urgency: 'none' | 'watch' | 'blocking';
};

export type RestockRow = {
    stock_item_id: string;
    name: string;
    /** When the item's band last changed — what "recently" is ordered on. */
    changed_at: string;
    is_essential: boolean;
};

/** Present-tense restock radar: what's *currently* out or low, most recently
 *  changed first. Distinct from `/reports/keeps-running-out`, which ranks on a
 *  lifetime count and still backs the reports page. */
export type RestockRadarResponse = {
    recently_out: RestockRow[];
    recently_low: RestockRow[];
};

export type BeforeYouShopResponse = {
    running_out: RunningOutRow[];
    plan_gaps: PlanGapRow[];
    /** Days until the nearest planned shop date on an active list; null when
     *  no active list names one. Negative means that date has passed. */
    shop_in_days: number | null;
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

    /** Owner 2026-09-04 — the three lists worth a shortcut (current · next ·
     *  last finished), picked and totalled server-side. Replaced a card that
     *  fetched a whole `ShoppingListDetail` to render three numbers. */
    getListsAsync = async (): Promise<DashboardListsResponse> =>
        await this.httpClient.get<DashboardListsResponse>('/dashboard/lists');

    /** Near-expiry stock joined to the recipes that would use it up. One of
     *  the two cards that replaced "Needs your attention" + "Dora suggests". */
    getUseItUpAsync = async (): Promise<UseItUpResponse> =>
        await this.httpClient.get<UseItUpResponse>('/dashboard/use-it-up');

    /** What won't survive until the next shop: recorded-low items that are on
     *  no active list, plus the coming plan's uncovered demand. */
    getBeforeYouShopAsync = async (): Promise<BeforeYouShopResponse> =>
        await this.httpClient.get<BeforeYouShopResponse>('/dashboard/before-you-shop');

    /** What just ran out and what just went low. */
    getRestockRadarAsync = async (): Promise<RestockRadarResponse> =>
        await this.httpClient.get<RestockRadarResponse>('/dashboard/restock-radar');
}
