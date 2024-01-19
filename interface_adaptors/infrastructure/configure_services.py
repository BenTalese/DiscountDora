from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.utils import get_classes_ending_with


def configure_interface_adaptors_services(service_provider: DependencyInjectorServiceProvider) -> None:
    for _Controller in get_classes_ending_with('Controller', 'interface_adaptors/controllers'):
        service_provider.register_service(providers.Factory, _Controller)
