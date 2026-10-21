"""Which one of its stock item a recipe ingredient means.

An ingredient linked to "Cheese" can narrow it with a name of its own
("tasty cheddar"), one of the item's preferred buys, or one of its linked
products. The name is what the recipe shows; the picks are ids only, carried
onto a shopping line when the recipe is added to one. There is deliberately no
precedence between them: the editor fills the name from a pick, so the label is
always the one displayed value (R-053). This module is the write rule for all
three (R-003).

Cookability ignores all of it: having any cheese still counts.
"""
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.preferred_buy import PreferredBuy
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.products.product_links import linked_stock_items
from dora_api.infrastructure.ports import Repository


class InvalidIngredientChoice(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class IngredientChoice:
    label: str | None
    preferred_buy_id: UUID | None
    selected_product_id: UUID | None


def resolve_ingredient_choice(
    repository: Repository,
    stock_item: StockItem | None,
    label: str | None,
    preferred_buy_id: UUID | None,
    selected_product_id: UUID | None,
) -> IngredientChoice:
    """Validate a requested choice against the ingredient's stock item.

    A preferred buy or product must belong to that item; an unlinked row has
    no item to narrow, so it can carry neither. The label is free text and is
    kept as given (trimmed, blank as null).
    """
    clean_label = (label or "").strip() or None
    if preferred_buy_id is None and selected_product_id is None:
        return IngredientChoice(clean_label, None, None)
    if stock_item is None:
        raise InvalidIngredientChoice(
            "An ingredient with no pantry item can't pick a preferred buy or product."
        )
    if preferred_buy_id is not None:
        pb = repository.get(PreferredBuy).by_id(preferred_buy_id)
        if pb is None or pb.stock_item_id != stock_item.id:
            raise InvalidIngredientChoice(
                f"Preferred buy {preferred_buy_id} does not belong to '{stock_item.name}'."
            )
    if selected_product_id is not None:
        # Read the join directly: `stock_item` arrives already in the session
        # with `products` noloaded, so an include would hand back the same
        # empty collection.
        link = linked_stock_items(repository, [selected_product_id]).get(selected_product_id)
        if link is None or link.stock_item_id != stock_item.id:
            raise InvalidIngredientChoice(
                f"Product {selected_product_id} is not linked to '{stock_item.name}'."
            )
    return IngredientChoice(clean_label, preferred_buy_id, selected_product_id)

