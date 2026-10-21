"""D-12 / B7 — `buy_verdict_enabled` is a per-user preference, not household state.

It used to be an install-wide `AppSetting`, so one person hiding the "should I
buy this?" overlay hid it for everybody (the owner confirmed that scoping was a
mistake). The rule it established: a setting that mutates shared state is
household-scoped; a setting that only changes what you see is per-user.

These pin the scope itself, which is the part a future refactor could quietly
undo — the *rendering* of the toggle is a browser check.
"""
import requests

BASE = "http://localhost:5170/api"
ME = f"{BASE}/auth/me"
APP_SETTINGS = f"{BASE}/app-settings"


def test__buy_verdict_enabled__is_on_me_and_defaults_true(api):
    me = requests.get(ME)
    assert me.status_code == 200, me.text
    assert me.json()["buy_verdict_enabled"] is True


def test__buy_verdict_enabled__round_trips_through_patch_me(api):
    try:
        off = requests.patch(ME, json={"buy_verdict_enabled": False})
        assert off.status_code == 200, off.text
        assert requests.get(ME).json()["buy_verdict_enabled"] is False

        on = requests.patch(ME, json={"buy_verdict_enabled": True})
        assert on.status_code == 200, on.text
        assert requests.get(ME).json()["buy_verdict_enabled"] is True
    finally:
        requests.patch(ME, json={"buy_verdict_enabled": True})


def test__buy_verdict_enabled__is_gone_from_app_settings(api):
    """Both halves of the move. The read shape must not carry it, and a client
    still sending it household-wide must be told (`extra="forbid"`) rather than
    have the write silently disappear."""
    settings = requests.get(APP_SETTINGS)
    assert settings.status_code == 200, settings.text
    assert "buy_verdict_enabled" not in settings.json()

    rejected = requests.patch(APP_SETTINGS, json={"buy_verdict_enabled": False})
    assert rejected.status_code in (400, 422), rejected.text


def test__health_no_longer_advertises_a_buy_verdict_feature_flag(api):
    """`features.buy_verdict` was the install-wide flag's delivery channel. A
    stale flag here would have the SPA answering a per-user question with a
    household answer."""
    info = requests.get(f"{BASE}/health")
    assert info.status_code == 200, info.text
    assert "buy_verdict" not in info.json().get("features", {})
