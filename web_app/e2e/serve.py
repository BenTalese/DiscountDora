"""Boot a seeded backend for the Playwright e2e layer (FU-540).

Playwright's `webServer` runs this. It:
  1. deletes the throwaway e2e DB so every run starts from a clean, freshly
     seeded state (the `dora`/`dora` admin the smoke specs log in as), and
  2. boots the real app via `dora_api.startup`, which — in debug+seed mode —
     builds the schema with `db.create_all()` (NOT migrations; sidesteps the
     FU-549 from-empty migration issue) and serves BOTH the API and the built
     SPA (`web_app/dist/spa`) on one origin.

Env (set by playwright.config.ts): DORA_DEBUG=true, DORA_ALLOW_DESTRUCTIVE=true
(→ seed), DORA_DB_PATH=<temp e2e db>, DORA_SPA_DIR=<abs dist/spa>,
DORA_API_PORT=5170. Run from the repo root.
"""
import os
import pathlib
import runpy
import sys

# Running this as a script puts web_app/e2e on sys.path, not the repo root —
# so `dora_api` (at the repo root) isn't importable. Add the repo root.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

_db = os.environ.get("DORA_DB_PATH")
if _db:
    p = pathlib.Path(_db)
    if p.exists():
        p.unlink()

# Hand off to the app's normal entrypoint (runs startup() as __main__).
runpy.run_module("dora_api.startup", run_name="__main__")
