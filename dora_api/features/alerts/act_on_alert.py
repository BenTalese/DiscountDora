"""POST /api/alerts/<alert_id>/action — apply an action to an alert.

Alerts are *derived* from current state, not stored, so "dismissing" an
alert means changing the underlying state so it doesn't re-fire:

  - reset_expiry: clear `expiry_date` on the linked stock item
  - extend_expiry: push `expiry_date` forward by 7 days
  - mark_restocked: set the stock level to "Stocked"
  - acknowledge_stocktake: bump `stock_level_last_updated` to now without
    changing the level (the user has "looked at it" but doesn't want to
    change anything)

The alert_id is the stable scoped key `<scope>:<id>:<kind>` (alert_key.py).
Only stock-scoped alerts carry actions today; we extract the stock item id
and route by the action in the body. Non-stock scopes (meal / list / system,
C-9.4+) have no act_on_alert actions yet.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.stock_status import StockStatus, level_for_status
from dora_api.features.alerts.alert_key import SCOPE_STOCK, parse_alert_key
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
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
            # R-021 — when no expiry is set, "extend by 7 days" anchors
            # on household-tz today, not server-local.
            from dora_api.features.app_settings.clock import household_today
            base = item.expiry_date or household_today(self.repository)
            item.expiry_date = base + timedelta(days=7)
        elif action == ACTION_MARK_RESTOCKED:
            stocked = level_for_status(
                self.repository.get(StockLevel).all(), StockStatus.STOCKED
            )
            if stocked is not None:
                item.stock_level = stocked
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
    # `<scope>:<id>:<kind>` — only stock-scoped alerts carry actions; parse
    # out the stock item id and route by the action in the body.
    parsed = parse_alert_key(alert_id)
    if parsed is None or parsed.scope != SCOPE_STOCK or parsed.stock_item_id is None:
        return bad_request(f"Malformed or non-actionable alert id '{alert_id}'.")
    stock_item_id = parsed.stock_item_id

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
