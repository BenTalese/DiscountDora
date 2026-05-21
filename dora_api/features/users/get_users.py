import logging
from dataclasses import dataclass
from uuid import UUID

from flask import request

from dora_api.domain.entities.user import User
from dora_api.features.routers import USER_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class UserDto:
    email: str | None
    send_deals_on_day: int
    username: str
    user_id: UUID
    is_admin: bool
    deals_email_enabled: bool

    @classmethod
    def from_entity(cls, user: User) -> 'UserDto':
        return UserDto(
            email = user.email,
            send_deals_on_day = user.send_deals_on_day,
            username = user.username,
            user_id = user.id,
            is_admin = bool(user.is_admin),
            deals_email_enabled = bool(user.deals_email_enabled),
        )


_FIELD_MAP: dict[str, EntityField] = {
    "user_id": EntityField(User, "id"),
}


class GetUsersHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[UserDto]:
        return self.repository.get(User).paginate(
            options, UserDto.from_entity, field_map=_FIELD_MAP
        )


@USER_ROUTER.route("")
def get_users():
    _Logger = logging.getLogger(__name__)
    # Admin-only — non-admin users shouldn't be able to enumerate accounts.
    from dora_api.features.users.update_user_as_admin import _require_admin
    _, err = _require_admin()
    if err is not None:
        return err
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetUsersHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} users.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
