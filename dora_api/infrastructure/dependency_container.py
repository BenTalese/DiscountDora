import inspect
import re
from typing import Optional, Tuple, Type

from dependency_injector import containers

from dora_api.domain.exceptions import DependencyConstructionError, DuplicateServiceError
from dora_api.domain.generics import TService


class DependencyContainer(containers.DeclarativeContainer):
    # TODO: This goes with the AI code below
    # def __init__(self):
    #     self._services: Dict[Type, providers.Provider] = {}

    def inject(self, service: type[TService]) -> TService:
        '''
        Summary
        -------
        Retrieves the specified service from the dependency_injector container.

        Parameters
        ----------
        `service` The service to be retrieved.

        Exceptions
        ----------
        Raises a `LookupError` if the service could not be resolved.

        Returns
        -------
        An instance of the requested service type with a lifetime as defined on the container.

        '''
        _ServiceName, _GenerationSuccess = self._try_generate_service_name(service)

        if _GenerationSuccess:
            _Service = self.providers.get(_ServiceName)

            if _Service is not None:
                try:
                    return _Service()
                except TypeError as ex:
                    raise DependencyConstructionError(
                        f"Unable to construct service '{service.__name__}'. "
                        "Make sure all required services are registered in the DI "
                        "container, and make sure all services implementing an "
                        "interface are implemented correctly. "
                        f"See inner exception: {ex}.")

        raise LookupError(f"Unable to retrieve '{service.__name__}' from DI container.")

    # TODO: Get inspiration from this AI generated version
    # def inject2(self, service_type: Type[TService], **runtime_overrides) -> TService:
    #     """
    #     Retrieve a service from the container.

    #     Optional runtime_overrides can override constructor parameters.
    #     """
    #     if service_type not in self._services:
    #         raise LookupError(f"Service not registered: {service_type.__name__}")

    #     provider_instance = self._services[service_type]

    #     if runtime_overrides:
    #         # Override parameters at runtime
    #         return provider_instance(**runtime_overrides)
    #     else:
    #         return provider_instance()

    def register_service(
            self,
            provider_method: type,
            concrete_type: type,
            interface_type: Optional[Type] = None,  # type: ignore
            *args,
            **kwargs) -> None:
        '''
        Summary
        -------
        Registers a service in the dependency_injector container with its dependencies. If dependencies of the service
        are detected to be registered in the container, they will be linked to the service automatically. Dependencies
        are detected via the type hints of the service's constructor's parameters.

        Parameters
        ----------
        `provider_method` The lifetime of the service, defined using the providers module from dependency_injector.\n
        `concrete_type` The concrete implementation of the service being registered. Can be registered on its own.\n
        `interface_type` The optional interface that the concrete type implements.\n
        `*args` Any required dependencies for this service to be constructed that are not registered in the
        dependency_injector container.

        Exceptions
        ----------
        Raises `DuplicateServiceError` if the dependency_injector container already contains a service of the same type.\n
        Raises `ValueError` if unable to generate a service name for the service.

        '''
        _DependencyName, _GenerationSuccess = self._try_generate_service_name(interface_type or concrete_type)

        if not _GenerationSuccess:
            raise ValueError(f"Failed to generate service name for {interface_type or concrete_type}.")

        if hasattr(self, _DependencyName):
            raise DuplicateServiceError(f"An already registered service is conflicting with {interface_type or concrete_type}.")

        _ConstructorDependencies = [_Param for _Param in inspect.signature(concrete_type.__init__).parameters.values()  # type: ignore
                                    if _Param.annotation != inspect.Parameter.empty
                                    and self._has_service(_Param.annotation)]

        if not _ConstructorDependencies:
            setattr(self, _DependencyName, provider_method(concrete_type, *args, **kwargs))
        else:
            _SubDependencies = []
            for _Dependency in _ConstructorDependencies:
                _SubDependencyName, _ = self._try_generate_service_name(_Dependency.annotation)
                _SubDependencies.append(getattr(self, _SubDependencyName))

            setattr(self, _DependencyName, provider_method(concrete_type, *_SubDependencies, *args, **kwargs))

    # TODO: Get inspiration from this AI generated version
    # def register_service2(
    #     self,
    #     provider_method: type,
    #     concrete_type: Type,
    #     interface_type: Optional[Type] = None,
    #     **runtime_kwargs
    # ) -> None:
    #     """
    #     Register a service in the container.

    #     Parameters
    #     ----------
    #     provider_method : providers.Factory, Singleton, etc.
    #     concrete_type : The concrete implementation class
    #     interface_type : Optional interface type for lookup
    #     runtime_kwargs : Any constructor arguments not registered in container
    #     """

    #     service_type = interface_type or concrete_type

    #     if service_type in self._services:
    #         raise DuplicateServiceError(f"Service already registered: {service_type.__name__}")

    #     constructor_params = inspect.signature(concrete_type.__init__).parameters
    #     auto_wired_kwargs = {}
    #     for param_name, param in constructor_params.items():
    #         if param_name == "self":
    #             continue
    #         annotation = param.annotation
    #         if annotation in self._services:
    #             auto_wired_kwargs[param_name] = self._services[annotation]()

    #     # Merge runtime overrides
    #     auto_wired_kwargs.update(runtime_kwargs)

    #     # Create provider
    #     provider_instance = provider_method(concrete_type, **auto_wired_kwargs)
    #     self._services[service_type] = provider_instance
    #     setattr(self._container, service_type.__name__, provider_instance)

    def _try_generate_service_name(self, service: type) -> Tuple[str, bool]:
        '''
        Summary
        -------
        Generates a service name from a given service type by extracting the fully qualified
        name of the service, then replacing dots with underscores.

        Parameters
        ----------
        `service` The service to generate a name for and true on success, otherwise empty string and false.

        Returns
        -------
        The generated name of the service.

        '''
        _TypeMatch = re.search(r"(?<=')[^']+(?=')", str(service))

        if not _TypeMatch:
            return "", False

        return _TypeMatch.group().replace('.', '_'), True

    def _has_service(self, service: type) -> bool:
        '''
        Summary
        -------
        Checks if a service exists in the dependency_injector container.

        Parameters
        ----------
        `service` The service that is being checked for existence in the container.

        Returns
        -------
        True if the service could be found, false otherwise.

        '''
        _ServiceName, _GenerationSuccess = self._try_generate_service_name(service)

        if _GenerationSuccess:
            return hasattr(self._container, _ServiceName)

        return False
