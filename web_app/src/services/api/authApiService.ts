import type {
    AuthenticatedUser,
    BudgetPeriod,
    FontFamilyPreference,
    FontSizePreference,
    ThemePreference,
    VoiceEngine
} from 'src/models/auth';
import AxiosHttpClient, { NormalisedApiError, resolveBaseURL } from './axiosHttpClient';

/** Settings rebuild Phase 4 — URL for a user's profile-picture bytes (served
 *  raw; 404 when unset). Pass a `version` (a counter bumped after upload /
 *  clear) to bust the browser cache. */
export function userImageUrl(userId: string, version?: number | string): string {
    const base = resolveBaseURL();
    const suffix = version !== undefined ? `?v=${encodeURIComponent(String(version))}` : '';
    return `${base}/users/${userId}/image${suffix}`;
}

export type LoginCommand = { username: string; password: string };
export type RegisterCommand = {
    username: string;
    password: string;
    email: string | null;
};
/** FU-200 — first-admin bootstrap. Email is required (not optional like
 *  /register) so password reset works on a fresh install. */
export type BootstrapAdminCommand = {
    username: string;
    password: string;
    email: string;
};
export type UpdateMeCommand = {
    send_deals_on_day?: number;
    // `email` removed from this command. Email changes flow
    // through `requestEmailChangeAsync` (password proof + confirmation
    // link); sending it via `updateMeAsync` is now a 400 from the
    // backend's `extra="forbid"` model.
    username?: string;
    deals_email_enabled?: boolean;
    deals_email_compact?: boolean;
    theme?: ThemePreference;
    font_family?: FontFamilyPreference;
    font_size?: FontSizePreference;
    /** P2-05 — grocery budget. Sending a positive number opts in;
     *  `clear_budget_amount: true` opts out. `0` is also treated as opt-out
     *  by the backend. */
    budget_amount?: number | null;
    clear_budget_amount?: boolean;
    budget_period?: BudgetPeriod;
    /** P2-13 — voice opt-in toggles. Saved per user. */
    voice_input_enabled?: boolean;
    voice_output_enabled?: boolean;
    /** Voice engine (`browser` | `piper`) + chosen Piper voice id. Server
     *  validates the voice id against its catalog (GET /api/tts/voices). */
    voice_engine?: VoiceEngine;
    voice_id?: string;
    /** C-cross Chunk 2 — per-user money-features opt-in. Layered with the
     *  install-wide `money_enabled` flag via `useMoneyEnabled()`. */
    money_features_enabled?: boolean;
    /** IMPL_PLAN_MEAL_PLANS_REBUILD §6.6 / Q3 — per-user batch-cooking
     *  posture. Default off ("fresh"); when on, the meal-planner reveals
     *  cook-pool affordances + shortfall warning. */
    batch_features_enabled?: boolean;
    /** FU-316 — when true, quick-add prompts every time (skips the
     *  session-remembered pick). Only matters when the user has >1 draft. */
    always_ask_which_shopping_list?: boolean;
    /** FU-181 loose-end 2 — target meal count for the sequential builder.
     *  Positive int 1..21 sets it; `null` clears back to the SPA fallback
     *  (BUILDER_TARGET_MEALS_FALLBACK = 7). */
    meals_per_week?: number | null;
    /** P8-07 — Zero-Input Pantry opt-out. `false` hides the inferred-level
     *  belief overlay; default `true`. */
    inferred_pantry_enabled?: boolean;
    /** C-cross Chunk 3 — per-user nutrition mode. Server rejects `complex`
     *  when no nutrition source has been configured (admin seam). */
    nutrition_mode?: 'off' | 'simple' | 'complex';
    /** C-cross Chunk 5 — per-user recipe-image opt-in. Saved photos
     *  survive a toggle (only rendering is suppressed). FU-508 dropped
     *  the stock-image companion. */
    show_recipe_images?: boolean;
    /** Onboarding C-5.4 — household cooking headcount (1–99). Server clears
     *  when `null` is sent. Drives serving-aware suggestions / shopping
     *  quantity hints. */
    household_headcount?: number | null;
    /** C-9.7 — alerts email digest channel. Cadence is `'off' | 'daily'
     *  | 'weekly'`; `alerts_email_day` is the weekly send day Mon=0 …
     *  Sun=6 (ignored on the daily cadence; saved either way). */
    alerts_email_enabled?: boolean;
    alerts_email_cadence?: 'off' | 'daily' | 'weekly';
    alerts_email_day?: number;
    /** Settings rebuild Phase 4 — profile picture. Data-URL string to set,
     *  `clear_image: true` to remove. Omitting both leaves it untouched. */
    image?: string | null;
    clear_image?: boolean;
    /** Dashboard rebuild Phase 2 — per-user dashboard layout JSON (card order +
     *  hidden set). A string sets it; `null` clears it back to the default
     *  layout. Omitting it leaves it untouched. */
    dashboard_layout?: string | null;
    /** FU-153 §7.1 / §7.4 — per-user assistant config. `llm_provider` is one
     *  of `'ollama' | 'openai' | 'anthropic' | 'gemini'`; URL/model are the
     *  per-provider fields; `llm_api_key` is write-only (server encrypts on
     *  save), `clear_llm_api_key: true` removes the saved key. */
    llm_enabled?: boolean;
    llm_provider?: 'ollama' | 'openai' | 'anthropic' | 'gemini' | null;
    llm_base_url?: string | null;
    llm_model?: string | null;
    llm_api_key?: string | null;
    clear_llm_api_key?: boolean;
    /** FU-360.6 — show/hide the Dora helper bubble for this account. */
    show_assistant?: boolean;
    /** FU-450 — good_deal alert threshold ('good' | 'great'). */
    good_deal_alert_threshold?: 'good' | 'great';
};
export type ChangePasswordCommand = {
    current_password: string;
    new_password: string;
};

