// Named-theme catalogue lives in services/themeService.ts. `light` and
// `dark` stay in the type for legacy values that may still be in the
// database; themeService maps them onto `pesto` and `midnight-snack`
// at apply time. `avocado` is similarly legacy — was retired when
// `pesto` (a fresher green) took over as the brand default.
export type ThemePreference =
    | 'system'
    | 'pesto'
    | 'pesto-dark'
    | 'lemon-tart'
    | 'lemon-tart-dark'
    | 'blueberry'
    | 'blueberry-dark'
    | 'cherry-cola'
    | 'cherry-cola-dark'
    | 'sourdough'
    | 'sourdough-dark'
    // Legacy — themeService maps these forward at apply time.
    | 'pesto-noir'      // → pesto-dark
    | 'midnight-snack'  // → lemon-tart-dark
    | 'avocado'         // → pesto
    | 'light'           // → pesto
    | 'dark';           // → pesto-dark
export type FontFamilyPreference =
    | 'default'
    | 'urbanist'
    | 'nunito'
    | 'inter'
    | 'lexend'
    | 'plus_jakarta_sans';
export type FontSizePreference = 'sm' | 'md' | 'lg' | 'xl';
export type BudgetPeriod = 'weekly' | 'monthly';

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
    // A1: false until the user clicks the verification link in the email
    // sent on registration. Drives the verify-banner on LoginPage and
    // the Settings → Account hint. First-user-is-admin auto-verifies.
    email_verified: boolean;
    // P2-05 — optional grocery budget. `null` amount = feature off
    // (the user hasn't opted in). Period chooses the rolling window.
    budget_amount: number | null;
    budget_period: BudgetPeriod;
    // P2-13 — voice opt-ins. Both default false; the SPA seeds its
    // per-page mic / volume toggles from these on boot.
    voice_input_enabled: boolean;
    voice_output_enabled: boolean;
};
