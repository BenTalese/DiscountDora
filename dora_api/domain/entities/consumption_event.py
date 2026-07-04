from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Source markers — WHY a consumption event was recorded. Kept as plain
# strings (not an enum column) to match the codebase's other kind/source
# columns (StockItemWasteEvent.reason, StockItemExpiryEvent.kind).
CONSUMPTION_SOURCE_COOK = "cook"      # depleted by finishing a recipe (P6-07)
CONSUMPTION_SOURCE_MANUAL = "manual"  # user manually lowered the level
CONSUMPTION_SOURCE_WASTE = "waste"    # thrown away (mirrors a waste event)


@dataclass
class ConsumptionEvent(BaseEntity):
    """P6-07 (FU-449) — append-only log of a stock item being *drawn down*.

    The missing leg of the closed loop: purchases (P6-01) told run-out
    prediction when stock came *in*, but nothing recorded when it went
    *out* by cooking. Every time the cook-mode finish dialog lowers an
    item's level (or a manual level drop happens), we persist a
    consumption event so cadence (P6-04) and the Zero-Input Pantry belief
    (P8-07) can blend consumption rhythm with purchase rhythm — i.e.
    run-out prediction shifts when you *cook* with something, not only
    when you *buy* it.

    Distinct from `CookEvent` (which is recipe-scoped: "you cooked Pasta
    Bake"). This is stock-item-scoped: "the Pasta Bake cook drew down your
    Passata." One cook can spawn several consumption events (one per
    depleted ingredient) or none (a cook where nothing was marked down).

    `stock_item_name` / `recipe_name` are denormalised so history survives
    a delete/rename — same policy as `StockItemWasteEvent.stock_item_name`
    and `CookEvent.recipe_name`. Both FKs are SET NULL on delete.

    `from_sequence` / `to_sequence` capture the level band transition
    (StockLevel.sequence) so the belief model can weight a drop-to-out
    more heavily than a drop-one-band; both nullable for robustness.
    """
    stock_item_id: UUID | None
    stock_item_name: str
    recipe_id: UUID | None
    recipe_name: str | None
    source: str
    from_sequence: int | None
    to_sequence: int | None
    occurred_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        STOCK_ITEM_NAME = "stock_item_name"
        RECIPE_ID = "recipe_id"
        RECIPE_NAME = "recipe_name"
        SOURCE = "source"
        FROM_SEQUENCE = "from_sequence"
        TO_SEQUENCE = "to_sequence"
        OCCURRED_AT = "occurred_at"
