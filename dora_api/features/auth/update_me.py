import logging
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.user import (ALLOWED_BUDGET_PERIODS,
                                           ALLOWED_FONT_FAMILIES,
                                           ALLOWED_FONT_SIZES, ALLOWED_THEMES,
                                           User)
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation, ok,
                                                  unauthorized)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Day of the week (0 = Mon … 6 = Sun) the weekly deals email should be sent.
    send_deals_on_day: int | None = Field(default=None, ge=0, le=6)
    email: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=255)
    deals_email_enabled: bool | None = None
    deals_email_compact: bool | None = None
    theme: str | None = None
    font_family: str | None = None
    font_size: str | None = None
    # P2-05 — grocery budget controls. `budget_amount` is the opt-in:
    # sending a positive number turns the feature on, sending
    # `clear_budget_amount: true` turns it off. Period change without
    # an amount change is allowed (lets the user re-pick weekly vs
    # monthly without resetting their number).
    budget_amount: float | None = Field(default=None, ge=0)
    clear_budget_amount: bool = False
    budget_period: str | None = None
    # P2-13 — voice opt-in toggles. Booleans only (no clear variant);
    # the feature is two-state per setting.
    voice_input_enabled: bool | None = None
    voice_output_enabled: bool | None = None


class UpdateMeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        request: UpdateMeRequest,
        user_id: UUID,
    ) -> tuple[AuthenticatedUserDto | None, str | None]:
        """Returns (dto, error_message). Error is set when the change is
        rejected (e.g. username collision or invalid enum value)."""
        _User: User | None = self.repository.get(User).by_id(user_id)
        if not _User:
            return None, None

        _SetFields = request.model_fields_set

        if "username" in _SetFields and request.username is not None:
            _UsernameField = EntityField(User, User.Fields.USERNAME)
            _SameName: User | None = (
                self.repository.get(User).one(_UsernameField.eq(request.username))
            )
            if _SameName and _SameName.id != user_id:
                return None, f"Username '{request.username}' is already taken."
            _User.username = request.username

        if "send_deals_on_day" in _SetFields and request.send_deals_on_day is not None:
            _User.send_deals_on_day = request.send_deals_on_day

        if "email" in _SetFields:
            _User.email = request.email

        if "deals_email_enabled" in _SetFields and request.deals_email_enabled is not None:
            _User.deals_email_enabled = request.deals_email_enabled

        if "deals_email_compact" in _SetFields and request.deals_email_compact is not None:
            _User.deals_email_compact = request.deals_email_compact

        if "theme" in _SetFields and request.theme is not None:
            if request.theme not in ALLOWED_THEMES:
                return None, f"Invalid theme '{request.theme}'."
            _User.theme = request.theme

        if "font_family" in _SetFields and request.font_family is not None:
            if request.font_family not in ALLOWED_FONT_FAMILIES:
                return None, f"Invalid font family '{request.font_family}'."
            _User.font_family = request.font_family

        if "font_size" in _SetFields and request.font_size is not None:
            if request.font_size not in ALLOWED_FONT_SIZES:
                return None, f"Invalid font size '{request.font_size}'."
            _User.font_size = request.font_size

        # P2-05 — budget. `clear_budget_amount` wins over any amount set
        # in the same payload so a clear+set in one request is unambiguous
        # (we treat clear as the user's primary intent).
        if request.clear_budget_amount:
            _User.budget_amount = None
        elif "budget_amount" in _SetFields and request.budget_amount is not None:
            # Zero is treated the same as "off" — there's nothing
            # meaningful to track against a $0 budget. Saves the
            # frontend from sending the clear flag separately.
            _User.budget_amount = request.budget_amount if request.budget_amount > 0 else None

        if "budget_period" in _SetFields and request.budget_period is not None:
            if request.budget_period not in ALLOWED_BUDGET_PERIODS:
                return None, f"Invalid budget period '{request.budget_period}'."
            _User.budget_period = request.budget_period

        # P2-13 — voice prefs. Plain bool fields; null is ignored.
        if "voice_input_enabled" in _SetFields and request.voice_input_enabled is not None:
            _User.voice_input_enabled = request.voice_input_enabled
        if "voice_output_enabled" in _SetFields and request.voice_output_enabled is not None:
            _User.voice_output_enabled = request.voice_output_enabled

        self.repository.save_changes()
        return AuthenticatedUserDto.from_entity(_User), None


@AUTH_ROUTER.route("/me", methods=["PATCH"])
@has_request_body(UpdateMeRequest)
def update_me():
    _Logger = logging.getLogger(__name__)
    _UserIdRaw = session.get(SESSION_USER_ID_KEY)
    if not _UserIdRaw:
        return unauthorized()
    try:
        _UserId = UUID(_UserIdRaw)
    except (ValueError, TypeError):
        session.clear()
        return unauthorized()

    _Request: UpdateMeRequest = get_request_body()
    _Dto, _Error = get_container().inject(UpdateMeHandler).handle(_Request, _UserId)

    if _Error is not None:
        return business_rule_violation(_Error)
    if _Dto is None:
        session.clear()
        return unauthorized()

    _Logger.info(f"Updated profile for user {_UserId}")
    return ok(_Dto)
