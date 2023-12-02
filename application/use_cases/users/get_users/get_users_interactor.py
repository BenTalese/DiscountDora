from clapy import Interactor

from application.dtos.user_dto import get_user_dto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.users.get_users.get_users_input_port import \
    GetUsersInputPort
from application.use_cases.users.get_users.iget_users_output_port import \
    IGetUsersOutputPort
from domain.entities.user import User


class GetUsersInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetUsersInputPort, output_port: IGetUsersOutputPort):
        await output_port \
            .present_users_async(self.persistence_context
                                       .get_entities(User)
                                       .project(get_user_dto))
