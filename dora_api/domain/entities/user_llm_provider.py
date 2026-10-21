from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class UserLlmProvider(BaseEntity):
    """One saved LLM-provider configuration for a user.

    The Assistant settings page lets a user fill in details for several
    providers (Ollama, OpenAI, Anthropic, Gemini) and flip between them,
    so each provider's config is its own row keyed on (user_id, provider)
    — this table is the single source of truth for provider details. The
    ``User`` row only carries which provider is *active* (``llm_provider``)
    plus the AI-mode opt-in (``llm_enabled``); the details live here.

    ``verified`` is set True only when a live probe (``/api/assistant/probe``)
    reached the provider with these exact settings; editing any field resets
    it to False. The Mode picker only offers providers whose row is verified,
    which is why entering arbitrary text no longer silently "works" — a
    provider isn't selectable until it has actually answered.

    ``api_key_encrypted`` is Fernet ciphertext (see
    ``infrastructure/security/secret_encryption.py``); the plaintext never
    leaves the handler that writes it and reads surface a derived
    ``has_api_key: bool``. Only the paid providers use it — Ollama leaves it
    NULL and relies on ``base_url``.
    """
    user_id: UUID
    provider: str
    base_url: str | None = None
    model: str | None = None
    api_key_encrypted: bytes | None = None
    verified: bool = False
    verified_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        PROVIDER = "provider"
        BASE_URL = "base_url"
        MODEL = "model"
        API_KEY_ENCRYPTED = "api_key_encrypted"
        VERIFIED = "verified"
        VERIFIED_AT = "verified_at"
