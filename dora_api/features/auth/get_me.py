from uuid import UUID

from flask import session

from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class GetMeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, user_id: UUID) -> AuthenticatedUserDto | None:
        entity = self.repository.get(User).by_id(user_id)
        return AuthenticatedUserDto.from_entity(entity) if entity else None


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

    _Dto = get_container().inject(GetMeHandler).handle(_UserId)
    if _Dto is None:
        # User row disappeared (deleted while logged in). Treat session as invalid.
        session.clear()
        return unauthorized()
    return ok(_Dto)
