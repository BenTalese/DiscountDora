"""FU-513 — snooze pruning moved off the GET read path.

Locks two invariants:

1. `GET /api/suggestions` **no longer mutates the DB.** The historic
   inline delete-and-commit at every dashboard load is gone; the read
   filter (`_is_suppressed_now`) still ignores expired snoozes for
   correctness — the row just stays until the scheduler sweeps it.
2. `prune_expired_snoozes` (the new APScheduler job, invoked directly
   here since the scheduler is disabled in `is_test_env`) removes
   elapsed snoozes and leaves dismissed rows + unexpired snoozes alone.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import requests

from dora_api.app import app
from dora_api.domain.entities.dora_suggestion_suppression import (
    SUPPRESSION_DECISION_DISMISSED, SUPPRESSION_DECISION_SNOOZED,
    DoraSuggestionSuppression,
)
from dora_api.features.suggestions.prune_expired_snoozes import \
    prune_expired_snoozes
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

BASE = "http://localhost:5170/api"


def _add_suppression(
    *,
    kind: str,
    dedup_key: str,
    decision: str,
    snoozed_until: datetime | None,
) -> None:
    now = datetime.now(timezone.utc)
    with app.app_context():
        repo = SqlAlchemyRepository()
        repo.add(DoraSuggestionSuppression(
            kind=kind,
            dedup_key=dedup_key,
            decision=decision,
            snoozed_until=snoozed_until,
            created_at=now,
        ))
        repo.save_changes()


def _all_suppressions() -> list[DoraSuggestionSuppression]:
    with app.app_context():
        return SqlAlchemyRepository().get(DoraSuggestionSuppression).all()


@pytest.fixture(autouse=True)
def _clean_suppressions_table():
    """Suggestions tests own the whole table for the duration of each
    case — start clean, end clean. Other suites don't touch it."""
    def _wipe():
        with app.app_context():
            repo = SqlAlchemyRepository()
            for row in repo.get(DoraSuggestionSuppression).all():
                repo.remove(row)
            repo.save_changes()
    _wipe()
    yield
    _wipe()


def test__get_suggestions__does_not_mutate_the_db_even_with_expired_snoozes():
    """The FU-513 invariant. Pre-fix, every GET deleted expired snoozes
    and committed; this test would fail (row count drops to 0)."""
    now = datetime.now(timezone.utc)
    _add_suppression(
        kind="use_soon",
        dedup_key=str(uuid4()),
        decision=SUPPRESSION_DECISION_SNOOZED,
        snoozed_until=now - timedelta(days=1),
    )
    assert len(_all_suppressions()) == 1

    resp1 = requests.get(f"{BASE}/suggestions")
    assert resp1.status_code == 200, resp1.text
    resp2 = requests.get(f"{BASE}/suggestions")
    assert resp2.status_code == 200, resp2.text

    # Row must still be there. Two GETs across the read path did not
    # mutate; only the scheduler prune should remove it.
    assert len(_all_suppressions()) == 1, (
        "GET /api/suggestions is writing to the DB again (FU-513 regression)"
    )


def test__prune_expired_snoozes__removes_only_elapsed_snoozed_rows():
    """Contract: dismissed rows are permanent; unexpired snoozes are
    kept; only snoozed rows with `snoozed_until <= now` are pruned."""
    now = datetime.now(timezone.utc)

    _add_suppression(
        kind="use_soon",
        dedup_key="expired-snooze",
        decision=SUPPRESSION_DECISION_SNOOZED,
        snoozed_until=now - timedelta(hours=1),
    )
    _add_suppression(
        kind="use_soon",
        dedup_key="future-snooze",
        decision=SUPPRESSION_DECISION_SNOOZED,
        snoozed_until=now + timedelta(days=1),
    )
    _add_suppression(
        kind="frequent_waster",
        dedup_key="permanent-dismiss",
        decision=SUPPRESSION_DECISION_DISMISSED,
        snoozed_until=None,
    )
    assert len(_all_suppressions()) == 3

    deleted = prune_expired_snoozes()

    assert deleted == 1
    remaining = {s.dedup_key for s in _all_suppressions()}
    assert remaining == {"future-snooze", "permanent-dismiss"}


def test__prune_expired_snoozes__is_noop_when_nothing_expired():
    """Empty-input branch: no rows in the table → 0 deleted, no errors."""
    assert prune_expired_snoozes() == 0

    # And with only unexpired rows: still no-op.
    now = datetime.now(timezone.utc)
    _add_suppression(
        kind="use_soon",
        dedup_key="future",
        decision=SUPPRESSION_DECISION_SNOOZED,
        snoozed_until=now + timedelta(days=7),
    )
    assert prune_expired_snoozes() == 0
    assert len(_all_suppressions()) == 1


def test__prune_expired_snoozes__leaves_snoozed_rows_with_null_snoozed_until_alone():
    """Defensive: a SNOOZED row with `snoozed_until IS NULL` should not
    be pruned. It's a data-integrity oddity, but the filter must be
    strict — never delete rows the read path is still respecting."""
    _add_suppression(
        kind="use_soon",
        dedup_key="null-until",
        decision=SUPPRESSION_DECISION_SNOOZED,
        snoozed_until=None,
    )
    assert prune_expired_snoozes() == 0
    assert len(_all_suppressions()) == 1
