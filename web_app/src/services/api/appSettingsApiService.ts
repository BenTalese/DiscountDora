import AxiosHttpClient from './axiosHttpClient';
import type { CadenceBand } from './stocktakeApiService';

/** FU-511 — install-wide auto-add mode. Kept as a shared enum so the
 *  Settings page and any surface that reads the setting stay in sync. */
export type AutoAddMode = 'off' | 'essential_only' | 'all';

export type AppSettings = {
    // single install-wide master kill-switch for the
    // assistant feature. Per-user LLM URL/model/provider/API key live
    // on the User row (see authStore.currentUser.llm_*).
    master_llm_enabled: boolean;
    scanning_enabled: boolean;
    // buy-verdict oracle. Default on (pure-personal feature).
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
    // install-wide currency (ISO 4217) + display locale (BCP-47).
    // Every money render in the SPA routes through the shared formatter
    // (composables/useMoney.ts), which reads these values from /api/health.
    currency: string;
    locale: string;
    // Alerts C-9.2 — household-wide alert thresholds (PROPOSAL_ALERTS §3.3).
    expiring_soon_window_days: number;
    // Phase D / FU-186 — admin-set URL the Product Search nav opens.
    // Empty string ⇒ unset; the nav entry renders disabled with a hint.
    product_search_url: string;
    // Hides the Product Search nav entry entirely, regardless of URL.
    product_search_hidden: boolean;
    // PROPOSAL_STOCKTAKE_MODE §4 + §8 — global cadence band + Auto toggle.
    // These are the single user-visible cadence dial; the old
    // `default_days_until_stocktake_alert` field was retired in the
    // 2026-07-04 cleanup.
    stocktake_default_cadence_band: CadenceBand;
    stocktake_auto_tuning_enabled: boolean;
    /** FU-511 — install-wide auto-add mode. Replaces the retired per-item
     *  `StockItem.auto_add_when_low` toggle. Auto-add fires per the mode:
     *    'off'            — never.
     *    'essential_only' — only for items with `is_flagged=true` (default).
     *    'all'            — always on a Stocked → Low/Out transition.
     *  Server owns the branching in `update_stock_item._try_auto_add`. */
    auto_add_mode: AutoAddMode;
    // FU-317 — install-wide meal-plan reconcile posture. True = today's
    // silent auto-drain (past-day entries are assumed cooked, pool drains
    // as the day rolls). False = the sweep writes `unresolved_manual`
    // receipts and leaves the pool + entries untouched, forcing every
    // past meal through the reconcile page. Owned by admin.
    auto_drain_past_meals: boolean;
    // operational config promoted from DORA_* env vars.
    // Bucket-C secrets (SMTP password, VAPID private key) live encrypted-at-
    // rest on the AppSetting row; the read DTO surfaces a `_configured` bool
    // instead of the ciphertext. Writes accept plaintext via the write DTO
    // (see below) and the handler encrypts on save.
    smtp_host: string;
    smtp_port: number;
    smtp_username: string;
    smtp_password_configured: boolean;
    smtp_from: string;
    smtp_use_tls: boolean;
    vapid_public_key: string;
    vapid_private_key_configured: boolean;
    vapid_subject: string;
    piper_bin: string;
    piper_bundled_voice_dir: string;
    piper_voice: string;
    email_enabled: boolean;
    audit_retention_days: number;
    public_url: string;
};

// the read DTO exposes `<field>_configured` bools; the
// write DTO accepts the plaintext value on `<field>` (server encrypts and
// returns only the bool). Empty string on a secret field is the explicit
// "clear the stored value" signal; omit the field to leave it unchanged.
export type UpdateAppSettingsCommand = Partial<Omit<AppSettings,
    'smtp_password_configured' | 'vapid_private_key_configured'>> & {
    smtp_password?: string;
    vapid_private_key?: string;
};

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
