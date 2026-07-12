"""STUB — FU-536: Alembic migration round-trip + portability tests.

WHY THIS MATTERS: there are 117 migration files in
dora_api/persistence/migrations/versions/ and ZERO tests. Migrations run at
startup via flask_migrate `upgrade()` (dora_api/startup.py:153). A bad
downgrade, a migration that isn't portable across SQLite and Postgres, or a
data-losing column drop would only be discovered in production — and FU-045
(the Postgres migration) is on the roadmap, so migration portability is about
to matter a lot. This is the single largest untested surface by file count.

SETUP: this is a UNIT-level test (tests/, not e2e/) — it must build its OWN
throwaway database, NOT reuse the seeded e2e `api` fixture. Use flask_migrate
against a temp SQLite file (and, gated behind an env flag or skipif, a
disposable Postgres for the portability half — coordinate with FU-405 CI).
Find the flask-migrate/alembic config the app uses (the app calls
`flask_migrate.upgrade()`; locate its Migrate() init + the versions dir).

CASES:
  1. Full up-migration on an empty DB — `upgrade head` from scratch succeeds
     and produces a schema whose tables/columns match the ORM metadata
     (compare `db.metadata.tables` keys/columns against the migrated schema;
     catches "model added, migration forgotten" drift).
  2. Down/up round-trip — `upgrade head` → `downgrade base` → `upgrade head`
     runs clean with no exception and lands on the same schema. Catches
     downgrades that were never actually written/tested (the common rot).
  3. Per-migration reversibility — for each revision, upgrade to it then
     downgrade one step; flag any revision whose `downgrade()` is a bare
     `pass` or raises (some may be legitimately irreversible — pin those with
     an explicit allowlist + comment rather than failing).
  4. Data-preserving migrations — for the handful that transform data (not
     just DDL), seed a row in the pre-migration schema, run the upgrade,
     assert the row survived + transformed correctly. Identify these by
     grepping versions/ for `op.execute` / `bulk_insert` / data backfills.
  5. SQLite vs Postgres portability — assert no migration uses a dialect-only
     construct that breaks the other (the R-005 posture). At minimum, run the
     full `upgrade head` on both engines under the CI matrix; ideally scan for
     known-unportable ops (server_default with dialect functions, etc.).
  6. Head uniqueness — exactly one alembic head (no unmerged branch), so
     startup `upgrade()` is unambiguous.

Name tests test__migrations__<property>.
"""
import pytest

pytestmark = pytest.mark.skip(reason="FU-536 stub — fill per module docstring")


def test__migrations__upgrade_head_from_empty_matches_orm_metadata():
    ...


def test__migrations__down_up_roundtrip_is_clean():
    ...


def test__migrations__single_head():
    ...


def test__migrations__data_transforms_preserve_rows():
    ...


@pytest.mark.skipif(True, reason="needs Postgres — gate on FU-405 CI matrix")
def test__migrations__upgrade_head_runs_on_postgres():
    ...
