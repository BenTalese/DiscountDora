// Named-theme catalogue lives in services/themeService.ts. `light` and
// `dark` stay in the type for legacy values that may still be in the
// database; themeService maps them onto `pesto` and `midnight-snack`
// at apply time. `avocado` is similarly legacy — was retired when
// `pesto` (a fresher green) took over as the brand default.
export type ThemePreference =
    | 'system'
    // Round-19: per-family system-mode keys so the picker can split mode
    // (System / Light / Dark) and family (Pesto / Lemon Tart / …)
    // independently — picking System + Cherry Cola now actually follows
    // the OS using Cherry Cola variants, not the old hardcoded pesto
    // fallback. The bare `system` legacy key still resolves to the
    // pesto family for back-compat.
    | 'system-pesto'
    | 'system-lemon-tart'
    | 'system-blueberry'
    | 'system-cherry-cola'
    | 'system-sourdough'
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
// Which engine speaks Dora's replies / cook-mode steps. `piper` is the
// neural voice (POST /api/tts); `browser` is the built-in Web Speech voice.
// useSpeechOutput falls back from piper → browser when Piper isn't available.
export type VoiceEngine = 'browser' | 'piper';

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
    // Voice engine + chosen Piper voice id (from the server catalog,
    // GET /api/tts/voices). Drive useSpeechOutput; only matter when
    // voice_output_enabled is on. Default `piper` / `amy`.
    voice_engine: VoiceEngine;
    voice_id: string;
    // C-cross Chunk 2 — per-user money-features opt-in (proposal §2.2).
    // Layered with the install-wide `money_enabled` flag via
    // `useMoneyEnabled()`. `budget_amount` above stays the per-user
    // budget — saved value survives toggling this off (data preserved).
    money_features_enabled: boolean;
    // C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
    // `off` | `simple` | `complex`. Use `useNutritionMode()` to read —
    // the composable layers this with install `features.nutrition`.
    nutrition_mode: 'off' | 'simple' | 'complex';
    // C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).
    // Both default true (visual richness on). Use `useImagePrefs()` to
    // read + write — the composable owns the optimistic-flip + rollback.
    show_recipe_images: boolean;
    show_stock_images: boolean;
    // Onboarding C-5.4 — household cooking headcount; null = not set (cook
    // mode falls back to each recipe's own serving size).
    household_headcount: number | null;
    // C-9.7 — alerts email digest channel (PROPOSAL_ALERTS §3.5). Off by
    // default; `alerts_email_cadence` is `'off' | 'daily' | 'weekly'` and
    // `alerts_email_day` is the weekly send day (Mon=0 … Sun=6, ignored on
    // daily). The toggle is gated on `features.email_smtp_configured` so a
    // self-hosted install without SMTP shows the control disabled (R-014).
    alerts_email_enabled: boolean;
    alerts_email_cadence: 'off' | 'daily' | 'weekly';
    alerts_email_day: number;
    // Settings rebuild Phase 4 — whether the user has a profile picture.
    // Bytes are fetched separately via `GET /users/<id>/image`; server-derived
    // so the SPA never keeps its own truth about whether a picture exists.
    has_image: boolean;
    // Dashboard rebuild Phase 2 — per-user dashboard layout JSON (card order +
    // hidden set), or null when the user hasn't customised. Parsed by the
    // dashboard to seed card order/visibility; persisted via PATCH /auth/me so
    // it survives a cache clear and follows the user across devices.
    dashboard_layout: string | null;
};
