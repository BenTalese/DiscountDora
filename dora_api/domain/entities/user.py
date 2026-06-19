from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


# Preference enum-like constants. Kept here so handlers and DTOs share one
# source of truth and the frontend can validate against these values too.
THEME_SYSTEM = "system"
# Named themes — five families with paired light + dark variants. See
# web_app/src/services/themeService.ts THEME_FAMILIES for the source-
# of-truth palette + label metadata. `system` (and the per-family
# `system-*` variants below) resolves on the client based on
# `prefers-color-scheme`.
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
# Round-19 — per-family system mode. Splits the Preferences picker into
# Mode (System / Light / Dark) + Theme (Pesto / Lemon Tart / …) so a
# user can follow the OS using any family's variants, not just Pesto.
THEME_SYSTEM_PESTO = "system-pesto"
THEME_SYSTEM_LEMON_TART = "system-lemon-tart"
THEME_SYSTEM_BLUEBERRY = "system-blueberry"
THEME_SYSTEM_CHERRY_COLA = "system-cherry-cola"
THEME_SYSTEM_SOURDOUGH = "system-sourdough"
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
    # Per-family system keys (round-19).
    THEME_SYSTEM_PESTO,
    THEME_SYSTEM_LEMON_TART,
    THEME_SYSTEM_BLUEBERRY,
    THEME_SYSTEM_CHERRY_COLA,
    THEME_SYSTEM_SOURDOUGH,
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

# C-cross Chunk 3 — nutrition mode (proposal §2.3). R-010 carve-out:
# closed-set string sentinel backed by `NUTRITION_MODE_VALUES`, a
# single validation point in `update_me.py`, and named constants for
# every read. SQLite-portable (no CHECK constraint).
NUTRITION_MODE_OFF = "off"
NUTRITION_MODE_SIMPLE = "simple"
NUTRITION_MODE_COMPLEX = "complex"
NUTRITION_MODE_VALUES = (
    NUTRITION_MODE_OFF,
    NUTRITION_MODE_SIMPLE,
    NUTRITION_MODE_COMPLEX,
)

# C-9.7 — per-user alerts-email cadence (PROPOSAL_ALERTS §4.4). `off` is
# the absent-feature value (paired with `alerts_email_enabled=False` it's
# the default for a fresh user — quiet until opted in). R-010 carve-out:
# closed-set string sentinel, single validation point in `update_me.py`.
ALERTS_EMAIL_CADENCE_OFF = "off"
ALERTS_EMAIL_CADENCE_DAILY = "daily"
ALERTS_EMAIL_CADENCE_WEEKLY = "weekly"
ALERTS_EMAIL_CADENCE_VALUES = (
    ALERTS_EMAIL_CADENCE_OFF,
    ALERTS_EMAIL_CADENCE_DAILY,
    ALERTS_EMAIL_CADENCE_WEEKLY,
)


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
    # C-cross Chunk 2 — per-user money-features opt-in (proposal §2.2).
    # Default False — Charter P10 Anti-creep. Layered with the
    # install-wide `money_enabled` AppSetting (see useFeatureFlags +
    # ADR-005): both must be true for any dollar surface to render.
    # `budget_amount` / `budget_period` above remain the per-user
    # budget controls — they only become editable when this is True,
    # but the saved value survives a toggle round-trip.
    money_features_enabled: bool = False
    # C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
    # `off` | `simple` | `complex`; default `off`. `complex` is a
    # reserved seam (validated against `AppSetting.nutrition_db_source`
    # being non-empty) — the DB integration ships later. Layered with
    # the install-wide `nutrition_enabled` AppSetting via
    # `useNutritionMode()` (ADR-005).
    nutrition_mode: str = NUTRITION_MODE_OFF
    # C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).
    # **Default True** — Charter P1 Effortless leans toward visual
    # richness; users who prefer a text-only UI flip these via inline
    # buttons on each surface (recipes overview ships its button this
    # chunk; stock overview ships its button when C-1 row redesign
    # next runs — FU-106). Image upload/edit/delete keeps working
    # regardless; only the *render* is suppressed.
    show_recipe_images: bool = True
    show_stock_images: bool = True
    # Onboarding C-5.4 — how many people the household usually cooks for.
    # NULL = not set (cook mode falls back to each recipe's own `servings`).
    # Read by RecipeCookMode to seed its per-session serving scaler (L44).
    household_headcount: int | None = None
    # C-9.7 — alerts email digest (PROPOSAL_ALERTS §3.5 / §4.4). Off by
    # default (P10 Anti-creep + the proposal §5 "channels: in-app on; email
    # off (opt-in)"). When `alerts_email_enabled` is True, the scheduled
    # digest job (`send_alerts_digest`) runs at the user's `alerts_email_
    # cadence` ('daily' | 'weekly'; 'off' is the no-feature value paired
    # with the disabled flag). `alerts_email_day` is the weekly send day
    # (Mon=0 … Sun=6) and is ignored on the daily cadence. Independent of
    # the deals-email `send_deals_on_day` so the two channels stay
    # uncoupled (per-channel cleanliness).
    alerts_email_enabled: bool = False
    alerts_email_cadence: str = ALERTS_EMAIL_CADENCE_OFF
    alerts_email_day: int = 0
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
        MONEY_FEATURES_ENABLED = "money_features_enabled"
        NUTRITION_MODE = "nutrition_mode"
        SHOW_RECIPE_IMAGES = "show_recipe_images"
        SHOW_STOCK_IMAGES = "show_stock_images"
        HOUSEHOLD_HEADCOUNT = "household_headcount"
        ALERTS_EMAIL_ENABLED = "alerts_email_enabled"
        ALERTS_EMAIL_CADENCE = "alerts_email_cadence"
        ALERTS_EMAIL_DAY = "alerts_email_day"
