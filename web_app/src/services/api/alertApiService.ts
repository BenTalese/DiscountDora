import type {
    AlertAction,
    AlertHistory,
    AlertPrefs,
    Alerts,
    Upcoming,
    UpdateAlertPrefCommand,
} from 'src/models/alert';
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

    // ── Per-user interaction state (C-9.1) ─────────────────────────────
    // alertId is the scoped key; it carries ':' but no '/', so it's a single
    // path segment server-side (matching the existing action endpoint).
    markReadAsync = async (alertId: string): Promise<void> =>
        await this.httpClient.post<void, undefined>(`/alerts/${alertId}/read`, undefined);

    markUnreadAsync = async (alertId: string): Promise<void> =>
        await this.httpClient.post<void, undefined>(`/alerts/${alertId}/unread`, undefined);

    markAllReadAsync = async (): Promise<void> =>
        await this.httpClient.post<void, undefined>('/alerts/read-all', undefined);

    snoozeAsync = async (alertId: string, days = 7): Promise<void> =>
        await this.httpClient.post<void, { days: number }>(
            `/alerts/${alertId}/snooze`,
            { days },
        );

    dismissAsync = async (alertId: string): Promise<void> =>
        await this.httpClient.post<void, undefined>(`/alerts/${alertId}/dismiss`, undefined);

    clearSuppressionAsync = async (alertId: string): Promise<void> =>
        await this.httpClient.delete<void>(`/alerts/${alertId}/suppression`);

    // ── Per-user preferences (C-9.2) ───────────────────────────────────
    // Enable/disable a kind + override its tier. The server applies these to
    // GET /alerts, so the badge/list already reflect them (R-003); the store
    // is for the (C-9.3) manage panel.
    getPrefsAsync = async (): Promise<AlertPrefs> =>
        await this.httpClient.get<AlertPrefs>('/alerts/prefs');

    updatePrefAsync = async (command: UpdateAlertPrefCommand): Promise<AlertPrefs> =>
        await this.httpClient.patch<AlertPrefs, UpdateAlertPrefCommand>('/alerts/prefs', command);

    // ── History (C-9.3) — the ledger audit trail for the hub's History section.
    getHistoryAsync = async (limit = 50): Promise<AlertHistory> =>
        await this.httpClient.get<AlertHistory>(`/alerts/history?limit=${limit}`);

    // ── Upcoming "this fortnight" timeline (C-9.6) — server-aggregated dated
    // events (expiries / planned shopping / meal-plan days) over the next N days.
    getUpcomingAsync = async (days = 14): Promise<Upcoming> =>
        await this.httpClient.get<Upcoming>(`/alerts/upcoming?days=${days}`);
}