export default class AuthApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    loginAsync = async (command: LoginCommand): Promise<AuthenticatedUser> =>
        await this.httpClient.post<AuthenticatedUser, LoginCommand>('/auth/login', command);

    registerAsync = async (command: RegisterCommand): Promise<AuthenticatedUser> =>
        await this.httpClient.post<AuthenticatedUser, RegisterCommand>('/auth/register', command);

    /** FU-200 — fresh-install probe. Returns `{ required: true }` when the
     *  DB has no users yet; the router uses this to route to /setup
     *  instead of /login. Never throws on a 401 (unauthenticated probes
     *  are explicitly allowed by the middleware). */
    bootstrapRequiredAsync = async (): Promise<boolean> => {
        const result = await this.httpClient.get<{ required: boolean }>(
            '/auth/bootstrap-required',
        );
        return result.required;
    };

    /** FU-200 — single-use first-admin creation. The server 410s once any
     *  user exists, so the SPA should only call this when
     *  bootstrapRequiredAsync() returned true. Success auto-logs the new
     *  admin in (session cookie set server-side). */
    bootstrapAdminAsync = async (
        command: BootstrapAdminCommand,
    ): Promise<AuthenticatedUser> =>
        await this.httpClient.post<AuthenticatedUser, BootstrapAdminCommand>(
            '/auth/bootstrap-admin', command,
        );

    logoutAsync = async (): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>('/auth/logout', {});

    updateMeAsync = async (command: UpdateMeCommand): Promise<AuthenticatedUser> =>
        await this.httpClient.patch<AuthenticatedUser, UpdateMeCommand>('/auth/me', command);

    changePasswordAsync = async (command: ChangePasswordCommand): Promise<void> =>
        await this.httpClient.post<void, ChangePasswordCommand>('/auth/me/password', command);

    // ── A1 out-of-band flows ───────────────────────────────────────
    verifyEmailAsync = async (token: string): Promise<void> =>
        await this.httpClient.post<void, { token: string }>('/auth/verify-email', { token });

    resendVerificationAsync = async (email: string): Promise<void> =>
        await this.httpClient.post<void, { email: string }>('/auth/resend-verification', { email });

    forgotPasswordAsync = async (email: string): Promise<void> =>
        await this.httpClient.post<void, { email: string }>('/auth/forgot-password', { email });

    resetPasswordAsync = async (token: string, newPassword: string): Promise<void> =>
        await this.httpClient.post<void, { token: string; new_password: string }>(
            '/auth/reset-password', { token, new_password: newPassword },
        );

    /** FU-197 — verified change-email flow. Requires the current
     *  password as proof-of-possession; on success the server emails a
     *  confirmation link to the NEW address and a heads-up notice to
     *  the OLD one. Nothing actually changes until the link is
     *  clicked. */
    requestEmailChangeAsync = async (
        newEmail: string,
        currentPassword: string,
    ): Promise<void> =>
        await this.httpClient.post<void, { new_email: string; current_password: string }>(
            '/auth/me/email', { new_email: newEmail, current_password: currentPassword },
        );

    confirmEmailChangeAsync = async (token: string): Promise<void> =>
        await this.httpClient.post<void, { token: string }>(
            '/auth/email-change/confirm', { token },
        );

    getMeAsync = async (): Promise<AuthenticatedUser | null> => {
        try {
            return await this.httpClient.get<AuthenticatedUser>('/auth/me');
        } catch (error) {
            // 401 means no session — caller treats null as "not logged in".
            // Network/server errors propagate so bootstrap can show a splash.
            if (error instanceof NormalisedApiError && error.status === 401) {
                return null;
            }
            throw error;
        }
    };
}
