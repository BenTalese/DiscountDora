from typing import List

from clapy import PipeConfiguration

from application.use_cases.users.get_users.get_users_input_port import \
    GetUsersInputPort
from application.use_cases.users.get_users.iget_users_output_port import \
    IGetUsersOutputPort

from .base_controller import DEFAULT_PIPELINE, BaseController


class UserController(BaseController):

    async def get_users_async(
            self,
            output_port: IGetUsersOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetUsersInputPort(), output_port, pipeline_configuration)
