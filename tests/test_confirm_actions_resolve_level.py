"""Pin the assistant's level-alias resolver to the canonical stock-status
contract (state-ownership refactor Chunk 1 / impl plan §1 — "no name
hardcodes").

The resolver maps user phrasings ("out", "low", "almost gone") to a
``StockStatus``, then picks the row in the StockLevel table whose
``sequence`` matches. Renaming the level's display label must therefore have
no effect on which row gets picked.
"""
from types import SimpleNamespace
from uuid import uuid4

from dora_api.domain.stock_status import StockStatus
from dora_api.features.assistant.confirm_actions import _resolve_level


def _level(sequence: int, name: str):
    return SimpleNamespace(id=uuid4(), sequence=sequence, name=name)


class _FakeAllQuery:
    def __init__(self, rows):
        self._rows = rows

    def all(self, *_args, **_kwargs):
        # confirm_actions only uses the no-filter form for the contract path
        # (level_for_status reads the full set and picks by sequence). The
        # substring fallback path passes a filter; we return the underlying
        # rows and let the test scenario decide what's there.
        return list(self._rows)


class _FakeRepo:
    def __init__(self, levels):
        self._levels = levels

    def get(self, _entity):
        return _FakeAllQuery(self._levels)


# Display names are deliberately *not* the seeded labels — that's the whole
# point: the alias map resolves through StockStatus, not through the name.
_WELL = _level(int(StockStatus.WELL_STOCKED), "Renamed-Well")
_SUFFICIENT = _level(int(StockStatus.SUFFICIENT_STOCK), "Renamed-Sufficient")
_LOW = _level(int(StockStatus.LOW_STOCK), "Renamed-Low")
_OUT = _level(int(StockStatus.OUT_OF_STOCK), "Renamed-Out")
_ALL_LEVELS = [_WELL, _SUFFICIENT, _LOW, _OUT]


def test__alias_resolves_to_sequence_not_name():
    repo = _FakeRepo(_ALL_LEVELS)
    # The seeded "Out of Stock" row has been renamed to "Renamed-Out", yet
    # "out" / "empty" / "gone" must still pick that same row.
    for phrase in ("out", "out of stock", "empty", "gone", "none", "finished"):
        assert _resolve_level(repo, phrase) is _OUT, phrase

    for phrase in ("low", "running low", "almost out", "almost gone"):
        assert _resolve_level(repo, phrase) is _LOW, phrase

    for phrase in ("sufficient", "ok", "fine"):
        assert _resolve_level(repo, phrase) is _SUFFICIENT, phrase

    for phrase in ("well stocked", "stocked up", "full", "plenty"):
        assert _resolve_level(repo, phrase) is _WELL, phrase


def test__alias_is_case_and_whitespace_insensitive():
    repo = _FakeRepo(_ALL_LEVELS)
    assert _resolve_level(repo, "  OUT  ") is _OUT
    assert _resolve_level(repo, "Almost Gone") is _LOW


def test__empty_input_returns_none():
    repo = _FakeRepo(_ALL_LEVELS)
    assert _resolve_level(repo, "") is None
