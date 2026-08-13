import logging
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.user import (ALERTS_EMAIL_CADENCE_VALUES,
                                           ALLOWED_FONT_FAMILIES,
                                           ALLOWED_FONT_SIZES,
                                           ALLOWED_LLM_PROVIDERS,
                                           ALLOWED_THEMES,
                                           ALLOWED_VOICE_ENGINES,
                                           NUTRITION_MODE_COMPLEX,
                                           NUTRITION_MODE_VALUES, User)
from dora_api.features.assistant.providers import get_provider_config
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.tts.voice_catalog import VOICE_IDS
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation, ok,
                                                  unauthorized)
from dora_api.infrastructure.auth_helpers import is_valid_email, normalise_email
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Day of the week (0 = Mon … 6 = Sun) the weekly deals email should be sent.
    send_deals_on_day: int | None = Field(default=None, ge=0, le=6)
    # Direct email edit. The old verified change-email flow (password proof +
    # confirmation link + old-address notice) was retired as overengineered
    # for this app — the owner edits their address inline and it's trusted.
    # Empty string clears the address; a non-empty value is validated +
    # deduped in the handler. Omit the field to leave it untouched.
    email: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=255)
    deals_email_enabled: bool | None = None
    deals_email_compact: bool | None = None
    theme: str | None = None
    font_family: str | None = None
    font_size: str | None = None
    # grocery budget moved to AppSetting (install-wide household budget);
    # edited via PATCH /api/budget/settings, not this endpoint.
    # voice opt-in toggles. Booleans only (no clear variant);
    # the feature is two-state per setting.
    voice_input_enabled: bool | None = None
    voice_output_enabled: bool | None = None
    # Voice engine + Piper voice. Closed-set sentinels validated below
    # (R-010 carve-out): engine ∈ ALLOWED_VOICE_ENGINES, voice_id ∈ the TTS
    # catalog's VOICE_IDS.
    voice_engine: str | None = None
    voice_id: str | None = None
    # money opt-in removed — money is one install-wide flag now.
    # FU-615 — `batch_features_enabled` moved to AppSetting (install-wide);
    # edited via PATCH /app-settings, not here.
    # Zero-Input Pantry opt-out (default True on the entity).
    inferred_pantry_enabled: bool | None = None
    # C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
    # Validated against NUTRITION_MODE_VALUES at the boundary
    # (R-010 carve-out for closed-set sentinels).
    nutrition_mode: str | None = None
    # C-cross Chunk 5 — per-user recipe-image opt-in (proposal §2.8).
    # FU-508 dropped the stock-image companion.
    show_recipe_images: bool | None = None
    # FU-615 — `household_headcount` moved to AppSetting (install-wide);
    # edited via PATCH /app-settings, not here.
    # alerts email digest prefs (PROPOSAL_ALERTS §3.5 / §4.4).
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
    # per-user assistant Mode. `llm_enabled` is the AI-mode opt-in and
    # `llm_provider` the active provider (closed-set sentinel, R-010,
    # validated below against ALLOWED_LLM_PROVIDERS). The per-provider
    # details (base URL / model / API key) are edited via the
    # `/assistant/providers` endpoints, not here. Enabling AI mode requires
    # the active provider to already be verified (see the guard below).
    llm_enabled: bool | None = None
    llm_provider: str | None = Field(default=None, max_length=16)
    # FU-360.6 — per-user "show the Dora helper bubble" opt-out. Plain bool;
    # null is ignored (leave untouched). Independent of `llm_enabled`.
    show_assistant: bool | None = None


class UpdateMeHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

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

        if "email" in _SetFields:
            # Empty/whitespace clears the address; otherwise validate format
            # and reject a duplicate held by another account (email drives
            # password-reset delivery, so it stays unique even though login
            # is by username). Owner-entered mail is trusted — the verified
            # change flow is gone — so a set address counts as verified.
            _EmailNorm = normalise_email(request.email)
            if _EmailNorm:
                if not is_valid_email(_EmailNorm):
                    return None, "That doesn't look like a valid email address."
                _EmailField = EntityField(User, User.Fields.EMAIL)
                _SameEmail: User | None = (
                    self.repository.get(User).one(_EmailField.eq(_EmailNorm))
                )
                if _SameEmail and _SameEmail.id != user_id:
                    return None, f"Email '{_EmailNorm}' is already in use."
            if _User.email != _EmailNorm:
                _User.email = _EmailNorm
                _User.email_verified = bool(_EmailNorm)

        if "send_deals_on_day" in _SetFields and request.send_deals_on_day is not None:
            _User.send_deals_on_day = request.send_deals_on_day

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

        # grocery budget moved to AppSetting (install-wide household budget);
        # edited via PATCH /api/budget/settings, not here.

        # voice prefs. Plain bool fields; null is ignored.
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

        # money opt-in removed — money is a single install-wide flag
        # (AppSetting.money_enabled); there is no per-user money layer.
        # FU-615 — batch cook-style moved to AppSetting (install-wide).
        # Zero-Input Pantry opt-out.
        if (
            "inferred_pantry_enabled" in _SetFields
            and request.inferred_pantry_enabled is not None
        ):
            _User.inferred_pantry_enabled = request.inferred_pantry_enabled

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

        # C-cross Chunk 5 — recipe-image opt-in. Plain bool; null is
        # ignored. Saved image bytes survive a toggle (only the render
        # is suppressed). FU-508 dropped the stock-image companion.
        if "show_recipe_images" in _SetFields and request.show_recipe_images is not None:
            _User.show_recipe_images = request.show_recipe_images

        # FU-615 — household headcount moved to AppSetting (install-wide);
        # edited via PATCH /app-settings.

        # alerts email digest. Plain bool + closed-set cadence +
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

        # per-user assistant Mode selection. `llm_provider` picks the active
        # provider (or None → Basic); `llm_enabled` is the AI opt-in. Details
        # for each provider live in the `UserLlmProvider` table, edited via
        # `/assistant/providers`.
        # FU-360.6 — show/hide the Dora helper bubble. Plain bool; null ignored.
        if "show_assistant" in _SetFields and request.show_assistant is not None:
            _User.show_assistant = request.show_assistant

        if "llm_provider" in _SetFields:
            provider = request.llm_provider
            if provider is not None:
                provider = provider.strip()
                if not provider:
                    provider = None
                elif provider not in ALLOWED_LLM_PROVIDERS:
                    return None, f"Invalid LLM provider '{provider}'."
            _User.llm_provider = provider
        if "llm_enabled" in _SetFields and request.llm_enabled is not None:
            _User.llm_enabled = request.llm_enabled

        # Cross-field validation: turning AI mode on requires an active
        # provider whose config has been verified (a live probe succeeded).
        # The Mode picker only offers verified providers, so this guards
        # direct/stale API calls.
        if _User.llm_enabled:
            if not _User.llm_provider:
                return None, "Pick a provider before enabling AI mode."
            active = get_provider_config(self.repository, user_id, _User.llm_provider)
            if active is None or not active.verified:
                return None, (
                    f"{_User.llm_provider} isn't verified yet — test the "
                    f"connection in Settings → Assistant before enabling AI mode."
                )

        self.repository.save_changes()
        active_provider = (
            get_provider_config(self.repository, user_id, _User.llm_provider)
            if _User.llm_provider else None
        )
        return AuthenticatedUserDto.from_entity(_User, active_provider), None


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
    _Dto, _Error = UpdateMeHandler(SqlAlchemyRepository()).handle(_Request, _UserId)

    if _Error is not None:
        return business_rule_violation(_Error)
    if _Dto is None:
        session.clear()
        return unauthorized()

    _Logger.info(f"Updated profile for user {_UserId}")
    return ok(_Dto)
