"""PATCH /api/app-settings — admin-only edit of install-wide settings.

Only the assistant (BYO-LLM) config lives here for now. Fields are optional;
only those present in the request body are changed.
"""
import logging
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.app_settings.clock import is_valid_timezone
from dora_api.features.app_settings.get_app_settings import AppSettingsDto, _to_dto
from dora_api.features.routers import APP_SETTINGS_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateAppSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # FU-153 §7.1 — single install-wide master kill-switch for the
    # assistant feature. Per-user LLM URL/model/provider/API key live on
    # the User row now (see auth/update_me).
    master_llm_enabled: bool | None = None
    scanning_enabled: bool | None = None
    # P8-05 — buy-verdict oracle toggle.
    buy_verdict_enabled: bool | None = None
    # C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
    meal_planning_enabled: bool | None = None
    money_enabled: bool | None = None
    nutrition_enabled: bool | None = None
    companion_ingestion_enabled: bool | None = None
    deals_email_enabled: bool | None = None
    # C-cross Chunk 3 — reserved seam for nutrition complex-mode. Empty
    # string is allowed (and is the default-seam state); the actual
    # source schema lands when the complex-mode integration ships.
    nutrition_db_source: str | None = Field(default=None, max_length=255)
    # Meal Plans C-2.K — household IANA timezone (validated below).
    timezone: str | None = Field(default=None, max_length=64)
    # Alerts C-9.2 — household-wide expiring-soon window (bounds double as
    # R-010 validation: 1–365 days). The old
    # `default_days_until_stocktake_alert` field was retired in the
    # 2026-07-04 stocktake cleanup — the band system (below) owns cadence.
    expiring_soon_window_days: int | None = Field(default=None, ge=1, le=365)
    # Phase D / FU-186 — admin-set URL the Product Search nav opens.
    # Empty string ⇒ unset; the nav entry renders disabled with a hint.
    # We allow any http(s) URL or empty; deeper validation is the operator's
    # problem (the field never echoes back as a clickable link to other
    # users — it ALWAYS opens via target="_blank" rel="noopener").
    product_search_url: str | None = Field(default=None, max_length=500)
    # FU-227 follow-up — AU vs US per-unit display locale.
    unit_pricing_locale: str | None = Field(default=None, max_length=8)
    # FU-342 — backup library controls. Retention 1–100; storage_path
    # blank ⇒ default `<data-dir>/backups`. Non-blank path is validated
    # for writeability on save.
    backup_retention_count: int | None = Field(default=None, ge=1, le=100)
    backup_storage_path: str | None = Field(default=None, max_length=1024)
    # FU-345 — image compression knobs. Quality 30–100; max dimension
    # 512–8192 (below 512 → images legibly small; above 8192 → cap is
    # bigger than any realistic camera output and the byte cap on the
    # request schema kicks in first).
    image_quality: int | None = Field(default=None, ge=30, le=100)
    image_max_dimension: int | None = Field(default=None, ge=512, le=8192)
    # PROPOSAL_STOCKTAKE_MODE §4 + §8 — the two stocktake knobs.
    # Cadence band is one of {'weekly','fortnightly','monthly'}; the
    # handler validates against the enum below so a typo can't silently
    # degrade the queue.
    stocktake_default_cadence_band: str | None = Field(default=None, max_length=16)
    stocktake_auto_tuning_enabled: bool | None = None
    # FU-333 Bucket B — operational config previously carried as `DORA_*`
    # env vars. SMTP password + VAPID private key stay env-only until the
    # Bucket-C encrypted-in-DB storage lands; they are absent from this
    # DTO so an accidental client-side send can't smuggle them into the
    # database as plaintext.
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_from: str | None = Field(default=None, max_length=255)
    smtp_use_tls: bool | None = None
    vapid_public_key: str | None = Field(default=None, max_length=255)
    vapid_subject: str | None = Field(default=None, max_length=255)
    piper_bin: str | None = Field(default=None, max_length=1024)
    piper_bundled_voice_dir: str | None = Field(default=None, max_length=1024)
    piper_voice: str | None = Field(default=None, max_length=255)
    email_enabled: bool | None = None
    # Retention bounds: 1 day floor (anything less is effectively "no
    # audit"), ~10-year ceiling on a small install DB.
    audit_retention_days: int | None = Field(default=None, ge=1, le=3650)
    public_url: str | None = Field(default=None, max_length=500)


