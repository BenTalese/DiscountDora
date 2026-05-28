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

export default class BudgetApiService {
    private httpClient = new AxiosHttpClient();

    getStatusAsync = async (): Promise<BudgetStatus> =>
        await this.httpClient.get<BudgetStatus>('/budget/status');

    getHistoryAsync = async (periods = 6): Promise<{ rows: BudgetHistoryRow[] }> =>
        await this.httpClient.get<{ rows: BudgetHistoryRow[] }>(
            `/budget/history?periods=${periods}`,
        );
}
