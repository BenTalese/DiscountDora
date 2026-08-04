"""Pluggable per-user LLM clients.

The assistant talks to whatever ``LlmClient`` it's handed. Today that's
one of four backends (Ollama, OpenAI, Anthropic, Gemini), chosen per
user from their saved provider preference. Construction lives in
``infrastructure.llm.factory`` so feature code never imports a concrete
provider; the assistant handler just calls
``build_assistant_client(user)``.

R-022 — the interface (``LlmClient``) is deliberately narrow:
availability probe + a tool-aware chat turn. Each provider's ``chat()``
normalises its native response to the OpenAI-style
``{role, content, tool_calls?}`` shape ``ask_assistant._parse_tool_call``
already consumes, so the routing/handler code is provider-agnostic.
"""
from dora_api.infrastructure.llm.anthropic_client import AnthropicClient
from dora_api.infrastructure.llm.factory import (
    build_assistant_client,
    build_assistant_client_from_provider,
)
from dora_api.infrastructure.llm.gemini_client import GeminiClient
from dora_api.infrastructure.security.secret_encryption import (
    EncryptionFailed,
    EncryptionUnavailable,
    encrypt as encrypt_api_key,
    decrypt as decrypt_api_key,
    encryption_available,
)
from dora_api.infrastructure.llm.llm_client import LlmClient, LlmUnavailable
from dora_api.infrastructure.llm.ollama_client import OllamaClient
from dora_api.infrastructure.llm.openai_client import OpenAiClient

__all__ = [
    "AnthropicClient",
    "EncryptionFailed",
    "EncryptionUnavailable",
    "GeminiClient",
    "LlmClient",
    "LlmUnavailable",
    "OllamaClient",
    "OpenAiClient",
    "build_assistant_client",
    "build_assistant_client_from_provider",
    "decrypt_api_key",
    "encrypt_api_key",
    "encryption_available",
]
