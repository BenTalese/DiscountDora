from pathlib import Path

from dependency_injector import providers

from dora_api.infrastructure.configuration_manager import ConfigurationManager
from dora_api.infrastructure.dependency_container import DependencyContainer
from dora_api.infrastructure.utils import get_classes_ending_with
from dora_api.services.iconfiguration_manager import IConfigurationManager


def build_dependency_container() -> DependencyContainer:
    container = DependencyContainer()

    # Example usage:
    # container.register_service(providers.Factory, SqlAlchemyGateway[Merchant], IRepository[Merchant], model_class=MerchantModel)

    container.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)

    for _Handler in get_classes_ending_with('handler', Path() / 'dora_api' / 'features'):
        container.register_service(providers.Factory, _Handler)

    return container
