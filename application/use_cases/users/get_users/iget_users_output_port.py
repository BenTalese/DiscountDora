from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.user_dto import UserDto
from application.services.iquerybuilder import IQueryBuilder


class IGetUsersOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_users_async(self, users: IQueryBuilder[UserDto]) -> None:
        pass
