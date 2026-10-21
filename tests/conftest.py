"""Top-level pytest conftest — pin the test DB backend for every test process.

FU-045 made Postgres the standard datastore. Unit tests at `tests/test_*.py`
import `dora_api.features.*` (which transitively imports `dora_api.app` and
resolves the DB URL at module import time) — without an explicit test DB they'd
try the default psycopg connection + fail.

`configure_db_env()` (FU-520 item 1) picks the backend: SQLite by default (the
fast, zero-dep local loop), or the dedicated `dora_test` Postgres when
`DORA_TEST_DB=postgres`. The override sits at the repo's tests/ root so it loads
before any `dora_api.app` import in any test module.
"""
from pathlib import Path

from dotenv import load_dotenv

from tests.db_backend import configure_db_env

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env", override=False)
configure_db_env()
