import importlib
import inspect
import os

from clapy import Common, DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.configure_services import \
    configure_application_services
from domain.infrastructure.configure_services import configure_domain_services
from framework.api.routes.products.create_product_presenter import \
    CreateProductPresenter
from framework.api.routes.products.get_products_presenter import \
    GetProductsPresenter
from framework.persistence.infrastructure.configure_services import \
    configure_persistence_services
from interface_adaptors.infrastructure.configure_services import \
    configure_interface_adaptors_services


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        return self \
            .configure_persistence_services() \
            .configure_core_services() \
            .register_presenters() \
            .service_provider

    def register_presenters(self):
        _PresenterClasses = []

        for _Root, _Directories, _Files in os.walk("framework/api/routes"):

            DIR_EXCLUSIONS = [r"__pycache__"]
            FILE_EXCLUSIONS = [r".*__init__\.py", r"^.*(?<!\.py)$"]
            Common.apply_exclusion_filter(_Directories, DIR_EXCLUSIONS)
            Common.apply_exclusion_filter(_Files, FILE_EXCLUSIONS)

            for _File in _Files:
                _Namespace = _Root.replace('/', '.').lstrip(".") + "." + _File[:-3]
                _Module = importlib.import_module(_Namespace, package=None)
                if _Module.__name__.endswith('presenter'):
                    [_PresenterClasses.append((_Class))
                     for _, _Class
                     in inspect.getmembers(_Module, inspect.isclass)
                     if _Class.__module__ == _Module.__name__]

        for _Presenter in _PresenterClasses:
            self.service_provider.register_service(providers.Factory, _Presenter)

        return self

    def configure_core_services(self):
        configure_domain_services(self.service_provider)
        configure_application_services(self.service_provider)
        self.service_provider.configure_clapy_services(["application/use_cases"], [r"venv", r"src"], [r".*main\.py"])
        configure_interface_adaptors_services(self.service_provider)
        return self

    def configure_persistence_services(self):
        configure_persistence_services(self.service_provider)
        return self
