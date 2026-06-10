"""PATCH /api/app-settings — admin-only edit of install-wide settings.

Only the assistant (BYO-LLM) config lives here for now. Fields are optional;
only those present in the request body are changed.
"""
import logging
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.app_settings.get_app_settings import AppSettingsDto, _to_dto
from dora_api.features.routers import APP_SETTINGS_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateAppSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_enabled: bool | None = None
    llm_base_url: str | None = Field(default=None, max_length=500)
    llm_model: str | None = Field(default=None, max_length=255)
    scanning_enabled: bool | None = None
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

        if "llm_base_url" in set_fields:
            setting.llm_base_url = (request.llm_base_url or "").strip()
        if "llm_model" in set_fields:
            setting.llm_model = (request.llm_model or "").strip()
        if "llm_enabled" in set_fields and request.llm_enabled is not None:
            setting.llm_enabled = request.llm_enabled
        if "scanning_enabled" in set_fields and request.scanning_enabled is not None:
            setting.scanning_enabled = request.scanning_enabled
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

        # Enabling without a connection is a misconfiguration — the assistant
        # would just silently fall back. Reject it so the admin gets told.
        if setting.llm_enabled and (not setting.llm_base_url or not setting.llm_model):
            return UpdateAppSettingsResponse(
                invalid_reason="Set both the LLM base URL and model before enabling the assistant."
            )

        self.repository.save_changes()
        return UpdateAppSettingsResponse(dto=_to_dto(setting))


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
    _Logger.info("Admin updated app settings (llm_enabled=%s)", _Response.dto.llm_enabled)
    return ok(_Response.dto)
