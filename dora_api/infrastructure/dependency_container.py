import inspect
import re
from typing import Any, Dict, Optional, Type, get_args, get_origin

from dependency_injector import containers, providers

from dora_api.domain.exceptions import DependencyConstructionError, DuplicateServiceError
from dora_api.domain.generics import TService


class DependencyContainer:
    """
    A thin, correct wrapper around dependency_injector's DynamicContainer.

    Design principles:
    - dependency_injector's container is the sole source of truth for providers.
    - Providers are wired to other providers, never to resolved instances.
    - This class manages only the type → provider_name mapping.
    - Generic aliases (e.g. IRepository[Merchant]) are fully supported and
      produce unique, collision-free provider names.
    """

    def __init__(self) -> None:
        self._container = containers.DynamicContainer()
        # Maps registered type (interface or concrete, including generic aliases)
        # to the attribute name used on the container. Contains no resolved objects.
        self._type_to_name: Dict[Any, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_service(
        self,
        provider_method: Type[providers.Provider],
        concrete_type: Type,
        interface_type: Optional[Any] = None,
        **explicit_kwargs,
    ) -> None:
        """
        Register a service with automatic constructor wiring.

        Parameters
        ----------
        provider_method:
            A dependency_injector provider class — providers.Singleton,
            providers.Factory, etc. Defines the service lifetime.
        concrete_type:
            The concrete class to instantiate. May be a generic alias
            (e.g. SqlAlchemyRepository[Merchant]).
        interface_type:
            Optional. If supplied, the service is resolved under this type.
            Supports generic aliases (e.g. IRepository[Merchant]).
        **explicit_kwargs:
            Constructor arguments that are not registered services and cannot
            be auto-wired — config values, primitives, model classes, etc.
            These are passed directly to the provider at construction time.

        Raises
        ------
        DuplicateServiceError
            If a service is already registered under the same type.
        """
        registration_type = interface_type if interface_type is not None else concrete_type

        if registration_type in self._type_to_name:
            raise DuplicateServiceError(
                f"Service already registered: {self._format_type(registration_type)}"
            )

        provider_name = self._build_provider_name(registration_type)

        # Resolve the raw class from a generic alias for instantiation.
        # providers.Factory(SqlAlchemyRepository[Merchant]) won't work —
        # dependency_injector needs the unparameterised class. The generic
        # type argument is captured separately via explicit_kwargs if needed.
        instantiation_class = get_origin(concrete_type) or concrete_type

        auto_wired_providers = self._resolve_constructor_providers(concrete_type)

        # explicit_kwargs override auto-wired providers, giving the caller
        # intentional control without fighting the framework.
        wired_kwargs = {**auto_wired_providers, **explicit_kwargs}

        provider_instance = provider_method(instantiation_class, **wired_kwargs)  # type: ignore
        setattr(self._container, provider_name, provider_instance)
        self._type_to_name[registration_type] = provider_name

    def inject(self, service_type: Any, **runtime_overrides) -> TService:  # type: ignore
        """
        Resolve a registered service from the container.

        Parameters
        ----------
        service_type:
            The type to resolve — must match what was passed as interface_type
            (or concrete_type) at registration. Supports generic aliases.
        **runtime_overrides:
            Per-call constructor overrides forwarded to the provider.
            Useful with Factory providers. Singleton providers ignore overrides
            after the first resolution — this is dependency_injector's behaviour.

        Raises
        ------
        LookupError
            If no service is registered under the given type.
        DependencyConstructionError
            If the provider fails to construct the service.
        """
        if service_type not in self._type_to_name:
            raise LookupError(
                f"No service registered for '{self._format_type(service_type)}'. "
                "Ensure it has been registered before calling inject()."
            )

        provider_name = self._type_to_name[service_type]
        provider_instance: providers.Provider = getattr(self._container, provider_name)

        try:
            return provider_instance(**runtime_overrides)
        except TypeError as ex:
            raise DependencyConstructionError(
                f"Failed to construct '{self._format_type(service_type)}'. "
                "Verify all non-injectable constructor parameters are supplied "
                "via explicit_kwargs at registration or runtime_overrides at resolution. "
                f"Inner exception: {ex}"
            ) from ex

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_constructor_providers(
        self, concrete_type: Any
    ) -> Dict[str, providers.Provider]:
        """
        Inspect the __init__ of concrete_type and return a dict mapping
        parameter names to their registered provider objects for any parameter
        whose annotation is registered in this container.

        Handles both plain types and generic aliases in annotations.
        Returns provider objects — never resolved instances. This is the
        invariant that keeps dependency_injector's lifetime semantics intact.
        """
        auto_wired: Dict[str, providers.Provider] = {}

        # Unwrap generic alias to get the inspectable class
        inspectable = get_origin(concrete_type) or concrete_type

        try:
            sig = inspect.signature(inspectable.__init__)
        except (ValueError, TypeError):
            return auto_wired

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                continue
            if annotation in self._type_to_name:
                provider_name = self._type_to_name[annotation]
                # Fetch the Provider object itself — do NOT call it.
                # dependency_injector recognises provider arguments and
                # resolves them at construction time, preserving lifetimes.
                auto_wired[param_name] = getattr(self._container, provider_name)

        return auto_wired

    def _build_provider_name(self, service_type: Any) -> str:
        """
        Derive a unique, stable attribute name for a type, including full
        support for generic aliases such as IRepository[Merchant].

        For plain types:
            dora_api.domain.foo.IFooService
            → dora_api_domain_foo_IFooService

        For generic aliases:
            dora_api.domain.IRepository[dora_api.domain.Merchant]
            → dora_api_domain_IRepository__dora_api_domain_Merchant_

        The recursive approach means arbitrarily nested generics
        (e.g. Dict[str, List[Merchant]]) also produce unique names,
        though such cases are unlikely in a DI context.
        """
        origin = get_origin(service_type)

        if origin is not None:
            # Generic alias — combine origin name with stringified args
            origin_name = self._build_provider_name(origin)
            args = get_args(service_type)
            args_name = "_".join(self._build_provider_name(a) for a in args)
            return f"{origin_name}__{args_name}_"

        # Plain type — use fully qualified name
        qualified = getattr(service_type, "__qualname__", None) or getattr(service_type, "__name__", "unknown")
        module = getattr(service_type, "__module__", "") or ""
        full = f"{module}.{qualified}" if module else qualified
        return re.sub(r"[^a-zA-Z0-9_]", "_", full)

    @staticmethod
    def _format_type(service_type: Any) -> str:
        """Human-readable type name for error messages, including generic aliases."""
        origin = get_origin(service_type)
        if origin is not None:
            args = get_args(service_type)
            origin_name = getattr(origin, "__name__", str(origin))
            args_str = ", ".join(getattr(a, "__name__", str(a)) for a in args)
            return f"{origin_name}[{args_str}]"
        return getattr(service_type, "__name__", str(service_type))

    def _is_registered(self, service_type: Any) -> bool:
        return service_type in self._type_to_name
