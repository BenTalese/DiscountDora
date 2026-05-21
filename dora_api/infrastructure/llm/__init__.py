"""Pluggable small-language-model client.

The assistant talks to whatever `LlmClient` it's handed. Today that's an Ollama
HTTP adapter pointed at an endpoint an admin configures (bring-your-own-LLM);
the interface is deliberately narrow (availability check + a tool-aware chat
turn) so an in-process or cloud adapter can slot in later without touching
feature code. Construction now happens where the config is read (see
features/assistant), so this package no longer depends on global config.
"""
from dora_api.infrastructure.llm.llm_client import LlmClient, LlmUnavailable
from dora_api.infrastructure.llm.ollama_client import OllamaClient

__all__ = ["LlmClient", "LlmUnavailable", "OllamaClient"]
