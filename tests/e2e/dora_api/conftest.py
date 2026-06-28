import io
import os
from pathlib import Path
from urllib.parse import urlsplit

# FU-045: pin the e2e suite to a SQLite temp database. Postgres is the
# standard datastore for dev + prod (Decision 5), but tests want zero
# external dependencies and per-process isolation. `DORA_DB_PATH` is the
# friendly SQLite shortcut — plain filesystem path; the config layer
# builds the URL. Set before importing `dora_api.app` so the env is in
# place when `DoraConfig.get_db_connection_string()` runs at import.
_REPO_ROOT = Path(__file__).resolve().parents[3]
(_REPO_ROOT / "data").mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "DORA_DB_PATH",
    str(_REPO_ROOT / "data" / "dora.test.db"),
)

import pytest
import requests

from dora_api.app import app
from dora_api.startup import startup


@pytest.fixture(scope="session", autouse=True)
def api():
    # FU-166: the e2e suite used to boot a real werkzeug HTTP server in a
    # thread and drive it with `requests` over the loopback socket — ~2.7s
    # per test (real TCP + the Windows `localhost` IPv6-fallback penalty),
    # ~13.5 min for the suite. We now dispatch in-process through Flask's
    # test client. The test bodies are untouched: they still call bare
    # `requests.get/post/...` (authenticated) and `requests.Session()` (a
    # fresh anonymous jar); we rebind both to thin adapters over
    # `app.test_client()`. No socket, no network stack.
    startup(is_test_env=True)

    # Authenticated client backing the module-level `requests.*` helpers.
    # The test client keeps its own cookie jar, so every subsequent call
    # carries the `dora_session` cookie — mirroring the old logged-in
    # `requests.Session`.
    client = app.test_client()
    _LoginResponse = client.post(
        "/api/auth/login",
        json={"username": "dora", "password": "dora"},
    )
    assert _LoginResponse.status_code == 200, (
        f"Test login failed ({_LoginResponse.status_code}): "
        f"{_LoginResponse.get_data(as_text=True)}"
    )

    _Originals = {
        name: getattr(requests, name)
        for name in ("get", "post", "put", "patch", "delete")
    }
    for name in _Originals:
        setattr(requests, name, _adapt(client, name))

    # `requests.Session()` → a brand-new (anonymous) test client. Tests that
    # call `_fresh_session()` want an isolated cookie jar; a fresh test
    # client is exactly that.
    _OriginalSession = requests.Session
    requests.Session = lambda: _TestClientSession(app.test_client())

    api_client = _TestClientSession(client)

    try:
        yield api_client
    finally:
        for name, fn in _Originals.items():
            setattr(requests, name, fn)
        requests.Session = _OriginalSession


def _to_path(url: str) -> str:
    """Strip scheme + host from a full test URL, leaving the path (and query
    string) the test client expects. Bodies still write absolute URLs like
    `http://localhost:5170/api/...`; the test client only wants `/api/...`."""
    parts = urlsplit(url)
    if not parts.scheme and not parts.netloc:
        return url  # already a bare path
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    return path


def _adapt(client, method_name: str):
    """Wrap one test-client verb so it accepts `requests`-style args and
    returns a `requests`-shaped response."""
    client_method = getattr(client, method_name)

    def _call(url: str, **kwargs):
        # `requests` uses `params=` for the query string; the werkzeug test
        # client uses `query_string=`. `json=`/`headers=` pass through as-is.
        if "params" in kwargs:
            kwargs["query_string"] = kwargs.pop("params")
        if "files" in kwargs:
            _translate_multipart(kwargs)
        return _TestClientResponse(client_method(_to_path(url), **kwargs))

    return _call


def _translate_multipart(kwargs: dict) -> None:
    """Fold `requests`-style `files=`/`data=` into the single `data` dict the
    werkzeug test client expects. requests file specs are
    `(filename, content[, content_type])`; werkzeug wants
    `(stream, filename[, content_type])` — different order, stream-first."""
    files = kwargs.pop("files")
    data = dict(kwargs.pop("data", None) or {})
    for field, spec in files.items():
        if isinstance(spec, (tuple, list)):
            filename, content = spec[0], spec[1]
            content_type = spec[2] if len(spec) > 2 else None
        else:
            filename, content, content_type = None, spec, None
        if hasattr(content, "read"):
            stream = content
        elif isinstance(content, bytes):
            stream = io.BytesIO(content)
        else:
            stream = io.BytesIO(str(content).encode())
        if content_type:
            data[field] = (stream, filename, content_type)
        else:
            data[field] = (stream, filename)
    kwargs["data"] = data
    kwargs["content_type"] = "multipart/form-data"


class _TestClientResponse:
    """Adapts a werkzeug `TestResponse` to the slice of the `requests.Response`
    API the suite touches: `.status_code`, `.headers`, `.text`, `.json()`."""

    def __init__(self, werkzeug_response):
        self._response = werkzeug_response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self):
        return self._response.headers

    @property
    def text(self) -> str:
        return self._response.get_data(as_text=True)

    @property
    def content(self) -> bytes:
        return self._response.get_data()

    def json(self):
        return self._response.get_json()


class _TestClientSession:
    """Stand-in for `requests.Session` backed by a single test client (its own
    cookie jar). Exposes the verb methods the suite uses."""

    def __init__(self, client):
        self._client = client

    def get(self, url, **kwargs):
        return _adapt(self._client, "get")(url, **kwargs)

    def post(self, url, **kwargs):
        return _adapt(self._client, "post")(url, **kwargs)

    def put(self, url, **kwargs):
        return _adapt(self._client, "put")(url, **kwargs)

    def patch(self, url, **kwargs):
        return _adapt(self._client, "patch")(url, **kwargs)

    def delete(self, url, **kwargs):
        return _adapt(self._client, "delete")(url, **kwargs)
