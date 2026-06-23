import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type AdminUser = {
    user_id: string;
    username: string;
    email: string | null;
    is_admin: boolean;
    send_deals_on_day: number;
    deals_email_enabled: boolean;
    // Settings rebuild Phase 4 — whether the user has a profile picture
    // (bulk-stamped server-side; bytes fetched via /users/<id>/image).
    has_image: boolean;
};

export type AdminUpdateUserCommand = {
    username?: string;
    email?: string | null;
    is_admin?: boolean;
    deals_email_enabled?: boolean;
};

export type ResetPasswordResult = { new_password: string };

export default class UserAdminApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<Page<AdminUser>> =>
        await this.httpClient.get<Page<AdminUser>>('/users');

    updateAsync = async (
        userId: string,
        command: AdminUpdateUserCommand
    ): Promise<void> =>
        await this.httpClient.patch<void, AdminUpdateUserCommand>(
            `/users/${userId}`,
            command
        );

    resetPasswordAsync = async (userId: string): Promise<ResetPasswordResult> =>
        await this.httpClient.post<ResetPasswordResult, Record<string, never>>(
            `/users/${userId}/reset-password`,
            {}
        );
}
