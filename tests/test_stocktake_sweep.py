"""Unit tests for the Sweep phase's rule (`features/stocktake/sweep.py`).

Chunk 6 / **D-4**. The property under test is *newliness*: the phase must show
the handful of items that left rotation since your last session, and must not
degenerate into "everything Dora has ever stopped tracking" — which is the
nagging the whole plan removes.

`_latest_activity_by_item` is the one part that touches the database, so it's
patched here; the dating rule itself is pure and that's what these pin.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

from dora_api.features.stocktake import sweep as sweep_module
from dora_api.features.stocktake.sweep import resolve_newly_swept

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
WINDOW = 60


@dataclass
class _Item:
    """Duck-typed StockItem — the rule reads `id` and `name` only."""
    name: str = "thing"
    id: UUID = field(default_factory=uuid4)


def _run(items, activity: dict[UUID, datetime], last_session_at):
    with patch.object(
        sweep_module, "_latest_activity_by_item", return_value=activity,
    ):
        return resolve_newly_swept(
            items,
            last_session_at=last_session_at,
            engagement_window_days=WINDOW,
            now=NOW,
        )


def test__resolve_newly_swept__NeverRanASession__IsEmpty():
    """The phase's debut must not dump every long-dead item into it. A user
    with no watermark sees nothing and gets a real Sweep from the next run —
    that's the correct behaviour, not a gap needing a backfill."""
    item = _Item()
    activity = {item.id: NOW - timedelta(days=90)}

    assert _run([item], activity, None) == []


def test__resolve_newly_swept__DroppedOutSinceLastSession__IsListed():
    """The core case: an item whose last activity was 61 days ago crossed the
    60-day line yesterday, and the last session was a week ago."""
    item = _Item(name="tinned peaches")
    activity = {item.id: NOW - timedelta(days=61)}

    swept = _run([item], activity, NOW - timedelta(days=7))

    assert [s.item.name for s in swept] == ["tinned peaches"]
    assert swept[0].dropped_out_at == NOW - timedelta(days=1)
    assert swept[0].last_activity_at == NOW - timedelta(days=61)


def test__resolve_newly_swept__DroppedOutBeforeLastSession__IsNotListed():
    """Already reported once. Showing it again every session is exactly the
    behaviour the watermark exists to prevent."""
    item = _Item()
    # Last activity 100 days ago ⇒ dropped out 40 days ago, well before the
    # session 7 days ago.
    activity = {item.id: NOW - timedelta(days=100)}

    assert _run([item], activity, NOW - timedelta(days=7)) == []


def test__resolve_newly_swept__NotYetDroppedOut__IsNotListed():
    """Guards against a future-dated departure being announced early. An item
    59 days idle is still in rotation; it can only appear here once the window
    has actually elapsed."""
    item = _Item()
    activity = {item.id: NOW - timedelta(days=59)}

    assert _run([item], activity, NOW - timedelta(days=30)) == []


def test__resolve_newly_swept__NoActivityEverRecorded__IsNotListed():
    """An item with no level changes and no list history was never tracked,
    rather than newly untracked. There is no departure to report, and treating
    "no evidence" as "just left" would fill the phase with items the user has
    never interacted with."""
    item = _Item()

    assert _run([item], {}, NOW - timedelta(days=365)) == []


def test__resolve_newly_swept__SeveralDepartures__NewestFirstThenByName():
    """Newest first: the most recent departure is the one the user is most
    likely to recognise and have an opinion about. Equal dates break on name so
    the list is deterministic between two calls on unchanged data."""
    older = _Item(name="older")
    newer = _Item(name="newer")
    same_b = _Item(name="bbb")
    same_a = _Item(name="aaa")
    activity = {
        older.id: NOW - timedelta(days=75),   # dropped out 15 days ago
        newer.id: NOW - timedelta(days=62),   # dropped out 2 days ago
        same_a.id: NOW - timedelta(days=65),  # both dropped out 5 days ago
        same_b.id: NOW - timedelta(days=65),
    }

    swept = _run([older, newer, same_b, same_a], activity,
                 NOW - timedelta(days=30))

    assert [s.item.name for s in swept] == ["newer", "aaa", "bbb", "older"]


def test__resolve_newly_swept__NoCandidates__IsEmpty():
    assert _run([], {}, NOW - timedelta(days=7)) == []


def test__resolve_newly_swept__DroppedOutExactlyAtTheWatermark__IsNotListed():
    """Boundary: `dropped_out_at == last_session_at` counts as already-seen.
    Picking the other side of that comparison would re-show one item on every
    consecutive session run, which is the annoying failure mode."""
    item = _Item()
    last_session = NOW - timedelta(days=10)
    # Activity 70 days ago ⇒ dropped out exactly 10 days ago.
    activity = {item.id: NOW - timedelta(days=70)}

    assert _run([item], activity, last_session) == []


def test__resolve_newly_swept__NaiveLastSessionAt__StillDatesTheDropOut():
    """A naive ``last_session_at`` must not blow the endpoint up.

    SQLite hands back naive datetimes for ``DateTime(timezone=True)`` columns,
    so ``User.stocktake_last_session_at`` arrives naive on a SQLite install
    while every value it is compared against here is tz-aware. The bare ``<=``
    raised TypeError and 500'd ``GET /api/stocktake/session`` for any user who
    had ever completed a run.

    It stayed hidden because nothing ever seeded a *past* session: the field
    was None on every dev and test user, and None short-circuits the whole
    function before the comparison. Same trap as FU-526, one field along.
    """
    item = _Item(name="vinegar")
    last_activity = NOW - timedelta(days=WINDOW + 5)   # dropped out 5 days ago
    naive_last_session = (NOW - timedelta(days=10)).replace(tzinfo=None)

    result = _run([item], {item.id: last_activity}, naive_last_session)

    assert [s.item.name for s in result] == ["vinegar"]
