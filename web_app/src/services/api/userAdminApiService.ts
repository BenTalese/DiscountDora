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

// admin-create counterpart to
// `/auth/register`. Server mints a one-time password + returns it once;
// admin relays it out-of-band. No verification email; the admin
// implicitly vouches.
export type AdminCreateUserCommand = {
    username: string;
    email?: string | null;
    is_admin?: boolean;
};

export type CreateUserResult = { user_id: string; new_password: string };

export type ResetPasswordResult = { new_password: string };

export default class UserAdminApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<Page<AdminUser>> =>
        await this.httpClient.get<Page<AdminUser>>('/users');

    createAsync = async (
        command: AdminCreateUserCommand,
    ): Promise<CreateUserResult> =>
        await this.httpClient.post<CreateUserResult, AdminCreateUserCommand>(
            '/users',
            command,
        );

    updateAsync = async (
        userId: string,
        command: AdminUpdateUserCommand
    ): Promise<void> =>
        await this.httpClient.patch<void, AdminUpdateUserCommand>(
            `/users/${userId}`,
            command
        );

    deleteAsync = async (userId: string): Promise<void> =>
        await this.httpClient.delete(`/users/${userId}`);

    resetPasswordAsync = async (userId: string): Promise<ResetPasswordResult> =>
        await this.httpClient.post<ResetPasswordResult, Record<string, never>>(
            `/users/${userId}/reset-password`,
            {}
        );
}
