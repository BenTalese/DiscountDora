from clapy import IServiceProvider
from flask import Blueprint, current_app
from framework.dora_api.infrastructure.view_model_decorator import has_view_model
from framework.dora_api.routes.users.get_users_presenter import GetUsersPresenter
from framework.dora_api.view_models.user_view_model import UserViewModel

from interface_adaptors.controllers.user_controller import UserController


USER_ROUTER = Blueprint("USER_ROUTER", __name__, url_prefix="/api/users")


@USER_ROUTER.route("")
@USER_ROUTER.route("<query>")
@has_view_model('get_users_async', UserViewModel)
async def get_users_async(query = None):
    service_provider: IServiceProvider = current_app.service_provider
    user_controller: UserController = service_provider.get_service(UserController)
    presenter = GetUsersPresenter()

    await user_controller.get_users_async(presenter)
    return presenter.result
