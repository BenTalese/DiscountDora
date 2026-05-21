import type {
    AuthenticatedUser,
    FontFamilyPreference,
    FontSizePreference,
    ThemePreference
} from 'src/models/auth';
import AxiosHttpClient from './axiosHttpClient';

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

    getMeAsync = async (): Promise<AuthenticatedUser | null> => {
        try {
            return await this.httpClient.get<AuthenticatedUser>('/auth/me');
        } catch {
            // 401 means no session — caller treats null as "not logged in".
            return null;
        }
    };
}
