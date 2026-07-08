from uuid import UUID

from flask import session

from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_PWD_V_KEY,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class GetMeHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, user_id: UUID) -> User | None:
        return self.repository.get(User).by_id(user_id)


@AUTH_ROUTER.route("/me")
def get_me():
    _UserIdRaw = session.get(SESSION_USER_ID_KEY)
    if not _UserIdRaw:
        return unauthorized()
    try:
        _UserId = UUID(_UserIdRaw)
    except (ValueError, TypeError):
        session.clear()
        return unauthorized()

    user = GetMeHandler(SqlAlchemyRepository()).handle(_UserId)
    if user is None:
        # User row disappeared (deleted while logged in). Treat session as invalid.
        session.clear()
        return unauthorized()

    # A1: session-staleness check. If this user's password was changed
    # after the session was minted, the cookie is invalid — covers reset
    # (which invalidates everyone) and self-serve change-password
    # invalidating other-device sessions.
    stamped = session.get(SESSION_PWD_V_KEY)
    if (
        user.password_changed_at is not None
        and stamped
        and stamped < user.password_changed_at.isoformat()
    ):
        session.clear()
        return unauthorized()

    return ok(AuthenticatedUserDto.from_entity(user))
