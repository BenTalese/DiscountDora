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
    # single install-wide kill-switch for the whole assistant
    # feature. Defence in depth: a user can configure their own LLM per
    # §7.1, but the admin keeps a master toggle that forces every user's
    # AI mode off regardless. Per-user URL / model / provider / API key
    # live on User (see entity below).
    master_llm_enabled: bool = True
    scanning_enabled: bool = False
    # buy-verdict oracle ("should I buy this?"). Defaults **on**
    # because it's a pure-personal feature: no external calls, no crowd
    # data, no config required — the composer just needs the user's own
    # shopping-list / waste history. Admin can turn it off if the row-level
    # badges feel noisy on their pantry.
    buy_verdict_enabled: bool = True
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
    # `products_enabled` removed —
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
    # Alerts C-9.2 — household-wide "expiring soon" window used by both the
    # alerts feed and the assistant (PROPOSAL_ALERTS §3.3). One server-side
    # source (R-003); the constant `EXPIRING_SOON_WINDOW_DAYS` is now the
    # seeded default, resolved via `stock_status.effective_expiring_soon_window`.
    expiring_soon_window_days: int = 7
    # Phase D / FU-186 — install-wide URL the Product Search nav entry opens
    # in a new tab when product data is present. Set by the install operator
    # to point at whatever search surface they run themselves (a sibling
    # companion, a static page, etc — Dora doesn't know or care).
    # Empty string ⇒ no URL configured; the "Product Search" nav entry is
    # hidden entirely until a URL is set (setting it, in Settings → Features,
    # is what makes the button appear). See
    # `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.1.
    product_search_url: str = ""
    # the AU-shelf vs US-shelf display convention for
    # per-unit prices. `"AU"` shows `/100ml`/`/100g`/`/L`/`/kg`/`/ea` with
    # the flip at 1 L / 1 kg; `"US"` shows `/fl oz`/`/qt`/`/oz`/`/lb`/`/ea`
    # with the flip at 1 qt / 1 lb. Compute math stays in canonical L/kg;
    # only the display denominator changes. Default `"AU"` because Dora's
    # built here and ships AU-first; admin can flip to `"US"` in Settings.
    unit_pricing_locale: str = "AU"
    # install-wide currency + display
    # locale, so a non-AU install renders money and dates in a form its users
    # recognise. Single-source (R-003): every money render on the client goes
    # through one `Intl.NumberFormat(locale, { style: 'currency', currency })`
    # wrapper that reads both values from `/api/health`. Household-scoped
    # (one currency per install) — user chose install-wide over per-user,
    # matching the "a household shares a currency" model in the brief.
    # `currency` is an ISO 4217 code (3 letters); `locale` is a BCP-47 tag.
    # Defaults keep AU-shipped behaviour intact for existing installs.
    currency: str = "AUD"
    locale: str = "en-AU"
    # backup library controls. `backup_retention_count` caps
    # the library; oldest above the cap is auto-dropped on each new
    # write. Default 5 is Pi-disk-conscious. `backup_storage_path`
    # empty ⇒ resolved to `$DORA_DATA_DIR/backups/` at runtime; an
    # admin may point at an external mount / NAS path (validated on
    # save).
    backup_retention_count: int = 5
    backup_storage_path: str = ""
    # install-wide image compression knobs. Applied at upload
    # time by the client-side `processImageFile` helper (R-003 pipeline
    # chokepoint) to every image surface. Existing images are untouched
    # — forward-only. 85 is visually indistinguishable from "original";
    # 60–70 is the disk-conscious floor. `image_max_dimension` caps the
    # longest edge in pixels; images above are scaled down first.
    image_quality: int = 85
    image_max_dimension: int = 1920
    # PROPOSAL_STOCKTAKE_MODE §4 + §8 — the two global stocktake knobs.
    # `stocktake_default_cadence_band` is the baseline cadence when Auto
    # is off, and the fallback for items with no movement history.
    # Values: `'weekly'` (7d) / `'fortnightly'` (14d) / `'monthly'` (30d).
    # `stocktake_auto_tuning_enabled` is the master switch for the
    # movement-history self-tuner ("auto = speed" per the user's design
    # call) — on by default so a fresh install "just works".
    stocktake_default_cadence_band: str = "fortnightly"
    stocktake_auto_tuning_enabled: bool = True
    # FU-317 (D5 install-wide, FU-517) — household-shared posture for the
    # daily meal-plan reconcile sweep. TRUE (default) keeps today's silent
    # `reconcile_consumed_meals` drain plus a new receipt the user can
    # dispute on `/meal-plans/reconcile`. FALSE flips the sweep to write
    # `unresolved_manual` receipts and leave `MealPlanEntry.consumed_at` +
    # `Recipe.available_meals` untouched — the reconcile page becomes the
    # mutation surface. Install-wide (not per-user) because `MealPlan` has
    # no user_id / household_id — the plan is household-shared, so the
    # posture must be too. See PROPOSAL_MEAL_RECONCILE.md §2 + §11 D5.
    auto_drain_past_meals: bool = True
    # FU-511 — install-wide auto-add mode. Replaces the per-item
    # `StockItem.auto_add_when_low` boolean with one setting shared by
    # every item. Values:
    #   `'off'`            — never auto-add on low.
    #   `'essential_only'` — fire only for items flagged as essential
    #                        (`is_essential=True`). Default.
    #   `'all'`            — fire for any item that transitions Stocked
    #                        → Low/Out.
    # The `essential_only` default is the closest single behaviour to
    # the pre-migration pattern (auto-add was conceptually a marker of
    # "staple you never want to run out of" — same shape as Essential).
    # Server-side authority; see `update_stock_item._try_auto_add`.
    auto_add_mode: str = "essential_only"
    # FU-615 — household cooking config, install-wide (moved off User).
    # `household_headcount` is how many people the household usually cooks
    # for; NULL = not set (cook mode falls back to each recipe's own
    # `servings`). `batch_features_enabled` is the household's cook-style:
    # False ("fresh") keeps the meal-planner pure scheduling, True ("batch")
    # reveals the cook-pool affordances (per-recipe ± / log-cook / "n free"),
    # the shortfall warning, and the "to cook by" line. Both were per-user
    # (a convenience home for cook-mode's scaler); a household has one
    # headcount + one cook-style, so they're install-wide now. Read by every
    # client via /api/health.cooking_policy; edited by an admin in
    # Settings → System → Cooking.
    household_headcount: int | None = None
    batch_features_enabled: bool = False
    # operational config that was formerly carried as
    # `DORA_*` env vars. An admin now configures a fresh install through
    # Settings → Admin → System; the two remaining bootstrap-only vars
    # (`DORA_SECRET_KEY`, `DORA_SECRET_ENCRYPTION_KEY`) stay in env because
    # they're read before the DB is reachable / are root keys the DB
    # ciphertext depends on. On desktop bundles both are auto-generated on
    # first boot (see `desktop_app.py _bootstrap_keys`).
    #
    # Bucket C secrets — SMTP password + VAPID private key — live here
    # encrypted at rest with the Fernet helper at
    # `infrastructure/security/secret_encryption` using
    # `DORA_SECRET_ENCRYPTION_KEY` as the wrapping key. The plaintext
    # never leaves the write handler; reads decrypt on demand inside the
    # resolver. The DTO surfaces a `<field>_configured: bool` instead of
    # the ciphertext so the admin UI can render Set/Change without ever
    # transporting the secret.
    #
    # SMTP (was DORA_SMTP_HOST / _PORT / _USERNAME / _PASSWORD / _FROM / _USE_TLS).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password_encrypted: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    # Push (was DORA_VAPID_PUBLIC_KEY / _PRIVATE_KEY / _SUBJECT).
    vapid_public_key: str = ""
    vapid_private_key_encrypted: str = ""
    vapid_subject: str = "mailto:admin@dora.local"
    # TTS / Piper (was DORA_PIPER_BIN / _BUNDLED_VOICE_DIR).
    piper_bin: str = ""
    piper_bundled_voice_dir: str = ""
    # Misc operational.
    # `email_enabled` was DORA_EMAIL_ENABLED — the install-wide "email
    # subsystem is switched on" flag surfaced via /api/health features.email.
    email_enabled: bool = False
    audit_retention_days: int = 365
    public_url: str = ""

    class Fields(BaseEntity.Fields):
        MASTER_LLM_ENABLED = "master_llm_enabled"
        SCANNING_ENABLED = "scanning_enabled"
        BUY_VERDICT_ENABLED = "buy_verdict_enabled"
        MEAL_PLANNING_ENABLED = "meal_planning_enabled"
        MONEY_ENABLED = "money_enabled"
        NUTRITION_ENABLED = "nutrition_enabled"
        COMPANION_INGESTION_ENABLED = "companion_ingestion_enabled"
        DEALS_EMAIL_ENABLED = "deals_email_enabled"
        NUTRITION_DB_SOURCE = "nutrition_db_source"
        TIMEZONE = "timezone"
        EXPIRING_SOON_WINDOW_DAYS = "expiring_soon_window_days"
        PRODUCT_SEARCH_URL = "product_search_url"
        UNIT_PRICING_LOCALE = "unit_pricing_locale"
        CURRENCY = "currency"
        LOCALE = "locale"
        BACKUP_RETENTION_COUNT = "backup_retention_count"
        BACKUP_STORAGE_PATH = "backup_storage_path"
        IMAGE_QUALITY = "image_quality"
        IMAGE_MAX_DIMENSION = "image_max_dimension"
        STOCKTAKE_DEFAULT_CADENCE_BAND = "stocktake_default_cadence_band"
        STOCKTAKE_AUTO_TUNING_ENABLED = "stocktake_auto_tuning_enabled"
        AUTO_DRAIN_PAST_MEALS = "auto_drain_past_meals"
        AUTO_ADD_MODE = "auto_add_mode"
        HOUSEHOLD_HEADCOUNT = "household_headcount"
        BATCH_FEATURES_ENABLED = "batch_features_enabled"
        SMTP_HOST = "smtp_host"
        SMTP_PORT = "smtp_port"
        SMTP_USERNAME = "smtp_username"
        SMTP_PASSWORD_ENCRYPTED = "smtp_password_encrypted"
        SMTP_FROM = "smtp_from"
        SMTP_USE_TLS = "smtp_use_tls"
        VAPID_PUBLIC_KEY = "vapid_public_key"
        VAPID_PRIVATE_KEY_ENCRYPTED = "vapid_private_key_encrypted"
        VAPID_SUBJECT = "vapid_subject"
        PIPER_BIN = "piper_bin"
        PIPER_BUNDLED_VOICE_DIR = "piper_bundled_voice_dir"
        EMAIL_ENABLED = "email_enabled"
        AUDIT_RETENTION_DAYS = "audit_retention_days"
        PUBLIC_URL = "public_url"
