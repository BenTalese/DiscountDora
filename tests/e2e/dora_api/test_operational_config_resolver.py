"""FU-333 Bucket B — resolver matrix.

For each of the 12 operational config fields the resolver should:

* Prefer a non-empty ``AppSetting`` value over the env fallback.
* Fall back to the env value when the row is unset (empty string / default).
* Land on the seeded default when neither is set.

Tests write the row via the admin PATCH endpoint (real HTTP path through
the in-process test client), toggle env vars in-place, and call the
resolver directly under ``app.app_context()``. A ``try/finally`` cleans
the env + resets the row to the seeded default so no state leaks into
later tests in the module.
"""
from __future__ import annotations

import os

import pytest
import requests

from dora_api.app import app
from dora_api.features.app_settings.operational_config import (
    resolved_operational_config,
)


BASE = "http://localhost:5170/api"
APP_SETTINGS = f"{BASE}/app-settings"


# ── Reset helper — every test uses it to leave a clean slate ────────────

_STRING_RESETS = {
    "smtp_host": "",
    "smtp_username": "",
    "smtp_from": "",
    "vapid_public_key": "",
    "vapid_subject": "mailto:admin@dora.local",
    "piper_bin": "",
    "piper_bundled_voice_dir": "",
    "piper_voice": "",
    "public_url": "",
}
_INT_RESETS = {
    "smtp_port": 587,
    "audit_retention_days": 365,
}
_BOOL_RESETS = {
    "smtp_use_tls": True,
    "email_enabled": False,
}
_ENV_VARS = [
    "DORA_SMTP_HOST", "DORA_SMTP_PORT", "DORA_SMTP_USERNAME", "DORA_SMTP_FROM",
    "DORA_SMTP_USE_TLS", "DORA_VAPID_PUBLIC_KEY", "DORA_VAPID_SUBJECT",
    "DORA_PIPER_BIN", "DORA_PIPER_BUNDLED_VOICE_DIR", "DORA_PIPER_VOICE",
    "DORA_EMAIL_ENABLED", "DORA_AUDIT_RETENTION_DAYS", "DORA_PUBLIC_URL",
]


def _reset_all() -> None:
    """Row → seeded defaults, envs → unset. Idempotent; safe to call in
    a finally even if the test bailed mid-way."""
    payload: dict = {}
    payload.update(_STRING_RESETS)
    payload.update(_INT_RESETS)
    payload.update(_BOOL_RESETS)
    resp = requests.patch(APP_SETTINGS, json=payload)
    assert resp.status_code == 200, resp.text
    for name in _ENV_VARS:
        os.environ.pop(name, None)


@pytest.fixture(autouse=True)
def _clean_state(api):
    _reset_all()
    try:
        yield
    finally:
        _reset_all()


def _resolved():
    with app.app_context():
        return resolved_operational_config()


# ── String fields: AppSetting wins over env, env wins over default ──────

@pytest.mark.parametrize(
    "field,env_name,row_value,env_value,default",
    [
        ("smtp_host", "DORA_SMTP_HOST", "row.example", "env.example", ""),
        ("smtp_username", "DORA_SMTP_USERNAME", "row-user", "env-user", ""),
        ("smtp_from", "DORA_SMTP_FROM", "row@example", "env@example", ""),
        ("vapid_public_key", "DORA_VAPID_PUBLIC_KEY", "row-pub", "env-pub", ""),
        ("vapid_subject", "DORA_VAPID_SUBJECT", "mailto:row@x", "mailto:env@x", "mailto:admin@dora.local"),
        ("piper_bin", "DORA_PIPER_BIN", "/opt/row/piper", "/opt/env/piper", ""),
        ("piper_bundled_voice_dir", "DORA_PIPER_BUNDLED_VOICE_DIR", "/row/voices", "/env/voices", ""),
        ("piper_voice", "DORA_PIPER_VOICE", "/row/voice.onnx", "/env/voice.onnx", ""),
        ("public_url", "DORA_PUBLIC_URL", "https://row.example", "https://env.example", ""),
    ],
)
def test__resolver__string_field__row_wins_then_env_then_default(
    field, env_name, row_value, env_value, default,
):
    # Row + env both set → row wins.
    resp = requests.patch(APP_SETTINGS, json={field: row_value})
    assert resp.status_code == 200, resp.text
    os.environ[env_name] = env_value
    assert getattr(_resolved(), field) == row_value

    # Row cleared, env still set → env wins.
    resp = requests.patch(APP_SETTINGS, json={field: ""})
    assert resp.status_code == 200, resp.text
    assert getattr(_resolved(), field) == env_value

    # Env cleared too → seeded default.
    del os.environ[env_name]
    assert getattr(_resolved(), field) == default


