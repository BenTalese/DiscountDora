import type { DashboardSummary } from 'src/models/dashboard';
import AxiosHttpClient from './axiosHttpClient';

export default class DashboardApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getSummaryAsync = async (): Promise<DashboardSummary> =>
        await this.httpClient.get<DashboardSummary>('/dashboard/summary');
}
