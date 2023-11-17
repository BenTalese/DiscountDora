from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers
from application.infrastructure.entity_existence_checker import EntityExistenceChecker
from application.services.ientity_existence_checker import IEntityExistenceChecker

from domain.infrastructure.configure_services import configure_domain_services


def configure_application_services(service_provider: DependencyInjectorServiceProvider) -> None:
    service_provider.register_service(providers.Factory, EntityExistenceChecker, IEntityExistenceChecker)
    configure_domain_services(service_provider)
