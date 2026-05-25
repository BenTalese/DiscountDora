import logging
from dataclasses import dataclass

from flask import session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import check_password_hash

from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.domain.entities.audit_event import SEVERITY_AUDIT, SEVERITY_WARN
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.infrastructure.audit import emit as audit_emit
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length = 1, max_length = 255)
    password: str = Field(min_length = 1, max_length = 255)


@dataclass(slots=True)
class LoginResponse:
    user: User | None = None


class LoginHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: LoginRequest) -> LoginResponse:
        _UsernameField = EntityField(User, User.Fields.USERNAME)
        _User: User | None = self.repository.get(User).one(_UsernameField.eq(request.username))
        if not _User or not _User.password_hash:
            return LoginResponse(user = None)
        if not check_password_hash(_User.password_hash, request.password):
            return LoginResponse(user = None)
        return LoginResponse(user = _User)


@AUTH_ROUTER.route("/login", methods=["POST"])
@has_request_body(LoginRequest)
def login():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(LoginHandler)
    _Request: LoginRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.user is None:
        _Logger.warning(f"Failed login attempt for username '{_Request.username}'")
        audit_emit(
            "auth.login.failed",
            severity=SEVERITY_WARN,
            payload={"username": _Request.username},
        )
        # Intentionally generic so we don't leak whether the user exists.
        return unauthorized("Invalid username or password.")

    session.clear()
    session[SESSION_USER_ID_KEY] = str(_Response.user.id)
    session.permanent = True

    _Logger.info(f"Login success for {_Response.user.username} ({_Response.user.id})")
    audit_emit(
        "auth.login.success",
        severity=SEVERITY_AUDIT,
        actor_user_id=_Response.user.id,
        entity_type="User",
        entity_id=_Response.user.id,
        payload={"username": _Response.user.username},
    )
    return ok(AuthenticatedUserDto.from_entity(_Response.user))
