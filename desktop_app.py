"""Desktop A — entry point for the bundled native app.

Run directly (`python desktop_app.py`) from a dev checkout that has
already built the SPA via `quasar build`, or as the PyInstaller
target for the installer pipeline.

Boot sequence:
    1. Resolve per-user data / cache / log dirs via platformdirs and
       export them as DORA_* env vars BEFORE any dora_api module
       loads (the env-first config layer reads them at import time).
    2. Tell the production gate to stand down (DORA_SKIP_PROD_VALIDATION).
    3. Run the Flask app on a random localhost port in a daemon
       thread using werkzeug.serving.make_server, so we can shut it
       down cleanly when the window closes.
    4. Poll /api/health until it answers 200 (max 5s).
    5. Launch a pywebview window pointed at the local Flask URL.
    6. On window close, shut Flask down and exit.

Nothing here is Docker-aware. Docker keeps using startup.sh.
"""
from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from platformdirs import (user_cache_dir, user_data_dir, user_log_dir)


APP_NAME = "Dora"
APP_PUBLISHER = "BenTalese"


def _set_default_env(name: str, value: str) -> None:
    """Like os.environ.setdefault, but treats empty-string values as
    unset (matches the convention the config layer uses)."""
    if not os.environ.get(name):
        os.environ[name] = value


def _bootstrap_paths() -> None:
    """Wire the per-OS user data dirs into the DORA_* env vars the
    config layer reads. Must run BEFORE any `from dora_api...` import
    happens, since `configuration_manager.py` reads env at module
    import time."""
    data = Path(user_data_dir(APP_NAME, APP_PUBLISHER))
    cache = Path(user_cache_dir(APP_NAME, APP_PUBLISHER))
    logs = Path(user_log_dir(APP_NAME, APP_PUBLISHER))
    for path in (data, cache, logs):
        path.mkdir(parents=True, exist_ok=True)

    _set_default_env("DORA_DATA_DIR", str(data))
    _set_default_env("DORA_CACHE_DIR", str(cache))
    _set_default_env("DORA_LOG_DIR", str(logs))

    # FU-045: the bundled desktop install is the canonical lightweight
    # self-host — pin it to SQLite under the per-user data dir. The
    # config layer would otherwise default to Postgres (the standard
    # for dev/hosted), which obviously isn't available on a freshly
    # installed end-user machine. `DORA_DB_PATH` is the SQLite shortcut
    # (plain filesystem path; the config layer builds the URL).
    _set_default_env("DORA_DB_PATH", str(data / "dora.data.db"))

    # Production profile + skip the required-vars gate (no public
    # CORS host, no bootstrap-admin email needed on a single-user
    # desktop install).
    _set_default_env("DORA_ENV", "production")
    _set_default_env("DORA_SKIP_PROD_VALIDATION", "true")
    # CORS doesn't apply when the SPA is served from the same Flask
    # origin, but the prod validation still inspects the var. Empty
    # is fine because we set SKIP=true above.
    _set_default_env("DORA_CORS_ORIGINS", "")


def _bootstrap_spa_dir() -> None:
    """Tell Flask where the built SPA lives.

    PyInstaller's one-folder bundle extracts data files to a path
    accessible via `sys._MEIPASS` (one-file mode) OR alongside the
    binary (one-folder mode). We try both. Falls back to the dev
    checkout path so `python desktop_app.py` from a built repo works
    without bundling at all."""
    if os.environ.get("DORA_SPA_DIR"):
        return
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "web_app" / "dist" / "spa")
    here = Path(__file__).resolve().parent
    candidates.append(here / "web_app" / "dist" / "spa")
    for c in candidates:
        if (c / "index.html").is_file():
            os.environ["DORA_SPA_DIR"] = str(c)
            return


