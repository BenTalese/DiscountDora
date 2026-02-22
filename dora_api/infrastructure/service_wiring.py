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
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.services.iconfiguration_manager import IConfigurationManager
from dora_api.services.irepository import IRepository


def build_dependency_container() -> DependencyContainer:
    container = DependencyContainer()

    container.register_service(providers.Factory, SqlAlchemyRepository[Merchant], IRepository[Merchant], model_class=Merchant)
    container.register_service(providers.Factory, SqlAlchemyRepository[Product], IRepository[Product], model_class=Product)
    container.register_service(providers.Factory, SqlAlchemyRepository[ProductOffer], IRepository[ProductOffer], model_class=ProductOffer)
    container.register_service(providers.Factory, SqlAlchemyRepository[ShoppingList], IRepository[ShoppingList], model_class=ShoppingList)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockItem], IRepository[StockItem], model_class=StockItem)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockLevel], IRepository[StockLevel], model_class=StockLevel)
    container.register_service(providers.Factory, SqlAlchemyRepository[StockLocation], IRepository[StockLocation], model_class=StockLocation)
    container.register_service(providers.Factory, SqlAlchemyRepository[User], IRepository[User], model_class=User)

    container.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)

    for _Handler in get_classes_ending_with('handler', Path() / 'dora_api' / 'features'):
        container.register_service(providers.Factory, _Handler)

    return container
