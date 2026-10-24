"""X5 — multi-source auto-generated shopping lists.

  POST /api/shopping-lists/auto-generate
      Generic builder. Each `sources.*` flag pulls candidate stock items
      from a different angle; the handler dedupes across sources and
      either appends to an existing list (`merge_into_list_id`) or creates
      a fresh one.

Lines produced here are NOT marked `is_auto_added`. That flag means "no
user action put this here" — it belongs to the low-stock hook in
update_stock_item, which fires on its own. Everything below runs because
the user ticked sources in the New list dialog seconds earlier, so the
lines are as asked-for as anything they typed by hand.

The per-source provenance this module used to stamp on each line
(`auto_recipe` / `auto_essential` / …), along with the priority ladder
that arbitrated between sources claiming the same item, was deleted on
2026-09-19: it restated the user's own dialog input back at them on every
row, forever. Dedupe is now just "first source to claim the item wins",
which is all the ladder ever affected once the labels were gone.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.shopping_list import (ShoppingList, ShoppingListLine,
                                                    format_list_date)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists._frequently_added import (
    DEFAULT_FREQUENTLY_ADDED_LIMIT, rank_frequently_added_ids)
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.features.shopping_lists._line_defaults import apply_line_defaults
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# Stock level sequences (seed.py): 0=Stocked, 1=Low, 2=Out.
SEQ_STOCKED = 0
SEQ_LOW = 1
SEQ_OUT = 2
LOW_OR_OUT = {SEQ_LOW, SEQ_OUT}


class AutoGenerateSources(BaseModel):
    model_config = ConfigDict(extra="forbid")
    low_stock: bool = False
    out_of_stock: bool = False
    # When True, only essential (is_essential) items count for the low/out
    # picks above — useful for "shop the staples I'm short on" runs.
    essentials_only_for_low: bool = False
    # Every essential item, whatever its stock level ("always have these
    # in"). Was called `flagged` until 2026-09-19, which implied a flag
    # column that has never existed — the collector reads `is_essential`,
    # the same field `essentials_only_for_low` filters on.
    essentials: bool = False
    frequently_added: bool = False
    # Top-N count for frequently_added (only consulted when flag is set).
    frequently_added_limit: int = DEFAULT_FREQUENTLY_ADDED_LIMIT
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
class _LineResult:
    line_id: UUID
    stock_item_id: UUID


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

    The handler returns the resulting list ID + the ids of the lines it
    wrote so the frontend can navigate straight to the new list without an
    extra round-trip.
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
        candidates: Dict[UUID, StockItem] = {}
        # FU-505 — recipe / meal-plan collectors append here whenever an
        # ingredient can't be turned into a stock-item-anchored line. The
        # SPA renders these as a "you'll need to add these manually" banner.
        unlinked_skipped: List[_UnlinkedSkip] = []

        if request.sources.low_stock or request.sources.out_of_stock:
            self._collect_low_or_out(candidates, request.sources)

        if request.sources.essentials:
            self._collect_essentials(candidates)

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
        new_lines: List[ShoppingListLine] = []
        skipped = 0
        for stock_item_id in candidates:
            if stock_item_id in on_list:
                skipped += 1
                continue
            new_lines.append(ShoppingListLine(
                shopping_list_id=target.id,
                stock_item_id=stock_item_id,
                quantity=1,
                sequence=next_sequence,
                added_at=now,
            ))
            next_sequence += 1
        apply_line_defaults(self.repository, new_lines)
        added: List[_LineResult] = []
        for line in new_lines:
            self.repository.add(line)
            added.append(
                _LineResult(line_id=line.id, stock_item_id=line.stock_item_id)
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
            # Household date through `format_list_date` (R-021 / R-056;
            # finalisation 03-R8) — was a server-local `strftime` copy.
            today = household_today(self.repository)
            list_name = f"Auto {n} · {format_list_date(today, today)}"

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
        candidates: Dict[UUID, StockItem],
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
            self._merge(candidates, item.id, item)

    def _collect_essentials(self, candidates: Dict[UUID, StockItem]) -> None:
        # "Always include in auto-generated lists" — essentials go on the
        # list even if currently stocked. The user has explicitly said
        # "always restock this".
        items: List[StockItem] = self.repository.get(StockItem).all(
            EntityField(StockItem, StockItem.Fields.IS_ESSENTIAL).eq(True)
        )
        for item in items:
            self._merge(candidates, item.id, item)

    def _collect_recipes(
        self,
        candidates: Dict[UUID, StockItem],
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
                self._merge(candidates, item.id, item)

    def _collect_meal_plan_week(
        self,
        candidates: Dict[UUID, StockItem],
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
                self._merge(candidates, item.id, item)

    def _collect_frequently_added(
        self,
        candidates: Dict[UUID, StockItem],
        limit: int,
    ) -> None:
        ranked_ids = rank_frequently_added_ids(self.repository.session, limit)
        if not ranked_ids:
            return
        items: List[StockItem] = self.repository.get(StockItem).all(
            EntityField(StockItem, "id").in_(ranked_ids)
        )
        for item in items:
            self._merge(
                candidates,
                item.id,
                item,
            )

    @staticmethod
    def _merge(
        candidates: Dict[UUID, StockItem],
        stock_item_id: UUID,
        item: StockItem,
    ) -> None:
        # First source to claim an item keeps it. Sources no longer differ
        # in what they write, so there is nothing left to arbitrate — this
        # is dedupe, not precedence.
        candidates.setdefault(stock_item_id, item)


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
