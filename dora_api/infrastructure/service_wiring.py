from pathlib import Path

from dependency_injector import providers

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User
from dora_api.infrastructure.configuration_manager import ConfigurationManager
from dora_api.infrastructure.dependency_container import DependencyContainer
from dora_api.infrastructure.utils import get_classes_ending_with
from dora_api.persistence.models.merchant_model import MerchantModel
from dora_api.persistence.models.product_model import ProductModel
from dora_api.persistence.models.product_offer_model import ProductOfferModel
from dora_api.persistence.models.shopping_list_model import ShoppingListModel
from dora_api.persistence.models.stock_item_model import StockItemModel
from dora_api.persistence.models.stock_level_model import StockLevelModel
from dora_api.persistence.models.stock_location_model import StockLocationModel
from dora_api.persistence.models.user_model import UserModel
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.services.iconfiguration_manager import IConfigurationManager
from dora_api.services.irepository import IRepository


def build_dependency_container() -> DependencyContainer:
    container = DependencyContainer()

    container.register_service(providers.Factory, SqlAlchemyRepository[Merchant], IRepository[Merchant], model_class=MerchantModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[Product], IRepository[Product], model_class=ProductModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[ProductOffer], IRepository[ProductOffer], model_class=ProductOfferModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[ShoppingList], IRepository[ShoppingList], model_class=ShoppingListModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockItem], IRepository[StockItem], model_class=StockItemModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockLevel], IRepository[StockLevel], model_class=StockLevelModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockLocation], IRepository[StockLocation], model_class=StockLocationModel)
    container.register_service(providers.Factory, SqlAlchemyRepository[User], IRepository[User], model_class=UserModel)

    container.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)

    for _Handler in get_classes_ending_with('handler', Path() / 'dora_api' / 'features'):
        container.register_service(providers.Factory, _Handler)

    return container
