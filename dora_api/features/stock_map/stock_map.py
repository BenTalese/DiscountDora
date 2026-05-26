"""N9 — Stock Map persistence.

  GET /api/stock-map  — returns the current install's layout blob
                        (or the empty default if none saved yet).
  PUT /api/stock-map  — replaces the layout blob.

The backend is intentionally dumb: it doesn't interpret the schema.
The SPA owns it (web_app/src/pages/StockMap.vue), which keeps
iteration cheap when new node attributes land.

Storage strategy: a single row in the StockMap table. The schema
isn't user-scoped today, so one map per install matches the rest of
the codebase. If we ever flip to per-user, a column + composite-key
swap goes here.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from flask import request
from pydantic import BaseModel, ConfigDict, Field

from dora_api.app import db
from dora_api.domain.entities.stock_map import StockMap
from dora_api.features.routers import STOCK_MAP_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Hard size cap so a runaway client can't blow up the DB. 256 KiB is
# generous for a few hundred rectangles with chip lists.
_MAX_LAYOUT_BYTES = 256 * 1024

_EMPTY_LAYOUT: dict[str, Any] = {
    "nodes": [],
    "canvas": {"w": 1200, "h": 800},
}


class SaveStockMapRequest(BaseModel):
    """The SPA owns the layout schema; we accept any dict it sends and
    only validate the envelope. The handler re-serialises to canonical
    JSON to strip oddities (NaN, comments, …) before storage."""
    model_config = ConfigDict(extra="forbid")
    layout: dict[str, Any] = Field(default_factory=dict)


def _load_singleton(repo: SqlAlchemyRepository) -> StockMap | None:
    """The table holds at most one row by convention. Take whichever
    one we find first."""
    rows = repo.get(StockMap).all()
    return rows[0] if rows else None


@STOCK_MAP_ROUTER.route("", methods=["GET"])
def get_stock_map():
    repo = SqlAlchemyRepository()
    existing = _load_singleton(repo)
    if existing is None:
        return ok({"layout": _EMPTY_LAYOUT, "updated_at": None})
    try:
        layout = json.loads(existing.layout)
    except (TypeError, ValueError):
        layout = _EMPTY_LAYOUT
    return ok({
        "layout": layout,
        "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
    })


@STOCK_MAP_ROUTER.route("", methods=["PUT"])
@has_request_body(SaveStockMapRequest)
def put_stock_map():
    _Logger = logging.getLogger(__name__)
    body: SaveStockMapRequest = get_request_body()
    encoded = json.dumps(body.layout, default=str, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > _MAX_LAYOUT_BYTES:
        return bad_request(
            f"Layout exceeds the {_MAX_LAYOUT_BYTES // 1024} KiB limit."
        )

    repo = SqlAlchemyRepository()
    existing = _load_singleton(repo)
    now = datetime.now(timezone.utc)
    if existing is None:
        row = StockMap(id=uuid4(), layout=encoded, updated_at=now)
        repo.session.add(row)
    else:
        # Direct UPDATE — the entity is dataclass-mapped but the
        # repository's add() expects unpersisted rows. Skip the
        # ORM dance and update via the table.
        table = db.metadata.tables["StockMap"]
        db.session.execute(
            table.update().where(table.c.id == existing.id).values(
                layout=encoded, updated_at=now,
            )
        )
    db.session.commit()
    _Logger.debug("Saved stock map (%d bytes)", len(encoded))
    return ok({"updated_at": now.isoformat()})
