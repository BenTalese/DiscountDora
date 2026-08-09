"""X5 — multi-source auto-generated shopping lists.

  POST /api/shopping-lists/auto-generate
      Generic builder. Each `sources.*` flag pulls candidate stock items
      from a different angle; the handler dedupes across sources, keeping
      the highest-priority provenance, and either appends to an existing
      list (`merge_into_list_id`) or creates a fresh one.

  POST /api/shopping-lists/<id>/append-low-stock-essentials
      Convenience wrapper — appends essential items that are low/out to the
      given list. Reuses the same handler.

Provenance priority (highest first), used when an item shows up via more
than one source:

    auto_recipe > auto_meal_plan > auto_flagged > auto_essential
      > auto_low_stock > auto_frequently_added

The priority drives which `added_via` chip the line gets in the UI, and
which subtitle ("from recipe X" / "low stock" / etc) is rendered. The
ranking favours user-initiated intent (a recipe the user picked beats
the silent low-stock fallback).
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (
    ADDED_VIA_AUTO_ESSENTIAL,
    ADDED_VIA_AUTO_FLAGGED,
    ADDED_VIA_AUTO_FREQUENTLY_ADDED,
    ADDED_VIA_AUTO_LOW_STOCK,
    ADDED_VIA_AUTO_MEAL_PLAN,
    ADDED_VIA_AUTO_RECIPE,
    SHOPPING_LIST_STATUS_DONE,
    ShoppingList,
    ShoppingListLine,
)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# Stock level sequences (seed.py): 0=Stocked, 1=Low, 2=Out.
SEQ_STOCKED = 0
SEQ_LOW = 1
SEQ_OUT = 2
LOW_OR_OUT = {SEQ_LOW, SEQ_OUT}


# Highest priority first. The handler picks the first (= most "intentional")
# provenance when an item is collected by multiple sources.
PROVENANCE_PRIORITY: Tuple[str, ...] = (
    ADDED_VIA_AUTO_RECIPE,
    ADDED_VIA_AUTO_MEAL_PLAN,
    ADDED_VIA_AUTO_FLAGGED,
    ADDED_VIA_AUTO_ESSENTIAL,
    ADDED_VIA_AUTO_LOW_STOCK,
    ADDED_VIA_AUTO_FREQUENTLY_ADDED,
)
_PRIORITY_INDEX: Dict[str, int] = {p: i for i, p in enumerate(PROVENANCE_PRIORITY)}


class AutoGenerateSources(BaseModel):
    model_config = ConfigDict(extra="forbid")
    low_stock: bool = False
    out_of_stock: bool = False
    # When True, only essential (is_essential) items count for the low/out
    # picks above — useful for "shop the staples I'm short on" runs.
    essentials_only_for_low: bool = False
    flagged: bool = False
    frequently_added: bool = False
    # Top-N count for frequently_added (only consulted when flag is set).
    frequently_added_limit: int = 10
    # ISO date naming the start of the meal-plan week to pull ingredients
    # from. Resolution: any MealPlanEntry between [week_start, week_start+6d].
    meal_plan_week: Optional[date] = None
    # Specific recipe IDs to ingest. For each recipe, subtract items that
    # are stocked. Mode == "missing" means subtract; we don't yet
    # support "ingredients regardless of stock" here (no UX path for it).
    recipes: List[UUID] = []


class AutoGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Optional explicit name; ignored if merging into an existing list.
    name: Optional[str] = None
    sources: AutoGenerateSources = AutoGenerateSources()
    # When set, append (deduplicated) to this existing list. When None, a
    # new list is created — auto-named "Auto N · <date>" if `name` is
    # blank, where N is the count of existing auto-generated lists + 1.
    merge_into_list_id: Optional[UUID] = None


@dataclass(slots=True)
class _Candidate:
    stock_item: StockItem
    added_via: str
    # Free-form provenance detail for the UI to render alongside the chip.
    # Examples: "Tomato Soup" (recipe name), "Mon 1 Jun" (meal plan day).
    # None means "no extra context, just the chip".
    detail: Optional[str] = None

    def replace_with(self, other: "_Candidate") -> "_Candidate":
        # Higher-priority provenance wins. Lower index in PROVENANCE_PRIORITY
        # = higher priority.
        if _PRIORITY_INDEX[other.added_via] < _PRIORITY_INDEX[self.added_via]:
            return other
        return self


@dataclass(slots=True)
class _LineResult:
    line_id: UUID
    stock_item_id: UUID
    added_via: str
    detail: Optional[str]


@dataclass(slots=True)
class _UnlinkedSkip:
    """FU-505 — a recipe ingredient the auto-generator couldn't turn into a
    shopping-list line because it isn't linked to any StockItem. Surfaced to
    the SPA as a warning banner so users know which items they still need to
    add manually (auto-gen only produces stock-item-anchored lines; a free-
    text-only line shape doesn't exist)."""
    recipe_name: str
    ingredient_name: str


@dataclass(slots=True)
class AutoGenerateResponse:
    shopping_list_id: Optional[UUID] = None
    list_not_found: bool = False
    nothing_to_add: bool = False
    added_count: int = 0
    skipped_already_on_list: int = 0
    lines: List[_LineResult] = field(default_factory=list)
    unlinked_skipped: List[_UnlinkedSkip] = field(default_factory=list)


class AutoGenerateHandler:
    """Pulls candidates from each enabled source, dedupes, writes lines.

    The handler intentionally returns the resulting list ID + per-line
    provenance so the frontend can navigate straight to the new list and
    render added_via chips without an extra round-trip.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: AutoGenerateRequest) -> AutoGenerateResponse:
        # ── Resolve target list on the merge path (existence check first) ─
        # For the create-new path we defer construction until after candidate
        # collection so a call that yields zero candidates doesn't leave a
        # lonely empty list behind (FU-351 — the "Draft my shop" one-click
        # entry point on the dashboard leans on this: if the user has no
        # meal plan / no low stock / no essentials, they get an honest
        # "nothing to draft" notice rather than a "Weekly shop · Sat 12 Jul"
        # phantom in the sidebar). NewListDialog always passes a
        # merge_into_list_id (it creates the list before auto-gen), so this
        # only affects the standalone create-new callers.
        target: Optional[ShoppingList] = None
        if request.merge_into_list_id is not None:
            target = self.repository.get(ShoppingList).by_id(request.merge_into_list_id)
            if target is None or target.is_done:
                return AutoGenerateResponse(list_not_found=True)

        # ── Collect candidates ────────────────────────────────────────────
        candidates: Dict[UUID, _Candidate] = {}
        # FU-505 — recipe / meal-plan collectors append here whenever an
        # ingredient can't be turned into a stock-item-anchored line. The
        # SPA renders these as a "you'll need to add these manually" banner.
        unlinked_skipped: List[_UnlinkedSkip] = []

        if request.sources.low_stock or request.sources.out_of_stock:
            self._collect_low_or_out(candidates, request.sources)

        if request.sources.flagged:
            self._collect_flagged(candidates)

        if request.sources.recipes:
            self._collect_recipes(candidates, request.sources.recipes, unlinked_skipped)

        if request.sources.meal_plan_week is not None:
            self._collect_meal_plan_week(
                candidates, request.sources.meal_plan_week, unlinked_skipped,
            )

        if request.sources.frequently_added:
            self._collect_frequently_added(
                candidates, request.sources.frequently_added_limit
            )

        if not candidates:
            # Create-new path with zero candidates: don't materialise an
            # empty list; return a null shopping_list_id + nothing_to_add.
            # Merge-into path with zero candidates: the target already
            # exists (user picked it), so still return its id so the
            # client can navigate to it.
            return AutoGenerateResponse(
                shopping_list_id=target.id if target is not None else None,
                nothing_to_add=True,
                unlinked_skipped=unlinked_skipped,
            )

        # Candidates exist → we're committing writes; the create-new path
        # can safely materialise the list now.
        if target is None:
            target = self._create_list(request.name)

        # ── Append, skipping items already on the target ─────────────────
        existing_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target.id)
        )
        on_list = {l.stock_item_id for l in existing_lines}
        next_sequence = (max((l.sequence for l in existing_lines), default=-1)) + 1

        now = datetime.now(timezone.utc)
        added: List[_LineResult] = []
        skipped = 0
        for stock_item_id, cand in candidates.items():
            if stock_item_id in on_list:
                skipped += 1
                continue
            line = ShoppingListLine(
                shopping_list_id=target.id,
                stock_item_id=stock_item_id,
                quantity=1,
                sequence=next_sequence,
                added_via=cand.added_via,
                added_at=now,
            )
            self.repository.add(line)
            next_sequence += 1
            added.append(
                _LineResult(
                    line_id=line.id,
                    stock_item_id=stock_item_id,
                    added_via=cand.added_via,
                    detail=cand.detail,
                )
            )

        self.repository.save_changes()
        return AutoGenerateResponse(
            shopping_list_id=target.id,
            added_count=len(added),
            skipped_already_on_list=skipped,
            lines=added,
            unlinked_skipped=unlinked_skipped,
        )

    # ── List creation ───────────────────────────────────────────────────

    def _create_list(self, name: Optional[str]) -> ShoppingList:
        now = datetime.now(timezone.utc)
        if name and name.strip():
            list_name = name.strip()
        else:
            # "Auto 3 · Sun 31 May" — N counts non-archived auto-named lists
            # to keep the sequence stable as old runs get archived.
            n = self._next_auto_index()
            list_name = f"Auto {n} · {now.strftime('%a %d %b')}"

        target = ShoppingList(name=list_name, created_at=now)
        self.repository.add(target)
        # FU-512 unit-of-work: no habit-commit here. `target.id` is
        # assigned client-side by `add()` (uuid4). The immediate downstream
        # `repository.get(ShoppingListLine).all(...).eq(target.id)` runs a
        # SELECT via SQLAlchemy, which autoflushes the pending
        # ShoppingList row before executing — so FK visibility is
        # guaranteed for the ShoppingListLine inserts that follow.
        # The single commit at the end of `handle()` persists the whole
        # unit; FU-351's empty-list guard (see L210-220) already prevents
        # a phantom-empty-list.
        return target

    def _next_auto_index(self) -> int:
        all_lists = self.repository.get(ShoppingList).all()
        # name is nullable now (UX-v2 self-labelled lists) — guard the scan.
        return sum(1 for l in all_lists if (l.name or "").startswith("Auto ")) + 1

    # ── Sources ─────────────────────────────────────────────────────────

    def _all_items_with_level(self) -> List[StockItem]:
        return (
            self.repository.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .all()
        )

    def _collect_low_or_out(
        self,
        candidates: Dict[UUID, _Candidate],
        sources: AutoGenerateSources,
    ) -> None:
        wanted_seqs = set()
        if sources.low_stock:
            wanted_seqs.add(SEQ_LOW)
        if sources.out_of_stock:
            wanted_seqs.add(SEQ_OUT)
        if not wanted_seqs:
            return

        items = self._all_items_with_level()
        for item in items:
            if item.stock_level is None:
                continue
            seq = getattr(item.stock_level, "sequence", -1)
            if seq not in wanted_seqs:
                continue
            if sources.essentials_only_for_low and not item.is_essential:
                continue
            via = (
                ADDED_VIA_AUTO_ESSENTIAL
                if sources.essentials_only_for_low and item.is_essential
                else ADDED_VIA_AUTO_LOW_STOCK
            )
            self._merge(candidates, item.id, _Candidate(stock_item=item, added_via=via))

    def _collect_flagged(self, candidates: Dict[UUID, _Candidate]) -> None:
        # "Always include in auto-generated lists" — flagged items go on the
        # list even if currently stocked. The user has explicitly said
        # "always restock this".
        items: List[StockItem] = self.repository.get(StockItem).all(
            EntityField(StockItem, StockItem.Fields.IS_ESSENTIAL).eq(True)
        )
        for item in items:
            self._merge(
                candidates,
                item.id,
                _Candidate(stock_item=item, added_via=ADDED_VIA_AUTO_FLAGGED),
            )

    def _collect_recipes(
        self,
        candidates: Dict[UUID, _Candidate],
        recipe_ids: List[UUID],
        unlinked_skipped: List[_UnlinkedSkip],
    ) -> None:
        # Pull each recipe with ingredients, then for each ingredient stock
        # item: if it's not stocked, schedule it. Recipe name goes into
        # `detail` so the UI can render "auto: recipe Tomato Soup".
        # FU-505 — ingredients without a linked StockItem can't be turned
        # into a shopping-list line (no stock-item id to anchor the line);
        # collect them so the response can carry a "you'll need to add
        # these manually" warning back to the SPA.
        for rid in recipe_ids:
            recipe = (
                self.repository.get(Recipe)
                .include(Recipe.Fields.INGREDIENTS)
                .by_id(rid)
            )
            if recipe is None:
                continue
            ingredients = recipe.ingredients or []
            for ing in ingredients:
                # R-032 — `stock_item` is lazy="noload" and is NOT included on
                # this `by_id().include(INGREDIENTS)` load, so reading the
                # relationship always returned None: every linked ingredient was
                # mis-reported as unlinked AND never added as a line (the recipe
                # + meal-plan sources silently added nothing). Read the loaded FK
                # column (`_stock_item_id`, the codebase's underscore-bound FK
                # convention) instead — FU-587 fix; the separate StockItem fetch
                # below already resolves the real rows.
                if ing._stock_item_id is None:
                    unlinked_skipped.append(_UnlinkedSkip(
                        recipe_name=recipe.name,
                        ingredient_name=(ing.raw_text or "").strip() or "(unnamed ingredient)",
                    ))
            stock_item_ids = [ing._stock_item_id for ing in ingredients if ing._stock_item_id is not None]
            if not stock_item_ids:
                continue
            items: List[StockItem] = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.STOCK_LEVEL)
                .all(EntityField(StockItem, "id").in_(stock_item_ids))
            )
            for item in items:
                if item.stock_level is not None and item.stock_level.sequence == SEQ_STOCKED:
                    continue
                self._merge(
                    candidates,
                    item.id,
                    _Candidate(
                        stock_item=item,
                        added_via=ADDED_VIA_AUTO_RECIPE,
                        detail=recipe.name,
                    ),
                )

    def _collect_meal_plan_week(
        self,
        candidates: Dict[UUID, _Candidate],
        week_start: date,
        unlinked_skipped: List[_UnlinkedSkip],
    ) -> None:
        # Window = 7 days starting at week_start. Pull every entry in range,
        # then every recipe their meals reference, then ingredients. Items
        # already stocked are subtracted (the user has them).
        week_end = week_start + timedelta(days=6)
        plans: List[MealPlan] = (
            self.repository.get(MealPlan).include(MealPlan.Fields.ENTRIES).all()
        )
        recipe_ids: List[UUID] = []
        for plan in plans:
            for entry in plan.entries or []:
                if not (week_start <= entry.scheduled_for <= week_end):
                    continue
                if entry.consumed_at is not None:
                    # Past entries already drew from the pool — they're
                    # not part of the upcoming shop.
                    continue
                _RecipeId = getattr(entry, "_recipe_id", None)
                if _RecipeId is not None:
                    recipe_ids.append(_RecipeId)

        if not recipe_ids:
            return

        # Dedupe recipe IDs and fetch with ingredients
        for rid in set(recipe_ids):
            recipe = (
                self.repository.get(Recipe)
                .include(Recipe.Fields.INGREDIENTS)
                .by_id(rid)
            )
            if recipe is None:
                continue
            ingredients = recipe.ingredients or []
            for ing in ingredients:
                # R-032 — `stock_item` is lazy="noload" and is NOT included on
                # this `by_id().include(INGREDIENTS)` load, so reading the
                # relationship always returned None: every linked ingredient was
                # mis-reported as unlinked AND never added as a line (the recipe
                # + meal-plan sources silently added nothing). Read the loaded FK
                # column (`_stock_item_id`, the codebase's underscore-bound FK
                # convention) instead — FU-587 fix; the separate StockItem fetch
                # below already resolves the real rows.
                if ing._stock_item_id is None:
                    unlinked_skipped.append(_UnlinkedSkip(
                        recipe_name=recipe.name,
                        ingredient_name=(ing.raw_text or "").strip() or "(unnamed ingredient)",
                    ))
            stock_item_ids = [ing._stock_item_id for ing in ingredients if ing._stock_item_id is not None]
            if not stock_item_ids:
                continue
            items: List[StockItem] = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.STOCK_LEVEL)
                .all(EntityField(StockItem, "id").in_(stock_item_ids))
            )
            for item in items:
                if item.stock_level is not None and item.stock_level.sequence == SEQ_STOCKED:
                    continue
                self._merge(
                    candidates,
                    item.id,
                    _Candidate(
                        stock_item=item,
                        added_via=ADDED_VIA_AUTO_MEAL_PLAN,
                        detail=f"Meal plan · {week_start.isoformat()}",
                    ),
                )

    def _collect_frequently_added(
        self,
        candidates: Dict[UUID, _Candidate],
        limit: int,
    ) -> None:
        # Top-N by historic add count across all lines (ticked + archived
        # included — past usage signal). Borrowed from the standalone
        # /frequently-added endpoint but inlined to avoid the round-trip.
        session = self.repository.session
        rows = session.execute(
            select(
                ShoppingListLine.stock_item_id,
                func.count().label("add_count"),
            ).group_by(ShoppingListLine.stock_item_id)
        ).all()
        if not rows:
            return
        counts: Dict[UUID, int] = {row[0]: int(row[1]) for row in rows}
        ranked_ids = sorted(counts.keys(), key=lambda i: -counts[i])[: max(1, limit)]
        if not ranked_ids:
            return
        items: List[StockItem] = self.repository.get(StockItem).all(
            EntityField(StockItem, "id").in_(ranked_ids)
        )
        for item in items:
            self._merge(
                candidates,
                item.id,
                _Candidate(
                    stock_item=item, added_via=ADDED_VIA_AUTO_FREQUENTLY_ADDED
                ),
            )

    @staticmethod
    def _merge(
        candidates: Dict[UUID, _Candidate],
        stock_item_id: UUID,
        new_cand: _Candidate,
    ) -> None:
        existing = candidates.get(stock_item_id)
        if existing is None:
            candidates[stock_item_id] = new_cand
        else:
            candidates[stock_item_id] = existing.replace_with(new_cand)


def _response_payload(response: AutoGenerateResponse) -> dict:
    return {
        "shopping_list_id": response.shopping_list_id,
        "added_count": response.added_count,
        "skipped_already_on_list": response.skipped_already_on_list,
        "nothing_to_add": response.nothing_to_add,
        "lines": [
            {
                "line_id": l.line_id,
                "stock_item_id": l.stock_item_id,
                "added_via": l.added_via,
                "detail": l.detail,
            }
            for l in response.lines
        ],
        # FU-505 — unlinked recipe/meal-plan ingredients the auto-generator
        # couldn't turn into stock-item-anchored lines. SPA renders a
        # warning banner listing them.
        "unlinked_skipped": [
            {
                "recipe_name": u.recipe_name,
                "ingredient_name": u.ingredient_name,
            }
            for u in response.unlinked_skipped
        ],
    }


@SHOPPING_LIST_ROUTER.route("/auto-generate", methods=["POST"])
@has_request_body(AutoGenerateRequest)
def auto_generate():
    _Logger = logging.getLogger(__name__)
    _Request: AutoGenerateRequest = get_request_body()
    _Response = AutoGenerateHandler(SqlAlchemyRepository()).handle(_Request)
    if _Response.list_not_found:
        return not_found("ShoppingList", _Request.merge_into_list_id or "?")
    _Logger.info(
        "Auto-generate -> list %s: +%d added, %d already on list",
        _Response.shopping_list_id,
        _Response.added_count,
        _Response.skipped_already_on_list,
    )
    return ok(_response_payload(_Response))
