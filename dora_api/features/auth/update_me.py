import logging
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.user import (ALERTS_EMAIL_CADENCE_VALUES,
                                           ALLOWED_BUDGET_PERIODS,
                                           ALLOWED_FONT_FAMILIES,
                                           ALLOWED_FONT_SIZES, ALLOWED_THEMES,
                                           ALLOWED_VOICE_ENGINES,
                                           NUTRITION_MODE_COMPLEX,
                                           NUTRITION_MODE_VALUES, User)
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.tts.voice_catalog import VOICE_IDS
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
    # Voice engine + Piper voice. Closed-set sentinels validated below
    # (R-010 carve-out): engine ∈ ALLOWED_VOICE_ENGINES, voice_id ∈ the TTS
    # catalog's VOICE_IDS.
    voice_engine: str | None = None
    voice_id: str | None = None
    # C-cross Chunk 2 — per-user money-features opt-in (proposal §2.2).
    money_features_enabled: bool | None = None
    # C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
    # Validated against NUTRITION_MODE_VALUES at the boundary
    # (R-010 carve-out for closed-set sentinels).
    nutrition_mode: str | None = None
    # C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).
    show_recipe_images: bool | None = None
    show_stock_images: bool | None = None
    # Onboarding C-5.4 — household cooking headcount (1–99; null clears it).
    household_headcount: int | None = Field(default=None, ge=1, le=99)
    # C-9.7 — alerts email digest prefs (PROPOSAL_ALERTS §3.5 / §4.4).
    # Cadence is a closed-set sentinel validated at this boundary (R-010
    # carve-out, same shape as `nutrition_mode`). Day is Mon=0 … Sun=6
    # and only consulted on the weekly cadence; saved either way so a
    # cadence flip back to weekly remembers the picked day.
    alerts_email_enabled: bool | None = None
    alerts_email_cadence: str | None = None
    alerts_email_day: int | None = Field(default=None, ge=0, le=6)
    # Settings rebuild Phase 4 (§2.9) — profile picture. Data-URL string to
    # set, `clear_image: true` to remove. Mirrors the Store image contract:
    # `image=None` without the clear flag means "leave untouched". Cap mirrors
    # the StockItem ceiling (~4.5 MB of base64).
    image: str | None = Field(default=None, max_length=6_000_000)
    clear_image: bool = False
    # Dashboard rebuild Phase 2 — per-user dashboard layout JSON (card order +
    # hidden set). Present-in-body sets it; sending `null` clears it back to
    # the default layout. Opaque to the backend (client view-state); the cap is
    # generous for the small JSON but bounds abuse.
    dashboard_layout: str | None = Field(default=None, max_length=20_000)


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

        # Voice engine + Piper voice. R-010 carve-out: closed-set sentinels
        # validated here against the domain engine set and the TTS catalog ids.
        if "voice_engine" in _SetFields and request.voice_engine is not None:
            if request.voice_engine not in ALLOWED_VOICE_ENGINES:
                return None, f"Invalid voice engine '{request.voice_engine}'."
            _User.voice_engine = request.voice_engine
        if "voice_id" in _SetFields and request.voice_id is not None:
            if request.voice_id not in VOICE_IDS:
                return None, f"Invalid voice '{request.voice_id}'."
            _User.voice_id = request.voice_id

        # C-cross Chunk 2 — per-user money opt-in. Plain bool; the
        # saved `budget_amount` survives toggling off (data preserved).
        if "money_features_enabled" in _SetFields and request.money_features_enabled is not None:
            _User.money_features_enabled = request.money_features_enabled

        # C-cross Chunk 3 — per-user nutrition mode. R-010 carve-out: a
        # closed-set sentinel validated at this single boundary point
        # against `NUTRITION_MODE_VALUES`. `complex` is additionally
        # gated by the install-wide `AppSetting.nutrition_db_source`
        # being non-empty — a user can't pick a mode the install
        # can't support.
        if "nutrition_mode" in _SetFields and request.nutrition_mode is not None:
            mode = request.nutrition_mode
            if mode not in NUTRITION_MODE_VALUES:
                return None, f"Invalid nutrition mode '{mode}'."
            if mode == NUTRITION_MODE_COMPLEX:
                _Setting = get_or_create_app_setting(self.repository)
                if not _Setting.nutrition_db_source:
                    return None, (
                        "Complex nutrition mode needs a nutrition data "
                        "source configured by an admin first."
                    )
            _User.nutrition_mode = mode

        # C-cross Chunk 5 — image-display opt-ins. Plain bools; null is
        # ignored. Saved image bytes survive a toggle (only the render
        # is suppressed).
        if "show_recipe_images" in _SetFields and request.show_recipe_images is not None:
            _User.show_recipe_images = request.show_recipe_images
        if "show_stock_images" in _SetFields and request.show_stock_images is not None:
            _User.show_stock_images = request.show_stock_images

        # Onboarding C-5.4 — household headcount. Present-in-body sets it (a
        # null clears it back to "use each recipe's servings"); the 1–99
        # bounds are enforced by the request model above.
        if "household_headcount" in _SetFields:
            _User.household_headcount = request.household_headcount

        # C-9.7 — alerts email digest. Plain bool + closed-set cadence +
        # 0–6 day. R-014 (shown-disabled when SMTP unset) is enforced on
        # the *frontend* via the `email_smtp_configured` feature flag;
        # the backend accepts the prefs regardless so a self-hosted user
        # who configures SMTP later doesn't have to re-toggle.
        if "alerts_email_enabled" in _SetFields and request.alerts_email_enabled is not None:
            _User.alerts_email_enabled = request.alerts_email_enabled
        if "alerts_email_cadence" in _SetFields and request.alerts_email_cadence is not None:
            cadence = request.alerts_email_cadence
            if cadence not in ALERTS_EMAIL_CADENCE_VALUES:
                return None, f"Invalid alerts email cadence '{cadence}'."
            _User.alerts_email_cadence = cadence
        if "alerts_email_day" in _SetFields and request.alerts_email_day is not None:
            _User.alerts_email_day = request.alerts_email_day

        # Settings rebuild Phase 4 — profile picture. `clear_image` wins over
        # any `image` in the same payload (clear is the primary intent), same
        # shape as the Store image handler. Stored as data-URL bytes.
        if request.clear_image:
            _User.image = None
        elif "image" in _SetFields and request.image is not None:
            _User.image = request.image.encode("utf-8")

        # Dashboard rebuild Phase 2 — layout JSON. Present-in-body sets it (a
        # null clears it back to the default layout). Stored verbatim; the
        # backend doesn't parse it (client view-state).
        if "dashboard_layout" in _SetFields:
            _User.dashboard_layout = request.dashboard_layout

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