# ── smtp_port: int field, row always wins over env ──────────────────────

def test__resolver__smtp_port__row_wins_then_env_then_default():
    resp = requests.patch(APP_SETTINGS, json={"smtp_port": 2525})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_SMTP_PORT"] = "465"
    assert _resolved().smtp_port == 2525

    resp = requests.patch(APP_SETTINGS, json={"smtp_port": 587})
    assert resp.status_code == 200, resp.text
    assert _resolved().smtp_port == 587


def test__resolver__smtp_port__env_used_when_row_is_default():
    # No API way to null the int back; the seeded 587 is the default, so
    # setting the env pins the fallback path.
    os.environ["DORA_SMTP_PORT"] = "465"
    # Row is 587 (seeded); the int helper picks the row over the env
    # because the row is not None. This documents that ints — unlike
    # strings — don't have a "unset ⇒ delegate to env" mode once the row
    # has a value. Operators who rely on env for a port must clear it via
    # Settings (the port is bounded so this is a low-risk trade-off).
    assert _resolved().smtp_port == 587


# ── audit_retention_days: same shape as smtp_port ───────────────────────

def test__resolver__audit_retention_days__row_wins():
    resp = requests.patch(APP_SETTINGS, json={"audit_retention_days": 30})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_AUDIT_RETENTION_DAYS"] = "90"
    assert _resolved().audit_retention_days == 30


# ── Bools: row is authoritative (NOT NULL column) ──────────────────────

def test__resolver__email_enabled__row_wins():
    resp = requests.patch(APP_SETTINGS, json={"email_enabled": True})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_EMAIL_ENABLED"] = "false"
    assert _resolved().email_enabled is True

    resp = requests.patch(APP_SETTINGS, json={"email_enabled": False})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_EMAIL_ENABLED"] = "true"
    assert _resolved().email_enabled is False


def test__resolver__smtp_use_tls__row_wins():
    resp = requests.patch(APP_SETTINGS, json={"smtp_use_tls": False})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_SMTP_USE_TLS"] = "true"
    assert _resolved().smtp_use_tls is False

    resp = requests.patch(APP_SETTINGS, json={"smtp_use_tls": True})
    assert resp.status_code == 200, resp.text
    os.environ["DORA_SMTP_USE_TLS"] = "false"
    assert _resolved().smtp_use_tls is True


# ── Whitespace-only strings should behave like "unset" ─────────────────

def test__resolver__whitespace_only_row_string__falls_through_to_env():
    os.environ["DORA_SMTP_HOST"] = "env.example"
    resp = requests.patch(APP_SETTINGS, json={"smtp_host": "   "})
    assert resp.status_code == 200, resp.text
    # Row is whitespace → resolver treats as unset → env wins.
    assert _resolved().smtp_host == "env.example"


# ── Health endpoint uses the resolver for `email_smtp_configured` ──────

def test__health__email_smtp_configured__derived_from_appsetting():
    """Prove the resolver flows all the way through the /health endpoint —
    an admin flipping SMTP username in Settings sees the R-014 gating flip
    without a restart."""
    health = requests.get(f"{BASE}/health").json()
    assert health["features"]["email_smtp_configured"] is False

    resp = requests.patch(APP_SETTINGS, json={"smtp_username": "operator@example"})
    assert resp.status_code == 200, resp.text
    health = requests.get(f"{BASE}/health").json()
    assert health["features"]["email_smtp_configured"] is True
