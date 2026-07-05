import AxiosHttpClient from './axiosHttpClient';
import type { CadenceBand } from './stocktakeApiService';

export type AppSettings = {
    // FU-153 §7.1 — single install-wide master kill-switch for the
    // assistant feature. Per-user LLM URL/model/provider/API key live
    // on the User row (see authStore.currentUser.llm_*).
    master_llm_enabled: boolean;
    scanning_enabled: boolean;
    // P8-05 — buy-verdict oracle. Default on (pure-personal feature).
    buy_verdict_enabled: boolean;
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
    // Phase D / FU-186 — admin-set URL the Product Search nav opens.
    // Empty string ⇒ unset; the nav entry renders disabled with a hint.
    product_search_url: string;
    // PROPOSAL_STOCKTAKE_MODE §4 + §8 — global cadence band + Auto toggle.
    // These are the single user-visible cadence dial; the old
    // `default_days_until_stocktake_alert` field was retired in the
    // 2026-07-04 cleanup.
    stocktake_default_cadence_band: CadenceBand;
    stocktake_auto_tuning_enabled: boolean;
    // FU-333 Bucket B — operational config promoted from DORA_* env vars.
    // SMTP password + VAPID private key stay env-only until Bucket C
    // (encrypted-in-DB storage) lands; they aren't in this DTO so an
    // accidental client send can't smuggle them into the database.
    smtp_host: string;
    smtp_port: number;
    smtp_username: string;
    smtp_from: string;
    smtp_use_tls: boolean;
    vapid_public_key: string;
    vapid_subject: string;
    piper_bin: string;
    piper_bundled_voice_dir: string;
    piper_voice: string;
    email_enabled: boolean;
    audit_retention_days: number;
    public_url: string;
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
