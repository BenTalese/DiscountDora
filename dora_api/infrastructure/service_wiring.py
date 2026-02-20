from pathlib import Path

from dependency_injector import providers

from application.infrastructure.entity_existence_checker import \
    EntityExistenceChecker
from application.infrastructure.utils import get_classes_ending_with
from application.services.ientity_existence_checker import \
    IEntityExistenceChecker
from application.services.irepository import IRepository
from dora_api.domain.entities.merchant import Merchant
from dora_api.infrastructure.configuration_manager import ConfigurationManager
from dora_api.infrastructure.dependency_container import DependencyContainer
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.services.iconfiguration_manager import IConfigurationManager


def build_dependency_container() -> DependencyContainer:
    container = DependencyContainer()

    container.register_service(providers.Factory, SqlAlchemyRepository[Merchant], IRepository[Merchant])
    container.register_service(providers.Factory, EntityExistenceChecker, IEntityExistenceChecker)
    container.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)

    for _Handler in get_classes_ending_with('handler', Path() / 'dora_api' / 'features'):
        container.register_service(providers.Factory, _Handler)

    return container
