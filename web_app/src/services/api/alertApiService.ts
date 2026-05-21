import type { AlertAction, Alerts } from 'src/models/alert';
import AxiosHttpClient from './axiosHttpClient';

export default class AlertApiService {
    private httpClient = new AxiosHttpClient();

    getAlertsAsync = async (): Promise<Alerts> =>
        await this.httpClient.get<Alerts>('/alerts');

    applyActionAsync = async (alertId: string, action: AlertAction): Promise<void> =>
        await this.httpClient.post<void, { action: AlertAction }>(
            `/alerts/${alertId}/action`,
            { action },
        );
}
