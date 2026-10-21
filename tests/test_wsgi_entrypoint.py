"""FU-397 — production WSGI entry point + gunicorn config.

The self-host container serves the API through gunicorn (a real WSGI server)
instead of Flask's dev server. These cover the two moving parts without
actually running gunicorn (which can't run on Windows — no fcntl):

  1. `dora_api.wsgi` exposes the Flask `app` as the WSGI callable and wires it
     up via `bootstrap()` at import time (bootstrap itself is stubbed here so
     the test doesn't run migrations / start the scheduler).
  2. `gunicorn.conf.py` derives its bind/worker settings from env, defaults to
     a single threaded worker (so the in-process scheduler stays singular), and
     warns when scaled past one worker.
"""
import importlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Env vars the gunicorn config reads — cleared before each config load so a
# stray value in the dev shell/.env can't skew the assertions.
_GUNICORN_ENV_VARS = (
    "DORA_API_HOST",
    "DORA_API_PORT",
    "DORA_BIND",
    "DORA_WEB_CONCURRENCY",
    "DORA_WEB_THREADS",
    "DORA_WEB_TIMEOUT",
    "DORA_WEB_GRACEFUL_TIMEOUT",
    "DORA_WEB_KEEPALIVE",
    "DORA_GUNICORN_LOG_LEVEL",
)


def _load_gunicorn_conf(monkeypatch, env: dict[str, str]) -> dict:
    """Exec gunicorn.conf.py in a fresh namespace under a controlled env."""
    for name in _GUNICORN_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    path = _REPO_ROOT / "gunicorn.conf.py"
    namespace: dict = {}
    exec(compile(path.read_text(), str(path), "exec"), namespace)  # noqa: S102
    return namespace


# ── WSGI entry point ──────────────────────────────────────────────────────

def test_wsgi_exposes_flask_app_and_bootstraps_once(monkeypatch):
    import dora_api.startup as startup_mod
    from dora_api.app import app as flask_app

    calls: list = []
    # Stub bootstrap so importing wsgi doesn't run migrations / scheduler.
    # `from dora_api.startup import bootstrap` reads the attribute at wsgi
    # import time, so patching it here (before the import below) takes effect.
    monkeypatch.setattr(startup_mod, "bootstrap", lambda *a, **k: calls.append((a, k)))

    sys.modules.pop("dora_api.wsgi", None)
    try:
        wsgi = importlib.import_module("dora_api.wsgi")
        # The WSGI callable gunicorn loads IS the shared Flask app.
        assert wsgi.app is flask_app
        # A Flask app is a WSGI callable.
        assert callable(wsgi.app)
        # bootstrap ran exactly once, at import.
        assert len(calls) == 1
    finally:
        # Drop the stubbed import so later tests re-import cleanly.
        sys.modules.pop("dora_api.wsgi", None)


# ── gunicorn config ───────────────────────────────────────────────────────

def test_gunicorn_defaults_to_single_threaded_worker(monkeypatch):
    ns = _load_gunicorn_conf(monkeypatch, {})
    # One worker on purpose — the in-process scheduler must not duplicate.
    assert ns["workers"] == 1
    assert ns["worker_class"] == "gthread"
    assert ns["threads"] >= 1
    # Logs to stdout/stderr for `docker logs`.
    assert ns["accesslog"] == "-"
    assert ns["errorlog"] == "-"


def test_gunicorn_bind_mirrors_api_host_and_port(monkeypatch):
    ns = _load_gunicorn_conf(monkeypatch, {"DORA_API_HOST": "127.0.0.1", "DORA_API_PORT": "6001"})
    assert ns["bind"] == "127.0.0.1:6001"


def test_gunicorn_bind_defaults_to_all_interfaces_5170(monkeypatch):
    ns = _load_gunicorn_conf(monkeypatch, {})
    assert ns["bind"] == "0.0.0.0:5170"


def test_gunicorn_dora_bind_overrides_host_port(monkeypatch):
    ns = _load_gunicorn_conf(
        monkeypatch,
        {"DORA_BIND": "unix:/tmp/dora.sock", "DORA_API_PORT": "5170"},
    )
    assert ns["bind"] == "unix:/tmp/dora.sock"


def test_gunicorn_concurrency_and_threads_are_env_driven(monkeypatch):
    ns = _load_gunicorn_conf(
        monkeypatch,
        {"DORA_WEB_CONCURRENCY": "3", "DORA_WEB_THREADS": "8"},
    )
    assert ns["workers"] == 3
    assert ns["threads"] == 8


def test_gunicorn_rejects_non_positive_worker_count(monkeypatch):
    # A bogus 0/negative value floors to 1 rather than booting a server with
    # no workers.
    ns = _load_gunicorn_conf(monkeypatch, {"DORA_WEB_CONCURRENCY": "0"})
    assert ns["workers"] == 1


def test_gunicorn_multi_worker_warns_about_scheduler(monkeypatch):
    ns = _load_gunicorn_conf(monkeypatch, {"DORA_WEB_CONCURRENCY": "2"})

    class _Log:
        def __init__(self):
            self.warnings: list[str] = []

        def warning(self, msg, *args):
            self.warnings.append(msg % args if args else msg)

    class _Server:
        log = _Log()

    server = _Server()
    ns["on_starting"](server)
    assert server.log.warnings, "expected a scheduler-duplication warning at >1 worker"
    assert "worker" in server.log.warnings[0].lower()


def test_gunicorn_single_worker_does_not_warn(monkeypatch):
    ns = _load_gunicorn_conf(monkeypatch, {})

    class _Log:
        def __init__(self):
            self.warnings: list[str] = []

        def warning(self, msg, *args):
            self.warnings.append(msg)

    class _Server:
        log = _Log()

    server = _Server()
    ns["on_starting"](server)
    assert server.log.warnings == []
