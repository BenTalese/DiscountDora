"""Unit coverage for `warn_if_insecure_cookies_in_production`.

Post-FU-387 (2026-07-09) the prod default flipped: `SESSION_COOKIE_SECURE`
is now `True` in production unless the operator explicitly opts out via
`DORA_SECURE_COOKIES=false`. The warning fires only on that explicit
opt-out — meant to make the choice audible at boot ("you're serving
prod without Secure cookies — sure?") for the LAN-behind-VPN /
no-cert home-lab case. Unset + `true` are both silent (the safe
default is now the default).
"""
import pytest

from dora_api.infrastructure import profile


@pytest.fixture
def _clean_env(monkeypatch):
    """Wipe every env var the function reads so each test starts from
    a known-empty baseline; individual tests set what they need."""
    for name in (
        "DORA_ENV",
        "DORA_SECURE_COOKIES",
        "DORA_SKIP_PROD_VALIDATION",
    ):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test__warn__silent_when_not_production(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "development")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__silent_when_production_and_var_unset(_clean_env, capsys):
    """Unset now inherits the safe default (SESSION_COOKIE_SECURE=True) —
    no warning, no nag."""
    _clean_env.setenv("DORA_ENV", "production")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__silent_when_explicitly_true(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "true")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__fires_when_explicitly_false(_clean_env, capsys):
    """Explicit `false` is a deliberate operator choice — nudge them
    once at boot so the LAN-behind-VPN / no-cert home-lab case is
    audible, not silent drift into insecure cookies."""
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "false")
    profile.warn_if_insecure_cookies_in_production()
    err = capsys.readouterr().err
    assert "DORA_SECURE_COOKIES=false" in err
    assert "Secure" in err


def test__warn__silent_when_skip_validation_set(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "false")
    _clean_env.setenv("DORA_SKIP_PROD_VALIDATION", "true")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__silent_when_var_is_whitespace_only(_clean_env, capsys):
    """A value that strips to empty falls through to the safe default
    (post-FU-387) — no warning."""
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "   ")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""
