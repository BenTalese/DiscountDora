import type { BudgetPeriod } from 'src/models/auth';
import AxiosHttpClient from './axiosHttpClient';

/** P2-05 — cross-shopping-list grocery budget. The settings (amount,
 *  period) live on the User row; this service only reads the computed
 *  status / history. Settings changes go through AuthApiService.updateMeAsync. */
export type BudgetStatus = {
    enabled: boolean;
    amount: number | null;
    period: BudgetPeriod;
    period_start: string | null;
    period_end: string | null;
    spent: number;
    projected_active: number;
    remaining: number | null;
    over_budget: boolean;
};

export type BudgetHistoryRow = {
    period_start: string;
    period_end: string;
    spent: number;
    over_budget: boolean;
};

/** The install-wide household budget settings (amount + period). Moved off
 *  the User row — the budget tracks spend across every *shared* shopping
 *  list, so it's one value per household, not per person. Editable by any
 *  authenticated member (value-driven: amount null/0 ⇒ off). */
export type BudgetSettings = {
    amount: number | null;
    period: BudgetPeriod;
};

export default class BudgetApiService {
    private httpClient = new AxiosHttpClient();

    getStatusAsync = async (): Promise<BudgetStatus> =>
        await this.httpClient.get<BudgetStatus>('/budget/status');

    getHistoryAsync = async (periods = 6): Promise<{ rows: BudgetHistoryRow[] }> =>
        await this.httpClient.get<{ rows: BudgetHistoryRow[] }>(
            `/budget/history?periods=${periods}`,
        );

    /** Set the household budget. Omit a field to leave it unchanged; send
     *  `amount: null` or `0` to clear the budget. */
    updateSettingsAsync = async (
        body: { amount?: number | null; period?: BudgetPeriod },
    ): Promise<BudgetSettings> =>
        await this.httpClient.patch<BudgetSettings, typeof body>('/budget/settings', body);
}
