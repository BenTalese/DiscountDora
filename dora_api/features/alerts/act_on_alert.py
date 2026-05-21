"""POST /api/alerts/<alert_id>/action — apply an action to an alert.

Alerts are *derived* from current state, not stored, so "dismissing" an
alert means changing the underlying state so it doesn't re-fire:

  - reset_expiry: clear `expiry_date` on the linked stock item
  - extend_expiry: push `expiry_date` forward by 7 days
  - mark_restocked: set the stock level to "Well-Stocked"
  - acknowledge_stocktake: bump `stock_level_last_updated` to now without
    changing the level (the user has "looked at it" but doesn't want to
    change anything)

The alert_id format is `<stock_item_id>:<kind>` — we extract the UUID and
match the action against the kind.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


ACTION_RESET_EXPIRY = "reset_expiry"
ACTION_EXTEND_EXPIRY = "extend_expiry"
ACTION_MARK_RESTOCKED = "mark_restocked"
ACTION_ACKNOWLEDGE_STOCKTAKE = "acknowledge_stocktake"


class AlertActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str


@dataclass(slots=True)
class AlertActionResponse:
    item_not_found: bool = False
    invalid_action: bool = False


class AlertActionHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: UUID, action: str) -> AlertActionResponse:
        item: StockItem | None = self.repository.get(StockItem).by_id(stock_item_id)
        if item is None:
            return AlertActionResponse(item_not_found=True)

        if action == ACTION_RESET_EXPIRY:
            item.expiry_date = None
        elif action == ACTION_EXTEND_EXPIRY:
            from datetime import date as _date
            base = item.expiry_date or _date.today()
            item.expiry_date = base + timedelta(days=7)
        elif action == ACTION_MARK_RESTOCKED:
            well_stocked: StockLevel | None = self.repository.get(StockLevel).one(
                EntityField(StockLevel, StockLevel.Fields.NAME).eq("Well-Stocked")
            )
            if well_stocked is not None:
                item.stock_level = well_stocked
            item.stock_level_last_updated = datetime.now(timezone.utc)
        elif action == ACTION_ACKNOWLEDGE_STOCKTAKE:
            item.stock_level_last_updated = datetime.now(timezone.utc)
        else:
            return AlertActionResponse(invalid_action=True)

        self.repository.save_changes()
        return AlertActionResponse()


@ALERT_ROUTER.route("/<alert_id>/action", methods=["POST"])
@has_request_body(AlertActionRequest)
def act_on_alert(alert_id: str):
    _Logger = logging.getLogger(__name__)
    # `<stock_item_id>:<kind>` — split, validate the UUID, route by action.
    parts = alert_id.split(":", 1)
    if len(parts) != 2:
        return bad_request(f"Malformed alert id '{alert_id}'.")
    try:
        stock_item_id = UUID(parts[0])
    except ValueError:
        return bad_request(f"Malformed alert id '{alert_id}'.")

    _Request: AlertActionRequest = get_request_body()
    _Response = get_container().inject(AlertActionHandler).handle(
        stock_item_id, _Request.action
    )
    if _Response.item_not_found:
        return not_found("StockItem", stock_item_id)
    if _Response.invalid_action:
        return business_rule_violation(f"Unknown action '{_Request.action}'.")
    _Logger.info(
        f"Alert action {_Request.action} applied to {stock_item_id} (alert {alert_id})"
    )
    return no_content()
