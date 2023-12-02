from application.dtos.user_dto import UserDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.users.get_users.iget_users_output_port import \
    IGetUsersOutputPort
from framework.api.base_presenter import BasePresenter
from framework.api.view_models.user_view_model import get_user_view_model


class GetUsersPresenter(BasePresenter, IGetUsersOutputPort):
    async def present_users_async(self, users: IQueryBuilder[UserDto]):
        await self.ok_async(users.project(get_user_view_model).execute())
