from pathlib import Path

from dependency_injector import providers

from dora_api.infrastructure.configuration_manager import ConfigurationManager
from dora_api.infrastructure.dependency_container import DependencyContainer
from dora_api.infrastructure.utils import get_classes_ending_with
from dora_api.services.iconfiguration_manager import IConfigurationManager


def build_dependency_container() -> DependencyContainer:
    container = DependencyContainer()

    # container.register_service(providers.Factory, SqlAlchemyGateway[Merchant], IRepository[Merchant], model_class=MerchantModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[Product], IRepository[Product], model_class=ProductModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[ProductOffer], IRepository[ProductOffer], model_class=ProductOfferModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[ShoppingList], IRepository[ShoppingList], model_class=ShoppingListModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[StockItem], IRepository[StockItem], model_class=StockItemModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[StockLevel], IRepository[StockLevel], model_class=StockLevelModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[StockLocation], IRepository[StockLocation], model_class=StockLocationModel)
    # container.register_service(providers.Factory, SqlAlchemyGateway[User], IRepository[User], model_class=UserModel)

    container.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)

    for _Handler in get_classes_ending_with('handler', Path() / 'dora_api' / 'features'):
        container.register_service(providers.Factory, _Handler)

    return container
