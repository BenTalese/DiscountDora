"""Admin-only user maintenance endpoints.

`PATCH /api/users/<user_id>` lets an admin change another user's username,
email, deals subscription, or admin flag. Password resets live on a
dedicated route (see reset_user_password.py) so they don't share a payload
with general edits.
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.user import User
from dora_api.features.auth.admin_gate import _require_admin
from dora_api.features.routers import USER_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository

# `_require_admin` moved to a shared module. Re-exported for
# feature modules that still import from here — no big-bang rename.
__all__ = ["AdminUpdateUserRequest", "AdminUpdateUserResponse", "_require_admin"]


class AdminUpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    is_admin: bool | None = None
    deals_email_enabled: bool | None = None
    # Settings rebuild Phase 4 (§2.9) — admins can clear a problematic user's
    # profile picture (and set one, for completeness). Same data-URL contract
    # as `/auth/me`: `clear_image` wins; `image=None` without it = untouched.
    image: str | None = Field(default=None, max_length=6_000_000)
    clear_image: bool = False


@dataclass(slots=True)
class AdminUpdateUserResponse:
    user_not_found: bool = False
    username_taken: bool = False
    would_remove_last_admin: bool = False


class AdminUpdateUserHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        request: AdminUpdateUserRequest,
        user_id: UUID,
    ) -> AdminUpdateUserResponse:
        _Target: User | None = self.repository.get(User).by_id(user_id)
        if _Target is None:
            return AdminUpdateUserResponse(user_not_found=True)

        _SetFields = request.model_fields_set

        if "username" in _SetFields and request.username is not None:
            _UsernameField = EntityField(User, User.Fields.USERNAME)
            _SameName: User | None = (
                self.repository.get(User).one(_UsernameField.eq(request.username))
            )
            # str(...) both sides — raw str path param vs UUID id (FU-528
            # family): a bare `!=` made an admin re-submitting a user's own
            # username 422 as "taken".
            if _SameName and str(_SameName.id) != str(user_id):
                return AdminUpdateUserResponse(username_taken=True)
            _Target.username = request.username

        if "email" in _SetFields:
            _Target.email = request.email

        if "is_admin" in _SetFields and request.is_admin is not None:
            # Guard against an admin demoting themselves into a system with
            # no admins. We don't block "demote someone else" because the
            # caller is already an admin and the system isn't single-user
            # by design.
            if not request.is_admin and _Target.is_admin:
                _IsAdminField = EntityField(User, User.Fields.IS_ADMIN)
                _AdminCount = self.repository.get(User).count(_IsAdminField.eq(True))
                if _AdminCount <= 1:
                    return AdminUpdateUserResponse(would_remove_last_admin=True)
            _Target.is_admin = request.is_admin

        if "deals_email_enabled" in _SetFields and request.deals_email_enabled is not None:
            _Target.deals_email_enabled = request.deals_email_enabled

        # Settings rebuild Phase 4 — profile picture. `clear_image` wins over
        # `image` in the same payload (mirrors update_me).
        if request.clear_image:
            _Target.image = None
        elif "image" in _SetFields and request.image is not None:
            _Target.image = request.image.encode("utf-8")

        self.repository.save_changes()
        return AdminUpdateUserResponse()


@USER_ROUTER.route("<uuid:user_id>", methods=["PATCH"])
@has_request_body(AdminUpdateUserRequest)
def admin_update_user(user_id: UUID):
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err

    _Request: AdminUpdateUserRequest = get_request_body()
    _Response = AdminUpdateUserHandler(SqlAlchemyRepository()).handle(_Request, user_id)

    if _Response.user_not_found:
        return not_found("User", user_id)
    if _Response.username_taken:
        return business_rule_violation(
            f"Username '{_Request.username}' is already taken."
        )
    if _Response.would_remove_last_admin:
        return business_rule_violation(
            "Refusing to remove the last admin — promote someone else first."
        )

    _Logger.info(f"Admin updated user {user_id}")
    return no_content()
