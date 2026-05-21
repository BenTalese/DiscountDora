from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AppSetting(BaseEntity):
    """Install-wide settings, edited by admins. A single row — see
    features/app_settings for the get-or-create accessor.

    The assistant (Dora's AI mode) is opt-in and bring-your-own-LLM: an admin
    enables it and points it at an LLM endpoint they run themselves (e.g. a
    local Ollama). Nothing is enabled or downloaded by default.
    """
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_model: str = ""

    class Fields(BaseEntity.Fields):
        LLM_ENABLED = "llm_enabled"
        LLM_BASE_URL = "llm_base_url"
        LLM_MODEL = "llm_model"
