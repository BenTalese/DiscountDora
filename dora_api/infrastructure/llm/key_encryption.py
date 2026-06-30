"""API-key encryption for per-user LLM provider keys.

FU-153 / DORA_ASSISTANT_ARCHITECTURE_PROPOSAL §7.4 — paid-provider API
keys (OpenAI, Anthropic, Gemini) are stored as Fernet ciphertext in
``User.llm_api_key_encrypted``. The plaintext never leaves the handler
that writes it; reads through the public API return a derived
``has_llm_api_key: bool`` instead.

The Fernet key comes from the environment variable
``DORA_LLM_KEY_ENCRYPTION_KEY``. Operators set it once at boot
(env file, systemd EnvironmentFile, k8s secret, whatever fits the
deployment) — same shape as every other secret the app needs (R-005
distribution posture: env-driven config). If the variable is unset,
:func:`encrypt` and :func:`decrypt` raise :class:`EncryptionUnavailable`
so callers can surface a friendly error ("API-key encryption isn't
configured for this install — set DORA_LLM_KEY_ENCRYPTION_KEY") instead
of crashing. Ollama doesn't need a key, so an install that only uses
Ollama can leave the env var unset; the variable is only required to
*save* a paid-provider key.

Why an env var, not a generated file:

- Matches every other secret the app needs (no special case).
- Postgres-friendly: the API server can be stateless (FU-045) and
  every replica reads the same key from its env.
- Operators get an explicit "I made a choice" signal — auto-generating
  a key file on first boot is convenient but hides the security model
  from the operator who'll eventually rotate the key.

Key generation (for ops docs):

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

The returned string is a 32-byte url-safe-base64 value; that's what
goes into the env var verbatim.
"""
import logging
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


_ENV_VAR = "DORA_LLM_KEY_ENCRYPTION_KEY"
_Logger = logging.getLogger(__name__)


class EncryptionUnavailable(Exception):
    """Raised when the encryption key isn't configured for this install.

    Callers should translate this to a user-friendly 422 ("API-key
    encryption isn't configured for this install — see operator docs")
    rather than a 500.
    """


class EncryptionFailed(Exception):
    """Raised when ciphertext can't be decoded (key rotated, blob
    corrupted). Treated by callers as "the saved key is no longer
    usable — ask the user to re-enter it"."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet | None:
    raw = os.environ.get(_ENV_VAR, "").strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode("ascii"))
    except (ValueError, TypeError) as exc:
        # Bad key format (must be 32-byte url-safe-base64). Log the
        # operator-facing detail; treat as "no key configured" so
        # callers fail-fast rather than papering over a misconfig.
        _Logger.error(
            "%s is set but invalid (%s). Generate a fresh key with "
            "`python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'`.",
            _ENV_VAR, exc,
        )
        return None


def encryption_available() -> bool:
    """Returns True iff the encryption key is configured AND parses.

    The Settings page reads this via the master-flag endpoint so the
    Save button on paid-provider fields can show a clear "encryption
    isn't configured — ask your admin to set DORA_LLM_KEY_ENCRYPTION_KEY"
    state, instead of failing only at save time.
    """
    return _fernet() is not None


def encrypt(plaintext: str) -> bytes:
    """Encrypt a UTF-8 plaintext API key. Raises EncryptionUnavailable
    when the env key is unset/invalid."""
    f = _fernet()
    if f is None:
        raise EncryptionUnavailable(
            f"{_ENV_VAR} isn't configured — paid-provider API keys can't be saved."
        )
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    """Decrypt a previously-encrypted blob. Raises EncryptionUnavailable
    when the env key is unset/invalid; raises EncryptionFailed when the
    blob can't be decoded with the current key (rotated / corrupted)."""
    f = _fernet()
    if f is None:
        raise EncryptionUnavailable(
            f"{_ENV_VAR} isn't configured — saved API keys can't be decrypted."
        )
    try:
        return f.decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise EncryptionFailed(
            "Saved API key couldn't be decrypted — the encryption key "
            "may have been rotated. Re-enter the key in Settings."
        ) from exc
