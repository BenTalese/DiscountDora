import threading
from time import sleep

import pytest
import requests

from dora_api.app import app
from dora_api.startup import startup


@pytest.fixture(scope="session")
def api():
    startup(is_test_env=True)

    thread = threading.Thread(
        target=lambda: app.run(host="localhost", port=5170, use_reloader=False, debug=False),
        daemon=True,
    )
    thread.start()

    sleep(2)

    # The API now gates non-public endpoints behind an authenticated session.
    # The tests issue bare `requests.get(...)` calls, which don't persist the
    # session cookie. Log in once and rebind the module-level request helpers to
    # an authenticated Session so every bare call carries the auth cookie.
    _Session = requests.Session()
    _LoginResponse = _Session.post(
        "http://localhost:5170/api/auth/login",
        json={"username": "dora", "password": "dora"},
    )
    assert _LoginResponse.status_code == 200, (
        f"Test login failed ({_LoginResponse.status_code}): {_LoginResponse.text}"
    )

    _Originals = {
        name: getattr(requests, name)
        for name in ("get", "post", "put", "patch", "delete")
    }
    for name in _Originals:
        setattr(requests, name, getattr(_Session, name))

    client = ApiClient("http://localhost:5170")
    client._session = _Session

    try:
        yield client
    finally:
        for name, fn in _Originals.items():
            setattr(requests, name, fn)


class ApiClient:
    def __init__(self, base_url: str):
        self._base = base_url
        self._session = requests.Session()

    def get(self, path: str, **kwargs):
        return self._session.get(f"{self._base}{path}", **kwargs)

    def post(self, path: str, **kwargs):
        return self._session.post(f"{self._base}{path}", **kwargs)

    def put(self, path: str, **kwargs):
        return self._session.put(f"{self._base}{path}", **kwargs)

    def delete(self, path: str, **kwargs):
        return self._session.delete(f"{self._base}{path}", **kwargs)
