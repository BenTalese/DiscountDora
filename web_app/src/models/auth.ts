export type ThemePreference = 'system' | 'light' | 'dark';
export type FontFamilyPreference =
    | 'default'
    | 'urbanist'
    | 'nunito'
    | 'inter'
    | 'lexend'
    | 'plus_jakarta_sans';
export type FontSizePreference = 'sm' | 'md' | 'lg';

export type AuthenticatedUser = {
    user_id: string;
    username: string;
    email: string | null;
    is_admin: boolean;
    send_deals_on_day: number;
    deals_email_enabled: boolean;
    deals_email_compact: boolean;
    theme: ThemePreference;
    font_family: FontFamilyPreference;
    font_size: FontSizePreference;
    // ISO timestamp; null until the user finishes (or skips) the first-run
    // wizard. The router guard reads this to bounce incomplete users to
    // /welcome.
    onboarding_completed_at: string | null;
    // ISO timestamp of this user's last successful GET /api/data/backup,
    // surfaced in Data → Backup & restore. Null until the user has taken
    // their first backup.
    last_backup_at: string | null;
};
