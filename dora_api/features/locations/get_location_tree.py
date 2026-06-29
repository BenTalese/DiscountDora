"""Returns the full location tree with item counts + heatmap scores.

A single call powers the Home Zones view, the Zone Detail view, and the
hierarchical destination picker — paginating tree shapes is more trouble
than it's worth at the data sizes we expect (dozens of nodes, hundreds of
items).
"""
import logging
from dataclasses import asdict, dataclass, field
from typing import List
from uuid import UUID

from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import effective_expiring_soon_window
from dora_api.features.app_settings.clock import household_today
from dora_api.features.locations.attention import (AttentionReasons,
                                                   reasons_for_item)
from dora_api.features.routers import LOCATION_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass
class LocationItemDto:
    stock_item_id: UUID
    name: str
    stock_level_name: str | None
    expiry_date: str | None
    is_flagged: bool
    attention_score: int
    attention_reasons: dict


@dataclass
class LocationNodeDto:
    location_id: UUID
    name: str
    kind: str
    parent_id: UUID | None
    sequence: int
    direct_item_count: int
    descendant_item_count: int
    attention_score: int
    attention_reasons: dict
    primary_reason: str | None
    items: List[LocationItemDto] = field(default_factory=list)
    children: List["LocationNodeDto"] = field(default_factory=list)


class GetLocationTreeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[LocationNodeDto]:
        locations: List[StockLocation] = self.repository.get(StockLocation).all()
        items: List[StockItem] = (
            self.repository.get(StockItem)
            .include("stock_level")
            .include("stock_location")
            .all()
        )

        # C-9.2 — heatmap honours the household-configured expiring-soon window
        # (same source as the alerts list, R-003), falling back to the default.
        _Settings: List[AppSetting] = self.repository.get(AppSetting).all()
        _Window = effective_expiring_soon_window(_Settings[0] if _Settings else None)
        # R-021 — heatmap calendar boundary uses household-tz today.
        _Today = household_today(self.repository)

        # Bucket items by their location_id (None = unassigned, surfaced
        # separately in the UI).
        items_by_location: dict[UUID, List[StockItem]] = {}
        for item in items:
            if item.stock_location is None:
                continue
            items_by_location.setdefault(item.stock_location.id, []).append(item)

        # Build nodes keyed by id. Reasons start as the per-node items;
        # rolled up via the children pass below.
        node_by_id: dict[UUID, LocationNodeDto] = {}
        reasons_by_id: dict[UUID, AttentionReasons] = {}

        for loc in locations:
            direct_items = items_by_location.get(loc.id, [])
            node_reasons = AttentionReasons()
            item_dtos: List[LocationItemDto] = []
            for item in direct_items:
                ir = reasons_for_item(item, today=_Today, expiring_soon_window=_Window)
                node_reasons = node_reasons.merge(ir)
                item_dtos.append(LocationItemDto(
                    stock_item_id = item.id,
                    name = item.name,
                    stock_level_name = (
                        item.stock_level.name if item.stock_level else None
                    ),
                    expiry_date = item.expiry_date.isoformat() if item.expiry_date else None,
                    is_flagged = bool(item.is_flagged),
                    attention_score = ir.score(),
                    attention_reasons = asdict(ir),
                ))

            reasons_by_id[loc.id] = node_reasons
            node_by_id[loc.id] = LocationNodeDto(
                location_id = loc.id,
                name = loc.name,
                kind = loc.kind,
                parent_id = loc.parent_id,
                sequence = loc.sequence or 0,
                direct_item_count = len(direct_items),
                descendant_item_count = len(direct_items),
                attention_score = 0,
                attention_reasons = {},
                primary_reason = None,
                items = item_dtos,
            )

        # Wire children into parents (sorted by sequence then name for stable
        # rendering) and roll up reasons from leaves to roots.
        children_by_parent: dict[UUID | None, List[LocationNodeDto]] = {}
        for node in node_by_id.values():
            children_by_parent.setdefault(node.parent_id, []).append(node)
        for siblings in children_by_parent.values():
            siblings.sort(key=lambda n: (n.sequence, n.name.lower()))

        def populate(node: LocationNodeDto) -> AttentionReasons:
            rolled = AttentionReasons()
            rolled = rolled.merge(reasons_by_id[node.location_id])
            for child in children_by_parent.get(node.location_id, []):
                child_rolled = populate(child)
                rolled = rolled.merge(child_rolled)
                node.descendant_item_count += child.descendant_item_count
                node.children.append(child)
            node.attention_score = rolled.score()
            node.attention_reasons = asdict(rolled)
            node.primary_reason = rolled.primary_label()
            return rolled

        roots = children_by_parent.get(None, [])
        for root in roots:
            populate(root)
        return roots


@LOCATION_ROUTER.route("", methods=["GET"])
def get_location_tree():
    _Logger = logging.getLogger(__name__)
    _Tree = get_container().inject(GetLocationTreeHandler).handle()
    _Logger.info(f"Returning location tree with {len(_Tree)} root zones.")
    return ok(_Tree)