@dataclass(slots=True)
class UpdateAppSettingsResponse:
    invalid_reason: str | None = None
    dto: AppSettingsDto | None = None


class UpdateAppSettingsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateAppSettingsRequest) -> UpdateAppSettingsResponse:
        setting = get_or_create_app_setting(self.repository)
        set_fields = request.model_fields_set

        if "master_llm_enabled" in set_fields and request.master_llm_enabled is not None:
            setting.master_llm_enabled = request.master_llm_enabled
        if "scanning_enabled" in set_fields and request.scanning_enabled is not None:
            setting.scanning_enabled = request.scanning_enabled
        if "buy_verdict_enabled" in set_fields and request.buy_verdict_enabled is not None:
            setting.buy_verdict_enabled = request.buy_verdict_enabled
        # C-cross Chunk 1 — install feature flags. Partial-update semantics
        # like every other field above: only fields present in the body
        # change; the rest are left alone.
        for _Attr in (
            "meal_planning_enabled",
            "money_enabled",
            "nutrition_enabled",
            "companion_ingestion_enabled",
            "deals_email_enabled",
        ):
            if _Attr in set_fields:
                value = getattr(request, _Attr)
                if value is not None:
                    setattr(setting, _Attr, value)
        # C-cross Chunk 3 — nutrition source seam. Free-form for now;
        # later complex-mode work parses it. Strip on save.
        if "nutrition_db_source" in set_fields:
            setting.nutrition_db_source = (request.nutrition_db_source or "").strip()

        # Meal Plans C-2.K — household timezone. Validate against the IANA
        # database so an unparseable zone can't silently degrade the "today"
        # boundary to UTC for the whole install.
        if "timezone" in set_fields and request.timezone is not None:
            _Tz = request.timezone.strip()
            if not is_valid_timezone(_Tz):
                return UpdateAppSettingsResponse(
                    invalid_reason=f"'{_Tz}' is not a recognised IANA timezone."
                )
            setting.timezone = _Tz

        # Alerts C-9.2 — household-wide alert thresholds. Bounds enforced by
        # the request model above (R-010).
        if "expiring_soon_window_days" in set_fields and request.expiring_soon_window_days is not None:
            setting.expiring_soon_window_days = request.expiring_soon_window_days

        # FU-227 follow-up — unit_pricing_locale. Validated against the
        # supported set so a typo can't silently degrade display.
        if "unit_pricing_locale" in set_fields and request.unit_pricing_locale is not None:
            from dora_api.domain.units import SUPPORTED_PRICING_LOCALES
            _Locale = request.unit_pricing_locale.strip().upper()
            if _Locale not in SUPPORTED_PRICING_LOCALES:
                return UpdateAppSettingsResponse(
                    invalid_reason=(
                        f"'{_Locale}' is not a supported unit-pricing locale. "
                        f"Supported: {sorted(SUPPORTED_PRICING_LOCALES)}."
                    ),
                )
            setting.unit_pricing_locale = _Locale

        # Phase D / FU-186 — product_search_url. Strip; reject obviously
        # non-http schemes so a typo doesn't render a hostile link, but
        # otherwise leave validation to the operator.
        if "product_search_url" in set_fields:
            _Url = (request.product_search_url or "").strip()
            if _Url and not (_Url.startswith("http://") or _Url.startswith("https://")):
                return UpdateAppSettingsResponse(
                    invalid_reason="Product search URL must start with http:// or https://."
                )
            setting.product_search_url = _Url

        # FU-342 — backup library controls. Retention is a plain int
        # bounded by the request model; storage path is validated for
        # writeability (an admin pointing at a bad NAS mount finds out
        # here, not on the next backup attempt).
        if "backup_retention_count" in set_fields and request.backup_retention_count is not None:
            setting.backup_retention_count = request.backup_retention_count
        if "backup_storage_path" in set_fields:
            _Path = (request.backup_storage_path or "").strip()
            if _Path:
                invalid = _validate_backup_storage_path(_Path)
                if invalid is not None:
                    return UpdateAppSettingsResponse(invalid_reason=invalid)
            setting.backup_storage_path = _Path

        # FU-345 — image compression knobs. Bounds enforced by the
        # request model. Applies forward-only: existing images are not
        # re-encoded (out of scope; power users can log a follow-up if
        # they want a re-encode pass).
        if "image_quality" in set_fields and request.image_quality is not None:
            setting.image_quality = request.image_quality
        if "image_max_dimension" in set_fields and request.image_max_dimension is not None:
            setting.image_max_dimension = request.image_max_dimension

        # PROPOSAL_STOCKTAKE_MODE §4 + §8 — cadence band + Auto toggle.
        # Band is validated against the enum so a typo can't degrade
        # the queue to the fallback silently (R-010).
        if (
            "stocktake_default_cadence_band" in set_fields
            and request.stocktake_default_cadence_band is not None
        ):
            from dora_api.features.stocktake.cadence import CadenceBand
            _Band = request.stocktake_default_cadence_band.strip().lower()
            try:
                CadenceBand(_Band)
            except ValueError:
                return UpdateAppSettingsResponse(
                    invalid_reason=(
                        f"'{_Band}' is not a valid cadence band. "
                        f"Allowed: {[b.value for b in CadenceBand]}."
                    ),
                )
            setting.stocktake_default_cadence_band = _Band
        if (
            "stocktake_auto_tuning_enabled" in set_fields
            and request.stocktake_auto_tuning_enabled is not None
        ):
            setting.stocktake_auto_tuning_enabled = request.stocktake_auto_tuning_enabled

        # FU-333 Bucket B — operational config. Strings strip on save; the
        # `public_url` scheme guard mirrors `product_search_url` above so a
        # typo can't produce a hostile link in outbound emails.
        if "public_url" in set_fields:
            _Url = (request.public_url or "").strip()
            if _Url and not (_Url.startswith("http://") or _Url.startswith("https://")):
                return UpdateAppSettingsResponse(
                    invalid_reason="Public URL must start with http:// or https://."
                )
            setting.public_url = _Url
        for _StrField in (
            "smtp_host", "smtp_username", "smtp_from",
            "vapid_public_key", "vapid_subject",
            "piper_bin", "piper_bundled_voice_dir", "piper_voice",
        ):
            if _StrField in set_fields:
                _Value = getattr(request, _StrField)
                setattr(setting, _StrField, (_Value or "").strip())
        for _NumericOrBool in (
            "smtp_port", "smtp_use_tls",
            "email_enabled", "audit_retention_days",
        ):
            if _NumericOrBool in set_fields:
                _Value = getattr(request, _NumericOrBool)
                if _Value is not None:
                    setattr(setting, _NumericOrBool, _Value)

        # FU-153 §7.1 — the install-wide setting is now a master kill-
        # switch only; the per-user "have you finished setting up?"
        # validation moved to auth/update_me.py.

        self.repository.save_changes()
        return UpdateAppSettingsResponse(dto=_to_dto(setting))


