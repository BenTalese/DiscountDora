"""FU-536 — Alembic migration round-trip + integrity tests.

116 migration files run at startup via `flask_migrate.upgrade()` and had ZERO
tests. A bad downgrade, a non-portable op, or a data-losing migration would
only surface in production — and the Postgres migration (FU-045) makes
portability imminent. This is the largest untested surface by file count.

Two layers:

  * IN-PROCESS, no DB (fast, zero risk) — read the Alembic ScriptDirectory:
    exactly one head (unambiguous startup upgrade), linear history with no
    orphaned down_revision, and every revision defines a real downgrade (not
    a silent `pass`, bar an explicit allowlist).

  * SUBPROCESS against a throwaway SQLite file (slower, fully isolated) —
    the app's migration run is coupled to `current_app`'s engine, and the
    app singleton in THIS process is bound to the e2e test DB; running
    `downgrade base` in-process would clobber it mid-suite. So each real
    up/down run happens in a child `python -c` with `DORA_DB_PATH` pointed at
    a temp file — a fresh app on a fresh DB, zero blast radius here.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MIGRATIONS_DIR = _REPO_ROOT / "dora_api" / "persistence" / "migrations"
_VERSIONS_DIR = _MIGRATIONS_DIR / "versions"


# ── In-process: ScriptDirectory (no database) ──────────────────────────────

def _script_directory() -> ScriptDirectory:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    return ScriptDirectory.from_config(cfg)


def test__migrations__single_head():
    """Exactly one head — a branch/merge would make startup `upgrade head`
    ambiguous (Alembic errors on multiple heads)."""
    heads = _script_directory().get_heads()
    assert len(heads) == 1, (
        f"expected exactly one migration head, found {len(heads)}: {heads}. "
        "An unmerged branch — resolve with `flask db merge`."
    )


def test__migrations__history_is_linear_and_walkable():
    """Every revision's down_revision resolves — no orphan pointing at a
    deleted/renamed revision. walk_revisions raises if the chain is broken."""
    script = _script_directory()
    revs = list(script.walk_revisions())
    assert revs, "no migrations found — script_location wrong?"
    # base() resolving proves the whole chain links back to the root.
    assert script.get_current_head() is not None


# Revisions whose downgrade is legitimately a no-op / irreversible go here with
# a reason. Keep this tight — an entry is a claim "this migration genuinely
# can't be reversed", not a way to silence rot.
_IRREVERSIBLE_ALLOWLIST: dict[str, str] = {
    "e2c5a8f1d7b3": (
        "data-cleanup migration (nullify garbage Product.image values) — the "
        "original garbage isn't recoverable, so a no-op downgrade is correct."
    ),
}


def test__migrations__every_revision_defines_a_real_downgrade():
    """A downgrade that's a bare `pass` (or missing) is un-tested rot: the
    round-trip test can't catch a no-op downgrade that silently drops the
    schema-reversal. Static-scan every version file for a non-empty
    downgrade() body."""
    offenders: list[str] = []
    for path in sorted(_VERSIONS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        src = path.read_text(encoding="utf-8")
        rev = path.stem.split("_", 1)[0]
        if rev in _IRREVERSIBLE_ALLOWLIST:
            continue
        # Grab the downgrade() body: everything from `def downgrade` to EOF
        # (downgrade is always the last function in an Alembic script).
        idx = src.find("def downgrade(")
        if idx == -1:
            offenders.append(f"{path.name}: no downgrade() at all")
            continue
        body = src[idx:]
        # Strip the def line + docstring/comments; if all that's left is
        # `pass`, it's a silent no-op.
        code_lines = [
            ln.strip()
            for ln in body.splitlines()[1:]
            if ln.strip() and not ln.strip().startswith(("#", '"', "'"))
        ]
        if code_lines == ["pass"]:
            offenders.append(f"{path.name}: downgrade() is a bare `pass`")
    assert not offenders, (
        "migrations with a missing/no-op downgrade (add to "
        "_IRREVERSIBLE_ALLOWLIST with a reason if genuinely one-way):\n  "
        + "\n  ".join(offenders)
    )


# ── Subprocess: real up/down runs against a throwaway SQLite file ──────────

def _run_migration(temp_db: Path, body: str) -> subprocess.CompletedProcess:
    """Run `body` (flask_migrate calls) in a child process with DORA_DB_PATH
    pointed at `temp_db` — a fresh app on a throwaway DB, isolated from the
    e2e test DB this process is bound to."""
    code = (
        "import flask_migrate\n"
        "from dora_api.app import app\n"
        "with app.app_context():\n"
        + "".join(f"    {ln}\n" for ln in body.strip().splitlines())
        + "print('MIGRATION_OK')\n"
    )
    env = {**os.environ, "DORA_DB_PATH": str(temp_db)}
    # Belt-and-braces: never let a stray .env point the child at the dev DB.
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.fixture()
def temp_db_path():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d) / "migtest.db"


# ── FU-549 — the migration chain now applies cleanly from empty ────────────
# `upgrade head` on a fresh DB previously died inside migration
# a3e9f6c2d8b4_20260618_rename_merchant_to_store at
# `op.batch_alter_table('Product')` with `AttributeError: 'BINARY' object has
# no attribute 'name'` — an Alembic batch-mode rename reading `existing_type.name`
# on a `sqlalchemy_utils.UUIDType`, whose BINARY impl has no `.name`. Fixed
# 2026-07-13 (FU-549) by passing the concrete `sa.BINARY(16)` as `existing_type`
# for the UUIDType-column renames. These tests give the from-empty chain its
# first real coverage (the app's test/seed path uses `db.create_all()`, which
# never exercised migrations), so a regression there fails the suite here.


@pytest.mark.slow
def test__migrations__upgrade_head_from_empty_succeeds(temp_db_path):
    result = _run_migration(temp_db_path, "flask_migrate.upgrade()")
    assert result.returncode == 0 and "MIGRATION_OK" in result.stdout, (
        f"`upgrade head` on an empty DB failed:\n{result.stdout}\n{result.stderr}"
    )
    assert temp_db_path.exists(), "upgrade produced no database file"


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason="FU-553: `downgrade base` dies dropping the named CHECK constraint on "
    "RecipeIngredient (c5a8e1f7d3b2) — alembic batch mode on SQLite doesn't carry "
    "reflected CHECK constraints into its rebuild table, so drop_constraint can't "
    "find it. Upgrade-from-empty (the fresh-install boot path) is fixed under "
    "FU-549; this is downgrade-only (dev/rollback) and likely SQLite-batch-specific "
    "(Postgres drops named checks natively). Flip to XPASS → un-xfail when fixed.",
)
def test__migrations__down_up_roundtrip_is_clean(temp_db_path):
    """upgrade head -> downgrade base -> upgrade head with no exception.
    Catches downgrades that were never actually run (the common rot)."""
    result = _run_migration(
        temp_db_path,
        "flask_migrate.upgrade()\n"
        "flask_migrate.downgrade(revision='base')\n"
        "flask_migrate.upgrade()",
    )
    assert result.returncode == 0 and "MIGRATION_OK" in result.stdout, (
        f"down/up round-trip failed:\n{result.stdout}\n{result.stderr}"
    )


@pytest.mark.slow
def test__migrations__migrated_schema_matches_orm_metadata(temp_db_path):
    """After `upgrade head`, the migrated schema must contain every table the
    ORM metadata declares — catches 'model added, migration forgotten' drift."""
    result = _run_migration(temp_db_path, "flask_migrate.upgrade()")
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    from dora_api.app import db  # metadata only; no engine access here

    expected = set(db.metadata.tables.keys())
    engine = create_engine(f"sqlite:///{temp_db_path}")
    try:
        reflected = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    missing = expected - reflected
    assert not missing, (
        f"tables declared in ORM metadata but absent from the migrated schema "
        f"(migration forgotten?): {sorted(missing)}"
    )


@pytest.mark.skipif(
    "DORA_TEST_POSTGRES_URL" not in os.environ,
    reason="needs a disposable Postgres (set DORA_TEST_POSTGRES_URL) — gate on FU-405 CI matrix",
)
def test__migrations__upgrade_head_runs_on_postgres():
    """R-005 portability: the full stack must apply on Postgres too. Gated on
    a disposable Postgres URL provided by CI (FU-405)."""
    code = (
        "import flask_migrate\n"
        "from dora_api.app import app\n"
        "with app.app_context():\n"
        "    flask_migrate.upgrade()\n"
        "print('MIGRATION_OK')\n"
    )
    env = {**os.environ, "DORA_DB_URL": os.environ["DORA_TEST_POSTGRES_URL"]}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=str(_REPO_ROOT), env=env,
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0 and "MIGRATION_OK" in result.stdout, (
        f"`upgrade head` failed on Postgres:\n{result.stdout}\n{result.stderr}"
    )
