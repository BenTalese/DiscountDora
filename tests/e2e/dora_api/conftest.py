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

    sleep(3)

    yield ApiClient("http://localhost:5170")


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
