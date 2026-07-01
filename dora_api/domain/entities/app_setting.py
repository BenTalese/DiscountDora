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
    # FU-153 §7.1 — single install-wide kill-switch for the whole assistant
    # feature. Defence in depth: a user can configure their own LLM per
    # §7.1, but the admin keeps a master toggle that forces every user's
    # AI mode off regardless. Per-user URL / model / provider / API key
    # live on User (see entity below).
    master_llm_enabled: bool = True
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
    # Phase D / FU-186 — install-wide URL the Product Search nav entry opens
    # in a new tab when product data is present. Set by the install operator
    # to point at whatever search surface they run themselves (a sibling
    # companion, a static page, etc — Dora doesn't know or care).
    # Empty string ⇒ no URL configured; the nav entry renders disabled with a
    # "Set up in Settings" hint (R-014 reveal-and-disable). See
    # `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.1.
    product_search_url: str = ""
    # FU-227 follow-up — the AU-shelf vs US-shelf display convention for
    # per-unit prices. `"AU"` shows `/100ml`/`/100g`/`/L`/`/kg`/`/ea` with
    # the flip at 1 L / 1 kg; `"US"` shows `/fl oz`/`/qt`/`/oz`/`/lb`/`/ea`
    # with the flip at 1 qt / 1 lb. Compute math stays in canonical L/kg;
    # only the display denominator changes. Default `"AU"` because Dora's
    # built here and ships AU-first; admin can flip to `"US"` in Settings.
    unit_pricing_locale: str = "AU"
    # FU-342 — backup library controls. `backup_retention_count` caps
    # the library; oldest above the cap is auto-dropped on each new
    # write. Default 5 is Pi-disk-conscious. `backup_storage_path`
    # empty ⇒ resolved to `$DORA_DATA_DIR/backups/` at runtime; an
    # admin may point at an external mount / NAS path (validated on
    # save).
    backup_retention_count: int = 5
    backup_storage_path: str = ""
    # FU-345 — install-wide image compression knobs. Applied at upload
    # time by the client-side `processImageFile` helper (R-003 pipeline
    # chokepoint) to every image surface. Existing images are untouched
    # — forward-only. 85 is visually indistinguishable from "original";
    # 60–70 is the disk-conscious floor. `image_max_dimension` caps the
    # longest edge in pixels; images above are scaled down first.
    image_quality: int = 85
    image_max_dimension: int = 1920

    class Fields(BaseEntity.Fields):
        MASTER_LLM_ENABLED = "master_llm_enabled"
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
        PRODUCT_SEARCH_URL = "product_search_url"
        UNIT_PRICING_LOCALE = "unit_pricing_locale"
        BACKUP_RETENTION_COUNT = "backup_retention_count"
        BACKUP_STORAGE_PATH = "backup_storage_path"
        IMAGE_QUALITY = "image_quality"
        IMAGE_MAX_DIMENSION = "image_max_dimension"
