"""OpenAI chat-completions client.

FU-153 §7.4 — paid-provider sibling to OllamaClient. OpenAI's
``/v1/chat/completions`` already returns the lingua franca tool-call
shape ``message.tool_calls = [{id, type: 'function', function: {name,
arguments}}]`` that ``ask_assistant._parse_tool_call`` consumes, so the
"adapter" here is mostly transport plumbing — the response is returned
as-is.

OpenAI also tolerates a self-hosted-relay ``base_url`` (e.g. an
LiteLLM proxy or Azure-OpenAI front), so the client accepts a base URL
override; the default is ``https://api.openai.com/v1``.
"""
import json
import logging
from time import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from dora_api.infrastructure.llm.llm_client import LlmClient, LlmUnavailable


_Logger = logging.getLogger(__name__)
_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAiClient(LlmClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
        enabled: bool = True,
        base_url: str | None = None,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._enabled = enabled
        self._base_url = (base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._available_cache: bool | None = None
        self._available_checked_at: float = 0.0

    def is_available(self) -> bool:
        if not self._enabled or not self._api_key:
            return False
        now = time()
        if self._available_cache is not None and (now - self._available_checked_at) < 15:
            return self._available_cache
        # OpenAI's /models is the cheapest auth-gated read; a 401 still
        # tells us the host is up but the key's wrong (treated as "not
        # available" so the fallback fires).
        available = False
        try:
            req = Request(f"{self._base_url}/models", method="GET", headers=self._headers())
            with urlopen(req, timeout=3) as resp:
                available = resp.status == 200
        except (URLError, OSError, ValueError) as exc:
            _Logger.debug("OpenAI not reachable: %s", exc)
        self._available_cache = available
        self._available_checked_at = now
        return available

    def list_models(self) -> list[str]:
        try:
            req = Request(f"{self._base_url}/models", method="GET", headers=self._headers())
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, OSError, ValueError) as exc:
            raise LlmUnavailable(f"OpenAI request failed: {exc}") from exc
        items = data.get("data") or []
        # Tool-capable chat models only. The exhaustive list is undocumented;
        # filtering by family prefix matches the SDK's recommended set.
        prefixes = ("gpt-4", "gpt-3.5", "o1", "o3")
        names = sorted({
            m["id"] for m in items
            if isinstance(m, dict) and isinstance(m.get("id"), str)
            and m["id"].startswith(prefixes)
        })
        return names

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if not self._enabled or not self._api_key:
            raise LlmUnavailable("OpenAI is disabled or missing API key.")

        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            body = json.dumps(payload).encode("utf-8")
            req = Request(
                f"{self._base_url}/chat/completions",
                data=body,
                method="POST",
                headers={**self._headers(), "Content-Type": "application/json"},
            )
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, OSError, ValueError) as exc:
            self._available_cache = False
            raise LlmUnavailable(f"OpenAI request failed: {exc}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise LlmUnavailable("OpenAI returned no choices.")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise LlmUnavailable("OpenAI returned no message.")
        # The OpenAI shape is the lingua franca tools.py / ask_assistant
        # already consume — return verbatim.
        return message

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}
