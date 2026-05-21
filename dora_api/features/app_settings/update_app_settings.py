"""PATCH /api/app-settings — admin-only edit of install-wide settings.

Only the assistant (BYO-LLM) config lives here for now. Fields are optional;
only those present in the request body are changed.
"""
import logging
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.app_settings.get_app_settings import AppSettingsDto
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

        # Enabling without a connection is a misconfiguration — the assistant
        # would just silently fall back. Reject it so the admin gets told.
        if setting.llm_enabled and (not setting.llm_base_url or not setting.llm_model):
            return UpdateAppSettingsResponse(
                invalid_reason="Set both the LLM base URL and model before enabling the assistant."
            )

        self.repository.save_changes()
        return UpdateAppSettingsResponse(dto=AppSettingsDto(
            llm_enabled=bool(setting.llm_enabled),
            llm_base_url=setting.llm_base_url or "",
            llm_model=setting.llm_model or "",
        ))


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
