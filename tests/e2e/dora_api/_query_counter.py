"""FU-138 — query-count harness for the e2e suite.

Subscribes to SQLAlchemy's `before_cursor_execute` hook on the global
`Engine` class, so every DB call dispatched through the in-process
Flask test client is observed. Filters down to SELECT statements
(the N+1 shape we're guarding against); INSERT/UPDATE/DELETE are
ignored because they're caller-driven, not engine-driven loops.

Now a shared harness: FU-138 seeded it for the recipe-list test; FU-534
(2026-07-12) made it the net for the R-032 noload/N+1 family across the
hot reads (`test_query_budgets.py`). Keep it minimal — a SELECT counter,
nothing more; endpoint-specific budgets live in the consuming tests.
"""
import re

from sqlalchemy import event
from sqlalchemy.engine import Engine


_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)


class SelectCounter:
    """Context manager that records every SELECT issued during its scope.

    Usage:
        with SelectCounter() as qc:
            response = requests.get(...)
        assert qc.count < ceiling
    """

    def __init__(self) -> None:
        self.statements: list[str] = []

    def __enter__(self) -> "SelectCounter":
        event.listen(Engine, "before_cursor_execute", self._on_execute)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        event.remove(Engine, "before_cursor_execute", self._on_execute)
        return False

    def _on_execute(
        self, _conn, _cursor, statement, _params, _context, _executemany,
    ) -> None:
        if _SELECT_RE.match(statement):
            self.statements.append(statement)

    @property
    def count(self) -> int:
        return len(self.statements)
