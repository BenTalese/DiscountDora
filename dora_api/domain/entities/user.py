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

# grocery-budget period constants moved to AppSetting (the budget is now an
# install-wide household concept, not per-user — see app_setting.py
# BUDGET_PERIOD_*). This "grocery budget belongs to the household, not the
# person" move mirrors FU-615 (household_headcount / batch_features_enabled).

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

# Voice — which speech engine speaks Dora's replies / cook-mode steps and,
# for the Piper engine, which catalog voice. R-010 carve-out: closed-set
# string sentinels validated at a single boundary (`update_me.py`). The
# engine is the user's *preference*; if Piper can't actually speak (no
# binary / model), the SPA transparently falls back to the browser voice
# (see useSpeechOutput) — so `piper` is a safe default. The set of valid
# `voice_id`s is owned by the TTS feature catalog (features/tts/
# voice_catalog.py `VOICE_IDS`), not duplicated here.
VOICE_ENGINE_BROWSER = "browser"
VOICE_ENGINE_PIPER = "piper"
ALLOWED_VOICE_ENGINES = (VOICE_ENGINE_BROWSER, VOICE_ENGINE_PIPER)

# per-user alerts-email cadence (PROPOSAL_ALERTS §4.4). `off` is
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

# per-user LLM provider. Closed set validated at the
# update_me boundary (R-010 carve-out, same shape as nutrition_mode /
# alerts_email_cadence). Ollama is the local/free path; OpenAI /
# Anthropic / Gemini are paid API providers that additionally require
# an encrypted API key.
LLM_PROVIDER_OLLAMA = "ollama"
LLM_PROVIDER_OPENAI = "openai"
LLM_PROVIDER_ANTHROPIC = "anthropic"
LLM_PROVIDER_GEMINI = "gemini"
ALLOWED_LLM_PROVIDERS = (
    LLM_PROVIDER_OLLAMA,
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_GEMINI,
)
# Subset that needs an API key — used by update_me to decide when to
# fail-fast if the install hasn't configured key encryption.
LLM_PROVIDERS_REQUIRING_API_KEY = (
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_GEMINI,
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
    # A1: marks whether the user has clicked the verify-email link sent on
    # registration. First-user-is-admin auto-verifies so a fresh install
    # without SMTP doesn't lock its admin out.
    email_verified: bool = False
    # A1: bumped on every successful password change / reset. Stored as
    # the cutoff a session cookie's issued-at must beat, so resetting a
    # password effectively invalidates every existing session.
    password_changed_at: datetime | None = None
    # grocery budget moved to AppSetting (install-wide household budget):
    # spend is summed across every shared shopping list, so the target has
    # to be shared too — a per-user budget compared against a household
    # spend total is incoherent. See app_setting.py + FU-615 precedent.
    # voice opt-ins. Off by default because the Web Speech APIs
    # are permission-gated and behaviour varies by browser; we never
    # silently activate a microphone or speaker. The SPA reads these on
    # boot to seed the per-page toggles.
    voice_input_enabled: bool = False
    voice_output_enabled: bool = False
    # Voice engine + Piper voice selection. `voice_engine` is `browser` |
    # `piper`; default `piper` so Dora uses the nicer neural voice when it's
    # available (the bundled Amy/Ryan models ship for this), with a
    # browser-speech fallback when it isn't. `voice_id` names the chosen
    # catalog voice (default Amy). Only consulted when `voice_output_enabled`
    # is on — these decide *how* she speaks, not *whether*.
    voice_engine: str = VOICE_ENGINE_PIPER
    voice_id: str = "amy"
    # money-features opt-in removed: money is a single install-wide
    # concern now (AppSetting.money_enabled). There is no per-user money
    # layer — if the install has money on, dollar surfaces render for
    # everyone; off hides them for everyone. Dropped the old per-user
    # `money_features_enabled` (owner call: "kitchen setup, not personal").
    # FU-615 — `batch_features_enabled` moved to AppSetting (install-wide
    # cook-style; a household has one cook-style, not one per person).
    # per-user "always ask which draft list on quick-add" toggle.
    # Zero-Input Pantry opt-out. Default True: inferred stock
    # levels (the belief overlay) are the headline experience. Charter 10 —
    # some users want purely manual control, so this toggle switches the
    # belief chip + inference-driven quick-checks off.
    inferred_pantry_enabled: bool = True
    # C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
    # `off` | `simple` | `complex`; default `off`. `complex` is a
    # reserved seam (validated against `AppSetting.nutrition_db_source`
    # being non-empty) — the DB integration ships later. Layered with
    # the install-wide `nutrition_enabled` AppSetting via
    # `useNutritionMode()` (ADR-005).
    nutrition_mode: str = NUTRITION_MODE_OFF
    # C-cross Chunk 5 — per-user image-display opt-in (proposal §2.8).
    # **Default True** — Charter P1 Effortless leans toward visual
    # richness; users who prefer a text-only UI flip it via the inline
    # button on the recipes overview. Image upload/edit/delete keeps
    # working regardless; only the *render* is suppressed. FU-508
    # dropped the stock-image half of this pair (photos of pantry items
    # were never meaningfully used; a linked Product carries the visual).
    show_recipe_images: bool = True
    # FU-615 — `household_headcount` moved to AppSetting (install-wide;
    # a household has one headcount). Cook mode reads it via /api/health.
    # alerts email digest (PROPOSAL_ALERTS §3.5 / §4.4). Off by
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
    # Settings rebuild Phase 4 (§2.9) — optional profile picture, stored as a
    # data-URL blob (same convention as Store/StockItem images). Deferred at
    # the ORM layer so list endpoints never drag the bytes per row; the
    # dedicated `/users/<id>/image` route triggers the load on access and
    # `has_image` is derived from an IS-NOT-NULL check (mirrors StoreDto).
    image: bytes | None = None
    # Dashboard rebuild Phase 2 — per-user dashboard layout (card order +
    # hidden set + future zone tweaks), stored as a small JSON string. NULL =
    # the user hasn't customised; the SPA falls back to the default order. Kept
    # opaque to the backend on purpose (it's pure client view-state, R-003:
    # presentation belongs to the client) — we persist it verbatim so it
    # survives a cache clear and follows the user across devices.
    dashboard_layout: str | None = None
    # per-user assistant config. `llm_enabled` is the user's own opt-in and
    # the sole gate on AI mode — there is no install-wide master switch
    # (removed 2026-08-12). `llm_provider` names the *active* provider
    # (closed-set sentinel, R-010 / ALLOWED_LLM_PROVIDERS) or NULL for
    # Basic mode. The per-provider details (base URL / model / API key /
    # verified) live in the `UserLlmProvider` child table so a user can
    # configure several providers and flip between them — this column just
    # points at the one in use.
    llm_enabled: bool = False
    llm_provider: str | None = None
    # FU-360.6 — per-user "show the Dora helper bubble at all" opt-out.
    # **Default True** (Charter P1 Effortless — the helper is discoverable by
    # default). Distinct from `llm_enabled`: that switches the AI *mode*; this
    # hides the whole assistant launcher for users who don't want it. When
    # False the SPA doesn't mount the bubble, so Basic *and* AI mode are gone.
    show_assistant: bool = True
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
        EMAIL_VERIFIED = "email_verified"
        PASSWORD_CHANGED_AT = "password_changed_at"
        VOICE_INPUT_ENABLED = "voice_input_enabled"
        VOICE_OUTPUT_ENABLED = "voice_output_enabled"
        VOICE_ENGINE = "voice_engine"
        VOICE_ID = "voice_id"
        INFERRED_PANTRY_ENABLED = "inferred_pantry_enabled"
        NUTRITION_MODE = "nutrition_mode"
        SHOW_RECIPE_IMAGES = "show_recipe_images"
        ALERTS_EMAIL_ENABLED = "alerts_email_enabled"
        ALERTS_EMAIL_CADENCE = "alerts_email_cadence"
        ALERTS_EMAIL_DAY = "alerts_email_day"
        IMAGE = "image"
        DASHBOARD_LAYOUT = "dashboard_layout"
        LLM_ENABLED = "llm_enabled"
        LLM_PROVIDER = "llm_provider"
        SHOW_ASSISTANT = "show_assistant"
