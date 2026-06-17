from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AppSetting(BaseEntity):
    """Install-wide settings, edited by admins. A single row — see
    features/app_settings for the get-or-create accessor.

    The assistant (Dora's AI mode) is opt-in and bring-your-own-LLM: an admin
    enables it and points it at an LLM endpoint they run themselves (e.g. a
    local Ollama). Nothing is enabled or downloaded by default.

    Scanning + QR labels (real-world barcode → product navigation, plus Dora's
    own item/shelf QR labels) are one opt-in surface gated by a single
    install-wide flag, off by default. Scanning is navigation-only — it never
    does live deal lookup.
    """
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_model: str = ""
    scanning_enabled: bool = False
    # C-cross Chunk 1 — install-wide feature flags (proposal §2.6). Surface
    # via `/api/health features.*` + admin-only `PATCH /api/admin/feature-
    # flags`. Per-user opt-ins (money, nutrition, image display) layer on
    # top of these — install flag = "available here at all"; user flag =
    # "do I personally want to see it". Defaults are conservative: only
    # `meal_planning_enabled` ships True so existing installs don't lose
    # the meal-plan feature on first boot post-deploy.
    meal_planning_enabled: bool = True
    money_enabled: bool = False
    nutrition_enabled: bool = False
    companion_ingestion_enabled: bool = False
    deals_email_enabled: bool = False
    # FU-209 (PROPOSAL_PRODUCTS_AS_OVERLAY): `products_enabled` removed —
    # products is now a *data-presence* overlay. `features.products` is derived
    # server-side from whether any `Product` row exists (see health_check), not
    # from an admin/persona flag. The column is dropped in migration
    # f1a2b3c4d5e6.
    # C-cross Chunk 3 — reserved seam for the nutrition `complex` mode
    # (proposal §2.3). Stores the admin-configured nutrition data source
    # (a free-form string for now — the actual schema lands when the
    # complex-mode integration ships). Empty string ⇒ no source ⇒ a
    # user cannot save `nutrition_mode='complex'` (rejected at the
    # `update_me.py` boundary).
    nutrition_db_source: str = ""
    # Meal Plans C-2.K — household IANA timezone (e.g. "Australia/Sydney").
    # The "today" date boundary is evaluated here, not server-local, so a
    # household is correct regardless of where the server is hosted. Default
    # UTC until an admin sets it in System settings. App-wide adoption: FU-174.
    timezone: str = "UTC"
    # Alerts C-9.2 — household-wide alert thresholds (PROPOSAL_ALERTS §3.3).
    # These shape the shared derived alert set + the location heatmap, so they
    # live here (one server-side source — R-003), never copied to the client.
    # `expiring_soon_window_days` supersedes the `EXPIRING_SOON_WINDOW_DAYS`
    # constant, which is now the seeded default (resolved via
    # `stock_status.effective_expiring_soon_window`). `default_days_until_
    # stocktake_alert` is the new-item default for the per-item stocktake
    # cadence (0 = off, matching the previous hardcoded create default).
    expiring_soon_window_days: int = 7
    default_days_until_stocktake_alert: int = 0

    class Fields(BaseEntity.Fields):
        LLM_ENABLED = "llm_enabled"
        LLM_BASE_URL = "llm_base_url"
        LLM_MODEL = "llm_model"
        SCANNING_ENABLED = "scanning_enabled"
        MEAL_PLANNING_ENABLED = "meal_planning_enabled"
        MONEY_ENABLED = "money_enabled"
        NUTRITION_ENABLED = "nutrition_enabled"
        COMPANION_INGESTION_ENABLED = "companion_ingestion_enabled"
        DEALS_EMAIL_ENABLED = "deals_email_enabled"
        NUTRITION_DB_SOURCE = "nutrition_db_source"
        TIMEZONE = "timezone"
        EXPIRING_SOON_WINDOW_DAYS = "expiring_soon_window_days"
        DEFAULT_DAYS_UNTIL_STOCKTAKE_ALERT = "default_days_until_stocktake_alert"
