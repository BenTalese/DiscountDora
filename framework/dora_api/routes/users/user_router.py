from clapy import IServiceProvider
from flask import Blueprint, current_app
from framework.dora_api.routes.users.get_users_presenter import GetUsersPresenter

from interface_adaptors.controllers.user_controller import UserController


USER_ROUTER = Blueprint("USER_ROUTER", __name__, url_prefix="/api/users")

@USER_ROUTER.route("")
@USER_ROUTER.route("<query>")
async def get_users_async(query = None):
    service_provider: IServiceProvider = current_app.service_provider
    user_controller: UserController = service_provider.get_service(UserController)
    presenter = GetUsersPresenter()

    await user_controller.get_users_async(presenter)
    return presenter.result
