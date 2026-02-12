from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.users.get_users.iget_users_output_port import \
    IGetUsersOutputPort
from domain.entities.user import User
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.user_view_model import get_user_view_model


class GetUsersPresenter(BasePresenter, IGetUsersOutputPort):
    async def present_users_async(self, users: IQueryBuilder[User]):
        await self.ok_async(users.project(get_user_view_model).execute())
