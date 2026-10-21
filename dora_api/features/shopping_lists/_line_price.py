"""Shopping-line price helpers (FU-227 chunk 5).

Two server-owned chokepoints, both deliberately framework-free and pure so the
``/finish`` handler, the budget/waste/assistant reports, and the dev seed can
all share one definition (R-003 — no domain rule lives in two places):

* :func:`line_paid_unit_price` — the **actual→picked ladder**. Before this
  extract it was copy-pasted in ``budget.py``, ``waste.py`` and
  ``assistant/tools.py`` (K2); the harvest path would have been the 5th copy.
* :func:`harvest_observation_fields` — the E4 rule that turns "what you paid for
  this line" into the folded ``(total_price, total_measure, unit)`` observation
  shape (A1). A sized product in a measurable dimension yields a *measure*
  observation; everything else falls back to a *count* observation in ``ea``.
* :func:`resolve_store_id` — the **store ladder** (2026-08-28), the money
  ladder's twin. Added when a fifth rung (`planned_store_id`) landed and the
  ordering was still an if/elif chain inline in the detail handler, where
  nothing could test it.
"""
from __future__ import annotations

from uuid import UUID

from dora_api.domain import units
from dora_api.domain.entities.shopping_list import ShoppingListLine


def line_paid_unit_price(line: ShoppingListLine) -> float | None:
    """The per-unit price actually paid for a shopping line, via the standard
    ladder: the user-entered ``actual_unit_price`` wins, else the
    ``picked_offer_price`` snapshot taken at commit-to-offer time, else
    ``None`` (no captured price — the line doesn't contribute to spend).

    R-003 chokepoint (K2): the single definition of "what did this line cost".
    """
    if line.actual_unit_price is not None:
        return float(line.actual_unit_price)
    if line.picked_offer_price is not None:
        return float(line.picked_offer_price)
    return None


def harvest_observation_fields(
    *,
    unit_price: float,
    quantity: int | None,
    size_value: float | None,
    size_unit: str | None,
    product_pack_count: int | None = None,
) -> tuple[float, float, str, int | None]:
    """Fold a finished line's price into one observation's
    ``(total_price, total_measure, unit, pack_count)`` (A1 / E4 + FU-227
    multipack follow-up).

    ``unit_price`` is per *item* (one bottle, one pack); ``quantity`` is how
    many items the line bought. ``total_price`` is therefore always
    ``unit_price × quantity`` — never multiplied by the measure (a sized
    product's pack size would otherwise be double-counted).

    The measure splits two ways:

    * **Sized product** — when the selected product has a positive size in a
      price dimension (volume / mass / count), the observation is a *measure*
      observation: ``total_measure = size_value × quantity`` in the product's
      canonical unit (e.g. 2 bottles × 2 L → 4 L). ``your_prices`` then
      normalises to the dimension's canonical denominator for the median.
    * **Sizeless / unsupported unit** — a *count* observation: one ``ea`` per
      item (``total_measure = quantity``, ``unit = "ea"``). Covers the
      "$9 for 3 punnets" case and product-less lines.

    The returned ``pack_count`` carries the multipack context: when the
    product has ``pack_count`` set (e.g. ``4`` for "125g × 4 pack"), the obs
    inherits ``product_pack_count × quantity`` so a "$4.20 for 1 box of
    4-pack" obs renders as "4 × 125g" rather than "500g flat". ``None`` for
    non-multipack purchases.
    """
    qty = quantity or 1
    total_price = float(unit_price) * qty
    pack_count: int | None = None
    if product_pack_count and product_pack_count > 0:
        pack_count = int(product_pack_count) * qty
    if size_value and float(size_value) > 0 and size_unit:
        udef = units.find_unit(size_unit)
        if udef is not None and udef.dimension in units.PRICE_DIMENSIONS:
            return total_price, float(size_value) * qty, udef.canonical, pack_count
    return total_price, float(qty), "ea", pack_count


def resolve_store_id(
    *,
    purchased_store_id: UUID | None,
    planned_store_id: UUID | None,
    usual_store_id: UUID | None,
    last_purchase_store_id: UUID | None,
    chosen_offer_store_id: UUID | None,
) -> UUID | None:
    """The **store ladder**: which store a shopping line is associated with.

    Five rungs, first non-null wins::

        purchased  → where you actually bought it (a record; only after the fact)
        planned    → where you mean to buy it, *on this list*
        usual      → ``StockItem.usual_store_id``, a standing preference
        last       → the store of the most recent actual purchase
        offer      → the chosen product offer's store

    Two orderings matter and both are deliberate:

    * **Intent beats history**, which is the reverse of
      :func:`line_paid_unit_price`. That ladder answers "what did this cost",
      where what you really paid outranks an advertised price; this one answers
      "where do I *plan* to buy it", where a stated intention outranks where you
      happened to shop last time.
    * **The more specific intent wins.** ``planned`` is a choice made for this
      list; ``usual`` is a habit that applies to every list. A shop where you're
      making an exception must not be overruled by the rule.

    R-003 chokepoint, and pure so the ordering is testable without a repository
    — the ladder decides which section a line lands in under Order-by → Store,
    so getting a rung wrong silently re-groups the list. ``None`` ⇒ the
    "No store set" bucket.
    """
    return (
        purchased_store_id
        or planned_store_id
        or usual_store_id
        or last_purchase_store_id
        or chosen_offer_store_id
    )
