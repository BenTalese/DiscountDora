import logging
from dataclasses import dataclass
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import generate_password_hash

from dora_api.domain.entities.user import User
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


SESSION_USER_ID_KEY = "user_id"


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length = 1, max_length = 255)
    password: str = Field(min_length = 4, max_length = 255)
    email: str | None = Field(default = None, max_length = 255)


@dataclass(slots=True)
class RegisterUserResponse:
    new_user_id: UUID = EMPTY_UUID
    username_taken: bool = False
    is_admin: bool = False


@dataclass(frozen=True, slots=True)
class AuthenticatedUserDto:
    """Public-safe projection of a User. Never includes password_hash."""
    user_id: UUID
    username: str
    email: str | None
    is_admin: bool
    send_deals_on_day: int
    deals_email_enabled: bool
    deals_email_compact: bool
    theme: str
    font_family: str
    font_size: str
    # Surfaced on the auth payload so the router guard (F1) can decide
    # whether to bounce the user to /welcome without an extra round-trip
    # per navigation.
    onboarding_completed_at: str | None
    # Last successful GET /api/data/backup. Used by the Data → Backup &
    # restore card to show "last backup N ago".
    last_backup_at: str | None

    @classmethod
    def from_entity(cls, user: User) -> "AuthenticatedUserDto":
        return AuthenticatedUserDto(
            user_id = user.id,
            username = user.username,
            email = user.email,
            is_admin = bool(user.is_admin),
            send_deals_on_day = user.send_deals_on_day,
            deals_email_enabled = bool(user.deals_email_enabled),
            deals_email_compact = bool(user.deals_email_compact),
            theme = user.theme,
            font_family = user.font_family,
            font_size = user.font_size,
            onboarding_completed_at = (
                user.onboarding_completed_at.isoformat()
                if user.onboarding_completed_at is not None
                else None
            ),
            last_backup_at = (
                user.last_backup_at.isoformat()
                if user.last_backup_at is not None
                else None
            ),
        )


class RegisterUserHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: RegisterUserRequest) -> RegisterUserResponse:
        _UsernameField = EntityField(User, User.Fields.USERNAME)
        _Existing: User | None = self.repository.get(User).one(_UsernameField.eq(request.username))
        if _Existing:
            return RegisterUserResponse(username_taken = True)

        # First-user-is-admin convention: on a fresh install the person who
        # registers gets the admin role so they can configure the system.
        # Subsequent registrations default to non-admin.
        _IsFirstUser = self.repository.get(User).count() == 0

        _NewUser = User(
            email = request.email,
            password_hash = generate_password_hash(request.password),
            send_deals_on_day = 0,
            username = request.username,
            is_admin = _IsFirstUser,
        )
        self.repository.add(_NewUser)
        self.repository.save_changes()
        return RegisterUserResponse(
            new_user_id = _NewUser.id,
            is_admin = _IsFirstUser,
        )


@AUTH_ROUTER.route("/register", methods=["POST"])
@has_request_body(RegisterUserRequest)
def register_user():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(RegisterUserHandler)
    _Request: RegisterUserRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.username_taken:
        _Logger.warning(f"Registration rejected — username already taken: {_Request.username}")
        return business_rule_violation(f"Username '{_Request.username}' is already taken.")

    # Auto-login: drop the new user's id into the session so they don't have
    # to re-enter their credentials immediately after registering.
    session.clear()
    session[SESSION_USER_ID_KEY] = str(_Response.new_user_id)
    session.permanent = True

    _Logger.info(f"Registered user {_Request.username} ({_Response.new_user_id})")
    return ok(AuthenticatedUserDto(
        user_id = _Response.new_user_id,
        username = _Request.username,
        email = _Request.email,
        is_admin = _Response.is_admin,
        send_deals_on_day = 0,
        deals_email_enabled = True,
        deals_email_compact = False,
        theme = "system",
        font_family = "default",
        font_size = "md",
        onboarding_completed_at= None,
        last_backup_at = None,
    ))
