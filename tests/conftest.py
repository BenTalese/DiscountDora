"""Top-level pytest conftest — pin DORA_DB_URL for every test process.

FU-045 made Postgres the standard datastore. The e2e suite has its own
conftest under `tests/e2e/dora_api/` that pins to SQLite for isolation,
but unit tests at `tests/test_*.py` import `dora_api.features.*` (which
transitively imports `dora_api.app` and resolves the DB URL at module
import time) — without this default they'd try psycopg + fail.

The override sits at the repo's tests/ root so it loads before any
`dora_api.app` import in any test module.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env", override=False)
(_REPO_ROOT / "data").mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "DORA_DB_PATH",
    str(_REPO_ROOT / "data" / "dora.test.db"),
)
