import type {
    AuthenticatedUser,
    FontFamilyPreference,
    FontSizePreference,
    ThemePreference
} from 'src/models/auth';
import AxiosHttpClient, { NormalisedApiError } from './axiosHttpClient';

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
