from abc import ABC, abstractmethod


class IConfigurationProvider(ABC):

    @abstractmethod
    def get_api_host(self) -> str:
        pass

    @abstractmethod
    def get_api_port(self) -> int:
        pass

    @abstractmethod
    def get_web_app_host(self) -> str:
        pass

    @abstractmethod
    def get_web_app_port(self) -> int:
        pass

    @abstractmethod
    def is_debug_mode_enabled(self) -> bool:
        pass

    @abstractmethod
    def is_reloader_enabled(self) -> bool:
        pass
