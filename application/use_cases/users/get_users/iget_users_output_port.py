from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.user import User


class IGetUsersOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_users_async(self, users: IQueryBuilder[User]) -> None:
        pass
