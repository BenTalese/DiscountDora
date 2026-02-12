from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.services.ipersistence_context import IPersistenceContext
from framework.dora_api.persistence.persistence_context import \
    SqlAlchemyPersistenceContext


def configure_persistence_services(service_provider: DependencyInjectorServiceProvider):
    service_provider.register_service(providers.Factory, SqlAlchemyPersistenceContext, IPersistenceContext)
