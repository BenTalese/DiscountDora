import AxiosHttpClient from './axiosHttpClient';

export type AppSettings = {
    llm_enabled: boolean;
    llm_base_url: string;
    llm_model: string;
    scanning_enabled: boolean;
    // C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
    meal_planning_enabled: boolean;
    money_enabled: boolean;
    nutrition_enabled: boolean;
    companion_ingestion_enabled: boolean;
    deals_email_enabled: boolean;
    // C-cross Chunk 3 — reserved seam. Empty string ⇒ users can't pick
    // `complex` nutrition mode. Free-form for now; later complex-mode
    // work parses it.
    nutrition_db_source: string;
    // Meal Plans C-2.K — household IANA timezone for the "today" boundary.
    timezone: string;
    // Alerts C-9.2 — household-wide alert thresholds (PROPOSAL_ALERTS §3.3).
    expiring_soon_window_days: number;
    default_days_until_stocktake_alert: number;
};

export type UpdateAppSettingsCommand = Partial<AppSettings>;

export type ProbeResult = {
    reachable: boolean;
    models: string[];
    error: string | null;
};

export default class AppSettingsApiService {
    private httpClient = new AxiosHttpClient();

    getAsync = async (): Promise<AppSettings> =>
        await this.httpClient.get<AppSettings>('/app-settings');

    updateAsync = async (command: UpdateAppSettingsCommand): Promise<AppSettings> =>
        await this.httpClient.patch<AppSettings, UpdateAppSettingsCommand>('/app-settings', command);

    probeAsync = async (baseUrl: string): Promise<ProbeResult> =>
        await this.httpClient.post<ProbeResult, { base_url: string }>('/app-settings/probe', {
            base_url: baseUrl,
        });
}
