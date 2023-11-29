from typing import List
from application.dtos.user_dto import UserDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.users.get_users.iget_users_output_port import IGetUsersOutputPort


class GetUsersPresenter(IGetUsersOutputPort):
    users: List[UserDto] = None

    async def present_users_async(self, users: IQueryBuilder[UserDto]):
        self.users = users.execute()
