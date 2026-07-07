"""Unit coverage for `warn_if_insecure_cookies_in_production`.

The warning is a first-time-setup catch — the point is that anyone
flipping the app to `DORA_ENV=production` without explicitly setting
`DORA_SECURE_COOKIES` sees an unmissable stderr banner. A missing var
is *not* the same as an explicit `false` — the operator has made a
deliberate choice in the latter case (LAN-only install, VPN-fronted,
etc.) and shouldn't be nagged.
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


def test__warn__fires_when_production_and_var_unset(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "production")
    profile.warn_if_insecure_cookies_in_production()
    err = capsys.readouterr().err
    assert "DORA_SECURE_COOKIES is unset" in err
    assert "Secure" in err


def test__warn__silent_when_explicitly_true(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "true")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__silent_when_explicitly_false(_clean_env, capsys):
    """Explicit `false` is a deliberate operator choice — don't nag."""
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "false")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__silent_when_skip_validation_set(_clean_env, capsys):
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SKIP_PROD_VALIDATION", "true")
    profile.warn_if_insecure_cookies_in_production()
    assert capsys.readouterr().err == ""


def test__warn__fires_when_var_is_whitespace_only(_clean_env, capsys):
    """A value that strips to empty is treated as unset — an admin who
    left the value blank in .env still gets caught."""
    _clean_env.setenv("DORA_ENV", "production")
    _clean_env.setenv("DORA_SECURE_COOKIES", "   ")
    profile.warn_if_insecure_cookies_in_production()
    assert "DORA_SECURE_COOKIES is unset" in capsys.readouterr().err
