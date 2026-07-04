import type { DashboardSummary } from 'src/models/dashboard';
import type { DoraScore } from 'src/models/doraScore';
import AxiosHttpClient from './axiosHttpClient';

export default class DashboardApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getSummaryAsync = async (): Promise<DashboardSummary> =>
        await this.httpClient.get<DashboardSummary>('/dashboard/summary');

    /** P8-08 — the dashboard's kitchen-health card fetches this
     *  separately from the summary so a slow score query (waste +
     *  consumption event scans) doesn't gate the rest of the page. */
    getDoraScoreAsync = async (): Promise<DoraScore> =>
        await this.httpClient.get<DoraScore>('/dashboard/dora-score');
}
