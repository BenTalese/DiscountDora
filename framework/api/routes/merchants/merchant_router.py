from clapy import IServiceProvider
from flask import Blueprint, current_app
from framework.api.routes.merchants.get_merchants_presenter import GetMerchantsPresenter

from interface_adaptors.controllers.merchant_controller import MerchantController

merchant_router = Blueprint("merchant_router", __name__, url_prefix="/api/merchants")

@merchant_router.route("")
@merchant_router.route("<query>")
async def get_merchants_async(query = None):
    service_provider: IServiceProvider = current_app.service_provider
    merchant_controller: MerchantController = service_provider.get_service(MerchantController)
    presenter = GetMerchantsPresenter()

    await merchant_controller.get_merchants_async(presenter)
    return presenter.result
