"""POST /api/auth/me/password — change the signed-in user's password.

Separate endpoint (instead of accepting `password` on `PATCH /auth/me`) so
the contract is unambiguous: changing a password requires the *current*
password as proof-of-possession, and the response is intentionally empty.
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import check_password_hash, generate_password_hash

from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import SESSION_USER_ID_KEY
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  no_content, unauthorized)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=4, max_length=255)


@dataclass(slots=True)
class ChangePasswordResponse:
    user_not_found: bool = False
    current_password_wrong: bool = False


class ChangePasswordHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: ChangePasswordRequest, user_id: UUID) -> ChangePasswordResponse:
        _User: User | None = self.repository.get(User).by_id(user_id)
        if _User is None or not _User.password_hash:
            return ChangePasswordResponse(user_not_found=True)
        if not check_password_hash(_User.password_hash, request.current_password):
            return ChangePasswordResponse(current_password_wrong=True)

        _User.password_hash = generate_password_hash(request.new_password)
        self.repository.save_changes()
        return ChangePasswordResponse()


@AUTH_ROUTER.route("/me/password", methods=["POST"])
@has_request_body(ChangePasswordRequest)
def change_password():
    _Logger = logging.getLogger(__name__)
    _UserIdRaw = session.get(SESSION_USER_ID_KEY)
    if not _UserIdRaw:
        return unauthorized()
    try:
        _UserId = UUID(_UserIdRaw)
    except (ValueError, TypeError):
        session.clear()
        return unauthorized()

    _Request: ChangePasswordRequest = get_request_body()
    _Response = get_container().inject(ChangePasswordHandler).handle(_Request, _UserId)

    if _Response.user_not_found:
        session.clear()
        return unauthorized()
    if _Response.current_password_wrong:
        return business_rule_violation("Current password is incorrect.")

    _Logger.info(f"Password changed for user {_UserId}")
    return no_content()
