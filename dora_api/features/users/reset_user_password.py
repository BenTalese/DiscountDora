"""POST /api/users/<user_id>/reset-password — admin sets a new password.

Admin convenience for the "I forgot my password" case. The new password is
sent in the response body (single use — the admin is expected to relay it to
the user out-of-band). We don't auto-email it because we don't have a
guarantee an SMTP server is configured.
"""
import logging
import secrets
import string
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.user import User
from dora_api.features.routers import USER_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.auth_helpers import hash_password
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# 12-char alphanumeric — readable enough to relay over chat, strong enough
# as a one-time pad until the user changes it themselves.
_RESET_ALPHABET = string.ascii_letters + string.digits


@dataclass(slots=True)
class ResetPasswordResponse:
    user_not_found: bool = False
    new_password: str | None = None


class ResetUserPasswordHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, user_id: UUID) -> ResetPasswordResponse:
        _Target: User | None = self.repository.get(User).by_id(user_id)
        if _Target is None:
            return ResetPasswordResponse(user_not_found=True)

        new_password = "".join(secrets.choice(_RESET_ALPHABET) for _ in range(12))
        _Target.password_hash = hash_password(new_password)
        self.repository.save_changes()
        return ResetPasswordResponse(new_password=new_password)


@USER_ROUTER.route("<user_id>/reset-password", methods=["POST"])
def reset_user_password(user_id: UUID):
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err

    _Response = ResetUserPasswordHandler(SqlAlchemyRepository()).handle(user_id)
    if _Response.user_not_found:
        return not_found("User", user_id)

    _Logger.info(f"Admin reset password for user {user_id}")
    return ok({"new_password": _Response.new_password})
