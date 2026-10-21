"""Production WSGI entry point (FU-397).

A real WSGI server fronts the app in production instead of Flask's dev
server (which is single-threaded, unhardened, and prints a "do not use in
production" banner for good reason). Run it with, e.g.::

    gunicorn -c gunicorn.conf.py dora_api.wsgi:app

Importing this module wires the app up (CORS, migrations, routers, and —
outside tests — the background scheduler) via `bootstrap()`, then exposes the
Flask `app` object as the WSGI callable gunicorn loads. The dev/desktop paths
do NOT import this module; they call `startup()` / `init_db()` directly.

Single-worker is the supported default (see gunicorn.conf.py): the in-process
APScheduler must run in exactly one process, so the daily/hourly jobs fire
once. Scaling to multiple workers/processes needs the worker-split +
externalised-scheduler work parked in OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md.
"""
from dora_api.app import app
from dora_api.startup import bootstrap

# Configure the app at import time so the WSGI server gets a ready-to-serve
# callable. gunicorn imports `dora_api.wsgi:app` in its (single) worker, so
# this runs once per process.
bootstrap()

__all__ = ["app"]