def _bootstrap_piper() -> None:
    """Point DORA_PIPER_BIN at the bundled Piper binary so Dora's neural voice
    works out of the box on desktop (R-018 / ADR-013).

    `dora.spec` ships `packaging/piper/` to `<bundle>/piper/` when the build
    fetched it (packaging/fetch_piper.py). One-folder + one-file PyInstaller
    both expose that via `sys._MEIPASS`; we also check alongside the script so
    a dev `python desktop_app.py` with a populated `packaging/piper/` works.
    If no bundled binary is found we leave DORA_PIPER_BIN unset — `/api/tts`
    then 503s and the SPA falls back to the browser voice. Voice models are
    downloaded on demand into the data dir, untouched here."""
    if os.environ.get("DORA_PIPER_BIN"):
        return
    exe = "piper.exe" if sys.platform.startswith("win") else "piper"
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
    here = Path(__file__).resolve().parent
    roots.append(here)                 # alongside the bundled executable
    roots.append(here / "packaging")   # dev checkout layout
    for root in roots:
        candidate = root / "piper" / exe
        if candidate.is_file():
            os.environ["DORA_PIPER_BIN"] = str(candidate)
            return


def _pick_free_port() -> int:
    """Bind to port 0 to let the kernel pick, then release. Tiny
    race window between release and Flask binding — acceptable for a
    local single-user desktop app."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(url: str, timeout_seconds: float = 5.0) -> bool:
    """Poll /api/health until it returns 2xx or the deadline passes."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if 200 <= resp.status < 300:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(0.1)
    return False


def main() -> int:
    _bootstrap_paths()
    _bootstrap_spa_dir()
    _bootstrap_piper()

    # Set up file-based logging early so anything that goes wrong
    # below leaves a trail in user_log_dir. The desktop bundle has
    # no stdout the user can see.
    log_dir = Path(os.environ["DORA_LOG_DIR"])
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "desktop.log", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    log = logging.getLogger("dora.desktop")
    log.info("Booting Dora desktop")
    log.info("  data=%s", os.environ["DORA_DATA_DIR"])
    log.info("  cache=%s", os.environ["DORA_CACHE_DIR"])
    log.info("  logs=%s", os.environ["DORA_LOG_DIR"])
    log.info("  spa=%s", os.environ.get("DORA_SPA_DIR") or "<not found>")

    # Import lazily so the env vars above are already set by the
    # time any `from dora_api...` module runs.
    from dora_api.app import app as dora_app
    from dora_api.startup import init_db, register_routers

    init_db(is_test_env=False)
    register_routers()

    from werkzeug.serving import make_server

    dora_port = _pick_free_port()
    dora_url = f"http://127.0.0.1:{dora_port}/"
    log.info("dora_api binding to %s", dora_url)

    dora_server = make_server("127.0.0.1", dora_port, dora_app, threaded=True)

    dora_thread = threading.Thread(
        target=dora_server.serve_forever, name="dora-flask", daemon=True,
    )
    dora_thread.start()

    if not _wait_for_health(f"{dora_url}api/health"):
        log.error("dora_api didn't answer /api/health within 5s; aborting")
        dora_server.shutdown()
        return 2

    spa_url = dora_url
    log.info("Flask ready; launching window at %s", spa_url)

    # pywebview/GTK turned out to be a deeper packaging fight than
    # was worth shipping for v1: PyGObject won't reliably install in
    # an isolated venv, and PyInstaller can't bundle the system `gi`
    # cleanly. The bundle opens the SPA in the user's default
    # browser instead and keeps the local Flask servers alive in the
    # foreground. Ctrl-C (or closing the launching terminal) shuts
    # everything down. Less native-feeling than a pywebview window
    # but reliable across Linux desktops. Revisit when there's time
    # to wrangle GTK bundling properly.
    import signal
    import webbrowser

    log.info("Opening %s in the default browser", spa_url)
    webbrowser.open(spa_url)

    stop = threading.Event()
    def _shutdown(*_: object) -> None:
        log.info("Shutdown signal received")
        stop.set()
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("[dora] Browser launched. Press Ctrl-C to quit.", flush=True)
    try:
        stop.wait()
    finally:
        log.info("Shutting Flask server down")
        dora_server.shutdown()
        dora_thread.join(timeout=5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
