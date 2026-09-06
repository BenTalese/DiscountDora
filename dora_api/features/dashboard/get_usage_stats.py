"""GET /api/dashboard/usage-stats — what this household has *done* with Dora.

Owner feedback 2026-09-05: *"About screen 'your kitchen' should be more 'your
usage of the app' rather than a repeat of the dashboard or reports. Like total
stock items (already there I think), total spend tracked, total meals planned,
total shopping lists, total recipes curated, etc."*

The About page's "at a glance" block was reading
`GET /api/dashboard/summary` — the dashboard's own payload — so it showed
*current state*: how many items are low, how many are out, what's coming up
this week. Those are the dashboard's job and they answer "what needs doing".
Standing in the About page they answered a question nobody asked there, and
they changed every time you shopped.

These are **cumulative** instead: counts that only ever go up, of things the
household has accumulated or done. The distinction is the whole point of the
owner's note — "items running low" is a chore list, "1,208 prices recorded" is
a record of use. Nothing here is a filtered or windowed figure; where an
entity is deletable the count is of what survives, which is the honest answer
to "how much have you got".

**Money-gated fields are None, not zero, when money is off** (R-058). Zero
would read as "you have tracked no spend", which is false — the install has
opted out of the question. The SPA drops the tile entirely rather than
rendering "—".
"""
import logging
from dataclasses import dataclass

from dora_api.app import db
from dora_api.domain.entities.shopping_list import SHOPPING_LIST_STATUS_DONE
from dora_api.features.app_settings.access import money_features_enabled
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class UsageStatsDto:
    stock_items: int
    recipes: int
    meals_planned: int
    meals_cooked: int
    shopping_lists: int
    shops_completed: int
    # Money-gated (R-058). None — never 0 — when the install has money off.
    total_spend: float | None
    prices_recorded: int | None


class GetUsageStatsHandler:
    def __init__(self, repository: SqlAlchemyRepository) -> None:
        self.repository = repository

    def _count(self, table_name: str, where=None) -> int:
        from sqlalchemy import func, select
        table = db.metadata.tables[table_name]
        stmt = select(func.count()).select_from(table)
        if where is not None:
            stmt = stmt.where(where)
        return int(db.session.execute(stmt).scalar() or 0)

    def _total_spend(self) -> float:
        """Lifetime spend, on exactly the definition `/reports/spend-by-store`
        uses — ticked lines on completed lists, priced `actual` first and
        `picked_offer` second, times quantity.

        Deliberately the same rule rather than a new one (R-003): if About says
        one number and the reports page says another for the same install, one
        of them is wrong and the user has no way to tell which. What is dropped
        here is only the *store attribution* — that report's remaining
        complexity is entirely about deciding which shop a line belongs to, and
        a single total doesn't ask.

        Lines with neither price are skipped, not counted as zero — the same
        silent-skip the report applies. That makes this a floor rather than a
        true total, which is the honest reading of "spend *tracked*".
        """
        from sqlalchemy import func, select
        lists = db.metadata.tables["ShoppingList"]
        lines = db.metadata.tables["ShoppingListLine"]
        unit_price = func.coalesce(
            lines.c.actual_unit_price, lines.c.picked_offer_price,
        )
        stmt = (
            select(func.sum(unit_price * func.coalesce(lines.c.quantity, 1)))
            .select_from(lines.join(lists, lists.c.id == lines.c.shopping_list_id))
            .where(
                lists.c.status == SHOPPING_LIST_STATUS_DONE,
                lines.c.is_ticked.is_(True),
                unit_price.isnot(None),
            )
        )
        return round(float(db.session.execute(stmt).scalar() or 0.0), 2)

    def handle(self) -> UsageStatsDto:
        lists = db.metadata.tables["ShoppingList"]
        money_on = money_features_enabled(self.repository)

        return UsageStatsDto(
            stock_items=self._count("StockItem"),
            recipes=self._count("Recipe"),
            # Every entry ever placed on a plan, including past weeks. The
            # dashboard counts only what is upcoming; this is the opposite
            # question and the reason the About block needed its own endpoint.
            meals_planned=self._count("MealPlanEntry"),
            # One row per cook (a batch cook that feeds five days is one
            # event), so this counts cooking sessions, not portions.
            meals_cooked=self._count("CookEvent"),
            shopping_lists=self._count("ShoppingList"),
            shops_completed=self._count(
                "ShoppingList", lists.c.status == SHOPPING_LIST_STATUS_DONE,
            ),
            total_spend=self._total_spend() if money_on else None,
            prices_recorded=(
                self._count("StockItemPriceObservation") if money_on else None
            ),
        )


@DASHBOARD_ROUTER.route("/usage-stats", methods=["GET"])
def get_usage_stats():
    _Logger = logging.getLogger(__name__)
    _Result = GetUsageStatsHandler(SqlAlchemyRepository()).handle()
    _Logger.debug(
        "Usage stats: %d items, %d recipes, %d meals planned",
        _Result.stock_items, _Result.recipes, _Result.meals_planned,
    )
    return ok(_Result)
