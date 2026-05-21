"""GET /api/search?q=... — global search across items and locations.

Returns each result with the full breadcrumb path of its containing
location (e.g. "Pantry > Middle shelf > Left side") so the UI can render
"where is this?" without a follow-up call.
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import SEARCH_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Cap so a one-character query doesn't dump the whole DB.
MAX_RESULTS_PER_KIND = 25


@dataclass
class SearchHitDto:
    kind: str  # "item" | "location"
    id: UUID
    name: str
    breadcrumb: List[str]
    location_id: UUID | None


@dataclass
class SearchResultsDto:
    query: str
    items: List[SearchHitDto]
    locations: List[SearchHitDto]


class GlobalSearchHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, query: str) -> SearchResultsDto:
        if not query.strip():
            return SearchResultsDto(query=query, items=[], locations=[])

        all_locations: List[StockLocation] = self.repository.get(StockLocation).all()
        loc_by_id: dict[UUID, StockLocation] = {loc.id: loc for loc in all_locations}

        # Substring (case-insensitive) match across both indexes.
        needle = query.lower()
        location_hits: List[SearchHitDto] = []
        for loc in all_locations:
            if needle in loc.name.lower():
                location_hits.append(SearchHitDto(
                    kind = "location",
                    id = loc.id,
                    name = loc.name,
                    breadcrumb = _breadcrumb(loc, loc_by_id),
                    location_id = loc.id,
                ))
            if len(location_hits) >= MAX_RESULTS_PER_KIND:
                break

        # Item match — single query with a case-insensitive contains filter.
        matched_items: List[StockItem] = (
            self.repository.get(StockItem)
            .include("stock_location")
            .all(EntityField(StockItem, StockItem.Fields.NAME).contains(query))
        )
        item_hits: List[SearchHitDto] = []
        for item in matched_items[:MAX_RESULTS_PER_KIND]:
            loc = item.stock_location
            item_hits.append(SearchHitDto(
                kind = "item",
                id = item.id,
                name = item.name,
                breadcrumb = _breadcrumb(loc, loc_by_id) if loc else [],
                location_id = loc.id if loc else None,
            ))

        return SearchResultsDto(
            query = query,
            items = item_hits,
            locations = location_hits,
        )


def _breadcrumb(location: StockLocation, loc_by_id: dict[UUID, StockLocation]) -> List[str]:
    """Walk up the parent chain, returning names from root to leaf."""
    path: List[str] = []
    cursor: StockLocation | None = location
    safety = 16  # tree depth guard against accidental cycles
    while cursor is not None and safety > 0:
        path.append(cursor.name)
        cursor = loc_by_id.get(cursor.parent_id) if cursor.parent_id else None
        safety -= 1
    path.reverse()
    return path


@SEARCH_ROUTER.route("", methods=["GET"])
def global_search():
    _Logger = logging.getLogger(__name__)
    _Query = request.args.get("q", "").strip()
    _Results = get_container().inject(GlobalSearchHandler).handle(_Query)
    _Logger.info(
        f"Search '{_Query}': {len(_Results.items)} items, {len(_Results.locations)} locations"
    )
    return ok(_Results)
