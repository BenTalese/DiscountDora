"""GET /api/stock-items/planned-demand

The per-item planned-demand signal (`planned_demand.py`) for every stock item
the upcoming plan needs. Shaped like `/stock-items/beliefs` on purpose — the
two are additive overlays the same surfaces read, and one client cache pattern
serving both is cheaper than two shapes that mean the same thing (R-003).

Items with no planned demand are **absent** rather than present-with-zero: the
map is a sparse overlay, and a pantry of 400 items would otherwise ship 400
empty objects to say nothing.

`enabled: false` when the meal planner is switched off install-wide, in which
case there is no plan to have demand against.
"""
import logging
from dataclasses import asdict

from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.stock_items._level_access import resolve_levels_by_item
from dora_api.features.stock_items.planned_demand import (
    PLANNED_DEMAND_HORIZON_DAYS, gather_planned_demand, planner_enabled)
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

_LOGGER = logging.getLogger(__name__)


@STOCK_ITEM_ROUTER.route("/planned-demand", methods=["GET"])
def get_planned_demand():
    repo = SqlAlchemyRepository()
    if not planner_enabled(repo):
        return ok({"enabled": False, "horizon_days": PLANNED_DEMAND_HORIZON_DAYS,
                   "demand": {}})

    # The recorded levels are what grades urgency (Out outranks Low), and they
    # come through `_level_access` rather than `item.stock_level` for the
    # R-032 reason that helper exists to solve.
    items: list[StockItem] = repo.get(StockItem).all()
    levels = resolve_levels_by_item(repo, items)
    recorded = {
        item_id: level.sequence
        for item_id, level in levels.items() if level is not None
    }

    demand = gather_planned_demand(repo, recorded_by_item=recorded)
    _LOGGER.debug("planned demand computed for %d items", len(demand))
    return ok({
        "enabled": True,
        "horizon_days": PLANNED_DEMAND_HORIZON_DAYS,
        "demand": {str(k): asdict(v) for k, v in demand.items()},
    })
