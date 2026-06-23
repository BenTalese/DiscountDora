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
 *  clear) to bust the browser cache. Mirrors `stockItemImageUrl`. */
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
export type UpdateMeCommand = {
    send_deals_on_day?: number;
    email?: string | null;
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
    /** C-cross Chunk 3 — per-user nutrition mode. Server rejects `complex`
     *  when no nutrition source has been configured (admin seam). */
    nutrition_mode?: 'off' | 'simple' | 'complex';
    /** C-cross Chunk 5 — per-user image-display opt-ins. Saved photos
     *  survive a toggle (only rendering is suppressed). */
    show_recipe_images?: boolean;
    show_stock_images?: boolean;
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

    requestEmailChangeAsync = async (newEmail: string): Promise<void> =>
        await this.httpClient.post<void, { new_email: string }>(
            '/auth/me/email', { new_email: newEmail },
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
