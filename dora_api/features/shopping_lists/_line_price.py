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
"""
from __future__ import annotations

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
) -> tuple[float, float, str]:
    """Fold a finished line's price into one observation's
    ``(total_price, total_measure, unit)`` (A1 / E4).

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
    """
    qty = quantity or 1
    total_price = float(unit_price) * qty
    if size_value and float(size_value) > 0 and size_unit:
        udef = units.find_unit(size_unit)
        if udef is not None and udef.dimension in units.PRICE_DIMENSIONS:
            return total_price, float(size_value) * qty, udef.canonical
    return total_price, float(qty), "ea"