def _validate_backup_storage_path(path_str: str) -> str | None:
    """FU-342 — accept only absolute paths that we can actually write to.
    Returns None on success, a user-facing reason on failure. Skips any
    creation on the AppSetting save; the create endpoint's mkdir handles
    directory materialisation, so we only assert the operator's chosen
    location is reachable."""
    import os
    from pathlib import Path
    try:
        candidate = Path(path_str).expanduser().resolve()
    except (OSError, ValueError):
        return f"'{path_str}' is not a valid filesystem path."
    if not candidate.is_absolute():
        return "Backup storage path must be absolute."
    # If the directory already exists, it must be a directory + writeable.
    if candidate.exists():
        if not candidate.is_dir():
            return f"'{candidate}' exists but is not a directory."
        if not os.access(candidate, os.W_OK):
            return f"'{candidate}' is not writeable by the server process."
        return None
    # Doesn't exist — check the nearest existing parent is writeable so
    # the create-endpoint mkdir will succeed.
    parent = candidate.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not parent.exists():
        return f"No existing ancestor of '{candidate}' — check the path."
    if not os.access(parent, os.W_OK):
        return f"Cannot create '{candidate}' — '{parent}' is not writeable."
    return None


@APP_SETTINGS_ROUTER.route("", methods=["PATCH"])
@has_request_body(UpdateAppSettingsRequest)
def update_app_settings():
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err
    _Request: UpdateAppSettingsRequest = get_request_body()
    _Response = UpdateAppSettingsHandler().handle(_Request)
    if _Response.invalid_reason is not None:
        return bad_request("Invalid settings.", detail=_Response.invalid_reason)
    _Logger.info("Admin updated app settings (master_llm_enabled=%s)", _Response.dto.master_llm_enabled)
    return ok(_Response.dto)
