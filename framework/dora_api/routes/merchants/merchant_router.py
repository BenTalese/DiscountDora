from clapy import IServiceProvider
from flask import Blueprint, current_app

from framework.dora_api.routes.merchants.get_merchants_presenter import \
    GetMerchantsPresenter
from interface_adaptors.controllers.merchant_controller import \
    MerchantController

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")

@MERCHANT_ROUTER.route("")
@MERCHANT_ROUTER.route("<query>")
async def get_merchants_async(query = None):
    service_provider: IServiceProvider = current_app.service_provider
    merchant_controller: MerchantController = service_provider.get_service(MerchantController)
    presenter = GetMerchantsPresenter()

    await merchant_controller.get_merchants_async(presenter)
    return presenter.result
