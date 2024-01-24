from base64 import b64encode
from typing import List

from application.dtos.product_dto import ProductDto
from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker
from application.use_cases.products.update_product.update_product_input_port import \
    UpdateProductInputPort
from framework.merchant_api import coles_logic, woolworths_logic
from framework.merchant_api.get_merchants_presenter import GetMerchantsPresenter
from framework.merchant_api.get_products_presenter import GetProductsPresenter
from framework.merchant_api.models import ScrapedProductOffer
from framework.merchant_api.session import create_session
from framework.merchant_api.update_product_presenter import \
    UpdateProductPresenter
from interface_adaptors.controllers.merchant_controller import \
    MerchantController
from interface_adaptors.controllers.product_controller import ProductController

# TODO: Make into use cases, this'll do for now though
# TODO: Logging --- would be useful to know what the search term was that caused the error, and which merchant, etc
# TODO: This is probably an action (combining use cases)

class WebScraper:
    def __init__(self, merchant_controller: MerchantController, product_controller: ProductController):
        self.merchant_controller = merchant_controller
        self.product_controller = product_controller

    def search_for_product(self, search_term: str, start_page: int = 1, limit_results_to: int = 10) -> List[ScrapedProductOffer]:
        with create_session() as _Session:
            _Session.get('https://www.woolworths.com.au')
            # TODO: Why do .get() here? seems you get connection time out without it when making request inside .search()
            _WoolworthsProductOffers = [ScrapedProductOffer.translate_woolworths_offer(_ProductOffer)
                                        for _ProductOffer
                                        in woolworths_logic.search(_Session, search_term, start_page, start_page + 1, limit_results_to)]

            _Session.get('https://www.coles.com.au/')
            _ColesProductOffers = [ScrapedProductOffer.translate_coles_offer(_ProductOffer)
                                for _ProductOffer
                                in coles_logic.search(_Session, search_term, start_page, start_page + 1, limit_results_to)]

            _ScrapedOffers = _WoolworthsProductOffers + _ColesProductOffers
            for _Offer in _ScrapedOffers:
                _Offer.image = b64encode(_Session.get(_Offer.image_uri).content)

            return _ScrapedOffers

    async def get_product_offers_async(self) -> List[ProductDto]:
        # TODO: Either own service collection, or this is part of the API...
        #       -> I think make this a hosted service, kept here in this folder, with the product controller as a dependency
        # TODO: register this controller as a service that can be DI'ed


        _GetMerchantsPresenter = GetMerchantsPresenter()
        await self.merchant_controller.get_merchants_async(_GetMerchantsPresenter)

        _GetProductsPresenter = GetProductsPresenter()
        await self.product_controller.get_products_async(_GetProductsPresenter)

        with create_session() as _Session:
            _Session.get('https://www.woolworths.com.au')
            _WoolworthsMerchantID = next(_Merchant.merchant_id for _Merchant in _GetMerchantsPresenter.merchants if _Merchant.name == "Woolworths")
            _WoolworthsProductOffers = [
                (_Product, ScrapedProductOffer.translate_woolworths_offer(woolworths_logic.get_by_stockcode(_Session, _Product.merchant_stockcode)))
                for _Product
                in _GetProductsPresenter.products
                if _Product.merchant_id == _WoolworthsMerchantID
            ]

            _Session.get('https://www.coles.com.au/')
            _ColesMerchantID = next(_Merchant.merchant_id for _Merchant in _GetMerchantsPresenter.merchants if _Merchant.name == "Coles")
            _ColesProductOffers = [
                (_Product, ScrapedProductOffer.translate_coles_offer(coles_logic.get_by_stockcode(_Session, _Product.merchant_stockcode, _Product.name)))
                for _Product
                in _GetProductsPresenter.products
                if _Product.merchant_id == _ColesMerchantID
            ]

            _UpdatedProducts: List[ProductDto] = []
            for _Product, _Offer in _WoolworthsProductOffers + _ColesProductOffers:
                _InputPort = UpdateProductInputPort(
                    is_available = AttributeChangeTracker(_Offer.is_available),
                    price_now = AttributeChangeTracker(_Offer.price_now),
                    price_was = AttributeChangeTracker(_Offer.price_was),
                    product_id = _Product.product_id)

                _Presenter = UpdateProductPresenter()
                await self.product_controller.update_product_async(_InputPort, _Presenter)
                _UpdatedProducts.append(_Presenter.result)

            for _Product in _UpdatedProducts:
                _Product.image = b64encode(_Product.image) # FIXME: THIS FEELS VERY WRONG, NEED TO REASSESS STORAGE AND RETRIEVAL OF IMAGES (could move encode to mapping)

            return _UpdatedProducts
