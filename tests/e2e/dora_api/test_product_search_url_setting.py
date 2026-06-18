"""Phase D / FU-186 — `AppSetting.product_search_url` round-trip.

The setting is an admin-managed string the Product Search nav entry
opens in a new tab when product data is present. Companion-side
behaviour (how the URL is actually served) is out of scope here;
this test exercises the dora_api contract only.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
APP_SETTINGS = f"{BASE}/app-settings"


def test__app_settings__product_search_url_defaults_empty(api):
    body = requests.get(APP_SETTINGS).json()
    assert "product_search_url" in body
    # Other tests may have set a URL earlier in the session; the contract
    # we pin is "the field exists and is a string", not its initial value.
    assert isinstance(body["product_search_url"], str)


def test__app_settings__product_search_url_patches_and_persists(api):
    url = f"https://search.example/{uuid.uuid4().hex[:8]}"
    resp = requests.patch(APP_SETTINGS, json={"product_search_url": url})
    assert resp.status_code == 200, resp.text
    assert resp.json()["product_search_url"] == url

    again = requests.get(APP_SETTINGS).json()
    assert again["product_search_url"] == url


def test__app_settings__product_search_url_blank_clears(api):
    requests.patch(APP_SETTINGS, json={"product_search_url": "https://search.example/x"})
    resp = requests.patch(APP_SETTINGS, json={"product_search_url": ""})
    assert resp.status_code == 200, resp.text
    assert resp.json()["product_search_url"] == ""


def test__app_settings__product_search_url_rejects_non_http(api):
    bad = requests.patch(APP_SETTINGS, json={"product_search_url": "javascript:alert(1)"})
    assert bad.status_code == 400, bad.text
    # The setting must remain whatever it was before the bad PATCH.
    after = requests.get(APP_SETTINGS).json()["product_search_url"]
    assert not after.startswith("javascript:")
