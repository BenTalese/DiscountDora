from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AppSetting(BaseEntity):
    """Install-wide settings, edited by admins. A single row — see
    features/app_settings for the get-or-create accessor.

    The assistant (Dora's AI mode) is opt-in and bring-your-own-LLM: an admin
    enables it and points it at an LLM endpoint they run themselves (e.g. a
    local Ollama). Nothing is enabled or downloaded by default.

    Scanning + QR labels (real-world barcode → product navigation, plus Dora's
    own item/shelf QR labels) are one opt-in surface gated by a single
    install-wide flag, off by default. Scanning is navigation-only — it never
    does live deal lookup.
    """
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_model: str = ""
    scanning_enabled: bool = False

    class Fields(BaseEntity.Fields):
        LLM_ENABLED = "llm_enabled"
        LLM_BASE_URL = "llm_base_url"
        LLM_MODEL = "llm_model"
        SCANNING_ENABLED = "scanning_enabled"
