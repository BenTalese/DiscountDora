from abc import ABC, abstractmethod
from typing import List

from framework.merchant_api.domain.entities.merchant import Merchant


class IConfigurationManager(ABC):

    @abstractmethod
    def get_all_merchants(self) -> List[Merchant]:
        pass

    @abstractmethod
    def get_api_host(self) -> str:
        pass

    @abstractmethod
    def get_api_port(self) -> int:
        pass

    @abstractmethod
    def get_iga_store_id(self) -> int:
        pass

    @abstractmethod
    def get_log_level(self) -> int:
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

    @abstractmethod
    def toggle_merchant_enabled_state(self, merchant_name: str) -> None:
        pass
