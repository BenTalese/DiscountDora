import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.user import User
from dora_api.features.routers import USER_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class UserDto:
    email: str | None
    send_deals_on_day: int
    username: str
    user_id: UUID

    @classmethod
    def from_entity(cls, user: User) -> 'UserDto':
        return UserDto(
            email = user.email,
            send_deals_on_day = user.send_deals_on_day,
            username = user.username,
            user_id = user.id.value
        )


class GetUsersHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[UserDto]:
        return self.repository.get(User).project(UserDto.from_entity)


@USER_ROUTER.route("")
@USER_ROUTER.route("<query>")
@has_response(UserDto)
def get_users(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get users.")
    _Handler = get_container().inject(GetUsersHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} users.")
    return ok(_Result)
