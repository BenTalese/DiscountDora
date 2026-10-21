"""Small helpers for asserting the FU-099 ``ErrorEntry`` wire shape.

Tests previously asserted ``errors: { field: ["raw Pydantic string"] }``
directly. After FU-099 each entry is ``{msg, code, raw}`` — friendly
translation + Pydantic code + raw message. The helpers below build the
expected entry so test bodies stay readable and a future change to the
friendly-copy table doesn't require touching dozens of tests.
"""
from __future__ import annotations

from dora_api.infrastructure.error_translation import translate_pydantic_error


def validation_err(code: str, raw: str) -> dict:
    """Build the expected ``ErrorEntry`` dict for a Pydantic validation
    error. The friendly ``msg`` is looked up from the central
    translation table so the assertion stays in lock-step with the
    server-side mapping.
    """
    return {"msg": translate_pydantic_error(code), "code": code, "raw": raw}


def domain_err(msg: str) -> dict:
    """Build the expected ``ErrorEntry`` dict for a domain / business-rule
    error (no Pydantic code — these messages are authored by us, so they
    *are* the friendly copy and ``raw`` is ``None``)."""
    return {"msg": msg, "code": "domain", "raw": None}
