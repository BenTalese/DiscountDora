from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


# Preference enum-like constants. Kept here so handlers and DTOs share one
# source of truth and the frontend can validate against these values too.
THEME_SYSTEM = "system"
# Named themes — five families with paired light + dark variants. See
# web_app/src/services/themeService.ts THEME_FAMILIES for the source-
# of-truth palette + label metadata. `system` resolves on the client to
# `pesto` (OS light) / `pesto-dark` (OS dark).
THEME_PESTO = "pesto"
THEME_PESTO_DARK = "pesto-dark"
THEME_LEMON_TART = "lemon-tart"
THEME_LEMON_TART_DARK = "lemon-tart-dark"
THEME_BLUEBERRY = "blueberry"
THEME_BLUEBERRY_DARK = "blueberry-dark"
THEME_CHERRY_COLA = "cherry-cola"
THEME_CHERRY_COLA_DARK = "cherry-cola-dark"
THEME_SOURDOUGH = "sourdough"
THEME_SOURDOUGH_DARK = "sourdough-dark"
# Legacy values accepted on the wire so existing rows don't fail
# validation; the SPA's themeService maps each to a current key at
# apply time:
#   pesto-noir       → pesto-dark
#   midnight-snack   → lemon-tart-dark   (absorbed into Lemon Tart family)
#   light, avocado   → pesto
#   dark             → pesto-dark
THEME_PESTO_NOIR = "pesto-noir"
THEME_MIDNIGHT_SNACK = "midnight-snack"
THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_AVOCADO = "avocado"
ALLOWED_THEMES = (
    THEME_SYSTEM,
    THEME_PESTO, THEME_PESTO_DARK,
    THEME_LEMON_TART, THEME_LEMON_TART_DARK,
    THEME_BLUEBERRY, THEME_BLUEBERRY_DARK,
    THEME_CHERRY_COLA, THEME_CHERRY_COLA_DARK,
    THEME_SOURDOUGH, THEME_SOURDOUGH_DARK,
    # Legacy
    THEME_PESTO_NOIR,
    THEME_MIDNIGHT_SNACK,
    THEME_LIGHT,
    THEME_DARK,
    THEME_AVOCADO,
)

FONT_FAMILY_DEFAULT = "default"
FONT_FAMILY_URBANIST = "urbanist"
FONT_FAMILY_NUNITO = "nunito"
FONT_FAMILY_INTER = "inter"
FONT_FAMILY_LEXEND = "lexend"
FONT_FAMILY_PLUS_JAKARTA_SANS = "plus_jakarta_sans"
ALLOWED_FONT_FAMILIES = (
    FONT_FAMILY_DEFAULT,
    FONT_FAMILY_URBANIST,
    FONT_FAMILY_NUNITO,
    FONT_FAMILY_INTER,
    FONT_FAMILY_LEXEND,
    FONT_FAMILY_PLUS_JAKARTA_SANS,
)

FONT_SIZE_SM = "sm"
FONT_SIZE_MD = "md"
FONT_SIZE_LG = "lg"
FONT_SIZE_XL = "xl"  # A6 — extra-large step
ALLOWED_FONT_SIZES = (FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL)

# P2-05 — grocery-budget period. `weekly` rolls from Monday; `monthly`
# from the 1st (local-civil-date for simplicity; the home use-case
# doesn't justify timezone gymnastics).
BUDGET_PERIOD_WEEKLY = "weekly"
BUDGET_PERIOD_MONTHLY = "monthly"
ALLOWED_BUDGET_PERIODS = (BUDGET_PERIOD_WEEKLY, BUDGET_PERIOD_MONTHLY)


@dataclass
class User(BaseEntity):
    email: str | None
    password_hash: str | None
    send_deals_on_day: int
    username: str
    is_admin: bool = False
    # Opt-out flag so users can disable the weekly deals email without losing
    # their preferred send day; defaults to True so existing users keep
    # receiving emails unless they explicitly turn it off.
    deals_email_enabled: bool = True
    deals_email_compact: bool = False
    theme: str = THEME_SYSTEM
    font_family: str = FONT_FAMILY_DEFAULT
    font_size: str = FONT_SIZE_MD
    # NULL until the user finishes (or skips) the welcome wizard. The
    # auth/router guard reads this on every navigation to decide whether
    # to bounce them to /welcome. Cleared by the Settings → Account
    # "Restart onboarding" entry.
    onboarding_completed_at: datetime | None = None
    # Stamped every time the user successfully downloads a backup via
    # GET /api/data/backup. Surfaced in the Data → Backup & restore card
    # so the user can see when they last took a snapshot.
    last_backup_at: datetime | None = None
    # A1: marks whether the user has clicked the verify-email link sent on
    # registration. First-user-is-admin auto-verifies so a fresh install
    # without SMTP doesn't lock its admin out.
    email_verified: bool = False
    # A1: bumped on every successful password change / reset. Stored as
    # the cutoff a session cookie's issued-at must beat, so resetting a
    # password effectively invalidates every existing session.
    password_changed_at: datetime | None = None
    # P2-05 — optional grocery budget. `budget_amount` NULL means the
    # feature is disabled (the user hasn't opted in); a positive value
    # turns on dashboard + assistant budget surfaces. `budget_period`
    # picks the rolling window. We deliberately don't store the period
    # *start* — it's derived from the current date so it can't go stale.
    budget_amount: float | None = None
    budget_period: str = BUDGET_PERIOD_WEEKLY
    # P2-13 — voice opt-ins. Off by default because the Web Speech APIs
    # are permission-gated and behaviour varies by browser; we never
    # silently activate a microphone or speaker. The SPA reads these on
    # boot to seed the per-page toggles.
    voice_input_enabled: bool = False
    voice_output_enabled: bool = False
    # TODO: avoid god object | separate auth credential from user profile

    class Fields(BaseEntity.Fields):
        EMAIL = "email"
        PASSWORD_HASH = "password_hash"
        SEND_DEALS_ON_DAY = "send_deals_on_day"
        USERNAME = "username"
        IS_ADMIN = "is_admin"
        DEALS_EMAIL_ENABLED = "deals_email_enabled"
        DEALS_EMAIL_COMPACT = "deals_email_compact"
        THEME = "theme"
        FONT_FAMILY = "font_family"
        FONT_SIZE = "font_size"
        ONBOARDING_COMPLETED_AT = "onboarding_completed_at"
        LAST_BACKUP_AT = "last_backup_at"
        EMAIL_VERIFIED = "email_verified"
        PASSWORD_CHANGED_AT = "password_changed_at"
        BUDGET_AMOUNT = "budget_amount"
        BUDGET_PERIOD = "budget_period"
        VOICE_INPUT_ENABLED = "voice_input_enabled"
        VOICE_OUTPUT_ENABLED = "voice_output_enabled"
